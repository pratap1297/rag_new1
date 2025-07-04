#!/usr/bin/env python3
"""
Check PDF Content in Detail
Extract and analyze the actual content from network layout PDFs
"""
import sys
from pathlib import Path
import json

# Add the rag_system to Python path
sys.path.insert(0, str(Path(__file__).parent / "rag_system" / "src"))

def analyze_pdf_content():
    """Analyze actual PDF content for network equipment information"""
    print("📄 DETAILED PDF CONTENT ANALYSIS")
    print("=" * 60)
    
    try:
        from core.dependency_container import DependencyContainer
        from core.dependency_container import register_core_services
        
        container = DependencyContainer()
        register_core_services(container)
        
        vector_store = container.get('vector_store')
        
        # Get all documents
        if hasattr(vector_store, 'client'):
            # Scroll through all documents to find network content
            results = []
            offset = None
            
            while True:
                response = vector_store.client.scroll(
                    collection_name=vector_store.collection_name,
                    limit=100,
                    offset=offset,
                    with_payload=True,
                    with_vectors=False
                )
                
                results.extend(response[0])
                offset = response[1]
                
                if offset is None:
                    break
            
            print(f"✅ Found {len(results)} total document chunks")
            
            # Group by file
            by_file = {}
            for result in results:
                filename = result.payload.get('filename', 'Unknown')
                if filename not in by_file:
                    by_file[filename] = []
                by_file[filename].append(result.payload)
            
            print(f"📁 Files found: {list(by_file.keys())}")
            
            # Analyze each PDF file in detail
            pdf_files = [f for f in by_file.keys() if f.endswith('.pdf')]
            
            for pdf_file in pdf_files:
                print(f"\n📄 ANALYZING: {pdf_file}")
                print("-" * 50)
                
                chunks = by_file[pdf_file]
                print(f"   Total chunks: {len(chunks)}")
                
                # Combine all text from this PDF
                full_text = ""
                for chunk in chunks:
                    text = chunk.get('text', '')
                    full_text += text + "\n"
                
                print(f"   Total text length: {len(full_text)} characters")
                
                # Look for network equipment keywords
                network_keywords = [
                    'router', 'switch', 'access point', 'ap', 'gateway', 'firewall',
                    'cisco', 'juniper', 'huawei', 'hp', 'dell', 'aruba',
                    'ethernet', 'wifi', 'wireless', 'network device',
                    'ip address', 'vlan', 'subnet', 'port',
                    'model', 'serial', 'mac address'
                ]
                
                found_keywords = []
                keyword_contexts = {}
                
                for keyword in network_keywords:
                    if keyword.lower() in full_text.lower():
                        found_keywords.append(keyword)
                        # Get context around keyword
                        text_lower = full_text.lower()
                        pos = text_lower.find(keyword.lower())
                        if pos != -1:
                            start = max(0, pos - 100)
                            end = min(len(full_text), pos + len(keyword) + 100)
                            context = full_text[start:end].strip()
                            keyword_contexts[keyword] = context
                
                if found_keywords:
                    print(f"   ✅ Found network keywords: {found_keywords}")
                    for keyword in found_keywords[:5]:  # Show first 5
                        print(f"      📝 {keyword}: {keyword_contexts.get(keyword, 'No context')[:150]}...")
                else:
                    print(f"   ⚠️  No explicit network equipment keywords found")
                
                # Show sample text to understand content structure
                print(f"\n   📋 Sample text from {pdf_file}:")
                sample_text = full_text[:500] if len(full_text) > 500 else full_text
                print(f"      {sample_text}...")
                
                # Look for structured data patterns
                print(f"\n   🔍 Looking for structured patterns:")
                
                # Look for table-like data
                lines = full_text.split('\n')
                table_lines = []
                for line in lines:
                    line = line.strip()
                    if line and ('|' in line or '\t' in line or '  ' in line):
                        table_lines.append(line)
                
                if table_lines:
                    print(f"   📊 Found {len(table_lines)} potential table rows:")
                    for table_line in table_lines[:5]:
                        print(f"      {table_line}")
                
                # Look for numbered lists or equipment inventories
                numbered_lines = []
                for line in lines:
                    line = line.strip()
                    if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                        numbered_lines.append(line)
                
                if numbered_lines:
                    print(f"   📝 Found {len(numbered_lines)} potential list items:")
                    for item in numbered_lines[:5]:
                        print(f"      {item}")
                
                # Look for IP addresses or network identifiers
                import re
                ip_pattern = r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
                mac_pattern = r'\b[0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}\b'
                
                ip_addresses = re.findall(ip_pattern, full_text)
                mac_addresses = re.findall(mac_pattern, full_text)
                
                if ip_addresses:
                    print(f"   🌐 Found IP addresses: {ip_addresses[:5]}")
                if mac_addresses:
                    print(f"   🔗 Found MAC addresses: {mac_addresses[:5]}")
            
            # Analyze ServiceNow incidents for network equipment mentions
            print(f"\n📄 ANALYZING: ServiceNow Incidents")
            print("-" * 50)
            
            if 'ServiceNow_Incidents_Last30Days.json' in by_file:
                incident_chunks = by_file['ServiceNow_Incidents_Last30Days.json']
                print(f"   Total incident chunks: {len(incident_chunks)}")
                
                # Look for network equipment in incidents
                network_incidents = []
                for chunk in incident_chunks:
                    text = chunk.get('text', '').lower()
                    if any(keyword in text for keyword in ['router', 'switch', 'access point', 'network', 'wifi', 'ethernet']):
                        network_incidents.append(chunk)
                
                print(f"   ✅ Found {len(network_incidents)} network-related incidents")
                
                for i, incident in enumerate(network_incidents[:3], 1):
                    print(f"   📋 Network Incident {i}:")
                    incident_text = incident.get('text', '')[:300] + "..." if len(incident.get('text', '')) > 300 else incident.get('text', '')
                    print(f"      {incident_text}")
            
            # Check Excel facility manager data
            print(f"\n📄 ANALYZING: Facility Managers Excel")
            print("-" * 50)
            
            if 'Facility_Managers_2024.xlsx' in by_file:
                excel_chunks = by_file['Facility_Managers_2024.xlsx']
                print(f"   Total Excel chunks: {len(excel_chunks)}")
                
                for i, chunk in enumerate(excel_chunks, 1):
                    print(f"   📊 Excel Sheet {i}:")
                    chunk_text = chunk.get('text', '')[:300] + "..." if len(chunk.get('text', '')) > 300 else chunk.get('text', '')
                    print(f"      {chunk_text}")
        
        return True
        
    except Exception as e:
        print(f"❌ PDF analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def suggest_queries():
    """Suggest better queries based on actual content"""
    print(f"\n💡 SUGGESTED QUERIES BASED ON ACTUAL CONTENT")
    print("=" * 60)
    
    suggestions = [
        "Show me network coverage areas",
        "What buildings have network coverage",
        "Signal strength information",
        "Network incidents and problems", 
        "WiFi coverage quality",
        "Access points in buildings",
        "Network infrastructure issues",
        "Building network layouts",
        "Facility managers contact information",
        "Network-related incidents last 30 days"
    ]
    
    for i, suggestion in enumerate(suggestions, 1):
        print(f"{i:2d}. {suggestion}")
    
    print(f"\n📝 Note: The documents appear to contain:")
    print(f"   - Network coverage maps and signal strength data")
    print(f"   - ServiceNow incidents (some network-related)")
    print(f"   - Facility manager contact information")
    print(f"   - Building layout information")
    print(f"   But may not contain detailed router/equipment inventories")

def main():
    """Run detailed PDF content analysis"""
    print("📄 DETAILED PDF CONTENT ANALYSIS")
    print("=" * 80)
    print("Analyzing actual content of network layout documents")
    print()
    
    success = analyze_pdf_content()
    
    if success:
        suggest_queries()
    
    print(f"\n📋 ANALYSIS COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main() 