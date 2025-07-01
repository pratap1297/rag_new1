#!/usr/bin/env python3

import requests
import json

def test_servicenow_query():
    """Test querying ServiceNow incidents to verify complete information"""
    
    # Test the query endpoint
    query_url = "http://localhost:8000/query"
    
    # Query about specific incident details
    test_queries = [
        "Tell me about incident INC030001",
        "What is the resolution for the high priority network incident?",
        "Show me details about the incidents including description and resolution",
        "What incidents are marked as resolved?"
    ]
    
    for query_text in test_queries:
        print(f"\n🔍 Testing query: '{query_text}'")
        print("=" * 60)
        
        query_data = {
            "query": query_text,
            "max_results": 5
        }
        
        try:
            response = requests.post(query_url, json=query_data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('success') and 'data' in result:
                    data = result['data']
                    print(f"✅ Response:")
                    print(f"{data.get('response', '')}")
                    
                    print(f"\n📋 Sources ({len(data.get('sources', []))} found):")
                    for i, source in enumerate(data.get('sources', [])[:3]):
                        text = source.get('text', '')
                        print(f"\n  Source {i+1} (Score: {source.get('score', 0):.3f}):")
                        
                        # Try to parse as JSON to check if it's a complete incident
                        try:
                            if text.strip().startswith('{'):
                                json_data = json.loads(text)
                                if 'incidents' in json_data:
                                    incidents = json_data['incidents']
                                    print(f"    📦 Complete JSON with {len(incidents)} incident(s)")
                                    for incident in incidents[:1]:  # Show first incident
                                        print(f"    🎫 Incident: {incident.get('number', 'N/A')}")
                                        print(f"       Priority: {incident.get('priority', 'N/A')}")
                                        print(f"       Description: {incident.get('description', 'N/A')[:100]}...")
                                        print(f"       Resolution: {incident.get('resolution', 'N/A')[:100]}...")
                                else:
                                    print(f"    📝 JSON object: {list(json_data.keys())}")
                            else:
                                print(f"    📄 Text fragment: {text[:200]}...")
                        except json.JSONDecodeError:
                            print(f"    📄 Text content: {text[:200]}...")
                
                else:
                    print(f"❌ Query failed: {result}")
            else:
                print(f"❌ Query failed with status {response.status_code}")
                print(f"Response: {response.text[:500]}...")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_servicenow_query() 