from __future__ import annotations
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from app.services.llm.base import LLMClient
from app.services.prompt_to_spec import TaskSpec

class GenFile(BaseModel):
    path: str
    content: str

class GenOutput(BaseModel):
    files: List[GenFile] = Field(default_factory=list)
    entrypoint: str = "generated_app/backend/main.py"
    run: Dict[str, Any] = Field(default_factory=dict)

SYSTEM_CODE = """You generate a COMPLETE, WORKING, premium full-stack website from a TaskSpec JSON.
- Backend: FastAPI
- Frontend: HTML/CSS/JS with Tailwind CSS (CDN)

🚨 CRITICAL VALIDATION RULES:
1. **EVERY route in main.py MUST have a corresponding HTML file**
2. **EVERY dependency used MUST be in requirements.txt**
3. **EVERY HTML file MUST be complete (<!DOCTYPE html> to </html>)**
4. **NO placeholder routes without files**

═══════════════════════════════════════════════════════════════════
PART 1: BACKEND (main.py)
═══════════════════════════════════════════════════════════════════

MANDATORY IMPORTS (COPY EXACTLY):
```python
import os
from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Optional
```

MANDATORY PATH SETUP (COPY EXACTLY):
```python
app = FastAPI()

# Get the parent directory (generated_app/) from backend/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

# Ensure directories exist
os.makedirs(FRONTEND_DIR, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
```

ROUTE PATTERN (for each page):
```python
@app.get("/")
def read_root(request: Request):
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
```

🚨 CRITICAL: If you use Form(...), you MUST add "python-multipart" to requirements.txt

═══════════════════════════════════════════════════════════════════
PART 2: REQUIREMENTS.TXT
═══════════════════════════════════════════════════════════════════

MANDATORY DEPENDENCIES:
```
fastapi
uvicorn
pydantic
```

CONDITIONAL DEPENDENCIES:
- If you use Form(...): add `python-multipart`
- If you use Jinja2: add `jinja2` (BUT DON'T USE JINJA2!)
- If you use database: add `sqlalchemy`

═══════════════════════════════════════════════════════════════════
PART 3: FRONTEND (HTML FILES)
═══════════════════════════════════════════════════════════════════

DESIGN RULES:
1. **Glassmorphism**: Use `backdrop-filter: blur(12px)` for navbars and cards
2. **Mesh Gradients**: Animated gradients in main.css
3. **Bento Grids**: Modern grid layouts
4. **Google Fonts**: 'Plus Jakarta Sans', 'Inter'
5. **Deep Content**: Minimum 6 sections per page
6. **NO "Lorem ipsum"**: Use realistic placeholder content

HTML TEMPLATE (EVERY file must follow this):
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Page Title</title>
    <link href="/static/main.css" rel="stylesheet">
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;700&family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
</head>
<body class="bg-gray-50 font-['Plus_Jakarta_Sans']">
    <!-- Glassmorphic Navbar -->
    <nav class="fixed w-full backdrop-blur-md bg-white/80 shadow-lg z-50 p-4">
        <!-- Nav content -->
    </nav>

    <!-- Hero Section -->
    <section class="min-h-screen bg-gradient-to-br from-purple-600 to-blue-500 flex items-center justify-center">
        <!-- Hero content -->
    </section>

    <!-- Feature Bento Grid -->
    <section class="container mx-auto p-8">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <!-- Feature cards with backdrop-blur -->
        </div>
    </section>

    <!-- More sections (min 6 total) -->

    <footer class="bg-gray-900 text-white p-8">
        <!-- Footer content -->
    </footer>

    <script src="/static/app.js"></script>
</body>
</html>
```

═══════════════════════════════════════════════════════════════════
PART 4: CSS (main.css)
═══════════════════════════════════════════════════════════════════

MANDATORY STYLES:
```css
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;700&family=Inter:wght@400;600;700&display=swap');

body {
    font-family: 'Plus Jakarta Sans', sans-serif;
}

/* Animated Mesh Gradient */
@keyframes mesh-gradient {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

.mesh-gradient {
    background: linear-gradient(45deg, #667eea 0%, #764ba2 25%, #f093fb 50%, #4facfe 75%, #00f2fe 100%);
    background-size: 400% 400%;
    animation: mesh-gradient 15s ease infinite;
}

/* Glassmorphism */
.glass {
    backdrop-filter: blur(12px);
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
}
```

═══════════════════════════════════════════════════════════════════
PART 5: JAVASCRIPT (app.js)
═══════════════════════════════════════════════════════════════════

```javascript
// Smooth scroll for navigation
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        document.querySelector(this.getAttribute('href')).scrollIntoView({
            behavior: 'smooth'
        });
    });
});

// Form submission handling
const forms = document.querySelectorAll('form');
forms.forEach(form => {
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        // Handle form submission
    });
});
```

═══════════════════════════════════════════════════════════════════
FILE STRUCTURE EXAMPLE
═══════════════════════════════════════════════════════════════════

For a 3-page site, you MUST generate:
```
generated_app/backend/main.py          ← Routes for ALL 3 pages
generated_app/backend/requirements.txt ← ALL dependencies
generated_app/frontend/index.html      ← Full HTML
generated_app/frontend/about.html      ← Full HTML
generated_app/frontend/contact.html    ← Full HTML
generated_app/frontend/main.css        ← Complete styles
generated_app/frontend/app.js          ← JavaScript
```

🚨 VALIDATION CHECKLIST (before returning JSON):
✅ Every route has a corresponding HTML file
✅ Every HTML file is complete (<!DOCTYPE> to </html>)
✅ requirements.txt includes ALL used dependencies
✅ main.py has the mandatory import block
✅ main.py has the mandatory path setup
✅ All HTML files link to /static/main.css
✅ No "Lorem ipsum" or "Feature 1/2/3" placeholders

OUTPUT FORMAT:
Return ONE JSON object with a 'files' array containing ALL files.
"""

