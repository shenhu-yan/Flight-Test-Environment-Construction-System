"""
环境优化任务 — 基于真实 DQN 训练 + 贝叶斯优化
"""
import asyncio
import json
import uuid
import numpy as np

# 任务停止标志：task_id -> True 表示应停止
_stop_flags: dict[str, bool] = {}


def request_stop(task_id: str):
    """请求停止指定优化任务。"""
    _stop_flags[task_id] = True


def is_stopped(task_id: str) -> bool:
    """检查任务是否被请求停止。"""
    return _stop_flags.get(task_id, False)


def clear_stop(task_id: str):
    """清理停止标志（任务完成后调用）。"""
    _stop_flags.pop(task_id, None)


async def _mark_task_error(db_url: str, task_id: str, error_msg: str):
    """将优化任务标记为出错状态。"""
    import asyncpg
    try:
        conn = await asyncpg.connect(db_url, timeout=5)
        await conn.execute(
            "UPDATE optimization_tasks SET status='error' WHERE id=$1",
            task_id
        )
        await conn.close()
    except Exception:
        pass


async def run_optimization_async(
    task_id: str,
    project_id: str,
    base_config: dict,
    param_space: dict,
    max_iterations: int = 10,
):
    """异步执行贝叶斯优化循环。"""
    from app.services.optimizer import BayesOptimizer
    from app.services.evaluator import build_config_from_params, evaluate_by_training
    from app.core.config import settings
    import asyncpg

    db_url = settings.DATABASE_URL.replace("+asyncpg", "")
    optimizer = BayesOptimizer()
    best_score = 0
    best_params = {}

    print(f"[Optimize] Starting task {task_id[:8]}: {max_iterations} iterations", flush=True)

    for i in range(max_iterations):
        if is_stopped(task_id):
            print(f"[Optimize] Stop requested at iter {i}", flush=True)
            break
        # 1. 优化器建议参数
        params = optimizer.suggest(param_space)

        # 2. 构建配置
        config = build_config_from_params(base_config, params)

        # 3. 训练评估（在线程池中执行）
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: evaluate_by_training(config, n_episodes=30)
        )
        score = result["score"]

        # 4. 反馈给优化器
        optimizer.observe(params, score)

        # 5. 更新最优
        if score > best_score:
            best_score = score
            best_params = params.copy()

        # 6. 更新数据库
        try:
            conn = await asyncpg.connect(db_url, timeout=5)
            await conn.execute(
                """UPDATE optimization_tasks
                   SET current_iteration=$1, best_score=$2, best_params=$3
                   WHERE id=$4""",
                i + 1, round(best_score, 2), json.dumps(best_params), task_id
            )
            await conn.close()
        except Exception as e:
            print(f"[Optimize] DB error at iter {i+1}: {e}", flush=True)

        print(f"[Optimize] Iter {i+1}/{max_iterations}: score={score:.1f}, best={best_score:.1f}", flush=True)

    # 7. 应用最优参数到环境
    print(f"[Optimize] Applying best params (score={best_score:.1f})", flush=True)
    try:
        conn = await asyncpg.connect(db_url, timeout=5)
        envs = await conn.fetch(
            "SELECT id, config FROM envs WHERE project_id=$1 AND status='active'",
            project_id
        )

        for env in envs:
            env_id = env["id"]
            old_config = json.loads(env["config"]) if isinstance(env["config"], str) else env["config"]
            new_config = build_config_from_params(old_config, best_params)

            snap_before = str(uuid.uuid4())
            await conn.execute(
                """INSERT INTO env_snapshots (id, env_id, config, trigger_type, operator, reason, created_at)
                   VALUES ($1, $2, $3, 'auto_adjust', '00000000-0000-0000-0000-000000000001', '智能优化调整', NOW())""",
                snap_before, env_id, json.dumps(old_config)
            )

            await conn.execute(
                "UPDATE envs SET config=$1, updated_at=NOW() WHERE id=$2",
                json.dumps(new_config), env_id
            )

            snap_after = str(uuid.uuid4())
            await conn.execute(
                """INSERT INTO env_snapshots (id, env_id, config, trigger_type, operator, reason, created_at)
                   VALUES ($1, $2, $3, 'auto_adjust', '00000000-0000-0000-0000-000000000001', $4, NOW())""",
                snap_after, env_id, json.dumps(new_config),
                f"优化完成，分数: {round(best_score, 2)}"
            )

            await conn.execute(
                """INSERT INTO adjustment_history (id, env_id, snapshot_before, snapshot_after, trigger_type, trigger_rule, operator, created_at)
                   VALUES ($1, $2, $3, $4, 'auto', NULL, '00000000-0000-0000-0000-000000000001', NOW())""",
                str(uuid.uuid4()), env_id, snap_before, snap_after
            )

        await conn.execute(
            "UPDATE optimization_tasks SET status='completed', best_score=$1, best_params=$2 WHERE id=$3",
            round(best_score, 2), json.dumps(best_params), task_id
        )
        await conn.close()
        print(f"[Optimize] Done! best={best_score:.1f}, applied to {len(envs)} envs", flush=True)

    except Exception as e:
        print(f"[Optimize] Apply error: {e}", flush=True)
        try:
            conn = await asyncpg.connect(db_url, timeout=5)
            await conn.execute(
                "UPDATE optimization_tasks SET status='error' WHERE id=$1", task_id
            )
            await conn.close()
        except Exception:
            pass


