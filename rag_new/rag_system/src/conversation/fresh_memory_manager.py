"""
FreshMemoryManager Module
Manages short-term, long-term, and working memory for the conversation
"""
import logging
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
from enum import Enum
import uuid


class MemoryType(Enum):
    """Types of memory in the conversation system"""
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    WORKING = "working"


class MemoryPriority(Enum):
    """Priority levels for memory chunks"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class FreshMemoryManager:
    """
    Manages short-term, long-term, and working memory for the conversation.
    Provides methods for storing, retrieving, and managing memory chunks.
    """
    
    def __init__(self):
        """Initialize the memory manager"""
        self.logger = logging.getLogger(__name__)
        
        # Initialize memory stores
        self.short_term_memory: Dict[str, Dict[str, Any]] = {}
        self.long_term_memory: Dict[str, Dict[str, Any]] = {}
        self.working_memory: Dict[str, Dict[str, Any]] = {}
        
        # Memory capacity limits
        self.max_short_term = 20
        self.max_long_term = 100
        self.max_working = 10
        
        self.logger.info("FreshMemoryManager initialized")
    
    def store_chunk(self, content: str, memory_type: MemoryType, 
                   priority: MemoryPriority = MemoryPriority.MEDIUM,
                   tags: Set[str] = None) -> str:
        """
        Store a chunk of information in the appropriate memory store
        
        Args:
            content: The text content to store
            memory_type: Which memory store to use
            priority: Importance of this memory chunk
            tags: Set of tags for categorization and retrieval
            
        Returns:
            str: ID of the stored chunk
        """
        chunk_id = str(uuid.uuid4())
        
        memory_chunk = {
            'id': chunk_id,
            'content': content,
            'priority': priority.value,
            'tags': tags or set(),
            'created_at': datetime.now().isoformat(),
            'last_accessed': datetime.now().isoformat(),
            'access_count': 0
        }
        
        # Store in the appropriate memory store
        if memory_type == MemoryType.SHORT_TERM:
            self._manage_capacity(self.short_term_memory, self.max_short_term)
            self.short_term_memory[chunk_id] = memory_chunk
        elif memory_type == MemoryType.LONG_TERM:
            self._manage_capacity(self.long_term_memory, self.max_long_term)
            self.long_term_memory[chunk_id] = memory_chunk
        elif memory_type == MemoryType.WORKING:
            self._manage_capacity(self.working_memory, self.max_working)
            self.working_memory[chunk_id] = memory_chunk
        
        self.logger.debug(f"Stored {memory_type.value} memory chunk: {chunk_id}")
        return chunk_id
    
    def get_chunk(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific memory chunk by ID"""
        # Check all memory stores
        for memory_store in [self.short_term_memory, self.long_term_memory, self.working_memory]:
            if chunk_id in memory_store:
                chunk = memory_store[chunk_id]
                # Update access metadata
                chunk['last_accessed'] = datetime.now().isoformat()
                chunk['access_count'] += 1
                return chunk
        
        return None
    
    def get_relevant_context(self, query: str, max_size: int = 1000) -> List[str]:
        """
        Get memory chunks relevant to the current query
        
        Args:
            query: The query to find relevant context for
            max_size: Maximum total size in characters
            
        Returns:
            List[str]: List of relevant memory chunk contents
        """
        # Simple keyword matching for now
        keywords = set(query.lower().split())
        
        relevant_chunks = []
        total_size = 0
        
        # First check working memory (highest priority)
        for chunk in self.working_memory.values():
            if total_size >= max_size:
                break
                
            content = chunk['content']
            chunk_keywords = set(content.lower().split())
            
            # Check for keyword overlap
            if keywords.intersection(chunk_keywords):
                relevant_chunks.append(content)
                total_size += len(content)
                # Update access metadata
                chunk['last_accessed'] = datetime.now().isoformat()
                chunk['access_count'] += 1
        
        # Then check short-term memory
        for chunk in self.short_term_memory.values():
            if total_size >= max_size:
                break
                
            content = chunk['content']
            chunk_keywords = set(content.lower().split())
            
            # Check for keyword overlap
            if keywords.intersection(chunk_keywords):
                relevant_chunks.append(content)
                total_size += len(content)
                # Update access metadata
                chunk['last_accessed'] = datetime.now().isoformat()
                chunk['access_count'] += 1
        
        # Finally check long-term memory
        for chunk in self.long_term_memory.values():
            if total_size >= max_size:
                break
                
            content = chunk['content']
            chunk_keywords = set(content.lower().split())
            
            # Check for keyword overlap
            if keywords.intersection(chunk_keywords):
                relevant_chunks.append(content)
                total_size += len(content)
                # Update access metadata
                chunk['last_accessed'] = datetime.now().isoformat()
                chunk['access_count'] += 1
        
        self.logger.info(f"Found {len(relevant_chunks)} relevant memory chunks for query")
        return relevant_chunks
    
    def _manage_capacity(self, memory_store: Dict[str, Dict[str, Any]], max_capacity: int) -> None:
        """
        Manage memory capacity by removing lowest priority or least recently used chunks
        
        Args:
            memory_store: The memory store to manage
            max_capacity: Maximum number of chunks allowed
        """
        if len(memory_store) < max_capacity:
            return
        
        # Sort by priority (low first) and then by last accessed time (oldest first)
        chunks_to_sort = list(memory_store.items())
        chunks_to_sort.sort(
            key=lambda x: (
                0 if x[1]['priority'] == MemoryPriority.LOW.value else 
                1 if x[1]['priority'] == MemoryPriority.MEDIUM.value else 2,
                x[1]['last_accessed']
            )
        )
        
        # Remove oldest, lowest priority chunks
        chunks_to_remove = chunks_to_sort[:len(memory_store) - max_capacity + 1]
        for chunk_id, _ in chunks_to_remove:
            del memory_store[chunk_id]
    
    def clear_memory(self, memory_type: Optional[MemoryType] = None) -> None:
        """Clear memory of the specified type, or all if not specified"""
        if memory_type == MemoryType.SHORT_TERM:
            self.short_term_memory.clear()
        elif memory_type == MemoryType.LONG_TERM:
            self.long_term_memory.clear()
        elif memory_type == MemoryType.WORKING:
            self.working_memory.clear()
        else:
            self.short_term_memory.clear()
            self.long_term_memory.clear()
            self.working_memory.clear()
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about the current memory usage"""
        return {
            'short_term_count': len(self.short_term_memory),
            'long_term_count': len(self.long_term_memory),
            'working_count': len(self.working_memory),
            'total_chunks': len(self.short_term_memory) + len(self.long_term_memory) + len(self.working_memory),
            'total_size_bytes': sum(len(chunk['content']) for chunk in self.short_term_memory.values()) +
                              sum(len(chunk['content']) for chunk in self.long_term_memory.values()) +
                              sum(len(chunk['content']) for chunk in self.working_memory.values())
        }
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Get a summary of the current context in memory"""
        return {
            'memory_stats': self.get_memory_stats(),
            'short_term_topics': self._extract_topics(self.short_term_memory),
            'working_topics': self._extract_topics(self.working_memory),
            'timestamp': datetime.now().isoformat()
        }
    
    def _extract_topics(self, memory_store: Dict[str, Dict[str, Any]]) -> List[str]:
        """Extract main topics from a memory store"""
        all_tags = set()
        for chunk in memory_store.values():
            all_tags.update(chunk.get('tags', set()))
        return list(all_tags) 