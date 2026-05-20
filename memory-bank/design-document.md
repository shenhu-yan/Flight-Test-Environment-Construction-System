# 基于强化学习的飞行试验环境构建系统 - 产品设计文档

## 1. 概述

### 1.1 文档目的

本文档定义系统整体架构、模块划分、核心数据模型、接口规范和关键技术方案，作为后续开发与测试的基准。

### 1.2 设计原则

| 原则 | 说明 |
| :--- | :--- |
| 算法无关性 | 环境对外暴露 Gymnasium 标准接口，不绑定任何特定 RL 算法 |
| 固定翼优先、架构可扩展 | V1.0 聚焦固定翼飞行器，架构层面预留旋翼/无人机扩展点 |
| 规则驱动先行、学习型可演进 | 动态调整策略 V1.0 采用规则驱动，策略引擎设计支持学习型策略插拔 |
| 项目隔离 | 所有数据（模型、环境、配置）以项目 ID 为隔离边界 |

### 1.3 术语定义

| 术语 | 定义 |
| :--- | :--- |
| Gymnasium | OpenAI Gym 的后续维护项目，提供标准化的 RL 环境接口 (`reset`/`step`/`close`) |
| JSBSim | 开源飞行动力学模型（FDM），用于固定翼飞行器物理仿真 |
| 环境产物 | Gymnasium 兼容的 Python 环境包 + JSON 配置文件的组合 |
| 策略库 | 动态调整策略的集合，V1.0 为规则驱动（if-then），长期可扩展学习型策略 |

---

## 2. 系统架构

### 2.1 总体架构

系统采用 B/S 架构，分为四层：

```
┌─────────────────────────────────────────────────────────┐
│                     前端展示层 (Browser)                  │
│   Vue3 + Three.js(3D预览) + ECharts(数据可视化)          │
├─────────────────────────────────────────────────────────┤
│                     网关层 (Nginx)                        │
│   静态资源托管 / 反向代理 / WebSocket 路由                │
├─────────────────────────────────────────────────────────┤
│                     后端服务层 (Python)                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │ 环境生成  │ │ 动态调整  │ │ 智能优化  │ │ 模型管理  │   │
│  │  服务     │ │  服务     │ │  服务     │ │  服务     │   │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘   │
│       │            │            │            │          │
│  ┌────┴────────────┴────────────┴────────────┴─────┐   │
│  │              公共服务 (权限/日志/消息)             │   │
│  └─────────────────────┬───────────────────────────┘   │
│                        │                                │
│  ┌─────────────────────┴───────────────────────────┐   │
│  │             WebSocket 接入服务                    │   │
│  │      (接收本地训练进程的实时指标上报)              │   │
│  └─────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────┤
│                     数据持久层                            │
│  PostgreSQL(业务数据) + MinIO(文件/模型存储) + Redis(缓存)│
└─────────────────────────────────────────────────────────┘

外部组件：
┌───────────────────┐     ┌────────────────────┐
│  JSBSim 仿真引擎   │     │  用户本地训练进程    │
│  (服务端内嵌调用)   │     │  (通过 WebSocket    │
│                    │     │   上报训练指标)      │
└───────────────────┘     └────────────────────┘
```

### 2.2 技术选型

| 层次 | 技术栈 | 选型理由 |
| :--- | :--- | :--- |
| 前端框架 | Vue 3 + TypeScript | 组件化开发、生态成熟 |
| 3D 预览 | Three.js | JSBSim 场景渲染、视角控制、场景缩放 |
| 数据可视化 | ECharts | 曲线/柱状图/热力图，支持实时刷新 |
| 后端框架 | FastAPI (Python) | 原生 async、WebSocket 支持、自动 OpenAPI 文档 |
| 仿真引擎 | JSBSim | 开源固定翼 FDM，Python 绑定可用 |
| 优化算法 | scikit-optimize (贝叶斯优化) | 轻量、与 Python 生态无缝集成 |
| 关系数据库 | PostgreSQL | 结构化业务数据、JSON 字段支持 |
| 文件存储 | MinIO | S3 兼容、适合模型文件与环境包存储 |
| 缓存 | Redis | 会话管理、实时指标缓冲 |
| 消息队列 | Redis Streams | 指标上报与调整指令的异步传递 |

### 2.3 核心数据流

```
用户通过前端配置需求
        │
        ▼
  环境生成服务 ──→ 调用 JSBSim 生成三类产物：
        │           1. Python 环境包 (Gymnasium 兼容)
        │           2. JSON 配置文件
        │           3. 场景预览数据 (供 Three.js 渲染)
        │
        ▼
  用户下载环境包 → 本地执行 RL 训练
        │
        ▼
  本地训练进程通过 WebSocket 上报指标
        │
        ▼
  动态调整服务 ←── 实时指标流
        │
        ├── 指标异常？→ 触发自动调整策略 → 下发调整建议
        │
        ▼
  智能优化服务 ←── 环境评估结果
        │
        ├── 贝叶斯优化 → 更新生成引擎参数
        │
        ▼
  模型管理服务 ←── 全生命周期管理
```

---

## 3. 功能模块详细设计

