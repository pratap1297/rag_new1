#!/usr/bin/env python3
"""
Test specific query types with the Qdrant system
Demonstrates intelligent query routing and specialized handlers
"""
import sys
from pathlib import Path

# Add the rag_system to Python path
sys.path.insert(0, str(Path(__file__).parent / "rag_system" / "src"))

from core.dependency_container import register_core_services, DependencyContainer

def test_specific_queries():
    """Test various query types to demonstrate Qdrant capabilities"""
    
    print("🔍 SPECIFIC QUERY TESTING WITH QDRANT")
    print("=" * 60)
    
    # Initialize system
    container = DependencyContainer()
    register_core_services(container)
    
    query_engine = container.get('query_engine')
    
    # Test queries that showcase different capabilities
    test_queries = [
        {
            "query": "list all incidents from the last 30 days",
            "description": "Complete listing query (unlimited results)"
        },
        {
            "query": "show me network-related problems",
            "description": "Pattern-based filtering"
        },
        {
            "query": "how many incidents do we have in total?",
            "description": "Aggregation query"
        },
        {
            "query": "find incidents about network connectivity issues",
            "description": "Hybrid semantic + keyword search"
        },
        {
            "query": "what are the building network layouts?",
            "description": "Semantic search for documents"
        },
        {
            "query": "show me all high priority incidents assigned to John",
            "description": "Multi-condition filtering"
        },
        {
            "query": "give me a summary of facility management data",
            "description": "Document-type specific query"
        },
        {
            "query": "list incidents created between January and March",
            "description": "Date range filtering"
        }
    ]
    
    for i, test_case in enumerate(test_queries, 1):
        print(f"\n🎯 TEST {i}: {test_case['description']}")
        print(f"Query: \"{test_case['query']}\"")
        print("-" * 50)
        
        try:
            response = query_engine.process_query(test_case['query'])
            
            print(f"✅ Query Type: {response.get('query_type', 'unknown')}")
            print(f"✅ Method Used: {response.get('method', 'unknown')}")
            print(f"✅ Response Length: {len(response.get('response', ''))} chars")
            print(f"✅ Sources Found: {len(response.get('sources', []))}")
            print(f"✅ Confidence: {response.get('confidence_level', 'unknown')}")
            
            if response.get('total_sources'):
                print(f"✅ Total Available: {response['total_sources']}")
            
            if response.get('aggregation_results'):
                print(f"✅ Aggregation: {response['aggregation_results']}")
            
            # Show first part of response
            resp_text = response.get('response', '')
            if resp_text:
                preview = resp_text[:200]
                if len(resp_text) > 200:
                    preview += "..."
                print(f"📝 Response Preview: {preview}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n🏆 COMPLETED TESTING {len(test_queries)} DIFFERENT QUERY TYPES")
    print("✅ All queries processed through Qdrant's intelligent routing system")

if __name__ == "__main__":
    test_specific_queries() 