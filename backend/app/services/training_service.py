"""
训练服务 - 在服务器端执行训练任务
"""

import asyncio
import json
import time
import random
import math
from typing import Optional
from sqlalchemy import text
from app.core.database import async_session


class TrainingService:
    def __init__(self):
        self.active_trainings: dict[str, dict] = {}

    async def start_training(
        self,
        env_id: str,
        project_id: str,
        config: dict,
        max_steps: int = 1000,
        user_id: str = None
    ) -> dict:
        """启动训练任务"""
        import uuid
        training_id = str(uuid.uuid4())

        self.active_trainings[training_id] = {
            "env_id": env_id,
            "project_id": project_id,
            "config": config,
            "max_steps": max_steps,
            "current_step": 0,
            "status": "running",
            "metrics_history": [],
            "user_id": user_id,
            "learning_rate": 0.1,
            "exploration_rate": 0.3,
        }

        asyncio.create_task(self._run_training(training_id))

        return {
            "training_id": training_id,
            "status": "running",
            "max_steps": max_steps,
        }

    async def _run_training(self, training_id: str):
        """执行训练任务"""
        training = self.active_trainings.get(training_id)
        if not training:
            return

        env_id = training["env_id"]
        project_id = training["project_id"]
        max_steps = training["max_steps"]

        # 初始化训练状态
        episode_reward = 0
        success_count = 0
        best_reward = -float('inf')
        consecutive_successes = 0

        # 获取环境配置中的难度系数
        config = training["config"]
        wind_speed = config.get("atmosphere", {}).get("wind_speed", 5)
        obstacle_count = config.get("obstacles", {}).get("count", 0)
        difficulty_factor = 1.0 + (wind_speed / 20) + (obstacle_count / 10)

        for step in range(1, max_steps + 1):
            if training["status"] != "running":
                break

            # 模拟训练步骤 - 随着训练进行，动作质量逐渐提高
            exploration = training["exploration_rate"] * math.exp(-step / 500)
            if random.random() < exploration:
                # 探索：随机动作
                action = [random.uniform(-1, 1) for _ in range(3)]
            else:
                # 利用：基于经验的动作
                noise = random.gauss(0, 0.3)
                action = [
                    max(-1, min(1, 0.5 + noise)),
                    max(-1, min(1, 0.3 + noise)),
                    max(-1, min(1, 0.2 + noise))
                ]

            # 计算奖励 - 基于动作质量和环境难度
            reward = self._calculate_reward(action, config, step, difficulty_factor)
            episode_reward += reward

            # 判断是否成功 - 奖励超过阈值视为成功
            success_threshold = 0.3 / difficulty_factor
            is_success = reward > success_threshold

            if is_success:
                success_count += 1
                consecutive_successes += 1
            else:
                consecutive_successes = 0

            # 计算指标
            success_rate = success_count / step
            convergence_speed = min(0.2 + step * 0.002 + success_rate * 0.3, 1.0)

            # 根据连续成功次数调整学习率
            if consecutive_successes > 5:
                training["learning_rate"] = min(training["learning_rate"] * 1.1, 0.5)
            elif consecutive_successes == 0 and step > 100:
                training["learning_rate"] = max(training["learning_rate"] * 0.9, 0.01)

            metrics = {
                "episode_reward": round(episode_reward, 2),
                "success_rate": round(success_rate, 4),
                "convergence_speed": round(convergence_speed, 4),
                "step": step,
            }

            # 记录指标
            training["current_step"] = step
            training["metrics_history"].append(metrics)

            # 保存到数据库
            await self._save_metrics(env_id, metrics)

            # 每10步更新一次状态
            if step % 10 == 0:
                await self._notify_progress(project_id, env_id, metrics)

            # 模拟训练延迟
            await asyncio.sleep(0.02)

        training["status"] = "completed"
        await self._notify_complete(project_id, env_id)

    def _calculate_reward(self, action: list, config: dict, step: int, difficulty_factor: float) -> float:
        """计算奖励 - 更真实的奖励函数"""
        # 基础奖励：动作的协调性
        action_sum = sum(action)
        action_variance = sum((a - action_sum/len(action))**2 for a in action) / len(action)
        coordination_reward = 1.0 - min(action_variance, 1.0)

        # 高度奖励：保持适当高度
        altitude_reward = 0.5 + 0.5 * math.sin(step * 0.01)

        # 速度奖励：适当的速度
        speed = math.sqrt(sum(a**2 for a in action))
        speed_reward = 1.0 - abs(speed - 0.5) * 2

        # 难度惩罚：环境越难，奖励越低
        difficulty_penalty = 1.0 / difficulty_factor

        # 总奖励
        total_reward = (coordination_reward * 0.4 + altitude_reward * 0.3 + speed_reward * 0.3) * difficulty_penalty

        # 添加噪声使训练更真实
        noise = random.gauss(0, 0.1)
        total_reward = max(0, total_reward + noise)

        return total_reward

    async def _save_metrics(self, env_id: str, metrics: dict):
        """保存指标到数据库"""
        async with async_session() as session:
            await session.execute(
                text(
                    """
                    INSERT INTO training_metrics (env_id, episode_reward, success_rate, convergence_speed, step, reported_at)
                    VALUES (:env_id, :episode_reward, :success_rate, :convergence_speed, :step, NOW())
                    """
                ),
                {
                    "env_id": env_id,
                    "episode_reward": metrics["episode_reward"],
                    "success_rate": metrics["success_rate"],
                    "convergence_speed": metrics["convergence_speed"],
                    "step": metrics["step"],
                }
            )
            await session.commit()

    async def _notify_progress(self, project_id: str, env_id: str, metrics: dict):
        """通知前端训练进度"""
        from app.services.ws_manager import manager
        await manager.broadcast_metrics(project_id, {
            "env_id": env_id,
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def _notify_complete(self, project_id: str, env_id: str):
        """通知前端训练完成"""
        from app.services.ws_manager import manager
        await manager.broadcast_notification(project_id, {
            "type": "info",
            "title": "训练完成",
            "content": f"环境 {env_id} 的训练已完成"
        })

    def stop_training(self, training_id: str):
        """停止训练"""
        if training_id in self.active_trainings:
            self.active_trainings[training_id]["status"] = "stopped"

    def get_training_status(self, training_id: str) -> Optional[dict]:
        """获取训练状态"""
        return self.active_trainings.get(training_id)


from datetime import datetime

training_service = TrainingService()
