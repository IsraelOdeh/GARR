import asyncio
import json
from fastapi.responses import StreamingResponse
import pandas as pd
import time
import serial
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState
# from serial_handler import ser, push_2_mc






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

def push_2_mc(min_threshold, max_threshold, rain):
    data = f"{min_threshold},{max_threshold},{rain}\n"
    ser.write(data.encode())
    print("Data pushed to microcontroller")

sensor_data = pd.DataFrame(columns=["Time", "Crop", "Moisture", "Temperature", "Humidity", "Irrigation"])

async def event_generator():
    global sensor_data, CurrentSoilMoisture
    """Yields sensor data as SSE events."""
    while True:
        print("here")

        
        try:
            if ser is not None:
                print("conn")
                data = ser.readline().decode().strip()
                print(data)
                values = data.split(",")
                if len(values) == 4:
                    temperature, moisture, humidity, irrigation = values
                    CurrentSoilMoisture = moisture
                    new_data = pd.DataFrame([[time.strftime("%H:%M:%S"), "Maize", moisture, temperature, humidity, irrigation]], 
                                            columns=["Time", "Crop", "Moisture", "Temperature", "Humidity", "Irrigation"])
                    sensor_data = pd.concat([sensor_data, new_data], ignore_index=True).tail(50)
                  
                  
                    event_str = f"event: myEvent\ndata: {json.dumps(
                        {'temperature': f'{temperature}',
                        'moisture': f'{moisture}',
                        'humidity': f'{humidity}',
                        'irrigation': f'{irrigation}'
                    })}\n\n"
                    yield event_str
                    await asyncio.sleep(2)  # Non-blocking delay
                # push_2_mc()
                yield f": keep-alive\n\n"
        except Exception as e:
            print(f"Error: {e}")
            break
        
        # yield f"data: {sensor_data}\n\n"
        # await asyncio.sleep(4)  # Simulate new data every 2 seconds

def get_sse_response():
    """Returns a streaming response for SSE clients."""
    return StreamingResponse(event_generator(), media_type="text/event-stream")




