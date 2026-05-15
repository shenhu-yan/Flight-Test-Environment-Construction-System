# 实施计划

本计划面向 AI 开发者，每一步小而具体，包含验证手段，不含代码。

前置要求：执行任何步骤前，必须完整阅读 `memory-bank/design-document.md` 和 `memory-bank/tech-stack.md` 以及 `CLAUDE.md`。

---

## 约定

### 目录结构

前端和后端位于同一 Git 仓库的两个子目录：`backend/` 和 `frontend/`。docker-compose.yml、README.md 等放在仓库根目录。

### JSBSim 调用执行策略

| 操作类型 | 执行方式 | 原因 |
| :--- | :--- | :--- |
| 环境生成（一次性） | Celery 后台任务队列 | 耗时 30 秒~5 分钟，不适合请求内等待 |
| 在线交互（step/reset） | `run_in_executor` 线程池 | 用户等待训练反馈，需保持会话 |
| 批量生成 / 贝叶斯优化迭代 | Celery 后台任务队列 | 长耗时，支持断点续生 |

### WebSocket 三端点设计

| 端点 | 连接方 | 用途 |
| :--- | :--- | :--- |
| `/ws/metrics` | 本地训练进程 | 训练指标上报 |
| `/ws/adjustment` | 本地训练进程 | 接收调整指令 |
| `/ws/frontend` | 前端浏览器 | 接收实时指标推送 + 通知 |

### 评估体系补充

- **挑战性**：后端 JSBSim 进程内运行随机策略 + 启发式规则（非真实 RL 训练），跑 100 步，验证环境数值稳定、奖励函数无崩溃、动作响应正常
- **有效性**：新环境无训练指标时，有效性评分默认为 50，提示"暂无训练数据"

### 初始用户

数据库种子脚本创建默认 admin 用户（username: admin / password: admin123），首次部署后强制修改密码。

---

## Phase 1 — 核心基座

### Step 1.1 项目骨架与 Docker 环境

**目标**：建立前后端目录结构和 Docker Compose 开发环境。

**指令**：

1. 创建 `backend/` 子目录，包含 `app/` 包目录和 `requirements.txt`，内容按 `memory-bank/tech-stack.md` 第 4.2 节的依赖清单填写（含 Celery）
2. 创建 `frontend/` 子目录，使用 Vite + Vue 3 + TypeScript 模板初始化，安装 `memory-bank/tech-stack.md` 第 4.1 节列出的所有依赖
3. 创建仓根目录 `docker-compose.yml`，定义 6 个服务：`postgres`（端口 5432，默认数据库 fltect）、`redis`（端口 6379）、`minio`（端口 9000/9001）、`backend`（构建自 `backend/Dockerfile`，映射端口 8000）、`celery_worker`（构建自同一 Dockerfile，启动命令为 Celery worker）、`frontend`（构建自 `frontend/Dockerfile`，映射端口 5173）
4. 创建 `backend/Dockerfile`：基于 python:3.12-slim，安装依赖。默认启动命令为 Uvicorn 运行 `app.main:app`；Celery worker 通过 docker-compose command 覆盖启动
5. 创建 `frontend/Dockerfile`：基于 node:20-alpine，安装依赖，启动 Vite dev server
6. 创建 `backend/app/main.py` 作为 FastAPI 应用入口，只挂载一个 `GET /api/health` 返回 `{"code": 0, "message": "ok"}`
7. 在 `backend/app/` 下创建 Celery 应用初始化模块，配置 broker 为 Redis，backend 为 Redis

**验证**：

- 执行 `docker-compose up -d`，6 个容器全部状态为 running
- 访问 `http://localhost:8000/api/health` 返回 `{"code": 0, "message": "ok"}`
- 访问 `http://localhost:8000/docs` 能看到 Swagger UI
- 访问 `http://localhost:5173` 能看到 Vue 默认页面
- `docker-compose logs celery_worker` 显示 Celery worker 就绪，无报错

---

### Step 1.2 数据库 Schema 与迁移

**目标**：用 Alembic 建立 `memory-bank/design-document.md` 第 4.2 节定义的全部业务表。

**指令**：

1. 在后端项目初始化 Alembic，配置异步引擎连接 PostgreSQL
2. 在 `app/models/` 下为每张表定义 SQLAlchemy 2.0 ORM 模型：`projects`、`tasks`、`envs`、`env_snapshots`、`adjustment_history`、`env_evaluations`、`training_metrics`、`models`、`model_versions`、`users`、`project_roles`、`templates`、`optimization_tasks`、`optimization_reports`、`notifications`、`operation_logs`、`system_logs`。字段类型与约束严格按照 `memory-bank/design-document.md` 第 4.2 节的表定义。`tasks` 表定义补充如下：

**tasks 表结构**：

| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| id | VARCHAR(36) PK | 任务 ID (UUID) |
| project_id | VARCHAR(36) FK | 所属项目 |
| name | VARCHAR(128) | 任务名称 |
| description | TEXT | 任务描述 |
| created_by | VARCHAR(36) FK | 创建人 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

3. 生成 Alembic 迁移脚本并执行

