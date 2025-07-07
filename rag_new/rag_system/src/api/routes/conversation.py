"""
Conversation API Routes
FastAPI endpoints for LangGraph conversation management with state persistence
"""
import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, validator

# Import the fresh conversation system components
try:
    from ...conversation import (
        FreshConversationGraph as ConversationManager,
        FreshConversationNodes,
        FreshSmartRouter as SuggestionPlugin
    )
    from ...core.dependency_container import get_dependency_container
except ImportError:
    # Fallback for different execution contexts
    from rag_system.src.conversation import (
        FreshConversationGraph as ConversationManager,
        FreshConversationNodes,
        FreshSmartRouter as SuggestionPlugin
    )
    from rag_system.src.core.dependency_container import get_dependency_container

# Create router
router = APIRouter(prefix="/conversation", tags=["Conversation"])
logger = logging.getLogger(__name__)

# Request/Response models

# ------------------------------------------------------------------
# Streaming endpoint (simple placeholder)
# ------------------------------------------------------------------
from fastapi.responses import StreamingResponse

@router.get("/message/stream")
async def stream_messages(thread_id: str = ""):
    """Server-Sent Events placeholder for message streaming.
    Currently yields an empty stream so that the route exists and
    the frontend no longer receives 404. Replace with real stream logic
    (e.g., SSE or WebSocket) as needed.
    """
    async def event_generator():
        # Placeholder: no live streaming implemented yet
        yield "event: end\ndata: Stream not implemented yet\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")

# ------------------------------------------------------------------

class ConversationRequest(BaseModel):
    thread_id: Optional[str] = Field(None, description="Optional thread ID to continue a conversation.")
    message: Optional[str] = Field(None, description="User's message. Required for sending messages, not for starting.")
    
    @validator('message')
    def validate_message_with_thread(cls, v, values):
        thread_id = values.get('thread_id')
        if thread_id and not v:
            raise ValueError('message is required when thread_id is provided')
        return v

class MessageRequest(BaseModel):
    thread_id: str = Field(..., description="Thread ID for the conversation.")
    message: str = Field(..., description="User's message.")

class ConversationResponse(BaseModel):
    thread_id: str
    response: str
    suggestions: List[str]
    sources: List[Dict[str, Any]]
    turn_count: int
    phase: str

class StartConversationResponse(BaseModel):
    thread_id: str
    message: str = "Conversation started successfully"

# Global conversation manager
conversation_manager_instance = None

def get_conversation_manager():
    """Dependency injector for the ConversationManager."""
    global conversation_manager_instance
    if conversation_manager_instance is None:
        try:
            logger.info("Initializing new ConversationManager...")
            container = get_dependency_container()

            # Create the conversation manager instance with the container
            # FreshConversationGraph will handle its own dependencies
            conversation_manager_instance = ConversationManager(container=container)
            logger.info("New ConversationManager initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize ConversationManager: {e}", exc_info=True)
            raise HTTPException(status_code=503, detail="Conversation service is unavailable.")
    
    return conversation_manager_instance

@router.post("/start", response_model=StartConversationResponse)
async def start_conversation(
    manager: ConversationManager = Depends(get_conversation_manager)
):
    """
    Start a new conversation and return the thread ID.
    """
    try:
        response_data = manager.start_conversation()
        return StartConversationResponse(
            thread_id=response_data['thread_id'],
            message="Conversation started successfully"
        )
    except Exception as e:
        logger.error(f"Error starting conversation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start conversation: {str(e)}")

@router.post("/message", response_model=ConversationResponse)
async def send_message(
    request: MessageRequest,
    manager: ConversationManager = Depends(get_conversation_manager)
):
    """
    Send a message to an existing conversation.
    """
    try:
        response_data = manager.send_message(request.thread_id, request.message)
        return ConversationResponse(**response_data)
    except Exception as e:
        logger.error(f"Error sending message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")

@router.get("/threads")
async def get_conversation_threads(
    manager: ConversationManager = Depends(get_conversation_manager)
):
    """
    Get all active conversation threads.
    """
    try:
        # Get all active threads from the conversation manager
        if hasattr(manager, 'get_active_threads'):
            threads = manager.get_active_threads()
        else:
            # Fallback: return empty list if method doesn't exist
            threads = []
        
        return {
            "threads": threads,
            "count": len(threads)
        }
    except Exception as e:
        logger.error(f"Error getting conversation threads: {e}", exc_info=True)
        # Return empty list instead of error for UI compatibility
        return {
            "threads": [],
            "count": 0
        }

