# 架构笔记

## 项目结构

```
backend/
├── app/
│   ├── api/              # FastAPI路由
│   ├── core/             # 核心配置
│   ├── models/           # SQLAlchemy模型
│   ├── schemas/          # Pydantic模型
│   ├── services/         # 业务服务
│   ├── tasks/            # Celery任务
│   ├── seed/             # 数据库种子
│   ├── celery_app.py     # Celery配置
│   └── main.py           # FastAPI入口
├── alembic/              # 数据库迁移
├── requirements.txt      # Python依赖
└── run.py                # 启动脚本

frontend/
├── src/
│   ├── api/              # Axios配置
│   ├── components/       # 组件
│   ├── layout/           # 布局
│   ├── router/           # 路由
│   ├── stores/           # Pinia状态
│   ├── views/            # 页面
│   └── main.ts
├── package.json
└── vite.config.ts
```

## 已完成功能

### Phase 1 — 核心基座
- [x] FastAPI应用入口 + Celery配置
- [x] SQLAlchemy ORM模型 (18张表)
- [x] Alembic数据库迁移
- [x] JWT认证与授权 (RBAC)
- [x] 用户CRUD
- [x] 项目管理与成员权限
- [x] 任务管理
- [x] 环境模板库 (3个内置模板)
- [x] 环境配置解析 (JSON/XML)
- [x] JSBSim引擎封装
- [x] 环境生成 (Celery异步)
- [x] 环境导出/导入
- [x] 三维预览数据生成
- [x] 模型管理 (上传/版本/下载)
- [x] Vue 3 + TypeScript前端框架
- [x] 登录页面
- [x] 环境管理页面 (配置面板 + 3D预览)
- [x] Three.js 3D预览组件
- [x] 模型库页面

### Phase 2 — 动态能力
- [x] WebSocket三端点接入 (/ws/metrics, /ws/adjustment, /ws/frontend)
- [x] 训练监控页面 (ECharts实时曲线)
- [x] 动态调整策略引擎 (规则驱动)
- [x] 手动调整与参数快照
- [x] 版本回滚

### Phase 3 — 智能优化
- [x] 环境质量评估体系 (四维评分)
- [x] 贝叶斯优化引擎 (scikit-optimize)
- [x] 优化效果验证与报告
- [x] 前端优化中心页面 (雷达图)
- [x] 持续优化定时任务 (APScheduler)

### Phase 4 — 完善体验
- [x] 批量生成环境
- [x] 消息提醒
- [x] 日志管理 (操作日志/系统日志/审计日志)
- [x] 模型状态监控与自动推荐
- [x] 前端设置与权限管理页面

## 启动方式

```bash
# Windows
.\start_dev.ps1

# 或手动启动
cd backend && python run.py
cd frontend && npm run dev
```

## API端点

### 认证
- POST /api/auth/login - 登录
- POST /api/auth/logout - 登出

### 环境管理
- GET /api/envs - 环境列表
- POST /api/envs - 创建环境
- GET /api/envs/{id} - 环境详情
- DELETE /api/envs/{id} - 删除环境
- POST /api/envs/batch - 批量生成
- POST /api/envs/import - 导入环境
- GET /api/envs/{id}/export - 导出环境
- GET /api/envs/{id}/preview - 获取预览数据
- POST /api/envs/{id}/adjust - 手动调整
- POST /api/envs/{id}/rollback - 版本回滚
- GET /api/envs/{id}/snapshots - 快照列表
- GET /api/envs/{id}/adjustment-history - 调整历史

### WebSocket
- /ws/metrics - 训练指标上报
- /ws/adjustment - 调整指令下发
- /ws/frontend - 前端实时推送

### 优化
- POST /api/envs/{id}/evaluate - 触发评估
- GET /api/envs/{id}/evaluations - 评估历史
- POST /api/optimization-tasks - 创建优化任务
- GET /api/optimization-tasks - 任务列表
- POST /api/optimization-tasks/{id}/stop - 停止任务
