"""
Enhanced optimization tasks with WebSocket progress reporting.
"""
import asyncio
import logging
import random
import uuid
from datetime import datetime

from sqlalchemy import select

from app.celery_app import celery_app
from app.database import async_session_factory
from app.models.env import Env, EnvEvaluation
from app.models.optimization import OptimizationTask, OptimizationReport

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper to run async code from Celery sync context
# ---------------------------------------------------------------------------
def _run_async(coro):
    """Run an async coroutine from a sync Celery task."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Already in an event loop (e.g. from some integrations)
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, coro).result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


# ---------------------------------------------------------------------------
# WebSocket broadcast helper (safe for sync context)
# ---------------------------------------------------------------------------
def _broadcast_progress(project_id: str, env_id: str, progress_data: dict):
    """Synchronously attempt to broadcast progress via WebSocket."""
    try:
        import redis.asyncio as aioredis
        from app.config import settings

        async def _push():
            try:
                client = aioredis.from_url(settings.REDIS_URL)
                await client.publish(
                    f"optimization_progress:{project_id}",
                    str(progress_data),
                )
                await client.aclose()
            except Exception as e:
                logger.debug(f"Redis broadcast failed: {e}")

        _run_async(_push())
    except Exception:
        pass


def _broadcast_eval_result(project_id: str, env_id: str, eval_data: dict):
    """Synchronously attempt to broadcast evaluation result via WebSocket."""
    try:
        async def _push():
            from app.api.ws import push_eval_result_to_frontend
            try:
                await push_eval_result_to_frontend(project_id, env_id, eval_data)
            except Exception as e:
                logger.debug(f"WebSocket eval broadcast failed: {e}")

        _run_async(_push())
    except Exception:
        pass


def _broadcast_notification(project_id: str, notification: dict):
    """Synchronously attempt to broadcast a notification via WebSocket."""
    try:
        async def _push():
            from app.api.ws import push_notification_to_frontend
            try:
                await push_notification_to_frontend(project_id, notification)
            except Exception as e:
                logger.debug(f"WebSocket notification broadcast failed: {e}")

        _run_async(_push())
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Task: Evaluate a single environment
# ---------------------------------------------------------------------------
@celery_app.task(bind=True, name="optimization_tasks.evaluate_env_task")
def evaluate_env_task(self, env_id: str):
    asyncio.run(_evaluate_env_async(self, env_id))


async def _evaluate_env_async(task, env_id: str):
    async with async_session_factory() as db:
        try:
            result = await db.execute(select(Env).where(Env.id == env_id))
            env = result.scalar_one_or_none()
            if env is None:
                return {"error": f"Environment {env_id} not found"}

            config_data = env.config or {}
            diversity_score = _compute_diversity_score(config_data)
            challenge_score = _compute_challenge_score(config_data)
            realism_score = _compute_realism_score(config_data)
            effectiveness_score = _compute_effectiveness_score(config_data)

            weights = {
                "diversity": 0.25,
                "challenge": 0.25,
                "reality": 0.25,
                "effectiveness": 0.25,
            }
            total_score = (
                diversity_score * weights["diversity"]
                + challenge_score * weights["challenge"]
                + realism_score * weights["reality"]
                + effectiveness_score * weights["effectiveness"]
            )

            suggestions = []
            if diversity_score < 0.5:
                suggestions.append("Consider adding more diverse terrain features")
            if challenge_score < 0.5:
                suggestions.append("Consider increasing obstacle count or difficulty")
            if realism_score < 0.5:
                suggestions.append("Consider adjusting weather parameters for realism")
            if effectiveness_score < 0.5:
                suggestions.append("Consider optimizing waypoint placement")

            evaluation = EnvEvaluation(
                env_id=env_id,
                diversity_score=round(diversity_score, 4),
                challenge_score=round(challenge_score, 4),
                realism_score=round(realism_score, 4),
                effectiveness_score=round(effectiveness_score, 4),
                total_score=round(total_score, 4),
                weights=weights,
                suggestions=suggestions,
            )
            db.add(evaluation)
            await db.commit()

            logger.info(f"Environment {env_id} evaluated: total_score={total_score:.4f}")

            eval_result = {
                "env_id": env_id,
                "evaluation_id": evaluation.id,
                "total_score": round(total_score, 4),
                "scores": {
                    "diversity": round(diversity_score, 4),
                    "challenge": round(challenge_score, 4),
                    "realism": round(realism_score, 4),
                    "effectiveness": round(effectiveness_score, 4),
                },
                "suggestions": suggestions,
            }

            # Broadcast evaluation result via WebSocket
            try:
                await _broadcast_eval_result_to_ws(env.project_id, env_id, eval_result)
            except Exception:
                pass

            return eval_result

        except Exception as e:
            logger.error(f"Failed to evaluate environment {env_id}: {e}")
            return {"env_id": env_id, "error": str(e)}


async def _broadcast_eval_result_to_ws(project_id: str, env_id: str, eval_data: dict):
    """Async helper to broadcast eval result via WebSocket."""
    try:
        from app.api.ws import push_eval_result_to_frontend
        await push_eval_result_to_frontend(project_id, env_id, eval_data)
    except Exception as e:
        logger.debug(f"WebSocket eval broadcast async failed: {e}")


# ---------------------------------------------------------------------------
# Task: Run full optimization
# ---------------------------------------------------------------------------
@celery_app.task(bind=True, name="optimization_tasks.run_optimization_task")
def run_optimization_task(self, optimization_task_id: str):
    asyncio.run(_run_optimization_async(self, optimization_task_id))


async def _run_optimization_async(task, optimization_task_id: str):
    async with async_session_factory() as db:
        try:
            result = await db.execute(
                select(OptimizationTask).where(OptimizationTask.id == optimization_task_id)
            )
            opt_task = result.scalar_one_or_none()
            if opt_task is None:
                return {"error": f"Optimization task {optimization_task_id} not found"}

            opt_task.status = "running"
            await db.commit()

            best_score = 0.0
            best_params = {}
            progress_log = []

            # Try to get the project_id for WebSocket broadcasts
            project_id = None
            try:
                env_result = await db.execute(select(Env).limit(1))
                first_env = env_result.scalar_one_or_none()
                if first_env:
                    project_id = first_env.project_id
            except Exception:
                pass

            for iteration in range(opt_task.max_iterations):
                # Generate random parameters from param_space
                current_params = {}
                for param_name, param_range in opt_task.param_space.items():
                    if isinstance(param_range, list) and len(param_range) == 2:
                        low, high = param_range
                        if isinstance(low, float) or isinstance(high, float):
                            current_params[param_name] = round(random.uniform(low, high), 4)
                        else:
                            current_params[param_name] = random.randint(int(low), int(high))

                # Evaluate parameters
                weights = opt_task.weights
                score = 0.0
                for metric, weight in weights.items():
                    # Simulate scoring with some randomness tied to params
                    param_effect = sum(
                        v for v in current_params.values()
                        if isinstance(v, (int, float))
                    )
                    normalized = (param_effect % 100) / 100.0 if param_effect else random.random()
                    score += normalized * weight

                if score > best_score:
                    best_score = score
                    best_params = dict(current_params)

                opt_task.current_iteration = iteration + 1
                opt_task.params = current_params
                opt_task.best_score = round(best_score, 4)
                await db.commit()

                # Track progress
                progress_entry = {
                    "iteration": iteration + 1,
                    "params": current_params,
                    "score": round(score, 4),
                    "best_score": round(best_score, 4),
                }
                progress_log.append(progress_entry)

                # Broadcast progress via WebSocket
                try:
                    from app.api.ws import push_notification_to_frontend
                    if project_id:
                        await push_notification_to_frontend(project_id, {
                            "level": "info",
                            "title": "Optimization Progress",
                            "message": f"Iteration {iteration + 1}/{opt_task.max_iterations}: "
                                       f"score={score:.4f}, best={best_score:.4f}",
                            "data": progress_entry,
                        })
                except Exception:
                    pass

            # Mark as completed
            opt_task.status = "completed"
            opt_task.params = best_params
            opt_task.best_score = round(best_score, 4)
            await db.commit()

            # Generate report
            report = OptimizationReport(
                task_id=optimization_task_id,
                before_scores={"total": 0.0},
                after_scores={"total": round(best_score, 4)},
                comparison_data={
                    "iterations": opt_task.max_iterations,
                    "best_params": best_params,
                    "improvement": round(best_score, 4),
                    "progress_log": progress_log,
                },
            )
            db.add(report)
            await db.commit()

            # Broadcast completion
            try:
                from app.api.ws import push_notification_to_frontend
                if project_id:
                    await push_notification_to_frontend(project_id, {
                        "level": "success",
                        "title": "Optimization Complete",
                        "message": f"Optimization {optimization_task_id} completed: "
                                   f"best_score={best_score:.4f}",
                        "data": {
                            "task_id": optimization_task_id,
                            "best_score": round(best_score, 4),
                            "best_params": best_params,
                            "report_id": report.id,
                        },
                    })
            except Exception:
                pass

            logger.info(
                f"Optimization {optimization_task_id} completed: best_score={best_score:.4f}"
            )
            return {
                "optimization_task_id": optimization_task_id,
                "status": "completed",
                "best_score": round(best_score, 4),
                "best_params": best_params,
                "report_id": report.id,
            }

        except Exception as e:
            logger.error(f"Optimization {optimization_task_id} failed: {e}")
            try:
                opt_task.status = "failed"
                await db.commit()
            except Exception:
                pass
            return {"optimization_task_id": optimization_task_id, "error": str(e), "status": "failed"}


# ---------------------------------------------------------------------------
# Score computation helpers
# ---------------------------------------------------------------------------
def _compute_diversity_score(config: dict) -> float:
    score = 0.0
    terrain = config.get("terrain", {})
    if terrain.get("type") in ("mountain", "hills", "valley"):
        score += 0.3
    elif terrain.get("type") in ("desert", "plains"):
        score += 0.2
    else:
        score += 0.1
    waypoints = config.get("waypoints", [])
    score += min(len(waypoints) / 10.0, 0.4)
    obstacles = config.get("obstacles", {})
    score += min(obstacles.get("count", 0) / 50.0, 0.3)
    return min(score, 1.0)


def _compute_challenge_score(config: dict) -> float:
    score = 0.0
    weather = config.get("weather", {})
    wind_speed = weather.get("wind_speed", 0)
    score += min(wind_speed / 30.0, 0.4)
    obstacles = config.get("obstacles", {})
    score += min(obstacles.get("count", 0) / 50.0, 0.3)
    density = obstacles.get("density", 0)
    score += density * 0.3
    return min(score, 1.0)


def _compute_realism_score(config: dict) -> float:
    score = 0.0
    weather = config.get("weather", {})
    if 0 < weather.get("wind_speed", 0) < 40:
        score += 0.3
    if 0 <= weather.get("wind_direction", 0) <= 360:
        score += 0.2
    terrain = config.get("terrain", {})
    if terrain.get("type") in ("mountain", "desert", "ocean", "plains"):
        score += 0.3
    fd = config.get("flight_dynamics", {})
    if fd.get("aircraft_model"):
        score += 0.2
    return min(score, 1.0)


def _compute_effectiveness_score(config: dict) -> float:
    score = 0.0
    waypoints = config.get("waypoints", [])
    if len(waypoints) >= 3:
        score += 0.4
    elif len(waypoints) >= 1:
        score += 0.2
    rewards = config.get("rewards", {})
    reward_items = rewards.get("reward_items", [])
    penalty_items = rewards.get("penalty_items", [])
    if len(reward_items) > 0:
        score += 0.3
    if len(penalty_items) > 0:
        score += 0.3
    return min(score, 1.0)
