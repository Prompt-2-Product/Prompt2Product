from __future__ import annotations
import asyncio
from pathlib import Path
from sqlmodel import Session

from app.core.config import settings
from app.services.workspace import project_workspace, write_files
from app.services.logging_service import log
from app.services.sandbox.venv_runner import VenvSandboxRunner
from app.db.repo import update_run_status

from app.services.llm.factory import get_llm_client
from app.services.router import ModelRouter
from app.services.prompt_enhancer import llm_enhance_prompt
from app.services.spec_generator import llm_prompt_to_spec
from app.services.code_generator import llm_spec_to_code, post_process_output, GenOutput, GenFile
from app.services.repair import llm_repair
from app.services.patcher import apply_unified_patch


from app.core.utils import parse_traceback

def validate_generated_files(files: list) -> list[str]:
    """
    Validates generated files for quality issues.
    Returns list of warning messages (non-blocking).
    """
    warnings = []
    
    for file in files:
        path = file["path"]
        content = file["content"]
        
        # Check HTML files
        if path.endswith(".html"):
            # Check for empty navigation placeholder
            if "<!-- Nav content -->" in content:
                warnings.append(f"{path}: Contains empty navigation placeholder")
            
            # Check for empty footer placeholder
            if "<!-- Footer content -->" in content:
                warnings.append(f"{path}: Contains empty footer placeholder")
            
            # Check for generic placeholders
            if "Lorem ipsum" in content:
                warnings.append(f"{path}: Contains 'Lorem ipsum' placeholder")
            if "Feature 1" in content or "Feature 2" in content:
                warnings.append(f"{path}: Contains generic 'Feature N' placeholders")
        
        # Check CSS files
        elif path.endswith("main.css"):
            lines = [line for line in content.split("\n") if line.strip() and not line.strip().startswith("//")]
            if len(lines) < 50:
                warnings.append(f"{path}: Only {len(lines)} lines (minimum 50 recommended)")
        
        # Check JS files
        elif path.endswith("app.js"):
            lines = [line for line in content.split("\n") if line.strip() and not line.strip().startswith("//")]
            if len(lines) < 30:
                warnings.append(f"{path}: Only {len(lines)} lines (minimum 30 recommended)")
        
        # Check backend main.py
        elif path.endswith("backend/main.py") or path.endswith("backend\\main.py"):
            # Check for incorrect HTMLResponse usage
            if "HTMLResponse(path=" in content:
                warnings.append(f"{path}: Uses HTMLResponse(path=...) which is invalid. Should be FileResponse.")
            
            # Check for Jinja2 usage
            if "Jinja2Templates" in content or "fastapi.templating" in content:
                 warnings.append(f"{path}: Uses Jinja2 templates (forbidden). Should be static FileResponse.")

            # Check for Database usage
            if "sqlalchemy" in content or "sqlite3" in content:
                 warnings.append(f"{path}: Uses Database (forbidden). Should be static content.")

            # Check for file serving routes
            if "FileResponse" not in content:
                warnings.append(f"{path}: Missing FileResponse import - HTML pages won't be served!")
            
            if "app.mount" not in content or "StaticFiles" not in content:
                warnings.append(f"{path}: Critical - static files route missing! CSS/JS won't load.")
            elif "fastapi.staticfiles" not in content and "starlette.staticfiles" not in content:
                 warnings.append(f"{path}: Usage of StaticFiles without import detected.")
            if '@app.get("/")' not in content and "@app.get('/')" not in content:
                warnings.append(f"{path}: Missing root route (@app.get('/')) - index.html won't be accessible!")
    
    return warnings



def _context_snippets(workspace: Path, error_text: str = "") -> str:
    """
    Send only important files to repair model (avoid huge context).
    Uses error traceback to narrow down files.
    """
    relevant_files = set()
    if error_text:
        matches = parse_traceback(error_text)
        for fname, _ in matches:
            # Clean up path (sometimes weird in trace)
            if "generated_app" in fname:
                # keep logical path relative to workspace
                # e.g. .../generated_app/backend/main.py
                # we try to find suffix in our candidate list
                start_idx = fname.find("generated_app")
                if start_idx != -1:
                    rel = fname[start_idx:].replace("\\", "/")
                    relevant_files.add(rel)

    candidates = [
        "generated_app/backend/main.py",
        "generated_app/backend/requirements.txt",
        "generated_app/frontend/app.js",
        "generated_app/frontend/index.html",
        "generated_app/frontend/menu.html",
        "generated_app/frontend/order.html",
        "generated_app/frontend/styles.css",
    ]
    
    # If we found specific files in trace, prioritize them + requirements.txt
    if relevant_files:
        # Always include requirements just in case
        relevant_files.add("generated_app/backend/requirements.txt")
        final_list = list(relevant_files)
    else:
        # Fallback to all candidates
        final_list = candidates

    parts = []
    for rel in final_list:
        p = workspace / rel
        if p.exists():
            text = p.read_text(encoding="utf-8")
            # limit size per file
            text = text[:4000]
            parts.append(f"\n--- FILE: {rel} (Use this exact path for patching) ---\n{text}\n")
    return "\n".join(parts)


