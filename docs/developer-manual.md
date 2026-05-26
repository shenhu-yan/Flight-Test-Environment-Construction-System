# 飞行试验环境构建系统 开发手册

**版本：1.0**
**日期：2026年5月**

---

## 第一章 概述

### 1.1 文档目的

本文档旨在为开发人员提供飞行试验环境构建系统的完整开发指南，包括环境搭建、配置说明、开发规范等内容。通过阅读本文档，开发人员可以快速上手项目开发，理解系统架构，并能够独立完成模块开发和调试工作。

### 1.2 项目简介

飞行试验环境构建系统是一套基于强化学习的飞行试验环境自动生成平台。系统根据用户需求自动生成 Gymnasium 兼容的飞行试验环境，支持动态调整和智能优化。V1.0 版本聚焦固定翼飞行器。

### 1.3 技术栈概览

| 层级 | 技术 | 版本 | 用途 |
|------|------|------|------|
| 前端框架 | Vue | 3.5+ | 响应式 UI 框架 |
| UI 组件库 | Element Plus | 2.14+ | 企业级 UI 组件 |
| 3D 渲染 | Three.js | 0.184+ | 三维场景预览 |
| 数据可视化 | ECharts | 6.0+ | 图表展示 |
| 后端框架 | FastAPI | 0.110+ | 异步 Web 框架 |
| ORM | SQLAlchemy | 2.0+ | 数据库操作 |
| 异步任务 | Celery | 5.3+ | 分布式任务队列 |
| 缓存/消息 | Redis | 7.0+ | 缓存和消息代理 |
| 数据库 | PostgreSQL | 15+ | 关系型数据库 |
| 对象存储 | MinIO | Latest | 文件存储 |
| 版本控制 | Git | 2.30+ | 代码版本管理 |
| 容器化 | Docker | 24+ | 应用容器化 |

### 1.4 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         用户浏览器                               │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    Vue 3 + TypeScript                     │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐  │  │
│  │  │ 环境管理 │ │ 训练监控 │ │ 优化中心 │ │  模型管理  │  │  │
│  │  │ 模块     │ │ 模块     │ │ 模块     │ │  模块      │  │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP/WebSocket
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Nginx 反向代理                              │
│              静态资源托管 + API 代理 + WebSocket 转发            │
│                          (端口 80)                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Proxy Pass
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI 后端服务                               │
│                       (端口 8000)                                │
│  ┌──────────────┐ ┌──────────────┐ ┌────────────────────────┐ │
│  │   环境生成   │ │   动态调整   │ │      智能优化          │ │
│  │   服务       │ │   服务       │ │      服务              │ │
│  └──────────────┘ └──────────────┘ └────────────────────────┘ │
│  ┌──────────────┐ ┌──────────────┐ ┌────────────────────────┐ │
│  │   模型管理   │ │   用户认证   │ │      WebSocket         │ │
│  │   服务       │ │   服务       │ │      服务              │ │
│  └──────────────┘ └──────────────┘ └────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
            │                 │                 │
            │                 │                 │
            ▼                 ▼                 ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  PostgreSQL  │    │    Redis     │    │    MinIO     │
│  (端口5432)  │    │  (端口6379)  │    │  (端口9000)  │
│              │    │              │    │              │
│  业务数据    │    │  缓存/消息   │    │  文件存储    │
└──────────────┘    └──────────────┘    └──────────────┘
```

---

## 第二章 开发环境搭建

### 2.1 操作系统要求

本系统支持以下操作系统进行开发：

| 操作系统 | 版本要求 | 备注 |
|----------|----------|------|
| Windows | 10/11 64位 | 推荐开发环境 |
| macOS | 12.0+ | 需要额外配置 |
| Ubuntu | 20.04+ | 推荐服务器部署 |
| CentOS | 8+ | 推荐服务器部署 |

本文档以 Windows 11 为主要开发环境进行说明。

### 2.2 Python 环境配置

#### 2.2.1 安装 Python

1. 访问 Python 官方网站：https://www.python.org/downloads/

2. 下载 Python 3.11 版本（推荐）

3. 运行安装程序，**务必勾选以下选项**：
   - [x] Install launcher for all users (recommended)
   - [x] Add Python 3.11 to PATH
   - [x] pip
   - [x] tcl/tk and IDLE
   - [x] py launcher

4. 选择 "Customize installation"，确保以下组件被选中：
   - pip
   - tcl/tk and IDLE
   - Python test suite
   - py launcher
   - for all users (requires admin privileges)

5. 安装完成后，打开命令提示符验证：

```cmd
python --version
# 输出: Python 3.11.x

pip --version
# 输出: pip 24.x.x from C:\Python311\Lib\site-packages\pip (python 3.11)
```

#### 2.2.2 配置 pip 镜像（国内用户推荐）

为了加速依赖包下载，配置国内镜像源：

```cmd
# 设置全局镜像（清华大学源）
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 验证配置
pip config list

# 输出示例:
# global.index-url='https://pypi.tuna.tsinghua.edu.cn/simple'
```

或者创建 pip 配置文件：

```ini
# %APPDATA%\pip\pip.ini (Windows)
# ~/.pip/pip.conf (Linux/Mac)

