# 飞行试验环境构建系统 - 项目技术文档

## 目录

- [项目概述](#项目概述)
- [系统架构](#系统架构)
- [前端技术详解](#前端技术详解)
- [后端技术详解](#后端技术详解)
- [数据库设计](#数据库设计)
- [API 接口文档](#api-接口文档)
- [部署方案](#部署方案)

---

## 项目概述

### 项目定位

基于强化学习的飞行试验环境构建系统，用于自动生成 Gymnasium 兼容的飞行模拟环境，支持：

- **环境生成**：根据配置参数自动生成飞行试验环境
- **动态调整**：根据训练指标实时调整环境参数
- **智能优化**：使用贝叶斯优化寻找最优环境配置

### 技术栈总览

| 层级 | 技术 | 用途 |
|------|------|------|
| 前端 | Vue 3 + TypeScript | 用户界面 |
| UI 框架 | Element Plus | 组件库 |
| 3D 渲染 | Three.js | 场景预览 |
| 数据可视化 | ECharts | 训练曲线 |
| 后端 | FastAPI | API 服务 |
| ORM | SQLAlchemy | 数据库操作 |
| 异步任务 | Celery | 后台任务 |
| 缓存/消息 | Redis | 缓存 + 消息队列 |
| 数据库 | PostgreSQL | 业务数据 |
| 对象存储 | MinIO | 文件存储 |

---

## 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────┐
│                      用户浏览器                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │              Vue 3 + TypeScript                  │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌───────┐ │   │
│  │  │环境管理 │ │训练监控 │ │优化中心 │ │模型库 │ │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └───────┘ │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                    Nginx (端口 80)                       │
│              静态资源 + 反向代理 API                      │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                 FastAPI 后端 (端口 8000)                  │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────┐  │
│  │  环境   │ │  动态   │ │  智能   │ │   模型      │  │
│  │  生成   │ │  调整   │ │  优化   │ │   管理      │  │
│  └─────────┘ └─────────┘ └─────────┘ └─────────────┘  │
└─────────────────────────────────────────────────────────┘
                    │           │           │
          ┌─────────┘     ┌─────┘     ┌─────┘
          ▼               ▼           ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ PostgreSQL  │  │    Redis    │  │    MinIO    │
│  (数据存储) │  │ (缓存/消息) │  │ (文件存储) │
└─────────────┘  └─────────────┘  └─────────────┘
```

### 请求流程

```
用户操作 → 前端发起请求 → Nginx 转发 → FastAPI 处理 → 数据库操作 → 返回结果
                │
                ├── WebSocket (实时数据)
                │   前端 ←→ 后端 (训练指标推送)
                │
                └── Celery (异步任务)
                    环境生成/批量生成/优化迭代
```

---

## 前端技术详解

### 目录结构

```
frontend/
├── src/
│   ├── api/              # Axios 配置
│   │   └── index.ts      # 请求拦截器、响应处理
│   ├── components/       # 公共组件
│   │   └── EnvPreview3D.vue  # 3D 环境预览
│   ├── layout/           # 布局组件
│   │   └── index.vue     # 主布局（侧边栏+头部）
│   ├── router/           # 路由配置
│   │   └── index.ts      # 页面路由
│   ├── stores/           # Pinia 状态管理
│   │   ├── auth.ts       # 认证状态
│   │   └── project.ts    # 项目状态
│   ├── views/            # 页面组件
│   │   ├── Login.vue     # 登录页
│   │   ├── Envs.vue      # 环境管理
│   │   ├── Monitor.vue   # 训练监控
│   │   ├── Optimization.vue  # 优化中心
│   │   ├── Models.vue    # 模型库
│   │   └── Settings.vue  # 设置
│   └── main.ts           # 入口文件
├── package.json          # 依赖配置
└── vite.config.ts        # Vite 配置
```

### 核心技术点

#### 1. Vue 3 Composition API

使用 `<script setup>` 语法糖：

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'

const count = ref(0)  // 响应式变量
const increment = () => count.value++  // 方法

onMounted(() => {
  // 组件挂载后执行
})
</script>
```

#### 2. Pinia 状态管理

```typescript
// stores/auth.ts
export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<User | null>(null)

  async function login(username: string, password: string) {
    const response = await api.post('/api/auth/login', { username, password })
    token.value = response.data.access_token
  }

  return { token, user, login }
})
```

#### 3. Three.js 3D 预览

```vue
<!-- EnvPreview3D.vue -->
<template>
  <div ref="container" class="preview-container"></div>
</template>

<script setup>
import * as THREE from 'three'

const initScene = () => {
  const scene = new THREE.Scene()
  const camera = new THREE.PerspectiveCamera(75, width/height, 0.1, 1000)
  const renderer = new THREE.WebGLRenderer()

  // 添加地形、障碍物、航路点等
}
</script>
```

#### 4. ECharts 实时曲线

```typescript
// 训练指标实时更新
const chart = echarts.init(chartRef.value)
chart.setOption({
  xAxis: { type: 'time' },
  yAxis: { type: 'value', name: '奖励值' },
  series: [{
    data: metrics.value.map(m => [m.time, m.reward]),
    type: 'line',
    smooth: true
  }]
})
```

### 路由配置

| 路径 | 页面 | 说明 |
|------|------|------|
| `/login` | Login.vue | 登录页 |
| `/envs` | Envs.vue | 环境管理 |
| `/monitor` | Monitor.vue | 训练监控 |
| `/optimization` | Optimization.vue | 优化中心 |
| `/models` | Models.vue | 模型库 |
| `/settings` | Settings.vue | 设置 |

---

## 后端技术详解

### 目录结构

```
backend/
├── app/
│   ├── api/              # API 路由
│   │   ├── auth.py       # 认证接口
│   │   ├── users.py      # 用户管理
│   │   ├── projects.py   # 项目管理
│   │   ├── envs.py       # 环境管理
│   │   ├── models.py     # 模型管理
│   │   ├── optimization.py  # 优化接口
│   │   ├── strategies.py # 策略管理
│   │   ├── notifications.py # 通知
│   │   ├── logs.py       # 日志
│   │   └── ws.py         # WebSocket
│   ├── core/             # 核心模块
│   │   ├── config.py     # 配置管理
│   │   ├── database.py   # 数据库连接
│   │   └── security.py   # 认证授权
│   ├── models/           # SQLAlchemy 模型
│   ├── schemas/          # Pydantic 模型
│   ├── services/         # 业务逻辑
│   │   ├── env_generator.py   # 环境生成
│   │   ├── jsbsim_engine.py   # JSBSim 引擎
│   │   ├── strategy_engine.py # 策略引擎
│   │   ├── evaluator.py       # 评估器
│   │   ├── optimizer.py       # 优化器
│   │   ├── training_service.py # 训练服务
│   │   └── ws_manager.py      # WebSocket 管理
│   ├── tasks/            # Celery 异步任务
│   │   ├── env_tasks.py      # 环境生成任务
│   │   └── optimization_tasks.py  # 优化任务
│   ├── seed/             # 数据库种子
│   └── main.py           # 应用入口
├── alembic/              # 数据库迁移
├── requirements.txt      # Python 依赖
└── Dockerfile           # Docker 配置
```

### 核心技术点

#### 1. FastAPI 异步框架

```python
from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession

app = FastAPI()

@app.get("/api/envs")
async def get_envs(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    result = await db.execute(text("SELECT * FROM envs WHERE project_id = :id"), {"id": project_id})
    return {"code": 0, "data": result.fetchall()}
```

#### 2. JWT 认证

```python
# 创建 token
def create_access_token(data: dict) -> str:
    expire = datetime.utcnow() + timedelta(minutes=1440)
    to_encode = data.copy()
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm="HS256")

# 验证 token
async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
    username = payload.get("sub")
    # 查询用户...
```

#### 3. Celery 异步任务

```python
# tasks/env_tasks.py
@celery_app.task
def generate_env_task(env_id: str, config: dict, project_id: str, user_id: str):
    # 1. 调用 JSBSim 生成环境
    # 2. 上传到 MinIO
    # 3. 更新数据库状态
    # 4. 发送 WebSocket 通知
```

#### 4. WebSocket 实时通信

```python
# ws_manager.py
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, project_id: str):
        await websocket.accept()
        self.active_connections[project_id] = websocket

    async def send_metrics(self, project_id: str, metrics: dict):
        if project_id in self.active_connections:
            await self.active_connections[project_id].send_json(metrics)
```

#### 5. 策略引擎

```python
# strategy_engine.py
class StrategyEngine:
    def evaluate(self, metrics: dict, strategies: list) -> list:
        """根据指标评估策略，返回触发的动作"""
        actions = []
        for strategy in strategies:
            if self._match_condition(metrics, strategy.condition):
                actions.append(strategy.action)
        return actions
```

### 依赖包说明

| 包名 | 版本 | 用途 |
|------|------|------|
| fastapi | >=0.110 | Web 框架 |
| uvicorn | >=0.29 | ASGI 服务器 |
| sqlalchemy | >=2.0 | ORM |
| asyncpg | >=0.29 | PostgreSQL 驱动 |
| celery | >=5.3 | 异步任务队列 |
| redis | >=5.0 | Redis 客户端 |
| python-jose | >=3.3 | JWT 处理 |
| passlib | >=1.7 | 密码加密 |
| jsbsim | >=1.1 | 飞行模拟引擎 |
| scikit-optimize | >=0.9 | 贝叶斯优化 |

---

## 数据库设计

### 表结构概览

```
users ──────────┐
                │
projects ───────┤
    │           │
    ├── project_roles
    │
    ├── tasks
    │   └── envs
    │       ├── env_snapshots
    │       ├── adjustment_history
    │       ├── env_evaluations
    │       └── training_metrics
    │
    ├── strategies
    ├── models
    │   └── model_versions
    │
    └── optimization_tasks
        └── optimization_reports

notifications (用户通知)
operation_logs (操作日志)
system_logs (系统日志)
```

### 核心表详解

#### users - 用户表

```sql
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,        -- UUID
    username VARCHAR(64) UNIQUE,       -- 用户名
    password_hash VARCHAR(256),        -- 密码哈希
    global_role VARCHAR(16),           -- 角色: admin/configurer/viewer
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

#### projects - 项目表

```sql
CREATE TABLE projects (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(128),                 -- 项目名称
    description TEXT,                  -- 项目描述
    created_by VARCHAR(36),            -- 创建者
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

#### envs - 环境表

```sql
CREATE TABLE envs (
    id VARCHAR(36) PRIMARY KEY,
    project_id VARCHAR(36),            -- 所属项目
    task_id VARCHAR(36),               -- 关联任务
    name VARCHAR(128),                 -- 环境名称
    config JSONB,                      -- 环境配置 (JSON)
    template_id VARCHAR(36),           -- 使用的模板
    status VARCHAR(16),                -- 状态: generating/active/deprecated
    storage_path VARCHAR(256),         -- MinIO 存储路径
    created_by VARCHAR(36),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

#### env_snapshots - 环境快照表

```sql
CREATE TABLE env_snapshots (
    id VARCHAR(36) PRIMARY KEY,
    env_id VARCHAR(36),                -- 关联环境
    config JSONB,                      -- 快照配置
    trigger_type VARCHAR(16),          -- 触发类型: manual_adjust/auto_adjust
    operator VARCHAR(36),              -- 操作者
    reason TEXT,                       -- 原因
    created_at TIMESTAMP
);
```

#### optimization_tasks - 优化任务表

```sql
CREATE TABLE optimization_tasks (
    id VARCHAR(36) PRIMARY KEY,
    project_id VARCHAR(36),
    param_space JSONB,                 -- 参数空间
    weights JSONB,                     -- 评估权重
    max_iterations INTEGER,            -- 最大迭代次数
    current_iteration INTEGER,         -- 当前迭代
    status VARCHAR(16),                -- 状态: running/completed
    best_params JSONB,                 -- 最优参数
    best_score FLOAT,                  -- 最优分数
    created_at TIMESTAMP
);
```

### JSONB 配置示例

环境配置 (envs.config):

```json
{
  "terrain": {
    "type": "hilly",
    "elevation_min": 0,
    "elevation_max": 200,
    "resolution": 1.0
  },
  "atmosphere": {
    "wind_speed": 10,
    "wind_direction": 90,
    "visibility": 10000
  },
  "aircraft": {
    "model": "c172x",
    "mass": 1043,
    "wingspan": 11.0
  },
  "reward": {
    "items": [
      {"name": "altitude_reward", "coefficient": 1.0}
    ],
    "penalties": [
      {"name": "collision_penalty", "coefficient": -10.0}
    ]
  },
  "obstacles": {
    "count": 5,
    "types": ["building", "tower"],
    "density": 0.3
  },
  "waypoints": [
    {"id": "wp1", "position": [0, 0, 100], "order": 1}
  ]
}
```

---

## API 接口文档

### 认证接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/login` | 登录 |
| POST | `/api/auth/logout` | 登出 |
| GET | `/api/auth/me` | 获取当前用户 |

### 用户管理

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/api/users` | 用户列表 | admin |
| POST | `/api/users` | 创建用户 | admin |
| PUT | `/api/users/{id}` | 更新用户 | admin |
| DELETE | `/api/users/{id}` | 删除用户 | admin |
| POST | `/api/users/{id}/reset-password` | 重置密码 | admin |

### 项目管理

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | `/api/projects` | 项目列表 | 登录用户 |
| POST | `/api/projects` | 创建项目 | 登录用户 |
| GET | `/api/projects/{id}` | 项目详情 | 项目成员 |
| PUT | `/api/projects/{id}` | 更新项目 | configurer |
| DELETE | `/api/projects/{id}` | 删除项目 | configurer |
| GET | `/api/projects/{id}/members` | 成员列表 | 项目成员 |
| POST | `/api/projects/{id}/members` | 添加成员 | configurer |
| PUT | `/api/projects/{id}/members/{uid}` | 修改角色 | configurer |
| DELETE | `/api/projects/{id}/members/{uid}` | 移除成员 | configurer |

### 环境管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/envs` | 环境列表 |
| POST | `/api/envs` | 创建环境 |
| GET | `/api/envs/{id}` | 环境详情 |
| DELETE | `/api/envs/{id}` | 删除环境 |
| POST | `/api/envs/batch` | 批量生成 |
| POST | `/api/envs/import` | 导入环境 |
| GET | `/api/envs/{id}/export` | 导出环境 |
| GET | `/api/envs/{id}/preview` | 获取预览 |
| POST | `/api/envs/{id}/adjust` | 手动调整 |
| POST | `/api/envs/{id}/rollback` | 版本回滚 |
| GET | `/api/envs/{id}/snapshots` | 快照列表 |
| POST | `/api/envs/{id}/train` | 开始训练 |
| POST | `/api/envs/{id}/stop-training` | 停止训练 |

### 优化接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/envs/{id}/evaluate` | 评估环境 |
| GET | `/api/envs/{id}/evaluations` | 评估历史 |
| DELETE | `/api/envs/{id}/evaluations/{eid}` | 删除评估 |
| POST | `/api/optimization-tasks` | 创建优化任务 |
| POST | `/api/optimization-tasks/auto` | 全自动优化 |
| GET | `/api/optimization-tasks` | 任务列表 |
| GET | `/api/optimization-tasks/{id}` | 任务详情 |
| DELETE | `/api/optimization-tasks/{id}` | 删除任务 |
| POST | `/api/optimization-tasks/{id}/stop` | 停止任务 |

### WebSocket 端点

| 路径 | 说明 |
|------|------|
| `/ws/metrics` | 训练指标上报 |
| `/ws/adjustment` | 调整指令下发 |
| `/ws/frontend` | 前端实时推送 |

---

## 部署方案

### Docker 部署

```bash
# 一键启动
docker compose up -d --build

# 服务组成
- frontend (Nginx)     :80
- backend (FastAPI)    :8000
- celery-worker        后台任务
- postgres             :5432
- redis                :6379
- minio                :9000/:9001
```

### 本地部署

```bash
# 1. 安装依赖
pip install -r requirements.txt
npm install

# 2. 启动数据库
# PostgreSQL + Redis

# 3. 启动后端
cd backend && python run.py

# 4. 启动前端
cd frontend && npm run dev
```

---

## 核心算法

### 环境评估四维评分

```
总分 = 0.25 × 多样性 + 0.25 × 挑战性 + 0.25 × 真实性 + 0.25 × 有效性

多样性 = (地形多样性 + 参数多样性) / 2
挑战性 = 风速挑战 × 0.3 + 障碍物挑战 × 0.4 + 地形挑战 × 0.3
真实性 = (机型真实性 + 参数合理性) / 2
有效性 = 基于奖励函数设计完整度
```

### 贝叶斯优化

使用 scikit-optimize 的 `gp_minimize`：

1. 定义参数空间 (风速、障碍物数量等)
2. 定义目标函数 (负的评估总分)
3. 迭代优化，寻找最优参数组合