### 3.1 环境生成模块 (EnvGen)

#### 3.1.1 模块职责

根据用户需求（XML/JSON 配置文件或图形化参数输入），调用 JSBSim 仿真引擎，生成 Gymnasium 兼容的 Python 环境包 + JSON 配置文件的组合产物，并产出三维预览数据。

#### 3.1.2 核心流程

```
┌─────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ 需求输入  │───→│ 参数解析  │───→│ 模板匹配  │───→│ 环境构建  │───→│ 产物打包  │
│(配置/图形)│    │ 与校验    │    │ 与实例化  │    │(JSBSim)  │    │ 与输出    │
└─────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
                                                    │
                                               ┌────┴────┐
                                               │ 预览数据 │
                                               │  生成    │
                                               └─────────┘
```

**步骤说明：**

1. **需求输入**：用户通过 XML/JSON 文件上传或图形化界面设置参数
2. **参数解析与校验**：解析输入参数，校验必填项、范围、类型。校验失败返回具体错误信息
3. **模板匹配与实例化**：从模板库匹配最接近的模板，用用户参数覆盖模板默认值，生成完整的参数集
4. **环境构建**：调用 JSBSim 引擎，根据参数集构建飞行动力学模型、场景地形、气象条件、障碍物布局
5. **预览数据生成**：基于环境参数生成轻量级场景描述（地形网格、障碍物位置、航路点），供前端 Three.js 渲染
6. **产物打包**：将 Python 环境包、JSON 配置文件、预览数据打包为环境产物，存储至 MinIO，元数据写入数据库

#### 3.1.3 需求映射

| PRD ID | 设计方案 |
| :--- | :--- |
| FG-01 | 上传 XML/JSON 文件后，后端 `参数解析器` 统一转换为内部 `EnvConfig` 对象；支持对配置文件做 schema 校验 |
| FG-02 | 前端提供可视化参数配置面板，包含：地形（类型/海拔范围）、气象（风速/风向/能见度）、飞行力学（机型/质量/翼展）、奖励函数（奖励项/惩罚项/系数）等控件组；提交后生成 `EnvConfig` |
| FG-03 | 模板库存储于 PostgreSQL，以 JSON 格式保存模板参数。模板字段：`template_id`、`name`、`aircraft_type`（fixed_wing/rotorcraft/uav）、`difficulty`（basic/medium/hard）、`config`（完整 EnvConfig） |
| FG-04 | 批量生成：用户指定数量 N 与参数差异范围 Δ，系统在基准配置上对指定维度施加随机扰动，生成 N 个差异化环境，各自分配唯一 `env_id` |
| FG-05 | 导出：将环境产物（Python 包 + JSON 配置）打包为 zip 文件下载；导入：上传 zip 文件，系统解析并还原环境记录 |
| FG-06 | 生成前预览：环境构建完成后、用户确认前，将预览数据推送给前端 Three.js 渲染三维场景；用户可在预览界面调整参数后重新生成 |

#### 3.1.4 环境产物结构

```
env_{env_id}/
├── env/
│   ├── __init__.py
│   ├── core.py              # Gymnasium 兼容环境主类
│   ├── jsbsim_config/       # JSBSim 配置文件集
│   │   ├── aircraft.xml     # 机型配置
│   │   ├── atmosphere.xml   # 气象配置
│   │   └── terrain.xml      # 地形配置
│   └── reward.py            # 奖励函数定义
├── config.json              # 环境配置参数（与前端配置一一对应）
└── preview/
    └── scene.json           # 三维预览数据（地形网格、障碍物坐标、航路点）
```

`core.py` 中的环境类遵循 Gymnasium 接口：

```python
class FlightEnv(gym.Env):
    metadata = {"render_modes": ["human", "rgb_array"]}

    def __init__(self, config_path: str, render_mode: str = None):
        """加载 JSON 配置，初始化 JSBSim 实例"""

    def reset(self, seed=None, options=None) -> tuple[ObsType, dict]:
        """重置仿真状态，返回初始观测"""

    def step(self, action) -> tuple[ObsType, float, bool, bool, dict]:
        """执行动作，推进一步仿真，返回 (obs, reward, terminated, truncated, info)"""

    def close(self):
        """释放 JSBSim 资源"""
```

---

### 3.2 动态调整模块 (DynAdjust)

#### 3.2.1 模块职责

实时接收本地训练进程上报的 RL 训练指标，根据指标变化自动/手动调整环境参数，记录完整调整历史。

#### 3.2.2 指标上报与接收

**通信协议**：WebSocket

**上报消息格式**：

```json
{
  "type": "metric_report",
  "project_id": "proj_001",
  "env_id": "env_001",
  "task_id": "task_001",
  "timestamp": 1716000000,
  "metrics": {
    "episode_reward": 125.3,
    "success_rate": 0.72,
    "convergence_speed": 0.85,
    "step": 5000
  }
}
```

**数据流**：

```
本地训练进程 ──WebSocket──→ 接入服务 ──Redis Streams──→ 指标处理服务
                                                      │
                                          ┌───────────┴───────────┐
                                          │ 写入 DB（持久化）       │
                                          │ 推送前端（实时展示）     │
                                          │ 触发策略引擎（异常检测） │
                                          └───────────────────────┘
```

