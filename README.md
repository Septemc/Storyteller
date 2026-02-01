# 📖 互动式小说生成系统——“说书人”项目 (Storyteller)

**本项目是一个基于 **FastAPI** + **SQLite** + **原生前端** 构建的互动小说/RPG 游戏引擎原型。其核心目标是构建一个能够承载大语言模型 (LLM) 的基础架构，并提供高度可配置的**动态角色模板系统。

## 🏆 核心亮点

* **低代码表单构建器**：内置强大的角色模板设计器，无需修改代码即可定义角色属性结构。
* **动态渲染引擎**：前端根据后端返回的 JSON 配置，动态生成编辑器输入框和角色预览界面。
* **全方位数据对齐**：通过 `mapping_config.json` 实现导入数据的模糊路径匹配，最大化保留导入信息。
* **富组件支持**：支持文本、数值、属性面板（六维图）、关系图谱（ECharts）及图像上传等多种展示类型。

---

## 🛠️ 技术架构

* **后端 (Backend)**：Python 3.8+，FastAPI，SQLAlchemy (ORM)，Pydantic。
* **数据库 (Database)**：SQLite（自动创建表结构）。
* **前端 (Frontend)**：原生 HTML5/JavaScript，CSS (Dark Theme)，ECharts (图表展示)。

---

## 📂 项目文件结构

### 1. 后端核心 (`/backend`)

* **`<span class="citation-554">main.py</span>`**：应用入口，配置 CORS 跨域、静态文件挂载并注册路由。
* **`<span class="citation-553">models.py</span>`**：SQLAlchemy 数据库模型，包含角色 (`<span class="citation-553">Character</span>`)、模板 (`<span class="citation-553">CharacterTemplate</span>`)、世界书 (`<span class="citation-553">WorldbookEntry</span>`) 等核心表。
* **`routes_characters.py`**：处理角色 CRUD、批量导入/导出以及路径匹配逻辑。
* **`routes_templates.py`**：管理角色模板的定义与持久化存储。
* **`mapping_config.json`**：定义数据库字段与导入 JSON 路径之间的映射契约。

### 2. 前端界面 (`/frontend`)

* `<span class="citation-552">characters.html</span>`：角色管理主页面，包含列表、预览、动态编辑器及模板设计器模态框。
* **`assets/js/characters.js`**：负责 MVVM 模式的 UI 重绘、模板路径解析及 ECharts 初始化。
* `<span class="citation-551">assets/css/style.css</span>`：全局暗色科幻风格样式定义。

---

## 🎨 角色模板设计器说明

在“角色模板设计器”中，您可以为每个字段配置以下 **6 个关键属性**：

1. **ID**：字段在模板内的唯一逻辑标识。
2. **Label**：用户界面上显示的字段名称。
3. **Type**：渲染组件类型（如：文本、长文本、数值、属性面板、对象列表、关系图谱、图像）。
4. **Tab**：该字段所属的标签页容器。
5. **Path**：**核心属性**。定义数据在数据库 `data_json` 中的具体存储/读取路径（如 `basic.name`）。
6. **Desc**：字段的功能描述或输入提示。

---

## 📥 安装与运行

1. **安装依赖**：
   **Bash**

   ```
   pip install -r requirements.txt
   ```
2. **启动服务**：
   **Bash**

   ```
   python -m backend.main
   ```

   或

   ```
   uvicorn backend.main:app --reload
   ```
3. **访问地址**：

   * 主界面：`http://localhost:8000`
   * 角色管理：`http://localhost:8000/characters.html`

---

## 💾 数据导出与备份

* **模板管理**：支持将设计的模板导出为标准 JSON 文件，并支持一键导入。
* **角色管理**：
  * **单个导出**：导出当前选中的角色完整 JSON 数据。
  * **批量导出**：一键备份所有角色数据为 JSON 数组。

---

---

---



# 🚀当前项目开发进度（截止2026-02-01）

### 1. 项目核心概览

本项目是一个基于 **FastAPI (后端)** + **SQLite (数据库)** + **原生 HTML/JS (前端)** 的互动小说/RPG 游戏引擎原型。

