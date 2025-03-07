import json
import LocalHost.config as config
from LocalHost.websocket_handler import push_2_mc
crop_data = json.load(open("./database/crop_threshold.json"))

crop_threshold = crop_data["moisture"]
min_threshold = 20
max_threshold = 60

async def get_crops():
    return {"crops":crop_data["list"]}

async def set_croptype(crop_type):
    if crop_type in crop_data["list"]:
        
        min_threshold, max_threshold = crop_data["moisture"][crop_type]
        push_2_mc(min_threshold, max_threshold, config.Rain)
        return {"moisture": crop_data["moisture"][crop_type], "temp_range": crop_data["optimal_temp"][crop_type], "humidity_range": crop_data["optimal_humidity"][crop_type]}
    return {"error": "Crop type not found"}
