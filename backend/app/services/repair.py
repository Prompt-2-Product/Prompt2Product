from __future__ import annotations
from app.services.llm.base import LLMClient

SYSTEM_REPAIR = """You are a code repair agent.
Given runtime errors and file context, output a patch to fix the code.

Rules:
1. Start output with: *** Begin Patch
2. For each file to change, start with: *** Update File: [PATH]
   - [PATH] MUST be the exact relative path shown in the context header.
3. Then output the NEW CONTENT of the file (complete file), prefixed with: +++ REPLACE ENTIRE FILE +++
4. End output with: *** End Patch

Example:
*** Begin Patch
*** Update File: generated_app/backend/main.py
+++ REPLACE ENTIRE FILE +++
from fastapi import FastAPI
...
*** End Patch
"""

async def llm_repair(llm: LLMClient, model: str, error_text: str, context: str) -> str:
    user = f"ERROR:\n{error_text}\n\nCONTEXT:\n{context}\n\nReturn the repair patch in the specified [*** Begin Patch] format."
    return await llm.chat(model=model, system=SYSTEM_REPAIR, user=user)
