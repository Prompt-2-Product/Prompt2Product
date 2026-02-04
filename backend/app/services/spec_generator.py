from __future__ import annotations
from app.services.prompt_to_spec import TaskSpec
from app.services.llm.base import LLMClient

from app.core.utils import extract_json

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
Styling theme must be: "light" or "dark".
API method must be: "GET", "POST", "PUT", "DELETE".

IMPORTANT:
- Do NOT include comments (// or #) inside or outside the JSON.
- Do NOT wrap in markdown code blocks (though we handle them).
- Ensure all strings are properly escaped.
"""

async def llm_prompt_to_spec(llm: LLMClient, model: str, prompt: str) -> TaskSpec:
    user = f"USER_PROMPT:\n{prompt}\n\nReturn TaskSpec JSON only."
    raw = await llm.chat(model=model, system=SYSTEM_SPEC, user=user)
    
    cleaned = extract_json(raw)
    
    try:
        return TaskSpec.model_validate_json(cleaned)
    except Exception as e:
        fix_system = f"{SYSTEM_SPEC}\n\nYour previous output had validation errors:\n{str(e)}\n\nOutput ONLY corrected JSON."
        raw2 = await llm.chat(model=model, system=fix_system, user=user)
        cleaned2 = extract_json(raw2)
        return TaskSpec.model_validate_json(cleaned2)
