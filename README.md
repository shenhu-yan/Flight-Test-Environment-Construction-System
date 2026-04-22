# Flight Test Environment Construction System

飞行试验环境构建系统 — 专为强化学习算法训练设计的专业化试验环境平台。

## 系统架构

```
┌─────────────────────────────────────────────────┐
│                   Frontend                       │
│         Vue 3 + Vite + Vue Router + Axios        │
│              http://localhost:3000                │
└──────────────────────┬──────────────────────────┘
                       │ Vite Proxy (/api → :5000)
┌──────────────────────▼──────────────────────────┐
│                   Backend                        │
│      Flask + SQLAlchemy + JWT + SQLite           │
│              http://localhost:5000                │
└──────────────────────────────────────────────────┘
```

## 核心功能

| 功能模块 | 说明 |
|---------|------|
| 环境生成 | 模板化/自定义配置，批量生成多样化飞行试验环境 |
| 动态调整 | 实时性能监控，自动/手动调整策略，历史回滚 |
| 智能优化 | 环境质量评估，优化算法，批量优化，验证机制 |
| 模型管理 | 项目隔离存储，版本控制，上传/下载/备份/恢复 |
| 用户交互 | 可视化界面，角色权限控制，响应式布局 |

## 技术栈

**后端：**
- Python 3.11+
- Flask 3.x — Web 框架
- Flask-SQLAlchemy — ORM
- Flask-JWT-Extended — JWT 认证
- Flask-CORS — 跨域支持
- SQLite — 数据库

**前端：**
- Vue 3.4+ — UI 框架
- Vite 5.x — 构建工具
- Vue Router 4.x — 路由管理
- Axios — HTTP 客户端

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 14+
- npm 或 yarn

### 后端启动

```bash
cd backend
pip install -r requirements.txt
python app.py
```

服务运行在 http://localhost:5000

### 前端启动

```bash
cd frontend
npm install
npm run dev
```

服务运行在 http://localhost:3000，API 请求通过 Vite 代理转发到后端。

### 默认用户

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123 | 系统管理员 |
| config | config123 | 配置人员 |
| dev | dev123 | 研发人员 |
| user | user123 | 普通用户 |

## 项目结构

```
Flight Test Environment Construction System/
├── backend/
│   ├── api/                        # API 路由
│   │   ├── __init__.py             # Blueprint 注册 & JWT 辅助函数
│   │   ├── user_routes.py          # 用户认证
│   │   ├── project_routes.py       # 项目管理
│   │   ├── environment_routes.py   # 环境管理
│   │   ├── model_routes.py         # 模型路由
│   │   ├── env_gen_routes.py       # 环境生成
│   │   ├── env_adjust_routes.py    # 环境调整
│   │   ├── env_optimize_routes.py  # 环境优化
│   │   ├── model_mgr_routes.py     # 模型管理
│   │   └── adjustment_routes.py    # 调整记录
│   ├── models/                     # 数据模型
│   │   ├── user.py
│   │   ├── project.py
│   │   ├── environment.py
│   │   ├── model.py
│   │   └── adjustment.py
│   ├── services/                   # 业务逻辑
│   │   ├── env_generator.py
│   │   ├── env_adjuster.py
│   │   ├── env_optimizer.py
│   │   └── model_manager.py
│   ├── app.py                      # 应用入口
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── views/                  # 页面组件
│   │   │   ├── Login.vue
│   │   │   ├── Dashboard.vue
│   │   │   ├── Projects.vue
│   │   │   ├── Environments.vue
│   │   │   ├── EnvGen.vue
│   │   │   ├── EnvAdjust.vue
│   │   │   ├── EnvOptimize.vue
│   │   │   ├── Models.vue
│   │   │   └── Users.vue
│   │   ├── router/
│   │   │   └── index.js
│   │   ├── App.vue
│   │   └── main.js
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
├── docs/
│   ├── DEPLOYMENT.md               # 部署指南
│   ├── USER_MANUAL.md              # 用户手册
│   └── TEST_REPORT.md              # 测试报告
└── .gitignore
```

## API 概览

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/auth/login | 用户登录 |
| GET | /api/auth/me | 获取当前用户 |
| GET/POST | /api/projects | 项目列表/创建 |
| PUT/DELETE | /api/projects/:id | 项目更新/删除 |
| GET/POST | /api/environments | 环境列表/创建 |
| GET | /api/environments/:id | 环境详情 |
| POST | /api/env-gen/generate | 环境生成 |
| GET/POST | /api/env-gen/templates | 模板管理 |
| POST | /api/env-adjust/auto | 自动调整 |
| POST | /api/env-adjust/manual | 手动调整 |
| GET | /api/env-adjust/history/:id | 调整历史 |
| POST | /api/env-adjust/rollback/:id | 调整回滚 |
| POST | /api/env-optimize/evaluate | 环境评估 |
| POST | /api/env-optimize/optimize | 环境优化 |
| POST | /api/env-optimize/batch-optimize | 批量优化 |
| POST | /api/models/mgr/upload | 模型上传 |
| GET | /api/models/mgr/download/:id | 模型下载 |
| DELETE | /api/models/mgr/:id | 模型删除 |
| GET/POST | /api/users | 用户列表/创建 |
| DELETE | /api/users/:id | 用户删除 |

所有 `/api/*` 接口（登录除外）需在请求头携带 `Authorization: Bearer <token>`。

## 角色权限

| 角色 | 环境生成 | 环境调整 | 环境优化 | 模型管理 | 模板管理 | 用户管理 |
|------|---------|---------|---------|---------|---------|---------|
| admin | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| config | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| dev | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| user | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

## 生产部署

```bash
# 前端构建
cd frontend
npm run build

# 后端使用 Gunicorn
cd backend
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

Nginx 配置示例：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        root /path/to/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

详细部署说明请参考 [DEPLOYMENT.md](docs/DEPLOYMENT.md)。

## 文档

- [部署指南](docs/DEPLOYMENT.md)
- [用户手册](docs/USER_MANUAL.md)
- [测试报告](docs/TEST_REPORT.md)

## License

MIT
