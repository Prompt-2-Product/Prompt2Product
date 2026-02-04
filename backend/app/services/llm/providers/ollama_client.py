import httpx
import sys
import json
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
        timeout: int = 1200,
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
            # Enable streaming
            native_payload = {"model": model, "messages": messages, "stream": True}
            print(f"DEBUG: Ollama Request URL: {native_url}")
            
            full_content = []
            
            try:
                async with client.stream("POST", native_url, json=native_payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            chunk = json.loads(line)
                            content = chunk.get("message", {}).get("content", "")
                            if content:
                                sys.stdout.write(content)
                                sys.stdout.flush()
                                full_content.append(content)
                        except ValueError:
                            pass
            except Exception as e:
                print(f"Stream error: {e}")
                raise e
            
            print("\n") # Newline at end
            return "".join(full_content)
 