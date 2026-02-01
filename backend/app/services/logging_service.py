from sqlmodel import Session
from app.db.repo import add_log

def log(session: Session, run_id: int, stage: str, message: str, level: str = "INFO"):
    add_log(session, run_id=run_id, stage=stage, level=level, message=message)
