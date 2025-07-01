#!/usr/bin/env python3
"""
Test API Debug
Debug the API ingestion process to see why JSON processor is not being used
"""

import requests
import json

def test_api_debug():
    """Test API with debug info"""
    print("🐛 Debug API Ingestion Process")
    print("=" * 40)
    
    api_url = "http://localhost:8000"
    
    # Sample ServiceNow JSON
    sample_json = {
        "incidents": [
            {
                "number": "INC999001",
                "priority": "High",
                "category": "Network",
                "short_description": "Debug test incident"
            }
        ]
    }
    
    text_content = json.dumps(sample_json, indent=2)
    
    # Test the logic locally first
    print("🔍 Local Logic Test:")
    
    def is_json_content(text_content):
        """Check if text is JSON content"""
        text_content = text_content.strip()
        return ((text_content.startswith('{') and text_content.endswith('}')) or
                (text_content.startswith('[') and text_content.endswith(']')))
    
    def is_servicenow_json(json_data):
        """Check if JSON data appears to be ServiceNow data"""
        servicenow_fields = ['number', 'sys_id', 'state', 'priority', 'category', 
                            'short_description', 'incident_number', 'created_by']
        
        # Check if it's a list of records directly
        if isinstance(json_data, list) and json_data:
            first_item = json_data[0]
            if isinstance(first_item, dict):
                return any(field in first_item for field in servicenow_fields)
        
        # Check if it's a single ServiceNow record
        elif isinstance(json_data, dict):
            # First check if it has ServiceNow fields directly
            if any(field in json_data for field in servicenow_fields):
                return True
            
            # Check for nested incidents structure (common ServiceNow export format)
            if 'incidents' in json_data:
                incidents = json_data['incidents']
                if isinstance(incidents, list) and incidents:
                    first_incident = incidents[0]
                    if isinstance(first_incident, dict):
                        return any(field in first_incident for field in servicenow_fields)
            
            # Check for other common ServiceNow container keys
            for container_key in ['records', 'result', 'data']:
                if container_key in json_data:
                    container_data = json_data[container_key]
                    if isinstance(container_data, list) and container_data:
                        first_record = container_data[0]
                        if isinstance(first_record, dict):
                            return any(field in first_record for field in servicenow_fields)
        
        return False
    
    print(f"   Is JSON content: {is_json_content(text_content)}")
    
    if is_json_content(text_content):
        try:
            json_data = json.loads(text_content)
            print(f"   JSON parse successful: {type(json_data)}")
            
            is_servicenow = is_servicenow_json(json_data)
            print(f"   Is ServiceNow JSON: {is_servicenow}")
            
            if isinstance(json_data, dict) and 'incidents' in json_data:
                incidents = json_data['incidents']
                print(f"   Found incidents array: {len(incidents)} items")
                if incidents:
                    first_incident = incidents[0]
                    print(f"   First incident fields: {list(first_incident.keys())}")
                    
                    servicenow_fields = ['number', 'sys_id', 'state', 'priority', 'category', 
                                        'short_description', 'incident_number', 'created_by']
                    found_fields = [f for f in servicenow_fields if f in first_incident]
                    print(f"   ServiceNow fields found: {found_fields}")
        except Exception as e:
            print(f"   JSON parse error: {e}")
    
    # Test metadata
    test_metadata = {
        "doc_path": "Debug_Test.json",
        "title": "Debug Test",
        "source_type": "web_upload",
        "operation": "upload",
        "source": "debug_test"
    }
    
    # Test ingestion
    print(f"\n📤 Testing API Ingestion:")
    try:
        ingest_data = {
            "text": text_content,
            "metadata": test_metadata
        }
        
        print(f"   Sending request to {api_url}/ingest...")
        response = requests.post(f"{api_url}/ingest", json=ingest_data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ API Response:")
            print(f"   Status: {result.get('status')}")
            print(f"   Chunks created: {result.get('chunks_created')}")
            print(f"   Processing method: {result.get('processing_method', 'NOT_SET')}")
            print(f"   Processor used: {result.get('processor_used', 'NOT_SET')}")
            
            # Check if it's using the correct logic
            if result.get('processing_method') == 'json_processor':
                print(f"🎯 SUCCESS: Using JSON processor!")
            elif result.get('processing_method') == 'text_chunking':
                print(f"❌ PROBLEM: Still using text chunking")
            else:
                print(f"⚠️ UNKNOWN: Processing method not set or unexpected value")
        else:
            print(f"❌ API Error: HTTP {response.status_code}")
            print(f"   Response: {response.text}")
    
    except Exception as e:
        print(f"❌ Request error: {e}")
    
    print(f"\n💡 **Expected Flow:**")
    print(f"1. is_json_content() should return True")
    print(f"2. json.loads() should parse successfully")
    print(f"3. is_servicenow_json() should return True")
    print(f"4. Processor should be found for .json file")
    print(f"5. Result should show 'processing_method': 'json_processor'")

if __name__ == "__main__":
    test_api_debug() 