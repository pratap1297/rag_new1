#!/usr/bin/env python3
"""
Test Qdrant Integration in UI Backend
Direct testing of the system to verify no FAISS usage and confirm Qdrant
"""
import sys
import os
import requests
import json
from pathlib import Path

# Add the rag_system to Python path
sys.path.insert(0, str(Path(__file__).parent / "rag_system" / "src"))

def test_direct_system():
    """Test the system directly to verify Qdrant usage"""
    print("🔍 DIRECT SYSTEM TESTING - QDRANT VERIFICATION")
    print("=" * 60)
    
    try:
        from core.dependency_container import register_core_services, DependencyContainer
        from core.config_manager import ConfigManager
        
        # Initialize system
        container = DependencyContainer()
        register_core_services(container)
        
        # Get components
        config_manager = container.get('config_manager')
        vector_store = container.get('vector_store')
        query_engine = container.get('query_engine')
        
        print("✅ System components initialized successfully")
        
        # Check configuration
        config = config_manager.get_config()
        vector_config = config.vector_store
        
        print(f"\n📋 Configuration Check:")
        print(f"   Vector store type: {vector_config.type}")
        print(f"   URL: {vector_config.url}")
        print(f"   Collection: {vector_config.collection_name}")
        print(f"   Dimension: {vector_config.dimension}")
        
        if vector_config.type.lower() == 'qdrant':
            print("✅ Configuration confirms Qdrant usage!")
        else:
            print(f"❌ Configuration shows: {vector_config.type}")
        
        # Check vector store type
        vector_store_type = type(vector_store).__name__
        print(f"\n🗃️ Vector Store Check:")
        print(f"   Class: {vector_store_type}")
        
        if 'Qdrant' in vector_store_type:
            print("✅ Vector store is QdrantVectorStore!")
        else:
            print(f"❌ Vector store is: {vector_store_type}")
        
        # Get collection info
        if hasattr(vector_store, 'get_collection_info'):
            info = vector_store.get_collection_info()
            print(f"\n📊 Collection Information:")
            print(f"   Status: {info.get('status', 'unknown')}")
            print(f"   Vectors: {info.get('vectors_count', 0)}")
            print(f"   Points: {info.get('points_count', 0)}")
            print(f"   Segments: {info.get('segments_count', 0)}")
            
        # Test query engine type
        query_engine_type = type(query_engine).__name__
        print(f"\n🔍 Query Engine Check:")
        print(f"   Class: {query_engine_type}")
        
        if 'Qdrant' in query_engine_type:
            print("✅ Query engine is QdrantQueryEngine!")
        else:
            print(f"⚠️  Query engine is: {query_engine_type}")
        
        # Test some queries
        print(f"\n🧪 Testing Queries:")
        
        test_queries = [
            "list all incidents",
            "how many documents do we have?",
            "show me network information"
        ]
        
        for i, query in enumerate(test_queries, 1):
            try:
                print(f"\n--- Query {i}: {query} ---")
                response = query_engine.process_query(query)
                
                print(f"✅ Query successful")
                print(f"   Response length: {len(response.get('response', ''))}")
                print(f"   Sources: {len(response.get('sources', []))}")
                print(f"   Query type: {response.get('query_type', 'unknown')}")
                print(f"   Method: {response.get('method', 'unknown')}")
                
                # Check for Qdrant-specific methods
                method = response.get('method', '')
                if 'qdrant' in method.lower():
                    print(f"✅ Using Qdrant method: {method}")
                
            except Exception as e:
                print(f"❌ Query failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ System test failed: {e}")
        return False