**验证**：

- `alembic upgrade head` 无报错
- 用 `psql` 或数据库客户端连接 PostgreSQL，执行 `\dt` 能列出全部 18 张表（含 `alembic_version`、`notifications`、`operation_logs`、`system_logs`）
- 抽查 `envs` 表的 `config` 列类型为 `jsonb`
- 抽查 `tasks` 表存在，且有 `project_id` 外键

---

### Step 1.3 用户认证与权限

**目标**：实现 JWT 登录、权限中间件和默认 admin 种子。

**指令**：

1. 创建数据库种子脚本 `app/seed/users.py`，插入默认 admin 用户（username: admin，password: admin123 的 bcrypt 哈希，global_role: admin）。项目启动时检测是否存在 admin 用户，若不存在则自动执行
2. 在 `app/schemas/` 定义 Pydantic 模型：`LoginRequest`（username + password）、`TokenResponse`（access_token + token_type）、`UserCreate`、`UserOut`
3. 在 `app/api/auth.py` 实现路由：`POST /api/auth/login`（校验用户名密码，签发 JWT，有效期 24h）、`POST /api/auth/logout`（将 token 加入 Redis 黑名单）
4. 在 `app/core/security.py` 实现：密码哈希（bcrypt）与校验函数、JWT 签发与验证函数、获取当前用户依赖项（`get_current_user`）
5. 在 `app/api/users.py` 实现路由：`GET /api/users`、`POST /api/users`、`PUT /api/users/{id}`、`DELETE /api/users/{id}`。除 `POST /api/users`（创建用户）仅需 admin 权限外，其余 GET 需登录、修改/删除需 admin 或本人
6. 将路由注册到 FastAPI 应用，鉴权依赖注入到需要保护的路由上

**验证**：

- 首次启动后，数据库 `users` 表中有 admin 用户记录
- 用 admin/admin123 调用 `POST /api/auth/login`，返回 200 和 JWT token
- 不带 token 调用 `GET /api/users`，返回 401
- 带 token 调用 `GET /api/users`，返回 200 和用户列表
- 用 viewer 角色用户尝试 `POST /api/users`，返回 403

---

### Step 1.4 项目与任务管理

**目标**：实现项目 CRUD、任务 CRUD 和成员管理。

**指令**：

1. 在 `app/schemas/` 定义 `ProjectCreate`、`ProjectOut`、`TaskCreate`、`TaskOut`、`MemberAdd` 等 Pydantic 模型
2. 在 `app/api/projects.py` 实现路由：`POST /api/projects`（创建项目，创建者自动成为项目 admin）、`GET /api/projects`（当前用户参与的项目列表）、`GET /api/projects/{id}`、`PUT /api/projects/{id}`、`DELETE /api/projects/{id}`
3. 在 `app/api/tasks.py` 实现路由：`POST /api/projects/{project_id}/tasks`（创建任务）、`GET /api/projects/{project_id}/tasks`（任务列表）、`GET /api/tasks/{id}`、`PUT /api/tasks/{id}`、`DELETE /api/tasks/{id}`
4. 在 `app/api/projects.py` 实现成员路由：`GET /api/projects/{id}/members`、`POST /api/projects/{id}/members`、`DELETE /api/projects/{id}/members/{user_id}`
5. 所有项目/任务操作强制校验当前用户是否为项目成员且角色权限匹配

**验证**：

- 创建项目后，`projects` 表有新记录，`project_roles` 表有创建者的 admin 记录
- 创建任务后，`tasks` 表有新记录，`project_id` 关联正确
- 非该项目成员调用 `GET /api/projects/{id}` 返回 403
- 成员添加与移除操作正确反映在 `project_roles` 表中

---

### Step 1.5 环境模板库

**目标**：实现模板 CRUD，并预置 3 个固定翼内置模板。

**指令**：

1. 在 `app/schemas/` 定义 `TemplateCreate`、`TemplateOut` 等 Pydantic 模型，`config` 字段为 JSONB 结构
2. 在 `app/api/templates.py` 实现路由：`GET /api/templates`、`POST /api/templates`、`PUT /api/templates/{id}`、`DELETE /api/templates/{id}`
3. 创建数据库种子脚本 `app/seed/templates.py`，插入 3 个内置模板（`is_builtin=True`）：固定翼基础难度、中等难度、高难度，每个模板的 `config` 包含完整的场景/气象/飞行力学/奖励函数参数框架
4. 项目启动时检测内置模板是否已存在，若不存在则自动执行种子脚本

**验证**：

- 调用 `GET /api/templates` 返回 3 个内置模板
- 创建自定义模板后，列表中包含 4 个模板，自定义模板的 `is_builtin` 为 false
- 不同 `aircraft_type`（目前仅 fixed_wing）和 `difficulty` 筛选参数工作正常

---

### Step 1.6 环境配置解析与校验

**目标**：实现从 XML/JSON 文件和图形化参数到内部 `EnvConfig` 对象的解析与校验。

**指令**：

