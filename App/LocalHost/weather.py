from datetime import datetime
import json
from pathlib import Path
import time
import pandas as pd
# from pyeto import deg2rad, et_rad, inv_rel_dist_earth_sun, sol_dec, sunset_hour_angle
import requests
import math
import LocalHost.crop_data as crop_data
import LocalHost.config as config
from LocalHost.websocket_handler import push_2_mc

CITY = "Minna"
URL = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/Minna?unitGroup=metric&key=HSEZGHEEGJ9NXYNHXFL4LVMLF&include=fcst%2Chours%2Ccurrent"



async def get_weather():
    try:
        response = requests.get(URL).json()
        # response = json.load(open("test.json"))
        # print(response)
    except Exception as e:
        return {"error": str(e)}

    coming_days = []
    # Remove forecast entries that have already passed
    # current_time = datetime.strptime(NOW, time_format)
    for entry in response["days"][:2]:
        entry["hours"] = [hour for hour in entry["hours"] if datetime.strptime(entry["datetime"] + " " + hour["datetime"], "%Y-%m-%d %H:%M:%S") > datetime.now()]
        for hours in entry["hours"]:
            coming_days.append(hours)
        
    # print(coming_days)
    forecast_weather = []
    forecast_moisture = []
    latitude = response["latitude"]
    i = 0
    date = datetime.strptime(response["days"][0]["datetime"], "%Y-%m-%d").strftime("%Y-%m-%d")
    for hour in coming_days[:3]:
            if i == 0:
                    if hour["conditions"] == "Rain":
                        config.Rain = 1
                        push_2_mc(config.min_threshold,config.max_threshold,config.Rain)
                    else:
                        config.Rain = 0
            forecast_weather.append({
                "DATE": hour["datetime"],
                "TEMP": hour["temp"],
                "RH": hour["humidity"],
                "condition": hour["conditions"],
                "icon": hour["icon"]
            })
   
   
    for entry in response["days"][:3]:
        for hour in entry["hours"]:
            forecast_moisture.append({
                "DATE": datetime.strptime(entry["datetime"], "%Y-%m-%d").strftime("%Y-%m-%d"),
                "TIME": datetime.strptime(hour["datetime"], "%H:%M:%S").strftime("%H:%M:%S"),
                "LAT": latitude,
                "TEMP": hour["temp"],
                "Tmin": entry["tempmin"],
                "Tmax":  entry["tempmax"],
                "Grossrad": entry["solarradiation"],
                "Tmean": (entry["tempmax"] + entry["tempmin"]) / 2,
                "PRCP": hour["precip"],
                "AWND": hour["windspeed"],
                "RH": hour["humidity"],
                "ATM": hour["pressure"]
            })
   
    config.dataset = pd.DataFrame(forecast_moisture)

    # predict_moisture()

    return {"forecast": forecast_weather}

crop = "Wheat"
growth_stage = "mid"

SCRIPT_DIR = Path(__file__).resolve().parent
kc_values =  json.load(open(SCRIPT_DIR.parent / "database/crop_threshold.json"))["kc_values"]


async def get_soil_properties():
    """Fetch soil properties (field capacity, wilting point) from SoilGrids API."""
    # SOILGRIDS_URL = f"https://rest.isric.org/soilgrids/v2.0/properties/query?lon=9.61373&lat=6.54367&property=clay&property=silt&property=sand&depth=5-15cm&value=mean"
    try:
        # response = requests.get(SOILGRIDS_URL).json()
        
        response = json.load(open(SCRIPT_DIR.parent / "database/soil.json"))
        
        properties = response["properties"]
    
    
        clay = (properties["layers"][0]["depths"][-1]["values"]["mean"])/10  # Clay content (%)
        sand = (properties["layers"][1]["depths"][-1]["values"]["mean"])/10  # Silt content (%)
        silt = (properties["layers"][2]["depths"][-1]["values"]["mean"])/10  # Sand content (%)
       

        # Estimate Field Capacity (FC) and Wilting Point (WP) using Saxton & Rawls equations
        # FC = (0.31 + 0.0021 * clay) * 100  # mm/m
        # WP = (0.14 + 0.0017 * clay) * 100  # mm/m

        return sand, silt, clay
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching soil properties: {e}")
        return None
    
import math
from datetime import datetime
import numpy as np

