#!/usr/bin/env python3
"""
Test script to verify Qdrant functionality after migration
"""
import sys
import os
sys.path.append('rag_system/src')

from storage.qdrant_store import QdrantVectorStore
from retrieval.qdrant_query_engine import QdrantQueryEngine

def test_qdrant_functionality():
    """Test Qdrant store and query engine functionality"""
    
    print("🦅 Testing Qdrant Integration")
    print("=" * 50)
    
    try:
        # Test Qdrant store initialization
        print("🔧 1. Testing Qdrant store initialization...")
        qdrant_store = QdrantVectorStore(
            url='localhost:6333',
            collection_name='rag_documents'
        )
        print("✅ Qdrant store initialized successfully")
        
        # Get collection info
        print("\n📊 2. Getting collection information...")
        info = qdrant_store.get_collection_info()
        print(f"   📈 Total points: {info.get('points_count', 0)}")
        print(f"   📏 Dimension: {info.get('config', {}).get('dimension', 'Unknown')}")
        print(f"   📐 Distance: {info.get('config', {}).get('distance', 'Unknown')}")
        
        # Test list all incidents functionality
        print("\n🔍 3. Testing 'list all incidents' functionality...")
        incidents = qdrant_store.list_all_incidents()
        print(f"   📊 Found {len(incidents)} incidents")
        
        if incidents:
            for i, incident in enumerate(incidents[:5], 1):
                incident_id = incident.get('id', 'Unknown')
                count = incident.get('occurrence_count', 0)
                sources = incident.get('sources', [])
                print(f"   {i}. {incident_id} - {count} occurrences from {len(sources)} sources")
        else:
            print("   ℹ️ No incidents found in vector store")
        
        # Test aggregation functionality
        print("\n📈 4. Testing aggregation by document type...")
        counts = qdrant_store.aggregate_by_type()
        print("   Document type counts:")
        for doc_type, count in counts.items():
            print(f"   - {doc_type}: {count}")
        
        # Test hybrid search
        print("\n🔍 5. Testing hybrid search...")
        results = qdrant_store.hybrid_search(
            filters={'doc_type': 'incident'},
            k=3
        )
        print(f"   📊 Hybrid search returned {len(results)} results")
        
        print("\n✅ All Qdrant functionality tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_query_engine():
    """Test Qdrant query engine functionality"""
    
    print("\n🧠 Testing Qdrant Query Engine")
    print("=" * 50)
    
    try:
        # Create mock dependencies for query engine
        class MockEmbedder:
            def embed_text(self, text):
                # Return a dummy embedding vector
                return [0.1] * 1024
        
        class MockLLMClient:
            def generate_response(self, query, context):
                return f"Mock response for: {query}"
        
        class MockConfig:
            pass
        
        # Initialize query engine
        qdrant_store = QdrantVectorStore(
            url='localhost:6333',
            collection_name='rag_documents'
        )
        
        query_engine = QdrantQueryEngine(
            qdrant_store=qdrant_store,
            embedder=MockEmbedder(),
            llm_client=MockLLMClient(),
            config=MockConfig()
        )
        
        print("✅ Query engine initialized successfully")
        
        # Test query type detection
        print("\n🔍 Testing query type detection...")
        test_queries = [
            "list all incidents",
            "show me incidents about database",
            "how many incidents are there",
            "what is ServiceNow"
        ]
        
        for query in test_queries:
            query_type = query_engine._detect_query_type(query)
            print(f"   '{query}' → {query_type}")
        
        print("\n✅ Query engine tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Query engine test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Qdrant Migration Verification Tests")
    print("=" * 60)
    
    # Test Qdrant functionality
    qdrant_success = test_qdrant_functionality()
    
    # Test query engine
    engine_success = test_query_engine()
    
    print("\n" + "=" * 60)
    print("📊 Test Results:")
    print(f"   Qdrant Store: {'✅ PASS' if qdrant_success else '❌ FAIL'}")
    print(f"   Query Engine: {'✅ PASS' if engine_success else '❌ FAIL'}")
    
    if qdrant_success and engine_success:
        print("\n🎉 All tests passed! Qdrant migration is successful!")
    else:
        print("\n⚠️ Some tests failed. Please check the errors above.") 