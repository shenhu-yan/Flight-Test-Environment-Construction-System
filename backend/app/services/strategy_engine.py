import json
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
            return avg_value == threshold

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

            snapshot_result = await session.execute(
                text(
                    """
                    INSERT INTO env_snapshots (id, env_id, config, trigger_type, reason, created_at)
                    VALUES (:id, :env_id, :config, 'auto_adjust', :reason, NOW())
                    RETURNING id
                    """
                ),
                {
                    "id": f"snapshot_{env_id}_{strategy_id}",
                    "env_id": env_id,
                    "config": json.dumps(config),
                    "reason": f"策略触发: {strategy_name}",
                }
            )
            snapshot_before = snapshot_result.fetchone()[0]

            for adj in adjustments:
                param = adj.get("param")
                op = adj.get("op")
                value = adj.get("value")

                if param in config.get("atmosphere", {}):
                    if op == "multiply":
                        config["atmosphere"][param] = round(config["atmosphere"][param] * value, 2)
                    elif op == "increase":
                        config["atmosphere"][param] = round(config["atmosphere"][param] + value, 2)
                    elif op == "decrease":
                        config["atmosphere"][param] = round(config["atmosphere"][param] - value, 2)
                elif param == "obstacle_count":
                    if op == "increase":
                        config["obstacles"]["count"] = max(0, config["obstacles"]["count"] + int(value))
                    elif op == "decrease":
                        config["obstacles"]["count"] = max(0, config["obstacles"]["count"] - int(value))

            snapshot_after_result = await session.execute(
                text(
                    """
                    INSERT INTO env_snapshots (id, env_id, config, trigger_type, reason, created_at)
                    VALUES (:id, :env_id, :config, 'auto_adjust', :reason, NOW())
                    RETURNING id
                    """
                ),
                {
                    "id": f"snapshot_{env_id}_{strategy_id}_after",
                    "env_id": env_id,
                    "config": json.dumps(config),
                    "reason": f"策略调整后: {strategy_name}",
                }
            )
            snapshot_after = snapshot_after_result.fetchone()[0]

            await session.execute(
                text(
                    """
                    INSERT INTO adjustment_history (id, env_id, snapshot_before, snapshot_after, trigger_type, trigger_rule, created_at)
                    VALUES (:id, :env_id, :snapshot_before, :snapshot_after, 'auto', :trigger_rule, NOW())
                    """
                ),
                {
                    "id": f"adj_{env_id}_{strategy_id}",
                    "env_id": env_id,
                    "snapshot_before": snapshot_before,
                    "snapshot_after": snapshot_after,
                    "trigger_rule": strategy_id,
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
