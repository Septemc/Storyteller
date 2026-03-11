<template>
  <main class="two-column-layout worldbook-page">
    <section class="left-panel worldbook-sidebar">
      <div class="panel-header">
        <div class="panel-title">世界书体系</div>
      </div>

      <div class="settings-section worldbook-toolbar-card">
        <div class="worldbook-top-row">
          <select id="world-selector" v-model="selectedWorldId" class="form-select worldbook-select" @change="applySelection(selectedWorldId)">
            <option v-for="world in worldOptions" :key="world.id" :value="world.id">
              {{ world.name }} ({{ world.count }} 条)
            </option>
          </select>

          <label class="world-switch" :class="{ active: selectedWorldApplied }">
            <input :checked="selectedWorldApplied" type="checkbox" @change="toggleSelectedWorldApplied($event.target.checked)">
            <span class="world-switch-track"></span>
            <span class="world-switch-label">启用</span>
          </label>

          <button id="btn-new-world" class="btn-secondary btn-small" @click="createWorldbook">新建</button>
          <label id="btn-import-world" class="btn-secondary btn-small">
            导入
            <input type="file" accept=".json" style="display: none;" @change="(event) => onImport(event, 'world')">
          </label>
          <button id="btn-export-world" class="btn-secondary btn-small" @click="exportCurrentWorld">导出</button>
          <button id="btn-delete-world" class="btn-secondary btn-small" style="color: var(--danger);" @click="deleteWorldbook">删除</button>
        </div>

        <div class="worldbook-status-line">
          <span class="worldbook-status-label">当前启用：</span>
          <span>{{ appliedWorldSummary }}</span>
        </div>
        <div id="import-status" class="small-text muted worldbook-status-line">{{ statusText }}</div>
      </div>

      <div class="settings-section worldbook-filter-card">
        <div class="search-wrapper worldbook-search">
          <input
            id="search-keyword"
            v-model="searchKeyword"
            class="form-input"
            type="search"
            placeholder="搜索内容..."
            autocomplete="new-password"
            autocapitalize="off"
            autocorrect="off"
            spellcheck="false"
            inputmode="search"
            enterkeyhint="search"
            name="worldbook_lookup_query"
            data-lpignore="true"
            data-form-type="other"
            data-search-guard="true"
            @keydown.enter.prevent="loadWorlds()"
          >
          <label class="semantic-toggle">
            <input id="semantic-search-toggle" v-model="useSemanticSearch" type="checkbox">
            <span>语义</span>
          </label>
          <button id="btn-search" class="btn-secondary btn-small" @click="loadWorlds()">搜</button>
        </div>

        <div class="worldbook-action-row">
          <button id="btn-create-category" class="btn-secondary btn-small" @click="createCategory">新建模块</button>
          <button id="btn-create-entry" class="btn-secondary btn-small" @click="createEntry">新建条目</button>
          <label id="btn-import-category" class="btn-secondary btn-small">
            导入模块
            <input type="file" accept=".json" style="display: none;" @change="(event) => onImport(event, 'category')">
          </label>
          <label id="btn-import-entry" class="btn-secondary btn-small">
            导入条目
            <input type="file" accept=".json" style="display: none;" @change="(event) => onImport(event, 'entry')">
          </label>
          <button id="btn-delete-node" class="btn-secondary btn-small" style="color: var(--danger);" @click="deleteSelection">删除</button>
        </div>

        <div class="small-text muted worldbook-status-line">
          {{ useSemanticSearch ? '当前使用语义检索结果显示模块与条目' : '当前使用关键词搜索' }}
        </div>
      </div>

      <div class="worldbook-tree-shell">
        <div v-if="selectedWorld" class="worldbook-root-card" :class="{ disabled: !selectedWorldApplied }">
          <div class="worldbook-root-title">
            {{ metaMap[selectedWorld.id]?.name || selectedWorld.id }}
          </div>
          <div class="worldbook-root-meta">
            <span>{{ selectedWorld.entries.length }} 条</span>
            <span>{{ selectedWorldModules.length }} 个模块</span>
            <span>{{ selectedWorldApplied ? '已启用' : '未启用' }}</span>
          </div>
          <div v-if="metaMap[selectedWorld.id]?.description" class="worldbook-root-description">
            {{ metaMap[selectedWorld.id]?.description }}
          </div>
        </div>

        <div id="tree-root" class="worldbook-tree-container worldbook-module-list">
          <template v-if="selectedWorldModules.length">
            <article
              v-for="module in selectedWorldModules"
              :key="module.key"
              class="worldbook-module-card"
              :class="{
                active: selectedCategory === module.name,
                disabled: !module.effectiveEnabled,
              }"
            >
              <div class="worldbook-module-header">
                <button class="worldbook-module-main" type="button" @click="selectModule(module)">
                  <span class="worldbook-module-arrow" :class="{ expanded: module.isExpanded }">▾</span>
                  <span class="worldbook-module-name">{{ module.name }}</span>
                  <span class="worldbook-module-count">{{ module.count }} 条</span>
                </button>

                <label class="mini-switch" :class="{ active: module.enabled }">
                  <input :checked="module.enabled" type="checkbox" @change.stop="setCategoryEnabled(module.name, $event.target.checked)">
                  <span class="mini-switch-track"></span>
                </label>
              </div>

              <div v-show="module.isExpanded" class="worldbook-entry-list">
                <button
                  v-for="entry in module.entries"
                  :key="entry.entry_id"
                  class="worldbook-entry-card"
                  :class="{
                    active: selectedEntryId === entry.entry_id,
                    disabled: !entry.effectiveEnabled,
                  }"
                  type="button"
                  @click="selectEntry(module.name, entry)"
                >
                  <div class="worldbook-entry-main">
                    <span class="worldbook-entry-title">{{ entry.title }}</span>
                    <span v-if="entry.tags?.length" class="worldbook-entry-tags">{{ entry.tags.join(' / ') }}</span>
                  </div>
                  <label class="mini-switch" :class="{ active: entry.enabled }">
                    <input :checked="entry.enabled" type="checkbox" @change.stop="toggleEntryEnabled(entry, $event.target.checked)">
                    <span class="mini-switch-track"></span>
                  </label>
                </button>
              </div>
            </article>
          </template>

          <div v-else class="placeholder-text worldbook-empty-state">
            {{ selectedWorld ? '当前世界书下没有可显示的模块或条目' : '请先从上方下拉框选择世界书' }}
          </div>
        </div>
      </div>
    </section>

    <section class="right-panel">
      <div class="panel-header">
        <div id="detail-title" class="panel-title">{{ currentDetailTitle }}</div>
        <div class="panel-header-right">
          <div class="toggle-group mode-toggle" style="margin-right: 10px;">
            <button id="mode-preview" :class="['btn-small', { active: mode === 'preview' }]" type="button" @click="mode = 'preview'">预览</button>
            <button id="mode-edit" :class="['btn-small', { active: mode === 'edit' }]" type="button" @click="mode = 'edit'">编辑</button>
          </div>
          <button id="btn-save-detail" class="btn-primary" @click="saveDetail">保存更改</button>
          <button id="btn-export-current" class="btn-secondary btn-small" style="margin-left: 8px;" @click="exportCurrentSelection">导出</button>
        </div>
      </div>

      <div id="detail-panel" class="detail-panel" style="flex: 1; display: flex; flex-direction: column; gap: 12px; overflow: auto;">
        <div v-if="mode === 'preview'" class="settings-section">
          <div v-if="selectedEntry">
            <div class="form-label">条目标题</div>
            <div class="form-input">{{ selectedEntry.title }}</div>
            <div class="form-label" style="margin-top: 10px;">正文</div>
            <div class="form-textarea" style="min-height: 240px; white-space: pre-wrap;">{{ selectedEntry.content }}</div>
          </div>
          <div v-else-if="selectedWorld">
            <div class="form-label">世界书名称</div>
            <input class="form-input" :value="metaMap[selectedWorld.id]?.name || selectedWorld.id" @input="updateWorldMeta('name', $event.target.value)">
            <div class="form-label" style="margin-top: 10px;">世界书描述</div>
            <textarea class="form-textarea" rows="6" :value="metaMap[selectedWorld.id]?.description || ''" @input="updateWorldMeta('description', $event.target.value)"></textarea>
          </div>
          <div v-else class="placeholder-text" style="color: var(--text-secondary); padding: 20px;">请从左侧选择世界书、模块或条目...</div>
        </div>

        <div v-if="mode === 'edit'" class="settings-section">
          <div class="half-grid">
            <div>
              <label class="form-label">世界书 ID</label>
              <input v-model="detailDraft.worldbook_id" class="form-input" readonly>
            </div>
            <div>
              <label class="form-label">模块</label>
              <input v-model="detailDraft.category" class="form-input">
            </div>
          </div>
          <div class="half-grid" style="margin-top: 12px;">
            <div>
              <label class="form-label">条目 ID</label>
              <input v-model="detailDraft.entry_id" class="form-input" placeholder="留空由后端生成">
            </div>
            <div>
              <label class="form-label">重要度</label>
              <input v-model.number="detailDraft.importance" class="form-input" type="number" min="0" max="1" step="0.1">
            </div>
          </div>
          <div style="margin-top: 12px;">
            <label class="form-label">标题</label>
            <input v-model="detailDraft.title" class="form-input">
          </div>
          <div style="margin-top: 12px;">
            <label class="form-label">标签</label>
            <input :value="(detailDraft.tags || []).join(', ')" class="form-input" @input="detailDraft.tags = $event.target.value.split(',').map((item) => item.trim()).filter(Boolean)">
          </div>
          <div style="margin-top: 12px;">
            <label class="form-check"><input v-model="detailDraft.canonical" type="checkbox"><span>标记为规范设定</span></label>
          </div>
          <div style="margin-top: 12px;">
            <label class="form-label">内容</label>
            <textarea v-model="detailDraft.content" class="form-textarea" rows="16"></textarea>
          </div>
          <div style="margin-top: 12px;">
            <label class="form-label">Meta (JSON)</label>
            <textarea class="form-textarea" rows="8" :value="metaText" @input="updateMetaText($event.target.value)"></textarea>
          </div>
        </div>
      </div>
    </section>
  </main>
