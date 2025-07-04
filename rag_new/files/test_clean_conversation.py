#!/usr/bin/env python3
"""
Test Clean Conversation Responses
Verify that the conversation system generates clean, formatted responses
"""
import requests
import json
import time

def test_clean_conversation_responses():
    """Test the conversation system for clean responses"""
    
    api_url = "http://localhost:8000"
    
    print("🧪 TESTING CLEAN CONVERSATION RESPONSES")
    print("=" * 50)
    
    # Test 1: Start conversation
    print("\n1. Starting conversation...")
    
    try:
        response = requests.post(f"{api_url}/api/conversation/start", json={})
        if response.status_code == 200:
            data = response.json()
            thread_id = data.get("thread_id")
            print(f"✅ Conversation started: {thread_id}")
            print(f"   Initial response: {data.get('response', '')[:100]}...")
        else:
            print(f"❌ Failed to start conversation: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error starting conversation: {e}")
        return
    
    # Test 2: Send assignment query (should get clean table format)
    print("\n2. Testing assignment query...")
    
    test_queries = [
        "which is assigned to whom?",
        "show me incident assignments",
        "who is handling what incidents?",
        "what are the current incident assignments?"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n   Test Query {i}: {query}")
        
        try:
            response = requests.post(
                f"{api_url}/api/conversation/message",
                json={
                    "message": query,
                    "thread_id": thread_id
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                response_text = data.get("response", "")
                sources = data.get("sources", [])
                
                print(f"   ✅ Response received ({len(response_text)} chars)")
                print(f"   📚 Sources: {len(sources)}")
                
                # Check response quality
                print(f"\n   📋 RESPONSE PREVIEW:")
                print(f"   {'-' * 40}")
                print(f"   {response_text[:400]}...")
                print(f"   {'-' * 40}")
                
                # Check for clean formatting
                has_table = "|" in response_text and "---" in response_text
                has_bullet_points = "•" in response_text or "-" in response_text
                has_raw_metadata = "Source 1" in response_text or "relevance:" in response_text
                has_technical_snippets = "metadata" in response_text.lower() or "score:" in response_text
                
                print(f"\n   📊 RESPONSE ANALYSIS:")
                print(f"   ✅ Has table format: {has_table}")
                print(f"   ✅ Has bullet points: {has_bullet_points}")
                print(f"   ❌ Contains raw metadata: {has_raw_metadata}")
                print(f"   ❌ Contains technical snippets: {has_technical_snippets}")
                
                # Check sources format
                if sources:
                    print(f"\n   📚 SOURCE ANALYSIS:")
                    for j, source in enumerate(sources[:2], 1):
                        print(f"   Source {j}:")
                        print(f"      Title: {source.get('title', 'N/A')}")
                        print(f"      Type: {source.get('type', 'N/A')}")
                        print(f"      Relevance: {source.get('relevance', 'N/A')}")
                        # Check if source has content snippets (should not)
                        if 'content' in source:
                            print(f"      ❌ WARNING: Source contains content snippets!")
                        else:
                            print(f"      ✅ Clean source metadata only")
                
                print()
                
                # Rate the response quality
                is_clean = not has_raw_metadata and not has_technical_snippets
                is_formatted = has_table or has_bullet_points
                
                if is_clean and is_formatted:
                    print(f"   🌟 RESPONSE QUALITY: EXCELLENT - Clean and formatted!")
                elif is_clean:
                    print(f"   ✅ RESPONSE QUALITY: GOOD - Clean but could use better formatting")
                elif is_formatted:
                    print(f"   ⚠️ RESPONSE QUALITY: FAIR - Formatted but contains raw metadata")
                else:
                    print(f"   ❌ RESPONSE QUALITY: POOR - Contains raw metadata and poor formatting")
                
            else:
                print(f"   ❌ Failed to get response: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error sending message: {e}")
        
        # Wait between requests
        time.sleep(2)
    
    # Test 3: Check conversation history
    print("\n3. Testing conversation history...")
    
    try:
        response = requests.get(f"{api_url}/api/conversation/history/{thread_id}")
        if response.status_code == 200:
            data = response.json()
            messages = data.get("messages", [])
            
            print(f"   ✅ History retrieved: {len(messages)} messages")
            
            # Check if assistant messages are clean
            assistant_messages = [msg for msg in messages if msg.get("type") == "assistant"]
            
            print(f"\n   📋 HISTORY ANALYSIS:")
            for i, msg in enumerate(assistant_messages[-2:], 1):  # Check last 2 assistant messages
                content = msg.get("content", "")
                has_raw_snippets = "Source 1" in content or "relevance:" in content
                
                print(f"   Message {i}: {'Clean' if not has_raw_snippets else 'Contains raw snippets'}")
                print(f"      Length: {len(content)} characters")
                print(f"      Preview: {content[:100]}...")
                
        else:
            print(f"   ❌ Failed to get history: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error getting history: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 CLEAN CONVERSATION TEST COMPLETED")
    
    print("\n💡 EXPECTED RESULTS:")
    print("   ✅ Responses should be clean and professionally formatted")
    print("   ✅ Tables should use | separators for structured data")
    print("   ✅ No raw source snippets or technical metadata in responses")
    print("   ✅ Sources should provide clean metadata only (title, type, relevance)")
    print("   ✅ Conversation history should contain clean responses only")

if __name__ == "__main__":
    test_clean_conversation_responses() 