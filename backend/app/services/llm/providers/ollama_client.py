import httpx
import sys
import json
import os
from typing import Optional, List, Dict, Any

_STREAM_TO_STDOUT = os.getenv("OLLAMA_STREAM_TO_STDOUT", "").strip().lower() in ("1", "true", "yes")

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
        max_tokens: int = 1200,
        **kwargs: Any,
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

        # Fine-tuned models (qwen-TS, qwen-code-model, etc.) are exported as
        # completion-only models with no chat template. They need /api/generate
        # with the Qwen2.5 instruct format applied manually.
        # Standard instruct models (qwen2.5:7b-instruct, qwen2.5-coder:3b) have
        # a built-in chat template and work correctly with /api/chat.
        is_finetuned = any(kw in model.lower() for kw in ["lora", "ts", "taskspec", "code-model"])

        async with httpx.AsyncClient(timeout=timeout) as client:
            if is_finetuned:
                # ─── /api/generate WITH CORRECT Qwen2.5 INSTRUCT FORMAT ───
                native_url = f"{self.base_url}/api/generate"
                sys_prompt = ""
                usr_prompt = ""
                for msg in messages:
                    role = msg.get("role", "")
                    if role == "system":
                        sys_prompt = msg.get("content", "")
                    elif role == "user":
                        usr_prompt = msg.get("content", "")
                raw_prompt = (
                    f"<|im_start|>system\n{sys_prompt}<|im_end|>\n"
                    f"<|im_start|>user\n{usr_prompt}<|im_end|>\n"
                    f"<|im_start|>assistant\n"
                )
                native_payload = {
                    "model": model,
                    "prompt": raw_prompt,
                    "stream": True,
                    "options": {"num_predict": max_tokens},
                }
            else:
                # ─── /api/chat FOR STANDARD INSTRUCT MODELS ───
                native_url = f"{self.base_url}/api/chat"
                native_payload = {
                    "model": model,
                    "messages": messages,
                    "stream": True,
                    "options": {"num_predict": max_tokens},
                }

            print(f"DEBUG: Ollama Request URL: {native_url}")
            print(f"DEBUG: Ollama Model: {model}")

            full_content = []

            try:
                async with client.stream("POST", native_url, json=native_payload) as response:
                    if response.status_code != 200:
                        body = await response.aread()
                        print(f"DEBUG: Ollama Error Response ({response.status_code}): {body.decode()}")
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            chunk = json.loads(line)
                            if is_finetuned:
                                content = chunk.get("response", "")
                            else:
                                content = chunk.get("message", {}).get("content", "")
                            if content:
                                if _STREAM_TO_STDOUT:
                                    sys.stdout.write(content)
                                    sys.stdout.flush()
                                full_content.append(content)
                        except ValueError:
                            pass
            except Exception as e:
                print(f"Stream error: {e}")
                raise e

            print("\n")  # Newline at end

            final_text = "".join(full_content)
            print(f"DEBUG: Raw model output ({len(final_text)} chars): {repr(final_text[:500])}")
            for marker in ["<|im_start|>", "<|im_end|>", "<|endoftext|>", "User:", "Assistant:"]:
                pos = final_text.find(marker)
                if pos != -1:
                    final_text = final_text[:pos]

            return final_text.strip()
 