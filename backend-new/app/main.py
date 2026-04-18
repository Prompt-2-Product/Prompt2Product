from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import shutil
import os
import asyncio
from typing import Optional, List, Dict
from pathlib import Path

from app.db.repo import list_projects, create_project, create_run, get_run, list_logs
from app.core.config import STORAGE_DIR
from app.pipeline.manager import run_pipeline, run_modification_pipeline

app = FastAPI(title="Prompt2Product Modular Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CreateProjectRequest(BaseModel):
    name: str

class CreateRunRequest(BaseModel):
    prompt: str
    entrypoint: Optional[str] = "app.main:app"

class ModifyRunRequest(BaseModel):
    prompt: str

@app.post("/projects")
def add_project(payload: CreateProjectRequest):
    return create_project(payload.name)

@app.get("/projects")
def get_projects():
    return list_projects()

def run_background_pipeline(run_id: int, project_id: int, prompt: str):
    asyncio.run(run_pipeline(run_id, project_id, prompt))

def run_background_modification(run_id: int, project_id: int, prompt: str):
    asyncio.run(run_modification_pipeline(run_id, project_id, prompt))

@app.post("/projects/{project_id}/runs")
def start_generation_run(project_id: int, payload: CreateRunRequest, background_tasks: BackgroundTasks):
    run = create_run(project_id, payload.entrypoint)
    background_tasks.add_task(run_background_pipeline, run["id"], project_id, payload.prompt)
    return {"run_id": run["id"], "status": run["status"], "attempts": run["attempts"]}

@app.get("/runs/{run_id}")
def fetch_run(run_id: int):
    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run

@app.get("/runs/{run_id}/logs")
def fetch_logs(run_id: int):
    return list_logs(run_id)

@app.post("/projects/{project_id}/runs/{run_id}/modify")
def modify_run(project_id: int, run_id: int, payload: ModifyRunRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_background_modification, run_id, project_id, payload.prompt)
    return {"message": "Modification started in background."}

@app.get("/projects/{project_id}/runs/{run_id}/download")
def download_project(project_id: int, run_id: int):
    output_dir = os.path.join(STORAGE_DIR, f"project_{project_id}", f"run_{run_id}")
    if not os.path.exists(output_dir):
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    zip_path = shutil.make_archive(os.path.join(output_dir, "project_download"), 'zip', output_dir)
    return FileResponse(zip_path, media_type='application/zip', filename=f"project_{project_id}_run_{run_id}.zip")

@app.get("/projects/{project_id}/runs/{run_id}/files")
def list_files(project_id: int, run_id: int):
    run_dir = Path(STORAGE_DIR) / f"project_{project_id}" / f"run_{run_id}"
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail="Run directory not found")
    
    # Exclude system files and project artifacts
    exclude_names = {'venv', '__pycache__', 'pipeline_output.json', 'backend.log', 'project_download.zip'}
    exclude_exts = {'.zip', '.pyc'}

    def build_tree(current_path: Path):
        name = current_path.name
        rel_path = str(current_path.relative_to(run_dir)).replace("\\", "/")
        if current_path.is_dir():
            children = []
            for p in current_path.iterdir():
                if p.name in exclude_names or p.suffix in exclude_exts or p.name.startswith('.'):
                    continue
                children.append(build_tree(p))
            return {
                "id": rel_path,
                "name": name, 
                "type": "folder", 
                "children": sorted(children, key=lambda x: (x['type'] != 'folder', x['name']))
            }
        else:
            return {"id": rel_path, "name": name, "type": "file"}

    # Return top level children
    tree = []
    for p in run_dir.iterdir():
        if p.name in exclude_names or p.suffix in exclude_exts or p.name.startswith('.'):
            continue
        tree.append(build_tree(p))
        
    return sorted(tree, key=lambda x: (x['type'] != 'folder', x['name']))

@app.get("/projects/{project_id}/runs/{run_id}/files/{file_path:path}")
def get_file_content(project_id: int, run_id: int, file_path: str):
    run_dir = Path(STORAGE_DIR).resolve() / f"project_{project_id}" / f"run_{run_id}"
    target_path = (run_dir / file_path).resolve()
    
    # Security check: ensure path is inside run_dir
    if not str(target_path).startswith(str(run_dir)):
        raise HTTPException(status_code=403, detail="Access denied")
        
    if not target_path.exists() or not target_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
        
    try:
        content = target_path.read_text(encoding='utf-8')
        return {"content": content}
    except UnicodeDecodeError:
        return {"content": "[Binary file content not supported in preview]"}

@app.get("/")
def health_check():
    return {"status": "Modular API is running!"}
