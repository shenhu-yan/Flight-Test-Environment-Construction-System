"""
训练服务 - 使用真正的强化学习训练
"""

import asyncio
import json
import math
import uuid
import numpy as np
from typing import Optional
from datetime import datetime
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
        """启动真正的RL训练任务"""
        # 同一环境只允许一个训练：停掉旧的
        for tid, t in list(self.active_trainings.items()):
            if t["env_id"] == env_id and t["status"] == "running":
                t["status"] = "stopped"

        training_id = str(uuid.uuid4())
        n_episodes = max(300, max_steps // 5)

        self.active_trainings[training_id] = {
            "env_id": env_id,
            "project_id": project_id,
            "config": config,
            "max_steps": max_steps,
            "n_episodes": n_episodes,
            "current_step": 0,
            "status": "running",
            "metrics_history": [],
            "user_id": user_id,
        }

        # 在主 event loop 中异步运行训练（不阻塞，因为训练内部有 asyncio.sleep）
        asyncio.create_task(self._run_rl_training(training_id))

        return {
            "training_id": training_id,
            "status": "running",
            "max_steps": max_steps,
        }

    async def _run_rl_training(self, training_id: str):
        """执行真正的RL训练"""
        from app.services.flight_env import FlightEnv, SimpleRLTrainer

        training = self.active_trainings.get(training_id)
        if not training:
            return

        env_id = training["env_id"]
        project_id = training["project_id"]
        config = training["config"]
        max_steps = training["max_steps"]

        print(f"[Training] Starting RL training for env {env_id}")

        try:
            env = FlightEnv(config=config, max_steps=max_steps)
            trainer = SimpleRLTrainer(env=env, learning_rate=0.001, gamma=0.99)

            n_episodes = max(300, max_steps // 5)
            print(f"[Training] Running {n_episodes} episodes, max_steps={max_steps}")

            for episode in range(n_episodes):
                training = self.active_trainings.get(training_id)
                if not training:
                    print(f"[Training] Training removed, stopping")
                    break
                if training.get("status", "running") != "running":
                    print(f"[Training] Status changed to {training.get('status')}, stopping")
                    break

                obs, info = env.reset()
                obs = obs.astype(np.float32)
                episode_reward = 0
                done = False
                step = 0
                max_steps_per_episode = 200
                min_distance = float('inf')

                while not done and step < max_steps_per_episode:
                    action, action_idx = trainer._select_action(obs, info)
                    next_obs, reward, terminated, truncated, info = env.step(action)
                    done = terminated or truncated
                    trainer._remember(obs.astype(np.float32), action_idx, reward,
                                      next_obs.astype(np.float32), terminated)
                    trainer._replay()
                    obs = next_obs
                    episode_reward += reward
                    step += 1
                    min_distance = min(min_distance, info.get("distance_to_target", 1000))
                    await asyncio.sleep(0.002)

                trainer.epsilon = max(trainer.epsilon_min, trainer.epsilon * trainer.epsilon_decay)
                training["current_step"] = episode + 1

                # 成功率
                success = 1 if min_distance < 100 else 0
                if '_total_successes' not in training:
                    training['_total_successes'] = 0
                    training['_total_episodes'] = 0
                training['_total_successes'] += success
                training['_total_episodes'] += 1
                success_rate = training['_total_successes'] / training['_total_episodes']

                # 收敛速度
                if '_reward_history' not in training:
                    training['_reward_history'] = []
                training['_reward_history'].append(episode_reward)
                raw_conv = 0.5
                if len(training['_reward_history']) >= 10:
                    recent_avg = sum(training['_reward_history'][-5:]) / 5
                    earlier_avg = sum(training['_reward_history'][-10:-5]) / 5
                    diff = recent_avg - earlier_avg
                    reward_std = float(np.std(training['_reward_history'])) if len(training['_reward_history']) > 1 else 1.0
                    scale = max(reward_std * 2.0, 10.0)
                    raw_conv = 1.0 / (1.0 + math.exp(-diff / scale))
                if '_conv_ema' not in training:
                    training['_conv_ema'] = 0.5
                training['_conv_ema'] = 0.3 * raw_conv + 0.7 * training['_conv_ema']
                convergence_speed = training['_conv_ema']

                metrics = {
                    "episode_reward": round(episode_reward, 2),
                    "success_rate": round(success_rate, 4),
                    "convergence_speed": round(convergence_speed, 4),
                    "step": episode + 1,
                }
                training["metrics_history"].append(metrics)

                # 保存到数据库（用项目的 async session）
                await self._save_metrics(env_id, metrics)
                await self._notify_progress(project_id, env_id, metrics)

                # 实时策略检查：将指标送入规则引擎，自动触发环境调整
                try:
                    from app.services.strategy_engine import strategy_engine
                    await strategy_engine.process_metric(project_id, env_id, {
                        "episode_reward": episode_reward,
                        "success_rate": success_rate,
                        "convergence_speed": convergence_speed,
                        "step": episode + 1,
                    })
                except Exception as e:
                    print(f"[Training] Strategy engine error: {e}", flush=True)

                if (episode + 1) % 20 == 0:
                    print(f"[Training] Ep {episode+1}/{n_episodes}: rew={episode_reward:.0f} SR={success_rate:.3f}")

                await asyncio.sleep(0.05)

            # 训练完成
            training["status"] = "completed"
            print(f"[Training] Completed: {n_episodes} episodes")
            await self._notify_complete(project_id, env_id)
            env.close()

        except Exception as e:
            training["status"] = "error"
            print(f"Training error: {e}")
            import traceback
            traceback.print_exc()

    async def _save_metrics(self, env_id: str, metrics: dict):
        """保存指标到数据库 - 重试3次"""
        from app.core.config import settings
        import asyncpg
        db_url = settings.DATABASE_URL.replace("+asyncpg", "")
        for attempt in range(3):
            try:
                conn = await asyncpg.connect(db_url, timeout=5)
                await conn.execute(
                    """INSERT INTO training_metrics
                       (env_id, episode_reward, success_rate, convergence_speed, step, reported_at)
                       VALUES ($1, $2, $3, $4, $5, NOW())""",
                    env_id, metrics["episode_reward"], metrics["success_rate"],
                    metrics["convergence_speed"], metrics["step"])
                await conn.close()
                return  # success
            except Exception as e:
                if attempt < 2:
                    await asyncio.sleep(0.5)
                else:
                    print(f"[Training] DB save failed after 3 attempts: {e}", flush=True)

    async def _notify_progress(self, project_id: str, env_id: str, metrics: dict):
        """通知前端训练进度"""
        try:
            from app.services.ws_manager import manager
            await manager.broadcast_metrics(project_id, {
                "env_id": env_id,
                "metrics": metrics,
                "timestamp": datetime.utcnow().isoformat()
            })
        except Exception as e:
            pass

    async def _notify_complete(self, project_id: str, env_id: str):
        """通知前端训练完成"""
        try:
            from app.services.ws_manager import manager
            await manager.broadcast_notification(project_id, {
                "type": "info",
                "title": "RL训练完成",
                "content": f"环境 {env_id} 的强化学习训练已完成"
            })
        except Exception as e:
            pass

    def stop_training(self, training_id: str):
        """停止训练"""
        if training_id in self.active_trainings:
            self.active_trainings[training_id]["status"] = "stopped"

    def get_training_status(self, training_id: str) -> Optional[dict]:
        """获取训练状态"""
        training = self.active_trainings.get(training_id)
        if training:
            n_episodes = training.get("n_episodes", max(300, training["max_steps"] // 5))
            return {
                "training_id": training_id,
                "status": training["status"],
                "current_step": training["current_step"],
                "max_steps": n_episodes,
                "progress": min(100, training["current_step"] / max(n_episodes, 1) * 100),
                "latest_metrics": training["metrics_history"][-1] if training["metrics_history"] else None,
            }
        return None

    def stop_all_trainings(self):
        """停止所有训练"""
        for training_id in list(self.active_trainings.keys()):
            self.stop_training(training_id)


training_service = TrainingService()
