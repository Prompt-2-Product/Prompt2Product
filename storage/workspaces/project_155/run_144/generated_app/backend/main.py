from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Mount the static files directory
app.mount("/static", StaticFiles(directory="../frontend/static"), name="static")

@app.get("/")
async def get_landing():
    return FileResponse("../frontend/Landing.html")

@app.get("/dashboard")
async def get_dashboard():
    return FileResponse("../frontend/Dashboard.html")

@app.get("/search-and-filters")
async def get_search_and_filters():
    return FileResponse("../frontend/SearchAndFilters.html")

@app.get("/pricing")
async def get_pricing():
    return FileResponse("../frontend/Pricing.html")

@app.get("/about")
async def get_about():
    return FileResponse("../frontend/About.html")

@app.get("/contact")
async def get_contact():
    return FileResponse("../frontend/Contact.html")

@app.get("/faq")
async def get_faq():
    return FileResponse("../frontend/FAQ.html")

@app.get("/blog-news")
async def get_blog_news():
    return FileResponse("../frontend/BlogNews.html")