* **核心目标**：构建一个承载大语言模型 (LLM) 的基础架构，实现高度可配置的动态角色模板系统。
* **当前状态**：角色管理与模板设计功能已基本完成，实现了从“硬编码”到“数据结构驱动”的转型。
* **技术特色**：采用低代码表单构建器思想，支持通过 JSON 契约动态渲染 UI 组件（如六维图、关系网络、图像上传）。

---

### 2. 项目目录结构

根据项目实际文件布局，整体结构如下：

**Plaintext**

```
Storyteller/
├── backend/                # 后端核心代码 [cite: 15]
│   ├── api/                # API 路由模块 [cite: 30]
│   ├── core/               # 业务逻辑骨架（待接入 LLM） [cite: 37]
│   ├── db/                 # 数据库层 [cite: 20]
│   │   └── crud/           # 数据库增删改查具体实现
│   ├── prompts/            # 提示词管理 [cite: 39]
│   ├── static/             # 静态资源存放
│   ├── config.py           # 全局配置 [cite: 19]
│   ├── main.py             # 后端程序入口 
│   └── mapping_config.json # 动态路径匹配逻辑配置
├── data/                   # 数据持久化目录 [cite: 61]
│   ├── worldbook_import/   # 世界书导入文件备份 [cite: 63]
│   └── db.sqlite           # 自动生成的数据库文件 [cite: 62]
├── frontend/               # 前端界面模块 [cite: 40]
│   ├── assets/             # 前端资源 [cite: 50]
│   │   ├── css/            # 样式表 [cite: 50]
│   │   └── js/             # 逻辑脚本 [cite: 52]
│   ├── characters.html     # 角色管理主页面 [cite: 44]
│   ├── dungeon.html        # 副本编辑器 [cite: 48]
│   ├── index.html          # 主游玩界面 [cite: 43]
│   ├── settings.html       # 系统设置页 [cite: 49]
│   └── worldbook.html      # 世界书管理页 [cite: 47]
├── .env                    # 环境变量 [cite: 13]
├── README.md               # 项目说明文档
└── requirements.txt        # Python 依赖清单 [cite: 14]
```

---

### 3. 文件职责说明

#### 3.1 后端核心 (backend/)

* `<span class="citation-635">main.py</span>`：启动 FastAPI 应用，配置 CORS 跨域，挂载静态文件，并在启动时自动初始化数据库表结构。
* `mapping_config.json`：**关键配置文件**。定义了数据库字段与导入 JSON 路径之间的映射契约，用于在不同格式的角色文件导入时进行最大化数据对齐。
* `<span class="citation-634">models.py</span>`：定义 SQLAlchemy ORM 模型，包含角色 (**`<span class="citation-634">Character</span>`)、模板 (`<span class="citation-634">CharacterTemplate</span>`)、世界书、副本节点等表。

**API 路由 (`backend/api/`):**

* `<span class="citation-633">routes_characters.py</span>`：****核心逻辑****。处理角色的 CRUD、批量/单个导入导出，以及支持深层嵌套路径的数据匹配读取。
* `<span class="citation-632">routes_templates.py</span>`：模板管理接口。支持自定义 Tab 标签页和 Field 字段结构的保存与读取。
* `<span class="citation-631">routes_story.py</span>`：处理剧情生成逻辑（目前为 Mock 占位）。
* `<span class="citation-630">routes_worldbook.py</span>` / `<span class="citation-630">routes_dungeon.py</span>`：分别处理世界书条目和副本关卡数据的管理。

#### 3.2 前端界面 (frontend/)

* `<span class="citation-629">characters.html</span>`：角色中心页面，包含角色列表、详情预览、动态编辑器以及“角色模板设计器”全屏模态框。
* `<span class="citation-628">assets/js/characters.js</span>`：****重构后的核心脚本****。实现了一套低代码渲染引擎，根据模板 JSON 自动生成输入控件，并集成了 ECharts 用于绘制关系网。
* `<span class="citation-627">assets/css/style.css</span>`：全局暗色科幻风格样式，定义了响应式布局、卡片展示及预览视图的高级样式。

