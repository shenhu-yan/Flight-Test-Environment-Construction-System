import json
import xml.etree.ElementTree as ET

from app.schemas.env_config import (
    EnvConfig,
    TerrainConfig,
    WeatherConfig,
    FlightDynamicsConfig,
    RewardConfig,
    RewardItem,
    ObstacleConfig,
    Waypoint,
)


def parse_json_config(file_content: str) -> EnvConfig:
    try:
        data = json.loads(file_content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")

    terrain = TerrainConfig(**data.get("terrain", {}))
    weather = WeatherConfig(**data.get("weather", {}))
    flight_dynamics = FlightDynamicsConfig(**data.get("flight_dynamics", {}))

    rewards_data = data.get("rewards", {})
    reward_items = [RewardItem(**item) for item in rewards_data.get("reward_items", [])]
    penalty_items = [RewardItem(**item) for item in rewards_data.get("penalty_items", [])]
    rewards = RewardConfig(reward_items=reward_items, penalty_items=penalty_items)

    obstacles = ObstacleConfig(**data.get("obstacles", {}))
    waypoints = [Waypoint(**wp) for wp in data.get("waypoints", [])]

    return EnvConfig(
        terrain=terrain,
        weather=weather,
        flight_dynamics=flight_dynamics,
        rewards=rewards,
        obstacles=obstacles,
        waypoints=waypoints,
    )


def parse_xml_config(file_content: str) -> EnvConfig:
    try:
        root = ET.fromstring(file_content)
    except ET.ParseError as e:
        raise ValueError(f"Invalid XML: {e}")

    terrain_elem = root.find("terrain")
    terrain_data = {}
    if terrain_elem is not None:
        terrain_data = {
            "type": terrain_elem.get("type", "mountain"),
            "elevation_min": float(terrain_elem.get("elevation_min", "0")),
            "elevation_max": float(terrain_elem.get("elevation_max", "3000")),
            "resolution": float(terrain_elem.get("resolution", "1.0")),
        }
    terrain = TerrainConfig(**terrain_data)

    weather_elem = root.find("weather")
    weather_data = {}
    if weather_elem is not None:
        weather_data = {
            "wind_speed": float(weather_elem.get("wind_speed", "5")),
            "wind_direction": float(weather_elem.get("wind_direction", "0")),
            "visibility": float(weather_elem.get("visibility", "10000")),
        }
    weather = WeatherConfig(**weather_data)

    dynamics_elem = root.find("flight_dynamics")
    dynamics_data = {}
    if dynamics_elem is not None:
        dynamics_data = {
            "aircraft_model": dynamics_elem.get("aircraft_model", "c172p"),
            "mass": float(dynamics_elem.get("mass", "1000")),
            "wingspan": float(dynamics_elem.get("wingspan", "11")),
        }
    flight_dynamics = FlightDynamicsConfig(**dynamics_data)

    rewards_elem = root.find("rewards")
    reward_items = []
    penalty_items = []
    if rewards_elem is not None:
        for ri in rewards_elem.findall("reward_item"):
            reward_items.append(RewardItem(
                name=ri.get("name", ""),
                coefficient=float(ri.get("coefficient", "1.0")),
            ))
        for pi in rewards_elem.findall("penalty_item"):
            penalty_items.append(RewardItem(
                name=pi.get("name", ""),
                coefficient=float(pi.get("coefficient", "1.0")),
            ))
    rewards = RewardConfig(reward_items=reward_items, penalty_items=penalty_items)

    obstacles_elem = root.find("obstacles")
    obstacles_data = {}
    if obstacles_elem is not None:
        types_str = obstacles_elem.get("types", "")
        obstacles_data = {
            "count": int(obstacles_elem.get("count", "0")),
            "types": [t.strip() for t in types_str.split(",") if t.strip()],
            "density": float(obstacles_elem.get("density", "0")),
        }
    obstacles = ObstacleConfig(**obstacles_data)

    waypoints = []
    waypoints_elem = root.find("waypoints")
    if waypoints_elem is not None:
        for wp_elem in waypoints_elem.findall("waypoint"):
            pos_str = wp_elem.get("position", "0,0,0")
            pos_parts = [float(p.strip()) for p in pos_str.split(",")]
            waypoints.append(Waypoint(
                id=wp_elem.get("id", ""),
                position=pos_parts,
                order=int(wp_elem.get("order", "0")),
            ))

    return EnvConfig(
        terrain=terrain,
        weather=weather,
        flight_dynamics=flight_dynamics,
        rewards=rewards,
        obstacles=obstacles,
        waypoints=waypoints,
    )
