# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

基于强化学习的飞行试验环境构建系统（B/S 架构）。系统根据用户需求自动生成 Gymnasium 兼容的飞行试验环境，支持动态调整和智能优化。V1.0 聚焦固定翼飞行器。

## Architecture

四层 B/S 架构：

1. **前端**：Vue 3 + TypeScript + Vite — Element Plus (UI) / Three.js (3D 预览) / ECharts (数据可视化)
2. **网关**：Nginx — 静态托管 / 反向代理 / WebSocket 升级
3. **后端**：FastAPI (Python 3.10+) — 单体服务，内置全部业务模块
4. **数据层**：PostgreSQL (业务数据, JSONB 配置) / MinIO (文件/模型存储) / Redis (缓存 + Streams 消息队列)

### Backend Module Structure

后端为 FastAPI 单体，按功能分模块，各模块通过内部 API 互相调用：

- **EnvGen** — 环境生成：调用 JSBSim 构建 Gymnasium 兼容环境包 + JSON 配置 + scene.json 预览数据
- **DynAdjust** — 动态调整：WebSocket 接收本地训练指标；规则驱动策略引擎（if-then）；调整指令通过 WebSocket 下发
- **IntellOpt** — 智能优化：四维评分（多样性/挑战性/真实性/有效性）；贝叶斯优化（scikit-optimize）；APScheduler 持续优化
- **ModelMgr** — 模型管理：项目级隔离；语义化版本；三级 RBAC（admin/configurer/viewer）
- **公共服务** — 认证(JWT)、权限、审计日志、消息通知

### Key Technical Decisions

- 环境产物 = Python 环境包 (Gymnasium `reset`/`step`/`close`) + JSON 配置 + scene.json（Three.js 渲染用）
- JSBSim 作为 Python 库内嵌调用，非独立进程；环境生成/批量生成/优化迭代走 Celery 任务队列，在线交互走 `run_in_executor` 线程池
- 训练在用户本地执行，系统通过 WebSocket 被动接收指标上报
- 指标流：WebSocket → Redis Streams → 指标处理服务（持久化 + 前端推送 + 策略触发）
- 优化器抽象基类 `BaseOptimizer(suggest/observe)` 留有进化策略扩展点
- 所有数据以 `project_id` 为隔离边界，PostgreSQL 行级安全策略

## Data Model Conventions

- 主键统一 `VARCHAR(36)` UUID
- 环境配置、模板参数、策略定义等用 PostgreSQL `JSONB` 字段
- 模型删除为软删除（status=deprecated）
- 环境参数每次调整前自动保存快照至 `env_snapshots` 表

## API Conventions

- RESTful + JSON，统一响应 `{ code, message, data }`
- 认证：`Authorization: Bearer <JWT>`
- WebSocket 通道：`/ws/metrics`（训练指标上报）、`/ws/adjustment`（调整指令下发）、`/ws/frontend`（前端实时推送）
- 需求编号沿用：FG-xx (环境生成)、DA-xx (动态调整)、IO-xx (智能优化)、MM-xx (模型管理)、UI-xx (用户交互)

## Design Documents

- `memory-bank/design-document.md` — 完整系统设计（架构、模块、数据模型、接口、技术方案）
- `memory-bank/tech-stack.md` — 技术栈选型与理由、依赖清单
- `memory-bank/implementation-plan.md` — 分步实施计划

## 重要提示

- 写任何代码前必须完整阅读 `memory-bank/architecture.md`
- 写任何代码前必须完整阅读 `memory-bank/design-document.md`
- 每完成一个重大功能或里程碑后，必须更新 `memory-bank/architecture.md`
- 在绘制任何ui时使用DESIGN.MD作为参考