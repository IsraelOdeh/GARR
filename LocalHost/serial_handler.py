import serial
import time

SERIAL_PORT = "COM2"
BAUD_RATE = 9600

ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
time.sleep(2)

def read_sensor():
    if ser is not None:
        data = ser.readline().decode().strip()
        values = data.split(",")
        if len(values) == 4:
            temperature, moisture, humidity, irrigation = values
            return {"temperature": temperature, "moisture": moisture, "humidity": humidity, "irrigation": irrigation}
    return {"error": "No data received"}

def push_2_mc(min_threshold=20, max_threshold=60, rain=1):
    data = f"{min_threshold},{max_threshold},{rain}\n"
    ser.write(data.encode())