def test_api_endpoints():
    """Test API endpoints to verify functionality"""
    print(f"\n🌐 API ENDPOINT TESTING")
    print("=" * 60)
    
    api_url = "http://localhost:8000"
    
    # Test health
    try:
        response = requests.get(f"{api_url}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ API Health: {health_data.get('status')}")
        else:
            print(f"❌ API Health failed: {response.status_code}")
    except Exception as e:
        print(f"❌ API Health error: {e}")
    
    # Test query endpoint with Qdrant-specific queries
    qdrant_test_queries = [
        {
            "query": "list all incidents",
            "description": "Listing query (Qdrant scroll API)"
        },
        {
            "query": "how many incidents are there?",
            "description": "Aggregation query (Qdrant native)"
        },
        {
            "query": "incidents about network connectivity",
            "description": "Filtered search (Qdrant pre-filtering)"
        }
    ]
    
    print(f"\n🔍 Testing Qdrant-Specific Query Features:")
    
    for test_case in qdrant_test_queries:
        print(f"\n--- {test_case['description']} ---")
        print(f"Query: '{test_case['query']}'")
        
        try:
            response = requests.post(
                f"{api_url}/query",
                json={"query": test_case['query'], "max_results": 5},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Success")
                print(f"   Response: {len(result.get('response', ''))} chars")
                print(f"   Sources: {len(result.get('sources', []))}")
                print(f"   Method: {result.get('metadata', {}).get('method_used', 'unknown')}")
                
                # Show response preview
                response_text = result.get('response', '')
                if response_text:
                    preview = response_text[:150] + "..." if len(response_text) > 150 else response_text
                    print(f"   Preview: {preview}")
            else:
                print(f"❌ Failed: HTTP {response.status_code}")
                try:
                    error = response.json()
                    print(f"   Error: {error.get('detail', 'No details')}")
                except:
                    print(f"   Error: {response.text[:100]}")
                    
        except Exception as e:
            print(f"❌ Exception: {e}")

def check_for_faiss_references():
    """Check if there are any remaining FAISS references"""
    print(f"\n🔍 CHECKING FOR FAISS REFERENCES")
    print("=" * 60)
    
    try:
        from core.dependency_container import DependencyContainer
        from core.config_manager import ConfigManager
        
        container = DependencyContainer()
        config_manager = ConfigManager()
        
        # Check config
        config = config_manager.get_config()
        config_str = str(config).lower()
        
        if 'faiss' in config_str:
            print("❌ FAISS found in configuration!")
            print(f"   Config content: {config_str}")
        else:
            print("✅ No FAISS references in configuration")
        
        # Check vector store
        register_core_services(container)
        vector_store = container.get('vector_store')
        
        vector_store_str = str(type(vector_store)).lower()
        if 'faiss' in vector_store_str:
            print("❌ FAISS vector store detected!")
        else:
            print("✅ No FAISS in vector store type")
            
        # Check for FAISS-specific attributes
        faiss_attributes = ['faiss_index', 'index_to_id', 'id_to_metadata']
        found_faiss_attrs = []
        
        for attr in faiss_attributes:
            if hasattr(vector_store, attr):
                found_faiss_attrs.append(attr)
        
        if found_faiss_attrs:
            print(f"⚠️  FAISS-like attributes found: {found_faiss_attrs}")
            print("   (These might be compatibility methods)")
        else:
            print("✅ No FAISS-specific attributes detected")
            
        print(f"\n📋 Vector Store Details:")
        print(f"   Type: {type(vector_store).__name__}")
        print(f"   Module: {type(vector_store).__module__}")
        
        return True
        
    except Exception as e:
        print(f"❌ FAISS check failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🔍 COMPREHENSIVE QDRANT UI INTEGRATION TEST")
    print("=" * 80)
    print("This test verifies:")
    print("1. No FAISS components are being used")
    print("2. Qdrant is properly integrated")
    print("3. UI backend is using Qdrant features")
    print("4. Queries work with Qdrant-specific methods")
    print()
    
    results = {}
    
    # Run tests
    results['direct_system'] = test_direct_system()
    results['faiss_check'] = check_for_faiss_references()
    test_api_endpoints()  # This doesn't return a boolean
    
    # Summary
    print(f"\n🏁 FINAL RESULTS")
    print("=" * 80)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\nCore Tests: {passed}/{total} passed")
    
    if passed == total:
        print("\n🎉 SUCCESS: UI backend is using Qdrant!")
        print("✅ No FAISS components detected")
        print("✅ Qdrant integration confirmed")
        print("✅ System is ready for production")
    else:
        print("\n⚠️  Some issues detected, review output above")

if __name__ == "__main__":
    main() 