#### 3.2.3 调整策略引擎

**V1.0 规则驱动策略**，每条策略结构如下：

```json
{
  "rule_id": "R001",
  "name": "收敛过慢时降低难度",
  "condition": {
    "metric": "convergence_speed",
    "operator": "<",
    "threshold": 0.3,
    "duration_steps": 1000
  },
  "action": {
    "type": "param_adjust",
    "adjustments": [
      {"param": "wind_speed", "op": "multiply", "value": 0.7},
      {"param": "obstacle_count", "op": "decrease", "value": 2}
    ]
  },
  "priority": 1,
  "enabled": true
}
```

**策略执行流程**：

```
指标到达 → 遍历已启用策略 → 条件匹配？
                            ├── 是 → 执行 action → 生成调整指令 → 记录历史
                            └── 否 → 跳过
```

**双模式设计**：

- **内置默认模式**：系统预置一组常见策略，使用默认阈值
- **用户自定义模式**：用户可修改策略阈值、启停策略、新增自定义策略

**调整指令下发**：调整指令通过 WebSocket 下发给本地训练进程，本地进程可选择应用或忽略。

#### 3.2.4 需求映射

| PRD ID | 设计方案 |
| :--- | :--- |
| DA-01 | WebSocket 接入服务实时接收指标；指标处理服务持久化至 `training_metrics` 表；前端通过 WebSocket 接收实时推送进行展示 |
| DA-02 | 策略引擎包含默认策略库；异常检测基于用户可配阈值 + 持续时间窗口；调整指令通过 WebSocket 实时下发 |
| DA-03 | 前端调整面板提供环境参数的实时编辑控件；修改后通过 REST API 提交，后端下发调整指令 |
| DA-04 | 每次 adjusts 操作写入 `adjustment_history` 表，记录：时间、操作人(系统/用户)、调整前后参数快照、触发原因、调整后的性能变化（异步回填） |
| DA-05 | 环境参数快照在每次调整前自动保存；版本回滚操作：选择目标版本 → 系统将参数覆盖为该版本快照 → 下发调整指令 |

---

### 3.3 智能优化模块 (IntellOpt)

#### 3.3.1 模块职责

对已生成的环境进行自动评估与优化，提升环境质量和后续生成效果。

#### 3.3.2 环境质量评估体系

**四维加权评分模型**：

$$
Score = w_1 \times D + w_2 \times C + w_3 \times R + w_4 \times E
$$

其中默认权重 $w_1=0.25, w_2=0.25, w_3=0.25, w_4=0.25$，用户可自定义。

| 维度 | 量化方法 | 数据来源 |
| :--- | :--- | :--- |
| 多样性 (D) | 配置参数的信息熵 + 参数空间覆盖率 | 环境配置参数库 + 同批环境参数分布 |
| 挑战性 (C) | 最优策略得分 / 随机策略得分 的比值，归一化到 [0, 100] | 后端 JSBSim 进程内运行随机策略+启发式规则 100 步 |
| 真实性 (R) | JSBSim 物理模型输出与参考飞行数据的吻合度（均方误差归一化） | JSBSim 仿真输出 vs 预置参考数据集 |
| 有效性 (E) | 训练曲线下面积（AUC），归一化到 [0, 100]；无训练数据时默认 50 分 | 用户上报的训练指标历史 |

**评估触发时机**：

- 环境生成后自动触发
- 用户手动触发
- 持续优化周期到达时批量触发

**评估输出**：四维分数 + 总分 + 各维度的定性优化建议。

#### 3.3.3 贝叶斯优化流程

```
┌──────────────┐
│  初始化       │  定义待优化参数空间（模板权重、随机化策略系数、物理建模精度等）
└──────┬───────┘
       │
       ▼
┌──────────────┐     ┌──────────────┐
│  生成建议参数  │────→│  用建议参数   │
│  (采集函数)    │     │  生成测试环境  │
└──────────────┘     └──────┬───────┘
                            │
                            ▼
                     ┌──────────────┐
                     │  评估环境得分  │
                     └──────┬───────┘
                            │
                            ▼
                     ┌──────────────┐
                     │  更新代理模型  │  (高斯过程)
                     └──────┬───────┘
                            │
                   是否达到迭代上限？
                   ┌─── 否 ────┘
                   │
                   ▼ 是
            ┌──────────────┐
            │  输出最优参数  │
            └──────┬───────┘
                   │
                   ▼
            ┌──────────────┐
            │  效果验证      │  用标准算法在优化前后环境中对比测试
            └──────┬───────┘
                   │
                   ▼
            ┌──────────────┐
            │  生成对比报告   │  图表形式展示优化前后差异
            └──────────────┘
```

**待优化参数空间（V1.0）**：

| 参数 | 范围 | 说明 |
| :--- | :--- | :--- |
| template_weight | [0.1, 1.0] | 模板参数对最终配置的影响权重 |
| randomization_strength | [0.0, 0.5] | 参数随机扰动强度 |
| physics_precision | [0.5, 1.0] | JSBSim 模型精度（影响计算步长） |
| obstacle_density_factor | [0.5, 2.0] | 障碍物密度系数 |
| wind_variability | [0.0, 1.0] | 风场变化幅度 |