[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
trusted-host = pypi.tuna.tsinghua.edu.cn
```

#### 2.2.3 创建虚拟环境

虚拟环境用于隔离项目依赖，避免不同项目之间的包冲突。

```cmd
# 进入项目后端目录
cd Flight-Test-Environment-Construction-System\backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境 (Windows)
.\venv\Scripts\activate

# 激活后命令行前缀会显示 (venv)
(venv) C:\...\backend>

# 验证虚拟环境
where python
# 输出: C:\...\backend\venv\Scripts\python.exe
```

#### 2.2.4 安装后端依赖

```cmd
# 确保虚拟环境已激活
# 升级 pip
python -m pip install --upgrade pip

# 安装依赖
pip install -r requirements.txt

# 验证安装
pip list
```

**requirements.txt 依赖说明**：

| 包名 | 版本要求 | 用途说明 |
|------|----------|----------|
| fastapi | >=0.110 | 高性能异步 Web 框架 |
| uvicorn[standard] | >=0.29 | ASGI 服务器 |
| sqlalchemy[asyncio] | >=2.0 | 异步 ORM 框架 |
| asyncpg | >=0.29 | PostgreSQL 异步驱动 |
| alembic | >=1.13 | 数据库迁移工具 |
| pydantic | >=2.6 | 数据验证和序列化 |
| pydantic-settings | >=2.0 | 配置管理 |
| python-jose[cryptography] | >=3.3 | JWT 令牌处理 |
| passlib[bcrypt] | >=1.7 | 密码哈希加密 |
| python-multipart | >=0.0.9 | 表单数据解析 |
| redis[hiredis] | >=5.0 | Redis 客户端 |
| minio | >=7.2 | MinIO 对象存储客户端 |
| apscheduler | >=3.10 | 定时任务调度 |
| celery[redis] | >=5.3 | 分布式任务队列 |
| jsbsim | >=1.1 | 飞行模拟引擎 |
| scikit-optimize | >=0.9 | 贝叶斯优化 |
| numpy | >=1.26 | 数值计算 |
| aiofiles | >=23.0 | 异步文件操作 |
| bcrypt | >=4.0 | 密码加密 |
| httpx | >=0.27 | HTTP 客户端 |

### 2.3 Node.js 环境配置

#### 2.3.1 安装 Node.js

1. 访问 Node.js 官方网站：https://nodejs.org/

2. 下载 LTS 版本（推荐 20.x）

3. 运行安装程序，使用默认配置安装

4. 安装完成后，打开命令提示符验证：

```cmd
node --version
# 输出: v20.x.x

npm --version
# 输出: 10.x.x
```

#### 2.3.2 配置 npm 镜像（国内用户推荐）

```cmd
# 设置淘宝镜像
npm config set registry https://registry.npmmirror.com

# 验证配置
npm config get registry
# 输出: https://registry.npmmirror.com

# 或者安装 nrm 管理多个镜像源
npm install -g nrm

# 使用淘宝源
nrm use taobao

# 查看可用源
nrm ls
```

#### 2.3.3 安装前端依赖

```cmd
# 进入前端目录
cd Flight-Test-Environment-Construction-System\frontend

# 安装依赖
npm install

# 安装完成后会生成 node_modules 目录和 package-lock.json
```

**前端依赖说明**：

| 包名 | 版本 | 用途说明 |
|------|------|----------|
| vue | ^3.5.34 | Vue 3 核心框架 |
| vue-router | ^5.0.7 | 路由管理 |
| pinia | ^3.0.4 | 状态管理 |
| element-plus | ^2.14.0 | UI 组件库 |
| @element-plus/icons-vue | ^2.3.2 | Element Plus 图标 |
| axios | ^1.16.1 | HTTP 请求库 |
| echarts | ^6.0.0 | 数据可视化 |
| three | ^0.184.0 | 3D 渲染引擎 |

#### 2.3.4 开发依赖说明

| 包名 | 版本 | 用途说明 |
|------|------|----------|
| vite | ^8.0.12 | 构建工具 |
| typescript | ~6.0.2 | TypeScript 编译器 |
| vue-tsc | ^3.2.8 | Vue 类型检查 |
| @vitejs/plugin-vue | ^6.0.6 | Vite Vue 插件 |

### 2.4 IDE 配置

#### 2.4.1 VS Code 安装与配置

**安装 VS Code**

1. 访问 https://code.visualstudio.com/
2. 下载并安装 Visual Studio Code

**安装必要扩展**

在 VS Code 扩展市场搜索并安装以下扩展：

| 扩展名称 | 发布者 | 用途 |
|----------|--------|------|
| Python | Microsoft | Python 语言支持 |
| Pylance | Microsoft | Python 智能提示 |
| Vue - Official (Volar) | Vue | Vue 3 语言支持 |
| ESLint | Microsoft | JavaScript/TypeScript 代码检查 |
| Prettier | Prettier | 代码格式化 |
| GitLens | GitLens | Git 增强功能 |
| Thunder Client | Thunder Client | API 测试 |

**配置 Python 解释器**

1. 按 `Ctrl+Shift+P` 打开命令面板
2. 输入 "Python: Select Interpreter"
3. 选择 `.\venv\Scripts\python.exe`

**配置 settings.json**

按 `Ctrl+Shift+P`，输入 "Preferences: Open User Settings (JSON)"，添加：

```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/backend/venv/Scripts/python.exe",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.fixAll.eslint": "explicit"
    },
    "[python]": {
        "editor.defaultFormatter": "ms-python.python",
        "editor.tabSize": 4
    },
    "[vue]": {
        "editor.defaultFormatter": "Vue.volar"
    },
    "[typescript]": {
        "editor.defaultFormatter": "esbenp.prettier-vscode"
    },
    "[json]": {
        "editor.defaultFormatter": "esbenp.prettier-vscode"
    },
    "files.associations": {
        "*.vue": "vue"
    }
}
```

#### 2.4.2 PyCharm 配置（可选）

1. 安装 PyCharm Professional 或 Community Edition
2. 打开项目，选择 backend 目录
3. 配置 Python 解释器：File → Settings → Project → Python Interpreter
4. 选择 existing environment，指向 `venv\Scripts\python.exe`

### 2.5 数据库环境配置

#### 2.5.1 PostgreSQL 安装

**Windows 安装步骤**

1. 访问 https://www.postgresql.org/download/windows/
2. 下载 PostgreSQL 15 安装程序
3. 运行安装程序：
   - 安装目录：`C:\Program Files\PostgreSQL\15`
   - 数据目录：`C:\Program Files\PostgreSQL\15\data`
   - 端口：5432（默认）
   - 设置超级用户密码：**务必记住！**
   - 区域设置：Default locale

4. 安装完成后，PostgreSQL 服务会自动启动

**验证安装**

```cmd
# 方法1: 使用 psql 命令行
"C:\Program Files\PostgreSQL\15\bin\psql.exe" -U postgres

