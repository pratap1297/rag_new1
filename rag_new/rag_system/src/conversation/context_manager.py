"""
Context Manager
Handles context validation, quality management, and poisoning prevention
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import hashlib

from .conversation_state import (
    ConversationState, ContextSegment, ContextQuality,
    Message, MessageType, SearchResult,
    MAX_CONTEXT_LENGTH, CONTEXT_QUALITY_THRESHOLD, get_relevant_conversation_history
)

class ContextManager:
    """Manages context quality and prevents context failures"""
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self.logger = logging.getLogger(__name__)
        
        # Context quality thresholds
        self.min_relevance_score = 0.6
        self.max_redundancy_ratio = 0.3
        self.conflict_threshold = 0.7
        
    def build_dynamic_context(self, state: ConversationState, 
                            purpose: str = "response") -> Tuple[str, ContextQuality]:
        """Build optimized context dynamically based on purpose"""
        
        self.logger.info(f"Building dynamic context for purpose: {purpose}")
        
        # Get relevant segments based on purpose
        if purpose == "response":
            segments = self._get_response_context_segments(state)
        elif purpose == "search":
            segments = self._get_search_context_segments(state)
        elif purpose == "validation":
            segments = self._get_validation_context_segments(state)
        else:
            segments = self._get_general_context_segments(state)
        
        # Filter and rank segments
        filtered_segments = self._filter_context_segments(segments, state)
        ranked_segments = self._rank_context_segments(filtered_segments, state)
        
        # Build context within token limit
        context, quality = self._assemble_context(ranked_segments, MAX_CONTEXT_LENGTH)
        
        # Update state with context quality
        state['context_segments'] = ranked_segments[:10]  # Keep top segments
        state['context_quality'] = quality
        
        return context, quality
    
    def validate_context_segment(self, segment: ContextSegment, 
                               state: ConversationState) -> Tuple[bool, float]:
        """Validate a context segment for quality and conflicts"""
        
        # Check for poisoned content
        if self._is_poisoned_content(segment.content, state):
            return False, 0.0
        
        # Check for conflicts
        conflicts = self._detect_conflicts(segment, state)
        if conflicts:
            segment.quality = ContextQuality.CONFLICTED
            return False, 0.3
        
        # Calculate quality score
        quality_score = self._calculate_segment_quality(segment, state)
        
        # Determine if segment passes threshold
        passes = quality_score >= CONTEXT_QUALITY_THRESHOLD
        
        return passes, quality_score
    
    def detect_context_poisoning(self, content: str, state: ConversationState) -> bool:
        """Detect if content contains hallucinations or errors"""
        
        # Pattern-based detection
        poison_patterns = [
            r"(?i)as an ai language model",  # Model self-reference
            r"(?i)i don't have access to",   # Capability denial in wrong context
            r"(?i)my training data",          # Training references
            r"(?i)i cannot access real-time", # When we do have search
        ]
        
        import re
        for pattern in poison_patterns:
            if re.search(pattern, content):
                self.logger.warning(f"Detected potential poisoning pattern: {pattern}")
                return True
        
        # Check against known facts
        if self._contradicts_known_facts(content, state):
            return True
        
        # Check for repetitive content (sign of poisoning)
        if self._is_repetitive_content(content, state):
            return True
        
        return False
    
    def quarantine_content(self, content_id: str, reason: str, 
                         state: ConversationState) -> ConversationState:
        """Quarantine suspicious content"""
        
        self.logger.warning(f"Quarantining content {content_id}: {reason}")
        
        new_state = state.copy()
        poisoned = new_state.get('poisoned_content', set())
        poisoned.add(content_id)
        new_state['poisoned_content'] = poisoned
        
        # Add to failed operations
        new_state['failed_operations'].append({
            'type': 'content_quarantine',
            'content_id': content_id,
            'reason': reason,
            'timestamp': datetime.now().isoformat(),
            'turn': state['turn_count']
        })
        
        return new_state
    
    def _get_response_context_segments(self, state: ConversationState) -> List[ContextSegment]:
        """Get context segments for response generation"""
        segments = []
        
        # Recent conversation history (filtered)
        relevant_messages = get_relevant_conversation_history(state, state.get('original_query'))
        for msg in relevant_messages:
            if msg.id not in state.get('poisoned_content', set()):
                segments.append(ContextSegment(
                    content=f"{msg.type.value}: {msg.content}",
                    source='conversation',
                    relevance=msg.quality_score,
                    quality=ContextQuality.HIGH if msg.validated else ContextQuality.MEDIUM,
                    tokens_estimate=len(msg.content.split())
                ))
        
        # Search results (validated)
        for result in state.get('search_results', [])[:5]:
            if result.validated or result.confidence > 0.7:
                segments.append(ContextSegment(
                    content=result.content,
                    source='search',
                    relevance=result.score,
                    quality=ContextQuality.HIGH if result.validated else ContextQuality.MEDIUM,
                    tokens_estimate=len(result.content.split())
                ))
        
        return segments

    def _get_search_context_segments(self, state: ConversationState) -> List[ContextSegment]:
        """Get context segments for search query enhancement"""
        segments = []
        
        # Only use high-quality, recent user messages for search context
        relevant_messages = get_relevant_conversation_history(state, max_messages=4)
        for msg in relevant_messages:
            if msg.type == MessageType.USER and msg.quality_score > 0.8:
                 segments.append(ContextSegment(
                    content=msg.content,
                    source='conversation',
                    relevance=msg.quality_score,
                    quality=ContextQuality.HIGH,
                    tokens_estimate=len(msg.content.split())
                ))
        return segments

    def _get_validation_context_segments(self, state: ConversationState) -> List[ContextSegment]:
        """Get context segments for response validation"""
        segments = []

        # Get all search results for validation
        for result in state.get('search_results', []):
            segments.append(ContextSegment(
                content=result.content,
                source='search',
                relevance=result.score,
                quality=ContextQuality.HIGH if result.validated else ContextQuality.MEDIUM,
                tokens_estimate=len(result.content.split())
            ))
        
        # Get recent conversation for consistency check
        relevant_messages = get_relevant_conversation_history(state, max_messages=2)
        for msg in relevant_messages:
             if msg.type == MessageType.ASSISTANT and msg.validated:
                segments.append(ContextSegment(
                    content=msg.content,
                    source='conversation',
                    relevance=msg.quality_score,
                    quality=ContextQuality.HIGH,
                    tokens_estimate=len(msg.content.split())
                ))

        return segments

    def _get_general_context_segments(self, state: ConversationState) -> List[ContextSegment]:
        """Get general purpose context segments"""
        return self._get_response_context_segments(state)

    def _filter_context_segments(self, segments: List[ContextSegment], 
                               state: ConversationState) -> List[ContextSegment]:
        """Filter out low-quality or conflicting segments"""
        
        filtered = []
        seen_content = set()
        
        for segment in segments:
            # Skip if below relevance threshold
            if segment.relevance < self.min_relevance_score:
                continue
            
            # Skip if redundant
            content_hash = hashlib.md5(segment.content.encode()).hexdigest()[:8]
            if content_hash in seen_content:
                continue
            seen_content.add(content_hash)
            
            # Validate segment
            passes, score = self.validate_context_segment(segment, state)
            if passes:
                segment.relevance = score  # Update with validated score
                filtered.append(segment)
        
        return filtered
    
    def _rank_context_segments(self, segments: List[ContextSegment], 
                             state: ConversationState) -> List[ContextSegment]:
        """Rank segments by relevance and quality"""
        
        # Calculate composite scores
        for segment in segments:
            quality_weight = {
                ContextQuality.HIGH: 1.0,
                ContextQuality.MEDIUM: 0.7,
                ContextQuality.LOW: 0.4,
                ContextQuality.CONFLICTED: 0.2,
                ContextQuality.POISONED: 0.0
            }
            
            segment.composite_score = (
                segment.relevance * 0.7 + 
                quality_weight.get(segment.quality, 0.5) * 0.3
            )
        
        # Sort by composite score
        segments.sort(key=lambda s: s.composite_score, reverse=True)
        
        return segments
    
    def _assemble_context(self, segments: List[ContextSegment], 
                        max_length: int) -> Tuple[str, ContextQuality]:
        """Assemble context from segments within token limit"""
        
        context_parts = []
        total_tokens = 0
        qualities = []
        
        for segment in segments:
            if total_tokens + segment.tokens_estimate > max_length:
                break
            
            context_parts.append(segment.content)
            total_tokens += segment.tokens_estimate
            qualities.append(segment.quality)
        
        # Determine overall quality
        if not qualities:
            overall_quality = ContextQuality.LOW
        elif ContextQuality.POISONED in qualities:
            overall_quality = ContextQuality.POISONED
        elif ContextQuality.CONFLICTED in qualities:
            overall_quality = ContextQuality.CONFLICTED
        elif all(q == ContextQuality.HIGH for q in qualities):
            overall_quality = ContextQuality.HIGH
        else:
            overall_quality = ContextQuality.MEDIUM
        
        context = "\n\n".join(context_parts)
        return context, overall_quality
    
    def _is_poisoned_content(self, content: str, state: ConversationState) -> bool:
        """Check if content is poisoned"""
        
        # Check against known poisoned content
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        if content_hash in state.get('poisoned_content', set()):
            return True
        
        # Detect new poisoning
        return self.detect_context_poisoning(content, state)
    
    def _detect_conflicts(self, segment: ContextSegment, 
                        state: ConversationState) -> List[Dict[str, Any]]:
        """Detect conflicts with existing context"""
        
        conflicts = []
        
        # Check against recent validated messages
        for msg in state['messages'][-5:]:
            if msg.validated and self._contents_conflict(segment.content, msg.content):
                conflicts.append({
                    'type': 'message_conflict',
                    'with_id': msg.id,
                    'severity': 'high'
                })
        
        # Check against other search results
        for result in state.get('search_results', []):
            if result.validated and self._contents_conflict(segment.content, result.content):
                conflicts.append({
                    'type': 'search_conflict',
                    'with_source': result.source,
                    'severity': 'medium'
                })
        
        return conflicts
    
    def _contents_conflict(self, content1: str, content2: str) -> bool:
        """Detect if two pieces of content conflict"""
        
        # Simple implementation - could be enhanced with NLI models
        # Check for contradictory statements
        contradictions = [
            ('is not', 'is'),
            ('cannot', 'can'),
            ('false', 'true'),
            ('incorrect', 'correct')
        ]
        
        content1_lower = content1.lower()
        content2_lower = content2.lower()
        
        for neg, pos in contradictions:
            if neg in content1_lower and pos in content2_lower:
                return True
            if pos in content1_lower and neg in content2_lower:
                return True
        
        return False
    
    def _contradicts_known_facts(self, content: str, state: ConversationState) -> bool:
        """Check if content contradicts known facts from validated sources"""
        
        # Check against validated search results
        for result in state.get('search_results', []):
            if result.validated and result.confidence > 0.8:
                if self._contents_conflict(content, result.content):
                    return True
        
        return False
    
    def _is_repetitive_content(self, content: str, state: ConversationState) -> bool:
        """Check if content is repetitive (sign of context poisoning)"""
        
        # Count similar content in recent messages
        similar_count = 0
        content_lower = content.lower()
        
        for msg in state['messages'][-10:]:
            msg_lower = msg.content.lower()
            # Simple similarity check - could use embeddings
            if len(set(content_lower.split()) & set(msg_lower.split())) > len(content_lower.split()) * 0.7:
                similar_count += 1
        
        return similar_count > 3
    
    def _calculate_segment_quality(self, segment: ContextSegment, 
                                 state: ConversationState) -> float:
        """Calculate quality score for a segment"""
        
        score = segment.relevance
        
        # Adjust based on source reliability
        source_weights = {
            'search': 0.9,
            'conversation': 0.8,
            'system': 1.0
        }
        score *= source_weights.get(segment.source, 0.7)
        
        # Penalize if conflicts exist
        if hasattr(segment, 'conflicts') and segment.conflicts:
            score *= 0.5
        
        # Boost if validated
        if segment.quality == ContextQuality.HIGH:
            score *= 1.2
        
        return min(score, 1.0) 