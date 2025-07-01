"""
LangGraph Conversation Nodes
Individual processing nodes for the conversation flow
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
        
        if not state.messages or state.turn_count == 0:
            # First interaction - provide greeting
            greeting = "Hello! I'm your AI assistant. I can help you find information, answer questions, and have a conversation about various topics. What would you like to know?"
            
            new_state = add_message_to_state(state, MessageType.ASSISTANT, greeting)
            new_state.current_phase = ConversationPhase.UNDERSTANDING
            return new_state
        
        return state
    
    def understand_intent(self, state: ConversationState) -> ConversationState:
        """Analyze user intent and extract key information"""
        self.logger.info("Processing intent understanding node")
        
        if not state.messages:
            return state
        
        # Get latest user message
        user_messages = [msg for msg in state.messages if msg.type == MessageType.USER]
        if not user_messages:
            return state
        
        latest_message = user_messages[-1]
        user_input = latest_message.content
        
        # Skip processing if empty message (initial greeting scenario)
        if not user_input.strip():
            self.logger.info("Empty user input detected, skipping intent analysis")
            return state
        
        # Create new state with updated values
        new_state = state
        new_state.original_query = user_input
        
        # Check if this is a contextual query that needs context
        if self._is_contextual_query(user_input, state):
            # Enhance query with conversation context
            enhanced_query = self._build_contextual_query(user_input, state)
            new_state.processed_query = enhanced_query
            new_state.is_contextual = True
            self.logger.info(f"Contextual query detected. Enhanced: '{enhanced_query}'")
        else:
            new_state.processed_query = user_input
            new_state.is_contextual = False
        
        # Track topic entities
        if 'building' in user_input.lower():
            match = re.search(r'building\s+([a-zA-Z0-9]+)', user_input, re.IGNORECASE)
            if match:
                new_state.current_topic = f"Building {match.group(1).upper()}"
                topic_entities = new_state.topic_entities
                topic_entities.append(f"Building {match.group(1).upper()}")
                new_state.topic_entities = topic_entities[-5:]  # Keep last 5 entities
        
        # ENHANCED INTENT DETECTION - THIS IS THE KEY FIX
        # Check if query contains information-seeking patterns
        info_seeking_patterns = [
            r'\b(what|how|when|where|why|who|which)\b',
            r'\b(tell me|show me|find|search|list|describe|explain)\b',
            r'\b(types?|kinds?|categories|examples?)\b',
            r'\b(access points?|equipment|network|building|employee|manager|incident|document)\b',
            r'\?$',  # Questions ending with ?
            r'\b(can you|could you|please)\b',  # Polite requests
            r'\b(information|details|data)\b',  # Information requests
        ]
        
        is_info_seeking = any(re.search(pattern, user_input.lower()) for pattern in info_seeking_patterns)
        
        # Enhanced intent patterns with more comprehensive detection
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
            new_state.user_intent = "goodbye"
            new_state.current_phase = ConversationPhase.ENDING
        elif "greeting" in detected_intents and state.turn_count <= 2:
            new_state.user_intent = "greeting"
            new_state.current_phase = ConversationPhase.GREETING
        elif "help" in detected_intents and len(user_input.split()) < 5:
            # Only treat as help if it's a short help request
            new_state.user_intent = "help"
            new_state.current_phase = ConversationPhase.RESPONDING
        else:
            # IMPORTANT: Default to information seeking for most queries
            # This ensures we search the knowledge base for questions
            new_state.user_intent = "information_seeking"
            new_state.current_phase = ConversationPhase.SEARCHING
            
            # Special handling for specific query types
            if is_info_seeking or "question" in detected_intents or "search" in detected_intents:
                new_state.confidence_score = 0.9
            else:
                new_state.confidence_score = 0.7
        
        # Extract keywords
        keywords = self._extract_keywords(user_input)
        new_state.query_keywords = keywords
        
        # Update topics discussed
        if keywords:
            new_topics = new_state.topics_discussed + keywords[:3]  # Add top 3 keywords
            new_state.topics_discussed = new_topics[-10:]  # Keep only recent topics
        
        self.logger.info(f"Intent: {new_state.user_intent}, Keywords: {keywords}")
        self.logger.info(f"Current phase after intent: {new_state.current_phase}")
        self.logger.info(f"Is contextual: {new_state.is_contextual}")
        self.logger.info(f"Is info seeking: {is_info_seeking}")
        return new_state
    
    def search_knowledge(self, state: ConversationState) -> ConversationState:
        """Search for relevant information using the query engine"""
        self.logger.info("Processing knowledge search node")
        
        new_state = state
        
        if not state.processed_query or not self.query_engine:
            self.logger.warning("No query to search or query engine unavailable")
            new_state.has_errors = True
            new_state.error_messages.append("No query to search or query engine unavailable")
            new_state.current_phase = ConversationPhase.RESPONDING
            new_state.requires_clarification = False
            new_state.search_results = []
            new_state.context_chunks = []
            return new_state

        try:
            # Create conversation context with bypass threshold for conversation queries
            conversation_context = {
                'bypass_threshold': True,  # Bypass similarity threshold for conversation consistency
                'is_contextual': state.is_contextual,
                'conversation_history': state.messages,
                'original_query': state.original_query
            }
            
            # ENHANCED: Try multiple search strategies
            search_strategies = []
            
            # Strategy 1: Enhanced/processed query
            search_strategies.append(('enhanced', state.processed_query))
            
            # Strategy 2: Original query
            if state.processed_query != state.original_query:
                search_strategies.append(('original', state.original_query))
            
            # Strategy 3: Keywords-based search
            if state.query_keywords:
                keyword_query = ' '.join(state.query_keywords[:3])
                if keyword_query and keyword_query not in [s[1] for s in search_strategies]:
                    search_strategies.append(('keywords', keyword_query))
            
            # Strategy 4: Topic entities
            if state.topic_entities:
                for entity in state.topic_entities[::-1]:  # Most recent first
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
                    
                    # Handle both regular search results and aggregation results
                    sources_count = 0
                    is_aggregation = False
                    
                    if search_result:
                        if search_result.get('sources'):
                            sources_count = len(search_result.get('sources', []))
                            self.logger.info(f"Strategy '{strategy_name}' found {sources_count} sources")
                        elif search_result.get('query_type') == 'aggregation' and search_result.get('response'):
                            # Aggregation results don't have sources but have direct responses
                            sources_count = 1  # Treat aggregation as having one "result"
                            is_aggregation = True
                            self.logger.info(f"Strategy '{strategy_name}' returned aggregation response")
                        
                        if sources_count > 0:
                            # Store successful result
                            search_attempts.append({
                                'strategy': strategy_name,
                                'query': query_text,
                                'result': search_result,
                                'source_count': sources_count,
                                'is_aggregation': is_aggregation
                            })
                            
                            # If we got good results, we might stop here
                            if sources_count >= 3 or is_aggregation:
                                break
                except Exception as e:
                    self.logger.warning(f"Search strategy '{strategy_name}' failed: {e}")
            
            new_state.search_attempts = search_attempts
            
            # Resolve conflicts if multiple strategies returned results
            if len(search_attempts) > 1:
                # Placeholder for conflict resolution - for now, just take the first one
                self.logger.info("Multiple search strategies successful, taking first result set")
                final_result = search_attempts[0]['result']
            elif len(search_attempts) == 1:
                final_result = search_attempts[0]['result']
            else:
                final_result = None
            
            # Process final search result
            if final_result:
                if final_result.get('query_type') == 'aggregation':
                    # Handle aggregation result
                    new_state.is_aggregation = True
                    new_state.aggregation_response = final_result.get('response', '')
                    new_state.search_results = []
                    new_state.context_chunks = []
                    self.logger.info(f"Aggregation query detected, response: {new_state.aggregation_response}")
                else:
                    # Handle standard search result
                    sources = final_result.get('sources', [])
                    
                    new_state.search_results = [
                        SearchResult(
                            doc_id=s.get('doc_id', ''),
                            source=s.get('source', ''),
                            text=s.get('text', ''),
                            relevance_score=s.get('similarity_score', 0.0),
                            certainty_score=s.get('certainty_score', 0.0)
                        ) for s in sources
                    ]
                    
                    # Sort by relevance and certainty
                    new_state.search_results.sort(key=lambda x: (x.relevance_score, x.certainty_score), reverse=True)
                    
                    # Build context from top results
                    new_state.context_chunks = [res.text for res in new_state.search_results[:3]]
            
            # Determine if we need clarification
            if not new_state.search_results and not new_state.is_aggregation:
                self.logger.info("No definitive search results, requires clarification")
                new_state.requires_clarification = True
                    else:
                new_state.requires_clarification = False

            new_state.current_phase = ConversationPhase.RESPONDING
            return new_state
            
        except Exception as e:
            self.logger.error(f"Error during knowledge search: {e}", exc_info=True)
            new_state.has_errors = True
            new_state.error_messages.append(f"Error during knowledge search: {e}")
            new_state.current_phase = ConversationPhase.RESPONDING
        return new_state
    
    def generate_response(self, state: ConversationState) -> ConversationState:
        """Generate a response based on the current conversation state"""
        self.logger.info("Processing response generation node")
        
        new_state = state

        # If it's an aggregation query, the response is already generated
        if new_state.is_aggregation:
            response_text = new_state.aggregation_response
            new_state = add_message_to_state(new_state, MessageType.ASSISTANT, response_text)
            new_state.response_confidence = 0.95  # High confidence for aggregations
            return new_state
            
        # If no context but we have a user query, try a direct LLM call for general knowledge
        if not new_state.context_chunks and new_state.original_query:
            self.logger.info("No context found, attempting direct LLM call")
            response_text = self._generate_general_response(new_state)
            new_state = add_message_to_state(new_state, MessageType.ASSISTANT, response_text)
            new_state.response_confidence = 0.5 # Lower confidence for general knowledge
            return new_state
            
        # If we have context, generate a contextual response
        if new_state.context_chunks:
            response_text = self._generate_contextual_response(new_state)
            new_state = add_message_to_state(new_state, MessageType.ASSISTANT, response_text)
            new_state.response_confidence = max(s.relevance_score for s in new_state.search_results) if new_state.search_results else 0.7
            
            # Generate follow-up questions for better user experience
            new_state.suggested_questions = self._generate_follow_up_questions(new_state)
            
            return new_state
            
        # Fallback response if no other conditions are met
        fallback_response = "I couldn't find a specific answer, but I'm here to help. Could you try rephrasing your question?"
        new_state = add_message_to_state(new_state, MessageType.ASSISTANT, fallback_response)
        new_state.response_confidence = 0.2
        return new_state
    
    def handle_clarification(self, state: ConversationState) -> ConversationState:
        """Handle requests for clarification"""
        self.logger.info("Processing clarification node")
        
        clarification = "I'd like to help you better. Could you provide more specific details about what you're looking for?"
        
        if state.get('clarification_questions'):
            clarification = f"{clarification} For example: {', '.join(state['clarification_questions'][:2])}"
        
        new_state = add_message_to_state(state, MessageType.ASSISTANT, clarification)
        new_state['current_phase'] = ConversationPhase.CLARIFYING
        return new_state
    
    def check_conversation_end(self, state: ConversationState) -> ConversationState:
        """Check if conversation should end"""
        self.logger.info("Processing conversation end check")
        
        new_state = state.copy()
        
        if should_end_conversation(state):
            farewell = "Thank you for our conversation! Feel free to ask if you have any other questions."
            new_state = add_message_to_state(new_state, MessageType.ASSISTANT, farewell)
            new_state['current_phase'] = ConversationPhase.ENDING
        
        return new_state
    
    def _is_contextual_query(self, query: str, state: ConversationState) -> bool:
        """Determine if a query is contextual and requires conversation history"""
        query_lower = query.lower()
        
        # Keywords that indicate contextual queries
        contextual_keywords = [
            'this', 'that', 'these', 'those', 'it', 'they', 'them', 
            'he', 'she', 'his', 'her', 'their', 'theirs',
            'more about', 'tell me more', 'what about', 'how about',
            'also', 'another', 'other', 'anything else',
            'like that', 'such as', 'for example'
        ]
        
        for keyword in contextual_keywords:
            if keyword in query_lower:
                return True
        
        # Check if query is very short and likely refers to previous context
        if len(query.split()) <= 4 and state.turn_count > 1:
            self.logger.info("Short query detected with conversation history - treating as contextual")
            return True
            
        # If we have previous messages, always consider some level of context
        if state.messages and len(state.messages) > 2:
            self.logger.info("Conversation has history - treating with partial context")
            # Not fully contextual but we'll maintain some conversation awareness
            return False # Not strictly contextual, but the system should be aware
        
        return False
    
    def _build_contextual_query(self, current_query: str, state: ConversationState) -> str:
        """Enhance a query with context from conversation history"""
        
        if not self.llm_client:
            self.logger.warning("LLM client not available, returning original query")
            return current_query
        
        # Get recent conversation history
        recent_messages = state.messages[-4:]  # Last 2 exchanges
        
        context_str = ""
        for msg in recent_messages:
            role = "User" if msg.type == MessageType.USER else "Assistant"
            context_str += f"{role}: {msg.content}\n"
            
        prompt = f"""Based on the following conversation history, rewrite the user's latest query to be a standalone, complete question.

