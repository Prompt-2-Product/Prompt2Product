import os
import re
from app.extensions.parsers import safe_parse, normalize_result
from app.extensions.fixers import fix_template_response, fix_python_imports, fix_child_template

JUNK_FILES = {
    "gikicoder.json", ".env.example", ".gitignore",
    "README.md", "pyproject.toml", ".env"
}

def extract_and_repair(raw_code: str, output_dir: str):
    result = safe_parse(raw_code)
    if result is None:
        raise ValueError("Could not parse JSON output from model")
        
    result = normalize_result(result)
    
    files = result.get("files", [])
    manifest = result.get("manifest", [])
    created = []

    for file_entry in files:
        if not isinstance(file_entry, dict):
            continue

        path = file_entry.get("path", "").strip()
        content = file_entry.get("content", "")

        if not path or os.path.basename(path) in JUNK_FILES:
            continue

        if content.strip() in ["<placeholder-image-data>", "<binary data>", "<binary>", ""]:
            continue

        path = path.replace(".html.jinja2", ".html").replace(".jinja2", ".html")

        if path.endswith(".py"):
            content = fix_template_response(content)
            content = fix_python_imports(path, content)

        if path.endswith(".html"):
            content = fix_child_template(path, content)

        full_path = os.path.join(output_dir, path)
        os.makedirs(os.path.dirname(full_path) or output_dir, exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        created.append(path)

    # Auto requirements.txt
    req_path = os.path.join(output_dir, "requirements.txt")
    needs_req = not os.path.exists(req_path)
    if not needs_req:
        with open(req_path) as f:
            rc = f.read()
        if any(bad in rc for bad in ["tortoise", "sqlalchemy", "jinja2-fs", "jose", "passlib"]):
            needs_req = True
    if needs_req:
        with open(req_path, "w") as f:
            f.write("fastapi\nuvicorn\njinja2\npython-multipart\naiofiles\nbcrypt\n")

    # Auto static folder
    for rel in ["main.py", "app/main.py"]:
        main_path = os.path.join(output_dir, rel)
        if os.path.exists(main_path):
            with open(main_path) as f:
                mc = f.read()
            if "StaticFiles" in mc:
                m = re.search(r"StaticFiles\(directory=['\"]([^'\"]+)['\"]", mc)
                static_dir = m.group(1) if m else "static"
                full_static = os.path.join(output_dir, static_dir)
                if not os.path.exists(full_static):
                    os.makedirs(full_static, exist_ok=True)

    return created, manifest, result
