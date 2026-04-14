from __future__ import annotations
import os
import re
from pathlib import Path
from typing import List, Dict, Any
from pydantic import BaseModel, Field, model_validator
from app.services.llm.base import LLMClient
from app.services.prompt_to_spec import TaskSpec
from app.core.utils import extract_json, extract_balanced_json_object, repair_json
from app.services.ui_assembler import UIAssembler
import json as json_lib

# --- New Pydantic Models for Page Plan ---
class Section(BaseModel):
    type: str = Field(..., description="Type of section (hero, features, pricing, testimonials, faq, contact, footer)")
    data: Dict[str, Any] = Field(..., description="Data for the section placeholders")

class Page(BaseModel):
    filename: str = Field(..., description="Filename like index.html")
    title: str
    nav_label: str = Field(..., description="Short label for navigation menu, e.g., 'About Us'")
    description: str
    sections: List[Section]

class PagePlan(BaseModel):
    brand_name: str
    pages: List[Page]

    @model_validator(mode='before')
    @classmethod
    def normalize_plan(cls, data: Any) -> Any:
        # Case 1: If LLM returns just a list of pages, wrap it
        if isinstance(data, list):
            data = {"brand_name": "My App", "pages": data}
        
        # Case 2: If LLM returns a dict
        if isinstance(data, dict):
            # If it's a single page (has 'filename' but not 'pages')
            if 'filename' in data and 'pages' not in data:
                data = {"brand_name": data.get("brand_name", "My App"), "pages": [data]}
            
            # Map common key variants to 'pages'
            for alt_key in ['files', 'page_list', 'site_pages']:
                if alt_key in data and 'pages' not in data:
                    data['pages'] = data[alt_key]
            
            # Final integrity checks
            if 'pages' not in data or not data['pages']:
                raise ValueError("LLM output is missing pages. Possible truncation.")
            
            # MANDATORY: index.html check
            # This prevents the 'succeeding' with just an about page
            has_index = any(
                p.get('filename') == 'index.html' if isinstance(p, dict) else False 
                for p in data['pages']
            )
            if not has_index:
                raise ValueError("LLM failed to generate index.html. Incomplete response suspected.")

            # Ensure brand_name exists
            if 'brand_name' not in data:
                data['brand_name'] = "My App"
                
        return data

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

SYSTEM_CODE = """You generate a COMPLETE, WORKING, premium full-stack website from a TaskSpec JSON.
- Backend: FastAPI
- Frontend: HTML/CSS/JS with custom Premium Design System (built-in)

═══════════════════════════════════════════════════════════════════
🚨 CONTENT GROUNDING & RELIABILITY RULES (MANDATORY)
═══════════════════════════════════════════════════════════════════

1. **GROUNDED CONTENT**: Do NOT use generic placeholders like "Contact us today" or "info@example.com".
   - If the app is for "Deep Sea Diving", use contact emails like "diver@deepsea-ocean.com" and missions like "Exploring the abyss since 1994."
   - Bios for team members must reflect their industry expertise (e.g., "Chief Underwater Architect").

2. **ICON-FIRST DESIGN (NO BROKEN IMAGES)**: 
   - NEVER use `<img>` tags for placeholders (e.g., "team1.jpg"). They appear as broken boxes.
   - Use **Bootstrap Icons** (`bi-icon-name`) or **Emojis** for all visual highlights.
   - For Team Members: Provide an `icon` name (e.g., `person-circle`, `inbox`, `rocket`).

3. **STRUCTURAL INTEGRITY**:
   - `index.html` MUST have a `hero` section and at least 2 other sections (features, pricing, etc.).
   - Every page MUST have a clear `description` that matches the theme.

4. **NAVIGATION**:
   - Headers are auto-generated. Use extensionless lowercase names for links: `/about`, `/pricing`, etc.

═══════════════════════════════════════════════════════════════════
🚨 STEP-BY-STEP GENERATION PROCESS
═══════════════════════════════════════════════════════════════════

STEP 1: Start with the FastAPI backend logic (refer to templates).

STEP 2: Design the PagePlan JSON.
Available Section Types: 'hero', 'features', 'pricing', 'testimonials', 'faq', 'team', 'contact'.

OUTPUT FORMAT (JSON ONLY):
{
  "brand_name": "OceanicEx",
  "footer_text": "Exploring the depths with cutting-edge sonar technology since 2010.",
  "pages": [
    {
      "filename": "index.html",
      "title": "OceanicEx - Marine Exploration Experts",
      "nav_label": "Home",
      "description": "Leading the world in deep-sea archaeological surveys and marine biology.",
      "sections": [
        {
          "type": "hero",
          "data": {
             "title": "Journey to the Abyss",
             "subtitle": "Uncovering the secrets of the midnight zone with our state-of-the-art ROV fleet.",
             "cta_text": "Our Missions",
             "cta_link": "/projects"
          }
        },
        {
          "type": "team",
          "data": {
             "title": "The Explorers",
             "subtitle": "Meet the scientists and engineers leading our deep-sea ventures.",
             "members": [
                {"name": "Dr. Sarah Tides", "role": "Marine Biologist", "bio": "Specialist in bioluminescent ecosystems.", "icon": "water"},
                {"name": "Mark Abyss", "role": "Lead ROV Pilot", "bio": "Over 5000 hours of deep-sea navigation.", "icon": "controller"}
             ]
          }
        }
      ]
    }
  ]
}

JSON SAFETY: Double quotes only. Escape \\" inside strings. No line breaks in strings. No comments.
"""