Conversation History:
{context_str}

User's Latest Query: "{current_query}"

Rewrite the user's query to be self-contained:"""

        try:
            enhanced_query = self.llm_client.generate(prompt, max_tokens=100)
            return enhanced_query.strip()
        except Exception as e:
            self.logger.error(f"Error enhancing query with LLM: {e}")
            return current_query # Fallback to original query
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        # A simple keyword extraction for now
        stop_words = set(['a', 'an', 'the', 'is', 'in', 'it', 'of', 'for', 'on', 'with'])
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        return keywords[:10]
    
    def _is_simple_followup_question(self, query: str, conversation_history: List[Message]) -> bool:
        """Use LLM to detect if this is a simple follow-up question requiring concise answer"""
        
        if not self.llm_client:
            return False
        
        context = ""
        recent_messages = conversation_history[-4:]
        for msg in recent_messages:
            role = "User" if msg.type == MessageType.USER else "Assistant"
            content = msg.content[:200]  # Truncate for context
            context += f"{role}: {content}\n"
        
        prompt = f"""Analyze the following query in the context of the conversation history. Is this a simple follow-up question that can likely be answered with information already presented?

Conversation:
{context}

Query: "{query}"

Answer with only 'yes' or 'no'."""
        
        try:
            response = self.llm_client.generate(prompt, max_tokens=5)
            return 'yes' in response.lower()
        except Exception as e:
            self.logger.error(f"LLM detection for simple follow-up failed: {e}")
            return False

    def _generate_contextual_response(self, state: ConversationState) -> str:
        """Generate a response using search results and conversation context"""
        
        if not self.llm_client:
            return "I have found some information, but I'm having trouble formulating a response right now."

        if state.is_aggregation:
             return state.aggregation_response

            else:
                # Enhanced response generation with clean formatting
                context_parts = []
            for i, result in enumerate(state.search_results[:3], 1):
                content = result.text[:400]
                context_parts.append(f"Source {i} ({result.source}, relevance: {result.relevance_score:.2f}):\n{content}")
                
                context_text = "\n\n".join(context_parts)
                
            prompt = f\"\"\"You are a professional assistant providing clean, well-formatted responses. Answer the user's query based on the available information.

