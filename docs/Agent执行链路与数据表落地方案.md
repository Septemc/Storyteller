# Agent 执行链路与数据表落地方案

**文档版本**: v0.1  
**整理日期**: 2026-03-14  
**对应主文档**: [Agent系统设计方案.md](/f:/_WorkSpace/Projects/Storyteller/Storyteller/docs/Agent系统设计方案.md)

---

## 1. 文档目标

本文档用于把 Agent 设计落到执行链路和数据表层面，作为后续开发实施时的落地参考。

重点回答：

- 执行链路如何从当前代码演进
- 哪些表建议扩展
- 哪些表建议新增
- 如何支持 SessionState 完整运行态
- 如何支持多分支存档
- 如何支持分域检索与统一 embedding

---

## 2. 当前代码层面的关键现状

现有主要基础表包括：

- `session_state`
- `story_segments`
- `characters`
- `worldbook`
- `worldbook_embeddings`
- `scripts`
- `dungeons`
- `dungeon_nodes`
- `presets`
- `llm_configs`
- `global_settings`

当前主要问题：

- `session_state` 还不承载完整会话绑定
- 没有分支树结构
- embedding 只覆盖世界书
- 没有事件账本表
- 没有变量状态表
- 没有 skill 执行日志表

---

## 3. 建议的执行链路

### 3.1 低强度基线链路

建议第一阶段低强度链路如下：

1. 读取 `SessionState`
2. 读取最近剧情片段
3. 读取摘要记忆
4. 读取当前剧本
5. 读取当前主角与相关角色
6. 进行轻量变量分析
7. 注入预设与输出格式约束
8. 生成正文
9. 抽取关键事件
10. 更新 SessionState 与摘要

### 3.2 中强度链路

在低强度基础上增加：

1. 检索路由
2. 世界书检索
3. 事件账本检索
4. 统一重排
5. 生成前补检索判定
6. 生成后自校验

### 3.3 高强度链路

在中强度基础上增加：

1. 结构化变量快照读取
2. 剧本约束分析
3. 副本触发评估
4. 生成中补检索
5. 事实一致性检查
6. 变量状态更新

### 3.4 超高强度链路

在高强度基础上增加：

1. 多次再检索
2. 多次一致性校验
3. 关键节点自动检查点
4. 死亡 / 结局分支自动生成

---

## 4. SessionState 表扩展建议

建议保留当前 `session_state` 表名，但重定义其含义：

> 每行代表一个可运行的故事分支状态

### 4.1 建议新增字段

- `root_session_id`
- `parent_session_id`
- `fork_from_segment_id`
- `branch_name`
- `branch_type`
- `branch_status`
- `selected_character_id`
- `selected_preset_id`
- `selected_llm_config_id`
- `selected_llm_model`
- `selected_script_id`
- `selected_dungeon_instance_id`
- `reasoning_level`
- `active_worldbook_scope_json`
- `active_character_scope_json`
- `runtime_summary_json`
- `runtime_state_json`
- `last_event_seq`
- `is_death_ending`
- `death_reason`

### 4.2 保留字段

- `session_id`
- `current_script_id`
- `current_dungeon_id`
- `current_node_id`
- `global_state_json`
- `total_word_count`
- `updated_at`

说明：

- 老字段可保留兼容
- 新字段逐步迁移替代老字段语义

---

## 5. 建议新增的数据表

### 5.1 `event_ledger`

用途：

- 存储结构化关键事件

建议字段：

- `id`
- `event_id`
- `session_id`
- `root_session_id`
- `story_segment_id`
- `event_type`
- `importance`
- `confidence`
- `status`
- `source_excerpt`
- `actors_json`
- `targets_json`
- `payload_json`
- `caused_state_changes_json`
- `created_at`

### 5.2 `variable_states`

用途：

- 存储实体当前状态快照

建议字段：

- `id`
- `session_id`
- `entity_type`
- `entity_id`
- `scope_type`
- `state_json`
- `version`
- `updated_by_event_id`
- `updated_at`

### 5.3 `memory_summaries`

用途：

- 存储短期 / 中期 / 长期摘要

建议字段：

- `id`
- `session_id`
- `memory_level`
- `source_start_order`
- `source_end_order`
- `summary_text`
- `anchors_json`
- `updated_at`

### 5.4 `turn_plans`

用途：

- 存储每轮计划，便于调试 Agent

建议字段：

- `id`
- `turn_id`
- `session_id`
- `user_input`
- `reasoning_level`
- `plan_json`
- `status`
- `created_at`

### 5.5 `skill_execution_logs`

用途：

- 记录 skill 调用与耗时

建议字段：

