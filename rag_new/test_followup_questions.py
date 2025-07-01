#!/usr/bin/env python3
"""
Test Follow-up Question Handling
Verify that simple follow-up questions get concise, direct answers
"""
import requests
import time

def test_followup_questions():
    """Test the conversation system for proper follow-up handling"""
    
    api_url = "http://localhost:8000"
    
    print("🧪 TESTING FOLLOW-UP QUESTION HANDLING")
    print("=" * 50)
    
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
    
    # Test 2: First question about document statistics
    print("\n2. Asking about document statistics...")
    
    try:
        response = requests.post(
            f"{api_url}/api/conversation/message",
            json={
                "message": "Total documents: 5",
                "thread_id": thread_id
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            response_text = data.get("response", "")
            
            print(f"✅ Initial response received ({len(response_text)} chars)")
            print(f"📋 Response preview: {response_text[:200]}...")
        else:
            print(f"❌ Failed to get response: {response.status_code}")
            return
            
    except Exception as e:
        print(f"❌ Error sending message: {e}")
        return
    
    # Wait a moment
    time.sleep(2)
    
    # Test 3: Follow-up question - "which are these?"
    print("\n3. Testing simple follow-up question...")
    
    test_followups = [
        "which are these?",
        "what are these?", 
        "list them",
        "show them"
    ]
    
    for i, followup in enumerate(test_followups, 1):
        print(f"\n   Follow-up {i}: '{followup}'")
        
        try:
            response = requests.post(
                f"{api_url}/api/conversation/message",
                json={
                    "message": followup,
                    "thread_id": thread_id
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                response_text = data.get("response", "")
                
                print(f"   ✅ Response received ({len(response_text)} chars)")
                
                # Check response characteristics
                is_concise = len(response_text) < 500  # Should be concise
                has_bullets = "•" in response_text or "-" in response_text
                has_verbose_analysis = "analysis" in response_text.lower() or "comprehensive" in response_text.lower()
                has_source_references = "source" in response_text.lower() and "relevance" in response_text.lower()
                
                print(f"\n   📊 RESPONSE ANALYSIS:")
                print(f"   ✅ Concise (< 500 chars): {is_concise}")
                print(f"   ✅ Has bullet points/list: {has_bullets}")
                print(f"   ❌ Contains verbose analysis: {has_verbose_analysis}")
                print(f"   ❌ Contains source references: {has_source_references}")
                
                print(f"\n   📋 RESPONSE:")
                print(f"   {'-' * 40}")
                print(f"   {response_text}")
                print(f"   {'-' * 40}")
                
                # Rate the response
                if is_concise and has_bullets and not has_verbose_analysis:
                    print(f"   🌟 QUALITY: EXCELLENT - Concise and direct!")
                elif is_concise and not has_verbose_analysis:
                    print(f"   ✅ QUALITY: GOOD - Concise but could use better formatting")
                elif not has_verbose_analysis:
                    print(f"   ⚠️ QUALITY: FAIR - Direct but could be more concise")
                else:
                    print(f"   ❌ QUALITY: POOR - Too verbose for simple follow-up")
                
            else:
                print(f"   ❌ Failed to get response: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error sending message: {e}")
        
        # Wait between requests
        time.sleep(3)
    
    print("\n" + "=" * 50)
    print("🎯 FOLLOW-UP QUESTION TEST COMPLETED")
    
    print("\n💡 EXPECTED RESULTS:")
    print("   ✅ Follow-up questions should get concise, direct answers")
    print("   ✅ Responses should be < 500 characters for simple follow-ups")
    print("   ✅ Should use bullet points or numbered lists")
    print("   ✅ No verbose analysis or source referencing")
    print("   ✅ Focus on answering 'which are these?' directly")

if __name__ == "__main__":
    test_followup_questions() 