# Skill 目录设计文档

**文档版本**: v0.1  
**整理日期**: 2026-03-14  
**对应主文档**: [Agent系统设计方案.md](/f:/_WorkSpace/Projects/Storyteller/Storyteller/docs/Agent系统设计方案.md)

---

## 1. 文档目标

本文档用于定义 Storyteller Agent 系统中的 Skill 目录、职责边界、触发时机与执行优先级。

设计原则：

- Skill 必须可调度
- Skill 必须有明确输入输出
- Skill 必须面向多题材通用
- Skill 必须支持从低强度逐步扩展到高强度

---

## 2. Skill 总体分类

建议分为六类：

- 绑定与上下文类
- 检索类
- 分析类
- 规划类
- 生成与校验类
- 回写类

---

## 3. Skill 基础协议

每个 Skill 建议统一具备以下元信息：

- `skill_name`
- `category`
- `purpose`
- `input_schema`
- `output_schema`
- `cost_level`
- `supports_reasoning_levels`
- `can_mutate_state`
- `fallback_strategy`

### 3.1 通用输入建议

- `session_id`
- `turn_id`
- `user_input`
- `reasoning_level`
- `session_bindings`
- `runtime_flags`

### 3.2 通用输出建议

- `success`
- `summary`
- `payload`
- `confidence`
- `used_sources`
- `cost_metrics`

---

## 4. 绑定与上下文类 Skill

### 4.1 `session_binding_skill`

职责：

- 读取当前 SessionState 的完整绑定
- 确认当前剧本、预设、LLM、主角、分支信息

低强度必需：是

### 4.2 `session_context_bootstrap_skill`

职责：

- 生成本轮最小上下文启动包
- 不做全量检索，只提供最小可运行信息

输出建议：

- 当前分支摘要
- 当前主角摘要
- 当前剧本摘要
- 当前副本摘要
- 当前推理强度配置

---

## 5. 检索类 Skill

### 5.1 `recent_story_retrieval_skill`

职责：

- 提取最近剧情片段
- 动态控制截取长度

低强度必需：是

### 5.2 `summary_memory_retrieval_skill`

职责：

- 读取短期 / 中期摘要
- 在低成本下提供压缩上下文

低强度必需：是

### 5.3 `worldbook_retrieval_skill`

职责：

- 检索世界书中的规则、地点、设定、势力、背景知识

适用：

- 设定解释
- 场景描写
- 世界规则约束

### 5.4 `character_retrieval_skill`

职责：

- 检索主角、当前相关角色、在场角色、被提及角色

输出建议：

- 基础资料
- 当前状态摘要
- 关系摘要
- 最近关键事件关联

### 5.5 `script_retrieval_skill`

职责：

- 检索全局剧本当前阶段与主线节点要求

低强度必需：是

### 5.6 `dungeon_retrieval_skill`

职责：

- 检索当前活跃副本实例
- 或检索潜在可触发副本模板

### 5.7 `event_ledger_retrieval_skill`

职责：

- 检索高影响历史事件
- 优先供变量分析与校验使用

### 5.8 `variable_snapshot_retrieval_skill`

职责：

- 读取当前关键实体的结构化状态

### 5.9 `branch_history_retrieval_skill`

职责：

- 在回档、分叉、死亡分支场景下读取分支祖先信息

---

## 6. 分析类 Skill

### 6.1 `intent_analysis_skill`

职责：

- 识别本轮输入类型
- 识别是对话、战斗、交易、探索、主线推进、支线触发还是结局风险

低强度必需：是

### 6.2 `retrieval_routing_skill`

职责：

- 判断优先检索哪些知识域
- 决定首轮检索顺序

### 6.3 `context_rerank_skill`

职责：

- 对多源召回结果统一重排

适用强度：

- 中 / 高 / 超高

### 6.4 `character_relevance_skill`

职责：

- 识别本轮真正重要的角色
- 缩小角色上下文范围

### 6.5 `variable_thinking_skill`

职责：

- 分析涉及哪些变量实体
- 判断哪些状态可能变化
- 识别哪些变化被禁止

低强度必需：建议轻量启用

### 6.6 `script_constraint_analysis_skill`

职责：

- 分析当前剧本节点允许什么、不允许什么

低强度必需：是，但可轻量

### 6.7 `dungeon_trigger_analysis_skill`

职责：

- 判断当前是否应触发副本
- 评估副本类型、时长、节奏、潜在结局

### 6.8 `genre_adaptation_skill`

职责：

- 根据当前题材标签修正分析倾向
- 确保系统不按单一题材思考

适用：

- 修仙 / 历史 / 都市 / 西幻等多题材切换

---

## 7. 规划类 Skill

### 7.1 `turn_plan_skill`

职责：

- 形成本轮基础执行计划
- 决定首批 skill

低强度必需：是

### 7.2 `story_planning_skill`

职责：

