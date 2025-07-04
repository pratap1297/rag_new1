"""
Test Conversation Flow System
This script tests the implementation of the conversation flow system.
"""
import logging
import sys
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Add the rag_system directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'rag_system'))

# Import the conversation components
try:
    from rag_system.src.conversation import (
        FreshConversationState,
        FreshConversationStateManager,
        FreshMemoryManager,
        FreshContextManager,
        FreshSmartRouter,
        FreshConversationNodes,
        FreshConversationGraph
    )
    print("✅ Successfully imported conversation components")
except ImportError as e:
    print(f"❌ Failed to import conversation components: {e}")
    sys.exit(1)


class MockQueryEngine:
    """Mock implementation of the QueryEngine for testing"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def process_query(self, query: str, **kwargs) -> Dict[str, Any]:
        """Process a query and return mock results"""
        self.logger.info(f"Processing query: {query}")
        
        # Create mock search results
        if "network" in query.lower() or "access point" in query.lower():
            return {
                'response': "I found information about network equipment.",
                'sources': [
                    {
                        'text': "Building A has 12 Cisco 3802I access points deployed across 3 floors.",
                        'similarity_score': 0.92,
                        'source': "network_inventory.pdf",
                        'metadata': {'page': 1, 'type': 'pdf'}
                    },
                    {
                        'text': "Access points in Building A operate on both 2.4GHz and 5GHz bands with WPA2-Enterprise security.",
                        'similarity_score': 0.85,
                        'source': "network_security.pdf",
                        'metadata': {'page': 3, 'type': 'pdf'}
                    }
                ]
            }
        elif "incident" in query.lower() or "issue" in query.lower():
            return {
                'response': "I found information about incidents.",
                'sources': [
                    {
                        'text': "There are currently 5 open network incidents: 3 in Building A and 2 in Building B.",
                        'similarity_score': 0.88,
                        'source': "incident_report.pdf",
                        'metadata': {'page': 1, 'type': 'pdf'}
                    }
                ]
            }
        else:
            # Generic response for other queries
            return {
                'response': "I found some general information.",
                'sources': [
                    {
                        'text': "The company's IT infrastructure includes networks across 3 buildings with centralized management.",
                        'similarity_score': 0.75,
                        'source': "it_overview.pdf",
                        'metadata': {'page': 1, 'type': 'pdf'}
                    }
                ]
            }


class MockLLMClient:
    """Mock implementation of the LLMClient for testing"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def generate(self, prompt: str) -> str:
        """Generate a response using the prompt"""
        self.logger.info(f"Generating response for prompt: {prompt[:50]}...")
        
        if "network" in prompt.lower() or "access point" in prompt.lower():
            return "Building A has 12 Cisco 3802I access points deployed across 3 floors. These access points operate on both 2.4GHz and 5GHz bands with WPA2-Enterprise security."
        elif "incident" in prompt.lower() or "issue" in prompt.lower():
            return "There are currently 5 open network incidents: 3 in Building A and 2 in Building B."
        else:
            return "The company's IT infrastructure includes networks across 3 buildings with centralized management."


class TestContainer:
    """Container for dependency injection"""
    
    def __init__(self):
        self.components = {}
    
    def register(self, name: str, component: Any) -> None:
        """Register a component"""
        self.components[name] = component
    
    def get(self, name: str, default=None) -> Any:
        """Get a component"""
        return self.components.get(name, default)


def test_conversation_flow():
    """Test the conversation flow system"""
    print("\n🔍 Testing Conversation Flow System")
    print("=" * 50)
    
    try:
        # Create mock dependencies
        query_engine = MockQueryEngine()
        llm_client = MockLLMClient()
        
        # Create container
        container = TestContainer()
        container.register('query_engine', query_engine)
        container.register('llm_client', llm_client)
        
        # Initialize components
        context_manager = FreshContextManager()
        memory_manager = FreshMemoryManager()
        smart_router = FreshSmartRouter(context_manager)
        state_manager = FreshConversationStateManager(
            context_manager=context_manager,
            memory_manager=memory_manager,
            smart_router=smart_router
        )
        
        container.register('context_manager', context_manager)
        container.register('memory_manager', memory_manager)
        container.register('smart_router', smart_router)
        container.register('state_manager', state_manager)
        
        # Create conversation graph
        conversation_graph = FreshConversationGraph(container)
        
        print("✅ Components initialized successfully")
        
        # Create initial state
        thread_id = f"test_{datetime.now().timestamp()}"
        initial_state = state_manager.create_initial_state(thread_id)
        
        print(f"✅ Created conversation with thread ID: {thread_id}")
        
        # Test queries
        test_queries = [
            "Hello!",
            "What access points are in Building A?",
            "Tell me more about them.",
            "Are there any network incidents?",
            "Thank you, goodbye!"
        ]
        
        # Process each query
        state = initial_state
        for i, query in enumerate(test_queries, 1):
            print(f"\n📝 Query {i}: {query}")
            
            # Add user message to state
            state = state_manager.add_message(state, 'user', query)
            
            # Process message through conversation graph
            state = conversation_graph.process_message(state)
            
            # Get the last assistant message
            messages = state.get('messages', [])
            assistant_messages = [msg for msg in messages if msg.get('type') == 'assistant']
            
            if assistant_messages:
                last_response = assistant_messages[-1].get('content', '')
                print(f"🤖 Response: {last_response}")
            else:
                print("❌ No response generated")
        
        print("\n✅ Conversation flow test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Conversation flow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_conversation_flow() 