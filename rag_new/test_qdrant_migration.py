#!/usr/bin/env python3
"""
Test script to verify FAISS to Qdrant migration
"""
import sys
import os
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_configuration():
    """Test that configuration loads correctly"""
    print("=== Testing Configuration ===")
    
    from rag_system.src.core.config_manager import ConfigManager
    
    config_manager = ConfigManager()
    config = config_manager.get_config()
    
    print(f"✅ Vector store type: {config.vector_store.type}")
    print(f"✅ Vector store URL: {config.vector_store.url}")
    print(f"✅ Collection name: {config.vector_store.collection_name}")
    print(f"✅ Dimension: {config.vector_store.dimension}")
    
    assert config.vector_store.type == "qdrant", f"Expected qdrant, got {config.vector_store.type}"
    print("✅ Configuration test passed")

def test_vector_store_creation():
    """Test that vector store is created correctly"""
    print("\n=== Testing Vector Store Creation ===")
    
    from rag_system.src.core.dependency_container import create_vector_store, DependencyContainer
    from rag_system.src.core.config_manager import ConfigManager
    
    container = DependencyContainer()
    container.register('config_manager', lambda c: ConfigManager())
    
    vector_store = create_vector_store(container)
    
    print(f"✅ Vector store type: {type(vector_store).__name__}")
    print(f"✅ Vector store module: {type(vector_store).__module__}")
    
    # Test basic functionality
    stats = vector_store.get_stats()
    print(f"✅ Vector store stats: {stats}")
    
    # Test that it's QdrantVectorStore
    assert type(vector_store).__name__ == "QdrantVectorStore", f"Expected QdrantVectorStore, got {type(vector_store).__name__}"
    print("✅ Vector store creation test passed")

def test_interface_compatibility():
    """Test that QdrantVectorStore has all required methods"""
    print("\n=== Testing Interface Compatibility ===")
    
    from rag_system.src.storage.qdrant_store import QdrantVectorStore
    
    store = QdrantVectorStore()
    
    # Test required methods exist
    required_methods = [
        'add_vectors',
        'search',
        'search_with_metadata',
        'get_stats',
        'delete_vectors',
        'get_vector_metadata',
        'find_vectors_by_doc_path',
        'delete_vectors_by_doc_path',
        'clear_index',
        'backup_index',
        'restore_index',
        'update_metadata'
    ]
    
    for method in required_methods:
        assert hasattr(store, method), f"Missing method: {method}"
        print(f"✅ Method exists: {method}")
    
    # Test required properties
    required_properties = ['id_to_metadata']
    for prop in required_properties:
        assert hasattr(store, prop), f"Missing property: {prop}"
        print(f"✅ Property exists: {prop}")
    
    print("✅ Interface compatibility test passed")

def test_basic_operations():
    """Test basic vector operations"""
    print("\n=== Testing Basic Operations ===")
    
    from rag_system.src.storage.qdrant_store import QdrantVectorStore
    import numpy as np
    
    store = QdrantVectorStore()
    
    # Test adding vectors
    test_vectors = [np.random.rand(1024).tolist() for _ in range(3)]
    test_metadata = [
        {'text': 'Test document 1', 'doc_id': 'test1'},
        {'text': 'Test document 2', 'doc_id': 'test2'},
        {'text': 'Test document 3', 'doc_id': 'test3'}
    ]
    
    vector_ids = store.add_vectors(test_vectors, test_metadata)
    print(f"✅ Added {len(vector_ids)} vectors")
    
    # Test search
    query_vector = np.random.rand(1024).tolist()
    results = store.search_with_metadata(query_vector, k=2)
    print(f"✅ Search returned {len(results)} results")
    
    # Test metadata retrieval
    if vector_ids:
        metadata = store.get_vector_metadata(vector_ids[0])
        print(f"✅ Retrieved metadata: {metadata is not None}")
    
    # Test stats
    stats = store.get_stats()
    print(f"✅ Stats: {stats}")
    
    print("✅ Basic operations test passed")

def test_dependency_injection():
    """Test that dependency injection works with new parameter names"""
    print("\n=== Testing Dependency Injection ===")
    
    # Test imports without actually creating components (to avoid API key issues)
    try:
        from rag_system.src.ingestion.ingestion_engine import IngestionEngine
        from rag_system.src.retrieval.query_engine import QueryEngine
        print("✅ Components can be imported")
        
        # Check constructor signatures
        import inspect
        
        # Check IngestionEngine constructor
        ing_sig = inspect.signature(IngestionEngine.__init__)
        ing_params = list(ing_sig.parameters.keys())
        assert 'vector_store' in ing_params, f"IngestionEngine missing vector_store parameter: {ing_params}"
        assert 'faiss_store' not in ing_params, f"IngestionEngine still has faiss_store parameter: {ing_params}"
        print("✅ IngestionEngine has correct constructor parameters")
        
        # Check QueryEngine constructor
        query_sig = inspect.signature(QueryEngine.__init__)
        query_params = list(query_sig.parameters.keys())
        assert 'vector_store' in query_params, f"QueryEngine missing vector_store parameter: {query_params}"
        assert 'faiss_store' not in query_params, f"QueryEngine still has faiss_store parameter: {query_params}"
        print("✅ QueryEngine has correct constructor parameters")
        
    except Exception as e:
        print(f"❌ Component import/inspection failed: {e}")
        raise
    
    print("✅ Dependency injection test passed")

def main():
    """Run all tests"""
    print("🚀 Starting FAISS to Qdrant Migration Tests")
    print("=" * 50)
    
    try:
        test_configuration()
        test_vector_store_creation()
        test_interface_compatibility()
        test_basic_operations()
        test_dependency_injection()
        
        print("\n" + "=" * 50)
        print("🎉 ALL TESTS PASSED!")
        print("✅ FAISS to Qdrant migration is working correctly")
        print("✅ System is ready to use Qdrant as the vector store")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 