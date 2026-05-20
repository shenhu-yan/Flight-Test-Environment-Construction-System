import json
from celery import shared_task
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.schemas.env_config import EnvConfig
from app.services.env_generator import generate_environment


@shared_task(bind=True, name="generate_env_task")
def generate_env_task(self, env_id: str, config_dict: dict, project_id: str, creator_id: str):
    engine = create_engine(settings.DATABASE_URL.replace("+asyncpg", "+psycopg2"))
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        session.execute(
            text("UPDATE envs SET status = 'generating' WHERE id = :id"),
            {"id": env_id}
        )
        session.commit()

        config = EnvConfig(**config_dict)
        result = generate_environment(env_id, config, project_id, creator_id)

        session.execute(
            text(
                """
                UPDATE envs
                SET status = 'active', storage_path = :storage_path, config = :config, updated_at = NOW()
                WHERE id = :id
                """
            ),
            {
                "id": env_id,
                "storage_path": result["storage_path"],
                "config": json.dumps(result["config"]),
            }
        )
        session.commit()

        return {"env_id": env_id, "status": "active"}

    except Exception as e:
        session.execute(
            text("UPDATE envs SET status = 'error', updated_at = NOW() WHERE id = :id"),
            {"id": env_id}
        )
        session.commit()
        raise e

    finally:
        session.close()


@shared_task(bind=True, name="batch_generate_envs_task")
def batch_generate_envs_task(self, batch_id: str, configs: list, project_id: str, creator_id: str):
    results = []
    for i, config_dict in enumerate(configs):
        env_id = configs[i].get("id")
        if env_id:
            result = generate_env_task.delay(env_id, config_dict["config"], project_id, creator_id)
            results.append({"env_id": env_id, "task_id": str(result.id)})
    return {"batch_id": batch_id, "tasks": results}
