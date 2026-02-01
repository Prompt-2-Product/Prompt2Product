from __future__ import annotations
from app.services.prompt_to_spec import TaskSpec
from app.services.llm.base import LLMClient

SYSTEM_SPEC = """You convert a user prompt into a STRICT JSON TaskSpec.
Return ONLY valid JSON. No markdown. No explanations.

TaskSpec keys:
- app_name (string)
- pages: [{name, route, sections}]
- api: [{method, path, desc}]
- data_models: [{name, fields:[{name,type}]}]
- styling: {theme, primary_color}
- constraints: {frontend, backend}

Constraints must be: frontend="html_css", backend="fastapi".
Pages must include: /, /menu, /order (at least).
API must include: GET /api/menu, POST /api/order (at least).
"""

async def llm_prompt_to_spec(llm: LLMClient, model: str, prompt: str) -> TaskSpec:
    user = f"USER_PROMPT:\n{prompt}\n\nReturn TaskSpec JSON only."
    raw = await llm.chat(model=model, system=SYSTEM_SPEC, user=user)

    try:
        return TaskSpec.model_validate_json(raw)
    except Exception:
        fix_system = SYSTEM_SPEC + "\nYour previous output was invalid JSON. Output ONLY corrected JSON."
        raw2 = await llm.chat(model=model, system=fix_system, user=user)
        return TaskSpec.model_validate_json(raw2)
