"""
FreshSmartRouter Module
Analyzes user queries to determine intent and routing
Enhanced with LLM-powered query decomposition and synonym resolution
"""
import logging
import re
import json
from typing import Dict, List, Any, Optional, Set, Tuple
from enum import Enum
from dataclasses import dataclass


class QueryIntent(Enum):
    """Types of query intents"""
    GREETING = "greeting"
    GOODBYE = "goodbye"
    HELP = "help"
    INFORMATION_SEEKING = "information_seeking"
    QUESTION = "question"
    FOLLOW_UP = "follow_up"
    CLARIFICATION = "clarification"
    COMMAND = "command"
    UNKNOWN = "unknown"


class QueryComplexity(Enum):
    """Complexity levels for queries"""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


class Route(Enum):
    """Possible routing destinations"""
    SEARCH = "search"
    RESPOND = "respond"
    END = "end"
    CLARIFY = "clarify"


@dataclass
class QueryAnalysis:
    """Analysis of a user query"""
    intent: QueryIntent
    complexity: QueryComplexity
    confidence: float
    keywords: List[str]
    entities: List[str]
    is_contextual: bool
    # New LLM-enhanced fields
    query_type: str = "single"  # "single", "multi", "aggregation"
    needs_decomposition: bool = False
    entity_type: str = ""
    scope: str = "specific"  # "specific", "all", "multiple"
    scope_targets: List[str] = None
    action: str = "find"  # "list", "count", "find", "compare"
    filters: Dict[str, Any] = None
    decomposed_queries: List[str] = None
    search_keywords: List[str] = None
    synonyms: Dict[str, List[str]] = None

    def __post_init__(self):
        """Initialize default values for new fields"""
        if self.scope_targets is None:
            self.scope_targets = []
        if self.filters is None:
            self.filters = {}
        if self.decomposed_queries is None:
            self.decomposed_queries = []
        if self.search_keywords is None:
            self.search_keywords = []
        if self.synonyms is None:
            self.synonyms = {}


@dataclass
class RoutingDecision:
    """Routing decision for a query"""
    route: Route
    confidence: float
    reasoning: str


