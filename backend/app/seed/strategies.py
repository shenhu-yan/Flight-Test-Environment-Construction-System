import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.env import StrategyRule

logger = logging.getLogger(__name__)


STRATEGIES_DATA = [
    {
        "name": "convergence_slow",
        "condition_config": {
            "convergence_speed": {"operator": "<", "threshold": 0.3},
        },
        "action_config": {
            "adjust": {
                "rewards.reward_items": [
                    {"name": "altitude_maintenance", "coefficient": 2.0},
                    {"name": "waypoint_reached", "coefficient": 10.0},
                ],
            },
            "description": "Increase rewards when convergence is slow",
        },
        "priority": 10,
    },
    {
        "name": "success_low",
        "condition_config": {
            "success_rate": {"operator": "<", "threshold": 0.2},
        },
        "action_config": {
            "adjust": {
                "obstacles.count": 5,
                "obstacles.density": 0.1,
            },
            "description": "Reduce obstacle difficulty when success rate is low",
        },
        "priority": 20,
    },
    {
        "name": "reward_high",
        "condition_config": {
            "episode_reward": {"operator": ">", "threshold": 500},
        },
        "action_config": {
            "adjust": {
                "obstacles.count": 30,
                "obstacles.density": 0.5,
                "weather.wind_speed": 20,
            },
            "description": "Increase difficulty when rewards are too high",
        },
        "priority": 5,
    },
]


async def seed_strategies(db: AsyncSession):
    for strategy_data in STRATEGIES_DATA:
        result = await db.execute(
            select(StrategyRule).where(StrategyRule.name == strategy_data["name"])
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            continue

        rule = StrategyRule(
            name=strategy_data["name"],
            project_id=None,
            condition_config=strategy_data["condition_config"],
            action_config=strategy_data["action_config"],
            priority=strategy_data["priority"],
            enabled=True,
        )
        db.add(rule)
        logger.info(f"Seeded strategy rule: {strategy_data['name']}")

    await db.commit()
    logger.info("Strategy rules seeding completed")
