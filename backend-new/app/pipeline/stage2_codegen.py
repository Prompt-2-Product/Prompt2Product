import httpx
import json
from app.core.config import OLLAMA_URL, CODER_MODEL

CODER_SYSTEM = """You are GIKI-Coder. Generate complete FastAPI web applications from TaskSpec JSON.

STRICT RULES — never violate:
- NEVER use tortoise, sqlalchemy, databases, motor — use Python dicts only
- NEVER use jinja2_fspaths or jinja2-fs — use Jinja2Templates(directory='templates') only
- NEVER import jose, passlib, python-jose — use simple mock auth functions
- NEVER use pydantic BaseSettings — hardcode config values directly in main.py
- NEVER import from app.templates — use Jinja2Templates(directory='templates')
- NEVER generate pyproject.toml — generate requirements.txt only
- ALWAYS write app = FastAPI() in main.py
- ALWAYS use TemplateResponse(request=request, name='page.html', context={...})
- ALWAYS include Tailwind CDN in base.html: <script src='https://cdn.tailwindcss.com'></script>
- ALWAYS use requirements.txt with ONLY: fastapi uvicorn jinja2 python-multipart aiofiles bcrypt
- templates directory is always 'templates' (flat) or 'app/templates' (nested)

Respond ONLY with a single valid JSON object containing: plan, manifest, files. No markdown, no explanation, no text outside the JSON."""

async def generate_code_async(taskspec: dict) -> str:
    lean = {
        "app_name"    : taskspec.get("app_name"),
        "app_type"    : taskspec.get("app_type"),
        "description" : taskspec.get("description"),
        "target_users": taskspec.get("target_users"),
        "frontend": {
            "pages"            : taskspec.get("frontend", {}).get("pages", []),
            "shared_components": taskspec.get("frontend", {}).get("shared_components", []),
            "features"         : taskspec.get("frontend", {}).get("features", []),
        },
        "backend" : {"endpoints": taskspec.get("backend", {}).get("endpoints", [])},
        "database": {"tables"   : taskspec.get("database", {}).get("tables", [])},
        "auth_required": taskspec.get("auth_required", False),
    }

    try:
        async with httpx.AsyncClient() as client:
            tags_resp = await client.get("http://localhost:11434/api/tags", timeout=5)
            models = [m["name"] for m in tags_resp.json().get("models", [])]
            coder_name = next((m for m in models if "code-model" in m or "giki" in m.lower()), CODER_MODEL)
    except Exception:
        coder_name = CODER_MODEL

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            OLLAMA_URL,
            json={
                "model": coder_name,
                "options": {
                    "temperature": 0.1,
                    "repeat_penalty": 1.1,
                    "top_p": 0.9,
                },
                "messages": [
                    {"role": "system", "content": CODER_SYSTEM},
                    {"role": "user", "content": 
                        "Generate a complete production-ready web app from this TaskSpec:\n"
                        + json.dumps(lean, indent=2)
                    }
                ],
                "stream": False,
            },
            timeout=360,
        )
        resp.raise_for_status()
        return resp.json()["message"]["content"]
