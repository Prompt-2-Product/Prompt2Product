import os
import re
import ast
import json
import time
import shutil
import httpx
import subprocess
from typing import Tuple, List
from app.extensions.parsers import safe_parse, normalize_result
from app.extensions.fixers import fix_template_response, fix_python_imports, fix_child_template
from app.core.config import OLLAMA_URL, CODER_MODEL

JUNK_FILES = {
    "gikicoder.json", ".env.example", ".gitignore",
    "README.md", "pyproject.toml", ".env"
}

REPAIR_MODEL = CODER_MODEL # Default to using the same coder model for repairs

def extract_files(result: dict, output_dir: str, log_fn=None):
    """Writes files from the result dictionary to the specified directory."""
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
            
        if log_fn:
            log_fn('extract', f"Materializing {path}...")

        if content.strip() in ["<placeholder-image-data>", "<binary data>", "<binary>", ""]:
            continue

        # Normalization of extensions
        path = path.replace(".html.jinja2", ".html").replace(".jinja2", ".html")

        # Apply rule-based fixers
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

    # Ensure requirements.txt exists and is valid
    req_path = os.path.join(output_dir, "requirements.txt")
    if os.path.exists(req_path):
        with open(req_path) as f:
            rc = f.read()
        if any(bad in rc for bad in ["tortoise", "sqlalchemy", "jinja2-fs", "jose", "passlib"]):
            with open(req_path, "w") as f:
                f.write("fastapi\nuvicorn\njinja2\npython-multipart\naiofiles\nbcrypt\n")
    else:
        with open(req_path, "w") as f:
            f.write("fastapi\nuvicorn\njinja2\npython-multipart\naiofiles\nbcrypt\n")

    return created, manifest

def run_sanity_tests(output_dir: str, result: dict) -> tuple[bool, list]:
    """
    Static checks on generated files — no execution needed.
    Returns (passed, list of issues found)
    """
    issues = []
    files  = result.get("files", [])
    paths  = [f.get("path", "") for f in files if isinstance(f, dict)]

    # Check 1 — main.py exists
    has_main = any(p.endswith("main.py") for p in paths)
    if not has_main:
        issues.append("Missing main.py")

    # Check 2 — base.html exists
    has_base = any("base.html" in p and "partials" not in p for p in paths)
    if not has_base:
        issues.append("Missing base.html")

    # Check 3 — Python syntax valid
    for f in files:
        if not isinstance(f, dict): continue
        path    = f.get("path", "")
        content = f.get("content", "")
        if not path.endswith(".py"): continue
        try:
            ast.parse(content)
        except SyntaxError as e:
            issues.append(f"Syntax error in {path}: {e.msg} line {e.lineno}")

    # Check 4 — No bad imports in main.py
    for f in files:
        if not isinstance(f, dict): continue
        if not f.get("path", "").endswith("main.py"): continue
        content = f.get("content", "")
        bad = ["from tortoise", "from sqlalchemy", "jinja2_fspaths",
               "from jose", "from passlib", "import app\n"]
        for b in bad:
            if b in content:
                issues.append(f"Bad import in main.py: {b.strip()}")

    # Check 5 — app = FastAPI() present in main.py
    for f in files:
        if not isinstance(f, dict): continue
        if not f.get("path", "").endswith("main.py"): continue
        if "app = FastAPI()" not in f.get("content", ""):
            issues.append("main.py missing: app = FastAPI()")

    # Check 6 — requirements.txt has no bad packages
    for f in files:
        if not isinstance(f, dict): continue
        if "requirements.txt" not in f.get("path", ""): continue
        content = f.get("content", "")
        for bad in ["tortoise", "sqlalchemy", "jinja2-fs", "jose", "passlib"]:
            if bad in content:
                issues.append(f"Bad package in requirements.txt: {bad}")

    passed = len(issues) == 0
    return passed, issues