def run_optimization_thread(
    task_id: str,
    project_id: str,
    base_config: dict,
    param_space: dict,
    max_iterations: int = 10,
):
    """线程入口 — 创建独立事件循环运行异步优化。"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run_optimization_async(
            task_id, project_id, base_config, param_space, max_iterations
        ))
    except Exception as e:
        print(f"[Optimize] Thread error: {e}", flush=True)
        try:
            import asyncpg
            from app.core.config import settings
            db_url = settings.DATABASE_URL.replace("+asyncpg", "")
            err_loop = asyncio.new_event_loop()
            err_loop.run_until_complete(_mark_task_error(db_url, task_id, str(e)))
            err_loop.close()
        except Exception:
            pass
    finally:
        loop.close()


def run_optimization_with_training_feedback(
    task_id: str,
    project_id: str,
    env_id: str,
    base_config: dict,
    max_iterations: int = 5,
    training_id: str = None,
):
    """迭代式训练+优化：训一段 → 优化参数 → 换参数再训 → 循环。"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_iterative_train_and_optimize(
            task_id, project_id, env_id, base_config, max_iterations, training_id
        ))
    except Exception as e:
        print(f"[Iterative] Thread error: {e}", flush=True)
        # 标记任务出错，避免前端永久轮询
        try:
            import asyncpg
            from app.core.config import settings
            db_url = settings.DATABASE_URL.replace("+asyncpg", "")
            err_loop = asyncio.new_event_loop()
            err_loop.run_until_complete(_mark_task_error(db_url, task_id, str(e)))
            err_loop.close()
        except Exception:
            pass
    finally:
        loop.close()


