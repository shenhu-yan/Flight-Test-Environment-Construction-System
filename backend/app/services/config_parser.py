import json
import xml.etree.ElementTree as ET
from typing import Union
from app.schemas.env_config import EnvConfig


def parse_json_config(config_data: Union[str, dict]) -> EnvConfig:
    if isinstance(config_data, str):
        config_data = json.loads(config_data)
    return EnvConfig(**config_data)


def parse_xml_config(xml_content: str) -> EnvConfig:
    root = ET.fromstring(xml_content)

    config_dict = {}

    terrain_elem = root.find("terrain")
    if terrain_elem is not None:
        config_dict["terrain"] = {
            "type": terrain_elem.findtext("type", "flat"),
            "elevation_min": float(terrain_elem.findtext("elevation_min", "0")),
            "elevation_max": float(terrain_elem.findtext("elevation_max", "100")),
            "resolution": float(terrain_elem.findtext("resolution", "1.0")),
        }

    atmosphere_elem = root.find("atmosphere")
    if atmosphere_elem is not None:
        config_dict["atmosphere"] = {
            "wind_speed": float(atmosphere_elem.findtext("wind_speed", "5.0")),
            "wind_direction": float(atmosphere_elem.findtext("wind_direction", "90")),
            "visibility": float(atmosphere_elem.findtext("visibility", "10000")),
        }

    aircraft_elem = root.find("aircraft")
    if aircraft_elem is not None:
        config_dict["aircraft"] = {
            "model": aircraft_elem.findtext("model", "c172x"),
            "mass": float(aircraft_elem.findtext("mass", "1043")),
            "wingspan": float(aircraft_elem.findtext("wingspan", "11.0")),
        }

    reward_elem = root.find("reward")
    if reward_elem is not None:
        items = []
        for item in reward_elem.findall("item"):
            items.append({
                "name": item.findtext("name", ""),
                "coefficient": float(item.findtext("coefficient", "1.0")),
            })
        penalties = []
        for penalty in reward_elem.findall("penalty"):
            penalties.append({
                "name": penalty.findtext("name", ""),
                "coefficient": float(penalty.findtext("coefficient", "-1.0")),
            })
        config_dict["reward"] = {"items": items, "penalties": penalties}

    obstacles_elem = root.find("obstacles")
    if obstacles_elem is not None:
        types = []
        for t in obstacles_elem.findall("type"):
            types.append(t.text)
        config_dict["obstacles"] = {
            "count": int(obstacles_elem.findtext("count", "0")),
            "types": types,
            "density": float(obstacles_elem.findtext("density", "0.0")),
        }

    waypoints_elem = root.find("waypoints")
    if waypoints_elem is not None:
        waypoints = []
        for wp in waypoints_elem.findall("waypoint"):
            position = wp.findtext("position", "0,0,100").split(",")
            waypoints.append({
                "id": wp.findtext("id", ""),
                "position": [float(p) for p in position],
                "order": int(wp.findtext("order", "1")),
            })
        config_dict["waypoints"] = waypoints

    return EnvConfig(**config_dict)
