#!/usr/bin/env python3
"""
Test Router Information Query
Specific test to find router information from ingested network layout documents
"""
import sys
from pathlib import Path

# Add the rag_system to Python path
sys.path.insert(0, str(Path(__file__).parent / "rag_system" / "src"))

def search_for_routers():
    """Search for router information in the ingested documents"""
    print("🔍 SEARCHING FOR ROUTER INFORMATION")
    print("=" * 60)
    
    try:
        from core.dependency_container import DependencyContainer
        from core.dependency_container import register_core_services
        
        container = DependencyContainer()
        register_core_services(container)
        
        query_engine = container.get('query_engine')
        vector_store = container.get('vector_store')
        
        # Check what data we have
        print("📊 System Data Check:")
        if hasattr(vector_store, 'get_collection_info'):
            info = vector_store.get_collection_info()
            print(f"   Total documents: {info.get('points_count', 0)}")
        
        # Test router-specific queries
        router_queries = [
            "how many routers in system",
            "what type of routers",
            "router information",
            "network routers",
            "router models",
            "show me all routers",
            "router configuration",
            "network equipment routers"
        ]
        
        print(f"\n🔍 Testing router-specific queries:")
        
        for i, query in enumerate(router_queries, 1):
            print(f"\n--- Query {i}: '{query}' ---")
            
            try:
                response = query_engine.process_query(query, top_k=20)
                
                print(f"✅ Response received")
                print(f"   Sources: {len(response.get('sources', []))}")
                print(f"   Method: {response.get('method', 'unknown')}")
                
                # Show response
                response_text = response.get('response', '')
                if response_text and len(response_text) > 10:
                    print(f"   📝 Response: {response_text}")
                else:
                    print(f"   📝 Response: (empty or very short)")
                
                # Show relevant sources with router information
                sources = response.get('sources', [])
                if sources:
                    print(f"   📄 Checking {len(sources)} sources for router info:")
                    router_found = False
                    
                    for j, source in enumerate(sources[:10], 1):
                        source_text = source.get('text', '').lower()
                        filename = source.get('filename', 'Unknown')
                        
                        # Look for router-related keywords
                        router_keywords = ['router', 'gateway', 'switch', 'network device', 'access point']
                        found_keywords = [kw for kw in router_keywords if kw in source_text]
                        
                        if found_keywords:
                            print(f"      ✅ Source {j} ({filename}): Found {found_keywords}")
                            # Show relevant excerpt
                            text_preview = source.get('text', '')[:200] + "..." if len(source.get('text', '')) > 200 else source.get('text', '')
                            print(f"         Text: {text_preview}")
                            router_found = True
                        elif 'network' in source_text or 'building' in source_text:
                            print(f"      📋 Source {j} ({filename}): Network/building related")
                    
                    if not router_found:
                        print(f"      ⚠️  No explicit router information found in sources")
                
            except Exception as e:
                print(f"❌ Query failed: {e}")
        
        # Try direct search in documents
        print(f"\n🔍 Direct Document Search:")
        try:
            # Search for router patterns directly
            if hasattr(vector_store, 'get_by_pattern'):
                router_docs = vector_store.get_by_pattern('router')
                print(f"✅ Pattern search 'router': {len(router_docs)} documents")
                
                for doc in router_docs[:3]:
                    text = doc.get('text', '')[:300] + "..." if len(doc.get('text', '')) > 300 else doc.get('text', '')
                    print(f"   📄 {text}")
                
                # Try other network terms
                network_docs = vector_store.get_by_pattern('network')
                print(f"✅ Pattern search 'network': {len(network_docs)} documents")
                
                equipment_docs = vector_store.get_by_pattern('equipment')
                print(f"✅ Pattern search 'equipment': {len(equipment_docs)} documents")
                
        except Exception as e:
            print(f"❌ Direct search failed: {e}")
        
        # Check raw document content
        print(f"\n📄 Raw Document Analysis:")
        try:
            # Get all metadata to see what we actually have
            if hasattr(vector_store, 'id_to_metadata'):
                all_metadata = vector_store.id_to_metadata
                print(f"✅ Found {len(all_metadata)} document chunks")
                
                router_content = []
                for doc_id, metadata in list(all_metadata.items())[:10]:  # Check first 10
                    text = metadata.get('text', '').lower()
                    filename = metadata.get('filename', 'Unknown')
                    
                    if any(keyword in text for keyword in ['router', 'gateway', 'switch', 'network device']):
                        router_content.append({
                            'filename': filename,
                            'text': metadata.get('text', '')[:400] + "..." if len(metadata.get('text', '')) > 400 else metadata.get('text', '')
                        })
                
                if router_content:
                    print(f"✅ Found {len(router_content)} chunks with router-related content:")
                    for content in router_content:
                        print(f"   📄 {content['filename']}:")
                        print(f"      {content['text']}")
                else:
                    print(f"⚠️  No router-related content found in first 10 documents")
                    print(f"   Let's check what content we do have:")
                    for i, (doc_id, metadata) in enumerate(list(all_metadata.items())[:5], 1):
                        filename = metadata.get('filename', 'Unknown')
                        text_preview = metadata.get('text', '')[:200] + "..." if len(metadata.get('text', '')) > 200 else metadata.get('text', '')
                        print(f"   📄 Document {i} ({filename}): {text_preview}")
                        
        except Exception as e:
            print(f"❌ Raw document analysis failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Router search failed: {e}")
        return False

def main():
    """Run router information search"""
    print("🔍 ROUTER INFORMATION SEARCH TEST")
    print("=" * 80)
    print("Searching for router information in network layout documents")
    print()
    
    success = search_for_routers()
    
    print(f"\n📋 ANALYSIS COMPLETE")
    print("=" * 80)
    
    if success:
        print("✅ Search completed successfully")
        print("📝 Check the output above for router information")
        print("💡 If no router info found, the documents may not contain specific router details")
    else:
        print("❌ Search encountered issues")

if __name__ == "__main__":
    main() 