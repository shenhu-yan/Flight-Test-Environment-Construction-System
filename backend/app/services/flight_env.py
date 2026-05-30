"""
真正的飞行试验环境 - Gymnasium 兼容
"""

import gymnasium as gym
from gymnasium import spaces
import numpy as np
import math
from typing import Optional, Tuple


class FlightEnv(gym.Env):
    """
    固定翼飞行器训练环境

    观测空间：
    - 高度 (归一化)
    - 速度 (归一化)
    - 航向角 (归一化)
    - 俯仰角 (归一化)
    - 横滚角 (归一化)
    - 风速 (归一化)
    - 到目标距离 (归一化)

    动作空间：
    - 油门 (-1 到 1)
    - 升降舵 (-1 到 1)
    - 副翼 (-1 到 1)
    """

    metadata = {"render_modes": ["human"], "render_fps": 30}

    def __init__(self, config: dict = None, max_steps: int = 1000):
        super().__init__()

        self.config = config or {}
        self.max_steps = max_steps

        # 从配置中读取参数
        self.wind_speed = self.config.get("atmosphere", {}).get("wind_speed", 5.0)
        self.wind_direction = self.config.get("atmosphere", {}).get("wind_direction", 90.0)
        self.obstacle_count = self.config.get("obstacles", {}).get("count", 0)
        self.terrain_type = self.config.get("terrain", {}).get("type", "flat")

        # 着陆区配置
        landing_cfg = self.config.get("landing", {})
        self.landing_type = landing_cfg.get("type", "runway")  # runway / carrier
        self.landing_width = landing_cfg.get("width", 100.0)   # 着陆区宽度(m)
        self.landing_length = landing_cfg.get("length", 200.0)  # 着陆区长度(m)

        # 阵风配置
        gust_cfg = self.config.get("gusts", {})
        self.gust_enabled = gust_cfg.get("enabled", False)
        self.gust_strength = gust_cfg.get("strength", 5.0)    # 阵风强度(m/s)
        self.gust_frequency = gust_cfg.get("frequency", 0.05)  # 每步触发概率

        # 移动障碍物配置
        moving_cfg = self.config.get("moving_obstacles", {})
        self.moving_obstacle_count = moving_cfg.get("count", 0)
        self.moving_obstacle_speed = moving_cfg.get("speed", 5.0)  # m/s
        self._moving_obstacles = []  # 运行时障碍物位置

        # 动作空间：[油门, 升降舵, 副翼]
        self.action_space = spaces.Box(
            low=np.array([-1.0, -1.0, -1.0]),
            high=np.array([1.0, 1.0, 1.0]),
            dtype=np.float32
        )

        # 观测空间：[高度, 速度, 航向偏差, 俯仰, 横滚, 目标距离, 风速]
        self.observation_space = spaces.Box(
            low=np.array([-1.0, -1.0, -1.0, -1.0, -1.0, 0.0, 0.0]),
            high=np.array([1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]),
            dtype=np.float32
        )

        # 飞行状态
        self.altitude = 100.0  # 高度 (m)
        self.velocity = 20.0   # 速度 (m/s)
        self.heading = 0.0     # 航向角 (度)
        self.pitch = 0.0       # 俯仰角 (度)
        self.roll = 0.0        # 横滚角 (度)
        self.position = np.array([0.0, 0.0])  # 水平位置 (x, y)

        # 目标位置
        self.target_position = np.array([500.0, 500.0])

        # 时间步
        self.current_step = 0

        # 奖励函数参数（可被优化器调整）
        reward_cfg = self.config.get("reward", {})
        self.reward_items = reward_cfg.get("items", [])
        self.penalty_items = reward_cfg.get("penalties", [])
        self.distance_scale = reward_cfg.get("distance_scale", 300.0)
        self.distance_weight = reward_cfg.get("distance_weight", 0.5)
        self.heading_weight = reward_cfg.get("heading_weight", 0.3)
        self.goal_bonus = reward_cfg.get("goal_bonus", 300.0)

    def reset(
        self,
        seed: Optional[int] = None,
        options: Optional[dict] = None
    ) -> Tuple[np.ndarray, dict]:
        super().reset(seed=seed)

        # 随机初始状态
        self.altitude = self.np_random.uniform(50, 200)
        self.velocity = self.np_random.uniform(15, 30)
        self.pitch = self.np_random.uniform(-5, 5)
        self.roll = self.np_random.uniform(-10, 10)
        self.position = np.array([
            self.np_random.uniform(-100, 100),
            self.np_random.uniform(-100, 100)
        ])

        # 随机目标位置
        self.target_position = np.array([
            self.np_random.uniform(200, 800),
            self.np_random.uniform(200, 800)
        ])

        # 初始航向大致朝向目标（±45° 噪声）
        target_vec = self.target_position - self.position
        target_heading = math.degrees(math.atan2(target_vec[1], target_vec[0])) % 360
        self.heading = (target_heading + self.np_random.uniform(-45, 45)) % 360

        # 初始化移动障碍物（在目标附近随机位置，随机方向移动）
        self._moving_obstacles = []
        for _ in range(self.moving_obstacle_count):
            obs_pos = self.target_position + np.array([
                self.np_random.uniform(-200, 200),
                self.np_random.uniform(-200, 200)
            ])
            obs_dir = self.np_random.uniform(0, 2 * math.pi)
            obs_vel = np.array([math.cos(obs_dir), math.sin(obs_dir)]) * self.moving_obstacle_speed
            self._moving_obstacles.append({"pos": obs_pos, "vel": obs_vel})

        self.current_step = 0

        observation = self._get_observation()
        info = self._get_info()

        return observation, info

    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, bool, dict]:
        self.current_step += 1

        # 解析动作
        throttle = float(np.clip(action[0], -1, 1))
        elevator = float(np.clip(action[1], -1, 1))
        aileron = float(np.clip(action[2], -1, 1))

        # 更新飞行状态（简化物理模型）
        self._update_physics(throttle, elevator, aileron)

        # 计算奖励
        reward = self._calculate_reward(action)

        # 检查终止条件
        terminated = self._check_terminated()
        truncated = self.current_step >= self.max_steps

        observation = self._get_observation()
        info = self._get_info()

        return observation, reward, terminated, truncated, info

    def _update_physics(self, throttle: float, elevator: float, aileron: float):
        """更新飞行物理状态"""
        dt = 0.5  # 时间步长

        # 油门影响速度（最低速度降至 2 m/s 以允许减速接近目标）
        speed_change = throttle * 10.0 * dt
        self.velocity = np.clip(self.velocity + speed_change, 2, 60)

        # 升降舵影响俯仰角
        pitch_rate = elevator * 15.0 * dt
        self.pitch = np.clip(self.pitch + pitch_rate, -30, 30)

        # 副翼影响横滚角（增大响应）
        roll_rate = aileron * 25.0 * dt
        self.roll = np.clip(self.roll + roll_rate, -60, 60)

        # 俯仰角影响高度
        altitude_change = self.velocity * math.sin(math.radians(self.pitch)) * dt
        self.altitude = np.clip(self.altitude + altitude_change, 0, 500)

        # 航向变化（增大航向响应，让转向更灵敏）
        heading_rate = math.tan(math.radians(self.roll)) * 9.81 / max(self.velocity, 5.0)
        self.heading = (self.heading + math.degrees(heading_rate) * dt) % 360

        # 更新水平位置
        heading_rad = math.radians(self.heading)
        self.position[0] += self.velocity * math.cos(heading_rad) * dt
        self.position[1] += self.velocity * math.sin(heading_rad) * dt

        # 稳态风的影响
        wind_effect_x = self.wind_speed * math.cos(math.radians(self.wind_direction)) * 0.1
        wind_effect_y = self.wind_speed * math.sin(math.radians(self.wind_direction)) * 0.1
        self.position[0] += wind_effect_x * dt
        self.position[1] += wind_effect_y * dt

        # 阵风影响（随机突变风力）
        if self.gust_enabled and self.np_random.random() < self.gust_frequency:
            gust_angle = self.np_random.uniform(0, 2 * math.pi)
            gust_x = self.gust_strength * math.cos(gust_angle) * 0.3
            gust_y = self.gust_strength * math.sin(gust_angle) * 0.3
            self.position[0] += gust_x * dt
            self.position[1] += gust_y * dt
            # 阵风也影响航向
            self.heading = (self.heading + self.np_random.uniform(-5, 5)) % 360

        # 更新移动障碍物位置（在目标附近来回移动）
        for obs in self._moving_obstacles:
            obs["pos"] += obs["vel"] * dt
            # 碰到边界反弹
            for dim in range(2):
                if abs(obs["pos"][dim] - self.target_position[dim]) > 250:
                    obs["vel"][dim] *= -1

    def _get_observation(self) -> np.ndarray:
        """获取观测值 - 包含相对目标信息，便于 agent 学习"""
        # 归一化观测值
        norm_altitude = (self.altitude - 250) / 250  # -1 到 1
        norm_velocity = (self.velocity - 30) / 20    # -1 到 1
        norm_pitch = self.pitch / 30                  # -1 到 1
        norm_roll = self.roll / 45                    # -1 到 1

        # 到目标距离（归一化）
        distance = np.linalg.norm(self.position - self.target_position)
        norm_distance = min(distance / 1000, 1.0)

        # 相对航向偏差（-1 到 1）：正=目标在右，负=目标在左
        target_vec = self.target_position - self.position
        target_heading = math.degrees(math.atan2(target_vec[1], target_vec[0])) % 360
        signed_diff = (target_heading - self.heading + 180) % 360 - 180  # -180 ~ +180
        norm_heading_error = signed_diff / 180.0  # -1 到 1

        # 风速影响（归一化到 0~1）
        wind_effect = min(self.wind_speed / 50.0, 1.0)

        return np.array([
            norm_altitude,
            norm_velocity,
            norm_heading_error,  # 核心：目标在哪个方向
            norm_pitch,
            norm_roll,
            norm_distance,       # 核心：离目标多远
            wind_effect,
        ], dtype=np.float32)

    def _get_info(self) -> dict:
        """获取附加信息"""
        distance = np.linalg.norm(self.position - self.target_position)
        return {
            "altitude": self.altitude,
            "velocity": self.velocity,
            "heading": self.heading,
            "pitch": self.pitch,
            "roll": self.roll,
            "position": self.position.tolist(),
            "target_position": self.target_position.tolist(),
            "distance_to_target": distance,
            "step": self.current_step,
        }

    def _calculate_reward(self, action: np.ndarray) -> float:
        """计算奖励 - 稀疏主导 + 轻量引导

        设计原则：
        - 成功 episode 总奖励显著为正（目标大奖主导）
        - 失败 episode 总奖励为负（时间惩罚 + 终止惩罚主导）
        - 密集引导奖励仅作辅助，不淹没主要信号
        """
        reward = 0.0

        distance = np.linalg.norm(self.position - self.target_position)

        # ── 时间惩罚：鼓励尽快到达目标 ──
        reward -= 1.0

        # ── 距离引导（轻量）：越近越好 ──
        distance_reward = math.exp(-distance / self.distance_scale)  # 0~1
        reward += distance_reward * self.distance_weight

        # ── 航向引导（轻量）：朝向目标 ──
        target_vec = self.target_position - self.position
        target_heading = math.degrees(math.atan2(target_vec[1], target_vec[0])) % 360
        heading_diff = abs(self.heading - target_heading)
        if heading_diff > 180:
            heading_diff = 360 - heading_diff
        heading_reward = 1.0 - heading_diff / 180.0
        reward += heading_reward * self.heading_weight

        # ── 接近目标递增奖励（距离<200m）──
        if distance < 200:
            reward += (200 - distance) / 200.0 * 2.0

        # ── 减速接近奖励：距离<200m 且速度低时额外加分 ──
        if distance < 200:
            speed_factor = max(0, 1.0 - self.velocity / 30.0)  # 速度越低分越高
            reward += speed_factor * 3.0

        # ── 到达着陆区：成功的核心信号 ──
        landing_radius = self.landing_width / 2.0  # 着陆区半径
        if distance < landing_radius:
            # 航母着陆额外加成（更难）
            carrier_bonus = 1.5 if self.landing_type == "carrier" else 1.0
            reward += self.goal_bonus * carrier_bonus

        # ── 移动障碍物碰撞检测 ──
        for obs in self._moving_obstacles:
            obs_dist = np.linalg.norm(self.position - obs["pos"])
            if obs_dist < 15:  # 碰撞半径 15m
                reward -= 50.0
                break

        # ── 终止惩罚 ──
        if self.altitude <= 0:
            reward -= 100.0
        if abs(self.position[0]) > 2000 or abs(self.position[1]) > 2000:
            reward -= 100.0

        # ── 动作平滑惩罚（极轻）──
        action_penalty = np.sum(np.abs(action)) * 0.02
        reward -= action_penalty

        # ── 用户自定义奖励项 ──
        for item in self.reward_items:
            coefficient = item.get("coefficient", 1.0)
            name = item.get("name", "")
            if name == "altitude_reward":
                altitude_reward = 1.0 - abs(self.altitude - 100) / 200
                reward += altitude_reward * coefficient * 0.3
            elif name == "speed_reward":
                speed_reward = 1.0 - abs(self.velocity - 25) / 20
                reward += speed_reward * coefficient * 0.3
            elif name == "distance_reward":
                reward += distance_reward * coefficient * 0.3

        # ── 用户自定义惩罚项 ──
        for item in self.penalty_items:
            coefficient = abs(item.get("coefficient", -1.0))
            name = item.get("name", "")
            if name == "collision_penalty" and self.altitude < 10:
                reward -= coefficient * 0.5
            elif name == "instability_penalty":
                stability_penalty = (abs(self.pitch) + abs(self.roll)) / 100.0
                reward -= stability_penalty * coefficient * 0.3

        return float(reward)

    def _check_terminated(self) -> bool:
        """检查是否终止"""
        # 碰撞地面
        if self.altitude <= 0:
            return True

        # 飞出边界
        if abs(self.position[0]) > 2000 or abs(self.position[1]) > 2000:
            return True

        # 到达着陆区
        distance = np.linalg.norm(self.position - self.target_position)
        landing_radius = self.landing_width / 2.0
        if distance < landing_radius:
            return True

        # 撞到移动障碍物
        for obs in self._moving_obstacles:
            if np.linalg.norm(self.position - obs["pos"]) < 15:
                return True

        return False

    def render(self):
        """渲染环境（文本模式）"""
        print(f"Step: {self.current_step}")
        print(f"Altitude: {self.altitude:.1f}m")
        print(f"Velocity: {self.velocity:.1f}m/s")
        print(f"Position: {self.position}")
        print(f"Target: {self.target_position}")
        print(f"Distance: {np.linalg.norm(self.position - self.target_position):.1f}m")

    def close(self):
        pass


