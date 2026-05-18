"""
APScheduler integration for continuous optimization scheduling.
Provides cron-based scheduling of optimization jobs per project.
"""
import logging
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def optimization_job(project_id: str, config: dict):
    """Scheduled job to run optimization for a project."""
    try:
        from app.tasks.optimization_tasks import run_optimization_task
        logger.info(f"Running scheduled optimization for project {project_id}")
        run_optimization_task.delay(project_id, config)
    except Exception as e:
        logger.error(f"Scheduled optimization failed for project {project_id}: {e}")


async def evaluation_job(project_id: str, env_ids: list[str]):
    """Scheduled job to run environment evaluation."""
    try:
        from app.tasks.optimization_tasks import evaluate_env_task
        logger.info(f"Running scheduled evaluation for project {project_id}, {len(env_ids)} envs")
        for env_id in env_ids:
            evaluate_env_task.delay(env_id)
    except Exception as e:
        logger.error(f"Scheduled evaluation failed for project {project_id}: {e}")


def add_optimization_schedule(project_id: str, cron_expression: str, config: dict):
    """
    Add or replace a cron-based optimization schedule for a project.
    
    Args:
        project_id: The project identifier
        cron_expression: 5-part cron string: "minute hour day month day_of_week"
                         Example: "0 */2 * * *" = every 2 hours
        config: Optimization configuration to pass to the job
    """
    job_id = f"optimization_{project_id}"
    try:
        scheduler.remove_job(job_id)
    except Exception:
        pass

    parts = cron_expression.strip().split()
    if len(parts) < 5:
        raise ValueError(
            f"Invalid cron expression: '{cron_expression}'. "
            "Expected 5 parts: minute hour day month day_of_week"
        )

    trigger = CronTrigger(
        minute=parts[0],
        hour=parts[1],
        day=parts[2],
        month=parts[3],
        day_of_week=parts[4],
    )
    scheduler.add_job(
        optimization_job,
        trigger,
        args=[project_id, config],
        id=job_id,
        replace_existing=True,
        name=f"optimization_{project_id}",
    )
    logger.info(f"Added optimization schedule for project {project_id}: {cron_expression}")


def add_evaluation_schedule(project_id: str, cron_expression: str, env_ids: list[str]):
    """Add or replace a cron-based evaluation schedule for a project."""
    job_id = f"evaluation_{project_id}"
    try:
        scheduler.remove_job(job_id)
    except Exception:
        pass

    parts = cron_expression.strip().split()
    if len(parts) < 5:
        raise ValueError(
            f"Invalid cron expression: '{cron_expression}'. "
            "Expected 5 parts: minute hour day month day_of_week"
        )

    trigger = CronTrigger(
        minute=parts[0],
        hour=parts[1],
        day=parts[2],
        month=parts[3],
        day_of_week=parts[4],
    )
    scheduler.add_job(
        evaluation_job,
        trigger,
        args=[project_id, env_ids],
        id=job_id,
        replace_existing=True,
        name=f"evaluation_{project_id}",
    )
    logger.info(f"Added evaluation schedule for project {project_id}: {cron_expression}")


def remove_optimization_schedule(project_id: str):
    """Remove the optimization schedule for a project."""
    job_id = f"optimization_{project_id}"
    try:
        scheduler.remove_job(job_id)
        logger.info(f"Removed optimization schedule for project {project_id}")
    except Exception:
        logger.debug(f"No optimization schedule to remove for project {project_id}")


def remove_evaluation_schedule(project_id: str):
    """Remove the evaluation schedule for a project."""
    job_id = f"evaluation_{project_id}"
    try:
        scheduler.remove_job(job_id)
        logger.info(f"Removed evaluation schedule for project {project_id}")
    except Exception:
        logger.debug(f"No evaluation schedule to remove for project {project_id}")


def list_schedules() -> list[dict]:
    """List all currently scheduled jobs."""
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger),
        })
    return jobs


def start_scheduler():
    """Start the APScheduler if not already running."""
    if not scheduler.running:
        scheduler.start()
        logger.info("APScheduler started")
    else:
        logger.debug("APScheduler already running")


def stop_scheduler():
    """Stop the APScheduler if running."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler stopped")