**预留接口**：优化器抽象基类，支持未来插拔进化策略：

```python
class BaseOptimizer(ABC):
    @abstractmethod
    def suggest(self, history: list[Observation]) -> dict: ...

    @abstractmethod
    def observe(self, params: dict, score: float) -> None: ...
```

#### 3.3.4 需求映射

| PRD ID | 设计方案 |
| :--- | :--- |
| IO-01 | 四维加权评分模型，每次评估输出分数与优化建议；评估结果存储于 `env_evaluations` 表 |
| IO-02 | 贝叶斯优化引擎（scikit-optimize），优化生成引擎的参数空间；优化结果更新生成引擎默认参数 |
| IO-03 | 用户可在前端配置各维度权重、优化目标；系统将权重传入评估函数和优化器 |
| IO-04 | 定时任务框架（APScheduler），按用户设定周期触发批量再评估与优化流程 |
| IO-05 | 优化完成自动运行基准算法对比测试，生成 ECharts 可视化报告；报告存储于 `optimization_reports` 表 |

---

### 3.4 模型管理模块 (ModelMgr)

#### 3.4.1 模块职责

对场景模型、物理模型、RL 算法模型、奖励函数模型等进行统一生命周期管理，确保项目级隔离和版本控制。

#### 3.4.2 模型分类

| 模型类型 | 格式 | 示例 |
| :--- | :--- | :--- |
| 场景模型 | JSBSim XML + 地形数据 | 机场场景、山区场景 |
| 物理模型 | JSBSim XML（机型配置） | Cessna172、F16 |
| RL 算法模型 | Python 包（.whl / .tar.gz） | 用户自定义算法 |
| 奖励函数模型 | Python 源码 / JSON 规则 | 着陆奖励、巡航奖励 |

#### 3.4.3 项目隔离与权限

```
项目 (project_id)
├── 任务 (task_id)
│   ├── 环境 A
│   ├── 环境 B
│   └── 模型 X (v1, v2, v3)
├── 模型 Y (v1)
└── ...

用户角色：
├── 系统管理员 (admin)    → 全局管理所有项目
├── 配置员 (configurer)   → 仅管理所属项目的模型
└── 查看员 (viewer)       → 仅可查看，不可修改
```

**权限矩阵**：

| 操作 | admin | configurer | viewer |
| :--- | :---: | :---: | :---: |
| 上传模型 | ✓ (全局) | ✓ (本项目) | ✗ |
| 修改模型 | ✓ (全局) | ✓ (本项目) | ✗ |
| 调用模型 | ✓ (全局) | ✓ (本项目) | ✓ (本项目) |
| 删除模型 | ✓ (全局) | ✓ (本项目) | ✗ |
| 导出模型 | ✓ (全局) | ✓ (本项目) | ✓ (本项目) |
| 管理用户 | ✓ | ✗ | ✗ |

#### 3.4.4 版本控制

- 模型更新时自动递增版本号（语义化版本：major.minor.patch）
- 保留所有历史版本的文件和元数据
- 版本对比：展示两个版本的元数据差异（参数、描述、大小）+ 配置文件 diff
- 版本回滚：一键回滚至历史版本（将旧版本标记为当前版本）

#### 3.4.5 需求映射

| PRD ID | 设计方案 |
| :--- | :--- |
| MM-01 | 统一 `models` 表管理所有类型模型的生命周期；上传 → MinIO 存储 + DB 元数据；删除 → 软删除（标记 `deprecated`） |
| MM-02 | 所有查询和操作强制携带 `project_id` 条件；数据层面行级安全策略（Row Level Security）确保隔离 |
| MM-03 | `model_versions` 表存储版本链；对比接口返回元数据 diff + 配置文件 diff；回滚接口将目标版本设为当前 |
| MM-04 | 多条件组合检索 API：`GET /api/models?project_id=&task_id=&type=&version=&created_after=`；环境生成等服务通过内部 API 调用 |
| MM-05 | 基于角色的访问控制（RBAC），操作审计日志写入 `audit_logs` 表 |
| MM-06 | `status` 字段标记模型状态（active/error/deprecated/recommended）；定时任务扫描弃用模型；高频调用模型自动标"推荐" |

---

### 3.5 用户交互模块 (UserInter)

#### 3.5.1 页面结构

```
┌─────────────────────────────────────────────────┐
│                    顶部导航栏                      │
│  Logo │  环境管理 │ 训练监控 │ 优化中心 │ 模型库 │ 设置 │
├─────────┬───────────────────────────────────────┤
│         │                                       │
│  侧边栏  │              主内容区                  │
│         │                                       │
│ 项目切换  │   根据导航切换：                       │
│ 快捷操作  │   - 环境生成 / 配置 / 预览             │
│ 消息通知  │   - 训练指标实时监控                   │
│         │   - 评估报告 / 优化任务                  │
│         │   - 模型列表 / 版本管理                  │
│         │   - 用户 / 权限 / 日志管理               │
│         │                                       │
├─────────┴───────────────────────────────────────┤
│                    底部状态栏                      │
│  WebSocket 连接状态 │ 当前项目 │ 最近消息            │
└─────────────────────────────────────────────────┘
```