1. 在 `app/schemas/env_config.py` 定义 `EnvConfig` Pydantic 模型，字段覆盖：地形（类型、海拔范围、分辨率）、气象（风速、风向、能见度）、飞行力学（机型、质量、翼展）、奖励函数（奖励项列表、惩罚项列表、系数）、障碍物（数量、类型、密度）、航路点列表。所有数值字段设置合理范围约束
2. 在 `app/services/config_parser.py` 实现两个解析函数：`parse_json_config`（接受 JSON 字符串/文件）、`parse_xml_config`（接受 XML 字符串/文件），两者均返回 `EnvConfig`。校验失败时抛出包含具体字段错误的异常
3. 在 `app/api/envs.py` 实现 `POST /api/envs/parse-config` 接口：接受上传的 XML/JSON 文件，返回解析后的 `EnvConfig` 或具体校验错误

**验证**：

- 上传一个格式正确的 JSON 配置文件，返回 200 和完整的 `EnvConfig`
- 上传一个风速超范围的 JSON，返回 422 和具体错误信息（如：wind_speed 超出范围 [0, 50]）
- 上传一个格式错误的 XML，返回 422 和解析错误信息
- 上传一个合法 XML，正确转换为 `EnvConfig`

---

### Step 1.7 JSBSim 集成与环境生成核心

**目标**：调用 JSBSim 根据 `EnvConfig` 构建飞行动力学模型，通过 Celery 异步生成 Gymnasium 兼容的环境产物。

**指令**：

1. 在 `app/services/jsbsim_engine.py` 封装 JSBSim 调用：`build_environment(config: EnvConfig) -> dict`，该函数根据 `EnvConfig` 的飞行力学参数选择机型配置、设定初始条件、配置气象；返回值为环境构建需要的 JSBSim 配置文件内容（aircraft XML、atmosphere XML、terrain XML）
2. 在 `app/services/env_generator.py` 实现环境生成主函数：接收 `EnvConfig`，调用 JSBSim 封装生成配置文件，将配置文件 + Gymnasium 兼容的 `core.py`（含 `FlightEnv` 类的 `reset`/`step`/`close`）+ `reward.py` + `config.json` 打包为 zip，上传至 MinIO，将元数据写入 `envs` 表
3. 在 `app/tasks/env_tasks.py` 定义 Celery 任务 `generate_env_task`：调用 `env_generator` 的主函数。任务参数为 `EnvConfig` + `project_id` + `creator_id`
4. 在 `app/api/envs.py` 实现路由：
   - `POST /api/envs`：接收 `EnvConfig` 或 `template_id`+覆盖参数，创建 `envs` 记录（status=generating），派发 Celery 任务，返回 `env_id` + `task_id`
   - `GET /api/envs`：环境列表
   - `GET /api/envs/{env_id}`：环境详情（含生成状态）
   - `DELETE /api/envs/{env_id}`：软删除（status 设为 deprecated）
5. Celery 任务完成后更新 `envs` 表 status 为 active，通过 WebSocket `/ws/frontend` 推送生成完成通知
6. 在 `FlightEnv` 的 `step` 方法中，JSBSim 调用使用 `run_in_executor` 避免阻塞事件循环

**验证**：

- 调用 `POST /api/envs` 传入合法 `EnvConfig`，返回 202 和 `env_id`（异步任务已派发）
- 紧接着查询 `GET /api/envs/{env_id}`，status 为 generating
- 等待 Celery 任务完成后，再次查询，status 为 active
- 数据库 `envs` 表记录的 `storage_path` 指向 MinIO 中的 zip 文件
- MinIO 对应 bucket 中存在该环境的 zip 文件
- 在后端进程内 import 生成的 `FlightEnv` 类，调用 `reset()` 返回合法观测值，调用 `step(random_action)` 返回 (obs, reward, terminated, truncated, info) 五元组
- 前端 WebSocket 连接 `/ws/frontend` 收到环境生成完成通知

---

### Step 1.8 环境导出与导入

**目标**：实现环境包的下载和上传还原。

**指令**：

1. 在 `app/api/envs.py` 实现 `GET /api/envs/{env_id}/export`：从 MinIO 获取 zip 文件，返回 StreamingResponse 下载
2. 实现 `POST /api/envs/import`：接受上传的 zip 文件，解析其中的 `config.json` 还原 `EnvConfig`，将文件存入 MinIO，在 `envs` 表创建记录（status=active，跳过 JSBSim 重新生成）

**验证**：

- 导出一个环境得到 zip 文件，解压后包含 `core.py`、`config.json`、`jsbsim_config/` 目录
- 将该 zip 文件导入新项目，成功创建新环境记录，`config` 与原环境一致
- 导入一个格式损坏的 zip，返回 400 错误

---

### Step 1.9 三维预览数据生成

**目标**：根据 `EnvConfig` 生成供前端 Three.js 渲染的 `scene.json`。

**指令**：

1. 在 `app/services/preview_generator.py` 实现函数：`generate_scene_data(config: EnvConfig) -> dict`，将地形高程网格、障碍物坐标与尺寸、航路点、风场方向/强度、跑道信息按 `memory-bank/design-document.md` 第 6.4 节定义的 `scene.json` 格式输出
2. 在 Celery 环境生成任务中集成：生成环境时自动调用此函数，将 `scene.json` 放入环境产物的 `preview/` 目录，MinIO 同步存储
3. 在 `app/api/envs.py` 实现 `GET /api/envs/{env_id}/preview`：返回该环境的 `scene.json`

