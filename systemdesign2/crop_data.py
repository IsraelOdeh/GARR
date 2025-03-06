import json

from websocket_handler import push_2_mc
import weather 
crop_data = json.load(open("crop_threshold.json"))

crop_threshold = crop_data["moisture"]
min_threshold = 20
max_threshold = 60

def get_crops():
    return {"crops":crop_data["list"]}

def set_croptype(crop_type):
    if crop_type in crop_data["list"]:
        print("finding crop")
        min_threshold, max_threshold = crop_data["list"][crop_type]
        push_2_mc(min_threshold, max_threshold, weather.Rain)
        return {"message": f"Crop type set to {crop_type}"}
    return {"error": "Crop type not found"}
