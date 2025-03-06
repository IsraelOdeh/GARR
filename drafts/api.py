import asyncio
from pyngrok import ngrok
from fastapi.websockets import WebSocketState
import pandas as pd
import requests
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import serial
import webbrowser
import threading
from fastapi.staticfiles import StaticFiles
import time


# Authenticate ngrok (only needed once)
# ngrok.set_auth_token("2tiPuZueOT7lygddUceX6cYsZdU_6A27SFURDL9iM48fPPVYm")

# Create a tunnel with a reserved domain (change 'your-subdomain' to something unique)
public_url = ngrok.connect(8000, hostname="amazing-pipefish-hopefully.ngrok-free.app").public_url

print(f"Public URL: {public_url}")



app = FastAPI()

# Mount the "static" folder to serve HTML, CSS, JS
app.mount("/static", StaticFiles(directory="static"), name="static")

crop_data = json.load(open("crop_threshold.json"))

SERIAL_PORT = "COM2"  #Arduino/Proteus COM port
BAUD_RATE = 9600
Rain = 1
crop = "Maize"

ser = None 

ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1) # Open serial connection
time.sleep(2)  # Allow time for connection


API_KEY = "81245a4060df8f46e902ae3ea046f888" 
CITY = "Minna" 
URL = f"http://api.openweathermap.org/data/2.5/forecast?q={CITY}&appid={API_KEY}&units=metric"

min_threshold = 20
max_threshold = 60

# Data storage for real-time updates
sensor_data = pd.DataFrame(columns=["Time", "Crop", "Moisture", "Temperature", "Humidity", "Irrigation"])

@app.get("/")
def home():
    return {"message": "Smart Irrigation API Running"}

@app.get("/get_crops")
def get_crops():   
    crop_list = [entry for entry in crop_data.keys()]
    return{"crops": crop_list }

    
    
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global crop, sensor_data
    await websocket.accept()
    while True:
        try:
            if ser is not None:
                print("here")

                data = ser.readline().decode().strip()
                values = data.split(",")
                print(data)
                if len(values) == 4:
                    temperature, moisture, humidity, irrigation = values
                    print("6789")
                    
                    
                    # Append new data
                    new_data = pd.DataFrame([[time.strftime("%H:%M:%S"), crop, moisture, temperature, humidity, irrigation]],columns=["Time", "Crop", "Moisture", "Temperature", "Humidity", "Irrigation"])
                    sensor_data = pd.concat([sensor_data, new_data], ignore_index=True).tail(50)  # Keep last 50 readings
                    print(sensor_data)
                    # print(websocket.application_state)
                    
                    if websocket.application_state == WebSocketState.CONNECTED:
                        print("Sending data to Socket")
                        await websocket.send_text(f"{temperature},{moisture},{humidity},{irrigation},{Rain}")
            
                push_2_mc()
            await asyncio.sleep(0.1)  # Prevent CPU overuse
        except WebSocketDisconnect:
            print("Client disconnected, stopping data transmission.")
        except Exception as e:
            print(f"Error: {e}")
            break
        
@app.get("/read_sensor")
def read_sensor():
    print("reading")
    if ser is not None:
        print("here")
        # line = ser.readline().decode().strip()
        data = ser.readline().decode().strip()
        values = data.split(",")
        print(data)
        if len(values) == 4:
            temperature, moisture, irrigation, humidity = values
            return {
                "temperature": temperature,
                "moisture": moisture,
                "irrigation": irrigation,
                "humidity": humidity
            }
    
    return {"error": "No data received"}


def push_2_mc():
    global min_threshold, max_threshold, Rain
    data = f"{min_threshold},{max_threshold},{Rain}\n"
    ser.write(data.encode())       
    


# @app.post("/set_croptype")
def set_croptype(crop_type: str):
    global crop,  min_threshold, max_threshold, Rain
    if crop_type in crop_data:
        min_threshold, max_threshold = crop_data[crop_type]
        Rain = 1
        push_2_mc()
        
        crop = crop_type
        return {"message": f"Crop type set to {crop_data}% moisture"}
    else:
        return {"error": "Crop type not found"}
        
@app.get('/forecast')
def get_weather(): 
    global Rain
    try:
        response = requests.get(URL)
        data = response.json()
        
    except Exception as e:
        return "error"
        
    print(data)
    forecast_list = []
    i = 0
    for entry in data["list"]:  # Iterate through forecast data
        if i < 3:
            if i == 0:
                if entry["weather"][0]["main"] == "Rain":
                    Rain = 1
                    data = f"{min_threshold},{max_threshold}\n"
                    ser.write(data.encode())      
                else:
                    Rain = 0
            forecast_list.append({
                "datetime": entry["dt_txt"],  
                "temperature": entry["main"]["temp"],
                "humidity": entry["main"]["humidity"],
                "condition": entry["weather"][0]["main"],
                "description": entry["weather"][0]["description"]
            })
            
            i += 1
            print(i)
        else:
            print("done")
            break
            
            
    print(forecast_list)
    return {"forecast": forecast_list}

      

      
# SEND RAIN STATE TO ARDUINO  
    
set_croptype("Barley")
    
def open_browser():
    time.sleep(1)  # Give Flask time to start
    webbrowser.open("http://localhost:8000/static/index.html")
    
    
if __name__ == "__main__":
    import uvicorn
    threading.Thread(target=open_browser).start()  # Run browser opener in separate thread
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")
