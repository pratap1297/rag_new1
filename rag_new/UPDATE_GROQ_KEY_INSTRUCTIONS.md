# How to Fix the Groq API Key Issue

## 🚨 Problem
Your Groq API key is invalid (401 error). The system cannot connect to Groq.

## 🔧 Solution 1: Update Groq API Key

### Step 1: Get New API Key
1. Go to https://console.groq.com
2. Sign in (or create free account)
3. Navigate to "API Keys" section
4. Click "Create API Key"
5. Copy the new key (starts with `gsk_`)

### Step 2: Update .env File
Edit `rag_new/rag_system/.env` and replace this line:
```
GROQ_API_KEY=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
```

With your new key:
```
GROQ_API_KEY=gsk_YOUR_NEW_KEY_HERE
```

### Step 3: Restart System
Stop and restart your RAG system to load the new key.

## 🔄 Solution 2: Switch to Azure (Temporary)

If you want to continue immediately, switch to Azure LLM:

### Update system_config.json
Edit `rag_new/data/config/system_config.json`:

Change:
```json
"llm": {
    "provider": "groq",
    "model_name": "meta-llama/llama-4-maverick-17b-128e-instruct"
}
```

To:
```json
"llm": {
    "provider": "azure", 
    "model_name": "Llama-4-Maverick-17B-128E-Instruct-FP8"
}
```

Your Azure keys are already configured and working.

## ✅ Test Commands

After fixing, test with:
```bash
python -c "
import os
os.environ['GROQ_API_KEY'] = 'your_new_key_here'
import groq
client = groq.Groq()
response = client.chat.completions.create(
    model='meta-llama/llama-4-maverick-17b-128e-instruct',
    messages=[{'role': 'user', 'content': 'Hello'}],
    max_tokens=5
)
print('✅ Working:', response.choices[0].message.content)
"
```

## 💡 Why This Happened

- Groq API keys can expire
- Free tier keys have limitations
- Keys might be revoked if not used

## 🎯 Recommendation

**Use Azure LLM for now** since your Azure keys are working, then get a new Groq key when convenient. Azure Llama model performs just as well as Groq! 