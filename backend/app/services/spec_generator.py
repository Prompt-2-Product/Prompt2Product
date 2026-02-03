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
Styling theme must be: "light" or "dark".
API method must be: "GET", "POST", "PUT", "DELETE".
"""

def _clean_json(raw: str) -> str:
    cleaned = raw.strip()
    # Remove markdown code blocks if present
    if "```" in cleaned:
        lines = cleaned.splitlines()
        # Strip opening (```json) and closing (```) fences
        message_lines = []
        in_code_block = False
        for line in lines:
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue
            if in_code_block or (not in_code_block and line.strip().startswith("{")):
                 # Simple heuristic: keep lines inside blocks, OR if no blocks, keep content starting with {
                 # But valid simple heuristic for LLM output is usually: content between first ``` and last ```
                 pass
        
        # Simpler approach strictly for fences at start/end
        if lines[0].strip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines)
    return cleaned.strip()

async def llm_prompt_to_spec(llm: LLMClient, model: str, prompt: str) -> TaskSpec:
    user = f"USER_PROMPT:\n{prompt}\n\nReturn TaskSpec JSON only."
    raw = await llm.chat(model=model, system=SYSTEM_SPEC, user=user)
    
    cleaned = _clean_json(raw)
    
    try:
        return TaskSpec.model_validate_json(cleaned)
    except Exception as e:
        fix_system = f"{SYSTEM_SPEC}\n\nYour previous output had validation errors:\n{str(e)}\n\nOutput ONLY corrected JSON."
        raw2 = await llm.chat(model=model, system=fix_system, user=user)
        cleaned2 = _clean_json(raw2)
        return TaskSpec.model_validate_json(cleaned2)
