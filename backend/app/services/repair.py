from __future__ import annotations
from app.services.llm.base import LLMClient

SYSTEM_REPAIR = """You are a code repair agent.
Given runtime errors and file context, output ONLY a unified diff patch.

Rules:
- Output ONLY patch text (no markdown).
- Use file paths exactly as provided.
- Make minimal changes to fix the error.
- If missing dependency, update generated_app/backend/requirements.txt.
"""

async def llm_repair(llm: LLMClient, model: str, error_text: str, context: str) -> str:
    user = f"ERROR:\n{error_text}\n\nCONTEXT:\n{context}\n\nReturn ONLY unified diff patch."
    return await llm.chat(model=model, system=SYSTEM_REPAIR, user=user)
