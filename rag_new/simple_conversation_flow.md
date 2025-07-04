You're right to ask for a review. The current code has become quite complex and could be simplified while making it more extensible. Let me create a cleaner, more modular version that follows better software engineering principles.I've completely rewritten the conversation system with a clean, modular architecture. Here are the key improvements:

## 🏗️ Architecture Improvements

### 1. **Protocol-Based Design**
- Uses Python Protocols for `LLMClient` and `VectorStore` interfaces
- Easy to swap implementations without changing core logic
- Clear contracts for external dependencies

### 2. **Single Responsibility Components**
- `StateManager`: Manages conversation state
- `LLMAnalyzer`: Handles all LLM-based analysis
- `LLMResponseGenerator`: Generates different types of responses
- `SearchManager`: Handles search operations
- `ConversationNodes`: Clean node implementations

### 3. **Plugin System**
- Easy to add new features without modifying core code
- Plugins can hook into any conversation phase
- Example plugins included (Suggestions, Metrics)

## 🎯 Key Benefits

### **Simplicity**
- Each class has one clear purpose
- Methods are short and focused
- Easy to understand flow

### **Extensibility**
```python
# Adding a new feature is as simple as:
class MyNewPlugin(Plugin):
    def process(self, state: ConversationState) -> ConversationState:
        # Add your feature logic
        return state

# Register it
manager = ConversationManager(llm, vector_store, plugins=[MyNewPlugin()])
```

### **Testability**
- Protocol-based design makes mocking easy
- Each component can be tested in isolation
- Clear interfaces between components

### **Maintainability**
- Consistent patterns throughout
- Clear separation of concerns
- Well-documented code

## 📦 Core Components Explained

### **StateManager**
Handles all state operations in one place:
- Creating initial state
- Adding messages
- Managing conversation history
- Phase transitions

### **LLMAnalyzer**
Centralizes all LLM analysis tasks:
- Intent detection
- Context validation
- Quality scoring

### **Plugin System**
Add features without touching core code:
```python
class ContextQualityPlugin(Plugin):
    """Plugin that monitors context quality"""
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
        self.phases = [ConversationPhase.SEARCHING]
    
    def process(self, state: ConversationState) -> ConversationState:
        # Add context quality monitoring
        if state.get('search_results'):
            # Analyze and score context quality
            state['context_quality'] = self._analyze_quality(state)
        return state
```

## 🚀 Usage Remains Simple

```python
# Initialize
manager = ConversationManager(
    llm_client=your_llm,
    vector_store=your_qdrant,
    plugins=[plugin1, plugin2]
)

# Use
thread = manager.start_conversation()
response = manager.send_message(thread['thread_id'], "Hello!")
```

## 🔧 Easy to Extend

Want to add a new feature? Here are some examples:

### **Add Conversation Memory**
```python
class MemoryPlugin(Plugin):
    def __init__(self, memory_store):
        self.memory = memory_store
        self.phases = [ConversationPhase.UNDERSTANDING]
    
    def process(self, state: ConversationState) -> ConversationState:
        # Save important facts to memory
        # Retrieve relevant memories
        return state
```

### **Add Multi-Language Support**
```python
class TranslationPlugin(Plugin):
    def __init__(self, translator):
        self.translator = translator
        self.phases = [ConversationPhase.UNDERSTANDING, ConversationPhase.RESPONDING]
    
    def process(self, state: ConversationState) -> ConversationState:
        # Detect language and translate if needed
        return state
```

### **Add Analytics**
```python
class AnalyticsPlugin(Plugin):
    def __init__(self, analytics_client):
        self.analytics = analytics_client
        self.phases = list(ConversationPhase)  # All phases
    
    def process(self, state: ConversationState) -> ConversationState:
        # Track conversation metrics
        self.analytics.track(state)
        return state
```

## 🎨 Design Principles Used

1. **SOLID Principles**
   - Single Responsibility: Each class has one job
   - Open/Closed: Extensible via plugins, closed for modification
   - Liskov Substitution: Protocols ensure substitutability
   - Interface Segregation: Small, focused interfaces
   - Dependency Inversion: Depends on abstractions (Protocols)

