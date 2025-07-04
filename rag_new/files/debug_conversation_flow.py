#!/usr/bin/env python3
"""
Debug Conversation Flow
Trace the exact execution flow to see why LLM-based context awareness isn't working
"""
import sys
from pathlib import Path

# Add rag_system/src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "rag_system"))

def debug_conversation_flow():
    """Debug the conversation flow step by step"""
    print("DEBUGGING CONVERSATION FLOW")
    print("=" * 60)
    
    try:
        # Import required modules
        from core.dependency_container import DependencyContainer, register_core_services
        from conversation.conversation_nodes import ConversationNodes
        from conversation.conversation_state import create_conversation_state, add_message_to_state, MessageType
        
        print("Modules imported successfully")
        
        # Create container and register services
        container = DependencyContainer()
        register_core_services(container)
        print("✅ Core services registered")
        
        # Test LLM client access
        llm_client = container.get('llm_client')
        print(f"🔧 LLM Client: {llm_client}")
        print(f"🔧 LLM Client provider: {llm_client.provider if llm_client else 'None'}")
        
        # Test LLM client directly
        print("\n🧪 TESTING LLM CLIENT DIRECTLY")
        print("-" * 50)
        try:
            direct_response = llm_client.generate("Test prompt", max_tokens=50)
            print(f"✅ Direct LLM call works: {direct_response[:100]}...")
        except Exception as e:
            print(f"❌ Direct LLM call failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Create conversation nodes
        print("\n🔧 Creating conversation nodes...")
        nodes = ConversationNodes(container)
        print(f"✅ Conversation nodes created")
        print(f"🔧 Nodes LLM client: {nodes.llm_client}")
        print(f"🔧 Nodes LLM client provider: {nodes.llm_client.provider if nodes.llm_client else 'None'}")
        
        # Create conversation state with context
        print("\n🔧 Creating conversation state...")
        state = create_conversation_state()
        
        # Add initial message with document count
        state = add_message_to_state(state, MessageType.USER, "How many tickets in the system")
        state = add_message_to_state(state, MessageType.ASSISTANT, """Document statistics:

Total documents: 5

• Change: 0 (0.0%)
• Incident: 5 (100.0%)
• Problem: 0 (0.0%)
• Request: 0 (0.0%)
• Task: 0 (0.0%)""")
        
        print("✅ Conversation state created with context")
        print(f"🔧 Message count: {len(state['messages'])}")
        
        # Add follow-up question
        state = add_message_to_state(state, MessageType.USER, "which are these?")
        state['original_query'] = "which are these?"
        state['processed_query'] = "which are these?"
        state['search_results'] = []  # No search results to force general response
        
        print("\n🧪 TESTING FOLLOW-UP DETECTION DETAILED")
        print("-" * 50)
        
        # Test _is_simple_followup_question method directly with more detail
        conversation_history = state.get('messages', [])
        query = "which are these?"
        
        print(f"🔧 Query: '{query}'")
        print(f"🔧 Conversation history length: {len(conversation_history)}")
        
        # Let's manually test the LLM call in the _is_simple_followup_question method
        recent_messages = conversation_history[-4:] if conversation_history else []
        context = ""
        
        for msg in recent_messages:
            role = "User" if msg.get('type') == MessageType.USER else "Assistant"
            content = msg.get('content', '')[:200]  # Truncate for context
            context += f"{role}: {content}\n"
        
        print(f"🔧 Context for LLM: {context[:300]}...")
        
        prompt = f"""Analyze this conversation to determine if the latest user query is a simple follow-up question that should get a concise, direct answer.

Recent Conversation:
{context}

Latest User Query: "{query}"

A simple follow-up question is one that:
- Asks for clarification about something just mentioned (like "which are these?", "what are those?")
- Requests a simple list or enumeration ("list them", "show me those", "name them")
- Asks for basic identification without detailed analysis
- Is clearly referencing something from the immediate conversation context

Answer with just: YES or NO

Analysis:"""
        
        print(f"🔧 Prompt length: {len(prompt)} chars")
        
        # Test the LLM call directly
        try:
            print("🔧 Testing LLM call for follow-up detection...")
            if nodes.llm_client:
                llm_response = nodes.llm_client.generate(prompt, max_tokens=10, temperature=0.1)
                print(f"✅ LLM Response: '{llm_response}'")
                print(f"🔧 Response stripped and upper: '{llm_response.strip().upper()}'")
                is_yes = llm_response.strip().upper() == "YES"
                print(f"🔧 Equals 'YES': {is_yes}")
            else:
                print("❌ No LLM client in nodes")
        except Exception as e:
            print(f"❌ LLM call failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Test the actual method
        print("\n🔧 Testing actual _is_simple_followup_question method...")
        is_followup = nodes._is_simple_followup_question(query, conversation_history)
        print(f"🔧 Method result: {is_followup}")
        
        # Test the LLM-based context response manually
        print("\n🧪 TESTING LLM-BASED CONTEXT RESPONSE")
        print("-" * 50)
        
        if is_followup and conversation_history:
            # Try to replicate the exact LLM call from _generate_general_response
            recent_context = ""
            for msg in conversation_history[-4:]:
                role = "User" if msg.get('type') == MessageType.USER else "Assistant"
                content = msg.get('content', '')[:300]
                recent_context += f"{role}: {content}\n"
            
            prompt = f"""The user is asking a follow-up question but no search results were found. Try to answer based on the recent conversation context.

Recent Conversation:
{recent_context}

Current Question: "{query}"

Instructions:
1. If the conversation context contains relevant information to answer the question, provide a direct answer
2. If you can identify what "these", "those", "them" refers to from the context, list those items
3. If the context mentions numbers (like "5 documents"), try to identify what those items are
4. Be concise and direct
5. If you truly cannot answer from context, acknowledge this politely

Provide a helpful response:"""
            
            print(f"🔧 Prompt length: {len(prompt)} chars")
            print(f"🔧 Recent context: {recent_context[:200]}...")
            
            try:
                print("🔧 Calling LLM with context prompt...")
                if nodes.llm_client:
                    llm_response = nodes.llm_client.generate(prompt, max_tokens=300, temperature=0.1)
                    print(f"✅ LLM Context Response: {llm_response}")
                    print(f"🔧 Response length: {len(llm_response)} chars")
                    
                    # Check if this is a generic response
                    is_generic = "I don't have specific information readily available" in llm_response
                    print(f"🔧 Is generic: {is_generic}")
                    
                    if not is_generic:
                        print("🎯 SUCCESS: LLM generated contextual response!")
                        return True
                else:
                    print("❌ No LLM client available")
                    
            except Exception as e:
                print(f"❌ LLM context call failed: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"❌ Skipping context response test - is_followup: {is_followup}, has_history: {bool(conversation_history)}")
        
        # Test _generate_general_response directly
        print("\n🧪 TESTING GENERAL RESPONSE GENERATION")
        print("-" * 50)
        
        print("🔧 Calling _generate_general_response...")
        response = nodes._generate_general_response(state)
        print(f"✅ Response generated ({len(response)} chars)")
        print(f"📋 Response: {response[:200]}...")
        
        # Check if response is generic or contextual
        is_generic = "I don't have specific information readily available" in response
        print(f"🔧 Is generic response: {is_generic}")
        
        return not is_generic
        
    except Exception as e:
        print(f"❌ Error in debug: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = debug_conversation_flow()
    if success:
        print("\n🎯 DEBUG: Context awareness is working!")
    else:
        print("\n💥 DEBUG: Context awareness is not working") 