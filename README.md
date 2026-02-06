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
   uvicorn backend.main:app --reload --port 8010
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

# 🚀项目开发展示

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
