from datetime import datetime
import json
import time
import pandas as pd
from pyeto import deg2rad, et_rad, inv_rel_dist_earth_sun, sol_dec, sunset_hour_angle
import requests
import math
import crop_data
import config
from websocket_handler import push_2_mc

CITY = "Minna"
URL = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/Minna?unitGroup=metric&key=HSEZGHEEGJ9NXYNHXFL4LVMLF&include=fcst%2Chours%2Ccurrent"


NOW = time.strftime("%H:%M:%S")

# dataset = pd.DataFrame()

def get_weather():
    try:
        # response = requests.get(URL).json()
        response = json.load(open("test.json"))
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
                        config.Rain = 1
                        push_2_mc(config.min_threshold,config.max_threshold,config.Rain)
                    else:
                        config.Rain = 0
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
   
    config.dataset = pd.DataFrame(forecast_moisture)

    # predict_moisture()

    return {"forecast": forecast_weather}


# get_weather()

# print(dataset.head())

crop = "Wheat"
growth_stage = "mid"


kc_values =  json.load(open("crop_threshold.json"))["kc_values"]



# def hargreaves_et0(row):
 
#     lat_rad = deg2rad(row["LAT"])
#     forecast_date = datetime.strptime(row["DATE"], "%Y-%m-%d")
    
#     day_of_year = forecast_date.timetuple().tm_yday
    
#     ra = et_rad(lat_rad, sol_dec(day_of_year), sunset_hour_angle(lat_rad, sol_dec(day_of_year ),),inv_rel_dist_earth_sun(day_of_year )) 
#     # print(f"Extraterrestrial Radiation (Ra): {ra:.2f} MJ/m²/day")
                
#     return 0.0023 * ra * (row["Tmean"] + 17.8) * (row["Tmax"] - row["Tmin"])**0.5
#     # return hargreaves(row["Tmin"], row["Tmax"], row["Tmean"], ra)

# def etc(row):
    
#     ET0 = row["ET0"]
    
#     # Get Crop Coefficient
#     Kc = kc_values[crop][growth_stage]

#     # Compute Crop Evapotranspiration (ETc)
  
#     return Kc * ET0

# def estimate_hydraulic_properties(silt, clay, sand, qSAT, qWP):
#     """Estimate Ks and S based on soil texture"""
#     # theta_r = 0.02 + 0.3 * qWP  # Residual water content estimate
#     theta_r = 0.1 + 0.0007 * clay - 0.000015*(sand**2)  # Saxton & Rawls (2006)
#     # Ks = 1930 * ((qSAT - theta_r) ** 3.1)  # Saxton & Rawls (2006)
#     Ks = 10**(1.88-0.0131*clay) #Cosby et al. (1984)
#     Psi = -10 *math.exp(1.54 -0.0095*sand + 0.0063*clay)  # Rawls & Brakensiek (1983)
#     delta_theta = qSAT - qWP  # Moisture difference
#     S = math.sqrt( 2 * Ks * abs(Psi) * (qSAT - config.CurrentSoilMoisture)) # Sorptivity equation
#     return Ks, S

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
    
# def calc_moisture(  silt, clay, sand):
#     """Calculate qSAT, qFC, and qWP using Jabloun & Sahli (2006) equations"""
#     qSAT = (
#         0.6658 * silt + 0.1567 * sand - 0.0079 * (silt ** 2)
#         - 12.31121 / sand - 6.4756 * math.log(sand)
#         - 0.0038 * (clay * silt) + 0.0038 * (clay * sand)
#         - 0.0042 * (silt * sand) + 52.7526
#     )
    
#     qFC = (
#         118.932 * clay + 119.0866 * silt + 119.1104 * sand
#         + 162.31731 / clay - 46.21921 / silt - 5.12991 / sand
#         + 18.1733 * math.log(clay) + 0.0013 * (clay * silt)
#         + 0.0022 * (silt * sand) - 11939.3493
#     )
    
