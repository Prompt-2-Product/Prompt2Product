from fastapi import FastAPI, Response
import json
from pydantic import BaseModel
app = FastAPI()
@app.get("/")
def read_root():
    return FileResponse("./frontend/index.html")

@app.get("/menu")
def read_menu():
    with open("./frontend/menu.html", "r") as f:
        return Response(f.read(), media_type="text/html")

@app.get("/order")
def read_order():
    with open("./frontend/order.html", "r") as f:
        return Response(f.read(), media_type="text/html")

from fastapi.responses import JSONResponse
from pydantic import BaseModel
class MenuItem(BaseModel):
    id: str
    name: str
@app.get("/api/menu")
def read_menu_items():
    menu_items = [
        {'id': 'item1', 'name': 'Item 1'},
        {'id': 'item2', 'name': 'Item 2'}
    ]
    return JSONResponse(content=menu_items, media_type="application/json")

from fastapi.requests import HTTPException
class OrderRequest(BaseModel):
    id: str
    item_id: str
@app.post("/api/order")
def create_order():
    data = json.loads(request.body.decode())
    order_id = data['id']
    item_id = data['item_id']
    if item_id == 'item1':
        return JSONResponse(content={'message': 'Order created'}, media_type="application/json")
    else:
        raise HTTPException(status_code=400, detail='Invalid item')
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)