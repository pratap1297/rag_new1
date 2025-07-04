"""
Ingestion Engine
Main engine for processing and ingesting documents
"""
import logging
import mimetypes
import hashlib
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..core.error_handling import IngestionError, FileProcessingError
from ..core.unified_error_handling import (
    ErrorCode, ErrorInfo, ErrorContext, Result, 
    with_error_handling, IngestionErrorHandler
)
from ..core.metadata_manager import get_metadata_manager, MetadataSchema
from .processors.base_processor import ProcessorRegistry
from .processors.excel_processor import ExcelProcessor
from .processors import create_processor_registry
from ..core.progress_tracker import ProgressTracker, ProgressStage, ProgressStatus
from ..ingestion.progress_integration import ProgressTrackedIngestion

class IngestionEngine:
    """Main document ingestion engine with progress tracking"""
    
    def __init__(self, chunker, embedder, faiss_store, metadata_store, config_manager, progress_tracker: Optional[ProgressTracker] = None):
        self.chunker = chunker
        self.embedder = embedder
        self.faiss_store = faiss_store
        self.metadata_store = metadata_store
        self.config_manager = config_manager
        self.config = config_manager.get_config()
        self.progress_tracker = progress_tracker or ProgressTracker()
        self.progress_helper = ProgressTrackedIngestion(self.progress_tracker)
        
        # Initialize metadata manager
        self.metadata_manager = get_metadata_manager()
        
        # Initialize processor registry with all available processors
        try:
            # Create processor config from ingestion config
            processor_config = self.config.ingestion.__dict__.copy()
            logging.info(f"DEBUG: Created processor config with keys: {list(processor_config.keys())}")
            
            # Add Azure AI config if available
            azure_config = None
            try:
                azure_config_obj = self.config_manager.get_config('azure_ai')
                if azure_config_obj:
                    azure_config = azure_config_obj.__dict__
                    processor_config['azure_ai'] = azure_config
                    logging.info("Azure AI config added to processor config")
            except Exception as e:
                logging.debug(f"Azure AI config not available: {e}")
            
            # Create registry with all processors
            self.processor_registry = create_processor_registry(processor_config)
            
            # If we have Azure config, ensure enhanced PDF processor is registered
            if azure_config and azure_config.get('computer_vision_endpoint') and azure_config.get('computer_vision_key'):
                try:
                    from .processors.enhanced_pdf_processor import EnhancedPDFProcessor
                    from ..integrations.azure_ai.azure_client import AzureAIClient
                    
                    # Create Azure client
                    azure_client = AzureAIClient(azure_config)
                    
                    # Create and register enhanced PDF processor
                    enhanced_pdf = EnhancedPDFProcessor(processor_config, azure_client)
                    self.processor_registry.register(enhanced_pdf)
                    logging.info("Enhanced PDF Processor with Azure CV registered successfully")
                except Exception as e:
                    logging.error(f"Failed to register Enhanced PDF Processor: {e}")
            
            logging.info(f"Processor registry initialized with {len(self.processor_registry.list_processors())} processors")
            
        except Exception as e:
            logging.error(f"Failed to create processor registry: {e}")
            logging.error(f"DEBUG: Exception type: {type(e)}")
            import traceback
            logging.error(f"DEBUG: Full traceback: {traceback.format_exc()}")
            # Fallback to empty registry
            self.processor_registry = ProcessorRegistry()
            # Still register Excel processor manually as fallback
            self._register_excel_processor()
        
        logging.info("Ingestion engine initialized with managed metadata")
    
    def _register_excel_processor(self):
        """Register Excel processor with robust Azure AI support if configured"""
        try:
            # Try to get Azure AI configuration
            azure_config = None
            try:
                azure_config = self.config_manager.get_config('azure_ai')
            except Exception as e:
                logging.debug(f"Azure AI config not available: {e}")
            
            # Use robust Excel processor with comprehensive error handling
            from .processors.robust_excel_processor import RobustExcelProcessor
            from ..integrations.azure_ai.config_validator import AzureAIConfigValidator
            from ..integrations.azure_ai.robust_azure_client import RobustAzureAIClient
            
            # Prepare processor config
            processor_config = self.config.ingestion.__dict__.copy()
            
            # Add Azure AI config if available
            if azure_config:
                try:
                    # Validate and fix Azure configuration
                    fixed_azure_config, issues = AzureAIConfigValidator.validate_and_fix(azure_config.__dict__)
                    
                    if issues:
                        logging.info(f"Azure AI configuration fixes applied: {len(issues)} issues")
                        for issue in issues[:5]:  # Log first 5 issues
                            logging.debug(f"Config fix: {issue}")
                    
                    # Check configuration status
                    config_status = AzureAIConfigValidator.get_configuration_status(fixed_azure_config)
                    
                    if config_status['overall']['configuration_complete']:
                        # Initialize robust Azure client
                        try:
                            azure_client = RobustAzureAIClient(fixed_azure_config)
                            
                            # Check client health
                            if azure_client.is_healthy():
                                processor_config['azure_ai'] = fixed_azure_config
                                excel_processor = RobustExcelProcessor(
                                    config=processor_config,
                                    azure_client=azure_client
                                )
                                available_services = azure_client.get_available_services()
                                logging.info(f"Excel processor registered with Azure AI support: {available_services}")
                            else:
                                # Client not healthy, use without Azure AI
                                excel_processor = RobustExcelProcessor(config=processor_config)
                                service_status = azure_client.get_service_status()
                                logging.warning(f"Azure AI services not healthy, using fallback processing. Status: {service_status['overall_health']}")
                        
                        except Exception as e:
                            # Azure client initialization failed
                            excel_processor = RobustExcelProcessor(config=processor_config)
                            logging.error(f"Failed to initialize Azure AI client: {e}")
                    else:
                        # Configuration incomplete
                        excel_processor = RobustExcelProcessor(config=processor_config)
                        missing_services = [s for s, status in config_status['services'].items() if not status['configured']]
                        logging.info(f"Azure AI configuration incomplete (missing: {missing_services}), using fallback processing")
                
                except Exception as e:
                    # Configuration validation failed
                    excel_processor = RobustExcelProcessor(config=processor_config)
                    logging.error(f"Azure AI configuration validation failed: {e}")
            else:
                # No Azure AI configuration
                excel_processor = RobustExcelProcessor(config=processor_config)
                logging.info("No Azure AI configuration found, using local processing only")
            
            # Register the processor
            self.processor_registry.register(excel_processor)
            
            # Log processor capabilities
            processor_info = excel_processor.get_processor_info()
            logging.info(f"Excel processor registered: {processor_info['capabilities']}")
            
        except ImportError as e:
            # Fallback to basic Excel processor if robust version not available
            logging.warning(f"Robust Excel processor not available: {e}")
            try:
                excel_processor = ExcelProcessor(config=self.config.ingestion.__dict__)
                self.processor_registry.register(excel_processor)
                logging.info("Basic Excel processor registered as fallback")
            except Exception as fallback_e:
                logging.error(f"Failed to register any Excel processor: {fallback_e}")
        
        except Exception as e:
            logging.error(f"Failed to register Excel processor: {e}")
            # Try basic fallback
            try:
                excel_processor = ExcelProcessor(config=self.config.ingestion.__dict__)
                self.processor_registry.register(excel_processor)
                logging.info("Basic Excel processor registered after error")
            except Exception as fallback_e:
                logging.error(f"All Excel processor registration attempts failed: {fallback_e}")
    
    def _generate_consistent_doc_id(self, file_path: Path, metadata: Dict[str, Any]) -> str:
        """Generate consistent doc_id that matches what deletion expects"""
        # Use the same logic as in delete_file
        if metadata.get('doc_path'):
            return metadata['doc_path']
        # Use original filename if available, otherwise use temp file path
        original_filename = metadata.get('original_filename')
        if original_filename:
            return original_filename
        return str(file_path)
    
    def _generate_doc_id(self, metadata: Dict[str, Any]) -> str:
        """Generate a proper document ID based on available metadata"""
        # Priority 1: Use doc_path if available (most reliable)
        if metadata.get('doc_path'):
            doc_path = metadata['doc_path']
            # Remove leading slash and convert to proper ID format
            if doc_path.startswith('/'):
                doc_path = doc_path[1:]
            return doc_path.replace('/', '_').replace(' ', '_')
        
        # Priority 2: Use filename if available
        if metadata.get('filename'):
            filename = metadata['filename']
            # Remove extension and clean up
            if '.' in filename:
                filename = filename.rsplit('.', 1)[0]
            return f"docs_{filename.replace(' ', '_').replace('-', '_')}"
        
        # Priority 3: Use file_name from file_path
        if metadata.get('file_name'):
            file_name = metadata['file_name']
            if '.' in file_name:
                file_name = file_name.rsplit('.', 1)[0]
            return f"docs_{file_name.replace(' ', '_').replace('-', '_')}"
        
        # Priority 4: Generate from file_path
        if metadata.get('file_path'):
            file_path = Path(metadata['file_path'])
            stem = file_path.stem
            return f"docs_{stem.replace(' ', '_').replace('-', '_')}"
        
        # Fallback: Generate a unique ID
        import uuid
        return f"docs_{uuid.uuid4().hex[:8]}"
    
    def _calculate_document_hash(self, file_path: Path) -> str:
        """Calculate hash of document content for deduplication"""
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def check_duplicate(self, file_path: str) -> Optional[str]:
        """Check if document already exists"""
        doc_hash = self._calculate_document_hash(Path(file_path))
        # Check in metadata store
        existing = self.metadata_store.find_by_hash(doc_hash)
        return existing.get('file_id') if existing else None
    
    def ingest_file(self, file_path: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Ingest a single file with progress tracking"""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileProcessingError(f"File not found: {file_path}")
        
        # Start progress tracking if available
        file_progress = None
        if self.progress_tracker:
            file_progress = self.progress_tracker.start_file(str(file_path))
        
        try:
            # Validation stage
            if self.progress_helper:
                with self.progress_helper.track_stage(str(file_path), ProgressStage.VALIDATING):
                    if file_path.stat().st_size > self.config.ingestion.max_file_size_mb * 1024 * 1024:
                        raise FileProcessingError(f"File too large: {file_path}")
            else:
                # Fallback without progress tracking
                if file_path.stat().st_size > self.config.ingestion.max_file_size_mb * 1024 * 1024:
                    raise FileProcessingError(f"File too large: {file_path}")
            
            # Check for duplicate document
            duplicate_file_id = self.check_duplicate(str(file_path))
            if duplicate_file_id:
                logging.info(f"Duplicate document detected: {file_path} (existing: {duplicate_file_id})")
                return {
                    'status': 'skipped',
                    'reason': 'duplicate',
                    'file_path': str(file_path),
                    'duplicate_file_id': duplicate_file_id
                }
            
            old_vectors_deleted = self._handle_existing_file(str(file_path))
            
            # ✅ FIX: Prepare enhanced metadata BEFORE calling processor
            # Get original filename for proper metadata handling
            original_filename = metadata.get('original_filename', str(file_path)) if metadata else str(file_path)
            
            # Create enhanced metadata that includes source information for processors
            enhanced_metadata = {
                'file_path': original_filename,  # Use original filename for file_path
                'original_filename': original_filename,
                'filename': os.path.basename(original_filename),  # Extract filename from original path
                'file_size': file_path.stat().st_size,
                'file_type': Path(original_filename).suffix,  # Get extension from original filename
                'source_type': metadata.get('source_type', 'file') if metadata else 'file',  # Respect input source_type
                'upload_source': metadata.get('upload_source', 'unknown') if metadata else 'unknown',  # ✅ PRESERVE upload_source
                'content_type': metadata.get('content_type') if metadata else None,
                'upload_timestamp': metadata.get('upload_timestamp') if metadata else None,
                'ingested_at': datetime.now().isoformat(),
                'processor': 'ingestion_engine',
                'is_update': old_vectors_deleted > 0,
                'replaced_vectors': old_vectors_deleted,
                'doc_hash': self._calculate_document_hash(file_path),
                # Include any additional metadata from the API call
                **(metadata or {})
            }
            
            # Set enhanced metadata for processors to use
            self._current_metadata = enhanced_metadata
            
            # Extraction stage
            extraction_start = datetime.now()
            if self.progress_helper:
                with self.progress_helper.track_stage(str(file_path), ProgressStage.EXTRACTING):
                    text_content = self._extract_text(file_path)
            else:
                text_content = self._extract_text(file_path)
            extraction_time = (datetime.now() - extraction_start).total_seconds()
            
            if not text_content.strip():
                return {
                    'status': 'skipped',
                    'reason': 'no_content',
                    'file_path': str(file_path)
                }
            
            # Use the enhanced metadata as file_metadata
            file_metadata = enhanced_metadata
            
            # Chunking stage
            chunking_start = datetime.now()
            if self.progress_helper:
                with self.progress_helper.track_stage(str(file_path), ProgressStage.CHUNKING):
                    # Check for processor chunks
                    if hasattr(self, '_use_processor_chunks') and self._use_processor_chunks and hasattr(self, '_processor_chunks'):
                        chunks = self._processor_chunks
                        logging.info(f"Using {len(chunks)} chunks from processor")
                        # Clean up flags
                        self._use_processor_chunks = False
                        self._processor_chunks = None
                    else:
                        chunks = self.chunker.chunk_text(text_content, file_metadata)
            else:
                # Same logic without progress tracking
                if hasattr(self, '_use_processor_chunks') and self._use_processor_chunks and hasattr(self, '_processor_chunks'):
                    chunks = self._processor_chunks
                    logging.info(f"Using {len(chunks)} chunks from processor")
                    self._use_processor_chunks = False
                    self._processor_chunks = None
                else:
                    chunks = self.chunker.chunk_text(text_content, file_metadata)
            chunking_time = (datetime.now() - chunking_start).total_seconds()
            
            if not chunks:
                return {
                    'status': 'skipped',
                    'reason': 'no_chunks',
                    'file_path': str(file_path)
                }
            
            # Validate chunk structure
            validated_chunks = self._validate_chunk_structure(chunks)
            
            # Embedding stage
            embedding_start = datetime.now()
            if self.progress_helper:
                with self.progress_helper.track_stage(str(file_path), ProgressStage.EMBEDDING):
                    chunk_texts = [chunk['text'] for chunk in validated_chunks]
                    embeddings = self.embedder.embed_texts(chunk_texts)
            else:
                chunk_texts = [chunk['text'] for chunk in validated_chunks]
                embeddings = self.embedder.embed_texts(chunk_texts)
            embedding_time = (datetime.now() - embedding_start).total_seconds()
            
            # Storing stage
            storage_start = datetime.now()
            if self.progress_helper:
                with self.progress_helper.track_stage(str(file_path), ProgressStage.STORING):
                    chunk_metadata_list = []
                    for i, (chunk, embedding) in enumerate(zip(validated_chunks, embeddings)):
                        try:
                            # Extract chunk metadata and ensure it's flat
                            chunk_meta = chunk.get('metadata', {})
                            
                            # If chunk metadata has nested 'metadata', extract it
                            if isinstance(chunk_meta.get('metadata'), dict):
                                nested_meta = chunk_meta.pop('metadata')
                                # Merge nested metadata into chunk_meta
                                for k, v in nested_meta.items():
                                    if k not in chunk_meta:
                                        chunk_meta[k] = v
                            
                            # ✅ FIX: Create base metadata that doesn't override processor metadata
                            # Only include essential chunk metadata that should NOT override processor data
                            base_chunk_metadata = {
                                'text': chunk['text'],
                                'content': chunk['text'],  # For compatibility
                                'chunk_index': i,
                                'total_chunks': len(validated_chunks),
                                'chunk_size': len(chunk['text']),
                                'doc_id': self._generate_consistent_doc_id(file_path, file_metadata),  # Use consistent ID
                                'doc_path': metadata.get('original_filename', str(file_path)) if metadata else str(file_path),  # Use original path for doc_path
                                'chunking_method': getattr(self.chunker.__class__, '__name__', 'unknown'),
                                'embedding_model': getattr(self.embedder, 'model_name', 'unknown')
                            }
                            
                            # ✅ FIX: Change merge order - put base_chunk_metadata FIRST so processor metadata takes priority
                            merged_metadata = self.metadata_manager.merge_metadata(
                                base_chunk_metadata,  # 1st: Basic chunk info (lowest priority)
                                file_metadata,        # 2nd: File metadata
                                metadata or {},       # 3rd: API upload metadata 
                                chunk_meta             # 4th: Processor chunk metadata (HIGHEST priority) ✅
                            )
                            
                            storage_metadata = self.metadata_manager.prepare_for_storage(merged_metadata)
                            chunk_metadata_list.append(storage_metadata)
                        except Exception as e:
                            logging.error(f"Failed to merge metadata for chunk {i}: {e}")
                            # Fallback metadata
                            fallback_meta = {
                                'text': chunk['text'],
                                'chunk_index': i,
                                'doc_id': self._generate_consistent_doc_id(file_path, file_metadata),
                                'doc_path': metadata.get('original_filename', str(file_path)) if metadata else str(file_path),
                                'filename': os.path.basename(metadata.get('original_filename', str(file_path))) if metadata else os.path.basename(file_path),
                                'file_path': metadata.get('original_filename', str(file_path)) if metadata else str(file_path),
                                'source_type': 'file'
                            }
                            chunk_metadata_list.append(fallback_meta)
                    
                    vector_ids = self.faiss_store.add_vectors(embeddings, chunk_metadata_list)
                    final_file_metadata = {
                        **file_metadata,
                        'chunk_count': len(validated_chunks),
                        'vector_ids': vector_ids,
                        'doc_id': chunk_metadata_list[0].get('doc_id', 'unknown') if chunk_metadata_list else 'unknown'
                    }
                    file_id = self.metadata_store.add_file_metadata(str(file_path), final_file_metadata)
            else:
                # Fallback without progress tracking (same fix applied)
                chunk_metadata_list = []
                for i, (chunk, embedding) in enumerate(zip(validated_chunks, embeddings)):
                    try:
                        # Extract chunk metadata and ensure it's flat
                        chunk_meta = chunk.get('metadata', {})
                        
                        # If chunk metadata has nested 'metadata', extract it
                        if isinstance(chunk_meta.get('metadata'), dict):
                            nested_meta = chunk_meta.pop('metadata')
                            # Merge nested metadata into chunk_meta
                            for k, v in nested_meta.items():
                                if k not in chunk_meta:
                                    chunk_meta[k] = v
                        
                        # ✅ FIX: Create base metadata that doesn't override processor metadata
                        # Only include essential chunk metadata that should NOT override processor data
                        base_chunk_metadata = {
                            'text': chunk['text'],
                            'content': chunk['text'],  # For compatibility
                            'chunk_index': i,
                            'total_chunks': len(validated_chunks),
                            'chunk_size': len(chunk['text']),
                            'doc_id': self._generate_consistent_doc_id(file_path, file_metadata),  # Use consistent ID
                            'doc_path': metadata.get('original_filename', str(file_path)) if metadata else str(file_path),  # Use original path for doc_path
                            'chunking_method': getattr(self.chunker.__class__, '__name__', 'unknown'),
                            'embedding_model': getattr(self.embedder, 'model_name', 'unknown')
                        }
                        
                        # ✅ FIX: Change merge order - put base_chunk_metadata FIRST so processor metadata takes priority
                        merged_metadata = self.metadata_manager.merge_metadata(
                            base_chunk_metadata,  # 1st: Basic chunk info (lowest priority)
                            file_metadata,        # 2nd: File metadata
                            metadata or {},       # 3rd: API upload metadata 
                            chunk_meta             # 4th: Processor chunk metadata (HIGHEST priority) ✅
                        )
                        
                        storage_metadata = self.metadata_manager.prepare_for_storage(merged_metadata)
                        chunk_metadata_list.append(storage_metadata)
                    except Exception as e:
                        logging.error(f"Failed to merge metadata for chunk {i}: {e}")
                        # Fallback metadata
                        fallback_meta = {
                            'text': chunk['text'],
                            'chunk_index': i,
                            'doc_id': self._generate_consistent_doc_id(file_path, file_metadata),
                            'doc_path': metadata.get('original_filename', str(file_path)) if metadata else str(file_path),
                            'filename': os.path.basename(metadata.get('original_filename', str(file_path))) if metadata else os.path.basename(file_path),
                            'file_path': metadata.get('original_filename', str(file_path)) if metadata else str(file_path),
                            'source_type': 'file'
                        }
                        chunk_metadata_list.append(fallback_meta)
                
                vector_ids = self.faiss_store.add_vectors(embeddings, chunk_metadata_list)
                final_file_metadata = {
                    **file_metadata,
                    'chunk_count': len(validated_chunks),
                    'vector_ids': vector_ids,
                    'doc_id': chunk_metadata_list[0].get('doc_id', 'unknown') if chunk_metadata_list else 'unknown'
                }
                file_id = self.metadata_store.add_file_metadata(str(file_path), final_file_metadata)
            
            storage_time = (datetime.now() - storage_start).total_seconds()
            
            # Indexing stage
            if self.progress_helper:
                with self.progress_helper.track_stage(str(file_path), ProgressStage.INDEXING):
                    pass
            
            # Finalizing stage
            if self.progress_helper:
                with self.progress_helper.track_stage(str(file_path), ProgressStage.FINALIZING):
                    pass
            
            # Complete the file if progress tracking is available
            if self.progress_tracker:
                metrics = {
                    'chunks_created': len(validated_chunks),
                    'vectors_created': len(vector_ids),
                    'extraction_time': extraction_time,
                    'chunking_time': chunking_time,
                    'embedding_time': embedding_time,
                    'storage_time': storage_time
                }
                self.progress_tracker.complete_file(str(file_path), metrics)
            
            logging.info(f"Successfully ingested file: {file_path} ({len(validated_chunks)} chunks)")
            if old_vectors_deleted > 0:
                logging.info(f"Replaced {old_vectors_deleted} old vectors for updated file")
            
            doc_id = chunk_metadata_list[0].get('doc_id', 'unknown') if chunk_metadata_list else 'unknown'
            return {
                'status': 'success',
                'file_id': file_id,
                'doc_id': doc_id,
                'file_path': str(file_path),
                'chunks_created': len(validated_chunks),
                'vectors_stored': len(vector_ids),
                'is_update': old_vectors_deleted > 0,
                'old_vectors_deleted': old_vectors_deleted
            }
            
        except Exception as e:
            logging.error(f"Failed to ingest file {file_path}: {e}")
            if self.progress_tracker:
                self.progress_tracker.fail_file(str(file_path), e)
            raise IngestionError(f"Failed to ingest file: {e}", details={"file_path": str(file_path)})
    
    def ingest_text(self, text: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Ingest raw text content with managed metadata"""
        try:
            if not text.strip():
                return {
                    'status': 'skipped',
                    'reason': 'no_content'
                }
            
            # ✅ NEW: Check if text is JSON and can use a processor
            text_stripped = text.strip()
            if ((text_stripped.startswith('{') and text_stripped.endswith('}')) or
                (text_stripped.startswith('[') and text_stripped.endswith(']'))):
                
                try:
                    import json
                    import tempfile
                    import os
                    
                    # Parse JSON to validate
                    json_data = json.loads(text)
                    logging.info(f"🔍 Detected JSON content in ingest_text, attempting processor route")
                    
                    # Check if it looks like ServiceNow data
                    def is_servicenow_json(data):
                        servicenow_fields = ['number', 'sys_id', 'state', 'priority', 'category', 
                                            'short_description', 'incident_number', 'created_by']
                        
                        if isinstance(data, list) and data:
                            first_item = data[0]
                            if isinstance(first_item, dict):
                                return any(field in first_item for field in servicenow_fields)
                        elif isinstance(data, dict):
                            # Check direct fields
                            if any(field in data for field in servicenow_fields):
                                return True
                            # Check nested structure (like {"incidents": [...]})
                            for key in ['incidents', 'records', 'result', 'data']:
                                if key in data and isinstance(data[key], list) and data[key]:
                                    first_record = data[key][0]
                                    if isinstance(first_record, dict):
                                        return any(field in first_record for field in servicenow_fields)
                        return False
                    
                    if is_servicenow_json(json_data):
                        logging.info(f"🎯 Detected ServiceNow JSON, using processor")
                        
                        # Create temporary JSON file
                        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as tmp_file:
                            json.dump(json_data, tmp_file, indent=2, ensure_ascii=False)
                            tmp_file_path = tmp_file.name
                        
                        try:
                            # Get processor for JSON files
                            processor = self.processor_registry.get_processor(tmp_file_path)
                            
                            if processor:
                                logging.info(f"📦 Using processor: {processor.__class__.__name__} for JSON content")
                                
                                # Use processor to get structured chunks
                                processor_result = processor.process(tmp_file_path, metadata or {})
                                
                                if processor_result.get('status') == 'success' and processor_result.get('chunks'):
                                    logging.info(f"✅ Processor created {len(processor_result['chunks'])} logical chunks")
                                    
                                    # Extract chunks and continue with normal ingestion flow
                                    processor_chunks = processor_result['chunks']
                                    
                                    # Store original metadata but update processing info
                                    base_metadata = {
                                        'source_type': metadata.get('source_type', 'text') if metadata else 'text',
                                        'ingested_at': datetime.now().isoformat(),
                                        'processor': f'{processor.__class__.__name__}_via_ingest_text',
                                        'text_length': len(text),
                                        'processing_method': 'json_processor'
                                    }
                                    
                                    # Preserve all other metadata fields
                                    if metadata:
                                        for key, value in metadata.items():
                                            if key not in base_metadata:
                                                base_metadata[key] = value
                                    
                                    # Generate embeddings for processor chunks
                                    chunk_texts = [chunk.get('text', str(chunk)) for chunk in processor_chunks]
                                    embeddings = self.embedder.embed_texts(chunk_texts)
                                    
                                    # Prepare chunk metadata using metadata manager
                                    chunk_metadata_list = []
                                    
                                    for i, (chunk, embedding) in enumerate(zip(processor_chunks, embeddings)):
                                        chunk_text = chunk.get('text', str(chunk))
                                        chunk_meta = chunk.get('metadata', {})
                                        
                                        # Create base metadata for this chunk
                                        base_chunk_metadata = {
                                            'text': chunk_text,
                                            'content': chunk_text,
                                            'chunk_index': i,
                                            'total_chunks': len(processor_chunks),
                                            'chunk_size': len(chunk_text),
                                            'doc_id': metadata.get('doc_path', metadata.get('title', 'json_document')) if metadata else 'json_document',
                                            'doc_path': metadata.get('doc_path', metadata.get('title', 'json_document')) if metadata else 'json_document',
                                            'chunking_method': f'{processor.__class__.__name__}_logical',
                                            'embedding_model': getattr(self.embedder, 'model_name', 'unknown')
                                        }
                                        
                                        # Merge metadata using the metadata manager
                                        merged_metadata = self.metadata_manager.merge_metadata(
                                            base_metadata,
                                            metadata or {},
                                            chunk_meta,
                                            base_chunk_metadata
                                        )
                                        
                                        storage_metadata = self.metadata_manager.prepare_for_storage(merged_metadata)
                                        chunk_metadata_list.append(storage_metadata)
                                    
                                    # Add to vector store (using the actual vector store - Qdrant or FAISS)
                                    vector_store = getattr(self, 'qdrant_store', None) or getattr(self, 'vector_store', None) or self.faiss_store
                                    vector_ids = vector_store.add_vectors(embeddings, chunk_metadata_list)
                                    
                                    # Get doc_id for response
                                    doc_id = chunk_metadata_list[0].get('doc_id', 'json_document') if chunk_metadata_list else 'json_document'
                                    
                                    logging.info(f"✅ Successfully processed JSON content with {processor.__class__.__name__} ({len(processor_chunks)} logical chunks)")
                                    
                                    return {
                                        'status': 'success',
                                        'doc_id': doc_id,
                                        'chunks_created': len(processor_chunks),
                                        'vectors_stored': len(vector_ids),
                                        'text_length': len(text),
                                        'processing_method': 'json_processor',
                                        'processor_used': processor.__class__.__name__
                                    }
                                else:
                                    logging.warning(f"⚠️ Processor failed or returned no chunks, falling back to text chunking")
                            else:
                                logging.info(f"🔄 No processor found for JSON file, using text chunking")
                        finally:
                            # Clean up temporary file
                            if os.path.exists(tmp_file_path):
                                os.unlink(tmp_file_path)
                    else:
                        logging.info(f"🔄 JSON content detected but not ServiceNow format, using text chunking")
                        
                except (json.JSONDecodeError, Exception) as e:
                    logging.info(f"🔄 JSON parsing failed or processor error: {e}, using text chunking")
            
            # ✅ FALLBACK: Continue with normal text processing
            # Prepare base metadata - preserve existing fields from metadata input
            base_metadata = {
                'source_type': metadata.get('source_type', 'text') if metadata else 'text',  # ✅ Preserve existing source_type
                'ingested_at': datetime.now().isoformat(),
                'processor': 'ingestion_engine_text',
                'text_length': len(text)
            }
            
            # Preserve all other metadata fields that were passed in
            if metadata:
                # Add all metadata fields, but don't override the ones we just set
                for key, value in metadata.items():
                    if key not in base_metadata:
                        base_metadata[key] = value
            
            # Chunk the text
            chunks = self.chunker.chunk_text(text, base_metadata)
            
            if not chunks:
                return {
                    'status': 'skipped',
                    'reason': 'no_chunks'
                }
            
            # Generate embeddings
            chunk_texts = [chunk['text'] for chunk in chunks]
            embeddings = self.embedder.embed_texts(chunk_texts)
            
            # Prepare chunk metadata using metadata manager
            chunk_metadata_list = []
            
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                try:
                    # Extract chunk metadata and ensure it's flat
                    chunk_meta = chunk.get('metadata', {})
                    
                    # If chunk metadata has nested 'metadata', extract it
                    if isinstance(chunk_meta.get('metadata'), dict):
                        nested_meta = chunk_meta.pop('metadata')
                        # Merge nested metadata into chunk_meta
                        for k, v in nested_meta.items():
                            if k not in chunk_meta:
                                chunk_meta[k] = v
                    
                    # Create base metadata for this chunk
                    base_chunk_metadata = {
                        'text': chunk['text'],
                        'content': chunk['text'],  # For compatibility
                        'chunk_index': i,
                        'total_chunks': len(chunks),
                        'chunk_size': len(chunk['text']),
                        'doc_id': metadata.get('doc_path', metadata.get('title', 'text_document')) if metadata else 'text_document',
                        'doc_path': metadata.get('doc_path', metadata.get('title', 'text_document')) if metadata else 'text_document',
                        'chunking_method': getattr(self.chunker.__class__, '__name__', 'unknown'),
                        'embedding_model': getattr(self.embedder, 'model_name', 'unknown')
                    }
                    
                    # Merge metadata using the metadata manager
                    merged_metadata = self.metadata_manager.merge_metadata(
                        base_metadata,           # Base metadata (now preserves input metadata)
                        metadata or {},          # Custom metadata from user
                        chunk_meta,              # Chunk-specific metadata (now flat)
                        base_chunk_metadata      # Final chunk data
                    )
                    
                    # Prepare for storage
                    storage_metadata = self.metadata_manager.prepare_for_storage(merged_metadata)
                    chunk_metadata_list.append(storage_metadata)
                    
                except Exception as e:
                    logging.error(f"Failed to merge metadata for text chunk {i}: {e}")
                    # Fallback to simple metadata
                    fallback_meta = {
                        'text': chunk['text'],
                        'chunk_index': i,
                        'doc_id': metadata.get('doc_path', metadata.get('title', 'text_document')) if metadata else 'text_document',
                        'doc_path': metadata.get('doc_path', metadata.get('title', 'text_document')) if metadata else 'text_document',
                        'source_type': metadata.get('source_type', 'text') if metadata else 'text'  # ✅ Preserve source_type in fallback too
                    }
                    chunk_metadata_list.append(fallback_meta)
            
            # Add to FAISS store
            vector_ids = self.faiss_store.add_vectors(embeddings, chunk_metadata_list)
            
            # Get doc_id for response
            doc_id = chunk_metadata_list[0].get('doc_id', 'text_document') if chunk_metadata_list else 'text_document'
            
            logging.info(f"Successfully ingested text content ({len(chunks)} chunks)")
            
            return {
                'status': 'success',
                'doc_id': doc_id,
                'chunks_created': len(chunks),
                'vectors_stored': len(vector_ids),
                'text_length': len(text)
            }
            
        except Exception as e:
            logging.error(f"Failed to ingest text: {e}")
            raise IngestionError(f"Failed to ingest text: {e}")
    
    def _handle_existing_file(self, file_path: str) -> int:
        """Handle existing file by deleting old vectors"""
        try:
            # Get identifying information from current metadata
            doc_path = getattr(self, '_current_metadata', {}).get('doc_path') if hasattr(self, '_current_metadata') else None
            filename = getattr(self, '_current_metadata', {}).get('filename') if hasattr(self, '_current_metadata') else None
            
            if not doc_path:
                # Try to extract from file_path
                doc_path = self._current_metadata.get('doc_path') if hasattr(self, '_current_metadata') and self._current_metadata else None
            
            # Find vectors to delete based on content hash
            vectors_to_delete = []
            
            # Get the doc_hash of the incoming file
            incoming_doc_hash = self._calculate_document_hash(Path(file_path))

            for vector_id, metadata in self.faiss_store.id_to_metadata.items():
                if metadata.get('deleted', False):
                    continue
                
                # Check for match based on doc_hash
                if metadata.get('doc_hash') == incoming_doc_hash:
                    vectors_to_delete.append(vector_id)
            
            if vectors_to_delete:
                self.faiss_store.delete_vectors(vectors_to_delete)
                return len(vectors_to_delete)
                
            return 0
            
        except Exception as e:
            logging.warning(f"Error handling existing file {file_path}: {e}")
            return 0
    
    def ingest_directory(self, directory_path: str, file_patterns: List[str] = None, batch_id: Optional[str] = None) -> Dict[str, Any]:
        """Ingest all files in a directory with batch progress tracking"""
        directory = Path(directory_path)
        if not directory.exists():
            raise IngestionError(f"Directory not found: {directory_path}")
        if file_patterns is None:
            file_patterns = self.config.ingestion.supported_formats
        files_to_ingest = []
        for pattern in file_patterns:
            files_to_ingest.extend(directory.rglob(f"*{pattern}"))
        if batch_id:
            self.progress_tracker.create_batch(batch_id, [str(f) for f in files_to_ingest])
        results = {
            'batch_id': batch_id,
            'total_files': len(files_to_ingest),
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'results': []
        }
        for file_path in files_to_ingest:
            try:
                result = self.ingest_file(str(file_path))
                results['results'].append(result)
                if result['status'] == 'success':
                    results['successful'] += 1
                elif result['status'] == 'skipped':
                    results['skipped'] += 1
            except Exception as e:
                results['failed'] += 1
                results['results'].append({
                    'status': 'failed',
                    'file_path': str(file_path),
                    'error': str(e)
                })
                logging.error(f"Failed to ingest {file_path}: {e}")
        logging.info(f"Directory ingestion completed: {results['successful']} successful, "
                    f"{results['failed']} failed, {results['skipped']} skipped")
        return results
    
    def _extract_text(self, file_path: Path) -> str:
        """Extract text content from various file types"""
        file_extension = file_path.suffix.lower()
        
        # ADD LOGGING: Start of text extraction
        logging.info(f"🔍 Using processor: {self.processor_registry.get_processor(str(file_path)).__class__.__name__ if self.processor_registry.get_processor(str(file_path)) else 'No specialized processor'} for {file_path}")
        
        # Reset processor flags
        self._processor_chunks = None
        self._use_processor_chunks = False
        
        # Check if we have a specialized processor
        processor = self.processor_registry.get_processor(str(file_path))
        if processor:
            try:
                # ADD LOGGING: Before processing
                processor_start = datetime.now()
                logging.info(f"🔍 Using processor: {processor.__class__.__name__} for {file_path}")
                
                result = processor.process(str(file_path), getattr(self, '_current_metadata', {}))
                
                # ADD LOGGING: After processing
                processor_time = (datetime.now() - processor_start).total_seconds()
                
                if result.get('status') == 'success' and result.get('chunks'):
                    logging.info(f"✅ Processor succeeded, chunks: {len(result.get('chunks', []))}")
                    logging.info(f"   Processing time: {processor_time:.2f}s")
                    
                    # ADD DETAILED LOGGING: Log chunk preview
                    if result.get('chunks') and logging.getLogger().isEnabledFor(logging.DEBUG):
                        for i, chunk in enumerate(result['chunks'][:3]):  # First 3 chunks
                            logging.debug(f"Chunk {i} preview: {chunk['text'][:200]}...")
                            chunk_metadata = chunk.get('metadata', {})
                            logging.debug(f"Chunk {i} metadata keys: {list(chunk_metadata.keys())}")
                            
                            # Log specific important metadata
                            important_keys = ['source_type', 'content_type', 'page_number', 'extraction_method', 'processor']
                            for key in important_keys:
                                if key in chunk_metadata:
                                    logging.debug(f"  {key}: {chunk_metadata[key]}")
                    
                    # ADD LOGGING: Save processor result for debugging
                    if os.getenv('RAG_SAVE_EXTRACTION_DUMPS', 'false').lower() == 'true' or logging.getLogger().isEnabledFor(logging.DEBUG):
                        debug_file = f"debug_processor_result_{file_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                        debug_path = Path("data/logs") / debug_file
                        debug_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        try:
                            # Create a serializable version with full content
                            debug_result = {k: v for k, v in result.items() if k not in ['chunks']}
                            debug_result['chunk_count'] = len(result.get('chunks', []))
                            debug_result['processing_time_seconds'] = processor_time
                            debug_result['processor_name'] = processor.__class__.__name__
                            
                            # Include extracted text if available
                            if 'text' in result:
                                debug_result['extracted_text'] = result['text']
                                debug_result['extracted_text_length'] = len(result['text'])
                                debug_result['extracted_text_preview'] = result['text'][:500] + "..." if len(result['text']) > 500 else result['text']
                            
                            # Include chunk details
                            chunks = result.get('chunks', [])
                            debug_result['chunks_detail'] = []
                            for i, chunk in enumerate(chunks[:5]):  # Limit to first 5 chunks for space
                                chunk_info = {
                                    'chunk_index': i,
                                    'content_length': len(chunk.get('content', '')),
                                    'content_preview': chunk.get('content', '')[:200] + "..." if len(chunk.get('content', '')) > 200 else chunk.get('content', ''),
                                    'metadata': chunk.get('metadata', {})
                                }
                                debug_result['chunks_detail'].append(chunk_info)
                            
                            if len(chunks) > 5:
                                debug_result['chunks_detail'].append({'note': f'... and {len(chunks) - 5} more chunks'})
                            
                            import json
                            with open(debug_path, 'w', encoding='utf-8') as f:
                                json.dump(debug_result, f, indent=2, ensure_ascii=False, default=str)
                            logging.debug(f"Processor result with content saved to {debug_path}")
                        except Exception as save_error:
                            logging.warning(f"Failed to save processor debug data: {save_error}")
                    
                    # Store processor chunks to use directly
                    self._processor_chunks = result['chunks']
                    self._use_processor_chunks = True
                    
                    # Update metadata
                    if hasattr(self, '_current_metadata') and self._current_metadata:
                        self._current_metadata.update({
                            'processor_used': processor.__class__.__name__,
                            'processor_chunk_count': len(result['chunks']),
                            'processor_processing_time': processor_time,
                            **{k: v for k, v in result.items() if k not in ['chunks', 'status', 'text']}
                        })
                    
                    # Return dummy text to satisfy the flow
                    return "[Processed by specialized processor]"
                else:
                    # ADD LOGGING: Processor failed or no chunks
                    if result.get('status') == 'success':
                        logging.warning(f"⚠️ Processor {processor.__class__.__name__} succeeded but returned no chunks")
                    else:
                        logging.warning(f"⚠️ Processor {processor.__class__.__name__} failed: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                processor_time = (datetime.now() - processor_start).total_seconds() if 'processor_start' in locals() else 0
                logging.error(f"❌ Processor {processor.__class__.__name__} failed for {file_path} (after {processor_time:.2f}s): {e}")
                import traceback
                logging.debug(f"Full traceback: {traceback.format_exc()}")
        
        # Default extraction methods
        try:
            # ADD LOGGING: Fallback to default extraction
            logging.info(f"🔄 Using default extraction for {file_extension} file: {file_path}")
            extraction_start = datetime.now()
            
            if file_extension == '.txt':
                text = self._extract_text_file(file_path)
            elif file_extension == '.pdf':
                text = self._extract_pdf_file(file_path)
            elif file_extension in ['.docx', '.doc']:
                text = self._extract_docx_file(file_path)
            elif file_extension == '.md':
                text = self._extract_markdown_file(file_path)
            elif file_extension in ['.xlsx', '.xls', '.xlsm']:
                text = self._extract_excel_basic(file_path)
            else:
                text = self._extract_text_file(file_path)
            
            # ADD LOGGING: Default extraction success
            extraction_time = (datetime.now() - extraction_start).total_seconds()
            logging.info(f"✅ Default extraction completed in {extraction_time:.2f}s")
            logging.info(f"   Extracted text length: {len(text):,} chars")
            logging.debug(f"   Text preview: {text[:200]}..." if len(text) > 200 else f"   Text: {text}")
            
            # ADD LOGGING: Save default extraction result for debugging
            if os.getenv('RAG_SAVE_EXTRACTION_DUMPS', 'false').lower() == 'true' or logging.getLogger().isEnabledFor(logging.DEBUG):
                debug_file = f"debug_default_extraction_{file_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                debug_path = Path("data/logs") / debug_file
                debug_path.parent.mkdir(parents=True, exist_ok=True)
                
                try:
                    debug_result = {
                        'extraction_method': 'default',
                        'file_path': str(file_path),
                        'file_extension': file_extension,
                        'processing_time_seconds': extraction_time,
                        'extracted_text': text,
                        'extracted_text_length': len(text),
                        'extracted_text_preview': text[:500] + "..." if len(text) > 500 else text,
                        'timestamp': datetime.now().isoformat(),
                        'status': 'success'
                    }
                    
                    import json
                    with open(debug_path, 'w', encoding='utf-8') as f:
                        json.dump(debug_result, f, indent=2, ensure_ascii=False, default=str)
                    logging.debug(f"Default extraction result with content saved to {debug_path}")
                except Exception as save_error:
                    logging.warning(f"Failed to save default extraction debug data: {save_error}")
            
            return text
            
        except Exception as e:
            extraction_time = (datetime.now() - extraction_start).total_seconds() if 'extraction_start' in locals() else 0
            error_msg = f"Failed to extract text from {file_path} (after {extraction_time:.2f}s): {e}"
            logging.error(f"❌ {error_msg}")
            raise FileProcessingError(error_msg)
    
    def _extract_text_file(self, file_path: Path) -> str:
        """Extract text from plain text file"""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    
    def _extract_pdf_file(self, file_path: Path) -> str:
        """Extract text from PDF file"""
        try:
            import PyPDF2
            text = ""
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except ImportError:
            raise FileProcessingError("PyPDF2 not installed. Cannot process PDF files.")
    
    def _extract_docx_file(self, file_path: Path) -> str:
        """Extract text from DOCX file"""
        try:
            import docx
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except ImportError:
            raise FileProcessingError("python-docx not installed. Cannot process DOCX files.")
    
    def _extract_markdown_file(self, file_path: Path) -> str:
        """Extract text from Markdown file"""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Simple markdown processing - remove formatting
        import re
        content = re.sub(r'^#+\s*', '', content, flags=re.MULTILINE)  # Remove headers
        content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)  # Remove bold
        content = re.sub(r'\*(.*?)\*', r'\1', content)  # Remove italic
        content = re.sub(r'`(.*?)`', r'\1', content)  # Remove code
        content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', content)  # Remove links
        
        return content
    
    def _extract_excel_basic(self, file_path: Path) -> str:
        """Basic Excel text extraction without Azure AI"""
        try:
            import pandas as pd
            excel_file = pd.ExcelFile(file_path)
            all_text = []
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                all_text.append(f"Sheet: {sheet_name}")
                all_text.append(df.to_string())
                all_text.append("\n")
            return "\n".join(all_text)
        except ImportError:
            raise FileProcessingError("pandas not installed. Cannot process Excel files without processor.")
        except Exception as e:
            raise FileProcessingError(f"Failed to extract Excel content: {e}")
    
    def delete_file(self, file_path: str, doc_path: str = None) -> Dict[str, Any]:
        """Delete all vectors associated with a file"""
        try:
            logging.info(f"Deleting vectors for file: {file_path}")
            
            # Find all vectors associated with this file
            vectors_to_delete = []
            
            # Get all vector metadata and find matches
            for vector_id, metadata in self.faiss_store.id_to_metadata.items():
                if metadata.get('deleted', False):
                    continue
                
                # Check multiple possible matching criteria
                is_match = False
                match_reason = ""
                
                # Priority 1: doc_path match (most reliable)
                if doc_path and metadata.get('doc_path') == doc_path:
                    is_match = True
                    match_reason = f"doc_path match: {metadata.get('doc_path')}"
                
                # Priority 2: Check nested metadata for doc_path
                elif doc_path and isinstance(metadata.get('metadata'), dict):
                    nested_doc_path = metadata['metadata'].get('doc_path')
                    if nested_doc_path == doc_path:
                        is_match = True
                        match_reason = f"nested doc_path match: {nested_doc_path}"
                
                # Priority 3: Direct file_path match
                elif metadata.get('file_path') == file_path:
                    is_match = True
                    match_reason = f"file_path match: {metadata.get('file_path')}"
                
                # Priority 4: Check nested metadata for original_path
                elif isinstance(metadata.get('metadata'), dict):
                    nested_original_path = metadata['metadata'].get('original_path')
                    if nested_original_path == file_path:
                        is_match = True
                        match_reason = f"nested original_path match: {nested_original_path}"
                
                if is_match:
                    vectors_to_delete.append(vector_id)
                    logging.info(f"Found vector to delete {vector_id}: {match_reason}")
            
            if vectors_to_delete:
                # Delete the vectors
                self.faiss_store.delete_vectors(vectors_to_delete)
                logging.info(f"Successfully deleted {len(vectors_to_delete)} vectors for file: {file_path}")
                
                return {
                    'status': 'success',
                    'file_path': file_path,
                    'vectors_deleted': len(vectors_to_delete),
                    'message': f"Deleted {len(vectors_to_delete)} vectors"
                }
            else:
                logging.info(f"No vectors found for file: {file_path}")
                return {
                    'status': 'success',
                    'file_path': file_path,
                    'vectors_deleted': 0,
                    'message': "No vectors found to delete"
                }
                
        except Exception as e:
            logging.error(f"Error deleting file {file_path}: {e}")
            return {
                'status': 'failed',
                'file_path': file_path,
                'error': str(e)
            }
    
    def get_ingestion_stats(self) -> Dict[str, Any]:
        """Get ingestion statistics"""
        # Get stats from metadata store
        collections = self.metadata_store.list_collections()
        
        stats = {
            'total_files': 0,
            'total_chunks': 0,
            'total_vectors': 0,
            'collections': len(collections)
        }
        
        # Get file count
        if 'files_metadata' in collections:
            file_stats = self.metadata_store.collection_stats('files_metadata')
            stats['total_files'] = file_stats.get('count', 0)
        
        # Get FAISS stats
        faiss_info = self.faiss_store.get_index_info()
        stats['total_vectors'] = faiss_info.get('ntotal', 0)
        stats['active_vectors'] = faiss_info.get('active_vectors', 0)
        
        return stats
    
    def _validate_chunk_structure(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate and fix chunk structure before processing"""
        validated_chunks = []
        
        for i, chunk in enumerate(chunks):
            if not isinstance(chunk, dict):
                logging.error(f"Invalid chunk type at index {i}: {type(chunk)}")
                continue
            
            # Ensure required fields
            if 'text' not in chunk:
                logging.error(f"Chunk {i} missing 'text' field")
                continue
            
            # Ensure metadata is not double-nested
            metadata = chunk.get('metadata', {})
            if isinstance(metadata.get('metadata'), dict):
                logging.warning(f"Found double-nested metadata in chunk {i}, flattening")
                nested = metadata.pop('metadata')
                metadata.update(nested)
            
            validated_chunk = {
                'text': chunk['text'],
                'chunk_index': chunk.get('chunk_index', i),
                'metadata': metadata
            }
            
            validated_chunks.append(validated_chunk)
        
        return validated_chunks

    def ingest_file_stream(self, file_path: str, chunk_callback=None):
        """Process large files in streaming fashion"""
        with open(file_path, 'r', encoding='utf-8') as f:
            buffer = ""
            while True:
                chunk = f.read(1024 * 1024)  # 1MB chunks
                if not chunk:
                    break
                buffer += chunk
                sentences, buffer = self._extract_complete_sentences(buffer)
                if sentences and chunk_callback:
                    chunk_callback(sentences)
            # Process any remaining sentences in the buffer
            if buffer.strip() and chunk_callback:
                chunk_callback([buffer.strip()])

    def _extract_complete_sentences(self, buffer: str):
        """Extract complete sentences from buffer, leaving incomplete at the end"""
        import re
        # This regex splits on sentence-ending punctuation followed by whitespace or end of string
        sentence_endings = re.compile(r'([.!?][\"\']?)(?=\s|$)')
        sentences = []
        last_end = 0
        for match in sentence_endings.finditer(buffer):
            end = match.end()
            sentences.append(buffer[last_end:end].strip())
            last_end = end
        remainder = buffer[last_end:]
        return [s for s in sentences if s], remainder