class Orchestrator:
    def __init__(self):
        self.runner = VenvSandboxRunner()
        self.router = ModelRouter()
        self.llm = get_llm_client()

    def execute_run(self, session: Session, run, prompt: str, host: str = "0.0.0.0"):
        """
        Sync entrypoint (FastAPI route uses sync).
        Internally we call async LLM via asyncio.run().
        """
        update_run_status(session, run, "running", attempts=run.attempts + 1)
        ws: Path = project_workspace(run.project_id, run.id)
        log(session, run.id, "workspace", f"Workspace: {ws}")

        # Use unique port per run to avoid conflicts
        port = 8010 + run.id
        log(session, run.id, "run", f"Will start generated app on http://{host}:{port}")

        try:
            # 0) PROMPT ENHANCEMENT
            log(session, run.id, "enhance", "Enhancing prompt...")
            enhance_model = self.router.enhance_model().model
            enhanced_prompt = asyncio.run(llm_enhance_prompt(self.llm, enhance_model, prompt))
            log(session, run.id, "enhance", f"Enhanced Prompt:\n{enhanced_prompt}")

            # 1) PROMPT -> SPEC (LLM)
            log(session, run.id, "spec", "Starting spec generation...")
            spec_model = self.router.spec_model().model
            spec = asyncio.run(llm_prompt_to_spec(self.llm, spec_model, enhanced_prompt))
            log(session, run.id, "spec", f"LLM TaskSpec: {spec.app_name}")

            # 2) SPEC -> CODE FILES (LLM - Skeleton Generation)
            log(session, run.id, "codegen", "Starting code generation...")
            code_model = self.router.code_model().model
            gen = asyncio.run(llm_spec_to_code(self.llm, code_model, spec))
            log(session, run.id, "codegen", f"LLM generated {len(gen.files)} skeleton files")

            # 2.5) CONTENT ENRICHMENT (NEW STAGE)
            log(session, run.id, "enrich", "Enriching content...")
            from app.services.content_enricher import enrich_html_content
            
            enriched_files = []
            html_count = 0
            for file in gen.files:
                if file.path.endswith('.html'):
                    html_count += 1
                    try:
                        # Extract page name from path
                        page_name = file.path.split('/')[-1].replace('.html', '')
                        enriched_content = asyncio.run(enrich_html_content(
                            self.llm, code_model, file.content, spec, page_name
                        ))
                        enriched_files.append({"path": file.path, "content": enriched_content})
                        log(session, run.id, "enrich", f"Enriched {page_name}.html")
                    except Exception as e:
                        log(session, run.id, "enrich", f"Enrichment failed for {file.path}: {str(e)}", level="WARN")
                        # Fall back to original content
                        enriched_files.append({"path": file.path, "content": file.content})
                else:
                    enriched_files.append({"path": file.path, "content": file.content})
            
            log(session, run.id, "enrich", f"Enriched {html_count} HTML files")
            
            # 2.6) VALIDATION (NEW STAGE)
            log(session, run.id, "validate", "Validating generated files...")
            validation_warnings = validate_generated_files(enriched_files)
            if validation_warnings:
                for warning in validation_warnings:
                    log(session, run.id, "validate", f"⚠️ {warning}", level="WARN")
                log(session, run.id, "validate", f"Found {len(validation_warnings)} quality issues (non-blocking)")
            else:
                log(session, run.id, "validate", "✅ All validation checks passed")
            
            # Write enriched files
            write_files(ws, enriched_files)
            log(session, run.id, "codegen", f"Wrote {len(enriched_files)} enriched files")

            backend_dir = ws / "generated_app" / "backend"
            req_path = backend_dir / "requirements.txt"

            # 3) VENV SETUP
            log(session, run.id, "sandbox", "Setting up virtual environment...")
            self.runner.setup(ws)
            log(session, run.id, "sandbox", "Venv sandbox created")

            # 4) RUN + REPAIR LOOP (Includes Dependency Install)
            attempts = 0
            while True:
                attempts += 1
                if attempts > settings.MAX_REPAIR_ATTEMPTS:
                    update_run_status(session, run, "failed")
                    log(session, run.id, "repair", "Max repair attempts reached", level="ERROR")
                    return

                # A. Install Dependencies
                log(session, run.id, "deps", f"Installing dependencies (Attempt {attempts})...")
                install_res = self.runner.install_deps(ws, req_path)
                
                if install_res.exit_code != 0:
                    # Installation Failed -> Repair
                    err = (install_res.stderr or "").strip()
                    out = (install_res.stdout or "").strip()
                    log(session, run.id, "deps", out if out else "No stdout")
                    log(session, run.id, "deps", err if err else "Unknown install error", level="ERROR")
                    
                    log(session, run.id, "repair", "Dependency install failed, attempting repair...")
                    # Fall through to repair logic below
                    error_text = f"Dependency Installation Failed:\n{err}\nOutput:\n{out}"
                    # Skip execution, go straight to repair
                else:
                    if install_res.stdout:
                        log(session, run.id, "deps", install_res.stdout.strip())

                    # B. Run Uvicorn
                    log(session, run.id, "run", f"Starting uvicorn attempt {attempts}")

                    # Sanity Check: Syntax
                    syntax_err = self.runner.check_syntax(ws)
                    if syntax_err:
                        log(session, run.id, "run", "Syntax check failed, skipping run", level="ERROR")
                        error_text = f"Syntax Error:\n{syntax_err}"
                    else:
                        run_res = self.runner.run_uvicorn(ws, backend_dir, host=host, port=port)

                        if run_res.exit_code == 0:
                            update_run_status(session, run, "success")
                            log(session, run.id, "done", "Generated app ran successfully")
                            return

                        # Failed
                        err = (run_res.stderr or "").strip()
                        out = (run_res.stdout or "").strip()
                        log(session, run.id, "run", out if out else "No stdout")
                        log(session, run.id, "run", err if err else "No stderr", level="ERROR")
                        error_text = f"Runtime Error:\n{err}\nOutput:\n{out}"

                # C. Repair (LLM) -> PATCH -> APPLY
                repair_model = self.router.repair_model().model
                context = _context_snippets(ws, error_text=error_text)
                
                # Check if we should abort if context is empty or error invalid? 
                # (Assuming llm_repair handles general queries)
                
                log(session, run.id, "repair", "Generating repair patch...")
                patch = asyncio.run(llm_repair(self.llm, repair_model, error_text=error_text, context=context))

                log(session, run.id, "repair", "Applying patch from repair LLM")
                apply_unified_patch(ws, patch)
                log(session, run.id, "repair", "Patch applied, retrying run...")

                # --- NEW HARDENING BLOCK --- #
                try:
                    log(session, run.id, "repair", "Running hardening logic on patched files...")
                    
                    files_to_harden = []
                    generated_app_dir = ws / "generated_app"
                    
                    # Check main.py
                    main_py_path = generated_app_dir / "backend" / "main.py"
                    if main_py_path.exists():
                        files_to_harden.append(GenFile(path="backend/main.py", content=main_py_path.read_text(encoding="utf-8")))
                    
                    # Check requirements.txt
                    req_txt_path = generated_app_dir / "backend" / "requirements.txt"
                    if req_txt_path.exists():
                        files_to_harden.append(GenFile(path="backend/requirements.txt", content=req_txt_path.read_text(encoding="utf-8")))

                    # Check app.js
                    app_js_path = generated_app_dir / "frontend" / "app.js"
                    if app_js_path.exists():
                        files_to_harden.append(GenFile(path="frontend/app.js", content=app_js_path.read_text(encoding="utf-8")))

                    # Check main.css
                    main_css_path = generated_app_dir / "frontend" / "main.css"
                    if main_css_path.exists():
                        files_to_harden.append(GenFile(path="frontend/main.css", content=main_css_path.read_text(encoding="utf-8")))

                    if files_to_harden:
                        dummy_output = GenOutput(files=files_to_harden)
                        processed = post_process_output(dummy_output)
                        
                        for f in processed.files:
                            # We assume path is relative to generated_app
                            # Note: f.path might be absolute if post_process modifies it incorrectly, 
                            # but GenFile paths are typically relative as created above.
                            # However, post_process checks endsswith, so it's safe.
                            
                            # Handle potential path separators
                            clean_path = f.path.replace("\\", "/")
                            full_path = generated_app_dir / clean_path
                            
                            full_path.parent.mkdir(parents=True, exist_ok=True)
                            full_path.write_text(f.content, encoding="utf-8")
                            
                        log(session, run.id, "repair", "Hardening complete: Files validated and potential errors fixed.")
                except Exception as e:
                     log(session, run.id, "repair", f"Hardening warning: {e}", level="WARN")

        except Exception as e:
            log(session, run.id, "fatal", f"{type(e).__name__}: {e}", level="ERROR")
            update_run_status(session, run, "failed")