- 形成本轮叙事规划
- 输出主要事件、禁止事项、可选推进方向

### 7.3 `dynamic_retrieval_decision_skill`

职责：

- 在生成前或生成中判断是否要追加检索

适用强度：

- 中 / 高 / 超高

### 7.4 `action_option_planning_skill`

职责：

- 规划本轮结束后给玩家的行动选项

---

## 8. 生成与校验类 Skill

### 8.1 `preset_injection_skill`

职责：

- 读取并注入 Session 当前预设
- 按层次注入文风、思考方式、角色表现风格

低强度必需：是

### 8.2 `story_generation_skill`

职责：

- 生成正文

低强度必需：是

### 8.3 `output_format_constraint_skill`

职责：

- 强制输出符合前端协议的 XML 结构

低强度必需：是

### 8.4 `generation_self_check_skill`

职责：

- 自检输出是否与规划冲突

适用强度：

- 中 / 高 / 超高

### 8.5 `fact_consistency_check_skill`

职责：

- 检查生成内容是否与角色状态、事件账本、剧本约束冲突

适用强度：

- 高 / 超高

### 8.6 `repair_generation_skill`

职责：

- 对不合格结果做局部修正，而不是整轮重写

---

## 9. 回写类 Skill

### 9.1 `event_extraction_skill`

职责：

- 从本轮结果中提取结构化事件

低强度必需：建议启用轻量版

### 9.2 `event_confirmation_skill`

职责：

- 过滤噪声事件
- 判断哪些事件能写入事件账本

### 9.3 `variable_state_update_skill`

职责：

- 根据事件更新结构化变量状态

### 9.4 `session_state_update_skill`

职责：

- 更新当前 SessionState 的运行态

### 9.5 `script_progress_update_skill`

职责：

- 推进剧本节点或记录偏离状态

### 9.6 `dungeon_state_update_skill`

职责：

- 更新副本实例进度、结局、是否关闭

### 9.7 `memory_summary_update_skill`

职责：

- 维护短中期摘要

### 9.8 `branch_checkpoint_skill`

职责：

- 在关键节点、结局、死亡事件后自动创建检查点或分支

---

## 10. 推理强度对应的 Skill 组合

### 10.1 低强度

建议默认启用：

- `session_binding_skill`
- `session_context_bootstrap_skill`
- `intent_analysis_skill`
- `turn_plan_skill`
- `recent_story_retrieval_skill`
- `summary_memory_retrieval_skill`
- `character_retrieval_skill`
- `script_retrieval_skill`
- `preset_injection_skill`
- `output_format_constraint_skill`
- `variable_thinking_skill` 轻量版
- `story_generation_skill`
- `event_extraction_skill` 轻量版
- `session_state_update_skill`

### 10.2 中强度

在低强度基础上增加：

- `worldbook_retrieval_skill`
- `event_ledger_retrieval_skill`
- `retrieval_routing_skill`
- `context_rerank_skill`
- `story_planning_skill`
- `dynamic_retrieval_decision_skill`
- `generation_self_check_skill`
- `memory_summary_update_skill`

### 10.3 高强度

在中强度基础上增加：

- `variable_snapshot_retrieval_skill`
- `script_constraint_analysis_skill`
- `dungeon_trigger_analysis_skill`
- `fact_consistency_check_skill`
- `event_confirmation_skill`
- `variable_state_update_skill`
- `script_progress_update_skill`
- `dungeon_state_update_skill`

### 10.4 超高强度

在高强度基础上增加：

- 多次 `dynamic_retrieval_decision_skill`
- 多次 `fact_consistency_check_skill`
- `branch_checkpoint_skill`
- 关键节点二次修正链路

---

## 11. 首批建议实现的 Skill

从开发顺序看，建议第一批先做以下 Skill：

1. `session_binding_skill`
2. `recent_story_retrieval_skill`
3. `summary_memory_retrieval_skill`
4. `character_retrieval_skill`
5. `script_retrieval_skill`
6. `intent_analysis_skill`
7. `turn_plan_skill`
8. `variable_thinking_skill` 初版
9. `preset_injection_skill`
10. `output_format_constraint_skill`
11. `story_generation_skill`
12. `event_extraction_skill` 初版
13. `session_state_update_skill`

这套组合足以支撑低强度可持续运行。

---

## 12. 扩展原则

后续新增 Skill 时建议遵循：

- 不要做题材专用硬编码 Skill
- 优先做通用抽象
- Skill 输出尽量结构化
- Skill 尽量可缓存
- Skill 尽量允许失败降级

---

## 13. 本文档结论

Storyteller 的 Skill 体系不应只是“把功能拆碎”，而应形成一套稳定的运行目录：

- 低强度依赖最小必要 Skill 保持持续生成
- 中高强度逐步增加检索深度、规划深度、回写深度
- 整套体系围绕 SessionState、事件账本、变量状态和剧本 / 副本双轨机制展开