---

### 4. 角色模板系统技术细节

目前角色系统已支持以下进阶特性：

1. **6 属性字段配置**：每个字段均包含 `id`, `label`, `type`, `tab`, `path`, `desc` 六项属性。
2. **富组件渲染**：支持文本、长文本、数值、属性面板（六维雷达图）、关系图谱、对象列表以及图像显示。
3. **动态路径匹配 (Pathing)**：前端通过 `getValueByPath` 实现对 `data_json` 中任意层级（如 `basic.name`）的读取与回写。
4. **安全交互逻辑**：删除角色/模板前均设有警告确认，导入数据时若存在模板字段缺失会触发警告提醒。

**下一步开发建议**：

* 接入真实的 LLM API 以替换 `<span class="citation-625">routes_story.py</span>` 中的模拟数据。
* 完善 `core/rag.py` 实现基于世界书背景的检索增强生成。


---

---

---




# 📝 互动式小说生成系统 - 深度项目任务清单

## 🟢 第一阶段：基础设施与核心架构 (Infrastructure & Core)

> **目标**：确保系统底座稳固，数据库设计合理，配置管理灵活。

### 1.1 环境与配置管理

* [ ]  **依赖标准化**：
  * [ ]  **锁定 **`<span class="citation-866">requirements.txt</span>` 中核心库的版本号（FastAPI, SQLAlchemy, Pydantic），防止未来更新导致兼容性破坏 ^^。
  * [ ]  建立虚拟环境自动激活脚本 (Windows/Linux)。
* [ ]  **全局配置系统 (`<span class="citation-865">config.py</span>`)** ^^：
  * [ ]  实现 `.env` 文件加载器，区分 `DEV` (开发)、`PROD` (生产) 环境。
  * [ ]  定义 LLM API 密钥管理的加密存储策略。
  * [ ]  配置静态资源缓存策略 (Cache-Control)。

### 1.2 数据库层 (`db/` & `models.py`)

* [ ]  **ORM 模型维护** ^^：
  * [ ]  审查 `Character` 表，确保存储大文本字段（如 `data_json`）的 SQLite 性能优化。
  * [ ]  为 `StorySegment` 添加全文索引 (FTS5)，以便未来实现剧情搜索功能。
  * [ ]  设计 `SessionState` 的自动备份机制（Snapshot），防止玩家存档损坏。
* [ ]  **数据库迁移 (Migration)**：
  * [ ]  **引入 **`<span class="citation-863">Alembic</span>` 工具。目前项目依赖 `<span class="citation-863">Base.metadata.create_all</span>` ^^，后续需支持数据库字段的版本回滚与无损变更。

### 1.3 基础路由与中间件

* [ ]  **CORS 策略收紧****：将 **`<span class="citation-862">main.py</span>` 中的 `<span class="citation-862">allow_origins=["*"]</span>` 修改为可配置的白名单模式，提高安全性 ^^。
* [ ]  **全局异常处理**：
  * [ ]  建立统一的 API 错误响应格式 (JSON Structure)。
  * [ ]  捕获 SQLite 锁死错误并实现自动重试机制。

---

## 🔵 第二阶段：角色与模板系统 (已完成主体的优化与维护)

> **目标**：巩固现有的低代码表单特性，提升数据交互的鲁棒性。

### 2.1 角色模板设计器 (`routes_templates.py` & Frontend)

* [ ]  **字段属性深度支持** ^^：
  * [ ]  **ID 唯一性校验**：前端 JS 实现实时校验，防止用户输入重复的 Field ID。
  * [ ]  **Path 智能提示**：在输入 `path` 时，提供基于 `mapping_config.json` 的自动补全建议。
  * [ ]  **Type 扩展**：为 `select` (下拉选框) 类型增加 `options` 配置界面（目前 JSON 结构支持但 UI 未实现）。
* [ ]  **模板交互优化**：
  * [ ]  实现 Tabs 和 Fields 的**拖拽排序**功能 (利用 SortableJS)。
  * [ ]  增加“模板另存为”功能，方便基于现有模板微调。

