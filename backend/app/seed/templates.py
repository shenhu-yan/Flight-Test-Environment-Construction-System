import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.template import Template

logger = logging.getLogger(__name__)


BASIC_TEMPLATE_CONFIG = {
    "terrain": {
        "type": "plains",
        "elevation_min": 0,
        "elevation_max": 500,
        "resolution": 5.0,
    },
    "weather": {
        "wind_speed": 3,
        "wind_direction": 0,
        "visibility": 15000,
    },
    "flight_dynamics": {
        "aircraft_model": "c172p",
        "mass": 1000,
        "wingspan": 11,
    },
    "rewards": {
        "reward_items": [
            {"name": "altitude_maintenance", "coefficient": 1.0},
            {"name": "waypoint_reached", "coefficient": 5.0},
            {"name": "fuel_efficiency", "coefficient": 0.5},
        ],
        "penalty_items": [
            {"name": "altitude_violation", "coefficient": -2.0},
            {"name": "overspeed", "coefficient": -3.0},
        ],
    },
    "obstacles": {
        "count": 5,
        "types": ["building", "tower"],
        "density": 0.1,
    },
    "waypoints": [
        {"id": "wp1", "position": [1000, 0, 300], "order": 1},
        {"id": "wp2", "position": [2000, 500, 300], "order": 2},
        {"id": "wp3", "position": [3000, 0, 300], "order": 3},
    ],
}

MEDIUM_TEMPLATE_CONFIG = {
    "terrain": {
        "type": "hills",
        "elevation_min": 0,
        "elevation_max": 2000,
        "resolution": 2.0,
    },
    "weather": {
        "wind_speed": 10,
        "wind_direction": 45,
        "visibility": 10000,
    },
    "flight_dynamics": {
        "aircraft_model": "c172p",
        "mass": 1000,
        "wingspan": 11,
    },
    "rewards": {
        "reward_items": [
            {"name": "altitude_maintenance", "coefficient": 1.0},
            {"name": "waypoint_reached", "coefficient": 8.0},
            {"name": "fuel_efficiency", "coefficient": 0.8},
            {"name": "smooth_flight", "coefficient": 0.5},
        ],
        "penalty_items": [
            {"name": "altitude_violation", "coefficient": -5.0},
            {"name": "overspeed", "coefficient": -5.0},
            {"name": "collision_risk", "coefficient": -10.0},
        ],
    },
    "obstacles": {
        "count": 15,
        "types": ["building", "tower", "mountain_peak"],
        "density": 0.3,
    },
    "waypoints": [
        {"id": "wp1", "position": [500, 200, 500], "order": 1},
        {"id": "wp2", "position": [1500, -300, 800], "order": 2},
        {"id": "wp3", "position": [2500, 400, 600], "order": 3},
        {"id": "wp4", "position": [3500, -200, 700], "order": 4},
        {"id": "wp5", "position": [4500, 0, 500], "order": 5},
    ],
}

HARD_TEMPLATE_CONFIG = {
    "terrain": {
        "type": "mountain",
        "elevation_min": 0,
        "elevation_max": 5000,
        "resolution": 1.0,
    },
    "weather": {
        "wind_speed": 25,
        "wind_direction": 180,
        "visibility": 5000,
    },
    "flight_dynamics": {
        "aircraft_model": "c172p",
        "mass": 1000,
        "wingspan": 11,
    },
    "rewards": {
        "reward_items": [
            {"name": "altitude_maintenance", "coefficient": 1.5},
            {"name": "waypoint_reached", "coefficient": 15.0},
            {"name": "fuel_efficiency", "coefficient": 1.0},
            {"name": "smooth_flight", "coefficient": 1.0},
            {"name": "terrain_following", "coefficient": 2.0},
        ],
        "penalty_items": [
            {"name": "altitude_violation", "coefficient": -10.0},
            {"name": "overspeed", "coefficient": -8.0},
            {"name": "collision_risk", "coefficient": -20.0},
            {"name": "terrain_collision", "coefficient": -50.0},
        ],
    },
    "obstacles": {
        "count": 40,
        "types": ["building", "tower", "mountain_peak", "power_line", "antenna"],
        "density": 0.7,
    },
    "waypoints": [
        {"id": "wp1", "position": [300, 500, 1000], "order": 1},
        {"id": "wp2", "position": [1000, -800, 1500], "order": 2},
        {"id": "wp3", "position": [2000, 600, 800], "order": 3},
        {"id": "wp4", "position": [2800, -400, 2000], "order": 4},
        {"id": "wp5", "position": [3500, 200, 1200], "order": 5},
        {"id": "wp6", "position": [4200, -600, 1800], "order": 6},
        {"id": "wp7", "position": [5000, 0, 1000], "order": 7},
    ],
}

TEMPLATES_DATA = [
    {
        "name": "Fixed Wing Basic",
        "aircraft_type": "fixed_wing",
        "difficulty": "basic",
        "config": BASIC_TEMPLATE_CONFIG,
    },
    {
        "name": "Fixed Wing Medium",
        "aircraft_type": "fixed_wing",
        "difficulty": "medium",
        "config": MEDIUM_TEMPLATE_CONFIG,
    },
    {
        "name": "Fixed Wing Hard",
        "aircraft_type": "fixed_wing",
        "difficulty": "hard",
        "config": HARD_TEMPLATE_CONFIG,
    },
]


async def seed_templates(db: AsyncSession):
    for template_data in TEMPLATES_DATA:
        result = await db.execute(
            select(Template).where(
                Template.name == template_data["name"],
                Template.is_builtin == True,
            )
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            continue

        template = Template(
            name=template_data["name"],
            aircraft_type=template_data["aircraft_type"],
            difficulty=template_data["difficulty"],
            config=template_data["config"],
            is_builtin=True,
            created_by=None,
        )
        db.add(template)
        logger.info(f"Seeded template: {template_data['name']}")

    await db.commit()
    logger.info("Templates seeding completed")
