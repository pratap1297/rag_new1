"""
Enhanced Conversation State Management
With context quality tracking and validation
"""
from typing import Dict, List, Any, Optional, Literal, Set
from typing_extensions import TypedDict
from datetime import datetime
from enum import Enum
import uuid
from dataclasses import dataclass, field

# Memory management constants
MAX_CONVERSATION_HISTORY = 20
MAX_RELEVANT_HISTORY = 6      # Only most relevant messages for context
MAX_TOPICS_DISCUSSED = 10
MAX_ERROR_MESSAGES = 5
MAX_SEARCH_ATTEMPTS = 5
MAX_CONTEXT_LENGTH = 4000     # Characters for LLM context
CONTEXT_QUALITY_THRESHOLD = 0.7

class MessageType(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"
    ERROR = "error"

class ConversationPhase(Enum):
    GREETING = "greeting"
    UNDERSTANDING = "understanding"
    SEARCHING = "searching"
    RESPONDING = "responding"
    CLARIFYING = "clarifying"
    VALIDATING = "validating"    # NEW: Validation phase
    ENDING = "ending"

class ContextQuality(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    CONFLICTED = "conflicted"
    POISONED = "poisoned"

@dataclass
class Message:
    """Enhanced message with validation and quality tracking"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: MessageType = MessageType.USER
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    confidence: float = 1.0
    validated: bool = False
    quality_score: float = 1.0
    conflicts_with: List[str] = field(default_factory=list)  # Message IDs that conflict

@dataclass
class SearchResult:
    """Enhanced search result with quality tracking"""
    content: str
    score: float
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    strategy_used: str = "direct"
    confidence: float = 1.0
    validated: bool = False
    conflicts: List[str] = field(default_factory=list)

@dataclass
class ContextSegment:
    """Represents a segment of context with quality tracking"""
    content: str
    source: str  # 'conversation', 'search', 'system'
    relevance: float
    quality: ContextQuality
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    tokens_estimate: int = 0

class ConversationState(TypedDict):
    """Enhanced conversation state with context quality management"""
    
    # Core conversation data
    conversation_id: str
    session_id: str
    messages: List[Message]
    
    # Current conversation context
    current_phase: ConversationPhase
    user_intent: Optional[str]
    confidence_score: float
    
    # Query processing
    original_query: str
    processed_query: str
    query_keywords: List[str]
    search_filters: Dict[str, Any]
    is_contextual: bool
    
    # Topic tracking
    current_topic: Optional[str]
    topic_entities: List[str]
    topics_discussed: List[str]
    
    # Search and retrieval
    search_results: List[SearchResult]
    search_attempts: List[Dict[str, Any]]  # Track all search attempts
    relevant_sources: List[Dict[str, Any]]
    context_chunks: List[str]
    
    # Context quality management
    context_segments: List[ContextSegment]
    context_quality: ContextQuality
    context_conflicts: List[Dict[str, Any]]
    poisoned_content: Set[str]  # IDs of poisoned content
    
    # Response generation
    generated_response: str
    response_confidence: float
    response_validated: bool
    validation_errors: List[str]
    
    # Conversation management
    turn_count: int
    last_activity: str
    conversation_summary: str
    quality_metrics: Dict[str, float]
    
    # Error handling
    has_errors: bool
    error_messages: List[str]
    retry_count: int
    failed_operations: List[Dict[str, Any]]
    
    # Follow-up and suggestions
    suggested_questions: List[str]
    related_topics: List[str]
    
    # Metadata
    user_preferences: Dict[str, Any]
    conversation_metadata: Dict[str, Any]

def create_conversation_state(thread_id: Optional[str] = None) -> ConversationState:
    """Create a new conversation state with enhanced defaults"""
    return ConversationState(
        conversation_id=str(uuid.uuid4()),
        session_id=thread_id or str(uuid.uuid4()),
        messages=[],
        current_phase=ConversationPhase.GREETING,
        user_intent=None,
        confidence_score=0.0,
        original_query="",
        processed_query="",
        query_keywords=[],
        search_filters={},
        is_contextual=False,
        current_topic=None,
        topic_entities=[],
        topics_discussed=[],
        search_results=[],
        search_attempts=[],
        relevant_sources=[],
        context_chunks=[],
        context_segments=[],
        context_quality=ContextQuality.HIGH,
        context_conflicts=[],
        poisoned_content=set(),
        generated_response="",
        response_confidence=0.0,
        response_validated=False,
        validation_errors=[],
        turn_count=0,
        last_activity=datetime.now().isoformat(),
        conversation_summary="",
        quality_metrics={
            'context_quality': 1.0,
            'response_quality': 1.0,
            'coherence': 1.0,
            'relevance': 1.0
        },
        has_errors=False,
        error_messages=[],
        retry_count=0,
        failed_operations=[],
        suggested_questions=[],
        related_topics=[],
        user_preferences={},
        conversation_metadata={}
    )

def add_message_to_state(state: ConversationState, message_type: MessageType, 
                        content: str, metadata: Dict[str, Any] = None,
                        confidence: float = 1.0, validated: bool = False) -> ConversationState:
    """Add a new message with quality tracking"""
    message = Message(
        type=message_type,
        content=content,
        metadata=metadata or {},
        confidence=confidence,
        validated=validated,
        quality_score=confidence
    )
    
    new_state = state.copy()
    new_state['messages'] = state['messages'][-MAX_CONVERSATION_HISTORY+1:] + [message]
    new_state['turn_count'] = state['turn_count'] + 1
    new_state['last_activity'] = datetime.now().isoformat()
    
    # Apply memory management
    new_state = _apply_memory_management(new_state)
    
    return new_state

def _apply_memory_management(state: ConversationState) -> ConversationState:
    """Enhanced memory management with quality-aware pruning"""
    managed_state = state.copy()
    
    # Prioritize high-quality content when pruning
    if 'messages' in managed_state and len(managed_state['messages']) > MAX_CONVERSATION_HISTORY:
        # Keep high-quality messages preferentially
        messages = managed_state['messages']
        sorted_messages = sorted(messages, 
                               key=lambda m: (m.quality_score, m.timestamp), 
                               reverse=True)
        managed_state['messages'] = sorted_messages[:MAX_CONVERSATION_HISTORY]
        # Re-sort by timestamp for chronological order
        managed_state['messages'].sort(key=lambda m: m.timestamp)
    
    # Limit other lists
    if 'topics_discussed' in managed_state:
        managed_state['topics_discussed'] = managed_state['topics_discussed'][-MAX_TOPICS_DISCUSSED:]
    
    if 'error_messages' in managed_state:
        managed_state['error_messages'] = managed_state['error_messages'][-MAX_ERROR_MESSAGES:]
    
    # Remove failed operations older than current turn - 5
    if 'failed_operations' in managed_state:
        current_turn = managed_state.get('turn_count', 0)
        managed_state['failed_operations'] = [
            op for op in managed_state['failed_operations']
            if op.get('turn', 0) > current_turn - 5
        ]
    
    # Clean up poisoned content references
    if 'poisoned_content' in managed_state:
        # Convert to list, limit, then back to set
        poisoned_list = list(managed_state['poisoned_content'])
        managed_state['poisoned_content'] = set(poisoned_list[-10:])  # Keep last 10
    
    return managed_state

def get_relevant_conversation_history(state: ConversationState, 
                                    query: str = None,
                                    max_messages: int = MAX_RELEVANT_HISTORY) -> List[Message]:
    """Get only relevant conversation history to avoid context distraction"""
    if not state['messages']:
        return []
    
    # Filter out error messages and low-quality content
    relevant_messages = [
        msg for msg in state['messages']
        if msg.type != MessageType.ERROR and 
           msg.quality_score > 0.5 and
           msg.id not in state.get('poisoned_content', set())
    ]
    
    # If we have a query, prioritize messages related to it
    if query and state.get('query_keywords'):
        # Score messages by keyword overlap
        query_keywords = set(state['query_keywords'])
        scored_messages = []
        
        for msg in relevant_messages[-max_messages*2:]:  # Look at 2x window
            msg_keywords = set(msg.content.lower().split())
            overlap = len(query_keywords & msg_keywords)
            scored_messages.append((overlap, msg))
        
        # Sort by relevance, then take top N
        scored_messages.sort(key=lambda x: x[0], reverse=True)
        return [msg for _, msg in scored_messages[:max_messages]]
    
    # Otherwise, return most recent high-quality messages
    return relevant_messages[-max_messages:]

def calculate_context_quality(state: ConversationState) -> ContextQuality:
    """Calculate overall context quality"""
    if not state['messages']:
        return ContextQuality.HIGH
    
    # Check for poisoned content
    if state.get('poisoned_content'):
        return ContextQuality.POISONED
    
    # Check for conflicts
    conflict_count = len(state.get('context_conflicts', []))
    if conflict_count > 2:
        return ContextQuality.CONFLICTED
    
    # Calculate quality metrics
    avg_message_quality = sum(msg.quality_score for msg in state['messages'][-10:]) / min(len(state['messages']), 10)
    error_rate = len(state.get('error_messages', [])) / max(state['turn_count'], 1)
    
    quality_score = avg_message_quality * (1 - error_rate)
    
    if quality_score > 0.8:
        return ContextQuality.HIGH
    elif quality_score > 0.5:
        return ContextQuality.MEDIUM
    else:
        return ContextQuality.LOW

def get_conversation_history(state: ConversationState, max_messages: int = 10) -> List[Message]:
    """Get recent conversation history"""
    return state['messages'][-max_messages:] if state['messages'] else []

def get_context_summary(state: ConversationState) -> str:
    """Get a summary of the conversation context"""
    if not state['messages']:
        return "New conversation"
    
    recent_messages = get_conversation_history(state, 5)
    user_messages = [msg['content'] for msg in recent_messages if msg['type'] == MessageType.USER]
    
    if user_messages:
        topics = state['topics_discussed']
        return f"Recent topics: {', '.join(topics[-3:])}" if topics else f"Last user message: {user_messages[-1][:100]}"
    
    return "Ongoing conversation"

def should_end_conversation(state: ConversationState) -> bool:
    """Determine if conversation should end"""
    # End conversation criteria
    return (
        state['turn_count'] > 50 or  # Too many turns
        any("goodbye" in msg['content'].lower() or "bye" in msg['content'].lower() 
            for msg in state['messages'][-2:] if msg['type'] == MessageType.USER) or
        state['current_phase'] == ConversationPhase.ENDING
    )