# 方法2: 添加到 PATH 后直接使用
psql -U postgres

# 输入密码后进入 psql 命令行
postgres=#
```

**Linux (Ubuntu) 安装**

```bash
# 更新包索引
sudo apt update

# 安装 PostgreSQL
sudo apt install postgresql postgresql-contrib

# 启动服务
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 切换到 postgres 用户
sudo -u postgres psql
```

#### 2.5.2 创建数据库

连接 PostgreSQL 后执行以下 SQL：

```sql
-- 创建数据库
CREATE DATABASE fltect
    WITH
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'Chinese (Simplified)_China.936'
    LC_CTYPE = 'Chinese (Simplified)_China.936'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1
    IS_TEMPLATE = False;

-- 查看数据库
\l

-- 连接到 fltect 数据库
\c fltect

-- 查看当前数据库
SELECT current_database();
```

#### 2.5.3 配置数据库连接

**方式一：修改配置文件**

编辑 `backend/app/core/config.py`：

```python
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    PROJECT_NAME: str = "Flight Test Environment Construction System"
    VERSION: str = "1.0.0"

    # 数据库配置
    DATABASE_URL: str = "postgresql+asyncpg://postgres:your_password@localhost:5432/fltect"

    # Redis 配置
    REDIS_URL: str = "redis://localhost:6379/0"

    # MinIO 配置
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "fltect"

    # JWT 配置
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # CORS 配置
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Celery 配置
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
```

**方式二：使用环境变量**

创建 `backend/.env` 文件：

```env
DATABASE_URL=postgresql+asyncpg://postgres:your_password@localhost:5432/fltect
REDIS_URL=redis://localhost:6379/0
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=fltect
JWT_SECRET_KEY=your-secret-key-change-in-production
```

**注意**：请将 `your_password` 替换为实际的 PostgreSQL 密码。

#### 2.5.4 数据库初始化

启动后端服务时，系统会自动创建所有数据表：

```cmd
# 激活虚拟环境
cd backend
.\venv\Scripts\activate

# 启动服务（自动创建表）
python run.py
```

**数据库表结构说明**

系统共包含 18 张数据表：

| 表名 | 说明 | 主要字段 |
|------|------|----------|
| users | 用户表 | id, username, password_hash, global_role |
| projects | 项目表 | id, name, description, created_by |
| project_roles | 项目角色表 | id, user_id, project_id, role |
| tasks | 任务表 | id, project_id, name, description |
| templates | 模板表 | id, name, aircraft_type, config |
| strategies | 策略表 | id, name, condition, action |
| envs | 环境表 | id, project_id, name, config, status |
| env_snapshots | 环境快照表 | id, env_id, config, trigger_type |
| adjustment_history | 调整历史表 | id, env_id, snapshot_before, snapshot_after |
| env_evaluations | 环境评估表 | id, env_id, diversity_score, challenge_score |
| training_metrics | 训练指标表 | id, env_id, episode_reward, success_rate |
| models | 模型表 | id, project_id, name, type, status |
| model_versions | 模型版本表 | id, model_id, version, storage_path |
| optimization_tasks | 优化任务表 | id, project_id, param_space, status |
| optimization_reports | 优化报告表 | id, task_id, before_scores, after_scores |
| notifications | 通知表 | id, user_id, title, content, read |
| operation_logs | 操作日志表 | id, user_id, action, resource_type |
| system_logs | 系统日志表 | id, level, module, message |

#### 2.5.5 Redis 配置

**Windows 安装 Redis**

1. 访问 https://github.com/tporadowski/redis/releases
2. 下载 Redis-x64-x.x.x.zip
3. 解压到目录，如 `C:\Redis`
4. 启动 Redis：

```cmd
# 直接运行
C:\Redis\redis-server.exe

