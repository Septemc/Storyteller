# Storyteller

Storyteller 是一个面向互动式小说与 AI 叙事生成的完整系统。  
它不是单纯的“续写器”，而是一个围绕 `Story -> SessionState -> Branch -> StorySegment` 运行的故事引擎，支持角色、世界书、剧本/副本、预设提示词、历史剧情、Agent 执行链路与结构化日志。

当前项目已经采用：

- `FastAPI + SQLAlchemy` 作为后端服务
- `PostgreSQL` 作为主数据库
- `Vue 3 + Vite + Pinia` 作为前端
- OpenAI 兼容接口作为大模型接入方式
- 会话级 Agent 运行链路、事件账本、角色动态同步、开发者日志与玩家可见 Agent Log

## 项目定位

本项目用于构建一个可长期运行、可多分支存档、可多故事并行的互动小说生成系统。  
系统的核心目标不是一次性生成文本，而是让 AI 在受约束的状态空间里持续推进故事：

- 玩家输入行动后，由 Agent 分析当前局面
- Agent 按需调用 skill 检索历史剧情、世界书、角色、剧本与副本信息
- 根据预设提示词、会话状态、推理强度和格式约束生成下一段剧情
- 正文生成完成后，继续执行角色同步、事件账本写回、变量快照记录与日志持久化

## 当前能力概览

### 1. 故事与会话

- 支持故事生成、剧情片段存储与历史回看
- 支持存档、分支、剧情片段级日志绑定
- 支持主角与当前会话上下文绑定
- 支持玩家可见 `Agent Log` 与开发者模式 `Agent Dev Log`

### 2. Agent 系统

- 已有低强度 Agent 第一阶段执行链路
- 支持 skill 注册与调用
- 支持开发者日志时间线记录
- 支持事件账本、变量快照、Agent 运行日志落库
- 支持角色同步 skill：根据正文识别新角色或已变化角色并更新数据库

### 3. 角色系统

- 角色模板按 `session_id` 管理
- 角色按 `session_id` 绑定到当前会话
- 角色数据采用 `data_json` 存储双态信息：
  - 开发者视角完整信息
  - 玩家视角可见信息
- 支持角色模板导入、激活、导出
- 支持角色导入、编辑、导出

### 4. 世界书与知识检索

- 支持世界书条目管理与导入
- 已有检索与 embedding 基础设施
- 支持为故事生成提供知识检索底座
- 启动时会自动清理孤立世界书向量记录

### 5. 剧本 / 副本 / 配置

- 支持副本/剧本数据管理
- 支持预设提示词管理
- 支持 LLM 配置管理
- 支持正则后处理规则配置
- 支持登录与基础鉴权能力

## 技术栈

### 后端

- `FastAPI`
- `SQLAlchemy 2`
- `Pydantic 2`
- `psycopg 3`
- `httpx`

### 前端

- `Vue 3`
- `Vite`
- `Pinia`
- `Vue Router`

### 数据与模型

- `PostgreSQL`
- OpenAI 兼容 LLM 接口
- embedding / similarity / retrieval 组件

## 核心数据概念

### Story

一个独立的故事工程。  
用于承载该故事下可用的角色集合、世界书范围、默认剧本、预设和配置。

### SessionState

某个故事下的一个运行态会话。  
它不是单纯的聊天上下文，而是一套完整状态快照，包含：

- 当前故事
- 当前会话
- 当前分支
- 当前主角
- 当前激活模板 / 预设 / LLM 配置
- 当前剧情上下文
- 当前角色集

### StorySegment

一次生成后的剧情片段。  
每个片段可以绑定：

- 玩家可见 Agent Log
- 开发者 Agent Dev Log
- 事件账本写回结果
- 变量快照写回结果

### Event Ledger

用于记录剧情中发生的结构化关键事件，例如：

- 角色死亡
- 身份变化
- 道具使用
- 状态突破
- 关系变化

### Character Dual State

角色信息同时保存两套视图：

- `full_profile`：开发者视角完整信息
- `player_profile`：玩家当前可知信息

## 目录结构

