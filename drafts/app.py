import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import pandas as pd
import time
import threading

# Define crop-based moisture thresholds
crop_thresholds = {
    "Wheat": 400,
    "Rice": 600,
    "Corn": 500,
    "Tomato": 450
}

# Function to determine irrigation status
def irrigation_decision(moisture, crop_type):
    threshold = crop_thresholds.get(crop_type, 500)  # Default threshold = 500 if crop not listed
    return "ON" if moisture < threshold else "OFF"

# Function to simulate moisture decrease over time
def decrease_moisture():
    global current_moisture, current_temperature, current_humidity
    while True:
        print('decreasing')
        # Decrease moisture dynamically based on temperature & humidity
        loss_rate = (0.1 * current_temperature) - (0.05 * current_humidity)  
        current_moisture = max(0, current_moisture - loss_rate)  # Prevent negative values
        time.sleep(3)  # Adjust simulation speed
print('done')
# Initialize sensor values
current_moisture = 500
current_temperature = 25
current_humidity = 50

# Start moisture decrease simulation in a background thread
moisture_thread = threading.Thread(target=decrease_moisture, daemon=True)
moisture_thread.start()


# Initialize app
app = dash.Dash(__name__)

# Data storage for real-time updates
sensor_data = pd.DataFrame(columns=["Time", "Crop", "Moisture", "Temperature", "Humidity", "Irrigation"])

# Layout of the dashboard
app.layout = html.Div([
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

                html.Label("💧 Enter Soil Moisture:"),
                dcc.Input(id='moisture-input', type='number', value=500, step=10),

                html.Label("🌡 Enter Temperature (°C):"),
                dcc.Input(id='temperature-input', type='number', value=25, step=0.1),

                html.Label("💦 Enter Humidity (%):"),
                dcc.Input(id='humidity-input', type='number', value=50, step=1),

                html.Button("Submit", id="submit-button", n_clicks=0, style={"margin-top": "10px"}),
            ], style={'width': '50%', 'margin': 'auto', 'padding': '20px', 'border': '1px solid black'}),


            html.H3("🌿 Current Soil Moisture:"),
            html.Div(id='moisture-display', style={'fontSize': '24px', 'color': 'blue'}),

            html.H3("🚰 Irrigation Status:"),
            html.Div(id='irrigation-status', style={'fontSize': '24px', 'color': 'green'}),

            dcc.Graph(id='live-chart'),
            dcc.Interval(id='interval-update', interval=3000, n_intervals=0)  # Update every 3 sec
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

# Callback to update sensor values and chart
@app.callback(
    [Output('moisture-display', 'children'),
     Output('irrigation-status', 'children'),
     Output('live-chart', 'figure')],
    [Input('submit-button', 'n_clicks'),
     Input('interval-update', 'n_intervals')],
    [State('crop-type', 'value'),
     State('moisture-input', 'value'),
     State('temperature-input', 'value'),
     State('humidity-input', 'value')]
)
def update_metrics(n_clicks, n_intervals, crop, moisture, temperature, humidity):
    global current_moisture, current_temperature, current_humidity, sensor_data

    if n_clicks > 0:  
        # moisture = current_moisture
        current_temperature = temperature
        current_humidity = humidity

    # Determine irrigation status
    irrigation_status = irrigation_decision(current_moisture, crop)

    # Append new data
    new_data = pd.DataFrame([[time.strftime("%H:%M:%S"), crop, current_moisture, current_temperature, current_humidity, irrigation_status]],
                            columns=["Time", "Crop", "Moisture", "Temperature", "Humidity", "Irrigation"])
    sensor_data = pd.concat([sensor_data, new_data], ignore_index=True).tail(50)  # Keep last 50 readings

    # Create real-time plot
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=sensor_data["Time"], y=sensor_data["Moisture"], mode='lines+markers', name="Moisture", line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=sensor_data["Time"], y=sensor_data["Temperature"], mode='lines+markers', name="Temperature", line=dict(color='red')))
    fig.add_trace(go.Scatter(x=sensor_data["Time"], y=sensor_data["Humidity"], mode='lines+markers', name="Humidity", line=dict(color='green')))
    fig.update_layout(title="📊 Sensor Readings Over Time", xaxis_title="Time", yaxis_title="Value")

    return f"Moisture Level: {current_moisture}%", f"Irrigation: {irrigation_status}", fig


# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
