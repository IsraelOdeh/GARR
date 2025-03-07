import asyncio
import json
import pandas as pd
import time
import serial
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState
import LocalHost.config as config


SERIAL_PORT = "COM2"
BAUD_RATE = 9600
CurrentSoilMoisture = 0

ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
time.sleep(2)


async def push_2_mc(min_threshold, max_threshold, rain):
    data = f"{min_threshold},{max_threshold},{rain}\n"
    ser.write(data.encode())
    # print("Data pushed to microcontroller")

sensor_data = pd.DataFrame(columns=["Time", "Crop", "Moisture", "Temperature", "Humidity", "Irrigation"])


async def websocket_endpoint(websocket: WebSocket):
    global sensor_data
    await websocket.accept()
    while True:
        try:
            if ser is not None:
        
                data = ser.readline().decode().strip()
                values = data.split(",")
                
                if len(values) == 5:
                    temperature, moisture, humidity,water_usage,irrigation = values
                    config.CurrentSoilMoisture = int(moisture)
                    
                    # Append new data
                    new_data = pd.DataFrame([[time.strftime("%H:%M:%S"), config.crop, moisture, temperature, humidity, irrigation]],columns=["Time", "Crop", "Moisture", "Temperature", "Humidity", "Irrigation"])
                    sensor_data = pd.concat([sensor_data, new_data], ignore_index=True).tail(50)  # Keep last 50 readings
                   
                    if websocket.application_state == WebSocketState.CONNECTED:
                        # print("Sending data to Socket")
                        if not sensor_data.empty:
                           
                            row = json.dumps(sensor_data.iloc[-1].to_dict())
                        
                            response = {
                                "temperature":temperature,
                                "moisture": moisture,
                                "humidity": humidity,
                                "water_usage": water_usage,
                                "irrigation": irrigation,
                                "rain": config.Rain,
                                "row": row
                                    }

                            await websocket.send_text(json.dumps(response))
                            
                        else:
                            print("Error: sensor_data DataFrame is empty! Cannot send last row.")
                
               
                await asyncio.sleep(0.1)  # Prevent CPU overuse
        except WebSocketDisconnect:
            print("Client disconnected, stopping data transmission.")
        except Exception as e:
            print(f"Error: {e}")
            break
    

async def to_mc():
     await push_2_mc(config.min_threshold,config.max_threshold,config.Rain)
     await asyncio.sleep(4)