**验证**：

- 创建环境后，调用 `GET /api/envs/{env_id}/preview` 返回合法的 JSON，包含 `terrain`、`obstacles`、`waypoints`、`wind`、`runway` 五个顶层字段
- `terrain.elevation` 为二维数组，维度与 `grid_size` 一致
- 修改 `EnvConfig` 中的风速参数后重新生成，`preview` 返回的 `wind.speed` 与新参数一致

---

### Step 1.10 前端 — 项目框架与布局

**目标**：建立前端项目结构、路由和全局布局。

**指令**：

1. 在 `frontend/` 中配置 Vue Router 路由表：`/login`、`/`（首页/环境管理）、`/monitor`（训练监控）、`/optimization`（优化中心）、`/models`（模型库）、`/settings`（设置/用户管理）
2. 实现全局布局组件：顶部导航栏（Logo + 导航链接 + 用户信息下拉）、侧边栏（项目切换 + 快捷操作）、主内容区（router-view）、底部状态栏
3. 实现 Pinia store：`useAuthStore`（管理 token 和登录状态）、`useProjectStore`（管理当前项目）
4. 实现 Axios 请求拦截器：自动附加 JWT token；响应拦截器处理 401 自动跳转登录页
5. 实现 Vue Router 导航守卫：未登录时重定向到 `/login`

**验证**：

- 未登录时访问 `/`，自动重定向到 `/login`
- 登录后导航栏显示各模块入口，点击可切换页面
- 切换项目后，侧边栏和页面头部显示新项目名称

---

### Step 1.11 前端 — 环境生成页面

**目标**：实现环境配置面板和参数化生成。

**指令**：

1. 实现环境生成页面，左侧为折叠分组的参数配置面板：地形组（类型下拉框、海拔范围双滑块、分辨率输入框）、气象组（风速/风向/能见度滑块和输入）、飞行力学组（机型下拉框、质量/翼展输入）、奖励函数组（奖励项/惩罚项动态列表，每项有名称和系数输入）、障碍物组（数量滑块、类型多选、密度滑块）
2. 实现模板选择模式：先选模板，配置面板自动填充模板参数，用户可在此基础上修改
3. 顶部提供"上传配置文件"按钮，支持 XML/JSON 文件上传，上传后自动填充配置面板
4. 底部操作栏：生成按钮调用 `POST /api/envs`，生成中显示 loading 状态（轮询环境状态直至 active）
5. 实现环境列表页面（`/` 路由主内容区），展示当前项目下的所有环境卡片（名称、状态、创建时间），支持点击进入详情

**验证**：

- 选择"固定翼-中等难度"模板，配置面板自动填充中等难度参数
- 修改风速滑块值后点击生成，请求体中的 `wind_speed` 值与滑块一致
- 上传一个 JSON 配置文件后，面板参数与文件内容一致
- 生成成功后，环境列表页出现新环境卡片，状态从 generating 变为 active

---

### Step 1.12 前端 — 三维预览组件

**目标**：集成 Three.js，根据 `scene.json` 渲染环境三维场景。

**指令**：

1. 创建 `EnvPreview3D` Vue 组件，接收 `sceneData` prop（scene.json 数据）
2. 组件内使用 Three.js 渲染：地形用 `PlaneGeometry` + 顶点位移、障碍物用 `BoxGeometry`/`ConeGeometry`、航路用 `Line` + `ArrowHelper`、风场用粒子系统、跑道用贴纹理的 `PlaneGeometry`
3. 添加 `OrbitControls`：鼠标左键旋转、右键平移、滚轮缩放
4. 添加图层控制面板：地形/障碍物/航路/气象 四个独立显隐开关，切换即刻生效
5. 将该组件集成到环境生成页面右侧，环境生成后自动调用 `GET /api/envs/{env_id}/preview` 获取 scene.json 并渲染

**验证**：

- 生成环境后，右侧预览区出现三维场景，可见地形起伏和障碍物
- 鼠标拖拽可旋转视角，滚轮可缩放
- 关闭"障碍物"图层，障碍物消失；重新开启，重新出现
- 风场粒子沿风向运动

---

### Step 1.13 模型管理基础功能

**目标**：实现模型上传、查询、删除和版本管理。

**指令**：

1. 在 `app/schemas/` 定义 `ModelCreate`、`ModelOut`、`ModelVersionOut` 等 Pydantic 模型
2. 在 `app/api/models.py` 实现路由：
   - `POST /api/models`：上传模型文件至 MinIO，在 `models` 表创建记录，在 `model_versions` 表创建 v1.0.0 版本
   - `GET /api/models`：多条件组合检索（project_id、task_id、type、status）
   - `GET /api/models/{id}`：模型详情含当前版本信息
   - `DELETE /api/models/{id}`：软删除（status 设为 deprecated）
   - `POST /api/models/{id}/versions`：上传新版本文件，自动递增版本号
   - `GET /api/models/{id}/versions`：版本列表
   - `POST /api/models/{id}/versions/diff`：两个版本的元数据对比
   - `POST /api/models/{id}/rollback`：将指定版本设为 current_version
   - `GET /api/models/{id}/versions/{ver}/download`：生成 MinIO 预签名 URL 返回
