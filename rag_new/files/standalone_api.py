"""
Standalone API for the Conversation Flow System
This script provides a FastAPI-based API for the conversation flow system.
"""
import logging
import sys
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('conversation_api.log')
    ]
)

# Add the rag_system directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'rag_system'))

# Import FastAPI
try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    import uvicorn
except ImportError:
    print("FastAPI or uvicorn not installed. Run: pip install fastapi uvicorn")
    sys.exit(1)

# Import the conversation components
try:
    from rag_system.src.conversation import (
        FreshConversationState,
        FreshConversationStateManager,
        FreshMemoryManager,
        FreshContextManager,
        FreshSmartRouter,
        FreshConversationGraph
    )
    print("✅ Successfully imported conversation components")
except ImportError as e:
    print(f"❌ Failed to import conversation components: {e}")
    sys.exit(1)


# Import mock components for testing
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


# Initialize components
container = TestContainer()
query_engine = MockQueryEngine()
llm_client = MockLLMClient()
context_manager = FreshContextManager()
memory_manager = FreshMemoryManager()
smart_router = FreshSmartRouter(context_manager)
state_manager = FreshConversationStateManager(
    context_manager=context_manager,
    memory_manager=memory_manager,
    smart_router=smart_router
)

container.register('query_engine', query_engine)
container.register('llm_client', llm_client)
container.register('context_manager', context_manager)
container.register('memory_manager', memory_manager)
container.register('smart_router', smart_router)
container.register('state_manager', state_manager)

# Create conversation graph
conversation_graph = FreshConversationGraph(container)

# Create FastAPI app
app = FastAPI(
    title="Conversation Flow API",
    description="API for the conversation flow system",
    version="1.0.0"
)

# Store active conversations
active_conversations = {}


# Define request and response models
class MessageRequest(BaseModel):
    thread_id: Optional[str] = None
    message: str
    user_id: Optional[str] = None


class MessageResponse(BaseModel):
    thread_id: str
    response: str
    sources: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None


@app.post("/api/conversation", response_model=MessageResponse)
async def process_message(request: MessageRequest):
    """Process a message in a conversation"""
    # Get or create thread ID
    thread_id = request.thread_id or f"thread_{uuid.uuid4()}"
    
    try:
        # Get or create conversation state
        if thread_id in active_conversations:
            state = active_conversations[thread_id]
        else:
            state = state_manager.create_initial_state(thread_id, request.user_id)
            active_conversations[thread_id] = state
        
        # Add user message to state
        state = state_manager.add_message(state, 'user', request.message)
        
        # Process message through conversation graph
        state = conversation_graph.process_message(state)
        
        # Get the last assistant message
        messages = state.get('messages', [])
        assistant_messages = [msg for msg in messages if msg.get('type') == 'assistant']
        
        if not assistant_messages:
            raise HTTPException(status_code=500, detail="No response generated")
        
        last_response = assistant_messages[-1].get('content', '')
        
        # Update active conversations
        active_conversations[thread_id] = state
        
        # Prepare sources if available
        sources = []
        search_results = state.get('search_results', [])
        if search_results:
            for result in search_results:
                sources.append({
                    'content': result.get('content', '')[:200] + '...',  # Truncate for response
                    'source': result.get('source', 'unknown'),
                    'score': result.get('score', 0.0)
                })
        
        # Prepare response
        response = MessageResponse(
            thread_id=thread_id,
            response=last_response,
            sources=sources if sources else None,
            metadata={
                'intent': state.get('user_intent'),
                'is_contextual': state.get('is_contextual', False),
                'turn_count': state.get('turn_count', 0)
            }
        )
        
        return response
        
    except Exception as e:
        logging.error(f"Error processing message: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")


@app.get("/api/conversation/{thread_id}/history")
async def get_conversation_history(thread_id: str):
    """Get the conversation history for a thread"""
    if thread_id not in active_conversations:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")
    
    state = active_conversations[thread_id]
    messages = state.get('messages', [])
    
    return {
        'thread_id': thread_id,
        'messages': messages,
        'turn_count': state.get('turn_count', 0)
    }


@app.delete("/api/conversation/{thread_id}")
async def delete_conversation(thread_id: str):
    """Delete a conversation"""
    if thread_id not in active_conversations:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")
    
    del active_conversations[thread_id]
    
    return {
        'status': 'success',
        'message': f"Thread {thread_id} deleted"
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'active_conversations': len(active_conversations)
    }


if __name__ == "__main__":
    print("Starting Conversation Flow API...")
    uvicorn.run("standalone_api:app", host="0.0.0.0", port=8000, reload=True) 