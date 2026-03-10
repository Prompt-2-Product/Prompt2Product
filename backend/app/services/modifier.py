from __future__ import annotations
from app.services.llm.base import LLMClient

SYSTEM_MODIFY = """You are an expert full-stack developer.
The user wants to make changes to their generated application.
Given the current code context and the user's request, output a patch to implement the changes.

Rules:
1. Start output with: *** Begin Patch
2. For each file to change, start with: *** Update File: [PATH]
   - [PATH] MUST be the exact relative path shown in the context header.
3. Then output the NEW CONTENT of the file (complete file), prefixed with: +++ REPLACE ENTIRE FILE +++
4. End output with: *** End Patch

Guidelines:
- Maintain consistency with the existing design system (Tailwind, Glassmorphism, etc. if used).
- Ensure all imports are correct.
- If the user asks for a new feature, add it to the appropriate files (Frontend/Backend).
- Provide the COMPLETE file content for any file you modify.
"""

async def llm_modify(llm: LLMClient, model: str, user_request: str, context: str) -> str:
    user_prompt = f"USER REQUEST: {user_request}\n\nCURRENT CODE CONTEXT:\n{context}\n\nPlease generate a patch to implement the requested changes."
    return await llm.chat(model=model, system=SYSTEM_MODIFY, user=user_prompt)
