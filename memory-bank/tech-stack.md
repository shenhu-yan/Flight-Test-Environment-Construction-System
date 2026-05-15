# 技术栈选型文档

## 1. 选型原则

简单且健壮——每层只选一个主力，拒绝同类技术并列，用最少的零件拼出完整系统。

## 2. 全景图

```
┌──────────────────────────────────────────────────────────┐
│  前端                                                     │
│  Vue 3 + Vite + TypeScript + Pinia + Vue Router           │
│  │ Three.js (3D)    │ ECharts (图表)   │ Element Plus (UI)│
├──────────────────────────────────────────────────────────┤
│  网关                                                     │
│  Nginx                                                    │
├──────────────────────────────────────────────────────────┤
│  后端                                                     │
│  FastAPI + Uvicorn + SQLAlchemy + Alembic + Pydantic       │
│  │ Celery (任务队列) │ APScheduler (定时) │ python-jose    │
│  │ jsbsim │ scikit-optimize (贝叶斯优化)                   │
├──────────────────────────────────────────────────────────┤
│  数据层                                                   │
│  PostgreSQL │ MinIO │ Redis                               │
└──────────────────────────────────────────────────────────┘
```

## 3. 详细选型

### 3.1 前端

| 技术 | 版本 | 职责 | 选型理由 |
| :--- | :--- | :--- | :--- |
| **Vue 3** | 3.4+ | UI 框架 | Composition API 写法简洁；国内生态完善、中文文档齐全 |
| **Vite** | 5.x | 构建工具 | 冷启动 < 1s；Vue 官方推荐；零配置开箱即用 |
| **TypeScript** | 5.x | 类型系统 | 编译期兜底，减少低级错误；IDE 支持好 |
| **Pinia** | 2.x | 状态管理 | Vue 3 官方方案；API 比 Vuex 简单一半；TS 直接推导类型 |
| **Vue Router** | 4.x | 路由 | Vue 官方路由，无替代必要 |
| **Element Plus** | 2.x | UI 组件库 | Vue 3 组件最全的中文友好库；表格/表单/弹窗开箱即用；免去自建组件的工程量 |
| **Three.js** | r160+ | 三维渲染 | JSBSim 场景渲染的业界标配；OrbitControls/粒子系统/几何体全内置 |
| **ECharts** | 5.x | 数据可视化 | 曲线/柱状图/热力图/雷达图全有；实时数据流刷新成熟；中文社区最大 |

**不选的为什么**：

- React：需要额外引入 Hooks 心智模型，本系统没有需要 React 生态的理由
- D3.js：底层绑定的绘图库，ECharts 封装更高级、开发更快
- Cesium：3D GIS 引擎，偏重地理信息，本系统不需要地球级渲染

### 3.2 后端

| 技术 | 版本 | 职责 | 选型理由 |
| :--- | :--- | :--- | :--- |
| **FastAPI** | 0.110+ | Web 框架 | 原生 async + WebSocket；Pydantic 自动校验；自带 OpenAPI 文档；与 JSBSim 同为 Python 生态，零桥接成本 |
| **Uvicorn** | 0.29+ | ASGI 服务器 | FastAPI 官方推荐；基于 uvloop，异步性能足够 |
| **SQLAlchemy** | 2.x | ORM | Python ORM 事实标准；2.0 异步 API 成熟；支持 PostgreSQL JSONB 字段 |
| **Alembic** | 1.13+ | 数据库迁移 | SQLAlchemy 官方迁移工具；版本化的 schema 变更，团队协作不乱 |
| **Pydantic** | 2.x | 数据校验 | FastAPI 内置依赖；请求/响应模型自动校验；JSON Schema 导出 |
| **APScheduler** | 3.10+ | 定时任务 | 轻量：无需额外部署调度服务；支持 Cron/Interval 触发；满足持续优化周期任务 |
| **Celery** | 5.3+ | 异步任务队列 | 环境生成/批量生成/优化迭代等长耗时任务异步执行；Redis 作 broker 和 backend；避免 JSBSim 阻塞请求线程 |
| **python-jose** | 3.3+ | JWT | 签发/验证 token；纯 Python 实现，无系统依赖 |
| **passlib[bcrypt]** | 1.7+ | 密码哈希 | bcrypt 自适应哈希；业界标配 |
| **jsbsim** | 1.1+ | 飞行动力学仿真 | 本系统选定的固定翼仿真引擎；Python 绑定直接 pip 安装 |
| **scikit-optimize** | 0.9+ | 贝叶斯优化 | 基于 scikit-learn 生态；API 极简（`ask`/`tell`）；无需 GPU |
| **minio** | 7.x | MinIO Python SDK | 文件上传/下载/预签名 URL；S3 兼容 |
| **redis[hiredis]** | 5.x | Redis 客户端 | 支持 Streams（消息队列）+ 缓存 + 会话；hiredis 加速解析 |

