#!/usr/bin/env python3
"""
Direct LLM Conversation Test
Test the conversation system directly without API overhead
"""
import sys
from pathlib import Path

# Add rag_system/src to path
sys.path.insert(0, str(Path("rag_system/src")))

def test_direct_conversation():
    """Test conversation with LLM client directly"""
    print("🧪 TESTING DIRECT LLM CONVERSATION")
    print("=" * 60)
    
    try:
        # Import required modules
        from core.dependency_container import DependencyContainer, register_core_services
        from conversation.conversation_manager import ConversationManager
        from conversation.conversation_state import MessageType
        
        print("✅ Modules imported successfully")
        
        # Create and register services
        print("🔧 Setting up dependency container...")
        container = DependencyContainer()
        register_core_services(container)
        print("✅ Core services registered")
        
        # Test LLM client directly
        print("🔧 Testing LLM client...")
        llm_client = container.get('llm_client')
        if llm_client:
            test_response = llm_client.generate("Hello", max_tokens=20)
            print(f"✅ LLM Client works: {test_response[:50]}...")
        else:
            print("❌ LLM Client is None")
            return False
        
        # Create conversation manager
        print("🔧 Creating conversation manager...")
        conversation_manager = ConversationManager(container)
        print("✅ Conversation manager created")
        
        # Test conversation scenarios
        print("\n🧪 TESTING CONVERSATION SCENARIOS")
        print("-" * 50)
        
        # Start conversation
        print("1. Starting conversation...")
        start_result = conversation_manager.start_conversation()
        thread_id = start_result['thread_id']
        print(f"✅ Conversation started: {thread_id}")
        print(f"Initial response: {start_result['response'][:100]}...")
        
        # Test scenario 1: Document count followed by follow-up
        print("\n2. Testing document count scenario...")
        response1 = conversation_manager.process_user_message(thread_id, "How many tickets in the system")
        print(f"Setup response: {response1['response'][:150]}...")
        
        # Follow-up question
        print("\n3. Testing follow-up question...")
        response2 = conversation_manager.process_user_message(thread_id, "which are these?")
        print(f"Follow-up response: {response2['response'][:200]}...")
        
        # Analyze response quality
        is_generic = "I don't have specific information readily available" in response2['response']
        is_contextual = not is_generic and len(response2['response']) > 50
        
        print(f"\n📊 RESPONSE ANALYSIS:")
        print(f"   Generic response: {'❌ Yes' if is_generic else '✅ No'}")
        print(f"   Contextual response: {'✅ Yes' if is_contextual else '❌ No'}")
        print(f"   Response length: {len(response2['response'])} chars")
        
        if is_contextual:
            print("✅ SUCCESS: Follow-up question answered contextually!")
        else:
            print("❌ ISSUE: Still getting generic responses")
            
        return is_contextual
        
    except Exception as e:
        print(f"❌ Error in direct conversation test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_direct_conversation()
    if success:
        print("\n🎯 DIRECT CONVERSATION TEST: PASSED")
    else:
        print("\n💥 DIRECT CONVERSATION TEST: FAILED") 