# 或安装为 Windows 服务
C:\Redis\redis-server.exe --service-install
C:\Redis\redis-server.exe --service-start
```

**验证 Redis**

```cmd
# 连接 Redis
C:\Redis\redis-cli.exe

# 测试连接
127.0.0.1:6379> ping
PONG

# 查看信息
127.0.0.1:6379> info server
```

**Linux 安装 Redis**

```bash
# 安装
sudo apt install redis-server

# 启动
sudo systemctl start redis
sudo systemctl enable redis

# 测试
redis-cli ping
# 输出: PONG
```

**配置 Redis 连接**

编辑 `backend/app/core/config.py`：

```python
REDIS_URL: str = "redis://localhost:6379/0"
CELERY_BROKER_URL: str = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
```

#### 2.5.6 MinIO 配置（可选）

MinIO 用于存储环境文件、模型文件等。

**下载 MinIO**

1. 访问 https://min.io/download
2. 下载 Windows 版本

**启动 MinIO**

```cmd
# 创建数据目录
mkdir minio-data

# 启动 MinIO
minio.exe server .\minio-data

# 访问控制台
# http://localhost:9001
# 用户名: minioadmin
# 密码: minioadmin
```

**配置 MinIO**

```python
MINIO_ENDPOINT: str = "localhost:9000"
MINIO_ACCESS_KEY: str = "minioadmin"
MINIO_SECRET_KEY: str = "minioadmin"
MINIO_BUCKET: str = "fltect"
```

---

## 第三章 项目结构详解

### 3.1 目录结构

```
Flight-Test-Environment-Construction-System/
├── backend/                    # 后端 Python 项目
│   ├── app/                   # 应用代码
│   │   ├── api/              # API 路由模块
│   │   ├── core/             # 核心配置
│   │   ├── models/           # 数据库模型
│   │   ├── schemas/          # Pydantic 模型
│   │   ├── services/         # 业务逻辑
│   │   ├── tasks/            # Celery 任务
│   │   └── seed/             # 种子数据
│   ├── alembic/              # 数据库迁移
│   ├── requirements.txt      # Python 依赖
│   ├── Dockerfile            # Docker 配置
│   └── run.py                # 启动脚本
├── frontend/                  # 前端 Vue 项目
│   ├── src/                   # 源代码
│   │   ├── api/             # API 配置
│   │   ├── components/      # 公共组件
│   │   ├── layout/          # 布局组件
│   │   ├── router/          # 路由配置
│   │   ├── stores/          # 状态管理
│   │   └── views/           # 页面组件
│   ├── public/                # 静态资源
│   ├── package.json           # npm 配置
│   ├── vite.config.ts         # Vite 配置
│   ├── tsconfig.json          # TypeScript 配置
│   └── Dockerfile             # Docker 配置
├── docs/                       # 文档目录
├── docker-compose.yml          # Docker 编排
├── .env                        # 环境变量
├── .gitignore                  # Git 忽略
├── README.md                   # 项目说明
├── Setup.md                    # 部署指南
├── install.ps1                 # Windows 安装脚本
├── start_dev.ps1               # 开发启动脚本
├── start.bat                   # Windows 启动批处理
├── docker-start.bat            # Docker 启动批处理
└── docker-stop.bat             # Docker 停止批处理
```

### 3.2 后端目录详解

#### 3.2.1 API 路由模块 (app/api/)

| 文件 | 说明 | 主要接口 |
|------|------|----------|
| auth.py | 认证接口 | login, logout, me |
| users.py | 用户管理 | CRUD, reset-password |
| projects.py | 项目管理 | CRUD, members |
| envs.py | 环境管理 | CRUD, adjust, rollback, train |
| models.py | 模型管理 | upload, download, versions |
| optimization.py | 优化接口 | evaluate, tasks |
| strategies.py | 策略管理 | CRUD |
| notifications.py | 通知管理 | list, read |
| logs.py | 日志管理 | operation, system |
| ws.py | WebSocket | metrics, adjustment, frontend |

#### 3.2.2 核心配置模块 (app/core/)

| 文件 | 说明 |
|------|------|
| config.py | 应用配置（数据库、Redis、JWT 等） |
| database.py | 数据库连接和会话管理 |
| security.py | 认证授权（JWT、密码加密、权限检查） |

**database.py 核心代码**

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings

# 创建异步引擎
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,  # 开发环境显示 SQL
    pool_pre_ping=True
)

# 创建异步会话工厂
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# 获取数据库会话
async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
```

