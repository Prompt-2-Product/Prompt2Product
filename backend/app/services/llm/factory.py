from __future__ import annotations
from app.core.config import settings
from app.services.llm.base import LLMClient
from app.services.llm.providers.ollama_client import OllamaLLM
from app.services.llm.providers.openai_compat_client import OpenAICompatLLM

def get_llm_client() -> LLMClient:
    mode = settings.LLM_MODE
    if mode == "api":
        return OpenAICompatLLM(base_url=settings.API_BASE_URL, api_key=settings.API_KEY)
    if mode == "ollama":
        return OllamaLLM(base_url=settings.OLLAMA_BASE_URL)
    raise ValueError(f"Unknown LLM_MODE: {mode}")
 