2. **Composition over Inheritance**
   - Manager composes smaller components
   - Plugins add behavior without inheritance

3. **Explicit over Implicit**
   - Clear method names
   - Obvious data flow
   - No hidden side effects

This architecture is much cleaner, easier to understand, and simple to extend with new features. The plugin system especially makes it easy to add capabilities without touching the core conversation logic.

# modular_conversation_system.py
"""
Modular LLM-Based Conversation System
=====================================
A clean, extensible architecture for conversation management with LangGraph and Qdrant.
Follows SOLID principles and uses composition for easy feature addition.
"""

import logging
import json
import uuid
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple, Protocol
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver


# ============================================================================
# Core Types and Protocols
# ============================================================================

class MessageType(Enum):
    """Types of messages in conversation"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ConversationPhase(Enum):
    """Phases of conversation flow"""
    GREETING = "greeting"
    UNDERSTANDING = "understanding"
    SEARCHING = "searching"
    RESPONDING = "responding"
    ENDING = "ending"


@dataclass
class Message:
    """Conversation message"""
    content: str
    type: MessageType = MessageType.USER
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class SearchResult:
    """Search result from knowledge base"""
    content: str
    score: float
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConversationState(Dict[str, Any]):
    """Type alias for conversation state"""
    pass


# ============================================================================
# Protocols for Extensibility
# ============================================================================

class LLMClient(Protocol):
    """Protocol for LLM clients"""
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from prompt"""
        ...


class VectorStore(Protocol):
    """Protocol for vector stores"""
    def search(self, query: str, k: int = 5, **kwargs) -> List[SearchResult]:
        """Search for similar documents"""
        ...


class Plugin(ABC):
    """Base class for conversation plugins"""
    
    @abstractmethod
    def process(self, state: ConversationState) -> ConversationState:
        """Process conversation state"""
        pass


# ============================================================================
# Core Components
# ============================================================================

class StateManager:
    """Manages conversation state with clean interface"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def create_initial_state(self, thread_id: str) -> ConversationState:
        """Create a new conversation state"""
        return {
            'thread_id': thread_id,
            'conversation_id': str(uuid.uuid4()),
            'messages': [],
            'phase': ConversationPhase.GREETING,
            'turn_count': 0,
            'context': {},
            'search_results': [],
            'metadata': {},
            'created_at': datetime.now().isoformat()
        }
    
    def add_message(self, state: ConversationState, 
                   message: Message) -> ConversationState:
        """Add a message to the conversation"""
        messages = state.get('messages', [])
        messages.append({
            'id': message.id,
            'type': message.type.value,
            'content': message.content,
            'metadata': message.metadata,
            'timestamp': message.timestamp.isoformat()
        })
        
        state['messages'] = messages[-50:]  # Keep last 50 messages
        state['turn_count'] = state.get('turn_count', 0) + 1
        state['last_activity'] = datetime.now().isoformat()
        
        return state
    
    def get_recent_messages(self, state: ConversationState, 
                           n: int = 5) -> List[Dict[str, Any]]:
        """Get recent messages from state"""
        return state.get('messages', [])[-n:]
    
    def update_phase(self, state: ConversationState, 
                    phase: ConversationPhase) -> ConversationState:
        """Update conversation phase"""
        state['phase'] = phase
        return state


# ============================================================================
# LLM-Based Components
# ============================================================================

class LLMAnalyzer:
    """Analyzes conversation using LLM"""
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
        self.logger = logging.getLogger(__name__)
    
    def analyze_intent(self, message: str, context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze user intent using LLM"""
        context_str = self._format_context(context)
        
        prompt = f"""Analyze the user's intent from their message.

Message: "{message}"

Recent context:
{context_str}

Provide analysis in JSON:
{{
    "intent": "question|greeting|goodbye|clarification|other",
    "is_contextual": true/false,
    "entities": ["list", "of", "entities"],
    "keywords": ["important", "keywords"],
    "suggested_action": "search|respond|clarify|end"
}}"""

        try:
            response = self.llm.generate(prompt, temperature=0.1)
            return self._parse_json(response)
        except Exception as e:
            self.logger.error(f"Intent analysis failed: {e}")
            return {
                "intent": "other",
                "is_contextual": False,
                "suggested_action": "search"
            }
    
    def validate_context(self, content: str, query: str) -> Dict[str, Any]:
        """Validate if content is relevant and accurate"""
        prompt = f"""Assess if this content is relevant and accurate for the query.

Query: "{query}"
Content: "{content[:500]}..."

Provide assessment in JSON:
{{
    "is_relevant": true/false,
    "quality_score": 0.0-1.0,
    "has_issues": true/false,
    "issues": ["list", "of", "issues"]
}}"""

        try:
            response = self.llm.generate(prompt, temperature=0.1)
            return self._parse_json(response)
        except Exception as e:
            self.logger.error(f"Context validation failed: {e}")
            return {"is_relevant": True, "quality_score": 0.7}
    
    def _format_context(self, messages: List[Dict[str, Any]]) -> str:
        """Format messages for context"""
        formatted = []
        for msg in messages:
            role = msg.get('type', 'user').title()
            content = msg.get('content', '')[:200]
            formatted.append(f"{role}: {content}")
        return "\n".join(formatted)
    
    def _parse_json(self, response: str) -> Dict[str, Any]:
        """Parse JSON from LLM response"""
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
        except:
            pass
        return {}


