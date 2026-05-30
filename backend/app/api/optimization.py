import uuid
import json
import threading
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db
from app.core.security import get_current_user, require_project_configurer
from app.tasks.optimization_tasks import run_optimization_thread

router = APIRouter()

# ──────────────────────────────────────────────
#  环境评估（快速启发式，前端即时展示用）
# ──────────────────────────────────────────────

@router.post("/envs/{env_id}/evaluate")
async def evaluate_env(
    env_id: str,
    weights: dict = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """快速评估环境配置（基于公式，不运行训练）。"""
    result = await db.execute(
        text("SELECT id, config FROM envs WHERE id = :id"),
        {"id": env_id}
    )
    env = result.fetchone()
    if not env:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Environment not found")

    config = json.loads(env[1]) if isinstance(env[1], str) else env[1]

    if weights is None:
        weights = {"diversity": 0.25, "challenge": 0.25, "realism": 0.25, "effectiveness": 0.25}

    # 多样性评分
    terrain_type = config.get("terrain", {}).get("type", "flat")
    wind_speed = config.get("atmosphere", {}).get("wind_speed", 5)
    obstacle_count = config.get("obstacles", {}).get("count", 0)
    waypoint_count = len(config.get("waypoints", []))
    reward_items = len(config.get("reward", {}).get("items", []))
    penalty_items = len(config.get("reward", {}).get("penalties", []))

    terrain_score = {"flat": 30, "hilly": 60, "mountainous": 90}.get(terrain_type, 50)
    param_diversity = min((wind_speed / 20 + obstacle_count / 20 + waypoint_count / 5 + reward_items / 3) * 25, 100)
    diversity_score = (terrain_score + param_diversity) / 2

    # 挑战性评分
    wind_challenge = min(wind_speed / 25 * 100, 100)
    obstacle_challenge = min(obstacle_count / 15 * 100, 100)
    terrain_challenge = {"flat": 20, "hilly": 50, "mountainous": 80}.get(terrain_type, 50)
    challenge_score = (wind_challenge * 0.3 + obstacle_challenge * 0.4 + terrain_challenge * 0.3)

    # 真实性评分
    aircraft_model = config.get("aircraft", {}).get("model", "c172x")
    mass = config.get("aircraft", {}).get("mass", 1000)
    wingspan = config.get("aircraft", {}).get("wingspan", 10)
    model_scores = {"c172x": 85, "f16": 90, "cessna": 80}
    model_score = model_scores.get(aircraft_model, 60)
    if 500 <= mass <= 50000 and 5 <= wingspan <= 50:
        param_score = 90
    elif 100 <= mass <= 100000 and 1 <= wingspan <= 100:
        param_score = 70
    else:
        param_score = 50
    realism_score = (model_score + param_score) / 2

    # 有效性评分
    if reward_items > 0 and penalty_items > 0:
        effectiveness_score = 75
    elif reward_items > 0:
        effectiveness_score = 60
    else:
        effectiveness_score = 40
    if obstacle_count > 0 and waypoint_count > 0:
        effectiveness_score = min(effectiveness_score + 10, 100)

    total_score = (
        weights.get("diversity", 0.25) * diversity_score +
        weights.get("challenge", 0.25) * challenge_score +
        weights.get("realism", 0.25) * realism_score +
        weights.get("effectiveness", 0.25) * effectiveness_score
    )

    # 生成建议
    suggestions = []
    if diversity_score < 40:
        suggestions.append("多样性严重不足，建议大幅增加参数变化范围")
    elif diversity_score < 60:
        suggestions.append("多样性偏低，建议增加参数变化范围")
    if challenge_score < 40:
        suggestions.append("挑战性严重不足，建议增加障碍物数量和风速")
    elif challenge_score < 60:
        suggestions.append("挑战性偏低，建议适当增加环境复杂度")
    if realism_score < 40:
        suggestions.append("真实性严重不足，建议使用标准机型参数")
    if effectiveness_score < 40:
        suggestions.append("有效性严重不足，建议优化奖励函数设计")
    if total_score < 50:
        suggestions.append("总体评分较低，建议使用更合适的模板")

    # 保存评估结果
    evaluation_id = str(uuid.uuid4())
    await db.execute(
        text(
            """INSERT INTO env_evaluations (id, env_id, diversity_score, challenge_score, realism_score, effectiveness_score, total_score, weights, suggestions, created_at)
               VALUES (:id, :env_id, :diversity_score, :challenge_score, :realism_score, :effectiveness_score, :total_score, :weights, :suggestions, NOW())"""
        ),
        {
            "id": evaluation_id, "env_id": env_id,
            "diversity_score": round(diversity_score, 2),
            "challenge_score": round(challenge_score, 2),
            "realism_score": round(realism_score, 2),
            "effectiveness_score": round(effectiveness_score, 2),
            "total_score": round(total_score, 2),
            "weights": json.dumps(weights),
            "suggestions": json.dumps(suggestions),
        }
    )
    await db.commit()

    return {
        "code": 0,
        "data": {
            "evaluation_id": evaluation_id,
            "diversity_score": round(diversity_score, 2),
            "challenge_score": round(challenge_score, 2),
            "realism_score": round(realism_score, 2),
            "effectiveness_score": round(effectiveness_score, 2),
            "total_score": round(total_score, 2),
            "suggestions": suggestions,
        }
    }


@router.delete("/envs/{env_id}/evaluations/{evaluation_id}")
async def delete_evaluation(
    env_id: str, evaluation_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        text("SELECT id FROM env_evaluations WHERE id = :id AND env_id = :env_id"),
        {"id": evaluation_id, "env_id": env_id}
    )
    if not result.fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation not found")
    await db.execute(text("DELETE FROM env_evaluations WHERE id = :id"), {"id": evaluation_id})
    return {"code": 0, "message": "Evaluation deleted successfully"}


@router.get("/envs/{env_id}/evaluations")
async def get_evaluations(
    env_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        text(
            """SELECT id, env_id, diversity_score, challenge_score, realism_score, effectiveness_score, total_score, weights, suggestions, created_at
               FROM env_evaluations WHERE env_id = :env_id ORDER BY created_at DESC"""
        ),
        {"env_id": env_id}
    )
    evaluations = result.fetchall()
    return {
        "code": 0,
        "data": [
            {
                "id": e[0], "env_id": e[1],
                "diversity_score": e[2], "challenge_score": e[3],
                "realism_score": e[4], "effectiveness_score": e[5],
                "total_score": e[6],
                "weights": json.loads(e[7]) if isinstance(e[7], str) else e[7],
                "suggestions": json.loads(e[8]) if isinstance(e[8], str) else e[8],
                "created_at": str(e[9]) if e[9] else None,
            }
            for e in evaluations
        ]
    }


# ──────────────────────────────────────────────
#  优化任务管理
# ──────────────────────────────────────────────

from pydantic import BaseModel

class AutoOptimizeRequest(BaseModel):
    project_id: str
    max_iterations: int = 10


def _build_param_space(envs_configs: list) -> dict:
    """根据项目中已有环境的配置，自动确定优化参数空间。"""
    wind_speeds = [c.get("atmosphere", {}).get("wind_speed", 10) for c in envs_configs]
    obstacle_counts = [c.get("obstacles", {}).get("count", 5) for c in envs_configs]

    avg_wind = sum(wind_speeds) / len(wind_speeds) if wind_speeds else 10
    avg_obstacle = sum(obstacle_counts) / len(obstacle_counts) if obstacle_counts else 5

    # 确保每个参数的下界 < 上界（scikit-optimize 要求）
    def _safe_range(low, high, fallback_low, fallback_high):
        if low >= high:
            return [fallback_low, fallback_high]
        return [low, high]

    return {
        "wind_speed": _safe_range(max(0, avg_wind * 0.5), min(50, avg_wind * 1.5), 0, 30),
        "obstacle_count": _safe_range(max(0, avg_obstacle * 0.5), min(50, avg_obstacle * 1.5), 0, 15),
        "wind_direction": [0, 360],
        "distance_scale": [100, 600],
        "distance_weight": [0.1, 1.0],
        "heading_weight": [0.1, 1.0],
    }


def _get_base_config(envs_configs: list) -> dict:
    """取第一个环境的配置作为优化基础。"""
    if envs_configs:
        return envs_configs[0]
    return {
        "terrain": {"type": "flat"},
        "atmosphere": {"wind_speed": 5, "wind_direction": 90},
        "aircraft": {"model": "c172x", "mass": 1043, "wingspan": 11},
        "reward": {"items": [], "penalties": []},
        "obstacles": {"count": 0},
    }


@router.post("/optimization-tasks/auto", status_code=status.HTTP_201_CREATED)
async def auto_optimize(
    request: AutoOptimizeRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """全自动智能优化 — 基于真实 DQN 训练 + 贝叶斯优化。"""
    print(f"[API] auto_optimize called!", flush=True)
    project_id = request.project_id
    max_iterations = min(request.max_iterations, 20)  # 上限20轮

    # 获取项目中的环境配置
    result = await db.execute(
        text("SELECT config FROM envs WHERE project_id = :pid AND status = 'active' LIMIT 5"),
        {"pid": project_id}
    )
    envs = result.fetchall()
    if not envs:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="没有可优化的环境")

    envs_configs = [json.loads(e[0]) if isinstance(e[0], str) else e[0] for e in envs]
    param_space = _build_param_space(envs_configs)
    base_config = _get_base_config(envs_configs)

    # 创建优化任务记录
    task_id = str(uuid.uuid4())
    await db.execute(
        text(
            """INSERT INTO optimization_tasks (id, project_id, param_space, weights, max_iterations, current_iteration, status, created_at)
               VALUES (:id, :pid, :ps, :w, :mi, 0, 'running', NOW())"""
        ),
        {
            "id": task_id, "pid": project_id,
            "ps": json.dumps(param_space),
            "w": json.dumps({"diversity": 0.25, "challenge": 0.25, "realism": 0.25, "effectiveness": 0.25}),
            "mi": max_iterations,
        }
    )
    await db.commit()

    # 在后台线程中启动优化（纯同步，不阻塞 API）
    thread = threading.Thread(
        target=run_optimization_thread,
        args=(task_id, project_id, base_config, param_space, max_iterations),
        daemon=True,
    )
    thread.start()

    resp = {
        "code": 0,
        "data": {
            "id": task_id,
            "status": "running",
            "max_iterations": max_iterations,
            "param_space": param_space,
            "message": "优化已启动，基于真实 DQN 训练 + 贝叶斯优化",
        }
    }
    print(f"[API] Returning: {resp}", flush=True)
    return resp


class ManualOptimizeRequest(BaseModel):
    project_id: str
    param_space: dict = None
    weights: dict = None
    max_iterations: int = 10


@router.post("/optimization-tasks", status_code=status.HTTP_201_CREATED)
async def create_optimization_task(
    request: ManualOptimizeRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """手动创建优化任务 — 用户自定义参数空间和权重。"""
    project_id = request.project_id
    max_iterations = min(request.max_iterations, 20)

    # 获取基础配置
    result = await db.execute(
        text("SELECT config FROM envs WHERE project_id = :pid AND status = 'active' LIMIT 1"),
        {"pid": project_id}
    )
    env = result.fetchone()
    base_config = json.loads(env[0]) if env and isinstance(env[0], str) else (env[0] if env else {})

    # 参数空间：用户指定或使用默认
    param_space = request.param_space or {
        "wind_speed": [0, 30],
        "obstacle_count": [0, 20],
        "wind_direction": [0, 360],
        "distance_scale": [100, 600],
        "distance_weight": [0.1, 1.0],
        "heading_weight": [0.1, 1.0],
    }

    weights = request.weights or {"diversity": 0.25, "challenge": 0.25, "realism": 0.25, "effectiveness": 0.25}

    # 创建任务记录
    task_id = str(uuid.uuid4())
    await db.execute(
        text(
            """INSERT INTO optimization_tasks (id, project_id, param_space, weights, max_iterations, current_iteration, status, created_at)
               VALUES (:id, :pid, :ps, :w, :mi, 0, 'running', NOW())"""
        ),
        {"id": task_id, "pid": project_id, "ps": json.dumps(param_space), "w": json.dumps(weights), "mi": max_iterations}
    )
    await db.commit()

    # 在后台线程中启动优化
    thread = threading.Thread(
        target=run_optimization_thread,
        args=(task_id, project_id, base_config, param_space, max_iterations),
        daemon=True,
    )
    thread.start()

    return {
        "code": 0,
        "data": {"id": task_id, "status": "running", "max_iterations": max_iterations}
    }


@router.delete("/optimization-tasks/{task_id}")
async def delete_optimization_task(
    task_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        text("SELECT id, status FROM optimization_tasks WHERE id = :id"),
        {"id": task_id}
    )
    task = result.fetchone()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Optimization task not found")
    if task[1] == 'running':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete a running task, stop it first")
    await db.execute(text("DELETE FROM optimization_tasks WHERE id = :id"), {"id": task_id})
    return {"code": 0, "message": "Optimization task deleted successfully"}


@router.get("/optimization-tasks")
async def get_optimization_tasks(
    project_id: str = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = "SELECT id, project_id, max_iterations, current_iteration, status, best_score, created_at FROM optimization_tasks WHERE 1=1"
    params = {}
    if project_id:
        query += " AND project_id = :project_id"
        params["project_id"] = project_id
    query += " ORDER BY created_at DESC"
    result = await db.execute(text(query), params)
    tasks = result.fetchall()
    return {
        "code": 0,
        "data": [
            {
                "id": t[0], "project_id": t[1], "max_iterations": t[2],
                "current_iteration": t[3], "status": t[4],
                "best_score": t[5], "created_at": str(t[6]) if t[6] else None,
            }
            for t in tasks
        ]
    }


@router.get("/optimization-tasks/{task_id}")
async def get_optimization_task(
    task_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        text(
            """SELECT id, project_id, param_space, weights, max_iterations, current_iteration, status, best_params, best_score, created_at
               FROM optimization_tasks WHERE id = :id"""
        ),
        {"id": task_id}
    )
    task = result.fetchone()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Optimization task not found")
    return {
        "code": 0,
        "data": {
            "id": task[0], "project_id": task[1],
            "param_space": json.loads(task[2]) if isinstance(task[2], str) else task[2],
            "weights": json.loads(task[3]) if isinstance(task[3], str) else task[3],
            "max_iterations": task[4], "current_iteration": task[5],
            "status": task[6],
            "best_params": json.loads(task[7]) if task[7] and isinstance(task[7], str) else task[7],
            "best_score": task[8],
            "created_at": str(task[9]) if task[9] else None,
        }
    }


@router.post("/optimization-tasks/{task_id}/stop")
async def stop_optimization_task(
    task_id: str,
    current_user: dict = Depends(require_project_configurer),
    db: AsyncSession = Depends(get_db)
):
    from app.tasks.optimization_tasks import request_stop
    result = await db.execute(
        text("SELECT id, status FROM optimization_tasks WHERE id = :id"),
        {"id": task_id}
    )
    task = result.fetchone()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Optimization task not found")
    if task[1] == 'completed':
        return {"code": 0, "message": "Task already completed"}
    request_stop(task_id)
    await db.execute(text("UPDATE optimization_tasks SET status = 'stopped' WHERE id = :id"), {"id": task_id})
    return {"code": 0, "message": "Optimization task stopped"}


@router.get("/optimization-reports/{report_id}")
async def get_optimization_report(
    report_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        text(
            """SELECT id, task_id, before_scores, after_scores, comparison_data, created_at
               FROM optimization_reports WHERE id = :id"""
        ),
        {"id": report_id}
    )
    report = result.fetchone()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Optimization report not found")
    return {
        "code": 0,
        "data": {
            "id": report[0], "task_id": report[1],
            "before_scores": json.loads(report[2]) if isinstance(report[2], str) else report[2],
            "after_scores": json.loads(report[3]) if isinstance(report[3], str) else report[3],
            "comparison_data": json.loads(report[4]) if isinstance(report[4], str) else report[4],
            "created_at": str(report[5]) if report[5] else None,
        }
    }


# ──────────────────────────────────────────────
#  定期自动重优化调度
# ──────────────────────────────────────────────

class ScheduleRequest(BaseModel):
    project_id: str
    interval_hours: int = 24
    max_iterations: int = 5


@router.post("/optimization-schedules")
async def create_schedule(
    request: ScheduleRequest,
    current_user: dict = Depends(get_current_user),
):
    """创建定期自动优化调度。"""
    from app.services.scheduler import optimization_scheduler
    optimization_scheduler.add_schedule(
        project_id=request.project_id,
        interval_hours=request.interval_hours,
        max_iterations=request.max_iterations,
    )
    info = optimization_scheduler.get_schedule(request.project_id)
    return {"code": 0, "data": info}


@router.get("/optimization-schedules")
async def list_schedules(
    current_user: dict = Depends(get_current_user),
):
    """列出所有定期优化调度。"""
    from app.services.scheduler import optimization_scheduler
    schedules = optimization_scheduler.list_schedules()
    return {"code": 0, "data": schedules}


@router.delete("/optimization-schedules/{project_id}")
async def delete_schedule(
    project_id: str,
    current_user: dict = Depends(get_current_user),
):
    """删除项目的定期优化调度。"""
    from app.services.scheduler import optimization_scheduler
    optimization_scheduler.remove_schedule(project_id)
    return {"code": 0, "message": "Schedule removed"}
