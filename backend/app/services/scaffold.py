# app/services/scaffold.py
from __future__ import annotations

from typing import Dict, List
from pathlib import Path

from app.services.prompt_to_spec import TaskSpec


def scaffold_from_spec(spec: TaskSpec) -> List[Dict[str, str]]:
    """
    Returns a list of files to create (path only, content filled later).
    Paths are relative to the run workspace root.
    """
    files: List[Dict[str, str]] = []

    # Generated app root inside workspace
    app_root = "generated_app"
    backend_root = f"{app_root}/backend"
    frontend_root = f"{app_root}/frontend"

    # Backend essentials
    files.append({"path": f"{backend_root}/main.py", "content": ""})
    files.append({"path": f"{backend_root}/requirements.txt", "content": ""})

    # Frontend essentials
    files.append({"path": f"{frontend_root}/styles.css", "content": ""})
    files.append({"path": f"{frontend_root}/app.js", "content": ""})

    # Create one html per page
    # Route "/" -> index.html, others -> <name>.html (safe)
    for page in spec.pages:
        if page.route == "/":
            html_name = "index.html"
        else:
            # /menu -> menu.html
            slug = page.route.strip("/").replace("/", "_") or "page"
            html_name = f"{slug}.html"
        files.append({"path": f"{frontend_root}/{html_name}", "content": ""})

    return files


def ensure_dirs(workspace: Path, files: List[Dict[str, str]]) -> None:
    """
    Create directories for all file paths.
    """
    for f in files:
        p = workspace / f["path"]
        p.parent.mkdir(parents=True, exist_ok=True)
