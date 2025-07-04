"""
FreshConversationNodes Module
Implements the nodes for the conversation flow
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from .fresh_conversation_state import FreshConversationState, SearchResult
from .fresh_smart_router import QueryIntent, QueryComplexity, Route


class FreshConversationNodes:
    """
    Implements the nodes for the conversation flow.
    Each node is responsible for a specific step in the conversation process.
    """
    
    def __init__(self, container=None):
        """Initialize with optional dependency container"""
        self.logger = logging.getLogger(__name__)
        self.container = container
        
        # Get dependencies from container if available
        self.query_engine = None
        self.llm_client = None
        self.state_manager = None
        self.memory_manager = None
        self.smart_router = None
        
        if container:
            # Get dependencies safely
            try:
                self.query_engine = container.get('query_engine')
            except KeyError:
                self.logger.warning("query_engine not found in container")
                
            try:
                self.llm_client = container.get('llm_client')
            except KeyError:
                self.logger.warning("llm_client not found in container")
                
            try:
                self.state_manager = container.get('state_manager')
            except KeyError:
                self.logger.warning("state_manager not found in container")
                
            try:
                self.memory_manager = container.get('memory_manager')
            except KeyError:
                self.logger.warning("memory_manager not found in container")
                
            try:
                self.smart_router = container.get('smart_router')
            except KeyError:
                self.logger.warning("smart_router not found in container")
        
        self.logger.info("FreshConversationNodes initialized")
    
    def initialize_conversation(self, state: FreshConversationState) -> FreshConversationState:
        """
        Initialize a new conversation
        
        Args:
            state: The initial conversation state
            
        Returns:
            FreshConversationState: Updated state
        """
        # Create a copy to avoid modifying the original
        new_state = FreshConversationState(**state)
        
        # Set initial values
        new_state['conversation_status'] = 'active'
        new_state['turn_count'] = 0
        new_state['created_at'] = datetime.now().isoformat()
        new_state['last_activity'] = datetime.now().isoformat()
        
        self.logger.info(f"Initialized conversation: {new_state['thread_id']}")
        return new_state
    
    def greet_user(self, state: FreshConversationState) -> FreshConversationState:
        """
        Generate a greeting for a new user
        
        Args:
            state: The current conversation state
            
        Returns:
            FreshConversationState: Updated state with greeting
        """
        # Create a copy to avoid modifying the original
        new_state = FreshConversationState(**state)
        
        # Generate greeting message
        greeting = "Hello! I'm your AI assistant. How can I help you today?"
        
        # Add greeting to state
        if self.state_manager:
            new_state = self.state_manager.add_message(new_state, 'assistant', greeting)
        else:
            # Fallback if state_manager not available
            messages = new_state.get('messages', [])
            messages.append({
                'type': 'assistant',
                'content': greeting,
                'timestamp': datetime.now().isoformat()
            })
            new_state['messages'] = messages
        
        return new_state
    
    def understand_intent(self, state: FreshConversationState) -> FreshConversationState:
        """
        Analyze the user's latest message and enrich the conversation state with a detailed query analysis.
        
        Args:
            state: The current conversation state with the latest user message
            
        Returns:
            FreshConversationState: Updated state with query analysis
        """
        self.logger.info("Processing understand_intent node")
        
        # Create a copy to avoid modifying the original
        new_state = FreshConversationState(**state)
        
        try:
            # Extract the latest user query from the state
            latest_query = None
            if self.state_manager:
                latest_query = self.state_manager.get_last_user_message(state)
            else:
                # Fallback if state_manager not available
                messages = state.get('messages', [])
                for message in reversed(messages):
                    if message.get('type') == 'user':
                        latest_query = message.get('content')
                        break
            
            if not latest_query:
                self.logger.warning("No user query found in state")
                new_state['has_errors'] = True
                new_state['error_messages'] = state.get('error_messages', []) + ["No user query found"]
                return new_state
            
            # Store original query
            new_state['original_query'] = latest_query
            
            # Invoke the FreshSmartRouter.analyze_query() method
            query_analysis = None
            if self.smart_router:
                query_analysis = self.smart_router.analyze_query(latest_query)
            else:
                self.logger.warning("SmartRouter not available, using default analysis")
                from .fresh_smart_router import QueryAnalysis, QueryIntent, QueryComplexity
                # Create a basic analysis
                query_analysis = QueryAnalysis(
                    intent=QueryIntent.INFORMATION_SEEKING,
                    complexity=QueryComplexity.MODERATE,
                    confidence=0.7,
                    keywords=latest_query.lower().split(),
                    entities=[],
                    is_contextual=False
                )
            
            # Populate the state with the results
            new_state['user_intent'] = query_analysis.intent.value
            new_state['query_complexity'] = query_analysis.complexity.value
            new_state['entities_mentioned'] = query_analysis.entities
            new_state['is_contextual'] = query_analysis.is_contextual
            
            # Create enhanced query if the query is contextual
            if query_analysis.is_contextual and self.llm_client:
                # Get conversation history for context
                recent_messages = []
                if self.state_manager:
                    recent_messages = self.state_manager.get_recent_messages(state, 5)
                else:
                    recent_messages = state.get('messages', [])[-5:]
                
                # Format conversation history
                conversation_history = "\n".join([
                    f"{msg.get('type')}: {msg.get('content')}" 
                    for msg in recent_messages
                ])
                
                # Create prompt for LLM
                prompt = f"""Given the following conversation history and the user's latest query, 
                create an enhanced search query that captures the full context of what the user is asking.
                
                Conversation history:
                {conversation_history}
                
                User's latest query: {latest_query}
                
                Enhanced search query:"""
                
                try:
                    enhanced_query = self.llm_client.generate(prompt)
                    new_state['processed_query'] = enhanced_query.strip()
                    self.logger.info(f"Enhanced contextual query: {enhanced_query.strip()}")
                except Exception as e:
                    self.logger.error(f"Failed to generate enhanced query: {e}")
                    new_state['processed_query'] = latest_query
            else:
                # If not contextual, use original query
                new_state['processed_query'] = latest_query
            
            self.logger.info(f"Query analysis complete: intent={new_state['user_intent']}, contextual={new_state['is_contextual']}")
            
        except Exception as e:
            self.logger.error(f"Error in understand_intent: {e}")
            new_state['has_errors'] = True
            new_state['error_messages'] = state.get('error_messages', []) + [f"Intent analysis error: {str(e)}"]
        
        return new_state
    
    def search_knowledge(self, state: FreshConversationState) -> FreshConversationState:
        """
        Execute a search against the QueryEngine using multiple strategies to ensure the best possible results.
        
        Args:
            state: The current conversation state with processed_query and original_query
            
        Returns:
            FreshConversationState: Updated state with search results
        """
        self.logger.info("Processing search_knowledge node")
        
        # Create a copy to avoid modifying the original
        new_state = FreshConversationState(**state)
        
        try:
            # Check if query_engine is available
            if not self.query_engine:
                self.logger.warning("QueryEngine not available")
                new_state['has_errors'] = True
                new_state['error_messages'] = state.get('error_messages', []) + ["Search engine unavailable"]
                return new_state
            
            # Get query information from state
            processed_query = state.get('processed_query')
            original_query = state.get('original_query')
            is_contextual = state.get('is_contextual', False)
            
            if not processed_query:
                self.logger.warning("No processed query available")
                new_state['has_errors'] = True
                new_state['error_messages'] = state.get('error_messages', []) + ["No query to search"]
                return new_state
            
            # Initialize search variables
            search_result = None
            search_attempts = []
            
            # Get conversation context for search
            conversation_context = {}
            recent_messages = []
            if self.state_manager:
                recent_messages = self.state_manager.get_recent_messages(state, 5)
            else:
                recent_messages = state.get('messages', [])[-5:]
            
            conversation_context['recent_messages'] = [
                {'role': msg.get('type'), 'content': msg.get('content')}
                for msg in recent_messages
            ]
            
            # Multi-Strategy Search Execution
            if is_contextual:
                # Attempt 1: Use processed_query
                try:
                    self.logger.info(f"Search attempt 1 (contextual): {processed_query}")
                    search_result = self.query_engine.process_query(
                        processed_query, 
                        conversation_context=conversation_context
                    )
                    search_attempts.append({
                        'strategy': 'processed_contextual',
                        'query': processed_query,
                        'result': search_result
                    })
                except Exception as e:
                    self.logger.warning(f"Search attempt 1 failed: {e}")
                
                # Attempt 2: If no significant sources, try original_query
                if not search_result or not search_result.get('sources') or len(search_result.get('sources', [])) < 2:
                    try:
                        self.logger.info(f"Search attempt 2 (original): {original_query}")
                        search_result = self.query_engine.process_query(
                            original_query,
                            conversation_context=conversation_context
                        )
                        search_attempts.append({
                            'strategy': 'original',
                            'query': original_query,
                            'result': search_result
                        })
                    except Exception as e:
                        self.logger.warning(f"Search attempt 2 failed: {e}")
                
                # Attempt 3: If still no results, extract main topic/entities
                if not search_result or not search_result.get('sources'):
                    entities = state.get('entities_mentioned', [])
                    keywords = state.get('processed_query', '').split()[:3]  # First 3 words
                    topic_query = ' '.join(entities + keywords).strip()
                    
                    if topic_query:
                        try:
                            self.logger.info(f"Search attempt 3 (topic): {topic_query}")
                            search_result = self.query_engine.process_query(
                                topic_query,
                                conversation_context=conversation_context
                            )
                            search_attempts.append({
                                'strategy': 'topic',
                                'query': topic_query,
                                'result': search_result
                            })
                        except Exception as e:
                            self.logger.warning(f"Search attempt 3 failed: {e}")
            else:
                # Check for LLM-extracted filters and perform structured counting
                try:
                    enhancer = getattr(self.query_engine, 'query_enhancer', None)
                    llm_filters = getattr(enhancer, 'last_filters', None) if enhancer else None
                except Exception:
                    llm_filters = None
                if llm_filters:
                    # Special case: count distinct buildings
                    if llm_filters.get('entity', '').lower() == 'building':
                        total_buildings = self.query_engine.count_documents(filters=None, distinct_key='building')
                        new_state['aggregation_result'] = {'type': 'buildings', 'count': total_buildings}
                        self.logger.info(f"Aggregation result (buildings): {total_buildings}")
                        return new_state

                    filters_copy = {k: v for k, v in llm_filters.items() if k != 'entity'}
                    total = self.query_engine.count_documents(filters=filters_copy or None)
                    new_state['aggregation_result'] = {'type': llm_filters.get('entity', 'items'), 'count': total}
                    self.logger.info(f"Aggregation result via LLM filters: {total} ({llm_filters})")
                    return new_state

                # Aggregation fallback for simple regex counting queries
                lowered_query = processed_query.lower()
                if lowered_query.startswith("how many incidents"):
                    total_inc = 0
                    if self.query_engine and hasattr(self.query_engine, "count_documents"):
                        total_inc = self.query_engine.count_documents("inc")
                    new_state['aggregation_result'] = {
                        'type': 'incidents',
                        'count': total_inc
                    }
                    self.logger.info(f"Aggregation result (incidents): {total_inc}")
                    return new_state
                if "router" in lowered_query and lowered_query.startswith("how many"):
                    total_rtr = 0
                    if self.query_engine and hasattr(self.query_engine, "count_documents"):
                        total_rtr = self.query_engine.count_documents("rtr")
                    new_state['aggregation_result'] = {
                        'type': 'routers',
                        'count': total_rtr
                    }
                    self.logger.info(f"Aggregation result (routers): {total_rtr}")
                    return new_state
                # Standard search for non-contextual queries
                try:
                    self.logger.info(f"Standard search: {processed_query}")
                    search_result = self.query_engine.process_query(
                        processed_query,
                        conversation_context=conversation_context
                    )
                    search_attempts.append({
                        'strategy': 'standard',
                        'query': processed_query,
                        'result': search_result
                    })
                except Exception as e:
                    self.logger.warning(f"Standard search failed: {e}")
            
            # Store all search attempts for analysis
            new_state['search_attempts'] = search_attempts
            
            # Process search results
            search_results_list = []
            context_chunks_list = []
            
            # Use the best result (last successful attempt)
            best_result = None
            for attempt in reversed(search_attempts):
                if attempt['result'] and attempt['result'].get('sources'):
                    best_result = attempt['result']
                    break
            
            if best_result and best_result.get('sources'):
                for source in best_result['sources']:
                    # Create SearchResult object
                    search_res = SearchResult(
                        content=source.get('text', ''),  # Query engine uses 'text' field
                        score=source.get('similarity_score', 0),
                        source=source.get('source', 'unknown'),
                        metadata=source.get('metadata', {})
                    )
                    search_results_list.append(search_res)
                    context_chunks_list.append(source.get('text', ''))
                
                # Update state with results
                new_state['search_results'] = search_results_list
                new_state['context_chunks'] = context_chunks_list
                new_state['query_engine_response'] = best_result.get('response', '')
                
                self.logger.info(f"Search completed with {len(search_results_list)} results")
            else:
                self.logger.warning("No search results found")
                new_state['search_results'] = []
                new_state['context_chunks'] = []
                new_state['query_engine_response'] = ""
        
        except Exception as e:
            self.logger.error(f"Error in search_knowledge: {e}")
            new_state['has_errors'] = True
            new_state['error_messages'] = state.get('error_messages', []) + [f"Search error: {str(e)}"]
            new_state['search_results'] = []
            new_state['context_chunks'] = []
        
        return new_state
    
    def generate_response(self, state: FreshConversationState) -> FreshConversationState:
        """
        Generate a final response for the user.
        
        Args:
            state: The current conversation state with context_chunks and search_results
            
        Returns:
            FreshConversationState: Updated state with the assistant's response
        """
        self.logger.info("Processing generate_response node")
        
        # Create a copy to avoid modifying the original
        new_state = FreshConversationState(**state)
        
        # If an aggregation result is present, craft an immediate response
        if 'aggregation_result' in state:
            agg = state['aggregation_result']
            if isinstance(agg, dict) and 'count' in agg:
                entity = agg.get('type', 'items')
                count_val = agg['count']
                response = f"There are {count_val} {entity} recorded in the system."
            else:
                count_val = agg if isinstance(agg, int) else None
                if count_val is not None:
                    response = f"There are {count_val} items recorded."
                else:
                    response = "I couldn't compute the count right now."
            # Add and return
            if self.state_manager:
                return self.state_manager.add_message(new_state, 'assistant', response)
            else:
                messages = new_state.get('messages', [])
                messages.append({'type': 'assistant', 'content': response, 'timestamp': datetime.now().isoformat()})
                new_state['messages'] = messages
                return new_state
        
        try:
            # Get required data from state
            context_chunks = state.get('context_chunks', [])
            search_results = state.get('search_results', [])
            user_intent = state.get('user_intent')
            original_query = state.get('original_query', '')
            
            response = ""
            
            # Handle different scenarios
            if user_intent == "goodbye":
                response = "Goodbye! Feel free to ask if you need anything else in the future."
            elif user_intent == "greeting":
                response = "Hello! How can I help you today?"
            elif user_intent == "help":
                response = "I'm here to help you find information. Just ask me any question, and I'll do my best to answer it using the available knowledge."
            else:
                # Generate response based on search results
                if self.llm_client and context_chunks:
                    # Construct detailed prompt for LLM
                    context_text = "\n\n".join([f"Source: {chunk}" for chunk in context_chunks])
                    
                    prompt = f"""Please answer the user's question based on the following context information.
                    If the context doesn't contain relevant information to answer the question fully, 
                    acknowledge what you don't know.
                    
                    Context:
                    {context_text}
                    
                    User's question: {original_query}
                    
                    Answer:"""
                    
                    try:
                        response = self.llm_client.generate(prompt)
                        self.logger.info("Generated response using LLM")
                    except Exception as e:
                        self.logger.error(f"LLM generation failed: {e}")
                        # Fall back to direct response
                        if search_results:
                            first_result = search_results[0]
                            response = f"Based on information from {first_result['source']}: {first_result['content'][:500]}..."
                        else:
                            response = "I couldn't generate a proper response. Please try asking in a different way."
                
                elif search_results:
                    # Fallback if LLM is not available
                    first_result = search_results[0]
                    response = f"Based on information from {first_result['source']}: {first_result['content'][:500]}..."
                    self.logger.info("Generated direct response from search results")
                
                else:
                    # No results found
                    response = "I couldn't find any specific information to answer your question. Could you please rephrase or provide more details?"
                    self.logger.warning("No information found to generate response")
            
            # Add response to state
            if self.state_manager:
                new_state = self.state_manager.add_message(new_state, 'assistant', response)
            else:
                # Fallback if state_manager not available
                messages = new_state.get('messages', [])
                messages.append({
                    'type': 'assistant',
                    'content': response,
                    'timestamp': datetime.now().isoformat()
                })
                new_state['messages'] = messages
            
            # Ensure search results and context chunks are preserved
            if 'search_results' not in new_state:
                new_state['search_results'] = search_results
            if 'context_chunks' not in new_state:
                new_state['context_chunks'] = context_chunks
            
            self.logger.info("Response generation complete")
            
        except Exception as e:
            self.logger.error(f"Error in generate_response: {e}")
            new_state['has_errors'] = True
            new_state['error_messages'] = state.get('error_messages', []) + [f"Response generation error: {str(e)}"]
            
            # Add fallback response
            if self.state_manager:
                new_state = self.state_manager.add_message(
                    new_state, 
                    'assistant', 
                    "I'm sorry, I encountered an error while generating a response. Please try again."
                )
            else:
                messages = new_state.get('messages', [])
                messages.append({
                    'type': 'assistant',
                    'content': "I'm sorry, I encountered an error while generating a response. Please try again.",
                    'timestamp': datetime.now().isoformat()
                })
                new_state['messages'] = messages
        
        return new_state
    
    def handle_clarification(self, state: FreshConversationState) -> FreshConversationState:
        """
        Handle cases where clarification is needed from the user
        
        Args:
            state: The current conversation state
            
        Returns:
            FreshConversationState: Updated state with clarification request
        """
        # Create a copy to avoid modifying the original
        new_state = FreshConversationState(**state)
        
        # Generate clarification message
        clarification_msg = "I'm not sure I understood your question. Could you please provide more details or rephrase it?"
        
        # Add clarification to state
        if self.state_manager:
            new_state = self.state_manager.add_message(new_state, 'assistant', clarification_msg)
        else:
            # Fallback if state_manager not available
            messages = new_state.get('messages', [])
            messages.append({
                'type': 'assistant',
                'content': clarification_msg,
                'timestamp': datetime.now().isoformat()
            })
            new_state['messages'] = messages
        
        return new_state 