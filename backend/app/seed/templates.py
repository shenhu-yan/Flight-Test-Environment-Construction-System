import json
from datetime import datetime
from sqlalchemy import text
from app.core.database import async_session

BUILTIN_TEMPLATES = [
    {
        "id": "00000000-0000-0000-0000-000000000001",
        "name": "固定翼基础难度",
        "aircraft_type": "fixed_wing",
        "difficulty": "basic",
        "config": {
            "terrain": {"type": "flat", "elevation_min": 0, "elevation_max": 100, "resolution": 1.0},
            "atmosphere": {"wind_speed": 5.0, "wind_direction": 90, "visibility": 10000},
            "aircraft": {"model": "c172x", "mass": 1043, "wingspan": 11.0},
            "reward": {"items": [{"name": "altitude_reward", "coefficient": 1.0}], "penalties": []},
            "obstacles": {"count": 0, "types": [], "density": 0.0},
            "waypoints": []
        }
    },
    {
        "id": "00000000-0000-0000-0000-000000000002",
        "name": "固定翼中等难度",
        "aircraft_type": "fixed_wing",
        "difficulty": "medium",
        "config": {
            "terrain": {"type": "hilly", "elevation_min": 0, "elevation_max": 500, "resolution": 1.0},
            "atmosphere": {"wind_speed": 10.0, "wind_direction": 180, "visibility": 8000},
            "aircraft": {"model": "c172x", "mass": 1043, "wingspan": 11.0},
            "reward": {"items": [{"name": "altitude_reward", "coefficient": 1.0}, {"name": "speed_reward", "coefficient": 0.5}], "penalties": [{"name": "collision_penalty", "coefficient": -10.0}]},
            "obstacles": {"count": 5, "types": ["building"], "density": 0.1},
            "waypoints": [{"id": "wp1", "position": [0, 0, 100], "order": 1}, {"id": "wp2", "position": [500, 0, 200], "order": 2}]
        }
    },
    {
        "id": "00000000-0000-0000-0000-000000000003",
        "name": "固定翼高难度",
        "aircraft_type": "fixed_wing",
        "difficulty": "hard",
        "config": {
            "terrain": {"type": "mountainous", "elevation_min": 0, "elevation_max": 1000, "resolution": 0.5},
            "atmosphere": {"wind_speed": 20.0, "wind_direction": 270, "visibility": 5000},
            "aircraft": {"model": "f16", "mass": 9072, "wingspan": 10.0},
            "reward": {"items": [{"name": "altitude_reward", "coefficient": 1.0}, {"name": "speed_reward", "coefficient": 1.0}, {"name": "fuel_efficiency", "coefficient": 0.3}], "penalties": [{"name": "collision_penalty", "coefficient": -50.0}, {"name": "stall_penalty", "coefficient": -20.0}]},
            "obstacles": {"count": 15, "types": ["building", "mountain"], "density": 0.3},
            "waypoints": [{"id": "wp1", "position": [0, 0, 100], "order": 1}, {"id": "wp2", "position": [300, 200, 300], "order": 2}, {"id": "wp3", "position": [600, -100, 500], "order": 3}]
        }
    }
]


async def seed_builtin_templates():
    async with async_session() as session:
        result = await session.execute(
            text("SELECT id FROM templates WHERE is_builtin = true LIMIT 1")
        )
        if result.fetchone() is None:
            now = datetime.utcnow()
            for template in BUILTIN_TEMPLATES:
                await session.execute(
                    text(
                        """
                        INSERT INTO templates (id, name, aircraft_type, difficulty, config, is_builtin, created_at)
                        VALUES (:id, :name, :aircraft_type, :difficulty, :config, true, :now)
                        """
                    ),
                    {
                        "id": template["id"],
                        "name": template["name"],
                        "aircraft_type": template["aircraft_type"],
                        "difficulty": template["difficulty"],
                        "config": json.dumps(template["config"]),
                        "now": now,
                    },
                )
            await session.commit()
