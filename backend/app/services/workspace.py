from pathlib import Path
from app.core.config import settings

def project_workspace(project_id: int, run_id: int) -> Path:
    root = settings.WORKSPACE_ROOT
    path = root / f"project_{project_id}" / f"run_{run_id}"
    path.mkdir(parents=True, exist_ok=True)
    return path

def write_files(ws: Path, files: list[dict]) -> None:
    for f in files:
        p = ws / f["path"]
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f["content"], encoding="utf-8")
