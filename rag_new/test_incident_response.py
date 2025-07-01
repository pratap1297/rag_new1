#!/usr/bin/env python3
"""
Test Incident Response
Quick test to check the current API response for incident-related questions
"""
import requests
import json

def test_incident_response():
    """Test the current API response for incident questions"""
    
    print("🧪 TESTING INCIDENT RESPONSE")
    print("=" * 60)
    
    # Test conversation setup
    thread_id = "test_incident_thread"
    base_url = "http://localhost:8000"
    
    # First, ask about document statistics to establish context
    print("\n1️⃣ Setting up context with document statistics...")
    
    stats_payload = {
        "message": "how many incidents are in system",
        "thread_id": thread_id
    }
    
    try:
        response = requests.post(f"{base_url}/conversation/message", json=stats_payload, timeout=30)
        if response.status_code == 200:
            stats_result = response.json()
            print(f"📊 Stats Response: {stats_result['response'][:200]}...")
        else:
            print(f"❌ Stats request failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error in stats request: {e}")
        return
    
    # Now ask the follow-up question
    print("\n2️⃣ Testing follow-up question...")
    
    followup_payload = {
        "message": "what are these?",
        "thread_id": thread_id
    }
    
    try:
        response = requests.post(f"{base_url}/conversation/message", json=followup_payload, timeout=30)
        if response.status_code == 200:
            followup_result = response.json()
            print(f"💭 Follow-up Response:")
            print(f"   {followup_result['response']}")
            print(f"\n📏 Response Length: {len(followup_result['response'])} characters")
            
            # Check if it's contextual
            response_text = followup_result['response'].lower()
            is_contextual = any(word in response_text for word in ['incident', 'these', 'they are', '5', 'five'])
            print(f"🎯 Is Contextual: {is_contextual}")
            
            # Check if it's concise
            is_concise = len(followup_result['response']) < 500
            print(f"✂️ Is Concise: {is_concise}")
            
            # Check for generic phrases
            has_generic = any(phrase in response_text for phrase in [
                "i don't have", "more details", "more information", "happy to help"
            ])
            print(f"🚫 Has Generic Content: {has_generic}")
            
        else:
            print(f"❌ Follow-up request failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error in follow-up request: {e}")

def main():
    """Main function"""
    test_incident_response()

if __name__ == "__main__":
    main() 