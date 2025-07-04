"""
FreshConversationState Module
Defines the state objects for the conversation system
"""
import logging
from typing import Dict, List, Any, Optional, TypedDict
from datetime import datetime
import uuid


class SearchResult(TypedDict):
    """Represents a single search result"""
    content: str  # The main text content of the document chunk
    score: float  # The similarity score from the search
    source: str   # The filename or origin of the document
    metadata: dict  # Any other metadata from the vector store


class FreshConversationState(dict):
    """
    Dictionary-like object that holds all data for the current conversation turn.
    This is the single source of truth that is passed between all nodes.
    """
    
    def __init__(self, thread_id: str = None, **kwargs):
        """Initialize a new conversation state"""
        # Generate IDs if not provided
        thread_id = thread_id or str(uuid.uuid4())
        conversation_id = kwargs.get('conversation_id', str(uuid.uuid4()))
        
        # Set default values
        defaults = {
            'thread_id': thread_id,
            'conversation_id': conversation_id,
            'messages': [],
            'turn_count': 0,
            'conversation_status': "active",
            'original_query': "",
            'processed_query': "",
            'user_intent': None,
            'query_complexity': None,
            'entities_mentioned': [],
            'is_contextual': False,
            'search_results': [],
            'context_chunks': [],
            'query_engine_response': "",
            'has_errors': False,
            'error_messages': [],
            'overall_quality_score': 1.0,
            'created_at': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat(),
        }
        
        # Override defaults with provided kwargs
        for key, value in kwargs.items():
            defaults[key] = value
        
        # Initialize with the combined dictionary
        super().__init__(**defaults)


class FreshConversationStateManager:
    """
    Utility class responsible for safe and consistent modifications to the FreshConversationState.
    """
    
    def __init__(self, context_manager=None, memory_manager=None, smart_router=None):
        """Initialize the state manager with optional dependencies"""
        self.logger = logging.getLogger(__name__)
        self.context_manager = context_manager
        self.memory_manager = memory_manager
        self.smart_router = smart_router
    
    def create_initial_state(self, thread_id: str = None, user_id: str = None) -> FreshConversationState:
        """Create a new conversation state"""
        thread_id = thread_id or str(uuid.uuid4())
        
        return FreshConversationState(
            thread_id=thread_id,
            user_id=user_id
        )
    
    def add_message(self, state: FreshConversationState, message_type: str, content: str, 
                   metadata: Dict[str, Any] = None) -> FreshConversationState:
        """Add a message to the conversation state"""
        if not isinstance(state, dict):
            self.logger.error(f"Invalid state object: {type(state)}")
            return state
        
        # Create a copy to avoid modifying the original
        new_state = FreshConversationState(**state)
        
        # Add the message
        message = {
            'id': str(uuid.uuid4()),
            'type': message_type,
            'content': content,
            'metadata': metadata or {},
            'timestamp': datetime.now().isoformat()
        }
        
        messages = new_state.get('messages', [])
        messages.append(message)
        new_state['messages'] = messages
        
        # Update turn count and activity timestamp
        if message_type == 'user':
            new_state['turn_count'] = new_state.get('turn_count', 0) + 1
        
        new_state['last_activity'] = datetime.now().isoformat()
        
        return new_state
    
    def update_search_results(self, state: FreshConversationState, 
                             search_results: List[SearchResult],
                             context_chunks: List[str]) -> FreshConversationState:
        """Update the search results and context chunks in the state"""
        new_state = FreshConversationState(**state)
        new_state['search_results'] = search_results
        new_state['context_chunks'] = context_chunks
        return new_state
    
    def get_recent_messages(self, state: FreshConversationState, count: int = 5) -> List[Dict[str, Any]]:
        """Get the most recent messages from the state"""
        messages = state.get('messages', [])
        return messages[-count:] if messages else []
    
    def get_last_user_message(self, state: FreshConversationState) -> Optional[str]:
        """Get the content of the last user message"""
        messages = state.get('messages', [])
        for message in reversed(messages):
            if message.get('type') == 'user':
                return message.get('content')
        return None 