Query: "{state.original_query}"

Available Information:
{context_text}

Response Guidelines:
1. Provide a direct, clear answer to the user's question
2. Use professional formatting:
   - Tables for structured data (use | separators)
   - Bullet points for lists
   - Clean headings for organization
3. Do NOT include technical metadata, source numbers, or relevance scores
4. Do NOT show raw source snippets in your response
5. Reference sources naturally (e.g., "Based on the incident data..." instead of "Source 1 shows...")
6. Focus on delivering the actual information requested

Generate a clean, professional response:\"\"\"
                
                try:
                    if self.llm_client:
                        response = self.llm_client.generate(prompt, max_tokens=600, temperature=0.7)
                        return response.strip()
                except Exception as e:
                    self.logger.error(f"LLM generation failed: {e}")
        
        # Fallback response
        return self._generate_general_response(state)
    
    def _generate_greeting_response(self, state: ConversationState) -> str:
        """Generate greeting response"""
        greetings = [
            "Hello! How can I help you today?",
            "Hi there! What would you like to know?",
            "Greetings! I'm here to assist you with any questions you might have.",
            "Hello! Feel free to ask me anything you'd like to know about."
        ]
        
        # Simple selection based on turn count
        return greetings[state.turn_count % len(greetings)]
    
    def _generate_farewell_response(self, state: ConversationState) -> str:
        """Generate farewell response"""
        farewells = [
            "Goodbye! It was great talking with you.",
            "Thank you for the conversation! Have a wonderful day!",
            "Farewell! Feel free to come back anytime you have questions.",
            "Goodbye! I hope I was able to help you today."
        ]
        
        return farewells[state.turn_count % len(farewells)]
    
    def _generate_help_response(self, state: ConversationState) -> str:
        """Generate help response"""
        return \"\"\"I'm here to help you with various tasks! Here's what I can do:

• Answer questions about topics in my knowledge base
• Help you find specific information
• Provide explanations and clarifications
• Have conversations about various subjects

Just ask me anything you'd like to know, and I'll do my best to provide a helpful response!\"\"\"
    
    def _generate_general_response(self, state: ConversationState) -> str:
        """Generate general response when no specific context is available"""
        
        query = state.original_query
        conversation_history = state.messages
        
        if not query:
            return "I'd be happy to help! Could you please tell me what you'd like to know about?"
        
        # Check if this might be a follow-up question even without search results
        is_simple_followup = self._is_simple_followup_question(query, conversation_history)
        
        if is_simple_followup and conversation_history:
            # Try to answer based on conversation context even without search results
            recent_context = ""
            for msg in conversation_history[-4:]:
                role = "User" if msg.type == MessageType.USER else "Assistant"
                content = msg.content[:300]
                recent_context += f"{role}: {content}\n"
            
            # Use LLM to generate response based on conversation context
            prompt = f\"\"\"The user is asking a follow-up question but no search results were found. Try to answer based on the recent conversation context.

Recent Conversation:
{recent_context}

Current Question: "{query}"

Instructions:
1. If the conversation context contains relevant information to answer the question, provide a direct answer
2. If you can identify what "these", "those", "them" refers to from the context, list those items
3. If the context mentions numbers (like "5 documents"), try to identify what those items are
4. Be concise and direct
5. If you truly cannot answer from context, acknowledge this politely