3. 所有操作强制校验 `project_id` 隔离和角色权限

**验证**：

- 上传一个模型文件，返回 201 和模型 ID，`models` 表有记录，`model_versions` 表有 v1.0.0
- 上传第二个版本，版本号为 v1.1.0，`current_version` 更新
- 调用 diff 接口对比 v1.0.0 和 v1.1.0，返回两个版本的元数据差异
- 调用 rollback 到 v1.0.0，`current_version` 变为 v1.0.0
- 非 project 成员调用上传接口，返回 403
- 调用 download 接口返回有效的预签名 URL，可下载文件

---

### Step 1.14 前端 — 模型库页面

**目标**：实现模型列表、详情、上传和版本管理的前端界面。

**指令**：

1. 实现模型库页面：上方筛选栏（模型类型下拉框、状态下拉框、搜索框）、主体为模型卡片列表
2. 实现模型详情弹窗/页面：基本信息 + 版本时间线 + 当前版本下载按钮
3. 实现上传弹窗：选择项目、模型类型、描述、选择文件；上传成功后刷新列表
4. 实现新版本上传：在模型详情中点击"上传新版本"，选择文件后自动递增版本号
5. 实现版本对比：选择两个版本，展示元数据差异表格
6. 实现版本回滚按钮：点击后二次确认，回滚后刷新详情

**验证**：

- 上传模型后列表中出现新卡片
- 详情页展示版本时间线，v1.0.0 在底部
- 上传新版本后时间线新增 v1.1.0 节点
- 版本对比弹出差异表格
- 回滚操作后，当前版本标签变为目标版本

---

## Phase 2 — 动态能力

### Step 2.1 WebSocket 三端点接入服务

**目标**：实现三个 WebSocket 端点，分别服务训练进程上报、调整指令下发、前端实时推送。

**指令**：

1. 在 `app/api/ws.py` 实现 WebSocket 端点 `/ws/metrics`：
   - 连接时验证 JWT token（查询参数方式）
   - 接收消息类型 `metric_report`，按 `project_id:env_id` 注册连接
   - 收到指标后：写入 Redis Stream `metrics:{project_id}:{env_id}`、持久化到 `training_metrics` 表、转发给已订阅该项目的前端 WebSocket 连接
2. 在 `app/api/ws.py` 实现 WebSocket 端点 `/ws/adjustment`：
   - 本地训练进程连接此端点接收调整指令
   - 调整指令由策略引擎或手动调整 API 触发，通过 `ConnectionManager` 转发
3. 在 `app/api/ws.py` 实现 WebSocket 端点 `/ws/frontend`：
   - 前端浏览器连接后订阅指定 `project_id`
   - 接收实时指标推送（type=metric_broadcast）和通知（type=notification）
4. 实现 `ConnectionManager` 类统一管理三端点的活跃连接
5. 实现心跳机制：客户端每 30s 发送 `heartbeat`，服务端 60s 无心跳断开连接

**验证**：

- 用 WebSocket 客户端工具连接 `/ws/metrics`（带 token），发送一条 `metric_report`，数据库 `training_metrics` 表新增一条记录
- 连接 `/ws/adjustment` 后，触发策略调整时该连接收到 `adjust_instruction` 消息
- 连接 `/ws/frontend` 后，发送训练指标时前端连接收到 `metric_broadcast` 消息
- 不带 token 连接任意端点，服务端立即关闭连接
- 停止心跳 60s 后，服务端自动断开连接

---

### Step 2.2 训练监控前端页面

**目标**：实现训练指标实时曲线展示和环境参数手动调整面板。

**指令**：

1. 实现训练监控页面 `/monitor`：
   - 上部区域：ECharts 实时曲线图，展示奖励值/成功率/收敛速度三条曲线，Y 轴各自独立，X 轴为训练步数。收到新指标时实时追加数据点并刷新图表
   - 下部区域：当前环境参数面板，展示从 `envs` 表获取的 config，每个参数旁有编辑图标，点击进入编辑状态
   - 右侧边栏：调整历史时间线，按时间倒序显示每次调整的摘要
2. 页面加载时建立 `/ws/frontend` WebSocket 连接，监听实时指标

**验证**：

- 模拟发送 10 条递增的 `metric_report`，图表曲线上出现 10 个点，奖励值曲线呈上升趋势
- 修改某环境参数后点击确认，调用 `POST /api/envs/{env_id}/adjust` 成功，参数面板显示新值
- 调整历史时间线出现新的调整记录

---

### Step 2.3 动态调整策略引擎

**目标**：实现规则驱动的策略引擎，指标异常时自动生成调整指令。

**指令**：

