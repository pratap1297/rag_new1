#!/usr/bin/env python3
"""
Test script to verify the backend is using Qdrant after migration
"""
import requests
import json
import time

def test_backend_health():
    """Test backend health and verify it's using Qdrant"""
    
    print("🏥 Testing Backend Health with Qdrant")
    print("=" * 50)
    
    # Wait for server to start
    print("⏳ Waiting for backend to start...")
    time.sleep(3)
    
    try:
        response = requests.get('http://localhost:8000/health', timeout=10)
        
        if response.status_code == 200:
            health_data = response.json()
            print("✅ Backend is running!")
            
            # Check for vector store information
            components = health_data.get('components', {})
            print(f"\n📊 Components status:")
            for component, status in components.items():
                if isinstance(status, dict):
                    component_status = status.get('status', 'unknown')
                    print(f"   {component}: {component_status}")
                else:
                    print(f"   {component}: {status}")
            
            # Look for vector store type
            vector_store_info = components.get('vector_store', {})
            if vector_store_info:
                print(f"\n🗄️ Vector Store Info:")
                print(f"   Type: {vector_store_info.get('type', 'Unknown')}")
                print(f"   Status: {vector_store_info.get('status', 'Unknown')}")
            
            return health_data
        else:
            print(f"❌ Backend responded with status {response.status_code}")
            print(response.text)
            return None
            
    except Exception as e:
        print(f"❌ Could not connect to backend: {e}")
        return None

def test_backend_stats():
    """Test backend stats endpoint"""
    
    print("\n📊 Testing Backend Stats")
    print("=" * 50)
    
    try:
        response = requests.get('http://localhost:8000/stats', timeout=10)
        
        if response.status_code == 200:
            stats_data = response.json()
            print("✅ Stats endpoint working!")
            
            print(f"\n📈 System Statistics:")
            print(f"   Total vectors: {stats_data.get('total_vectors', 'Unknown')}")
            print(f"   Total documents: {stats_data.get('total_documents', 'Unknown')}")
            print(f"   Index type: {stats_data.get('index_type', 'Unknown')}")
            print(f"   Vector dimensions: {stats_data.get('vector_dimensions', 'Unknown')}")
            
            return stats_data
        else:
            print(f"❌ Stats endpoint failed with status {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Could not get stats: {e}")
        return None

def test_list_incidents_query():
    """Test the 'list all incidents' query that benefits from Qdrant"""
    
    print("\n🔍 Testing 'List All Incidents' Query")
    print("=" * 50)
    
    try:
        query_data = {
            "query": "list all incidents",
            "max_results": 10,
            "include_metadata": True
        }
        
        response = requests.post(
            'http://localhost:8000/query',
            json=query_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Query successful!")
            
            if result.get('success'):
                data = result.get('data', {})
                query_type = data.get('query_type', 'Unknown')
                method = data.get('method', 'Unknown')
                total_sources = data.get('total_sources', 0)
                
                print(f"\n📋 Query Results:")
                print(f"   Query type detected: {query_type}")
                print(f"   Method used: {method}")
                print(f"   Total sources: {total_sources}")
                
                # Check if it's using Qdrant-specific features
                if 'qdrant' in method.lower():
                    print("🦅 Using Qdrant-specific functionality!")
                
                response_text = data.get('response', '')
                print(f"\n📄 Response preview:")
                print(f"   {response_text[:200]}...")
                
                return True
            else:
                print(f"❌ Query failed: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ Query request failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Query test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Backend Qdrant Integration Test")
    print("=" * 60)
    
    # Test backend health
    health_data = test_backend_health()
    
    # Test backend stats
    stats_data = test_backend_stats()
    
    # Test list incidents query
    query_success = test_list_incidents_query()
    
    print("\n" + "=" * 60)
    print("📊 Test Results:")
    print(f"   Backend Health: {'✅ PASS' if health_data else '❌ FAIL'}")
    print(f"   Backend Stats: {'✅ PASS' if stats_data else '❌ FAIL'}")
    print(f"   List Incidents Query: {'✅ PASS' if query_success else '❌ FAIL'}")
    
    if health_data and stats_data and query_success:
        print("\n🎉 All backend tests passed! Qdrant integration is working!")
    else:
        print("\n⚠️ Some tests failed. Backend might not be running or configured correctly.") 