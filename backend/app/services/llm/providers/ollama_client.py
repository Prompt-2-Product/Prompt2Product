import httpx
from typing import Optional, List, Dict, Any

class OllamaLLM:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    async def chat(
        self,
        model: str,
        messages: Optional[List[Dict[str, Any]]] = None,
        system: Optional[str] = None,
        user: Optional[str] = None,
        timeout: int = 300,
    ) -> str:
        """
        Supports two calling styles:
          A) chat(model=..., messages=[...], system="...")
          B) chat(model=..., system="...", user="...")
        """
        # Build messages if caller used user/system style
        if messages is None:
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            if user:
                messages.append({"role": "user", "content": user})
        else:
            # Prepend system prompt if provided separately
            if system:
                messages = [{"role": "system", "content": system}] + list(messages)

        async with httpx.AsyncClient(timeout=timeout) as client:
            # 1) Try Ollama native endpoint
            native_url = f"{self.base_url}/api/chat"
            native_payload = {"model": model, "messages": messages, "stream": False}
            print(f"DEBUG: Ollama Request URL: {native_url}")
            print(f"DEBUG: Ollama Request Payload: {native_payload}")
            r = await client.post(native_url, json=native_payload)

            r = await client.post(native_url, json=native_payload)
            r.raise_for_status()
            data = r.json()
            return data["message"]["content"]