def run_correctness_tests(output_dir: str, run_cmd: str, port: int = 8099) -> tuple[bool, list]:
    """
    Start the app, hit all routes, check for 500 errors.
    Returns (passed, list of issues found)
    """
    issues  = []
    process = None

    # Modify run_cmd to use test port
    test_cmd = re.sub(r"--port \d+", f"--port {port}", run_cmd)
    if "--port" not in test_cmd:
        test_cmd += f" --port {port}"

    try:
        # Start the app
        print(f"    🚀 Testing app on port {port}...")
        process = subprocess.Popen(
            test_cmd.split(),
            cwd            = output_dir,
            stdout         = subprocess.PIPE,
            stderr         = subprocess.PIPE,
        )

        # Wait for startup
        time.sleep(5)

        # Check if process crashed immediately
        if process.poll() is not None:
            stderr = process.stderr.read().decode()
            issues.append(f"App crashed on startup: {stderr[:500]}")
            return False, issues

        # Hit all routes
        base_url = f"http://localhost:{port}"
        routes_to_test = ["/"]

        # Extract routes from main.py
        for root, dirs, files_list in os.walk(output_dir):
            for fname in files_list:
                if fname == "main.py":
                    with open(os.path.join(root, fname)) as mf:
                        mc = mf.read()
                    found = re.findall(r'@app\.get\(["\']([^"\']+)["\']', mc)
                    routes_to_test.extend(found)
                    break

        routes_to_test = list(set(routes_to_test))

        for route in routes_to_test:
            # Skip API routes and dynamic routes that might fail without params
            if "/api/" in route or "{" in route:
                continue
            try:
                resp = httpx.get(
                    f"{base_url}{route}",
                    timeout          = 5,
                    follow_redirects = True,
                )
                if resp.status_code == 500:
                    issues.append(f"Route {route} returned 500")
                elif resp.status_code not in [200, 301, 302, 307, 308, 404]:
                    # 404 is allowed as it might be a missing static file, but 500 is a logic error
                    print(f"    ⚠️ {route} → {resp.status_code}")
                else:
                    print(f"    ✅ {route} → {resp.status_code}")
            except Exception as e:
                issues.append(f"Route {route} failed: {str(e)[:100]}")

    except Exception as e:
        issues.append(f"Could not start app: {e}")

    finally:
        if process:
            # Capture any stderr before terminating
            if process.poll() is not None:
                err = process.stderr.read().decode()
                if err: issues.append(f"Runtime error: {err[:500]}")
            
            # Kill process group to ensure children are gone
            process.terminate()
            try:
                process.wait(timeout=3)
            except:
                process.kill()

    passed = len(issues) == 0
    return passed, issues

def repair_with_error(result: dict, error_log: str) -> dict:
    """Send error log to repair LLM for targeted fix."""
    
    # Find the file that caused the error
    file_match = re.search(r'File ".*?([^/]+\.(?:py|html))"', error_log)
    target_file = file_match.group(1) if file_match else None

    repaired = []
    for f in result.get("files", []):
        path    = f.get("path", "")
        content = f.get("content", "")
        fname   = os.path.basename(path)

        # Only repair the file that caused the error
        if target_file and fname != target_file:
            repaired.append(f)
            continue

        if not path.endswith((".py", ".html")):
            repaired.append(f)
            continue

        print(f"    🔧 Mini-repair: {path} (error-targeted)")
        try:
            resp = httpx.post(
                OLLAMA_URL,
                json={
                    "model"  : REPAIR_MODEL,
                    "messages": [
                        {
                            "role"   : "system",
                            "content": (
                                "You are a FastAPI code repair assistant. "
                                "Fix the file based on the runtime error provided. "
                                "Return ONLY the fixed file content. "
                                "No explanation, no markdown fences."
                            )
                        },
                        {
                            "role"   : "user",
                            "content": (
                                f"File: {path}\n\n"
                                f"Runtime Error:\n{error_log[:1000]}\n\n"
                                f"Current Content:\n{content}"
                            )
                        }
                    ],
                    "stream": False,
                },
                timeout=120,
            )
            data = resp.json()
            fixed = ""
            if "message" in data:
                fixed = data["message"]["content"].strip()
            elif "response" in data:
                fixed = data["response"].strip()
                
            fixed = re.sub(r"^```[a-z]*\n?", "", fixed)
            fixed = re.sub(r"\n?```$", "", fixed).strip()
            
            if fixed and len(fixed) > 20:
                repaired.append({"path": path, "content": fixed})
            else:
                repaired.append(f)
        except Exception as e:
            print(f"      ❌ Mini-repair failed: {e}")
            repaired.append(f)

    result["files"] = repaired
    return result

def extract_and_repair(raw_code: str, output_dir: str):
    """Legacy wrapper for backward compatibility."""
    result = safe_parse(raw_code)
    if result is None:
        raise ValueError("Could not parse JSON output from model")
    result = normalize_result(result)
    created, manifest = extract_files(result, output_dir)
    return created, manifest, result
