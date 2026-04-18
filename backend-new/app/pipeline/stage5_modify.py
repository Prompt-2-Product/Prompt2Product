import os
import shutil
import json
import httpx
from typing import List, Dict, Tuple
from app.core.config import OLLAMA_URL, CODER_MODEL
from app.extensions.parsers import safe_parse

MODIFY_SYSTEM = """You are a UI modification specialist. 
The user wants to tweak the styles or content of a specific page.

RULES:
- ONLY modify the provided context.
- Keep the overall design consistent.
- Output ONLY a JSON object with a "files" array.
- Each file MUST have "path" and "content" (the FULL updated file content).
- DO NOT use markdown code blocks or explanation text.

Example format:
{
  "files": [
    {"path": "templates/index.html", "content": "... full code with changes ..."}
  ]
}"""

def find_target_files(output_dir: str, user_request: str) -> List[str]:
    """
    Finds which files to send as context.
    If the user mentions a specific page, target that.
    Otherwise, target CSS and common layout files.
    """
    request_low = user_request.lower()
    all_files = []
    
    # Walk the directory to find HTML and CSS files
    for root, _, filenames in os.walk(output_dir):
        for f in filenames:
            if f.endswith(('.html', '.css', '.js')):
                rel = os.path.relpath(os.path.join(root, f), output_dir)
                all_files.append(rel)

    # Keywords to match pages
    # e.g. "contact page" -> contact.html
    targets = []
    for f in all_files:
        name_no_ext = os.path.splitext(os.path.basename(f))[0].lower()
        if name_no_ext in request_low:
            targets.append(f)
    
    # If no specific page found, or we want shared styles
    if not targets:
        # Default to index and common css
        for f in all_files:
            if "index.html" in f or "base.html" in f or f.endswith(".css"):
                targets.append(f)
    else:
        # Always include CSS if found
        for f in all_files:
            if f.endswith(".css") and f not in targets:
                targets.append(f)
                
    return targets[:5] # Limit to top 5 files to save tokens

async def apply_modification_async(output_dir: str, user_request: str, log_fn) -> bool:
    # 1. Create backup
    backup_dir = os.path.join(output_dir, ".backup")
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir, exist_ok=True)
        # Copy current state to backup (excluding venv)
        for item in os.listdir(output_dir):
            if item in ["venv", ".backup", "__pycache__"]: continue
            s = os.path.join(output_dir, item)
            d = os.path.join(backup_dir, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)
        log_fn("modify", "Backup created in .backup/")

    # 2. Extract context
    targets = find_target_files(output_dir, user_request)
    if not targets:
        log_fn("modify", "No relevant files found for modification.", "WARN")
        return False
        
    log_fn("modify", f"Targeting files for edit: {', '.join(targets)}")
    
    context_blocks = []
    for t in targets:
        with open(os.path.join(output_dir, t), 'r', encoding='utf-8') as f:
            content = f.read()
            context_blocks.append(f"--- FILE: {t} ---\n{content}")
    
    context_str = "\n\n".join(context_blocks)

    # 3. Call LLM
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                OLLAMA_URL,
                json={
                    "model": CODER_MODEL,
                    "messages": [
                        {"role": "system", "content": MODIFY_SYSTEM},
                        {"role": "user", "content": f"USER REQUEST: {user_request}\n\nCURRENT CODE:\n{context_str}\n\nApply the change and return FULL updated files in JSON."}
                    ],
                    "options": {"temperature": 0.2},
                    "stream": False
                },
                timeout=120
            )
            resp.raise_for_status()
            raw_response = resp.json()["message"]["content"]
            
            # 4. Parse and Write
            data = safe_parse(raw_response)
            if not data or "files" not in data:
                log_fn("modify", "Failed to parse modification response.", "ERROR")
                return False
                
            for f_entry in data["files"]:
                path = f_entry.get("path")
                content = f_entry.get("content")
                if path and content:
                    full_path = os.path.join(output_dir, path)
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    with open(full_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    log_fn("modify", f"Updated {path}")
            
            return True
            
    except Exception as e:
        log_fn("modify", f"Error during modification: {e}", "ERROR")
        return False