#### 3.5.2 核心页面设计

**环境生成页**：
- 左侧：参数配置面板（折叠分组：地形/气象/飞行力学/奖励函数）
- 右侧：三维预览区（Three.js 渲染），支持鼠标拖拽旋转、滚轮缩放、元素隐藏/显示
- 底部：操作栏（生成/批量生成/保存为模板/导出）

**训练监控页**：
- 上部：训练指标实时曲线（ECharts，奖励值/成功率/收敛速度，WebSocket 实时刷新）
- 下部：环境参数当前状态 + 手动调整面板
- 侧边：调整历史时间线

**优化中心页**：
- 环境评估结果四维雷达图
- 优化任务管理（启动/停止/查看进度）
- 优化前后对比报告（图表）

**模型库页**：
- 模型列表（支持筛选、搜索）
- 模型详情（版本历史、版本对比）
- 上传/下载/删除操作

#### 3.5.3 三维预览功能

| 功能 | 实现方式 |
| :--- | :--- |
| 地形渲染 | Three.js 加载地形高程数据，生成网格曲面 |
| 障碍物显示 | 基于坐标信息渲染几何体（建筑物/山体） |
| 航路显示 | 航路点连线 + 箭头指向 |
| 视角控制 | OrbitControls：鼠标左键旋转、右键平移、滚轮缩放 |
| 元素显隐 | 图层控制面板：地形/障碍物/航路/气象 各自独立显隐开关 |
| 气象可视化 | 粒子系统表示风场方向和强度 |

#### 3.5.4 需求映射

| PRD ID | 设计方案 |
| :--- | :--- |
| UI-01 | 模块化单页应用，每个功能模块为独立路由页面 |
| UI-02 | Three.js + OrbitControls 实现；`scene.json` 数据驱动渲染 |
| UI-03 | ECharts 绑定 WebSocket 实时数据源；支持曲线/柱状图/热力图；图表可导出为 PNG/SVG |
| UI-04 | 三级 RBAC，前端路由守卫 + 后端接口鉴权双保障 |
| UI-05 | WebSocket 推送 + 前端消息中心（角标数字 + 弹窗通知 + 站内信列表） |
| UI-06 | 后端 `operation_logs` + `system_logs` 双表；前端日志查询页支持多条件筛选、CSV 导出 |

---

## 4. 数据模型设计

### 4.1 核心实体关系

```
project ──1:N──→ task ──1:N──→ env
project ──1:N──→ model ──1:N──→ model_version
env ──1:N──→ env_snapshot (参数快照/版本)
env ──1:N──→ env_evaluation
env ──1:N──→ training_metric
env ──1:N──→ adjustment_history
user ──N:M──→ project_role
optimization_task ──1:N──→ optimization_report
```

### 4.2 核心表结构

#### projects

| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| id | VARCHAR(36) PK | 项目 ID (UUID) |
| name | VARCHAR(128) | 项目名称 |
| description | TEXT | 项目描述 |
| created_by | VARCHAR(36) FK | 创建人 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

#### tasks

| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| id | VARCHAR(36) PK | 任务 ID (UUID) |
| project_id | VARCHAR(36) FK | 所属项目 |
| name | VARCHAR(128) | 任务名称 |
| description | TEXT | 任务描述 |
| created_by | VARCHAR(36) FK | 创建人 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

#### envs

| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| id | VARCHAR(36) PK | 环境 ID |
| project_id | VARCHAR(36) FK | 所属项目 |
| task_id | VARCHAR(36) FK | 所属任务（可空） |
| name | VARCHAR(128) | 环境名称 |
| config | JSONB | 环境完整配置参数 |
| template_id | VARCHAR(36) FK | 基于的模板（可空） |
| status | VARCHAR(16) | generating / active / deprecated |
| storage_path | VARCHAR(256) | MinIO 存储路径 |
| created_by | VARCHAR(36) FK | 创建人 |
| created_at | TIMESTAMP | 创建时间 |

#### env_snapshots

| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| id | VARCHAR(36) PK | 快照 ID |
| env_id | VARCHAR(36) FK | 环境 ID |
| config | JSONB | 参数快照 |
| trigger_type | VARCHAR(16) | auto_adjust / manual_adjust / initial |
| operator | VARCHAR(36) FK | 操作人 |
| reason | TEXT | 调整原因 |
| created_at | TIMESTAMP | 快照时间 |

#### adjustment_history

| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| id | VARCHAR(36) PK | 记录 ID |
| env_id | VARCHAR(36) FK | 环境 ID |
| snapshot_before | VARCHAR(36) FK | 调整前快照 |
| snapshot_after | VARCHAR(36) FK | 调整后快照 |
| trigger_type | VARCHAR(16) | auto / manual |
| trigger_rule | VARCHAR(36) FK | 触发的策略 ID（自动调整时） |
| operator | VARCHAR(36) FK | 操作人 |
| metric_change | JSONB | 调整后性能变化（异步回填） |
| created_at | TIMESTAMP | 调整时间 |

