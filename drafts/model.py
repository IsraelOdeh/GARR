from datetime import datetime
import json
import numpy as np
import pandas as pd
import requests
import time
from pyeto import deg2rad,  inv_rel_dist_earth_sun, sol_dec, sunset_hour_angle, et_rad

CITY = "Minna" 
API_KEY = "81245a4060df8f46e902ae3ea046f888" 
URL = f"http://api.openweathermap.org/data/2.5/forecast?q={CITY}&appid={API_KEY}&units=metric"

NOW = time.strftime("%H:%M:%S")

try:
    response = requests.get("https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/Minna?unitGroup=metric&key=HSEZGHEEGJ9NXYNHXFL4LVMLF&include=fcst%2Chours%2Ccurrent").json()
    # response = json.load(open("test.json"))

    # Remove entries from the JSON response that are not needed
    response["days"][0]["hours"] = list(filter(lambda hour: datetime.strptime(hour["datetime"], "%H:%M:%S") > datetime.strptime(NOW, "%H:%M:%S"), response["days"][0]["hours"]))
    
    forecast_data = []
    latitude = response["latitude"]
    
    for entry in response["days"]:
        for hour in entry["hours"]:
            forecast_data.append({
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
    dataset = pd.DataFrame(forecast_data)
    
    # print(dataset.head())
    # return {"forecast": forecast_list}
except Exception as e:
    print(e)
    # return {"error":"An error was encountered"}
    

# Crop Coefficients (Kc values)
kc_values = {
    "wheat": {"initial": 0.4, "mid": 1.15, "late": 0.3},
    "corn": {"initial": 0.4, "mid": 1.2, "late": 0.5},
    "rice": {"initial": 1.0, "mid": 1.2, "late": 0.9},
}

crop = "wheat"
growth_stage = "mid"


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

# Compute ET0 (Reference Evapotranspiration) using Hargreaves-Samani method
dataset["ET0"] = dataset.apply(hargreaves_et0, axis=1)

# Compute Crop Evapotranspiration (ETc)
dataset["ETc"] = dataset.apply(etc, axis=1)


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
    

sand, silt, clay = get_soil_properties()
print(f"soils{sand},{silt},{clay}")

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
    # soil_moisture = qFC  
    soil_moisture = 90
    t = 1
    infiltration_rate =(S/ np.sqrt(t)) + Ks
    
    R = max(0, dataset["PRCP"][0] - infiltration_rate)
    
    D = max(0, soil_moisture + dataset["PRCP"][0] - ETc - R - qFC)
    
    # Water balance equation with constraints
    soil_moisture = max(qWP, min(qFC, soil_moisture + P - ETc - D - R)) # in mm/m3 or %


    nxt_R = max(0, dataset["PRCP"][1] - infiltration_rate)
    
    nxt_D = max(0, soil_moisture + dataset["PRCP"][1] - ETc - R - qFC)
    nxt_soil_moisture = round(max(qWP, min(qFC, soil_moisture + P -dataset["ETc"][1] - nxt_D - nxt_R)),2) # in mm/m3 or %
        
    return soil_moisture, nxt_soil_moisture

soil_moisture, nxt_soil_moisture = soil_water_balance(silt, clay, sand, dataset["PRCP"][0], dataset["ETc"][0])

# Update Soil Moisture
# dataset["moist"] = dataset.apply(lambda row: moisture(row), axis=1)

print(soil_moisture, nxt_soil_moisture)