class LLMResponseGenerator:
    """Generates responses using LLM"""
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
        self.logger = logging.getLogger(__name__)
    
    def generate_response(self, query: str, context: str, 
                         response_type: str = "normal") -> str:
        """Generate appropriate response based on type"""
        
        generators = {
            "normal": self._generate_normal_response,
            "no_results": self._generate_no_results_response,
            "greeting": self._generate_greeting,
            "clarification": self._generate_clarification
        }
        
        generator = generators.get(response_type, self._generate_normal_response)
        return generator(query, context)
    
    def _generate_normal_response(self, query: str, context: str) -> str:
        """Generate response with context"""
        prompt = f"""Answer the user's question based on the provided context.

Question: "{query}"

Context:
{context}

Provide a helpful, accurate response. If the context doesn't fully answer the question, acknowledge what you can answer and what you cannot."""

        try:
            return self.llm.generate(prompt, temperature=0.3, max_tokens=500)
        except Exception as e:
            self.logger.error(f"Response generation failed: {e}")
            return "I encountered an error generating a response. Please try again."
    
    def _generate_no_results_response(self, query: str, context: str) -> str:
        """Generate response when no results found"""
        prompt = f"""The user asked: "{query}"

No specific information was found. Generate a helpful response that:
1. Acknowledges the question
2. Explains that specific information wasn't found
3. Suggests how they might rephrase or what details would help"""

        try:
            return self.llm.generate(prompt, temperature=0.5, max_tokens=200)
        except:
            return "I couldn't find specific information about your question. Could you provide more details?"
    
    def _generate_greeting(self, query: str, context: str) -> str:
        """Generate greeting response"""
        prompt = "Generate a friendly, professional greeting for an AI assistant. Be concise and welcoming."
        
        try:
            return self.llm.generate(prompt, temperature=0.7, max_tokens=100)
        except:
            return "Hello! How can I help you today?"
    
    def _generate_clarification(self, query: str, context: str) -> str:
        """Generate clarification request"""
        prompt = f"""The user asked: "{query}"

Generate a polite clarification request that helps understand what specific information they need."""

        try:
            return self.llm.generate(prompt, temperature=0.5, max_tokens=150)
        except:
            return "Could you please provide more details about what you're looking for?"


# ============================================================================
# Search Component
# ============================================================================

class SearchManager:
    """Manages search operations"""
    
    def __init__(self, vector_store: Optional[VectorStore] = None, 
                 llm_analyzer: Optional[LLMAnalyzer] = None):
        self.vector_store = vector_store
        self.analyzer = llm_analyzer
        self.logger = logging.getLogger(__name__)
    
    def search(self, query: str, state: ConversationState) -> List[SearchResult]:
        """Execute search with optional context enhancement"""
        if not self.vector_store:
            return []
        
        try:
            # Basic search
            results = self.vector_store.search(query, k=10)
            
            # Validate results if analyzer available
            if self.analyzer:
                validated_results = []
                for result in results:
                    validation = self.analyzer.validate_context(result.content, query)
                    if validation.get('is_relevant', True) and validation.get('quality_score', 0) > 0.5:
                        validated_results.append(result)
                
                return validated_results[:5]
            
            return results[:5]
            
        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            return []