</template>

<script setup>
import { onMounted } from 'vue';
import { useWorldbookPage } from '../composables/useWorldbookPage';
import { initThemePage } from '../page_logic/theme-init.module';

const {
  appliedWorldSummary,
  applySelection,
  bootstrap,
  createCategory,
  createEntry,
  createWorldbook,
  currentDetailTitle,
  deleteSelection,
  deleteWorldbook,
  detailDraft,
  exportCurrentSelection,
  exportCurrentWorld,
  importFiles,
  loadWorlds,
  metaMap,
  metaText,
  mode,
  saveDetail,
  searchKeyword,
  selectedEntry,
  selectedEntryId,
  selectedWorld,
  selectedWorldApplied,
  selectedWorldId,
  selectedWorldModules,
  setCategoryEnabled,
  statusText,
  toggleCategoryExpanded,
  toggleEntryEnabled,
  toggleSelectedWorldApplied,
  updateMetaText,
  updateWorldMeta,
  useSemanticSearch,
  worldOptions,
} = useWorldbookPage();

function selectModule(module) {
  toggleCategoryExpanded(module.name);
  applySelection(selectedWorldId.value, module.name);
}

function selectEntry(categoryName, entry) {
  applySelection(selectedWorldId.value, categoryName, entry.entry_id);
}

