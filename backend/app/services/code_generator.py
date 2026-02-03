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
IMPORTANT: Escape all special characters in "content" strings properly (e.g. quotes, newlines).
Do NOT include comments (// or #) inside the JSON.
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

async def llm_spec_to_code(llm: LLMClient, model: str, spec: TaskSpec) -> GenOutput:
    user = f"TASKSPEC_JSON:\n{spec.model_dump_json(indent=2)}\n\nReturn code files JSON only."
    raw = await llm.chat(model=model, system=SYSTEM_CODE, user=user)
    
    cleaned = _clean_json(raw)
    
    try:
        output = GenOutput.model_validate_json(cleaned)
    except Exception as e:
        fix_system = f"{SYSTEM_CODE}\n\nYour previous output had validation errors:\n{str(e)}\n\nOutput ONLY corrected JSON."
        raw2 = await llm.chat(model=model, system=fix_system, user=user)
        cleaned2 = _clean_json(raw2)
        output = GenOutput.model_validate_json(cleaned2)

    # Post-process to fix common LLM escaping issues (like double \\n in requirements.txt)
    for file in output.files:
        if file.path.endswith("requirements.txt"):
            file.content = file.content.replace("\\n", "\n")
            
    return output
