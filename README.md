# 飞行试验管理系统

> Flight Test System — 用于管理和跟踪飞行试验全流程的 Web 应用系统。

## 项目概述

本系统提供飞行试验数据管理、任务调度、报告生成等功能，采用前后端分离架构，支持 Docker 一键部署。

## 技术栈

| 层级 | 技术 |
|------|------|
| **前端** | Vue 3 + TypeScript + Vite + Ant Design Vue |
| **后端** | Python 3.11 + FastAPI + SQLAlchemy + Celery |
| **数据库** | PostgreSQL 14 |
| **缓存/消息** | Redis 7 |
| **对象存储** | MinIO (S3 兼容) |
| **反向代理** | Nginx |
| **容器化** | Docker + Docker Compose |

## 前置要求

### 开发环境
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+ (本地运行或 Docker)
- Redis 7+ (本地运行或 Docker)
- MinIO (可选，用于文件存储)

### Docker 部署
- Docker 20.10+
- Docker Compose v2+

## 快速开始

### 开发模式

1. **克隆项目**

```bash
git clone <repository-url>
cd flight-test-system
```

2. **配置环境变量**

```bash
cp .env.example .env
# 编辑 .env 文件，修改数据库、Redis 等连接信息
```

3. **启动后端**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

4. **启动前端**

```bash
cd frontend
npm install
npm run dev
```

5. **启动 Celery Worker（可选）**

```bash
cd backend
celery -A app.celery_app worker -l info
```

6. **一键启动（推荐）**

```bash
# PowerShell
.\start_dev.ps1

# Bash
bash start_dev.sh
```

### Docker 部署

1. **配置环境变量**

```bash
cp .env.example .env
# 编辑 .env 文件
```

2. **构建并启动所有服务**

```bash
docker compose up -d --build
```

3. **查看服务状态**

```bash
docker compose ps
```

4. **查看日志**

```bash
docker compose logs -f backend
```

5. **停止服务**

```bash
docker compose down
```

6. **清除数据卷**

```bash
docker compose down -v
```

### 部分Docker部署
1. **启动依赖服务**

```bash
docker compose -f docker-compose.dev.yml up -d
```
2. **启动后端**
```bash
cd backend

# 创建虚拟环境（如果还没有）
python -m venv .venv

# 激活虚拟环境
.venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 运行数据库迁移（如果有）
alembic upgrade head

# 启动后端
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

3. **启动前端**
```bash
cd frontend

# 安装依赖（如果还没安装）
npm install

# 启动前端
npm run dev
```

4. **快速测试**
```bash
# 测试后端
curl http://localhost:8000/docs

# 测试前端（浏览器打开）
start http://localhost:3000

# 测试 MinIO 控制台
start http://localhost:9001
```
## 默认凭据

| 服务 | 用户名 | 密码 |
|------|--------|------|
| **管理后台** | admin | admin123 |
| **PostgreSQL** | flight_admin | flight_secret |
| **MinIO Console** | minioadmin | miniosecret |

> ⚠️ 生产环境请务必修改所有默认密码！

## API 文档

启动后端服务后，访问以下地址：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 项目结构

```
flight-test-system/
├── backend/                  # 后端代码
│   ├── app/                  # 应用主模块
│   │   ├── api/              # API 路由
│   │   ├── core/             # 核心配置（安全、数据库等）
│   │   ├── models/           # 数据模型
│   │   ├── schemas/          # Pydantic 模式
│   │   ├── services/         # 业务逻辑
│   │   └── tasks/            # Celery 任务
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                 # 前端代码
│   ├── src/
│   │   ├── api/              # API 请求
│   │   ├── components/       # 公共组件
│   │   ├── views/            # 页面视图
│   │   ├── stores/           # Pinia 状态管理
│   │   └── router/           # 路由配置
│   ├── Dockerfile
│   └── package.json
├── nginx/                    # Nginx 配置
│   ├── nginx.conf
│   └── frontend.conf
├── docker-compose.yml        # Docker Compose 编排
├── .env.example              # 环境变量模板
├── .gitignore
├── start_dev.ps1             # Windows 开发启动脚本
├── start_dev.sh              # Linux/Mac 开发启动脚本
└── README.md
```

## 服务端口

| 服务 | 端口 | 说明 |
|------|------|------|
| Nginx | 80 | 前端入口 + API 代理 |
| Backend | 8000 | FastAPI 后端 |
| PostgreSQL | 5432 | 数据库 |
| Redis | 6379 | 缓存 / 消息队列 |
| MinIO API | 9000 | 对象存储 API |
| MinIO Console | 9001 | 对象存储管理界面 |

## License

MIT
