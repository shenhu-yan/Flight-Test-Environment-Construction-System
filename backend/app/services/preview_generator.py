import math
import random

from app.schemas.env_config import EnvConfig


def generate_scene_data(config: EnvConfig) -> dict:
    terrain_type = config.terrain.type
    elevation_min = config.terrain.elevation_min
    elevation_max = config.terrain.elevation_max
    resolution = config.terrain.resolution

    grid_size = 50
    grid_step = resolution * 10
    terrain_grid = []
    for i in range(grid_size):
        row = []
        for j in range(grid_size):
            if terrain_type == "mountain":
                base = (elevation_min + elevation_max) / 2
                amplitude = (elevation_max - elevation_min) / 4
                noise = amplitude * math.sin(i * 0.3) * math.cos(j * 0.3)
                elevation = base + noise
            elif terrain_type == "desert":
                base = elevation_min + (elevation_max - elevation_min) * 0.3
                noise = random.uniform(-50, 50)
                elevation = base + noise
            elif terrain_type == "ocean":
                base = elevation_min
                noise = random.uniform(-10, 10)
                elevation = base + noise
            else:
                base = (elevation_min + elevation_max) / 2
                noise = random.uniform(-20, 20)
                elevation = base + noise
            row.append(round(max(elevation_min, min(elevation_max, elevation)), 2))
        terrain_grid.append(row)

    obstacles = []
    obstacle_count = config.obstacles.count
    obstacle_types = config.obstacles.types
    for i in range(obstacle_count):
        obs_type = obstacle_types[i % len(obstacle_types)] if obstacle_types else "generic"
        obstacles.append({
            "id": f"obstacle_{i}",
            "type": obs_type,
            "position": [
                round(random.uniform(-5000, 5000), 2),
                round(random.uniform(-5000, 5000), 2),
                round(random.uniform(elevation_min + 50, elevation_max + 200), 2),
            ],
            "radius": round(random.uniform(10, 100), 2),
        })

    waypoints_data = []
    for wp in config.waypoints:
        waypoints_data.append({
            "id": wp.id,
            "position": [round(p, 2) for p in wp.position],
            "order": wp.order,
        })

    wind = {
        "speed": config.weather.wind_speed,
        "direction": config.weather.wind_direction,
        "gust_speed": round(config.weather.wind_speed * random.uniform(1.0, 1.5), 2),
    }

    runway = {
        "length": 2000,
        "width": 30,
        "heading": config.weather.wind_direction,
        "position": [0, 0, round(elevation_min + 10, 2)],
        "surface": "asphalt",
    }

    return {
        "terrain": {
            "type": terrain_type,
            "grid_size": grid_size,
            "grid_step": grid_step,
            "elevation_min": elevation_min,
            "elevation_max": elevation_max,
            "grid": terrain_grid,
        },
        "obstacles": obstacles,
        "waypoints": waypoints_data,
        "wind": wind,
        "runway": runway,
        "bounds": {
            "x_min": -grid_size * grid_step / 2,
            "x_max": grid_size * grid_step / 2,
            "y_min": -grid_size * grid_step / 2,
            "y_max": grid_size * grid_step / 2,
            "z_min": elevation_min,
            "z_max": elevation_max + 500,
        },
        "metadata": {
            "generated_at": __import__("datetime").datetime.utcnow().isoformat(),
            "config_version": "1.0",
        },
    }
