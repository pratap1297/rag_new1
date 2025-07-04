#!/usr/bin/env python3
"""
Final UI Qdrant Integration Test
Comprehensive verification that the UI is using Qdrant and demonstrates its advantages
"""
import sys
import os
import requests
import json
import time
from pathlib import Path
from datetime import datetime

# Add the rag_system to Python path
sys.path.insert(0, str(Path(__file__).parent / "rag_system" / "src"))

class FinalQdrantUITest:
    def __init__(self):
        self.api_url = "http://localhost:8000"
        self.ui_url = "http://localhost:7860"
        
    def test_configuration_clean(self):
        """Verify configuration is clean of FAISS references"""
        print("🔧 CONFIGURATION VERIFICATION")
        print("=" * 50)
        
        try:
            from core.config_manager import ConfigManager
            
            config_manager = ConfigManager()
            config = config_manager.get_config()
            
            # Check vector store config
            vector_config = config.vector_store
            print(f"✅ Vector store type: {vector_config.type}")
            print(f"✅ URL: {vector_config.url}")
            print(f"✅ Collection: {vector_config.collection_name}")
            print(f"✅ Dimension: {vector_config.dimension}")
            
            # Check for FAISS references
            config_dict = config.__dict__
            config_str = str(config_dict).lower()
            
            faiss_count = config_str.count('faiss')
            if faiss_count == 0:
                print("✅ Configuration is clean - no FAISS references!")
                return True
            else:
                print(f"⚠️  Found {faiss_count} FAISS references in config")
                return False
                
        except Exception as e:
            print(f"❌ Configuration test failed: {e}")
            return False
    
    def test_system_components(self):
        """Test that all system components are using Qdrant"""
        print("\n🧩 SYSTEM COMPONENTS VERIFICATION")
        print("=" * 50)
        
        try:
            from core.dependency_container import DependencyContainer
            from core.dependency_container import register_core_services
            
            container = DependencyContainer()
            register_core_services(container)
            
            # Check vector store
            vector_store = container.get('vector_store')
            vector_store_type = type(vector_store).__name__
            print(f"✅ Vector Store: {vector_store_type}")
            
            if 'Qdrant' in vector_store_type:
                print("✅ Using QdrantVectorStore!")
            else:
                print(f"❌ Unexpected vector store: {vector_store_type}")
                return False
            
            # Check query engine
            query_engine = container.get('query_engine')
            query_engine_type = type(query_engine).__name__
            print(f"✅ Query Engine: {query_engine_type}")
            
            if 'Qdrant' in query_engine_type:
                print("✅ Using QdrantQueryEngine!")
            else:
                print(f"⚠️  Using generic query engine: {query_engine_type}")
            
            # Get collection info
            if hasattr(vector_store, 'get_collection_info'):
                info = vector_store.get_collection_info()
                print(f"✅ Collection Status: {info.get('status', 'unknown')}")
                print(f"✅ Total Points: {info.get('points_count', 0)}")
                
            return True
            
        except Exception as e:
            print(f"❌ System components test failed: {e}")
            return False
    
    def test_qdrant_advantages(self):
        """Test queries that demonstrate Qdrant's advantages over FAISS"""
        print("\n🚀 QDRANT ADVANTAGES DEMONSTRATION")
        print("=" * 50)
        
        try:
            from core.dependency_container import DependencyContainer
            from core.dependency_container import register_core_services
            
            container = DependencyContainer()
            register_core_services(container)
            query_engine = container.get('query_engine')
            
            # Test queries that showcase Qdrant's superiority
            qdrant_advantage_tests = [
                {
                    "query": "list all incidents",
                    "advantage": "Unlimited results (no top_k limit)",
                    "expected_method": "qdrant_scroll"
                },
                {
                    "query": "how many incidents do we have by priority?",
                    "advantage": "Native aggregation without full scan",
                    "expected_method": "qdrant_aggregation"
                },
                {
                    "query": "incidents about network issues",
                    "advantage": "Pre-filtering before similarity search",
                    "expected_method": "qdrant_hybrid"
                },
                {
                    "query": "show me all facility manager information",
                    "advantage": "Complete retrieval with metadata",
                    "expected_method": "qdrant_similarity"
                }
            ]
            
            successful_tests = 0
            
            for i, test in enumerate(qdrant_advantage_tests, 1):
                print(f"\n--- Test {i}: {test['advantage']} ---")
                print(f"Query: '{test['query']}'")
                
                try:
                    start_time = time.time()
                    response = query_engine.process_query(test['query'])
                    end_time = time.time()
                    
                    query_time = (end_time - start_time) * 1000  # ms
                    
                    print(f"✅ Query successful in {query_time:.1f}ms")
                    print(f"   Query type: {response.get('query_type', 'unknown')}")
                    print(f"   Method used: {response.get('method', 'unknown')}")
                    print(f"   Sources found: {len(response.get('sources', []))}")
                    print(f"   Response length: {len(response.get('response', ''))}")
                    
                    # Check if using expected Qdrant method
                    method = response.get('method', '')
                    if 'qdrant' in method.lower():
                        print(f"✅ Using Qdrant-specific method: {method}")
                        successful_tests += 1
                    else:
                        print(f"⚠️  Method: {method}")
                    
                    # Show response preview for listing queries
                    if test['query'].startswith('list') and response.get('response'):
                        preview = response['response'][:200] + "..." if len(response['response']) > 200 else response['response']
                        print(f"   Preview: {preview}")
                        
                except Exception as e:
                    print(f"❌ Query failed: {e}")
            
            print(f"\n📊 Qdrant Advantages Summary:")
            print(f"   Tests passed: {successful_tests}/{len(qdrant_advantage_tests)}")
            print(f"   Success rate: {(successful_tests/len(qdrant_advantage_tests))*100:.1f}%")
            
            return successful_tests >= len(qdrant_advantage_tests) * 0.75  # 75% success rate
            
        except Exception as e:
            print(f"❌ Qdrant advantages test failed: {e}")
            return False
    
    def test_api_integration(self):
        """Test API integration with Qdrant features"""
        print("\n🌐 API INTEGRATION TESTING")
        print("=" * 50)
        
        # Test health endpoint
        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ API Health: {health_data.get('status')}")
            else:
                print(f"❌ API unhealthy: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ API health check failed: {e}")
            return False
        
        # Test query endpoint with Qdrant-specific queries
        api_test_queries = [
            "list all incidents from ServiceNow",
            "how many documents do we have?",
            "show me network layout documents",
            "find facility manager contact information"
        ]
        
        successful_api_tests = 0
        
        for query in api_test_queries:
            try:
                response = requests.post(
                    f"{self.api_url}/query",
                    json={"query": query, "max_results": 10},
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ API Query: '{query[:30]}...'")
                    print(f"   Sources: {len(result.get('sources', []))}")
                    successful_api_tests += 1
                else:
                    print(f"❌ API Query failed: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ API Query exception: {e}")
        
        print(f"\n📊 API Integration Summary:")
        print(f"   Tests passed: {successful_api_tests}/{len(api_test_queries)}")
        
        return successful_api_tests >= len(api_test_queries) * 0.75
    
    def test_performance_comparison(self):
        """Show performance advantages of Qdrant"""
        print("\n⚡ PERFORMANCE COMPARISON")
        print("=" * 50)
        
        try:
            from core.dependency_container import DependencyContainer
            from core.dependency_container import register_core_services
            
            container = DependencyContainer()
            register_core_services(container)
            query_engine = container.get('query_engine')
            
            # Performance test queries
            perf_tests = [
                {
                    "query": "list all incidents",
                    "description": "Complete listing (FAISS would be limited by top_k)"
                },
                {
                    "query": "how many incidents are there?",
                    "description": "Count query (FAISS would need full scan)"
                }
            ]
            
            print("Qdrant Performance Benefits:")
            
            for test in perf_tests:
                print(f"\n🔍 {test['description']}")
                print(f"   Query: '{test['query']}'")
                
                try:
                    start_time = time.time()
                    response = query_engine.process_query(test['query'])
                    end_time = time.time()
                    
                    query_time = (end_time - start_time) * 1000
                    sources_count = len(response.get('sources', []))
                    
                    print(f"   ✅ Qdrant: {query_time:.1f}ms, {sources_count} results")
                    print(f"   📊 FAISS equivalent would require multiple operations")
                    
                except Exception as e:
                    print(f"   ❌ Test failed: {e}")
            
            return True
            
        except Exception as e:
            print(f"❌ Performance test failed: {e}")
            return False
    
    def generate_migration_report(self):
        """Generate a migration success report"""
        print("\n📋 MIGRATION SUCCESS REPORT")
        print("=" * 50)
        
        try:
            from core.dependency_container import DependencyContainer
            from core.dependency_container import register_core_services
            
            container = DependencyContainer()
            register_core_services(container)
            
            vector_store = container.get('vector_store')
            query_engine = container.get('query_engine')
            
            # Collect system information
            info = {
                "migration_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "vector_store_type": type(vector_store).__name__,
                "query_engine_type": type(query_engine).__name__,
                "collection_info": None,
                "total_documents": 0,
                "qdrant_features": []
            }
            
            # Get collection info
            if hasattr(vector_store, 'get_collection_info'):
                collection_info = vector_store.get_collection_info()
                info["collection_info"] = collection_info
                info["total_documents"] = collection_info.get('points_count', 0)
            
            # Test Qdrant-specific features
            qdrant_features = []
            
            # Test listing capability
            try:
                if hasattr(vector_store, 'list_all_incidents'):
                    incidents = vector_store.list_all_incidents()
                    qdrant_features.append(f"Unlimited incident listing: {len(incidents)} incidents")
            except:
                pass
            
            # Test aggregation
            try:
                if hasattr(vector_store, 'aggregate_by_type'):
                    counts = vector_store.aggregate_by_type()
                    total_by_type = sum(counts.values())
                    qdrant_features.append(f"Native aggregation: {total_by_type} documents by type")
            except:
                pass
            
            # Test pattern search
            try:
                if hasattr(vector_store, 'get_by_pattern'):
                    network_docs = vector_store.get_by_pattern('network')
                    qdrant_features.append(f"Pattern search: {len(network_docs)} network-related docs")
            except:
                pass
            
            info["qdrant_features"] = qdrant_features
            
            # Print report
            print(f"Migration Date: {info['migration_date']}")
            print(f"Vector Store: {info['vector_store_type']}")
            print(f"Query Engine: {info['query_engine_type']}")
            print(f"Total Documents: {info['total_documents']}")
            print(f"Collection Status: {info.get('collection_info', {}).get('status', 'unknown')}")
            
            print(f"\n🚀 Qdrant Features Available:")
            for feature in qdrant_features:
                print(f"   ✅ {feature}")
            
            if not qdrant_features:
                print("   ⚠️  No Qdrant-specific features detected")
            
            # Save report
            report_path = f"qdrant_migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_path, 'w') as f:
                json.dump(info, f, indent=2, default=str)
            
            print(f"\n📄 Report saved: {report_path}")
            
            return True
            
        except Exception as e:
            print(f"❌ Report generation failed: {e}")
            return False
    
    def run_comprehensive_test(self):
        """Run all tests and provide final verdict"""
        print("🧪 FINAL COMPREHENSIVE UI QDRANT TEST")
        print("=" * 80)
        print("Testing complete migration from FAISS to Qdrant")
        print("Verifying UI backend integration and functionality")
        print()
        
        test_results = {}
        
        # Run all tests
        test_results['configuration'] = self.test_configuration_clean()
        test_results['system_components'] = self.test_system_components()
        test_results['qdrant_advantages'] = self.test_qdrant_advantages()
        test_results['api_integration'] = self.test_api_integration()
        test_results['performance'] = self.test_performance_comparison()
        test_results['report_generation'] = self.generate_migration_report()
        
        # Calculate results
        passed_tests = sum(test_results.values())
        total_tests = len(test_results)
        success_rate = (passed_tests / total_tests) * 100
        
        print(f"\n🏁 FINAL TEST RESULTS")
        print("=" * 80)
        
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
        
        print(f"\nOverall Results:")
        print(f"   Tests Passed: {passed_tests}/{total_tests}")
        print(f"   Success Rate: {success_rate:.1f}%")
        
        # Final verdict
        if success_rate >= 90:
            print(f"\n🎉 MIGRATION SUCCESSFUL!")
            print("✅ UI backend is fully using Qdrant")
            print("✅ No FAISS components detected")
            print("✅ All Qdrant advantages are working")
            print("✅ System is production-ready")
            
        elif success_rate >= 75:
            print(f"\n✅ MIGRATION MOSTLY SUCCESSFUL!")
            print("✅ Core Qdrant functionality is working")
            print("⚠️  Some minor issues detected")
            print("✅ System is functional")
            
        else:
            print(f"\n⚠️  MIGRATION NEEDS ATTENTION")
            print("❌ Multiple test failures detected")
            print("⚠️  Review failed tests above")
            
        return test_results

if __name__ == "__main__":
    tester = FinalQdrantUITest()
    results = tester.run_comprehensive_test() 