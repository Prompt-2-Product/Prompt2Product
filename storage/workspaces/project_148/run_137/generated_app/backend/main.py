from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Mount static files directory
app.mount("/static", StaticFiles(directory="../frontend"), name="static")

@app.get("/")
async def home(request: Request):
    return FileResponse("../frontend/landing_page.html")
@app.get("/dashboard")
async def dashboard(request: Request):
    return FileResponse("../frontend/dashboard.html")

@app.get("/pricing")
async def pricing(request: Request):
    return FileResponse("../frontend/pricing.html")

@app.get("/about")
async def about(request: Request):
    return FileResponse("../frontend/about.html")

@app.get("/contact")
async def contact(request: Request):
    return FileResponse("../frontend/contact.html")

@app.get("/faq")
async def faq(request: Request):
    return FileResponse("../frontend/faq.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)