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
  generated_app/backend/Dockerfile
  generated_app/frontend/index.html
  generated_app/frontend/app.js
  generated_app/docker-compose.yml
  (Only create menu.html/order.html/styles.css if strictly necessary for the MVP. Start small.)
- Backend:
  - MUST import: `os`, `from fastapi import FastAPI`, `from fastapi.responses import FileResponse`, `from fastapi.staticfiles import StaticFiles`.
  - The root route MUST return a `FileResponse` object.
  - Paths MUST be relative to the `backend/` folder (e.g. `../frontend/...`).
  - Example `main.py` structure:
    ```python
    import os
    from fastapi import FastAPI
    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles

    app = FastAPI()

    BASE_DIR = os.path.dirname(__file__)
    FRONTEND_DIR = os.path.join(BASE_DIR, "../frontend")

    @app.get("/")
    async def read_index():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    # ... other routes ...
    ```
- requirements.txt must contain fastapi, uvicorn, and aiofiles.
- Do NOT use version numbers in requirements.txt.
- Dockerfile instructions:
  - Use python:3.9-slim
  - WORKDIR /app
  - COPY requirements.txt .
  - RUN pip install --no-cache-dir -r requirements.txt
  - COPY . .
  - EXPOSE 8000
  - CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
- docker-compose.yml instructions:
  - service name: web
  - build: ./backend
  - env_file: .env (if it exists)
  - ports: "8000:8000"
- Output MUST be ONE SINGLE VALID JSON OBJECT.
- DO NOT split files into multiple JSON objects. 
- DO NOT provide multiple code blocks.
- Format: { "files":[{"path":"...","content":"..."}] }
- IMPORTANT:
  1. Escape all double quotes in "content" as \\"
  2. Escape all newlines in "content" as \\n
  3. No trailing commas in arrays.
  4. NO markown code blocks OR conversational text outside the single JSON object.
  5. Include ALL requested files in the same "files" list inside the ONE JSON object.
- No explanations. No comments.
"""

from app.core.utils import extract_json, clean_requirements_text, repair_json

def post_process_output(output: GenOutput) -> GenOutput:
    for file in output.files:
        # If the model used code_files, it will be empty here if not handled well.
        # But repair_json should have fixed the key name.
        
        # Fix common LLM escaping issues (like double \\n)
        if "\\n" in file.content:
            file.content = file.content.replace("\\n", "\n")
        
        if file.path.endswith("requirements.txt"):
            file.content = clean_requirements_text(file.content)
    return output

async def llm_spec_to_code(llm: LLMClient, model: str, spec: TaskSpec) -> GenOutput:
    user = f"TASKSPEC_JSON:\n{spec.model_dump_json(indent=2)}\n\nReturn code files in ONE JSON object with a 'files' key."
    current_system = SYSTEM_CODE
    
    attempts = 0
    max_attempts = 3
    
    while attempts < max_attempts:
        attempts += 1
        try:
            # Increase max_tokens for full code generation (multi-file JSON is large)
            raw = await llm.chat(model=model, system=current_system, user=user, max_tokens=8192)
            cleaned = extract_json(raw)
            repaired = repair_json(cleaned) # Apply 'dirty' fix
            output = GenOutput.model_validate_json(repaired)
            return post_process_output(output) # Success Path
            
        except Exception as e:
            error_msg = str(e)
            print(f"JSON Validation failed (Attempt {attempts}/{max_attempts}): {error_msg}")
            
            # Log the raw output for debugging
            try:
                debug_path = os.path.join(os.getcwd(), "failed_llm_output.txt")
                with open(debug_path, "w", encoding="utf-8") as f:
                    f.write(f"--- ATTEMPT {attempts} ---\nERROR: {error_msg}\n\nRAW OUTPUT:\n{raw}")
                print(f"Raw output saved to {debug_path} for debugging")
            except:
                pass

            if attempts >= max_attempts:
                raise e # Give up
            
            # Detect split JSON specifically for better feedback
            extra_feedback = ""
            if "Multiple" in error_msg:
                extra_feedback = "\n- CRITICAL: You split your output into multiple JSON objects or markdown blocks. Merge everything into ONE single JSON object."
            
            # Feed back the previous failure for better recovery
            error_feedback = f"""
PREVIOUS OUTPUT CAUSED ERROR: {error_msg}
{extra_feedback}

YOUR PREVIOUS RAW OUTPUT (FOR REFERENCE):
{raw}

IMPORTANT: 
- Return ONLY the fully corrected, COMPLETE, and CONSOLIDATED JSON object. 
- Ensure all files are in the 'files' array inside ONE root object.
- NO conversational text.
"""
            current_system = SYSTEM_CODE + "\n\n" + error_feedback
    
    # Should not be reachable but for safety:
    return GenOutput()

