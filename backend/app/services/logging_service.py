from sqlmodel import Session
from app.db.repo import add_log

def log(session: Session, run_id: int, stage: str, message: str, level: str = "INFO"):
    # Mirror logs to terminal so users can trace flow live.
    print(f"[{level}] [run:{run_id}] [{stage}] {message}", flush=True)
    add_log(session, run_id=run_id, stage=stage, level=level, message=message)
