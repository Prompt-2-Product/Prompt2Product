"""
test_pipeline_v10.py
--------------------
  Stage 0: Smart Prompt Enhancement (Ollama qwen2.5:7b-instruct) — only for vague prompts
  Stage 1: TaskSpec    — qwen_taskspec_only_lora_v3 (direct Python, V3 template)
  Stage 2: Code Gen    — qwen-code-model via Ollama (strict system prompt + low temp)
  Stage 3: Repair      — commented out

Usage:
    python test_pipeline_v10.py
    python test_pipeline_v10.py --prompt "fitness app"
    python test_pipeline_v10.py --prompt "Build a gym system with member management and attendance tracking"
"""

import torch
import json
import re
import os
import httpx
import argparse
from unsloth import FastLanguageModel

# ── CONFIG ────────────────────────────────────────────────────────────────────
TASKSPEC_MODEL  = "qwen_taskspec_only_lora_v3"
CODER_MODEL     = "qwen-code-model"
ENHANCE_MODEL   = "qwen2.5:7b-instruct"
OLLAMA_URL      = "http://localhost:11434/api/chat"
MAX_LENGTH_TS   = 1024
JUNK_FILES      = {
    "gikicoder.json", ".env.example", ".gitignore",
    "README.md", "pyproject.toml", ".env"
}

DEFAULT_PROMPT = (
    "Build an AI-powered fitness tracking application that integrates with "
    "smartwatches to track activities, provides personalized workout plans "
    "based on biometric data, and allows users to participate in community "
    "social challenges with leaderboards."
)

ENHANCE_SYSTEM = """You are a product requirements specialist.
Convert a short vague app idea into ONE detailed sentence describing the application.
Rules:
- Identify key user roles and their core actions
- Mention real features, not vague terms
- Output ONE sentence only. No bullets, no headings, no explanation.
- Keep it under 40 words.
Examples:
Input: fitness app
Output: Build an AI-powered fitness tracking app where users can log workouts, track calories, view progress charts, and join community challenges with leaderboards.
Input: school system
Output: Build a school management system where admins manage students and teachers, teachers post assignments and grades, and students view schedules and results.
Input: ecommerce
Output: Build a multi-vendor ecommerce platform where sellers manage products and inventory, customers browse, add to cart, checkout, and track orders."""

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

# ── ARGS ──────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument("--prompt", default=DEFAULT_PROMPT)
args   = parser.parse_args()
PROMPT = args.prompt

# ── LOAD TASKSPEC MODEL ───────────────────────────────────────────────────────
print("\nLoading TaskSpec model (V3)...")
ts_model, ts_tokenizer = FastLanguageModel.from_pretrained(
    model_name=TASKSPEC_MODEL, load_in_4bit=True, max_seq_length=MAX_LENGTH_TS,
)
FastLanguageModel.for_inference(ts_model)
print("TaskSpec model ready.\n")

# ─────────────────────────────────────────────────────────────────────────────
# STAGE 0 — Smart Prompt Enhancement
# ─────────────────────────────────────────────────────────────────────────────
def needs_enhancement(prompt: str) -> bool:
    """
    Returns True only if prompt is too vague to generate a good TaskSpec.
    Skips enhancement if prompt already has enough detail.
    """
    words          = prompt.strip().split()
    word_count     = len(words)
    prompt_lower   = prompt.lower()

    # Always enhance if very short
    if word_count <= 4:
        return True

    # Detail signals — if prompt already mentions these, it's specific enough
    detail_signals = [
        "page", "pages", "route", "routes",
        "endpoint", "endpoints", "api",
        "table", "database", "db",
        "admin", "seller", "customer", "student", "teacher", "doctor", "patient",
        "login", "register", "signup", "auth",
        "dashboard", "profile", "manage", "track", "list",
        "crud", "upload", "download", "report",
        "cart", "order", "payment", "booking",
        "with", "where", "allows", "can", "should",
    ]

    detail_count = sum(1 for s in detail_signals if s in prompt_lower)

    # If prompt has 5+ words AND 2+ detail signals — already detailed enough
    if word_count >= 5 and detail_count >= 2:
        return False

    # If prompt is longer than 15 words — definitely detailed enough
    if word_count > 15:
        return False

    return True