**security.py 核心代码**

```python
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 令牌方案
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# 创建访问令牌
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

# 验证密码
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# 获取密码哈希
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# 获取当前用户
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(
        text("SELECT id, username, global_role FROM users WHERE username = :username"),
        {"username": username}
    )
    user = result.fetchone()
    if user is None:
        raise credentials_exception
    return {"id": user[0], "username": user[1], "global_role": user[2]}

# 要求管理员权限
async def require_admin(current_user: dict = Depends(get_current_user)):
    if current_user["global_role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user
```

#### 3.2.3 数据库模型 (app/models/)

| 文件 | 说明 |
|------|------|
| base.py | 基础模型类 |
| user.py | 用户模型 |
| project.py | 项目模型 |
| env.py | 环境模型 |
| model.py | 模型管理模型 |
| optimization.py | 优化任务模型 |

**base.py**

```python
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
```

**user.py 示例**

```python
from sqlalchemy import Column, String, DateTime
from app.models.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True)
    username = Column(String(64), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    global_role = Column(String(16), default="viewer")
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)
```

#### 3.2.4 业务逻辑 (app/services/)

| 文件 | 说明 |
|------|------|
| env_generator.py | 环境生成服务 |
| jsbsim_engine.py | JSBSim 飞行模拟引擎封装 |
| strategy_engine.py | 策略引擎（规则驱动） |
| evaluator.py | 环境质量评估器 |
| optimizer.py | 贝叶斯优化器 |
| training_service.py | 训练服务管理 |
| ws_manager.py | WebSocket 连接管理 |

**env_generator.py 核心代码**

```python
import json
import zipfile
from io import BytesIO
from minio import Minio
from app.core.config import settings

class EnvGenerator:
    def __init__(self):
        self.minio_client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=False,
        )

    async def generate(self, env_id: str, config: dict, project_id: str) -> str:
        """生成环境并上传到 MinIO"""
        # 1. 根据配置生成环境文件
        env_files = self._create_env_files(config)

        # 2. 打包为 ZIP
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for filename, content in env_files.items():
                zipf.writestr(filename, content)

        # 3. 上传到 MinIO
        storage_path = f"envs/{project_id}/{env_id}.zip"
        zip_buffer.seek(0)

        bucket = settings.MINIO_BUCKET
        if not self.minio_client.bucket_exists(bucket):
            self.minio_client.make_bucket(bucket)

        self.minio_client.put_object(
            bucket,
            storage_path,
            zip_buffer,
            length=zip_buffer.getbuffer().nbytes,
            content_type="application/zip",
        )

        return storage_path

    def _create_env_files(self, config: dict) -> dict:
        """根据配置创建环境文件"""
        files = {}

        # 创建 config.json
        files["config.json"] = json.dumps(config, indent=2)

        # 创建 scene.json (Three.js 预览数据)
        files["scene.json"] = json.dumps(self._generate_scene_data(config), indent=2)

        # 创建 Python 环境包
        files["__init__.py"] = ""
        files["env.py"] = self._generate_env_code(config)

        return files

    def _generate_scene_data(self, config: dict) -> dict:
        """生成 Three.js 预览数据"""
        import numpy as np

        terrain = config.get("terrain", {})
        obstacles = config.get("obstacles", {})

        return {
            "terrain": {
                "grid_size": [100, 100],
                "resolution": terrain.get("resolution", 1.0),
                "elevation": np.random.uniform(
                    terrain.get("elevation_min", 0),
                    terrain.get("elevation_max", 100),
                    (100, 100)
                ).tolist(),
            },
            "obstacles": [
                {
                    "type": "building",
                    "position": [float(np.random.uniform(0, 500)) for _ in range(3)],
                    "size": [10, 10, 20],
                }
                for _ in range(obstacles.get("count", 0))
            ],
            "waypoints": config.get("waypoints", []),
            "wind": {
                "direction": [1.0, 0.5, 0.0],
                "speed": config.get("atmosphere", {}).get("wind_speed", 5),
                "variability": 0.3,
            },
        }
```

#### 3.2.5 异步任务 (app/tasks/)

| 文件 | 说明 |
|------|------|
| env_tasks.py | 环境生成异步任务 |
| optimization_tasks.py | 优化任务 |

**env_tasks.py**

```python
from celery import Celery
from app.core.config import settings

# 创建 Celery 实例
celery_app = Celery(
    "worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

@celery_app.task
def generate_env_task(env_id: str, config: dict, project_id: str, user_id: str):
    """异步生成环境"""
    import asyncio
    from app.services.env_generator import EnvGenerator

    generator = EnvGenerator()

    # 运行异步代码
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        storage_path = loop.run_until_complete(
            generator.generate(env_id, config, project_id)
        )

        # 更新数据库状态
        # ...

        return {"status": "success", "storage_path": storage_path}
    finally:
        loop.close()
```

### 3.3 前端目录详解

#### 3.3.1 页面组件 (src/views/)

