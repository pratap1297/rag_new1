#!/usr/bin/env python3

import requests
import json
import time
import tempfile
import os

def test_excel_upload_fix():
    """Test that Excel upload now works without the NoneType comparison error"""
    
    print("🔍 Testing Excel Upload Fix")
    print("=" * 50)
    
    # Create a simple test Excel content
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
        # Upload via /upload endpoint
        print(f"📤 Uploading Excel file via /upload endpoint...")
        
        with open(temp_path, 'rb') as f:
            files = {'file': ('Test_Excel_Fix.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            data = {
                'upload_source': 'web_upload',
                'original_path': 'Test_Excel_Fix.xlsx',
                'description': 'Test Excel file to verify upload fix'
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
            
            # Wait for processing
            time.sleep(3)
            
            # Test query to verify the file was processed
            print(f"\n🔍 Querying for the uploaded file...")
            query_response = requests.post(
                'http://localhost:8000/query',
                json={'query': 'Test_Excel_Fix managers', 'max_results': 5},
                timeout=30
            )
            
            if query_response.status_code == 200:
                query_data = query_response.json()
                print(f"✅ Query successful!")
                print(f"   Results found: {len(query_data.get('results', []))}")
                
                if query_data.get('results'):
                    for i, result in enumerate(query_data['results'][:3]):
                        print(f"   Result {i+1}: {result.get('content', '')[:100]}...")
                        print(f"     Source: {result.get('source', 'Unknown')}")
                        print(f"     Score: {result.get('score', 0)}")
                else:
                    print("   No results found in query")
            else:
                print(f"❌ Query failed: {query_response.status_code}")
                print(f"   Response: {query_response.text}")
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    
    print("\n🎉 Excel upload fix test completed successfully!")
    return True

def test_excel_processor_direct():
    """Test the Excel processor directly to verify the fix"""
    
    print("\n🔍 Testing Excel Processor Directly")
    print("=" * 50)
    
    try:
        # Import the processor
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent / "rag_system" / "src"))
        
        from ingestion.processors.robust_excel_processor import RobustExcelProcessor
        
        # Create a test config with None values to test the fix
        test_config = {
            'max_file_size_mb': None,  # This should trigger the fix
            'process_images': True,
            'process_charts': False,
            'include_formulas': False,
            'max_rows_per_sheet': None,  # This should also trigger the fix
            'max_cols_per_sheet': None   # This should also trigger the fix
        }
        
        # Initialize processor
        processor = RobustExcelProcessor(test_config)
        
        print(f"✅ Processor initialized successfully")
        print(f"   max_file_size_mb: {processor.max_file_size_mb}")
        print(f"   max_rows_per_sheet: {processor.max_rows_per_sheet}")
        print(f"   max_cols_per_sheet: {processor.max_cols_per_sheet}")
        
        # Verify the fix worked
        if processor.max_file_size_mb == 50:
            print("✅ max_file_size_mb fix applied correctly")
        else:
            print(f"❌ max_file_size_mb fix failed: {processor.max_file_size_mb}")
            return False
            
        if processor.max_rows_per_sheet == 10000:
            print("✅ max_rows_per_sheet fix applied correctly")
        else:
            print(f"❌ max_rows_per_sheet fix failed: {processor.max_rows_per_sheet}")
            return False
            
        if processor.max_cols_per_sheet == 100:
            print("✅ max_cols_per_sheet fix applied correctly")
        else:
            print(f"❌ max_cols_per_sheet fix failed: {processor.max_cols_per_sheet}")
            return False
        
        print("🎉 Excel processor direct test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during direct processor test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Excel Upload Fix Tests")
    
    results = []
    
    # Test 1: Direct processor test
    results.append(("Excel Processor Direct Test", test_excel_processor_direct()))
    
    # Test 2: API upload test
    results.append(("Excel API Upload Test", test_excel_upload_fix()))
    
    # Summary
    print("\n" + "="*50)
    print("📊 TEST RESULTS SUMMARY")
    print("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Excel upload fix is working.")
    else:
        print("⚠️ Some tests failed. Check the logs above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 