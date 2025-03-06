from datetime import date, datetime
import json
import math
import pandas as pd
import requests
import time

CITY = "Minna" 
API_KEY = "81245a4060df8f46e902ae3ea046f888" 
URL = f"http://api.openweathermap.org/data/2.5/forecast?q={CITY}&appid={API_KEY}&units=metric"

NOW = time.strftime("%H:%M:%S")

try:
    response = requests.get("http://dataservice.accuweather.com/locations/v1/cities/NG/search?apikey=w7W8vo0mxzqx44A3r97dO9TcbIl2WO7h&q=Minna").json()
    # response = json.load(open("test.json"))
    
    print(response)
    # print({
    #             "nxt2": [
    #                             response["days"][0],
    #                             response["days"][1]
    #                         ]
    #         })
    # Remove entries from the JSON response that are not needed
    response["days"][0]["hours"] = list(filter(lambda hour: datetime.strptime(hour["datetime"], "%H:%M:%S") > datetime.strptime(NOW, "%H:%M:%S"), response["days"][0]["hours"]))
    # print(response["days"][0]["hours"])
    
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
    print(pd.DataFrame(forecast_data))
    # for entry in response["list"]:
    #     forecast_data.append({
    #         "DATE": pd.to_datetime(entry["dt_txt"]).strftime("%Y-%m-%d"),
    #         "TEMP": entry["main"]["temp"],
    #         "Tmin": entry["main"]["temp_min"],
    #         "Tmax": entry["main"]["temp_max"],
    #         "Tmean":  (entry["main"]["temp_max"] + entry["main"]["temp_min"]) / 2,
    #         "PRCP": entry.get("rain", {}).get("3h", 0),  # Rainfall in mm (last 3 hours)
    #         "AWND": entry["wind"]["speed"],  # Wind speed in m/s
    #         "RH": entry["main"]["humidity"],  # Relative humidity in %
    #         "ATM": entry["main"]["grnd_level"]  # Relative humidity in %
    #     })
    # # return
    # # print(pd.DataFrame(forecast_data))
    # dataset = pd.DataFrame(forecast_data)
    # print(dataset.head())
    # print(forecast_data)
    # return {"forecast": forecast_list}
except Exception as e:
    print(e)
    # return {"error":"An error was encountered"}
   