"""
FreshContextManager Module
Manages context for the conversation system
"""
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime
import uuid
from dataclasses import dataclass


@dataclass
class ContextChunk:
    """Represents a chunk of context"""
    content: str
    source: str
    chunk_type: str
    confidence: float
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class FreshContextManager:
    """
    Manages context for the conversation system.
    Handles adding, retrieving, and filtering context chunks.
    """
    
    def __init__(self):
        """Initialize the context manager"""
        self.logger = logging.getLogger(__name__)
        
        # Context storage
        self.context_chunks: Dict[str, ContextChunk] = {}
        
        # Context type priorities (higher = more important)
        self.type_priorities = {
            'knowledge': 3,
            'conversation': 2,
            'system': 1
        }
        
        self.logger.info("FreshContextManager initialized")
    
    def add_chunk(self, content: str, source: str, chunk_type: str, 
                 confidence: float) -> Tuple[bool, str]:
        """
        Add a context chunk
        
        Args:
            content: The text content
            source: Where this content came from
            chunk_type: Type of context (knowledge, conversation, system)
            confidence: Confidence score (0-1)
            
        Returns:
            Tuple[bool, str]: Success flag and message/chunk_id
        """
        if not content or not isinstance(content, str):
            return False, "Invalid content"
        
        if chunk_type not in self.type_priorities:
            chunk_type = 'knowledge'  # Default
        
        chunk_id = str(uuid.uuid4())
        chunk = ContextChunk(
            content=content,
            source=source,
            chunk_type=chunk_type,
            confidence=max(0.0, min(1.0, confidence))  # Clamp to 0-1
        )
        
        self.context_chunks[chunk_id] = chunk
        return True, chunk_id
    
    def get_chunk(self, chunk_id: str) -> Optional[ContextChunk]:
        """Get a specific context chunk by ID"""
        return self.context_chunks.get(chunk_id)
    
    def get_relevant_chunks(self, query: str, max_chunks: int = 5) -> List[ContextChunk]:
        """
        Get chunks relevant to the query
        
        Args:
            query: The query to match against
            max_chunks: Maximum number of chunks to return
            
        Returns:
            List[ContextChunk]: List of relevant chunks
        """
        # Simple keyword matching for now
        keywords = set(query.lower().split())
        
        scored_chunks = []
        for chunk_id, chunk in self.context_chunks.items():
            content = chunk.content.lower()
            
            # Count keyword matches
            match_count = sum(1 for keyword in keywords if keyword in content)
            
            # Calculate relevance score
            type_priority = self.type_priorities.get(chunk.chunk_type, 1)
            relevance = (match_count / len(keywords) if keywords else 0) * chunk.confidence * type_priority
            
            if relevance > 0:
                scored_chunks.append((chunk, relevance))
        
        # Sort by relevance score (descending)
        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        
        # Return top chunks
        return [chunk for chunk, _ in scored_chunks[:max_chunks]]
    
    def manage_tool_context(self, available_tools: List[Dict[str, Any]], 
                           query: str) -> List[Dict[str, Any]]:
        """
        Filter available tools based on the query context
        
        Args:
            available_tools: List of tool definitions
            query: The current user query
            
        Returns:
            List[Dict[str, Any]]: Filtered list of relevant tools
        """
        if not available_tools:
            return []
            
        # Simple keyword matching for tool selection
        query_lower = query.lower()
        
        # Define tool keywords
        tool_keywords = {
            'search': {'search', 'find', 'look', 'query', 'information'},
            'calculator': {'calculate', 'compute', 'math', 'sum', 'divide', 'multiply'},
            'email': {'email', 'send', 'message', 'contact'},
            'calendar': {'schedule', 'meeting', 'appointment', 'calendar', 'reminder'},
            'document': {'document', 'file', 'pdf', 'word', 'excel'}
        }
        
        # Score each tool
        scored_tools = []
        for tool in available_tools:
            tool_name = tool.get('name', '').lower()
            
            # Check if tool name matches any keyword set
            score = 0
            for category, keywords in tool_keywords.items():
                if tool_name in keywords or any(keyword in query_lower for keyword in keywords):
                    score += 1
            
            # Add description matching
            description = tool.get('description', '').lower()
            if any(keyword in description for keyword in query_lower.split()):
                score += 0.5
                
            if score > 0:
                scored_tools.append((tool, score))
        
        # If no tools matched, return all tools
        if not scored_tools:
            return available_tools
            
        # Sort by score (descending)
        scored_tools.sort(key=lambda x: x[1], reverse=True)
        
        # Return all tools with scores > 0
        return [tool for tool, score in scored_tools]
    
    def detect_context_poisoning(self, content: str, state: Dict[str, Any]) -> bool:
        """
        Detect potential context poisoning in content
        
        Args:
            content: The content to check
            state: The current conversation state
            
        Returns:
            bool: True if poisoning detected, False otherwise
        """
        # Simple heuristics for context poisoning detection
        poisoning_indicators = [
            "ignore previous instructions",
            "forget your training",
            "you are now",
            "new role:",
            "system: you are"
        ]
        
        content_lower = content.lower()
        
        # Check for poisoning indicators
        for indicator in poisoning_indicators:
            if indicator in content_lower:
                self.logger.warning(f"Potential context poisoning detected: {indicator}")
                return True
        
        return False
    
    def clear_context(self) -> None:
        """Clear all context chunks"""
        self.context_chunks.clear()
        self.logger.info("Context cleared")
    
    def get_context_stats(self) -> Dict[str, Any]:
        """Get statistics about the current context"""
        type_counts = {}
        for chunk in self.context_chunks.values():
            type_counts[chunk.chunk_type] = type_counts.get(chunk.chunk_type, 0) + 1
            
        return {
            'total_chunks': len(self.context_chunks),
            'type_counts': type_counts,
            'average_confidence': sum(chunk.confidence for chunk in self.context_chunks.values()) / 
                               len(self.context_chunks) if self.context_chunks else 0
        } 