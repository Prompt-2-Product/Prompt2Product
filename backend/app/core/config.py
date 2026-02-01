from __future__ import annotations
from pydantic import BaseModel
from pathlib import Path
import os

# ✅ Load .env here so it always loads before Settings() is created
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


class Settings(BaseModel):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")
    WORKSPACE_ROOT: Path = Path(__file__).resolve().parents[1] / "storage" / "workspaces"

    # LLM mode
    LLM_MODE: str = os.getenv("LLM_MODE", "ollama").strip().lower()

    # Ollama
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").strip()

    # OpenAI-compatible API
    API_BASE_URL: str = os.getenv("API_BASE_URL", "").strip()
    API_KEY: str = os.getenv("API_KEY", "").strip()

    # Model names (use API_MODEL_* if present, else MODEL_*)
    MODEL_SPEC: str = (os.getenv("API_MODEL_SPEC") or os.getenv("MODEL_SPEC") or "").strip()
    MODEL_CODE: str = (os.getenv("API_MODEL_CODE") or os.getenv("MODEL_CODE") or "").strip()
    MODEL_REPAIR: str = (os.getenv("API_MODEL_REPAIR") or os.getenv("MODEL_REPAIR") or "").strip()

    MAX_REPAIR_ATTEMPTS: int = int(os.getenv("MAX_REPAIR_ATTEMPTS", "2"))


settings = Settings()
