#!/usr/bin/env python3
"""
Test Aggregation Debug
Debug the exact structure of aggregation responses from query engine
"""
import sys
from pathlib import Path
import json

# Add rag_system/src to path
sys.path.insert(0, str(Path("rag_system/src")))

def debug_aggregation_response():
    """Debug the aggregation response structure"""
    
    print("🐛 DEBUGGING AGGREGATION RESPONSE STRUCTURE")
    print("=" * 70)
    
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
        print(f"✅ Query engine retrieved: {type(query_engine)}")
        
        print("\n📊 Testing aggregation query...")
        
        # Test the aggregation query
        query = 'how many incidents are in system'
        print(f"🔍 Query: '{query}'")
        
        result = query_engine.process_query(
            query,
            top_k=5,
            conversation_context=""
        )
        
        print("\n🔧 RESULT STRUCTURE:")
        print("=" * 50)
        
        if result:
            print(f"Type: {type(result)}")
            print(f"Keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            
            # Print the complete structure 
            print("\n📋 Complete Result:")
            print(json.dumps(result, indent=2, default=str))
            
            # Check specific fields
            print("\n🔍 Key Analysis:")
            if isinstance(result, dict):
                for key, value in result.items():
                    print(f"  {key}: {type(value)} = {value}")
            
        else:
            print("❌ Result is None or empty")
        
        print("\n" + "=" * 70)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_aggregation_response() 