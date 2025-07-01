"""
Conflict Resolver
Handles conflicts between different information sources
"""
import logging
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime

from .conversation_state import SearchResult, ConversationState

class ConflictResolver:
    """Resolves conflicts between different information sources"""
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self.logger = logging.getLogger(__name__)
        
    def resolve_search_conflicts(self, search_attempts: List[Dict[str, Any]], 
                               state: ConversationState) -> Dict[str, Any]:
        """Resolve conflicts between different search strategies"""
        
        if not search_attempts:
            return None
        
        # If only one attempt, no conflicts to resolve
        if len(search_attempts) == 1:
            return search_attempts[0]['result']
        
        self.logger.info(f"Resolving conflicts between {len(search_attempts)} search attempts")
        
        # Analyze conflicts
        conflicts = self._identify_conflicts(search_attempts)
        
        if not conflicts:
            # No conflicts, merge results
            return self._merge_search_results(search_attempts)
        
        # Resolve conflicts
        resolution_strategy = self._determine_resolution_strategy(conflicts, state)
        resolved_result = self._apply_resolution_strategy(
            search_attempts, conflicts, resolution_strategy, state
        )
        
        # Log resolution
        state['context_conflicts'].extend(conflicts)
        
        return resolved_result
    
    def validate_information_consistency(self, new_info: str, 
                                       existing_info: List[str]) -> Tuple[bool, List[str]]:
        """Validate if new information is consistent with existing information"""
        
        conflicts = []
        
        for existing in existing_info:
            if self._information_conflicts(new_info, existing):
                conflicts.append(existing)
        
        is_consistent = len(conflicts) == 0
        return is_consistent, conflicts
    
    def _identify_conflicts(self, search_attempts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify conflicts between search results"""
        
        conflicts = []
        
        # Compare each pair of attempts
        for i in range(len(search_attempts)):
            for j in range(i + 1, len(search_attempts)):
                attempt1 = search_attempts[i]
                attempt2 = search_attempts[j]
                
                # Compare sources
                sources1 = set(s.get('source', '') for s in attempt1['result'].get('sources', []))
                sources2 = set(s.get('source', '') for s in attempt2['result'].get('sources', []))
                
                # Check for conflicting information
                if sources1 and sources2:
                    # Different sources might have conflicting info
                    overlap = sources1 & sources2
                    if not overlap and len(sources1) > 0 and len(sources2) > 0:
                        # Different sources, potential conflict
                        conflict_info = self._analyze_source_conflict(
                            attempt1['result']['sources'],
                            attempt2['result']['sources']
                        )
                        
                        if conflict_info:
                            conflicts.append({
                                'type': 'source_conflict',
                                'attempt1': i,
                                'attempt2': j,
                                'details': conflict_info
                            })
        
        return conflicts
    
    def _analyze_source_conflict(self, sources1: List[Dict], 
                                sources2: List[Dict]) -> Optional[Dict[str, Any]]:
        """Analyze potential conflicts between source sets"""
        
        # Simple conflict detection based on content similarity
        # but different conclusions
        
        for s1 in sources1[:2]:  # Check top sources
            for s2 in sources2[:2]:
                content1 = s1.get('text', '')
                content2 = s2.get('text', '')
                
                if self._information_conflicts(content1, content2):
                    return {
                        'source1': s1.get('source', 'unknown'),
                        'source2': s2.get('source', 'unknown'),
                        'conflict_type': 'contradictory_information'
                    }
        
        return None
    
    def _information_conflicts(self, info1: str, info2: str) -> bool:
        """Check if two pieces of information conflict"""
        
        # Normalize
        info1_lower = info1.lower()
        info2_lower = info2.lower()
        
        # Check for numerical conflicts
        import re
        numbers1 = re.findall(r'\b\d+\b', info1)
        numbers2 = re.findall(r'\b\d+\b', info2)
        
        if numbers1 and numbers2 and numbers1 != numbers2:
            # Different numbers about same topic might indicate conflict
            return True
        
        # Check for contradictory statements
        contradictions = [
            ('is not', 'is'),
            ('are not', 'are'),
            ('cannot', 'can'),
            ('does not', 'does'),
            ('no', 'yes'),
            ('false', 'true')
        ]
        
        for neg, pos in contradictions:
            if (neg in info1_lower and pos in info2_lower) or \
               (pos in info1_lower and neg in info2_lower):
                return True
        
        return False
    
    def _determine_resolution_strategy(self, conflicts: List[Dict[str, Any]], 
                                     state: ConversationState) -> str:
        """Determine best strategy for resolving conflicts"""
        
        # Analyze conflict types
        conflict_types = [c['type'] for c in conflicts]
        
        if 'source_conflict' in conflict_types:
            # Prefer more reliable sources
            return 'source_reliability'
        elif 'temporal_conflict' in conflict_types:
            # Prefer more recent information
            return 'recency'
        else:
            # Default to score-based resolution
            return 'highest_score'
    
    def _apply_resolution_strategy(self, search_attempts: List[Dict[str, Any]], 
                                 conflicts: List[Dict[str, Any]],
                                 strategy: str, state: ConversationState) -> Dict[str, Any]:
        """Apply resolution strategy to conflicting results"""
        
        if strategy == 'source_reliability':
            # Rank attempts by source reliability
            scored_attempts = []
            for attempt in search_attempts:
                reliability = self._calculate_source_reliability(attempt['result'])
                scored_attempts.append((reliability, attempt))
            
            scored_attempts.sort(key=lambda x: x[0], reverse=True)
            best_attempt = scored_attempts[0][1]
            
            # Mark conflicts in the result
            self._mark_conflicts_in_result(best_attempt['result'], conflicts)
            
            return best_attempt['result']
        
        elif strategy == 'recency':
            # Prefer more recent information
            # For now, use the search attempt order as proxy
            return search_attempts[-1]['result']
        
        else:  # highest_score
            # Use attempt with highest average scores
            best_score = -1
            best_result = None
            
            for attempt in search_attempts:
                sources = attempt['result'].get('sources', [])
                if sources:
                    avg_score = sum(s.get('score', 0) for s in sources) / len(sources)
                    if avg_score > best_score:
                        best_score = avg_score
                        best_result = attempt['result']
            
            return best_result or search_attempts[0]['result']
    
    def _calculate_source_reliability(self, result: Dict[str, Any]) -> float:
        """Calculate reliability score for search result"""
        
        sources = result.get('sources', [])
        if not sources:
            return 0.0
        
        reliability_scores = []
        
        for source in sources:
            score = source.get('score', 0)
            source_name = source.get('source', '')
            
            # Boost score for certain source types
            if 'official' in source_name.lower():
                score *= 1.2
            elif 'verified' in source_name.lower():
                score *= 1.1
            
            reliability_scores.append(score)
        
        return sum(reliability_scores) / len(reliability_scores)
    
    def _merge_search_results(self, search_attempts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge non-conflicting search results"""
        
        merged_sources = []
        seen_content = set()
        
        for attempt in search_attempts:
            sources = attempt['result'].get('sources', [])
            
            for source in sources:
                # Create content hash to avoid duplicates
                content_hash = hash(source.get('text', ''))
                
                if content_hash not in seen_content:
                    seen_content.add(content_hash)
                    # Mark which strategy found this
                    source['strategy_used'] = attempt['strategy']
                    merged_sources.append(source)
        
        # Sort by score
        merged_sources.sort(key=lambda s: s.get('score', 0), reverse=True)
        
        # Take first result as base and update sources
        merged_result = search_attempts[0]['result'].copy()
        merged_result['sources'] = merged_sources[:10]  # Limit to top 10
        merged_result['merged_from'] = len(search_attempts)
        
        return merged_result
    
    def _mark_conflicts_in_result(self, result: Dict[str, Any], 
                                conflicts: List[Dict[str, Any]]):
        """Mark conflicts in the result for transparency"""
        
        result['has_conflicts'] = True
        result['conflict_count'] = len(conflicts)
        result['conflict_resolution'] = 'source_reliability'
        
        # Add conflict warnings to sources
        for source in result.get('sources', []):
            source['may_conflict'] = True