1. 在 `app/services/strategy_engine.py` 实现策略引擎：
   - 从数据库加载该项目已启用的策略规则列表
   - 收到新指标时，遍历策略规则，检查 `condition`（metric + operator + threshold + duration_steps）
   - 匹配成功时，执行 `action.adjustments`，生成调整指令消息
   - 调整指令推送至 `/ws/adjustment` 端点（type=adjust_instruction）
   - 自动保存调整前参数快照，写入 `adjustment_history` 表，trigger_type=auto
2. 在 `app/api/strategies.py` 实现路由：
   - `GET /api/strategies`：查询策略列表（支持按 project_id 筛选）
   - `PUT /api/strategies/{id}`：修改策略（阈值、启停）
   - `POST /api/strategies`：新增自定义策略
3. 创建种子脚本 `app/seed/strategies.py`，预置 3 条默认策略：收敛过慢降难度、成功率过低减障碍、奖励过高增复杂度

**验证**：

- 发送连续 5 条 `convergence_speed < 0.3` 的指标，触发"收敛过慢"策略
- `adjustment_history` 表新增一条 trigger_type=auto 的记录
- `/ws/adjustment` 连接收到 `adjust_instruction` 消息
- 修改策略阈值为 0.1，重新发送 convergence_speed=0.2 的指标，不再触发（0.2 > 0.1 不满足条件）
- 手动禁用某策略后，同等条件不再触发

---

### Step 2.4 手动调整与参数快照

**目标**：支持用户在训练过程中手动修改环境参数，并保存完整快照。

**指令**：

1. 在 `app/api/envs.py` 实现 `POST /api/envs/{env_id}/adjust`：
   - 接收用户修改的参数 delta
   - 保存调整前参数快照至 `env_snapshots` 表（trigger_type=manual_adjust）
   - 合并修改后更新 `envs.config`
   - 保存调整后参数快照至 `env_snapshots` 表
   - 写入 `adjustment_history` 表（trigger_type=manual）
   - 通过 `/ws/adjustment` 端点下发调整指令给本地训练进程
2. 实现 `GET /api/envs/{env_id}/snapshots`：返回该环境的参数快照列表
3. 实现 `GET /api/envs/{env_id}/adjustment-history`：返回调整历史，支持分页

**验证**：

- 手动调整风速参数后，`envs` 表的 `config.wind_speed` 更新
- `env_snapshots` 表新增两条记录（before + after）
- `adjustment_history` 记录包含调整前后快照 ID 和操作人
- `/ws/adjustment` 连接收到调整指令

---

### Step 2.5 版本回滚

**目标**：支持将环境参数回滚至指定历史快照。

**指令**：

1. 在 `app/api/envs.py` 实现 `POST /api/envs/{env_id}/rollback`：接收 `snapshot_id`，将该快照的 config 覆盖写入 `envs.config`，保存当前状态为 before 快照，写入 `adjustment_history` 表（reason 记录回滚目标快照 ID），通过 `/ws/adjustment` 端点下发调整指令

**验证**：

- 经过两次调整后，调用回滚至第一次调整前的快照
- `envs.config` 与该快照的 config 一致
- `/ws/adjustment` 连接收到回滚后的调整指令
- `adjustment_history` 新增一条记录，reason 包含回滚目标快照 ID

---

## Phase 3 — 智能优化

### Step 3.1 环境质量评估体系

**目标**：实现四维评分模型（多样性、挑战性、真实性、有效性）。

**指令**：

1. 在 `app/services/evaluator.py` 实现评估服务：
   - **多样性**：计算当前环境配置参数与同批环境参数的信息熵 + 参数空间覆盖率，归一化到 [0, 100]
   - **挑战性**：在后端 JSBSim 进程内运行随机策略 + 启发式规则 100 步，获取随机策略得分；对比环境内置的最优策略得分预设值（基于 JSBSim 标准工况），计算比值归一化到 [0, 100]
   - **真实性**：用当前环境 JSBSim 参数运行短时仿真，提取关键飞行指标（升力、阻力、俯仰角速率等），与预置参考数据集计算均方误差，反归一化到 [0, 100]
   - **有效性**：查询该环境关联的 `training_metrics` 历史数据，计算奖励曲线的 AUC，归一化到 [0, 100]。若无训练数据，默认 50 分，建议文字标注"暂无训练数据"
   - 四维加权求和得到总分，权重默认各 0.25
   - 基于四维分数生成定性优化建议（如"真实性偏低，建议提高物理建模精度"）
2. 预置参考飞行数据集（JSON 格式），包含标准工况下的关键飞行指标数组，存放在项目的 `data/reference_flight_data/` 目录
3. 在 `app/tasks/optimization_tasks.py` 定义 Celery 任务 `evaluate_env_task`：调用评估服务，结果写入 `env_evaluations` 表
4. 在 `app/api/optimization.py` 实现 `POST /api/envs/{env_id}/evaluate`：派发 Celery 评估任务，返回 task_id
5. 实现 `GET /api/envs/{env_id}/evaluations`：查询该环境的评估历史

**验证**：

