import asyncio
import sys
import os

# Set up paths
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from backend.app.services.llm.providers.ollama_client import OllamaLLM

async def test():
    # Use the URL from .env
    base_url = "http://127.0.0.1:11435"
    model = "qwen2.5:7b-instruct"
    print(f"Testing Ollama at {base_url} with model {model}...")
    
    llm = OllamaLLM(base_url=base_url)
    try:
        # Use a short timeout for the test to see if it fails fast
        res = await llm.chat(
            model=model, 
            system="You are a helpful assistant.", 
            user="Say 'Ollama is alive' and nothing else.", 
            timeout=30
        )
        print("--- Response ---")
        print(res)
        print("----------------")
    except Exception as e:
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {e}")

if __name__ == "__main__":
    asyncio.run(test())