# ============================================================================
# Conversation Nodes (Clean Implementation)
# ============================================================================

class ConversationNodes:
    """Clean implementation of conversation nodes"""
    
    def __init__(self, 
                 state_manager: StateManager,
                 llm_analyzer: LLMAnalyzer,
                 response_generator: LLMResponseGenerator,
                 search_manager: SearchManager):
        self.state_mgr = state_manager
        self.analyzer = llm_analyzer
        self.generator = response_generator
        self.search_mgr = search_manager
        self.logger = logging.getLogger(__name__)
    
    def greet(self, state: ConversationState) -> ConversationState:
        """Handle greeting"""
        if state.get('turn_count', 0) == 0:
            greeting = self.generator.generate_response("", "", "greeting")
            message = Message(content=greeting, type=MessageType.ASSISTANT)
            state = self.state_mgr.add_message(state, message)
        
        return self.state_mgr.update_phase(state, ConversationPhase.UNDERSTANDING)
    
    def understand(self, state: ConversationState) -> ConversationState:
        """Understand user intent"""
        messages = state.get('messages', [])
        if not messages:
            return state
        
        # Get last user message
        user_messages = [m for m in messages if m['type'] == MessageType.USER.value]
        if not user_messages:
            return state
        
        last_message = user_messages[-1]['content']
        context = self.state_mgr.get_recent_messages(state, 3)
        
        # Analyze intent
        analysis = self.analyzer.analyze_intent(last_message, context)
        
        # Store analysis in state
        state['current_analysis'] = analysis
        state['current_query'] = last_message
        
        # Update phase based on intent
        if analysis.get('intent') == 'goodbye':
            state = self.state_mgr.update_phase(state, ConversationPhase.ENDING)
        elif analysis.get('suggested_action') == 'search':
            state = self.state_mgr.update_phase(state, ConversationPhase.SEARCHING)
        else:
            state = self.state_mgr.update_phase(state, ConversationPhase.RESPONDING)
        
        return state
    
    def search(self, state: ConversationState) -> ConversationState:
        """Search for relevant information"""
        query = state.get('current_query', '')
        if not query:
            return self.state_mgr.update_phase(state, ConversationPhase.RESPONDING)
        
        # Execute search
        results = self.search_mgr.search(query, state)
        state['search_results'] = [
            {
                'content': r.content,
                'score': r.score,
                'source': r.source,
                'metadata': r.metadata
            }
            for r in results
        ]
        
        return self.state_mgr.update_phase(state, ConversationPhase.RESPONDING)
    
    def respond(self, state: ConversationState) -> ConversationState:
        """Generate and add response"""
        query = state.get('current_query', '')
        search_results = state.get('search_results', [])
        
        # Build context from search results
        if search_results:
            context = "\n\n".join([
                f"Source: {r['source']}\n{r['content'][:300]}..."
                for r in search_results[:3]
            ])
            response_type = "normal"
        else:
            context = ""
            response_type = "no_results"
        
        # Generate response
        response = self.generator.generate_response(query, context, response_type)
        
        # Add to conversation
        message = Message(content=response, type=MessageType.ASSISTANT)
        state = self.state_mgr.add_message(state, message)
        
        # Clear current query
        state['current_query'] = None
        state['current_analysis'] = None
        
        return state


# ============================================================================
# Plugin System for Extensibility
# ============================================================================

