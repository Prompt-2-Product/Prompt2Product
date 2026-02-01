# app/services/code_writer.py
from __future__ import annotations

from typing import Dict, List

from app.services.prompt_to_spec import TaskSpec, ApiSpec, PageSpec


def _nav_links(spec: TaskSpec) -> str:
    links = []
    for page in spec.pages:
        label = page.name
        href = page.route
        links.append(f'<a href="{href}">{label}</a>')
    return "\n    ".join(links)


def _html_filename_for_route(route: str) -> str:
    if route == "/":
        return "index.html"
    slug = route.strip("/").replace("/", "_") or "page"
    return f"{slug}.html"


def write_code_from_spec(spec: TaskSpec, files: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Fills file contents based on spec.
    Input: list of {'path':..., 'content': ''} from scaffold.
    Output: list of {'path':..., 'content': '...'} ready to write.
    """
    app_name = spec.app_name
    nav = _nav_links(spec)

    primary = spec.styling.primary_color
    theme = spec.styling.theme

    # Minimal CSS
    css = f"""
:root {{
  --primary: {primary};
}}

body {{
  font-family: Arial, sans-serif;
  margin: 0;
  background: {"#0f1115" if theme == "dark" else "#ffffff"};
  color: {"#f3f4f6" if theme == "dark" else "#111827"};
}}

.nav {{
  padding: 12px 16px;
  background: {"#151823" if theme == "dark" else "#f4f4f5"};
  display: flex;
  gap: 14px;
  align-items: center;
}}

.nav a {{
  text-decoration: none;
  color: {"#f3f4f6" if theme == "dark" else "#111827"};
  font-weight: 600;
}}

.nav a:hover {{
  color: var(--primary);
}}

.container {{
  padding: 22px;
  max-width: 1000px;
  margin: 0 auto;
}}

.grid {{
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}}

@media (max-width: 820px) {{
  .grid {{ grid-template-columns: repeat(2, 1fr); }}
}}

@media (max-width: 520px) {{
  .grid {{ grid-template-columns: 1fr; }}
}}

.card {{
  border: 1px solid {"#2a2f3a" if theme == "dark" else "#e5e7eb"};
  padding: 14px;
  border-radius: 12px;
  background: {"#121622" if theme == "dark" else "#ffffff"};
}}

.btn {{
  background: var(--primary);
  color: white;
  border: none;
  padding: 10px 12px;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 700;
}}

.btn:hover {{
  opacity: 0.92;
}}
""".strip()

    # Basic JS (menu load + order post)
    js = """
async function loadMenu() {
  const res = await fetch("/api/menu");
  const items = await res.json();
  const box = document.getElementById("items");
  if (!box) return;

  box.innerHTML = items.map(i => `
    <div class="card">
      <h3>${i.name}</h3>
      <p>Price: ${i.price}</p>
      <button class="btn" onclick="addToCart(${i.id})">Add</button>
    </div>
  `).join("");
}

function addToCart(id) {
  const cart = JSON.parse(localStorage.getItem("cart") || "[]");
  cart.push(id);
  localStorage.setItem("cart", JSON.stringify(cart));
  alert("Added to cart!");
}

async function submitOrder() {
  const cart = JSON.parse(localStorage.getItem("cart") || "[]");
  const payload = { items: cart };
  const res = await fetch("/api/order", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  alert("Order response: " + JSON.stringify(data));
}
""".strip()

    # HTML templates per page
    def make_html(page: PageSpec) -> str:
        title = f"{page.name} - {app_name}" if page.route != "/" else app_name

        body_extra = ""
        scripts = ""

        if page.route == "/menu":
            body_extra = """
    <h1>Menu</h1>
    <div id="items" class="grid"></div>
""".rstrip()
            scripts = """
  <script src="/static/app.js"></script>
  <script>loadMenu();</script>
""".rstrip()

        elif page.route == "/order":
            body_extra = """
    <h1>Order</h1>
    <p>Your cart is stored in the browser (localStorage).</p>
    <button class="btn" onclick="submitOrder()">Submit Order</button>
""".rstrip()
            scripts = """
  <script src="/static/app.js"></script>
""".rstrip()

        else:
            # Home or any other page
            body_extra = f"""
    <h1>{app_name}</h1>
    <p>This is a generated full-stack website (FastAPI + HTML/CSS).</p>
""".rstrip()

        html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>{title}</title>
  <link rel="stylesheet" href="/static/styles.css" />
</head>
<body>
  <nav class="nav">
    {nav}
  </nav>

  <main class="container">
{body_extra}
  </main>
{scripts}
</body>
</html>
"""
        return html

    # Backend main.py (serves pages + static + simple APIs)
    # Build page routes
    page_routes = []
    for page in spec.pages:
        filename = _html_filename_for_route(page.route)
        func_name = "home" if page.route == "/" else f"page_{page.route.strip('/').replace('/', '_')}"
        route = page.route
        page_routes.append((route, func_name, filename))

    # Basic API endpoints (we implement /api/menu and /api/order as MVP)
    # You can later expand automatically from spec.api
    backend_main = f"""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

app = FastAPI(title="{app_name}")

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = (BASE_DIR.parent / "frontend").resolve()

app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

def read_html(filename: str) -> str:
    return (FRONTEND_DIR / filename).read_text(encoding="utf-8")

{"".join([f'''
@app.get("{route}", response_class=HTMLResponse)
def {func_name}():
    return read_html("{fname}")
''' for route, func_name, fname in page_routes])}

# --- MVP data + APIs ---
MENU = [
    {{"id": 1, "name": "Burger", "price": 250}},
    {{"id": 2, "name": "Fries", "price": 120}},
    {{"id": 3, "name": "Pizza Slice", "price": 300}},
]

@app.get("/api/menu")
def get_menu():
    return JSONResponse(MENU)

@app.post("/api/order")
def create_order(payload: dict):
    # Simple demo response
    items = payload.get("items", [])
    return {{"status": "ok", "items_received": items, "message": "Order created (demo)."}}
""".strip()

    requirements = "fastapi\nuvicorn\n"

    # Fill the files list
    out: List[Dict[str, str]] = []
    for f in files:
        path = f["path"]

        if path.endswith("generated_app/frontend/styles.css"):
            out.append({"path": path, "content": css})
        elif path.endswith("generated_app/frontend/app.js"):
            out.append({"path": path, "content": js})
        elif path.endswith("generated_app/backend/main.py"):
            out.append({"path": path, "content": backend_main})
        elif path.endswith("generated_app/backend/requirements.txt"):
            out.append({"path": path, "content": requirements})
        elif path.startswith("generated_app/frontend/") and path.endswith(".html"):
            # find which page this is
            filename = path.split("/")[-1]
            page = next((p for p in spec.pages if _html_filename_for_route(p.route) == filename), None)
            if page is None:
                # fallback page
                out.append({"path": path, "content": make_html(PageSpec(name="Page", route="/page", sections=[]))})
            else:
                out.append({"path": path, "content": make_html(page)})
        else:
            # unchanged
            out.append({"path": path, "content": f.get("content", "")})

    return out
