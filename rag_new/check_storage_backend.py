#!/usr/bin/env python3
"""
Check Storage Backend
Check what vector storage backend the system is using
"""

def check_storage_backend():
    """Check what storage backend is being used"""
    print("🔍 Checking Storage Backend")
    print("=" * 30)
    
    try:
        import sys
        sys.path.append('rag_system/src')
        
        from core.system_init import initialize_system
        
        container = initialize_system()
        print("✅ System initialized")
        
        # Check available services
        available_services = list(container.container._providers.keys()) if hasattr(container.container, '_providers') else []
        print(f"📦 Available services: {available_services}")
        
        # Check for FAISS store
        try:
            faiss_store = container.get('faiss_store')
            print(f"📊 FAISS store type: {type(faiss_store)}")
            print(f"📊 FAISS store class: {faiss_store.__class__.__name__}")
        except Exception as e:
            print(f"❌ FAISS store error: {e}")
        
        # Check for Qdrant store
        try:
            qdrant_store = container.get('qdrant_store')
            print(f"📊 Qdrant store type: {type(qdrant_store)}")
            print(f"📊 Qdrant store class: {qdrant_store.__class__.__name__}")
        except Exception as e:
            print(f"❌ Qdrant store error: {e}")
        
        # Check ingestion engine
        try:
            ingestion_engine = container.get('ingestion_engine')
            print(f"🔧 Ingestion engine type: {type(ingestion_engine)}")
            
            # Check what storage it's using
            if hasattr(ingestion_engine, 'faiss_store'):
                print(f"🔧 Ingestion engine uses faiss_store: {type(ingestion_engine.faiss_store)}")
                print(f"🔧 Faiss store class name: {ingestion_engine.faiss_store.__class__.__name__}")
            
            if hasattr(ingestion_engine, 'qdrant_store'):
                print(f"🔧 Ingestion engine uses qdrant_store: {type(ingestion_engine.qdrant_store)}")
                
        except Exception as e:
            print(f"❌ Ingestion engine error: {e}")
    
    except Exception as e:
        print(f"❌ System check error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_storage_backend() 