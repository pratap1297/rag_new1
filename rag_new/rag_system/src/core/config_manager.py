"""
Configuration Management for RAG System
Handles loading, validation, and management of system configuration
"""
import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Any, Optional, List

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    # Additionally attempt to load a `.env` file that resides next to the
    # rag_system package (useful when the application is launched from the
    # project root but the .env is stored inside rag_system/).
    try:
        _package_env = Path(__file__).resolve().parent.parent / ".env"
        load_dotenv(_package_env, override=False)
    except Exception:
        # It's fine if the extra .env is missing
        pass
except ImportError:
    pass

@dataclass
class VectorStoreConfig:
    """Vector store configuration (supports both FAISS and Qdrant)"""
    type: str = "qdrant"  # "faiss" or "qdrant"
    # Common settings
    dimension: int = 1024
    backup_enabled: bool = True
    backup_interval: int = 3600
    
    # FAISS-specific settings
    faiss_index_path: str = "data/vectors/faiss_index.bin"
    index_type: str = "flat"
    nprobe: int = 10
    enable_gpu: bool = False
    
    # Qdrant-specific settings
    url: str = "localhost:6333"
    collection_name: str = "rag_documents"
    on_disk_storage: bool = True
    distance: str = "cosine"

@dataclass
class DatabaseConfig:
    """Database configuration (legacy - for backward compatibility)"""
    faiss_index_path: str = "data/vectors/index.faiss"
    metadata_path: str = "data/metadata"
    backup_path: str = "data/backups"
    max_backup_count: int = 5
    # Additional fields from config file
    backup_enabled: bool = True
    backup_interval: int = 3600
    index_type: str = "flat"
    nprobe: int = 10
    enable_gpu: bool = False

@dataclass
class EmbeddingConfig:
    """Embedding model configuration"""
    provider: str = "azure"  # sentence-transformers, cohere, azure
    model_name: str = "Cohere-embed-v3-english"
    dimension: int = 1024  # Cohere v3 dimension
    batch_size: int = 96
    device: str = "cpu"
    api_key: Optional[str] = None

@dataclass
class LLMConfig:
    """LLM configuration"""
    provider: str = "azure"  # groq, openai, cohere, azure
    model_name: str = "Llama-4-Maverick-17B-128E-Instruct-FP8"
    api_key: Optional[str] = None
    temperature: float = 0.1
    max_tokens: int = 1000

@dataclass
class APIConfig:
    """API server configuration"""
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    reload: bool = False
    cors_origins: list = None
    health_check_timeout: float = 10.0  # 10 seconds for health checks
    stats_timeout: float = 10.0  # 10 seconds for stats operations
    llm_test_timeout: float = 15.0  # 15 seconds for LLM test operations

@dataclass
class IngestionConfig:
    """Data ingestion configuration"""
    chunk_size: int = 1000
    chunk_overlap: int = 200
    supported_formats: list = None
    max_file_size_mb: int = 100
    batch_size: int = 10
    timeout: float = 300.0  # 5 minutes default for text ingestion
    file_timeout: float = 600.0  # 10 minutes default for file processing

@dataclass
class RetrievalConfig:
    """Retrieval configuration"""
    top_k: int = 5
    similarity_threshold: float = 0.7  # Good default for normalized cosine similarity (range -1 to 1)
    rerank_top_k: int = 3
    enable_reranking: bool = True

@dataclass
class MonitoringConfig:
    """Monitoring configuration"""
    enable_metrics: bool = True
    metrics_port: int = 9090
    log_level: str = "INFO"
    log_format: str = "json"

