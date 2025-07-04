#!/usr/bin/env python3
"""
Test JSON Content Retrieval
Check how the ServiceNow incidents JSON is stored and retrieved
"""

import requests
import json

def test_json_content_retrieval():
    """Test how JSON content is stored and retrieved"""
    print("🔍 Testing JSON Content Retrieval")
    print("=" * 40)
    
    api_url = "http://localhost:8000"
    
    # 1. Test query for incidents
    print("📋 Testing incident query...")
    try:
        query_data = {
            'query': 'incidents ServiceNow details',
            'max_results': 10,
            'include_metadata': True
        }
        
        response = requests.post(f"{api_url}/query", json=query_data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            if result.get('success') and 'data' in result:
                data = result['data']
                sources = data.get('sources', [])
                print(f"✅ Query returned {len(sources)} sources")
                
                # Examine each source
                for i, source in enumerate(sources, 1):
                    print(f"\n📄 Source {i}:")
                    print(f"   Doc ID: {source.get('doc_id', 'N/A')}")
                    print(f"   Score: {source.get('score', 0):.3f}")
                    
                    # Show content length and preview
                    content = source.get('text', source.get('content', ''))
                    print(f"   Content length: {len(content)} characters")
                    print(f"   Content preview: {content[:200]}...")
                    
                    # Check if it's JSON content
                    try:
                        if content.strip().startswith('{') or content.strip().startswith('['):
                            print(f"   📊 Detected JSON content")
                            # Try to parse it
                            json_data = json.loads(content)
                            if isinstance(json_data, dict) and 'incidents' in json_data:
                                incidents = json_data['incidents']
                                print(f"   📋 Contains {len(incidents)} incidents")
                            elif isinstance(json_data, list):
                                print(f"   📋 Contains {len(json_data)} items")
                        else:
                            print(f"   📝 Text content (possibly chunked)")
                    except json.JSONDecodeError:
                        print(f"   📝 Text content (not valid JSON)")
            else:
                print(f"❌ Query failed: {result.get('error', 'Unknown error')}")
        else:
            print(f"❌ Query failed: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Query error: {e}")
    
    # 2. Check all vectors for JSON content
    print(f"\n🔍 Checking all vectors for JSON content...")
    try:
        response = requests.get(f"{api_url}/manage/vectors?limit=20", timeout=15)
        if response.status_code == 200:
            vectors = response.json()
            print(f"📊 Found {len(vectors)} total vectors")
            
            json_vectors = []
            for vector in vectors:
                metadata = vector.get('metadata', {})
                content = metadata.get('text', metadata.get('content', ''))
                doc_path = metadata.get('doc_path', '')
                
                # Check if this is JSON-related
                if ('json' in doc_path.lower() or 
                    'servicenow' in content.lower() or 
                    'incidents' in content.lower() or
                    content.strip().startswith('{')):
                    json_vectors.append({
                        'vector_id': vector.get('vector_id'),
                        'doc_path': doc_path,
                        'content_length': len(content),
                        'content_preview': content[:150],
                        'is_json': content.strip().startswith('{') or content.strip().startswith('[')
                    })
            
            print(f"📋 Found {len(json_vectors)} JSON-related vectors:")
            for i, jv in enumerate(json_vectors, 1):
                print(f"\n   Vector {i}:")
                print(f"      ID: {jv['vector_id']}")
                print(f"      Path: {jv['doc_path']}")
                print(f"      Length: {jv['content_length']} chars")
                print(f"      Is JSON: {jv['is_json']}")
                print(f"      Preview: {jv['content_preview']}...")
                
                # If it's full JSON, try to count incidents
                if jv['is_json'] and jv['content_length'] > 100:
                    try:
                        full_content = None
                        # Get full content from vector details
                        detail_response = requests.get(f"{api_url}/vectors/{jv['vector_id']}?include_embedding=false", timeout=10)
                        if detail_response.status_code == 200:
                            detail_data = detail_response.json()
                            if detail_data.get('success'):
                                full_content = detail_data['data'].get('content', '')
                        
                        if full_content:
                            json_data = json.loads(full_content)
                            if isinstance(json_data, dict) and 'incidents' in json_data:
                                incidents = json_data['incidents']
                                print(f"      📋 Contains {len(incidents)} incidents")
                                
                                # Show incident summaries
                                for idx, incident in enumerate(incidents[:3], 1):
                                    print(f"         {idx}. {incident.get('incident_number', 'N/A')}: {incident.get('short_description', 'N/A')[:50]}...")
                                if len(incidents) > 3:
                                    print(f"         ... and {len(incidents) - 3} more incidents")
                    except Exception as parse_error:
                        print(f"      ❌ JSON parse error: {parse_error}")
            
        else:
            print(f"❌ Failed to get vectors: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Vector check error: {e}")
    
    # 3. Provide recommendations
    print(f"\n💡 **Recommendations:**")
    print(f"1. **Check chunking strategy**: JSON files should ideally be stored as single chunks")
    print(f"2. **Verify content completeness**: Ensure all incident data is in the chunks")
    print(f"3. **Test larger max_results**: Try asking for more results in conversations")
    print(f"4. **Re-upload if needed**: If content is incomplete, re-upload the JSON file")

if __name__ == "__main__":
    test_json_content_retrieval() 