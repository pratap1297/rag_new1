#!/usr/bin/env python3
"""
Test script to check Groq API key validity and troubleshoot issues
"""

import os
import sys
from pathlib import Path

# Add the rag_system to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "rag_system" / "src"))

def load_env_file():
    """Load environment variables from .env file"""
    env_file = project_root / "rag_system" / ".env"
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        print(f"✅ Loaded environment from: {env_file}")
    else:
        print(f"❌ .env file not found: {env_file}")

def check_groq_api_key():
    """Check if Groq API key is valid"""
    print("\n🔑 Checking Groq API Key")
    print("=" * 50)
    
    # Load environment
    load_env_file()
    
    groq_api_key = os.getenv('GROQ_API_KEY')
    
    if not groq_api_key:
        print("❌ GROQ_API_KEY not found in environment")
        return False
    
    print(f"✅ API Key found: {groq_api_key[:10]}...{groq_api_key[-10:]}")
    print(f"📏 Length: {len(groq_api_key)} characters")
    
    # Check format
    if not groq_api_key.startswith('gsk_'):
        print("⚠️  API key doesn't start with 'gsk_' - might be invalid")
        return False
    
    if len(groq_api_key) < 50:
        print("⚠️  API key seems too short")
        return False
    
    print("✅ API key format looks valid")
    return True

def test_groq_connection():
    """Test Groq API connection"""
    print("\n🤖 Testing Groq API Connection")
    print("=" * 50)
    
    try:
        # Import groq
        import groq
        print("✅ Groq package imported successfully")
        
        # Get API key
        groq_api_key = os.getenv('GROQ_API_KEY')
        if not groq_api_key:
            print("❌ No API key available")
            return False
        
        # Create client
        client = groq.Groq(api_key=groq_api_key)
        print("✅ Groq client created")
        
        # Test simple request
        print("🚀 Testing simple request...")
        response = client.chat.completions.create(
            model="meta-llama/llama-4-maverick-17b-128e-instruct",
            messages=[{"role": "user", "content": "Say hello"}],
            max_tokens=10,
            temperature=0.1
        )
        
        result = response.choices[0].message.content
        print(f"✅ Groq API working! Response: {result}")
        return True
        
    except ImportError:
        print("❌ Groq package not installed")
        print("💡 Install with: pip install groq")
        return False
    except Exception as e:
        error_str = str(e)
        print(f"❌ Groq API test failed: {e}")
        
        # Analyze error
        if "invalid_api_key" in error_str.lower() or "401" in error_str:
            print("\n🔑 API KEY ISSUE DETECTED!")
            print("📋 Possible solutions:")
            print("1. Check if your API key is correct")
            print("2. Verify your Groq account is active")
            print("3. Check if the API key has expired")
            print("4. Try regenerating the API key at https://console.groq.com")
            
        elif "503" in error_str or "service unavailable" in error_str.lower():
            print("\n🚨 GROQ SERVICE UNAVAILABLE!")
            print("📋 This is a temporary Groq server issue:")
            print("1. Wait a few minutes and try again")
            print("2. Check Groq status at https://status.groq.com")
            print("3. Consider switching to Azure LLM temporarily")
            
        elif "429" in error_str or "rate limit" in error_str.lower():
            print("\n⏰ RATE LIMIT EXCEEDED!")
            print("📋 Solutions:")
            print("1. Wait before making more requests")
            print("2. Upgrade your Groq plan for higher limits")
            
        elif "timeout" in error_str.lower():
            print("\n⏰ TIMEOUT ISSUE!")
            print("📋 Solutions:")
            print("1. Check your internet connection")
            print("2. Try again in a few minutes")
            
        return False

def suggest_alternatives():
    """Suggest alternative LLM providers"""
    print("\n🔄 Alternative LLM Providers")
    print("=" * 50)
    
    print("If Groq is having issues, you can switch to:")
    print()
    print("1. 🔵 Azure AI (Already configured)")
    print("   - Update system_config.json: 'provider': 'azure'")
    print("   - Your Azure keys are already in .env")
    print("   - Model: Llama-4-Maverick-17B-128E-Instruct-FP8")
    print()
    print("2. 🟢 OpenAI (If you have API key)")
    print("   - Add OPENAI_API_KEY to .env")
    print("   - Update system_config.json: 'provider': 'openai'")
    print("   - Model: gpt-3.5-turbo or gpt-4")
    print()
    print("3. 🟡 Cohere (If you have API key)")
    print("   - Add COHERE_API_KEY to .env")
    print("   - Update system_config.json: 'provider': 'cohere'")

def fix_groq_config():
    """Provide steps to fix Groq configuration"""
    print("\n🔧 How to Fix Groq Configuration")
    print("=" * 50)
    
    print("1. 🔑 Get a new Groq API key:")
    print("   - Go to https://console.groq.com")
    print("   - Sign in to your account")
    print("   - Navigate to 'API Keys' section")
    print("   - Create a new API key")
    print("   - Copy the key (starts with 'gsk_')")
    print()
    print("2. 📝 Update your .env file:")
    print("   - Edit rag_system/.env")
    print("   - Replace the GROQ_API_KEY line with your new key")
    print("   - Save the file")
    print()
    print("3. 🔄 Restart your system:")
    print("   - Stop the current RAG system")
    print("   - Start it again to load the new key")
    print()
    print("4. ✅ Test the connection:")
    print("   - Run this script again to verify")

def main():
    """Run all tests and provide guidance"""
    print("🚀 Groq API Key Troubleshooting Tool")
    print("=" * 60)
    
    # Check API key format
    key_valid = check_groq_api_key()
    
    if key_valid:
        # Test connection
        connection_ok = test_groq_connection()
        
        if connection_ok:
            print("\n🎉 SUCCESS! Groq is working correctly")
        else:
            print("\n❌ Groq API issues detected")
            suggest_alternatives()
            fix_groq_config()
    else:
        print("\n❌ API key issues detected")
        fix_groq_config()
    
    print("\n" + "=" * 60)
    print("📋 SUMMARY")
    print("=" * 60)
    
    if key_valid:
        print("✅ API key format is valid")
        print("⚠️  But connection issues detected")
        print("💡 This is likely a temporary Groq server issue")
        print("🔄 Try again in a few minutes or switch to Azure")
    else:
        print("❌ API key needs to be fixed")
        print("🔑 Get a new key from https://console.groq.com")
        print("📝 Update your .env file")

if __name__ == "__main__":
    main() 