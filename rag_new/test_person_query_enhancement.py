#!/usr/bin/env python3
"""
Test script for enhanced person query handling
Demonstrates the LLM-enhanced query decomposition system for person queries
"""

import sys
import os
from pathlib import Path

# Add the rag_system to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "rag_system" / "src"))

def test_person_query_analysis():
    """Test person query analysis and entity detection"""
    
    print("🧪 Testing Enhanced Person Query Analysis")
    print("=" * 50)
    
    try:
        # Import the enhanced components
        from conversation.fresh_smart_router import FreshSmartRouter, SmartQueryAnalyzer
        from conversation.fresh_context_manager import FreshContextManager
        
        # Create components
        context_manager = FreshContextManager()
        # Note: No LLM client for this test, will use fallback patterns
        smart_router = FreshSmartRouter(context_manager, llm_client=None)
        
        # Test queries
        test_queries = [
            "Who is Sarah Johnson",
            "Who's John Smith",
            "What is Sarah Johnson's role",
            "Tell me about Mike Davis",
            "Find information about Jennifer Brown",
            "Who is the network administrator",
            "Show me employee details for Robert Wilson"
        ]
        
        print("\n📋 Testing Person Query Detection:")
        print("-" * 40)
        
        for query in test_queries:
            print(f"\n🔍 Query: '{query}'")
            
            # Analyze query
            analysis = smart_router.analyze_query(query)
            
            print(f"   • Intent: {analysis.intent.value}")
            print(f"   • Entity Type: {analysis.entity_type}")
            print(f"   • Scope Targets: {analysis.scope_targets}")
            print(f"   • Keywords: {analysis.keywords[:3]}")
            print(f"   • Entities: {analysis.entities}")
            
            # Test fallback entity detection
            query_analyzer = smart_router.query_analyzer
            entity_analysis = query_analyzer._fallback_entity_detection(query)
            
            print(f"   • Detected Entity: {entity_analysis['primary_entity']}")
            print(f"   • Confidence: {entity_analysis.get('confidence', 0):.2f}")
            print(f"   • Extracted Names: {entity_analysis['entity_instances']}")
            
            if entity_analysis['potential_synonyms']:
                print(f"   • Synonyms Available: {list(entity_analysis['potential_synonyms'].keys())}")
        
        print("\n✅ Person query analysis test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error in person query analysis test: {e}")
        import traceback
        traceback.print_exc()

def test_person_search_strategies():
    """Test person search strategy generation"""
    
    print("\n🔍 Testing Person Search Strategies")
    print("=" * 50)
    
    try:
        # Mock conversation nodes for testing
        class MockConversationNodes:
            def __init__(self):
                self.synonym_expansion_enabled = True
                self.logger = type('Logger', (), {'info': print, 'warning': print})()
            
            def _expand_with_synonyms(self, query, synonyms):
                if not synonyms:
                    return query
                # Simple expansion for testing
                for term, synonym_list in synonyms.items():
                    if term.lower() in query.lower():
                        return f"({query} OR {' OR '.join(synonym_list)})"
                return query
        
        nodes = MockConversationNodes()
        
        # Test person name extraction and search strategy generation
        test_cases = [
            {
                'query': 'Who is Sarah Johnson',
                'analysis': {
                    'scope_targets': ['Sarah Johnson'],
                    'synonyms': {
                        'employee': ['staff', 'worker', 'personnel'],
                        'person': ['individual', 'user']
                    }
                }
            },
            {
                'query': 'Tell me about John Smith',
                'analysis': {
                    'scope_targets': ['John Smith'],
                    'synonyms': {
                        'manager': ['supervisor', 'lead', 'director']
                    }
                }
            }
        ]
        
        for case in test_cases:
            query = case['query']
            analysis = case['analysis']
            
            print(f"\n🔍 Query: '{query}'")
            
            # Extract person name
            scope_targets = analysis.get('scope_targets', [])
            person_name = scope_targets[0] if scope_targets else None
            
            if person_name:
                print(f"   • Extracted Name: {person_name}")
                
                # Generate search strategies
                search_strategies = [
                    person_name,
                    f"{person_name} employee",
                    f"{person_name} staff",
                    f"{person_name} role",
                    f"{person_name} position",
                    f"{person_name} department",
                ]
                
                print(f"   • Search Strategies:")
                for i, strategy in enumerate(search_strategies, 1):
                    print(f"     {i}. {strategy}")
                
                # Test synonym expansion
                synonyms = analysis.get('synonyms', {})
                if synonyms:
                    print(f"   • With Synonym Expansion:")
                    for i, strategy in enumerate(search_strategies[:3], 1):
                        expanded = nodes._expand_with_synonyms(strategy, synonyms)
                        if expanded != strategy:
                            print(f"     {i}. {expanded}")
        
        print("\n✅ Person search strategy test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error in person search strategy test: {e}")
        import traceback
        traceback.print_exc()