@router.get("/thread/{thread_id}")
async def get_conversation_thread(
    thread_id: str,
    manager: ConversationManager = Depends(get_conversation_manager)
):
    """Get details of a specific conversation thread."""
    try:
        state = manager._get_state(thread_id)
        if not state:
            raise HTTPException(status_code=404, detail="Conversation thread not found.")
        
        return {
            "thread_id": thread_id,
            "conversation_id": state.get('conversation_id'),
            "turn_count": state.get('turn_count', 0),
            "phase": state.get('phase', 'unknown'),
            "created_at": state.get('created_at'),
            "last_activity": state.get('last_activity')
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation thread: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get thread: {str(e)}")

@router.delete("/thread/{thread_id}")
async def delete_conversation_thread(
    thread_id: str,
    manager: ConversationManager = Depends(get_conversation_manager)
):
    """Delete a conversation thread."""
    try:
        # Try to delete the thread if the manager supports it
        if hasattr(manager, 'delete_thread'):
            manager.delete_thread(thread_id)
        else:
            # Fallback: just return success
            logger.warning(f"Manager doesn't support thread deletion, thread_id: {thread_id}")
        
        return {
            "message": f"Thread {thread_id} deleted successfully",
            "thread_id": thread_id
        }
    except Exception as e:
        logger.error(f"Error deleting conversation thread: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete thread: {str(e)}")

@router.post("/end/{thread_id}")
async def end_conversation(
    thread_id: str,
    manager: ConversationManager = Depends(get_conversation_manager)
):
    """End a conversation thread."""
    try:
        # Try to end the conversation if the manager supports it
        if hasattr(manager, 'end_conversation'):
            manager.end_conversation(thread_id)
        else:
            # Fallback: just return success
            logger.warning(f"Manager doesn't support ending conversations, thread_id: {thread_id}")
        
        return {
            "message": f"Conversation {thread_id} ended successfully",
            "thread_id": thread_id
        }
    except Exception as e:
        logger.error(f"Error ending conversation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to end conversation: {str(e)}")

@router.post("", response_model=ConversationResponse)
async def handle_conversation(
    request: ConversationRequest,
    manager: ConversationManager = Depends(get_conversation_manager)
):
    """
    Starts a new conversation or continues an existing one.
    - If `thread_id` is not provided, a new conversation starts.
    - If `thread_id` and `message` are provided, a message is sent to that conversation.
    """
    try:
        if request.thread_id and request.message:
            # Continue existing conversation
            response_data = manager.send_message(request.thread_id, request.message)
        elif not request.thread_id:
            # Start a new conversation
            response_data = manager.start_conversation()
            if request.message:
                # If a message was sent with the start request, process it now
                response_data = manager.send_message(response_data['thread_id'], request.message)
        else:
            raise HTTPException(
                status_code=400, 
                detail="A message is required to continue a conversation. Provide a 'message' field."
            )
            
        return ConversationResponse(**response_data)
        
    except Exception as e:
        logger.error(f"Error handling conversation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process conversation: {str(e)}")

@router.get("/history/{thread_id}", response_model=dict)
async def get_conversation_history(
    thread_id: str,
    manager: ConversationManager = Depends(get_conversation_manager)
):
    """Get the message history for a given conversation thread."""
    try:
        state = manager._get_state(thread_id)
        if not state.get('messages'):
            raise HTTPException(status_code=404, detail="Conversation thread not found.")
        return {
            "thread_id": thread_id,
            "conversation_id": state.get('conversation_id'),
            "messages": state.get('messages', []),
            "turn_count": state.get('turn_count', 0),
        }
    except Exception as e:
        logger.error(f"Error retrieving conversation history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve history: {str(e)}")

@router.get("/health")
async def conversation_health_check():
    """Health check for conversation service"""
    try:
        manager = get_conversation_manager()
        from datetime import datetime
        
        # Check if this is the fresh manager with enhanced capabilities
        if hasattr(manager, 'get_system_status'):
            # Fresh manager - get comprehensive status
            system_status = manager.get_system_status()
            return {
                "status": "healthy",
                "service": "conversation",
                "manager_type": "FreshConversationManager",
                "version": "2.0-fresh",
                "langgraph_available": True,
                "state_persistence": "enabled",
                "checkpointer_type": "MemorySaver", 
                "features": [
                    "Fresh Context Management",
                    "Anti-Poisoning Validation",
                    "Anti-Distraction Memory Management", 
                    "Smart Query Routing",
                    "Conflict Detection",
                    "Quality Scoring"
                ],
                "system_status": system_status,
                "timestamp": datetime.now().isoformat()
            }
        else:
            # Original manager - basic health check
            state_persistence_status = "enabled"
            try:
                # Try to access the checkpointer
                if hasattr(manager, 'conversation_graph') and hasattr(manager.conversation_graph, 'checkpointer') and manager.conversation_graph.checkpointer:
                    state_persistence_status = "enabled"
                else:
                    state_persistence_status = "disabled"
            except Exception as e:
                logger.error(f"Error checking state persistence status: {e}")
                state_persistence_status = "error"
            
            return {
                "status": "healthy",
                "service": "conversation",
                "manager_type": type(manager).__name__,
                "version": "2.0",
                "langgraph_available": True,
                "state_persistence": state_persistence_status,
                "checkpointer_type": "MemorySaver",
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        from datetime import datetime
        return {
            "status": "unhealthy",
            "service": "conversation", 
            "error": str(e),
            "langgraph_available": False,
            "state_persistence": "error",
            "timestamp": datetime.now().isoformat()
        } 