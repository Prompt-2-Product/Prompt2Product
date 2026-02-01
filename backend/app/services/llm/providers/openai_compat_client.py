from __future__ import annotations
import httpx
from app.services.llm.base import LLMClient

class OpenAICompatLLM(LLMClient):
    """
    Works with any OpenAI-compatible endpoint:
    POST {base_url}/v1/chat/completions
    """
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    async def chat(self, model: str, system: str, user: str) -> str:
        if not self.base_url or not self.api_key:
            raise RuntimeError("API_BASE_URL or API_KEY missing for LLM_MODE=api")

        url = f"{self.base_url}/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.2,
        }

        async with httpx.AsyncClient(timeout=180) as client:
            r = await client.post(url, headers=headers, json=payload)
            r.raise_for_status()
            data = r.json()
            return data["choices"][0]["message"]["content"]
