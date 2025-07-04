"""
FreshSmartRouter Module
Analyzes user queries to determine intent and routing
"""
import logging
import re
from typing import Dict, List, Any, Optional, Set
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


@dataclass
class RoutingDecision:
    """Routing decision for a query"""
    route: Route
    confidence: float
    reasoning: str


class FreshSmartRouter:
    """
    Analyzes user queries to determine intent and routing.
    Provides guidance on how to handle different types of queries.
    """
    
    def __init__(self, context_manager=None):
        """Initialize the smart router"""
        self.logger = logging.getLogger(__name__)
        self.context_manager = context_manager
        
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
        
        self.logger.info("FreshSmartRouter initialized")
    
    def analyze_query(self, query: str) -> QueryAnalysis:
        """
        Analyze a user query to determine intent and other characteristics
        
        Args:
            query: The user's query text
            
        Returns:
            QueryAnalysis: Analysis of the query
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
        
        # Detect intent
        intent = self._detect_intent(query_lower)
        
        # Detect complexity
        complexity = self._detect_complexity(query)
        
        # Extract keywords and entities
        keywords = self._extract_keywords(query)
        entities = self._extract_entities(query)
        
        # Check if contextual
        is_contextual = self._is_contextual(query_lower)
        
        # Calculate confidence
        confidence = 0.8  # Base confidence
        if intent == QueryIntent.UNKNOWN:
            confidence = 0.5
        
        analysis = QueryAnalysis(
            intent=intent,
            complexity=complexity,
            confidence=confidence,
            keywords=keywords,
            entities=entities,
            is_contextual=is_contextual
        )
        
        self.logger.debug(f"Query analysis: {intent.value}, contextual: {is_contextual}")
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
        if re.search(r"^(and|also|what about|how about)", query_lower):
            return QueryIntent.FOLLOW_UP
        
        # Default to information seeking for anything else
        return QueryIntent.INFORMATION_SEEKING
    
    def _detect_complexity(self, query: str) -> QueryComplexity:
        """Determine the complexity of a query"""
        # Simple heuristics based on length and structure
        word_count = len(query.split())
        
        if word_count <= 5:
            return QueryComplexity.SIMPLE
        elif word_count <= 15:
            return QueryComplexity.MODERATE
        else:
            return QueryComplexity.COMPLEX
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract important keywords from the query"""
        # Simple keyword extraction - remove stopwords
        stopwords = {"a", "an", "the", "is", "are", "was", "were", "be", "been", 
                    "being", "to", "of", "and", "or", "but", "in", "on", "at", 
                    "for", "with", "about", "by", "as", "into", "like", "through", 
                    "after", "over", "between", "out", "against", "during", "without",
                    "before", "under", "around", "among"}
        
        words = query.lower().split()
        keywords = [word for word in words if word not in stopwords and len(word) > 2]
        
        return keywords
    
    def _extract_entities(self, query: str) -> List[str]:
        """Extract named entities from the query"""
        # Simple entity extraction - look for capitalized words not at start
        words = query.split()
        entities = []
        
        for i, word in enumerate(words):
            # Skip first word if it's the only one capitalized (likely just sentence start)
            if i == 0 and len(words) > 1 and word[0].isupper() and not words[1][0].isupper():
                continue
                
            # Check for capitalized words (potential entities)
            if word[0].isupper() and not all(c.isupper() for c in word):
                entities.append(word.strip(".,;:!?()[]{}\"'"))
        
        return entities
    
    def _is_contextual(self, query_lower: str) -> bool:
        """Determine if a query is contextual (refers to previous conversation)"""
        # Check for contextual indicators
        for pattern in self.contextual_indicators:
            if re.search(pattern, query_lower):
                return True
        
        # Check for incomplete sentences
        if len(query_lower.split()) <= 3 and not re.search(r"[.!?]$", query_lower):
            return True
            
        return False 