| 文件 | 说明 | 主要功能 |
|------|------|----------|
| Login.vue | 登录页 | 用户登录表单 |
| Envs.vue | 环境管理 | 环境配置、3D 预览、环境列表 |
| Monitor.vue | 训练监控 | 实时训练曲线、训练控制 |
| Optimization.vue | 优化中心 | 环境评估、智能优化 |
| Models.vue | 模型库 | 模型上传、版本管理 |
| Settings.vue | 设置 | 用户管理、项目成员管理 |

**Envs.vue 核心代码**

```vue
<template>
  <div class="envs-page">
    <el-row :gutter="20">
      <el-col :span="14">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>环境配置</span>
              <div>
                <el-button @click="uploadConfig">上传配置文件</el-button>
                <el-button type="primary" @click="generateEnv" :loading="generating">
                  生成环境
                </el-button>
              </div>
            </div>
          </template>

          <el-form :model="config" label-width="120px">
            <el-divider content-position="left">基本信息</el-divider>
            <el-form-item label="环境名称">
              <el-input v-model="envName" placeholder="请输入环境名称" />
            </el-form-item>

            <el-divider content-position="left">地形配置</el-divider>
            <el-form-item label="地形类型">
              <el-select v-model="config.terrain.type">
                <el-option label="平坦" value="flat" />
                <el-option label="丘陵" value="hilly" />
                <el-option label="山地" value="mountainous" />
              </el-select>
            </el-form-item>

            <!-- 更多配置项... -->
          </el-form>
        </el-card>
      </el-col>

      <el-col :span="10">
        <el-card class="preview-card">
          <template #header>
            <span>三维预览</span>
          </template>
          <EnvPreview3D v-if="sceneData" :sceneData="sceneData" />
          <el-empty v-else description="生成环境后可预览3D场景" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '@/api'
import { useProjectStore } from '@/stores/project'
import { ElMessage } from 'element-plus'
import EnvPreview3D from '@/components/EnvPreview3D.vue'

const projectStore = useProjectStore()
const envName = ref('')
const generating = ref(false)
const sceneData = ref<any>(null)

const config = ref({
  terrain: { type: 'flat', elevation_min: 0, elevation_max: 100, resolution: 1.0 },
  atmosphere: { wind_speed: 5, wind_direction: 90, visibility: 10000 },
  aircraft: { model: 'c172x', mass: 1043, wingspan: 11.0 },
  reward: { items: [], penalties: [] },
  obstacles: { count: 0, types: [], density: 0.0 },
  waypoints: []
})

const generateEnv = async () => {
  if (!projectStore.currentProject) {
    ElMessage.warning('请先选择项目')
    return
  }

  generating.value = true
  try {
    const response = await api.post('/api/envs', {
      project_id: projectStore.currentProject.id,
      name: envName.value,
      config: config.value
    })
    ElMessage.success('环境生成任务已提交')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '生成失败')
  } finally {
    generating.value = false
  }
}
</script>
```

#### 3.3.2 状态管理 (src/stores/)

| 文件 | 说明 |
|------|------|
| auth.ts | 认证状态管理 |
| project.ts | 项目状态管理 |

**auth.ts**

```typescript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'

interface User {
  id: string
  username: string
  global_role: string
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<User | null>(null)

  const isAuthenticated = computed(() => !!token.value)

  async function login(username: string, password: string) {
    const response = await api.post('/api/auth/login', { username, password })
    token.value = response.data.access_token
    localStorage.setItem('token', response.data.access_token)
    await fetchUser()
  }

  async function fetchUser() {
    try {
      const response = await api.get('/api/auth/me')
      user.value = response.data.data
    } catch (error) {
      logout()
    }
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
  }

  return { token, user, isAuthenticated, login, fetchUser, logout }
})
```

**project.ts**

```typescript
import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api'

interface Project {
  id: string
  name: string
  description?: string
  created_by?: string
  created_at?: string
}

export const useProjectStore = defineStore('project', () => {
  const projects = ref<Project[]>([])
  const currentProject = ref<Project | null>(null)

  async function fetchProjects() {
    const response = await api.get('/api/projects')
    projects.value = response.data.data
    if (projects.value.length > 0 && !currentProject.value) {
      currentProject.value = projects.value[0]
    }
  }

  async function createProject(name: string, description?: string) {
    const response = await api.post('/api/projects', { name, description })
    await fetchProjects()
    return response.data.data
  }

  async function deleteProject(projectId: string) {
    await api.delete(`/api/projects/${projectId}`)
    if (currentProject.value?.id === projectId) {
      currentProject.value = null
    }
    await fetchProjects()
  }

  function setCurrentProject(project: Project) {
    currentProject.value = project
  }

  return { projects, currentProject, fetchProjects, createProject, deleteProject, setCurrentProject }
})
```

#### 3.3.3 路由配置 (src/router/)

