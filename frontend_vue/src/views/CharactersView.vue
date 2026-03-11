<template>
  <main class="two-column-layout">
    <section class="left-panel">
      <div class="panel-header">
        <div class="panel-title">角色管理</div>
      </div>

      <div class="settings-section" style="padding-bottom: 12px; border-bottom: 1px solid var(--border-soft); margin-bottom: 10px;">
        <label class="form-label">管理角色模板</label>
        <div style="display: flex; gap: 5px; margin-bottom: 8px;">
          <select id="template-select" v-model="selectedTemplateId" class="form-select" style="flex: 1;">
            <option v-for="template in templates" :key="template.id" :value="template.id">{{ template.name }}</option>
          </select>
          <button
            id="tpl-apply-btn"
            class="btn-small btn-primary"
            title="将此模板应用到当前角色"
            @click="updateCharacterMeta('template_id', selectedTemplateId)"
          >
            应用
          </button>
          <label id="template-import-btn" class="btn-small btn-secondary" title="从文件导入 JSON 格式模板">
            导入
            <input type="file" accept=".json" style="display: none;" @change="onTemplateImport">
          </label>
          <button id="tpl-export-btn" class="btn-small btn-secondary" @click="exportCurrentTemplate">导出</button>
          <button id="tpl-delete-btn" class="btn-small btn-secondary" style="color: var(--danger);" title="删除当前模板" @click="deleteCurrentTemplate">
            删除
          </button>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 5px;">
          <button id="tpl-edit-btn" class="btn-small btn-secondary" @click="openDesigner(false)">编辑选中模板</button>
          <button id="tpl-new-btn" class="btn-small btn-secondary" @click="openDesigner(true)">新建角色模板</button>
        </div>
      </div>

      <div class="settings-section" style="flex: 1; display: flex; flex-direction: column; min-height: 0;">
        <div class="search-wrapper" style="position: relative; margin-bottom: 10px;">
          <input
            id="character-search"
            v-model="searchKeyword"
            class="form-input"
            type="search"
            placeholder="搜索 ID 或名称..."
            style="padding-right: 32px;"
            autocomplete="new-password"
            autocapitalize="off"
            autocorrect="off"
            spellcheck="false"
            inputmode="search"
            enterkeyhint="search"
            name="character_lookup_query"
            data-lpignore="true"
            data-form-type="other"
            data-search-guard="true"
            @input="loadCharacters"
            @keydown.enter.prevent="loadCharacters"
          >
          <button
            id="btn-character-search"
            class="icon-button"
            style="position: absolute; right: 6px; top: 50%; transform: translateY(-50%);"
            @click="loadCharacters"
          >
            搜
          </button>
        </div>

        <div style="display: flex; gap: 4px; align-items: center; margin-bottom: 10px;">
          <label id="character-import-btn" class="btn-secondary btn-small" style="flex: 1;" title="导入角色 JSON">
            导入
            <input type="file" accept=".json" multiple style="display: none;" @change="onCharacterImport">
          </label>
          <button id="character-export-all-btn" class="btn-secondary btn-small" style="flex: 1;" title="批量导出角色" @click="exportAllCharacters">
            导出
          </button>
          <button id="character-new-btn" class="btn-primary btn-small" style="flex: 1;" title="创建新角色" @click="createNewCharacter">
            新建
          </button>
          <button id="character-delete-all-btn" class="btn-secondary btn-small" style="color: var(--danger); flex: 1;" title="删除全部角色" @click="clearAllCharacters">
            清空
          </button>
        </div>

        <div class="character-list-scroll-area" style="flex: 1; overflow-y: auto; border: 1px solid var(--border-soft); border-radius: var(--radius-sm); background: rgba(0,0,0,0.1);">
          <ul id="character-list" class="list" style="margin-top: 0;">
            <li
              v-for="character in filteredCharacters"
              :key="character.character_id"
              :class="['list-item', { active: selectedCharacterId === character.character_id }]"
              @click="selectCharacter(character.character_id)"
            >
              {{ character.basic?.name || character.basic?.f_name || character.character_id }} ({{ character.character_id }})
            </li>
            <li v-if="!filteredCharacters.length && !loading" class="list-item muted">暂无角色</li>
          </ul>
        </div>
      </div>
    </section>

    <section class="right-panel">
      <div class="panel-header">
        <div id="right-panel-title" class="panel-title">{{ currentCharacter.character_id || '角色详情' }}</div>
        <div class="panel-header-right">
          <button id="character-apply-btn" class="btn-secondary btn-small" title="将当前角色设为本存档主角" @click="applyToSession">
            应用到存档
          </button>
          <button id="character-export-single-btn" class="btn-small btn-secondary" @click="exportCurrentCharacter">导出当前角色</button>
          <button id="character-delete-btn" class="btn-small btn-secondary" style="color: var(--danger); margin-right: 10px;" @click="deleteCurrentCharacter">
            删除角色
          </button>
          <div class="toggle-group mode-toggle" style="margin-right: 10px;">
            <button id="view-mode-btn" :class="['btn-small', { active: mode === 'preview' }]" type="button" @click="mode = 'preview'">预览</button>
            <button id="edit-mode-btn" :class="['btn-small', { active: mode === 'edit' }]" type="button" @click="mode = 'edit'">编辑</button>
          </div>
          <button id="character-save-btn" class="btn-primary" @click="saveCharacter">保存角色</button>
          <span id="character-status" class="small-text" style="margin-left: 10px;">{{ statusText }}</span>
        </div>
      </div>

      <div v-show="mode === 'preview'" id="character-renderer" class="detail-panel rendered-view">
        <div v-if="!currentCharacter.character_id" class="placeholder-text" style="color: var(--text-secondary); padding: 20px;">请从左侧列表选择角色...</div>
        <div v-else class="settings-section" style="display: flex; flex-direction: column; gap: 16px;">
          <section v-for="section in previewSections" :key="section.id" class="char-card">
            <div class="panel-title" style="margin-bottom: 10px;">{{ section.label }}</div>
            <div class="half-grid">
              <div v-for="field in section.fields" :key="field.id" style="display: flex; flex-direction: column; gap: 4px;">
                <label class="small-text muted">{{ field.label }}</label>
                <div class="form-input" style="min-height: 40px; white-space: pre-wrap;">{{ stringifyFieldValue(field.type, getFieldValue(field)) }}</div>
              </div>
            </div>
          </section>
        </div>
      </div>

      <div v-show="mode === 'edit'" id="character-editor" class="detail-panel">
        <div class="settings-section half-grid">
          <div>
            <label class="form-label">角色编号 (ID)</label>
            <input id="f-char-id" :value="currentCharacter.character_id" class="form-input" placeholder="例如 NPC_001" @input="updateCharacterMeta('character_id', $event.target.value)">
          </div>
          <div>
            <label class="form-label">角色类型</label>
            <select id="f-char-type" :value="currentCharacter.type" class="form-select" @change="updateCharacterMeta('type', $event.target.value)">
              <option value="npc">NPC</option>
              <option value="protagonist">主角</option>
              <option value="major">重要角色</option>
            </select>
          </div>
        </div>
        <hr style="border: 0; border-top: 1px solid var(--border-soft); margin: 15px 0;">
        <div id="editor-tabs-nav" class="character-tabs">
          <button
            v-for="section in previewSections"
            :key="section.id"
            type="button"
            :class="['character-tab-btn', { active: editTab === section.id }]"
            @click="editTab = section.id"
          >
            {{ section.label }}
          </button>
        </div>
        <div id="editor-fields-container" style="margin-top: 10px;">
          <div v-for="field in currentEditFields" :key="field.id" class="settings-section">
            <label class="form-label">{{ field.label }}</label>
            <input
              v-if="field.type === 'text' || field.type === 'number' || field.type === 'tags'"
              :value="getEditorValue(field)"
              class="form-input"
              :type="field.type === 'number' ? 'number' : 'text'"
              @input="updateEditorInput(field, $event.target.value)"
              @blur="commitEditorValue(field)"
            >
            <textarea
              v-else
              :value="getEditorValue(field)"
              class="form-textarea"
              rows="6"
              @input="updateEditorInput(field, $event.target.value)"
              @blur="commitEditorValue(field)"
            ></textarea>
          </div>
        </div>
      </div>
    </section>
  </main>

  <div v-if="designerOpen" id="template-designer-modal" class="modal-overlay" style="display: flex;">
    <div class="modal-window">
      <div class="modal-header">
        <div style="display: flex; gap: 15px; align-items: center;">
          <span class="panel-title" style="color: var(--accent);">角色模板设计器</span>
          <input id="design-tpl-id" v-model="designerState.id" class="form-input" style="width: 140px;" placeholder="模板唯一 ID">
          <input id="design-tpl-name" v-model="designerState.name" class="form-input" style="width: 200px;" placeholder="显示名称">
        </div>
        <div class="modal-header-right">
          <button id="save-template-btn" class="btn-primary" @click="saveDesigner">保存模板配置</button>
          <button id="close-designer-btn" class="btn-secondary" @click="closeDesigner">关闭</button>
        </div>
      </div>

      <div class="modal-body" style="display: grid; grid-template-columns: 280px 1fr; gap: 20px; padding: 0;">
        <div style="border-right: 1px solid var(--border-soft); padding: 20px; background: rgba(0,0,0,0.1);">
          <div class="section-inline-header" style="margin-bottom: 15px;">
            <span class="form-label" style="font-weight: bold;">1. 标签页 (Tabs)</span>
            <button id="design-add-tab-btn" class="btn-small-inline btn-secondary" @click="addDesignerTab">+ 添加新标签</button>
          </div>
          <div id="design-tabs-container" style="display: flex; flex-direction: column; gap: 8px;">
            <div v-for="(tab, index) in designerState.config.tabs" :key="tab.id" style="display: flex; gap: 6px;">
              <input v-model="tab.id" class="form-input" placeholder="tab_basic">
              <input v-model="tab.label" class="form-input" placeholder="标签名称">
              <button class="btn-small btn-secondary" @click="designerState.config.tabs.splice(index, 1)">删</button>
            </div>
          </div>
        </div>

        <div style="padding: 20px; overflow-y: auto;">
          <div class="section-inline-header" style="margin-bottom: 15px;">
            <span class="form-label" style="font-weight: bold;">2. 字段配置 (Fields)</span>
            <button id="design-add-field-btn" class="btn-small btn-secondary" @click="addDesignerField">+ 添加新字段</button>
          </div>
          <div id="design-fields-container" style="display: flex; flex-direction: column; gap: 12px;">
            <div v-for="(field, index) in designerState.config.fields" :key="field.id" class="char-card">
              <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-bottom: 10px;">
                <div><label class="small-text muted">内部 ID</label><input v-model="field.id" class="form-input"></div>
                <div><label class="small-text muted">显示标签</label><input v-model="field.label" class="form-input"></div>
                <div>
                  <label class="small-text muted">类型</label>
                  <select v-model="field.type" class="form-select">
                    <option value="text">文本</option>
                    <option value="textarea">长文本</option>
                    <option value="json">JSON</option>
                    <option value="tags">标签</option>
                    <option value="number">数字</option>
                  </select>
                </div>
              </div>
              <div style="display: grid; grid-template-columns: 1fr 1fr auto; gap: 10px;">
                <div>
                  <label class="small-text muted">所属标签</label>
                  <select v-model="field.tab" class="form-select">
                    <option v-for="tab in designerState.config.tabs" :key="tab.id" :value="tab.id">{{ tab.label }}</option>
                  </select>
                </div>
                <div><label class="small-text muted">数据路径</label><input v-model="field.path" class="form-input"></div>
                <div style="display: flex; align-items: end;"><button class="btn-small btn-secondary" style="color: var(--danger);" @click="designerState.config.fields.splice(index, 1)">删除</button></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import { useCharactersPage } from '../composables/useCharactersPage';
