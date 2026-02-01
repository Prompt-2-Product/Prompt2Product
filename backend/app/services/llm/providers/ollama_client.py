from __future__ import annotations
import httpx
from app.services.llm.base import LLMClient

class OllamaLLM(LLMClient):
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    async def chat(self, model: str, system: str, user: str) -> str:
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
        }
        async with httpx.AsyncClient(timeout=180) as client:
            r = await client.post(url, json=payload)
            r.raise_for_status()
            return r.json()["message"]["content"]
