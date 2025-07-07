"""
Dependency Injection Container
Manages system components and their dependencies
"""
from typing import Dict, Any, Callable, Optional, TypeVar, Type
import threading
from functools import wraps
import json
from pathlib import Path
from datetime import datetime

T = TypeVar('T')

class DependencyContainer:
    """Simple dependency injection container"""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._singletons: Dict[str, Any] = {}
        self._lock = threading.RLock()  # Use reentrant lock to allow recursive calls
        self._creating = set()  # Track services being created to prevent circular deps
    
    def register(self, name: str, factory: Callable, singleton: bool = True):
        """Register a service factory"""
        with self._lock:
            self._factories[name] = factory
            if not singleton and name in self._singletons:
                del self._singletons[name]
    
    def register_instance(self, name: str, instance: Any):
        """Register a service instance directly"""
        with self._lock:
            self._services[name] = instance
            self._singletons[name] = instance
    
    def get(self, name: str) -> Any:
        """Get a service instance"""
        # Check if already instantiated (thread-safe read)
        if name in self._singletons:
            return self._singletons[name]
        
        if name in self._services:
            return self._services[name]
        
        # Use lock for creation
        with self._lock:
            # Double-check after acquiring lock
            if name in self._singletons:
                return self._singletons[name]
            
            if name in self._services:
                return self._services[name]
            
            # Check for circular dependency
            if hasattr(self, '_creating') and name in self._creating:
                raise RuntimeError(f"Circular dependency detected for service '{name}'")
            
            # Create from factory
            if name in self._factories:
                if not hasattr(self, '_creating'):
                    self._creating = set()
                
                self._creating.add(name)
                try:
                    factory = self._factories[name]
                    instance = factory(self)
                    self._singletons[name] = instance
                    return instance
                finally:
                    self._creating.discard(name)
            
            raise KeyError(f"Service '{name}' not registered")
    
    def has(self, name: str) -> bool:
        """Check if service is registered"""
        return name in self._services or name in self._factories or name in self._singletons
    
    def list_services(self) -> list:
        """List all registered services"""
        all_services = set()
        all_services.update(self._services.keys())
        all_services.update(self._factories.keys())
        all_services.update(self._singletons.keys())
        return list(all_services)

