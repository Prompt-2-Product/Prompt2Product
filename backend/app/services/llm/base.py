from __future__ import annotations
from abc import ABC, abstractmethod

class LLMClient(ABC):
    """
    Common interface for any LLM provider (local or API).
    """
    @abstractmethod
    async def chat(self, model: str, system: str, user: str) -> str:
        raise NotImplementedError
