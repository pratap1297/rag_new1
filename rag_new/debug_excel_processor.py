#!/usr/bin/env python3

import json
from pathlib import Path
import sys

print("🚀 Starting Excel processor debug script...")

# Add the current directory to the path so we can import modules
sys.path.append('.')

def test_excel_processor_directly():
    """Test the Excel processor directly to see what metadata it returns"""
    
    print("🔍 Testing Excel Processor Directly")
    print("=" * 50)
    
    try:
        # Import the Excel processor
        print("📦 Importing Excel processor...")
        from rag_system.src.ingestion.processors.excel_processor import ExcelProcessor
        
        # Create processor
        print("⚙️ Creating processor instance...")
        processor = ExcelProcessor()
        
        # Test with the existing Excel file
        excel_file_path = "document_generator/test_data/Facility_Managers_2024.xlsx"
        
        # Simulate metadata that would come from web upload
        test_metadata = {
            'upload_source': 'web_upload',
            'original_filename': 'Facility_Managers_2024_TEST.xlsx',
            'filename': 'Facility_Managers_2024_TEST.xlsx',
            'file_path': 'Facility_Managers_2024_TEST.xlsx',
            'content_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'upload_timestamp': '2025-07-01T12:00:00',
            'source_type': 'file'
        }
        
        print(f"📤 Input metadata:")
        for key, value in test_metadata.items():
            print(f"   {key}: {value}")
        
        print(f"\n📊 Processing Excel file: {excel_file_path}")
        
        # Process the file
        result = processor.process(excel_file_path, test_metadata)
        
        print(f"\n✅ Processing result:")
        print(f"   Status: {result.get('status', 'Unknown')}")
        print(f"   File name: {result.get('file_name', 'Unknown')}")
        print(f"   Sheets: {len(result.get('sheets', []))}")
        print(f"   Chunks: {len(result.get('chunks', []))}")
        
        print(f"\n📋 Result metadata:")
        metadata = result.get('metadata', {})
        for key, value in metadata.items():
            if key != 'properties':  # Skip properties for brevity
                print(f"   {key}: {value}")
        
        print(f"\n🧩 Chunk metadata:")
        chunks = result.get('chunks', [])
        for i, chunk in enumerate(chunks[:2]):  # Show first 2 chunks
            print(f"\n   Chunk {i+1}:")
            print(f"      Text length: {len(chunk.get('text', ''))}")
            print(f"      Text preview: {chunk.get('text', '')[:100]}...")
            
            chunk_metadata = chunk.get('metadata', {})
            print(f"      Metadata:")
            for key, value in chunk_metadata.items():
                print(f"         {key}: {value}")
        
        print(f"\n🔍 Checking for source metadata preservation:")
        if chunks:
            chunk_meta = chunks[0].get('metadata', {})
            upload_source = chunk_meta.get('upload_source', 'NOT_FOUND')
            content_type = chunk_meta.get('content_type', 'NOT_FOUND')
            original_filename = chunk_meta.get('original_filename', 'NOT_FOUND')
            
            print(f"   upload_source: {upload_source}")
            print(f"   content_type: {content_type}")
            print(f"   original_filename: {original_filename}")
            
            if upload_source == 'web_upload':
                print(f"   ✅ Source metadata is preserved in chunks!")
            else:
                print(f"   ❌ Source metadata NOT preserved in chunks")
        
    except ImportError as e:
        print(f"❌ Failed to import Excel processor: {e}")
        import traceback
        traceback.print_exc()
    except FileNotFoundError:
        print(f"❌ Test Excel file not found: {excel_file_path}")
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🔄 Calling test function...")
    test_excel_processor_directly()
    print("✅ Test function completed.") 