#### env_evaluations

| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| id | VARCHAR(36) PK | 评估 ID |
| env_id | VARCHAR(36) FK | 环境 ID |
| diversity_score | FLOAT | 多样性评分 0-100 |
| challenge_score | FLOAT | 挑战性评分 0-100 |
| realism_score | FLOAT | 真实性评分 0-100 |
| effectiveness_score | FLOAT | 有效性评分 0-100 |
| total_score | FLOAT | 总分 |
| weights | JSONB | 各维度权重 |
| suggestions | JSONB | 优化建议 |
| evaluated_at | TIMESTAMP | 评估时间 |

#### training_metrics

| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| id | BIGSERIAL PK | 自增 ID |
| env_id | VARCHAR(36) FK | 环境 ID |
| task_id | VARCHAR(36) FK | 任务 ID |
| episode_reward | FLOAT | 奖励值 |
| success_rate | FLOAT | 成功率 |
| convergence_speed | FLOAT | 收敛速度 |
| step | INTEGER | 训练步数 |
| reported_at | TIMESTAMP | 上报时间 |

#### models

| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| id | VARCHAR(36) PK | 模型 ID |
| project_id | VARCHAR(36) FK | 所属项目 |
| name | VARCHAR(128) | 模型名称 |
| type | VARCHAR(32) | scene / physics / rl_algorithm / reward |
| status | VARCHAR(16) | active / error / deprecated / recommended |
| description | TEXT | 描述 |
| current_version | VARCHAR(20) | 当前版本号 |
| created_by | VARCHAR(36) FK | 上传者 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

#### model_versions

| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| id | VARCHAR(36) PK | 版本 ID |
| model_id | VARCHAR(36) FK | 模型 ID |
| version | VARCHAR(20) | 版本号 (semver) |
| storage_path | VARCHAR(256) | MinIO 存储路径 |
| metadata | JSONB | 版本元数据（参数/描述/大小） |
| created_at | TIMESTAMP | 创建时间 |

#### users

| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| id | VARCHAR(36) PK | 用户 ID |
| username | VARCHAR(64) | 用户名 |
| password_hash | VARCHAR(256) | 密码哈希 |
| global_role | VARCHAR(16) | admin / configurer / viewer |
| created_at | TIMESTAMP | 创建时间 |

#### project_roles

| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| id | VARCHAR(36) PK | ID |
| user_id | VARCHAR(36) FK | 用户 ID |
| project_id | VARCHAR(36) FK | 项目 ID |
| role | VARCHAR(16) | admin / configurer / viewer |

#### templates

| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| id | VARCHAR(36) PK | 模板 ID |
| name | VARCHAR(128) | 模板名称 |
| aircraft_type | VARCHAR(32) | fixed_wing / rotorcraft / uav |
| difficulty | VARCHAR(16) | basic / medium / hard |
| config | JSONB | 完整环境配置 |
| is_builtin | BOOLEAN | 是否内置模板 |
| created_by | VARCHAR(36) FK | 创建人 |
| created_at | TIMESTAMP | 创建时间 |

#### optimization_tasks

| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| id | VARCHAR(36) PK | 任务 ID |
| project_id | VARCHAR(36) FK | 项目 ID |
| param_space | JSONB | 待优化参数空间定义 |
| weights | JSONB | 评估维度权重 |
| max_iterations | INTEGER | 最大迭代次数 |
| current_iteration | INTEGER | 当前迭代 |
| status | VARCHAR(16) | pending / running / completed / failed |
| best_params | JSONB | 最优参数 |
| best_score | FLOAT | 最优分数 |
| created_at | TIMESTAMP | 创建时间 |

#### optimization_reports

| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| id | VARCHAR(36) PK | 报告 ID |
| task_id | VARCHAR(36) FK | 优化任务 ID |
| before_scores | JSONB | 优化前各维度分数 |
| after_scores | JSONB | 优化后各维度分数 |
| comparison_data | JSONB | 对比图表数据 |
| created_at | TIMESTAMP | 创建时间 |

---

## 5. 接口设计

### 5.1 接口规范

- 所有 REST API 遵循 RESTful 风格，使用 JSON 格式
- 统一响应格式：

```json
{
  "code": 0,
  "message": "success",
  "data": { ... }
}
```

- 错误码范围：`0` 成功，`4xx` 客户端错误，`5xx` 服务端错误
- 所有接口需携带 `Authorization: Bearer <token>` 头部（登录接口除外）

### 5.2 核心接口列表

#### 5.2.1 环境生成

| 方法 | 路径 | 说明 |
| :--- | :--- | :--- |
| POST | /api/envs | 生成单个环境 |
| POST | /api/envs/batch | 批量生成环境 |
| GET | /api/envs | 查询环境列表 |
| GET | /api/envs/{env_id} | 获取环境详情 |
| DELETE | /api/envs/{env_id} | 删除环境 |
| POST | /api/envs/{env_id}/preview | 生成预览数据 |
| GET | /api/envs/{env_id}/export | 导出环境包 |
| POST | /api/envs/import | 导入环境包 |
| GET | /api/templates | 查询模板列表 |
| POST | /api/templates | 创建模板 |
| PUT | /api/templates/{id} | 修改模板 |
| DELETE | /api/templates/{id} | 删除模板 |