Provide a helpful response:\"\"\"
            
            try:
                if self.llm_client:
                    response = self.llm_client.generate(prompt, max_tokens=300, temperature=0.1)
                    return response.strip()
            except Exception as e:
                self.logger.error(f"LLM generation failed for context-based response: {e}")
        
        # Generate a helpful response acknowledging the query
        return f\"\"\"I understand you're asking about "{query}". While I don't have specific information readily available on this topic right now, I'd be happy to help you in other ways. 

Could you provide more details about what specifically you'd like to know? This would help me give you a more targeted response.\"\"\"
    
    def _generate_follow_up_questions(self, state: ConversationState) -> List[str]:
        """Generate intelligent follow-up questions using LLM and search context"""
        
        self.logger.info("🔥 FOLLOW-UP QUESTIONS METHOD CALLED 🔥")
        
        # Check if we should skip LLM generation to reduce API calls
        # Only generate new questions every few turns or when we have new search results
        turn_count = state.turn_count
        has_new_search_results = len(state.search_results) > 0
        
        # If we have previous suggestions and it's not time to refresh, reuse them
        if (state.suggested_questions and 
            len(state.suggested_questions) >= 2 and 
            turn_count % 3 != 0 and 
            not has_new_search_results):
            self.logger.info("Reusing existing suggested questions to reduce LLM calls")
            return state.suggested_questions
        
        try:
            self.logger.info("Starting follow-up question generation")
            
            # If no LLM client, return basic fallback questions
            if not self.llm_client:
                self.logger.warning("No LLM client available, using fallback questions")
                return self._generate_fallback_follow_up_questions(state)
            
            # Get context from search results and conversation
            context_info = self._build_suggestion_context(state)
            self.logger.info(f"Built context info with length: {len(context_info)}")
            
            if not context_info:
                self.logger.warning("No context info available, using fallback questions")
                return self._generate_fallback_follow_up_questions(state)
            
            # Create a focused prompt for generating relevant follow-up questions
            prompt = f\"\"\"Based on the user's question and the information found, generate 3-4 intelligent follow-up questions that would be genuinely helpful.

