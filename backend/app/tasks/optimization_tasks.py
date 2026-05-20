import json
from celery import shared_task
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.services.evaluator import evaluator


@shared_task(bind=True, name="evaluate_env_task")
def evaluate_env_task(self, env_id: str, weights: dict = None):
    engine = create_engine(settings.DATABASE_URL.replace("+asyncpg", "+psycopg2"))
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        result = loop.run_until_complete(evaluator.evaluate(env_id, weights))

        return {"env_id": env_id, "evaluation": result}

    finally:
        session.close()


@shared_task(bind=True, name="run_optimization_task")
def run_optimization_task(self, task_id: str, param_space: dict, weights: dict, max_iterations: int):
    import asyncio
    from app.services.optimizer import optimizer

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    engine = create_engine(settings.DATABASE_URL.replace("+asyncpg", "+psycopg2"))
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        session.execute(
            text("UPDATE optimization_tasks SET status = 'running' WHERE id = :id"),
            {"id": task_id}
        )
        session.commit()

        best_score = 0
        best_params = None

        for i in range(max_iterations):
            suggest_result = loop.run_until_complete(optimizer.suggest(param_space, weights))

            score = suggest_result.get("score", 0)

            loop.run_until_complete(optimizer.observe(suggest_result.get("params", {}), score))

            if score > best_score:
                best_score = score
                best_params = suggest_result.get("params", {})

            session.execute(
                text(
                    """
                    UPDATE optimization_tasks
                    SET current_iteration = :iteration, best_score = :best_score, best_params = :best_params
                    WHERE id = :id
                    """
                ),
                {
                    "id": task_id,
                    "iteration": i + 1,
                    "best_score": best_score,
                    "best_params": json.dumps(best_params),
                }
            )
            session.commit()

        session.execute(
            text("UPDATE optimization_tasks SET status = 'completed' WHERE id = :id"),
            {"id": task_id}
        )
        session.commit()

        return {"task_id": task_id, "best_score": best_score, "best_params": best_params}

    except Exception as e:
        session.execute(
            text("UPDATE optimization_tasks SET status = 'failed' WHERE id = :id"),
            {"id": task_id}
        )
        session.commit()
        raise e

    finally:
        session.close()
