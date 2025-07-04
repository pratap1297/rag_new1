#!/usr/bin/env python3

import requests
import json
import time

def test_excel_fresh_upload():
    """Test Excel upload after cleaning existing files"""
    
    print("🔍 Testing Excel Fresh Upload")
    print("=" * 50)
    
    try:
        # First, get all files and delete Excel-related ones
        print("🗑️ Cleaning existing Excel files...")
        files_response = requests.get('http://localhost:8000/files', timeout=30)
        
        if files_response.status_code == 200:
            files_data = files_response.json()
            if files_data.get('success') and 'files' in files_data:
                files = files_data['files']
                
                excel_files = []
                for file_info in files:
                    file_path = file_info.get('file_path', '')
                    filename = file_info.get('filename', '')
                    
                    if ('xlsx' in filename.lower() or 
                        'excel' in filename.lower() or
                        'facility' in filename.lower() or
                        'webui' in filename.lower()):
                        excel_files.append(file_info)
                
                print(f"   Found {len(excel_files)} Excel files to delete")
                
                for file_info in excel_files:
                    file_path = file_info.get('file_path', '')
                    doc_id = file_info.get('doc_id', '')
                    
                    if file_path:
                        print(f"   Deleting: {file_path}")
                        delete_response = requests.delete(
                            f'http://localhost:8000/files/{file_path}',
                            timeout=30
                        )
                        if delete_response.status_code != 200:
                            print(f"   Warning: Delete failed for {file_path}: {delete_response.status_code}")
            else:
                print("   No files found or API error")
        else:
            print(f"   Warning: Could not get files list: {files_response.status_code}")
        
        # Wait a moment for cleanup
        time.sleep(2)
        
        # Now upload a fresh Excel file
        excel_file_path = "document_generator/test_data/Facility_Managers_2024.xlsx"
        unique_filename = f"Fresh_Excel_Test_{int(time.time())}.xlsx"
        
        print(f"\n📤 Uploading fresh Excel file as: {unique_filename}")
        
        with open(excel_file_path, 'rb') as f:
            files = {'file': (unique_filename, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            data = {
                'upload_source': 'web_upload',
                'original_path': unique_filename,
                'description': 'Fresh Excel file for metadata testing'
            }
            
            response = requests.post(
                'http://localhost:8000/upload',
                files=files,
                data=data,
                timeout=60
            )
        
        if response.status_code == 200:
            upload_result = response.json()
            print(f"✅ Upload response received!")
            print(f"   Status: {upload_result.get('status', 'Unknown')}")
            print(f"   File ID: {upload_result.get('file_id', 'Unknown')}")
            print(f"   Chunks created: {upload_result.get('chunks_created', 0)}")
            print(f"   File path: {upload_result.get('file_path', 'Unknown')}")
            
            if upload_result.get('status') == 'success':
                print(f"🎉 Upload successful!")
                
                # Wait for processing
                time.sleep(3)
                
                # Check the results
                print(f"\n🔍 Querying for the new file...")
                query_response = requests.post(
                    'http://localhost:8000/query',
                    json={'query': f'{unique_filename} Excel managers', 'max_results': 5},
                    timeout=30
                )
                
                if query_response.status_code == 200:
                    query_data = query_response.json()
                    if query_data.get('success') and 'data' in query_data:
                        sources = query_data['data'].get('sources', [])
                        
                        if sources:
                            print(f"✅ Found {len(sources)} sources!")
                            
                            # Check first source for metadata
                            first_source = sources[0]
                            metadata = first_source.get('metadata', {})
                            
                            upload_source = metadata.get('upload_source', 'NOT_FOUND')
                            content_type = metadata.get('content_type', 'NOT_FOUND')
                            source_type = metadata.get('source_type', 'NOT_FOUND')
                            original_filename = metadata.get('original_filename', 'NOT_FOUND')
                            
                            print(f"\n📋 Metadata check:")
                            print(f"   upload_source: {upload_source}")
                            print(f"   content_type: {content_type}")
                            print(f"   source_type: {source_type}")
                            print(f"   original_filename: {original_filename}")
                            
                            if upload_source == 'web_upload':
                                print(f"   ✅ METADATA FIX WORKING! upload_source preserved!")
                            else:
                                print(f"   ❌ Metadata fix not working: upload_source = '{upload_source}'")
                            
                            if source_type in ['excel_sheet', 'sheet_data']:
                                print(f"   ✅ Excel processor source_type preserved!")
                            else:
                                print(f"   ❌ Excel processor source_type not preserved: '{source_type}'")
                        else:
                            print(f"❌ No sources found in query results")
                    else:
                        print(f"❌ Query failed: {query_data}")
                else:
                    print(f"❌ Query request failed: {query_response.status_code}")
            else:
                print(f"❌ Upload failed: {upload_result}")
        else:
            print(f"❌ Upload request failed: {response.status_code}")
            print(f"   Response: {response.text}")
    
    except FileNotFoundError:
        print(f"❌ Test Excel file not found: {excel_file_path}")
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_excel_fresh_upload() 