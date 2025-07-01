#!/usr/bin/env python3
"""
Debug Ingest Processing
Test the JSON detection and processor selection logic
"""

import json
import tempfile
import os

def test_json_detection():
    """Test the JSON detection logic"""
    print("🔍 Testing JSON Detection Logic")
    print("=" * 40)
    
    # Sample JSON content
    sample_json = {
        "incidents": [
            {
                "number": "INC030001",
                "priority": "High",
                "category": "Network",
                "short_description": "No WiFi signal at loading dock"
            }
        ]
    }
    
    text = json.dumps(sample_json, indent=2)
    
    def is_json_content(text_content):
        """Check if text is JSON content"""
        text_content = text_content.strip()
        return ((text_content.startswith('{') and text_content.endswith('}')) or
                (text_content.startswith('[') and text_content.endswith(']')))
    
    def is_servicenow_json(json_data):
        """Check if JSON data appears to be ServiceNow data"""
        if isinstance(json_data, list) and json_data:
            # Check first item for ServiceNow fields
            first_item = json_data[0]
            if isinstance(first_item, dict):
                servicenow_fields = ['number', 'sys_id', 'state', 'priority', 'category', 
                                    'short_description', 'incident_number', 'created_by']
                return any(field in first_item for field in servicenow_fields)
        elif isinstance(json_data, dict):
            # Check if it's a single ServiceNow record
            servicenow_fields = ['number', 'sys_id', 'state', 'priority', 'category', 
                                'short_description', 'incident_number', 'created_by']
            return any(field in json_data for field in servicenow_fields)
        return False
    
    print(f"📝 Text content preview: {text[:100]}...")
    print(f"🔍 Is JSON content: {is_json_content(text)}")
    
    if is_json_content(text):
        try:
            json_data = json.loads(text)
            print(f"✅ JSON parse successful")
            print(f"🎯 Is ServiceNow JSON: {is_servicenow_json(json_data)}")
            
            # Test nested structure
            if isinstance(json_data, dict) and 'incidents' in json_data:
                incidents = json_data['incidents']
                print(f"📋 Found 'incidents' key with {len(incidents)} items")
                
                if incidents:
                    first_incident = incidents[0]
                    print(f"🎫 First incident fields: {list(first_incident.keys())}")
                    
                    # Check for ServiceNow fields in nested structure
                    servicenow_fields = ['number', 'sys_id', 'state', 'priority', 'category', 
                                        'short_description', 'incident_number', 'created_by']
                    found_fields = [field for field in servicenow_fields if field in first_incident]
                    print(f"✅ ServiceNow fields found: {found_fields}")
                    
                    # Test with nested incidents
                    nested_check = is_servicenow_json(incidents)  # Check the incidents array directly
                    print(f"🎯 Is ServiceNow (nested check): {nested_check}")
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parse failed: {e}")
    
    # Test processor detection
    print(f"\n🔧 Testing Processor Detection")
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as tmp_file:
        json.dump(sample_json, tmp_file, indent=2, ensure_ascii=False)
        tmp_file_path = tmp_file.name
    
    try:
        # Try to import and test processor registry
        import sys
        sys.path.append('rag_system/src')
        
        from ingestion.processor_registry import ProcessorRegistry
        from core.config_manager import ConfigManager
        
        config_manager = ConfigManager()
        registry = ProcessorRegistry(config_manager)
        
        processor = registry.get_processor(tmp_file_path)
        print(f"📦 Processor found: {processor.__class__.__name__ if processor else 'None'}")
        
        if processor:
            print(f"🔍 Processor type: {type(processor)}")
            print(f"📋 Processor supports JSON: {'json' in tmp_file_path.lower()}")
        
    except Exception as e:
        print(f"❌ Processor test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        if os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)
    
    print(f"\n💡 **Debugging Notes:**")
    print(f"1. JSON detection should work if content starts/ends with {{ }} or [ ]")
    print(f"2. ServiceNow detection looks for specific fields in JSON structure")
    print(f"3. Processor registry should return ServiceNowProcessor for .json files")
    print(f"4. If processor is None, check processor registry configuration")

if __name__ == "__main__":
    test_json_detection() 