async function onImport(event, modeName) {
  await importFiles(event.target.files, modeName);
  event.target.value = '';
}

onMounted(async () => {
  document.title = 'Storyteller | 世界书';
  document.body.setAttribute('data-page', 'worldbook');
  initThemePage();
  await bootstrap();
});
</script>

<style scoped>
.worldbook-page {
  gap: 18px;
}

.worldbook-sidebar {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.worldbook-toolbar-card,
.worldbook-filter-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.worldbook-top-row,
.worldbook-action-row {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.worldbook-select {
  min-width: 260px;
  flex: 1 1 260px;
}

.worldbook-status-line {
  line-height: 1.5;
}

.worldbook-status-label {
  color: var(--text-primary);
  font-weight: 600;
}

.worldbook-search {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto;
  gap: 10px;
  align-items: center;
}

.semantic-toggle {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--text-secondary);
  font-size: 13px;
  white-space: nowrap;
}

.worldbook-tree-shell {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 0;
  flex: 1;
}

.worldbook-root-card {
  padding: 14px 16px;
  border: 1px solid var(--border-soft);
  border-radius: 18px;
  background:
    linear-gradient(135deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02)),
    rgba(0, 0, 0, 0.04);
}

.worldbook-root-card.disabled {
  opacity: 0.75;
}

