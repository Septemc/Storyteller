<template>
  <main class="two-column-layout characters-page">
    <CharactersSidebar
      :audience-mode="audienceMode"
      :filtered-characters="filteredCharacters"
      :loading="loading"
      :search-keyword="searchKeyword"
      :selected-character-id="selectedCharacterId"
      :selected-template-id="selectedTemplateId"
      :template-status-text="templateStatusText"
      :templates="templates"
      @activate-template="activateSelectedTemplate"
      @clear-characters="clearAllCharacters"
      @create-character="createNewCharacter"
      @create-template="openTemplateCreator"
      @delete-template="deleteSelectedTemplate"
      @edit-template="openTemplateEditor"
      @export-characters="exportAllCharacters"
      @export-template="exportSelectedTemplate"
      @import-character="importCharacters"
      @import-template="importTemplates"
      @search="runSearch"
      @select-character="selectCharacter"
      @update:search-keyword="searchKeyword = $event"
      @update:selected-template-id="selectedTemplateId = $event"
    />

    <section class="right-panel detail-panel">
      <div class="panel-header">
        <div class="panel-title">{{ currentCharacter.character_id || '角色详情' }}</div>
        <div class="panel-header-right header-actions">
          <div class="toggle-group"><button :class="['btn-small', { active: audienceMode === 'player' }]" @click="audienceMode = 'player'">玩家模式</button><button :class="['btn-small', { active: audienceMode === 'developer' }]" @click="audienceMode = 'developer'">开发者模式</button></div>
          <div class="toggle-group"><button :class="['btn-small', { active: mode === 'preview' }]" @click="mode = 'preview'">预览</button><button :class="['btn-small', { active: mode === 'edit' }]" @click="mode = 'edit'">编辑</button></div>
          <button class="btn-secondary btn-small" @click="applyToSession">设为当前主角</button>
          <button class="btn-secondary btn-small" @click="exportCurrentCharacter">导出当前</button>
          <button class="btn-secondary btn-small danger-btn" @click="deleteCurrentCharacter">删除角色</button>
          <button class="btn-primary btn-small" :disabled="!selectedTemplateId" @click="saveCharacter">保存</button>
        </div>
      </div>

      <div class="settings-section detail-scroll">
        <div class="meta-grid">
          <div class="field-block"><label class="form-label">角色 ID</label><input :value="currentCharacter.character_id" class="form-input" :disabled="mode !== 'edit'" @input="updateCharacterMeta('character_id', $event.target.value)"></div>
          <div class="field-block"><label class="form-label">模板 ID</label><input :value="currentCharacter.template_id" class="form-input" disabled></div>
          <div class="field-block"><label class="form-label">角色类型</label><select :value="currentCharacter.type" class="form-select" :disabled="mode !== 'edit'" @change="updateCharacterMeta('type', $event.target.value)"><option value="npc">NPC</option><option value="major">重要角色</option><option value="protagonist">主角</option><option value="antagonist">反派</option></select></div>
          <div class="field-block"><label class="form-label">状态</label><select :value="currentCharacter.status" class="form-select" :disabled="mode !== 'edit'" @change="updateCharacterMeta('status', $event.target.value)"><option value="active">active</option><option value="死亡">死亡</option><option value="退场">退场</option><option value="失踪">失踪</option></select></div>
        </div>

        <div v-if="mode === 'edit'" class="toggle-group"><button :class="['btn-small', { active: editScope === 'full' }]" @click="editScope = 'full'">编辑完整信息</button><button :class="['btn-small', { active: editScope === 'player' }]" @click="editScope = 'player'">编辑玩家视角</button></div>

        <div v-for="section in previewSections" :key="section.id" class="char-card">
          <div class="panel-title section-title">{{ section.label }}</div>
          <div class="half-grid fields-grid">
            <CharacterFieldView
              v-for="field in section.fields"
              :key="field.id"
              :editable="mode === 'edit'"
              :editor-value="getEditorValue(field)"
              :field="field"
              :player-mode="audienceMode === 'player'"
              :value="getFieldValue(field)"
              @commit="commitEditorValue(field)"
              @update="updateEditorInput(field, $event)"
            />
          </div>
        </div>

        <div class="small-text muted">{{ statusText }}</div>
      </div>
    </section>

    <TemplateEditorModal
      :open="templateEditorOpen"
      :create-mode="templateEditorCreateMode"
      :template-id="templateEditorId"
      :name="templateEditorName"
      :config="templateEditorConfig"
      @close="closeTemplateEditor"
      @save="saveTemplateEditor"
      @update:config="templateEditorConfig = $event"
      @update:name="templateEditorName = $event"
      @update:template-id="templateEditorId = $event"
    />
  </main>
</template>

<script setup>
import { onMounted } from 'vue';
import CharacterFieldView from '../components/characters/CharacterFieldView.vue';
import CharactersSidebar from '../components/characters/CharactersSidebar.vue';
import TemplateEditorModal from '../components/characters/TemplateEditorModal.vue';
import { useCharactersPage } from '../composables/useCharactersPage';
import { initThemePage } from '../page_logic/theme-init.module';

const state = useCharactersPage();
const { activateSelectedTemplate, applyToSession, audienceMode, bootstrap, clearAllCharacters, closeTemplateEditor, commitEditorValue, createNewCharacter, currentCharacter, deleteCurrentCharacter, deleteSelectedTemplate, editScope, exportAllCharacters, exportCurrentCharacter, exportSelectedTemplate, getEditorValue, getFieldValue, loading, mode, openTemplateCreator, openTemplateEditor, previewSections, runSearch, saveCharacter, saveTemplateEditor, searchKeyword, selectCharacter, selectedCharacterId, selectedTemplateId, statusText, templateEditorConfig, templateEditorCreateMode, templateEditorId, templateEditorName, templateEditorOpen, templateStatusText, templates, updateCharacterMeta, updateEditorInput, importFromFiles, filteredCharacters } = state;
async function importCharacters(files) { await importFromFiles(files, 'character'); }
async function importTemplates(files) { await importFromFiles(files, 'template'); }

onMounted(async () => {
  document.title = 'Storyteller | 角色';
  document.body.setAttribute('data-page', 'characters');
  initThemePage();
  await bootstrap();
});
</script>

<style scoped>
.characters-page { height: calc(100vh - 112px); min-height: 720px; }
.detail-panel { overflow: hidden; }
.detail-scroll { height: calc(100% - 76px); display: flex; flex-direction: column; gap: 14px; overflow: auto; }
.header-actions { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.meta-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }
.fields-grid { align-items: start; }
.section-title { margin-bottom: 12px; }
.danger-btn { color: var(--danger); }
@media (max-width: 980px) { .characters-page { height: auto; min-height: 0; } .meta-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
</style>
