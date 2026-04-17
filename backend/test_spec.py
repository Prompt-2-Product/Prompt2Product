import asyncio
import sys
from app.services.llm.providers.ollama_client import OllamaLLM

async def test():
    llm = OllamaLLM("http://127.0.0.1:11435")
    print("Sending request to qwen-TS...")
    try:
        raw = await llm.chat(
            model="qwen-TS", 
            system="Generate valid TaskSpec JSON only. Do not output markdown, comments, or explanation.", 
            user="Build a weather app", 
            max_tokens=4096
        )
        print(f"\n\n================ RAW RESPONSE ================\n{repr(raw)}")
    except Exception as e:
        print("Failed:", e)

if __name__ == "__main__":
    asyncio.run(test())
