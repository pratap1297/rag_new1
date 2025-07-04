"""
Fresh Conversation Manager Direct
A direct implementation that avoids import chain issues for API use
"""
import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid
import sys
from pathlib import Path

# Add conversation directory to path for direct imports
conversation_dir = Path(__file__).parent.parent / "conversation"
sys.path.insert(0, str(conversation_dir))

# Import fresh components directly without relative imports
try:
    from fresh_context_manager import FreshContextManager
    from fresh_memory_manager import FreshMemoryManager, MemoryType, MemoryPriority
    from fresh_smart_router import FreshSmartRouter
    from fresh_conversation_state import FreshConversationState, FreshConversationStateManager
    from fresh_conversation_graph import FreshConversationGraph
except ImportError as e:
    # If that fails, try the module imports
    logging.warning(f"Direct import failed: {e}")
    raise ImportError("Could not import fresh components - ensure files exist in conversation directory")

class FreshConversationManagerDirect:
    """
    Direct fresh conversation manager for API use
    Bypasses import chain issues by importing components directly
    """
    
    def __init__(self, container=None):
        self.logger = logging.getLogger(__name__)
        self.container = container
        
        # Initialize fresh components
        try:
            self.context_manager = FreshContextManager()
            self.memory_manager = FreshMemoryManager()
            self.smart_router = FreshSmartRouter(self.context_manager)
            self.state_manager = FreshConversationStateManager(
                context_manager=self.context_manager,
                memory_manager=self.memory_manager,
                smart_router=self.smart_router
            )
            
            # Initialize conversation graph - but make it optional
            try:
                self.conversation_graph = FreshConversationGraph(container)
                self.logger.info("Fresh conversation graph initialized successfully")
            except Exception as e:
                self.logger.warning(f"Could not initialize conversation graph: {e}")
                self.conversation_graph = None
            
            # Active conversations storage
            self.active_conversations: Dict[str, FreshConversationState] = {}
            
            # Performance metrics
            self.metrics = {
                'total_conversations': 0,
                'successful_responses': 0,
                'failed_responses': 0,
                'average_response_time': 0.0,
                'context_quality_avg': 0.0
            }
            
            self.logger.info("Fresh Conversation Manager Direct initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Fresh Conversation Manager Direct: {e}")
            raise
    
    def start_conversation(self, thread_id: str = None, user_id: str = None, session_id: str = None) -> Dict[str, Any]:
        """Start a new conversation"""
        try:
            # Generate thread_id if not provided
            if not thread_id:
                thread_id = f"thread_{uuid.uuid4().hex[:12]}"
            
            # Check if conversation already exists
            if thread_id in self.active_conversations:
                self.logger.info(f"Resuming existing conversation for thread {thread_id}")
                state = self.active_conversations[thread_id]
                return {
                    'thread_id': thread_id,
                    'conversation_id': state['conversation_id'],
                    'status': 'resumed',
                    'turn_count': state['turn_count'],
                    'timestamp': datetime.now().isoformat()
                }
            
            # Create new conversation state
            state = self.state_manager.create_conversation_state(
                user_id=user_id,
                session_id=session_id
            )
            
            # Override thread_id if provided
            state['thread_id'] = thread_id
            
            # Store in active conversations
            self.active_conversations[thread_id] = state
            
            # Update metrics
            self.metrics['total_conversations'] += 1
            
            self.logger.info(f"Started new conversation: {thread_id}")
            
            return {
                'thread_id': thread_id,
                'conversation_id': state['conversation_id'],
                'status': 'started',
                'turn_count': 0,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error starting conversation: {e}")
            self.metrics['failed_responses'] += 1
            return {'error': f"Failed to start conversation: {str(e)}"}
    
    def process_user_message(self, thread_id: str, message: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a user message"""
        start_time = datetime.now()
        
        try:
            # Get or create conversation state
            if thread_id not in self.active_conversations:
                self.logger.info(f"Creating new conversation for thread {thread_id}")
                self.start_conversation(thread_id)
            
            state = self.active_conversations[thread_id]
            
            # Update state with current message
            state['original_query'] = message
            state['processed_query'] = message
            state['turn_count'] += 1
            state['last_activity'] = datetime.now().isoformat()
            
            # Add user message to conversation
            user_message = {
                'type': 'user',
                'content': message,
                'timestamp': datetime.now().isoformat(),
                'metadata': metadata or {}
            }
            state['messages'].append(user_message)
            
            # Try to process with conversation graph first
            if self.conversation_graph:
                try:
                    result = self.conversation_graph.process_message(state)
                    
                    if isinstance(result, dict) and 'error' not in result:
                        # Update stored state
                        self.active_conversations[thread_id] = result
                        
                        # Calculate response time
                        response_time = (datetime.now() - start_time).total_seconds()
                        self._update_metrics(response_time, result.get('overall_quality_score', 0.8))
                        
                        # Format response
                        response = self._format_response(result, response_time)
                        self.metrics['successful_responses'] += 1
                        
                        self.logger.info(f"Successfully processed message for thread {thread_id}")
                        return response
                        
                except Exception as e:
                    self.logger.warning(f"Conversation graph processing failed: {e}")
            
            # Fallback processing without conversation graph
            self.logger.info("Using simplified processing without conversation graph")
            
            # Analyze query with smart router
            analysis = self.smart_router.analyze_query(message)
            routing = self.smart_router.route_query(analysis)
            
            # Generate response based on intent
            if analysis.intent.value in ['greeting', 'farewell']:
                response_text = self._generate_simple_response(message, analysis.intent.value)
            else:
                # Try to get relevant context
                relevant_chunks = self.context_manager.get_relevant_context(message)
                
                if relevant_chunks:
                    # Generate context-based response
                    context_text = "\n".join([chunk.content for chunk in relevant_chunks[:3]])
                    response_text = f"Based on the available information: {context_text[:500]}..."
                else:
                    # Generate general response
                    response_text = f"I understand you're asking about '{message}'. Could you provide more specific details about what you'd like to know?"
            
            # Add assistant message to conversation
            assistant_message = {
                'type': 'assistant',
                'content': response_text,
                'timestamp': datetime.now().isoformat(),
                'metadata': {
                    'intent': analysis.intent.value,
                    'complexity': analysis.complexity.value,
                    'route': routing.route.value,
                    'simplified_processing': True
                }
            }
            state['messages'].append(assistant_message)
            
            # Update state
            state['user_intent'] = analysis.intent.value
            state['query_complexity'] = analysis.complexity.value
            state['confidence_score'] = analysis.confidence
            state['current_phase'] = 'responding'
            
            # Store updated state
            self.active_conversations[thread_id] = state
            
            # Calculate response time and update metrics
            response_time = (datetime.now() - start_time).total_seconds()
            self._update_metrics(response_time, 0.7)  # Default quality score for simplified processing
            self.metrics['successful_responses'] += 1
            
            # Format and return response
            return {
                'response': response_text,
                'thread_id': thread_id,
                'conversation_id': state['conversation_id'],
                'turn_count': state['turn_count'],
                'current_phase': state['current_phase'],
                'confidence_score': state['confidence_score'],
                'timestamp': state['last_activity'],
                'suggested_questions': self._generate_simple_suggestions(analysis.intent.value),
                'related_topics': [],
                'sources': [],
                'total_sources': 0,
                'errors': [],
                'warnings': ['Using simplified processing'],
                'intent': analysis.intent.value,
                'complexity': analysis.complexity.value,
                'response_time': response_time,
                'quality_score': 0.7,
                'processing_mode': 'simplified'
            }
            
        except Exception as e:
            self.logger.error(f"Error processing user message: {e}")
            self.metrics['failed_responses'] += 1
            return self._generate_fallback_response(thread_id, message, str(e))
    
    def _generate_simple_response(self, message: str, intent: str) -> str:
        """Generate simple response based on intent"""
        message_lower = message.lower()
        
        if intent == 'greeting':
            if any(word in message_lower for word in ['hello', 'hi', 'hey']):
                return "Hello! I'm here to help you with any questions you might have. What would you like to know?"
            else:
                return "Greetings! How can I assist you today?"
        
        elif intent == 'farewell':
            return "Thank you for the conversation! Feel free to ask if you need anything else."
        
        else:
            return f"I understand you're asking about '{message}'. Let me help you with that."
    
    def _generate_simple_suggestions(self, intent: str) -> List[str]:
        """Generate simple follow-up suggestions"""
        if intent == 'greeting':
            return [
                "What information are you looking for?",
                "How can I help you today?",
                "Do you have any specific questions?"
            ]
        elif intent == 'information_seeking':
            return [
                "Could you provide more details?",
                "What specific aspect interests you?",
                "Would you like more information about this topic?"
            ]
        else:
            return [
                "Is there anything else I can help with?",
                "Do you need clarification on anything?",
                "What other information would be useful?"
            ]
    
    def _generate_fallback_response(self, thread_id: str, message: str, error_details: str) -> Dict[str, Any]:
        """Generate a fallback response when processing fails"""
        
        # Simple intent detection
        message_lower = message.lower()
        if any(word in message_lower for word in ['hello', 'hi', 'hey']):
            response_text = "Hello! I'm here to help you. What would you like to know?"
            intent = "greeting"
        elif any(word in message_lower for word in ['thank', 'thanks', 'bye']):
            response_text = "You're welcome! Feel free to ask if you need anything else."
            intent = "farewell"
        else:
            response_text = f"I understand you're asking about '{message}'. Let me help you with that. Could you provide a bit more context?"
            intent = "unknown"
        
        return {
            'response': response_text,
            'thread_id': thread_id,
            'conversation_id': self.active_conversations.get(thread_id, {}).get('conversation_id', 'fallback'),
            'turn_count': self.active_conversations.get(thread_id, {}).get('turn_count', 1),
            'current_phase': 'responding',
            'confidence_score': 0.5,
            'timestamp': datetime.now().isoformat(),
            'suggested_questions': [
                "Could you provide more details?",
                "What specific information are you looking for?",
                "Is there anything else I can help you with?"
            ],
            'related_topics': [],
            'sources': [],
            'total_sources': 0,
            'errors': [f"System fallback: {error_details}"],
            'warnings': ['Using emergency fallback response'],
            'intent': intent,
            'complexity': 'simple',
            'is_fallback': True,
            'processing_mode': 'emergency_fallback'
        }
    
    def _format_response(self, state: FreshConversationState, response_time: float) -> Dict[str, Any]:
        """Format the conversation state into API response format"""
        
        # Get the latest assistant message
        assistant_messages = [msg for msg in state.get('messages', []) if msg.get('type') == 'assistant']
        response_text = assistant_messages[-1].get('content', 'I apologize, but I was unable to generate a response.') if assistant_messages else 'Hello! How can I help you today?'
        
        return {
            'response': response_text,
            'thread_id': state['thread_id'],
            'conversation_id': state['conversation_id'],
            'turn_count': state['turn_count'],
            'current_phase': state['current_phase'],
            'confidence_score': state['confidence_score'],
            'timestamp': state['last_activity'],
            'suggested_questions': state.get('suggested_questions', []),
            'related_topics': state.get('topics_discussed', []),
            'sources': self._format_sources(state.get('search_results', [])),
            'total_sources': len(state.get('search_results', [])),
            'errors': state.get('error_messages', []),
            'warnings': state.get('warning_messages', []),
            'intent': state.get('user_intent', 'unknown'),
            'complexity': state.get('query_complexity', 'simple'),
            'response_time': response_time,
            'quality_score': state.get('overall_quality_score', 0.8),
            'processing_mode': 'full_graph'
        }
    
    def _format_sources(self, search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format search results into source format"""
        sources = []
        
        for i, result in enumerate(search_results[:5]):  # Limit to top 5 sources
            source = {
                'id': i + 1,
                'content': result.get('content', ''),
                'source': result.get('source', 'Unknown'),
                'relevance_score': result.get('score', 0.0),
                'metadata': result.get('metadata', {})
            }
            sources.append(source)
        
        return sources
    
    def get_conversation_history(self, thread_id: str, max_messages: int = 20) -> Dict[str, Any]:
        """Get conversation history for a thread"""
        try:
            if thread_id not in self.active_conversations:
                return {
                    'error': f'Conversation not found for thread {thread_id}',
                    'messages': [],
                    'thread_id': thread_id,
                    'conversation_id': '',
                    'turn_count': 0,
                    'current_phase': 'not_found',
                    'topics_discussed': []
                }
            
            state = self.active_conversations[thread_id]
            messages = state.get('messages', [])
            
            # Limit messages
            if len(messages) > max_messages:
                messages = messages[-max_messages:]
            
            return {
                'messages': messages,
                'thread_id': thread_id,
                'conversation_id': state['conversation_id'],
                'turn_count': state['turn_count'],
                'current_phase': state['current_phase'],
                'topics_discussed': state.get('topics_discussed', []),
                'entities_mentioned': state.get('entities_mentioned', []),
                'overall_quality_score': state.get('overall_quality_score', 0.8)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting conversation history: {e}")
            return {'error': f"Failed to get conversation history: {str(e)}"}
    
    def end_conversation(self, thread_id: str) -> Dict[str, Any]:
        """End a conversation"""
        try:
            if thread_id in self.active_conversations:
                state = self.active_conversations[thread_id]
                final_turn_count = state['turn_count']
                
                # Archive the conversation (for now just remove from active)
                del self.active_conversations[thread_id]
                
                self.logger.info(f"Ended conversation for thread {thread_id}")
                return {
                    'status': 'ended',
                    'thread_id': thread_id,
                    'final_turn_count': final_turn_count,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'not_found',
                    'thread_id': thread_id,
                    'message': 'Conversation not found'
                }
                
        except Exception as e:
            self.logger.error(f"Error ending conversation: {e}")
            return {'error': f"Failed to end conversation: {str(e)}"}
    
    def get_active_conversations(self) -> Dict[str, Any]:
        """Get list of active conversations"""
        try:
            active_threads = []
            
            for thread_id, state in self.active_conversations.items():
                thread_info = {
                    'thread_id': thread_id,
                    'conversation_id': state['conversation_id'],
                    'turn_count': state['turn_count'],
                    'current_phase': state['current_phase'],
                    'last_activity': state['last_activity'],
                    'user_id': state.get('user_id'),
                    'quality_score': state.get('overall_quality_score', 0.8)
                }
                active_threads.append(thread_info)
            
            return {
                'active_conversations': active_threads,
                'total_active': len(active_threads),
                'system_metrics': self.metrics
            }
            
        except Exception as e:
            self.logger.error(f"Error getting active conversations: {e}")
            return {'error': f"Failed to get active conversations: {str(e)}"}
    
    def _update_metrics(self, response_time: float, quality_score: float):
        """Update performance metrics"""
        
        # Update average response time
        current_avg = self.metrics['average_response_time']
        total_responses = self.metrics['successful_responses']
        
        if total_responses > 0:
            self.metrics['average_response_time'] = (current_avg * (total_responses - 1) + response_time) / total_responses
        else:
            self.metrics['average_response_time'] = response_time
        
        # Update average quality score
        current_quality_avg = self.metrics['context_quality_avg']
        if total_responses > 0:
            self.metrics['context_quality_avg'] = (current_quality_avg * (total_responses - 1) + quality_score) / total_responses
        else:
            self.metrics['context_quality_avg'] = quality_score
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get system health and status"""
        return {
            'status': 'healthy',
            'conversation_manager': 'fresh_direct_implementation',
            'active_conversations': len(self.active_conversations),
            'metrics': self.metrics,
            'components': {
                'context_manager': 'initialized',
                'memory_manager': 'initialized',
                'smart_router': 'initialized',
                'conversation_graph': 'initialized' if self.conversation_graph else 'simplified_mode'
            },
            'context_summary': self.context_manager.get_context_summary(),
            'memory_summary': self.memory_manager.get_context_summary(),
            'processing_mode': 'full_graph' if self.conversation_graph else 'simplified',
            'timestamp': datetime.now().isoformat()
        }
    
    # API compatibility methods
    def list_active_conversations(self):
        """Alias for get_active_conversations for API compatibility"""
        return self.get_active_conversations()
    
    def get_active_sessions(self):
        """Legacy method for backward compatibility"""
        return self.get_active_conversations() 