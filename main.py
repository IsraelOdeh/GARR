import time
import threading
import webbrowser
from pydantic import BaseModel
import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

from websocket_handler import  websocket_endpoint
from weather import  get_soil_properties, get_weather, predict_moisture
from crop_data import get_crops, set_croptype


# ngrok.set_auth_token("2tiPuZueOT7lygddUceX6cYsZdU_6A27SFURDL9iM48fPPVYm")
# Setup ngrok tunnel
# public_url = ngrok.connect(8000, hostname="up-cobra-hardy.ngrok-free.app").public_url
# print(f"Public URL: {public_url}")

app = FastAPI()

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # Allow all origins (or specify ["http://localhost:8000"])
#     allow_credentials=True,
#     allow_methods=["*"],   # Allow all methods (GET, POST, etc.)
#     allow_headers=["*"],   # Allow all headers
# )
@app.middleware("http")
async def log_request_time(request:
    Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    print(f"Request: {request.url} took {process_time} seconds")
    return response


app.mount("/static", StaticFiles(directory="static"), name="static")

class CropType(BaseModel):
    crop_type: str

# Routes
app.get("/")(lambda: {"message": "Smart Irrigation API Running"})
app.get("/get_crops")(get_crops)
@app.post("/set_croptype")
async def crop_type(request: CropType):
    
    data = await  set_croptype(request.crop_type)
    return data
# app.get("/read_sensor")(read_sensor)
app.get("/forecast")(get_weather)
app.get("/moisture_forecast")(predict_moisture)

app.websocket("/ws")(websocket_endpoint)
  

def open_browser():
    time.sleep(1)
    webbrowser.open("http://localhost:8000/static/r.html")

if __name__ == "__main__":
    threading.Thread(target=open_browser).start()
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")