async def generate_code(llm: LLMClient, model: str, task_spec: TaskSpec) -> GenOutput:
    """
    Generates a Bootstrap-based UI plan and assembles the application code.
    """
    
    # 1. Generate Page Plan using LLM
    # Construct prompt from TaskSpec fields
    description = f"App Name: {task_spec.app_name}"
    if task_spec.notes:
        description += f"\nNotes: {task_spec.notes}"
        
    structure_requirements = "Planned Pages:\n"
    for p in task_spec.pages:
        structure_requirements += f"- {p.name} ({p.route}): {', '.join(p.sections)}\n"

    prompt = f"Design a website for: {description}\n\nStrictly follow this page structure:\n{structure_requirements}"
    
    attempts = 0
    max_attempts = 3
    
    while attempts < max_attempts:
        attempts += 1
        try:
            response = await llm.chat(model=model, system=SYSTEM_CODE, user=prompt)
            
            # Multiple extraction strategies: extract_json can return a truncated inner {...}
            # via non-greedy regex; balanced scan fixes that.
            candidates: list[str] = []
            extracted = extract_json(response)
            if extracted:
                candidates.append(extracted)
            balanced = extract_balanced_json_object(
                response, required_substrings=('"brand_name"', '"pages"')
            )
            if balanced and balanced not in candidates:
                candidates.append(balanced)
            stripped = response.strip()
            if stripped and stripped not in candidates:
                candidates.append(stripped)

            plan_dict = None
            last_err: BaseException | None = None
            for raw in candidates:
                for use_repair in (False, True):
                    try:
                        blob = repair_json(raw) if use_repair else raw
                        plan_dict = json_lib.loads(blob)
                        break
                    except (json_lib.JSONDecodeError, TypeError) as e:
                        last_err = e
                if plan_dict is not None:
                    break

            if plan_dict is None:
                raise ValueError(f"Could not parse PagePlan JSON: {last_err}")

            # DEBUG: Print keys to help diagnose structure issues
            if isinstance(plan_dict, dict):
                 print(f"DEBUG: PagePlan keys: {list(plan_dict.keys())}")
            
            page_plan = PagePlan(**plan_dict)
            
            # If successful, break loop
            break
            
        except Exception as e:
            if attempts >= max_attempts:
                print(f"Failed to parse PagePlan after {max_attempts} attempts: {e}")
                raise ValueError(f"LLM failed to generate valid PagePlan: {e}")
            
            # Add error to prompt for next attempt
            print(f"JSON Parse Error (Attempt {attempts}): {e}. Retrying...")
            prompt += f"\n\nERROR: The previous JSON was invalid: {e}\nFix the JSON syntax and return ONLY the JSON."

    # 2. Assemble HTML Files
    gen_files = []
    
    # Pre-calculate navigation links
    nav_links = []
    for page in page_plan.pages:
        slug = page.filename.replace(".html", "")
        route = "/" if slug == "index" else f"/{slug}"
        nav_links.append({"label": page.nav_label, "href": route})

    # Frontend Files
    for page in page_plan.pages:
        # Convert Pydantic model to dict for assembler
        page_dict = page.dict()
        page_dict["brand_name"] = page_plan.brand_name
        
        html_content = UIAssembler.assemble_page(page_dict, nav_links=nav_links)
        gen_files.append(GenFile(path=f"generated_app/frontend/{page.filename}", content=html_content))

    # 3. Generate Backend (main.py) with dynamic routes
    backend_code = generate_backend_code(page_plan)
    gen_files.append(GenFile(path="generated_app/backend/main.py", content=backend_code))
    
    # 4. Generate Requirements
    reqs = "fastapi\nuvicorn\n"
    gen_files.append(GenFile(path="generated_app/backend/requirements.txt", content=reqs))
    
    return GenOutput(files=gen_files)


def generate_backend_code(plan: PagePlan) -> str:
    """
    Generates FastAPI backend serving the generated HTML pages.
    """
    routes = ""
    for page in plan.pages:
        slug = page.filename.replace(".html", "")
        if slug == "index":
            route_path = "/"
            func_name = "read_root"
        else:
            route_path = f"/{slug}"
            func_name = f"read_{slug.replace('-', '_')}"
            
        routes += f"""
@app.get("{route_path}")
def {func_name}():
    return FileResponse(os.path.join(FRONTEND_DIR, "{page.filename}"))
"""

    return f"""import os
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Get the parent directory (generated_app/) from backend/
# __file__ is inside backend/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

# Ensure directories exist
os.makedirs(FRONTEND_DIR, exist_ok=True)

# Mount static files (if any custom css/js is added later)
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# ═══════════════════════════════════════════════════════════════════
# ROUTES
# ═══════════════════════════════════════════════════════════════════
{routes}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""

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