- `id`
- `turn_id`
- `session_id`
- `skill_name`
- `input_summary`
- `output_summary`
- `latency_ms`
- `success`
- `created_at`

### 5.6 `knowledge_chunks`

用途：

- 统一承载分域知识切块

建议字段：

- `id`
- `chunk_id`
- `source_type`
- `source_id`
- `session_scope`
- `title`
- `content`
- `metadata_json`
- `updated_at`

### 5.7 `knowledge_embeddings`

用途：

- 统一承载知识切块向量

建议字段：

- `id`
- `chunk_id`
- `embedding_json`
- `embedding_model`
- `dimension`
- `content_hash`
- `updated_at`

### 5.8 `dungeon_instances`

用途：

- 将“副本模板”与“当前副本实例”分离

建议字段：

- `id`
- `instance_id`
- `session_id`
- `template_id`
- `status`
- `current_stage`
- `ending_type`
- `runtime_state_json`
- `created_at`
- `updated_at`

---

## 6. 世界书向量表如何演进

当前已有：

- `worldbook_embeddings`

建议演进方向：

### 阶段一

- 保留 `worldbook_embeddings`
- 新增其他知识域检索实现
- 不立即废弃旧表

### 阶段二

- 引入 `knowledge_chunks` 与 `knowledge_embeddings`
- 将世界书、角色、剧本、副本、事件、摘要统一切块

### 阶段三

- 检索层统一从 `knowledge_*` 表读取
- `worldbook_embeddings` 逐步转为兼容层或迁移完成后下线

这样能避免一次性改动过大。

---

## 7. 推荐的分域 chunk 策略

### 7.1 角色域

切块建议：

- 基础资料块
- 当前状态块
- 关系块
- 隐秘信息块

### 7.2 世界书域

切块建议：

- 地点块
- 势力块
- 规则块
- 历史块

### 7.3 剧本域

切块建议：

- 主线阶段块
- 节点目标块
- 禁止事项块

### 7.4 副本域

切块建议：

- 模板块
- 触发条件块
- 结局块
- 当前实例状态块

### 7.5 事件账本域

切块建议：

- 单事件块
- 高影响事件簇块

### 7.6 摘要域

切块建议：

- 短期摘要块
- 中期摘要块
- 里程碑摘要块

---

## 8. 路由与存储层演进建议

### 8.1 当前可保留的模块

- `orchestrator.py`
- `rag.py`
- `prompts.py`
- `storage.py`
- `routes_story.py`

### 8.2 建议新增的核心模块

- `backend/core/skills/`
- `backend/core/agent_runner.py`
- `backend/core/turn_planner.py`
- `backend/core/event_ledger.py`
- `backend/core/variable_state.py`
- `backend/core/knowledge_index.py`
- `backend/core/branching.py`

### 8.3 `orchestrator.py` 的未来角色

建议逐步把它从“直接生成器”调整为：

- 调度入口
- Agent 运行器外壳

而不是继续让它承担所有逻辑。

---

## 9. 数据迁移顺序建议

### Phase 1

- 扩展 `session_state`
- 新增 `memory_summaries`
- 新增 `turn_plans`

### Phase 2

- 新增 `event_ledger`
- 新增 `variable_states`

### Phase 3

- 新增 `knowledge_chunks`
- 新增 `knowledge_embeddings`

### Phase 4

- 新增 `dungeon_instances`
- 重构剧本 / 副本运行链路

---

## 10. 与前端协议的兼容建议

短期建议：

- 保持四标签 XML 输出不变
- 继续由前端按区域渲染

中期建议：

- 增加结构化元信息接口
- 不让前端只从正文字符串反推所有状态

例如可补充：

- `/api/session/runtime`
- `/api/session/branches`
- `/api/session/events`
- `/api/session/variables`

---

## 11. 第一阶段最低落地目标

如果只先做低强度可用版，建议至少落地：

- SessionState 会话绑定扩展
- 最近剧情与摘要联合上下文
- 基础计划层
- 角色 / 剧本 / 摘要三类检索
- 轻量变量思考
- 事件抽取初版
- SessionState 更新
- 多分支存档骨架

这套链路能保证后续不推翻重来。

---

## 12. 本文档结论

从工程实施角度看，最重要的不是一次把所有 Agent 能力全部做完，而是先把下面三件事建对：

- `session_state` 从轻量会话升级为完整分支运行态
- 检索底座从“只有世界书向量”升级为“分域知识 + 统一 embedding 架构”
- 新增事件账本和变量状态两层结构化中枢

只要这三件事立住，后续无论扩展中强度、高强度还是多题材适配，都能平滑推进。