```text
Storyteller/
├─ backend/
│  ├─ api/                      # 兼容层路由入口
│  ├─ core/                     # 底层通用能力与历史兼容模块
│  ├─ db/
│  │  ├─ crud/                  # 数据访问层
│  │  └─ models/                # 数据模型
│  ├─ modules/
│  │  ├─ agent/                 # Agent runner、skill、日志、账本
│  │  ├─ characters/            # 角色模块
│  │  ├─ configuration/         # 预设、LLM、正则配置
│  │  ├─ dungeon/               # 剧本 / 副本
│  │  ├─ knowledge/             # 检索与 embedding
│  │  ├─ story/                 # 故事生成主链路
│  │  ├─ system/                # 认证与系统级能力
│  │  └─ worldbook/             # 世界书模块
│  ├─ prompts/                  # Prompt 资源
│  ├─ scripts/                  # 启动迁移 / 重建脚本
│  └─ main.py                   # FastAPI 入口
├─ frontend_vue/                # Vue 3 前端
├─ frontend/                    # 旧前端兼容目录
├─ docs/                        # 设计文档
├─ data/                        # 本地数据目录
├─ scripts/                     # 运行辅助脚本
├─ requirements.txt
├─ .env.example
└─ start_storyteller.bat
```

## 运行要求

- Python `3.11+` 或兼容版本
- Node.js `18+`
- PostgreSQL `14+` 推荐

## 环境变量

项目通过 `.env` 读取配置，前缀为 `NOVEL_`。

最关键的是数据库连接：

```env
NOVEL_DATABASE_URL=postgresql+psycopg://username:password@127.0.0.1:5433/database_name
```

`.env.example` 已给出示例。  
如果填写的是 `postgresql://...`，后端会在检测到本地安装了 `psycopg` 时自动转换为 `postgresql+psycopg://...`。

## 安装与启动

### 1. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 2. 安装前端依赖

```bash
cd frontend_vue
npm install
```

### 3. 构建前端

```bash
cd frontend_vue
npm run build
```

### 4. 启动后端

```bash
uvicorn backend.main:app --reload --port 8010
```

或使用项目自带脚本：

```powershell
.\scripts\restart_backend.ps1
```

Windows 也可以直接双击：

```text
start_storyteller.bat
```

### 5. 访问地址

- 主界面：`http://localhost:8010`

## 前端开发模式

如果需要单独开发前端：

```bash
cd frontend_vue
npm run dev
```

默认地址：

- 前端开发服务器：`http://localhost:5173`

后端会优先托管 `frontend_vue/dist`；如果未构建，则回退到旧 `frontend/` 目录。

## 启动时自动执行的内容

后端启动时会自动执行以下初始化逻辑：

- 创建数据库表
- 校正 `characters` 表结构
- 校正 `character_templates` 表结构
- 执行世界书相关迁移
- 清理孤立世界书 embedding 记录

因此在更新模型后，重启后端通常即可触发表结构修正。

## 主要页面

- `/story`：故事生成主界面
- `/characters`：角色管理页面
- `/worldbook`：世界书页面
- `/dungeon`：剧本 / 副本页面
- `/settings`：系统配置页面
- `/login`：登录页面

## 主要开发文档

项目设计文档位于 `docs/`，其中建议优先阅读：

- [Agent系统设计方案.md](/f:/_WorkSpace/Projects/Storyteller/Storyteller/docs/Agent系统设计方案.md)
- [Skill目录设计文档.md](/f:/_WorkSpace/Projects/Storyteller/Storyteller/docs/Skill目录设计文档.md)
- [变量思考与事件账本详细设计.md](/f:/_WorkSpace/Projects/Storyteller/Storyteller/docs/变量思考与事件账本详细设计.md)
- [Agent执行链路与数据表落地方案.md](/f:/_WorkSpace/Projects/Storyteller/Storyteller/docs/Agent执行链路与数据表落地方案.md)

## 测试与校验

### 后端语法校验

```bash
python -m compileall backend
```

### 前端构建校验

```bash
cd frontend_vue
npm run build
```

### 单元测试

```bash
pytest -q
```

## 开发说明

### 1. 当前状态

项目已经完成业务级目录拆分，后端主逻辑以 `modules/` 为中心组织。  
当前 Agent 已有可运行主链路，但仍处于持续扩展阶段，重点在于继续完善：

- 更高强度推理链路
- 中途二次检索
- 更强的变量思考能力
- 剧本与副本的动态推进
- 更稳健的结构化抽取

### 2. 角色模板使用方式

角色模板必须来自数据库，不使用前端硬编码模板。  
如果当前会话没有模板，角色同步 skill 会因 `no_template` 跳过，角色页也不会伪造默认模板。  
正确流程是：

1. 导入角色模板
2. 在当前 `session_id` 下激活模板
3. 再进行角色创建、导入或剧情生成

### 3. Agent 日志

系统区分两种日志：

- `Agent Log`：玩家可见，不剧透，显示过程信息
- `Agent Dev Log`：开发者可见，包含 skill 调用、检索结果、上下文构造和写回结果

两类日志都会按 `StorySegment` 持久化到数据库。

## License

本仓库当前未单独声明开源许可证。  
如需对外分发或开源，请先补充许可证文件与使用条款。
