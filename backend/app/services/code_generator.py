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
  generated_app/frontend/app.js
  (Only create menu.html/order.html/styles.css if strictly necessary for the MVP. Start small.)
- Backend routes:
  GET / -> index.html
  GET /api/menu returns JSON list
  POST /api/order accepts JSON and returns confirmation JSON
- requirements.txt must contain fastapi and uvicorn.
- Do NOT use exact version numbers in requirements.txt (e.g. use "fastapi" NOT "fastapi==0.92.0").
- Output MUST be STRICT JSON ONLY with:
  { "files":[{"path":"...","content":"..."}], "entrypoint":"...", "run":{...} }
No markdown. No explanations.
IMPORTANT: Escape all special characters in "content" strings properly (e.g. quotes, newlines).
Do NOT include comments (// or #) inside the JSON.
Keep it simple. A Single-File MVP (main.py + index.html) is often best for the first pass.
"""

from app.core.utils import extract_json

async def llm_spec_to_code(llm: LLMClient, model: str, spec: TaskSpec) -> GenOutput:
    user = f"TASKSPEC_JSON:\n{spec.model_dump_json(indent=2)}\n\nReturn code files JSON only."
    raw = await llm.chat(model=model, system=SYSTEM_CODE, user=user)
    
    cleaned = extract_json(raw)
    
    try:
        output = GenOutput.model_validate_json(cleaned)
    except Exception as e:
        fix_system = f"{SYSTEM_CODE}\n\nYour previous output had validation errors:\n{str(e)}\n\nOutput ONLY corrected JSON."
        raw2 = await llm.chat(model=model, system=fix_system, user=user)
        cleaned2 = extract_json(raw2)
        output = GenOutput.model_validate_json(cleaned2)

    # Post-process to fix common LLM escaping issues (like double \\n in requirements.txt)
    # Post-process to fix common LLM escaping issues (like double \\n)
    import re
    for file in output.files:
        if "\\n" in file.content:
            file.content = file.content.replace("\\n", "\n")
        
        if file.path.endswith("requirements.txt"):
            # Safety net: remove version pins if LLM ignored instructions
            # Replace "pkg==1.2.3" or "pkg>=1.2" with "pkg"
            file.content = re.sub(r"==[^\s]+", "", file.content)
            file.content = re.sub(r">=[^\s]+", "", file.content)
            
    return output
