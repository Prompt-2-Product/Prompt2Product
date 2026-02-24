from __future__ import annotations
from typing import List, Dict, Any
from pydantic import BaseModel, Field, model_validator
from app.services.llm.base import LLMClient
from app.services.prompt_to_spec import TaskSpec
from app.core.utils import extract_json, clean_requirements_text, repair_json
import os
import re
import json as json_lib

class GenFile(BaseModel):
    path: str
    content: str

    @model_validator(mode='before')
    @classmethod
    def fix_path_and_name(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # FIX: LLM often outputs 'name' instead of 'path'
            if 'path' not in data and 'name' in data:
                data['path'] = data['name']
            
            # FIX: Ensure full paths if LLM outputs bare filenames
            if 'path' in data:
                path = data['path']
                if '/' not in path and '\\' not in path:
                    if path.endswith(('.html', '.css', '.js')):
                        data['path'] = f"generated_app/frontend/{path}"
                    elif path.endswith(('.py', '.txt', '.sql', '.env')):
                        data['path'] = f"generated_app/backend/{path}"
        return data

class GenOutput(BaseModel):
    files: List[GenFile] = Field(default_factory=list)
    entrypoint: str = "generated_app/backend/main.py"
    run: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode='before')
    @classmethod
    def normalize_files(cls, data: Any) -> Any:
        # DEBUG: Print raw LLM output to understand structure
        try:
             print(f"DEBUG: GenOutput raw data: {json_lib.dumps(data, indent=2)}")
        except:
             print(f"DEBUG: GenOutput raw data (non-json): {data}")

        # FIX: DeepSeek often outputs a dict of {filename: content} instead of a list
        # Case 1: The root object is just the dict of files
        if isinstance(data, dict):
            # If it has keys that look like files and NO 'files' key
            if 'files' not in data and any('.' in k for k in data.keys()):
                # Convert dict to list of GenFile dicts
                new_files = []
                for path, content in data.items():
                    if isinstance(content, str):
                        new_files.append({"path": path, "content": content})
                if new_files:
                    return {"files": new_files}

            # Case 2: 'files' key exists but is a dict {filename: content} instead of list
            # OR a dict of categories {category: [file_objects]}
            if 'files' in data and isinstance(data['files'], dict):
                file_dict = data['files']
                new_files_list = []
                for key, value in file_dict.items():
                     # Simple key: value (filename: content)
                     if isinstance(value, str):
                        new_files_list.append({"path": key, "content": value})
                     # Nested category: [file_objects]
                     elif isinstance(value, list):
                        for item in value:
                            if isinstance(item, dict):
                                # Extract path/name and content
                                # DeepSeek uses 'file_name' sometimes, or 'name', or 'path'
                                fpath = item.get('file_name', item.get('path', item.get('name')))
                                fcontent = item.get('content')
                                if fpath and fcontent:
                                    new_files_list.append({"path": fpath, "content": fcontent})
                
                # Only replace if we found files
                if new_files_list:
                    data['files'] = new_files_list
        
        return data