from app.core.utils import extract_json, clean_requirements_text, repair_json
import os
import json as json_lib

def aggressive_json_clean(text: str) -> str:
    """
    Aggressively clean JSON output from LLM to fix common issues.
    """
    # 1. CRITICAL FIX: Replace backticks with escaped quotes
    # The LLM is using JavaScript template literal syntax: "content": `...`
    # We need to convert this to valid JSON: "content": "..."
    # This is tricky because the content itself might have quotes that need escaping
    
    import re
    
    # Strategy: Find all "content": `...` patterns and convert them
    def replace_backtick_strings(match):
        key = match.group(1)  # The key name (e.g., "content")
        value = match.group(2)  # The value between backticks
        
        # Escape any quotes in the value
        value = value.replace('\\', '\\\\')  # Escape backslashes first
        value = value.replace('"', '\\"')    # Escape quotes
        value = value.replace('\n', '\\n')   # Escape newlines
        value = value.replace('\r', '\\r')   # Escape carriage returns
        value = value.replace('\t', '\\t')   # Escape tabs
        
        return f'"{key}": "{value}"'
    
    # Match "key": `value` where value can span multiple lines
    # This regex finds: "any_key": `anything including newlines`
    text = re.sub(r'"([^"]+)":\s*`([^`]*)`', replace_backtick_strings, text, flags=re.DOTALL)
    
    # 2. Try to parse and identify other issues
    try:
        json_lib.loads(text)
        return text  # Already valid after backtick fix
    except json_lib.JSONDecodeError as e:
        # Log the error for debugging
        print(f"JSON parse error after backtick fix: {e}")
        pass
    
    # 3. Last resort: return as-is and let the error propagate
    return text

