#!/usr/bin/env python3
"""
Test Context Awareness for Follow-up Questions
Verify that follow-up questions get answered using conversation context
"""
import requests
import time

def test_context_awareness():
    """Test the conversation system's context awareness"""
    
    api_url = "http://localhost:8000"
    
    print("🧪 TESTING CONTEXT AWARENESS FOR FOLLOW-UP QUESTIONS")
    print("=" * 60)
    
    # Test 1: Start conversation
    print("\n1. Starting new conversation...")
    
    try:
        response = requests.post(f"{api_url}/api/conversation/start", json={})
        if response.status_code == 200:
            data = response.json()
            thread_id = data.get("thread_id")
            print(f"✅ Conversation started: {thread_id}")
        else:
            print(f"❌ Failed to start conversation: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error starting conversation: {e}")
        return
    
    # Test 2: Send a message about documents
    print("\n2. Setting up context with document information...")
    
    test_scenarios = [
        {
            "setup": "How many tickets in the system",
            "followup": "which are these?",
            "description": "Document count followed by identification"
        },
        {
            "setup": "We have 3 access points in Building A",
            "followup": "what are those?",
            "description": "Equipment count followed by identification"
        },
        {
            "setup": "There are 5 network incidents this week",
            "followup": "show them",
            "description": "Incident count followed by listing request"
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n🧪 SCENARIO {i}: {scenario['description']}")
        print("-" * 40)
        
        # Setup context
        print(f"   Setup: '{scenario['setup']}'")
        
        try:
            response = requests.post(
                f"{api_url}/api/conversation/message",
                json={
                    "message": scenario["setup"],
                    "thread_id": thread_id
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                setup_response = data.get("response", "")
                print(f"   ✅ Setup response ({len(setup_response)} chars)")
                print(f"   📋 Setup response: {setup_response[:150]}...")
            else:
                print(f"   ❌ Failed setup: {response.status_code}")
                continue
                
        except Exception as e:
            print(f"   ❌ Setup error: {e}")
            continue
        
        # Wait between messages
        time.sleep(2)
        
        # Follow-up question
        print(f"\n   Follow-up: '{scenario['followup']}'")
        
        try:
            response = requests.post(
                f"{api_url}/api/conversation/message",
                json={
                    "message": scenario["followup"],
                    "thread_id": thread_id
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                followup_response = data.get("response", "")
                
                print(f"   ✅ Follow-up response received ({len(followup_response)} chars)")
                
                # Analyze response quality
                is_contextual = not ("I don't have specific information" in followup_response)
                is_concise = len(followup_response) < 500
                has_generic_response = "Could you provide more details" in followup_response
                refers_to_context = any(word in followup_response.lower() for word in ['these', 'those', 'documents', 'tickets', 'incidents', 'access points'])
                
                print(f"\n   📊 RESPONSE ANALYSIS:")
                print(f"      Contextual (not generic): {is_contextual}")
                print(f"      Concise (< 500 chars): {is_concise}")
                print(f"      Avoids generic response: {not has_generic_response}")
                print(f"      References context: {refers_to_context}")
                
                # Rate the response
                if is_contextual and not has_generic_response:
                    if refers_to_context and is_concise:
                        print(f"   🌟 EXCELLENT: Context-aware and direct!")
                    elif refers_to_context:
                        print(f"   ✅ GOOD: Context-aware but could be more concise")
                    else:
                        print(f"   ✅ FAIR: Better than generic but could reference context more")
                else:
                    print(f"   ❌ POOR: Generic response, not using conversation context")
                
                print(f"\n   📋 ACTUAL RESPONSE:")
                print(f"   {'-' * 40}")
                print(f"   {followup_response}")
                print(f"   {'-' * 40}")
                
            else:
                print(f"   ❌ Failed follow-up: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Follow-up error: {e}")
        
        # Wait between scenarios
        time.sleep(3)
    
    print("\n" + "=" * 60)
    print("🎯 CONTEXT AWARENESS TEST COMPLETED")
    
    print("\n💡 EXPECTED IMPROVEMENTS:")
    print("   ✅ Follow-up questions should reference conversation context")
    print("   ✅ Should avoid generic 'I don't have information' responses")
    print("   ✅ Should identify what 'these', 'those', 'them' refers to")
    print("   ✅ Should be concise and direct based on context")
    print("   ✅ Should work even when search results are not available")

if __name__ == "__main__":
    test_context_awareness() 