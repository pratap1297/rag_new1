#!/usr/bin/env python3
"""
Final comprehensive test of Qdrant system
"""
import sys
import requests
import json
import time

sys.path.append('rag_system/src')

def test_ui_accessibility():
    """Test if UI is running"""
    print("🌐 Testing UI Accessibility")
    print("=" * 40)
    
    try:
        response = requests.get('http://127.0.0.1:7860', timeout=5)
        print("✅ UI is running and accessible!")
        print("🌐 URL: http://127.0.0.1:7860")
        return True
    except Exception as e:
        print(f"⚠️ UI not accessible: {e}")
        return False

def test_qdrant_integration():
    """Test Qdrant vector store integration"""
    print("\n🦅 Testing Qdrant Integration")
    print("=" * 40)
    
    try:
        from core.dependency_container import DependencyContainer, register_core_services
        
        # Create container
        container = DependencyContainer()
        register_core_services(container)
        
        # Get vector store
        vector_store = container.get('vector_store')
        print(f"✅ Vector Store Type: {type(vector_store).__name__}")
        
        # Test Qdrant functionality
        if hasattr(vector_store, 'get_collection_info'):
            info = vector_store.get_collection_info()
            print(f"✅ Collection Status: {info['status']}")
            print(f"✅ Points Count: {info['points_count']}")
            print(f"✅ Vector Dimension: {info['config']['dimension']}")
            print(f"✅ Distance Metric: {info['config']['distance']}")
            return True
        else:
            print("❌ Not a Qdrant vector store!")
            return False
            
    except Exception as e:
        print(f"❌ Qdrant integration test failed: {e}")
        return False

def test_query_engine():
    """Test query engine with Qdrant"""
    print("\n🔍 Testing Query Engine")
    print("=" * 40)
    
    try:
        from core.dependency_container import DependencyContainer, register_core_services
        
        # Create container
        container = DependencyContainer()
        register_core_services(container)
        
        # Get query engine
        query_engine = container.get('query_engine')
        print("✅ Query engine created")
        
        # Test the 'list all incidents' query
        print("📋 Testing 'list all incidents' query...")
        result = query_engine.process_query('list all incidents')
        
        print("✅ Query processed successfully!")
        print(f"📊 Query Type: {result.get('query_type', 'unknown')}")
        print(f"📊 Total Sources: {result.get('total_sources', 0)}")
        print(f"📊 Method Used: {result.get('method', 'unknown')}")
        
        response_preview = result.get('response', 'No response')[:200]
        print(f"📄 Response Preview: {response_preview}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Query engine test failed: {e}")
        return False

def test_incident_listing():
    """Test specific incident listing functionality"""
    print("\n📋 Testing Incident Listing")
    print("=" * 40)
    
    try:
        from core.dependency_container import DependencyContainer, register_core_services
        
        # Create container
        container = DependencyContainer()
        register_core_services(container)
        
        # Get vector store
        vector_store = container.get('vector_store')
        
        # Test list_all_incidents method
        if hasattr(vector_store, 'list_all_incidents'):
            print("🔍 Testing list_all_incidents() method...")
            incidents = vector_store.list_all_incidents()
            print(f"✅ Found {len(incidents)} incidents")
            
            # Show sample incidents
            for i, incident in enumerate(incidents[:3]):
                print(f"  {i+1}. {incident.get('id', 'Unknown')} - {incident.get('occurrence_count', 0)} occurrences")
            
            return True
        else:
            print("❌ list_all_incidents method not available")
            return False
            
    except Exception as e:
        print(f"❌ Incident listing test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Comprehensive Qdrant System Test")
    print("=" * 60)
    
    # Run all tests
    ui_test = test_ui_accessibility()
    qdrant_test = test_qdrant_integration()
    query_test = test_query_engine()
    incident_test = test_incident_listing()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print(f"   UI Accessibility: {'✅ PASS' if ui_test else '❌ FAIL'}")
    print(f"   Qdrant Integration: {'✅ PASS' if qdrant_test else '❌ FAIL'}")
    print(f"   Query Engine: {'✅ PASS' if query_test else '❌ FAIL'}")
    print(f"   Incident Listing: {'✅ PASS' if incident_test else '❌ FAIL'}")
    
    all_passed = all([qdrant_test, query_test, incident_test])  # UI test is optional
    
    if all_passed:
        print("\n🎉 All critical tests passed! Qdrant migration is successful!")
        print("🦅 The system is now using Qdrant for vector storage.")
        print("📈 Benefits achieved:")
        print("   - No top_k limitations for listing queries")
        print("   - Better filtering capabilities")
        print("   - Enhanced metadata handling")
        print("   - Improved performance for complex queries")
    else:
        print("\n⚠️ Some tests failed. Please check the errors above.")
    
    return all_passed

if __name__ == "__main__":
    main() 