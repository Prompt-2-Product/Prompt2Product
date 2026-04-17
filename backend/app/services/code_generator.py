from __future__ import annotations
import os
import re
from pathlib import Path
from typing import List, Dict, Any
from pydantic import BaseModel, Field, model_validator
from app.services.llm.base import LLMClient
from app.services.prompt_to_spec import TaskSpec
from app.core.utils import extract_json, extract_balanced_json_object, repair_json
import json as json_lib

class GenFile(BaseModel):
    path: str
    content: str

    @model_validator(mode='before')
    @classmethod
    def fix_path_and_name(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # FIX: LLM often outputs 'name' instead of 'path'
            if 'path' not in data and 'name' in data:
                data['path'] = data['name']
            
            # FIX: Ensure full paths if LLM outputs bare filenames
            if 'path' in data:
                path = data['path']
                if '/' not in path and '\\' not in path:
                    if path.endswith(('.html', '.css', '.js')):
                        data['path'] = f"generated_app/frontend/{path}"
                    elif path.endswith(('.py', '.txt', '.sql', '.env')):
                        data['path'] = f"generated_app/backend/{path}"
        return data

class GenOutput(BaseModel):
    plan: str = Field(default="No plan provided.")
    manifest: List[str] = Field(default_factory=list)
    files: List[GenFile] = Field(default_factory=list)
    entrypoint: str = "generated_app/backend/main.py"
    run: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode='before')
    @classmethod
    def normalize_files(cls, data: Any) -> Any:
        # DEBUG: Print raw LLM output to understand structure
        try:
             print(f"DEBUG: GenOutput raw data: {json_lib.dumps(data, indent=2)}")
        except:
             print(f"DEBUG: GenOutput raw data (non-json): {data}")

        # FIX: DeepSeek often outputs a dict of {filename: content} instead of a list
        # Case 1: The root object is just the dict of files
        if isinstance(data, dict):
            # If it has keys that look like files and NO 'files' key
            if 'files' not in data and any('.' in k for k in data.keys()):
                # Convert dict to list of GenFile dicts
                new_files = []
                for path, content in data.items():
                    if isinstance(content, str):
                        new_files.append({"path": path, "content": content})
                if new_files:
                    return {"files": new_files}

            # Case 2: 'files' key exists but is a dict {filename: content} instead of list
            # OR a dict of categories {category: [file_objects]}
            if 'files' in data and isinstance(data['files'], dict):
                file_dict = data['files']
                new_files_list = []
                for key, value in file_dict.items():
                     # Simple key: value (filename: content)
                     if isinstance(value, str):
                        new_files_list.append({"path": key, "content": value})
                     # Nested category: [file_objects]
                     elif isinstance(value, list):
                        for item in value:
                            if isinstance(item, dict):
                                # Extract path/name and content
                                # DeepSeek uses 'file_name' sometimes, or 'name', or 'path'
                                fpath = item.get('file_name', item.get('path', item.get('name')))
                                fcontent = item.get('content')
                                if fpath and fcontent:
                                    new_files_list.append({"path": fpath, "content": fcontent})
                
                # Only replace if we found files
                if new_files_list:
                    data['files'] = new_files_list
        
        return data

async def generate_code(llm: LLMClient, model: str, task_spec: TaskSpec) -> GenOutput:
    """
    Generates application code from TaskSpec using the finetuned coder model.
    """
    
    prompt = f"Generate a complete production-ready web app for {task_spec.app_name}. Here is the architecture specification:\n{task_spec.model_dump_json()}"
    system_prompt = "You are a senior full-stack developer. Generate complete, working code for the requested application based on the TaskSpec."
    
    attempts = 0
    max_attempts = 3

    while attempts < max_attempts:
        attempts += 1
        try:
            response = await llm.chat(
                model=model, 
                system=system_prompt, 
                user=prompt,
                max_tokens=8192  # Increased for full app JSON generation
            )
            
            # Extract JSON payload
            candidates: list[str] = []
            extracted = extract_json(response)
            if extracted:
                candidates.append(extracted)
            
            balanced = extract_balanced_json_object(response, required_substrings=('"files"',))
            if balanced and balanced not in candidates:
                candidates.append(balanced)
            stripped = response.strip()
            if stripped and stripped not in candidates:
                candidates.append(stripped)

            parsed_data = None
            last_err: BaseException | None = None
            for raw in candidates:
                for use_repair in (False, True):
                    try:
                        blob = repair_json(raw) if use_repair else raw
                        parsed_data = json_lib.loads(blob)
                        break
                    except (json_lib.JSONDecodeError, TypeError) as e:
                        last_err = e
                if parsed_data is not None:
                    break

            if parsed_data is None:
                raise ValueError(f"Could not parse JSON output: {last_err}")

            return GenOutput(**parsed_data)
            
        except Exception as e:
            if attempts >= max_attempts:
                print(f"Failed to generate output after {max_attempts} attempts: {e}")
                raise ValueError(f"LLM failed to generate valid code output: {e}")
            
            # Add error to prompt for next attempt
            print(f"JSON Parse Error (Attempt {attempts}): {e}. Retrying...")
            prompt += f"\n\nERROR: The previous JSON was invalid: {e}\nFix the JSON syntax and return ONLY a valid JSON object."

