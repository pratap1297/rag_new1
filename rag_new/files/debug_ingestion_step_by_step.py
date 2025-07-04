#!/usr/bin/env python3

import sys
import json
import time
import logging
from pathlib import Path

# Set up logging to see everything
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add the current directory to the path so we can import modules
sys.path.append('.')
sys.path.append('./rag_system/src')

def debug_excel_ingestion():
    """Debug Excel ingestion step by step"""
    
    print("🔍 DEBUG: Excel Ingestion Step by Step")
    print("=" * 60)
    
    try:
        # Import required modules with fallbacks
        print("📦 Importing modules...")
        
        try:
            from rag_system.src.core.container import Container
        except ImportError:
            try:
                from core.container import Container
            except ImportError:
                print("❌ Could not import Container. Let's use API instead...")
                # Fallback to API testing
                import requests
                
                print("🔄 Using API endpoint for testing...")
                
                excel_file_path = "document_generator/test_data/Facility_Managers_2024.xlsx"
                
                # Upload via API with debug metadata
                with open(excel_file_path, 'rb') as f:
                    files = {'file': ('DEBUG_API_Test.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
                    data = {
                        'upload_source': 'web_upload',
                        'original_path': 'DEBUG_API_Test.xlsx',
                        'description': 'Debug test for metadata preservation'
                    }
                    
                    print(f"📤 Uploading via API with debug metadata...")
                    response = requests.post(
                        'http://localhost:8000/upload',
                        files=files,
                        data=data,
                        timeout=60
                    )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ API Upload result:")
                    print(f"   Status: {result.get('status', 'Unknown')}")
                    print(f"   Chunks: {result.get('chunks_created', 0)}")
                    
                    if result.get('status') == 'success':
                        # Wait and check vectors
                        time.sleep(2)
                        
                        print(f"\n🔍 Checking vectors via API...")
                        vector_response = requests.get('http://localhost:8000/vectors?include_content=true&page_size=10')
                        
                        if vector_response.status_code == 200:
                            vector_data = vector_response.json()
                            vectors = vector_data.get('data', {}).get('vectors', [])
                            
                            debug_vectors = [v for v in vectors if 'DEBUG_API_Test' in str(v.get('metadata', {}))]
                            
                            if debug_vectors:
                                print(f"✅ Found {len(debug_vectors)} debug vectors!")
                                
                                metadata = debug_vectors[0].get('metadata', {})
                                upload_source = metadata.get('upload_source', 'NOT_FOUND')
                                content_type = metadata.get('content_type', 'NOT_FOUND')
                                source_type = metadata.get('source_type', 'NOT_FOUND')
                                
                                print(f"\n📋 API Test Metadata Check:")
                                print(f"   upload_source: {upload_source}")
                                print(f"   content_type: {content_type}")
                                print(f"   source_type: {source_type}")
                                
                                success_count = 0
                                if upload_source == 'web_upload':
                                    print(f"   ✅ upload_source preserved!")
                                    success_count += 1
                                else:
                                    print(f"   ❌ upload_source NOT preserved")
                                
                                if content_type and content_type != 'NOT_FOUND':
                                    print(f"   ✅ content_type preserved!")
                                    success_count += 1
                                else:
                                    print(f"   ❌ content_type NOT preserved")
                                
                                if source_type in ['excel_sheet', 'sheet_data']:
                                    print(f"   ✅ source_type preserved!")
                                    success_count += 1
                                else:
                                    print(f"   ❌ source_type NOT preserved")
                                
                                print(f"\n📊 API Metadata Fix Success: {success_count}/3")
                                
                                if success_count == 3:
                                    print(f"🎉 METADATA FIXES WORKING VIA API!")
                                else:
                                    print(f"❌ METADATA FIXES NOT WORKING VIA API")
                                    
                                    # Print all metadata for debugging
                                    print(f"\n🔍 Complete API metadata:")
                                    for key, value in metadata.items():
                                        print(f"   {key}: {value}")
                            else:
                                print(f"❌ No debug vectors found via API")
                        else:
                            print(f"❌ Vector API failed: {vector_response.status_code}")
                    else:
                        print(f"❌ API upload failed: {result}")
                else:
                    print(f"❌ API request failed: {response.status_code}, {response.text}")
                return
        
        # Continue with direct ingestion engine test if imports work
        print("⚙️ Initializing container...")
        container = Container()
        ingestion_engine = container.get('ingestion_engine')
        
        # Test metadata that should be passed
        test_metadata = {
            'upload_source': 'web_upload',
            'original_filename': 'DEBUG_Direct_Test.xlsx',
            'filename': 'DEBUG_Direct_Test.xlsx',
            'file_path': 'DEBUG_Direct_Test.xlsx',
            'content_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'upload_timestamp': '2025-07-01T12:30:00',
            'source_type': 'file'
        }
        
        print(f"\n📋 Test metadata to be passed:")
        for key, value in test_metadata.items():
            print(f"   {key}: {value}")
        
        # Test file path
        excel_file_path = "document_generator/test_data/Facility_Managers_2024.xlsx"
        print(f"\n📊 Processing Excel file: {excel_file_path}")
        
        # Step 1: Test the ingestion engine directly
        print(f"\n🔧 Step 1: Testing ingestion_engine.ingest_file()...")
        
        # Use the real file path
        result = ingestion_engine.ingest_file(excel_file_path, test_metadata)
        
        print(f"✅ Ingestion result:")
        print(f"   Status: {result.get('status', 'Unknown')}")
        print(f"   File ID: {result.get('file_id', 'Unknown')}")
        print(f"   Chunks created: {result.get('chunks_created', 0)}")
        print(f"   Vectors stored: {result.get('vectors_stored', 0)}")
        
        if result.get('status') == 'success':
            print(f"\n🎉 Direct ingestion successful!")
            
            # Step 2: Check what's actually stored
            print(f"\n🔍 Step 2: Checking stored vectors...")
            
            # Get the vector store
            vector_store = container.get('vector_store')
            
            # Check recent vectors
            vector_count = 0
            recent_vectors = []
            
            for vector_id, metadata in vector_store.id_to_metadata.items():
                if metadata and not metadata.get('deleted', False):
                    # Check if this is from our test file
                    if ('DEBUG_Direct_Test' in str(metadata) or 
                        metadata.get('filename') == 'DEBUG_Direct_Test.xlsx' or
                        metadata.get('original_filename') == 'DEBUG_Direct_Test.xlsx'):
                        recent_vectors.append((vector_id, metadata))
                        vector_count += 1
            
            print(f"   Found {vector_count} vectors from our test file")
            
            if recent_vectors:
                # Analyze the first vector's metadata
                vector_id, metadata = recent_vectors[0]
                print(f"\n📋 First vector metadata analysis:")
                print(f"   Vector ID: {vector_id}")
                print(f"   Metadata keys: {list(metadata.keys())}")
                
                # Check specific source metadata
                upload_source = metadata.get('upload_source', 'NOT_FOUND')
                content_type = metadata.get('content_type', 'NOT_FOUND')
                source_type = metadata.get('source_type', 'NOT_FOUND')
                original_filename = metadata.get('original_filename', 'NOT_FOUND')
                
                print(f"\n🔍 Source metadata check:")
                print(f"   upload_source: {upload_source}")
                print(f"   content_type: {content_type}")
                print(f"   source_type: {source_type}")
                print(f"   original_filename: {original_filename}")
                
                # Success/failure analysis
                success_count = 0
                if upload_source == 'web_upload':
                    print(f"   ✅ upload_source preserved correctly!")
                    success_count += 1
                else:
                    print(f"   ❌ upload_source NOT preserved: '{upload_source}'")
                
                if content_type and content_type != 'NOT_FOUND':
                    print(f"   ✅ content_type preserved!")
                    success_count += 1
                else:
                    print(f"   ❌ content_type NOT preserved: '{content_type}'")
                
                if source_type in ['excel_sheet', 'sheet_data']:
                    print(f"   ✅ Excel processor source_type preserved!")
                    success_count += 1
                else:
                    print(f"   ❌ Excel processor source_type NOT preserved: '{source_type}'")
                
                print(f"\n📊 Direct Metadata Fix Success Rate: {success_count}/3")
                
                if success_count == 3:
                    print(f"🎉 ALL METADATA FIXES WORKING!")
                elif success_count > 0:
                    print(f"⚠️ PARTIAL SUCCESS - Some metadata preserved")
                else:
                    print(f"❌ METADATA FIXES NOT WORKING")
                
                # Show all metadata for debugging
                print(f"\n🔍 Complete metadata dump:")
                for key, value in metadata.items():
                    print(f"   {key}: {value}")
            else:
                print(f"❌ No vectors found from our test file!")
        else:
            print(f"❌ Direct ingestion failed: {result}")
    
    except Exception as e:
        print(f"❌ Error during debug: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_excel_ingestion() 