#### 5.2.2 动态调整

| 方法 | 路径 | 说明 |
| :--- | :--- | :--- |
| WebSocket | /ws/metrics | 训练指标上报通道 |
| WebSocket | /ws/adjustment | 调整指令下发通道 |
| WebSocket | /ws/frontend | 前端实时推送通道（指标广播 + 通知） |
| POST | /api/envs/{env_id}/adjust | 手动调整环境参数 |
| POST | /api/envs/{env_id}/rollback | 回滚至指定快照 |
| GET | /api/envs/{env_id}/snapshots | 查询快照列表 |
| GET | /api/envs/{env_id}/adjustment-history | 查询调整历史 |
| GET | /api/strategies | 查询策略列表 |
| PUT | /api/strategies/{id} | 修改策略（阈值/启停） |
| POST | /api/strategies | 新增自定义策略 |

#### 5.2.3 智能优化

| 方法 | 路径 | 说明 |
| :--- | :--- | :--- |
| POST | /api/envs/{env_id}/evaluate | 触发环境评估 |
| GET | /api/envs/{env_id}/evaluations | 查询评估历史 |
| POST | /api/optimization-tasks | 创建优化任务 |
| GET | /api/optimization-tasks | 查询优化任务列表 |
| GET | /api/optimization-tasks/{id} | 查询优化任务详情 |
| POST | /api/optimization-tasks/{id}/stop | 停止优化任务 |
| GET | /api/optimization-reports/{id} | 查询优化报告 |

#### 5.2.4 模型管理

| 方法 | 路径 | 说明 |
| :--- | :--- | :--- |
| POST | /api/models | 上传模型 |
| GET | /api/models | 检索模型列表 |
| GET | /api/models/{id} | 获取模型详情 |
| DELETE | /api/models/{id} | 删除模型（软删除） |
| GET | /api/models/{id}/versions | 获取版本列表 |
| GET | /api/models/{id}/versions/{ver} | 获取指定版本详情 |
| POST | /api/models/{id}/versions/diff | 版本对比 |
| POST | /api/models/{id}/rollback | 回滚至指定版本 |
| GET | /api/models/{id}/versions/{ver}/download | 下载模型文件 |

#### 5.2.5 用户与权限

| 方法 | 路径 | 说明 |
| :--- | :--- | :--- |
| POST | /api/auth/login | 登录 |
| POST | /api/auth/logout | 登出 |
| GET | /api/users | 用户列表 |
| POST | /api/users | 创建用户 |
| PUT | /api/users/{id} | 修改用户 |
| DELETE | /api/users/{id} | 删除用户 |
| GET | /api/projects/{id}/members | 项目成员列表 |
| POST | /api/projects/{id}/members | 添加项目成员 |
| DELETE | /api/projects/{id}/members/{user_id} | 移除项目成员 |

#### 5.2.6 日志

| 方法 | 路径 | 说明 |
| :--- | :--- | :--- |
| GET | /api/logs/operations | 操作日志查询 |
| GET | /api/logs/system | 系统日志查询 |
| GET | /api/logs/audit | 审计日志查询 |

---

## 6. 关键技术方案

### 6.1 JSBSim 集成方案

JSBSim 作为 Python 库集成到后端服务。根据操作类型采用混合执行策略：

| 操作类型 | 执行方式 | 原因 |
| :--- | :--- | :--- |
| 环境生成（一次性） | Celery 后台任务队列 | 耗时 30 秒~5 分钟，不适合请求内等待 |
| 在线交互（step/reset） | `run_in_executor` 线程池 | 用户等待训练反馈，需保持会话 |
| 批量生成 / 贝叶斯优化迭代 | Celery 后台任务队列 | 长耗时，支持断点续生 |

```python
import jsbsim

class JSBSimEngine:
    def __init__(self, config: EnvConfig):
        self.fdm = jsbsim.FGFDMExec(root_dir=config.jsbsim_root)
        self.fdm.load_model(config.aircraft_model)
        self.fdm.load_ic(config.initial_conditions, use_standalone_tag=False)

    def step(self, action: dict) -> dict:
        """推进一个仿真步长，返回状态"""
        self._apply_action(action)
        result = self.fdm.run()
        return self._extract_state()

    def reset(self):
        """重置仿真到初始条件"""
        self.fdm.reset_to_initial_conditions(0)
```

**机型扩展预留**：通过 `aircraft_model` 参数切换 JSBSim 机型配置文件，无需修改代码：

```python
AIRCRAFT_REGISTRY = {
    "fixed_wing": ["c172x", "f16", "737"],
    # 预留
    # "rotorcraft": ["uh60"],
    # "uav": ["rq1_predator"],
}
```

### 6.2 WebSocket 通信方案

**连接管理**：

