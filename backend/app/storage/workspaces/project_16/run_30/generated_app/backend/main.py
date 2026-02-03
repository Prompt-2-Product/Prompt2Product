from fastapi import FastAPI, Response
from pydantic import BaseModel
app = FastAPI()
@app.get("/")
def read_root():
    return Response(template_path / "index.html")
@app.get("/menu")
def read_menu():
    return Response(template_path / "menu.html")
@app.get("/order")
def read_order():
    return Response(template_path / "order.html")
from fastapi.responses import JSONResponse
@app.post("/api/order")
def create_order(item: dict):
    return JSONResponse(content={"message": "Order created successfully!"})
# API to get menu items as JSON
from pydantic import BaseModel
class MenuItem(BaseModel):
    name: str
    price: float
@app.get("/api/menu")
def read_menu_items():
    return [MenuItem(name="Burger", price=5.99), MenuItem(name="Fries", price=2.99)]