# --- Backward Compatibility for Orchestrator ---
llm_spec_to_code = generate_code

def _collect_frontend_html_rel_paths(files: List[GenFile]) -> List[str]:
    rels: List[str] = []
    for f in files:
        p = f.path.replace("\\", "/")
        if not p.endswith(".html") or "/frontend/" not in p:
            continue
        rels.append(p.split("/frontend/", 1)[1])
    return sorted(set(rels))


def _http_routes_for_html(rel: str) -> List[str]:
    """Paths the app should serve for this file (extensionless + .html where useful)."""
    rel = rel.replace("\\", "/")
    if rel == "index.html":
        return ["/", "/index.html"]
    stem = rel[:-5]  # drop .html
    base = "/" + stem
    return [base, base + ".html"]


def _file_join_snippet(rel: str) -> str:
    parts = rel.replace("\\", "/").split("/")
    args = ", ".join(repr(p) for p in parts)
    return f"os.path.join(FRONTEND_DIR, {args})"


def _func_base_name(rel: str) -> str:
    r = rel.replace("\\", "/")
    stem = r[: -len(".html")] if r.endswith(".html") else r
    stem = stem.replace("/", "_").replace("-", "_")
    stem = re.sub(r"[^a-zA-Z0-9_]", "_", stem)
    if stem and stem[0].isdigit():
        stem = "page_" + stem
    return stem or "page"


def _existing_fastapi_routes(main_py: str) -> set[str]:
    return set(re.findall(r'@app\.get\(\s*["\']([^"\']+)["\']', main_py))


def _any_html_route_missing(main_py: str, html_rels: List[str]) -> bool:
    ex = _existing_fastapi_routes(main_py)
    for rel in html_rels:
        for r in _http_routes_for_html(rel):
            if r not in ex:
                return True
    return False


def _ensure_main_py_html_routes(main_py: str, html_rels: List[str]) -> str:
    if not html_rels:
        return main_py
    existing = _existing_fastapi_routes(main_py)
    blocks: List[str] = []
    used_funcs: set[str] = set()
    for rel in html_rels:
        routes = _http_routes_for_html(rel)
        missing = [r for r in routes if r not in existing]
        if not missing:
            continue
        fname = _func_base_name(rel)
        func = f"read_{fname}"
        n = 2
        while func in used_funcs:
            func = f"read_{fname}_{n}"
            n += 1
        used_funcs.add(func)
        join_snip = _file_join_snippet(rel)
        decorators = "\n".join(f'@app.get("{r}")' for r in missing)
        for r in missing:
            existing.add(r)
        blocks.append(f"{decorators}\ndef {func}():\n    return FileResponse({join_snip})\n")
    if not blocks:
        return main_py
    inject = (
        "\n# ═══ Auto-injected HTML routes (post_process) ═══\n"
        + "\n".join(blocks)
    )
    return main_py.rstrip() + inject + "\n"


def repair_main_routes_on_disk(workspace: Path) -> bool:
    """
    Inject missing FastAPI routes for every frontend/**/*.html when main.py is incomplete.
    Returns True if main.py was written.
    """
    fe = workspace / "generated_app" / "frontend"
    main_path = workspace / "generated_app" / "backend" / "main.py"
    if not fe.is_dir() or not main_path.is_file():
        return False
    rels = sorted(p.relative_to(fe).as_posix() for p in fe.rglob("*.html"))
    if not rels:
        return False
    content = main_path.read_text(encoding="utf-8")
    if "FileResponse" not in content or "FRONTEND_DIR" not in content:
        return False
    new_content = _ensure_main_py_html_routes(content, rels)
    if new_content == content:
        return False
    main_path.write_text(new_content, encoding="utf-8")
    return True


def post_process_output(output: GenOutput) -> GenOutput:
    """
    Fix common LLM issues: escaped newlines in files, truncated main.py without page routes.
    """
    html_rels = _collect_frontend_html_rel_paths(output.files)
    for f in output.files:
        if "\\\\n" in f.content:
            f.content = f.content.replace("\\\\n", "\n")
        if not (
            f.path.endswith("backend/main.py") or f.path.endswith("backend\\main.py")
        ):
            continue
        content = f.content
        if "FileResponse" not in content:
            continue
        if "FRONTEND_DIR" not in content:
            continue
        if not html_rels:
            continue
        if '@app.get("/")' not in content and "@app.get('/')" not in content:
            f.content = _ensure_main_py_html_routes(content, html_rels)
            continue
        if _any_html_route_missing(content, html_rels):
            f.content = _ensure_main_py_html_routes(content, html_rels)
    return output