### 2.2 角色数据管理 (`routes_characters.py`)

* [ ]  **Upsert 逻辑增强**：
  * [ ]  **在 **`<span class="citation-860">import_characters</span>` 中，增加“冲突解决策略”选项（覆盖、跳过、重命名） ^^。
* [ ]  **全量数据快照**：
  * [ ]  开发一个后台任务，定期清理 `data_json` 中不再被任何 Template 引用的“僵尸数据”。
* [ ]  **多媒体资源管理**：
  * [ ]  实现 `/api/assets/upload` 接口，支持用户上传角色头像。
  * [ ]  在 `Character` 模型中增加 `avatar_path` 字段，或将其整合进 `data_json`。

### 2.3 智能导入引擎 (`mapping_config.json`)

* [ ]  **模糊匹配算法升级**：
  * [ ]  实现正则匹配支持（如 `"attr_.*"` 可自动映射到属性组）。
  * [ ]  增加权重机制：当多个路径都存在时，优先选择权重高的路径（如 `basic.name` > `info.name`）。
* [ ]  **导入预检 UI**：
  * [ ]  前端上传 JSON 后，先展示“差异对比报告”，确认无误后再写入数据库。

---

## 🔴 第三阶段：剧情编排与 LLM 接入 (核心攻坚)

> **目标**：替换 Mock 数据，让系统真正“活”起来。

### 3.1 LLM 客户端层 (`core/llm_client.py`)

* [ ]  **多模型适配器**：
  * [ ]  定义抽象基类 `LLMProvider`。
  * [ ]  实现 `OpenAIProvider` (GPT-4o/mini)。
  * [ ]  实现 `AnthropicProvider` (Claude 3.5 Sonnet)。
  * [ ]  实现 `LocalProvider` (Ollama/vLLM 接口适配)。
* [ ]  **稳健性设计**：
  * [ ]  实现 API 请求的指数退避重试 (Exponential Backoff)。
  * [ ]  增加 Token 计数与消耗估算功能。

### 3.2 提示词工程系统 (`core/prompts.py`)

* [ ]  **动态提示词模板**：
  * [ ]  使用 `Jinja2` 渲染 Prompt。
  * [ ]  模板变量注入：`{{ character_bio }}`, `{{ current_scene }}`, `{{ world_rules }}`。
* [ ]  **上下文组装器 (Context Builder)**：
  * [ ]  **滑动窗口机制**：自动截取最近 N 轮对话，防止 Token 溢出。
  * [ ]  **关键信息摘要**：集成 `summary.py`，对久远的历史对话进行语义总结并注入 System Prompt。

### 3.3 剧情中控引擎 (`core/orchestrator.py`)

* [ ]  **Turn-Loop (回合循环) 实现**：
  * [ ]  **Input Processing**：接收用户输入 -> 解析意图 (行动/对话/查询)。
  * [ ]  **State Check**：检查当前 HP、位置、物品状态。
  * [ ]  **Generation**：调用 LLM 生成剧情。
  * [ ]  **Post-Processing**：解析 LLM 返回的 JSON/XML，提取结构化数据（如：扣除 5 金币）。
* [ ]  **结构化输出解析**：
  * [ ]  强制 LLM 输出特定格式（如 `<action>attack</action><result>damage:10</result>`），并编写正则解析器。

---

## 🟣 第四阶段：世界书与 RAG 系统 (知识增强)

> **目标**：让 AI 记住庞大的世界观设定。

### 4.1 向量数据库集成 (`core/rag.py`)

* [ ]  **向量库选型**：
  * [ ]  集成 `ChromaDB` 或 `FAISS` (本地轻量级)。
* [ ]  **嵌入服务 (Embedding)**：
  * [ ]  接入 `text-embedding-3-small` 或本地 `bge-m3` 模型。
* [ ]  **数据同步管道**：
  * [ ]  **当 **`<span class="citation-859">WorldbookEntry</span>` ^^ 更新时，自动触发向量索引的更新。

### 4.2 检索逻辑实现

* [ ]  **关键词提取**：
  * [ ]  在生成剧情前，先用 LLM 提取用户输入中的关键词（如“黑鸦城”、“青锋剑”）。