def enhance_prompt(prompt: str) -> str:
    """Enhance a vague prompt using Ollama qwen2.5:7b-instruct."""
    if not needs_enhancement(prompt):
        print(f"   ℹ️  Prompt is detailed — skipping enhancement")
        return prompt

    print(f"   🔧 Prompt is vague ({len(prompt.split())} words) — enhancing...")
    try:
        resp = httpx.post(
            OLLAMA_URL,
            json={
                "model"  : ENHANCE_MODEL,
                "messages": [
                    {"role": "system", "content": ENHANCE_SYSTEM},
                    {"role": "user",   "content": prompt}
                ],
                "options": {"temperature": 0.3, "num_predict": 80},
                "stream" : False,
            },
            timeout=60,
        )
        resp.raise_for_status()
        enhanced = resp.json()["message"]["content"].strip()

        # Safety — if enhancement is way longer than original or looks wrong, use original
        if len(enhanced.split()) > 60 or len(enhanced) < 10:
            print(f"   ⚠️  Enhancement unusable — using original")
            return prompt

        print(f"   ✅ Enhanced: {enhanced[:100]}")
        return enhanced

    except Exception as e:
        print(f"   ⚠️  Enhancement failed ({e}) — using original prompt")
        return prompt

# ─────────────────────────────────────────────────────────────────────────────
# STAGE 1 — TaskSpec
# ─────────────────────────────────────────────────────────────────────────────
def generate_taskspec(prompt: str):
    input_text = (
        f"<|system|>\n"
        f"Generate valid TaskSpec JSON only. Do not output markdown, comments, or explanation.\n"
        f"<|user|>\n{prompt}\n"
        f"<|assistant|>\n"
    )
    inputs    = ts_tokenizer(input_text, return_tensors="pt").to("cuda")
    input_len = inputs["input_ids"].shape[1]
    max_new   = max(50, MAX_LENGTH_TS - input_len - 10)

    with torch.no_grad():
        outputs = ts_model.generate(
            **inputs, max_new_tokens=max_new, temperature=0.3,
            top_p=0.9, repetition_penalty=1.05, do_sample=True,
        )
    full = ts_tokenizer.decode(outputs[0], skip_special_tokens=True)
    raw  = full.split("<|assistant|>")[-1].strip()
    return raw, json.loads(raw)

