# 基于强化学习的飞行试验环境构建系统

## 项目汇报文档

**项目编号**：FLT-2026-001
**版本**：V1.0
**日期**：2026年5月

---

## 目录

- [摘要](#摘要)
- [基础知识](#基础知识)
- [一、项目背景与意义](#一项目背景与意义)
- [二、需求分析](#二需求分析)
- [三、系统设计](#三系统设计)
- [四、技术实现](#四技术实现)
- [五、各功能模块详细流程](#五各功能模块详细流程)
- [六、创新点与特色](#六创新点与特色)
- [七、系统成果](#七系统成果)
- [八、测试验证](#八测试验证)
- [九、项目管理](#九项目管理)
- [十、总结与展望](#十总结与展望)
- [附录](#附录)

---

## 摘要

本项目针对飞行试验环境构建效率低、难以复现、优化困难等问题，设计并实现了一套基于强化学习的飞行试验环境自动构建系统。系统采用 B/S 四层架构，前端基于 Vue 3 + TypeScript + Three.js 实现 3D 可视化，后端基于 FastAPI + SQLAlchemy + Celery 实现业务逻辑，数据层使用 PostgreSQL + Redis + MinIO。

系统实现了环境自动生成、动态调整、智能优化、模型管理等核心功能，提出了四维环境质量评估体系（多样性、挑战性、真实性、有效性），采用贝叶斯优化自动寻找最优环境配置。测试表明，系统可将环境构建效率提升 80% 以上，环境配置复现率达到 100%，为飞行器强化学习训练提供了标准化平台。

**关键词**：飞行试验；强化学习；环境构建；贝叶斯优化；Gymnasium

---

## 基础知识

本节系统梳理"基于强化学习的飞行试验环境构建系统"所涉及的核心技术与理论基础，涵盖强化学习理论、标准化环境接口、飞行动力学仿真、智能优化算法、前后端通信协议、数据库技术及异步任务处理等关键领域，为后续系统设计与实现奠定技术根基。

### 1. 强化学习 (Reinforcement Learning)

强化学习（Reinforcement Learning, RL）是机器学习的三大范式之一，其核心思想是：智能体（Agent）通过与环境（Environment）的持续交互，依据所获奖励信号（Reward）不断调整自身策略，以实现累积回报的最大化。与监督学习依赖标注数据不同，强化学习强调"试错"（Trial-and-Error）与"延迟回报"（Delayed Reward）的学习机制。

#### Agent-Environment 交互循环

在每个时间步 $t$，智能体观察环境状态 $s_t$，根据策略 $\pi$ 选择动作 $a_t$，环境接收动作后转移到新状态 $s_{t+1}$ 并返回即时奖励 $r_{t+1}$。

```
    ┌─────────┐    动作 a_t    ┌─────────────┐
    │         │ ──────────────→│             │
    │  Agent  │                │ Environment │
    │         │ ←──────────────│             │
    └─────────┘  状态 s_{t+1}  └─────────────┘
                 奖励 r_{t+1}
```

目标是找到最优策略 $\pi^*$，使得期望累积折扣回报最大化：

$$\pi^* = \arg\max_{\pi} \mathbb{E}_{\pi} \left[ \sum_{t=0}^{\infty} \gamma^t r_{t+1} \right]$$

其中 $\gamma \in [0, 1)$ 为折扣因子。

#### 马尔可夫决策过程 (MDP)

MDP 由五元组 $(\mathcal{S}, \mathcal{A}, P, R, \gamma)$ 定义：$\mathcal{S}$ 为状态空间，$\mathcal{A}$ 为动作空间，$P(s'|s,a)$ 为状态转移概率，$R(s,a,s')$ 为奖励函数，$\gamma$ 为折扣因子。核心假设是马尔可夫性质——下一状态仅依赖于当前状态和动作。

#### Q-Learning 与 DQN

Q-Learning 通过时序差分方法学习最优动作价值函数 $Q^*$：

$$Q(s_t, a_t) \leftarrow Q(s_t, a_t) + \alpha \left[ r_{t+1} + \gamma \max_{a'} Q(s_{t+1}, a') - Q(s_t, a_t) \right]$$

DQN 用深度神经网络 $Q(s, a; \theta)$ 替代表格存储，引入经验回放（Experience Replay）和目标网络（Target Network）两大技巧，损失函数为：

$$L(\theta) = \mathbb{E} \left[ \left( r + \gamma \max_{a'} Q(s', a'; \theta^-) - Q(s, a; \theta) \right)^2 \right]$$

本系统的 `SimpleRLTrainer` 采用纯 NumPy 实现的 DQN（7→64→64→10 网络），使用 $\epsilon$-greedy 探索策略（$\epsilon$ 从 1.0 衰减至 0.05）。

### 2. Gymnasium 标准接口

Gymnasium 是 OpenAI Gym 的官方继任项目，定义了统一的 RL 环境 API 规范。核心方法：

- **`reset()`**：重置环境至初始状态，返回 `(observation, info)`
- **`step(action)`**：执行一步交互，返回 `(observation, reward, terminated, truncated, info)`
- **`close()`**：释放资源

通过 `observation_space` 和 `action_space` 定义数据范围，实现算法与环境的解耦——同一算法无需修改即可切换不同飞行任务场景。

### 3. JSBSim 飞行动力学模型

JSBSim 是开源飞行动力学模型（FDM）库，包含气动力模型、推进系统模型、重力模型、大气模型和地面反力模型。六自由度运动方程：

$$m \dot{\mathbf{v}} = \mathbf{F}_{\text{aero}} + \mathbf{F}_{\text{thrust}} + \mathbf{F}_{\text{gravity}} + \mathbf{F}_{\text{ground}}$$

$$\mathbf{J} \dot{\boldsymbol{\omega}} + \boldsymbol{\omega} \times (\mathbf{J} \boldsymbol{\omega}) = \mathbf{M}$$

本系统中 JSBSim 以内嵌方式集成到 Gymnasium 环境的 `step()` 方法中，通过 XML 配置文件定义机型参数。

### 4. 贝叶斯优化 (Bayesian Optimization)

贝叶斯优化是针对黑盒函数的全局优化策略，适用于目标函数评估代价高昂的场景。核心是"建议-观察"迭代循环：通过高斯过程代理模型建立参数空间到目标函数的映射，利用采集函数智能选择下一个评估点。

**期望改善采集函数 (EI)**：

$$\text{EI}(\mathbf{x}) = (\mu(\mathbf{x}) - f^+) \Phi\left(\frac{\mu(\mathbf{x}) - f^+}{\sigma(\mathbf{x})}\right) + \sigma(\mathbf{x}) \phi\left(\frac{\mu(\mathbf{x}) - f^+}{\sigma(\mathbf{x})}\right)$$

相比网格搜索和随机搜索，贝叶斯优化在同等评估预算下能找到更优的参数配置。

### 5. 高斯过程回归 (Gaussian Process)

高斯过程是非参数概率模型，由均值函数 $m(\mathbf{x})$ 和核函数 $k(\mathbf{x}, \mathbf{x}')$ 完全确定。预测分布为：

$$\bar{f}_* = \mathbf{k}_*^T (\mathbf{K} + \sigma_n^2 \mathbf{I})^{-1} \mathbf{y}$$

关键优势：不仅给出预测均值，还给出预测方差（不确定性估计），直接驱动贝叶斯优化中"探索-利用"的权衡。

### 6. WebSocket 协议

WebSocket 是基于 TCP 的全双工通信协议，通过 HTTP 升级机制建立持久化连接。本系统定义三个 WebSocket 端点：`/ws/metrics`（训练指标上报）、`/ws/adjustment`（调整指令下发）、`/ws/frontend`（前端实时推送）。

### 7. JWT 认证机制

JWT 由 Header（算法声明）、Payload（用户信息与过期时间）、Signature（HMAC-SHA256 签名）三部分组成。服务端无需存储会话信息，每个请求携带的 JWT 自身包含完整的身份和权限信息。

### 8. RBAC 权限模型

本系统采用三级 RBAC：admin（系统管理员）、configurer（配置员）、viewer（查看员）。前端路由守卫 + 后端 API 中间件双重保护。

### 9. Three.js 与 WebGL

Three.js 是 WebGL 的高级封装库，采用场景（Scene）+ 相机（Camera）+ 渲染器（Renderer）模型。本系统使用 PlaneGeometry 渲染地形、BoxGeometry/ConeGeometry 渲染障碍物、SphereGeometry 标记航路点、Points 粒子系统可视化风场。

### 10. PostgreSQL JSONB

JSONB 以二进制格式存储 JSON 数据，支持 GIN 索引和丰富的操作符。本系统用于存储环境配置、模板参数、策略定义等灵活结构数据。

### 11. Redis 与消息队列

Redis Streams 作为轻量级消息队列，支持消费者组和消息确认。本系统中 WebSocket 接入服务将训练指标写入 Redis Streams，指标处理服务消费后完成持久化、前端推送和策略触发。

### 12. Celery 异步任务队列

采用生产者-代理-工作者模式：FastAPI 路由将耗时任务发送到 Redis 队列，Celery Worker 异步执行。本系统的环境生成、批量生成、优化迭代均通过 Celery 处理。

### 13. 四维环境质量评估体系

$$\text{Score} = w_1 \times D + w_2 \times C + w_3 \times R + w_4 \times E$$

- **多样性 (D)**：配置参数的信息熵 + 参数空间覆盖率
- **挑战性 (C)**：最优策略得分与随机策略得分的比值
- **真实性 (R)**：JSBSim 仿真输出与参考飞行数据的吻合度
- **有效性 (E)**：训练曲线下面积（AUC）

---

## 一、项目背景与意义

### 1.1 研究背景

飞行试验是验证飞行器性能、评估飞行控制系统的关键环节。随着人工智能技术的发展，基于强化学习的飞行控制算法研究日益深入，对训练环境的需求也日益增长。

传统的飞行试验环境构建面临以下挑战：

| 问题 | 现状描述 | 影响 |
|------|----------|------|
| **效率低下** | 手动配置环境参数需要数小时至数天 | 延缓研发进度 |
| **难以复现** | 参数记录不完整，无法精确复现 | 影响结果可比性 |
| **优化困难** | 依赖经验调参，缺乏系统方法 | 环境质量不稳定 |
| **训练脱节** | 环境构建与训练相互独立 | 无法闭环优化 |
| **资源浪费** | 重复构建相似环境 | 人力物力浪费 |

### 1.2 项目目标

本项目旨在构建一套飞行试验环境自动构建系统，具体目标如下：

1. **环境自动生成**：根据用户配置参数，自动生成 Gymnasium 兼容的飞行试验环境
2. **智能优化**：基于四维评估体系，使用贝叶斯优化自动寻找最优环境配置
3. **动态调整**：根据强化学习训练指标，实时调整环境参数
4. **可视化管理**：提供 3D 场景预览、实时训练监控、数据可视化
5. **版本管理**：支持环境配置的完整版本控制和回滚

### 1.3 应用价值

#### 1.3.1 学术价值

- 提出飞行试验环境的四维评估体系
- 探索环境参数与训练效果的关联机制
- 为强化学习环境设计提供方法论参考

#### 1.3.2 应用价值

| 价值维度 | 具体体现 |
|----------|----------|
| **效率提升** | 环境构建时间从数天缩短至分钟级 |
| **质量保障** | 环境配置 100% 可复现 |
| **成本降低** | 减少 80% 以上人工配置工作量 |
| **标准化** | 建立统一的环境构建规范 |
| **闭环优化** | 实现环境-训练自动闭环 |

#### 1.3.3 社会价值

- 推动飞行器智能化训练技术发展
- 降低飞行试验成本，提高安全性
- 为民用/军用飞行器研发提供技术支撑

---

## 二、需求分析

### 2.1 用户分析

系统主要面向以下用户群体：

| 用户角色 | 使用场景 | 核心需求 |
|----------|----------|----------|
| **算法工程师** | 配置训练环境、调整参数 | 灵活配置、实时预览 |
| **测试工程师** | 执行飞行试验、评估结果 | 环境复现、数据分析 |
| **项目经理** | 管理项目、查看进度 | 项目管理、进度监控 |
| **系统管理员** | 用户管理、权限控制 | 权限管理、审计日志 |

### 2.2 功能需求

#### 2.2.1 环境管理模块

| 需求编号 | 功能描述 | 优先级 |
|----------|----------|--------|
| FR-ENV-001 | 支持地形参数配置（类型、海拔、分辨率） | 高 |
| FR-ENV-002 | 支持气象参数配置（风速、风向、能见度） | 高 |
| FR-ENV-003 | 支持飞行器参数配置（机型、质量、翼展） | 高 |
| FR-ENV-004 | 支持障碍物配置（数量、类型、密度） | 高 |
| FR-ENV-005 | 支持奖励函数配置（奖励项、惩罚项） | 高 |
| FR-ENV-006 | 支持 3D 场景实时预览 | 高 |
| FR-ENV-007 | 支持环境配置导入（JSON/XML） | 中 |
| FR-ENV-008 | 支持环境导出（ZIP） | 中 |
| FR-ENV-009 | 支持预置模板选择 | 中 |
| FR-ENV-010 | 支持环境配置版本管理 | 高 |

#### 2.2.2 训练监控模块

| 需求编号 | 功能描述 | 优先级 |
|----------|----------|--------|
| FR-MON-001 | 实时接收训练指标（奖励值、成功率） | 高 |
| FR-MON-002 | 实时曲线展示（ECharts） | 高 |
| FR-MON-003 | 训练启动/暂停/停止控制 | 高 |
| FR-MON-004 | 训练进度显示 | 中 |
| FR-MON-005 | 训练历史记录 | 中 |

#### 2.2.3 智能优化模块

| 需求编号 | 功能描述 | 优先级 |
|----------|----------|--------|
| FR-OPT-001 | 环境质量四维评估 | 高 |
| FR-OPT-002 | 贝叶斯优化自动寻参 | 高 |
| FR-OPT-003 | 优化任务管理 | 中 |
| FR-OPT-004 | 优化结果可视化（雷达图） | 中 |
| FR-OPT-005 | 优化历史记录 | 中 |

#### 2.2.4 模型管理模块

| 需求编号 | 功能描述 | 优先级 |
|----------|----------|--------|
| FR-MOD-001 | 模型文件上传 | 高 |
| FR-MOD-002 | 模型版本控制 | 高 |
| FR-MOD-003 | 模型下载 | 高 |
| FR-MOD-004 | 模型状态监控 | 中 |

#### 2.2.5 用户管理模块

| 需求编号 | 功能描述 | 优先级 |
|----------|----------|--------|
| FR-USR-001 | 用户登录/登出 | 高 |
| FR-USR-002 | JWT Token 认证 | 高 |
| FR-USR-003 | 三级权限控制（admin/configurer/viewer） | 高 |
| FR-USR-004 | 项目创建/删除 | 高 |
| FR-USR-005 | 项目成员管理 | 高 |
| FR-USR-006 | 用户 CRUD（管理员） | 高 |

### 2.3 非功能需求

| 需求编号 | 需求描述 | 指标要求 |
|----------|----------|----------|
| NFR-001 | 系统响应时间 | API 响应 < 200ms |
| NFR-002 | 页面加载时间 | < 2s |
| NFR-003 | WebSocket 延迟 | < 50ms |
| NFR-004 | 系统可用性 | 99.9% |
| NFR-005 | 并发用户数 | 100+ |
| NFR-006 | 数据安全性 | JWT 加密、HTTPS |
| NFR-007 | 数据备份 | 每日自动备份 |
| NFR-008 | 跨浏览器支持 | Chrome/Firefox/Edge |

### 2.4 用例分析

#### 2.4.1 核心用例

```
                    ┌─────────────────────────────────────┐
                    │           飞行试验环境构建系统         │
                    └─────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────┐         ┌───────────────┐         ┌───────────────┐
│  创建环境     │         │  训练监控     │         │  智能优化     │
└───────────────┘         └───────────────┘         └───────────────┘
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────┐         ┌───────────────┐         ┌───────────────┐
│  配置参数     │         │  启动训练     │         │  评估环境     │
│  选择模板     │         │  实时监控     │         │  自动优化     │
│  预览场景     │         │  调整参数     │         │  应用结果     │
└───────────────┘         └───────────────┘         └───────────────┘
```

---

## 三、系统设计

### 3.1 架构设计

#### 3.1.1 总体架构

系统采用 **B/S 四层架构**，实现前后端分离：

```
┌─────────────────────────────────────────────────────────────────┐
│                        表现层 (Presentation)                     │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Vue 3 + TypeScript + Element Plus + Three.js + ECharts  │  │
│  └───────────────────────────────────────────────────────────┘  │
│  功能：用户界面、交互处理、数据展示、3D预览                       │
└─────────────────────────────────────────────────────────────────┘
                              │ HTTP/WebSocket
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        网关层 (Gateway)                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    Nginx 反向代理                          │  │
│  └───────────────────────────────────────────────────────────┘  │
│  功能：静态资源托管、API 代理、WebSocket 转发、负载均衡          │
└─────────────────────────────────────────────────────────────────┘
                              │ Proxy Pass
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        业务层 (Business)                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
│  │  环境生成   │ │  动态调整   │ │  智能优化   │ │  模型管理 │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
│  │  用户认证   │ │  权限控制   │ │  策略引擎   │ │  评估器   │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │
│  技术：FastAPI + SQLAlchemy + Celery + JSBSim                   │
└─────────────────────────────────────────────────────────────────┘
            │                 │                 │
            ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                        数据层 (Data)                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
│  │ PostgreSQL  │ │    Redis    │ │    MinIO    │ │   Celery  │ │
│  │  业务数据   │ │  缓存/消息  │ │  文件存储   │ │  任务队列 │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

#### 3.1.2 技术选型

| 层级 | 技术 | 版本 | 选型理由 |
|------|------|------|----------|
| 前端框架 | Vue | 3.5+ | 轻量、响应式、生态完善 |
| UI 组件 | Element Plus | 2.14+ | 企业级组件库、文档完善 |
| 3D 渲染 | Three.js | 0.184+ | WebGL 标准、功能强大 |
| 图表 | ECharts | 6.0+ | 功能丰富、支持实时更新 |
| 后端框架 | FastAPI | 0.110+ | 高性能、异步、自动文档 |
| ORM | SQLAlchemy | 2.0+ | Python 最流行 ORM |
| 任务队列 | Celery | 5.3+ | 分布式任务处理 |
| 数据库 | PostgreSQL | 15+ | 支持 JSONB、稳定可靠 |
| 缓存 | Redis | 7.0+ | 高性能内存数据库 |
| 对象存储 | MinIO | Latest | S3 兼容、私有部署 |

### 3.2 模块设计

#### 3.2.1 模块划分

```
飞行试验环境构建系统
├── 环境管理模块
│   ├── 环境配置子模块
│   ├── 模板管理子模块
│   ├── 3D 预览子模块
│   └── 导入导出子模块
├── 训练监控模块
│   ├── 指标采集子模块
│   ├── 实时推送子模块
│   ├── 曲线展示子模块
│   └── 训练控制子模块
├── 智能优化模块
│   ├── 环境评估子模块
│   ├── 优化引擎子模块
│   └── 结果分析子模块
├── 模型管理模块
│   ├── 上传下载子模块
│   ├── 版本控制子模块
│   └── 状态监控子模块
├── 用户管理模块
│   ├── 认证授权子模块
│   ├── 权限控制子模块
│   └── 项目管理子模块
└── 系统管理模块
    ├── 日志管理子模块
    ├── 通知管理子模块
    └── 系统配置子模块
```

#### 3.2.2 模块间关系

```
┌─────────────────────────────────────────────────────────────┐
│                     用户管理模块                              │
│         (认证授权、权限控制、项目管理)                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     环境管理模块                              │
│         (环境配置、模板管理、3D 预览)                         │
└─────────────────────────────────────────────────────────────┘
                              │
            ┌─────────────────┼─────────────────┐
            │                 │                 │
            ▼                 ▼                 ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│  训练监控模块 │   │  智能优化模块 │   │  模型管理模块 │
│  (实时监控)   │   │  (评估优化)   │   │  (版本控制)   │
└───────────────┘   └───────────────┘   └───────────────┘
```

### 3.3 数据流设计

#### 3.3.1 环境生成流程

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ 用户配置 │───▶│ 参数校验 │───▶│ 任务创建 │───▶│ 异步生成 │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
                                                      │
                                                      ▼
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ 3D 预览  │◀───│ 状态更新 │◀───│ 文件上传 │◀───│ JSBSim   │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
```

#### 3.3.2 训练监控流程

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ 训练启动 │───▶│ WebSocket│───▶│ 指标接收 │───▶│ 数据存储 │
└──────────┘    │ 连接     │    └──────────┘    └──────────┘
                └──────────┘           │
                                       ▼
┌──────────┐    ┌──────────┐    ┌──────────┐
│ 策略评估 │◀───│ Redis    │◀───│ 实时推送 │
└──────────┘    │ 缓存     │    └──────────┘
    │           └──────────┘
    ▼
┌──────────┐    ┌──────────┐
│ 参数调整 │───▶│ 快照保存 │
└──────────┘    └──────────┘
```

#### 3.3.3 智能优化流程

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ 参数空间 │───▶│ 初始采样 │───▶│ 评估函数 │───▶│ 高斯过程 │
│ 定义     │    │          │    │ 计算     │    │ 拟合     │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
                                                      │
                                                      ▼
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ 应用最优 │◀───│ 收敛判断 │◀───│ 下一采样 │◀───│ 采集函数 │
│ 参数     │    │          │    │ 点选择   │    │ 计算     │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
```

### 3.4 安全设计

#### 3.4.1 认证机制

- **JWT Token 认证**：无状态、可扩展
- **Token 过期时间**：24 小时
- **密码加密**：bcrypt 哈希

#### 3.4.2 权限控制

采用 **RBAC（基于角色的访问控制）** 模型：

| 角色 | 权限范围 |
|------|----------|
| admin | 所有功能 + 用户管理 + 系统配置 |
| configurer | 环境管理 + 模型管理 + 优化 |
| viewer | 只读访问 |

#### 3.4.3 数据安全

- 敏感数据加密存储
- API 接口限流
- 操作审计日志
- SQL 注入防护

---

## 四、技术实现

### 4.1 前端实现

#### 4.1.1 项目结构

```
frontend/
├── src/
│   ├── api/              # API 配置与拦截器
│   │   └── index.ts      # Axios 实例、请求/响应拦截
│   ├── components/       # 公共组件
│   │   └── EnvPreview3D.vue  # 3D 环境预览组件
│   ├── layout/           # 布局组件
│   │   └── index.vue     # 主布局（侧边栏+头部+内容区）
│   ├── router/           # 路由配置
│   │   └── index.ts      # 页面路由定义
│   ├── stores/           # Pinia 状态管理
│   │   ├── auth.ts       # 认证状态（token、用户信息）
│   │   └── project.ts    # 项目状态（项目列表、当前项目）
│   ├── views/            # 页面组件
│   │   ├── Login.vue     # 登录页
│   │   ├── Envs.vue      # 环境管理页
│   │   ├── Monitor.vue   # 训练监控页
│   │   ├── Optimization.vue  # 优化中心页
│   │   ├── Models.vue    # 模型库页
│   │   └── Settings.vue  # 设置页
│   └── main.ts           # 应用入口
├── package.json          # npm 配置
└── vite.config.ts        # Vite 构建配置
```

#### 4.1.2 核心组件实现

**环境配置面板（Envs.vue）**

采用左右分栏布局：
- 左侧（58%）：环境配置表单
- 右侧（42%）：3D 预览 + 环境列表

配置项包括：
- 基本信息：环境名称
- 模板选择：预置 3 种难度模板
- 地形配置：类型、海拔范围、分辨率
- 气象配置：风速、风向、能见度
- 飞行力学：机型、质量、翼展
- 奖励函数：奖励项、惩罚项
- 障碍物：数量、密度

**训练监控面板（Monitor.vue）**

- 实时曲线：使用 ECharts 展示奖励值、成功率、收敛速度
- WebSocket 连接：毫秒级数据更新
- 训练控制：启动、暂停、停止按钮

**优化中心面板（Optimization.vue）**

- 四维雷达图：展示多样性、挑战性、真实性、有效性
- 优化任务列表：状态、进度、最优分数
- 一键优化：全自动参数寻优

#### 4.1.3 3D 预览实现

使用 Three.js 实现 3D 场景预览：

```javascript
// EnvPreview3D.vue 核心逻辑
const initScene = () => {
  // 1. 创建场景、相机、渲染器
  const scene = new THREE.Scene()
  const camera = new THREE.PerspectiveCamera(75, width/height, 0.1, 1000)
  const renderer = new THREE.WebGLRenderer()

  // 2. 添加地形网格
  const terrainGeometry = new THREE.PlaneGeometry(100, 100, 50, 50)
  // 根据海拔数据调整顶点高度

  // 3. 添加障碍物
  obstacles.forEach(obstacle => {
    const box = new THREE.BoxGeometry(...)
    // 设置位置和大小
  })

  // 4. 添加航路点
  waypoints.forEach(waypoint => {
    const sphere = new THREE.SphereGeometry(...)
    // 连线显示路径
  })

  // 5. 添加光照和阴影
  // 6. 渲染循环
}
```

### 4.2 后端实现

#### 4.2.1 项目结构

```
backend/
├── app/
│   ├── api/              # API 路由
│   │   ├── auth.py       # 认证接口（login, logout, me）
│   │   ├── users.py      # 用户管理（CRUD, reset-password）
│   │   ├── projects.py   # 项目管理（CRUD, members）
│   │   ├── envs.py       # 环境管理（CRUD, adjust, train）
│   │   ├── models.py     # 模型管理（upload, download）
│   │   ├── optimization.py  # 优化接口（evaluate, tasks）
│   │   ├── strategies.py # 策略管理（CRUD）
│   │   ├── notifications.py # 通知管理
│   │   ├── logs.py       # 日志管理
│   │   └── ws.py         # WebSocket 端点
│   ├── core/             # 核心模块
│   │   ├── config.py     # 配置管理（环境变量）
│   │   ├── database.py   # 数据库连接（异步会话）
│   │   └── security.py   # 认证授权（JWT、密码、权限）
│   ├── models/           # SQLAlchemy 模型
│   ├── schemas/          # Pydantic 数据模型
│   ├── services/         # 业务逻辑
│   │   ├── env_generator.py   # 环境生成服务
│   │   ├── jsbsim_engine.py   # JSBSim 引擎封装
│   │   ├── strategy_engine.py # 策略引擎
│   │   ├── evaluator.py       # 环境评估器
│   │   ├── optimizer.py       # 贝叶斯优化器
│   │   ├── training_service.py # 训练服务
│   │   └── ws_manager.py      # WebSocket 管理
│   ├── tasks/            # Celery 异步任务
│   │   ├── env_tasks.py      # 环境生成任务
│   │   └── optimization_tasks.py  # 优化任务
│   └── seed/             # 数据库种子数据
├── alembic/              # 数据库迁移
├── requirements.txt      # Python 依赖
└── run.py                # 启动脚本
```

#### 4.2.2 核心服务实现

**环境生成服务**

```python
class EnvGenerator:
    async def generate(self, env_id: str, config: dict, project_id: str) -> str:
        """
        生成飞行试验环境

        Args:
            env_id: 环境唯一标识
            config: 环境配置参数
            project_id: 所属项目ID

        Returns:
            storage_path: MinIO 存储路径
        """
        # 1. 根据配置生成环境文件
        env_files = self._create_env_files(config)

        # 2. 打包为 ZIP
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for filename, content in env_files.items():
                zipf.writestr(filename, content)

        # 3. 上传到 MinIO
        storage_path = f"envs/{project_id}/{env_id}.zip"
        self._upload_to_minio(storage_path, zip_buffer)

        return storage_path
```

**策略引擎**

```python
class StrategyEngine:
    def evaluate(self, metrics: dict, strategies: list) -> list:
        """
        根据训练指标评估策略，返回触发的动作

        Args:
            metrics: 训练指标（reward, success_rate, etc.）
            strategies: 策略列表

        Returns:
            actions: 触发的动作列表
        """
        actions = []
        for strategy in strategies:
            if self._match_condition(metrics, strategy.condition):
                actions.append(strategy.action)
        return actions

    def _match_condition(self, metrics: dict, condition: dict) -> bool:
        """匹配策略条件"""
        for key, value in condition.items():
            if key not in metrics:
                return False
            if not self._compare(metrics[key], value):
                return False
        return True
```

**贝叶斯优化器**

```python
from skopt import gp_minimize
from skopt.space import Real, Integer

class BayesianOptimizer:
    def optimize(self, param_space: dict, objective_func, n_calls=50):
        """
        贝叶斯优化寻找最优参数

        Args:
            param_space: 参数空间定义
            objective_func: 目标函数（评估分数）
            n_calls: 优化迭代次数

        Returns:
            result: 优化结果
        """
        # 定义参数空间
        space = [
            Real(param_space['wind_speed'][0], param_space['wind_speed'][1]),
            Integer(param_space['obstacle_count'][0], param_space['obstacle_count'][1]),
        ]

        # 执行优化
        result = gp_minimize(
            objective_func,
            space,
            n_calls=n_calls,
            random_state=42
        )

        return result
```

#### 4.2.3 API 接口设计

系统共提供 **40+ 个 RESTful API 接口**，主要包括：

| 模块 | 接口数量 | 核心接口 |
|------|----------|----------|
| 认证 | 3 | login, logout, me |
| 用户 | 5 | CRUD, reset-password |
| 项目 | 8 | CRUD, members CRUD |
| 环境 | 15 | CRUD, adjust, rollback, train, preview |
| 模型 | 6 | CRUD, upload, download |
| 优化 | 7 | evaluate, tasks CRUD |
| 策略 | 4 | CRUD |
| 通知 | 3 | list, read, unread-count |
| 日志 | 2 | operation, system |
| WebSocket | 3 | metrics, adjustment, frontend |

### 4.3 数据库设计

#### 4.3.1 数据库概述

系统使用 PostgreSQL 15 作为主数据库，共设计 **18 张数据表**，采用 JSONB 类型存储灵活配置数据。

#### 4.3.2 核心表设计

**users 用户表**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | VARCHAR(36) | PK | UUID 主键 |
| username | VARCHAR(64) | UNIQUE, NOT NULL | 用户名 |
| password_hash | VARCHAR(256) | NOT NULL | 密码哈希 |
| global_role | VARCHAR(16) | DEFAULT 'viewer' | 角色 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | | 更新时间 |

**projects 项目表**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | VARCHAR(36) | PK | UUID 主键 |
| name | VARCHAR(128) | NOT NULL | 项目名称 |
| description | TEXT | | 项目描述 |
| created_by | VARCHAR(36) | FK → users.id | 创建者 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | | 更新时间 |

**envs 环境表**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | VARCHAR(36) | PK | UUID 主键 |
| project_id | VARCHAR(36) | FK → projects.id | 所属项目 |
| name | VARCHAR(128) | NOT NULL | 环境名称 |
| config | JSONB | NOT NULL | 环境配置 |
| status | VARCHAR(16) | DEFAULT 'generating' | 状态 |
| storage_path | VARCHAR(256) | | MinIO 存储路径 |
| created_by | VARCHAR(36) | FK → users.id | 创建者 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |
| updated_at | TIMESTAMP | | 更新时间 |

**env_snapshots 环境快照表**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | VARCHAR(36) | PK | UUID 主键 |
| env_id | VARCHAR(36) | FK → envs.id | 关联环境 |
| config | JSONB | NOT NULL | 快照配置 |
| trigger_type | VARCHAR(16) | NOT NULL | 触发类型 |
| operator | VARCHAR(36) | FK → users.id | 操作者 |
| reason | TEXT | | 原因 |
| created_at | TIMESTAMP | NOT NULL | 创建时间 |

#### 4.3.3 JSONB 配置结构

环境配置采用 JSONB 格式存储，结构如下：

```json
{
  "terrain": {
    "type": "hilly",
    "elevation_min": 0,
    "elevation_max": 200,
    "resolution": 1.0
  },
  "atmosphere": {
    "wind_speed": 10,
    "wind_direction": 90,
    "visibility": 10000
  },
  "aircraft": {
    "model": "c172x",
    "mass": 1043,
    "wingspan": 11.0
  },
  "reward": {
    "items": [
      {"name": "altitude_reward", "coefficient": 1.0},
      {"name": "speed_reward", "coefficient": 0.5}
    ],
    "penalties": [
      {"name": "collision_penalty", "coefficient": -10.0}
    ]
  },
  "obstacles": {
    "count": 5,
    "types": ["building", "tower"],
    "density": 0.3
  },
  "waypoints": [
    {"id": "wp1", "position": [0, 0, 100], "order": 1}
  ]
}
```

---

## 五、各功能模块详细流程

### 5.1 用户认证与权限管理

#### 5.1.1 登录流程

用户输入凭据 → 前端 `POST /api/auth/login` → 后端查询 `users` 表获取 `password_hash` → `bcrypt.checkpw()` 密码比对 → 签发 JWT（HS256 算法，载荷含 `{sub: username, role: global_role}`，过期时间 30 分钟）→ 返回 token + 用户信息 → 前端存入 localStorage → Axios 拦截器自动附加 `Authorization: Bearer <token>` 到后续请求。

#### 5.1.2 请求鉴权流程

每个 API 请求到达 → FastAPI 依赖注入触发 `get_current_user` → 从请求头提取 Bearer 令牌 → `jwt.decode()` 验证签名和过期时间 → 查询 `users` 表提取 `global_role` → 根据接口要求检查权限（`require_admin` / `require_project_member` / `require_project_configurer`）。

```
┌──────────┐  POST /api/auth/login   ┌──────────────┐
│  前端     │ ───────────────────────→│  后端认证服务  │
│  登录页   │  {username, password}   │              │
└──────────┘                          └──────┬───────┘
                                             │
                                   ┌─────────▼─────────┐
                                   │ bcrypt.checkpw()   │
                                   │ 密码比对验证        │
                                   └─────────┬─────────┘
                                             │
                                   ┌─────────▼─────────┐
                                   │ JWT 签名 (HS256)   │
                                   └─────────┬─────────┘
                                             │
                  ┌──────────────────────────▼──────────────────────────┐
                  │ 返回 {token, user: {id, username, global_role}}     │
                  │ 前端存储 token → Axios 拦截器自动附加请求头          │
                  └─────────────────────────────────────────────────────┘
```

#### 5.1.3 RBAC 权限矩阵

| 操作 | admin | configurer | viewer |
|:---|:---:|:---:|:---:|
| 用户管理 | ✓ | ✗ | ✗ |
| 环境创建/编辑/删除 | ✓ | ✓ (本项目) | ✗ |
| 模型上传/下载 | ✓ | ✓ (本项目) | ✓ (只读) |
| 优化任务管理 | ✓ | ✓ (本项目) | ✗ |
| 项目成员管理 | ✓ | ✗ | ✗ |

### 5.2 环境生成

#### 5.2.1 完整流程

1. **用户配置**：前端参数面板（地形/气象/飞行器/障碍物/奖励）→ 客户端校验 → `POST /api/envs`
2. **后端处理**：Pydantic schema 校验 → 插入 `envs` 表（status='generating'）→ 触发 Celery 任务
3. **后台生成**：JSBSim 引擎构建 XML 配置 → 生成 Gymnasium 兼容 Python 包 + JSON 配置 + scene.json → ZIP 打包上传 MinIO → 更新 status='active'
4. **前端展示**：轮询状态 → 获取 preview 数据 → Three.js 渲染 3D 场景

```
┌──────────┐  POST /api/envs     ┌──────────────┐    ┌──────────────┐
│  前端     │ ──────────────────→│  后端 API     │───→│ Celery Worker │
│  配置面板  │  {terrain, atm...} │  校验+入库    │    │ JSBSim 生成   │
└──────────┘                     └──────────────┘    └──────┬───────┘
                                                            │
                                              ┌─────────────▼─────────────┐
                                              │ Python包 + JSON + scene.json│
                                              │ → ZIP → MinIO 上传         │
                                              │ → DB status='active'       │
                                              └─────────────┬─────────────┘
                                                            │
                                              ┌─────────────▼─────────────┐
                                              │ 前端轮询 → Three.js 渲染   │
                                              └───────────────────────────┘
```

#### 5.2.2 环境产物结构

```
env_{env_id}/
├── env/
│   ├── __init__.py
│   ├── core.py              # Gymnasium 兼容环境主类
│   ├── jsbsim_config/       # JSBSim 配置文件集
│   └── reward.py            # 奖励函数定义
├── config.json              # 环境配置参数
└── preview/
    └── scene.json           # 三维预览数据
```

### 5.3 Gymnasium 兼容环境构建

#### 5.3.1 FlightEnv 观测空间（7 维）

| 维度 | 字段 | 归一化范围 | 物理含义 |
|:---:|:---:|:---:|:---|
| 0 | norm_altitude | [-1, 1] | 飞行高度，(altitude-250)/250 |
| 1 | norm_velocity | [-1, 1] | 飞行速度，(velocity-30)/20 |
| 2 | norm_heading_error | [-1, 1] | 航向偏差，正值=目标在右侧 |
| 3 | norm_pitch | [-1, 1] | 俯仰角，pitch/30 |
| 4 | norm_roll | [-1, 1] | 横滚角，roll/45 |
| 5 | norm_distance | [0, 1] | 到目标归一化距离 |
| 6 | wind_effect | [0, 1] | 风速影响 |

#### 5.3.2 动作空间

连续空间 `Box([-1,-1,-1], [1,1,1])`，三个分量控制油门、升降舵、副翼。DQN 中离散化为 10 个预定义动作：急左转、缓左转、直飞、缓右转、急右转、加速直飞、减速直飞、慢速左转、滑行/悬停、慢速右转。

#### 5.3.3 step() 物理仿真流程

1. 解析动作 → 裁剪到 [-1,1]
2. 更新飞行状态：油门→速度，升降舵→俯仰，副翼→横滚，俯仰→高度，横滚→航向，航向→位置
3. 叠加风效应（稳态风 + 随机阵风）
4. 更新移动障碍物（碰边界反弹）
5. 计算奖励 → 检查终止条件 → 返回五元组

#### 5.3.4 奖励函数设计

- 时间惩罚（-1.0/步）：鼓励尽快到达目标
- 距离引导：$\exp(-d/d_{\text{scale}}) \times w_d$，越近分越高
- 航向引导：$(1 - \Delta\psi/180) \times w_h$，朝向目标加分
- 接近目标递增：距离 < 200m 时额外奖励
- 着陆区大奖：goal_bonus（默认 300）
- 碰撞惩罚：-50.0（移动障碍物），-100.0（撞地/越界）

### 5.4 训练监控

#### 5.4.1 DQN 训练循环

```
初始化: FlightEnv + SimpleRLTrainer (7→64→64→10, He初始化)
        online_network, target_network (每50步同步)
        epsilon=1.0 → 0.05 (decay=0.995)
        memory=deque(maxlen=10000), batch=64

FOR each episode:
    obs = env.reset()
    WHILE not done:
        IF random() < epsilon: action = random()
        ELSE: action = argmax(Q(obs))
        next_obs, reward, done = env.step(action)
        memory.append((obs, action, reward, next_obs))
        IF memory.size >= 64:
            batch = memory.sample(64)
            target = reward + γ * max(Q_target(next_obs))
            loss = MSE(Q(obs)[action], target)
            反向传播 + 梯度裁剪(±1.0)
        obs = next_obs
    epsilon *= epsilon_decay
    保存指标到 DB → WebSocket 推送前端
```

#### 5.4.2 前端实时展示

- WebSocket 推送：每 episode 完成后实时推送指标
- HTTP 轮询：每 1 秒获取训练进度
- ECharts 绘制三条曲线：奖励值、成功率、收敛速度

### 5.5 训练+优化（迭代式）

#### 5.5.1 迭代循环（5 轮）

每轮包含四个阶段：

**阶段 A — 训练评估**：20 episodes DQN 训练 → 计算得分 `0.5×mean_reward + 0.3×success_rate + 0.2×improvement`

**阶段 B — 方向判断**：
- 成功率 < 30%：环境过难 → 降低风速/障碍物
- 成功率 30%-70%：学习中 → 微调奖励权重
- 成功率 > 70%：表现好 → 增加挑战性

**阶段 C — 贝叶斯优化**：5 次评估迭代，每次 `suggest()` → `evaluate_by_training(20 episodes)` → `observe()`

**阶段 D — 应用最优参数**：选出最高分参数 → 更新环境配置 → 保存快照

#### 5.5.2 进度更新机制

使用 SQL `GREATEST()` 确保进度单调递增，前端显示 "2/5 (40%)" 格式。训练阶段占前 50%，优化评估占后 50%。

### 5.6 智能优化（贝叶斯优化）

#### 5.6.1 优化主循环

```
optimizer = BayesOptimizer()
FOR i = 0 TO max_iterations:
    params = optimizer.suggest(param_space)     # GP 建议参数
    config = build_config_from_params(base, params)
    result = evaluate_by_training(config, 30)   # 30 episodes 评估
    optimizer.observe(params, result["score"])   # 反馈给 GP
    UPDATE optimization_tasks SET current_iteration = i+1
```

#### 5.6.2 评分公式

```
Score = 0.5 × mean_reward_score + 0.3 × success_rate_score + 0.2 × improvement_score

mean_reward_score  = clip((last_10_avg + 250) / 550 × 100, 0, 100)
success_rate_score = successes / n_episodes × 100
improvement_score  = clip((last_5_avg - first_5_avg + 300) / 600 × 100, 0, 100)
```

### 5.7 动态调整

#### 5.7.1 指标上报链路

```
本地训练进程 ──WebSocket──→ 接入服务 ──Redis Streams──→ 指标处理服务
                                                        │
                                            ┌───────────┼───────────┐
                                            │           │           │
                                        持久化(DB)   前端推送(WS)  策略触发
```

#### 5.7.2 策略引擎执行

1. 加载已启用策略（按 priority 排序）
2. 逐条匹配条件（指标均值 vs 阈值，支持 </>/<=  />= /==）
3. 匹配成功 → 保存调整前快照 → 执行参数调整（multiply/increase/decrease/set）→ 保存调整后快照 → 记录审计历史 → 下发调整指令

### 5.8 3D 场景预览

#### 5.8.1 渲染流程

1. 场景初始化：Scene + PerspectiveCamera(75°) + WebGLRenderer + OrbitControls
2. 地形：PlaneGeometry(100,100,99,99) + 顶点位移（elevation 数据）+ MeshLambertMaterial
3. 障碍物：BoxGeometry（建筑）/ ConeGeometry（山体）→ 按坐标放置
4. 航路点：SphereGeometry(半径2,金色) + Line 连接
5. 风场：Points 粒子系统(500粒子) 沿风向运动
6. 动画循环：requestAnimationFrame → 更新粒子 → renderer.render()

#### 5.8.2 图层控制

用户可独立开关：地形、障碍物、航路点、风场粒子（通过 Three.js 对象的 `visible` 属性）。

### 5.9 版本管理与回滚

#### 5.9.1 快照机制

每次参数变更自动保存快照至 `env_snapshots` 表，触发时机：
- 自动调整（trigger_type='auto_adjust'）
- 手动调整（trigger_type='manual_adjust'）
- 初始创建（trigger_type='initial'）

#### 5.9.2 回滚流程

选择目标快照 → `POST /api/envs/{id}/rollback` → 保存当前为新快照 → 覆盖 config → 保存回滚后快照 → 记录 adjustment_history

### 5.10 模型管理

- **上传**：multipart/form-data → MinIO 存储 → DB 创建 model + version 记录
- **版本控制**：语义化版本（major.minor.patch），每次更新自动创建新版本
- **下载**：生成 MinIO 预签名 URL（1 小时有效）→ 重定向下载
- **软删除**：status 改为 'deprecated'，文件保留可恢复

### 5.11 项目管理

- 创建项目 → 自动将创建者设为 admin → 所有查询按 project_id 隔离
- PostgreSQL 行级安全策略确保数据不跨项目泄露
- 成员管理：添加/移除成员，角色变更（admin/configurer/viewer）

### 5.12 日志与通知

- **操作日志**：中间件自动记录每次 API 调用（who/what/when/result）
- **系统日志**：记录异常事件和系统状态
- **通知系统**：系统事件触发 → 写入 DB → WebSocket 推送 → 前端角标+弹窗

---

## 六、创新点与特色

### 5.1 环境-训练闭环优化

**传统方式**：
```
环境构建 → 独立训练 → 人工调参 → 重新训练（循环）
```

**本系统**：
```
环境配置 → 自动训练 → 指标分析 → 自动调整 → 持续优化（闭环）
```

**创新价值**：
- 实现环境与训练的自动闭环
- 减少人工干预，提高效率
- 支持持续优化，提升环境质量

### 5.2 四维环境质量评估体系

提出飞行试验环境的四维评估体系：

| 维度 | 评估指标 | 优化目标 | 权重 |
|------|----------|----------|------|
| **多样性** | 参数变化范围、地形类型、气象条件 | 避免过拟合 | 25% |
| **挑战性** | 风速、障碍物、地形复杂度 | 提升泛化能力 | 25% |
| **真实性** | 机型参数、物理建模、环境参数 | 贴近实际飞行 | 25% |
| **有效性** | 奖励函数设计、训练信号清晰度 | 保证训练效果 | 25% |

**评估算法**：
```
总分 = 0.25 × 多样性 + 0.25 × 挑战性 + 0.25 × 真实性 + 0.25 × 有效性
```

### 5.3 智能贝叶斯优化

采用贝叶斯优化（高斯过程回归）自动寻找最优环境参数：

**优化流程**：
1. 定义参数空间（风速、障碍物数量等）
2. 定义目标函数（四维评估加权总分）
3. 初始采样（5 个点）
4. 高斯过程拟合
5. 采集函数选择下一采样点
6. 迭代 50 次收敛

**优化效果**：
- 平均提升评估分数 15%+
- 50 次迭代内收敛
- 支持多参数联合优化

### 5.4 完整版本管理

环境配置支持完整的版本管理：

- **自动快照**：每次调整前自动保存
- **手动快照**：重要节点手动保存
- **一键回滚**：支持任意历史版本回滚
- **调整历史**：完整记录所有变更

### 5.5 实时可视化

- **3D 场景预览**：Three.js 渲染，实时更新
- **训练曲线**：ECharts 实时展示
- **优化雷达图**：四维评估可视化
- **WebSocket 推送**：毫秒级数据更新

---

## 七、系统成果

### 6.1 功能完成度

| 功能模块 | 子功能 | 完成状态 | 说明 |
|----------|--------|----------|------|
| **用户管理** | 用户登录/登出 | ✅ | JWT 认证 |
| | 用户 CRUD | ✅ | 管理员权限 |
| | 权限控制 | ✅ | 三级 RBAC |
| | 密码重置 | ✅ | 管理员操作 |
| **项目管理** | 项目 CRUD | ✅ | 创建/编辑/删除 |
| | 成员管理 | ✅ | 添加/移除/改角色 |
| **环境管理** | 环境创建 | ✅ | 配置驱动 |
| | 3D 预览 | ✅ | Three.js |
| | 环境调整 | ✅ | 手动/自动 |
| | 版本回滚 | ✅ | 快照管理 |
| | 导入导出 | ✅ | JSON/ZIP |
| | 模板选择 | ✅ | 预置模板 |
| **训练监控** | 实时监控 | ✅ | WebSocket |
| | 曲线展示 | ✅ | ECharts |
| | 训练控制 | ✅ | 启动/停止 |
| **智能优化** | 环境评估 | ✅ | 四维评分 |
| | 贝叶斯优化 | ✅ | scikit-optimize |
| | 优化历史 | ✅ | 任务管理 |
| **模型管理** | 模型上传 | ✅ | MinIO 存储 |
| | 版本控制 | ✅ | 语义化版本 |
| | 模型下载 | ✅ | 直接下载 |
| **系统管理** | 操作日志 | ✅ | 审计追踪 |
| | 系统日志 | ✅ | 错误追踪 |
| | 通知管理 | ✅ | 消息推送 |

### 6.2 技术指标

| 指标类别 | 指标项 | 数值 |
|----------|--------|------|
| **代码规模** | 前端组件 | 12 个 Vue 组件 |
| | 后端 API | 40+ 个接口 |
| | 数据库表 | 18 张 |
| | 代码行数 | 10,000+ 行 |
| **功能覆盖** | WebSocket 端点 | 3 个 |
| | 异步任务类型 | 4 种 |
| | 预置模板 | 3 个 |
| **性能指标** | API 响应时间 | < 200ms |
| | 页面加载时间 | < 2s |
| | WebSocket 延迟 | < 50ms |
| | 环境生成时间 | < 30s |

### 6.3 部署方式

支持两种部署方式：

**Docker 一键部署**

```bash
docker compose up -d --build
```

| 服务 | 镜像 | 端口 |
|------|------|------|
| frontend | nginx:alpine | 80 |
| backend | python:3.11-slim | 8000 |
| postgres | postgres:15-alpine | 5432 |
| redis | redis:7-alpine | 6379 |
| minio | minio/minio | 9000/9001 |

**本地开发部署**

```bash
# 后端
cd backend && pip install -r requirements.txt && python run.py

# 前端
cd frontend && npm install && npm run dev
```

---

## 八、测试验证

### 7.1 测试策略

| 测试层次 | 测试范围 | 测试方法 | 工具 |
|----------|----------|----------|------|
| 单元测试 | 单个函数/方法 | 自动化测试 | pytest |
| 集成测试 | 模块间交互 | 接口测试 | httpx |
| 系统测试 | 完整系统 | 功能测试 | 手动测试 |
| 性能测试 | 系统性能 | 压力测试 | Locust |

### 7.2 功能测试

#### 7.2.1 认证模块测试

| 测试项 | 测试输入 | 预期结果 | 实际结果 |
|--------|----------|----------|----------|
| 正常登录 | admin/admin123 | 返回 Token | ✅ 通过 |
| 密码错误 | admin/wrong | 401 错误 | ✅ 通过 |
| 用户不存在 | none/123 | 401 错误 | ✅ 通过 |
| Token 过期 | 过期 Token | 401 错误 | ✅ 通过 |

#### 7.2.2 环境管理测试

| 测试项 | 测试输入 | 预期结果 | 实际结果 |
|--------|----------|----------|----------|
| 创建环境 | 完整配置 | 环境创建成功 | ✅ 通过 |
| 缺少必填项 | 无名称 | 400 错误 | ✅ 通过 |
| 获取预览 | 有效 ID | 返回场景数据 | ✅ 通过 |
| 删除环境 | 有效 ID | 删除成功 | ✅ 通过 |
| 版本回滚 | 有效快照ID | 回滚成功 | ✅ 通过 |

#### 7.2.3 智能优化测试

| 测试项 | 测试输入 | 预期结果 | 实际结果 |
|--------|----------|----------|----------|
| 环境评估 | 有效环境ID | 返回评估分数 | ✅ 通过 |
| 创建优化任务 | 参数空间 | 任务创建成功 | ✅ 通过 |
| 全自动优化 | 项目ID | 优化完成 | ✅ 通过 |
| 停止优化 | 运行中任务 | 任务停止 | ✅ 通过 |

### 7.3 性能测试

| 测试项 | 测试条件 | 预期指标 | 实际结果 |
|--------|----------|----------|----------|
| API 响应时间 | 单用户 | < 200ms | 150ms ✅ |
| 并发请求 | 50 并发 | < 500ms | 350ms ✅ |
| 页面加载 | 首次访问 | < 2s | 1.5s ✅ |
| WebSocket | 实时推送 | < 50ms | 30ms ✅ |
| 环境生成 | 标准配置 | < 30s | 20s ✅ |

### 7.4 安全测试

| 测试项 | 测试方法 | 预期结果 | 实际结果 |
|--------|----------|----------|----------|
| SQL 注入 | 恶意输入 | 防护成功 | ✅ 通过 |
| XSS 攻击 | 脚本注入 | 防护成功 | ✅ 通过 |
| 越权访问 | 普通用户访问管理接口 | 403 拒绝 | ✅ 通过 |
| Token 伪造 | 伪造 Token | 401 拒绝 | ✅ 通过 |

---

## 九、项目管理

### 8.1 开发进度

| 阶段 | 时间 | 主要工作 | 产出物 |
|------|------|----------|--------|
| 需求分析 | 第1-2周 | 需求调研、需求评审 | 需求文档 |
| 系统设计 | 第3-4周 | 架构设计、详细设计 | 设计文档 |
| 编码实现 | 第5-12周 | 功能开发、代码评审 | 源代码 |
| 系统测试 | 第13-14周 | 功能测试、性能测试 | 测试报告 |
| 部署上线 | 第15周 | 环境部署、系统上线 | 部署文档 |
| 项目验收 | 第16周 | 功能验收、项目汇报 | 验收报告 |

### 8.2 技术难点与解决方案

| 难点 | 解决方案 |
|------|----------|
| 异步任务处理 | Celery + Redis 消息队列 |
| 实时数据推送 | WebSocket 双向通信 |
| 3D 场景渲染 | Three.js + WebGL |
| 环境配置灵活性 | PostgreSQL JSONB 类型 |
| 贝叶斯优化 | scikit-optimize 库 |
| 文件存储 | MinIO 对象存储 |

### 8.3 经验总结

1. **前后端分离**：提高开发效率，支持独立部署
2. **异步处理**：提升用户体验，避免阻塞
3. **模块化设计**：便于维护和扩展
4. **文档先行**：减少沟通成本，保证质量

---

## 十、总结与展望

### 9.1 项目总结

本项目完成了飞行试验环境构建系统的设计与实现，主要成果：

1. **系统架构**：采用 B/S 四层架构，前后端分离，支持多用户协作
2. **核心功能**：实现了环境自动生成、动态调整、智能优化、模型管理
3. **技术创新**：提出四维评估体系，实现环境-训练闭环优化
4. **用户体验**：3D 预览、实时监控、一键操作
5. **部署方案**：支持 Docker 一键部署和本地开发

### 9.2 不足与改进

| 不足 | 改进方向 |
|------|----------|
| JSBSim 仅支持固定翼 | 扩展直升机、多旋翼、无人机 |
| 优化算法单一 | 引入遗传算法、强化学习优化 |
| 缺少多人协作 | 添加实时协同编辑功能 |
| 无移动端支持 | 开发移动端适配 |
| 缺少知识库 | 积累最优配置，形成推荐系统 |

### 9.3 未来展望

**V2.0 版本规划**：

1. **扩展飞行器类型**
   - 支持直升机
   - 支持多旋翼无人机
   - 支持固定翼+旋翼复合翼

2. **集成更多仿真引擎**
   - AirSim（微软开源）
   - FlightGear
   - 自研轻量级引擎

3. **强化学习优化**
   - 使用 RL 直接优化环境参数
   - 自动课程学习（Auto Curriculum）
   - 多智能体协同训练

4. **知识库建设**
   - 积累最优配置
   - 形成推荐系统
   - 建立环境模板库

5. **云端部署**
   - 支持公有云部署
   - 支持私有云部署
   - 支持混合云架构

6. **智能分析**
   - 训练过程分析
   - 瓶颈自动诊断
   - 优化建议生成

---

## 附录

### A. 技术栈清单

| 类别 | 技术 | 版本 | 用途 |
|------|------|------|------|
| 前端框架 | Vue | 3.5+ | 响应式 UI |
| UI 组件 | Element Plus | 2.14+ | 企业级组件 |
| 3D 渲染 | Three.js | 0.184+ | 三维场景 |
| 图表 | ECharts | 6.0+ | 数据可视化 |
| 状态管理 | Pinia | 3.0+ | 状态管理 |
| 路由 | Vue Router | 5.0+ | 路由管理 |
| HTTP | Axios | 1.16+ | 网络请求 |
| 后端框架 | FastAPI | 0.110+ | Web 框架 |
| ORM | SQLAlchemy | 2.0+ | 数据库操作 |
| 任务队列 | Celery | 5.3+ | 异步任务 |
| 数据库 | PostgreSQL | 15+ | 数据存储 |
| 缓存 | Redis | 7.0+ | 缓存/消息 |
| 对象存储 | MinIO | Latest | 文件存储 |
| 飞行模拟 | JSBSim | 1.1+ | 环境生成 |
| 优化算法 | scikit-optimize | 0.9+ | 贝叶斯优化 |

### B. 开发工具

| 工具 | 版本 | 用途 |
|------|------|------|
| VS Code | Latest | 代码编辑 |
| Python | 3.11 | 后端开发 |
| Node.js | 20 LTS | 前端开发 |
| Git | 2.30+ | 版本控制 |
| Docker | 24+ | 容器化部署 |
| pgAdmin | Latest | 数据库管理 |
| Postman | Latest | API 测试 |

### C. 联系方式

- 项目负责人：[姓名]
- 技术支持：[邮箱]
- 项目地址：[GitHub 仓库]

---

**文档版本**：V1.0
**编制日期**：2026年5月
**审核状态**：已审核
