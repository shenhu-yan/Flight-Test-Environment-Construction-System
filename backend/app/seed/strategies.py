import json
from sqlalchemy import text
from app.core.database import async_session

DEFAULT_STRATEGIES = [
    # ── 阶段1：环境太难，算法学不会 → 大幅降低难度 ──
    {
        "id": "00000000-0000-0000-0000-000000000001",
        "name": "成功率极低：降低风速、扩大着陆区",
        "condition": {
            "metric": "success_rate",
            "operator": "<",
            "threshold": 0.1,
            "duration_steps": 30
        },
        "action": {
            "type": "param_adjust",
            "adjustments": [
                {"param": "wind_speed", "op": "multiply", "value": 0.5},
                {"param": "landing.width", "op": "multiply", "value": 2.0},
                {"param": "obstacle_count", "op": "decrease", "value": 3},
                {"param": "gusts.enabled", "op": "set", "value": False},
                {"param": "moving_obstacles.count", "op": "set", "value": 0}
            ]
        },
        "priority": 1,
        "enabled": True
    },
    # ── 阶段2：收敛过慢 → 降低环境复杂度 ──
    {
        "id": "00000000-0000-0000-0000-000000000002",
        "name": "收敛过慢：减少干扰因素",
        "condition": {
            "metric": "convergence_speed",
            "operator": "<",
            "threshold": 0.4,
            "duration_steps": 30
        },
        "action": {
            "type": "param_adjust",
            "adjustments": [
                {"param": "wind_speed", "op": "multiply", "value": 0.7},
                {"param": "obstacle_count", "op": "decrease", "value": 2}
            ]
        },
        "priority": 2,
        "enabled": True
    },
    # ── 阶段3：学得不错 → 增加侧风 ──
    {
        "id": "00000000-0000-0000-0000-000000000003",
        "name": "成功率>40%：增加侧风挑战",
        "condition": {
            "metric": "success_rate",
            "operator": ">",
            "threshold": 0.4,
            "duration_steps": 30
        },
        "action": {
            "type": "param_adjust",
            "adjustments": [
                {"param": "wind_speed", "op": "increase", "value": 5.0},
                {"param": "wind_direction", "op": "set", "value": 90}
            ]
        },
        "priority": 3,
        "enabled": True
    },
    # ── 阶段4：太简单了 → 加入阵风、缩小着陆区、加移动障碍物 ──
    {
        "id": "00000000-0000-0000-0000-000000000004",
        "name": "成功率>70%：增加环境复杂度",
        "condition": {
            "metric": "success_rate",
            "operator": ">",
            "threshold": 0.7,
            "duration_steps": 30
        },
        "action": {
            "type": "param_adjust",
            "adjustments": [
                {"param": "gusts.enabled", "op": "set", "value": True},
                {"param": "gusts.strength", "op": "set", "value": 8.0},
                {"param": "landing.width", "op": "multiply", "value": 0.7},
                {"param": "moving_obstacles.count", "op": "set", "value": 3},
                {"param": "moving_obstacles.speed", "op": "set", "value": 5.0}
            ]
        },
        "priority": 4,
        "enabled": True
    },
    # ── 阶段5：难度加太猛 → 回调 ──
    {
        "id": "00000000-0000-0000-0000-000000000005",
        "name": "成功率<30%（曾>60%）：回调难度",
        "condition": {
            "metric": "success_rate",
            "operator": "<",
            "threshold": 0.3,
            "duration_steps": 30
        },
        "action": {
            "type": "param_adjust",
            "adjustments": [
                {"param": "gusts.strength", "op": "multiply", "value": 0.7},
                {"param": "landing.width", "op": "multiply", "value": 1.3},
                {"param": "moving_obstacles.speed", "op": "multiply", "value": 0.7}
            ]
        },
        "priority": 5,
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
