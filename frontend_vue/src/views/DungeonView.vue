<template>
  <main class="two-column-layout">
    <section class="left-panel">
      <div class="panel-header">
        <div class="panel-title">剧本大纲</div>
      </div>

      <div class="settings-section" style="padding-bottom: 12px; border-bottom: 1px solid var(--border-soft); margin-bottom: 10px;">
        <div style="display: flex; gap: 8px; margin-bottom: 6px; align-items: center;">
          <select id="dungeon-selector" v-model="selectedScriptId" class="form-select" style="flex: 1;" @change="selectScript(selectedScriptId)">
            <option v-for="script in scripts" :key="script.script_id" :value="script.script_id">{{ script.name }}</option>
          </select>
          <button id="btn-apply-script" class="btn-primary btn-small" @click="applyScript">应用</button>
          <button id="btn-new-dungeon" class="btn-secondary btn-small" @click="createScript">新建</button>
          <label id="btn-import-script" class="btn-secondary btn-small">
            导入
            <input type="file" accept=".json" style="display: none;" @change="(event) => onImport(event, 'script')">
          </label>
          <button id="btn-export-script" class="btn-secondary btn-small" @click="exportCurrent">导出</button>
          <button id="btn-delete-dungeon" class="btn-secondary btn-small" style="color: var(--danger);" @click="deleteCurrent">删除</button>
        </div>
        <div id="applied-dungeon-info" class="small-text muted" style="margin-top: 6px; color: var(--accent);">
          {{ statusText }}
        </div>
      </div>

      <div class="settings-section">
        <div class="search-wrapper" style="position: relative;">
          <input
            id="search-keyword"
            v-model="searchKeyword"
            class="form-input"
            type="search"
            placeholder="搜索节点..."
            style="padding-right: 32px;"
            autocomplete="new-password"
            autocapitalize="off"
            autocorrect="off"
            spellcheck="false"
            inputmode="search"
            enterkeyhint="search"
            name="dungeon_lookup_query"
            data-lpignore="true"
            data-form-type="other"
            data-search-guard="true"
          >
          <button id="btn-search" class="icon-button" style="position: absolute; right: 6px; top: 50%; transform: translateY(-50%);">搜</button>
        </div>
        <div class="toolbar-actions" style="display: flex; gap: 4px; margin-top: 10px; flex-wrap: wrap;">
          <button id="btn-create-dungeon" class="btn-secondary btn-small" style="flex: 1;" @click="createDungeon">新建副本</button>
          <button id="btn-create-node" class="btn-secondary btn-small" style="flex: 1;" @click="createNode">新建节点</button>
          <label id="btn-import-dungeon" class="btn-secondary btn-small" style="flex: 1;">
            导入副本
            <input type="file" accept=".json" style="display: none;" @change="(event) => onImport(event, 'dungeon')">
          </label>
          <label id="btn-import-node" class="btn-secondary btn-small" style="flex: 1;">
            导入节点
            <input type="file" accept=".json" style="display: none;" @change="(event) => onImport(event, 'node')">
          </label>
          <button id="btn-delete-node" class="btn-secondary btn-small" style="color: var(--danger);" @click="deleteCurrent">删除</button>
        </div>
      </div>

      <div id="tree-root" class="worldbook-tree-container" style="flex: 1; min-height: 200px; overflow: auto;">
        <div v-if="selectedScript" class="tree-node">
          <div class="tree-node-label">{{ selectedScript.name }}</div>
          <div class="tree-node-children" style="padding-left: 14px;">
            <div
              v-for="dungeonId in selectedScript.dungeon_ids"
              :key="dungeonId"
              :class="['tree-node-label', { active: selectedDungeonId === dungeonId }]"
              @click="selectDungeon(dungeonId)"
            >
              {{ dungeonId }}
            </div>
          </div>
        </div>
        <div v-if="selectedDungeon" class="tree-node" style="margin-top: 12px;">
          <div class="tree-node-label">{{ selectedDungeon.name }}</div>
          <div class="tree-node-children" style="padding-left: 14px;">
            <div
              v-for="node in filteredNodes"
              :key="node.node_id"
              :class="['tree-node-label', { active: selectedNodeId === node.node_id }]"
              @click="selectNode(node.node_id)"
            >
              {{ node.name }}
            </div>
          </div>
        </div>
        <div v-if="!selectedScript" class="placeholder-text" style="color: var(--text-secondary); padding: 20px;">请从左侧选择剧本或节点...</div>
      </div>
    </section>

    <section class="right-panel">
      <div class="panel-header">
        <div id="detail-title" class="panel-title">{{ detailTitle }}</div>
        <div class="panel-header-right">
          <div class="toggle-group mode-toggle" style="margin-right: 10px;">
            <button id="mode-preview" :class="['btn-small', { active: mode === 'preview' }]" type="button" @click="mode = 'preview'">预览</button>
            <button id="mode-edit" :class="['btn-small', { active: mode === 'edit' }]" type="button" @click="mode = 'edit'">编辑</button>
          </div>
          <button id="btn-save-detail" class="btn-primary" @click="saveDetail">保存更改</button>
          <button id="btn-export-current" class="btn-secondary btn-small" style="margin-left: 8px;" @click="exportCurrent">导出</button>
        </div>
      </div>

      <div id="detail-panel" class="detail-panel" style="flex: 1; display: flex; flex-direction: column; gap: 12px; overflow: auto;">
        <div v-if="mode === 'preview'" class="settings-section">
          <pre v-if="selectedNode" class="form-textarea" style="white-space: pre-wrap;">{{ JSON.stringify(selectedNode, null, 2) }}</pre>
          <pre v-else-if="selectedDungeon" class="form-textarea" style="white-space: pre-wrap;">{{ JSON.stringify(selectedDungeon, null, 2) }}</pre>
          <pre v-else-if="selectedScript" class="form-textarea" style="white-space: pre-wrap;">{{ JSON.stringify(selectedScript, null, 2) }}</pre>
          <div v-else class="placeholder-text" style="color: var(--text-secondary); padding: 20px;">请从左侧选择剧本或节点...</div>
        </div>

        <div v-if="mode === 'edit'" class="settings-section">
          <div class="half-grid">
            <div>
              <label class="form-label">剧本 ID</label>
              <input v-model="scriptDraft.script_id" class="form-input">
            </div>
            <div>
              <label class="form-label">剧本名称</label>
              <input v-model="scriptDraft.name" class="form-input">
            </div>
          </div>
          <div style="margin-top: 12px;">
            <label class="form-label">剧本描述</label>
            <textarea v-model="scriptDraft.description" class="form-textarea" rows="4"></textarea>
          </div>

          <hr style="border: 0; border-top: 1px solid var(--border-soft); margin: 15px 0;">

          <div class="half-grid">
            <div>
              <label class="form-label">副本 ID</label>
              <input v-model="dungeonDraft.dungeon_id" class="form-input">
            </div>
            <div>
              <label class="form-label">副本名称</label>
              <input v-model="dungeonDraft.name" class="form-input">
            </div>
          </div>
          <div style="margin-top: 12px;">
            <label class="form-label">副本描述</label>
            <textarea v-model="dungeonDraft.description" class="form-textarea" rows="4"></textarea>
          </div>
          <div class="half-grid" style="margin-top: 12px;">
            <div><label class="form-label">最低等级</label><input v-model.number="dungeonDraft.level_min" class="form-input" type="number"></div>
            <div><label class="form-label">最高等级</label><input v-model.number="dungeonDraft.level_max" class="form-input" type="number"></div>
          </div>
          <div style="margin-top: 12px;">
            <label class="form-label">全局规则 JSON</label>
            <textarea class="form-textarea" rows="6" :value="JSON.stringify(dungeonDraft.global_rules || {}, null, 2)" @input="updateGlobalRules($event.target.value)"></textarea>
          </div>
          <div style="margin-top: 12px;">
            <label class="form-label">节点列表</label>
            <div v-for="node in dungeonDraft.nodes" :key="node.node_id" class="char-card" style="margin-bottom: 10px;">
              <div class="half-grid">
                <div><label class="small-text muted">节点 ID</label><input v-model="node.node_id" class="form-input"></div>
                <div><label class="small-text muted">节点名称</label><input v-model="node.name" class="form-input"></div>
              </div>
              <div class="half-grid" style="margin-top: 10px;">
                <div><label class="small-text muted">排序</label><input v-model.number="node.index" class="form-input" type="number"></div>
                <div><label class="small-text muted">进度</label><input v-model.number="node.progress_percent" class="form-input" type="number"></div>
              </div>
              <div style="margin-top: 10px;"><label class="small-text muted">摘要要求</label><textarea v-model="node.summary_requirements" class="form-textarea" rows="3"></textarea></div>
            </div>
          </div>
        </div>
      </div>
    </section>
  </main>
</template>

<script setup>
import { onMounted } from 'vue';
import { useDungeonPage } from '../composables/useDungeonPage';
import { initThemePage } from '../page_logic/theme-init.module';

const {
  applyScript,
  bootstrap,
  createDungeon,
  createNode,
  createScript,
  deleteCurrent,
  detailTitle,
  dungeonDraft,
  exportCurrent,
  filteredNodes,
  importJson,
  mode,
  saveDetail,
  scriptDraft,
  scripts,
  searchKeyword,
  selectDungeon,
  selectedDungeon,
  selectedDungeonId,
  selectNode,
  selectedNode,
  selectedNodeId,
  selectScript,
  selectedScript,
  selectedScriptId,
  statusText,
} = useDungeonPage();

function updateGlobalRules(value) {
  try {
    dungeonDraft.value.global_rules = JSON.parse(value || '{}');
  } catch {
    // keep draft text stable until valid JSON is entered
  }
}

async function onImport(event, modeName) {
  await importJson(event.target.files, modeName);
  event.target.value = '';
}

onMounted(async () => {
  document.title = 'Storyteller | 剧本';
  document.body.setAttribute('data-page', 'dungeon');
  initThemePage();
  await bootstrap();
});
</script>
