# 飞行试验环境构建系统

基于强化学习的飞行试验环境构建系统（B/S 架构）。根据用户需求自动生成 Gymnasium 兼容的飞行试验环境，支持动态调整和智能优化。

## 功能特性

| 模块 | 功能 |
|------|------|
| 环境管理 | 创建/编辑/删除环境，3D 预览，导入/导出 |
| 训练监控 | 实时训练指标曲线，WebSocket 实时推送 |
| 优化中心 | 四维质量评估（多样性/挑战性/真实性/有效性），贝叶斯优化 |
| 模型管理 | 上传/版本管理/下载，三级权限控制 |
| 用户管理 | 用户 CRUD，角色分配，密码重置 |
| 项目管理 | 项目创建/删除，成员管理，权限控制 |

## 技术栈

- **前端**：Vue 3 + TypeScript + Element Plus + Three.js + ECharts
- **后端**：FastAPI + SQLAlchemy + Celery + Redis
- **数据库**：PostgreSQL 15 + MinIO（文件存储）

---

## 快速开始

### 方式一：Docker 一键部署（推荐）

**前提条件**：安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/)

```bash
# 1. 双击 docker-start.bat 或运行：
docker compose up -d --build

# 2. 访问
#    前端：http://localhost
#    后端：http://localhost:8000
#    MinIO：http://localhost:9001
```

**停止服务**：双击 `docker-stop.bat` 或运行 `docker compose down`

### 方式二：本地开发环境

**前提条件**：
- Python 3.10+
- Node.js 18+
- PostgreSQL 14+（需创建 `fltect` 数据库）
- Redis

```bash
# 1. 一键安装（双击 setup.bat 或运行）：
.\install.ps1

# 2. 启动：
.\start_dev.ps1
```

---

## 默认账号

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123 | 管理员 |

## 角色权限

| 角色 | 权限 |
|------|------|
| admin | 所有功能 + 用户管理 |
| configurer | 环境/模型/优化配置 |
| viewer | 只读 |

---

## 使用流程

### 1. 创建项目

1. 登录后点击右上角项目选择器
2. 输入项目名称创建

### 2. 创建环境

1. 进入「环境管理」页面
2. 点击「新建环境」
3. 选择模板或自定义配置
4. 等待生成完成，查看 3D 预览

### 3. 训练监控

1. 进入「训练监控」页面
2. 选择环境开始训练
3. 实时查看训练曲线

### 4. 智能优化

1. 进入「优化中心」页面
2. 选择环境进行评估
3. 点击「智能优化」自动寻找最优配置

### 5. 用户管理

1. 进入「设置」页面（需要 admin 权限）
2. 创建/编辑/删除用户
3. 管理项目成员和角色

---

## 端口配置

编辑 `.env` 文件修改端口：

```env
FRONTEND_PORT=80      # 前端
BACKEND_PORT=8000     # 后端
POSTGRES_PORT=5432    # 数据库
REDIS_PORT=6379       # Redis
MINIO_API_PORT=9000   # MinIO API
MINIO_CONSOLE_PORT=9001  # MinIO 控制台
```

---

## 项目结构

```
├── backend/              # Python 后端
│   ├── app/
│   │   ├── api/          # API 路由
│   │   ├── core/         # 配置、安全
│   │   ├── models/       # 数据模型
│   │   ├── schemas/      # Pydantic 模型
│   │   ├── services/     # 业务逻辑
│   │   └── tasks/        # Celery 异步任务
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/             # Vue 前端
│   ├── src/
│   │   ├── api/          # Axios 配置
│   │   ├── views/        # 页面组件
│   │   ├── stores/       # Pinia 状态
│   │   └── router/       # 路由配置
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml    # Docker 编排
├── install.ps1           # 一键安装脚本
├── start_dev.ps1         # 开发启动脚本
└── docker-start.bat      # Docker 启动
```

---

## 常见问题

**Q: Docker 启动后访问不了？**
A: 等待 1-2 分钟让服务完全启动，检查 `docker compose logs` 查看日志。

**Q: 数据库连接失败？**
A: 确保 PostgreSQL 服务已启动，检查用户名密码是否正确。

**Q: 如何重置数据库？**
A: `docker compose down -v && docker compose up -d --build`（会清除数据）
