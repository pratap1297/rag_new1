#!/usr/bin/env python3
"""
Test Enhanced Conversation System
Comprehensive test to verify our enhanced conversation system with context awareness
"""
import requests
import json
import time

def test_enhanced_conversation():
    """Test the enhanced conversation system with better context awareness"""
    
    print("🧪 TESTING ENHANCED CONVERSATION SYSTEM")
    print("=" * 80)
    
    # Wait for server to start
    print("⏳ Waiting for server to start...")
    time.sleep(15)
    
    # Test conversation setup
    thread_id = "enhanced_test_thread"
    base_url = "http://localhost:8000"
    api_endpoint = f"{base_url}/api/conversation/message"
    
    print(f"\\n📡 API Endpoint: {api_endpoint}")
    print(f"🧵 Thread ID: {thread_id}")
    print("\\n" + "=" * 80)
    
    # Test 1: Document Statistics Query
    print("\\n1️⃣ TEST 1: Document Statistics Query")
    print("-" * 50)
    
    stats_payload = {
        "message": "how many incidents are in system",
        "thread_id": thread_id
    }
    
    print(f"🔍 Query: '{stats_payload['message']}'")
    
    try:
        print("⏳ Sending request...")
        response = requests.post(api_endpoint, json=stats_payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            stats_response = result.get('response', '')
            print(f"✅ Status: Success")
            print(f"📊 Response Length: {len(stats_response)} characters")
            print(f"🎯 Response Preview: {stats_response[:200]}...")
            print(f"🧵 Thread ID: {result.get('thread_id', 'N/A')}")
            print(f"🔄 Turn Count: {result.get('turn_count', 'N/A')}")
            print(f"📍 Phase: {result.get('current_phase', 'N/A')}")
            print(f"🎯 Confidence: {result.get('confidence_score', 'N/A')}")
            
            # Check if we got the expected document statistics
            if "incident" in stats_response.lower() and ("5" in stats_response or "total" in stats_response.lower()):
                print("✅ PASS: Got incident statistics in response")
                first_response = stats_response
            else:
                print("❌ FAIL: Response doesn't contain incident statistics")
                first_response = stats_response
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"📝 Error: {response.text}")
            return
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    print("\\n" + "=" * 80)
    
    # Test 2: Follow-up Context Question (This is the key test!)
    print("\\n2️⃣ TEST 2: Follow-up Context Question")
    print("-" * 50)
    
    # Wait a moment for the conversation state to be saved
    print("⏳ Waiting for conversation state to be saved...")
    time.sleep(3)
    
    followup_payload = {
        "message": "which are these?",
        "thread_id": thread_id
    }
    
    print(f"🔍 Follow-up Query: '{followup_payload['message']}'")
    print("🎯 Expected: Should use conversation context to understand 'these' refers to the incidents")
    
    try:
        print("⏳ Sending follow-up request...")
        response = requests.post(api_endpoint, json=followup_payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            followup_response = result.get('response', '')
            print(f"✅ Status: Success")
            print(f"📊 Response Length: {len(followup_response)} characters")
            print(f"🎯 Full Response: {followup_response}")
            print(f"🧵 Thread ID: {result.get('thread_id', 'N/A')}")
            print(f"🔄 Turn Count: {result.get('turn_count', 'N/A')}")
            print(f"📍 Phase: {result.get('current_phase', 'N/A')}")
            print(f"🎯 Confidence: {result.get('confidence_score', 'N/A')}")
            
            # Enhanced analysis of the response
            print("\\n🔬 ENHANCED ANALYSIS:")
            print("-" * 30)
            
            # Check if it's contextual (not generic)
            generic_indicators = [
                "I don't have specific information",
                "Could you provide more details",
                "I'd be happy to help you in other ways",
                "What specifically you'd like to know"
            ]
            
            is_generic = any(indicator.lower() in followup_response.lower() for indicator in generic_indicators)
            print(f"❓ Generic Response: {'❌ YES' if is_generic else '✅ NO'}")
            
            # Check if it references context
            context_indicators = [
                "these",
                "incidents",
                "5",
                "mentioned",
                "earlier",
                "previous",
                "above",
                "refers to"
            ]
            
            has_context = any(indicator.lower() in followup_response.lower() for indicator in context_indicators)
            print(f"🔗 Uses Context: {'✅ YES' if has_context else '❌ NO'}")
            
            # Check if it's concise (not overly verbose)
            is_concise = len(followup_response) < 500
            print(f"📏 Concise Response: {'✅ YES' if is_concise else '❌ NO'} ({len(followup_response)} chars)")
            
            # Check for specific incident references
            has_incident_details = any(term in followup_response.lower() for term in ["incident", "inc", "ticket"])
            print(f"🎯 References Incidents: {'✅ YES' if has_incident_details else '❌ NO'}")
            
            # Overall assessment
            print("\\n🏆 OVERALL ASSESSMENT:")
            print("-" * 25)
            
            if not is_generic and has_context and is_concise:
                print("🌟 EXCELLENT: Context awareness is working perfectly!")
                print("✅ The system successfully understood 'these' refers to the incidents")
                print("✅ Response is contextual, concise, and relevant")
            elif not is_generic and has_context:
                print("✅ GOOD: Context awareness is working")
                print("⚠️  Response could be more concise")
            elif not is_generic:
                print("⚠️  PARTIAL: Non-generic response but limited context usage")
            else:
                print("❌ POOR: Still giving generic responses")
                
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"📝 Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\\n" + "=" * 80)
    
    # Test 3: Additional Context Test
    print("\\n3️⃣ TEST 3: Additional Context Test")
    print("-" * 50)
    
    time.sleep(2)
    
    context_payload = {
        "message": "tell me more about them",
        "thread_id": thread_id
    }
    
    print(f"🔍 Query: '{context_payload['message']}'")
    print("🎯 Expected: Should understand 'them' refers to the incidents from conversation")
    
    try:
        print("⏳ Sending request...")
        response = requests.post(api_endpoint, json=context_payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            context_response = result.get('response', '')
            print(f"✅ Status: Success")
            print(f"📊 Response Length: {len(context_response)} characters")
            print(f"🎯 Response: {context_response}")
            
            # Quick analysis
            is_contextual = "incident" in context_response.lower() or "these" in context_response.lower() or "them" in context_response.lower()
            print(f"🔗 Contextual: {'✅ YES' if is_contextual else '❌ NO'}")
            
        else:
            print(f"❌ Request failed with status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\\n" + "=" * 80)
    print("🎯 ENHANCED CONVERSATION TEST COMPLETED")
    print("=" * 80)

def main():
    """Main function"""
    test_enhanced_conversation()

if __name__ == "__main__":
    main() 