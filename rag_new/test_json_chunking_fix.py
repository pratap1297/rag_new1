#!/usr/bin/env python3
"""
Test JSON Chunking Fix
Verify that JSON files now use ServiceNowProcessor for logical chunking
"""

import requests
import json
import time

def test_json_chunking_fix():
    """Test that JSON files get proper logical chunking"""
    print("🧪 Testing JSON Chunking Fix")
    print("=" * 50)
    
    api_url = "http://localhost:8000"
    
    # Sample ServiceNow incidents JSON
    sample_json = {
        "incidents": [
            {
                "number": "INC030001",
                "priority": "High",
                "category": "Network",
                "subcategory": "Wireless Connectivity",
                "created": "2025-06-01 19:10:12",
                "reporter": "Jane Doe",
                "assigned_to": "Sarah Johnson",
                "location": "Building C - Loading Bays 1-5",
                "short_description": "No WiFi signal at loading dock",
                "description": "Loading dock workers report no WiFi connectivity in bays 1-5. This is affecting productivity and barcode scanning operations.",
                "state": "In Progress",
                "work_notes": [
                    {"time": "14:25", "note": "Initial investigation started"},
                    {"time": "15:30", "note": "Signal strength testing in progress"},
                    {"time": "16:45", "note": "Identified coverage gap, planning AP relocation"}
                ]
            },
            {
                "number": "INC030002",
                "priority": "Critical",
                "category": "Environmental",
                "subcategory": "Temperature Control",
                "created": "2025-06-05 08:15:30",
                "reporter": "Mike Wilson",
                "assigned_to": "Tom Brown",
                "location": "Building A - Freezer Zone 2",
                "short_description": "Temperature monitoring system cannot communicate",
                "description": "Temperature monitoring system in freezer zone 2 has lost communication with central control. Risk of product loss due to temperature variations.",
                "state": "Resolved",
                "resolution": "Emergency replacement completed. Environmental enclosure heating element repaired.",
                "resolved": "2025-06-07 21:10:12",
                "work_notes": [
                    {"time": "14:25", "note": "Monitoring for stability"},
                    {"time": "15:42", "note": "Equipment status checked"},
                    {"time": "17:15", "note": "Emergency repair completed"}
                ]
            },
            {
                "number": "INC030003",
                "priority": "Medium",
                "category": "IT Equipment",
                "subcategory": "Hardware Failure",
                "created": "2025-06-10 10:30:00",
                "reporter": "Lisa Davis",
                "assigned_to": "Alex Chen",
                "location": "Building B - Office Area",
                "short_description": "Workstation performance degradation",
                "description": "Multiple workstations in Building B office area experiencing slow performance and random freezes.",
                "state": "New",
                "work_notes": [
                    {"time": "11:00", "note": "Initial assessment scheduled"},
                    {"time": "13:30", "note": "Hardware diagnostics running"}
                ]
            }
        ]
    }
    
    # Test metadata
    test_metadata = {
        "doc_path": "ServiceNow_Test_Incidents.json",
        "title": "ServiceNow Test Incidents",
        "source_type": "web_upload",
        "operation": "upload",
        "source": "test_fix"
    }
    
    print("📋 Testing JSON content ingestion...")
    print(f"   Sample data: {len(sample_json['incidents'])} incidents")
    print(f"   Content size: {len(json.dumps(sample_json))} characters")
    
    # Test 1: Upload via /ingest endpoint
    try:
        print("\n🔍 Test 1: Upload via /ingest endpoint")
        
        ingest_data = {
            "text": json.dumps(sample_json, indent=2),
            "metadata": test_metadata
        }
        
        response = requests.post(f"{api_url}/ingest", json=ingest_data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Ingestion successful")
            print(f"   Status: {result.get('status')}")
            print(f"   Chunks created: {result.get('chunks_created')}")
            print(f"   Processing method: {result.get('processing_method', 'unknown')}")
            print(f"   Processor used: {result.get('processor_used', 'none')}")
            
            # Check if logical chunking was used
            if result.get('processing_method') == 'json_processor':
                print(f"🎯 SUCCESS: JSON processor was used!")
                expected_chunks = len(sample_json['incidents'])
                actual_chunks = result.get('chunks_created', 0)
                
                if actual_chunks == expected_chunks:
                    print(f"✅ Perfect chunking: {actual_chunks} chunks for {expected_chunks} incidents")
                else:
                    print(f"⚠️ Chunking mismatch: {actual_chunks} chunks for {expected_chunks} incidents")
            else:
                print(f"❌ FAILED: Still using text chunking instead of JSON processor")
        else:
            print(f"❌ Ingestion failed: HTTP {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Ingestion error: {e}")
    
    # Wait a moment for processing
    time.sleep(2)
    
    # Test 2: Query the data to see chunk quality
    print(f"\n🔍 Test 2: Query the ingested data")
    try:
        query_data = {
            'query': 'incidents ServiceNow high priority network issues',
            'max_results': 5,
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
                    print(f"   Content preview: {content[:300]}...")
                    
                    # Check for complete incident info
                    if 'INC' in content and ('priority' in content.lower() or 'category' in content.lower()):
                        print(f"   ✅ Contains complete incident information")
                    else:
                        print(f"   ❌ Appears to be fragmented content")
            else:
                print(f"❌ Query failed: {result.get('error', 'Unknown error')}")
        else:
            print(f"❌ Query failed: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Query error: {e}")
    
    # Test 3: Check vector metadata directly
    print(f"\n🔍 Test 3: Check vector metadata")
    try:
        response = requests.get(f"{api_url}/manage/vectors?limit=10", timeout=15)
        if response.status_code == 200:
            vectors = response.json()
            print(f"📊 Found {len(vectors)} recent vectors")
            
            # Look for our test vectors
            test_vectors = []
            for vector in vectors:
                metadata = vector.get('metadata', {})
                if metadata.get('source') == 'test_fix':
                    test_vectors.append(vector)
            
            print(f"🎯 Found {len(test_vectors)} vectors from our test:")
            for i, tv in enumerate(test_vectors, 1):
                metadata = tv.get('metadata', {})
                content = metadata.get('text', metadata.get('content', ''))
                print(f"\n   Vector {i}:")
                print(f"      Processing method: {metadata.get('processing_method', 'unknown')}")
                print(f"      Processor: {metadata.get('processor', 'unknown')}")
                print(f"      Content length: {len(content)} chars")
                print(f"      Content preview: {content[:200]}...")
                
                # Check if it contains a complete incident
                if 'INC' in content and 'short_description' in content:
                    print(f"      ✅ Contains complete incident record")
                else:
                    print(f"      ❌ Appears to be fragmented")
            
        else:
            print(f"❌ Failed to get vectors: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Vector check error: {e}")
    
    print(f"\n🎯 **Test Summary:**")
    print(f"If JSON chunking fix is working correctly, you should see:")
    print(f"  ✅ Processing method: 'json_processor'")
    print(f"  ✅ Processor used: 'ServiceNowProcessor'")
    print(f"  ✅ 3 chunks created (one per incident)")
    print(f"  ✅ Each chunk contains complete incident information")
    print(f"  ✅ No 200-character fragmentation")

if __name__ == "__main__":
    test_json_chunking_fix() 