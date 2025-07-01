"""
Conversation Manager
High-level manager for LangGraph conversations with built-in state persistence
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import uuid

from .conversation_state import (
    ConversationState, MessageType, ConversationPhase,
    create_conversation_state, add_message_to_state, get_conversation_history,
    MAX_CONVERSATION_HISTORY, _apply_memory_management
)
from .conversation_graph import ConversationGraph

# Memory management constants
MAX_CONVERSATION_AGE_HOURS = 24  # Maximum age of conversations to keep
MAX_ACTIVE_CONVERSATIONS = 100   # Maximum number of active conversations

class ConversationManager:
    """Manages conversations using LangGraph with built-in state persistence"""
    
    def __init__(self, container=None, db_path: str = None):
        self.container = container
        self.logger = logging.getLogger(__name__)
        
        # Initialize conversation graph with state persistence
        self.conversation_graph = ConversationGraph(container, db_path)
        
        # Run initial cleanup of old conversations
        try:
            cleanup_result = self.cleanup_old_conversations()
            self.logger.info(f"Initial conversation cleanup: {cleanup_result.get('cleaned_count', 0)} conversations removed")
        except Exception as e:
            self.logger.warning(f"Initial conversation cleanup failed: {e}")
        
        self.logger.info("ConversationManager initialized with LangGraph state persistence and memory management")
    
    def start_conversation(self, thread_id: Optional[str] = None) -> Dict[str, Any]:
        """Start a new conversation or get existing one using thread_id"""
        
        if thread_id is None:
            thread_id = str(uuid.uuid4())
        
        try:
            # Process initial greeting (empty message to trigger greeting)
            state = self.conversation_graph.process_message(thread_id, "")
            
            # Format initial response
            response = self._format_response(state, thread_id)
            
            self.logger.info(f"Started/retrieved conversation for thread: {thread_id}")
            return response
            
        except Exception as e:
            self.logger.error(f"Error starting conversation: {e}")
            return {
                'response': "Hello! I'm your AI assistant. I can help you find information, answer questions, and have a conversation about various topics. What would you like to know?",
                'thread_id': thread_id,
                'error': str(e)
            }
    
    def process_user_message(self, thread_id: str, message: str) -> Dict[str, Any]:
        """Process a user message using LangGraph state management"""
        
        try:
            # Process message through LangGraph with state persistence
            updated_state = self.conversation_graph.process_message(thread_id, message)
            
            # Format response
            response = self._format_response(updated_state, thread_id)
            
            self.logger.info(f"Processed message for thread {thread_id}")
            return response
            
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            return {
                'response': "I apologize, but I encountered an error. Please try again.",
                'error': str(e),
                'thread_id': thread_id
            }
    
    def get_conversation_history(self, thread_id: str, max_messages: int = 20) -> Dict[str, Any]:
        """Get conversation history for a thread using LangGraph state"""
        
        try:
            return self.conversation_graph.get_conversation_history(thread_id, max_messages)
        except Exception as e:
            self.logger.error(f"Error getting conversation history: {e}")
            return {
                'messages': [],
                'thread_id': thread_id,
                'error': str(e)
            }
    
    def end_conversation(self, thread_id: str) -> Dict[str, Any]:
        """End a conversation by processing a goodbye message"""
        
        try:
            # Process goodbye message to trigger farewell
            final_state = self.conversation_graph.process_message(thread_id, "goodbye")
            
            # Generate conversation summary
            summary = self._generate_conversation_summary(final_state)
            
            self.logger.info(f"Ended conversation for thread {thread_id}")
            
            return {
                'message': 'Conversation ended',
                'summary': summary,
                'thread_id': thread_id,
                'total_turns': final_state.turn_count
            }
        except Exception as e:
            self.logger.error(f"Error ending conversation: {e}")
            return {
                'message': 'Error ending conversation',
                'thread_id': thread_id,
                'error': str(e)
            }
    
    def list_active_conversations(self) -> Dict[str, Any]:
        """List all conversation threads (placeholder - would need database query)"""
        
        try:
            # This would require querying the SQLite database directly
            # For now, return a placeholder response
            threads = self.conversation_graph.list_conversation_threads()
            
            return {
                'active_count': len(threads),
                'threads': threads
            }
        except Exception as e:
            self.logger.error(f"Error listing conversations: {e}")
            return {
                'active_count': 0,
                'threads': [],
                'error': str(e)
            }
    
    def cleanup_old_conversations(self) -> Dict[str, Any]:
        """Clean up old conversations to prevent memory leaks"""
        
        try:
            # Get all conversation threads
            threads = self.conversation_graph.list_conversation_threads()
            cleaned_count = 0
            current_time = datetime.now()
            
            for thread_id in threads:
                try:
                    # Get conversation history to check age
                    history = self.get_conversation_history(thread_id, max_messages=1)
                    
                    if history.messages:
                        # Check if conversation is old
                        last_message = history.messages[-1]
                        last_activity = last_message.timestamp
                        
                        if (current_time - last_activity).total_seconds() > MAX_CONVERSATION_AGE_HOURS * 3600:
                            # Remove old conversation
                            self.conversation_graph.checkpointer.delete({"configurable": {"thread_id": thread_id}})
                            cleaned_count += 1
                            self.logger.info(f"Cleaned up old conversation: {thread_id}")
                    
                except Exception as e:
                    self.logger.warning(f"Error checking conversation {thread_id}: {e}")
                    continue
            
            self.logger.info(f"Conversation cleanup completed: {cleaned_count} old conversations removed")
            
            return {
                'cleaned_count': cleaned_count,
                'total_threads': len(threads),
                'timestamp': current_time.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error during conversation cleanup: {e}")
            return {
                'cleaned_count': 0,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory usage statistics for conversations"""
        
        try:
            threads = self.conversation_graph.list_conversation_threads()
            total_messages = 0
            total_topics = 0
            
            for thread_id in threads:
                try:
                    history = self.get_conversation_history(thread_id)
                    total_messages += len(history.messages)
                    total_topics += len(history.topics_discussed)
                except:
                    continue
            
            return {
                'active_conversations': len(threads),
                'total_messages': total_messages,
                'total_topics': total_topics,
                'max_conversation_history': MAX_CONVERSATION_HISTORY,
                'max_conversation_age_hours': MAX_CONVERSATION_AGE_HOURS,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting memory stats: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _format_response(self, state: ConversationState, thread_id: str) -> Dict[str, Any]:
        """Format conversation state into response"""
        
        # Get the latest assistant message
        assistant_messages = [msg for msg in state.messages if msg.type == MessageType.ASSISTANT]
        latest_response = assistant_messages[-1].content if assistant_messages else ""
        
        response = {
            'response': latest_response,
            'thread_id': thread_id,
            'conversation_id': state.conversation_id,
            'turn_count': state.turn_count,
            'current_phase': state.current_phase.value,
            'confidence_score': state.response_confidence,
            'confidence': state.response_confidence,  # Add alias for compatibility
            'timestamp': datetime.now().isoformat()
        }
        
        # Add optional fields if available
        if state.suggested_questions:
            response['suggested_questions'] = state.suggested_questions
        
        if state.related_topics:
            response['related_topics'] = state.related_topics
        
        # For sources, provide clean metadata only (no content snippets)
        if state.search_results:
            response['sources'] = [
                {
                    'title': result.source,
                    'doc_id': result.doc_id,
                    'relevance': self._format_relevance_score(result.relevance_score)
                } for result in state.search_results
            ]
            response['total_sources'] = len(state.search_results)
        else:
            response['total_sources'] = 0
        
        if state.has_errors:
            response['errors'] = state.error_messages
        
        return response
    
    def _get_source_type(self, source: str) -> str:
        """Determine source type based on filename"""
        if not source:
            return "Document"
        
        source_lower = source.lower()
        if '.xlsx' in source_lower or '.xls' in source_lower:
            return "Excel File"
        elif '.pdf' in source_lower:
            return "PDF Document"
        elif '.txt' in source_lower:
            return "Text File"
        elif '.json' in source_lower:
            return "Data File"
        elif '.md' in source_lower:
            return "Markdown Document"
        else:
            return "Document"
    
    def _format_relevance_score(self, score: float) -> str:
        """Format relevance score as user-friendly text"""
        if score >= 0.8:
            return "Highly Relevant"
        elif score >= 0.6:
            return "Very Relevant"
        elif score >= 0.4:
            return "Relevant"
        elif score >= 0.2:
            return "Somewhat Relevant"
        else:
            return "Low Relevance"
    
    def _generate_conversation_summary(self, state: ConversationState) -> str:
        """Generate a summary of the conversation"""
        
        if not state.messages:
            return "No conversation content"
        
        user_messages = [msg.content for msg in state.messages if msg.type == MessageType.USER]
        topics = state.topics_discussed
        
        summary_parts = []
        
        if topics:
            summary_parts.append(f"Topics discussed: {', '.join(topics[-5:])}")
        
        if user_messages:
            summary_parts.append(f"Total user messages: {len(user_messages)}")
        
        summary_parts.append(f"Conversation turns: {state.turn_count}")
        
        return "; ".join(summary_parts)
    
    # Deprecated methods for backward compatibility
    def get_or_create_conversation(self, session_id: str) -> ConversationState:
        """Deprecated: Use thread_id based methods instead"""
        self.logger.warning("get_or_create_conversation is deprecated. Use thread_id based methods.")
        # For backward compatibility, treat session_id as thread_id
        try:
            return self.conversation_graph._get_or_create_state(session_id)
        except Exception as e:
            self.logger.error(f"Error in deprecated method: {e}")
            return create_conversation_state(session_id)
    
    def get_active_sessions(self) -> Dict[str, Any]:
        """Deprecated: Use list_active_conversations instead"""
        self.logger.warning("get_active_sessions is deprecated. Use list_active_conversations.")
        return self.list_active_conversations() 