import { initThemePage } from '../page_logic/theme-init.module';

const {
  activeTemplate,
  addDesignerField,
  addDesignerTab,
  applyToSession,
  bootstrap,
  clearAllCharacters,
  closeDesigner,
  commitEditorValue,
  createNewCharacter,
  currentCharacter,
  deleteCurrentCharacter,
  deleteCurrentTemplate,
  designerOpen,
  designerState,
  exportAllCharacters,
  exportCurrentCharacter,
  filteredCharacters,
  getEditorValue,
  importFromFiles,
  loadCharacters,
  loading,
  mode,
  openDesigner,
  previewSections,
  saveCharacter,
  saveDesigner,
  searchKeyword,
  selectCharacter,
  selectedCharacterId,
  selectedTemplateId,
  statusText,
  stringifyFieldValue,
  templates,
  updateCharacterMeta,
  updateEditorInput,
} = useCharactersPage();

const editTab = ref('tab_basic');

const currentEditFields = computed(() => {
  const section = previewSections.value.find((item) => item.id === editTab.value) || previewSections.value[0];
  return section?.fields || [];
});

function getFieldValue(field) {
  const keys = String(field.path || '').split('.').filter(Boolean);
  let current = currentCharacter.value;
  for (const key of keys) {
    current = current?.[key];
  }
  return current;
}

function exportCurrentTemplate() {
  if (!activeTemplate.value) return;
  const blob = new Blob([JSON.stringify(activeTemplate.value, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = `${activeTemplate.value.id}.json`;
  anchor.click();
  URL.revokeObjectURL(url);
}

async function onCharacterImport(event) {
  await importFromFiles(event.target.files);
  event.target.value = '';
}

async function onTemplateImport(event) {
  const file = event.target.files?.[0];
  if (!file) return;
  const text = await file.text();
  const payload = JSON.parse(text);
  openDesigner(true);
  Object.assign(designerState, payload);
  event.target.value = '';
}

onMounted(async () => {
  document.title = 'Storyteller | 角色';
  document.body.setAttribute('data-page', 'characters');
  initThemePage();
  await bootstrap();
});
</script>
