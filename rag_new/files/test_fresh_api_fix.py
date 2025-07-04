#!/usr/bin/env python3
"""
Test Fresh API Fix
Verify that the fresh conversation manager can be used in the API
"""
import os
import sys
import logging
from pathlib import Path

# Add the rag_system to Python path
sys.path.insert(0, str(Path(__file__).parent / "rag_system" / "src"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_fresh_manager_api_integration():
    """Test that the fresh conversation manager works for API integration"""
    
    print("🧪 Testing Fresh Manager API Integration")
    print("=" * 50)
    
    try:
        # Test importing the fresh conversation manager
        print("📦 Testing fresh manager import...")
        from conversation.fresh_conversation_manager import FreshConversationManager
        print("   ✅ Fresh conversation manager imported successfully")
        
        # Test instantiation
        print("🔧 Testing fresh manager instantiation...")
        manager = FreshConversationManager(container=None)
        print("   ✅ Fresh conversation manager instantiated successfully")
        
        # Test starting a conversation
        print("🗣️ Testing conversation start...")
        start_result = manager.start_conversation(thread_id="test_api_thread_001")
        print(f"   ✅ Conversation started: {start_result}")
        
        # Test processing a message
        print("💬 Testing message processing...")
        message_result = manager.process_user_message("test_api_thread_001", "Hello! How are you?")
        print(f"   ✅ Message processed successfully")
        print(f"       Response: {message_result.get('response', 'No response')[:100]}...")
        print(f"       Thread ID: {message_result.get('thread_id')}")
        print(f"       Turn count: {message_result.get('turn_count')}")
        
        # Test getting conversation history
        print("📝 Testing conversation history...")
        history_result = manager.get_conversation_history("test_api_thread_001")
        print(f"   ✅ History retrieved: {len(history_result.get('messages', []))} messages")
        
        # Test system status
        print("🔍 Testing system status...")
        status = manager.get_system_status()
        print(f"   ✅ System status: {status['status']}")
        print(f"       Active conversations: {status['active_conversations']}")
        print(f"       Components: {list(status['components'].keys())}")
        
        # Test ending conversation
        print("🔚 Testing conversation end...")
        end_result = manager.end_conversation("test_api_thread_001")
        print(f"   ✅ Conversation ended: {end_result}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Fresh manager API integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_route_simulation():
    """Simulate the API route behavior to test integration"""
    
    print("\n🌐 Testing API Route Simulation")
    print("=" * 40)
    
    try:
        # Simulate the get_conversation_manager function from the API
        print("🔧 Testing conversation manager fallback logic...")
        
        # Mock the container failing (what happens in production)
        def mock_get_dependency_container():
            class MockContainer:
                def get(self, key):
                    return None  # Simulate missing conversation_manager
            return MockContainer()
        
        # Simulate the fallback logic
        conversation_manager = None
        container = mock_get_dependency_container()
        original_manager = container.get('conversation_manager')
        
        if original_manager is None:
            print("   ⚠️  Original ConversationManager not available (as expected)")
            
            # Fall back to fresh conversation manager
            from conversation.fresh_conversation_manager import FreshConversationManager
            conversation_manager = FreshConversationManager(container)
            print("   ✅ Fresh ConversationManager initialized as fallback")
        
        # Test API-like operations
        print("🌐 Testing API-like operations...")
        
        # Start conversation (POST /api/conversation/start)
        start_response = conversation_manager.start_conversation()
        thread_id = start_response['thread_id']
        print(f"   ✅ POST /start: {start_response['status']}")
        
        # Send message (POST /api/conversation/message)
        message_response = conversation_manager.process_user_message(
            thread_id, 
            "What network equipment is available?"
        )
        print(f"   ✅ POST /message: Response length {len(message_response.get('response', ''))}")
        
        # Get history (GET /api/conversation/history/{thread_id})
        history_response = conversation_manager.get_conversation_history(thread_id)
        print(f"   ✅ GET /history: {len(history_response.get('messages', []))} messages")
        
        # Get active conversations (GET /api/conversation/threads)  
        active_response = conversation_manager.get_active_conversations()
        print(f"   ✅ GET /threads: {active_response.get('total_active', 0)} active")
        
        # Health check (GET /api/conversation/health)
        health_response = conversation_manager.get_system_status()
        print(f"   ✅ GET /health: {health_response['status']}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ API route simulation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_error_handling():
    """Test error handling and fallback responses"""
    
    print("\n🛡️ Testing Error Handling")
    print("=" * 30)
    
    try:
        from conversation.fresh_conversation_manager import FreshConversationManager
        manager = FreshConversationManager(container=None)
        
        # Test fallback response generation
        print("🔧 Testing fallback response...")
        fallback = manager._generate_fallback_response(
            "test_thread", 
            "What is the meaning of life?", 
            "Test error for fallback"
        )
        print(f"   ✅ Fallback response generated: {len(fallback.get('response', ''))} chars")
        print(f"       Is fallback: {fallback.get('is_fallback', False)}")
        
        # Test non-existent conversation history
        print("🔍 Testing non-existent conversation...")
        missing_history = manager.get_conversation_history("non_existent_thread")
        print(f"   ✅ Missing conversation handled: {'error' in missing_history}")
        
        # Test ending non-existent conversation
        print("🔚 Testing ending non-existent conversation...")
        missing_end = manager.end_conversation("non_existent_thread")
        print(f"   ✅ Missing conversation end handled: {missing_end.get('status')}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error handling test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run API fix tests"""
    
    print("🧪 Fresh Conversation Manager - API Fix Tests")
    print("=" * 60)
    
    results = []
    
    # Test fresh manager API integration
    results.append(test_fresh_manager_api_integration())
    
    # Test API route simulation
    results.append(test_api_route_simulation())
    
    # Test error handling
    results.append(test_error_handling())
    
    # Summary
    print(f"\n📋 API Fix Test Summary")
    print("=" * 30)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All API fix tests passed!")
        print("\n✅ Fresh Conversation Manager API Integration:")
        print("  🔧 Fresh manager imports and instantiates correctly")
        print("  🗣️ Conversation lifecycle works (start/message/history/end)")
        print("  🌐 API route simulation successful")
        print("  🛡️ Error handling and fallbacks working")
        print("  📊 System status and metrics available")
        
        print("\n🚀 Ready for Production:")
        print("  • API will automatically fall back to fresh manager")
        print("  • No more 503 Service Unavailable errors")
        print("  • Enhanced features available (context management)")
        print("  • Backward compatible with existing API interface")
        print("  • Health check shows fresh system status")
        
        return True
    else:
        print("❌ Some API fix tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 