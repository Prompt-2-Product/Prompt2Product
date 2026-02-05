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
from app.services.spec_generator import llm_prompt_to_spec
from app.services.code_generator import llm_spec_to_code
from app.services.repair import llm_repair
from app.services.patcher import apply_unified_patch


from app.core.utils import parse_traceback

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
            parts.append(f"\n--- FILE: {rel} ---\n{text}\n")
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
        port = 8000 + run.id
        log(session, run.id, "run", f"Will start generated app on http://{host}:{port}")

        try:
            # 1) PROMPT -> SPEC (LLM)
            log(session, run.id, "spec", "Starting spec generation...")
            spec_model = self.router.spec_model().model
            spec = asyncio.run(llm_prompt_to_spec(self.llm, spec_model, prompt))
            log(session, run.id, "spec", f"LLM TaskSpec: {spec.app_name}")

            # 2) SPEC -> CODE FILES (LLM)
            log(session, run.id, "codegen", "Starting code generation...")
            code_model = self.router.code_model().model
            gen = asyncio.run(llm_spec_to_code(self.llm, code_model, spec))
            files = [{"path": f.path, "content": f.content} for f in gen.files]

            write_files(ws, files)
            log(session, run.id, "codegen", f"LLM generated {len(files)} files")

            backend_dir = ws / "generated_app" / "backend"
            req_path = backend_dir / "requirements.txt"

            # 3) VENV SETUP + INSTALL
            log(session, run.id, "sandbox", "Setting up virtual environment...")
            self.runner.setup(ws)
            log(session, run.id, "sandbox", "Venv sandbox created")

            log(session, run.id, "deps", "Installing dependencies...")
            install_res = self.runner.install_deps(ws, req_path)
            if install_res.stdout:
                log(session, run.id, "deps", install_res.stdout.strip())
            if install_res.exit_code != 0:
                log(session, run.id, "deps", install_res.stderr or "Dependency install failed", level="ERROR")
                update_run_status(session, run, "failed")
                return

            # 4) RUN + REPAIR LOOP
            attempts = 0
            while True:
                attempts += 1
                log(session, run.id, "run", f"Starting uvicorn attempt {attempts}")

                # Sanity Check: Syntax
                syntax_err = self.runner.check_syntax(ws)
                if syntax_err:
                    log(session, run.id, "run", "Syntax check failed, skipping run", level="ERROR")
                    out = ""
                    err = syntax_err
                    # Proceed directly to repair below
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


                if attempts >= settings.MAX_REPAIR_ATTEMPTS:
                    update_run_status(session, run, "failed")
                    log(session, run.id, "repair", "Max repair attempts reached", level="ERROR")
                    return

                # 5) REPAIR (LLM) -> PATCH -> APPLY
                repair_model = self.router.repair_model().model
                context = _context_snippets(ws, error_text=err or out)
                patch = asyncio.run(llm_repair(self.llm, repair_model, error_text=err or out, context=context))

                log(session, run.id, "repair", "Applying patch from repair LLM")
                apply_unified_patch(ws, patch)
                log(session, run.id, "repair", "Patch applied, retrying run...")

        except Exception as e:
            log(session, run.id, "fatal", f"{type(e).__name__}: {e}", level="ERROR")
            update_run_status(session, run, "failed")