#     qWP = (
#         -1.5722 * silt - 0.5423 * sand - 0.0072 * (clay ** 2)
#         + 0.0072 * (silt ** 2) - 0.0059 * (sand ** 2)
#         + 160.14591 / clay + 6.60011 / sand
#         + 0.0022 * (clay * silt) - 0.0039 * (clay * sand) + 92.3851
#     )
    
#     qSAT = round(qSAT, 2)
#     qFC = round(qFC, 2)
#     qWP = round(qWP, 2)
    
#     print(qSAT, qFC, qWP)
#     return qSAT, qFC, qWP

# def soil_water_balance(silt, clay, sand, P, ETc):
#     """
#     Calculate soil moisture balance using estimated soil properties.

#     Parameters:
#     silt (float): Silt content percentage.
#     clay (float): Clay content percentage.
#     sand (float): Sand content percentage.
#     P (list): Precipitation values.
#     ETc (list): Crop Evapotranspiration values.

#     Returns:
#     tuple: Current soil moisture and next soil moisture values.
#     """
#     qSAT, qFC, qWP = calc_moisture(silt, clay, sand)
    
#     print(  qSAT, qFC, qWP )
#     Ks, S = estimate_hydraulic_properties(silt, clay, sand, qSAT, qWP)
    
#     # Initial soil moisture assumed at field capacity
#     # config.CurrentSoilMoisture = qFC  
#     # config.CurrentSoilMoisture = 60
#     t = 1
#     infiltration_rate =(S/ math.sqrt(t)) + Ks
    
#     if len(P) > 0:
#         R = max(0, P[0] - infiltration_rate)
#     else:
#         R = 0
#     print(P[0])
#     print(config.CurrentSoilMoisture)
#     D = max(0, config.CurrentSoilMoisture + P[0] - ETc[0] - R - qFC)
    
#     # Water balance equation with constraints
#     SoilMoisture = max(qWP, min(qFC, config.CurrentSoilMoisture + P[0] - ETc[0] - D - R)) # in mm/m3 or %


#     nxt_R = max(0, P[1] - infiltration_rate)
    
#     nxt_D = max(0, SoilMoisture + P[1] - ETc[1] - R - qFC)
#     NxtSoilMoisture = round(max(qWP, min(qFC, SoilMoisture + P[1] - ETc[1] - nxt_D - nxt_R)),2) # in mm/m3 or %
#     print(SoilMoisture, NxtSoilMoisture)
#     return SoilMoisture, NxtSoilMoisture


# def predict_moisture():

#     print(config.dataset)
    
#     dataset = config.dataset
#     # Compute ET0 (Reference Evapotranspiration) using Hargreaves-Samani method
#     dataset["ET0"] = dataset.apply(hargreaves_et0, axis=1)

#     # Compute Crop Evapotranspiration (ETc)
#     dataset["ETc"] = dataset.apply(etc, axis=1)


#     sand, silt, clay = get_soil_properties()
#     print(f"soils{sand},{silt},{clay}")
    
#     SoilMoisture, NxtSoilMoisture = soil_water_balance(silt, clay, sand, dataset["PRCP"][:2], dataset["ETc"][:2])
    
    
#     return { 
#                 "SoilMoisture": SoilMoisture, 
#                 "2hrNxtSoilMoisture": NxtSoilMoisture
#             }


# # SoilMoisture, NxtSoilMoisture = soil_water_balance(silt, clay, sand, dataset["PRCP"][0], dataset["ETc"][0])

# # Update Soil Moisture
# # dataset["moist"] = dataset.apply(lambda row: moisture(row), axis=1)

# # predict_moisture()

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

# Example Usage
# if __name__ == "__main__":
def predict_moisture():
    # Input parameters
    try:
        get_weather()
        sand, silt, clay = get_soil_properties()
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

        print(f"ET₀: {et0:.1f} mm/day → ETc: {etc*24*10:.1f} mm/day")
        print(f"+1h: {results[0]:.3f} m³/m³, +2h: {results[1]:.3f} m³/m³")
        return{ "1h": round(results[0],3), "2h": round(results[1],3) }
    except Exception as e:
        print(f"Error: {e}")
        return(f"Error: {e}")
# predict_moisture()