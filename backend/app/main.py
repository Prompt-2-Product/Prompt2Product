from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import Session

from app.db.database import init_db, get_session
from app.db import repo
from app.core.schemas import CreateProjectRequest, CreateRunRequest, RunStatusResponse
from app.services.orchestrator import Orchestrator

app = FastAPI(title="Prompt2Product Backend (MVP)")
orch = Orchestrator()
from dotenv import load_dotenv
load_dotenv()
@app.on_event("startup")
def on_startup():
    init_db()

@app.post("/projects")
def create_project(payload: CreateProjectRequest, session: Session = Depends(get_session)):
    p = repo.create_project(session, payload.name)
    return p

@app.get("/projects")
def list_projects(session: Session = Depends(get_session)):
    return repo.list_projects(session)

@app.post("/projects/{project_id}/runs", response_model=RunStatusResponse)
def start_run(project_id: int, payload: CreateRunRequest, session: Session = Depends(get_session)):
    p = repo.get_project(session, project_id)
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")

    run = repo.create_run(session, project_id, entrypoint=payload.entrypoint)

    # For MVP: run synchronously (later: background worker / queue)
    orch.execute_run(session, run, payload.prompt)

    run = repo.get_run(session, run.id)
    return RunStatusResponse(run_id=run.id, status=run.status, attempts=run.attempts)

@app.get("/runs/{run_id}")
def get_run(run_id: int, session: Session = Depends(get_session)):
    r = repo.get_run(session, run_id)
    if not r:
        raise HTTPException(status_code=404, detail="Run not found")
    return r

@app.get("/runs/{run_id}/logs")
def get_logs(run_id: int, session: Session = Depends(get_session)):
    return repo.list_logs(session, run_id)
