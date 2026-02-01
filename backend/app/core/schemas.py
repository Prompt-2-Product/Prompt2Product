from pydantic import BaseModel

class CreateProjectRequest(BaseModel):
    name: str

class CreateRunRequest(BaseModel):
    prompt: str
    entrypoint: str = "main.py"

class RunStatusResponse(BaseModel):
    run_id: int
    status: str
    attempts: int
