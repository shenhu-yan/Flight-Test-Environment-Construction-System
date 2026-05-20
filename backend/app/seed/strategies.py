import json
from sqlalchemy import text
from app.core.database import async_session

DEFAULT_STRATEGIES = [
    {
        "id": "00000000-0000-0000-0000-000000000001",
        "name": "收敛过慢时降低难度",
        "condition": {
            "metric": "convergence_speed",
            "operator": "<",
            "threshold": 0.3,
            "duration_steps": 1000
        },
        "action": {
            "type": "param_adjust",
            "adjustments": [
                {"param": "wind_speed", "op": "multiply", "value": 0.7},
                {"param": "obstacle_count", "op": "decrease", "value": 2}
            ]
        },
        "priority": 1,
        "enabled": True
    },
    {
        "id": "00000000-0000-0000-0000-000000000002",
        "name": "成功率过低减少障碍",
        "condition": {
            "metric": "success_rate",
            "operator": "<",
            "threshold": 0.2,
            "duration_steps": 500
        },
        "action": {
            "type": "param_adjust",
            "adjustments": [
                {"param": "obstacle_count", "op": "decrease", "value": 3}
            ]
        },
        "priority": 2,
        "enabled": True
    },
    {
        "id": "00000000-0000-0000-0000-000000000003",
        "name": "奖励过高增加复杂度",
        "condition": {
            "metric": "episode_reward",
            "operator": ">",
            "threshold": 500,
            "duration_steps": 2000
        },
        "action": {
            "type": "param_adjust",
            "adjustments": [
                {"param": "wind_speed", "op": "multiply", "value": 1.3},
                {"param": "obstacle_count", "op": "increase", "value": 2}
            ]
        },
        "priority": 3,
        "enabled": True
    }
]


async def seed_default_strategies():
    async with async_session() as session:
        result = await session.execute(
            text("SELECT id FROM strategies LIMIT 1")
        )
        if result.fetchone() is None:
            for strategy in DEFAULT_STRATEGIES:
                await session.execute(
                    text(
                        """
                        INSERT INTO strategies (id, name, condition, action, priority, enabled, created_at)
                        VALUES (:id, :name, :condition, :action, :priority, :enabled, NOW())
                        """
                    ),
                    {
                        "id": strategy["id"],
                        "name": strategy["name"],
                        "condition": json.dumps(strategy["condition"]),
                        "action": json.dumps(strategy["action"]),
                        "priority": strategy["priority"],
                        "enabled": strategy["enabled"],
                    },
                )
            await session.commit()
