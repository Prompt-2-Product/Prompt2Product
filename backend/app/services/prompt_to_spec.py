from __future__ import annotations
from typing import List, Literal, Optional
from pydantic import BaseModel, Field

class FieldSpec(BaseModel):
    name: str
    type: str

class ModelSpec(BaseModel):
    name: str
    fields: List[FieldSpec] = Field(default_factory=list)

class ApiSpec(BaseModel):
    method: Literal["GET", "POST", "PUT", "DELETE"]
    path: str
    desc: str = ""

class PageSpec(BaseModel):
    name: str
    route: str
    sections: List[str] = Field(default_factory=list)

class StylingSpec(BaseModel):
    theme: Literal["light", "dark"] = "light"
    primary_color: str = "#2d6cdf"

class ConstraintsSpec(BaseModel):
    frontend: Literal["html_css"] = "html_css"
    backend: Literal["fastapi"] = "fastapi"

class TaskSpec(BaseModel):
    app_name: str = "Generated App"
    pages: List[PageSpec] = Field(default_factory=list)
    api: List[ApiSpec] = Field(default_factory=list)
    data_models: List[ModelSpec] = Field(default_factory=list)
    styling: StylingSpec = Field(default_factory=StylingSpec)
    constraints: ConstraintsSpec = Field(default_factory=ConstraintsSpec)
    notes: Optional[str] = None
