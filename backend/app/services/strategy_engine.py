"""
Enhanced Strategy Engine with WebSocket integration.
Evaluates incoming training metrics against strategy rules and
triggers automatic environment adjustments with full snapshot tracking.
"""
import logging
import uuid
from typing import Any, Optional
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.env import StrategyRule, Env, EnvSnapshot, AdjustmentHistory, TrainingMetric

logger = logging.getLogger(__name__)


class StrategyEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def load_rules(self, project_id: str | None = None) -> list[StrategyRule]:
        """Load all enabled rules, optionally filtered by project."""
        stmt = select(StrategyRule).where(StrategyRule.enabled == True)
        if project_id:
            stmt = stmt.where(
                (StrategyRule.project_id == project_id) | (StrategyRule.project_id.is_(None))
            )
        stmt = stmt.order_by(StrategyRule.priority.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def evaluate_metrics(self, env_id: str, metrics: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Evaluate incoming metrics against all enabled rules.
        Returns list of adjustment instructions to send.
        """
        env_result = await self.db.execute(select(Env).where(Env.id == env_id))
        env = env_result.scalar_one_or_none()
        if env is None:
            logger.warning(f"Environment {env_id} not found during metric evaluation")
            return []

        rules = await self.load_rules(env.project_id)
        adjustments = []

        for rule in rules:
            condition = rule.condition_config
            if self._check_condition(condition, metrics):
                adjustment = await self._execute_rule(rule, env, metrics)
                if adjustment:
                    adjustments.append(adjustment)

        return adjustments

    def _check_condition(self, condition: dict, metrics: dict[str, Any]) -> bool:
        """
        Check if a rule's condition is met by the current metrics.
        
        Supports two formats:
        1. Simple: { "metric_name": { "operator": ">", "threshold": 0.5 } }
        2. Legacy dict: { "metric_name": value, ... } (equality check)
        """
        conditions_met = True
        for key, condition_value in condition.items():
            metric_value = metrics.get(key)
            if metric_value is None:
                conditions_met = False
                break

            if isinstance(condition_value, dict):
                op = condition_value.get("operator", ">")
                threshold = condition_value.get("threshold", 0.0)
                try:
                    metric_value = float(metric_value)
                    threshold = float(threshold)
                except (ValueError, TypeError):
                    conditions_met = False
                    break

                if op == ">" and metric_value <= threshold:
                    conditions_met = False
                elif op == "<" and metric_value >= threshold:
                    conditions_met = False
                elif op == ">=" and metric_value < threshold:
                    conditions_met = False
                elif op == "<=" and metric_value > threshold:
                    conditions_met = False
                elif op == "==" and metric_value != threshold:
                    conditions_met = False
                elif op == "!=" and metric_value == threshold:
                    conditions_met = False
            elif isinstance(condition_value, (int, float)):
                try:
                    if float(metric_value) != float(condition_value):
                        conditions_met = False
                except (ValueError, TypeError):
                    conditions_met = False

            if not conditions_met:
                break

        return conditions_met

    async def _execute_rule(
        self, rule: StrategyRule, env: Env, metrics: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        """Execute a strategy rule: save snapshots, apply adjustments, record history."""
        action = rule.action_config
        action_type = action.get("type", "")

        if action_type == "param_adjust":
            return await self._apply_param_adjust(rule, env, action, metrics)
        elif action_type == "notify":
            return await self._apply_notify(rule, env, action, metrics)
        else:
            logger.debug(f"Skipping rule {rule.id} with unknown action type: {action_type}")
            return None

    async def _apply_param_adjust(
        self, rule: StrategyRule, env: Env, action: dict, metrics: dict
    ) -> Optional[dict[str, Any]]:
        """Apply parameter adjustments based on rule action config."""
        old_config = dict(env.config) if env.config else {}

        # Save before snapshot
        snapshot_before = EnvSnapshot(
            id=str(uuid.uuid4()),
            env_id=env.id,
            config=old_config,
            trigger_type="auto_adjust",
            reason=f"Triggered by rule: {rule.name} (id={rule.id})",
        )
        self.db.add(snapshot_before)
        await self.db.flush()

        # Apply adjustments to config
        new_config = dict(old_config)
        for adj in action.get("adjustments", []):
            param = adj.get("param", "")
            op = adj.get("op", "set")
            value = adj.get("value", 0)

            # Support nested params like "weather.wind_speed"
            parts = param.split(".")
            target = new_config
            for part in parts[:-1]:
                if part in target and isinstance(target[part], dict):
                    target = target[part]
                else:
                    break
            leaf_key = parts[-1]

            if leaf_key in target:
                current_val = target[leaf_key]
                try:
                    current_val = float(current_val)
                    value = float(value)
                    if op == "multiply":
                        target[leaf_key] = round(current_val * value, 6)
                    elif op == "add":
                        target[leaf_key] = round(current_val + value, 6)
                    elif op == "decrease":
                        target[leaf_key] = round(max(0, current_val - value), 6)
                    elif op == "set":
                        target[leaf_key] = value
                    else:
                        logger.warning(f"Unknown operation: {op}")
                except (ValueError, TypeError):
                    if op == "set":
                        target[leaf_key] = value
                    else:
                        logger.warning(f"Cannot apply '{op}' to non-numeric param: {param}")
            else:
                if op == "set":
                    target[leaf_key] = value
                else:
                    logger.debug(f"Param {param} not found in config, skipping {op}")

        env.config = new_config

        # Save after snapshot
        snapshot_after = EnvSnapshot(
            id=str(uuid.uuid4()),
            env_id=env.id,
            config=new_config,
            trigger_type="auto_adjust",
            reason=f"After rule: {rule.name} (id={rule.id})",
        )
        self.db.add(snapshot_after)
        await self.db.flush()

        # Compute metric changes
        metric_change = {}
        for key in set(list(old_config.keys()) + list(new_config.keys())):
            if old_config.get(key) != new_config.get(key):
                metric_change[key] = {
                    "before": old_config.get(key),
                    "after": new_config.get(key),
                }

        # Record adjustment history
        history = AdjustmentHistory(
            id=str(uuid.uuid4()),
            env_id=env.id,
            snapshot_before=snapshot_before.id,
            snapshot_after=snapshot_after.id,
            trigger_type="auto",
            trigger_rule=rule.id,
            metric_change=metric_change,
        )
        self.db.add(history)
        await self.db.commit()

        logger.info(
            f"Auto-adjustment applied: env={env.id}, rule={rule.name}, "
            f"changes={len(metric_change)} params"
        )

        # Build adjustment instruction
        instruction = {
            "env_id": env.id,
            "config": new_config,
            "reason": f"Auto-adjust: {rule.name}",
            "rule_id": rule.id,
            "rule_name": rule.name,
            "metric_change": metric_change,
            "trigger_metrics": metrics,
            "snapshot_before_id": snapshot_before.id,
            "snapshot_after_id": snapshot_after.id,
        }

        # Push via WebSocket if available
        try:
            from app.api.ws import manager
            await manager.send_adjustment(env.project_id, env.id, instruction)
            await manager.broadcast_notification(env.project_id, {
                "level": "warning",
                "title": "Auto-Adjustment Applied",
                "message": f"Rule '{rule.name}' triggered parameter changes for env {env.name}",
                "data": {
                    "env_id": env.id,
                    "rule_id": rule.id,
                    "changes": metric_change,
                },
            })
        except Exception as e:
            logger.warning(f"WebSocket push failed during adjustment: {e}")

        return instruction

    async def _apply_notify(
        self, rule: StrategyRule, env: Env, action: dict, metrics: dict
    ) -> Optional[dict[str, Any]]:
        """Send a notification without modifying config."""
        message = action.get("message", f"Rule {rule.name} triggered")
        level = action.get("level", "info")

        instruction = {
            "env_id": env.id,
            "type": "notification",
            "level": level,
            "message": message,
            "rule_id": rule.id,
            "rule_name": rule.name,
            "trigger_metrics": metrics,
        }

        # Record as adjustment history (no config change)
        history = AdjustmentHistory(
            id=str(uuid.uuid4()),
            env_id=env.id,
            trigger_type="notification",
            trigger_rule=rule.id,
        )
        self.db.add(history)
        await self.db.commit()

        # Push via WebSocket
        try:
            from app.api.ws import manager
            await manager.broadcast_notification(env.project_id, {
                "level": level,
                "title": f"Strategy Rule: {rule.name}",
                "message": message,
                "data": {
                    "env_id": env.id,
                    "rule_id": rule.id,
                },
            })
        except Exception as e:
            logger.warning(f"WebSocket push failed during notification: {e}")

        return instruction

    async def apply_manual_adjustment(
        self, env_id: str, new_config: dict, operator_id: str, reason: str = ""
    ) -> dict[str, Any]:
        """Apply a manual config adjustment (from user)."""
        env_result = await self.db.execute(select(Env).where(Env.id == env_id))
        env = env_result.scalar_one_or_none()
        if env is None:
            raise ValueError(f"Environment {env_id} not found")

        old_config = dict(env.config) if env.config else {}

        snapshot_before = EnvSnapshot(
            id=str(uuid.uuid4()),
            env_id=env_id,
            config=old_config,
            trigger_type="manual_adjust",
            operator=operator_id,
            reason=f"Manual adjustment: {reason}",
        )
        self.db.add(snapshot_before)
        await self.db.flush()

        env.config = new_config

        snapshot_after = EnvSnapshot(
            id=str(uuid.uuid4()),
            env_id=env_id,
            config=new_config,
            trigger_type="manual_adjust",
            operator=operator_id,
            reason=f"After manual adjustment: {reason}",
        )
        self.db.add(snapshot_after)
        await self.db.flush()

        history = AdjustmentHistory(
            id=str(uuid.uuid4()),
            env_id=env_id,
            snapshot_before=snapshot_before.id,
            snapshot_after=snapshot_after.id,
            trigger_type="manual",
            operator=operator_id,
        )
        self.db.add(history)
        await self.db.commit()

        instruction = {
            "env_id": env_id,
            "config": new_config,
            "reason": reason,
            "operator_id": operator_id,
            "snapshot_before_id": snapshot_before.id,
            "snapshot_after_id": snapshot_after.id,
        }

        # Push via WebSocket
        try:
            from app.api.ws import manager
            await manager.send_adjustment(env.project_id, env_id, instruction)
        except Exception as e:
            logger.warning(f"WebSocket push failed during manual adjustment: {e}")

        return instruction

    async def get_latest_metrics(self, env_id: str, limit: int = 10) -> list[dict[str, Any]]:
        """Get the latest training metrics for an environment."""
        stmt = (
            select(TrainingMetric)
            .where(TrainingMetric.env_id == env_id)
            .order_by(TrainingMetric.reported_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        metrics = result.scalars().all()
        return [
            {
                "episode_reward": m.episode_reward,
                "success_rate": m.success_rate,
                "convergence_speed": m.convergence_speed,
                "step": m.step,
                "reported_at": m.reported_at.isoformat() if m.reported_at else None,
            }
            for m in metrics
        ]

    async def get_adjustment_history(self, env_id: str, limit: int = 20) -> list[dict[str, Any]]:
        """Get adjustment history for an environment."""
        stmt = (
            select(AdjustmentHistory)
            .where(AdjustmentHistory.env_id == env_id)
            .order_by(AdjustmentHistory.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        records = result.scalars().all()
        return [
            {
                "id": h.id,
                "env_id": h.env_id,
                "trigger_type": h.trigger_type,
                "trigger_rule": h.trigger_rule,
                "operator": h.operator,
                "metric_change": h.metric_change,
                "created_at": h.created_at.isoformat() if h.created_at else None,
            }
            for h in records
        ]