@dataclass
class FolderMonitoringConfig:
    """Folder monitoring configuration"""
    enabled: bool = True
    check_interval_seconds: int = 60
    monitored_folders: list = None
    supported_extensions: list = None
    max_file_size_mb: int = 100
    auto_ingest: bool = True
    recursive: bool = True
    
    def __post_init__(self):
        if self.monitored_folders is None:
            self.monitored_folders = []
        if self.supported_extensions is None:
            self.supported_extensions = [".txt", ".md", ".pdf", ".docx", ".doc", ".json", ".csv", ".xlsx", ".xls", ".xlsm", ".xlsb", ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif", ".webp", ".svg"]

@dataclass
class AzureAIConfig:
    """Azure AI services configuration"""
    computer_vision_endpoint: str = ""
    computer_vision_key: str = ""
    document_intelligence_endpoint: str = ""  # Optional
    document_intelligence_key: str = ""  # Optional
    max_image_size_mb: int = 4
    ocr_language: str = "en"
    enable_handwriting: bool = True
    enable_document_intelligence: bool = False  # Optional feature

@dataclass
class ConversationConfig:
    """Conversation and query analysis configuration"""
    # LLM-enhanced query analysis
    enable_llm_query_analysis: bool = True
    max_decomposed_queries: int = 10
    synonym_expansion_enabled: bool = True
    
    # Query decomposition settings
    enable_query_decomposition: bool = True
    decomposition_threshold: float = 0.7  # Confidence threshold for decomposition
    
    # Aggregation query settings
    enable_aggregation_detection: bool = True
    aggregation_keywords: list = None
    
    # Response synthesis settings
    enable_response_synthesis: bool = True
    max_synthesis_context_length: int = 4000
    
    def __post_init__(self):
        if self.aggregation_keywords is None:
            self.aggregation_keywords = [
                "how many", "count", "total", "number of", "sum", "aggregate",
                "list all", "show all", "find all", "get all"
            ]

@dataclass
class SystemConfig:
    """Main system configuration"""
    environment: str = "development"
    debug: bool = False
    data_dir: str = "data"
    log_dir: str = "logs"
    
    # Component configs
    vector_store: VectorStoreConfig = None  # New unified vector store config
    database: DatabaseConfig = None  # Legacy support
    embedding: EmbeddingConfig = None
    llm: LLMConfig = None
    api: APIConfig = None
    ingestion: IngestionConfig = None
    retrieval: RetrievalConfig = None
    monitoring: MonitoringConfig = None
    folder_monitoring: FolderMonitoringConfig = None
    azure_ai: AzureAIConfig = None
    conversation: ConversationConfig = None
    
    def __post_init__(self):
        if self.vector_store is None:
            self.vector_store = VectorStoreConfig()
        if self.database is None:
            self.database = DatabaseConfig()
        if self.embedding is None:
            self.embedding = EmbeddingConfig()
        if self.llm is None:
            self.llm = LLMConfig()
        if self.api is None:
            self.api = APIConfig()
            self.api.cors_origins = ["*"] if self.debug else []
        if self.ingestion is None:
            self.ingestion = IngestionConfig()
            self.ingestion.supported_formats = [".pdf", ".docx", ".doc", ".txt", ".md", ".json", ".csv", ".xlsx", ".xls", ".xlsm", ".xlsb", ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif", ".webp", ".svg"]
        if self.retrieval is None:
            self.retrieval = RetrievalConfig()
        if self.monitoring is None:
            self.monitoring = MonitoringConfig()
        if self.folder_monitoring is None:
            self.folder_monitoring = FolderMonitoringConfig()
        if self.azure_ai is None:
            self.azure_ai = AzureAIConfig()
        if self.conversation is None:
            self.conversation = ConversationConfig()

class ConfigManager:
    """Configuration manager with environment overrides"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "data/config/system_config.json"
        self.config = self._load_config()
        self._apply_env_overrides()
    
    def _load_config(self) -> SystemConfig:
        """Load configuration from file or create default"""
        config_file = Path(self.config_path)
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                return self._dict_to_config(config_data)
            except Exception as e:
                print(f"Error loading config: {e}. Using defaults.")
        
        return SystemConfig()
    
    def _dict_to_config(self, data: Dict[str, Any]) -> SystemConfig:
        """Convert dictionary to SystemConfig"""
        # Extract nested configs
        vector_store_data = data.pop('vector_store', {})
        database_data = data.pop('database', {})
        embedding_data = data.pop('embedding', {})
        llm_data = data.pop('llm', {})
        api_data = data.pop('api', {})
        ingestion_data = data.pop('ingestion', {})
        retrieval_data = data.pop('retrieval', {})
        monitoring_data = data.pop('monitoring', {})
        folder_monitoring_data = data.pop('folder_monitoring', {})
        azure_ai_data = data.pop('azure_ai', {})
        conversation_data = data.pop('conversation', {})
        
        # Remove unknown fields to prevent TypeError
        known_fields = {'environment', 'debug', 'data_dir', 'log_dir'}
        filtered_data = {k: v for k, v in data.items() if k in known_fields}
        
        config = SystemConfig(**filtered_data)
        
        # Create each config with safe field filtering
        config.vector_store = self._safe_create_config(VectorStoreConfig, vector_store_data)
        config.database = self._safe_create_config(DatabaseConfig, database_data)
        config.embedding = self._safe_create_config(EmbeddingConfig, embedding_data)
        config.llm = self._safe_create_config(LLMConfig, llm_data)
        config.api = self._safe_create_config(APIConfig, api_data)
        config.ingestion = self._safe_create_config(IngestionConfig, ingestion_data)
        config.retrieval = self._safe_create_config(RetrievalConfig, retrieval_data)
        config.monitoring = self._safe_create_config(MonitoringConfig, monitoring_data)
        config.folder_monitoring = self._safe_create_config(FolderMonitoringConfig, folder_monitoring_data)
        config.azure_ai = self._safe_create_config(AzureAIConfig, azure_ai_data)
        config.conversation = self._safe_create_config(ConversationConfig, conversation_data)
        
        return config
    
    def _safe_create_config(self, config_class, data):
        """Safely create config object by filtering unknown fields"""
        if not data:
            return config_class()
        
        # Get field names from the dataclass
        import dataclasses
        field_names = {field.name for field in dataclasses.fields(config_class)}
        
        # Filter data to only include known fields
        filtered_data = {k: v for k, v in data.items() if k in field_names}
        
        try:
            return config_class(**filtered_data)
        except Exception as e:
            print(f"Warning: Failed to create {config_class.__name__} with data {filtered_data}: {e}")
            return config_class()
    
    def _apply_env_overrides(self):
        """Apply environment variable overrides"""
        # System level
        self.config.environment = os.getenv('RAG_ENVIRONMENT', self.config.environment)
        self.config.debug = os.getenv('RAG_DEBUG', str(self.config.debug)).lower() == 'true'
        
        # LLM config
        if os.getenv('RAG_LLM_API_KEY'):
            self.config.llm.api_key = os.getenv('RAG_LLM_API_KEY')
        if os.getenv('RAG_LLM_PROVIDER'):
            self.config.llm.provider = os.getenv('RAG_LLM_PROVIDER')
        if os.getenv('RAG_LLM_MODEL'):
            self.config.llm.model_name = os.getenv('RAG_LLM_MODEL')
        
        # Provider-specific API keys
        if os.getenv('GROQ_API_KEY'):
            if self.config.llm.provider == 'groq':
                self.config.llm.api_key = os.getenv('GROQ_API_KEY')
        if os.getenv('OPENAI_API_KEY'):
            if self.config.llm.provider == 'openai':
                self.config.llm.api_key = os.getenv('OPENAI_API_KEY')
        if os.getenv('COHERE_API_KEY'):
            if self.config.llm.provider == 'cohere':
                self.config.llm.api_key = os.getenv('COHERE_API_KEY')
            # Also set for embedding if using Cohere
            if self.config.embedding.provider == 'cohere':
                self.config.embedding.api_key = os.getenv('COHERE_API_KEY')
        if os.getenv('AZURE_API_KEY'):
            if self.config.llm.provider == 'azure':
                self.config.llm.api_key = os.getenv('AZURE_API_KEY')
            # Also set for embedding if using Azure
            if self.config.embedding.provider == 'azure':
                self.config.embedding.api_key = os.getenv('AZURE_API_KEY')
        
        # Embedding config
        if os.getenv('RAG_EMBEDDING_PROVIDER'):
            self.config.embedding.provider = os.getenv('RAG_EMBEDDING_PROVIDER')
        if os.getenv('RAG_EMBEDDING_MODEL'):
            self.config.embedding.model_name = os.getenv('RAG_EMBEDDING_MODEL')
        
        # Dynamically calculate embedding dimension based on provider and model
        from .constants import get_embedding_dimension
        self.config.embedding.dimension = get_embedding_dimension(
            self.config.embedding.provider, 
            self.config.embedding.model_name
        )
        
        # API config
        if os.getenv('RAG_API_HOST'):
            self.config.api.host = os.getenv('RAG_API_HOST')
        if os.getenv('RAG_API_PORT'):
            self.config.api.port = int(os.getenv('RAG_API_PORT'))
        
        # Monitoring
        if os.getenv('RAG_LOG_LEVEL'):
            self.config.monitoring.log_level = os.getenv('RAG_LOG_LEVEL')
        
        # Azure AI config - check both short and long environment variable names
        cv_endpoint = os.getenv('AZURE_CV_ENDPOINT') or os.getenv('AZURE_COMPUTER_VISION_ENDPOINT')
        if cv_endpoint:
            self.config.azure_ai.computer_vision_endpoint = cv_endpoint
            
        cv_key = os.getenv('AZURE_CV_KEY') or os.getenv('AZURE_COMPUTER_VISION_KEY')
        if cv_key:
            self.config.azure_ai.computer_vision_key = cv_key
            
        di_endpoint = os.getenv('AZURE_DI_ENDPOINT') or os.getenv('AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT')
        if di_endpoint:
            self.config.azure_ai.document_intelligence_endpoint = di_endpoint
            
        di_key = os.getenv('AZURE_DI_KEY') or os.getenv('AZURE_DOCUMENT_INTELLIGENCE_KEY')
        if di_key:
            self.config.azure_ai.document_intelligence_key = di_key
    
    def get_config(self, component: Optional[str] = None) -> Any:
        """Get configuration for specific component or entire config"""
        if component is None:
            return self.config
        
        return getattr(self.config, component, None)
    
    def _sanitize_config(self) -> Dict[str, Any]:
        """Return a dict representation of the config with secrets removed so that
        they are not persisted to disk. This prevents accidental leakage of API
        keys that should live only in environment variables or secret stores."""
        cfg = asdict(self.config)

        # Blank out known secret fields; use defensive checks in case keys are missing
        try:
            cfg["llm"]["api_key"] = None
        except Exception:
            pass
        try:
            cfg["embedding"]["api_key"] = None
        except Exception:
            pass
        try:
            cfg.get("azure_ai", {})["computer_vision_key"] = None
        except Exception:
            pass
        try:
            cfg.get("azure_ai", {})["document_intelligence_key"] = None
        except Exception:
            pass

        return cfg

    def save_config(self):
        """Save current configuration to file, ensuring that secrets are stripped."""
        config_file = Path(self.config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)

        sanitized = self._sanitize_config()
        with open(config_file, "w") as f:
            json.dump(sanitized, f, indent=2)
    
    def update_config(self, component: str, updates: Dict[str, Any]):
        """Update specific component configuration"""
        if hasattr(self.config, component):
            component_config = getattr(self.config, component)
            for key, value in updates.items():
                if hasattr(component_config, key):
                    setattr(component_config, key, value)
            self.save_config()
    
    def validate_config(self) -> Dict[str, Any]:
        """Validate configuration and return any issues"""
        issues = {}
        
        # Validate LLM API key
        if not self.config.llm.api_key:
            issues['llm_api_key'] = "LLM API key not configured"
        
        # Validate paths
        data_dir = Path(self.config.data_dir)
        if not data_dir.exists():
            issues['data_dir'] = f"Data directory does not exist: {data_dir}"
        
        # Validate embedding model
        try:
            from sentence_transformers import SentenceTransformer
            # This will validate the model name
            model_name = self.config.embedding.model_name
            if not model_name:
                issues['embedding_model'] = "Embedding model name not specified"
        except ImportError:
            issues['sentence_transformers'] = "sentence-transformers not installed"
        
        return issues 