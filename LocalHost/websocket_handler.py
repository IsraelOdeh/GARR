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

# def read_sensor():
#     if ser is not None:
#         data = ser.readline().decode().strip()
#         values = data.split(",")
#         if len(values) == 4:
#             temperature, moisture, humidity, irrigation = values
#             return {"temperature": temperature, "moisture": moisture, "humidity": humidity, "irrigation": irrigation}
#     return {"error": "No data received"}

async def push_2_mc(min_threshold, max_threshold, rain):
    data = f"{min_threshold},{max_threshold},{rain}\n"
    ser.write(data.encode())
    # print("Data pushed to microcontroller")

sensor_data = pd.DataFrame(columns=["Time", "Crop", "Moisture", "Temperature", "Humidity", "Irrigation"])

# async def event_generator():
#     global sensor_data, CurrentSoilMoisture
#     """Yields sensor data as SSE events."""
#     while True:
#         print("here")

        
#         try:
#             if ser is not None:
#                 print("conn")
#                 data = ser.readline().decode().strip()
#                 print(data)
#                 values = data.split(",")
#                 if len(values) == 4:
#                     temperature, moisture, humidity, irrigation = values
#                     CurrentSoilMoisture = moisture
#                     new_data = pd.DataFrame([[time.strftime("%H:%M:%S"), "Maize", moisture, temperature, humidity, irrigation]], 
#                                             columns=["Time", "Crop", "Moisture", "Temperature", "Humidity", "Irrigation"])
#                     sensor_data = pd.concat([sensor_data, new_data], ignore_index=True).tail(50)
                  
                  
#                     event_str = f"event: myEvent\ndata: {json.dumps(
#                         {'temperature': f'{temperature}',
#                         'moisture': f'{moisture}',
#                         'humidity': f'{humidity}',
#                         'irrigation': f'{irrigation}'
#                     })}\n\n"
#                     yield event_str
#                     await asyncio.sleep(2)  # Non-blocking delay
#                 # push_2_mc()
#                 yield f": keep-alive\n\n"
#         except Exception as e:
#             print(f"Error: {e}")
#             break
        
#         # yield f"data: {sensor_data}\n\n"
#         # await asyncio.sleep(4)  # Simulate new data every 2 seconds



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
                        print("Sending data to Socket")
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

