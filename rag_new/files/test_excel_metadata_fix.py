#!/usr/bin/env python3

import requests
import json
import time

def test_excel_metadata_fix():
    """Test that the Excel metadata fix is working"""
    
    print("🔍 Testing Excel Metadata Fix")
    print("=" * 50)
    
    excel_file_path = "document_generator/test_data/Facility_Managers_2024.xlsx"
    
    try:
        # Upload via /upload endpoint with unique filename
        unique_filename = f"Excel_Metadata_Fix_Test_{int(time.time())}.xlsx"
        print(f"📤 Uploading Excel file as: {unique_filename}")
        
        with open(excel_file_path, 'rb') as f:
            files = {'file': (unique_filename, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            data = {
                'upload_source': 'web_upload',
                'original_path': unique_filename,
                'description': 'Test Excel file for metadata fix verification'
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
            
            if upload_result.get('status') != 'success':
                print(f"❌ Upload had issues: {upload_result}")
                return
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return
        
        # Wait for processing
        time.sleep(3)
        
        # Check vector database directly for the new file
        print(f"\n🔍 Checking vector database for: {unique_filename}")
        vector_response = requests.get(
            'http://localhost:8000/vectors?include_content=true&page_size=20',
            timeout=30
        )
        
        if vector_response.status_code == 200:
            vector_data = vector_response.json()
            if vector_data.get('success') and 'data' in vector_data:
                vectors = vector_data['data'].get('vectors', [])
                
                # Find vectors for our new file
                new_file_vectors = []
                for vector in vectors:
                    metadata = vector.get('metadata', {})
                    content = vector.get('content', '')
                    
                    if (unique_filename in str(metadata) or 
                        unique_filename in content or
                        f"Excel_Metadata_Fix_Test_{int(time.time())}" in str(metadata)):
                        new_file_vectors.append(vector)
                
                if new_file_vectors:
                    print(f"✅ Found {len(new_file_vectors)} vectors for the new file!")
                    
                    for i, vector in enumerate(new_file_vectors):
                        print(f"\n   Vector {i+1}:")
                        metadata = vector.get('metadata', {})
                        
                        upload_source = metadata.get('upload_source', 'NOT_FOUND')
                        original_filename = metadata.get('original_filename', 'NOT_FOUND')
                        content_type = metadata.get('content_type', 'NOT_FOUND')
                        source_type = metadata.get('source_type', 'NOT_FOUND')
                        
                        print(f"      upload_source: {upload_source}")
                        print(f"      original_filename: {original_filename}")
                        print(f"      content_type: {content_type}")
                        print(f"      source_type: {source_type}")
                        
                        # Check if the fix worked
                        if upload_source == 'web_upload':
                            print(f"      ✅ Metadata fix is working! upload_source preserved!")
                        else:
                            print(f"      ❌ Metadata fix not working: upload_source = '{upload_source}'")
                        
                        if source_type == 'excel_sheet':
                            print(f"      ✅ Excel processor source_type preserved!")
                        else:
                            print(f"      ❌ Excel processor source_type not preserved: '{source_type}'")
                            
                        # Show a sample of other metadata
                        print(f"      All metadata keys: {list(metadata.keys())}")
                        break  # Just check first vector
                else:
                    print(f"❌ No vectors found for new file: {unique_filename}")
                    print(f"   Available doc_ids: {[v.get('metadata', {}).get('doc_id', 'unknown') for v in vectors[:5]]}")
            else:
                print(f"❌ Vector API response error: {vector_data}")
        else:
            print(f"❌ Vector API request failed: {vector_response.status_code}")
    
    except FileNotFoundError:
        print(f"❌ Test Excel file not found: {excel_file_path}")
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_excel_metadata_fix() 