class PluginManager:
    """Manages conversation plugins"""
    
    def __init__(self):
        self.plugins: List[Plugin] = []
        self.logger = logging.getLogger(__name__)
    
    def register(self, plugin: Plugin) -> None:
        """Register a new plugin"""
        self.plugins.append(plugin)
        self.logger.info(f"Registered plugin: {plugin.__class__.__name__}")
    
    def apply_plugins(self, state: ConversationState, 
                     phase: ConversationPhase) -> ConversationState:
        """Apply all plugins for the given phase"""
        for plugin in self.plugins:
            try:
                if hasattr(plugin, 'phases') and phase in plugin.phases:
                    state = plugin.process(state)
            except Exception as e:
                self.logger.error(f"Plugin {plugin.__class__.__name__} failed: {e}")
        
        return state


# Example Plugin
class SuggestionPlugin(Plugin):
    """Plugin that adds follow-up suggestions"""
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
        self.phases = [ConversationPhase.RESPONDING]
    
    def process(self, state: ConversationState) -> ConversationState:
        """Add suggestions to response"""
        if not state.get('search_results'):
            return state
        
        # Generate suggestions based on results
        context = state.get('search_results', [])[0].get('content', '')[:200]
        prompt = f"""Based on this topic: {context}

Generate 3 natural follow-up questions the user might ask.
One question per line."""

        try:
            suggestions = self.llm.generate(prompt, temperature=0.7)
            state['suggestions'] = [s.strip() for s in suggestions.split('\n') if s.strip()][:3]
        except:
            pass
        
        return state


# ============================================================================
# Main Conversation Manager
# ============================================================================

class ConversationManager:
    """Main conversation manager with clean architecture"""
    
    def __init__(self, 
                 llm_client: LLMClient,
                 vector_store: Optional[VectorStore] = None,
                 plugins: Optional[List[Plugin]] = None):
        
        # Initialize components
        self.state_manager = StateManager()
        self.llm_analyzer = LLMAnalyzer(llm_client)
        self.response_generator = LLMResponseGenerator(llm_client)
        self.search_manager = SearchManager(vector_store, self.llm_analyzer)
        
        # Initialize nodes
        self.nodes = ConversationNodes(
            self.state_manager,
            self.llm_analyzer,
            self.response_generator,
            self.search_manager
        )
        
        # Plugin system
        self.plugin_manager = PluginManager()
        if plugins:
            for plugin in plugins:
                self.plugin_manager.register(plugin)
        
        # Build graph
        self.graph = self._build_graph()
        self.checkpointer = MemorySaver()
        self.logger = logging.getLogger(__name__)
    
    def _build_graph(self) -> StateGraph:
        """Build the conversation flow graph"""
        workflow = StateGraph(dict)
        
        # Add nodes
        workflow.add_node("greet", self._wrap_node(self.nodes.greet))
        workflow.add_node("understand", self._wrap_node(self.nodes.understand))
        workflow.add_node("search", self._wrap_node(self.nodes.search))
        workflow.add_node("respond", self._wrap_node(self.nodes.respond))
        
        # Define flow
        workflow.set_entry_point("greet")
        workflow.add_edge("greet", "understand")
        
        # Conditional routing
        workflow.add_conditional_edges(
            "understand",
            self._route_from_understanding,
            {
                "search": "search",
                "respond": "respond",
                "end": END
            }
        )
        
        workflow.add_edge("search", "respond")
        
        workflow.add_conditional_edges(
            "respond",
            self._route_from_response,
            {
                "continue": "understand",
                "end": END
            }
        )
        
        return workflow.compile(checkpointer=self.checkpointer)
    
    def _wrap_node(self, node_func):
        """Wrap node function with plugin processing"""
        def wrapped(state: ConversationState) -> ConversationState:
            # Process node
            state = node_func(state)
            
            # Apply plugins
            phase = state.get('phase', ConversationPhase.UNDERSTANDING)
            state = self.plugin_manager.apply_plugins(state, phase)
            
            return state
        
        return wrapped
    
    def _route_from_understanding(self, state: ConversationState) -> str:
        """Route from understanding phase"""
        phase = state.get('phase', ConversationPhase.UNDERSTANDING)
        
        if phase == ConversationPhase.ENDING:
            return "end"
        elif phase == ConversationPhase.SEARCHING:
            return "search"
        else:
            return "respond"
    
    def _route_from_response(self, state: ConversationState) -> str:
        """Route from response phase"""
        if state.get('phase') == ConversationPhase.ENDING:
            return "end"
        
        # Continue if under turn limit
        if state.get('turn_count', 0) < 50:
            return "continue"
        
        return "end"
    
    def start_conversation(self, thread_id: Optional[str] = None) -> Dict[str, Any]:
        """Start a new conversation"""
        thread_id = thread_id or str(uuid.uuid4())
        
        # Create initial state
        initial_state = self.state_manager.create_initial_state(thread_id)
        
        # Process through graph
        config = {"configurable": {"thread_id": thread_id}}
        state = self.graph.invoke(initial_state, config)
        
        return self._format_response(state)
    
    def send_message(self, thread_id: str, message: str) -> Dict[str, Any]:
        """Send a message in existing conversation"""
        # Get current state
        config = {"configurable": {"thread_id": thread_id}}
        current_state = self._get_state(thread_id)
        
        # Add user message
        user_message = Message(content=message, type=MessageType.USER)
        current_state = self.state_manager.add_message(current_state, user_message)
        
        # Process through graph
        state = self.graph.invoke(current_state, config)
        
        return self._format_response(state)
    
    def _get_state(self, thread_id: str) -> ConversationState:
        """Get conversation state"""
        config = {"configurable": {"thread_id": thread_id}}
        checkpoint = self.checkpointer.get_tuple(config)
        
        if checkpoint and checkpoint.checkpoint:
            return checkpoint.checkpoint.get("channel_values", {})
        
        return self.state_manager.create_initial_state(thread_id)
    
    def _format_response(self, state: ConversationState) -> Dict[str, Any]:
        """Format state as API response"""
        messages = state.get('messages', [])
        assistant_messages = [m for m in messages if m['type'] == MessageType.ASSISTANT.value]
        last_response = assistant_messages[-1]['content'] if assistant_messages else ""
        
        return {
            'thread_id': state.get('thread_id'),
            'response': last_response,
            'suggestions': state.get('suggestions', []),
            'sources': [
                {
                    'content': s['content'][:200] + '...',
                    'source': s['source'],
                    'score': s['score']
                }
                for s in state.get('search_results', [])[:3]
            ],
            'turn_count': state.get('turn_count', 0),
            'phase': state.get('phase', ConversationPhase.UNDERSTANDING).value
        }


