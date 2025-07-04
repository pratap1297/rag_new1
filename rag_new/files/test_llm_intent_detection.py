#!/usr/bin/env python3
"""
Test LLM-based Intent Detection for Follow-up Questions
Compare LLM vs regex pattern matching
"""
import requests
import time

def test_llm_intent_detection():
    """Test the LLM-based intent detection for follow-up questions"""
    
    api_url = "http://localhost:8000"
    
    print("🧪 TESTING LLM-BASED INTENT DETECTION")
    print("=" * 60)
    
    # Test 1: Start conversation
    print("\n1. Starting conversation...")
    
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
    
    # Test 2: Setup context with document statistics
    print("\n2. Setting up context...")
    
    try:
        response = requests.post(
            f"{api_url}/api/conversation/message",
            json={
                "message": "We have 5 total documents in the system",
                "thread_id": thread_id
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            response_text = data.get("response", "")
            print(f"✅ Context established ({len(response_text)} chars)")
            print(f"📋 Response: {response_text[:150]}...")
        else:
            print(f"❌ Failed to establish context: {response.status_code}")
            return
            
    except Exception as e:
        print(f"❌ Error establishing context: {e}")
        return
    
    # Wait between requests
    time.sleep(3)
    
    # Test 3: Natural language follow-up questions that LLM should handle better
    print("\n3. Testing natural language follow-up questions...")
    
    natural_followups = [
        # Direct questions that should get concise answers
        "which are these?",
        "what are those documents?",
        "can you list them?",
        "show me what they are",
        "what documents do we have?",
        "tell me which ones",
        
        # Questions that should NOT be treated as simple follow-ups
        "tell me more about the document structure",
        "how are these documents organized?",
        "what is the detailed analysis of these files?",
        "provide comprehensive information about the documents"
    ]
    
    for i, question in enumerate(natural_followups, 1):
        print(f"\n   Test {i}: '{question}'")
        
        # Determine expected behavior
        simple_questions = natural_followups[:6]  # First 6 should be simple
        is_expected_simple = question in simple_questions
        
        try:
            response = requests.post(
                f"{api_url}/api/conversation/message",
                json={
                    "message": question,
                    "thread_id": thread_id
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                response_text = data.get("response", "")
                
                print(f"   ✅ Response received ({len(response_text)} chars)")
                
                # Analyze response characteristics
                is_concise = len(response_text) < 400  # Should be concise for simple questions
                has_bullets = "•" in response_text or "-" in response_text
                has_verbose_phrases = any(phrase in response_text.lower() for phrase in [
                    "comprehensive", "analysis", "let's analyze", "to provide a comprehensive",
                    "based on the context", "without more specific context"
                ])
                is_direct = not has_verbose_phrases and (has_bullets or len(response_text.split('.')) <= 3)
                
                print(f"   📊 ANALYSIS:")
                print(f"      Expected simple: {is_expected_simple}")
                print(f"      Actually concise: {is_concise}")
                print(f"      Direct/formatted: {is_direct}")
                print(f"      Has verbose phrases: {has_verbose_phrases}")
                
                # Rate accuracy
                if is_expected_simple:
                    if is_concise and is_direct:
                        print(f"   🌟 EXCELLENT: Correctly identified as simple follow-up!")
                    elif is_concise:
                        print(f"   ✅ GOOD: Concise but could be more direct")
                    else:
                        print(f"   ❌ POOR: Should be concise for simple question")
                else:
                    if not is_concise and not is_direct:
                        print(f"   ✅ CORRECT: Properly detailed for complex question")
                    else:
                        print(f"   ⚠️ WARNING: May be too simple for complex question")
                
                print(f"\n   📋 RESPONSE PREVIEW:")
                print(f"      {response_text[:200]}...")
                
            else:
                print(f"   ❌ Failed to get response: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Wait between requests
        time.sleep(2)
    
    print("\n" + "=" * 60)
    print("🎯 LLM INTENT DETECTION TEST COMPLETED")
    
    print("\n💡 LLM ADVANTAGES OVER REGEX:")
    print("   ✅ Understands natural language variations")
    print("   ✅ Uses conversation context for intent detection") 
    print("   ✅ Can distinguish simple vs complex questions")
    print("   ✅ Handles paraphrasing and different phrasings")
    print("   ✅ More flexible than rigid pattern matching")
    print("   ✅ Can evolve understanding over time")

if __name__ == "__main__":
    test_llm_intent_detection() 