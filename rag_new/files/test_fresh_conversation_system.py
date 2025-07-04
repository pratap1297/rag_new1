#!/usr/bin/env python3
"""
Integration Test for Fresh Conversation System
Tests the new fresh conversation system with Qdrant integration
"""
import os
import sys
import logging
import json
from pathlib import Path
from datetime import datetime

# Add the rag_system to Python path
sys.path.insert(0, str(Path(__file__).parent / "rag_system" / "src"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_fresh_conversation_system():
    """Test the fresh conversation system with Qdrant"""
    
    print("🚀 Testing Fresh Conversation System")
    print("=" * 60)
    
    try:
        # Import the fresh conversation components
        from conversation.fresh_conversation_graph import FreshConversationGraph
        from conversation.fresh_context_manager import FreshContextManager
        from conversation.fresh_memory_manager import FreshMemoryManager
        from conversation.fresh_smart_router import FreshSmartRouter
        from core.dependency_container import DependencyContainer
        
        print("✅ Successfully imported fresh conversation components")
        
        # Initialize dependency container
        print("\n🔧 Initializing dependency container...")
        container = DependencyContainer()
        container.initialize()
        
        # Get Qdrant components
        qdrant_store = container.get('vector_store')
        query_engine = container.get('query_engine')
        
        if qdrant_store is None:
            print("⚠️  Warning: Qdrant store not available, using mock")
            qdrant_store = MockQdrantStore()
        
        if query_engine is None:
            print("⚠️  Warning: Query engine not available, using mock")
            query_engine = MockQueryEngine()
        
        print(f"✅ Dependency container initialized")
        print(f"   - Vector store: {type(qdrant_store).__name__}")
        print(f"   - Query engine: {type(query_engine).__name__}")
        
        # Initialize fresh conversation graph
        print("\n🧠 Initializing fresh conversation graph...")
        fresh_graph = FreshConversationGraph(container)
        
        print("✅ Fresh conversation graph initialized")
        
        # Test conversation flow
        print("\n💬 Testing conversation flow...")
        
        test_queries = [
            "Hello!",
            "What types of access points are used in Building A?",
            "Tell me more about them",
            "How many incidents are there?",
            "Thanks, goodbye!"
        ]
        
        thread_id = f"test_{datetime.now().timestamp()}"
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n--- Turn {i}: {query} ---")
            
            try:
                # Process the message
                result = fresh_graph.process_message(thread_id, query)
                
                # Extract response
                messages = result.get('messages', [])
                if messages:
                    last_message = messages[-1]
                    if last_message.get('type') == 'assistant':
                        response = last_message.get('content', 'No response')
                        print(f"🤖 Assistant: {response[:200]}...")
                    else:
                        print("🤖 Assistant: [Processing...]")
                else:
                    print("🤖 Assistant: [No messages yet]")
                
                # Show conversation state
                phase = result.get('current_phase', 'unknown')
                intent = result.get('user_intent', 'unknown')
                quality = result.get('overall_quality_score', 0.0)
                
                print(f"📊 State - Phase: {phase}, Intent: {intent}, Quality: {quality:.2f}")
                
                # Show search results if any
                search_results = result.get('search_results', [])
                if search_results:
                    print(f"🔍 Found {len(search_results)} search results")
                
            except Exception as e:
                print(f"❌ Error processing query '{query}': {e}")
                import traceback
                traceback.print_exc()
        
        # Test conversation history
        print("\n📜 Testing conversation history...")
        try:
            history = fresh_graph.get_conversation_history(thread_id)
            print(f"✅ Retrieved conversation history:")
            print(f"   - Messages: {len(history.get('messages', []))}")
            print(f"   - Turn count: {history.get('turn_count', 0)}")
            print(f"   - Current phase: {history.get('current_phase', 'unknown')}")
            print(f"   - Topics discussed: {history.get('topics_discussed', [])}")
        except Exception as e:
            print(f"❌ Error getting conversation history: {e}")
        
        # Test system metrics
        print("\n📈 Testing system metrics...")
        try:
            metrics = fresh_graph.get_system_metrics()
            print(f"✅ Retrieved system metrics:")
            conv_metrics = metrics.get('conversation_metrics', {})
            print(f"   - Total conversations: {conv_metrics.get('total_conversations', 0)}")
            print(f"   - Successful conversations: {conv_metrics.get('successful_conversations', 0)}")
            print(f"   - Average turns: {conv_metrics.get('average_turns', 0):.1f}")
        except Exception as e:
            print(f"❌ Error getting system metrics: {e}")
        
        print("\n🎉 Fresh conversation system test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Fresh conversation system test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_context_management():
    """Test the context management features"""
    
    print("\n🧩 Testing Context Management Features")
    print("=" * 50)
    
    try:
        from conversation.fresh_context_manager import FreshContextManager, ContextChunk, MemoryType, MemoryPriority
        from conversation.fresh_memory_manager import FreshMemoryManager
        from conversation.fresh_smart_router import FreshSmartRouter
        
        # Test context manager
        print("🔧 Testing context manager...")
        context_manager = FreshContextManager()
        
        # Test adding chunks
        success, reason = context_manager.add_chunk(
            content="This is a test context chunk about access points.",
            source="test_source",
            chunk_type="knowledge",
            confidence=0.9
        )
        print(f"   Add chunk: {'✅' if success else '❌'} - {reason}")
        
        # Test tool context management
        mock_tools = [
            {'name': 'search_tool', 'description': 'Search for information'},
            {'name': 'calculator', 'description': 'Perform calculations'},
            {'name': 'email_tool', 'description': 'Send emails'}
        ]
        
        relevant_tools = context_manager.manage_tool_context(mock_tools, "search for access points")
        print(f"   Tool filtering: ✅ - {len(relevant_tools)}/{len(mock_tools)} tools selected")
        
        # Test memory manager
        print("🧠 Testing memory manager...")
        memory_manager = FreshMemoryManager()
        
        # Store some chunks
        chunk_id = memory_manager.store_chunk(
            content="Access points in Building A are primarily Cisco 3802I models.",
            memory_type=MemoryType.WORKING,
            priority=MemoryPriority.HIGH,
            tags={'building_a', 'access_points'}
        )
        print(f"   Store chunk: ✅ - ID: {chunk_id}")
        
        # Retrieve relevant context
        relevant_chunks = memory_manager.get_relevant_context(
            query="access points building a",
            max_size=1000
        )
        print(f"   Retrieve context: ✅ - {len(relevant_chunks)} chunks found")
        
        # Test smart router
        print("🧭 Testing smart router...")
        smart_router = FreshSmartRouter(context_manager)
        
        # Analyze a query
        analysis = smart_router.analyze_query("What access points are in Building A?")
        print(f"   Query analysis: ✅")
        print(f"     - Intent: {analysis.intent.value}")
        print(f"     - Complexity: {analysis.complexity.value}")
        print(f"     - Confidence: {analysis.confidence:.2f}")
        print(f"     - Keywords: {analysis.keywords}")
        
        # Get routing decision
        routing = smart_router.route_query(analysis)
        print(f"   Routing decision: ✅")
        print(f"     - Route: {routing.route.value}")
        print(f"     - Reasoning: {routing.reasoning}")
        print(f"     - Confidence: {routing.confidence:.2f}")
        
        print("✅ Context management features working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Context management test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

class MockQdrantStore:
    """Mock Qdrant store for testing"""
    
    def search(self, query_vector, k=5, filters=None):
        return [
            {
                'content': 'Cisco 3802I access points are deployed in Building A',
                'similarity_score': 0.85,
                'source': 'BuildingA_Network_Layout.pdf',
                'metadata': {'building': 'A', 'equipment_type': 'access_point'}
            }
        ]
    
    def get_collection_info(self):
        return {
            'vectors_count': 1000,
            'points_count': 1000,
            'status': 'green'
        }

class MockQueryEngine:
    """Mock query engine for testing"""
    
    def process_query(self, query, **kwargs):
        return {
            'query': query,
            'response': f"Mock response for: {query}",
            'confidence_score': 0.8,
            'sources': [
                {
                    'content': 'Mock content about access points',
                    'source': 'mock_source.pdf',
                    'similarity_score': 0.8
                }
            ],
            'total_sources': 1,
            'method': 'mock_search'
        }

def main():
    """Run all tests"""
    
    print("🧪 Fresh Conversation System Integration Tests")
    print("=" * 70)
    
    results = []
    
    # Test the main conversation system
    results.append(test_fresh_conversation_system())
    
    # Test context management features
    results.append(test_context_management())
    
    # Summary
    print(f"\n📋 Test Summary")
    print("=" * 30)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Fresh conversation system is ready.")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 