from datetime import datetime
import json
import time
import numpy as np
import pandas as pd
from pyeto import deg2rad, et_rad, inv_rel_dist_earth_sun, sol_dec, sunset_hour_angle
import requests
import crop_data
# import weather
import websocket_handler
from websocket_handler import push_2_mc

API_KEY = "81245a4060df8f46e902ae3ea046f888"
CITY = "Minna"
URL = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/Minna?unitGroup=metric&key=HSEZGHEEGJ9NXYNHXFL4LVMLF&include=fcst%2Chours%2Ccurrent"

Rain = 0
NOW = time.strftime("%H:%M:%S")

dataset = pd.DataFrame()

def get_weather():
    global dataset, Rain
    try:
        response = requests.get(URL).json()
        # print(response)
    except Exception as e:
        return {"error": str(e)}

   # Remove entries from the JSON response that are not needed
    response["days"][0]["hours"] = list(filter(lambda hour: datetime.strptime(hour["datetime"], "%H:%M:%S") > datetime.strptime(NOW, "%H:%M:%S"), response["days"][0]["hours"]))
    coming_days = []
    for entry in response["days"][:2]:
        for hour in entry["hours"] :
            coming_days.append(hour)
        
    # print(coming_days)
    forecast_weather = []
    forecast_moisture = []
    latitude = response["latitude"]
    i = 0
    date = datetime.strptime(response["days"][0]["datetime"], "%Y-%m-%d").strftime("%Y-%m-%d")
    for hour in coming_days[:3]:
            print(hour)
            if i == 0:
                    if hour["conditions"] == "Rain":
                        Rain = 1
                        push_2_mc(crop_data.min_threshold,crop_data.max_threshold,Rain)
                    else:
                        Rain = 0
        # for hour in entry["hours"][:3]:
            forecast_weather.append({
                "DATE": hour["datetime"],
                "TEMP": hour["temp"],
                "RH": hour["humidity"],
                "condition": hour["conditions"]
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
   
    dataset = pd.DataFrame(forecast_moisture)

    return {"forecast": forecast_weather}


# get_weather()

# print(dataset.head())

crop = "Wheat"
growth_stage = "mid"


kc_values =  json.load(open("crop_threshold.json"))["kc_values"]



def hargreaves_et0(row):
 
    lat_rad = deg2rad(row["LAT"])
    forecast_date = datetime.strptime(row["DATE"], "%Y-%m-%d")
    
    day_of_year = forecast_date.timetuple().tm_yday
    
    ra = et_rad(lat_rad, sol_dec(day_of_year), sunset_hour_angle(lat_rad, sol_dec(day_of_year ),),inv_rel_dist_earth_sun(day_of_year )) 
    # print(f"Extraterrestrial Radiation (Ra): {ra:.2f} MJ/m²/day")
                
    return 0.0023 * ra * (row["Tmean"] + 17.8) * (row["Tmax"] - row["Tmin"])**0.5
    # return hargreaves(row["Tmin"], row["Tmax"], row["Tmean"], ra)

def etc(row):
    
    ET0 = row["ET0"]
    
    # Get Crop Coefficient
    Kc = kc_values[crop][growth_stage]

    # Compute Crop Evapotranspiration (ETc)
  
    return Kc * ET0

def estimate_hydraulic_properties(silt, clay, sand, qSAT, qWP):
    """Estimate Ks and S based on soil texture"""
    theta_r = 0.02 + 0.3 * qWP  # Residual water content estimate
    Ks = 1930 * ((qSAT - theta_r) ** 3.1)  # Saxton & Rawls (2006)
    Psi = 10 ** (1.88 - 0.0131 * sand)  # Rawls & Brakensiek (1985)
    delta_theta = qSAT - qWP  # Moisture difference
    S = np.sqrt(2 * Ks * Psi * delta_theta)  # Sorptivity equation
    return Ks, S

def get_soil_properties():
    """Fetch soil properties (field capacity, wilting point) from SoilGrids API."""
    # SOILGRIDS_URL = f"https://rest.isric.org/soilgrids/v2.0/properties/query?lon=9.61373&lat=6.54367&property=clay&property=silt&property=sand&depth=5-15cm&value=mean"
    try:
        # response = requests.get(SOILGRIDS_URL).json()
        response = json.load(open("soil.json"))
        
        properties = response["properties"]
    
    
        clay = (properties["layers"][0]["depths"][-1]["values"]["mean"])/10  # Clay content (%)
        sand = (properties["layers"][1]["depths"][-1]["values"]["mean"])/10  # Silt content (%)
        silt = (properties["layers"][2]["depths"][-1]["values"]["mean"])/10  # Sand content (%)
        print(clay, sand, silt)

        # Estimate Field Capacity (FC) and Wilting Point (WP) using Saxton & Rawls equations
        # FC = (0.31 + 0.0021 * clay) * 100  # mm/m
        # WP = (0.14 + 0.0017 * clay) * 100  # mm/m

        return sand, silt, clay
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching soil properties: {e}")
        return None
    
def calc_moisture(  silt, clay, sand):
    """Calculate qSAT, qFC, and qWP using Jabloun & Sahli (2006) equations"""
    qSAT = (
        0.6658 * silt + 0.1567 * sand - 0.0079 * (silt ** 2)
        - 12.31121 / sand - 6.4756 * np.log(sand)
        - 0.0038 * (clay * silt) + 0.0038 * (clay * sand)
        - 0.0042 * (silt * sand) + 52.7526
    )
    
    qFC = (
        118.932 * clay + 119.0866 * silt + 119.1104 * sand
        + 162.31731 / clay - 46.21921 / silt - 5.12991 / sand
        + 18.1733 * np.log(clay) + 0.0013 * (clay * silt)
        + 0.0022 * (silt * sand) - 11939.3493
    )
    
    qWP = (
        -1.5722 * silt - 0.5423 * sand - 0.0072 * (clay ** 2)
        + 0.0072 * (silt ** 2) - 0.0059 * (sand ** 2)
        + 160.14591 / clay + 6.60011 / sand
        + 0.0022 * (clay * silt) - 0.0039 * (clay * sand) + 92.3851
    )
    
    qSAT = round(qSAT, 2)
    qFC = round(qFC, 2)
    qWP = round(qWP, 2)
    
    print(qSAT, qFC, qWP)
    return qSAT, qFC, qWP

def soil_water_balance(silt, clay, sand, P, ETc):
    """Calculate soil moisture balance using estimated soil properties"""
    qSAT, qFC, qWP = calc_moisture(silt, clay, sand)
    
    Ks, S = estimate_hydraulic_properties(silt, clay, sand, qSAT, qWP)
    
    # Initial soil moisture assumed at field capacity
    # websocket_handler.CurrentSoilMoisture = qFC  
    # websocket_handler.CurrentSoilMoisture = 60
    t = 1
    infiltration_rate =(S/ np.sqrt(t)) + Ks
    
    R = max(0, dataset["PRCP"][0] - infiltration_rate)
    
    D = max(0, websocket_handler.CurrentSoilMoisture + dataset["PRCP"][0] - ETc - R - qFC)
    
    # Water balance equation with constraints
    SoilMoisture = max(qWP, min(qFC, websocket_handler.CurrentSoilMoisture + P - ETc - D - R)) # in mm/m3 or %


    nxt_R = max(0, dataset["PRCP"][1] - infiltration_rate)
    
    nxt_D = max(0, SoilMoisture + dataset["PRCP"][1] - ETc - R - qFC)
    NxtSoilMoisture = round(max(qWP, min(qFC, SoilMoisture + P -dataset["ETc"][1] - nxt_D - nxt_R)),2) # in mm/m3 or %
        
    return SoilMoisture, NxtSoilMoisture


def predict_moisture():
    global dataset
    get_weather()
    
    # Compute ET0 (Reference Evapotranspiration) using Hargreaves-Samani method
    dataset["ET0"] = dataset.apply(hargreaves_et0, axis=1)

    # Compute Crop Evapotranspiration (ETc)
    dataset["ETc"] = dataset.apply(etc, axis=1)


    sand, silt, clay = get_soil_properties()
    print(f"soils{sand},{silt},{clay}")
    
    SoilMoisture, NxtSoilMoisture = soil_water_balance(silt, clay, sand, dataset["PRCP"][0], dataset["ETc"][0])
    return SoilMoisture, NxtSoilMoisture
# SoilMoisture, NxtSoilMoisture = soil_water_balance(silt, clay, sand, dataset["PRCP"][0], dataset["ETc"][0])

# Update Soil Moisture
# dataset["moist"] = dataset.apply(lambda row: moisture(row), axis=1)

# predict_moisture()