SYSTEM_CODE = """You generate a COMPLETE, WORKING, premium full-stack website from a TaskSpec JSON.
- Backend: FastAPI
- Frontend: HTML/CSS/JS with Tailwind CSS (CDN)

═══════════════════════════════════════════════════════════════════
🚨 STEP-BY-STEP GENERATION PROCESS (FOLLOW EXACTLY)
═══════════════════════════════════════════════════════════════════

STEP 1: START WITH THIS EXACT main.py TEMPLATE
───────────────────────────────────────────────────────────────────
Copy this template EXACTLY and fill in the {PLACEHOLDERS}:

```python
import os
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Optional

app = FastAPI()

# Get the parent directory (generated_app/) from backend/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

# Ensure directories exist
os.makedirs(FRONTEND_DIR, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# ═══════════════════════════════════════════════════════════════════
# FILE SERVING ROUTES (REQUIRED FOR EVERY HTML PAGE)
# ═══════════════════════════════════════════════════════════════════

@app.get("/")
def read_root(request: Request):
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

@app.get("/about")
def read_about(request: Request):
    return FileResponse(os.path.join(FRONTEND_DIR, "about.html"))

@app.get("/contact")
def read_contact(request: Request):
    return FileResponse(os.path.join(FRONTEND_DIR, "contact.html"))

# {ADD_MORE_ROUTES_FOR_EACH_PAGE_IN_TASKSPEC}

# ═══════════════════════════════════════════════════════════════════
# OPTIONAL: API ROUTES (only if TaskSpec requires dynamic data)
# ═══════════════════════════════════════════════════════════════════

# Example:
# @app.get("/api/items")
# def get_items():
#     return {"items": []}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

🚨 CRITICAL: You MUST include:
1. The exact imports shown above
2. The BASE_DIR and FRONTEND_DIR setup
3. The app.mount() for static files
4. A @app.get() route for EVERY HTML file you create
5. FileResponse for each route

───────────────────────────────────────────────────────────────────
STEP 2: CREATE requirements.txt
───────────────────────────────────────────────────────────────────

```
fastapi
uvicorn
```

Add "python-multipart" ONLY if you use Form(...) in main.py.

───────────────────────────────────────────────────────────────────
STEP 3: CREATE HTML FILES
───────────────────────────────────────────────────────────────────

For EACH page in TaskSpec.pages, create a complete HTML file following this template:

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
        <div class="container mx-auto flex justify-between items-center">
            <a href="/" class="text-2xl font-bold text-gray-800">Logo</a>
            <div class="hidden md:flex space-x-6">
                <a href="/" class="text-gray-600 hover:text-blue-600 transition">Home</a>
                <a href="/about" class="text-gray-600 hover:text-blue-600 transition">About</a>
                <a href="/contact" class="text-gray-600 hover:text-blue-600 transition">Contact</a>
            </div>
            <!-- Mobile Menu Button -->
            <button data-menu-toggle class="md:hidden text-gray-600">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path></svg>
            </button>
        </div>
        <!-- Mobile Menu (Hidden by default) -->
        <div data-mobile-menu class="hidden md:hidden bg-white border-t p-4">
            <a href="/" class="block py-2 text-gray-600">Home</a>
            <a href="/about" class="block py-2 text-gray-600">About</a>
        </div>
    </nav>

    <!-- Hero Section -->
    <section class="min-h-screen bg-gradient-to-br from-purple-600 to-blue-500 flex items-center justify-center pt-20">
        <div class="text-center p-8 glass max-w-4xl">
            <h1 class="text-white font-extrabold mb-4 text-5xl">Hero Title</h1>
            <p class="text-white text-xl mb-8">Compelling description goes here.</p>
            <button class="bg-white text-blue-600 px-8 py-3 rounded-full font-bold hover:bg-opacity-90 transition transform hover:scale-105">Get Started</button>
        </div>
    </section>

    <!-- Feature Bento Grid -->
    <section class="container mx-auto p-8 my-12">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div class="glass p-8 text-center card-hover">
                <h3 class="text-xl font-bold mb-4">Feature 1</h3>
                <p>Description of feature 1.</p>
            </div>
            <!-- More cards -->
        </div>
    </section>

    <!-- More sections (min 6 total) -->
    
    <footer class="bg-gray-900 text-white p-12 mt-20">
        <div class="container mx-auto grid grid-cols-1 md:grid-cols-4 gap-8">
            <div>
                <h3 class="font-bold text-xl mb-4">Brand</h3>
                <p class="text-gray-400">Short description.</p>
            </div>
            <div>
                <h4 class="font-bold mb-4">Links</h4>
                <ul class="space-y-2 text-gray-400">
                    <li><a href="/" class="hover:text-white">Home</a></li>
                    <li><a href="/about" class="hover:text-white">About</a></li>
                </ul>
            </div>
            <!-- More columns -->
        </div>
        <div class="border-t border-gray-800 mt-8 pt-8 text-center text-gray-500">
            &copy; 2024 Brand. All rights reserved.
        </div>
    </footer>

    <script src="/static/app.js"></script>
</body>
</html>
```

───────────────────────────────────────────────────────────────────
STEP 4: CREATE main.css (MINIMUM 50 LINES)
───────────────────────────────────────────────────────────────────

🚨 CRITICAL: Copy this ENTIRE template and expand it to at least 50 lines.
DO NOT write "/* generated content */" - use this actual code:

```css
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;700&family=Inter:wght@400;600;700&display=swap');

/* Theme-specific color variables - CUSTOMIZE based on app industry */
:root {
    --primary: #10b981;      /* Adjust to match app theme (e.g., green for plants, red for food) */
    --primary-dark: #059669;
    --secondary: #34d399;
    --background: #f9fafb;
    --text: #1f2937;
    --text-light: #6b7280;
    --border: #e5e7eb;
}

body {
    font-family: 'Plus Jakarta Sans', sans-serif;
    background-color: var(--background);
    color: var(--text);
    overflow-x: hidden;
}

/* Animated Mesh Gradient */
@keyframes mesh-gradient {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

.mesh-gradient {
    background: linear-gradient(45deg, var(--primary) 0%, var(--secondary) 25%, #6ee7b7 50%, #a7f3d0 75%, #d1fae5 100%);
    background-size: 400% 400%;
    animation: mesh-gradient 15s ease infinite;
}

/* Glassmorphism */
.glass {
    backdrop-filter: blur(12px);
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 16px;
}

/* Card Hover Effects */
.card-hover {
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.card-hover:hover {
    transform: translateY(-8px);
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
}

/* Smooth Transitions */
a, button {
    transition: all 0.2s ease;
}

/* Responsive Typography */
h1 { font-size: clamp(2rem, 5vw, 4rem); }
h2 { font-size: clamp(1.5rem, 4vw, 3rem); }
h3 { font-size: clamp(1.25rem, 3vw, 2rem); }

/* Add more theme-specific styles to reach 50+ lines */
```

───────────────────────────────────────────────────────────────────
STEP 5: CREATE app.js (MINIMUM 30 LINES)
───────────────────────────────────────────────────────────────────

🚨 CRITICAL: Copy this ENTIRE template and expand it to at least 30 lines.
DO NOT write "// generated content" - use this actual code:

```javascript
document.addEventListener('DOMContentLoaded', function() {
    // Smooth scroll for navigation
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });

    // Mobile menu toggle
    const menuToggle = document.querySelector('[data-menu-toggle]');
    const mobileMenu = document.querySelector('[data-mobile-menu]');

    if (menuToggle && mobileMenu) {
        menuToggle.addEventListener('click', () => {
            mobileMenu.classList.toggle('hidden');
        });
    }

    // Form submission handling
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(form);
            console.log('Form submitted:', Object.fromEntries(formData));
        });
    });

    // Scroll reveal animations - DISABLED BY DEFAULT
    // const observerOptions = { ... };
    // const observer = new IntersectionObserver(...);
    // document.querySelectorAll('.animate-on-scroll').forEach(...);

    // Optional: Add simple fade-in on load if desired
    document.body.classList.add('opacity-100');
});
```

───────────────────────────────────────────────────────────────────
FINAL VALIDATION CHECKLIST
───────────────────────────────────────────────────────────────────

Before returning your JSON output, verify:
✅ main.py has FileResponse import
✅ main.py has app.mount("/static", ...)
✅ main.py has @app.get("/") route for index.html
✅ main.py has a route for EVERY HTML file
✅ main.css is at least 50 lines (NOT "/* generated content */")
✅ app.js is at least 30 lines (NOT "// generated content")
✅ All HTML files have actual navigation links (NOT "<!-- Nav content -->")
✅ requirements.txt includes fastapi and uvicorn

OUTPUT FORMAT:
Return ONE JSON object with a 'files' array containing ALL files.

🚨 CRITICAL: File paths MUST include the full directory structure starting with "generated_app/"

CORRECT JSON EXAMPLE:
```json
{
  "files": [
    {
      "path": "generated_app/backend/main.py",
      "content": "import os\\nfrom fastapi import FastAPI..."
    },
    {
      "path": "generated_app/backend/requirements.txt",
      "content": "fastapi\\nuvicorn"
    },
    {
      "path": "generated_app/frontend/index.html",
      "content": "<!DOCTYPE html>..."
    },
    {
      "path": "generated_app/frontend/main.css",
      "content": "@import url(...)..."
    },
    {
      "path": "generated_app/frontend/app.js",
      "content": "// Smooth scroll..."
    }
  ]
}
```
"""

