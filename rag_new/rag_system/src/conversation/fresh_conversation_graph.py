"""
FreshConversationGraph Module
Implements the directed graph for the conversation flow
"""
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import uuid

from .fresh_conversation_state import FreshConversationState
from .fresh_conversation_nodes import FreshConversationNodes
from .fresh_smart_router import Route


class FreshConversationGraph:
    """
    Implements the directed graph for the conversation flow.
    Manages the execution of conversation nodes based on routing decisions.
    """
    
    def __init__(self, container=None):
        """Initialize with optional dependency container"""
        self.logger = logging.getLogger(__name__)
        self.container = container
        
        # Initialize nodes
        self.nodes = FreshConversationNodes(container)
        
        # Build graph
        self.graph = self._build_graph()
        
        # Active conversations
        self.active_conversations: Dict[str, FreshConversationState] = {}
        
        self.logger.info("FreshConversationGraph initialized")
    
    def _build_graph(self) -> Dict[str, Dict[str, Callable]]:
        """
        Build the conversation graph structure
        
        Returns:
            Dict: The graph structure with nodes and edges
        """
        # Define the graph structure
        graph = {
            'initialize': {
                'next': lambda _: 'greet',
                'node': self.nodes.initialize_conversation
            },
            'greet': {
                'next': lambda _: 'wait_for_input',
                'node': self.nodes.greet_user
            },
            'wait_for_input': {
                'next': lambda _: 'understand',
                'node': lambda state: state  # Passthrough node
            },
            'understand': {
                'next': self._route_after_understanding,
                'node': self.nodes.understand_intent
            },
            'search': {
                'next': lambda _: 'respond',
                'node': self.nodes.search_knowledge
            },
            'respond': {
                'next': lambda _: 'wait_for_input',
                'node': self.nodes.generate_response
            },
            'clarify': {
                'next': lambda _: 'wait_for_input',
                'node': self.nodes.handle_clarification
            },
            'end': {
                'next': lambda _: None,  # End of conversation
                'node': lambda state: state  # Passthrough node
            }
        }
        
        return graph
    
    def _route_after_understanding(self, state: FreshConversationState) -> str:
        """
        Determine the next node based on the user's intent
        
        Args:
            state: The current conversation state
            
        Returns:
            str: The name of the next node
        """
        user_intent = state.get('user_intent')
        
        # Apply routing logic based on the requirements
        if user_intent == 'goodbye':
            return 'end'
        elif user_intent in ['greeting', 'help']:
            return 'respond'
        else:
            # Default to search for all other intents (critical "search-first" principle)
            return 'search'
    
    def process_message(self, state: FreshConversationState) -> FreshConversationState:
        """
        Process a user message through the conversation graph
        
        Args:
            state: The current conversation state with the user's message
            
        Returns:
            FreshConversationState: Updated state with the assistant's response
        """
        thread_id = state.get('thread_id')
        self.logger.info(f"Processing message for thread {thread_id}")
        
        # Store the state in active conversations
        self.active_conversations[thread_id] = state
        
        # Determine starting node
        current_node = 'understand'
        
        # Process through the graph
        while current_node:
            try:
                self.logger.debug(f"Executing node: {current_node}")
                
                # Get the node function
                node_func = self.graph.get(current_node, {}).get('node')
                if not node_func:
                    self.logger.error(f"Node function not found for {current_node}")
                    break
                
                # Execute the node function
                state = node_func(state)
                
                # Get the next node function
                next_func = self.graph.get(current_node, {}).get('next')
                if not next_func:
                    self.logger.error(f"Next function not found for {current_node}")
                    break
                
                # Determine the next node
                next_node = next_func(state)
                
                # Check if we're done
                if next_node == 'wait_for_input' or next_node is None:
                    break
                
                current_node = next_node
                
            except Exception as e:
                self.logger.error(f"Error processing node {current_node}: {e}")
                state['has_errors'] = True
                state['error_messages'] = state.get('error_messages', []) + [f"Graph error: {str(e)}"]
                break
        
        # Update the state in active conversations
        self.active_conversations[thread_id] = state
        
        return state
    
    def get_conversation_history(self, thread_id: str) -> List[Dict[str, Any]]:
        """
        Get the conversation history for a thread
        
        Args:
            thread_id: The ID of the conversation thread
            
        Returns:
            List[Dict[str, Any]]: The conversation messages
        """
        state = self.active_conversations.get(thread_id)
        if not state:
            return []
        
        return state.get('messages', [])
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """
        Get system metrics about the conversation graph
        
        Returns:
            Dict[str, Any]: System metrics
        """
        return {
            'active_conversations': len(self.active_conversations),
            'timestamp': datetime.now().isoformat()
        }
    
    def send_message(self, thread_id: str, message: str) -> Dict[str, Any]:
        """
        Send a message in an existing conversation
        
        Args:
            thread_id: The ID of the conversation thread
            message: The user's message
            
        Returns:
            Dict[str, Any]: Updated conversation state with response
        """
        # Get existing state or raise error
        if thread_id not in self.active_conversations:
            raise ValueError(f"Conversation {thread_id} not found")
            
        current_state = self.active_conversations[thread_id]
        
        # Add user message to state
        messages = current_state.get('messages', [])
        messages.append({
            'type': 'user',
            'content': message,
            'timestamp': datetime.now().isoformat()
        })
        current_state['messages'] = messages
        current_state['last_activity'] = datetime.now().isoformat()
        current_state['turn_count'] = current_state.get('turn_count', 0) + 1
        
        # Process through graph
        processed_state = self.process_message(current_state)
        
        # Update active conversations with processed state
        self.active_conversations[thread_id] = processed_state
        
        # Get latest bot message
        latest_message = next((msg for msg in reversed(processed_state.get('messages', [])) 
                             if msg.get('type') == 'assistant'), None)
        
        # Return conversation info
        return {
            'thread_id': thread_id,
            'response': latest_message.get('content', '') if latest_message else '',
            'suggestions': processed_state.get('suggestions', []),
            'sources': processed_state.get('sources', []),
            'turn_count': processed_state.get('turn_count', 0),
            'phase': 'wait_for_input'
        }

    def start_conversation(self) -> Dict[str, Any]:
        """
        Start a new conversation
        
        Returns:
            Dict[str, Any]: Initial conversation state with thread_id
        """
        # Create new conversation state
        thread_id = str(uuid.uuid4())
        # Build initial state correctly using keyword arguments
        initial_state = FreshConversationState(
            thread_id=thread_id,
            turn_count=0,
            messages=[],
            has_errors=False,
            error_messages=[],
            created_at=datetime.now().isoformat(),
            last_activity=datetime.now().isoformat()
        )
        
        # Initialize through the graph
        current_state = initial_state
        current_node = 'initialize'
        
        while current_node:
            try:
                # Get and execute the node function
                node_func = self.graph.get(current_node, {}).get('node')
                if not node_func:
                    self.logger.error(f"Node function not found for {current_node}")
                    break
                
                current_state = node_func(current_state)
                
                # Get and execute the next function
                next_func = self.graph.get(current_node, {}).get('next')
                if not next_func:
                    self.logger.error(f"Next function not found for {current_node}")
                    break
                
                next_node = next_func(current_state)
                
                # Stop at wait_for_input
                if next_node == 'wait_for_input':
                    break
                    
                current_node = next_node
                
            except Exception as e:
                self.logger.error(f"Error in conversation initialization at node {current_node}: {e}")
                current_state['has_errors'] = True
                current_state['error_messages'] = current_state.get('error_messages', []) + [f"Initialization error: {str(e)}"]
                break
        
        # Store in active conversations
        self.active_conversations[thread_id] = current_state
        
        # Return conversation info
        return {
            'thread_id': thread_id,
            'response': current_state.get('messages', [])[-1]['content'] if current_state.get('messages') else '',
            'suggestions': current_state.get('suggestions', []),
            'sources': current_state.get('sources', []),
            'turn_count': current_state.get('turn_count', 0),
            'phase': current_node or 'error'
        }

    def cleanup_old_conversations(self, max_age_minutes: int = 60) -> int:
        """
        Clean up old conversations to free memory
        
        Args:
            max_age_minutes: Maximum age in minutes before a conversation is removed
            
        Returns:
            int: Number of conversations removed
        """
        now = datetime.now()
        to_remove = []
        
        for thread_id, state in self.active_conversations.items():
            last_activity = state.get('last_activity')
            if not last_activity:
                continue
                
            try:
                last_activity_time = datetime.fromisoformat(last_activity)
                age_minutes = (now - last_activity_time).total_seconds() / 60
                
                if age_minutes > max_age_minutes:
                    to_remove.append(thread_id)
            except (ValueError, TypeError):
                # If date parsing fails, keep the conversation
                pass
        
        # Remove old conversations
        for thread_id in to_remove:
            del self.active_conversations[thread_id]
        
        self.logger.info(f"Cleaned up {len(to_remove)} old conversations")
        return len(to_remove) 