- 对一个新生成的环境触发评估，返回 202（异步任务已派发）
- 等待 Celery 任务完成后，`env_evaluations` 表新增一条包含四维分数的记录
- 四维分数均在 [0, 100] 区间内，总分为加权和
- suggestions 字段为非空，包含针对性建议
- 新环境（无训练数据）的有效性分数为 50，建议包含"暂无训练数据"
- 修改环境配置使参数高度单一，重新评估，多样性分数下降

---

### Step 3.2 贝叶斯优化引擎

**目标**：实现基于 scikit-optimize 的贝叶斯优化，通过 Celery 后台执行优化迭代。

**指令**：

1. 在 `app/services/optimizer.py` 实现优化器类，继承 `BaseOptimizer` 抽象基类：
   - 构造函数接收参数空间定义和权重配置
   - `suggest` 方法调用 scikit-optimize 的 `Optimizer.ask`
   - `observe` 方法调用 `Optimizer.tell`
   - 优化目标函数通过调用评估服务计算加权总分
2. 在 `app/tasks/optimization_tasks.py` 定义 Celery 任务 `run_optimization_task`：
   - 每次迭代：调用 `suggest` → 用建议参数生成测试环境 → 评估环境得分 → `observe` 记录结果 → 更新 `optimization_tasks` 表的 `current_iteration` 和 `best_score` → 通过 `/ws/frontend` 推送迭代进度
   - 达到最大迭代次数或收到停止信号时结束
3. 在 `app/api/optimization.py` 实现路由：
   - `POST /api/optimization-tasks`：创建优化任务，指定参数空间、权重、最大迭代次数，派发 Celery 任务
   - `GET /api/optimization-tasks`：查询优化任务列表
   - `GET /api/optimization-tasks/{id}`：查询任务详情含当前迭代和最优结果
   - `POST /api/optimization-tasks/{id}/stop`：设置停止标志，Celery 任务在下一个迭代开始时检测并停止

**验证**：

- 创建优化任务，设置最大迭代 5 次，返回 202
- 任务状态从 pending → running → completed
- `/ws/frontend` 连接收到每次迭代的进度推送
- `optimization_tasks` 表的 `current_iteration` 从 0 递增到 5
- `best_params` 非空，`best_score` 大于第一次迭代的分数（优化有效）
- 手动停止任务时，状态变为 completed，迭代次数停在当前值

---

### Step 3.3 优化效果验证与报告

**目标**：优化完成后自动对比测试，生成可视化报告。

**指令**：

1. 优化任务完成时（Celery 任务末尾），自动触发效果验证：
   - 用优化前的生成参数生成 3 个测试环境，各自运行评估取四维分数平均值
   - 用优化后的生成参数生成 3 个测试环境，各自运行评估取四维分数平均值
   - 对比前后四维分数和总分
2. 生成对比报告数据（含前后分数和差值），写入 `optimization_reports` 表
3. 在 `app/api/optimization.py` 实现 `GET /api/optimization-reports/{id}`：返回报告数据

**验证**：

- 优化完成后，`optimization_reports` 表新增一条记录
- `before_scores` 和 `after_scores` 都包含 diversity/challenge/realism/effectiveness/total 五个字段
- 前端获取报告数据后可渲染为对比图表

---

### Step 3.4 前端 — 优化中心页面

**目标**：实现评估展示、优化任务管理和效果报告页面。

**指令**：

1. 实现优化中心页面 `/optimization`：
   - 上部：环境评估结果展示区——四维雷达图（ECharts radar）+ 总分 + 优化建议文字
   - 中部：优化任务管理区——新建任务按钮、任务列表（状态标签、进度条、操作按钮）
   - 下部：优化报告区——选择报告后展示前后对比柱状图（四维 + 总分）和差值标注
2. 新建任务弹窗：配置权重（四个滑块，值代表百分比，总和 100%）、参数空间范围、最大迭代次数
3. 任务进行中：通过 `/ws/frontend` 接收迭代进度实时更新进度条和当前最优分数

**验证**：

- 选择一个已有评估的环境，雷达图正确显示四维分数
- 创建优化任务后，任务列表出现新条目，状态为 running
- 进度条实时更新（通过 WebSocket 推送）
- 优化完成后，点击查看报告，柱状图显示前后对比

---

### Step 3.5 持续优化定时任务

**目标**：按用户设定周期自动重新评估和优化环境库。

**指令**：

1. 在 `app/services/scheduler.py` 配置 APScheduler：
   - 提供 `add_optimization_schedule` 函数，接受项目 ID、周期（cron 表达式）、优化参数配置
   - 定时触发时：查询该项目所有 active 状态的环境，派发批量 Celery 评估任务，对低分环境触发优化
2. 在设置页面或 API 提供周期配置入口：`POST /api/projects/{id}/optimization-schedule`
3. 定时任务执行的优化结果与手动触发的优化走同一套流程，产生评估记录和优化报告

**验证**：

- 配置一个短周期（如每分钟）的定时任务
- 等待两个周期，`env_evaluations` 表新增对应的批量评估记录
- 低分环境自动触发优化，`optimization_tasks` 表新增任务

---

## Phase 4 — 完善体验

### Step 4.1 批量生成环境

**目标**：支持一次性生成多个差异化环境。

**指令**：

