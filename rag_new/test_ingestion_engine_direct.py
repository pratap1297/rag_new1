#!/usr/bin/env python3
"""
Test Ingestion Engine Direct
Test calling the ingestion engine's ingest_text method directly
"""

import json

def test_ingestion_engine_direct():
    """Test the ingestion engine directly"""
    print("🔧 Testing Ingestion Engine Direct")
    print("=" * 40)
    
    try:
        import sys
        sys.path.append('rag_system/src')
        
        from core.system_init import initialize_system
        
        container = initialize_system()
        print("✅ System initialized")
        
        # Get ingestion engine
        ingestion_engine = container.get('ingestion_engine')
        print(f"🔧 Ingestion engine: {type(ingestion_engine)}")
        
        # Sample ServiceNow JSON
        sample_json = {
            "incidents": [
                {
                    "number": "INC999002",
                    "priority": "High",
                    "category": "Network",
                    "short_description": "Direct engine test incident"
                }
            ]
        }
        
        text_content = json.dumps(sample_json, indent=2)
        
        # Test metadata
        test_metadata = {
            "doc_path": "Direct_Engine_Test.json",
            "title": "Direct Engine Test",
            "source_type": "web_upload",
            "operation": "upload",
            "source": "direct_test"
        }
        
        print(f"📤 Calling ingestion_engine.ingest_text() directly...")
        print(f"   Text content length: {len(text_content)}")
        print(f"   Metadata: {test_metadata}")
        
        # Call the ingestion engine directly
        result = ingestion_engine.ingest_text(text_content, test_metadata)
        
        print(f"✅ Direct Ingestion Result:")
        print(f"   Status: {result.get('status')}")
        print(f"   Chunks created: {result.get('chunks_created')}")
        print(f"   Vectors stored: {result.get('vectors_stored')}")
        print(f"   Text length: {result.get('text_length')}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_ingestion_engine_direct() 