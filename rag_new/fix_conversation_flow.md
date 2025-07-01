Looking at your conversation system, I can see the issue. The problem is in the `conversation_nodes.py` file, specifically in how it routes queries after understanding intent. When you ask a follow-up question about building access points, the system isn't properly routing it through the search pipeline.

Here's the fix:Now, let me also update the routing logic in the conversation graph:## Summary of the Fix

The main issues were:

1. **Intent Detection Problem**: The system wasn't properly identifying information-seeking queries. Questions like "What types of access points are used in Building A?" were not being routed to the search pipeline.

2. **Routing Logic Issue**: The `_route_after_understanding` method in `conversation_graph.py` was not defaulting to search for general queries.

3. **Search Strategy**: The search method wasn't trying multiple strategies when the initial search failed.

## Key Changes Made:

### In `conversation_nodes.py`:

1. **Enhanced Intent Detection**: Added more comprehensive patterns to detect information-seeking queries, including patterns for "types", "kinds", "list", etc.

2. **Default to Information Seeking**: Changed the logic to default most queries to "information_seeking" intent, which ensures they go through the search pipeline.

3. **Multiple Search Strategies**: Implemented a multi-strategy search approach that tries:
   - Enhanced/processed query
   - Original query
   - Keywords-based search
   - Topic entities search

4. **Better Logging**: Added detailed logging to track what's happening during search.

### In `conversation_graph.py`:

1. **Fixed Routing Logic**: Changed `_route_after_understanding` to:
   - Default to "search" for unknown/general intents
   - Always route "information_seeking" intent to search
   - Better handle edge cases

2. **Enhanced Logging**: Added more detailed logging to track routing decisions.

## How to Apply the Fix:

1. Replace the content of `src/conversation/conversation_nodes.py` with the fixed version above.

2. Update the `_route_after_understanding` method in `src/conversation/conversation_graph.py` with the enhanced routing logic.

3. Restart your application.

## Testing the Fix:

After applying these changes, your conversation flow should work correctly:

```
User: "What types of access points are used in Building A?"
Bot: [Should now search the knowledge base and return results about Cisco 3802I access points]

User: "Tell me more about them"
Bot: [Should provide additional details from the knowledge base]
```

The key insight is that the conversation system needs to be more aggressive about routing queries to the search pipeline rather than trying to respond directly. This ensures that questions about your knowledge base content actually search that content.

"""
LangGraph Conversation Nodes - FIXED VERSION
Individual processing nodes for the conversation flow with enhanced search routing
"""
import logging
from typing import Dict, Any, List
import re
from datetime import datetime

from .conversation_state import (
    ConversationState, ConversationPhase, MessageType, Message, SearchResult,
    add_message_to_state, get_conversation_history, should_end_conversation
)

