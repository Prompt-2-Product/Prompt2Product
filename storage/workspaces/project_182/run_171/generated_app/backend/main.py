import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()

# Get the parent directory (generated_app/) from backend/
# __file__ is inside backend/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

# Ensure directories exist
os.makedirs(FRONTEND_DIR, exist_ok=True)

# Mount static files (if any custom css/js is added later)
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# ═══════════════════════════════════════════════════════════════
# ═══ Auto-injected HTML routes (post_process) ═══
@app.get("/about")
@app.get("/about.html")
def read_about():
    return FileResponse(os.path.join(FRONTEND_DIR, 'about.html'))

@app.get("/blog/news")
@app.get("/blog/news.html")
def read_blog_news():
    return FileResponse(os.path.join(FRONTEND_DIR, 'blog', 'news.html'))

@app.get("/contact")
@app.get("/contact.html")
def read_contact():
    return FileResponse(os.path.join(FRONTEND_DIR, 'contact.html'))

@app.get("/dashboard")
@app.get("/dashboard.html")
def read_dashboard():
    return FileResponse(os.path.join(FRONTEND_DIR, 'dashboard.html'))

@app.get("/historical-data")
@app.get("/historical-data.html")
def read_historical_data():
    return FileResponse(os.path.join(FRONTEND_DIR, 'historical-data.html'))

@app.get("/")
@app.get("/index.html")
def read_index():
    return FileResponse(os.path.join(FRONTEND_DIR, 'index.html'))

@app.get("/settings")
@app.get("/settings.html")
def read_settings():
    return FileResponse(os.path.join(FRONTEND_DIR, 'settings.html'))