User's Question: "{state.original_query}"

Information Found:
{context_info[:1000]}

Generate follow-up questions that:
1. Explore specific details mentioned in the information
2. Ask about practical applications or next steps
3. Clarify relationships between entities/concepts

Make the questions specific, actionable, and based on the actual content found. Avoid generic questions.

Format as a simple list:
- Question 1
- Question 2
- Question 3\"\"\"

            self.logger.info("Sending prompt to LLM for follow-up questions")
            response = self.llm_client.generate(prompt, max_tokens=200, temperature=0.7)
            self.logger.info(f"LLM response length: {len(response)}")
            
            # Parse the questions from the response
            questions = self._parse_follow_up_questions(response)
            self.logger.info(f"Parsed {len(questions)} questions from LLM response")
            
            if questions:
                self.logger.info(f"Generated {len(questions)} contextual follow-up questions")
                return questions
            else:
                self.logger.warning("Failed to parse LLM-generated questions, using fallback")
                return self._generate_fallback_follow_up_questions(state)
                
        except Exception as e:
            self.logger.error(f"Error generating follow-up questions: {e}")
            return self._generate_fallback_follow_up_questions(state)
    
    def _extract_related_topics(self, state: ConversationState) -> List[str]:
        """Extract related topics from search results and conversation context"""
        
        related_topics = []
        
        # Extract topics from search results
        if state.search_results:
            for result in state.search_results[:3]:  # Top 3 results
                content = result.text
                
                # Extract specific topics based on content patterns
                if 'building' in content.lower():
                    # Extract building references
                    building_matches = re.findall(r'building\s+([a-zA-Z0-9]+)', content, re.IGNORECASE)
                    for match in building_matches:
                        related_topics.append(f"Building {match.upper()}")
                
                if 'cisco' in content.lower():
                    # Extract Cisco model references
                    cisco_matches = re.findall(r'cisco\s+(\w+)', content, re.IGNORECASE)
                    for match in cisco_matches:
                        if match not in ['access', 'point', 'points']:
                            related_topics.append(f"Cisco {match}")
                
                if 'access point' in content.lower() or 'ap' in content.lower():
                    related_topics.append("Access Points")
                
                if 'employee' in content.lower():
                    related_topics.append("Employee Records")
                
                if 'incident' in content.lower():
                    related_topics.append("Incidents")
                
                if 'certification' in content.lower():
                    related_topics.append("Certifications")
                
                if 'manager' in content.lower():
                    related_topics.append("Management")
        
        # Extract topics from current query
        query = state.original_query.lower()
        if 'antenna' in query:
            related_topics.append("External Antennas")
        if 'model' in query:
            related_topics.append("Equipment Models")
        if 'specification' in query:
            related_topics.append("Technical Specifications")
        
        # Add topics from conversation history
        if state.topics_discussed:
            related_topics.extend(state.topics_discussed[-3:])  # Last 3 topics
        
        # Remove duplicates and limit to 5 topics
        unique_topics = []
        seen = set()
        for topic in related_topics:
            if topic.lower() not in seen:
                unique_topics.append(topic)
                seen.add(topic.lower())
        
        return unique_topics[:5]
    
    def _build_suggestion_context(self, state: ConversationState) -> str:
        """Build context information for generating suggestions"""
        context_parts = []
        
        # Add enhanced search results context with metadata
        if state.search_results:
            context_parts.append("=== SEARCH RESULTS ===")
            for i, result in enumerate(state.search_results[:3], 1):
                content_preview = result.text[:250]
                source = result.source
                score = result.relevance_score
                metadata = result.metadata
                
                context_parts.append(f"Result {i} (Score: {score:.2f}, Source: {source}):")
                context_parts.append(content_preview + "...")
                
                # Include relevant metadata for better context
                if metadata:
                    meta_info = []
                    if metadata.get('doc_path'):
                        meta_info.append(f"Document: {metadata['doc_path']}")
                    if metadata.get('filename'):
                        meta_info.append(f"File: {metadata['filename']}")
                    if metadata.get('chunk_index') is not None:
                        meta_info.append(f"Section: {metadata['chunk_index']}")
                    
                    if meta_info:
                        context_parts.append(f"Metadata: {', '.join(meta_info)}")
                
                context_parts.append("")
        
        # Add conversation context if available
        if state.messages and len(state.messages) > 1:
            context_parts.append("=== CONVERSATION CONTEXT ===")
            recent_messages = state.messages[-4:]  # Last 2 exchanges
            for msg in recent_messages:
                role = "User" if msg.type == MessageType.USER else "Assistant"
                content = msg.content[:150]
                context_parts.append(f"{role}: {content}...")
            context_parts.append("")
        
        # Add any entities or topics mentioned
        if state.extracted_entities:
            context_parts.append("=== ENTITIES MENTIONED ===")
            context_parts.append(", ".join(state.extracted_entities[:5]))
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    def _parse_follow_up_questions(self, response: str) -> List[str]:
        """Parse follow-up questions from LLM response"""
        questions = []
        
        # Split by lines and look for questions
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and headers
            if not line or line.startswith('=') or line.startswith('#'):
                continue
            
            # Remove list markers
            line = re.sub(r'^[-•*\d.]+\s*', '', line)
            
            # Check if it's a question
            if line.endswith('?') and len(line) > 10:
                # Clean up the question
                question = line.strip()
                if question and question not in questions:
                    questions.append(question)
        
        return questions[:4]  # Return max 4 questions
    
    def _generate_fallback_follow_up_questions(self, state: ConversationState) -> List[str]:
        """Generate fallback questions when LLM approach fails"""
        original_query = state.original_query.lower()
        questions = []
        
        # Generate based on query type and search results
        if 'who is' in original_query or 'who are' in original_query:
            if state.search_results:
                # Extract name from query for more specific questions
                name_match = re.search(r'who is\s+([^?]+)', original_query, re.IGNORECASE)
                if name_match:
                    name = name_match.group(1).strip()
                    # Generate smart questions based on what we found in search results
                    content_analysis = ""
                    for result in state.search_results[:2]:
                        content_analysis += result.text[:300]
                    
                    questions = []
                    if 'manager' in content_analysis.lower() or 'floor' in content_analysis.lower():
                        questions.append(f"What specific responsibilities does {name} have as a manager?")
                        questions.append(f"Which team members report to {name}?")
                    if 'building' in content_analysis.lower():
                        questions.append(f"What other staff work in the same building as {name}?")
                    if 'contact' in content_analysis.lower() or 'phone' in content_analysis.lower():
                        questions.append(f"What's the best way to reach {name} for urgent matters?")
                    if 'certification' in content_analysis.lower():
                        questions.append(f"What other certifications or qualifications does {name} have?")
                    
                    # Fill with generic questions if we don't have enough specific ones
                    if len(questions) < 3:
                        questions.extend([
                            f"What projects is {name} currently working on?",
                            f"Who are {name}'s key contacts and collaborators?",
                            f"What is {name}'s availability and working schedule?"
                        ])
                    
                    questions = questions[:4]  # Limit to 4 questions
                else:
                    questions = [
                        "What is their role and main responsibilities?",
                        "What team or department are they part of?",
                        "How can I contact them?",
                        "What are their key qualifications?"
                    ]
            else:
                questions = [
                    "Can you provide more details about this person?",
                    "What specific information are you looking for?",
                    "Would you like me to search for related contacts?",
                    "Is there a particular context or department you're interested in?"
                ]
        
        elif 'what is' in original_query or 'what are' in original_query:
            if state.search_results:
                questions = [
                    "What are the specific technical details?",
                    "How is this used in practice?",
                    "What are the key features or specifications?",
                    "Are there different types or variations?"
                ]
            else:
                questions = [
                    "Can you be more specific about what aspect you're interested in?",
                    "What particular details would be most helpful?",
                    "Is there a specific context or use case you're considering?",
                    "Would you like me to search for related information?"
                ]
        
        elif 'how' in original_query:
            if state.search_results:
                questions = [
                    "What are the specific step-by-step instructions?",
                    "What tools or resources are needed?",
                    "Are there any prerequisites or requirements?",
                    "What are common challenges or troubleshooting tips?"
                ]
            else:
                questions = [
                    "What specific aspect of the process interests you most?",
                    "Are you looking for general guidance or specific instructions?",
                    "What's your current level of experience with this?",
                    "Would you like me to find detailed documentation?"
                ]
        
        else:
            # Generic questions based on whether we have results
            if state.search_results:
                questions = [
                    "Would you like more detailed information about this topic?",
                    "Are there specific aspects you'd like me to elaborate on?",
                    "How does this relate to your specific needs or project?",
                    "Would you like to explore related topics or concepts?"
                ]
            else:
                questions = [
                    "Can you provide more specific details about what you're looking for?",
                    "What particular aspect would be most helpful to know about?",
                    "Is there additional context that might help me find better information?",
                    "Would you like me to search for related topics?"
                ]
        
        return questions[:4]  # Return max 4 questions
    
    def _is_complex_correlation_query(self, query: str) -> bool:
        """Determine if a query requires complex data correlation"""
        query_lower = query.lower()
        
        # Patterns that indicate complex correlation queries
        complex_patterns = [
            r'find.+then.+identify',  # Find X then identify Y
            r'find.+and.+list',        # Find X and list Y
            r'identify.+associated.+with',  # Identify X associated with Y
            r'match.+with.+from',      # Match X with Y from Z
            r'correlate',              # Explicit correlation request
            r'cross-reference',        # Cross-reference request
            r'link.+to.+and',         # Link X to Y and Z
            r'which.+has.+and.+also'  # Which X has Y and also Z
        ]
        
        for pattern in complex_patterns:
            if re.search(pattern, query_lower):
                return True
        
        # Check for multi-step queries
        if all(word in query_lower for word in ['find', 'then', 'list']):
            return True
        
        # Check for queries asking for multiple related pieces of information
        if query_lower.count('and') >= 2 and any(word in query_lower for word in ['identify', 'list', 'find']):
            return True
        
        return False

    def _should_use_direct_response(self, state: ConversationState) -> bool:
        """
        Determine if we should use the direct query engine response 
        instead of generating an LLM response
        """
        try:
            # Check if we have aggregation or statistical query results
            query_engine_response = state.query_engine_response
            if not query_engine_response:
                return False
            
            # Look for statistical/aggregation response patterns
            aggregation_indicators = [
                'Document statistics:',
                'Total documents:',
                'Found ',
                ' in the system:'
            ]
            
            for indicator in aggregation_indicators:
                if indicator in query_engine_response:
                    self.logger.info(f"Direct response indicator found: {indicator}")
                    return True
            
            # Check if the original query was statistical/aggregational
            messages = state.messages
            if messages:
                latest_user_message = None
                for msg in reversed(messages):
                    if msg.type == MessageType.USER:
                        latest_user_message = msg
                        break
                
                if latest_user_message:
                    query = latest_user_message.content.lower()
                    
                    # Statistical/aggregation query patterns
                    stat_patterns = [
                        r'\b(how many|count|number of|total)\b',
                        r'\b(statistics|stats|summary)\b',
                        r'\b(show all|list all|get all)\b',
                        r'\b(group by|per|by category)\b'
                    ]
                    
                    for pattern in stat_patterns:
                        if re.search(pattern, query):
                            self.logger.info(f"Statistical query pattern found: {pattern}")
                            return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error in _should_use_direct_response: {e}")
            return False