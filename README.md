# Automated Irrigation System

A virtual simulation-based irrigation control system that bridges Proteus hardware simulation with a web-based GUI for real-time monitoring and control.

## Prerequisites

- [VSPE (Virtual Serial Port Emulator)](https://www.eterlogic.com/Products.VSPE.html)
- [Proteus 8 Professional](https://www.labcenter.com/)

## Setup Guide

### 1. Virtual COM Port Setup

1. Install **VSPE**
2. Launch VSPE and:
   - Go to **Device → Create New Device**
   - Select **"Virtual Pair"** connector type
   - Set **First port** to `COM1` and **Second port** to `COM2`
   - Click **Create Device**

### 2. Proteus Simulation

1. Open `ProteusCircuit.pdsprj` (located in the `/Proteus Simulation` directory)
2. Configure the virtual terminal:
   - Right-click on **"GSM Module"** → **Edit Properties**
   - Set **Port** to `COM1` or `COM2` (matching VSPE)
3. Run the simulation

### 3. Start Application (Windows)

```bat
run.bat
```

## System Workflow

1. **Proteus Simulation**
   - Soil moisture/temperature sensors generate virtual data
   - Data transmitted via virtual COM port (`COM1 → COM2`)

2. **Web Server**
   - Listens on `COM2` for serial data
   - Processes sensor values using Python scripts
   - Serves real-time updates via WebSocket

3. **Dashboard**
   - Displays live sensor values
   - Shows irrigation pump status
   - Visualizes historical trends

## Usage Instructions

### Adjust Sensors in Proteus

1. Double-click sensor components
2. Modify analog values:
   - **Soil Moisture:** 0–1023 (0 = dry, 1023 = wet)
   - **Temperature:** 0–100 (°C)

### Monitor Web Dashboard

- Access `http://localhost:3000`
- Real-time updates will appear in 2–3 seconds

### Trigger Irrigation

- Click **"Manual Override"** in the dashboard
- Observe pump activation in the Proteus simulation

## Troubleshooting

| Issue | Solution |
|-------|----------|
| COM Port Conflict | Close other serial port software |
| No Data in Dashboard | Check VSPE connection status |
| Proteus Simulation Freeze | Reduce simulation speed to 75% |
| Web Interface Not Loading | Reload browser |