```python
class ConnectionManager:
    """管理 WebSocket 连接，按 project_id + env_id 分组"""

    active_connections: dict[str, WebSocket]  # key: f"{project_id}:{env_id}"

    async def register(self, project_id: str, env_id: str, ws: WebSocket): ...
    async def unregister(self, project_id: str, env_id: str): ...
    async def broadcast_adjustment(self, env_id: str, instruction: dict): ...
```

**消息类型定义**：

| 方向 | type | 说明 |
| :--- | :--- | :--- |
| Client → Server | metric_report | 训练指标上报 |
| Client → Server | heartbeat | 心跳保活 |
| Server → Client | adjust_instruction | 环境调整指令 |
| Server → Client | metric_broadcast | 指标实时推送（前端） |
| Server → Client | notification | 消息通知 |

**断线重连**：客户端实现指数退避重连（1s → 2s → 4s → ... → 30s cap）；重连后补发缺失区间的指标。

### 6.3 贝叶斯优化集成方案

```python
from skopt import Optimizer
from skopt.space import Real

class EnvOptimizer(BaseOptimizer):
    def __init__(self, param_space: dict, weights: dict):
        self.space = [
            Real(bounds[0], bounds[1], name=name)
            for name, bounds in param_space.items()
        ]
        self.optimizer = Optimizer(dimensions=self.space)
        self.weights = weights

    def suggest(self, history: list[Observation]) -> dict:
        if not history:
            return self.optimizer.ask(n_points=1, strategy="cl_min")[0]
        return self.optimizer.ask(n_points=1)[0]

    def observe(self, params: dict, score: float) -> None:
        self.optimizer.tell(list(params.values()), score)

    def evaluate(self, env_id: str) -> float:
        """调用评估体系计算加权总分"""
        scores = self._compute_four_dimensions(env_id)
        return sum(self.weights[k] * scores[k] for k in scores)
```

### 6.4 三维预览方案

**数据格式** (`scene.json`)：

```json
{
  "terrain": {
    "grid_size": [100, 100],
    "resolution": 1.0,
    "elevation": [[0.0, 0.5, 1.2, ...], ...]
  },
  "obstacles": [
    {"type": "building", "position": [10, 20, 0], "size": [5, 5, 30]},
    {"type": "mountain", "position": [50, 50, 0], "radius": 20, "height": 100}
  ],
  "waypoints": [
    {"id": "wp1", "position": [0, 0, 100], "order": 1},
    {"id": "wp2", "position": [100, 0, 150], "order": 2}
  ],
  "wind": {
    "direction": [1.0, 0.5, 0.0],
    "speed": 10.0,
    "variability": 0.3
  },
  "runway": {
    "position": [0, 0, 0],
    "heading": 90,
    "length": 3000,
    "width": 60
  }
}
```

**前端渲染**：

- 地形：`PlaneGeometry` + 顶点位移实现地形高低
- 障碍物：`BoxGeometry`（建筑）/ `ConeGeometry`（山体）
- 航路：`Line` + 箭头（`ArrowHelper`）
- 风场：`Points` 粒子系统，沿风向运动
- 跑道：`PlaneGeometry` 贴跑道纹理

---

## 7. 部署方案

### 7.1 单机部署（V1.0 推荐）

```
┌─────────────────────────────────────────┐
│              服务器 (Linux)               │
│                                         │
│  ┌─────────┐   ┌─────────────────────┐ │
│  │  Nginx  │──→│  FastAPI (UVicorn)  │ │
│  │         │   │  (4 worker)        │ │
│  └─────────┘   └──────────┬──────────┘ │
│                           │             │
│  ┌──────────┐  ┌──────────┴──────────┐ │
│  │  MinIO   │  │  PostgreSQL + Redis │ │
│  └──────────┘  └─────────────────────┘ │
└─────────────────────────────────────────┘
```

- Nginx：静态资源托管 + 反向代理 + WebSocket 升级
- UVicorn：4 worker 进程，异步处理 HTTP + WebSocket
- PostgreSQL + Redis + MinIO：单机部署，满足低并发场景

### 7.2 环境要求

| 组件 | 最低版本 | 说明 |
| :--- | :--- | :--- |
| Python | 3.10+ | 后端运行时 |
| Node.js | 18+ | 前端构建 |
| PostgreSQL | 14+ | 业务数据存储 |
| Redis | 7+ | 缓存 + 消息队列 |
| MinIO | latest | 文件存储 |
| Nginx | 1.24+ | 反向代理 |

---

## 8. 开发分期建议

### Phase 1 — 核心基座（P0 需求）

- 用户认证与权限体系
- 项目管理
- 环境生成核心流程（JSBSim 集成 + 模板库 + 参数配置）
- 三维预览
- 模型管理基础功能（上传/查询/删除）

### Phase 2 — 动态能力（P0 + 部分 P1）

- WebSocket 指标上报与实时展示
- 动态调整策略引擎
- 手动调整
- 调整历史与版本回滚

### Phase 3 — 智能优化（P0 + P1）

- 四维评估体系
- 贝叶斯优化引擎
- 优化效果验证与报告
- 持续优化定时任务

### Phase 4 — 完善体验（剩余 P1）

- 批量生成
- 导入/导出
- 消息提醒
- 日志管理
- 模型状态监控与自动推荐