* [ ]  **混合检索**：
  * [ ]  结合 关键词匹配 (SQL LIKE) 和 语义检索 (Vector Similarity)。
* [ ]  **上下文注入**：
  * [ ]  将检索到的 Top-3 条目拼接到 System Prompt 的 `[Relevant World Info]` 部分。

---

## 🟡 第五阶段：副本与游戏性机制 (Game Mechanics)

> **目标**：引入数值玩法和分支逻辑。

### 5.1 变量与状态系统 (`core/variables.py`)

* [ ]  **变量追踪器**：
  * [ ]  实现 `GlobalVariables` (全局开关) 和 `CharacterVariables` (好感度、San值)。
* [ ]  **表达式求值引擎**：
  * [ ]  实现简单的逻辑判断，例如：`if character.relation.Su_Li > 50 then unlock_hidden_option`。

### 5.2 副本节点逻辑 (`routes_dungeon.py`)

* [ ]  **节点流转控制**：
  * [ ]  实现 `enter_node` 和 `exit_node` 逻辑。
  * [ ]  **条件判定****：进入节点前检查 **`<span class="citation-858">entry_conditions_json</span>` ^^。
* [ ]  **自动化结算**：
  * [ ]  定义节点奖励（Item/Exp），在完成节点后自动写入 `SessionState`。

---

## 🟠 第六阶段：前端交互与体验 (UX Polish)

> **目标**：打造沉浸式的游玩体验。

### 6.1 主游玩界面 (`index.html` & `main.js`)

* [ ]  **流式打字机效果**：
  * [ ]  对接后端 Server-Sent Events (SSE) 接口，实现文字逐个蹦出的效果。
* [ ]  **多模态展示**：
  * [ ]  当剧情提到某个角色时，侧边栏自动高亮该角色卡片。
  * [ ]  背景音乐/音效触发器 (基于 LLM 返回的 Tag)。

### 6.2 可视化增强 (`assets/css/style.css`)

* [ ]  **移动端适配**：
  * [ ]  优化 Grid 布局，在手机端将侧边栏折叠为抽屉菜单。
* [ ]  **主题切换**：
  * [ ]  增加“羊皮纸风格” (Fantasy) 和 “赛博霓虹” (Sci-Fi) 主题切换。

### 6.3 关系图谱交互 (`characters.js` + ECharts)

* [ ]  **交互式钻取**：
  * [ ]  **点击关系图中的节点，直接弹窗显示该角色的简略信息 **^^。
* [ ]  **动态力导向图**：
  * [ ]  根据“亲密度”数值动态调整连线的粗细和颜色。

---

## ⚪ 第七阶段：测试与运维 (Ops)

> **目标**：保证系统的稳定性与可分发性。

### 7.1 自动化测试

* [ ]  **单元测试 (Pytest)**：
  * [ ]  覆盖所有 Pydantic 模型的验证逻辑。
  * [ ]  测试 `mapping_config.json` 的解析器对各种边缘 Case 的处理能力。
* [ ]  **集成测试**：
  * [ ]  模拟完整的 User Journey：创建角色 -> 开启会话 -> 发送对话 -> 验证数据库变更。

### 7.2 打包与分发

* [ ]  **Docker 化**：
  * [ ]  编写 `Dockerfile`，将 Python 环境与前端资源打包。
  * [ ]  编写 `docker-compose.yml`，一键启动服务。
* [ ]  **一键启动脚本**：
  * [ ]  提供 `run.bat` 和 `run.sh`，自动检测 Python 环境并安装依赖。

---

### 📅 优先级建议

1. **P0 (最高优先级)**：完成 **3.1 LLM 客户端** 与 **3.3 剧情中控**。没有这个，项目只是一个静态数据库。
2. **P1**：完成 **4.1 向量数据库**。没有记忆的 AI 无法进行长篇跑团。
3. **P2**：完善 **5.1 变量系统**。增加游戏的策略深度。
4. **P3**：前端 **6.1 流式输出** 与 **6.2 移动端适配**。提升感官体验。
