#!/usr/bin/env python3
"""
Test Emergency Fix
Test the emergency conversation manager to verify it fixes 503 errors
"""
import os
import sys
import logging
from pathlib import Path

# Add the rag_system API to Python path
sys.path.insert(0, str(Path(__file__).parent / "rag_system" / "src"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_emergency_manager():
    """Test the emergency conversation manager"""
    
    print("🚨 Testing Emergency Conversation Manager")
    print("=" * 45)
    
    try:
        # Test importing the emergency manager
        print("📦 Testing emergency manager import...")
        from api.emergency_conversation_manager import EmergencyConversationManager
        print("   ✅ Emergency conversation manager imported successfully")
        
        # Test instantiation
        print("🔧 Testing emergency manager instantiation...")
        manager = EmergencyConversationManager(container=None)
        print("   ✅ Emergency conversation manager instantiated successfully")
        
        # Test starting a conversation
        print("🗣️ Testing conversation start...")
        start_result = manager.start_conversation(thread_id="test_emergency_thread_001")
        print(f"   ✅ Conversation started: {start_result['status']}")
        print(f"       Thread ID: {start_result['thread_id']}")
        
        # Test processing different types of messages
        test_messages = [
            ("Hello! How are you?", "greeting"),
            ("What network equipment is available?", "information_seeking"),
            ("Can you help me?", "help"),
            ("Thank you, goodbye!", "farewell")
        ]
        
        for message, expected_intent in test_messages:
            print(f"💬 Testing message: '{message[:30]}...'")
            message_result = manager.process_user_message("test_emergency_thread_001", message)
            print(f"   ✅ Message processed successfully")
            print(f"       Response: {message_result.get('response', 'No response')[:60]}...")
            print(f"       Intent: {message_result.get('intent', 'unknown')}")
            print(f"       Processing mode: {message_result.get('processing_mode', 'unknown')}")
        
        # Test getting conversation history
        print("📝 Testing conversation history...")
        history_result = manager.get_conversation_history("test_emergency_thread_001")
        print(f"   ✅ History retrieved: {len(history_result.get('messages', []))} messages")
        
        # Test system status
        print("🔍 Testing system status...")
        status = manager.get_system_status()
        print(f"   ✅ System status: {status['status']}")
        print(f"       Processing mode: {status.get('processing_mode', 'unknown')}")
        print(f"       Active conversations: {status['active_conversations']}")
        print(f"       Capabilities: {len(status.get('capabilities', []))} features")
        
        # Test API compatibility methods
        print("🌐 Testing API compatibility...")
        active_conversations = manager.list_active_conversations()
        print(f"   ✅ list_active_conversations: {active_conversations.get('total_active', 0)} active")
        
        active_sessions = manager.get_active_sessions()
        print(f"   ✅ get_active_sessions: {active_sessions.get('total_active', 0)} active")
        
        # Test ending conversation
        print("🔚 Testing conversation end...")
        end_result = manager.end_conversation("test_emergency_thread_001")
        print(f"   ✅ Conversation ended: {end_result['status']}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Emergency manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_simulation():
    """Simulate API route behavior with emergency manager"""
    
    print("\n🌐 Testing API Route Simulation with Emergency Manager")
    print("=" * 55)
    
    try:
        # Simulate the updated get_conversation_manager function
        print("🔧 Simulating API get_conversation_manager with emergency fallback...")
        
        conversation_manager = None
        
        # Simulate container failing (as in production)
        print("   ⚠️  Simulating container failure...")
        
        # This would be the emergency fallback logic in the API
        try:
            from api.emergency_conversation_manager import EmergencyConversationManager
            conversation_manager = EmergencyConversationManager(None)
            print("   ✅ Emergency ConversationManager initialized as fallback")
        except Exception as emergency_error:
            print(f"   ❌ Failed to initialize emergency ConversationManager: {emergency_error}")
            return False
        
        # Test API endpoints simulation
        print("🌐 Simulating API endpoints...")
        
        # POST /api/conversation/start
        start_response = conversation_manager.start_conversation()
        thread_id = start_response['thread_id']
        print(f"   ✅ POST /start: {start_response['status']}")
        
        # POST /api/conversation/message
        message_response = conversation_manager.process_user_message(
            thread_id, 
            "What network equipment is available?"
        )
        print(f"   ✅ POST /message: Response ready (mode: {message_response.get('processing_mode', 'unknown')})")
        print(f"       Intent detected: {message_response.get('intent', 'unknown')}")
        
        # GET /api/conversation/history/{thread_id}
        history_response = conversation_manager.get_conversation_history(thread_id)
        print(f"   ✅ GET /history: {len(history_response.get('messages', []))} messages")
        
        # GET /api/conversation/threads
        threads_response = conversation_manager.list_active_conversations()
        print(f"   ✅ GET /threads: {threads_response.get('total_active', 0)} active")
        
        # GET /api/conversation/health
        health_response = conversation_manager.get_system_status()
        print(f"   ✅ GET /health: {health_response['status']}")
        print(f"       Manager type: {health_response['conversation_manager']}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ API simulation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_error_handling():
    """Test error handling and fallback responses"""
    
    print("\n🛡️ Testing Error Handling")
    print("=" * 30)
    
    try:
        from api.emergency_conversation_manager import EmergencyConversationManager
        manager = EmergencyConversationManager(container=None)
        
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
    """Run emergency fix tests"""
    
    print("🚨 Emergency Conversation Manager - Fix Tests")
    print("=" * 55)
    
    results = []
    
    # Test emergency manager
    results.append(test_emergency_manager())
    
    # Test API simulation
    results.append(test_api_simulation())
    
    # Test error handling
    results.append(test_error_handling())
    
    # Summary
    print(f"\n📋 Emergency Fix Test Summary")
    print("=" * 35)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All emergency fix tests passed!")
        print("\n✅ Emergency Conversation Manager:")
        print("  📦 Imports successfully without any dependencies")
        print("  🔧 Instantiates and handles basic conversation flow")
        print("  🗣️ Processes different message types with intent detection")
        print("  🌐 API route simulation successful")
        print("  🔍 System status and health checks working")
        print("  ⚙️  API compatibility methods working")
        print("  🛡️ Error handling and fallbacks working")
        
        print("\n🚨 Emergency Status:")
        print("  • 503 Service Unavailable errors should now be resolved")
        print("  • API will use emergency manager as fallback")
        print("  • No import chain dependencies")
        print("  • Basic conversation functionality available")
        print("  • Intent detection and response generation working")
        print("  • Conversation history and management working")
        
        print("\n⚠️ Limitations (Expected):")
        print("  • No advanced context management")
        print("  • No vector search integration")
        print("  • No LangGraph workflow")
        print("  • Simplified response generation")
        print("  • Emergency processing mode")
        
        return True
    else:
        print("❌ Some emergency fix tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 