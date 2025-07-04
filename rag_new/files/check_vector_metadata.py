#!/usr/bin/env python3

import requests
import json

def check_stored_metadata():
    """Check what metadata is actually stored in the vector database"""
    
    print("🔍 Checking Vector Database Metadata")
    print("=" * 50)
    
    try:
        # Get recent vectors
        response = requests.get(
            'http://localhost:8000/vectors?include_content=true&page_size=10',
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and 'data' in data:
                vectors = data['data'].get('vectors', [])
                
                print(f"📊 Found {len(vectors)} vectors")
                
                # Look for Excel-related vectors
                excel_vectors = []
                for vector in vectors:
                    metadata = vector.get('metadata', {})
                    content = vector.get('content', '')
                    
                    # Check if this is Excel-related
                    if ('xlsx' in content.lower() or 
                        'excel' in content.lower() or 
                        'WebUI_Test' in str(metadata) or
                        'WebUI_Test' in content or
                        metadata.get('source_type') == 'excel_sheet'):
                        excel_vectors.append(vector)
                
                if excel_vectors:
                    print(f"\n📋 Found {len(excel_vectors)} Excel-related vectors:")
                    for i, vector in enumerate(excel_vectors):
                        print(f"\n   Vector {i+1}:")
                        print(f"      ID: {vector.get('id', 'Unknown')}")
                        
                        metadata = vector.get('metadata', {})
                        print(f"      Metadata keys: {list(metadata.keys())}")
                        
                        # Check specific source metadata
                        upload_source = metadata.get('upload_source', 'NOT_FOUND')
                        original_filename = metadata.get('original_filename', 'NOT_FOUND')
                        content_type = metadata.get('content_type', 'NOT_FOUND')
                        source_type = metadata.get('source_type', 'NOT_FOUND')
                        
                        print(f"      upload_source: {upload_source}")
                        print(f"      original_filename: {original_filename}")
                        print(f"      content_type: {content_type}")
                        print(f"      source_type: {source_type}")
                        
                        content = vector.get('content', '')
                        print(f"      Content preview: {content[:100]}...")
                        
                        # Check if this vector has correct metadata
                        if upload_source == 'web_upload':
                            print(f"      ✅ Has correct upload_source!")
                        else:
                            print(f"      ❌ Missing or incorrect upload_source")
                else:
                    print(f"\n❌ No Excel-related vectors found")
                    
                    # Show all vectors for debugging
                    print(f"\n   All vectors:")
                    for i, vector in enumerate(vectors[:5]):
                        metadata = vector.get('metadata', {})
                        print(f"      {i+1}. ID: {vector.get('id', 'Unknown')}")
                        print(f"         source_type: {metadata.get('source_type', 'NOT_FOUND')}")
                        print(f"         upload_source: {metadata.get('upload_source', 'NOT_FOUND')}")
                        print(f"         Content: {vector.get('content', '')[:50]}...")
            else:
                print(f"❌ API response error: {data}")
        else:
            print(f"❌ API request failed: {response.status_code}")
            print(f"   Response: {response.text}")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_stored_metadata() 