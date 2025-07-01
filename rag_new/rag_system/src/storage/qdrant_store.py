"""
Qdrant Vector Store Implementation
Replaces FAISS with Qdrant for better filtering and metadata handling
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import uuid
from pathlib import Path
import json
import re

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, 
    Filter, FieldCondition, Range, MatchValue,
    SearchRequest, ScrollRequest, UpdateStatus,
    HasIdCondition, MatchAny, MatchText
)
import numpy as np

try:
    from ..core.error_handling import (
        StorageError, ErrorCode, ErrorInfo, ErrorContext, 
        Result, with_error_handling
    )
except ImportError:
    try:
        from rag_system.src.core.error_handling import (
            StorageError, ErrorCode, ErrorInfo, ErrorContext, 
            Result, with_error_handling
        )
    except ImportError:
        # Fallback for when running as script
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent / 'core'))
        from error_handling import (
            StorageError, ErrorCode, ErrorInfo, ErrorContext, 
            Result, with_error_handling
        )

class QdrantVectorStore:
    """Qdrant-based vector store with advanced filtering and metadata support"""
    
    def __init__(self, 
                 url: str = "localhost:6333",
                 collection_name: str = "rag_documents",
                 dimension: int = 1024,
                 on_disk: bool = True):
        """
        Initialize Qdrant vector store
        
        Args:
            url: Qdrant server URL
            collection_name: Name of the collection
            dimension: Vector dimension
            on_disk: Store vectors on disk (for large datasets)
        """
        self.client = QdrantClient(url=url)
        self.collection_name = collection_name
        self.dimension = dimension
        
        # Create or verify collection
        self._init_collection(on_disk)
        
        logging.info(f"Qdrant store initialized: {url}/{collection_name}")
    
    def _init_collection(self, on_disk: bool):
        """Initialize Qdrant collection"""
        collections = self.client.get_collections().collections
        
        if not any(col.name == self.collection_name for col in collections):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.dimension,
                    distance=Distance.COSINE,
                    on_disk=on_disk
                )
            )
            logging.info(f"Created collection: {self.collection_name}")
        else:
            logging.info(f"Using existing collection: {self.collection_name}")
    
    def add_vectors(self, vectors: List[List[float]], metadata: List[Dict[str, Any]]) -> List[str]:
        """Add vectors with metadata to Qdrant"""
        if len(vectors) != len(metadata):
            raise ValueError("Vectors and metadata count mismatch")
        
        points = []
        vector_ids = []
        
        for vector, meta in zip(vectors, metadata):
            # Generate ID
            vector_id = str(uuid.uuid4())
            vector_ids.append(vector_id)
            
            # Prepare payload with enhanced metadata
            payload = {
                **meta,
                'vector_id': vector_id,
                'added_at': datetime.now().isoformat(),
                # Extract specific fields for filtering
                'doc_type': self._extract_doc_type(meta),
                'has_incident': self._contains_incident(meta.get('text', '')),
                'incident_ids': self._extract_incident_ids(meta.get('text', '')),
                'source_file': meta.get('filename', meta.get('file_path', 'unknown'))
            }
            
            points.append(PointStruct(
                id=vector_id,
                vector=vector,
                payload=payload
            ))
        
        # Batch upload
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        
        logging.info(f"Added {len(vectors)} vectors to Qdrant")
        return vector_ids
    
    def search(self, query_vector: List[float], k: int = 5, 
               filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search with optional filters"""
        
        # Build Qdrant filter
        qdrant_filter = self._build_filter(filters) if filters else None
        
        # Search
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=k,
            query_filter=qdrant_filter,
            with_payload=True,
            with_vectors=False
        )
        
        # Format results
        formatted_results = []
        for result in results:
            formatted_result = {
                **result.payload,
                'similarity_score': result.score,
                'vector_id': result.id
            }
            formatted_results.append(formatted_result)
        
        return formatted_results
    
    def search_with_metadata(self, query_vector: List[float], k: int = 5) -> List[Dict[str, Any]]:
        """Search with enhanced metadata format for query engine compatibility"""
        results = self.search(query_vector, k)
        
        # Format for query engine compatibility
        formatted_results = []
        for result in results:
            formatted_result = {
                'similarity_score': result.get('similarity_score', 0.0),
                'score': result.get('similarity_score', 0.0),  # For compatibility
                'vector_id': str(result.get('vector_id', 'unknown')),
                'doc_id': result.get('doc_id', 'unknown'),
                'content': result.get('content', result.get('text', '')),
                'text': result.get('content', result.get('text', '')),  # For compatibility
                'filename': result.get('filename', result.get('file_path', 'unknown')),
                'chunk_id': result.get('chunk_id', f"chunk_{result.get('vector_id', 'unknown')}"),
                'chunk_index': result.get('chunk_index', 0),
                'page_number': result.get('page_number'),
                'metadata': result
            }
            formatted_results.append(formatted_result)
        
        return formatted_results
    
    def list_all_incidents(self) -> List[Dict[str, Any]]:
        """List all documents containing incidents - efficient implementation"""
        
        # Method 1: Filter by incident flag
        incident_filter = Filter(
            must=[
                FieldCondition(
                    key="has_incident",
                    match=MatchValue(value=True)
                )
            ]
        )
        
        # Use scroll to get ALL matching documents
        results = []
        offset = None
        
        while True:
            response = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=incident_filter,
                limit=100,  # Batch size
                offset=offset,
                with_payload=True,
                with_vectors=False
            )
            
            results.extend(response[0])
            offset = response[1]
            
            if offset is None:
                break
        
        # Extract and deduplicate incidents
        all_incidents = {}
        for result in results:
            incident_ids = result.payload.get('incident_ids', [])
            text = result.payload.get('text', '')
            source = result.payload.get('source_file', 'unknown')
            
            for inc_id in incident_ids:
                if inc_id not in all_incidents:
                    all_incidents[inc_id] = {
                        'id': inc_id,
                        'sources': [source],
                        'first_mention': text[:200],
                        'occurrence_count': 1
                    }
                else:
                    all_incidents[inc_id]['occurrence_count'] += 1
                    if source not in all_incidents[inc_id]['sources']:
                        all_incidents[inc_id]['sources'].append(source)
        
        return list(all_incidents.values())
    
    def get_by_pattern(self, pattern: str, field: str = "text") -> List[Dict[str, Any]]:
        """Get all documents matching a pattern in a specific field"""
        
        # Qdrant supports regex-like patterns in text search
        pattern_filter = Filter(
            must=[
                FieldCondition(
                    key=field,
                    match=MatchText(text=pattern)
                )
            ]
        )
        
        results = []
        offset = None
        
        while True:
            response = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=pattern_filter,
                limit=100,
                offset=offset,
                with_payload=True
            )
            
            results.extend(response[0])
            offset = response[1]
            
            if offset is None:
                break
        
        return [r.payload for r in results]
    
    def aggregate_by_type(self) -> Dict[str, int]:
        """Get counts by document type"""
        
        # Note: Qdrant doesn't have built-in aggregation like MongoDB
        # We'll use scroll with filters for each type
        
        doc_types = ['incident', 'change', 'problem', 'request', 'task']
        counts = {}
        
        for doc_type in doc_types:
            type_filter = Filter(
                must=[
                    FieldCondition(
                        key="doc_type",
                        match=MatchValue(value=doc_type)
                    )
                ]
            )
            
            # Count using scroll
            count = 0
            offset = None
            
            while True:
                response = self.client.scroll(
                    collection_name=self.collection_name,
                    scroll_filter=type_filter,
                    limit=100,
                    offset=offset,
                    with_payload=False,
                    with_vectors=False
                )
                
                count += len(response[0])
                offset = response[1]
                
                if offset is None:
                    break
            
            counts[doc_type] = count
        
        return counts
    
    def hybrid_search(self, 
                     query_vector: Optional[List[float]] = None,
                     filters: Dict[str, Any] = None,
                     text_query: Optional[str] = None,
                     k: int = 10) -> List[Dict[str, Any]]:
        """
        Hybrid search combining vector similarity and filters
        Perfect for queries like "list all incidents about database"
        """
        
        # Build filter
        qdrant_filter = self._build_filter(filters) if filters else Filter()
        
        # Add text search to filter if provided
        if text_query:
            text_conditions = []
            for word in text_query.split():
                text_conditions.append(
                    FieldCondition(
                        key="text",
                        match=MatchText(text=word)
                    )
                )
            
            if text_conditions:
                if qdrant_filter.must:
                    qdrant_filter.must.extend(text_conditions)
                else:
                    qdrant_filter.must = text_conditions
        
        # If we have a query vector, do similarity search with filters
        if query_vector:
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=k,
                query_filter=qdrant_filter,
                with_payload=True
            )
            
            return [{'score': r.score, **r.payload} for r in results]
        
        # Otherwise, just filter
        else:
            results = []
            offset = None
            
            while len(results) < k:
                response = self.client.scroll(
                    collection_name=self.collection_name,
                    scroll_filter=qdrant_filter,
                    limit=min(k - len(results), 100),
                    offset=offset,
                    with_payload=True
                )
                
                results.extend(response[0])
                offset = response[1]
                
                if offset is None:
                    break
            
            return [r.payload for r in results[:k]]
    
    def _extract_doc_type(self, metadata: Dict[str, Any]) -> str:
        """Extract document type from metadata"""
        text = metadata.get('text', '').upper()
        
        if 'INC' in text:
            return 'incident'
        elif 'CHG' in text:
            return 'change'
        elif 'PRB' in text:
            return 'problem'
        elif 'REQ' in text:
            return 'request'
        elif 'TASK' in text:
            return 'task'
        else:
            return 'other'
    
    def _contains_incident(self, text: str) -> bool:
        """Check if text contains incident reference"""
        return bool(re.search(r'INC\d{6}', text, re.IGNORECASE))
    
    def _extract_incident_ids(self, text: str) -> List[str]:
        """Extract all incident IDs from text"""
        return re.findall(r'INC\d{6}', text, re.IGNORECASE)
    
    def _build_filter(self, filters: Dict[str, Any]) -> Filter:
        """Build Qdrant filter from dictionary"""
        conditions = []
        
        for key, value in filters.items():
            if isinstance(value, list):
                # Match any of the values
                conditions.append(
                    FieldCondition(
                        key=key,
                        match=MatchAny(any=value)
                    )
                )
            elif isinstance(value, dict):
                # Range query
                if 'gte' in value or 'lte' in value:
                    conditions.append(
                        FieldCondition(
                            key=key,
                            range=Range(
                                gte=value.get('gte'),
                                lte=value.get('lte')
                            )
                        )
                    )
            else:
                # Exact match
                conditions.append(
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value)
                    )
                )
        
        return Filter(must=conditions) if conditions else None
    
    def delete_by_filter(self, filters: Dict[str, Any]) -> int:
        """Delete vectors matching filters"""
        qdrant_filter = self._build_filter(filters)
        
        result = self.client.delete(
            collection_name=self.collection_name,
            points_selector=qdrant_filter
        )
        
        return result.status == UpdateStatus.COMPLETED
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get collection statistics"""
        info = self.client.get_collection(self.collection_name)
        
        return {
            'vectors_count': info.vectors_count,
            'indexed_vectors_count': info.indexed_vectors_count,
            'points_count': info.points_count,
            'segments_count': info.segments_count,
            'status': info.status,
            'config': {
                'dimension': info.config.params.vectors.size,
                'distance': info.config.params.vectors.distance,
                'on_disk': info.config.params.vectors.on_disk
            }
        }
    
    # Compatibility methods to match FAISS interface
    def search_with_metadata(self, query_vector: List[float], k: int = 5, 
                           filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search with metadata - compatibility method"""
        return self.search(query_vector, k, filters)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics - compatibility method"""
        info = self.get_collection_info()
        return {
            'vector_count': info['vectors_count'],
            'dimension': info['config']['dimension'],
            'status': 'ready' if info['status'] == 'green' else 'not_ready',
            'indexed_vectors': info['indexed_vectors_count'],
            'total_size_mb': info['points_count'] * info['config']['dimension'] * 4 / (1024 * 1024)  # Estimate
        }
    
    def delete_vectors(self, vector_ids: List[str]) -> bool:
        """Delete vectors by IDs - compatibility method"""
        try:
            from qdrant_client.models import PointIdsList
            
            result = self.client.delete(
                collection_name=self.collection_name,
                points_selector=PointIdsList(points=vector_ids)
            )
            
            return result.status == UpdateStatus.COMPLETED
            
        except Exception as e:
            logging.error(f"Failed to delete vectors: {e}")
            return False
    
    def get_vector_by_id(self, vector_id: str) -> Optional[Dict[str, Any]]:
        """Get vector and metadata by ID - compatibility method"""
        try:
            results = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[vector_id],
                with_payload=True,
                with_vectors=True
            )
            
            if results:
                result = results[0]
                return {
                    'id': result.id,
                    'vector': result.vector,
                    'metadata': result.payload
                }
            
            return None
            
        except Exception as e:
            logging.error(f"Failed to get vector by ID: {e}")
            return None
    
    def update_metadata(self, vector_id: str, metadata: Dict[str, Any]) -> bool:
        """Update metadata for a vector - compatibility method"""
        try:
            # Get current vector
            current = self.get_vector_by_id(vector_id)
            if not current:
                return False
            
            # Update with new metadata
            updated_payload = {**current['metadata'], **metadata}
            
            # Update in Qdrant
            self.client.set_payload(
                collection_name=self.collection_name,
                payload=updated_payload,
                points=[vector_id]
            )
            
            return True
            
        except Exception as e:
            logging.error(f"Failed to update metadata: {e}")
            return False
    
    def find_vectors_by_doc_path(self, doc_path: str) -> List[str]:
        """Find vector IDs by document path"""
        doc_filter = Filter(
            must=[
                FieldCondition(
                    key="source_file",
                    match=MatchValue(value=doc_path)
                )
            ]
        )
        
        results = []
        offset = None
        
        while True:
            response = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=doc_filter,
                limit=100,
                offset=offset,
                with_payload=True
            )
            
            results.extend([r.id for r in response[0]])
            offset = response[1]
            
            if offset is None:
                break
        
        return results
    
    def delete_vectors_by_doc_path(self, doc_path: str) -> int:
        """Delete all vectors associated with a document path"""
        vector_ids = self.find_vectors_by_doc_path(doc_path)
        if vector_ids:
            self.delete_vectors(vector_ids)
        return len(vector_ids)
    
    def clear_index(self):
        """Clear all vectors from the collection"""
        self.client.delete_collection(self.collection_name)
        self._init_collection(on_disk=True)
        logging.info("Cleared Qdrant collection")
    
    def backup_index(self, backup_path: str):
        """Backup the Qdrant collection (placeholder)"""
        # Qdrant has built-in backup mechanisms, this is a placeholder
        logging.info(f"Qdrant backup would be saved to {backup_path}")
        # In production, you would use Qdrant's snapshot functionality
    
    def restore_index(self, backup_path: str):
        """Restore the Qdrant collection (placeholder)"""
        # Qdrant has built-in restore mechanisms, this is a placeholder
        logging.info(f"Qdrant would be restored from {backup_path}")
        # In production, you would use Qdrant's snapshot functionality
    
    @property
    def id_to_metadata(self) -> Dict[str, Any]:
        """
        Compatibility property that returns all metadata mapped by vector ID.
        This is a heavy operation - use with caution for large collections.
        """
        try:
            # Get all points using scroll
            all_metadata = {}
            offset = None
            
            while True:
                response = self.client.scroll(
                    collection_name=self.collection_name,
                    limit=1000,  # Process in batches
                    offset=offset,
                    with_payload=True,
                    with_vectors=False  # Don't need vectors for metadata
                )
                
                # Add to mapping
                for point in response[0]:
                    all_metadata[str(point.id)] = point.payload
                
                offset = response[1]
                if offset is None:
                    break
            
            return all_metadata
            
        except Exception as e:
            logging.error(f"Failed to retrieve id_to_metadata mapping: {e}")
            return {}
    
    def get_all_metadata(self) -> Dict[str, Any]:
        """Get all metadata - alias for id_to_metadata property"""
        return self.id_to_metadata
    
    def get_metadata_by_id(self, vector_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific vector ID"""
        try:
            results = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[vector_id],
                with_payload=True,
                with_vectors=False
            )
            
            if results:
                return results[0].payload
            return None
            
        except Exception as e:
            logging.error(f"Failed to get metadata for {vector_id}: {e}")
            return None
    
    def get_vector_metadata(self, vector_id) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific vector - FAISS compatibility method"""
        # Convert vector_id to string if it's an int (for FAISS compatibility)
        if isinstance(vector_id, int):
            vector_id = str(vector_id)
        return self.get_metadata_by_id(vector_id)
    
    def mark_deleted(self, vector_id: str) -> bool:
        """Mark a vector as deleted (FAISS compatibility)"""
        try:
            current_metadata = self.get_metadata_by_id(vector_id)
            if current_metadata:
                updated_metadata = {
                    **current_metadata,
                    'deleted': True,
                    'deleted_at': datetime.now().isoformat()
                }
                return self.update_metadata(vector_id, updated_metadata)
            return False
            
        except Exception as e:
            logging.error(f"Failed to mark vector {vector_id} as deleted: {e}")
            return False 