class SimpleRLTrainer:
    """
    DQN 训练器 - 纯 NumPy 实现，无 PyTorch 依赖
    使用经验回放 + 目标网络 + 梯度裁剪
    """

    def __init__(self, env: FlightEnv, learning_rate: float = 0.001, gamma: float = 0.99):
        self.env = env
        self.learning_rate = learning_rate
        self.gamma = gamma

        # 离散化动作空间：10个动作
        self.discrete_actions = [
            np.array([0.5, 0.0, -0.8]),    # 0: 急左转
            np.array([0.5, 0.0, -0.3]),    # 1: 缓左转
            np.array([0.5, 0.0, 0.0]),     # 2: 直飞
            np.array([0.5, 0.0, 0.3]),     # 3: 缓右转
            np.array([0.5, 0.0, 0.8]),     # 4: 急右转
            np.array([0.8, 0.0, 0.0]),     # 5: 加速直飞
            np.array([0.2, 0.0, 0.0]),     # 6: 减速直飞
            np.array([0.05, 0.0, -0.3]),   # 7: 慢速左转
            np.array([0.05, 0.0, 0.0]),    # 8: 滑行/悬停
            np.array([0.05, 0.0, 0.3]),    # 9: 慢速右转
        ]
        self.n_actions = len(self.discrete_actions)

        # 神经网络：7 → 64 → 64 → 10
        self.obs_dim = 7
        self.h1 = 64
        self.h2 = 64
        self._init_network()

        # 探索参数
        self.epsilon = 1.0
        self.epsilon_min = 0.05
        self.epsilon_decay = 0.995

        # 经验回放（用 deque 自动淘汰旧数据，O(1)）
        from collections import deque
        self.memory = deque(maxlen=10000)
        self.batch_size = 64

        # 目标网络同步频率
        self.target_update_freq = 50
        self.train_step_count = 0

    def _init_network(self):
        """初始化在线网络和目标网络（He 初始化）"""
        scale1 = np.sqrt(2.0 / self.obs_dim)
        scale2 = np.sqrt(2.0 / self.h1)
        scale3 = np.sqrt(2.0 / self.h2)

        self.online_w1 = np.random.randn(self.obs_dim, self.h1).astype(np.float32) * scale1
        self.online_b1 = np.zeros(self.h1, dtype=np.float32)
        self.online_w2 = np.random.randn(self.h1, self.h2).astype(np.float32) * scale2
        self.online_b2 = np.zeros(self.h2, dtype=np.float32)
        self.online_w3 = np.random.randn(self.h2, self.n_actions).astype(np.float32) * scale3
        self.online_b3 = np.zeros(self.n_actions, dtype=np.float32)

        # 目标网络 = 在线网络的副本
        self.target_w1 = self.online_w1.copy()
        self.target_b1 = self.online_b1.copy()
        self.target_w2 = self.online_w2.copy()
        self.target_b2 = self.online_b2.copy()
        self.target_w3 = self.online_w3.copy()
        self.target_b3 = self.online_b3.copy()

    def _forward(self, x, w1, b1, w2, b2, w3, b3):
        """前向传播，返回每层激活值用于反向传播"""
        z1 = x @ w1 + b1
        a1 = np.maximum(0, z1)  # ReLU
        z2 = a1 @ w2 + b2
        a2 = np.maximum(0, z2)  # ReLU
        q = a2 @ w3 + b3
        return q, (x, z1, a1, z2, a2)

    def _predict_q(self, obs_batch, online=True):
        """批量预测 Q 值"""
        if online:
            w1, b1 = self.online_w1, self.online_b1
            w2, b2 = self.online_w2, self.online_b2
            w3, b3 = self.online_w3, self.online_b3
        else:
            w1, b1 = self.target_w1, self.target_b1
            w2, b2 = self.target_w2, self.target_b2
            w3, b3 = self.target_w3, self.target_b3
        q, _ = self._forward(obs_batch, w1, b1, w2, b2, w3, b3)
        return q

    def _train_batch(self, obs_batch, action_indices, targets):
        """一步梯度下降 + 梯度裁剪"""
        batch_size = obs_batch.shape[0]

        # 前向传播
        q_all, (x, z1, a1, z2, a2) = self._forward(
            obs_batch, self.online_w1, self.online_b1,
            self.online_w2, self.online_b2,
            self.online_w3, self.online_b3
        )

        # 只取实际执行的动作的 Q 值
        q_taken = q_all[np.arange(batch_size), action_indices]

        # MSE loss 对 q_taken 的梯度
        diff = q_taken - targets
        loss = np.mean(diff ** 2)

        # 输出层梯度
        dq = np.zeros_like(q_all)
        dq[np.arange(batch_size), action_indices] = 2.0 * diff / batch_size

        # 反向传播：w3, b3
        grad_w3 = a2.T @ dq
        grad_b3 = np.sum(dq, axis=0)

        # 裁剪梯度
        grad_w3 = np.clip(grad_w3, -1.0, 1.0)
        grad_b3 = np.clip(grad_b3, -1.0, 1.0)

        # 反向传播到隐藏层 2
        da2 = dq @ self.online_w3.T
        dz2 = da2 * (z2 > 0).astype(np.float32)

        grad_w2 = a1.T @ dz2
        grad_b2 = np.sum(dz2, axis=0)
        grad_w2 = np.clip(grad_w2, -1.0, 1.0)
        grad_b2 = np.clip(grad_b2, -1.0, 1.0)

        # 反向传播到隐藏层 1
        da1 = dz2 @ self.online_w2.T
        dz1 = da1 * (z1 > 0).astype(np.float32)

        grad_w1 = x.T @ dz1
        grad_b1 = np.sum(dz1, axis=0)
        grad_w1 = np.clip(grad_w1, -1.0, 1.0)
        grad_b1 = np.clip(grad_b1, -1.0, 1.0)

        # 更新权重
        self.online_w3 -= self.learning_rate * grad_w3
        self.online_b3 -= self.learning_rate * grad_b3
        self.online_w2 -= self.learning_rate * grad_w2
        self.online_b2 -= self.learning_rate * grad_b2
        self.online_w1 -= self.learning_rate * grad_w1
        self.online_b1 -= self.learning_rate * grad_b1

        return loss

    def _sync_target_network(self):
        """同步目标网络"""
        self.target_w1 = self.online_w1.copy()
        self.target_b1 = self.online_b1.copy()
        self.target_w2 = self.online_w2.copy()
        self.target_b2 = self.online_b2.copy()
        self.target_w3 = self.online_w3.copy()
        self.target_b3 = self.online_b3.copy()

    def _remember(self, obs, action_idx, reward, next_obs, terminated):
        """存入经验回放（deque 自动淘汰最旧数据）"""
        self.memory.append((obs, action_idx, reward, next_obs, terminated))

    def _replay(self):
        """从经验回放中采样并训练"""
        if len(self.memory) < self.batch_size:
            return

        indices = np.random.choice(len(self.memory), self.batch_size, replace=False)
        batch = [self.memory[i] for i in indices]

        obs_batch = np.array([t[0] for t in batch], dtype=np.float32)
        action_indices = np.array([t[1] for t in batch], dtype=np.int32)
        rewards = np.array([t[2] for t in batch], dtype=np.float32)
        next_obs_batch = np.array([t[3] for t in batch], dtype=np.float32)
        terminateds = np.array([t[4] for t in batch], dtype=np.float32)

        # 目标 Q 值
        next_q = self._predict_q(next_obs_batch, online=False)
        max_next_q = np.max(next_q, axis=1)
        targets = rewards + self.gamma * max_next_q * (1.0 - terminateds)

        self._train_batch(obs_batch, action_indices, targets)

        self.train_step_count += 1
        if self.train_step_count % self.target_update_freq == 0:
            self._sync_target_network()

    def _select_action(self, obs: np.ndarray, info: dict = None) -> tuple:
        """选择动作（epsilon-greedy）"""
        if np.random.random() < self.epsilon:
            idx = np.random.randint(self.n_actions)
        else:
            obs_batch = obs.reshape(1, -1).astype(np.float32)
            q_values = self._predict_q(obs_batch, online=True)[0]
            idx = int(np.argmax(q_values))
        return self.discrete_actions[idx], idx

    def train(self, max_episodes: int = 100, callback=None):
        """训练入口"""
        episode_rewards = []

        for episode in range(max_episodes):
            obs, info = self.env.reset()
            obs = obs.astype(np.float32)
            episode_reward = 0
            done = False

            while not done:
                action, action_idx = self._select_action(obs, info)
                next_obs, reward, terminated, truncated, info = self.env.step(action)
                next_obs = next_obs.astype(np.float32)
                done = terminated or truncated

                self._remember(obs, action_idx, reward, next_obs, terminated)
                self._replay()

                obs = next_obs
                episode_reward += reward

            self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
            episode_rewards.append(episode_reward)

            if callback:
                callback(episode, episode_reward, self.epsilon)

        return episode_rewards

    def predict(self, obs: np.ndarray, info: dict = None) -> np.ndarray:
        """预测动作"""
        obs_batch = obs.reshape(1, -1).astype(np.float32)
        q_values = self._predict_q(obs_batch, online=True)[0]
        idx = int(np.argmax(q_values))
        return self.discrete_actions[idx]
