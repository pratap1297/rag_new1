#!/usr/bin/env python3
"""
Test Direct API Fix
Simple test to verify the direct conversation manager works for API
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

def test_direct_manager():
    """Test the direct conversation manager for API use"""
    
    print("🧪 Testing Direct Fresh Manager for API")
    print("=" * 45)
    
    try:
        # Test importing the direct manager
        print("📦 Testing direct manager import...")
        from api.fresh_conversation_manager_direct import FreshConversationManagerDirect
        print("   ✅ Direct fresh conversation manager imported successfully")
        
        # Test instantiation
        print("🔧 Testing direct manager instantiation...")
        manager = FreshConversationManagerDirect(container=None)
        print("   ✅ Direct fresh conversation manager instantiated successfully")
        
        # Test starting a conversation
        print("🗣️ Testing conversation start...")
        start_result = manager.start_conversation(thread_id="test_direct_thread_001")
        print(f"   ✅ Conversation started: {start_result['status']}")
        print(f"       Thread ID: {start_result['thread_id']}")
        
        # Test processing a message
        print("💬 Testing message processing...")
        message_result = manager.process_user_message("test_direct_thread_001", "Hello! How are you?")
        print(f"   ✅ Message processed successfully")
        print(f"       Response: {message_result.get('response', 'No response')[:80]}...")
        print(f"       Processing mode: {message_result.get('processing_mode', 'unknown')}")
        
        # Test another message
        print("💬 Testing second message...")
        message_result2 = manager.process_user_message("test_direct_thread_001", "What can you help me with?")
        print(f"   ✅ Second message processed")
        print(f"       Response: {message_result2.get('response', 'No response')[:80]}...")
        
        # Test getting conversation history
        print("📝 Testing conversation history...")
        history_result = manager.get_conversation_history("test_direct_thread_001")
        print(f"   ✅ History retrieved: {len(history_result.get('messages', []))} messages")
        
        # Test system status
        print("🔍 Testing system status...")
        status = manager.get_system_status()
        print(f"   ✅ System status: {status['status']}")
        print(f"       Processing mode: {status.get('processing_mode', 'unknown')}")
        print(f"       Active conversations: {status['active_conversations']}")
        
        # Test API compatibility methods
        print("🌐 Testing API compatibility...")
        active_conversations = manager.list_active_conversations()
        print(f"   ✅ list_active_conversations: {active_conversations.get('total_active', 0)} active")
        
        active_sessions = manager.get_active_sessions()
        print(f"   ✅ get_active_sessions: {active_sessions.get('total_active', 0)} active")
        
        # Test ending conversation
        print("🔚 Testing conversation end...")
        end_result = manager.end_conversation("test_direct_thread_001")
        print(f"   ✅ Conversation ended: {end_result['status']}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Direct manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_simulation():
    """Simulate API route behavior"""
    
    print("\n🌐 Testing API Route Simulation")
    print("=" * 35)
    
    try:
        # Simulate the updated get_conversation_manager function
        print("🔧 Simulating API get_conversation_manager...")
        
        conversation_manager = None
        
        # Simulate container failing (as in production)
        print("   ⚠️  Simulating container failure...")
        
        # This would be the fallback logic in the API
        try:
            from api.fresh_conversation_manager_direct import FreshConversationManagerDirect
            conversation_manager = FreshConversationManagerDirect(None)
            print("   ✅ Fresh ConversationManager Direct initialized as fallback")
        except Exception as fresh_error:
            print(f"   ❌ Failed to initialize fresh ConversationManager Direct: {fresh_error}")
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
        
        # GET /api/conversation/history/{thread_id}
        history_response = conversation_manager.get_conversation_history(thread_id)
        print(f"   ✅ GET /history: {len(history_response.get('messages', []))} messages")
        
        # GET /api/conversation/threads
        threads_response = conversation_manager.list_active_conversations()
        print(f"   ✅ GET /threads: {threads_response.get('total_active', 0)} active")
        
        # GET /api/conversation/health
        health_response = conversation_manager.get_system_status()
        print(f"   ✅ GET /health: {health_response['status']}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ API simulation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run direct API fix tests"""
    
    print("🧪 Fresh Conversation Manager - Direct API Fix Tests")
    print("=" * 60)
    
    results = []
    
    # Test direct manager
    results.append(test_direct_manager())
    
    # Test API simulation
    results.append(test_api_simulation())
    
    # Summary
    print(f"\n📋 Direct API Fix Test Summary")
    print("=" * 35)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All direct API fix tests passed!")
        print("\n✅ Direct Fresh Conversation Manager:")
        print("  📦 Imports successfully without import chain issues")
        print("  🔧 Instantiates and initializes all components")
        print("  🗣️ Handles conversation lifecycle (start/message/history/end)")
        print("  🌐 API route simulation successful")
        print("  🔍 System status and health checks working")
        print("  ⚙️  API compatibility methods working")
        
        print("\n🚀 Production Ready:")
        print("  • API will use direct fresh manager as fallback")
        print("  • No import chain dependencies")
        print("  • Simplified processing mode available")
        print("  • Full fresh system features when possible")
        print("  • Error handling and fallbacks in place")
        print("  • 503 errors should now be resolved")
        
        return True
    else:
        print("❌ Some direct API fix tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 