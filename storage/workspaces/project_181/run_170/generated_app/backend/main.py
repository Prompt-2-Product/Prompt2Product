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

@app.get("/maps")
def read_maps():
    return FileResponse(os.path.join(FRONTEND_DIR, "maps.html"))

@app.get("/local-weather")
def read_local_weather():
    return FileResponse(os.path.join(FRONTEND_DIR, "local-weather.html"))

@app.get("/about-us")
def read_about_us():
    return FileResponse(os.path.join(FRONTEND_DIR, "about-us.html"))

@app.get("/contact")
def read_contact():
    return FileResponse(os.path.join(FRONTEND_DIR, "contact.html"))

@app.get("/faqs")
def read_faqs():
    return FileResponse(os.path.join(FRONTEND_DIR, "faqs.html"))

@app.get("/blog")
def read_blog():
    return FileResponse(os.path.join(FRONTEND_DIR, "blog.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
