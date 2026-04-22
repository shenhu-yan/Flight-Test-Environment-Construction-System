# 飞行试验环境系统部署指南

## 系统架构

本系统采用前后端分离架构：
- **后端**：Flask + SQLAlchemy + SQLite + JWT认证
- **前端**：Vue 3 + Vite + Vue Router + Axios

## 后端部署

### 1. 环境准备

#### 系统要求
- Python 3.7+
- pip 包管理器

#### 依赖安装

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置文件

创建 `.env` 文件（已提供模板）：

```env
# 密钥配置
SECRET_KEY=dev-secret-key-change-in-production
JWT_SECRET_KEY=jwt-dev-secret-key-change-in-production

# 数据库配置（SQLite）
SQLALCHEMY_DATABASE_URI=sqlite:///flight_test_env.db
SQLALCHEMY_TRACK_MODIFICATIONS=False

# 数据库配置（MySQL，可选）
# SQLALCHEMY_DATABASE_URI=mysql+pymysql://root:password@localhost/flight_test_env?charset=utf8mb4
```

### 3. 启动服务

```bash
cd backend
python app.py

# 服务将运行在 http://127.0.0.1:5000
```

启动后系统会自动：
- 创建数据库表
- 创建默认用户（admin、config、dev、user）

## 前端部署

### 1. 环境准备

#### 系统要求
- Node.js 14+
- npm 或 yarn

#### 依赖安装

```bash
cd frontend
npm install
```

### 2. 代理配置

前端通过 Vite 开发服务器代理请求到后端，配置文件为 `vite.config.js`：

```javascript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true
      }
    }
  }
})
```

前端 Axios 配置（`src/main.js`）中 `baseURL` 设置为 `/api`，所有 API 请求会自动通过 Vite 代理转发到后端，无需手动配置后端地址。

### 3. 启动开发服务器

```bash
cd frontend
npm run dev

# 服务默认运行在 http://localhost:3000
# 若端口被占用，Vite 会自动使用 3001、3002 等替代端口
```

### 4. 构建生产版本

```bash
cd frontend
npm run build

# 构建文件将生成在 dist 目录
```

## 生产环境部署

### 后端
- 使用 Gunicorn 作为 WSGI 服务器
- 使用 Nginx 作为反向代理
- 配置 HTTPS
- 修改 `.env` 中的密钥为强随机字符串

### 前端
- 部署到 Nginx 或其他静态文件服务器
- Nginx 配置反向代理将 `/api` 请求转发到后端
- 配置 CORS 策略

### Nginx 配置示例

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        root /var/www/flight-test-env/dist;
        try_files $uri $uri/ /index.html;
    }

    # API 反向代理
    location /api {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 数据库迁移

当修改数据模型时，需要进行数据库迁移：

```bash
pip install Flask-Migrate
flask db init
flask db migrate -m "描述迁移内容"
flask db upgrade
```

## 常见问题

### 1. 数据库连接失败
- 检查 `.env` 文件中的数据库配置
- 确保 MySQL 服务正在运行（如使用 MySQL）
- 确保数据库用户权限正确

### 2. 前端无法连接后端
- 确保后端服务正在运行（http://localhost:5000）
- 检查 `vite.config.js` 中的代理配置
- 开发模式下 Vite 会自动代理 API 请求，无需手动配置 CORS

### 3. 依赖安装失败
- 确保 Python 和 Node.js 版本正确
- 尝试使用虚拟环境
- 检查网络连接，可切换 npm 镜像源：`npm config set registry https://registry.npmjs.org/`

### 4. JWT 认证失败（Subject must be a string）
- 确保 Flask-JWT-Extended 版本兼容
- 系统使用 JSON 字符串作为 JWT identity，已在 `api/__init__.py` 中提供 `get_current_user()` 辅助函数

### 5. 端口被占用
- Vite 开发服务器会自动尝试下一个可用端口
- 后端端口可在 `app.py` 中修改 `app.run(port=5000)`

## 系统默认用户

系统初始化时会自动创建以下默认用户：

| 角色 | 用户名 | 密码 | 权限 |
|------|--------|------|------|
| 系统管理员 | admin | admin123 | 所有权限 |
| 配置人员 | config | config123 | 环境配置、模板管理、模型管理 |
| 研发人员 | dev | dev123 | 环境生成、调整、优化、模型管理 |
| 普通用户 | user | user123 | 查看、导出 |

## 项目目录结构

```
Flight Test Environment Construction System/
├── backend/
│   ├── api/                    # API路由
│   │   ├── __init__.py         # Blueprint注册、辅助函数
│   │   ├── user_routes.py      # 认证与用户管理
│   │   ├── project_routes.py   # 项目管理
│   │   ├── environment_routes.py # 环境管理
│   │   ├── env_gen_routes.py   # 环境生成
│   │   ├── env_adjust_routes.py # 环境调整
│   │   ├── env_optimize_routes.py # 环境优化
│   │   ├── model_routes.py     # 模型基础路由
│   │   ├── model_mgr_routes.py # 模型管理路由
│   │   └── adjustment_routes.py # 调整记录路由
│   ├── models/                 # 数据模型
│   ├── services/               # 业务逻辑
│   ├── app.py                  # 应用入口
│   └── requirements.txt        # Python依赖
├── frontend/
│   ├── src/
│   │   ├── views/              # 页面组件
│   │   ├── router/             # 路由配置
│   │   ├── main.js             # 应用入口
│   │   └── App.vue             # 根组件
│   ├── vite.config.js          # Vite配置
│   ├── package.json            # Node.js依赖
│   └── index.html              # HTML模板
├── docs/                       # 文档
└── .gitignore
```
