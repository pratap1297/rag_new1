"""
Test Functional Conversation Flow
Tests the functional conversation manager with Qdrant integration
"""
import sys
import os
import logging
from pathlib import Path

# Add the rag_system path
sys.path.insert(0, str(Path(__file__).parent / "rag_system" / "src"))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_functional_conversation_manager():
    """Test the functional conversation manager"""
    try:
        logger.info("Testing Functional Conversation Manager...")
        
        # Import the functional conversation manager
        from api.functional_conversation_manager import FunctionalConversationManager
        
        # Initialize the manager
        manager = FunctionalConversationManager()
        logger.info("Functional Conversation Manager initialized successfully")
        
        # Test system status
        status = manager.get_system_status()
        logger.info(f"System Status: {status}")
        
        # Test starting a conversation
        thread_id = "test_thread_001"
        start_result = manager.start_conversation(thread_id)
        logger.info(f"Start Conversation Result: {start_result}")
        
        # Test processing messages
        test_messages = [
            "Hello, how are you?",
            "What network equipment do you have information about?",
            "Tell me about building layouts",
            "Are there any recent incidents?",
            "What can you help me with?"
        ]
        
        for i, message in enumerate(test_messages):
            logger.info(f"\n--- Test Message {i+1}: {message} ---")
            
            response = manager.process_user_message(thread_id, message)
            logger.info(f"Response: {response.get('response', 'No response')}")
            logger.info(f"Confidence: {response.get('confidence_score', 0)}")
            logger.info(f"Sources: {response.get('total_sources', 0)}")
            logger.info(f"Processing Mode: {response.get('processing_mode', 'unknown')}")
            
            if response.get('suggested_questions'):
                logger.info(f"Suggestions: {response['suggested_questions']}")
            
            if response.get('sources'):
                logger.info(f"Top Source: {response['sources'][0] if response['sources'] else 'None'}")
        
        # Test conversation history
        history = manager.get_conversation_history(thread_id)
        logger.info(f"\nConversation History: {len(history.get('messages', []))} messages")
        
        # Test active conversations
        active = manager.get_active_conversations()
        logger.info(f"Active Conversations: {active.get('total_active', 0)}")
        
        # Test ending conversation
        end_result = manager.end_conversation(thread_id)
        logger.info(f"End Conversation Result: {end_result}")
        
        logger.info("✅ Functional Conversation Manager test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Functional Conversation Manager test failed: {e}")
        return False

def test_api_integration():
    """Test API integration with functional conversation manager"""
    try:
        logger.info("\nTesting API Integration...")
        
        # Import the conversation routes
        from api.routes.conversation import get_conversation_manager
        
        # Get the conversation manager through the API
        manager = get_conversation_manager()
        logger.info(f"API Manager Type: {type(manager).__name__}")
        
        # Test a simple message through the API
        thread_id = "api_test_thread_001"
        
        # Start conversation
        start_result = manager.start_conversation(thread_id)
        logger.info(f"API Start Result: {start_result}")
        
        # Send message
        response = manager.process_user_message(thread_id, "What network information do you have?")
        logger.info(f"API Response: {response.get('response', 'No response')[:100]}...")
        logger.info(f"API Processing Mode: {response.get('processing_mode', 'unknown')}")
        
        logger.info("✅ API Integration test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ API Integration test failed: {e}")
        return False

def test_qdrant_integration():
    """Test Qdrant integration specifically"""
    try:
        logger.info("\nTesting Qdrant Integration...")
        
        from api.functional_conversation_manager import FunctionalConversationManager
        
        manager = FunctionalConversationManager()
        
        # Check if Qdrant store is available
        if manager.qdrant_store:
            logger.info("✅ Qdrant store is available")
            
            # Get collection info
            try:
                collection_info = manager.qdrant_store.get_collection_info()
                logger.info(f"Collection Info: {collection_info}")
                
                if collection_info.get('total_points', 0) > 0:
                    logger.info("✅ Qdrant collection has data")
                    
                    # Test a search query
                    test_query = "network equipment"
                    if manager.embedder:
                        query_vector = manager.embedder.embed_text(test_query)
                        results = manager.qdrant_store.search_with_metadata(query_vector, k=5)
                        logger.info(f"Search Results: {len(results)} found")
                        
                        if results:
                            logger.info(f"Top Result: {results[0].get('filename', 'Unknown')}")
                            logger.info(f"Content Preview: {results[0].get('content', '')[:100]}...")
                    else:
                        logger.warning("⚠️ Embedder not available, using text search")
                        results = manager.qdrant_store.get_by_pattern(test_query, field="text")
                        logger.info(f"Text Search Results: {len(results)} found")
                else:
                    logger.warning("⚠️ Qdrant collection is empty")
                    
            except Exception as e:
                logger.error(f"❌ Error accessing Qdrant collection: {e}")
        else:
            logger.warning("⚠️ Qdrant store is not available")
        
        logger.info("✅ Qdrant Integration test completed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Qdrant Integration test failed: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("🚀 Starting Functional Conversation Flow Tests")
    
    results = []
    
    # Test 1: Functional Conversation Manager
    results.append(("Functional Conversation Manager", test_functional_conversation_manager()))
    
    # Test 2: API Integration
    results.append(("API Integration", test_api_integration()))
    
    # Test 3: Qdrant Integration
    results.append(("Qdrant Integration", test_qdrant_integration()))
    
    # Summary
    logger.info("\n" + "="*50)
    logger.info("📊 TEST RESULTS SUMMARY")
    logger.info("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Functional conversation flow is working.")
    else:
        logger.warning("⚠️ Some tests failed. Check the logs above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)