# 部署指南

## 目录

- [方式一：Docker 部署（推荐）](#方式一docker-部署推荐)
- [方式二：本地部署](#方式二本地部署)
- [端口配置](#端口配置)
- [常见问题](#常见问题)

---

## 方式一：Docker 部署（推荐）

### 前提条件

安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/)

- Windows: 下载安装 Docker Desktop for Windows
- macOS: 下载安装 Docker Desktop for Mac
- Linux: 参考 [官方文档](https://docs.docker.com/engine/install/)

### 部署步骤

```bash
# 1. 解压项目到任意目录

# 2. 进入项目目录
cd Flight-Test-Environment-Construction-System

# 3. 双击 docker-start.bat 或运行：
docker compose up -d --build

# 4. 等待构建完成（首次约 3-5 分钟）

# 5. 打开浏览器访问
#    前端：http://localhost
#    后端：http://localhost:8000/docs
```

### 常用命令

```bash
# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f

# 查看某个服务日志
docker compose logs -f backend

# 停止服务
docker compose down

# 重启服务
docker compose restart

# 重新构建并启动
docker compose up -d --build

# 清除数据并重建（慎用）
docker compose down -v && docker compose up -d --build
```

### 服务说明

| 服务 | 端口 | 说明 |
|------|------|------|
| frontend | 80 | 前端页面 |
| backend | 8000 | 后端 API |
| postgres | 5432 | PostgreSQL 数据库 |
| redis | 6379 | Redis 缓存 |
| minio | 9000/9001 | MinIO 文件存储 |
| celery-worker | - | 异步任务处理器 |

---

## 方式二：本地部署

### 前提条件

| 软件 | 版本 | 下载地址 |
|------|------|----------|
| Python | 3.10+ | https://www.python.org/downloads/ |
| Node.js | 18+ | https://nodejs.org/ |
| PostgreSQL | 14+ | https://www.postgresql.org/download/windows/ |
| Redis | 5+ | https://github.com/tporadowski/redis/releases |

**注意**：安装 Python 时务必勾选 **Add Python to PATH**

### 部署步骤

#### 1. 安装依赖软件

安装 PostgreSQL：
```bash
# 安装完成后，创建数据库
psql -U postgres -c "CREATE DATABASE fltect;"
```

安装 Redis：
```bash
# Windows: 下载解压后运行 redis-server.exe
# 或安装为 Windows 服务
```

#### 2. 一键安装项目依赖

```bash
# 方式 A：使用 PowerShell 脚本（推荐）
.\install.ps1

# 方式 B：使用批处理
setup.bat
```

#### 3. 手动安装（如一键脚本失败）

```bash
# 后端
cd backend
python -m venv venv
.\venv\Scripts\activate    # Windows
# source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# 前端
cd ../frontend
npm install
```

#### 4. 启动服务

```bash
# 方式 A：一键启动
.\start_dev.ps1
# 或
start.bat

# 方式 B：手动启动（需打开 3 个终端）
# 终端 1 - 后端
cd backend
python run.py

# 终端 2 - Celery Worker
cd backend
celery -A app.celery_app worker --loglevel=info

# 终端 3 - 前端
cd frontend
npm run dev
```

#### 5. 访问系统

```
前端地址：http://localhost:5173
后端地址：http://localhost:8000
API 文档：http://localhost:8000/docs
```

---

## 端口配置

### Docker 部署

编辑项目根目录的 `.env` 文件：

```env
# 前端端口
FRONTEND_PORT=80

# 后端端口
BACKEND_PORT=8000

# 数据库端口
POSTGRES_PORT=5432

# Redis 端口
REDIS_PORT=6379

# MinIO 端口
MINIO_API_PORT=9000
MINIO_CONSOLE_PORT=9001
```

修改后重启服务：
```bash
docker compose down && docker compose up -d
```

### 本地部署

数据库连接配置在 `backend/app/core/config.py`：

```python
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/fltect"
REDIS_URL = "redis://localhost:6379/0"
```

---

## 默认账号

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123 | 管理员 |

登录后请立即修改密码！

---

## 常见问题

### Q: Docker 构建失败

**原因**：网络问题或 Docker 未启动

**解决**：
```bash
# 确保 Docker Desktop 已启动
# 尝试使用国内镜像源（编辑 Docker daemon.json）
{
  "registry-mirrors": ["https://mirror.ccs.tencentyun.com"]
}
```

### Q: 端口被占用

**解决**：
```bash
# 查看占用端口的进程
netstat -ano | findstr :80

# 修改 .env 文件中的端口
FRONTEND_PORT=8080
```

### Q: 数据库连接失败

**解决**：
```bash
# 检查 PostgreSQL 服务是否运行
# Windows:
net start postgresql*

# Linux/Mac:
sudo systemctl status postgresql
```

### Q: Redis 连接失败

**解决**：
```bash
# 检查 Redis 服务
redis-cli ping
# 应返回 PONG
```

### Q: MinIO 无法访问

**解决**：
```bash
# Docker 部署：检查容器状态
docker compose ps minio

# 本地部署：手动启动
minio.exe server .\minio-data
```

### Q: 前端页面空白

**解决**：
```bash
# 检查后端是否运行
curl http://localhost:8000/api/health

# 查看浏览器控制台错误
# 确保 API 地址正确
```

### Q: 如何完全重置

```bash
# Docker 部署
docker compose down -v
docker compose up -d --build

# 本地部署
# 删除数据库
psql -U postgres -c "DROP DATABASE fltect;"
psql -U postgres -c "CREATE DATABASE fltect;"
```

### Q: 如何备份数据

```bash
# Docker 部署
docker exec fltect-postgres pg_dump -U postgres fltect > backup.sql

# 本地部署
pg_dump -U postgres fltect > backup.sql
```

### Q: 如何恢复数据

```bash
# Docker 部署
docker exec -i fltect-postgres psql -U postgres fltect < backup.sql

# 本地部署
psql -U postgres fltect < backup.sql
```

---

## 系统要求

### 最低配置

| 资源 | 要求 |
|------|------|
| CPU | 2 核 |
| 内存 | 4 GB |
| 硬盘 | 10 GB |
| 系统 | Windows 10/11, macOS 12+, Ubuntu 20.04+ |

### 推荐配置

| 资源 | 要求 |
|------|------|
| CPU | 4 核+ |
| 内存 | 8 GB+ |
| 硬盘 | 20 GB+ SSD |

---

## 技术支持

如遇到问题，请检查：

1. 查看日志：`docker compose logs` 或查看终端输出
2. 检查服务状态：`docker compose ps`
3. 确认端口未被占用
4. 确认防火墙未阻止相关端口
