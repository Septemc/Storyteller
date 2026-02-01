# 📖 互动式小说生成系统 (Storyteller)

**本项目是一个基于 **FastAPI** + **SQLite** + **原生前端** 构建的互动小说/RPG 游戏引擎原型。其核心目标是构建一个能够承载大语言模型 (LLM) 的基础架构，并提供高度可配置的**动态角色模板系统。

## 🚀 核心亮点

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
