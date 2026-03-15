<template>
  <section class="left-panel characters-sidebar">
    <div class="panel-header"><div class="panel-title">角色模块</div></div>
    <div class="settings-section sidebar-scroll">
      <div class="field-block section-block">
        <div class="section-heading">角色模板</div>
        <div class="template-select-row">
          <select :value="selectedTemplateId" class="form-select stretch" @change="$emit('update:selectedTemplateId', $event.target.value)">
            <option v-if="!templates.length" value="">当前存档暂无角色模板</option>
            <option v-for="item in templates" :key="item.id" :value="item.id">{{ item.name }}</option>
          </select>
          <div class="template-status-chip" :title="templateStatusText">{{ templateStatusText }}</div>
        </div>
        <div class="button-strip">
          <button class="btn-primary btn-small" :disabled="!selectedTemplateId" @click="$emit('activate-template')">应用模板</button>
          <button class="btn-secondary btn-small" :disabled="!selectedTemplateId" @click="$emit('edit-template')">编辑模板</button>
          <button class="btn-secondary btn-small" @click="$emit('create-template')">新建模板</button>
          <label class="btn-secondary btn-small">导入模板<input type="file" accept=".json" hidden @change="emitFiles($event, 'import-template')"></label>
          <button class="btn-secondary btn-small" :disabled="!selectedTemplateId" @click="$emit('export-template')">导出模板</button>
          <button class="btn-secondary btn-small danger-btn" :disabled="!selectedTemplateId" @click="$emit('delete-template')">删除模板</button>
        </div>
      </div>

      <div class="field-block section-block">
        <div class="section-heading">角色列表</div>
        <div class="search-box">
          <input :value="searchKeyword" class="form-input search-input" placeholder="搜索角色 ID / 名称" @input="$emit('update:searchKeyword', $event.target.value)" @keyup.enter="$emit('search')">
          <button class="search-btn" type="button" aria-label="搜索" @click="$emit('search')"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"></circle><path d="m20 20-3.5-3.5"></path></svg></button>
        </div>
        <div class="button-strip">
          <button class="btn-primary btn-small" :disabled="!selectedTemplateId" @click="$emit('create-character')">新建角色</button>
          <label class="btn-secondary btn-small">导入角色<input type="file" accept=".json" multiple hidden @change="emitFiles($event, 'import-character')"></label>
          <button class="btn-secondary btn-small" @click="$emit('export-characters')">导出全部</button>
          <button class="btn-secondary btn-small danger-btn" @click="$emit('clear-characters')">删除全部</button>
        </div>
      </div>

      <div class="list-shell">
        <button v-for="item in filteredCharacters" :key="item.character_id" :class="['list-item', 'character-item', { active: selectedCharacterId === item.character_id }]" @click="$emit('select-character', item.character_id)">
          <div class="character-name">{{ audienceMode === 'developer' ? item.developer_name || item.display_name : item.display_name }}</div>
          <div class="character-meta"><span>{{ item.character_id }}</span><span>{{ item.status }}</span><span>{{ item.type }}</span></div>
        </button>
        <div v-if="!filteredCharacters.length && !loading" class="muted empty-box">暂无角色</div>
      </div>
    </div>
  </section>
</template>

<script setup>
defineProps({
  audienceMode: { type: String, default: 'player' },
  filteredCharacters: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  searchKeyword: { type: String, default: '' },
  selectedCharacterId: { type: String, default: '' },
  selectedTemplateId: { type: String, default: '' },
  templateStatusText: { type: String, default: '' },
  templates: { type: Array, default: () => [] },
});

const emit = defineEmits(['activate-template', 'clear-characters', 'create-character', 'create-template', 'delete-template', 'edit-template', 'export-characters', 'export-template', 'import-character', 'import-template', 'search', 'select-character', 'update:searchKeyword', 'update:selectedTemplateId']);
function emitFiles(event, name) { emit(name, event.target.files); event.target.value = ''; }
</script>

<style scoped>
.characters-sidebar { overflow: hidden; }
.sidebar-scroll { height: calc(100% - 76px); display: flex; flex-direction: column; gap: 14px; overflow: hidden; }
.section-block { display: flex; flex-direction: column; gap: 10px; }
.section-heading { font-size: 13px; font-weight: 700; color: var(--text-secondary); }
.template-select-row { display: flex; gap: 8px; align-items: center; }
.template-status-chip { flex: 0 0 auto; max-width: 44%; min-height: 30px; display: inline-flex; align-items: center; padding: 0 10px; border: 1px solid var(--border-soft); border-radius: 10px; color: var(--text-secondary); background: rgba(255, 255, 255, 0.04); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-size: 12px; line-height: 1; }
.button-strip { display: flex; gap: 8px; flex-wrap: wrap; }
.search-box { position: relative; }
.search-input { padding-right: 42px; }
.search-btn { position: absolute; top: 50%; right: 10px; transform: translateY(-50%); border: 0; background: transparent; color: var(--text-secondary); cursor: pointer; }
.list-shell { flex: 1; min-height: 0; border: 1px solid var(--border-soft); border-radius: 14px; padding: 10px; overflow: auto; background: rgba(0, 0, 0, 0.08); }
.character-item { width: 100%; text-align: left; display: flex; flex-direction: column; gap: 6px; }
.character-name { font-weight: 700; }
.character-meta { display: flex; flex-wrap: wrap; gap: 10px; font-size: 12px; color: var(--text-secondary); }
.empty-box { padding: 18px; text-align: center; }
.danger-btn { color: var(--danger); }
</style>
