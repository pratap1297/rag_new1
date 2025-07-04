#!/usr/bin/env python3
"""
Test Frontend API with Qdrant
Verifies the UI backend is using Qdrant and test various query types
"""
import requests
import json
import time
from datetime import datetime

class FrontendAPITester:
    def __init__(self, api_url="http://localhost:8000"):
        self.api_url = api_url
        self.ui_url = "http://localhost:7860"  # Default Gradio port
        
    def test_backend_health(self):
        """Test if backend API is running"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ Backend API is healthy")
                print(f"   Status: {health_data.get('status', 'unknown')}")
                print(f"   Timestamp: {health_data.get('timestamp', 'unknown')}")
                return True
            else:
                print(f"❌ Backend API unhealthy: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Backend API not accessible: {e}")
            return False
    
    def test_ui_health(self):
        """Test if UI is running"""
        try:
            response = requests.get(self.ui_url, timeout=5)
            if response.status_code == 200:
                print(f"✅ Frontend UI is accessible at {self.ui_url}")
                return True
            else:
                print(f"❌ Frontend UI not accessible: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Frontend UI not accessible: {e}")
            return False
    
    def test_vector_store_status(self):
        """Test vector store status to confirm it's Qdrant"""
        try:
            response = requests.get(f"{self.api_url}/vector-store/stats", timeout=10)
            if response.status_code == 200:
                stats = response.json()
                print(f"✅ Vector store stats retrieved:")
                print(f"   Type: {stats.get('store_type', 'unknown')}")
                print(f"   Total vectors: {stats.get('total_vectors', 0)}")
                print(f"   Collection status: {stats.get('collection_status', 'unknown')}")
                print(f"   Implementation: {stats.get('implementation', 'unknown')}")
                
                # Check if it's using Qdrant
                if 'qdrant' in str(stats).lower():
                    print("✅ Confirmed: System is using Qdrant!")
                    return True
                else:
                    print("⚠️  Cannot confirm Qdrant usage from stats")
                    return False
            else:
                print(f"❌ Cannot get vector store stats: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error getting vector store stats: {e}")
            return False
    
    def test_query_api(self):
        """Test query API with different query types"""
        test_queries = [
            {
                "query": "list all incidents",
                "expected_type": "listing",
                "description": "Test listing query (Qdrant advantage)"
            },
            {
                "query": "how many incidents do we have?",
                "expected_type": "aggregation", 
                "description": "Test aggregation query (Qdrant advantage)"
            },
            {
                "query": "show me network layout information",
                "expected_type": "semantic",
                "description": "Test semantic search"
            },
            {
                "query": "incidents about network",
                "expected_type": "filtered",
                "description": "Test filtered search (Qdrant advantage)"
            }
        ]
        
        print(f"\n🔍 Testing Query API Endpoints")
        print("=" * 50)
        
        successful_queries = 0
        total_queries = len(test_queries)
        
        for i, test_case in enumerate(test_queries, 1):
            print(f"\n--- Query {i}/{total_queries}: {test_case['description']} ---")
            print(f"Query: '{test_case['query']}'")
            
            try:
                # Test the query endpoint
                payload = {
                    "query": test_case['query'],
                    "max_results": 5
                }
                
                response = requests.post(
                    f"{self.api_url}/query", 
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Query successful")
                    print(f"   Response length: {len(result.get('response', ''))} chars")
                    print(f"   Sources found: {len(result.get('sources', []))}")
                    print(f"   Confidence: {result.get('confidence_level', 'unknown')}")
                    print(f"   Method used: {result.get('metadata', {}).get('method_used', 'unknown')}")
                    
                    # Check if using Qdrant-specific methods
                    method_used = result.get('metadata', {}).get('method_used', '')
                    if 'qdrant' in method_used.lower():
                        print(f"✅ Confirmed: Using Qdrant method '{method_used}'")
                    
                    successful_queries += 1
                    
                    # Show preview of response
                    response_preview = result.get('response', '')[:200]
                    if response_preview:
                        print(f"   Preview: {response_preview}...")
                        
                else:
                    print(f"❌ Query failed: HTTP {response.status_code}")
                    try:
                        error_detail = response.json()
                        print(f"   Error: {error_detail.get('detail', 'No details')}")
                    except:
                        print(f"   Error: {response.text[:200]}")
                        
            except Exception as e:
                print(f"❌ Query exception: {e}")
        
        print(f"\n📊 Query Test Summary")
        print(f"   Successful: {successful_queries}/{total_queries}")
        print(f"   Success rate: {(successful_queries/total_queries)*100:.1f}%")
        
        return successful_queries == total_queries
    
    def test_document_management(self):
        """Test document management endpoints"""
        print(f"\n📄 Testing Document Management")
        print("=" * 50)
        
        try:
            # Get document list
            response = requests.get(f"{self.api_url}/documents", timeout=10)
            if response.status_code == 200:
                docs = response.json()
                print(f"✅ Retrieved document list: {len(docs)} documents")
                for doc in docs[:3]:  # Show first 3
                    print(f"   - {doc.get('filename', 'Unknown')}")
                if len(docs) > 3:
                    print(f"   ... and {len(docs) - 3} more")
                return True
            else:
                print(f"❌ Cannot get document list: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error getting documents: {e}")
            return False
    
    def test_vector_search(self):
        """Test vector search endpoints"""
        print(f"\n🔍 Testing Vector Search")
        print("=" * 50)
        
        try:
            # Test vector search
            payload = {
                "search_term": "network",
                "limit": 10
            }
            
            response = requests.post(
                f"{self.api_url}/vector-store/search",
                json=payload,
                timeout=15
            )
            
            if response.status_code == 200:
                results = response.json()
                print(f"✅ Vector search successful")
                print(f"   Results found: {len(results.get('results', []))}")
                print(f"   Search term: network")
                
                # Check if results indicate Qdrant usage
                if results.get('vector_store_type') == 'qdrant':
                    print("✅ Confirmed: Vector search using Qdrant")
                
                return True
            else:
                print(f"❌ Vector search failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Vector search error: {e}")
            return False
    
    def run_full_test(self):
        """Run all tests"""
        print("🧪 FRONTEND API TESTING WITH QDRANT")
        print("=" * 60)
        print(f"Backend API: {self.api_url}")
        print(f"Frontend UI: {self.ui_url}")
        print(f"Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        test_results = {
            'backend_health': self.test_backend_health(),
            'ui_health': self.test_ui_health(),
            'vector_store_status': self.test_vector_store_status(),
            'query_api': self.test_query_api(),
            'document_management': self.test_document_management(),
            'vector_search': self.test_vector_search()
        }
        
        print(f"\n🏁 FINAL TEST RESULTS")
        print("=" * 60)
        
        passed = sum(test_results.values())
        total = len(test_results)
        
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
        
        print(f"\nOverall: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED! Frontend is working with Qdrant!")
        elif passed >= total * 0.8:
            print("⚠️  Most tests passed, system is mostly functional")
        else:
            print("❌ Multiple test failures, system needs attention")
        
        return test_results

if __name__ == "__main__":
    tester = FrontendAPITester()
    results = tester.run_full_test() 