#!/usr/bin/env python3
"""
Query Network Equipment Information
Extract actual access point and network equipment data from documents
"""
import sys
from pathlib import Path

# Add the rag_system to Python path
sys.path.insert(0, str(Path(__file__).parent / "rag_system" / "src"))

def query_network_equipment():
    """Query for actual network equipment information"""
    print("🌐 NETWORK EQUIPMENT INFORMATION")
    print("=" * 60)
    
    try:
        from core.dependency_container import DependencyContainer
        from core.dependency_container import register_core_services
        
        container = DependencyContainer()
        register_core_services(container)
        
        query_engine = container.get('query_engine')
        vector_store = container.get('vector_store')
        
        # Targeted queries based on actual content
        equipment_queries = [
            "What Cisco access points are in the buildings",
            "Show me all AP models and types",
            "Access point placement information",
            "Cisco 3802I access points",
            "Cisco 3802E access points", 
            "Cisco 1562E access points",
            "MDF and IDF network equipment",
            "Internal and external antenna types",
            "WiFi coverage in buildings",
            "Access point locations by building"
        ]
        
        print(f"🔍 Querying access point information:")
        equipment_found = {}
        
        for i, query in enumerate(equipment_queries, 1):
            print(f"\n--- Query {i}: '{query}' ---")
            
            try:
                response = query_engine.process_query(query, top_k=10)
                
                sources = response.get('sources', [])
                print(f"✅ Found {len(sources)} relevant sources")
                
                # Extract equipment information from sources
                for source in sources:
                    text = source.get('text', '').upper()
                    filename = source.get('filename', 'Unknown')
                    
                    # Look for Cisco equipment
                    if 'CISCO' in text:
                        cisco_models = []
                        if 'CISCO 3802I' in text:
                            cisco_models.append('3802I (Internal)')
                        if 'CISCO 3802E' in text:
                            cisco_models.append('3802E (External Sector)')
                        if 'CISCO 1562E' in text:
                            cisco_models.append('1562E (External Omni)')
                        
                        if cisco_models:
                            if filename not in equipment_found:
                                equipment_found[filename] = set()
                            equipment_found[filename].update(cisco_models)
                
                # Show relevant excerpts
                relevant_sources = [s for s in sources if 'cisco' in s.get('text', '').lower() or 'ap' in s.get('text', '').lower()]
                
                if relevant_sources:
                    print(f"   📄 Relevant equipment info found:")
                    for source in relevant_sources[:3]:
                        text = source.get('text', '')
                        # Extract AP-related lines
                        lines = text.split('\n')
                        ap_lines = [line.strip() for line in lines if any(keyword in line.upper() for keyword in ['CISCO', 'AP', 'MODEL', 'ANTENNA', 'MDF', 'IDF'])]
                        if ap_lines:
                            print(f"      📍 {source.get('filename', 'Unknown')}: {' | '.join(ap_lines[:3])}")
                
            except Exception as e:
                print(f"❌ Query failed: {e}")
        
        # Summarize equipment found
        print(f"\n📊 NETWORK EQUIPMENT SUMMARY")
        print("=" * 50)
        
        if equipment_found:
            total_models = set()
            for filename, models in equipment_found.items():
                print(f"📄 {filename}:")
                for model in sorted(models):
                    print(f"   • Cisco {model}")
                    total_models.add(model)
            
            print(f"\n🔢 TOTAL EQUIPMENT COUNT:")
            print(f"   • Total unique AP models: {len(total_models)}")
            print(f"   • Total buildings with equipment: {len(equipment_found)}")
            print(f"   • Equipment types found:")
            for model in sorted(total_models):
                print(f"     - Cisco {model}")
        
        # Get specific building information
        print(f"\n🏢 BUILDING-SPECIFIC QUERIES")
        print("=" * 50)
        
        building_queries = [
            "Building A access points",
            "Building B access points", 
            "Building C access points"
        ]
        
        for query in building_queries:
            print(f"\n🔍 {query}:")
            try:
                response = query_engine.process_query(query, top_k=5)
                sources = response.get('sources', [])
                
                # Extract building-specific equipment
                building_equipment = []
                for source in sources:
                    text = source.get('text', '')
                    filename = source.get('filename', '')
                    
                    if query.split()[1].lower() in filename.lower():  # Match building
                        lines = text.split('\n')
                        equipment_lines = []
                        for line in lines:
                            if any(keyword in line.upper() for keyword in ['CISCO', 'AP MODEL', 'ANTENNA TYPE', 'MDF', 'IDF']):
                                equipment_lines.append(line.strip())
                        
                        if equipment_lines:
                            building_equipment.extend(equipment_lines)
                
                if building_equipment:
                    print(f"   ✅ Equipment found:")
                    for item in building_equipment[:10]:  # Show first 10
                        if item:
                            print(f"      • {item}")
                else:
                    print(f"   ⚠️  No specific equipment details found")
                    
            except Exception as e:
                print(f"   ❌ Query failed: {e}")
        
        # Network incident summary
        print(f"\n🚨 NETWORK INCIDENTS SUMMARY")
        print("=" * 50)
        
        try:
            incident_response = query_engine.process_query("Network incidents WiFi problems", top_k=10)
            incident_sources = incident_response.get('sources', [])
            
            network_incidents = []
            for source in incident_sources:
                text = source.get('text', '')
                if 'INC' in text and any(keyword in text.lower() for keyword in ['network', 'wifi', 'coverage', 'signal']):
                    # Extract incident ID and summary
                    lines = text.split('\n')
                    incident_info = {}
                    for line in lines:
                        if line.startswith('Incident:'):
                            incident_info['id'] = line.split(':')[1].strip()
                        elif line.startswith('Priority:'):
                            incident_info['priority'] = line.split(':')[1].strip()
                        elif line.startswith('Category:'):
                            incident_info['category'] = line.split(':')[1].strip()
                        elif line.startswith('Summary:'):
                            incident_info['summary'] = line.split(':')[1].strip()
                        elif line.startswith('Location:'):
                            incident_info['location'] = line.split(':')[1].strip()
                    
                    if incident_info:
                        network_incidents.append(incident_info)
            
            if network_incidents:
                print(f"   ✅ Found {len(network_incidents)} network-related incidents:")
                for i, incident in enumerate(network_incidents, 1):
                    print(f"   {i}. {incident.get('id', 'Unknown')} - {incident.get('priority', 'Unknown')} Priority")
                    print(f"      📍 {incident.get('location', 'Unknown location')}")
                    print(f"      📝 {incident.get('summary', 'No summary')}")
                    print(f"      🏷️  {incident.get('category', 'Unknown category')}")
                    print()
            else:
                print(f"   ⚠️  No network incidents found")
                
        except Exception as e:
            print(f"   ❌ Incident query failed: {e}")
        
        return equipment_found
        
    except Exception as e:
        print(f"❌ Network equipment query failed: {e}")
        import traceback
        traceback.print_exc()
        return {}

def main():
    """Run network equipment queries"""
    print("🌐 NETWORK EQUIPMENT QUERY SYSTEM")
    print("=" * 80)
    print("Extracting access point and network equipment information")
    print()
    
    equipment = query_network_equipment()
    
    print(f"\n📋 FINAL SUMMARY")
    print("=" * 80)
    
    if equipment:
        print("✅ Network equipment information successfully extracted")
        print(f"📊 Equipment found in {len(equipment)} building documents")
        print("🔍 The system contains Cisco access points, not traditional routers")
        print("📡 Access points provide WiFi coverage for warehouse/facility operations")
    else:
        print("⚠️  Limited network equipment details found")
        print("💡 The documents focus on WiFi coverage and signal strength rather than detailed equipment inventories")

if __name__ == "__main__":
    main() 