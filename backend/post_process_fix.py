def post_process_output(output: GenOutput) -> GenOutput:
    """
    Post-process LLM output to fix common issues and inject missing code.
    This compensates for smaller models not following complex instructions.
    """
    # Collect all HTML files to generate routes
    html_files = []
    for file in output.files:
        if file.path.endswith(".html") and "frontend" in file.path:
            # Extract filename from path
            filename = file.path.split("/")[-1]
            route = "/" if filename == "index.html" else f"/{filename.replace('.html', '')}"
            html_files.append((route, filename))
    
    for file in output.files:
        # Fix common LLM escaping issues (like double backslash-n)
        if "\\\\n" in file.content:
            file.content = file.content.replace("\\\\n", "\n")

        
        # FIX 1: main.py - Inject missing file serving routes
        if file.path.endswith("backend/main.py") or file.path.endswith("backend\\main.py"):
            content = file.content
            
            # Check if FileResponse is missing
            if "FileResponse" not in content:
                # Inject complete template
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
                # Remove any existing app = FastAPI() line
                content_lines = content.split("\n")
                filtered_lines = [line for line in content_lines if "app = FastAPI()" not in line and not (line.strip().startswith("import") or line.strip().startswith("from"))]
                
                file.content = template + "\n".join(filtered_lines)
            
            # Ensure static mounting exists
            elif "app.mount" not in content or "StaticFiles" not in content:
                # Find where to inject
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
                # Inject routes at the end
                routes = "\n"
                for route, filename in html_files:
                    func_name = f"read_{filename.replace('.html', '').replace('-', '_')}"
                    routes += f'''@app.get("{route}")
def {func_name}(request: Request):
    return FileResponse(os.path.join(FRONTEND_DIR, "{filename}"))

'''
                file.content += routes
        
        # FIX 2: main.css - Expand if too short
        if file.path.endswith("main.css"):
            lines = [l for l in file.content.split("\n") if l.strip() and not l.strip().startswith("/*")]
            if len(lines) < 50:
                # Inject full CSS template
                file.content = '''@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;700&family=Inter:wght@400;600;700&display=swap');

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

/* Utility Classes */
.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 1rem;
}
'''
        
        # FIX 3: app.js - Expand if too short
        if file.path.endswith("app.js"):
            lines = [l for l in file.content.split("\n") if l.strip() and not l.strip().startswith("//")]
            if len(lines) < 30:
                # Inject full JS template
                file.content = '''// Smooth scroll for navigation
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

// Scroll reveal animations
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('opacity-100', 'translate-y-0');
            entry.target.classList.remove('opacity-0', 'translate-y-4');
        }
    });
}, observerOptions);

document.querySelectorAll('.animate-on-scroll').forEach(el => {
    el.classList.add('opacity-0', 'translate-y-4', 'transition-all', 'duration-700');
    observer.observe(el);
});
'''
        
        # FIX 4: requirements.txt - Clean and ensure basics
        if file.path.endswith("requirements.txt"):
            file.content = clean_requirements_text(file.content)
            # Ensure fastapi and uvicorn are present
            if "fastapi" not in file.content.lower():
                file.content = "fastapi\n" + file.content
            if "uvicorn" not in file.content.lower():
                file.content += "\nuvicorn"
    
    return output
