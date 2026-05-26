# 飞行试验环境构建系统 - 开发手册

## 目录

- [开发环境要求](#开发环境要求)
- [编程环境配置](#编程环境配置)
- [数据库配置](#数据库配置)
- [后端开发指南](#后端开发指南)
- [前端开发指南](#前端开发指南)
- [调试与测试](#调试与测试)
- [代码规范](#代码规范)

---

## 开发环境要求

### 硬件要求

| 资源 | 最低配置 | 推荐配置 |
|------|----------|----------|
| CPU | 4 核 | 8 核+ |
| 内存 | 8 GB | 16 GB+ |
| 硬盘 | 50 GB | 100 GB SSD |
| 网络 | 需要互联网 | 稳定网络 |

### 软件要求

| 软件 | 版本要求 | 说明 |
|------|----------|------|
| Python | 3.10 - 3.12 | 后端运行环境 |
| Node.js | 18 LTS+ | 前端构建 |
| PostgreSQL | 14 - 16 | 数据库 |
| Redis | 6 - 7 | 缓存/消息队列 |
| Git | 2.30+ | 版本控制 |
| Docker | 24+ | 可选，容器化开发 |

---

## 编程环境配置

### 1. Python 环境配置

#### 安装 Python

1. 下载 Python 3.11: https://www.python.org/downloads/
2. 安装时勾选 **Add Python to PATH**
3. 验证安装：

```bash
python --version
# Python 3.11.x

pip --version
# pip 24.x.x
```

#### 创建虚拟环境

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
.\venv\Scripts\activate

# Linux/Mac:
source venv/bin/activate

# 验证
where python  # 应显示 venv\Scripts\python.exe
```

#### 安装依赖

```bash
# 激活虚拟环境后
pip install -r requirements.txt

# 验证安装
pip list
```

#### 核心依赖说明

| 包名 | 版本 | 用途 |
|------|------|------|
| fastapi | >=0.110 | Web 框架 |
| uvicorn | >=0.29 | ASGI 服务器 |
| sqlalchemy | >=2.0 | ORM |
| asyncpg | >=0.29 | PostgreSQL 驱动 |
| celery | >=5.3 | 异步任务 |
| redis | >=5.0 | Redis 客户端 |
| python-jose | >=3.3 | JWT |
| passlib | >=1.7 | 密码加密 |
| pydantic | >=2.6 | 数据验证 |

### 2. Node.js 环境配置

#### 安装 Node.js

1. 下载 Node.js 20 LTS: https://nodejs.org/
2. 安装时勾选 **Automatically install the necessary tools**
3. 验证安装：

```bash
node --version
# v20.x.x

npm --version
# 10.x.x
```

#### 配置 npm 镜像（可选，国内加速）

```bash
npm config set registry https://registry.npmmirror.com

# 验证
npm config get registry
# https://registry.npmmirror.com
```

#### 安装前端依赖

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 验证
ls node_modules/
```

#### 核心依赖说明

| 包名 | 版本 | 用途 |
|------|------|------|
| vue | 3.5+ | 前端框架 |
| element-plus | 2.14+ | UI 组件库 |
| three | 0.184+ | 3D 渲染 |
| echarts | 6.0+ | 图表 |
| axios | 1.16+ | HTTP 请求 |
| pinia | 3.0+ | 状态管理 |
| vue-router | 5.0+ | 路由 |

### 3. IDE 配置

#### VS Code 推荐配置

安装扩展：

```
- Python (ms-python.python)
- Volar (Vue 语言支持)
- ESLint
- Prettier
- GitLens
```

VS Code 设置 (.vscode/settings.json)：

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/backend/venv/Scripts/python.exe",
  "editor.formatOnSave": true,
  "[python]": {
    "editor.defaultFormatter": "ms-python.python"
  },
  "[vue]": {
    "editor.defaultFormatter": "Vue.volar"
  }
}
```

---

## 数据库配置

### 1. PostgreSQL 配置

#### 安装 PostgreSQL

**Windows:**

1. 下载: https://www.postgresql.org/download/windows/
2. 安装时设置密码（记住！）
3. 默认端口: 5432
4. 安装完成后启动服务

**Linux (Ubuntu):**

```bash
# 安装
sudo apt update
sudo apt install postgresql postgresql-contrib

# 启动服务
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 切换到 postgres 用户
sudo -u postgres psql
```

#### 创建数据库

```bash
# 连接 PostgreSQL
psql -U postgres

# 或使用图形化工具 (pgAdmin, DBeaver)
```

执行 SQL：

```sql
-- 创建数据库
CREATE DATABASE fltect;

-- 验证
\l  -- 列出所有数据库
\q  -- 退出
```

#### 配置连接

编辑 `backend/app/core/config.py`：

```python
class Settings(BaseSettings):
    # 数据库连接
    DATABASE_URL: str = "postgresql+asyncpg://postgres:your_password@localhost:5432/fltect"

    # 如果修改了端口
    # DATABASE_URL: str = "postgresql+asyncpg://postgres:your_password@localhost:5433/fltect"
```

或使用环境变量 (.env)：

```env
DATABASE_URL=postgresql+asyncpg://postgres:your_password@localhost:5432/fltect
```

#### 数据库初始化

```bash
# 激活虚拟环境
cd backend
.\venv\Scripts\activate

# 启动应用（自动创建表）
python run.py

# 或使用 Alembic 迁移
alembic upgrade head
```

#### 常用数据库命令

```bash
# 连接数据库
psql -U postgres -d fltect

# 查看表
\dt

# 查看表结构
\d envs

# 查看数据
SELECT * FROM users;

# 备份数据库
pg_dump -U postgres fltect > backup.sql

# 恢复数据库
psql -U postgres fltect < backup.sql
```

### 2. Redis 配置

#### 安装 Redis

**Windows:**

1. 下载: https://github.com/tporadowski/redis/releases
2. 解压后运行 `redis-server.exe`
3. 或安装为 Windows 服务

**Linux:**

```bash
# 安装
sudo apt install redis-server

# 启动
sudo systemctl start redis
sudo systemctl enable redis

# 测试连接
redis-cli ping
# PONG
```

#### 配置连接

编辑 `backend/app/core/config.py`：

```python
class Settings(BaseSettings):
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
```

#### Redis 常用命令

```bash
# 连接 Redis
redis-cli

# 查看所有键
KEYS *

# 清空所有数据
FLUSHALL

# 查看 Redis 信息
INFO
```

### 3. MinIO 配置（可选）

#### 安装 MinIO

```bash
# Windows: 下载 minio.exe
# https://min.io/download

# 启动
minio.exe server .\minio-data

# 访问控制台
# http://localhost:9001
# 用户名: minioadmin
# 密码: minioadmin
```

#### 配置连接

```python
class Settings(BaseSettings):
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "fltect"
```

---

## 后端开发指南

### 项目结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # 应用入口
│   ├── api/                 # API 路由
│   │   ├── __init__.py
│   │   ├── auth.py          # 认证
│   │   ├── users.py         # 用户
│   │   ├── projects.py      # 项目
│   │   ├── envs.py          # 环境
│   │   ├── models.py        # 模型
│   │   ├── optimization.py  # 优化
│   │   └── ws.py            # WebSocket
│   ├── core/                # 核心配置
│   │   ├── config.py        # 配置管理
│   │   ├── database.py      # 数据库
│   │   └── security.py      # 认证授权
│   ├── models/              # SQLAlchemy 模型
│   ├── schemas/             # Pydantic 模型
│   ├── services/            # 业务逻辑
│   ├── tasks/               # Celery 任务
│   └── seed/                # 种子数据
├── alembic/                 # 数据库迁移
├── requirements.txt
└── run.py                   # 启动脚本
```

### 启动服务

```bash
# 激活虚拟环境
.\venv\Scripts\activate

# 方式1: 直接启动
python run.py

# 方式2: 使用 uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 方式3: 启动 Celery Worker
celery -A app.celery_app worker --loglevel=info
```

### 添加新 API

1. 在 `app/api/` 下创建路由文件
2. 在 `app/main.py` 注册路由
3. 编写接口逻辑

示例：

```python
# app/api/new_module.py
from fastapi import APIRouter, Depends
from app.core.security import get_current_user

router = APIRouter()

@router.get("/new-endpoint")
async def new_endpoint(current_user: dict = Depends(get_current_user)):
    return {"code": 0, "data": "Hello"}
```

```python
# app/main.py
from app.api import new_module
app.include_router(new_module.router, prefix="/api/new", tags=["新模块"])
```

### 添加新数据表

1. 在 `app/models/` 定义模型
2. 在 `app/seed/` 添加种子数据（可选）
3. 重启应用自动创建表

```python
# app/models/new_table.py
from sqlalchemy import Column, String, DateTime
from app.models.base import Base

class NewTable(Base):
    __tablename__ = "new_table"

    id = Column(String(36), primary_key=True)
    name = Column(String(128), nullable=False)
    created_at = Column(DateTime, nullable=False)
```

---

## 前端开发指南

### 项目结构

```
frontend/
├── src/
│   ├── api/                 # API 配置
│   │   └── index.ts         # Axios 实例
│   ├── components/          # 公共组件
│   │   └── EnvPreview3D.vue # 3D 预览
│   ├── layout/              # 布局
│   │   └── index.vue        # 主布局
│   ├── router/              # 路由
│   │   └── index.ts
│   ├── stores/              # 状态管理
│   │   ├── auth.ts
│   │   └── project.ts
│   ├── views/               # 页面
│   │   ├── Login.vue
│   │   ├── Envs.vue
│   │   ├── Monitor.vue
│   │   ├── Optimization.vue
│   │   ├── Models.vue
│   │   └── Settings.vue
│   └── main.ts
├── package.json
└── vite.config.ts
```

### 启动服务

```bash
# 安装依赖
npm install

# 开发模式
npm run dev

# 构建生产版本
npm run build

# 预览生产版本
npm run preview
```

### 添加新页面

1. 在 `src/views/` 创建 Vue 组件
2. 在 `src/router/index.ts` 添加路由

```vue
<!-- src/views/NewPage.vue -->
<template>
  <div class="new-page">
    <h1>新页面</h1>
  </div>
</template>

<script setup lang="ts">
// 组件逻辑
</script>

<style scoped>
/* 样式 */
</style>
```

```typescript
// src/router/index.ts
{
  path: 'new-page',
  name: 'NewPage',
  component: () => import('@/views/NewPage.vue'),
  meta: { title: '新页面' }
}
```

### 添加新 API 调用

```typescript
// src/api/index.ts 已有 axios 实例

// 在组件中使用
import api from '@/api'

const fetchData = async () => {
  const response = await api.get('/api/some-endpoint')
  return response.data
}
```

### 状态管理 (Pinia)

```typescript
// src/stores/example.ts
import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api'

export const useExampleStore = defineStore('example', () => {
  const data = ref([])

  async function fetchData() {
    const response = await api.get('/api/data')
    data.value = response.data.data
  }

  return { data, fetchData }
})
```

---

## 调试与测试

### 后端调试

#### VS Code 调试配置

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
      "envFile": "${workspaceFolder}/backend/.env"
    }
  ]
}
```

#### API 测试

```bash
# 使用 curl
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 使用 httpie
http POST localhost:8000/api/auth/login username=admin password=admin123
```

#### 访问 API 文档

启动服务后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 前端调试

#### 浏览器开发者工具

1. 打开 Chrome/Firefox
2. 按 F12 打开开发者工具
3. 使用 Console/Network/Elements 面板

#### Vue DevTools

安装 Vue DevTools 浏览器扩展，可查看：
- 组件树
- 状态数据
- 事件追踪

### 数据库调试

```bash
# 连接数据库
psql -U postgres -d fltect

# 查看慢查询
SELECT * FROM pg_stat_activity WHERE state = 'active';

# 查看表大小
SELECT pg_size_pretty(pg_total_relation_size('envs'));
```

---

## 代码规范

### Python 规范

- 遵循 PEP 8
- 使用 type hints
- 函数/类添加 docstring
- 使用 Black 格式化

```python
# 好的示例
async def get_user(user_id: str, db: AsyncSession) -> dict:
    """获取用户信息"""
    result = await db.execute(
        text("SELECT * FROM users WHERE id = :id"),
        {"id": user_id}
    )
    return result.fetchone()
```

### TypeScript/Vue 规范

- 使用 `<script setup>` 语法
- 使用 Composition API
- 组件名使用 PascalCase
- 变量/函数使用 camelCase

```vue
<!-- 好的示例 -->
<script setup lang="ts">
import { ref, onMounted } from 'vue'

interface User {
  id: string
  name: string
}

const users = ref<User[]>([])

const loadUsers = async () => {
  // ...
}

onMounted(() => {
  loadUsers()
})
</script>
```

### Git 规范

#### 提交信息格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

类型：
- feat: 新功能
- fix: 修复
- docs: 文档
- style: 格式
- refactor: 重构
- test: 测试
- chore: 构建/工具

示例：

```
feat(env): 添加环境批量生成功能

- 支持批量生成环境
- 添加随机参数变化
- 优化生成速度

Closes #123
```

### 分支管理

```
main          # 主分支，稳定版本
├── develop   # 开发分支
│   ├── feature/xxx  # 功能分支
│   ├── fix/xxx      # 修复分支
│   └── ...
└── release/x.x.x    # 发布分支
```

---

## 常见问题

### Q: pip install 失败

```bash
# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 或配置全局镜像
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q: npm install 失败

```bash
# 清除缓存
npm cache clean --force

# 使用淘宝镜像
npm install --registry https://registry.npmmirror.com
```

### Q: 数据库连接失败

```bash
# 检查 PostgreSQL 服务是否运行
# Windows: 服务管理器
# Linux: sudo systemctl status postgresql

# 检查端口
netstat -an | grep 5432

# 检查用户密码
psql -U postgres
```

### Q: Redis 连接失败

```bash
# 检查 Redis 服务
redis-cli ping

# 应返回 PONG
```

### Q: 端口被占用

```bash
# 查找占用进程
netstat -ano | findstr :8000

# 结束进程
taskkill /PID <进程ID> /F
```