def aggressive_json_clean(text: str) -> str:
    """
    Aggressively clean JSON output from LLM to fix common issues.
    """
    import re
    # 1. CRITICAL FIX: Replace backticks with escaped quotes
    def replace_backtick_strings(match):
        key = match.group(1)
        value = match.group(2)
        value = value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
        return f'"{key}": "{value}"'
    
    text = re.sub(r'"([^"]+)":\s*`([^`]*)`', replace_backtick_strings, text, flags=re.DOTALL)
    
    try:
        json_lib.loads(text)
        return text
    except json_lib.JSONDecodeError as e:
        print(f"JSON parse error after backtick fix: {e}")
        pass
    return text

def post_process_output(output: GenOutput) -> GenOutput:
    """
    Post-process LLM output to fix common issues and inject missing code.
    This compensates for smaller models not following complex instructions.
    """

    # Collect all HTML files to generate routes
    html_files = []
    for file in output.files:
        if file.path.endswith(".html") and "frontend" in file.path:
            filename = file.path.split("/")[-1]
            route = "/" if filename == "index.html" else f"/{filename.replace('.html', '')}"
            html_files.append((route, filename))
            
            # FIX 11: Navbar List Styling (Project 58)
            # If <nav> contains <ul> but no classes, inject Tailwind
            if "<nav" in file.content and "<ul" in file.content:
                # Add classes to bare <ul>
                file.content = re.sub(r'<ul(?![^>]*class)', '<ul class="flex space-x-6 list-none p-0 m-0"', file.content)
                
                # Style links inside list items (common pattern <li><a href="...">)
                # We use a robust regex that matches simple <a> tags without classes
                file.content = re.sub(
                    r'<li>\s*<a href="([^"]+)"(?![^>]*class)>([^<]+)</a>\s*</li>', 
                    r'<li><a href="\1" class="text-white hover:text-green-200 transition font-medium text-lg">\2</a></li>', 
                    file.content
                )
    
    for file in output.files:
        # Fix common LLM escaping issues
        if "\\\\n" in file.content:
            file.content = file.content.replace("\\\\n", "\n")
        
        # FIX 1: main.py - Inject missing file serving routes
        if file.path.endswith("backend/main.py") or file.path.endswith("backend\\main.py"):
            content = file.content
            
            # FIX 1.7: Detect and REGENERATE main.py if forbidden patterns (Jinja2, Database) or Fragile Paths are found
            # Project 47: Jinja2 usage
            # Project 49: Broken SQLAlchemy usage
            # Project 56: Fragile relative path (FileNotFoundError)
            forbidden_tokens = ["Jinja2Templates", "fastapi.templating", "sqlalchemy", "sqlite3", "database"]
            
            # Check for fragile relative paths (e.g. directory="generated_app/frontend") which fail in different CWDs
            has_fragile_path = 'directory="generated_app' in content or "directory='generated_app" in content
            
            # Check for missing robust Base Directory setup (must use os.path.dirname(os.path.dirname...))
            missing_base_dir = "os.path.dirname(os.path.dirname" not in content

            if any(token in content for token in forbidden_tokens) or has_fragile_path or missing_base_dir:
                new_content = """import os
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Get the parent directory (generated_app/) from backend/
# __file__ is inside backend/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
os.makedirs(FRONTEND_DIR, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# ═══════════════════════════════════════════════════════════════════
# FILE SERVING ROUTES
# ═══════════════════════════════════════════════════════════════════
"""
                # Find all HTML files in the output to generate routes
                for f in output.files:
                    if f.path.endswith(".html") and "frontend" in f.path:
                        fname = f.path.split("/")[-1]
                        route_name = fname.replace(".html", "")
                        route_path = "/" if route_name == "index" else f"/{route_name}"
                        func_name = f"read_{route_name.replace('-', '_')}"
                        
                        new_content += f"""
@app.get("{route_path}")
def {func_name}(request: Request):
    return FileResponse(os.path.join(FRONTEND_DIR, "{fname}"))
"""
                
                new_content += """
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""
                file.content = new_content
                # Update content variable for subsequent checks (though regeneration handles most)
                content = new_content

            # FIX 1.5: Detect and fix invalid HTMLResponse usage (Project 46 regression)
            if "HTMLResponse(path=" in content:
                # Replace with FileResponse
                content = content.replace("HTMLResponse(path=", "FileResponse(")
                if "FileResponse" not in content.split("import")[1 if "import" in content else 0]:
                     content = content.replace("from fastapi.responses import HTMLResponse", "from fastapi.responses import FileResponse, HTMLResponse")
                file.content = content

            # FIX 1.8: Ensure StaticFiles import (Project 50 regression)
            if "StaticFiles" in content and "from fastapi.staticfiles import StaticFiles" not in content:
                if "from starlette.staticfiles import StaticFiles" in content:
                    # Replace starlette import with fastapi one (safer)
                    content = content.replace("from starlette.staticfiles import StaticFiles", "from fastapi.staticfiles import StaticFiles")
                else:
                    # Inject import
                    if "from fastapi import" in content:
                        content = content.replace("from fastapi import", "from fastapi.staticfiles import StaticFiles\nfrom fastapi import")
                    else:
                        content = "from fastapi.staticfiles import StaticFiles\n" + content
                file.content = content

            # FIX 1.6: Enforce correct BASE_DIR setup
            # If BASE_DIR is defined incorrectly (e.g. pointing to backend instead of generated_app)
            if "BASE_DIR = os.path.dirname(os.path.abspath(__file__))" in content and "os.path.dirname(os.path.dirname" not in content:
                # Replace the whole block with the correct one
                correct_setup = '''
# Get the parent directory (generated_app/) from backend/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
os.makedirs(FRONTEND_DIR, exist_ok=True)
'''
                # Regex replace the bad block
                content = re.sub(r'BASE_DIR = os\.path\.dirname\(os\.path\.abspath\(__file__\)\).*?STATIC_DIR = .*?frontend.*?\)', correct_setup, content, flags=re.DOTALL)
                # Also simpler replacement if regex fails
                if "STATIC_DIR" in content:
                     content = content.replace("STATIC_DIR", "FRONTEND_DIR")
                
                file.content = content

            # Check if FileResponse is missing

            if "FileResponse" not in content:
                template = '''import os
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Optional

app = FastAPI()

# Get the parent directory (generated_app/) from backend/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

# Ensure directories exist
os.makedirs(FRONTEND_DIR, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

'''
                # Add routes for all HTML files
                for route, filename in html_files:
                    func_name = f"read_{filename.replace('.html', '').replace('-', '_')}"
                    template += f'''@app.get("{route}")
def {func_name}(request: Request):
    return FileResponse(os.path.join(FRONTEND_DIR, "{filename}"))

'''
                # Append original content (API routes, models, etc.)
                content_lines = content.split("\n")
                filtered_lines = [line for line in content_lines if "app = FastAPI()" not in line and not (line.strip().startswith("import") or line.strip().startswith("from"))]
                file.content = template + "\n".join(filtered_lines)
            
            # Ensure static mounting exists
            elif "app.mount" not in content or "StaticFiles" not in content:
                lines = content.split("\n")
                inject_index = 0
                for i, line in enumerate(lines):
                    if "app = FastAPI()" in line:
                        inject_index = i + 1
                        break
                static_mount = '''
# Get the parent directory (generated_app/) from backend/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
os.makedirs(FRONTEND_DIR, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
'''
                lines.insert(inject_index, static_mount)
                file.content = "\n".join(lines)
            
            # Ensure file serving routes exist
            if '@app.get("/")' not in content and "@app.get('/')" not in content:
                routes = "\n"
                for route, filename in html_files:
                    func_name = f"read_{filename.replace('.html', '').replace('-', '_')}"
                    routes += f'''@app.get("{route}")
def {func_name}(request: Request):
    return FileResponse(os.path.join(FRONTEND_DIR, "{filename}"))

'''
                file.content += routes
        
        # FIX 12: Requirements Hardening (Project 60)
        # Remove hallucinatory dependencies
        if file.path.endswith("requirements.txt"):
            lines = file.content.splitlines()
            cleaned_lines = []
            forbidden_deps = ["templatetags", "django", "flask", "sqlite3"] # sqlite3 is stdlib, not pypi
            for line in lines:
                pkg = line.strip().split("==")[0].split(">=")[0].lower()
                if pkg and pkg not in forbidden_deps:
                    cleaned_lines.append(line)
            
            # Ensure essentials
            if "fastapi" not in file.content: cleaned_lines.append("fastapi")
            if "uvicorn" not in file.content: cleaned_lines.append("uvicorn")
            
            file.content = "\n".join(cleaned_lines)

        # FIX 2: main.css - Expand if too short AND force visibility
        if file.path.endswith("main.css"):
            # FIX 5: Prevent Blank Page (Project 48/51)
            # LLM often adds .animate-on-scroll { opacity: 0 } even if we remove JS.
            # We must override this to ensure content is visible.
            force_visibility = "\n\n/* FORCE VISIBILITY - Prevent Blank Page */\n.animate-on-scroll {\n    opacity: 1 !important;\n    transform: none !important;\n}\n"
            
            if force_visibility not in file.content:
                file.content += force_visibility

            lines = [l for l in file.content.split("\n") if l.strip() and not l.strip().startswith("/*")]
            if len(lines) < 20:
                file.content += '''
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;700&family=Inter:wght@400;600;700&display=swap');

/* Theme-specific color variables */
:root {
    --primary: #10b981;
    --primary-dark: #059669;
    --secondary: #34d399;
    --background: #f9fafb;
    --text: #1f2937;
    --text-light: #6b7280;
    --border: #e5e7eb;
}

body {
    font-family: 'Plus Jakarta Sans', sans-serif;
    background-color: var(--background);
    color: var(--text);
    overflow-x: hidden;
}

/* Animated Mesh Gradient */
@keyframes mesh-gradient {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

.mesh-gradient {
    background: linear-gradient(45deg, var(--primary) 0%, var(--secondary) 25%, #6ee7b7 50%, #a7f3d0 75%, #d1fae5 100%);
    background-size: 400% 400%;
    animation: mesh-gradient 15s ease infinite;
}

/* Glassmorphism */
.glass {
    backdrop-filter: blur(12px);
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 16px;
}

/* Card Hover Effects */
.card-hover {
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.card-hover:hover {
    transform: translateY(-8px);
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
}

/* Smooth Transitions */
a, button {
    transition: all 0.2s ease;
}

/* Responsive Typography */
h1 { font-size: clamp(2rem, 5vw, 4rem); }
h2 { font-size: clamp(1.5rem, 4vw, 3rem); }
h3 { font-size: clamp(1.25rem, 3vw, 2rem); }
'''

        # FIX 6: Frontend Hardening (Project 53)
        # 1. Enforce Tailwind CDN
        if file.path.endswith(".html"):
            if "cdn.tailwindcss.com" not in file.content:
                # Inject into head
                if "</head>" in file.content:
                    file.content = file.content.replace("</head>", '<script src="https://cdn.tailwindcss.com"></script>\n</head>')
                else:
                    # No head tag? Prepend to body or file
                    file.content = '<script src="https://cdn.tailwindcss.com"></script>\n' + file.content

            # FIX 5 (HTML part): Remove dangerous animate-on-scroll class if it causes issues
            if 'class="animate-on-scroll"' in file.content:
                file.content = file.content.replace('class="animate-on-scroll"', 'class=""')

            # FIX 8: Structural Hardening (Project 55/61)
            # If Navbar is empty placeholder OR MISSING ENTIRELY, inject real navbar
            has_navbar_placeholder = "<!-- Navbar content -->" in file.content or "<!-- Nav content -->" in file.content
            has_nav_tag = "<nav" in file.content
            
            if has_navbar_placeholder or not has_nav_tag:
                 navbar_inner = '''
    <div class="container mx-auto flex justify-between items-center p-4">
        <a href="/" class="text-2xl font-bold text-white drop-shadow-md">EcoApp</a>
        <div class="hidden md:flex space-x-6">
            <a href="/" class="text-white hover:text-green-200 transition font-medium">Home</a>
            <a href="/about" class="text-white hover:text-green-200 transition font-medium">About</a>
            <a href="/features" class="text-white hover:text-green-200 transition font-medium">Features</a>
            <a href="/contact" class="text-white hover:text-green-200 transition font-medium">Contact</a>
        </div>
        <button data-menu-toggle class="md:hidden text-white">☰</button>
    </div>
    <!-- Mobile Menu -->
    <div data-mobile-menu class="hidden md:hidden bg-white/10 backdrop-blur-md p-4 mt-2 rounded-lg border border-white/20">
        <a href="/" class="block py-2 text-white hover:bg-white/10 rounded px-2">Home</a>
        <a href="/about" class="block py-2 text-white hover:bg-white/10 rounded px-2">About</a>
    </div>
'''
                 if has_navbar_placeholder:
                     file.content = file.content.replace("<!-- Navbar content -->", navbar_inner)
                     file.content = file.content.replace("<!-- Nav content -->", navbar_inner)
                 elif not has_nav_tag:
                     # Inject after body start
                     # Wrapp in <nav>
                     full_navbar = f'<nav class="glass mb-8 w-full z-50">{navbar_inner}</nav>'
                     if "<body" in file.content:
                         file.content = re.sub(r'(<body[^>]*>)', r'\1\n' + full_navbar, file.content, count=1)
                     else:
                         file.content = full_navbar + "\n" + file.content

            # FIX 9: Typography Injection (If bare tags)
            # Only match bare tags without attributes to avoid breaking existing styles
            file.content = file.content.replace("<h1>", '<h1 class="text-4xl md:text-5xl font-bold text-white mb-6 drop-shadow-lg">')
            file.content = file.content.replace("<h2>", '<h2 class="text-3xl md:text-4xl font-bold text-white mb-5 drop-shadow-md">')
            file.content = file.content.replace("<h3>", '<h3 class="text-xl md:text-2xl font-semibold text-white mb-3">')
            file.content = file.content.replace("<p>", '<p class="text-lg text-white/90 mb-6 leading-relaxed">')
            file.content = file.content.replace("<section id=\"hero\">", '<section id="hero" class="container mx-auto px-4 py-16 md:py-24 text-center glass rounded-3xl mt-8">')
            
            # Button/Link styling if it looks like a CTA
            # (Hard to target generically, generally generic links get default style)
            # But "get started" usually in <a>
            # We can't globally replace <a>.

        # FIX 3: app.js - Expand if too short AND Disable Fetch
        if file.path.endswith("app.js"):
            # FIX 7: Disable API calls that overwrite static content with "undefined"
            if "fetch(" in file.content:
                 # Comment out fetch calls
                 # Simple regex replacement might be risky, but commenting out the line is safer for simple scripts
                 # However, multiline fetches exist.
                 # Better: Replace "fetch(" with "// DISABLED: fetch("
                 file.content = file.content.replace("fetch(", "// DISABLED (Prevent Undefined): fetch(")
                 
                 # Also comment out .then chaining to prevent syntax errors?
                 # If we comment out `fetch(..)...`, the subsequent `.then` might hang?
                 # Javascript: // fetch().then(...) 
                 # If it's on one line, fine. 
                 # If multiline:
                 # fetch(...)
                 #   .then(...)
                 # Then `// fetch(...)` leaves `.then(...)` which is SyntaxError.
                 
                 # Alternative: Replace `fetch` with a dummy function that returns a never-resolving promise?
                 # No, better to wrapp it?
                 # Easiest: append a "Safe Mode" script that overrides fetch?
                 # `window.fetch = () => new Promise(() => {});` (Never resolves).
                 # This prevents the `.then` callbacks from running!
                 # And it prevents "undefined" overwrite.
                 
                 file.content = "// SAFETY: Disable API calls to prevent content overwrite\nwindow.fetch = () => new Promise(() => {});\n\n" + file.content

            lines = [l for l in file.content.split("\n") if l.strip() and not l.strip().startswith("//")]
            if len(lines) < 10:
                file.content = '''document.addEventListener('DOMContentLoaded', function() {
    // Smooth scroll for navigation
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });

    // Mobile menu toggle
    const menuToggle = document.querySelector('[data-menu-toggle]');
    const mobileMenu = document.querySelector('[data-mobile-menu]');

    if (menuToggle && mobileMenu) {
        menuToggle.addEventListener('click', () => {
            mobileMenu.classList.toggle('hidden');
        });
    }

    // Form submission handling
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(form);
            console.log('Form submitted:', Object.fromEntries(formData));
        });
    });

    // Scroll reveal animations - DISABLED BY DEFAULT
    // const observerOptions = { ... };
    // const observer = new IntersectionObserver(...);
    // document.querySelectorAll('.animate-on-scroll').forEach(...);

    // Optional: Add simple fade-in on load if desired
    document.body.classList.add('opacity-100');
});
'''
        
        # FIX 4: requirements.txt - Clean and ensure basics
        if file.path.endswith("requirements.txt"):
            file.content = clean_requirements_text(file.content)
            if "fastapi" not in file.content.lower():
                file.content = "fastapi\n" + file.content
            if "uvicorn" not in file.content.lower():
                file.content += "\nuvicorn"
    
    # FIX 10: Auto-Routing - Create missing HTML files based on links in index.html (Relocated to END)
    # Scan index.html for links like /blog, /about and ensure corresponding .html files exist
    existing_files = {f.path.split("/")[-1]: f for f in output.files if f.path.endswith(".html")}
    
    if "index.html" in existing_files:
        index_content = existing_files["index.html"].content
        # Find href="/name" references
        links = re.findall(r'href=["\'](/[^"\'#]+)["\']', index_content)
        
        for link in links:
            if link == "/" or link.startswith("/static"): continue
            
            page_name = link.strip("/") + ".html"
            if page_name not in existing_files:
                # Create Stub Page
                stub_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{link.strip("/").title()} - Generated Page</title>
    <link rel="stylesheet" href="/static/main.css">
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="mesh-gradient min-h-screen flex flex-col">
    <!-- Navbar (Will be injected/std) -->
    <nav class="container mx-auto p-6 flex justify-between items-center glass mb-8">
        <a href="/" class="text-2xl font-bold text-white">Home</a>
        <div class="space-x-4">
            <a href="{link}" class="text-green-300 font-bold">{link.strip("/").title()}</a>
        </div>
    </nav>
    
    <main class="container mx-auto p-8 glass rounded-3xl flex-grow text-center">
        <h1 class="text-4xl font-bold text-white mb-6">{link.strip("/").title()}</h1>
        <p class="text-xl text-white/80">This page was automatically generated.</p>
        <a href="/" class="inline-block mt-8 bg-white text-green-600 px-6 py-2 rounded-full font-bold hover:bg-gray-100 transition">Back to Home</a>
    </main>
    
    <script src="/static/app.js"></script>
</body>
</html>'''
                # Create GenFile and add to output
                new_file = GenFile(path=f"generated_app/frontend/{page_name}", content=stub_content)
                output.files.append(new_file)
                # Add to existing map to prevent dupes
                existing_files[page_name] = new_file

    return output

async def llm_spec_to_code(llm: LLMClient, model: str, spec: TaskSpec) -> GenOutput:
    user = f"TASKSPEC_JSON:\n{spec.model_dump_json(indent=2)}\n\nReturn code files in ONE JSON object with a 'files' key."
    current_system = SYSTEM_CODE
    
    attempts = 0
    max_attempts = 3
    
    while attempts < max_attempts:
        attempts += 1
        try:
            raw = await llm.chat(model=model, system=current_system, user=user, max_tokens=8192)
            cleaned = extract_json(raw)
            repaired = repair_json(cleaned)
            repaired = aggressive_json_clean(repaired)
            
            try:
                output = GenOutput.model_validate_json(repaired)
            except Exception as parse_error:
                raise parse_error
            
            return post_process_output(output)
            
        except Exception as e:
            error_msg = str(e)
            print(f"JSON Validation failed (Attempt {attempts}/{max_attempts}): {error_msg}")
            if attempts >= max_attempts:
                raise e
            
            extra_feedback = ""
            if "invalid escape" in error_msg.lower():
                extra_feedback = "\n- CRITICAL: You have invalid escape sequences. In JSON strings, use \\\\ for backslash, \\n for newline (already escaped), \\\" for quotes."
            elif "Multiple" in error_msg:
                extra_feedback = "\n- CRITICAL: Merge all files into ONE single JSON object with a 'files' array."
            
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
    
    return GenOutput()
