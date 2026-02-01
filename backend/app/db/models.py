from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field

class Project(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Run(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(index=True)
    status: str = Field(default="queued")  # queued | running | success | failed
    entrypoint: str = Field(default="main.py")
    attempts: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class LogEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: int = Field(index=True)
    stage: str
    level: str = Field(default="INFO")  # INFO | ERROR
    message: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
