#!/usr/bin/env python3
"""
Test script to verify configuration loading
"""
import sys
import json
sys.path.append('rag_system/src')

from core.config_manager import ConfigManager

def test_config_loading():
    """Test configuration loading and vector store detection"""
    
    print("🔧 Testing Configuration Loading")
    print("=" * 50)
    
    try:
        # Initialize config manager
        print("1. Loading configuration...")
        config_manager = ConfigManager()
        
        # Get the full config
        config = config_manager.get_config()
        
        print(f"✅ Configuration loaded successfully")
        print(f"   Environment: {config.environment}")
        print(f"   Debug: {config.debug}")
        
        # Check vector store configuration
        print("\n2. Checking vector store configuration...")
        if hasattr(config, 'vector_store') and config.vector_store:
            vs_config = config.vector_store
            print(f"✅ Vector store configuration found:")
            print(f"   Type: {vs_config.type}")
            print(f"   Dimension: {vs_config.dimension}")
            
            if vs_config.type.lower() == 'qdrant':
                print(f"   🦅 Qdrant settings:")
                print(f"     URL: {vs_config.url}")
                print(f"     Collection: {vs_config.collection_name}")
                print(f"     On disk: {vs_config.on_disk_storage}")
                print(f"     Distance: {vs_config.distance}")
            else:
                print(f"   📁 FAISS settings:")
                print(f"     Index path: {vs_config.faiss_index_path}")
                print(f"     Index type: {vs_config.index_type}")
        else:
            print("❌ No vector_store configuration found")
        
        # Check legacy database configuration
        print("\n3. Checking legacy database configuration...")
        if hasattr(config, 'database') and config.database:
            db_config = config.database
            print(f"ℹ️ Legacy database configuration:")
            print(f"   FAISS index path: {db_config.faiss_index_path}")
            print(f"   Metadata path: {db_config.metadata_path}")
        else:
            print("❌ No database configuration found")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_dependency_container():
    """Test dependency container vector store creation"""
    
    print("\n🔧 Testing Dependency Container")
    print("=" * 50)
    
    try:
        from core.dependency_container import DependencyContainer, register_core_services
        
        # Create container
        print("1. Creating dependency container...")
        container = DependencyContainer()
        
        # Register core services
        print("2. Registering core services...")
        register_core_services(container)
        
        # Create vector store
        print("3. Creating vector store...")
        vector_store = container.get('vector_store')
        
        print(f"✅ Vector store created successfully")
        print(f"   Type: {type(vector_store).__name__}")
        
        # Test vector store basic functionality
        if hasattr(vector_store, 'get_collection_info'):
            print("   🦅 Testing Qdrant functionality...")
            info = vector_store.get_collection_info()
            print(f"   Collection info: {info}")
        elif hasattr(vector_store, 'get_stats'):
            print("   📁 Testing FAISS functionality...")
            stats = vector_store.get_stats()
            print(f"   Stats: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ Dependency container test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Configuration and Vector Store Tests")
    print("=" * 60)
    
    # Test configuration loading
    config_success = test_config_loading()
    
    # Test dependency container
    container_success = test_dependency_container()
    
    print("\n" + "=" * 60)
    print("📊 Test Results:")
    print(f"   Configuration Loading: {'✅ PASS' if config_success else '❌ FAIL'}")
    print(f"   Dependency Container: {'✅ PASS' if container_success else '❌ FAIL'}")
    
    if config_success and container_success:
        print("\n🎉 All tests passed! Configuration is working correctly!")
    else:
        print("\n⚠️ Some tests failed. Check the errors above.") 