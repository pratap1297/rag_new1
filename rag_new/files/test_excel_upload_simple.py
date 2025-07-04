#!/usr/bin/env python3

import requests
import json
import time

def test_existing_excel_upload():
    """Test uploading the existing Excel file that we know works"""
    
    print("🔍 Testing Existing Excel File Upload")
    print("=" * 50)
    
    excel_file_path = "document_generator/test_data/Facility_Managers_2024.xlsx"
    
    try:
        # Upload via /upload endpoint (simulating web UI)
        print(f"📤 Uploading existing Excel file: {excel_file_path}")
        
        with open(excel_file_path, 'rb') as f:
            files = {'file': ('Facility_Managers_2024_WebUI_Test.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            data = {
                'upload_source': 'web_upload',
                'original_path': 'Facility_Managers_2024_WebUI_Test.xlsx',
                'description': 'Test Excel file for source metadata verification'
            }
            
            response = requests.post(
                'http://localhost:8000/upload',
                files=files,
                data=data,
                timeout=60
            )
        
        if response.status_code == 200:
            upload_result = response.json()
            print(f"✅ Upload successful!")
            print(f"   Status: {upload_result.get('status', 'Unknown')}")
            print(f"   File ID: {upload_result.get('file_id', 'Unknown')}")
            print(f"   Chunks created: {upload_result.get('chunks_created', 0)}")
            print(f"   File path: {upload_result.get('file_path', 'Unknown')}")
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return
        
        # Wait a moment for processing
        time.sleep(3)
        
        # Query to check source metadata
        print(f"\n🔍 Querying to check source metadata...")
        query_response = requests.post(
            'http://localhost:8000/query',
            json={'query': 'Facility_Managers_2024_WebUI_Test Excel managers', 'max_results': 10},
            timeout=30
        )
        
        if query_response.status_code == 200:
            query_result = query_response.json()
            if query_result.get('success') and 'data' in query_result:
                sources = query_result['data'].get('sources', [])
                print(f"✅ Query returned {len(sources)} sources")
                
                # Check source metadata
                excel_sources = [s for s in sources if 'WebUI_Test' in s.get('doc_id', '') or 'WebUI_Test' in s.get('text', '')]
                
                if excel_sources:
                    print(f"\n📋 Found {len(excel_sources)} Excel-related sources:")
                    for i, source in enumerate(excel_sources):
                        print(f"\n   Source {i+1}:")
                        print(f"      Doc ID: {source.get('doc_id', 'Unknown')}")
                        print(f"      Score: {source.get('score', 0):.3f}")
                        print(f"      Content: {source.get('text', '')[:150]}...")
                        
                        # Extract metadata from the source
                        metadata = source.get('metadata', {})
                        print(f"      📝 Metadata:")
                        print(f"         upload_source: {metadata.get('upload_source', 'NOT_FOUND')}")
                        print(f"         original_filename: {metadata.get('original_filename', 'NOT_FOUND')}")
                        print(f"         source_type: {metadata.get('source_type', 'NOT_FOUND')}")
                        print(f"         content_type: {metadata.get('content_type', 'NOT_FOUND')}")
                        print(f"         upload_timestamp: {metadata.get('upload_timestamp', 'NOT_FOUND')}")
                        
                        # Check if source information is preserved
                        upload_source = metadata.get('upload_source', 'unknown')
                        if upload_source == 'web_upload':
                            print(f"         ✅ Source metadata preserved correctly!")
                        else:
                            print(f"         ❌ Source metadata missing or incorrect: '{upload_source}'")
                
                else:
                    print(f"❌ No Excel-related sources found in query results")
                    # Show all sources for debugging
                    print("\n   All sources returned:")
                    for i, source in enumerate(sources[:3]):
                        print(f"      {i+1}. Doc ID: {source.get('doc_id', 'Unknown')}")
                        print(f"         Content: {source.get('text', '')[:100]}...")
            else:
                print(f"❌ Query failed: {query_result}")
        else:
            print(f"❌ Query request failed: {query_response.status_code}")
            print(f"   Response: {query_response.text}")
    
    except FileNotFoundError:
        print(f"❌ Test Excel file not found: {excel_file_path}")
        print("   Please make sure the test file exists in the expected location")
    except Exception as e:
        print(f"❌ Error during test: {e}")

if __name__ == "__main__":
    test_existing_excel_upload() 