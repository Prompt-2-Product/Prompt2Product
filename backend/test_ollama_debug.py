import httpx
import asyncio
import os

from dotenv import load_dotenv

# Force reload of .env
load_dotenv(override=True)

MODEL = os.getenv("MODEL_SPEC", "llama3.1:8b")
BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")

async def test_ollama():
    print(f"Testing Ollama at {BASE_URL} with model {MODEL}")
    
    url = f"{BASE_URL}/api/chat"
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": "Hello"}],
        "stream": False
    }
    
    print(f"Sending payload: {payload}")
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, json=payload)
            print(f"Status Code: {resp.status_code}")
            print(f"Response Body: {resp.text}")
            resp.raise_for_status()
            print("Success!")
    except Exception:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ollama())
