import json
import logging

from app.celery_app import celery_app
from app.database import async_session_factory
from app.models.env import Env, EnvSnapshot
from app.schemas.env_config import EnvConfig
from app.services.env_generator import generate_env_package

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="env_tasks.generate_env_task")
def generate_env_task(self, env_id: str):
    import asyncio

    asyncio.run(_generate_env_async(self, env_id))


async def _generate_env_async(task, env_id: str):
    async with async_session_factory() as db:
        try:
            from sqlalchemy import select
            result = await db.execute(select(Env).where(Env.id == env_id))
            env = result.scalar_one_or_none()
            if env is None:
                logger.error(f"Environment {env_id} not found")
                return {"error": f"Environment {env_id} not found"}

            env.status = "generating"
            await db.commit()

            if env.config:
                config_data = env.config
            else:
                config_data = {
                    "terrain": {"type": "mountain", "elevation_min": 0, "elevation_max": 3000, "resolution": 1.0},
                    "weather": {"wind_speed": 5, "wind_direction": 0, "visibility": 10000},
                    "flight_dynamics": {"aircraft_model": "c172p", "mass": 1000, "wingspan": 11},
                    "rewards": {"reward_items": [], "penalty_items": []},
                    "obstacles": {"count": 0, "types": [], "density": 0},
                    "waypoints": [],
                }

            config = EnvConfig(**config_data)

            snapshot = EnvSnapshot(
                env_id=env_id,
                config=config_data,
                trigger_type="auto_generation",
                operator=None,
                reason="Initial environment generation",
            )
            db.add(snapshot)

            storage_path = await generate_env_package(env, config, db)

            env.status = "ready"
            await db.commit()

            logger.info(f"Environment {env_id} generated successfully: {storage_path}")
            return {"env_id": env_id, "storage_path": storage_path, "status": "ready"}

        except Exception as e:
            logger.error(f"Failed to generate environment {env_id}: {e}")
            env.status = "failed"
            await db.commit()
            return {"env_id": env_id, "error": str(e), "status": "failed"}


@celery_app.task(bind=True, name="env_tasks.batch_generate_envs_task")
def batch_generate_envs_task(self, env_ids: list[str]):
    import asyncio

    asyncio.run(_batch_generate_async(self, env_ids))


async def _batch_generate_async(task, env_ids: list[str]):
    results = []
    for env_id in env_ids:
        try:
            result = await _generate_env_async(task, env_id)
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to generate env {env_id}: {e}")
            results.append({"env_id": env_id, "error": str(e), "status": "failed"})
    return results
