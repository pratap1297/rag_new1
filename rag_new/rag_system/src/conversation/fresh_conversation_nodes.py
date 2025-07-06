"""
FreshConversationNodes Module
Implements the nodes for the conversation flow
Enhanced with LLM-powered query decomposition and synonym resolution
"""
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import re

from .fresh_conversation_state import FreshConversationState, SearchResult
from .fresh_smart_router import QueryIntent, QueryComplexity, Route


class FreshConversationNodes:
    """
    Implements the nodes for the conversation flow.
    Each node is responsible for a specific step in the conversation process.
    Enhanced with LLM-powered query decomposition and synonym resolution.
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
        self.config_manager = None
        
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
                
            try:
                self.config_manager = container.get('config_manager')
            except KeyError:
                self.logger.warning("config_manager not found in container")
        
        # Load configuration for LLM-enhanced features
        if self.config_manager:
            config = self.config_manager.get_config()
            conversation_config = config.conversation
            self.enable_llm_query_analysis = conversation_config.enable_llm_query_analysis
            self.max_decomposed_queries = conversation_config.max_decomposed_queries
            self.synonym_expansion_enabled = conversation_config.synonym_expansion_enabled
            self.enable_query_decomposition = conversation_config.enable_query_decomposition
            self.enable_aggregation_detection = conversation_config.enable_aggregation_detection
            self.enable_response_synthesis = conversation_config.enable_response_synthesis
        else:
            # Default configuration
            self.enable_llm_query_analysis = True
            self.max_decomposed_queries = 10
            self.synonym_expansion_enabled = True
            self.enable_query_decomposition = True
            self.enable_aggregation_detection = True
            self.enable_response_synthesis = True
        
        self.logger.info(f"FreshConversationNodes initialized with LLM enhancement: {self.enable_llm_query_analysis}")

    def _analyze_query_with_llm(self, query: str) -> Dict[str, Any]:
        """Use LLM to understand query structure and intent"""
        
        if not self.llm_client or not self.enable_llm_query_analysis:
            return {"needs_decomposition": False}
        
        analysis_prompt = f"""Analyze this query and provide a structured response:
        Query: "{query}"
        
        Respond in JSON format:
        {{
            "query_type": "single" or "multi" or "aggregation",
            "needs_decomposition": true/false,
            "entity_type": "what is being asked about (e.g., 'AP models', 'incidents', 'employees')",
            "scope": "specific" or "all" or "multiple",
            "scope_targets": ["list of specific targets if scope is specific, e.g., 'Building A'"],
            "action": "list" or "count" or "find" or "compare",
            "filters": {{"any filters mentioned": "value"}},
            "decomposed_queries": ["if needs_decomposition, list simpler queries"],
            "search_keywords": ["key terms to search for"],
            "synonyms": {{"term": ["synonym1", "synonym2"]}}
        }}
        
        Examples:
        - "List all AP models in all buildings" → needs decomposition into queries for each building
        - "How many incidents in December" → aggregation query with time filter
        - "Show me all network devices across all locations" → multi-entity query needing synonym expansion
        """
        
        try:
            response = self.llm_client.generate(analysis_prompt)
            return json.loads(response)
        except Exception as e:
            self.logger.error(f"LLM analysis failed: {e}")
            return {"needs_decomposition": False}

    def _expand_with_synonyms(self, query: str, synonyms: Dict[str, List[str]]) -> str:
        """Expand query with synonyms for better matching"""
        
        if not self.synonym_expansion_enabled or not synonyms:
            return query
            
        expanded = query
        for term, synonym_list in synonyms.items():
            if term.lower() in query.lower():
                # Create OR expression
                synonym_expr = f"({term} OR {' OR '.join(synonym_list)})"
                expanded = expanded.replace(term, synonym_expr)
        
        return expanded

    def _generate_query_decomposition(self, query: str, analysis: Dict[str, Any]) -> List[str]:
        """Generate query decomposition if LLM didn't provide it"""
        
        if not self.llm_client or not self.enable_query_decomposition:
            return [query]
        
        decomposition_prompt = f"""Break down this complex query into simpler, more specific queries:
        
        Original query: "{query}"
        Entity type: {analysis.get('entity_type', 'unknown')}
        Scope: {analysis.get('scope', 'unknown')}
        
        Generate 2-5 specific queries that together would answer the original question.
        Return as a JSON array of strings.
        
        Example:
        "List all AP models in all buildings" → 
        ["AP models in Building A", "AP models in Building B", "AP models in Building C"]
        """
        
        try:
            response = self.llm_client.generate(decomposition_prompt)
            decomposed = json.loads(response)
            return decomposed[:self.max_decomposed_queries]
        except Exception as e:
            self.logger.error(f"Query decomposition failed: {e}")
            return [query]

    def _handle_decomposed_search(self, state: FreshConversationState, 
                                 analysis: Dict[str, Any]) -> FreshConversationState:
        """Handle queries that need to be broken down"""
        
        if not self.enable_query_decomposition:
            # Fall back to regular search if decomposition is disabled
            return self._handle_regular_search(state, analysis)
        
        decomposed_queries = analysis.get('decomposed_queries', [])
        if not decomposed_queries:
            # LLM didn't provide decomposition, try to generate
            decomposed_queries = self._generate_query_decomposition(
                state['processed_query'],
                analysis
            )
        
        # Execute each sub-query
        all_results = []
        all_chunks = []
        results_by_query = {}
        
        for sub_query in decomposed_queries:
            # Apply synonym expansion
            expanded_query = self._expand_with_synonyms(sub_query, analysis.get('synonyms', {}))
            
            if self.query_engine:
                result = self.query_engine.process_query(
                    expanded_query,
                    conversation_context={}
                )
                
                if result and result.get('sources'):
                    results_by_query[sub_query] = result['sources']
                    all_results.extend(result['sources'])
                    all_chunks.extend([s.get('text', '') for s in result['sources']])
        
        # Store structured results
        new_state = state.copy()
        new_state['search_results'] = all_results
        new_state['context_chunks'] = all_chunks
        new_state['decomposed_search'] = True
        new_state['search_structure'] = {
            'original_query': state['original_query'],
            'analysis': analysis,
            'results_by_query': results_by_query
        }
        
        return new_state

    def _handle_generic_aggregation(self, state: FreshConversationState, 
                                   analysis: Dict[str, Any]) -> FreshConversationState:
        """Handle aggregation queries generically using LLM analysis"""
        
        if not self.enable_aggregation_detection:
            # Fall back to regular search if aggregation detection is disabled
            return self._handle_regular_search(state, analysis)
        
        entity_type = analysis.get('entity_type', '')
        filters = analysis.get('filters', {})
        
        # Use LLM to determine what to search for
        if self.llm_client and entity_type:
            search_prompt = f"""Given that user wants to count '{entity_type}', 
            what search terms should I use to find these in documents?
            Provide a JSON array of search terms and patterns.
            
            Example: For "AP models" → ["AP", "access point", "Cisco3802", "Cisco1562"]
            For "incidents" → ["INC", "incident", "INCIDENT"]
            """
            
            try:
                search_terms = json.loads(self.llm_client.generate(search_prompt))
            except:
                search_terms = [entity_type]
        else:
            search_terms = [entity_type]
        
        # Execute count with dynamic search terms
        total_count = 0
        if self.query_engine and hasattr(self.query_engine, 'count_documents'):
            for term in search_terms:
                count = self.query_engine.count_documents(
                    query=term,
                    filters=filters
                )
                total_count += count
        
        # Build result description
        filter_desc = ""
        if filters:
            filter_desc = " with filters: " + ", ".join([f"{k}={v}" for k, v in filters.items()])
        
        new_state = state.copy()
        new_state['aggregation_result'] = {
            'type': entity_type + filter_desc,
            'count': total_count,
            'search_terms_used': search_terms
        }
        
        return new_state

    def _handle_person_query(self, state: FreshConversationState, 
                            analysis: Dict[str, Any]) -> FreshConversationState:
        """Handle person/employee queries with specialized search strategies"""
        
        processed_query = state['processed_query']
        scope_targets = analysis.get('scope_targets', [])
        
        # Extract person name from query or analysis
        person_name = None
        if scope_targets:
            person_name = scope_targets[0]  # First target is usually the person name
        else:
            # Try to extract from query using pattern matching
            name_pattern = r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b'
            matches = re.findall(name_pattern, processed_query)
            if matches:
                person_name = matches[0]
        
        if not person_name:
            self.logger.warning("Could not extract person name from query")
            return self._handle_regular_search(state, analysis)
        
        # Create multiple search strategies for person queries
        search_strategies = [
            person_name,  # Exact name
            f"{person_name} employee",  # Name + employee
            f"{person_name} staff",  # Name + staff
            f"{person_name} role",  # Name + role
            f"{person_name} position",  # Name + position
            f"{person_name} department",  # Name + department
        ]
        
        # Apply synonym expansion if available
        synonyms = analysis.get('synonyms', {})
        if synonyms and self.synonym_expansion_enabled:
            expanded_strategies = []
            for strategy in search_strategies:
                expanded = self._expand_with_synonyms(strategy, synonyms)
                expanded_strategies.append(expanded)
            search_strategies = expanded_strategies
        
        # Execute search with multiple strategies
        all_results = []
        all_chunks = []
        best_result = None
        best_score = 0
        
        conversation_context = {
            'bypass_threshold': True,
            'is_contextual': state.get('is_contextual', False),
            'conversation_history': state.get('messages', []),
            'original_query': state.get('original_query', ''),
            'query_analysis': analysis,
            'person_name': person_name
        }
        
        for strategy in search_strategies[:3]:  # Try top 3 strategies
            try:
                if self.query_engine:
                    result = self.query_engine.process_query(
                        strategy,
                        top_k=5,
                        conversation_context=conversation_context
                    )
                    
                    if result and result.get('sources'):
                        sources = result['sources']
                        # Calculate relevance score for person queries
                        person_relevance = self._calculate_person_relevance(sources, person_name)
                        
                        if person_relevance > best_score:
                            best_result = result
                            best_score = person_relevance
                        
                        all_results.extend(sources)
                        all_chunks.extend([s.get('text', '') for s in sources])
                        
            except Exception as e:
                self.logger.warning(f"Person search strategy '{strategy}' failed: {e}")
        
        # Create enhanced state with person-specific results
        new_state = state.copy()
        
        if best_result and best_result.get('sources'):
            # Use best result for primary response
            new_state['search_results'] = best_result['sources']
            new_state['context_chunks'] = [s.get('text', '') for s in best_result['sources']]
            new_state['query_engine_response'] = best_result.get('response', '')
            
            # Store person-specific metadata
            new_state['search_metadata'] = {
                'original_query': processed_query,
                'person_name': person_name,
                'search_strategies_used': search_strategies[:3],
                'person_relevance_score': best_score,
                'search_strategy': 'person_specialized'
            }
            
            # Mark as person query for specialized response generation
            new_state['is_person_query'] = True
            new_state['person_analysis'] = analysis
            
            self.logger.info(f"Person search successful for '{person_name}': {len(best_result['sources'])} results, relevance: {best_score:.3f}")
        else:
            # No good results found
            new_state['search_results'] = []
            new_state['context_chunks'] = []
            new_state['query_engine_response'] = ''
            new_state['is_person_query'] = True
            new_state['person_name'] = person_name
            self.logger.info(f"No relevant results found for person query: '{person_name}'")
        
        return new_state
    
    def _calculate_person_relevance(self, sources: List[Dict], person_name: str) -> float:
        """Calculate how relevant the sources are for a person query"""
        
        if not sources or not person_name:
            return 0.0
        
        total_relevance = 0.0
        name_parts = person_name.lower().split()
        
        for source in sources:
            text = source.get('text', '').lower()
            relevance = 0.0
            
            # Check for exact name match
            if person_name.lower() in text:
                relevance += 1.0
            
            # Check for individual name parts
            for part in name_parts:
                if part in text:
                    relevance += 0.3
            
            # Check for person-related keywords
            person_keywords = ['employee', 'staff', 'manager', 'director', 'engineer', 
                             'analyst', 'coordinator', 'specialist', 'role', 'position', 
                             'department', 'team', 'contact', 'email', 'phone']
            
            for keyword in person_keywords:
                if keyword in text:
                    relevance += 0.1
            
            # Boost relevance if name appears near person keywords
            for part in name_parts:
                for keyword in person_keywords:
                    pattern = f"{part}.*{keyword}|{keyword}.*{part}"
                    if re.search(pattern, text):
                        relevance += 0.2
            
            total_relevance += min(relevance, 2.0)  # Cap individual source relevance
        
        return total_relevance / len(sources) if sources else 0.0

    def _handle_regular_search(self, state: FreshConversationState, 
                              analysis: Dict[str, Any]) -> FreshConversationState:
        """Handle regular search without decomposition or aggregation"""
        
        # Check if this is a person query that should use specialized handling
        entity_type = analysis.get('entity_type', '')
        if entity_type == 'person' or 'person' in entity_type.lower():
            return self._handle_person_query(state, analysis)
        
        processed_query = state['processed_query']
        
        # Apply synonym expansion if enabled
        expanded_query = processed_query
        if self.synonym_expansion_enabled and analysis.get('synonyms'):
            expanded_query = self._expand_with_synonyms(processed_query, analysis['synonyms'])
            self.logger.info(f"Expanded query with synonyms: {expanded_query}")
        
        # Create conversation context
        conversation_context = {
            'bypass_threshold': True,
            'is_contextual': state.get('is_contextual', False),
            'conversation_history': state.get('messages', []),
            'original_query': state.get('original_query', ''),
            'query_analysis': analysis
        }
        
        # Execute search
        new_state = state.copy()
        if self.query_engine:
            search_result = self.query_engine.process_query(
                expanded_query,
                top_k=5,
                conversation_context=conversation_context
            )
            
            if search_result and search_result.get('sources'):
                new_state['search_results'] = search_result['sources']
                new_state['context_chunks'] = [s.get('text', '') for s in search_result['sources']]
                new_state['query_engine_response'] = search_result.get('response', '')
                
                # Store search metadata
                new_state['search_metadata'] = {
                    'original_query': processed_query,
                    'expanded_query': expanded_query,
                    'synonyms_used': analysis.get('synonyms', {}),
                    'search_strategy': 'regular'
                }
            else:
                new_state['search_results'] = []
                new_state['context_chunks'] = []
                new_state['query_engine_response'] = ''
        
        return new_state

    def _generate_structured_response(self, state: FreshConversationState) -> str:
        """Generate response for decomposed/structured queries"""
        
        if not self.enable_response_synthesis or not self.llm_client:
            # Fall back to simple formatting
            search_structure = state.get('search_structure', {})
            results_by_query = search_structure.get('results_by_query', {})
            return self._format_structured_results_fallback(results_by_query)
        
        search_structure = state.get('search_structure', {})
        analysis = search_structure.get('analysis', {})
        results_by_query = search_structure.get('results_by_query', {})
        
        # Use LLM to synthesize results
        synthesis_prompt = f"""Synthesize these search results into a comprehensive answer.
        
        Original query: {search_structure.get('original_query')}
        Query type: {analysis.get('query_type')}
        Entity type: {analysis.get('entity_type')}
        
        Results by sub-query:
        {json.dumps(results_by_query, indent=2)}
        
        Provide a well-structured response that:
        1. Directly answers the original query
        2. Organizes information logically
        3. Highlights patterns or commonalities
        4. Notes any gaps or missing information
        """
        
        try:
            response = self.llm_client.generate(synthesis_prompt)
            return response
        except Exception as e:
            self.logger.error(f"LLM synthesis failed: {e}")
            return self._format_structured_results_fallback(results_by_query)

    def _format_structured_results_fallback(self, results_by_query: Dict[str, Any]) -> str:
        """Fallback formatting for structured results"""
        
        if not results_by_query:
            return "I couldn't find any relevant information for your query."
        
        response_parts = []
        for query, results in results_by_query.items():
            response_parts.append(f"**{query}:**")
            if results:
                for result in results[:3]:  # Show top 3 results per query
                    response_parts.append(f"- {result.get('text', '')[:200]}...")
            else:
                response_parts.append("- No results found")
            response_parts.append("")
        
        return "\n".join(response_parts)

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
            
            # Store enhanced analysis results
            new_state['query_analysis'] = {
                'query_type': query_analysis.query_type,
                'needs_decomposition': query_analysis.needs_decomposition,
                'entity_type': query_analysis.entity_type,
                'scope': query_analysis.scope,
                'scope_targets': query_analysis.scope_targets,
                'action': query_analysis.action,
                'filters': query_analysis.filters,
                'decomposed_queries': query_analysis.decomposed_queries,
                'search_keywords': query_analysis.search_keywords,
                'synonyms': query_analysis.synonyms
            }
            
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
                    self.logger.info(f"Enhanced contextual query: {enhanced_query}")
                except Exception as e:
                    self.logger.error(f"Failed to enhance contextual query: {e}")
                    new_state['processed_query'] = latest_query
            else:
                new_state['processed_query'] = latest_query
            
            return new_state
            
        except Exception as e:
            self.logger.error(f"Error in understand_intent: {e}")
            new_state['has_errors'] = True
            new_state['error_messages'] = state.get('error_messages', []) + [f"Intent analysis failed: {e}"]
            return new_state

    def search_knowledge(self, state: FreshConversationState) -> FreshConversationState:
        """
        Search for relevant information using the query engine
        Enhanced with query decomposition and synonym expansion
        
        Args:
            state: The current conversation state
            
        Returns:
            FreshConversationState: Updated state with search results
        """
        self.logger.info("Processing search_knowledge node with LLM enhancement")
        
        # Create a copy to avoid modifying the original
        new_state = FreshConversationState(**state)
        
        if not state.get('processed_query') or not self.query_engine:
            self.logger.warning("No query to search or query engine unavailable")
            new_state['has_errors'] = True
            new_state['error_messages'] = state.get('error_messages', []) + ["No query to search or query engine unavailable"]
            new_state['search_results'] = []
            new_state['context_chunks'] = []
            return new_state

        try:
            processed_query = state['processed_query']
            
            # Analyze query with LLM if available
            query_analysis = self._analyze_query_with_llm(processed_query)
            
            # Handle different query types based on configuration
            if query_analysis.get('needs_decomposition') and self.enable_query_decomposition:
                return self._handle_decomposed_search(new_state, query_analysis)
            
            if query_analysis.get('query_type') == 'aggregation' and self.enable_aggregation_detection:
                return self._handle_generic_aggregation(new_state, query_analysis)
            
            # Handle regular search with optional synonym expansion
            return self._handle_regular_search(new_state, query_analysis)
            
        except Exception as e:
            self.logger.error(f"Error in search_knowledge: {e}")
            new_state['has_errors'] = True
            new_state['error_messages'] = state.get('error_messages', []) + [f"Search failed: {e}"]
            new_state['search_results'] = []
            new_state['context_chunks'] = []
            return new_state

    def generate_response(self, state: FreshConversationState) -> FreshConversationState:
        """
        Generate a response based on the current state
        Enhanced with structured response generation for decomposed queries
        
        Args:
            state: The current conversation state
            
        Returns:
            FreshConversationState: Updated state with response
        """
        self.logger.info("Processing generate_response node")
        
        # Create a copy to avoid modifying the original
        new_state = FreshConversationState(**state)
        
        try:
            # Handle person queries with specialized formatting
            if state.get('is_person_query'):
                response = self._generate_person_response(new_state)
                return self._add_response_to_state(new_state, response)
            
            # Handle decomposed searches
            if state.get('decomposed_search'):
                response = self._generate_structured_response(new_state)
                return self._add_response_to_state(new_state, response)
            
            # Handle aggregation results
            if state.get('aggregation_result'):
                agg_result = state['aggregation_result']
                response = f"I found {agg_result['count']} {agg_result['type']}."
                if agg_result.get('search_terms_used'):
                    response += f" (Searched for: {', '.join(agg_result['search_terms_used'])})"
                return self._add_response_to_state(new_state, response)
            
            # Handle regular responses
            search_results = state.get('search_results', [])
            query_engine_response = state.get('query_engine_response', '')
            
            if query_engine_response:
                # Use query engine response if available
                response = query_engine_response
            elif search_results:
                # Generate response from search results
                response = self._generate_response_from_results(state, search_results)
            else:
                # No results found
                response = self._generate_no_results_response(state)
            
            return self._add_response_to_state(new_state, response)
            
        except Exception as e:
            self.logger.error(f"Error in generate_response: {e}")
            response = "I apologize, but I encountered an error while generating a response. Please try rephrasing your question."
            return self._add_response_to_state(new_state, response)

    def _generate_person_response(self, state: FreshConversationState) -> str:
        """Generate specialized response for person queries"""
        
        person_name = state.get('person_name', 'the person')
        search_results = state.get('search_results', [])
        search_metadata = state.get('search_metadata', {})
        
        if not search_results:
            return f"I couldn't find any information about {person_name} in the available documents. They may not be listed in the current system records, or their information might be stored under a different name or format."
        
        # Extract person-relevant information from results
        person_info = self._extract_person_info(search_results, person_name)
        
        if not person_info:
            # Found results but no clear person information
            return f"I found some documents that mention {person_name}, but I couldn't extract clear information about them. The available information might be incomplete or formatted in a way that's difficult to parse."
        
        # Format person information response
        response_parts = [f"Here's what I found about {person_name}:"]
        
        # Add structured information
        if person_info.get('role'):
            response_parts.append(f"• Role/Position: {person_info['role']}")
        
        if person_info.get('department'):
            response_parts.append(f"• Department: {person_info['department']}")
        
        if person_info.get('contact'):
            response_parts.append(f"• Contact: {person_info['contact']}")
        
        if person_info.get('location'):
            response_parts.append(f"• Location: {person_info['location']}")
        
        # Add additional context if available
        if person_info.get('additional_info'):
            response_parts.append(f"• Additional Information: {person_info['additional_info']}")
        
        # Add source information
        sources = set()
        for result in search_results[:3]:
            source = result.get('source', 'Unknown source')
            if source != 'Unknown source':
                sources.add(source)
        
        if sources:
            response_parts.append(f"\nSources: {', '.join(list(sources)[:3])}")
        
        # Add confidence indicator
        relevance_score = search_metadata.get('person_relevance_score', 0)
        if relevance_score < 0.5:
            response_parts.append("\n(Note: This information has low confidence - please verify independently)")
        
        return "\n".join(response_parts)
    
    def _extract_person_info(self, search_results: List[Dict], person_name: str) -> Dict[str, str]:
        """Extract structured person information from search results"""
        
        person_info = {}
        name_parts = person_name.lower().split()
        
        for result in search_results:
            text = result.get('text', '')
            text_lower = text.lower()
            
            # Skip if person name not in this result
            if not any(part in text_lower for part in name_parts):
                continue
            
            # Extract role/position information
            role_patterns = [
                rf"{re.escape(person_name.lower())}[^\n]*?(manager|director|engineer|analyst|coordinator|specialist|admin|administrator)",
                rf"(manager|director|engineer|analyst|coordinator|specialist|admin|administrator)[^\n]*?{re.escape(person_name.lower())}",
                rf"{re.escape(person_name.lower())}[^\n]*?(role|position|title)[^\n]*?:([^\n]+)",
                rf"(role|position|title)[^\n]*?{re.escape(person_name.lower())}[^\n]*?:([^\n]+)"
            ]
            
            for pattern in role_patterns:
                matches = re.findall(pattern, text_lower, re.IGNORECASE)
                if matches:
                    if isinstance(matches[0], tuple):
                        person_info['role'] = matches[0][-1].strip()
                    else:
                        person_info['role'] = matches[0].strip()
                    break
            
            # Extract department information
            dept_patterns = [
                rf"{re.escape(person_name.lower())}[^\n]*?department[^\n]*?:([^\n]+)",
                rf"department[^\n]*?{re.escape(person_name.lower())}[^\n]*?:([^\n]+)",
                rf"{re.escape(person_name.lower())}[^\n]*?(IT|HR|Finance|Operations|Engineering|Sales|Marketing|Support)"
            ]
            
            for pattern in dept_patterns:
                matches = re.findall(pattern, text_lower, re.IGNORECASE)
                if matches:
                    person_info['department'] = matches[0].strip()
                    break
            
            # Extract contact information
            contact_patterns = [
                rf"{re.escape(person_name.lower())}[^\n]*?([\w\.-]+@[\w\.-]+\.\w+)",
                rf"{re.escape(person_name.lower())}[^\n]*?(\(\d{3}\)\s*\d{3}-\d{4}|\d{3}-\d{3}-\d{4})",
                rf"email[^\n]*?{re.escape(person_name.lower())}[^\n]*?:([^\n]+)",
                rf"phone[^\n]*?{re.escape(person_name.lower())}[^\n]*?:([^\n]+)"
            ]
            
            for pattern in contact_patterns:
                matches = re.findall(pattern, text_lower, re.IGNORECASE)
                if matches:
                    person_info['contact'] = matches[0].strip()
                    break
            
            # Extract location information
            location_patterns = [
                rf"{re.escape(person_name.lower())}[^\n]*?(building [A-Z0-9]+|floor \d+|room \d+)",
                rf"location[^\n]*?{re.escape(person_name.lower())}[^\n]*?:([^\n]+)",
                rf"office[^\n]*?{re.escape(person_name.lower())}[^\n]*?:([^\n]+)"
            ]
            
            for pattern in location_patterns:
                matches = re.findall(pattern, text_lower, re.IGNORECASE)
                if matches:
                    person_info['location'] = matches[0].strip()
                    break
        
        # If we found some basic info, add a snippet of additional context
        if person_info and search_results:
            # Get the most relevant snippet
            best_result = search_results[0]
            text = best_result.get('text', '')
            
            # Find sentence containing the person's name
            sentences = text.split('.')
            for sentence in sentences:
                if person_name.lower() in sentence.lower():
                    # Clean and limit the sentence
                    clean_sentence = sentence.strip()
                    if len(clean_sentence) > 200:
                        clean_sentence = clean_sentence[:200] + "..."
                    if clean_sentence and clean_sentence not in str(person_info.values()):
                        person_info['additional_info'] = clean_sentence
                    break
        
        return person_info

    def _add_response_to_state(self, state: FreshConversationState, response: str) -> FreshConversationState:
        """Add response to conversation state"""
        
        if self.state_manager:
            return self.state_manager.add_message(state, 'assistant', response)
        else:
            # Fallback if state_manager not available
            messages = state.get('messages', [])
            messages.append({
                'type': 'assistant',
                'content': response,
                'timestamp': datetime.now().isoformat()
            })
            state['messages'] = messages
            return state

    def _generate_response_from_results(self, state: FreshConversationState, results: List[Dict]) -> str:
        """Generate response from search results"""
        
        if not results:
            return "I couldn't find any relevant information for your query."
        
        # Use first result's text as base
        main_content = results[0].get('text', '')
        
        # Add source information
        source_info = []
        for result in results[:3]:  # Show top 3 sources
            source = result.get('source', 'Unknown source')
            source_info.append(f"- {source}")
        
        response = f"{main_content}\n\nSources:\n" + "\n".join(source_info)
        return response

    def _generate_no_results_response(self, state: FreshConversationState) -> str:
        """Generate response when no results are found"""
        
        original_query = state.get('original_query', 'your query')
        return f"I couldn't find any information related to '{original_query}'. Could you try rephrasing your question or providing more specific details?"

    def handle_clarification(self, state: FreshConversationState) -> FreshConversationState:
        """
        Handle clarification requests
        
        Args:
            state: The current conversation state
            
        Returns:
            FreshConversationState: Updated state with clarification
        """
        self.logger.info("Processing handle_clarification node")
        
        # Create a copy to avoid modifying the original
        new_state = FreshConversationState(**state)
        
        clarification_message = "I need more information to help you better. Could you please provide more details about what you're looking for?"
        
        return self._add_response_to_state(new_state, clarification_message) 