```typescript
// src/router/index.ts
import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    name: 'Layout',
    component: () => import('@/layout/index.vue'),
    redirect: '/envs',
    meta: { requiresAuth: true },
    children: [
      {
        path: 'envs',
        name: 'Envs',
        component: () => import('@/views/Envs.vue'),
        meta: { title: '环境管理' }
      },
      {
        path: 'monitor',
        name: 'Monitor',
        component: () => import('@/views/Monitor.vue'),
        meta: { title: '训练监控' }
      },
      {
        path: 'optimization',
        name: 'Optimization',
        component: () => import('@/views/Optimization.vue'),
        meta: { title: '优化中心' }
      },
      {
        path: 'models',
        name: 'Models',
        component: () => import('@/views/Models.vue'),
        meta: { title: '模型库' }
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/Settings.vue'),
        meta: { title: '设置' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  if (to.meta.requiresAuth !== false && !authStore.isAuthenticated) {
    next('/login')
  } else if (to.path === '/login' && authStore.isAuthenticated) {
    next('/')
  } else {
    next()
  }
})

export default router
```

---

## 第四章 开发规范

### 4.1 Python 代码规范

#### 4.1.1 代码风格

- 遵循 PEP 8 规范
- 使用 4 个空格缩进
- 行长度限制 88 个字符（Black 默认）
- 使用 type hints

#### 4.1.2 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 文件名 | snake_case | env_generator.py |
| 类名 | PascalCase | EnvGenerator |
| 函数名 | snake_case | generate_env |
| 变量名 | snake_case | env_config |
| 常量名 | UPPER_SNAKE_CASE | MAX_RETRIES |
| 私有成员 | _前缀 | _internal_method |

#### 4.1.3 函数/类文档

```python
async def get_env(
    env_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    获取环境详情

    Args:
        env_id: 环境 ID
        current_user: 当前登录用户
        db: 数据库会话

    Returns:
        包含环境信息的字典

    Raises:
        HTTPException: 环境不存在时抛出 404
    """
    result = await db.execute(
        text("SELECT * FROM envs WHERE id = :id"),
        {"id": env_id}
    )
    env = result.fetchone()
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found")
    return {"code": 0, "data": env}
```

#### 4.1.4 异常处理

```python
# 好的实践
try:
    result = await some_async_operation()
except SpecificException as e:
    logger.error(f"Operation failed: {e}")
    raise HTTPException(status_code=500, detail=str(e))
finally:
    await cleanup()

# 避免的写法
try:
    result = await some_async_operation()
except:  # 不要捕获所有异常
    pass  # 不要静默忽略
```

### 4.2 TypeScript/Vue 代码规范

#### 4.2.1 Vue 组件规范

- 使用 `<script setup>` 语法
- 使用 Composition API
- 组件名使用 PascalCase
- Props 使用 camelCase，模板中使用 kebab-case

```vue
<!-- 好的示例 -->
<script setup lang="ts">
import { ref, computed } from 'vue'

interface Props {
  envId: string
  envName: string
}

const props = defineProps<Props>()

const displayName = computed(() => `${props.envName} (${props.envId})`)
</script>

<template>
  <div class="env-card">
    <h3>{{ displayName }}</h3>
  </div>
</template>
```

#### 4.2.2 TypeScript 规范

```typescript
// 使用 interface 定义对象类型
interface User {
  id: string
  username: string
  global_role: string
  created_at?: string
}

// 使用 type 定义联合类型
type UserRole = 'admin' | 'configurer' | 'viewer'

// 使用 enum 定义枚举
enum EnvStatus {
  Generating = 'generating',
  Active = 'active',
  Deprecated = 'deprecated'
}

// 函数返回类型
async function fetchUsers(): Promise<User[]> {
  const response = await api.get('/api/users')
  return response.data.data
}
```

#### 4.2.3 API 调用规范

```typescript
// src/api/index.ts
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 30000,
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      const authStore = useAuthStore()
      authStore.logout()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api
```

### 4.3 Git 规范

#### 4.3.1 分支命名

```
main              # 主分支
├── develop       # 开发分支
├── feature/xxx   # 功能分支
├── fix/xxx       # 修复分支
├── hotfix/xxx    # 紧急修复
└── release/x.x.x # 发布分支
```

#### 4.3.2 提交信息格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type 类型**：

| 类型 | 说明 | 示例 |
|------|------|------|
| feat | 新功能 | feat(env): 添加环境批量生成 |
| fix | 修复 | fix(auth): 修复登录失败问题 |
| docs | 文档 | docs: 更新开发手册 |
| style | 格式 | style: 格式化代码 |
| refactor | 重构 | refactor(api): 重构用户接口 |
| test | 测试 | test: 添加单元测试 |
| chore | 构建/工具 | chore: 更新依赖 |

**示例**：

```
feat(env): 添加环境批量生成功能

- 支持批量生成环境
- 添加随机参数变化
- 优化生成速度

Closes #123
```

---

## 第五章 调试与测试

### 5.1 后端调试

#### 5.1.1 VS Code 调试配置