class SmartQueryAnalyzer:
    """Advanced query analysis with LLM support"""
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self.logger = logging.getLogger(__name__)
        
    def analyze_entities_and_scope(self, query: str) -> Dict[str, Any]:
        """Extract entities and scope using LLM"""
        
        if not self.llm_client:
            return self._fallback_entity_detection(query)
            
        prompt = f"""Extract entities and scope from this query. Be generic and identify patterns.
        
        Query: "{query}"
        
        Identify:
        1. Entity type (what kind of thing: device, location, document, person, etc.)
        2. Specific instances mentioned (Building A, Floor 2, John Doe, etc.)
        3. Scope indicators (all, every, each, specific, between X and Y)
        4. Synonyms that might be needed
        
        Return JSON:
        {{
            "primary_entity": "main thing being asked about",
            "entity_instances": ["specific instances mentioned"],
            "scope": "all" or "specific" or "range",
            "potential_synonyms": {{
                "entity": ["synonym1", "synonym2"],
                "instance": ["alternate names"]
            }},
            "requires_multi_search": true/false
        }}
        """
        
        try:
            response = self.llm_client.generate(prompt)
            return json.loads(response)
        except Exception as e:
            self.logger.error(f"LLM entity analysis failed: {e}")
            return self._fallback_entity_detection(query)
    
    def _fallback_entity_detection(self, query: str) -> Dict[str, Any]:
        """Fallback entity detection using patterns"""
        query_lower = query.lower()
        
        # Basic entity patterns
        entity_patterns = {
            "person": r"(who is|who's|person|employee|staff|manager|director|engineer|analyst|coordinator|specialist|technician|admin|administrator|user)",
            "device": r"(ap|access point|switch|router|device|equipment|server|computer|laptop|phone)",
            "location": r"(building|floor|room|area|site|location|office|facility)",
            "document": r"(document|file|report|manual|guide|policy|procedure|specification)",
            "incident": r"(incident|issue|problem|ticket|case|error|fault|outage)",
            "network": r"(network|ip|subnet|vlan|wifi|ethernet|connection|bandwidth)",
            "security": r"(security|access|permission|role|authentication|authorization)"
        }
        
        primary_entity = "unknown"
        confidence = 0.0
        
        # Check for person names (capitalized words that could be names)
        name_pattern = r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b'
        if re.search(name_pattern, query):
            primary_entity = "person"
            confidence = 0.9
        
        # Check other entity patterns
        for entity_type, pattern in entity_patterns.items():
            if re.search(pattern, query_lower):
                if primary_entity == "unknown" or confidence < 0.8:
                    primary_entity = entity_type
                    confidence = 0.8
                break
        
        # Detect scope
        scope = "specific"
        if re.search(r"\b(all|every|each)\b", query_lower):
            scope = "all"
        elif re.search(r"\b(between|from.*to)\b", query_lower):
            scope = "range"
        
        # Enhanced synonyms for person queries
        potential_synonyms = {}
        if primary_entity == "person":
            potential_synonyms = {
                "employee": ["staff", "worker", "personnel", "team member"],
                "manager": ["supervisor", "lead", "director", "head"],
                "engineer": ["developer", "architect", "specialist", "analyst"],
                "admin": ["administrator", "support", "IT staff"],
                "user": ["person", "individual", "employee"]
            }
        elif primary_entity == "device":
            potential_synonyms = {
                "AP": ["access point", "wireless AP", "WiFi AP", "wireless access point"],
                "switch": ["network switch", "ethernet switch"],
                "router": ["network router", "gateway"],
                "server": ["host", "machine", "system"]
            }
        
        return {
            "primary_entity": primary_entity,
            "entity_instances": self._extract_names_or_identifiers(query),
            "scope": scope,
            "potential_synonyms": potential_synonyms,
            "requires_multi_search": scope == "all",
            "confidence": confidence
        }
    
    def _extract_names_or_identifiers(self, query: str) -> List[str]:
        """Extract names, IDs, or other identifiers from query"""
        identifiers = []
        
        # Extract person names (First Last pattern)
        name_pattern = r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b'
        names = re.findall(name_pattern, query)
        identifiers.extend(names)
        
        # Extract building/room identifiers
        building_pattern = r'\b(?:building|bldg)\s*([A-Z0-9]+)\b'
        buildings = re.findall(building_pattern, query, re.IGNORECASE)
        identifiers.extend([f"Building {b}" for b in buildings])
        
        # Extract room numbers
        room_pattern = r'\b(?:room|rm)\s*([A-Z0-9]+)\b'
        rooms = re.findall(room_pattern, query, re.IGNORECASE)
        identifiers.extend([f"Room {r}" for r in rooms])
        
        # Extract IP addresses
        ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        ips = re.findall(ip_pattern, query)
        identifiers.extend(ips)
        
        # Extract model numbers (common patterns)
        model_pattern = r'\b[A-Z]+\d+[A-Z]*\b'
        models = re.findall(model_pattern, query)
        identifiers.extend(models)
        
        return identifiers