class SoilMoisturePredictor:
    def __init__(self, sand, silt, clay, initial_moisture, lat):
        self.sand = sand  # %
        self.silt = silt  # %
        self.clay = clay  # %
        self.lat = lat    # degrees
        self.current_moisture = initial_moisture  # m³/m³

        # Hydraulic properties
        self.theta_sat, self.theta_fc, self.theta_wp = self.calculate_hydraulic_properties()
        self.Ks = self.calculate_saturated_conductivity()  # cm/hour
        self.psi_f = self.calculate_matric_potential()  # cm

    # ---------------------------
    # Core Hydraulic Functions
    # ---------------------------
    def calculate_hydraulic_properties(self):
        """Saxton & Rawls (2006) equations"""
        theta_sat = 0.332 - 0.0007251*self.sand + 0.1276*math.log10(self.clay)
        theta_wp = theta_sat * (0.2576 - 0.002*self.sand)
        theta_fc = theta_sat * (0.026 + 0.005*self.clay + 0.0158*self.silt)
        return round(theta_sat,3), round(theta_fc,3), round(theta_wp,3)

    def calculate_saturated_conductivity(self):
        """Cosby et al. (1984)"""
        return (10**(1.88 - 0.0131*self.clay)) / 24  # cm/day → cm/hour

    def calculate_matric_potential(self):
        """Rawls & Brakensiek (1983)"""
        return -10 * math.exp(1.54 - 0.0095*self.sand + 0.0036*self.clay)

    # ---------------------------
    # ET Calculation Functions
    # ---------------------------
    def hargreaves_et0(self, tmin, tmax, tmean, date):
        """
        Hargreaves-Samani ET₀ (Allen et al., 1998)
        Returns ET₀ in mm/day
        """
        lat_rad = math.radians(self.lat)
        doy = datetime.strptime(date, "%Y-%m-%d").timetuple().tm_yday
        
        # Solar geometry calculations
        delta = 0.409 * math.sin(2*math.pi*doy/365 - 1.39)  # Solar declination
        dr = 1 + 0.033 * math.cos(2*math.pi*doy/365)        # Earth-Sun distance
        
        # Extraterrestrial radiation (Ra in MJ/m²/day)
        omega = math.acos(-math.tan(lat_rad) * math.tan(delta))  # Sunset hour angle
        ra = (24*60/math.pi) * 0.0820 * dr * (
            omega * math.sin(lat_rad) * math.sin(delta) + 
            math.cos(lat_rad) * math.cos(delta) * math.sin(omega)
        )
        
        return 0.0023 * ra * (tmean + 17.8) * math.sqrt(tmax - tmin)

    def calculate_etc(self, et0, crop_type, growth_stage):
        """
        FAO-56 Crop Coefficient Approach
        et0: Reference ET (mm/day)
        Returns ETc in cm/hour
        """
        kc_values = {
            'maize': [0.3, 0.8, 1.2, 0.6],  # Example growth stages
            'wheat': [0.4, 0.9, 1.1, 0.4]
        }
        kc = kc_values[crop_type][growth_stage]
        return (kc * et0) / 24 / 10  # Convert mm/day → cm/hour

    # ---------------------------
    # Water Balance Functions  
    # ---------------------------
    def update_moisture(self, P, etc):
        """
        P: Precipitation (cm/hour)
        etc: Crop ET (cm/hour)
        """
        # Convert moisture to cm depth (1m root zone)
        moisture_cm = self.current_moisture * 100
        
        # Green-Ampt infiltration
        S = math.sqrt(2 * self.Ks * abs(self.psi_f) * max(self.theta_sat,(self.theta_sat - self.current_moisture)))
        F = S * math.sqrt(1) + self.Ks * 1  # Hourly infiltration
        runoff = max(0, P - F)
        
        # Update moisture
        moisture_cm += (P - runoff) - etc
        moisture_cm = max(self.theta_wp*100, min(self.theta_sat*100, moisture_cm))
        
        # Drainage calculation
        if moisture_cm/100 > self.theta_fc:
            drainage = self.Ks * ((moisture_cm/100 - self.theta_fc)/(self.theta_sat - self.theta_fc))**3
            moisture_cm -= drainage
        
        self.current_moisture = moisture_cm / 100
        return self.current_moisture

async def predict_moisture():
    # Input parameters
    try:
        await get_weather()
        sand, silt, clay = await get_soil_properties()
        initial_moisture = config.CurrentSoilMoisture/100
        latitude = config.dataset["LAT"][0]
        soil_params = {
            'sand': sand, 'silt': silt, 'clay': clay,
            'initial_moisture': initial_moisture, 'lat': latitude  
        }
    
        date = config.dataset["DATE"][0]
        tmin = config.dataset["Tmin"][0]
        tmax = config.dataset["Tmax"][0]
        tmean = config.dataset["Tmean"][0]
        precip  = [config.dataset["PRCP"][0], config.dataset["PRCP"][1]]
        weather_data = {
            'date': date,
            'tmin': tmin, 'tmax': tmax, 'tmean': tmean,
            'precip': precip  # cm/hour
        }

        # Initialize model
        model = SoilMoisturePredictor(**soil_params)

        # Calculate ET components
        et0 = model.hargreaves_et0(weather_data['tmin'], weather_data['tmax'], 
                                  weather_data['tmean'], weather_data['date'])
        etc = model.calculate_etc(et0, 'maize', 2)  # Maize in mid-season

        # Run predictions
        results = [
            model.update_moisture(weather_data['precip'][0], etc),
            model.update_moisture(weather_data['precip'][1], etc)
        ]

        return{ "prediction":
            {
               "1h": round(results[0] *100,2) , 
               "2h": round(results[1]* 100,2)
            },
            "properties": {
               "ET": round(etc,3),
               "Sand": sand,
               "Silt": silt,
                "Clay": clay
            }
       }
    
    except Exception as e:
        print(f"Error: {e}")
        return{f"Error: {e}"}