# ─────────────────────────────────────────────────────────────────────────────
# STAGE 2 — Code Generation via Ollama
# ─────────────────────────────────────────────────────────────────────────────
def generate_code(taskspec: dict) -> str:
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
        tags_resp  = httpx.get("http://localhost:11434/api/tags", timeout=5)
        models     = [m["name"] for m in tags_resp.json().get("models", [])]
        print(f"   Available Ollama models: {models}")
        coder_name = next(
            (m for m in models if "code-model" in m or "giki" in m.lower()),
            CODER_MODEL
        )
        print(f"   Using model: {coder_name}")
    except Exception as e:
        print(f"   ⚠️  Could not list models: {e}")
        coder_name = CODER_MODEL

    resp = httpx.post(
        OLLAMA_URL,
        json={
            "model"  : coder_name,
            "options": {
                "temperature"   : 0.1,   # low temp — follow fine-tuned patterns
                "repeat_penalty": 1.1,   # discourage base model drift
                "top_p"         : 0.9,
            },
            "messages": [
                {"role": "system", "content": CODER_SYSTEM},
                {"role": "user",   "content":
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

# ─────────────────────────────────────────────────────────────────────────────
# ROBUST JSON PARSER
# ─────────────────────────────────────────────────────────────────────────────
def safe_parse(text: str):
    start = text.find("{")
    if start == -1:
        return None
    text = text[start:].strip()
    text = re.sub(r"^```[a-z]*\n?", "", text)
    text = re.sub(r"\n?```$", "", text).strip()

    # Fix JS template literals ${...} → {...}
    text = re.sub(r'\$\{([^}]*)\}', r'{\1}', text)

    # Fix missing newline between import statements
    text = re.sub(r'(import\s+\w+)\s+(from\s+)', r'\1\\n\2', text)

    # Pass 1: strip // comments outside strings
    cleaned_comments = []
    in_string = escape = False
    i = 0
    while i < len(text):
        ch = text[i]
        if escape:
            cleaned_comments.append(ch); escape = False; i += 1; continue
        if ch == "\\" and in_string:
            escape = True; cleaned_comments.append(ch); i += 1; continue
        if ch == '"':
            in_string = not in_string; cleaned_comments.append(ch); i += 1; continue
        if not in_string and ch == "/" and i + 1 < len(text) and text[i+1] == "/":
            while i < len(text) and text[i] != "\n":
                i += 1
            continue
        cleaned_comments.append(ch)
        i += 1
    text = "".join(cleaned_comments)

    # Pass 2: escape unescaped control chars + fix invalid escape sequences
    result = []
    in_string = escape = False
    for ch in text:
        if escape:
            if ch in ('"', '\\', '/', 'b', 'f', 'n', 'r', 't', 'u'):
                result.append('\\')
                result.append(ch)
            else:
                result.append(ch)   # drop bad backslash
            escape = False
            continue
        if ch == "\\" and in_string:
            escape = True
            continue
        if ch == '"':
            in_string = not in_string; result.append(ch); continue
        if in_string:
            if ch == "\n": result.append("\\n")
            elif ch == "\r": pass
            elif ch == "\t": result.append("\\t")
            else: result.append(ch)
        else:
            result.append(ch)

    cleaned = "".join(result)

    try:
        return json.loads(cleaned)
    except:
        pass

    # Bracket repair
    stack = []
    in_str = escape = False
    for ch in cleaned:
        if escape: escape = False; continue
        if ch == "\\" and in_str: escape = True; continue
        if ch == '"': in_str = not in_str; continue
        if in_str: continue
        if ch in "{[": stack.append("}" if ch == "{" else "]")
        elif ch in "}]" and stack: stack.pop()
    try:
        return json.loads(cleaned + "".join(reversed(stack)))
    except:
        return None
def normalize_result(data: dict) -> dict:
    """Normalize result — handle all file formats the coder model produces."""
    if not isinstance(data, dict):
        return data

    # ── Normalize manifest ────────────────────────────────────────────────────
    manifest = data.get("manifest", [])
    if isinstance(manifest, dict):
        # {"files": ["main.py", ...]} or {"main.py": ..., "templates/base.html": ...}
        data["manifest"] = manifest.get("files", list(manifest.keys()))
    elif not isinstance(manifest, list):
        data["manifest"] = []

    # ── Normalize files ───────────────────────────────────────────────────────
    files      = data.get("files", [])
    normalized = []

    # Case 1 — files is a dict
    if isinstance(files, dict):
        for path, value in files.items():
            if isinstance(value, str):
                # {"requirements.txt": "fastapi uvicorn..."}
                if value.strip():
                    normalized.append({"path": path, "content": value})
                else:
                    print(f"    ⚠️  Empty content for: {path}")

            elif isinstance(value, dict):
                # {"main.py": {"content": "from fastapi..."}}
                content = value.get("content", "")
                if content.strip():
                    normalized.append({"path": path, "content": content})
                else:
                    print(f"    ⚠️  Empty content for: {path}")

            elif value is None:
                print(f"    ⚠️  None content for: {path}")

            else:
                # Unknown format — try str conversion
                try:
                    normalized.append({"path": path, "content": str(value)})
                except:
                    print(f"    ⚠️  Could not convert content for: {path}")

    # Case 2 — files is a list
    elif isinstance(files, list):
        for f in files:
            if isinstance(f, dict):
                path    = f.get("path", f.get("name", "")).strip()
                content = f.get("content", "")

                # Handle nested content dict: {"path": "x", "content": {"code": "..."}}
                if isinstance(content, dict):
                    content = content.get("code", content.get("content", str(content)))

                if not path:
                    print(f"    ⚠️  Missing path in file entry")
                    continue

                if content.strip():
                    normalized.append({"path": path, "content": content})
                else:
                    print(f"    ⚠️  Empty content for: {path}")

            elif isinstance(f, str):
                # Filename only — no content available
                print(f"    ⚠️  No content for: {f}")

            else:
                print(f"    ⚠️  Unknown file entry type: {type(f)}")

    else:
        print(f"    ⚠️  Unexpected files type: {type(files)}")

    data["files"] = normalized
    return data
# ─────────────────────────────────────────────────────────────────────────────
# POST-PROCESSING HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def fix_template_response(content: str) -> str:
    """Fix old-style TemplateResponse to new request= keyword style."""
    def replace_old_style(match):
        name    = match.group(1)
        context = match.group(2)
        context = re.sub(r"['\"]request['\"]\s*:\s*request\s*,?\s*", "", context).strip()
        context = context.strip("{} \n")
        if context:
            return f"TemplateResponse(request=request, name={name}, context={{{context}}})"
        return f"TemplateResponse(request=request, name={name}, context={{}})"

    content = re.sub(
        r"TemplateResponse\(\s*(['\"][^'\"]+['\"])\s*,\s*(\{[^}]+\})\s*\)",
        replace_old_style, content
    )
    # Fix missing request=
    content = re.sub(
        r"TemplateResponse\(\s*(name\s*=\s*['\"][^'\"]+['\"])",
        r"TemplateResponse(request=request, \1",
        content
    )
    # Fix positional request arg
    content = re.sub(
        r"TemplateResponse\(\s*request\s*,\s*(['\"][^'\"]+['\"])\s*,\s*(\{[^}]+\})\s*\)",
        lambda m: f"TemplateResponse(request=request, name={m.group(1)}, context={m.group(2)})",
        content
    )
    # Fix return dict style
    def replace_dict_return(match):
        context = match.group(1)
        context = re.sub(r"['\"]request['\"]\s*:\s*request\s*,?\s*", "", context).strip()
        context = context.strip("{} \n")
        if context:
            return f"return templates.TemplateResponse(request=request, name='home.html', context={{{context}}})"
        return f"return templates.TemplateResponse(request=request, name='home.html', context={{}})"
    content = re.sub(
        r"return\s+\{\s*['\"]request['\"]\s*:\s*request\s*,?([^}]*)\}",
        replace_dict_return, content
    )
    return content


def fix_python_imports(path: str, content: str) -> str:
    """Fix bad imports the coder model commonly generates."""
    fname = os.path.basename(path)

    # Replace entire config.py / settings.py
    if fname in ("config.py", "settings.py"):
        return (
            'class Settings:\n'
            '    SECRET_KEY          = "dev_secret_key"\n'
            '    SMARTWATCH_API_KEY  = "dev_smartwatch_key"\n'
            '    DATABASE_URL        = "sqlite:///./app.db"\n'
            '    DEBUG               = True\n'
            '    APP_NAME            = "App"\n\n'
            'settings = Settings()\n'
        )

    # Replace entire deps.py / auth.py / security.py
    if fname in ("deps.py", "auth.py", "dependencies.py", "security.py"):
        return (
            '# Auth deps stub — jose/passlib replaced\n'
            'from fastapi import HTTPException\n\n'
            'async def get_current_active_user():\n'
            '    return {"id": 1, "name": "Demo User", "email": "demo@example.com"}\n\n'
            'async def get_current_user():\n'
            '    return {"id": 1, "name": "Demo User", "email": "demo@example.com"}\n'
        )

    # Replace entire models.py if uses ORM
    if fname == "models.py" and (
        "from tortoise" in content or "from sqlalchemy" in content
    ):
        return (
            '# Auto-generated in-memory db — ORM replaced\n'
            'db = {\n'
            '    "users": [],\n'
            '    "items": [],\n'
            '    "records": [],\n'
            '}\n\n'
            'class MockModel:\n'
            '    @classmethod\n'
            '    def get_all(cls):\n'
            '        return []\n\n'
            'WorkoutPlan          = MockModel\n'
            'CommunityChallenge   = MockModel\n'
            'User                 = MockModel\n'
            'ActivityLog          = MockModel\n'
            'ChallengeParticipant = MockModel\n'
        )

    # Replace session.py if uses ORM
    if fname == "session.py" and ("tortoise" in content or "sqlalchemy" in content):
        return (
            '# Session stub — ORM replaced\n'
            'def get_db():\n'
            '    return {}\n'
        )

    # Remove bad imports
    content = re.sub(r"from tortoise[^\n]*\n", "", content)
    content = re.sub(r"from sqlalchemy[^\n]*\n", "", content)
    content = re.sub(r"import sqlalchemy[^\n]*\n", "", content)
    content = re.sub(r"from jinja2_fspaths[^\n]*\n", "", content)
    content = re.sub(r"import jinja2_fspaths[^\n]*\n", "", content)
    content = re.sub(r"from jinja2[-_]fs[^\n]*\n", "", content)
    content = re.sub(r"[^\n]*jinja2_fspaths[^\n]*\n", "", content)
    content = re.sub(r"from jose[^\n]*\n", "", content)
    content = re.sub(r"import jose[^\n]*\n", "", content)
    content = re.sub(r"from passlib[^\n]*\n", "", content)
    content = re.sub(r"import passlib[^\n]*\n", "", content)
    content = re.sub(r"from cryptography[^\n]*\n", "", content)
    content = re.sub(r"from app\.core\.config import[^\n]*\n", "", content)
    content = re.sub(r"from app\.config import[^\n]*\n", "", content)
    content = re.sub(r"from config import[^\n]*\n", "", content)
    content = re.sub(r"from dotenv[^\n]*\n", "", content)
    content = re.sub(r"import dotenv[^\n]*\n", "", content)
    content = re.sub(r"load_dotenv\(\)[^\n]*\n", "", content)
    content = re.sub(r"from app\.templates[^\n]*\n", "", content)
    content = re.sub(r"from templates[^\n]*\n", "", content)
    content = content.replace("from pydantic import BaseSettings", "# BaseSettings removed")
    content = content.replace("from pydantic_settings import BaseSettings", "# BaseSettings removed")

    # Fix response_class=templates.TemplateResponse
    content = re.sub(
        r"response_class\s*=\s*templates\.TemplateResponse",
        "response_class=HTMLResponse", content
    )

    # Fix settings references after config import removed
    if fname == "main.py" and "settings." in content and "class Settings" not in content:
        content = re.sub(r"settings\.[A-Z_a-z]+", '"dev_value"', content)

    # Fix import app then app.mount pattern
    if fname == "main.py" and "import app" in content and "app = FastAPI()" not in content:
        content = re.sub(r"^import app\n", "", content, flags=re.MULTILINE)
        lines  = content.split("\n")
        insert = 0
        for i, line in enumerate(lines):
            if line.startswith("from ") or line.startswith("import "):
                insert = i + 1
        lines.insert(insert, "\napp = FastAPI()\n")
        content = "\n".join(lines)

    # Ensure templates initialized if templates import removed
    if fname == "main.py" and "Jinja2Templates" not in content and "templates" in content:
        templates_dir = "app/templates" if "app/" in path else "templates"
        content = content.replace(
            "app = FastAPI()",
            f'app = FastAPI()\ntemplates = Jinja2Templates(directory="{templates_dir}")'
        )

    return content


def fix_child_template(path: str, content: str) -> str:
    """Ensure non-base templates correctly extend base.html."""
    fname = os.path.basename(path)
    if fname == "base.html" or "templates/" not in path:
        return content

    if content.strip().startswith("{% extends"):
        block_count = content.count("{% block content %}")
        if block_count <= 1:
            return content
        parts = content.split("{% block content %}")
        return "{% extends 'base.html' %}\n{% block content %}" + parts[-1]

    body_match = re.search(r"<body[^>]*>(.*?)</body>", content, re.DOTALL)
    if body_match:
        inner = body_match.group(1).strip()
        inner = re.sub(r"\{%-?\s*block content\s*-?%\}.*?\{%-?\s*endblock\s*-?%\}",
                       "", inner, count=1, flags=re.DOTALL).strip()
        return f"{{% extends 'base.html' %}}\n{{% block content %}}\n{inner}\n{{% endblock %}}"

    cleaned = re.sub(r"\{%-?\s*block content\s*-?%\}", "", content, count=1)
    cleaned = re.sub(r"\{%-?\s*endblock\s*-?%\}", "", cleaned, count=1)
    return f"{{% extends 'base.html' %}}\n{{% block content %}}\n{cleaned.strip()}\n{{% endblock %}}"


def detect_run_cmd(output_dir: str, port: int = 8001) -> str:
    """Detect correct uvicorn command based on where main.py is."""
    candidates = [
        ("app/main.py",        "uvicorn app.main:app"),
        ("src/main.py",        "uvicorn src.main:app"),
        ("giki_coder/main.py", "uvicorn giki_coder.main:app"),
        ("main.py",            "uvicorn main:app"),
    ]
    for rel_path, cmd in candidates:
        if os.path.exists(os.path.join(output_dir, rel_path)):
            return f"{cmd} --reload --port {port}"
    return f"uvicorn main:app --reload --port {port}"


def extract_files(result: dict, output_dir: str):
    files    = result.get("files", [])
    manifest = result.get("manifest", [])
    created  = []

    for file_entry in files:
        # Skip non-dict entries — model returned filename only without content
        if not isinstance(file_entry, dict):
            print(f"    ⏭️  Skipped non-dict entry: {file_entry}")
            continue

        path    = file_entry.get("path", "").strip()
        content = file_entry.get("content", "")

        if not path or os.path.basename(path) in JUNK_FILES:
            print(f"    ⏭️  Skipped: {path}"); continue

        # Skip binary/empty placeholders
        if content.strip() in ["<placeholder-image-data>", "<binary data>", "<binary>", ""]:
            print(f"    ⏭️  Skipped binary/empty: {path}"); continue

        # Strip .jinja2 extensions
        path = path.replace(".html.jinja2", ".html").replace(".jinja2", ".html")

        # Fix Python files
        if path.endswith(".py"):
            content = fix_template_response(content)
            content = fix_python_imports(path, content)

        # Fix HTML templates
        if path.endswith(".html"):
            content = fix_child_template(path, content)

        full_path = os.path.join(output_dir, path)
        os.makedirs(os.path.dirname(full_path) or output_dir, exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        created.append(path)
        print(f"    ✅ {path}  ({len(content):,} chars)")

    # Auto requirements.txt — write if missing or has bad packages
    req_path  = os.path.join(output_dir, "requirements.txt")
    needs_req = not os.path.exists(req_path)
    if not needs_req:
        with open(req_path) as f:
            rc = f.read()
        if any(bad in rc for bad in ["tortoise", "sqlalchemy", "jinja2-fs", "jose", "passlib"]):
            needs_req = True
    if needs_req:
        with open(req_path, "w") as f:
            f.write("fastapi\nuvicorn\njinja2\npython-multipart\naiofiles\nbcrypt\n")
        print(f"    🔧 requirements.txt written")

    # Auto static folder if StaticFiles mounted
    for rel in ["main.py", "app/main.py"]:
        main_path = os.path.join(output_dir, rel)
        if os.path.exists(main_path):
            with open(main_path) as f:
                mc = f.read()
            if "StaticFiles" in mc:
                m          = re.search(r"StaticFiles\(directory=['\"]([^'\"]+)['\"]", mc)
                static_dir = m.group(1) if m else "static"
                full_static = os.path.join(output_dir, static_dir)
                if not os.path.exists(full_static):
                    os.makedirs(full_static, exist_ok=True)
                    print(f"    🔧 Created {static_dir}/ folder")

    return created, manifest


def validate_output(result: dict, created: list, manifest: list):
    issues     = []
    file_paths = [f["path"] for f in result.get("files", [])]

    if not any(p.endswith("main.py") for p in file_paths):
        issues.append("❌ Missing main.py")
    if not any("base.html" in p and "partials" not in p for p in file_paths):
        issues.append("❌ Missing base.html")

    for f in result.get("files", []):
        path    = f.get("path", "")
        content = f.get("content", "")
        if "templates/" in path and "partials" not in path and "base.html" not in path:
            if "extends" not in content:
                issues.append(f"⚠️  {path} does not extend base.html")
        if "templates/" in path:
            nested = re.findall(r"\{\{[^}]*\b(\w+\.\w+\.\w+)\b[^}]*\}\}", content)
            nested = [n for n in nested if not any(x in n for x in ["loop.", "self.", "url_for"])]
            if nested:
                issues.append(f"⚠️  Nested dict in {path}: {list(set(nested))}")
    return issues

# ─────────────────────────────────────────────────────────────────────────────
# PIPELINE
# ─────────────────────────────────────────────────────────────────────────────
print("="*60)
print("PIPELINE v10 — Enhance → TaskSpec → CodeGen")
print("="*60)
print(f"Prompt: {PROMPT}\n")

# ── Stage 0: Smart Enhancement ────────────────────────────────────────────────
print("── STAGE 0: Smart Prompt Enhancement ───────────────────────")
enhanced_prompt = enhance_prompt(PROMPT)
if enhanced_prompt != PROMPT:
    print(f"   Original : {PROMPT}")
    print(f"   Enhanced : {enhanced_prompt}")

# ── Stage 1: TaskSpec ─────────────────────────────────────────────────────────
print("\n── STAGE 1: TaskSpec (V3) ───────────────────────────────────")
try:
    raw_ts, taskspec = generate_taskspec(enhanced_prompt)
    print(raw_ts)
    print(f"\n✅ {taskspec.get('app_name')}")
    print(f"   pages:{len(taskspec.get('frontend',{}).get('pages',[]))}  "
          f"endpoints:{len(taskspec.get('backend',{}).get('endpoints',[]))}  "
          f"tables:{len(taskspec.get('database',{}).get('tables',[]))}")
except Exception as e:
    print(f"❌ TaskSpec failed: {e}"); exit(1)

del ts_model
torch.cuda.empty_cache()
print("\nTaskSpec model unloaded from VRAM.")

# ── Stage 2: Code Generation ──────────────────────────────────────────────────
print("\n── STAGE 2: Code Generation (Ollama) ────────────────────────")
print("Generating... (1-3 mins)")
try:
    raw_code = generate_code(taskspec)
except Exception as e:
    print(f"❌ Code generation failed: {e}")
    print("\nTip: Run 'ollama list' to check available model names")
    exit(1)

with open("raw_code_output.json", "w") as f:
    f.write(raw_code)

result = safe_parse(raw_code)
if result is None:
    print("❌ Could not parse JSON — saved to raw_code_output.json")
    print("Preview:", raw_code[:300])
    exit(1)
result = normalize_result(result)  # ← add this line
print(f"✅ {len(result.get('files', []))} files generated")
for f in result.get("files", []):
    if isinstance(f, dict):
        print(f"   • {f.get('path', '?')}")
    else:
        print(f"   • {f}")
# ── Extract ────────────────────────────────────────────────────────────────────
app_name   = taskspec.get("app_name", "app")
app_name   = re.sub(r"[^a-zA-Z0-9\s]", "", app_name).strip()
app_name   = app_name.replace(" ", "_").lower()[:30]
output_dir = f"generated_{app_name}"

print(f"\n── Extracting to ./{output_dir}/ ────────────────────────────")
created, manifest = extract_files(result, output_dir)

# ── Validate ───────────────────────────────────────────────────────────────────
print("\n── Validation ───────────────────────────────────────────────")
issues = validate_output(result, created, manifest)
if issues:
    for issue in issues:
        print(f"  {issue}")
else:
    print("  ✅ All checks passed")

# ── Run script ─────────────────────────────────────────────────────────────────
run_cmd = detect_run_cmd(output_dir)
run_sh  = os.path.join(output_dir, "run.sh")
with open(run_sh, "w") as f:
    f.write("#!/bin/bash\n")
    f.write("pip install fastapi uvicorn jinja2 python-multipart aiofiles bcrypt\n")
    f.write(run_cmd + "\n")
os.chmod(run_sh, 0o755)

# ── Save ───────────────────────────────────────────────────────────────────────
with open(f"{output_dir}/pipeline_output.json", "w", encoding="utf-8") as f:
    json.dump({
        "user_prompt"    : PROMPT,
        "enhanced_prompt": enhanced_prompt,
        "taskspec"       : taskspec,
        "result"         : result,
    }, f, indent=2, ensure_ascii=False)

print(f"\n✅ Saved to ./{output_dir}/")
print(f"▶  cd {output_dir} && {run_cmd}")
print("\n🎉 Pipeline v10 PASSED!")