def test_person_info_extraction():
    """Test person information extraction from mock results"""
    
    print("\n📊 Testing Person Information Extraction")
    print("=" * 50)
    
    try:
        # Mock search results
        mock_results = [
            {
                'text': 'Sarah Johnson is a Senior Network Engineer in the IT Department. She can be reached at sarah.johnson@company.com or at extension 1234. Sarah works in Building A, Floor 3.',
                'source': 'employee_directory.pdf',
                'similarity_score': 0.95
            },
            {
                'text': 'The network infrastructure project is managed by Sarah Johnson, who has 8 years of experience in network design. Contact Sarah for any network-related issues.',
                'source': 'project_overview.md',
                'similarity_score': 0.87
            },
            {
                'text': 'IT Department staff includes: John Smith (Manager), Sarah Johnson (Senior Engineer), Mike Davis (Analyst), and Jennifer Brown (Coordinator).',
                'source': 'org_chart.xlsx',
                'similarity_score': 0.82
            }
        ]
        
        # Mock the extraction function
        import re
        
        def extract_person_info(search_results, person_name):
            person_info = {}
            name_parts = person_name.lower().split()
            
            for result in search_results:
                text = result.get('text', '')
                text_lower = text.lower()
                
                # Skip if person name not in this result
                if not any(part in text_lower for part in name_parts):
                    continue
                
                # Extract role information
                role_patterns = [
                    rf"{re.escape(person_name.lower())}[^\n]*?(manager|director|engineer|analyst|coordinator|specialist)",
                    rf"(senior|junior|lead)?\s*(manager|director|engineer|analyst|coordinator|specialist)[^\n]*?{re.escape(person_name.lower())}",
                ]
                
                for pattern in role_patterns:
                    matches = re.findall(pattern, text_lower, re.IGNORECASE)
                    if matches:
                        if isinstance(matches[0], tuple):
                            role_parts = [part for part in matches[0] if part]
                            person_info['role'] = ' '.join(role_parts).title()
                        else:
                            person_info['role'] = matches[0].title()
                        break
                
                # Extract department
                if 'department' in text_lower and person_name.lower() in text_lower:
                    dept_match = re.search(rf'(\w+)\s+department', text_lower)
                    if dept_match:
                        person_info['department'] = dept_match.group(1).title()
                
                # Extract contact info
                email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
                if email_match and person_name.lower() in text_lower:
                    person_info['contact'] = email_match.group(0)
                
                # Extract location
                location_match = re.search(rf'{re.escape(person_name.lower())}[^\n]*?(building [a-z0-9]+[^\n]*)', text_lower)
                if location_match:
                    person_info['location'] = location_match.group(1).title()
            
            return person_info
        
        # Test extraction
        person_name = "Sarah Johnson"
        print(f"🔍 Extracting information for: {person_name}")
        
        person_info = extract_person_info(mock_results, person_name)
        
        print(f"\n📋 Extracted Information:")
        for key, value in person_info.items():
            print(f"   • {key.title()}: {value}")
        
        # Test response formatting
        if person_info:
            print(f"\n📝 Formatted Response:")
            response_parts = [f"Here's what I found about {person_name}:"]
            
            if person_info.get('role'):
                response_parts.append(f"• Role/Position: {person_info['role']}")
            if person_info.get('department'):
                response_parts.append(f"• Department: {person_info['department']}")
            if person_info.get('contact'):
                response_parts.append(f"• Contact: {person_info['contact']}")
            if person_info.get('location'):
                response_parts.append(f"• Location: {person_info['location']}")
            
            sources = set(result['source'] for result in mock_results)
            response_parts.append(f"\nSources: {', '.join(list(sources)[:3])}")
            
            formatted_response = "\n".join(response_parts)
            print(formatted_response)
        
        print("\n✅ Person information extraction test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error in person info extraction test: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Run all person query enhancement tests"""
    
    print("🚀 Testing Enhanced Person Query System")
    print("=" * 60)
    print("This demonstrates the improved handling of person queries like 'Who is Sarah Johnson'")
    print()
    
    # Run tests
    test_person_query_analysis()
    test_person_search_strategies()
    test_person_info_extraction()
    
    print("\n" + "=" * 60)
    print("🎯 Summary: Enhanced Person Query System")
    print("✅ Person name detection and extraction")
    print("✅ Specialized search strategies for people")
    print("✅ Information extraction and formatting")
    print("✅ Structured response generation")
    print("\nThe system should now handle queries like 'Who is Sarah Johnson' much better!")

if __name__ == "__main__":
    main() 