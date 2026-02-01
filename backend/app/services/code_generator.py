from __future__ import annotations
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from app.services.llm.base import LLMClient
from app.services.prompt_to_spec import TaskSpec

class GenFile(BaseModel):
    path: str
    content: str

class GenOutput(BaseModel):
    files: List[GenFile] = Field(default_factory=list)
    entrypoint: str = "generated_app/backend/main.py"
    run: Dict[str, Any] = Field(default_factory=dict)

SYSTEM_CODE = """You generate a full-stack website:
- Backend MUST be FastAPI.
- Frontend MUST be HTML/CSS/JS.
- Backend must serve frontend pages and /static assets.
- Create this structure in paths:
  generated_app/backend/main.py
  generated_app/backend/requirements.txt
  generated_app/frontend/index.html
  generated_app/frontend/menu.html
  generated_app/frontend/order.html
  generated_app/frontend/styles.css
  generated_app/frontend/app.js
- Backend routes:
  GET / -> index.html
  GET /menu -> menu.html
  GET /order -> order.html
  GET /api/menu returns JSON list
  POST /api/order accepts JSON and returns confirmation JSON
- requirements.txt must contain fastapi and uvicorn.
- Output MUST be STRICT JSON ONLY with:
  { "files":[{"path":"...","content":"..."}], "entrypoint":"...", "run":{...} }
No markdown. No explanations.
"""

async def llm_spec_to_code(llm: LLMClient, model: str, spec: TaskSpec) -> GenOutput:
    user = f"TASKSPEC_JSON:\n{spec.model_dump_json(indent=2)}\n\nReturn code files JSON only."
    raw = await llm.chat(model=model, system=SYSTEM_CODE, user=user)

    try:
        return GenOutput.model_validate_json(raw)
    except Exception:
        fix_system = SYSTEM_CODE + "\nYour previous output was invalid JSON. Output ONLY corrected JSON."
        raw2 = await llm.chat(model=model, system=fix_system, user=user)
        return GenOutput.model_validate_json(raw2)
