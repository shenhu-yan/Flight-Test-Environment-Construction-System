"""
定期自动重优化调度器 — 基于 APScheduler，支持数据库持久化
"""
import json
import logging
import asyncio
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)


class OptimizationScheduler:
    """管理定期优化任务的调度器，调度配置持久化到数据库。"""

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        self._jobs: dict[str, str] = {}  # project_id -> job_id

    def add_schedule(self, project_id: str, interval_hours: int = 24, max_iterations: int = 5):
        """为项目添加定期优化调度。"""
        self.remove_schedule(project_id)

        job = self.scheduler.add_job(
            _run_scheduled_optimization,
            trigger=IntervalTrigger(hours=interval_hours),
            args=[project_id, max_iterations],
            id=f"opt_{project_id}",
            name=f"Scheduled optimization for {project_id[:8]}",
            replace_existing=True,
            misfire_grace_time=3600,
        )
        self._jobs[project_id] = job.id

        # 持久化到数据库
        self._save_to_db(project_id, interval_hours, max_iterations)
        logger.info(f"[Scheduler] Added schedule for project {project_id[:8]}: every {interval_hours}h")

    def remove_schedule(self, project_id: str):
        """移除项目的定期优化调度。"""
        job_id = self._jobs.pop(project_id, None)
        if job_id:
            try:
                self.scheduler.remove_job(job_id)
            except Exception:
                pass
        self._remove_from_db(project_id)

    def get_schedule(self, project_id: str) -> dict | None:
        """获取项目的调度信息。"""
        job_id = self._jobs.get(project_id)
        if not job_id:
            return None
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                return {
                    "project_id": project_id,
                    "job_id": job_id,
                    "interval_hours": job.trigger.interval.total_seconds() / 3600,
                    "next_run_time": str(job.next_run_time) if job.next_run_time else None,
                }
        except Exception:
            pass
        return None

    def list_schedules(self) -> list[dict]:
        """列出所有调度。"""
        result = []
        for project_id in self._jobs:
            info = self.get_schedule(project_id)
            if info:
                result.append(info)
        return result

    def restore_from_db(self):
        """从数据库恢复调度配置（启动时调用）。"""
        try:
            from app.core.config import settings
            import asyncpg

            async def _restore():
                try:
                    conn = await asyncpg.connect(settings.DATABASE_URL.replace("+asyncpg", ""), timeout=5)
                    rows = await conn.fetch(
                        "SELECT project_id, interval_hours, max_iterations FROM optimization_schedules"
                    )
                    await conn.close()
                    for row in rows:
                        pid = row["project_id"]
                        if pid not in self._jobs:
                            self.add_schedule(pid, row["interval_hours"], row["max_iterations"])
                            logger.info(f"[Scheduler] Restored schedule for project {pid[:8]}")
                except Exception as e:
                    logger.info(f"[Scheduler] No schedules to restore (table may not exist yet): {e}")

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(_restore())
            finally:
                loop.close()
        except Exception as e:
            logger.info(f"[Scheduler] Restore skipped: {e}")

    def _save_to_db(self, project_id: str, interval_hours: int, max_iterations: int):
        """保存调度到数据库。"""
        try:
            from app.core.config import settings
            import asyncpg

            async def _save():
                try:
                    conn = await asyncpg.connect(settings.DATABASE_URL.replace("+asyncpg", ""), timeout=5)
                    # 建表（如果不存在）
                    await conn.execute("""
                        CREATE TABLE IF NOT EXISTS optimization_schedules (
                            project_id VARCHAR(36) PRIMARY KEY,
                            interval_hours INTEGER NOT NULL DEFAULT 24,
                            max_iterations INTEGER NOT NULL DEFAULT 5,
                            created_at TIMESTAMP DEFAULT NOW()
                        )
                    """)
                    await conn.execute(
                        """INSERT INTO optimization_schedules (project_id, interval_hours, max_iterations)
                           VALUES ($1, $2, $3)
                           ON CONFLICT (project_id) DO UPDATE SET interval_hours=$2, max_iterations=$3""",
                        project_id, interval_hours, max_iterations
                    )
                    await conn.close()
                except Exception as e:
                    logger.error(f"[Scheduler] Save error: {e}")

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(_save())
            finally:
                loop.close()
        except Exception:
            pass

    def _remove_from_db(self, project_id: str):
        """从数据库删除调度。"""
        try:
            from app.core.config import settings
            import asyncpg

            async def _remove():
                try:
                    conn = await asyncpg.connect(settings.DATABASE_URL.replace("+asyncpg", ""), timeout=5)
                    await conn.execute("DELETE FROM optimization_schedules WHERE project_id=$1", project_id)
                    await conn.close()
                except Exception:
                    pass

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(_remove())
            finally:
                loop.close()
        except Exception:
            pass

    def shutdown(self):
        """关闭调度器。"""
        self.scheduler.shutdown(wait=False)


def _run_scheduled_optimization(project_id: str, max_iterations: int = 5):
    """调度任务的执行函数 — 在后台线程中运行。"""
    from app.tasks.optimization_tasks import run_optimization_thread
    from app.core.config import settings
    import asyncpg
    import uuid
    import asyncio

    db_url = settings.DATABASE_URL.replace("+asyncpg", "")
    logger.info(f"[Scheduler] Running scheduled optimization for project {project_id[:8]}")

    async def _do_schedule():
        try:
            conn = await asyncpg.connect(db_url, timeout=10)
            rows = await conn.fetch(
                "SELECT config FROM envs WHERE project_id=$1 AND status='active' LIMIT 5",
                project_id
            )
            if not rows:
                logger.warning(f"[Scheduler] No active envs found for project {project_id[:8]}")
                await conn.close()
                return

            envs_configs = [json.loads(r["config"]) if isinstance(r["config"], str) else r["config"] for r in rows]

            # 构建参数空间
            wind_speeds = [c.get("atmosphere", {}).get("wind_speed", 10) for c in envs_configs]
            obstacle_counts = [c.get("obstacles", {}).get("count", 5) for c in envs_configs]
            avg_wind = sum(wind_speeds) / len(wind_speeds)
            avg_obstacle = sum(obstacle_counts) / len(obstacle_counts)

            def _safe_range(low, high, fb_lo, fb_hi):
                return [fb_lo, fb_hi] if low >= high else [low, high]

            param_space = {
                "wind_speed": _safe_range(max(0, avg_wind * 0.5), min(50, avg_wind * 1.5), 0, 30),
                "obstacle_count": _safe_range(max(0, avg_obstacle * 0.5), min(50, avg_obstacle * 1.5), 0, 15),
                "wind_direction": [0, 360],
                "distance_scale": [100, 600],
                "distance_weight": [0.1, 1.0],
                "heading_weight": [0.1, 1.0],
            }

            base_config = envs_configs[0]

            # 创建优化任务记录
            task_id = str(uuid.uuid4())
            await conn.execute(
                """INSERT INTO optimization_tasks (id, project_id, param_space, weights, max_iterations, current_iteration, status, created_at)
                   VALUES ($1, $2, $3, $4, $5, 0, 'running', NOW())""",
                task_id, project_id, json.dumps(param_space),
                json.dumps({"diversity": 0.25, "challenge": 0.25, "realism": 0.25, "effectiveness": 0.25}),
                max_iterations
            )
            await conn.close()

            # 执行优化
            run_optimization_thread(task_id, project_id, base_config, param_space, max_iterations)

        except Exception as e:
            logger.error(f"[Scheduler] Error: {e}")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_do_schedule())
    finally:
        loop.close()


# 全局单例
optimization_scheduler = OptimizationScheduler()
