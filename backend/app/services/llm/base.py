from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any

class LLMClient(ABC):
    """
    Common interface for any LLM provider (local or API).
    """
    @abstractmethod
    async def chat(self, model: str, system: str, user: str, **kwargs: Any) -> str:
        raise NotImplementedError
