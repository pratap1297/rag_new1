#!/usr/bin/env python3

import requests
import json

def test_query():
    """Test the query endpoint with a simple query"""
    
    # Test the query endpoint
    query_url = "http://localhost:8000/query"
    
    # Simple query about incidents
    query_data = {
        "query": "What incidents are there?",
        "max_results": 3
    }
    
    try:
        print(f"🔍 Testing query endpoint...")
        print(f"Query: {query_data['query']}")
        
        response = requests.post(query_url, json=query_data, timeout=30)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Query successful!")
            print(f"Success: {result.get('success')}")
            
            if result.get('success') and 'data' in result:
                data = result['data']
                print(f"Response: {data.get('response', '')[:200]}...")
                print(f"Sources found: {len(data.get('sources', []))}")
                
                # Show sources
                for i, source in enumerate(data.get('sources', [])[:3]):
                    print(f"  Source {i+1}: {source.get('text', '')[:100]}...")
            else:
                print(f"❌ Query failed: {result}")
        else:
            print(f"❌ Query failed with status {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_query() 