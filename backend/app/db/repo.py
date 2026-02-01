from sqlmodel import Session, select
from app.db.models import Project, Run, LogEvent

def create_project(session: Session, name: str) -> Project:
    p = Project(name=name)
    session.add(p)
    session.commit()
    session.refresh(p)
    return p

def get_project(session: Session, project_id: int) -> Project | None:
    return session.get(Project, project_id)

def list_projects(session: Session) -> list[Project]:
    return list(session.exec(select(Project)).all())

def create_run(session: Session, project_id: int, entrypoint: str = "main.py") -> Run:
    r = Run(project_id=project_id, entrypoint=entrypoint, status="queued")
    session.add(r)
    session.commit()
    session.refresh(r)
    return r

def get_run(session: Session, run_id: int) -> Run | None:
    return session.get(Run, run_id)

def update_run_status(session: Session, run: Run, status: str, attempts: int | None = None) -> Run:
    run.status = status
    if attempts is not None:
        run.attempts = attempts
    session.add(run)
    session.commit()
    session.refresh(run)
    return run

def add_log(session: Session, run_id: int, stage: str, level: str, message: str) -> LogEvent:
    e = LogEvent(run_id=run_id, stage=stage, level=level, message=message)
    session.add(e)
    session.commit()
    session.refresh(e)
    return e

def list_logs(session: Session, run_id: int) -> list[LogEvent]:
    stmt = select(LogEvent).where(LogEvent.run_id == run_id).order_by(LogEvent.id)
    return list(session.exec(stmt).all())
