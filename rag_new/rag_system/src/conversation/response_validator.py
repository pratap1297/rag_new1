"""
Response Validator
Validates generated responses for quality and accuracy
"""
import logging
from typing import Dict, Any, Tuple, List
import re

from .conversation_state import ConversationState, Message, MessageType

class ResponseValidator:
    """Validates LLM responses before adding to conversation state"""
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self.logger = logging.getLogger(__name__)
        
        # Validation thresholds
        self.min_confidence = 0.6
        self.max_hallucination_score = 0.3
        
    def validate_response(self, response: str, state: ConversationState, 
                        sources: List[Dict[str, Any]] = None) -> Tuple[bool, float, List[str]]:
        """Validate a response for quality and accuracy"""
        
        validation_errors = []
        confidence_scores = []
        
        # Run validation checks
        checks = [
            self._check_hallucination(response, sources, state),
            self._check_consistency(response, state),
            self._check_completeness(response, state),
            self._check_relevance(response, state),
            self._check_factual_accuracy(response, sources)
        ]
        
        for passed, confidence, errors in checks:
            confidence_scores.append(confidence)
            if not passed:
                validation_errors.extend(errors)
        
        # Calculate overall confidence
        overall_confidence = sum(confidence_scores) / len(confidence_scores)
        overall_passed = overall_confidence >= self.min_confidence and not validation_errors
        
        return overall_passed, overall_confidence, validation_errors
    
    def _check_hallucination(self, response: str, sources: List[Dict[str, Any]], 
                           state: ConversationState) -> Tuple[bool, float, List[str]]:
        """Check for hallucinations in response"""
        
        errors = []
        
        # Pattern-based hallucination detection
        hallucination_patterns = [
            r"(?i)as of my last update",
            r"(?i)i don't have real-time",
            r"(?i)my training data",
            r"(?i)i cannot browse",
            r"(?i)i'm not sure about the specific"
        ]
        
        response_lower = response.lower()
        pattern_matches = 0
        
        for pattern in hallucination_patterns:
            if re.search(pattern, response):
                pattern_matches += 1
                errors.append(f"Potential hallucination pattern: {pattern}")
        
        # Check if response contains information not in sources
        if sources:
            source_content = " ".join(s.get('text', '') for s in sources)
            
            # Extract specific claims from response
            claims = self._extract_claims(response)
            unsupported_claims = 0
            
            for claim in claims:
                if not self._claim_supported_by_sources(claim, source_content):
                    unsupported_claims += 1
            
            if unsupported_claims > len(claims) * 0.3:  # More than 30% unsupported
                errors.append(f"Response contains {unsupported_claims} unsupported claims")
        
        hallucination_score = (pattern_matches * 0.2) + (unsupported_claims * 0.1)
        confidence = 1.0 - min(hallucination_score, 1.0)
        passed = hallucination_score <= self.max_hallucination_score
        
        return passed, confidence, errors
    
    def _check_consistency(self, response: str, 
                         state: ConversationState) -> Tuple[bool, float, List[str]]:
        """Check if response is consistent with conversation history"""
        
        errors = []
        inconsistencies = 0
        
        # Check against recent validated messages
        recent_messages = [
            msg for msg in state['messages'][-5:]
            if msg.type == MessageType.ASSISTANT and msg.validated
        ]
        
        for msg in recent_messages:
            if self._responses_conflict(response, msg.content):
                inconsistencies += 1
                errors.append(f"Conflicts with previous response: {msg.id}")
        
        confidence = 1.0 - (inconsistencies * 0.2)
        passed = inconsistencies == 0
        
        return passed, confidence, errors
    
    def _check_completeness(self, response: str, 
                          state: ConversationState) -> Tuple[bool, float, List[str]]:
        """Check if response adequately addresses the query"""
        
        errors = []
        query = state.get('original_query', '')
        
        if not query:
            return True, 1.0, []
        
        # Check if response is too short
        if len(response.split()) < 10 and '?' in query:
            errors.append("Response too short for the query")
            return False, 0.5, errors
        
        # Check if key query terms are addressed
        query_keywords = set(state.get('query_keywords', []))
        response_keywords = set(response.lower().split())
        
        coverage = len(query_keywords & response_keywords) / len(query_keywords) if query_keywords else 1.0
        
        if coverage < 0.3:
            errors.append("Response doesn't address key query terms")
        
        confidence = coverage
        passed = coverage >= 0.5
        
        return passed, confidence, errors
    
    def _check_relevance(self, response: str, 
                       state: ConversationState) -> Tuple[bool, float, List[str]]:
        """Check if response is relevant to the query"""
        
        errors = []
        query = state.get('original_query', '')
        
        # Simple relevance check based on keyword overlap
        query_words = set(query.lower().split())
        response_words = set(response.lower().split())
        
        overlap = len(query_words & response_words) / len(query_words) if query_words else 1.0
        
        if overlap < 0.2:
            errors.append("Response seems unrelated to query")
        
        confidence = overlap
        passed = overlap >= 0.3
        
        return passed, confidence, errors
    
    def _check_factual_accuracy(self, response: str, 
                              sources: List[Dict[str, Any]]) -> Tuple[bool, float, List[str]]:
        """Check factual accuracy against sources"""
        
        if not sources:
            # Can't verify without sources
            return True, 0.7, []
        
        errors = []
        
        # Extract factual claims
        claims = self._extract_factual_claims(response)
        verified_claims = 0
        
        source_content = " ".join(s.get('text', '') for s in sources)
        
        for claim in claims:
            if self._verify_claim(claim, source_content):
                verified_claims += 1
        
        accuracy = verified_claims / len(claims) if claims else 1.0
        
        if accuracy < 0.5:
            errors.append(f"Only {verified_claims}/{len(claims)} claims verified")
        
        confidence = accuracy
        passed = accuracy >= 0.6
        
        return passed, confidence, errors
    
    def _extract_claims(self, text: str) -> List[str]:
        """Extract factual claims from text"""
        
        # Simple sentence-based extraction
        sentences = text.split('.')
        claims = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            # Look for factual patterns
            if any(word in sentence.lower() for word in ['is', 'are', 'has', 'have', 'was', 'were']):
                claims.append(sentence)
        
        return claims
    
    def _extract_factual_claims(self, text: str) -> List[str]:
        """Extract specific factual claims"""
        
        claims = []
        
        # Look for specific patterns
        patterns = [
            r'(\w+)\s+(?:is|are)\s+(\w+)',  # X is Y
            r'(\w+)\s+(?:has|have)\s+(\w+)', # X has Y
            r'(\d+)\s+(\w+)',                # Numbers
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                claims.append(' '.join(match))
        
        return claims
    
    def _claim_supported_by_sources(self, claim: str, source_content: str) -> bool:
        """Check if a claim is supported by sources"""
        
        # Simple keyword-based check
        claim_words = set(claim.lower().split())
        source_words = set(source_content.lower().split())
        
        # If most claim words appear in sources, consider it supported
        overlap = len(claim_words & source_words) / len(claim_words) if claim_words else 0
        
        return overlap > 0.6
    
    def _verify_claim(self, claim: str, source_content: str) -> bool:
        """Verify a specific factual claim"""
        
        # More sophisticated than _claim_supported_by_sources
        # Could use NLI models in production
        
        claim_lower = claim.lower()
        source_lower = source_content.lower()
        
        # Check if claim appears nearly verbatim
        if claim_lower in source_lower:
            return True
        
        # Check key elements
        key_elements = [word for word in claim_lower.split() 
                       if len(word) > 3 and word not in ['the', 'and', 'for']]
        
        found_elements = sum(1 for elem in key_elements if elem in source_lower)
        
        return found_elements >= len(key_elements) * 0.7
    
    def _responses_conflict(self, response1: str, response2: str) -> bool:
        """Check if two responses conflict"""
        
        # Extract key statements
        statements1 = set(self._extract_claims(response1))
        statements2 = set(self._extract_claims(response2))
        
        # Check for contradictions
        for s1 in statements1:
            for s2 in statements2:
                if self._statements_contradict(s1, s2):
                    return True
        
        return False
    
    def _statements_contradict(self, statement1: str, statement2: str) -> bool:
        """Check if two statements contradict each other"""
        
        s1_lower = statement1.lower()
        s2_lower = statement2.lower()
        
        # Check for explicit contradictions
        if ('not' in s1_lower and 'not' not in s2_lower) or \
           ('not' in s2_lower and 'not' not in s1_lower):
            # Check if they're about the same subject
            s1_words = set(s1_lower.split())
            s2_words = set(s2_lower.split())
            
            overlap = len(s1_words & s2_words) / min(len(s1_words), len(s2_words))
            if overlap > 0.5:
                return True
        
        return False