class FreshSmartRouter:
    """
    Analyzes user queries to determine intent and routing.
    Enhanced with LLM-powered query decomposition and synonym resolution.
    """
    
    def __init__(self, context_manager=None, llm_client=None, config_manager=None):
        """Initialize the smart router"""
        self.logger = logging.getLogger(__name__)
        self.context_manager = context_manager
        self.llm_client = llm_client
        self.config_manager = config_manager
        
        # Initialize query analyzer
        self.query_analyzer = SmartQueryAnalyzer(llm_client)
        
        # Load configuration
        if config_manager:
            config = config_manager.get_config()
            conversation_config = config.conversation
            self.enable_llm_query_analysis = conversation_config.enable_llm_query_analysis
            self.max_decomposed_queries = conversation_config.max_decomposed_queries
            self.synonym_expansion_enabled = conversation_config.synonym_expansion_enabled
        else:
            # Default configuration
            self.enable_llm_query_analysis = True
            self.max_decomposed_queries = 10
            self.synonym_expansion_enabled = True
        
        # Intent patterns
        self.intent_patterns = {
            QueryIntent.GREETING: [
                r"^(hi|hello|hey|greetings|good morning|good afternoon|good evening)[\s\.,!]*$",
                r"^(how are you|how's it going|what's up|how do you do)[\s\.,!?]*$"
            ],
            QueryIntent.GOODBYE: [
                r"^(bye|goodbye|farewell|see you|talk to you later|exit|quit)[\s\.,!]*$",
                r"(thanks|thank you).*(bye|goodbye|that's all|that will be all)[\s\.,!]*$",
                r"(bye|goodbye).*(thanks|thank you)[\s\.,!]*$"
            ],
            QueryIntent.HELP: [
                r"^(help|assist|support|guide|how does this work|what can you do)[\s\.,!?]*$",
                r"^(show me|tell me|explain|instructions|tutorial)[\s\.,!?]*$"
            ],
            QueryIntent.COMMAND: [
                r"^(search for|find|look up|show me|display|list|get|retrieve)",
                r"^(create|add|insert|update|delete|remove|change)"
            ]
        }
        
        # Contextual indicators
        self.contextual_indicators = [
            r"(it|this|that|these|those|they|them|their|its|his|her|hers)",
            r"(the same|similar|related|more|again|also|too)",
            r"(previous|before|earlier|last time)"
        ]
        
        self.logger.info(f"FreshSmartRouter initialized with LLM enhancement: {self.enable_llm_query_analysis}")
    
    def analyze_query_with_llm(self, query: str) -> Dict[str, Any]:
        """Use LLM to understand query structure and intent"""
        
        if not self.llm_client or not self.enable_llm_query_analysis:
            return {"needs_decomposition": False}
        
        analysis_prompt = f"""Analyze this query and provide a structured response:
        Query: "{query}"
        
        Respond in JSON format:
        {{
            "query_type": "single" or "multi" or "aggregation",
            "needs_decomposition": true/false,
            "entity_type": "what is being asked about (e.g., 'person', 'AP models', 'incidents', 'employees')",
            "scope": "specific" or "all" or "multiple",
            "scope_targets": ["list of specific targets if scope is specific, e.g., 'Sarah Johnson', 'Building A'"],
            "action": "list" or "count" or "find" or "compare" or "identify",
            "filters": {{"any filters mentioned": "value"}},
            "decomposed_queries": ["if needs_decomposition, list simpler queries"],
            "search_keywords": ["key terms to search for"],
            "synonyms": {{"term": ["synonym1", "synonym2"]}}
        }}
        
        Examples:
        - "Who is Sarah Johnson" → {{"entity_type": "person", "action": "identify", "scope_targets": ["Sarah Johnson"], "search_keywords": ["Sarah Johnson", "employee", "staff"]}}
        - "List all AP models in all buildings" → needs decomposition into queries for each building
        - "How many incidents in December" → aggregation query with time filter
        - "Show me all network devices across all locations" → multi-entity query needing synonym expansion
        - "What is John Smith's role" → {{"entity_type": "person", "action": "find", "scope_targets": ["John Smith"], "search_keywords": ["John Smith", "role", "position", "title"]}}
        """
        
        try:
            response = self.llm_client.generate(analysis_prompt)
            return json.loads(response)
        except Exception as e:
            self.logger.error(f"LLM analysis failed: {e}")
            return {"needs_decomposition": False}
    
    def expand_with_synonyms(self, query: str, synonyms: Dict[str, List[str]]) -> str:
        """Expand query with synonyms for better matching"""
        
        if not self.synonym_expansion_enabled or not synonyms:
            return query
            
        expanded = query
        for term, synonym_list in synonyms.items():
            if term.lower() in query.lower():
                # Create OR expression for better search
                synonym_expr = f"({term} OR {' OR '.join(synonym_list)})"
                expanded = expanded.replace(term, synonym_expr)
        
        return expanded
    
    def analyze_query(self, query: str) -> QueryAnalysis:
        """
        Analyze a user query to determine intent and other characteristics
        Enhanced with LLM-powered analysis
        
        Args:
            query: The user's query text
            
        Returns:
            QueryAnalysis: Enhanced analysis of the query
        """
        if not query or not isinstance(query, str):
            return QueryAnalysis(
                intent=QueryIntent.UNKNOWN,
                complexity=QueryComplexity.SIMPLE,
                confidence=1.0,
                keywords=[],
                entities=[],
                is_contextual=False
            )
        
        # Normalize query
        query = query.strip()
        query_lower = query.lower()
        
        # Basic analysis
        intent = self._detect_intent(query_lower)
        complexity = self._detect_complexity(query)
        keywords = self._extract_keywords(query)
        entities = self._extract_entities(query)
        is_contextual = self._is_contextual(query_lower)
        
        # Enhanced LLM analysis
        llm_analysis = self.analyze_query_with_llm(query)
        
        # Entity and scope analysis
        entity_analysis = self.query_analyzer.analyze_entities_and_scope(query)
        
        # Calculate confidence
        confidence = 0.8  # Base confidence
        if intent == QueryIntent.UNKNOWN:
            confidence = 0.5
        
        # Create enhanced analysis
        analysis = QueryAnalysis(
            intent=intent,
            complexity=complexity,
            confidence=confidence,
            keywords=keywords,
            entities=entities,
            is_contextual=is_contextual,
            # LLM-enhanced fields
            query_type=llm_analysis.get('query_type', 'single'),
            needs_decomposition=llm_analysis.get('needs_decomposition', False),
            entity_type=llm_analysis.get('entity_type', entity_analysis.get('primary_entity', '')),
            scope=llm_analysis.get('scope', entity_analysis.get('scope', 'specific')),
            scope_targets=llm_analysis.get('scope_targets', entity_analysis.get('entity_instances', [])),
            action=llm_analysis.get('action', 'find'),
            filters=llm_analysis.get('filters', {}),
            decomposed_queries=llm_analysis.get('decomposed_queries', []),
            search_keywords=llm_analysis.get('search_keywords', keywords),
            synonyms=llm_analysis.get('synonyms', entity_analysis.get('potential_synonyms', {}))
        )
        
        self.logger.debug(f"Enhanced query analysis: {intent.value}, type: {analysis.query_type}, "
                         f"decomposition: {analysis.needs_decomposition}, entity: {analysis.entity_type}")
        return analysis

    def route_query(self, analysis: QueryAnalysis) -> RoutingDecision:
        """
        Determine routing based on query analysis
        
        Args:
            analysis: Analysis of the query
            
        Returns:
            RoutingDecision: Where to route the query
        """
        intent = analysis.intent
        
        # Apply routing logic
        if intent == QueryIntent.GOODBYE:
            return RoutingDecision(
                route=Route.END,
                confidence=0.9,
                reasoning="User expressed intention to end conversation"
            )
        elif intent in [QueryIntent.GREETING, QueryIntent.HELP]:
            return RoutingDecision(
                route=Route.RESPOND,
                confidence=0.9,
                reasoning=f"Direct response appropriate for {intent.value}"
            )
        else:
            # Default to search for all other intents (critical "search-first" principle)
            return RoutingDecision(
                route=Route.SEARCH,
                confidence=0.8,
                reasoning="Default to search for information seeking queries"
            )
    
    def _detect_intent(self, query_lower: str) -> QueryIntent:
        """Detect the intent of a query"""
        # Check pattern-based intents
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    return intent
        
        # Special case for goodbye intent with "thank you" variations
        if ("thank" in query_lower or "thanks" in query_lower) and ("bye" in query_lower or "goodbye" in query_lower):
            return QueryIntent.GOODBYE
        
        # Check for question patterns
        if re.search(r"^(who|what|when|where|why|how|is|are|can|could|would|will|should)", query_lower):
            return QueryIntent.QUESTION
        
        # Check for follow-up patterns
        if re.search(r"^(and|also|additionally|furthermore|moreover)", query_lower):
            return QueryIntent.FOLLOW_UP
        
        # Default to information seeking
        return QueryIntent.INFORMATION_SEEKING

    def _detect_complexity(self, query: str) -> QueryComplexity:
        """Detect query complexity"""
        word_count = len(query.split())
        if word_count <= 3:
            return QueryComplexity.SIMPLE
        elif word_count <= 10:
            return QueryComplexity.MODERATE
        else:
            return QueryComplexity.COMPLEX

    def _extract_keywords(self, query: str) -> List[str]:
        """Extract keywords from query"""
        # Simple keyword extraction
        stop_words = {'the', 'is', 'are', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an'}
        words = re.findall(r'\b\w+\b', query.lower())
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        return keywords[:10]  # Limit to top 10 keywords

    def _extract_entities(self, query: str) -> List[str]:
        """Extract entities from query"""
        # Simple entity extraction (can be enhanced with NER)
        entities = []
        
        # Building patterns
        building_matches = re.findall(r'\b(building\s+[a-zA-Z0-9]+|[a-zA-Z0-9]+\s+building)\b', query, re.IGNORECASE)
        entities.extend(building_matches)
        
        # Floor patterns
        floor_matches = re.findall(r'\b(floor\s+\d+|\d+\w*\s+floor)\b', query, re.IGNORECASE)
        entities.extend(floor_matches)
        
        # Room patterns
        room_matches = re.findall(r'\b(room\s+\w+|\w+\s+room)\b', query, re.IGNORECASE)
        entities.extend(room_matches)
        
        return entities

    def _is_contextual(self, query_lower: str) -> bool:
        """Check if query is contextual"""
        for indicator in self.contextual_indicators:
            if re.search(indicator, query_lower):
                return True
        return False 