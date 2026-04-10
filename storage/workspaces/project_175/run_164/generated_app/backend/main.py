import os
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Get the parent directory (generated_app/) from backend/
# __file__ is inside backend/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

# Ensure directories exist
os.makedirs(FRONTEND_DIR, exist_ok=True)

# Mount static files (if any custom css/js is added later)
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# ═══════════════════════════════════════════════════════════════════
# ROUTES
# ═══════════════════════════════════════════════════════════════════

@app.get("/")
def read_root():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

@app.get("/dashboard")
def read_dashboard():
    return FileResponse(os.path.join(FRONTEND_DIR, "dashboard.html"))

@app.get("/pricing")
def read_pricing():
    return FileResponse(os.path.join(FRONTEND_DIR, "pricing.html"))

@app.get("/about")
def read_about():
    return FileResponse(os.path.join(FRONTEND_DIR, "about.html"))

@app.get("/contact")
def read_contact():
    return FileResponse(os.path.join(FRONTEND_DIR, "contact.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