def post_process_output(output: GenOutput) -> GenOutput:
    for file in output.files:
        # Fix common LLM escaping issues (like double \\n)
        if "\\n" in file.content:
            file.content = file.content.replace("\\n", "\n")
        
        # Safety Injection Layer: Fix missing imports in main.py
        if file.path.endswith("main.py"):
            content = file.content
            needed_imports = []
            
            # Check for FastAPI components
            if "FastAPI" in content and "from fastapi import FastAPI" not in content:
                needed_imports.append("from fastapi import FastAPI")
            if "FileResponse" in content and "FileResponse" not in content.split("import")[1 if "import" in content else 0]:
                if "from fastapi.responses import" in content:
                    if "FileResponse" not in content:
                         content = content.replace("from fastapi.responses import ", "from fastapi.responses import FileResponse, ")
                else:
                    needed_imports.append("from fastapi.responses import FileResponse")
            
            # Simple prepend for missed imports
            if needed_imports:
                file.content = "\n".join(needed_imports) + "\n" + content

        if file.path.endswith("requirements.txt"):
            file.content = clean_requirements_text(file.content)
    return output

async def llm_spec_to_code(llm: LLMClient, model: str, spec: TaskSpec) -> GenOutput:
    user = f"TASKSPEC_JSON:\n{spec.model_dump_json(indent=2)}\n\nReturn code files in ONE JSON object with a 'files' key."
    current_system = SYSTEM_CODE
    
    attempts = 0
    max_attempts = 3
    
    while attempts < max_attempts:
        attempts += 1
        try:
            # Increase max_tokens for full code generation (multi-file JSON is large)
            raw = await llm.chat(model=model, system=current_system, user=user, max_tokens=8192)
            
            # Save raw output for debugging
            try:
                debug_path = os.path.join(os.getcwd(), f"llm_output_attempt_{attempts}.txt")
                with open(debug_path, "w", encoding="utf-8") as f:
                    f.write(raw)
            except:
                pass
            
            cleaned = extract_json(raw)
            repaired = repair_json(cleaned)
            repaired = aggressive_json_clean(repaired)
            
            # Try to parse with better error handling
            try:
                output = GenOutput.model_validate_json(repaired)
            except Exception as parse_error:
                # Save the cleaned/repaired version for debugging
                try:
                    debug_path = os.path.join(os.getcwd(), f"cleaned_json_attempt_{attempts}.txt")
                    with open(debug_path, "w", encoding="utf-8") as f:
                        f.write(f"PARSE ERROR: {str(parse_error)}\n\n")
                        f.write(repaired)
                except:
                    pass
                raise parse_error
            
            return post_process_output(output) # Success Path
            
        except Exception as e:
            error_msg = str(e)
            print(f"JSON Validation failed (Attempt {attempts}/{max_attempts}): {error_msg}")

            if attempts >= max_attempts:
                raise e # Give up
            
            # Provide very specific feedback based on the error
            extra_feedback = ""
            if "invalid escape" in error_msg.lower():
                extra_feedback = "\n- CRITICAL: You have invalid escape sequences. In JSON strings, use \\\\ for backslash, \\n for newline (already escaped), \\\" for quotes."
            elif "Multiple" in error_msg:
                extra_feedback = "\n- CRITICAL: Merge all files into ONE single JSON object with a 'files' array."
            
            # Feed back the previous failure for better recovery
            error_feedback = f"""
PREVIOUS OUTPUT CAUSED ERROR: {error_msg}
{extra_feedback}

RULES FOR VALID JSON:
1. All string content must have properly escaped characters:
   - Backslash: \\\\
   - Newline: \\n (this is already escaped, don't add more backslashes)
   - Quote: \\"
   - Tab: \\t
2. Return ONE JSON object: {{"files": [...]}}
3. No markdown code blocks around the JSON.

Output ONLY the fully corrected JSON."""
            current_system = SYSTEM_CODE + "\n\n" + error_feedback
    
    # Should not be reachable but for safety:
    return GenOutput()

