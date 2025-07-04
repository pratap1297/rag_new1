#!/usr/bin/env python3

import requests
import json
import tempfile
import time

def test_excel_source_metadata():
    """Test that Excel files uploaded via web UI have correct source metadata"""
    
    print("🔍 Testing Excel File Source Metadata")
    print("=" * 50)
    
    # Create a simple test Excel content (as text to simulate)
    excel_content = """Name,Position,Building,Floor
Maria Garcia,Floor Manager,Building A,1
David Chen,Shift Supervisor,Building B,2
Sarah Johnson,Area Coordinator,Building C,1
Michael Brown,Safety Manager,Building A,3"""
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xlsx', delete=False) as tmp_file:
        tmp_file.write(excel_content)
        temp_path = tmp_file.name
    
    try:
        # Upload via /upload endpoint (simulating web UI)
        print(f"📤 Uploading Excel file via /upload endpoint...")
        
        with open(temp_path, 'rb') as f:
            files = {'file': ('Test_Managers.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            data = {
                'upload_source': 'web_upload',
                'original_path': 'Test_Managers.xlsx',
                'description': 'Test Excel file for source metadata verification'
            }
            
            response = requests.post(
                'http://localhost:8000/upload',
                files=files,
                data=data,
                timeout=30
            )
        
        if response.status_code == 200:
            upload_result = response.json()
            print(f"✅ Upload successful!")
            print(f"   File ID: {upload_result.get('file_id', 'Unknown')}")
            print(f"   Chunks created: {upload_result.get('chunks_created', 0)}")
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return
        
        # Wait a moment for processing
        time.sleep(2)
        
        # Query to verify metadata
        print(f"\n🔍 Querying to check source metadata...")
        query_response = requests.post(
            'http://localhost:8000/query',
            json={'query': 'Test_Managers Excel file', 'max_results': 10},
            timeout=30
        )
        
        if query_response.status_code == 200:
            query_result = query_response.json()
            if query_result.get('success') and 'data' in query_result:
                sources = query_result['data'].get('sources', [])
                print(f"✅ Query returned {len(sources)} sources")
                
                # Check source metadata
                excel_sources = [s for s in sources if 'Test_Managers' in s.get('doc_id', '') or 'xlsx' in s.get('text', '').lower()]
                
                if excel_sources:
                    print(f"\n📋 Found {len(excel_sources)} Excel-related sources:")
                    for i, source in enumerate(excel_sources):
                        print(f"\n   Source {i+1}:")
                        print(f"      Doc ID: {source.get('doc_id', 'Unknown')}")
                        print(f"      Score: {source.get('score', 0):.3f}")
                        print(f"      Content: {source.get('text', '')[:100]}...")
                        
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
                            print(f"         ❌ Source metadata missing or incorrect: {upload_source}")
                
                else:
                    print(f"❌ No Excel-related sources found in query results")
            else:
                print(f"❌ Query failed: {query_result}")
        else:
            print(f"❌ Query request failed: {query_response.status_code}")
            print(f"   Response: {query_response.text}")
        
        # Check vectors endpoint for detailed metadata
        print(f"\n🔍 Checking vectors endpoint for metadata...")
        vectors_response = requests.get(
            'http://localhost:8000/vectors?include_content=true&page_size=50',
            timeout=30
        )
        
        if vectors_response.status_code == 200:
            vectors_result = vectors_response.json()
            if vectors_result.get('success') and 'data' in vectors_result:
                vectors = vectors_result['data'].get('vectors', [])
                excel_vectors = [v for v in vectors if 'Test_Managers' in str(v.get('metadata', {})) or 'xlsx' in str(v.get('content', '')).lower()]
                
                if excel_vectors:
                    print(f"📊 Found {len(excel_vectors)} Excel vectors:")
                    for i, vector in enumerate(excel_vectors[:3]):  # Show first 3
                        metadata = vector.get('metadata', {})
                        print(f"\n   Vector {i+1}:")
                        print(f"      ID: {vector.get('id', 'Unknown')}")
                        print(f"      upload_source: {metadata.get('upload_source', 'NOT_FOUND')}")
                        print(f"      source_type: {metadata.get('source_type', 'NOT_FOUND')}")
                        print(f"      content_type: {metadata.get('content_type', 'NOT_FOUND')}")
                        print(f"      Content preview: {vector.get('content', '')[:100]}...")
                else:
                    print(f"❌ No Excel vectors found")
            else:
                print(f"❌ Vectors request failed: {vectors_result}")
        else:
            print(f"❌ Vectors endpoint failed: {vectors_response.status_code}")
    
    finally:
        # Cleanup
        import os
        try:
            os.unlink(temp_path)
        except:
            pass

if __name__ == "__main__":
    test_excel_source_metadata() 