def inject(*dependencies):
    """Decorator for dependency injection"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Assume first argument is the container
            if args and hasattr(args[0], 'get'):
                container = args[0]
                injected_deps = {}
                
                for dep_name in dependencies:
                    if dep_name not in kwargs:
                        injected_deps[dep_name] = container.get(dep_name)
                
                kwargs.update(injected_deps)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Service registration helpers
def create_config_manager(container: DependencyContainer):
    """Factory for ConfigManager"""
    from .config_manager import ConfigManager
    return ConfigManager()

def create_json_store(container: DependencyContainer):
    """Factory for JSONStore"""
    print(f"     🔧 Creating JSON store...")
    from .json_store import JSONStore
    print(f"     📋 JSONStore imported")
    # Use default path to avoid circular dependency with config_manager
    json_store = JSONStore("data")
    print(f"     ✅ JSON store created successfully")
    return json_store

def create_metadata_store(container: DependencyContainer):
    """Factory for PersistentJSONMetadataStore"""
    try:
        from ..storage.persistent_metadata_store import PersistentJSONMetadataStore
    except ImportError:
        try:
            from rag_system.src.storage.persistent_metadata_store import PersistentJSONMetadataStore
        except ImportError:
            # Last fallback for when running as script
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from storage.persistent_metadata_store import PersistentJSONMetadataStore
    # Use default path to avoid circular dependency with config_manager
    return PersistentJSONMetadataStore("data/metadata")

def create_log_store(container: DependencyContainer):
    """Factory for PersistentJSONLogStore (persistent file-based log store)"""
    class PersistentJSONLogStore:
        """Simple persistent log store that writes events to a JSON file on disk."""
        def __init__(self, log_dir="data/logs"):
            self.log_dir = Path(log_dir)
            self.log_dir.mkdir(parents=True, exist_ok=True)
            self.log_file = self.log_dir / "log_events.json"
            # Initialize log file if it doesn't exist
            if not self.log_file.exists():
                with open(self.log_file, 'w', encoding='utf-8') as f:
                    json.dump([], f)

        def log_event(self, event_type, event_data):
            """Append a log event to the persistent log file."""
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            except Exception:
                logs = []
            logs.append({
                'timestamp': datetime.now().isoformat(),
                'type': event_type,
                'data': event_data
            })
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)

    print(f"     🔧 Creating persistent JSON log store...")
    log_store = PersistentJSONLogStore("data/logs")
    print(f"     ✅ Persistent JSON log store created successfully")
    return log_store

def create_vector_store(container: DependencyContainer):
    """Factory for Vector Store (FAISS or Qdrant)"""
    print(f"     🔧 Creating vector store...")
    
    # Get config to determine which vector store to use
    config_manager = container.get('config_manager')
    config = config_manager.get_config()
    embedding_config = config_manager.get_config('embedding')
    
    # Determine vector store type from config
    vector_store_config = getattr(config, 'vector_store', None)
    if vector_store_config and hasattr(vector_store_config, 'type'):
        vector_store_type = vector_store_config.type
    else:
        # Default to Qdrant if not specified, and log a warning.
        vector_store_type = 'qdrant'
        logging.warning("Vector store type not specified in config, defaulting to Qdrant.")
    
    try:
        from .constants import get_embedding_dimension
    except ImportError:
        try:
            from rag_system.src.core.constants import get_embedding_dimension
        except ImportError:
            # Last fallback for when running as script
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).parent))
            from constants import get_embedding_dimension
    
    # Get dynamic dimension based on provider and model
    dimension = get_embedding_dimension(
        embedding_config.provider, 
        embedding_config.model_name
    )
    
    if vector_store_type.lower() == 'qdrant':
        print(f"     🦅 Creating Qdrant store...")
        try:
            from ..storage.qdrant_store import QdrantVectorStore
        except ImportError:
            try:
                from rag_system.src.storage.qdrant_store import QdrantVectorStore
            except ImportError:
                # Last fallback for when running as script
                import sys
                from pathlib import Path
                sys.path.insert(0, str(Path(__file__).parent.parent))
                from storage.qdrant_store import QdrantVectorStore
        
        # Get Qdrant config from vector_store section
        url = vector_store_config.url
        collection_name = vector_store_config.collection_name
        on_disk = vector_store_config.on_disk_storage
        
        print(f"     📋 Qdrant config: url={url}, collection={collection_name}, dimension={dimension}")
        vector_store = QdrantVectorStore(
            url=url,
            collection_name=collection_name,
            dimension=dimension,
            on_disk=on_disk
        )
        print(f"     ✅ Qdrant store created successfully with dimension {dimension}")
    else:
        print(f"     📁 Creating FAISS store...")
        try:
            from ..storage.faiss_store import FAISSStore
        except ImportError:
            try:
                from rag_system.src.storage.faiss_store import FAISSStore
            except ImportError:
                # Last fallback for when running as script
                import sys
                from pathlib import Path
                sys.path.insert(0, str(Path(__file__).parent.parent))
                from storage.faiss_store import FAISSStore
        
        # Get FAISS config - use vector_store config if available, otherwise fall back to database config
        if vector_store_config:
            index_path = vector_store_config.faiss_index_path
        else:
            # Fallback to legacy database config
            database_config = config_manager.get_config('database')
            index_path = database_config.faiss_index_path
        
        print(f"     📋 FAISS config: path={index_path}, dimension={dimension}")
        vector_store = FAISSStore(
            index_path=index_path,
            dimension=dimension
        )
        print(f"     ✅ FAISS store created successfully with dimension {dimension}")
    
    return vector_store

def create_faiss_store(container: DependencyContainer):
    """Legacy factory for FAISSStore - redirects to create_vector_store"""
    return create_vector_store(container)

def create_embedder(container: DependencyContainer):
    """Factory for Embedder"""
    print(f"     🔧 Creating embedder...")
    try:
        from ..ingestion.embedder import Embedder
    except ImportError:
        try:
            from rag_system.src.ingestion.embedder import Embedder
        except ImportError:
            # Last fallback for when running as script
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from ingestion.embedder import Embedder
    import os
    
    # Get config to use correct embedding provider and model
    config_manager = container.get('config_manager')
    embedding_config = config_manager.get_config('embedding')
    
    print(f"     📋 Embedder config: provider={embedding_config.provider}, model={embedding_config.model_name}")
    
    # Get endpoint for Azure if needed
    endpoint = None
    if embedding_config.provider == 'azure':
        endpoint = os.getenv('AZURE_EMBEDDINGS_ENDPOINT')
    
    embedder = Embedder(
        provider=embedding_config.provider,
        model_name=embedding_config.model_name,
        device=embedding_config.device,
        batch_size=embedding_config.batch_size,
        api_key=embedding_config.api_key,
        endpoint=endpoint
    )
    print(f"     ✅ Embedder created successfully")
    return embedder

def create_chunker(container: DependencyContainer):
    """Factory for Chunker with memory-efficient semantic chunking"""
    try:
        from ..ingestion.chunker import Chunker
    except ImportError:
        try:
            from rag_system.src.ingestion.chunker import Chunker
        except ImportError:
            # Last fallback for when running as script
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from ingestion.chunker import Chunker
    
    # Use default values to avoid circular dependency with config_manager
    # Enable semantic chunking by default for better performance
    # Model will be loaded on demand to save memory
    chunker = Chunker(
        chunk_size=1000,
        chunk_overlap=200,
        use_semantic=True  # Enable semantic chunking with lazy loading
    )
    
    print(f"     ✅ Chunker created with memory-efficient semantic chunking")
    return chunker

def create_llm_client(container: DependencyContainer):
    """Factory for LLMClient"""
    try:
        from ..retrieval.llm_client import LLMClient
    except ImportError:
        try:
            from rag_system.src.retrieval.llm_client import LLMClient
        except ImportError:
            # Last fallback for when running as script
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from retrieval.llm_client import LLMClient
    
    # Get configuration from config manager
    config_manager = container.get('config_manager')
    llm_config = config_manager.get_config('llm')
    
    # Get endpoint for Azure if needed
    endpoint = None
    if llm_config.provider == 'azure':
        import os
        endpoint = os.getenv('AZURE_CHAT_ENDPOINT')
    
    return LLMClient(
        provider=llm_config.provider,
        model_name=llm_config.model_name,
        api_key=llm_config.api_key,
        temperature=llm_config.temperature,
        max_tokens=llm_config.max_tokens,
        endpoint=endpoint
    )

def create_reranker(container: DependencyContainer):
    """Factory for Reranker"""
    print(f"     🔧 Creating reranker...")
    try:
        from ..retrieval.reranker import create_reranker as create_reranker_func
    except ImportError:
        try:
            from rag_system.src.retrieval.reranker import create_reranker as create_reranker_func
        except ImportError:
            # Last fallback for when running as script
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from retrieval.reranker import create_reranker as create_reranker_func
    
    config_manager = container.get('config_manager')
    reranker = create_reranker_func(config_manager)
    print(f"     ✅ Reranker created successfully: {reranker.get_model_info()['model_name']}")
    return reranker

def create_query_enhancer(container: DependencyContainer):
    """Factory for QueryEnhancer"""
    print(f"     🔧 Creating query enhancer...")
    try:
        from ..retrieval.query_enhancer import create_query_enhancer as create_query_enhancer_func
    except ImportError:
        try:
            from rag_system.src.retrieval.query_enhancer import create_query_enhancer as create_query_enhancer_func
        except ImportError:
            # Last fallback for when running as script
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from retrieval.query_enhancer import create_query_enhancer as create_query_enhancer_func
    
    import os
    config_manager = container.get('config_manager')
    enable_llm = os.getenv('ENABLE_LLM_QUERY_ENHANCER', 'false').lower() in ('1', 'true', 'yes')
    if enable_llm:
        try:
            from ..retrieval.llm_query_enhancer import LLMQueryEnhancer
        except ImportError:
            from rag_system.src.retrieval.llm_query_enhancer import LLMQueryEnhancer
        llm_client = container.get('llm_client')
        query_enhancer = LLMQueryEnhancer(llm_client)
        print("     ✅ LLMQueryEnhancer enabled via flag")
    else:
        query_enhancer = create_query_enhancer_func(config_manager)
        print(f"     ✅ Query enhancer created successfully: {query_enhancer.get_enhancer_info()['enhancer_type']}")
    return query_enhancer

def create_query_engine(container: DependencyContainer):
    """Factory for QueryEngine - creates appropriate engine based on vector store type"""
    
    # Get config to determine which query engine to use
    config_manager = container.get('config_manager')
    config = config_manager.get_config()
    
    # Determine vector store type from config
    vector_store_config = getattr(config, 'vector_store', None)
    if vector_store_config:
        vector_store_type = vector_store_config.type
    else:
        vector_store_type = 'faiss'  # Default fallback
    
    if vector_store_type.lower() == 'qdrant':
        # Use specialized QdrantQueryEngine
        try:
            from ..retrieval.qdrant_query_engine import QdrantQueryEngine
        except ImportError:
            try:
                from rag_system.src.retrieval.qdrant_query_engine import QdrantQueryEngine
            except ImportError:
                # Last fallback for when running as script
                import sys
                from pathlib import Path
                sys.path.insert(0, str(Path(__file__).parent.parent))
                from retrieval.qdrant_query_engine import QdrantQueryEngine
        
        return QdrantQueryEngine(
            qdrant_store=container.get('vector_store'),
            embedder=container.get('embedder'),
            llm_client=container.get('llm_client'),
            config=config
        )
    else:
        # Use standard QueryEngine for FAISS
        try:
            from ..retrieval.query_engine import QueryEngine
        except ImportError:
            try:
                from rag_system.src.retrieval.query_engine import QueryEngine
            except ImportError:
                # Last fallback for when running as script
                import sys
                from pathlib import Path
                sys.path.insert(0, str(Path(__file__).parent.parent))
                from retrieval.query_engine import QueryEngine
        
        return QueryEngine(
            vector_store=container.get('vector_store'),
            embedder=container.get('embedder'),
            llm_client=container.get('llm_client'),
            metadata_store=container.get('metadata_store'),
            config_manager=config_manager,
            reranker=container.get('reranker'),
            query_enhancer=container.get('query_enhancer')
        )

def create_ingestion_engine(container: DependencyContainer):
    """Factory for IngestionEngine"""
    try:
        from ..ingestion.ingestion_engine import IngestionEngine
    except ImportError:
        try:
            from rag_system.src.ingestion.ingestion_engine import IngestionEngine
        except ImportError:
            # Last fallback for when running as script
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from ingestion.ingestion_engine import IngestionEngine
    return IngestionEngine(
        chunker=container.get('chunker'),
        embedder=container.get('embedder'),
        vector_store=container.get('vector_store'),
        metadata_store=container.get('metadata_store'),
        config_manager=container.get('config_manager')
    )

def create_verified_ingestion_engine(container: DependencyContainer):
    """Factory for VerifiedIngestionEngine"""
    print(f"     🔧 Creating verified ingestion engine...")
    try:
        from .verified_ingestion_engine import VerifiedIngestionEngine
        from .pipeline_verifier import PipelineVerifier
        
        ingestion_engine = container.get('ingestion_engine')
        verifier = PipelineVerifier(debug_mode=True, save_intermediate=True)
        
        verified_engine = VerifiedIngestionEngine(ingestion_engine, verifier)
        print(f"     ✅ Verified ingestion engine created successfully")
        return verified_engine
    except Exception as e:
        print(f"     ❌ Failed to create verified ingestion engine: {e}")
        # Return the regular ingestion engine as fallback
        return container.get('ingestion_engine')

def create_servicenow_integration(container: DependencyContainer):
    """Factory for ServiceNow Integration"""
    print(f"     🔧 Creating ServiceNow integration...")
    try:
        try:
            from ..integrations.servicenow import ServiceNowIntegration
        except ImportError:
            from rag_system.src.integrations.servicenow import ServiceNowIntegration
        config_manager = container.get('config_manager')
        ingestion_engine = container.get('ingestion_engine')
        
        integration = ServiceNowIntegration(
            config_manager=config_manager,
            ingestion_engine=ingestion_engine
        )
        print(f"     ✅ ServiceNow integration created successfully")
        return integration
    except Exception as e:
        print(f"     ⚠️ ServiceNow integration creation failed: {e}")
        # Return None if ServiceNow integration fails - it's optional
        return None

def create_conversation_manager(container: DependencyContainer):
    """Factory for ConversationManager"""
    print(f"     🔧 Creating conversation manager...")
    
    try:
        from ..conversation.fresh_conversation_manager import FreshConversationManager
        from ..conversation.fresh_conversation_state import FreshConversationStateManager
        from ..conversation.fresh_context_manager import FreshContextManager
        from ..conversation.fresh_memory_manager import FreshMemoryManager
        from ..conversation.fresh_smart_router import FreshSmartRouter
        from ..conversation.fresh_conversation_nodes import FreshConversationNodes
        from ..conversation.fresh_conversation_graph import FreshConversationGraph
    except ImportError:
        try:
            from rag_system.src.conversation.fresh_conversation_manager import FreshConversationManager
            from rag_system.src.conversation.fresh_conversation_state import FreshConversationStateManager
            from rag_system.src.conversation.fresh_context_manager import FreshContextManager
            from rag_system.src.conversation.fresh_memory_manager import FreshMemoryManager
            from rag_system.src.conversation.fresh_smart_router import FreshSmartRouter
            from rag_system.src.conversation.fresh_conversation_nodes import FreshConversationNodes
            from rag_system.src.conversation.fresh_conversation_graph import FreshConversationGraph
        except ImportError:
            # Last fallback for when running as script
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from conversation.fresh_conversation_manager import FreshConversationManager
            from conversation.fresh_conversation_state import FreshConversationStateManager
            from conversation.fresh_context_manager import FreshContextManager
            from conversation.fresh_memory_manager import FreshMemoryManager
            from conversation.fresh_smart_router import FreshSmartRouter
            from conversation.fresh_conversation_nodes import FreshConversationNodes
            from conversation.fresh_conversation_graph import FreshConversationGraph
    
    # Create managers
    context_manager = FreshContextManager()
    memory_manager = FreshMemoryManager()
    smart_router = FreshSmartRouter(context_manager, container.get('llm_client'))
    
    # Register smart router in container for other components
    container.register_instance('smart_router', smart_router)
    
    # Create conversation components
    state_manager = FreshConversationStateManager(context_manager, memory_manager, smart_router)
    nodes = FreshConversationNodes(container)
    graph = FreshConversationGraph(nodes, state_manager)
    
    # Create conversation manager
    conversation_manager = FreshConversationManager(graph, state_manager)
    
    print(f"     ✅ Conversation manager created successfully")
    return conversation_manager

def create_smart_router(container: DependencyContainer):
    """Factory for FreshSmartRouter with LLM client dependency"""
    print(f"     🔧 Creating smart router...")
    
    try:
        from ..conversation.fresh_smart_router import FreshSmartRouter
        from ..conversation.fresh_context_manager import FreshContextManager
    except ImportError:
        try:
            from rag_system.src.conversation.fresh_smart_router import FreshSmartRouter
            from rag_system.src.conversation.fresh_context_manager import FreshContextManager
        except ImportError:
            # Last fallback for when running as script
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from conversation.fresh_smart_router import FreshSmartRouter
            from conversation.fresh_context_manager import FreshContextManager
    
    # Create context manager
    context_manager = FreshContextManager()
    
    # Get dependencies
    llm_client = container.get('llm_client')
    config_manager = container.get('config_manager')
    
    # Create smart router with dependencies
    smart_router = FreshSmartRouter(context_manager, llm_client, config_manager)
    
    print(f"     ✅ Smart router created successfully with LLM enhancement")
    return smart_router

def create_ingestion_verifier(container: DependencyContainer):
    """Factory for ingestion verifier"""
    print(f"     🔧 Creating ingestion verifier...")
    
    try:
        from ..ingestion.ingestion_verifier import IngestionVerifier
    except ImportError:
        try:
            from rag_system.src.ingestion.ingestion_verifier import IngestionVerifier
        except ImportError:
            # Last fallback for when running as script
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from ingestion.ingestion_verifier import IngestionVerifier
    
    return IngestionVerifier(container)

def create_ingestion_debugger(container: DependencyContainer):
    """Factory for ingestion debugger"""
    print(f"     🔧 Creating ingestion debugger...")
    
    try:
        from ..ingestion.ingestion_debugger import IngestionDebugger
    except ImportError:
        try:
            from rag_system.src.ingestion.ingestion_debugger import IngestionDebugger
        except ImportError:
            # Last fallback for when running as script
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from ingestion.ingestion_debugger import IngestionDebugger
    
    return IngestionDebugger(container)

def register_core_services(container: DependencyContainer):
    """Register all core services"""
    print("🔧 Registering core services...")
    
    # Core services
    container.register('config_manager', create_config_manager)
    container.register('json_store', create_json_store)
    container.register('metadata_store', create_metadata_store)
    container.register('log_store', create_log_store)
    
    # Vector and embedding services
    container.register('vector_store', create_vector_store)
    container.register('embedder', create_embedder)
    container.register('chunker', create_chunker)
    
    # LLM and query services
    container.register('llm_client', create_llm_client)
    container.register('reranker', create_reranker)
    container.register('query_enhancer', create_query_enhancer)
    container.register('query_engine', create_query_engine)
    
    # Conversation services
    container.register('smart_router', create_smart_router)
    container.register('conversation_manager', create_conversation_manager)
    
    # Ingestion services
    container.register('ingestion_engine', create_ingestion_engine)
    container.register('verified_ingestion_engine', create_verified_ingestion_engine)
    container.register('ingestion_verifier', create_ingestion_verifier)
    container.register('ingestion_debugger', create_ingestion_debugger)
    
    # Integration services
    container.register('servicenow_integration', create_servicenow_integration)
    
    print("✅ Core services registered successfully")

# Global container instance
_container = None

def get_dependency_container() -> DependencyContainer:
    """Get the global dependency container"""
    global _container
    if _container is None:
        _container = DependencyContainer()
        register_core_services(_container)
    return _container

def set_dependency_container(container: DependencyContainer):
    """Set the global dependency container"""
    global _container
    _container = container
