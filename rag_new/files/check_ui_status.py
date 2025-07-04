#!/usr/bin/env python3
"""
Check UI status and provide testing instructions
"""
import requests
import time

def check_ui_status():
    """Check if UI is running"""
    try:
        response = requests.get('http://127.0.0.1:7860', timeout=5)
        return response.status_code == 200
    except:
        return False

def main():
    print("🔍 Checking UI Status...")
    print("=" * 50)
    
    ui_running = check_ui_status()
    
    if ui_running:
        print("✅ UI is running at http://127.0.0.1:7860")
        print("🌐 You can now access the frontend UI!")
        
        print("\n📁 Available test files for upload:")
        print("   Location: D:\\Projects-D\\pepsi-final2\\document_generator\\test_data")
        print("   - BuildingA_Network_Layout.pdf (11 KB)")
        print("   - BuildingB_Network_Layout.pdf (6 KB)")
        print("   - BuildingC_Network_Layout.pdf (6 KB)")
        print("   - Facility_Managers_2024.xlsx (8.5 KB)")
        print("   - ServiceNow_Incidents_Last30Days.json (5 KB)")
        
        print("\n🧪 Testing Steps:")
        print("1. Open http://127.0.0.1:7860 in your browser")
        print("2. Upload files from the test_data directory")
        print("3. Test Qdrant functionality with queries like:")
        print("   - 'list all incidents' (should show ALL incidents, no limits)")
        print("   - 'show all network layouts'")
        print("   - 'find building information'")
        print("   - 'count total incidents'")
        
        print("\n🦅 Qdrant Benefits to Verify:")
        print("✅ No top_k limitations for listing queries")
        print("✅ Better metadata filtering")
        print("✅ Complete result retrieval")
        print("✅ Enhanced query performance")
        
    else:
        print("❌ UI is not running")
        print("🔄 Please start the UI with: python launch_fixed_ui.py")
    
    return ui_running

if __name__ == "__main__":
    main() 