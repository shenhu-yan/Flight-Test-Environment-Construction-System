import uuid
import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db
from app.core.security import get_current_user, require_project_configurer
from app.tasks.optimization_tasks import evaluate_env_task, run_optimization_task

router = APIRouter()


@router.post("/envs/{env_id}/evaluate")
async def evaluate_env(
    env_id: str,
    weights: dict = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        text("SELECT id, config FROM envs WHERE id = :id"),
        {"id": env_id}
    )
    env = result.fetchone()
    if not env:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Environment not found")

    config = json.loads(env[1]) if isinstance(env[1], str) else env[1]

    # 基于环境配置计算评估分数
    import math

    # 多样性评分：基于配置参数的丰富程度
    terrain_type = config.get("terrain", {}).get("type", "flat")
    wind_speed = config.get("atmosphere", {}).get("wind_speed", 5)
    obstacle_count = config.get("obstacles", {}).get("count", 0)
    waypoint_count = len(config.get("waypoints", []))
    reward_items = len(config.get("reward", {}).get("items", []))
    penalty_items = len(config.get("reward", {}).get("penalties", []))

    # 地形多样性
    terrain_score = {"flat": 30, "hilly": 60, "mountainous": 90}.get(terrain_type, 50)
    # 参数多样性
    param_diversity = min((wind_speed / 20 + obstacle_count / 20 + waypoint_count / 5 + reward_items / 3) * 25, 100)
    diversity_score = (terrain_score + param_diversity) / 2

    # 挑战性评分：基于环境难度
    wind_challenge = min(wind_speed / 25 * 100, 100)
    obstacle_challenge = min(obstacle_count / 15 * 100, 100)
    terrain_challenge = {"flat": 20, "hilly": 50, "mountainous": 80}.get(terrain_type, 50)
    challenge_score = (wind_challenge * 0.3 + obstacle_challenge * 0.4 + terrain_challenge * 0.3)

    # 真实性评分：基于参数的合理性
    aircraft_model = config.get("aircraft", {}).get("model", "c172x")
    mass = config.get("aircraft", {}).get("mass", 1000)
    wingspan = config.get("aircraft", {}).get("wingspan", 10)

    # 机型真实性
    model_scores = {"c172x": 85, "f16": 90, "cessna": 80}
    model_score = model_scores.get(aircraft_model, 60)

    # 参数合理性
    if 500 <= mass <= 50000 and 5 <= wingspan <= 50:
        param_score = 90
    elif 100 <= mass <= 100000 and 1 <= wingspan <= 100:
        param_score = 70
    else:
        param_score = 50

    realism_score = (model_score + param_score) / 2

    # 有效性评分：基于奖励函数设计
    if reward_items > 0 and penalty_items > 0:
        effectiveness_score = 75
    elif reward_items > 0:
        effectiveness_score = 60
    else:
        effectiveness_score = 40

    # 根据配置完善程度调整
    if obstacle_count > 0 and waypoint_count > 0:
        effectiveness_score = min(effectiveness_score + 10, 100)

    if weights is None:
        weights = {"diversity": 0.25, "challenge": 0.25, "realism": 0.25, "effectiveness": 0.25}

    total_score = (
        weights.get("diversity", 0.25) * diversity_score +
        weights.get("challenge", 0.25) * challenge_score +
        weights.get("realism", 0.25) * realism_score +
        weights.get("effectiveness", 0.25) * effectiveness_score
    )

    suggestions = []

    # 多样性建议
    if diversity_score < 40:
        suggestions.append("多样性严重不足，建议大幅增加参数变化范围，尝试不同的地形类型和气象条件")
    elif diversity_score < 60:
        suggestions.append("多样性偏低，建议增加参数变化范围，引入更多随机因素")
    elif diversity_score > 80:
        suggestions.append("多样性良好，参数配置丰富多样")

    # 挑战性建议
    if challenge_score < 40:
        suggestions.append("挑战性严重不足，建议增加障碍物数量、提高风速、增加航路点复杂度")
    elif challenge_score < 60:
        suggestions.append("挑战性偏低，建议适当增加环境复杂度")
    elif challenge_score > 80:
        suggestions.append("挑战性良好，环境难度适中")

    # 真实性建议
    if realism_score < 40:
        suggestions.append("真实性严重不足，建议使用标准机型参数、合理的气象条件、真实的物理建模")
    elif realism_score < 60:
        suggestions.append("真实性偏低，建议使用更真实的物理参数和环境配置")
    elif realism_score > 80:
        suggestions.append("真实性良好，物理参数设置合理")

    # 有效性建议
    if effectiveness_score < 40:
        suggestions.append("有效性严重不足，建议优化奖励函数设计、调整奖励系数、增加有效的训练信号")
    elif effectiveness_score < 60:
        suggestions.append("有效性不足，建议优化奖励函数，确保训练信号清晰有效")
    elif effectiveness_score > 80:
        suggestions.append("有效性良好，训练效果显著")

    # 综合建议
    if total_score < 50:
        suggestions.append("总体评分较低，建议重新审视环境配置，考虑使用更合适的模板")
    elif total_score > 75:
        suggestions.append("总体评分良好，环境配置较为合理")

    # 具体优化建议
    if diversity_score < 60 and challenge_score < 60:
        suggestions.append("建议尝试中等难度模板，在多样性和挑战性之间取得平衡")
    if effectiveness_score < 50 and realism_score > 70:
        suggestions.append("环境真实性好但训练效果差，建议调整奖励函数系数")

    # 保存评估结果
    evaluation_id = str(uuid.uuid4())
    await db.execute(
        text(
            """
            INSERT INTO env_evaluations (id, env_id, diversity_score, challenge_score, realism_score, effectiveness_score, total_score, weights, suggestions, created_at)
            VALUES (:id, :env_id, :diversity_score, :challenge_score, :realism_score, :effectiveness_score, :total_score, :weights, :suggestions, NOW())
            """
        ),
        {
            "id": evaluation_id,
            "env_id": env_id,
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
    env_id: str,
    evaluation_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        text("SELECT id FROM env_evaluations WHERE id = :id AND env_id = :env_id"),
        {"id": evaluation_id, "env_id": env_id}
    )
    if not result.fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation not found")

    await db.execute(
        text("DELETE FROM env_evaluations WHERE id = :id"),
        {"id": evaluation_id}
    )
    return {"code": 0, "message": "Evaluation deleted successfully"}


@router.get("/envs/{env_id}/evaluations")
async def get_evaluations(
    env_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        text(
            """
            SELECT id, env_id, diversity_score, challenge_score, realism_score, effectiveness_score, total_score, weights, suggestions, created_at
            FROM env_evaluations WHERE env_id = :env_id
            ORDER BY created_at DESC
            """
        ),
        {"env_id": env_id}
    )
    evaluations = result.fetchall()
    return {
        "code": 0,
        "data": [
            {
                "id": e[0],
                "env_id": e[1],
                "diversity_score": e[2],
                "challenge_score": e[3],
                "realism_score": e[4],
                "effectiveness_score": e[5],
                "total_score": e[6],
                "weights": json.loads(e[7]) if isinstance(e[7], str) else e[7],
                "suggestions": json.loads(e[8]) if isinstance(e[8], str) else e[8],
                "created_at": str(e[9]) if e[9] else None,
            }
            for e in evaluations
        ]
    }


from pydantic import BaseModel

class AutoOptimizeRequest(BaseModel):
    project_id: str
    max_iterations: int = 10


@router.post("/optimization-tasks/auto", status_code=status.HTTP_201_CREATED)
async def auto_optimize(
    request: AutoOptimizeRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """全自动智能优化 - 系统自动分析并优化环境参数"""
    project_id = request.project_id
    max_iterations = request.max_iterations

    # 获取项目中所有活跃环境的配置，分析参数范围
    result = await db.execute(
        text("SELECT config FROM envs WHERE project_id = :project_id AND status = 'active' LIMIT 5"),
        {"project_id": project_id}
    )
    envs = result.fetchall()

    if not envs:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="没有可优化的环境")

    # 分析当前配置，确定优化参数空间
    wind_speeds = []
    obstacle_counts = []
    for env in envs:
        config = json.loads(env[0]) if isinstance(env[0], str) else env[0]
        wind_speeds.append(config.get("atmosphere", {}).get("wind_speed", 10))
        obstacle_counts.append(config.get("obstacles", {}).get("count", 5))

    # 根据当前值自动确定优化范围（当前值的±50%作为搜索范围）
    avg_wind = sum(wind_speeds) / len(wind_speeds)
    avg_obstacle = sum(obstacle_counts) / len(obstacle_counts)

    param_space = {
        "wind_speed": [max(0, avg_wind * 0.5), min(50, avg_wind * 1.5)],
        "obstacle_count": [max(0, avg_obstacle * 0.5), min(50, avg_obstacle * 1.5)],
        "wind_direction": [0, 360],
    }

    # 自动权重：根据当前各维度表现调整
    weights = {"diversity": 0.25, "challenge": 0.25, "realism": 0.25, "effectiveness": 0.25}

    # 创建优化任务
    task_id = str(uuid.uuid4())
    await db.execute(
        text(
            """
            INSERT INTO optimization_tasks (id, project_id, param_space, weights, max_iterations, current_iteration, status, created_at)
            VALUES (:id, :project_id, :param_space, :weights, :max_iterations, 0, 'running', NOW())
            """
        ),
        {
            "id": task_id,
            "project_id": project_id,
            "param_space": json.dumps(param_space),
            "weights": json.dumps(weights),
            "max_iterations": max_iterations,
        }
    )
    await db.commit()

    # 执行智能优化
    import random
    import math

    def evaluate_params_detailed(params: dict) -> dict:
        wind_speed = params.get("wind_speed", 10)
        obstacle_count = params.get("obstacle_count", 5)

        wind_challenge = min(wind_speed / 25 * 100, 100)
        obstacle_challenge = min(obstacle_count / 15 * 100, 100)
        challenge_score = (wind_challenge * 0.5 + obstacle_challenge * 0.5)
        diversity_score = min((wind_speed / 20 + obstacle_count / 20) * 50, 100)
        realism_score = 80
        effectiveness_score = 70
        total_score = (diversity_score * 0.25 + challenge_score * 0.25 +
                       realism_score * 0.25 + effectiveness_score * 0.25)

        return {
            "total": total_score,
            "diversity": diversity_score,
            "challenge": challenge_score,
            "realism": realism_score,
            "effectiveness": effectiveness_score,
        }

    def smart_adjust(current_params, scores, iteration, max_iter, p_space):
        new_params = current_params.copy()
        learning_rate = max(0.1, 1.0 - iteration / max_iter)
        wind_range = p_space.get("wind_speed", [0, 50])
        obstacle_range = p_space.get("obstacle_count", [0, 50])

        if scores["total"] < 40:
            new_params["wind_speed"] = min(current_params["wind_speed"] + 5 * learning_rate, wind_range[1])
            new_params["obstacle_count"] = min(current_params["obstacle_count"] + 3 * learning_rate, obstacle_range[1])
        elif scores["challenge"] < 50:
            new_params["wind_speed"] = min(current_params["wind_speed"] + 3 * learning_rate, wind_range[1])
            new_params["obstacle_count"] = min(current_params["obstacle_count"] + 2 * learning_rate, obstacle_range[1])
        elif scores["diversity"] < 50:
            new_params["wind_speed"] = min(current_params["wind_speed"] + 2 * learning_rate, wind_range[1])
            new_params["obstacle_count"] = min(current_params["obstacle_count"] + 1 * learning_rate, obstacle_range[1])
        elif scores["total"] < 70:
            new_params["wind_speed"] = max(wind_range[0], min(current_params["wind_speed"] + random.uniform(-2, 2) * learning_rate, wind_range[1]))
            new_params["obstacle_count"] = max(obstacle_range[0], min(current_params["obstacle_count"] + random.uniform(-1, 1) * learning_rate, obstacle_range[1]))
        else:
            exploration = random.uniform(-1, 1) * learning_rate
            new_params["wind_speed"] = max(wind_range[0], min(current_params["wind_speed"] + exploration, wind_range[1]))
            new_params["obstacle_count"] = max(obstacle_range[0], min(current_params["obstacle_count"] + exploration * 0.5, obstacle_range[1]))

        new_params["wind_direction"] = (current_params["wind_direction"] + random.uniform(-5, 5)) % 360
        return new_params

    best_score = 0
    best_params = {}
    current_params = {
        "wind_speed": avg_wind,
        "obstacle_count": avg_obstacle,
        "wind_direction": 90.0,
    }

    for i in range(max_iterations):
        scores = evaluate_params_detailed(current_params)
        if scores["total"] > best_score:
            best_score = scores["total"]
            best_params = current_params.copy()

        current_params = smart_adjust(current_params, scores, i, max_iterations, param_space)

        await db.execute(
            text("UPDATE optimization_tasks SET current_iteration = :iter, best_score = :score, best_params = :params WHERE id = :id"),
            {"id": task_id, "iter": i + 1, "score": round(best_score, 2), "params": json.dumps(best_params)}
        )
        await db.commit()

    # 应用最优参数到所有环境并记录调整历史
    result = await db.execute(
        text("SELECT id, config FROM envs WHERE project_id = :project_id AND status = 'active'"),
        {"project_id": project_id}
    )
    all_envs = result.fetchall()

    for env in all_envs:
        env_id = env[0]
        old_config = json.loads(env[1]) if isinstance(env[1], str) else env[1]
        new_config = old_config.copy()

        if "wind_speed" in best_params:
            new_config.setdefault("atmosphere", {})["wind_speed"] = round(best_params["wind_speed"], 2)
        if "obstacle_count" in best_params:
            new_config.setdefault("obstacles", {})["count"] = int(best_params["obstacle_count"])
        if "wind_direction" in best_params:
            new_config.setdefault("atmosphere", {})["wind_direction"] = round(best_params["wind_direction"], 2)

        # 保存调整前的快照
        snapshot_before_id = str(uuid.uuid4())
        await db.execute(
            text(
                """
                INSERT INTO env_snapshots (id, env_id, config, trigger_type, operator, reason, created_at)
                VALUES (:id, :env_id, :config, 'auto_adjust', :operator, :reason, NOW())
                """
            ),
            {
                "id": snapshot_before_id,
                "env_id": env_id,
                "config": json.dumps(old_config),
                "operator": current_user["id"],
                "reason": "智能优化调整",
            }
        )

        # 更新环境配置
        await db.execute(
            text("UPDATE envs SET config = :config, updated_at = NOW() WHERE id = :id"),
            {"id": env_id, "config": json.dumps(new_config)}
        )

        # 保存调整后的快照
        snapshot_after_id = str(uuid.uuid4())
        await db.execute(
            text(
                """
                INSERT INTO env_snapshots (id, env_id, config, trigger_type, operator, reason, created_at)
                VALUES (:id, :env_id, :config, 'auto_adjust', :operator, :reason, NOW())
                """
            ),
            {
                "id": snapshot_after_id,
                "env_id": env_id,
                "config": json.dumps(new_config),
                "operator": current_user["id"],
                "reason": f"智能优化完成，最优分数: {round(best_score, 2)}",
            }
        )

        # 记录调整历史
        await db.execute(
            text(
                """
                INSERT INTO adjustment_history (id, env_id, snapshot_before, snapshot_after, trigger_type, trigger_rule, operator, created_at)
                VALUES (:id, :env_id, :snapshot_before, :snapshot_after, 'auto', NULL, :operator, NOW())
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "env_id": env_id,
                "snapshot_before": snapshot_before_id,
                "snapshot_after": snapshot_after_id,
                "operator": current_user["id"],
            }
        )

    await db.execute(
        text("UPDATE optimization_tasks SET status = 'completed' WHERE id = :id"),
        {"id": task_id}
    )
    await db.commit()

    return {
        "code": 0,
        "data": {
            "id": task_id,
            "status": "completed",
            "best_score": round(best_score, 2),
            "best_params": best_params,
            "message": f"优化完成！最优分数: {round(best_score, 2)}"
        }
    }


@router.post("/optimization-tasks", status_code=status.HTTP_201_CREATED)
async def create_optimization_task(
    task_data: dict,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    task_id = str(uuid.uuid4())

    await db.execute(
        text(
            """
            INSERT INTO optimization_tasks (id, project_id, param_space, weights, max_iterations, current_iteration, status, created_at)
            VALUES (:id, :project_id, :param_space, :weights, :max_iterations, 0, 'running', NOW())
            """
        ),
        {
            "id": task_id,
            "project_id": task_data.get("project_id"),
            "param_space": json.dumps(task_data.get("param_space", {})),
            "weights": json.dumps(task_data.get("weights", {})),
            "max_iterations": task_data.get("max_iterations", 10),
        }
    )

    # 智能优化任务
    import random
    import math

    def evaluate_params_detailed(params: dict) -> dict:
        """基于参数计算详细的评估分数"""
        wind_speed = params.get("wind_speed", 10)
        obstacle_count = params.get("obstacle_count", 5)

        # 挑战性分数：风速和障碍物的综合难度
        wind_challenge = min(wind_speed / 25 * 100, 100)
        obstacle_challenge = min(obstacle_count / 15 * 100, 100)
        challenge_score = (wind_challenge * 0.5 + obstacle_challenge * 0.5)

        # 多样性分数：参数的变化程度
        diversity_score = min((wind_speed / 20 + obstacle_count / 20) * 50, 100)

        # 真实性分数（固定）
        realism_score = 80

        # 有效性分数：基于配置完善程度
        effectiveness_score = 70

        # 加权总分
        total_score = (diversity_score * 0.25 + challenge_score * 0.25 +
                       realism_score * 0.25 + effectiveness_score * 0.25)

        return {
            "total": total_score,
            "diversity": diversity_score,
            "challenge": challenge_score,
            "realism": realism_score,
            "effectiveness": effectiveness_score,
        }

    def smart_adjust_params(current_params: dict, scores: dict, iteration: int, max_iterations: int, param_space: dict) -> dict:
        """根据评估分数智能调整参数"""
        new_params = current_params.copy()
        wind_range = param_space.get("wind_speed", [0, 50])
        obstacle_range = param_space.get("obstacle_count", [0, 50])

        # 学习率随迭代递减
        learning_rate = max(0.1, 1.0 - iteration / max_iterations)

        # 根据各维度分数调整参数
        total_score = scores["total"]
        challenge_score = scores["challenge"]
        diversity_score = scores["diversity"]

        # 策略1：总分低时，大幅调整
        if total_score < 40:
            # 大幅增加挑战性
            new_params["wind_speed"] = min(current_params["wind_speed"] + 5 * learning_rate, wind_range[1])
            new_params["obstacle_count"] = min(current_params["obstacle_count"] + 3 * learning_rate, obstacle_range[1])
        # 策略2：挑战性低时，增加风速和障碍物
        elif challenge_score < 50:
            new_params["wind_speed"] = min(current_params["wind_speed"] + 3 * learning_rate, wind_range[1])
            new_params["obstacle_count"] = min(current_params["obstacle_count"] + 2 * learning_rate, obstacle_range[1])
        # 策略3：多样性低时，增加参数变化
        elif diversity_score < 50:
            new_params["wind_speed"] = min(current_params["wind_speed"] + 2 * learning_rate, wind_range[1])
            new_params["obstacle_count"] = min(current_params["obstacle_count"] + 1 * learning_rate, obstacle_range[1])
        # 策略4：分数中等时，微调
        elif total_score < 70:
            # 尝试不同方向
            if random.random() > 0.5:
                new_params["wind_speed"] = max(wind_range[0], min(current_params["wind_speed"] + random.uniform(-2, 2) * learning_rate, wind_range[1]))
                new_params["obstacle_count"] = max(obstacle_range[0], min(current_params["obstacle_count"] + random.uniform(-1, 1) * learning_rate, obstacle_range[1]))
            else:
                # 尝试相反方向
                new_params["wind_speed"] = max(wind_range[0], min(current_params["wind_speed"] - random.uniform(0, 2) * learning_rate, wind_range[1]))
                new_params["obstacle_count"] = max(obstacle_range[0], min(current_params["obstacle_count"] - random.uniform(0, 1) * learning_rate, obstacle_range[1]))
        # 策略5：分数高时，小幅探索
        else:
            exploration = random.uniform(-1, 1) * learning_rate
            new_params["wind_speed"] = max(wind_range[0], min(current_params["wind_speed"] + exploration, wind_range[1]))
            new_params["obstacle_count"] = max(obstacle_range[0], min(current_params["obstacle_count"] + exploration * 0.5, obstacle_range[1]))

        # 风向随机微调
        new_params["wind_direction"] = (current_params["wind_direction"] + random.uniform(-5, 5)) % 360

        return new_params

    max_iterations = task_data.get("max_iterations", 10)
    param_space = task_data.get("param_space", {})
    best_score = 0
    best_params = {}
    score_history = []

    # 初始参数（使用参数空间的中间值）
    current_params = {
        "wind_speed": (param_space.get("wind_speed", [0, 50])[0] + param_space.get("wind_speed", [0, 50])[1]) / 2,
        "obstacle_count": (param_space.get("obstacle_count", [0, 50])[0] + param_space.get("obstacle_count", [0, 50])[1]) / 2,
        "wind_direction": (param_space.get("wind_direction", [0, 360])[0] + param_space.get("wind_direction", [0, 360])[1]) / 2,
    }

    for i in range(max_iterations):
        # 基于当前参数计算详细分数
        scores = evaluate_params_detailed(current_params)
        score = scores["total"]
        score_history.append(scores)

        if score > best_score:
            best_score = score
            best_params = current_params.copy()

        # 智能调整参数
        current_params = smart_adjust_params(current_params, scores, i, max_iterations, param_space)

        await db.execute(
            text(
                "UPDATE optimization_tasks SET current_iteration = :iteration, best_score = :best_score, best_params = :best_params WHERE id = :id"
            ),
            {"id": task_id, "iteration": i + 1, "best_score": round(best_score, 2), "best_params": json.dumps(best_params)}
        )
        await db.commit()

    await db.execute(
        text("UPDATE optimization_tasks SET status = 'completed' WHERE id = :id"),
        {"id": task_id}
    )
    await db.commit()

    # 将最优参数应用到项目中的所有环境
    project_id = task_data.get("project_id")
    if project_id and best_params:
        result = await db.execute(
            text("SELECT id, config FROM envs WHERE project_id = :project_id AND status = 'active'"),
            {"project_id": project_id}
        )
        envs = result.fetchall()

        for env in envs:
            env_id = env[0]
            env_config = json.loads(env[1]) if isinstance(env[1], str) else env[1]

            # 应用优化后的参数
            if "wind_speed" in best_params:
                env_config.setdefault("atmosphere", {})["wind_speed"] = round(best_params["wind_speed"], 2)
            if "obstacle_count" in best_params:
                env_config.setdefault("obstacles", {})["count"] = int(best_params["obstacle_count"])
            if "wind_direction" in best_params:
                env_config.setdefault("atmosphere", {})["wind_direction"] = round(best_params["wind_direction"], 2)

            # 保存更新后的配置
            await db.execute(
                text("UPDATE envs SET config = :config, updated_at = NOW() WHERE id = :id"),
                {"id": env_id, "config": json.dumps(env_config)}
            )

        await db.commit()

    return {"code": 0, "data": {"id": task_id, "status": "completed", "best_score": round(best_score, 2), "best_params": best_params}}


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

    await db.execute(
        text("DELETE FROM optimization_tasks WHERE id = :id"),
        {"id": task_id}
    )
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
                "id": t[0],
                "project_id": t[1],
                "max_iterations": t[2],
                "current_iteration": t[3],
                "status": t[4],
                "best_score": t[5],
                "created_at": str(t[6]) if t[6] else None,
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
            """
            SELECT id, project_id, param_space, weights, max_iterations, current_iteration, status, best_params, best_score, created_at
            FROM optimization_tasks WHERE id = :id
            """
        ),
        {"id": task_id}
    )
    task = result.fetchone()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Optimization task not found")

    return {
        "code": 0,
        "data": {
            "id": task[0],
            "project_id": task[1],
            "param_space": json.loads(task[2]) if isinstance(task[2], str) else task[2],
            "weights": json.loads(task[3]) if isinstance(task[3], str) else task[3],
            "max_iterations": task[4],
            "current_iteration": task[5],
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
    result = await db.execute(
        text("SELECT id, status FROM optimization_tasks WHERE id = :id"),
        {"id": task_id}
    )
    task = result.fetchone()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Optimization task not found")

    if task[1] == 'completed':
        return {"code": 0, "message": "Task already completed"}

    await db.execute(
        text("UPDATE optimization_tasks SET status = 'completed' WHERE id = :id"),
        {"id": task_id}
    )

    return {"code": 0, "message": "Optimization task stopped"}


@router.get("/optimization-reports/{report_id}")
async def get_optimization_report(
    report_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        text(
            """
            SELECT id, task_id, before_scores, after_scores, comparison_data, created_at
            FROM optimization_reports WHERE id = :id
            """
        ),
        {"id": report_id}
    )
    report = result.fetchone()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Optimization report not found")

    return {
        "code": 0,
        "data": {
            "id": report[0],
            "task_id": report[1],
            "before_scores": json.loads(report[2]) if isinstance(report[2], str) else report[2],
            "after_scores": json.loads(report[3]) if isinstance(report[3], str) else report[3],
            "comparison_data": json.loads(report[4]) if isinstance(report[4], str) else report[4],
            "created_at": str(report[5]) if report[5] else None,
        }
    }