创建 `.vscode/launch.json`：

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: FastAPI",
            "type": "python",
            "request": "launch",
            "module": "uvicorn",
            "args": ["app.main:app", "--reload", "--port", "8000"],
            "cwd": "${workspaceFolder}/backend",
            "envFile": "${workspaceFolder}/backend/.env",
            "console": "integratedTerminal"
        },
        {
            "name": "Python: Celery Worker",
            "type": "python",
            "request": "launch",
            "module": "celery",
            "args": ["-A", "app.celery_app", "worker", "--loglevel=info"],
            "cwd": "${workspaceFolder}/backend",
            "envFile": "${workspaceFolder}/backend/.env",
            "console": "integratedTerminal"
        }
    ]
}
```

#### 5.1.2 API 测试

**使用 curl 测试**

```cmd
# 登录获取 token
curl -X POST http://localhost:8000/api/auth/login ^
  -H "Content-Type: application/json" ^
  -d "{\"username\":\"admin\",\"password\":\"admin123\"}"

# 使用 token 请求
curl -X GET http://localhost:8000/api/envs ^
  -H "Authorization: Bearer <your_token>"
```

**使用 httpie 测试**

```cmd
# 安装 httpie
pip install httpie

# 登录
http POST localhost:8000/api/auth/login username=admin password=admin123

# 请求
http GET localhost:8000/api/envs Authorization:"Bearer <token>"
```

#### 5.1.3 日志查看

```bash
# 查看后端日志（控制台输出）

# 查看 Celery 任务日志
# 日志输出到控制台

# 生产环境日志
# 配置日志文件输出
```

### 5.2 前端调试

#### 5.2.1 浏览器开发者工具

1. 打开 Chrome/Firefox
2. 按 F12 打开开发者工具
3. 使用以下面板：
   - **Console**：查看日志和错误
   - **Network**：查看网络请求
   - **Elements**：查看 DOM 结构
   - **Application**：查看 LocalStorage、Cookie

#### 5.2.2 Vue DevTools

安装 Vue DevTools 浏览器扩展：
- Chrome: https://chrome.google.com/webstore/detail/vuejs-devtools/nhdogjmejiglipccpnnnanhbledajbpd
- Firefox: https://addons.mozilla.org/en-US/firefox/addon/vue-js-devtools/

功能：
- 查看组件树
- 查看组件状态
- 编辑状态
- 性能分析

### 5.3 数据库调试

#### 5.3.1 使用 psql 命令行

```bash
# 连接数据库
psql -U postgres -d fltect

# 查看所有表
\dt

# 查看表结构
\d users

# 查看数据
SELECT * FROM users;

# 查看慢查询
SELECT * FROM pg_stat_activity WHERE state = 'active';

# 查看表大小
SELECT pg_size_pretty(pg_total_relation_size('envs'));
```

#### 5.3.2 使用图形化工具

推荐工具：
- **pgAdmin**: PostgreSQL 官方工具
- **DBeaver**: 通用数据库工具
- **Navicat**: 商业数据库工具

---

## 第六章 部署指南

### 6.1 Docker 部署

#### 6.1.1 前提条件

- 安装 Docker Desktop: https://www.docker.com/products/docker-desktop/

#### 6.1.2 启动服务

```bash
# 构建并启动
docker compose up -d --build

# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f

# 停止服务
docker compose down
```

#### 6.1.3 服务端口

| 服务 | 端口 | 说明 |
|------|------|------|
| frontend | 80 | 前端页面 |
| backend | 8000 | 后端 API |
| postgres | 5432 | 数据库 |
| redis | 6379 | 缓存 |
| minio | 9000/9001 | 对象存储 |

### 6.2 本地部署

#### 6.2.1 启动后端

```bash
cd backend
.\venv\Scripts\activate
python run.py
```

#### 6.2.2 启动前端

```bash
cd frontend
npm run dev
```

#### 6.2.3 一键启动

```cmd
# Windows
.\start_dev.ps1
# 或
start.bat
```

---

## 第七章 常见问题

### 7.1 依赖安装问题

**Q: pip install 失败**

```bash
# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 或升级 pip
python -m pip install --upgrade pip
```

**Q: npm install 失败**

```bash
# 清除缓存
npm cache clean --force

# 使用淘宝镜像
npm install --registry https://registry.npmmirror.com
```

### 7.2 数据库问题

**Q: 连接失败**

```bash
# 检查 PostgreSQL 服务
# Windows: 服务管理器
# Linux: sudo systemctl status postgresql

# 检查端口
netstat -an | grep 5432

# 检查用户密码
psql -U postgres
```

**Q: 表不存在**

```bash
# 启动应用会自动创建表
python run.py

# 或使用 Alembic 迁移
alembic upgrade head
```

### 7.3 端口问题

**Q: 端口被占用**

```bash
# 查找占用进程
netstat -ano | findstr :8000

# 结束进程
taskkill /PID <进程ID> /F
```

### 7.4 认证问题

**Q: JWT Token 无效**

- 检查 Token 是否过期
- 检查 JWT_SECRET_KEY 配置
- 检查请求头格式：`Authorization: Bearer <token>`

---

## 附录

### A. 环境变量配置

```env
# 数据库
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/fltect

# Redis
REDIS_URL=redis://localhost:6379/0

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=fltect

# JWT
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# CORS
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
```

### B. 默认账号

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123 | 管理员 |

### C. 联系方式

- 项目地址: [GitHub Repository]
- 问题反馈: [Issues]

---

**文档版本**: 1.0
**最后更新**: 2026年5月