.worldbook-root-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
}

.worldbook-root-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 14px;
  margin-top: 8px;
  color: var(--text-secondary);
  font-size: 13px;
}

.worldbook-root-description {
  margin-top: 10px;
  color: var(--text-secondary);
  line-height: 1.6;
}

.worldbook-module-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 2px;
}

.worldbook-module-card {
  border: 1px solid var(--border-soft);
  border-radius: 18px;
  background:
    linear-gradient(180deg, rgba(255,255,255,0.04), rgba(255,255,255,0.015)),
    rgba(0, 0, 0, 0.05);
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

.worldbook-module-card.active {
  border-color: color-mix(in srgb, var(--accent) 42%, var(--border-soft));
  box-shadow: 0 0 0 1px color-mix(in srgb, var(--accent) 24%, transparent), 0 12px 24px rgba(0, 0, 0, 0.05);
}

.worldbook-module-card.disabled {
  opacity: 0.72;
}

.worldbook-module-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 14px 16px;
}

.worldbook-module-main {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  background: transparent;
  border: 0;
  color: inherit;
  padding: 0;
  cursor: pointer;
  text-align: left;
}

.worldbook-module-arrow {
  font-size: 12px;
  transition: transform 0.18s ease;
  color: var(--text-secondary);
}

.worldbook-module-arrow.expanded {
  transform: rotate(0deg);
}

.worldbook-module-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.worldbook-module-count {
  color: var(--text-secondary);
  font-size: 12px;
}

.worldbook-entry-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 0 12px 12px 12px;
}

.worldbook-entry-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  width: 100%;
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.05);
  padding: 11px 12px;
  cursor: pointer;
  transition: border-color 0.18s ease, transform 0.18s ease, background 0.18s ease;
}

.worldbook-entry-card:hover {
  transform: translateY(-1px);
  border-color: color-mix(in srgb, var(--accent) 30%, var(--border-soft));
}

.worldbook-entry-card.active {
  border-color: color-mix(in srgb, var(--accent) 44%, var(--border-soft));
  background: color-mix(in srgb, var(--accent) 10%, transparent);
}

.worldbook-entry-card.disabled {
  opacity: 0.62;
}

.worldbook-entry-main {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.worldbook-entry-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.worldbook-entry-tags {
  color: var(--text-secondary);
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.worldbook-empty-state {
  padding: 24px 16px;
  text-align: center;
}

.world-switch,
.mini-switch {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  user-select: none;
}

.world-switch input,
.mini-switch input {
  display: none;
}

.world-switch-track,
.mini-switch-track {
  position: relative;
  display: inline-block;
  background: rgba(0, 0, 0, 0.12);
  border: 1px solid rgba(0, 0, 0, 0.08);
  transition: background 0.18s ease, border-color 0.18s ease;
}

.world-switch-track::after,
.mini-switch-track::after {
  content: '';
  position: absolute;
  top: 50%;
  background: #fff;
  border-radius: 999px;
  transform: translateY(-50%);
  transition: left 0.18s ease;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.18);
}

.world-switch-track {
  width: 44px;
  height: 24px;
  border-radius: 999px;
}

.world-switch-track::after {
  left: 3px;
  width: 16px;
  height: 16px;
}

.world-switch.active .world-switch-track,
.mini-switch.active .mini-switch-track {
  background: color-mix(in srgb, var(--accent) 55%, transparent);
  border-color: color-mix(in srgb, var(--accent) 60%, var(--border-soft));
}

.world-switch.active .world-switch-track::after {
  left: 23px;
}

.world-switch-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
}

.mini-switch-track {
  width: 36px;
  height: 20px;
  border-radius: 999px;
}

.mini-switch-track::after {
  left: 2px;
  width: 14px;
  height: 14px;
}

.mini-switch.active .mini-switch-track::after {
  left: 18px;
}

@media (max-width: 900px) {
  .worldbook-search {
    grid-template-columns: 1fr;
  }

  .worldbook-top-row,
  .worldbook-action-row {
    flex-direction: column;
    align-items: stretch;
  }

  .worldbook-select {
    min-width: 0;
  }
}
</style>