class ConversationNodes:
    """Collection of LangGraph nodes for conversation processing"""
    
    def __init__(self, container=None):
        self.container = container
        self.logger = logging.getLogger(__name__)
        
        # Get system components
        if container:
            self.query_engine = container.get('query_engine')
            self.embedder = container.get('embedder') 
            self.llm_client = container.get('llm_client')
        else:
            self.query_engine = None
            self.embedder = None
            self.llm_client = None
    
    def greet_user(self, state: ConversationState) -> ConversationState:
        """Initial greeting and conversation setup"""
        self.logger.info("Processing greeting node")
        
        if not state['messages'] or state['turn_count'] == 0:
            # First interaction - provide greeting
            greeting = "Hello! I'm your AI assistant. I can help you find information, answer questions, and have a conversation about various topics. What would you like to know?"
            
            new_state = add_message_to_state(state, MessageType.ASSISTANT, greeting)
            new_state['current_phase'] = ConversationPhase.UNDERSTANDING
            return new_state
        
        return state
    
    def understand_intent(self, state: ConversationState) -> ConversationState:
        """Analyze user intent and extract key information"""
        self.logger.info("Processing intent understanding node")
        
        if not state['messages']:
            return state
        
        # Get latest user message
        user_messages = [msg for msg in state['messages'] if msg['type'] == MessageType.USER]
        if not user_messages:
            return state
        
        latest_message = user_messages[-1]
        user_input = latest_message['content']
        
        # Skip processing if empty message (initial greeting scenario)
        if not user_input.strip():
            self.logger.info("Empty user input detected, skipping intent analysis")
            return state
        
        # Create new state with updated values
        new_state = state.copy()
        new_state['original_query'] = user_input
        
        # Check if this is a contextual query that needs context
        if self._is_contextual_query(user_input, state):
            # Enhance query with conversation context
            enhanced_query = self._build_contextual_query(user_input, state)
            new_state['processed_query'] = enhanced_query
            new_state['is_contextual'] = True
            self.logger.info(f"Contextual query detected. Enhanced: '{enhanced_query}'")
        else:
            new_state['processed_query'] = user_input
            new_state['is_contextual'] = False
        
        # Track topic entities
        if 'building' in user_input.lower():
            match = re.search(r'building\s+([a-zA-Z0-9]+)', user_input, re.IGNORECASE)
            if match:
                new_state['current_topic'] = f"Building {match.group(1).upper()}"
                topic_entities = new_state.get('topic_entities', [])
                topic_entities.append(f"Building {match.group(1).upper()}")
                new_state['topic_entities'] = topic_entities[-5:]  # Keep last 5 entities
        
        # ENHANCED INTENT DETECTION - THIS IS THE KEY FIX
        # Check if query contains information-seeking patterns
        info_seeking_patterns = [
            r'\b(what|how|when|where|why|who|which)\b',
            r'\b(tell me|show me|find|search|list|describe|explain)\b',
            r'\b(types?|kinds?|categories|examples?)\b',
            r'\b(access points?|equipment|network|building|employee|manager)\b',
            r'\?$',  # Questions ending with ?
        ]
        
        is_info_seeking = any(re.search(pattern, user_input.lower()) for pattern in info_seeking_patterns)
        
        # Extract intent patterns
        intent_patterns = {
            "greeting": [r"\b(hello|hi|hey|good morning|good afternoon)\b"],
            "question": [r"\b(what|how|when|where|why|who)\b", r"\?"],
            "search": [r"\b(find|search|look for|show me)\b"],
            "comparison": [r"\b(compare|versus|vs|difference|better)\b"],
            "explanation": [r"\b(explain|tell me about|describe)\b"],
            "help": [r"\b(help|assist|support)\b"],
            "goodbye": [r"\b(bye|goodbye|see you|farewell)\b"],
            "clarification": [r"\b(what was|repeat|again|previous)\b"],
            "follow_up": [r"\b(more|also|additionally|furthermore|tell me more)\b"],
            "listing": [r"\b(list|show|what types?|what kinds?)\b"],
            "information_seeking": info_seeking_patterns  # Add our enhanced patterns
        }
        
        detected_intents = []
        for intent, patterns in intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, user_input.lower()):
                    detected_intents.append(intent)
                    break
        
        # CRITICAL FIX: Determine primary intent with better logic
        if "goodbye" in detected_intents:
            new_state['user_intent'] = "goodbye"
            new_state['current_phase'] = ConversationPhase.ENDING
        elif "greeting" in detected_intents and state['turn_count'] <= 2:
            new_state['user_intent'] = "greeting"
            new_state['current_phase'] = ConversationPhase.GREETING
        elif "help" in detected_intents and len(user_input.split()) < 5:
            # Only treat as help if it's a short help request
            new_state['user_intent'] = "help"
            new_state['current_phase'] = ConversationPhase.RESPONDING
        else:
            # IMPORTANT: Default to information seeking for most queries
            # This ensures we search the knowledge base for questions
            new_state['user_intent'] = "information_seeking"
            new_state['current_phase'] = ConversationPhase.SEARCHING
            
            # Special handling for specific query types
            if is_info_seeking or "question" in detected_intents or "search" in detected_intents:
                new_state['confidence_score'] = 0.9
            else:
                new_state['confidence_score'] = 0.7
        
        # Extract keywords
        keywords = self._extract_keywords(user_input)
        new_state['query_keywords'] = keywords
        
        # Update topics discussed
        if keywords:
            new_topics = new_state['topics_discussed'] + keywords[:3]  # Add top 3 keywords
            new_state['topics_discussed'] = new_topics[-10:]  # Keep only recent topics
        
        self.logger.info(f"Intent: {new_state['user_intent']}, Keywords: {keywords}")
        self.logger.info(f"Current phase after intent: {new_state['current_phase']}")
        self.logger.info(f"Is contextual: {new_state.get('is_contextual', False)}")
        self.logger.info(f"Is info seeking: {is_info_seeking}")
        return new_state
    
    def search_knowledge(self, state: ConversationState) -> ConversationState:
        """Search for relevant information using the query engine"""
        self.logger.info("Processing knowledge search node")
        
        new_state = state.copy()
        
        if not state.get('processed_query') or not self.query_engine:
            self.logger.warning("No query to search or query engine unavailable")
            new_state['has_errors'] = True
            new_state['error_messages'] = state.get('error_messages', []) + ["No query to search or query engine unavailable"]
            new_state['current_phase'] = ConversationPhase.RESPONDING
            new_state['requires_clarification'] = False
            new_state['search_results'] = []
            new_state['context_chunks'] = []
            return new_state

        try:
            # Create conversation context with bypass threshold for conversation queries
            conversation_context = {
                'bypass_threshold': True,  # Bypass similarity threshold for conversation consistency
                'is_contextual': state.get('is_contextual', False),
                'conversation_history': state.get('messages', []),
                'original_query': state.get('original_query', '')
            }
            
            # ENHANCED: Try multiple search strategies
            search_strategies = []
            
            # Strategy 1: Enhanced/processed query
            search_strategies.append(('enhanced', state['processed_query']))
            
            # Strategy 2: Original query
            if state['processed_query'] != state['original_query']:
                search_strategies.append(('original', state['original_query']))
            
            # Strategy 3: Keywords-based search
            if state.get('query_keywords'):
                keyword_query = ' '.join(state['query_keywords'][:3])
                if keyword_query and keyword_query not in [s[1] for s in search_strategies]:
                    search_strategies.append(('keywords', keyword_query))
            
            # Strategy 4: Topic entities
            if state.get('topic_entities'):
                for entity in state['topic_entities'][::-1]:  # Most recent first
                    if entity not in [s[1] for s in search_strategies]:
                        search_strategies.append(('entity', entity))
            
            all_results = []
            search_attempts = []
            
            # Try each strategy
            for strategy_name, query_text in search_strategies:
                self.logger.info(f"Search strategy '{strategy_name}': '{query_text}'")
                
                try:
                    search_result = self.query_engine.process_query(
                        query_text,
                        top_k=5,
                        conversation_context=conversation_context
                    )
                    
                    if search_result and search_result.get('sources'):
                        sources_count = len(search_result.get('sources', []))
                        self.logger.info(f"Strategy '{strategy_name}' found {sources_count} sources")
                        
                        # Store successful result
                        search_attempts.append({
                            'strategy': strategy_name,
                            'query': query_text,
                            'result': search_result,
                            'source_count': sources_count
                        })
                        
                        # If we got good results, we might stop here
                        if sources_count >= 3:
                            self.logger.info(f"Good results from strategy '{strategy_name}', using these")
                            break
                    else:
                        self.logger.info(f"Strategy '{strategy_name}' returned no sources")
                        
                except Exception as e:
                    self.logger.warning(f"Strategy '{strategy_name}' failed: {e}")
            
            # Use the best result
            best_result = None
            if search_attempts:
                # Sort by source count and take the best
                search_attempts.sort(key=lambda x: x['source_count'], reverse=True)
                best_result = search_attempts[0]['result']
                self.logger.info(f"Using results from strategy '{search_attempts[0]['strategy']}' with {search_attempts[0]['source_count']} sources")
            
            # Process the best search result
            if best_result and isinstance(best_result, dict):
                sources = best_result.get('sources', [])
                
                if sources:
                    search_results = []
                    context_chunks = []
                    
                    self.logger.info(f"Processing {len(sources)} sources from search result")
                    
                    for i, source in enumerate(sources):
                        # The source format from query_engine includes these fields
                        search_res = SearchResult(
                            content=source.get('text', ''),  # Note: query_engine uses 'text' field
                            score=source.get('similarity_score', source.get('score', 0)),
                            source=source.get('source', source.get('metadata', {}).get('filename', 'unknown')),
                            metadata=source.get('metadata', {})
                        )
                        search_results.append(search_res)
                        
                        # Add to context chunks
                        if search_res['content']:
                            context_chunks.append(search_res['content'])
                    
                    new_state['search_results'] = search_results
                    new_state['context_chunks'] = context_chunks
                    new_state['relevant_sources'] = sources
                    
                    # Store the query engine response if available
                    response = best_result.get('response', '')
                    new_state['query_engine_response'] = response if isinstance(response, str) else ''
                    
                    self.logger.info(f"Found {len(search_results)} relevant sources")
                else:
                    # No sources found
                    self.logger.info("No sources found in search result")
                    new_state['search_results'] = []
                    new_state['context_chunks'] = []
                    response = best_result.get('response', '')
                    new_state['query_engine_response'] = response if isinstance(response, str) else ''
                
                new_state['current_phase'] = ConversationPhase.RESPONDING
            else:
                # No valid search results
                self.logger.warning(f"No valid search results from any strategy")
                new_state['current_phase'] = ConversationPhase.RESPONDING
                new_state['requires_clarification'] = False
                new_state['search_results'] = []
                new_state['context_chunks'] = []
            
        except Exception as e:
            self.logger.error(f"Search failed: {e}", exc_info=True)
            new_state['has_errors'] = True
            new_state['error_messages'] = state.get('error_messages', []) + [f"Search error: {str(e)}"]
            new_state['current_phase'] = ConversationPhase.RESPONDING
        
        return new_state
    
    def generate_response(self, state: ConversationState) -> ConversationState:
        """Generate response using LLM with retrieved context"""
        self.logger.info("🎯 GENERATE_RESPONSE METHOD CALLED 🎯")
        self.logger.info("Processing response generation node")
        
        new_state = state.copy()
        
        # Check what we have to work with
        has_search_results = bool(state.get('search_results'))
        has_query_engine_response = bool(state.get('query_engine_response'))
        has_context_chunks = bool(state.get('context_chunks'))
        
        self.logger.info(f"Response generation state: search_results={has_search_results}, "
                        f"query_engine_response={has_query_engine_response}, "
                        f"context_chunks={has_context_chunks}")
        
        if not self.llm_client:
            # Even without LLM client, we can still provide a response using search results
            if state.get('search_results') and state['search_results']:
                # Use the first search result with source attribution
                first_result = state['search_results'][0]
                source = first_result.get('source', 'Unknown source')
                content = first_result['content'][:300]
                response = f"Based on information from {source}: {content}..."
                self.logger.info("Generated response using search results without LLM")
            elif state.get('query_engine_response'):
                response = state['query_engine_response']
                self.logger.info("Using query engine response without LLM")
            else:
                response = "I apologize, but I couldn't find relevant information to answer your question."
                self.logger.info("No search results available for response generation")
            
            # Preserve all search-related data when adding the response
            response_state = add_message_to_state(new_state, MessageType.ASSISTANT, response)
            # Ensure search_results are preserved in the response state
            if state.get('search_results'):
                response_state['search_results'] = state['search_results']
            if state.get('context_chunks'):
                response_state['context_chunks'] = state['context_chunks']
            if state.get('query_engine_response'):
                response_state['query_engine_response'] = state['query_engine_response']
            
            return response_state
        
        try:
            if state['user_intent'] == "goodbye":
                response = self._generate_farewell_response(state)
            elif state['user_intent'] == "greeting":
                response = self._generate_greeting_response(state)
            elif state['user_intent'] == "help":
                response = self._generate_help_response(state)
            else:
                # Generate contextual response based on search results
                response = self._generate_contextual_response(state)
            
            # Add response to conversation
            new_state = add_message_to_state(new_state, MessageType.ASSISTANT, response)
            
            # Set the conversation phase to RESPONDING to indicate we've generated a response
            new_state['current_phase'] = ConversationPhase.RESPONDING
            
            # Only generate follow-up questions and related topics occasionally to reduce LLM calls
            # Use turn count to determine when to generate suggestions (every 3 turns)
            if state.get('turn_count', 0) % 3 == 0:
                self.logger.info("🚀 Generating follow-up questions")
                new_state['suggested_questions'] = self._generate_follow_up_questions(state)
                self.logger.info(f"🎯 Generated {len(new_state['suggested_questions'])} suggested questions")
                new_state['related_topics'] = self._extract_related_topics(state)
            else:
                # Reuse previous suggestions if available
                new_state['suggested_questions'] = state.get('suggested_questions', [])
                new_state['related_topics'] = state.get('related_topics', [])
            
            # Set response confidence
            new_state['response_confidence'] = 0.8 if state.get('search_results') else 0.6
            
            # Log source information for debugging
            if state.get('search_results'):
                sources = [r.get('source', 'Unknown') for r in state['search_results'][:3]]
                self.logger.info(f"Response generated using sources: {sources}")
            else:
                self.logger.info("Response generated without search results")
            
            self.logger.info("Response generated successfully")
            
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            error_response = "I apologize, but I encountered an error generating a response. Please try rephrasing your question."
            new_state = add_message_to_state(new_state, MessageType.ASSISTANT, error_response)
            new_state['has_errors'] = True
            new_state['error_messages'] = state.get('error_messages', []) + [str(e)]
        
        return new_state


