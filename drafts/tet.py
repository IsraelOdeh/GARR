import threading
import serial
import dash
from dash import dcc, html
import time
from dash.dependencies import Input, Output, State

SERIAL_PORT = "COM2"  # Update to your actual port
BAUD_RATE = 9600

# Define crop-based moisture thresholds
crop_thresholds = {
    "Wheat": 400,
    "Rice": 600,
    "Corn": 500,
    "Tomato": 450
}


Temperature =  None
Moisture = None
Irrigation = None
Humidity =  None

ser = None  # Global variable for serial connection


def data_log():
    global Temperature, Moisture, Irrigation, Humidity
    while True:
        # print("true")
        
        try:
            if ser is not None:
                # ser.write(b'fuhijinjjjjj')
                thresh = 30
                maxi = 60
                data = f"{thresh},{maxi}\n"
                ser.write(data.encode())
                line = ser.readline().decode().strip()
                print(line)
            
            
                data = ser.readline().decode("utf-8").strip()
                # return f"Sensor Data: {data}"
                values = data.split(",")
                print(values)
                if len(values) == 3:
                    Temperature, Humidity, Moisture = float(values[0]), float(values[1]), float(values[2])
                    Irrigation= "ON" if Moisture < 500 else "OFF"  
                print(Moisture, Temperature, Humidity)
            
            
            
                # i = i + 1
                # print(i)
                # values = line.split(",")
                # if len(values) == 3:
                #     moisture, temperature, crop_type = int(values[0]), float(values[1]), values[2]
                #     irrigation_status = "ON" if moisture < 500 else "OFF"  

                #     # Store in Database
                #     cursor.execute("INSERT INTO sensor_data (moisture, temperature, crop_type, irrigation_status) VALUES (?, ?, ?, ?)", 
                #                    (moisture, temperature, crop_type, irrigation_status))
                #     conn.commit()

        except KeyboardInterrupt:
            ser.close()
            # conn.close()
            break

# Start data logging in a background thread
moisture_thread = threading.Thread(target=data_log, daemon=True)
moisture_thread.start()


def get_serial_connection():
    global ser
    if ser is None:
        try:
            ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
            print(f"✅ Connected to {SERIAL_PORT}")
            time.sleep(2)  # Allow time for connection
        except serial.SerialException as e:
            print(f"⚠️ Serial connection error: {e}")
            ser = None
    return ser

# Initialize Dash app
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Smart Irrigation Dashboard"),
    dcc.Interval(id="interval", interval=1000),  # Auto-refresh every 2 seconds
    html.Div(id="sensor-output"),
    
    dcc.Tabs([
        dcc.Tab(label='Simulation', children=[
            html.H1("🚀 Smart Irrigation Dashboard", style={'textAlign': 'center'}),

            html.Div([
                html.Label("🌱 Select Crop Type:"),
                dcc.Dropdown(
                    id='crop-type',
                    options=[{'label': crop, 'value': crop} for crop in crop_thresholds.keys()],
                    value="Wheat",
                    clearable=False
                ),

                # html.Label("💧 Enter Soil Moisture:"),
                # dcc.Input(id='moisture-input', type='number', value=500, step=10),

                # html.Label("🌡 Enter Temperature (°C):"),
                # dcc.Input(id='temperature-input', type='number', value=25, step=0.1),

                # html.Label("💦 Enter Humidity (%):"),
                # dcc.Input(id='humidity-input', type='number', value=50, step=1),

                html.Button("Submit", id="submit-button", n_clicks=0, style={"margin-top": "10px"}),
            ], style={'width': '50%', 'margin': 'auto', 'padding': '20px', 'border': '1px solid black'}),


            html.H3("🌿 Current Temperature:"),
            html.Div(id='temperature-display', style={'fontSize': '24px', 'color': 'blue'}),

            html.H3("🌿 Current Soil Moisture:"),
            html.Div(id='moisture-display', style={'fontSize': '24px', 'color': 'blue'}),

            html.H3("🚰 Irrigation Status:"),
            html.Div(id='irrigation-status', style={'fontSize': '24px', 'color': 'green'}),
            
             html.H3("🚰 HUMDITY:"),
            html.Div(id='humidity-display', style={'fontSize': '24px', 'color': 'green'}),

            dcc.Graph(id='live-chart'),
            # dcc.Interval(id='interval-update', interval=3000, n_intervals=0)  # Update every 3 sec
        ]),
        dcc.Tab(label='System Model', children=[
            dcc.Graph(
                figure={
                    'data': [
                        {'x': [1, 2, 3], 'y': [1, 4, 1],
                            'type': 'bar', 'name': 'SF'},
                        {'x': [1, 2, 3], 'y': [1, 2, 3],
                         'type': 'bar', 'name': 'Montréal'},
                    ]
                }
            )
        ]),
    ])

])

@app.callback(
    [Output('temperature-display', 'children'),
     Output('moisture-display', 'children'),
     Output('irrigation-status', 'children'),
     Output('humidity-display', 'children')],
    [Input('interval', 'n_intervals')]
)
def update_sensor_data(n):
    global Temperature, Moisture, Irrigation, Humidity, ser
    # print('sensingggggggggggggggggg')
    ser = get_serial_connection()
    
    # if ser and ser.in_waiting > 0:
    #     data = ser.readline().decode("utf-8").strip()
    #     # return f"Sensor Data: {data}"
    #     values = data.split(",")
    #     print(values)
    #     if len(values) == 3:
    #         temperature, humidity, moisture = float(values[0]), float(values[1]), float(values[2])
    #         irrigation_status = "ON" if moisture < 500 else "OFF"  
    #     # print(moisture, tem perature, humidity)
    # # return 
    return f"Temperature: {Temperature}%",f"Moisture: {Moisture}", f"Irrigation: {Irrigation}", f"humidity: {Humidity}"


if __name__ == "__main__":
    app.run_server(debug=True)
