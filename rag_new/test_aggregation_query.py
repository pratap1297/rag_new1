#!/usr/bin/env python3
"""
Test Aggregation Query
Test the query engine's aggregation functionality directly
"""
import sys
from pathlib import Path

# Add rag_system/src to path
sys.path.insert(0, str(Path("rag_system/src")))

def test_aggregation_query():
    """Test the query engine aggregation directly"""
    
    print("🧪 TESTING QUERY ENGINE AGGREGATION")
    print("=" * 60)
    
    try:
        # Import required modules
        from core.dependency_container import DependencyContainer, register_core_services
        
        print("✅ Modules imported successfully")
        
        # Create and register services
        container = DependencyContainer()
        register_core_services(container)
        
        print("✅ Container and services registered")
        
        # Get query engine
        query_engine = container.get('query_engine')
        
        if not query_engine:
            print("❌ Query engine not found in container")
            return
        
        print(f"✅ Query engine retrieved: {type(query_engine)}")
        
        # Test aggregation query
        print("\n📊 Testing aggregation query...")
        query = "how many incidents are in system"
        
        print(f"🔍 Query: '{query}'")
        result = query_engine.process_query(query)
        
        print(f"\n📋 Query Engine Result:")
        print(f"   Query Type: {result.get('query_type', 'unknown')}")
        print(f"   Method: {result.get('method', 'unknown')}")
        print(f"   Confidence: {result.get('confidence_score', 'unknown')}")
        
        if 'aggregation_results' in result:
            print(f"   Aggregation Results: {result['aggregation_results']}")
        
        print(f"\n🎯 Response:")
        print(f"{result.get('response', 'No response')}")
        
        # Test if we get proper statistics
        response = result.get('response', '')
        if 'Document statistics' in response and 'Total documents' in response:
            print("\n✅ SUCCESS: Proper aggregation response generated!")
        else:
            print("\n❌ ISSUE: Response doesn't contain proper document statistics")
            print(f"   Actual response: {response}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_aggregation_query() 