"""
LangGraph Conversation Flow - FIXED VERSION
Defines the conversation flow graph using LangGraph with improved routing
"""
import logging
from typing import Dict, Any, Literal, List
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
import os

from .conversation_state import (
    ConversationState, ConversationPhase, MessageType,
    add_message_to_state, _apply_memory_management
)
from .conversation_nodes import ConversationNodes

class ConversationGraph:
    """LangGraph-based conversation flow manager with improved routing"""
    
    def __init__(self, container=None, db_path: str = None):
        self.container = container
        self.logger = logging.getLogger(__name__)
        
        # Initialize nodes
        self.nodes = ConversationNodes(container)
        
        # Set up checkpointer for state persistence
        if db_path is None:
            # Default to data directory
            data_dir = os.path.join(os.path.dirname(__file__), "../../../data")
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, "conversations.db")
        
        self.checkpointer = MemorySaver()
        self.logger.info(f"Initialized Memory checkpointer for state persistence")
        
        # Build graph
        self.graph = self._build_graph()
        
        self.logger.info("ConversationGraph initialized with state persistence")
    
    def _build_graph(self) -> StateGraph:
        """Build the conversation flow graph"""
        
        # Create the graph using ConversationState directly
        workflow = StateGraph(ConversationState)
        
        # Add nodes directly without wrappers
        workflow.add_node("greet", self.nodes.greet_user)
        workflow.add_node("understand", self.nodes.understand_intent) 
        workflow.add_node("search", self.nodes.search_knowledge)
        workflow.add_node("respond", self.nodes.generate_response)
        workflow.add_node("clarify", self.nodes.handle_clarification)
        
        # Define the flow logic
        workflow.set_entry_point("greet")
        
        # From greet, go to understand
        workflow.add_edge("greet", "understand")
        
        # From understand, route based on intent
        workflow.add_conditional_edges(
            "understand",
            self._route_after_understanding,
            {
                "search": "search",
                "respond": "respond", 
                "end": END
            }
        )
        
        # From search, route based on results
        workflow.add_conditional_edges(
            "search",
            self._route_after_search,
            {
                "respond": "respond",
                "clarify": "clarify"
            }
        )
        
        # From respond, conditionally end or continue the conversation
        workflow.add_conditional_edges(
            "respond",
            self._route_conversation_end,
            {
                "continue": "understand",
                "end": END
            }
        )
        
        # From clarify, go back to understand for next turn
        workflow.add_edge("clarify", "understand")
        
        # Compile the graph with Memory checkpointer for state persistence
        compiled_graph = workflow.compile(
            checkpointer=self.checkpointer,
            interrupt_before=None,
            interrupt_after=None,
            debug=False
        )
        
        self.logger.info("Conversation graph compiled successfully with Memory state persistence")
        return compiled_graph
    
    def _route_after_understanding(self, state: ConversationState) -> Literal["search", "respond", "end"]:
        """Route after understanding user intent - ENHANCED VERSION"""
        
        try:
            user_intent = state.get('user_intent', 'general')
            turn_count = state.get('turn_count', 0)
            current_phase = state.get('current_phase', ConversationPhase.UNDERSTANDING)
            
            self.logger.info(f"Routing after understanding - intent: {user_intent}, turn: {turn_count}, phase: {current_phase}")
            
            # Check if this is a goodbye message
            if user_intent == "goodbye":
                self.logger.info("Routing to END - goodbye intent")
                return "end"
                
            # For greetings and help, go directly to respond ONLY if they're simple
            elif user_intent in ["greeting", "help"]:
                # Check if it's a simple greeting/help or if it contains a question
                original_query = state.get('original_query', '').lower()
                
                # If the greeting/help message also contains a question, search
                if any(word in original_query for word in ['what', 'how', 'when', 'where', 'why', 'which', '?']):
                    self.logger.info("Greeting/help contains question - routing to SEARCH")
                    return "search"
                else:
                    self.logger.info(f"Simple {user_intent} - routing to RESPOND")
                    return "respond"
                
            # CRITICAL FIX: For information seeking, ALWAYS search
            elif user_intent == "information_seeking":
                self.logger.info("Information seeking intent - routing to SEARCH")
                return "search"
                
            # For questions, search, or explanation intents
            elif user_intent in ["question", "search", "explanation"]:
                self.logger.info(f"{user_intent} intent - routing to SEARCH")
                return "search"
                
            # For follow-up questions, always search to maintain context
            elif user_intent == "follow_up" or state.get('is_contextual', False):
                self.logger.info("Follow-up or contextual query - routing to SEARCH")
                return "search"
                
            # DEFAULT: When in doubt, search!
            # This is the key fix - we default to searching rather than responding
            else:
                self.logger.info(f"Unknown/general intent '{user_intent}' - defaulting to SEARCH")
                return "search"
                
        except Exception as e:
            self.logger.error(f"Error in routing after understanding: {e}")
            # On error, default to search to try to find information
            return "search"
    
    def _route_after_search(self, state: ConversationState) -> Literal["respond", "clarify"]:
        """Route after searching knowledge base"""
        
        try:
            requires_clarification = state.get('requires_clarification', False)
            search_results = state.get('search_results', [])
            has_query_engine_response = bool(state.get('query_engine_response'))
            
            self.logger.info(f"Routing after search - clarification needed: {requires_clarification}, "
                           f"results: {len(search_results)}, has QE response: {has_query_engine_response}")
            
            # Only go to clarify if explicitly requested, not just because no results
            if requires_clarification:
                self.logger.info("Routing to CLARIFY - clarification explicitly required")
                return "clarify"
            else:
                # Always go to respond - let the response generator handle no results case
                self.logger.info("Routing to RESPOND")
                return "respond"
        except Exception as e:
            self.logger.error(f"Error in routing after search: {e}")
            return "respond"
    
    def _route_conversation_end(self, state: ConversationState) -> Literal["continue", "end"]:
        """Route to determine if conversation should end"""
        
        try:
            current_phase = state.get('current_phase', ConversationPhase.UNDERSTANDING)
            user_intent = state.get('user_intent', None)
            turn_count = state.get('turn_count', 0)
            
            # Log the routing decision factors
            self.logger.info(f"Routing conversation end - phase: {current_phase}, "
                           f"intent: {user_intent}, turns: {turn_count}")
            
            # End conversation if:
            # 1. Explicitly in ending phase or goodbye intent
            # 2. Too many turns (to prevent infinite loops)
            # 3. Error count is too high
            # 4. Single-turn question has been answered (for API calls)
            should_end = (
                current_phase == ConversationPhase.ENDING or 
                user_intent == "goodbye" or
                turn_count > 20 or  # Limit total turns to prevent loops
                state.get('retry_count', 0) > 3 or  # Too many retries
                len(state.get('error_messages', [])) > 5  # Too many errors
            )
            
            if should_end:
                self.logger.info(f"Ending conversation: phase={current_phase}, intent={user_intent}, turns={turn_count}")
                return "end"
            else:
                self.logger.info("Continuing conversation")
                return "continue"
                
        except Exception as e:
            self.logger.error(f"Error in routing conversation end: {e}")
            # Default to ending conversation on error to prevent loops
            return "end"
    
    def process_message(self, thread_id: str, user_message: str, config: Dict[str, Any] = None) -> ConversationState:
        """Process a user message through the conversation graph using LangGraph state management"""
        
        try:
            # Create config with thread_id for LangGraph state management
            if config is None:
                config = {}
            config["configurable"] = {"thread_id": thread_id}
            # Set recursion limit to prevent infinite loops
            config["recursion_limit"] = 100
            
            # Get current state from checkpointer or create new one
            current_state = self._get_or_create_state(thread_id)
            
            # Add user message to state if it's not empty (for initial greeting)
            if user_message.strip():
                current_state = add_message_to_state(current_state, MessageType.USER, user_message)
            
            # Log the state before processing
            self.logger.info(f"Processing message for thread {thread_id}: '{user_message[:50]}...'")
            self.logger.info(f"Current turn count: {current_state.get('turn_count', 0)}")
            
            # Run the graph with LangGraph state management
            result = self.graph.invoke(
                current_state, 
                config=config
            )
            
            # Apply memory management to prevent leaks
            result = _apply_memory_management(result)
            
            # Safely access current_phase with a default value if it doesn't exist
            current_phase = result.get('current_phase', 'UNKNOWN')
            self.logger.info(f"Conversation processed successfully for thread {thread_id}, phase: {current_phase}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing conversation: {e}", exc_info=True)
            
            # Handle error gracefully
            error_response = "I apologize, but I encountered an error processing your message. Please try again."
            
            # Try to get current state for error handling
            try:
                current_state = self._get_or_create_state(thread_id)
            except:
                # If we can't get state, create a minimal one
                from .conversation_state import create_conversation_state
                current_state = create_conversation_state(thread_id)
            
            error_state = add_message_to_state(current_state, MessageType.ASSISTANT, error_response)
            error_state['has_errors'] = True
            error_state['error_messages'] = current_state.get('error_messages', []) + [str(e)]
            
            # Apply memory management to error state as well
            error_state = _apply_memory_management(error_state)
            
            return error_state
    
    def _get_or_create_state(self, thread_id: str) -> ConversationState:
        """Get existing state from checkpointer or create new conversation state"""
        
        try:
            # Try to get existing state from checkpointer
            config = {"configurable": {"thread_id": thread_id}}
            checkpoint = self.checkpointer.get_tuple(config)
            
            if checkpoint and checkpoint.checkpoint:
                # Return existing state
                state = checkpoint.checkpoint.get("channel_values", {})
                if state:
                    self.logger.info(f"Retrieved existing conversation state for thread {thread_id}")
                    return state
            
            # Create new state if none exists
            from .conversation_state import create_conversation_state
            new_state = create_conversation_state(thread_id)
            self.logger.info(f"Created new conversation state for thread {thread_id}")
            return new_state
            
        except Exception as e:
            self.logger.error(f"Error getting/creating state for thread {thread_id}: {e}")
            # Fallback to creating new state
            from .conversation_state import create_conversation_state
            return create_conversation_state(thread_id)
    
    def get_conversation_history(self, thread_id: str, max_messages: int = 20) -> Dict[str, Any]:
        """Get conversation history for a thread using LangGraph state"""
        
        try:
            state = self._get_or_create_state(thread_id)
            
            messages = state.get('messages', [])[-max_messages:] if state.get('messages') else []
            
            return {
                'messages': [
                    {
                        'type': msg['type'].value if hasattr(msg['type'], 'value') else str(msg['type']),
                        'content': msg['content'],
                        'timestamp': msg['timestamp'],
                        'metadata': msg['metadata']
                    }
                    for msg in messages
                ],
                'thread_id': thread_id,
                'conversation_id': state.get('conversation_id', ''),
                'turn_count': state.get('turn_count', 0),
                'current_phase': state.get('current_phase', ConversationPhase.UNDERSTANDING).value if hasattr(state.get('current_phase'), 'value') else str(state.get('current_phase', 'understanding')),
                'topics_discussed': state.get('topics_discussed', [])
            }
        except Exception as e:
            self.logger.error(f"Error getting conversation history for thread {thread_id}: {e}")
            return {
                'messages': [],
                'thread_id': thread_id,
                'conversation_id': '',
                'turn_count': 0,
                'current_phase': 'understanding',
                'topics_discussed': []
            }
    
    def list_conversation_threads(self) -> List[str]:
        """List all conversation threads stored in checkpointer"""
        
        try:
            # Get all stored threads from checkpointer
            if not self.checkpointer or not hasattr(self.checkpointer, 'storage'):
                self.logger.warning("Checkpointer not available or missing storage attribute")
                return []
                
            # For MemorySaver, we need to access the internal storage
            try:
                # MemorySaver stores data in a dict
                storage = getattr(self.checkpointer, 'storage', {})
                thread_ids = []
                
                # Extract thread_ids from storage keys
                for key in storage.keys():
                    if isinstance(key, dict) and 'thread_id' in key:
                        thread_ids.append(key['thread_id'])
                
                self.logger.info(f"Found {len(thread_ids)} conversation threads in memory")
                return list(set(thread_ids))  # Remove duplicates
                
            except Exception as storage_error:
                self.logger.error(f"Storage access error: {storage_error}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error listing conversation threads: {e}")
            return []        