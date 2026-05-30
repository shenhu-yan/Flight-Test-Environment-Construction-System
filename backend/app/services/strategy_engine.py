import json
import uuid
from sqlalchemy import text
from app.core.database import async_session
from app.services.ws_manager import send_adjustment_instruction


class StrategyEngine:
    def __init__(self):
        self.metric_history: dict[str, list] = {}

    async def process_metric(self, project_id: str, env_id: str, metrics: dict):
        key = f"{project_id}:{env_id}"
        if key not in self.metric_history:
            self.metric_history[key] = []

        self.metric_history[key].append(metrics)
        if len(self.metric_history[key]) > 1000:
            self.metric_history[key] = self.metric_history[key][-1000:]

        async with async_session() as session:
            result = await session.execute(
                text(
                    """
                    SELECT id, name, condition, action, priority
                    FROM strategies
                    WHERE enabled = true AND (project_id = :project_id OR project_id IS NULL)
                    ORDER BY priority ASC
                    """
                ),
                {"project_id": project_id}
            )
            strategies = result.fetchall()

        for strategy in strategies:
            strategy_id, name, condition, action, priority = strategy
            condition_data = json.loads(condition) if isinstance(condition, str) else condition
            action_data = json.loads(action) if isinstance(action, str) else action

            if self._check_condition(condition_data, key):
                await self._execute_action(project_id, env_id, strategy_id, name, action_data)
                break

    def _check_condition(self, condition: dict, key: str) -> bool:
        metric_name = condition.get("metric")
        operator = condition.get("operator")
        threshold = condition.get("threshold")
        duration_steps = condition.get("duration_steps", 100)

        history = self.metric_history.get(key, [])
        if len(history) < duration_steps:
            return False

        recent_metrics = history[-duration_steps:]
        values = [m.get(metric_name) for m in recent_metrics if m.get(metric_name) is not None]

        if not values:
            return False

        avg_value = sum(values) / len(values)

        if operator == "<":
            return avg_value < threshold
        elif operator == ">":
            return avg_value > threshold
        elif operator == "<=":
            return avg_value <= threshold
        elif operator == ">=":
            return avg_value >= threshold
        elif operator == "==":
            return abs(avg_value - threshold) < 0.01

        return False

    async def _execute_action(self, project_id: str, env_id: str, strategy_id: str, strategy_name: str, action: dict):
        adjustments = action.get("adjustments", [])

        async with async_session() as session:
            result = await session.execute(
                text("SELECT config FROM envs WHERE id = :id"),
                {"id": env_id}
            )
            env = result.fetchone()
            if not env:
                return

            config = json.loads(env[0]) if isinstance(env[0], str) else env[0]

            admin_id = "00000000-0000-0000-0000-000000000001"

            snapshot_result = await session.execute(
                text(
                    """
                    INSERT INTO env_snapshots (id, env_id, config, trigger_type, operator, reason, created_at)
                    VALUES (:id, :env_id, :config, 'auto_adjust', :operator, :reason, NOW())
                    RETURNING id
                    """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "env_id": env_id,
                    "config": json.dumps(config),
                    "operator": admin_id,
                    "reason": f"策略触发: {strategy_name}",
                }
            )
            snapshot_before = snapshot_result.fetchone()[0]

            for adj in adjustments:
                param = adj.get("param")
                op = adj.get("op")
                value = adj.get("value")

                # 气象参数
                if param in config.get("atmosphere", {}):
                    if op == "multiply":
                        config["atmosphere"][param] = round(config["atmosphere"][param] * value, 2)
                    elif op == "increase":
                        config["atmosphere"][param] = round(config["atmosphere"][param] + value, 2)
                    elif op == "decrease":
                        config["atmosphere"][param] = round(config["atmosphere"][param] - value, 2)
                    elif op == "set":
                        config["atmosphere"][param] = value

                # 障碍物数量
                elif param == "obstacle_count":
                    if op == "increase":
                        config["obstacles"]["count"] = max(0, config["obstacles"]["count"] + int(value))
                    elif op == "decrease":
                        config["obstacles"]["count"] = max(0, config["obstacles"]["count"] - int(value))

                # 着陆区参数（带范围限制）
                elif param.startswith("landing."):
                    key = param.split(".")[1]
                    landing = config.setdefault("landing", {"type": "runway", "width": 100, "length": 200})
                    if op == "multiply":
                        landing[key] = round(max(20, min(500, landing.get(key, 100) * value)), 2)
                    elif op == "increase":
                        landing[key] = round(max(20, min(500, landing.get(key, 100) + value)), 2)
                    elif op == "decrease":
                        landing[key] = max(20, round(landing.get(key, 100) - value, 2))
                    elif op == "set":
                        landing[key] = max(20, min(500, value))

                # 阵风参数
                elif param.startswith("gusts."):
                    key = param.split(".")[1]
                    gusts = config.setdefault("gusts", {"enabled": False, "strength": 5, "frequency": 0.05})
                    if op == "set":
                        gusts[key] = value
                    elif op == "multiply":
                        gusts[key] = round(gusts.get(key, 5) * value, 2)
                    elif op == "increase":
                        gusts[key] = round(gusts.get(key, 5) + value, 2)
                    elif op == "decrease":
                        gusts[key] = max(0, round(gusts.get(key, 5) - value, 2))

                # 移动障碍物参数
                elif param.startswith("moving_obstacles."):
                    key = param.split(".")[1]
                    moving = config.setdefault("moving_obstacles", {"count": 0, "speed": 5})
                    if op == "set":
                        moving[key] = value
                    elif op == "increase":
                        moving[key] = moving.get(key, 0) + int(value)
                    elif op == "decrease":
                        moving[key] = max(0, moving.get(key, 0) - int(value))
                    elif op == "multiply":
                        moving[key] = round(moving.get(key, 5) * value, 2)

                # 奖励参数
                elif param.startswith("reward."):
                    key = param.split(".")[1]
                    reward = config.setdefault("reward", {})
                    if op == "multiply":
                        reward[key] = round(reward.get(key, 0) * value, 4)
                    elif op == "set":
                        reward[key] = value

            snapshot_after_result = await session.execute(
                text(
                    """
                    INSERT INTO env_snapshots (id, env_id, config, trigger_type, operator, reason, created_at)
                    VALUES (:id, :env_id, :config, 'auto_adjust', :operator, :reason, NOW())
                    RETURNING id
                    """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "env_id": env_id,
                    "config": json.dumps(config),
                    "operator": admin_id,
                    "reason": f"策略调整后: {strategy_name}",
                }
            )
            snapshot_after = snapshot_after_result.fetchone()[0]

            await session.execute(
                text(
                    """
                    INSERT INTO adjustment_history (id, env_id, snapshot_before, snapshot_after, trigger_type, trigger_rule, operator, created_at)
                    VALUES (:id, :env_id, :snapshot_before, :snapshot_after, 'auto', :trigger_rule, :operator, NOW())
                    """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "env_id": env_id,
                    "snapshot_before": snapshot_before,
                    "snapshot_after": snapshot_after,
                    "trigger_rule": strategy_id,
                    "operator": admin_id,
                }
            )

            await session.execute(
                text("UPDATE envs SET config = :config, updated_at = NOW() WHERE id = :id"),
                {"id": env_id, "config": json.dumps(config)}
            )

            await session.commit()

        await send_adjustment_instruction(project_id, env_id, {
            "type": "adjust_instruction",
            "strategy": strategy_name,
            "adjustments": adjustments,
            "new_config": config,
        })


strategy_engine = StrategyEngine()
