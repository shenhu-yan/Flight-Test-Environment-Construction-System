# 飞行试验环境构建系统 - 前端演示项目

## 项目说明

本项目是「飞行试验环境构建系统」的纯前端演示版本，所有后端功能已移除，使用 Mock 数据替代真实 API 调用，可独立运行无需后端服务。

## 技术栈

- Vue 3 + Vite 5
- Vue Router 4
- Axios（已配置但未实际调用后端）
- ECharts 5（图表可视化）

## 快速启动

### 1. 安装依赖

```bash
npm install
```

### 2. 启动开发服务器

```bash
npm run dev
```

启动后访问 http://localhost:3001/

### 3. 构建生产版本

```bash
npm run build
```

### 4. 预览生产版本

```bash
npm run preview
```

## 登录账号

| 用户名   | 密码       | 角色     |
|----------|-----------|----------|
| admin    | admin123  | 管理员   |
| config   | config123 | 配置员   |
| dev      | dev123    | 开发者   |
| user     | user123   | 查看用户 |

## 页面说明

| 页面       | 路径           | 说明                       |
|-----------|---------------|---------------------------|
| 登录页     | /             | 用户登录（本地验证）         |
| 仪表盘     | /dashboard    | 系统概览、统计图表           |
| 项目管理   | /projects     | 项目的增删改查              |
| 环境管理   | /environments | 环境列表、状态筛选、详情查看   |
| 模型管理   | /models       | 模型列表、上传、筛选         |
| 环境生成   | /env-gen      | 环境配置生成、模板管理、导入   |
| 环境调整   | /env-adjust   | 实时监测、自动/手动调整       |
| 环境优化   | /env-optimize | 环境评估、优化、可视化        |
| 用户管理   | /users        | 用户列表、创建用户（仅管理员） |

## 与完整版的区别

- 所有 API 请求已替换为本地 Mock 数据
- 登录验证在本地完成，不依赖后端
- 数据操作（增删改）仅在当前会话生效，刷新后恢复
- 端口为 3001，与原前端 3000 不冲突

## 项目结构

```
proj1/
├── index.html
├── package.json
├── vite.config.js
├── public/
└── src/
    ├── main.js              # 入口文件，Axios 配置
    ├── App.vue              # 根组件，导航栏
    ├── router/
    │   └── index.js         # 路由配置与权限守卫
    └── views/
        ├── Login.vue        # 登录页
        ├── Dashboard.vue    # 仪表盘
        ├── Projects.vue     # 项目管理
        ├── Environments.vue # 环境管理
        ├── Models.vue       # 模型管理
        ├── Users.vue        # 用户管理
        ├── EnvGen.vue       # 环境生成
        ├── EnvAdjust.vue    # 环境动态调整
        └── EnvOptimize.vue  # 环境优化
```