async def _iterative_train_and_optimize(
    task_id: str,
    project_id: str,
    env_id: str,
    base_config: dict,
    n_rounds: int = 5,
    training_id: str = None,
):
    """核心循环：每轮训练 → 读结果 → 优化参数 → 应用 → 下一轮。

    每轮训练 20 个 episode，优化器根据训练结果调整参数，
    下一轮用新参数继续训练。环境随训练进程逐步进化。
    进度粒度：每 5 个 episode + 每次优化评估更新一次进度。
    """
    from app.services.optimizer import BayesOptimizer
    from app.services.evaluator import build_config_from_params, evaluate_by_training
    from app.core.config import settings
    import asyncpg

    db_url = settings.DATABASE_URL.replace("+asyncpg", "")
    loop = asyncio.get_running_loop()
    episodes_per_round = 20  # 每轮训练 episode 数（减少计算量）
    import copy
    current_config = copy.deepcopy(base_config)
    all_scores = []  # 每轮的训练分数

    # 复用贝叶斯优化器，跨轮次保留学习成果
    optimizer = BayesOptimizer()

    def _safe_range(low, high, fb_lo, fb_hi):
        return [fb_lo, fb_hi] if low >= high else [low, high]

    # 清掉旧指标
    try:
        conn = await asyncpg.connect(db_url, timeout=5)
        await conn.execute("DELETE FROM training_metrics WHERE env_id=$1", env_id)
        await conn.close()
    except Exception:
        pass

    # 创建共享 DQN（整个优化过程复用，换参数后继续训练）
    from app.services.flight_env import FlightEnv, SimpleRLTrainer
    shared_env = FlightEnv(config=current_config, max_steps=200)
    shared_trainer = SimpleRLTrainer(env=shared_env, learning_rate=0.001, gamma=0.99)

    for round_num in range(n_rounds):
        if is_stopped(task_id):
            break

        if training_id:
            from app.services.training_service import training_service
            t = training_service.active_trainings.get(training_id)
            if t:
                t["current_step"] = round_num * episodes_per_round

        print(f"\n[Round {round_num+1}/{n_rounds}] wind={current_config.get('atmosphere',{}).get('wind_speed',0):.1f} obs={current_config.get('obstacles',{}).get('count',0)}", flush=True)

        # ── 用当前参数继续训练共享 DQN ──
        # 更新环境配置（不重建 trainer，保留学到的 Q 值）
        shared_env.config = current_config
        shared_env.wind_speed = current_config.get("atmosphere", {}).get("wind_speed", 5)
        shared_env.wind_direction = current_config.get("atmosphere", {}).get("wind_direction", 90)
        shared_env.obstacle_count = current_config.get("obstacles", {}).get("count", 0)
        reward_cfg = current_config.get("reward", {})
        shared_env.distance_weight = reward_cfg.get("distance_weight", 0.5)
        shared_env.heading_weight = reward_cfg.get("heading_weight", 0.3)
        shared_env.distance_scale = reward_cfg.get("distance_scale", 300)

        # 训练并收集数据
        ep_rewards = []
        ep_successes = []
        step_offset = round_num * episodes_per_round

        # 复用单个 DB 连接（减少连接开销）
        conn = None
        try:
            conn = await asyncpg.connect(db_url, timeout=5)
        except Exception:
            pass

        for ep in range(episodes_per_round):
            if is_stopped(task_id):
                break
            obs, info = shared_env.reset()
            obs = obs.astype(np.float32)
            ep_reward = 0
            done = False
            step = 0
            min_dist = float('inf')

            while not done and step < 200:
                action, action_idx = shared_trainer._select_action(obs, info)
                next_obs, reward, terminated, truncated, info = shared_env.step(action)
                next_obs = next_obs.astype(np.float32)
                done = terminated or truncated
                shared_trainer._remember(obs, action_idx, reward, next_obs, terminated)
                shared_trainer._replay()
                obs = next_obs
                ep_reward += reward
                step += 1
                min_dist = min(min_dist, info.get("distance_to_target", 1000))

            shared_trainer.epsilon = max(shared_trainer.epsilon_min, shared_trainer.epsilon * shared_trainer.epsilon_decay)
            ep_rewards.append(ep_reward)
            ep_successes.append(min_dist < 100)

            # 保存每 episode 指标到 DB
            if conn:
                try:
                    sr = sum(ep_successes) / len(ep_successes)
                    conv = 0.5
                    if len(ep_rewards) >= 10:
                        r5 = sum(ep_rewards[-5:]) / 5
                        p5 = sum(ep_rewards[-10:-5]) / 5
                        conv = max(0.0, min(1.0, 0.5 + (r5 - p5) / 500))
                    await conn.execute(
                        """INSERT INTO training_metrics
                           (env_id, episode_reward, success_rate, convergence_speed, step, reported_at)
                           VALUES ($1, $2, $3, $4, $5, NOW())""",
                        env_id, round(ep_reward, 2), round(sr, 4), round(conv, 4), step_offset + ep + 1
                    )
                except Exception:
                    pass

            # 每 5 个 episode 更新一次子步骤进度
            if (ep + 1) % 5 == 0:
                try:
                    # 训练阶段占当前轮的前 50%，确保进度只增不减
                    sub_progress = round_num + 0.5 + (ep + 1) / episodes_per_round * 0.5
                    await conn.execute(
                        """UPDATE optimization_tasks
                           SET current_iteration = GREATEST(current_iteration, $1)
                           WHERE id=$2""",
                        round(sub_progress, 2), task_id
                    )
                except Exception:
                    pass
                await asyncio.sleep(0)  # 让出事件循环
                print(f"[Iterative] Round {round_num+1} training: {ep+1}/{episodes_per_round}", flush=True)

        # 关闭本轮训练的 DB 连接
        if conn:
            try:
                await conn.close()
            except Exception:
                pass

        # 计算本轮分数
        n = len(ep_rewards)
        success_rate = sum(ep_successes) / n if n > 0 else 0
        mean_reward = sum(ep_rewards[-10:]) / min(10, n) if n > 0 else 0
        mean_score = max(0, min(100, (mean_reward + 250) / 550 * 100))
        sr_score = success_rate * 100
        if n >= 10:
            imp = (sum(ep_rewards[-5:])/5 - sum(ep_rewards[:5])/5)
            imp_score = max(0, min(100, (imp + 300) / 600 * 100))
        else:
            imp_score = 50
        score = 0.5 * mean_score + 0.3 * sr_score + 0.2 * imp_score
        all_scores.append(score)

        print(f"  score={score:.1f} reward={mean_reward:.0f} SR={success_rate:.2f} eps={shared_trainer.epsilon:.3f}", flush=True)

        # 更新前端可追踪的训练进度
        if training_id:
            from app.services.training_service import training_service
            t = training_service.active_trainings.get(training_id)
            if t:
                t["current_step"] = (round_num + 1) * episodes_per_round
                t["metrics_history"].append({
                    "episode_reward": round(mean_reward, 2),
                    "success_rate": round(success_rate, 4),
                    "convergence_speed": round(score / 100, 4),
                    "step": (round_num + 1) * episodes_per_round,
                })

        # 更新优化任务进度（整轮完成，确保只增不减）
        try:
            conn = await asyncpg.connect(db_url, timeout=5)
            await conn.execute(
                """UPDATE optimization_tasks
                   SET current_iteration = GREATEST(current_iteration, $1),
                       best_score = GREATEST(best_score, $2)
                   WHERE id=$3""",
                round_num + 1, round(max(all_scores), 2), task_id
            )
            await conn.close()
            print(f"[Iterative] Round {round_num+1}/{n_rounds} complete", flush=True)
        except Exception:
            pass

        # ── 第二步：根据本轮结果决定优化方向 ──
        wind = current_config.get("atmosphere", {}).get("wind_speed", 10)
        obs_count = current_config.get("obstacles", {}).get("count", 5)

        if success_rate < 0.1:
            param_space = {
                "wind_speed": _safe_range(0, wind * 0.7, 0, 15),
                "obstacle_count": _safe_range(0, max(1, obs_count * 0.5), 0, 5),
                "distance_weight": [0.3, 1.0],
                "heading_weight": [0.2, 0.8],
            }
            direction = "too hard, reducing difficulty"
        elif success_rate < 0.3:
            param_space = {
                "wind_speed": _safe_range(max(0, wind * 0.5), min(50, wind * 1.5), 0, 30),
                "obstacle_count": _safe_range(0, min(20, obs_count + 5), 0, 15),
                "distance_weight": [0.1, 1.0],
                "heading_weight": [0.1, 0.8],
            }
            direction = "learning, fine-tuning"
        else:
            param_space = {
                "wind_speed": _safe_range(wind, min(50, wind * 1.8), 5, 40),
                "obstacle_count": _safe_range(obs_count, min(30, obs_count * 1.5 + 2), 2, 20),
                "distance_weight": [0.1, 0.7],
                "heading_weight": [0.1, 0.5],
            }
            direction = "doing well, can increase challenge"

        print(f"[Iterative] Assessment: {direction}", flush=True)

        # ── 第三步：贝叶斯优化搜索更好的参数（5轮评估，每轮20 episodes）──
        best_params = {}
        best_eval_score = 0
        n_evals = 5
        n_eval_eps = 20  # 减少评估 episode 数
        for opt_i in range(n_evals):
            if is_stopped(task_id):
                break
            params = optimizer.suggest(param_space)
            eval_config = build_config_from_params(current_config, params)
            eval_result = await loop.run_in_executor(
                None, lambda cfg=eval_config: evaluate_by_training(cfg, n_episodes=n_eval_eps)
            )
            optimizer.observe(params, eval_result["score"])
            if eval_result["score"] > best_eval_score:
                best_eval_score = eval_result["score"]
                best_params = params.copy()

            # 更新子步骤进度：优化评估占当前轮的后 50%，确保进度只增不减
            sub_progress = round_num + 1.0 + (opt_i + 1) / n_evals * 0.5
            try:
                conn = await asyncpg.connect(db_url, timeout=5)
                await conn.execute(
                    """UPDATE optimization_tasks
                       SET current_iteration = GREATEST(current_iteration, $1)
                       WHERE id=$2""",
                    round(sub_progress, 2), task_id
                )
                await conn.close()
            except Exception:
                pass

            await asyncio.sleep(0)  # 让出事件循环
            print(f"[Iterative]   Opt eval {opt_i+1}/{n_evals}: score={eval_result['score']:.1f}", flush=True)

        # ── 第四步：应用优化后的参数 ──
        if best_params:
            new_config = build_config_from_params(current_config, best_params)

            # 保存快照
            try:
                conn = await asyncpg.connect(db_url, timeout=5)
                snap_before = str(uuid.uuid4())
                await conn.execute(
                    """INSERT INTO env_snapshots (id, env_id, config, trigger_type, operator, reason, created_at)
                       VALUES ($1, $2, $3, 'auto_adjust', '00000000-0000-0000-0000-000000000001', $4, NOW())""",
                    snap_before, env_id, json.dumps(current_config),
                    f"Round {round_num+1} 优化前 (SR={success_rate:.2f})"
                )
                await conn.execute(
                    "UPDATE envs SET config=$1, updated_at=NOW() WHERE id=$2",
                    json.dumps(new_config), env_id
                )
                snap_after = str(uuid.uuid4())
                await conn.execute(
                    """INSERT INTO env_snapshots (id, env_id, config, trigger_type, operator, reason, created_at)
                       VALUES ($1, $2, $3, 'auto_adjust', '00000000-0000-0000-0000-000000000001', $4, NOW())""",
                    snap_after, env_id, json.dumps(new_config),
                    f"Round {round_num+1} 优化后 (best_eval={best_eval_score:.1f})"
                )
                await conn.execute(
                    """INSERT INTO adjustment_history (id, env_id, snapshot_before, snapshot_after, trigger_type, trigger_rule, operator, created_at)
                       VALUES ($1, $2, $3, $4, 'auto', NULL, '00000000-0000-0000-0000-000000000001', NOW())""",
                    str(uuid.uuid4()), env_id, snap_before, snap_after
                )
                await conn.close()
            except Exception:
                pass

            current_config = new_config
            changed = [f"{k}={v:.2f}" for k, v in best_params.items()]
            print(f"[Iterative] Applied: {', '.join(changed)}", flush=True)
        else:
            print(f"[Iterative] No improvement found, keeping current params", flush=True)

    # ── 完成 ──
    try:
        conn = await asyncpg.connect(db_url, timeout=5)
        await conn.execute(
            "UPDATE optimization_tasks SET status='completed', best_score=$1 WHERE id=$2",
            round(max(all_scores), 2), task_id
        )
        await conn.close()
    except Exception:
        pass

    # 标记训练完成（前端可感知）
    if training_id:
        from app.services.training_service import training_service
        t = training_service.active_trainings.get(training_id)
        if t:
            t["status"] = "completed"
            t["current_step"] = n_rounds * episodes_per_round

    print(f"\n[Iterative] Done! {n_rounds} rounds completed.", flush=True)
    print(f"[Iterative] Score trend: {' → '.join([f'{s:.0f}' for s in all_scores])}", flush=True)
