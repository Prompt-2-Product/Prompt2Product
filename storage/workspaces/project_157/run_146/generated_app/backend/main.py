import os
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

os.makedirs(FRONTEND_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/about")
def read_about():
    return FileResponse(os.path.join(FRONTEND_DIR, "about.html"))

@app.get("/blog")
def read_blog():
    return FileResponse(os.path.join(FRONTEND_DIR, "blog.html"))

@app.get("/calculator")
def read_calculator():
    return FileResponse(os.path.join(FRONTEND_DIR, "calculator.html"))

@app.get("/contact")
def read_contact():
    return FileResponse(os.path.join(FRONTEND_DIR, "contact.html"))

@app.get("/faq")
def read_faq():
    return FileResponse(os.path.join(FRONTEND_DIR, "faq.html"))

@app.get("/")
def read_root():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