# ============================================================================
# Example Usage and Extension
# ============================================================================

if __name__ == "__main__":
    # Example custom plugin
    class MetricsPlugin(Plugin):
        """Plugin that tracks conversation metrics"""
        
        def __init__(self):
            self.phases = [ConversationPhase.RESPONDING]
        
        def process(self, state: ConversationState) -> ConversationState:
            """Track response time and quality"""
            state['metrics'] = state.get('metrics', {})
            state['metrics']['responses'] = state['metrics'].get('responses', 0) + 1
            state['metrics']['last_response_time'] = datetime.now().isoformat()
            return state
    
    
    # Mock implementations for testing
    class MockLLMClient:
        def generate(self, prompt: str, **kwargs) -> str:
            if "JSON" in prompt:
                return '{"intent": "question", "suggested_action": "search"}'
            return "This is a mock response."
    
    
    class MockVectorStore:
        def search(self, query: str, k: int = 5, **kwargs) -> List[SearchResult]:
            return [
                SearchResult(
                    content="Mock search result about Building A access points",
                    score=0.95,
                    source="mock_doc.pdf"
                )
            ]
    
    
    # Initialize system
    llm = MockLLMClient()
    vector_store = MockVectorStore()
    
    # Create plugins
    suggestion_plugin = SuggestionPlugin(llm)
    metrics_plugin = MetricsPlugin()
    
    # Create manager
    manager = ConversationManager(
        llm_client=llm,
        vector_store=vector_store,
        plugins=[suggestion_plugin, metrics_plugin]
    )
    
    # Use the system
    thread = manager.start_conversation()
    print(f"Started conversation: {thread['thread_id']}")
    
    response = manager.send_message(
        thread['thread_id'],
        "What access points are in Building A?"
    )
    print(f"Response: {response['response']}")
    print(f"Sources: {response['sources']}")
    print(f"Suggestions: {response['suggestions']}")