**不选的为什么**：

- Django：同步框架，WebSocket 需要额外引入 Channels，复杂度翻倍
- Flask + SocketIO：非原生 async，手动管理协程成本高
- Celery 替代品（Huey/Dramatiq）：Celery 生态最成熟、文档最全；Redis 兼作 broker/backend 不引入新依赖
- Kafka/RabbitMQ：本系统指标上报量小，Redis Streams 完全够用，引入 Kafka 属于过度设计

### 3.3 数据层

| 技术 | 版本 | 职责 | 选型理由 |
| :--- | :--- | :--- | :--- |
| **PostgreSQL** | 14+ | 关系数据库 | JSONB 字段存储环境配置/模板参数，无需 NoSQL 副库；行级安全策略支持项目隔离；事务可靠 |
| **MinIO** | latest | 文件存储 | S3 兼容 API；单机部署一条命令启动；存环境包/模型文件/JSBSim XML 配置 |
| **Redis** | 7.x | 缓存 + 消息 | 会话/指标缓冲用 KV；指标流用 Streams；一个组件覆盖两个需求 |

**不选的为什么**：

- MySQL：JSON 字段支持弱于 PostgreSQL（无 JSONB 索引），本系统大量 JSON 配置存储
- MongoDB：本系统有明确的关系模型（项目→任务→环境），用文档库反而丧失关联查询能力
- S3 云存储：MinIO 本地部署即可，无需引入云服务依赖

### 3.4 网关与部署

| 技术 | 版本 | 职责 | 选型理由 |
| :--- | :--- | :--- | :--- |
| **Nginx** | 1.24+ | 反向代理 | 静态资源托管 + 反向代理 + WebSocket 升级；工业级稳定 |
| **Docker** | 24+ | 容器化部署 | docker-compose 一键拉起全部服务（FastAPI/PostgreSQL/Redis/MinIO/Nginx）；环境一致性 |

## 4. 依赖清单

### 4.1 前端 package.json 核心依赖

```json
{
  "dependencies": {
    "vue": "^3.4",
    "vue-router": "^4.3",
    "pinia": "^2.1",
    "element-plus": "^2.6",
    "three": "^0.162",
    "echarts": "^5.5",
    "axios": "^1.6"
  },
  "devDependencies": {
    "vite": "^5.2",
    "typescript": "^5.4",
    "@vitejs/plugin-vue": "^5.0",
    "vue-tsc": "^2.0"
  }
}
```

### 4.2 后端 requirements.txt 核心依赖

```
fastapi>=0.110
uvicorn[standard]>=0.29
sqlalchemy[asyncio]>=2.0
asyncpg>=0.29
alembic>=1.13
pydantic>=2.6
python-jose[cryptography]>=3.3
passlib[bcrypt]>=1.7
python-multipart>=0.0.9
redis[hiredis]>=5.0
minio>=7.2
apscheduler>=3.10
celery[redis]>=5.3
jsbsim>=1.1
scikit-optimize>=0.9
numpy>=1.26
aiofiles>=23.0
```

## 5. 版本与兼容性

| 约束 | 最低版本 | 说明 |
| :--- | :--- | :--- |
| Python | 3.10+ | `match` 语法、`tuple[...]` 类型标注 |
| Node.js | 18+ | Vite 5 运行要求 |
| 浏览器 | Chrome 90+ / Edge 90+ / Firefox 90+ | Three.js WebGL 2.0 兼容底线 |

## 6. 为什么这套栈"简单且健壮"

| 维度 | 体现 |
| :--- | :--- |
| **语言统一** | 后端 Python 与 JSBSim/scikit-optimize 同生态，零桥接；前端纯 TypeScript |
| **组件最少** | 数据层 3 个（PG/MinIO/Redis），后端 1 个框架（FastAPI），前端 1 个框架（Vue 3） |
| **无多余中间件** | 不上 Kafka/RabbitMQ/Nginx 之外的网关；APScheduler 进程内跑定时任务，Celery+Redis 跑长耗时异步任务，指标流 Redis Streams 进程内消费 |
| **成熟可靠** | 每一项都是该领域的头号选择（FastAPI 在 Python async Web、Vue 3 在国内前端、PostgreSQL 在关系库、Celery 在 Python 任务队列），文档和社区问题量足够踩坑无忧 |
| **一键部署** | Docker Compose 一个 `docker-compose.yml` 拉起全部 7 个服务（含 Celery worker） |
