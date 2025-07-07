#!/usr/bin/env python3
"""
Test script to verify API fixes after server restart
"""
import requests
import json
import time

def test_api_endpoints():
    """Test various API endpoints to verify fixes"""
    
    base_url = "http://localhost:8000"
    
    print("🧪 Testing API endpoints after fixes...")
    
    # Test 1: Stats endpoint (should not have faiss_store error)
    print("\n1. Testing /stats endpoint...")
    try:
        response = requests.get(f"{base_url}/stats", timeout=10)
        if response.status_code == 200:
            print("✅ Stats endpoint working")
            data = response.json()
            if 'vector_store' in str(data):
                print("✅ Using vector_store (not faiss_store)")
            else:
                print("⚠️ No vector_store reference found in stats")
        else:
            print(f"❌ Stats endpoint failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Stats endpoint error: {e}")
    
    # Test 2: Conversation health endpoint
    print("\n2. Testing /api/conversation/health endpoint...")
    try:
        response = requests.get(f"{base_url}/api/conversation/health", timeout=10)
        if response.status_code == 200:
            print("✅ Conversation health endpoint working")
            data = response.json()
            print(f"   Status: {data.get('status', 'unknown')}")
        else:
            print(f"❌ Conversation health failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Conversation health error: {e}")
    
    # Test 3: Conversation threads endpoint
    print("\n3. Testing /api/conversation/threads endpoint...")
    try:
        response = requests.get(f"{base_url}/api/conversation/threads", timeout=10)
        if response.status_code == 200:
            print("✅ Conversation threads endpoint working")
            data = response.json()
            print(f"   Threads count: {data.get('count', 0)}")
        else:
            print(f"❌ Conversation threads failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Conversation threads error: {e}")
    
    # Test 4: Conversation start endpoint
    print("\n4. Testing /api/conversation/start endpoint...")
    try:
        response = requests.post(f"{base_url}/api/conversation/start", json={}, timeout=10)
        if response.status_code == 200:
            print("✅ Conversation start endpoint working")
            data = response.json()
            thread_id = data.get('thread_id')
            print(f"   Thread ID: {thread_id}")
            
            # Test 5: Send message to the conversation
            if thread_id:
                print("\n5. Testing /api/conversation/message endpoint...")
                try:
                    message_response = requests.post(
                        f"{base_url}/api/conversation/message",
                        json={"thread_id": thread_id, "message": "Hello, test message"},
                        timeout=30
                    )
                    if message_response.status_code == 200:
                        print("✅ Conversation message endpoint working")
                        msg_data = message_response.json()
                        print(f"   Response length: {len(msg_data.get('response', ''))}")
                    else:
                        print(f"❌ Conversation message failed: {message_response.status_code}")
                        print(f"   Response: {message_response.text}")
                except Exception as e:
                    print(f"❌ Conversation message error: {e}")
        else:
            print(f"❌ Conversation start failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Conversation start error: {e}")
    
    # Test 6: Health check
    print("\n6. Testing /health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Health endpoint working")
            data = response.json()
            print(f"   Status: {data.get('status', 'unknown')}")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
    
    print("\n🏁 API endpoint testing complete!")

if __name__ == "__main__":
    test_api_endpoints() 