1. 在 `app/tasks/env_tasks.py` 定义 Celery 任务 `batch_generate_envs_task`：接收基准 `EnvConfig`、数量 N、参数差异范围 Δ，在基准配置上对指定维度施加均匀随机扰动，串行生成 N 个环境，每完成一个更新进度，返回 ID 列表
2. 在 `app/api/envs.py` 实现 `POST /api/envs/batch`：派发批量生成 Celery 任务，返回 batch_task_id
3. 前端环境生成页面添加"批量生成"模式：用户指定数量和差异范围后点击生成，通过 WebSocket 接收进度

**验证**：

- 批量生成 5 个环境，返回 batch_task_id
- 等待完成后，数据库和 MinIO 中存在 5 个环境记录和文件
- 5 个环境的配置在指定维度上有差异，未指定维度保持一致
- WebSocket 实时推送生成进度

---

### Step 4.2 消息提醒

**目标**：对关键节点进行页面弹窗和站内信提醒。

**指令**：

1. 创建数据库表 `notifications`：id、user_id、type（info/warning/error）、title、content、read（boolean）、created_at
2. 在后端关键节点触发消息：环境生成完成/失败、策略触发调整、优化任务完成等，向项目成员写入通知记录，同时通过 `/ws/frontend` 推送
3. 实现 `GET /api/notifications`：查询当前用户的通知列表
4. 实现 `PUT /api/notifications/{id}/read`：标记已读
5. 前端实现消息中心：导航栏铃铛图标（显示未读数角标）、点击展开通知列表、点击通知跳转对应页面、弹出 toast 提醒新通知

**验证**：

- 环境生成完成后，创建者收到通知，铃铛角标数字 +1
- 点击通知跳转到对应环境详情页
- 标记已读后角标数字 -1

---

### Step 4.3 日志管理

**目标**：记录和查询用户操作日志与系统运行日志。

**指令**：

1. 创建数据库表 `operation_logs`：id、user_id、action（操作类型）、resource_type、resource_id、detail（JSONB）、ip_address、created_at
2. 创建数据库表 `system_logs`：id、level（info/warn/error）、module、message、detail（JSONB）、created_at
3. 实现后端中间件：自动记录所有写操作（POST/PUT/DELETE）到 `operation_logs`
4. 在后端关键位置（异常捕获、服务启停、定时任务执行）写入 `system_logs`
5. 实现查询 API：`GET /api/logs/operations` 和 `GET /api/logs/system`，支持按操作人/时间/类型筛选，支持 CSV 导出
6. 前端实现日志查询页面：筛选条件 + 日志列表表格 + 导出按钮

**验证**：

- 创建一个环境后，`operation_logs` 新增一条 action=create、resource_type=env 的记录
- 手动触发一个异常，`system_logs` 新增一条 level=error 的记录
- 日志查询页面按时间范围筛选，结果数量与数据库一致
- CSV 导出文件可正常打开，包含筛选结果

---

### Step 4.4 模型状态监控与自动推荐

**目标**：自动标记高频调用的优质模型为"推荐"，定期清理弃用模型。

**指令**：

1. 在 `model_versions` 表新增 `download_count` 字段（INTEGER，默认 0）
2. 在 `app/api/models.py` 的下载/调用接口中，每次模型被下载/调用时递增 `download_count`
3. 创建 APScheduler 定时任务：每日扫描所有模型，将 `download_count` 超过阈值且 status=active 的模型标记为 `recommended`
4. 创建 APScheduler 定时任务：每月扫描 status=deprecated 超过 90 天的模型版本，删除其 MinIO 文件和数据库版本记录
5. 前端模型库页面：`recommended` 状态的模型卡片显示推荐标签；支持按 `recommended` 状态筛选

**验证**：

- 多次下载某模型后，等待每日定时任务执行，该模型状态自动变为 `recommended`
- 前端模型列表中推荐模型显示标签
- 将模型标记为 deprecated，90 天后执行清理任务，MinIO 中对应文件被删除

---

### Step 4.5 前端 — 设置与权限管理页面

**目标**：实现用户管理、项目成员管理和权限配置界面。

**指令**：

1. 实现设置页面 `/settings`：
   - 用户管理 Tab（仅 admin 可见）：用户列表表格（用户名、全局角色、创建时间）、新增用户弹窗、编辑角色弹窗、删除二次确认
   - 项目成员 Tab：当前项目的成员列表、添加成员弹窗（选择用户和角色）、移除成员
   - 优化调度 Tab：配置持续优化的周期和参数
2. 非管理员访问 `/settings` 时，仅显示项目成员 Tab 和优化调度 Tab

**验证**：

- admin 用户可看到用户管理 Tab，viewer 用户看不到
- 添加新用户后，用户列表刷新出现新记录
- 切换项目后，项目成员列表更新为对应项目的成员
- 配置优化调度后，APScheduler 注册对应的定时任务

---

## 验证总则

每个 Step 完成后，必须同时满足以下条件才能进入下一步：

1. 该 Step 所有"验证"条目全部通过
2. 前一步的功能未被破坏（无回归）
3. `docker-compose up` 后全系统可正常启动
