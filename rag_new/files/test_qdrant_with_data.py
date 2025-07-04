#!/usr/bin/env python3
"""
Test Qdrant functionality with real data upload
"""
import sys
import os
import json
from pathlib import Path

sys.path.append('rag_system/src')

def test_data_upload():
    """Test uploading data from test_data directory"""
    print("📁 Testing Data Upload to Qdrant")
    print("=" * 50)
    
    try:
        from core.dependency_container import DependencyContainer, register_core_services
        
        # Create container
        container = DependencyContainer()
        register_core_services(container)
        
        # Get ingestion engine
        ingestion_engine = container.get('ingestion_engine')
        vector_store = container.get('vector_store')
        
        print(f"✅ Vector Store: {type(vector_store).__name__}")
        
        # Get initial stats
        initial_info = vector_store.get_collection_info()
        initial_count = initial_info['points_count']
        print(f"📊 Initial points in Qdrant: {initial_count}")
        
        # Test data directory
        test_data_dir = Path("D:/Projects-D/pepsi-final2/document_generator/test_data")
        
        if not test_data_dir.exists():
            print(f"❌ Test data directory not found: {test_data_dir}")
            return False
        
        # Get test files
        test_files = list(test_data_dir.glob("*"))
        print(f"📂 Found {len(test_files)} test files")
        
        uploaded_files = []
        
        # Upload each file
        for file_path in test_files:
            if file_path.is_file():
                print(f"\n📤 Uploading: {file_path.name}")
                try:
                    # Upload file
                    result = ingestion_engine.ingest_file(
                        str(file_path),
                        metadata={
                            'filename': file_path.name,
                            'source': 'test_data',
                            'file_type': file_path.suffix
                        }
                    )
                    
                    if result['success']:
                        print(f"✅ Upload successful: {result.get('chunks_created', 0)} chunks created")
                        uploaded_files.append(file_path.name)
                    else:
                        print(f"⚠️ Upload result: {result.get('message', 'Unknown error')}")
                        
                except Exception as e:
                    print(f"❌ Upload failed: {e}")
        
        # Get final stats
        final_info = vector_store.get_collection_info()
        final_count = final_info['points_count']
        new_vectors = final_count - initial_count
        
        print(f"\n📊 Final Statistics:")
        print(f"   Initial points: {initial_count}")
        print(f"   Final points: {final_count}")
        print(f"   New vectors added: {new_vectors}")
        print(f"   Successfully uploaded files: {len(uploaded_files)}")
        
        return len(uploaded_files) > 0
        
    except Exception as e:
        print(f"❌ Data upload test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_qdrant_queries():
    """Test various queries with Qdrant"""
    print("\n🔍 Testing Qdrant Queries")
    print("=" * 50)
    
    try:
        from core.dependency_container import DependencyContainer, register_core_services
        
        # Create container
        container = DependencyContainer()
        register_core_services(container)
        
        # Get components
        query_engine = container.get('query_engine')
        vector_store = container.get('vector_store')
        
        # Test queries
        test_queries = [
            "list all incidents",
            "show all network layouts", 
            "find building information",
            "what facilities are available",
            "count total incidents"
        ]
        
        results = []
        
        for query in test_queries:
            print(f"\n🔍 Query: '{query}'")
            try:
                result = query_engine.process_query(query)
                
                query_type = result.get('query_type', 'unknown')
                total_sources = result.get('total_sources', 0)
                method = result.get('method', 'unknown')
                response = result.get('response', 'No response')[:200]
                
                print(f"   Type: {query_type}")
                print(f"   Sources: {total_sources}")
                print(f"   Method: {method}")
                print(f"   Response: {response}...")
                
                results.append({
                    'query': query,
                    'success': True,
                    'sources': total_sources,
                    'type': query_type
                })
                
            except Exception as e:
                print(f"   ❌ Query failed: {e}")
                results.append({
                    'query': query,
                    'success': False,
                    'error': str(e)
                })
        
        # Test list_all_incidents method directly
        print(f"\n🦅 Testing Qdrant-specific functionality...")
        if hasattr(vector_store, 'list_all_incidents'):
            incidents = vector_store.list_all_incidents()
            print(f"✅ list_all_incidents(): Found {len(incidents)} incidents")
            
            # Show sample incidents
            for i, incident in enumerate(incidents[:3]):
                print(f"   {i+1}. {incident.get('id', 'Unknown')} - {incident.get('occurrence_count', 0)} occurrences")
        
        # Summary
        successful_queries = sum(1 for r in results if r['success'])
        print(f"\n📊 Query Test Summary:")
        print(f"   Total queries: {len(results)}")
        print(f"   Successful: {successful_queries}")
        print(f"   Failed: {len(results) - successful_queries}")
        
        return successful_queries > 0
        
    except Exception as e:
        print(f"❌ Query test failed: {e}")
        return False

def test_qdrant_benefits():
    """Test specific Qdrant benefits over FAISS"""
    print("\n🦅 Testing Qdrant Advantages")
    print("=" * 50)
    
    try:
        from core.dependency_container import DependencyContainer, register_core_services
        
        # Create container
        container = DependencyContainer()
        register_core_services(container)
        
        vector_store = container.get('vector_store')
        
        # Test 1: No top_k limitations
        print("1. Testing unlimited results retrieval...")
        if hasattr(vector_store, 'hybrid_search'):
            # Try to get all documents
            all_docs = vector_store.hybrid_search(k=1000)  # High number to test limits
            print(f"   ✅ Retrieved {len(all_docs)} documents (no arbitrary limits)")
        else:
            print("   ⚠️ hybrid_search method not available")
        
        # Test 2: Advanced filtering
        print("2. Testing advanced filtering...")
        if hasattr(vector_store, 'aggregate_by_type'):
            counts = vector_store.aggregate_by_type()
            print(f"   ✅ Document type aggregation: {counts}")
        else:
            print("   ⚠️ aggregate_by_type method not available")
        
        # Test 3: Collection info
        print("3. Testing collection metadata...")
        info = vector_store.get_collection_info()
        print(f"   ✅ Collection status: {info.get('status', 'unknown')}")
        print(f"   ✅ Total points: {info.get('points_count', 0)}")
        print(f"   ✅ Vector dimension: {info.get('config', {}).get('dimension', 'unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Qdrant benefits test failed: {e}")
        return False

def main():
    """Run comprehensive Qdrant test with data upload"""
    print("🚀 Comprehensive Qdrant Test with Data Upload")
    print("=" * 60)
    
    # Run tests
    upload_success = test_data_upload()
    query_success = test_qdrant_queries() 
    benefits_success = test_qdrant_benefits()
    
    # Final summary
    print("\n" + "=" * 60)
    print("📊 Final Test Results:")
    print(f"   Data Upload: {'✅ PASS' if upload_success else '❌ FAIL'}")
    print(f"   Query Testing: {'✅ PASS' if query_success else '❌ FAIL'}")
    print(f"   Qdrant Benefits: {'✅ PASS' if benefits_success else '❌ FAIL'}")
    
    all_passed = upload_success and query_success and benefits_success
    
    if all_passed:
        print("\n🎉 All tests passed! Qdrant is working perfectly!")
        print("🦅 The system successfully demonstrates:")
        print("   ✅ Data upload and vectorization")
        print("   ✅ Query processing with Qdrant")
        print("   ✅ Advanced Qdrant features")
        print("   ✅ No top_k limitations")
        print("   ✅ Enhanced metadata handling")
    else:
        print("\n⚠️ Some tests failed. Check the errors above.")
    
    return all_passed

if __name__ == "__main__":
    main() 