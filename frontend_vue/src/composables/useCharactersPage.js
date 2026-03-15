import { computed, reactive, ref, watch } from 'vue';
import * as charactersApi from '../services/modules/characters';
import * as storyApi from '../services/modules/story';
import * as templatesApi from '../services/modules/templates';
import { useSaveManagerStore } from '../stores/saveManager';
import { useSessionStore } from '../stores/session';
import {
  confirmAction,
  createEmptyCharacter,
  createTemplateId,
  deepClone,
  downloadJson,
  ensureCharacterShape,
  getByPath,
  isBufferedField,
  normalizeTemplate,
  parseFieldValue,
  safeParseJson,
  setByPath,
  stringifyFieldValue,
} from './characters/utils';

export function useCharactersPage() {
  const sessionStore = useSessionStore();
  const saveStore = useSaveManagerStore();
  const templates = ref([]);
  const selectedTemplateId = ref('');
  const characters = ref([]);
  const selectedCharacterId = ref('');
  const currentCharacter = ref(createEmptyCharacter(''));
  const searchKeyword = ref('');
  const mode = ref('preview');
  const audienceMode = ref(saveStore.developerMode ? 'developer' : 'player');
  const editScope = ref('full');
  const loading = ref(false);
  const statusText = ref('');
  const fieldInputs = reactive({});
  const templateEditorOpen = ref(false);
  const templateEditorCreateMode = ref(false);
  const templateEditorId = ref('');
  const templateEditorName = ref('');
  const templateEditorConfig = ref('{}');
  const sessionId = computed(() => sessionStore.currentSessionId || '');
  const activeTemplateId = computed(() => templates.value.find((item) => item.is_active)?.id || '');
  const selectedTemplate = computed(() => templates.value.find((item) => item.id === selectedTemplateId.value) || null);
  const activeTemplate = computed(() => templates.value.find((item) => item.id === activeTemplateId.value) || null);
  const previewSections = computed(() => {
    const config = selectedTemplate.value?.config || {};
    const tabs = Array.isArray(config.tabs) ? config.tabs : [];
    const fields = Array.isArray(config.fields) ? config.fields : [];
    return tabs.map((tab) => ({ ...tab, fields: fields.filter((field) => field.tab === tab.id) }));
  });
  const displayProfile = computed(() => audienceMode.value === 'developer' ? currentCharacter.value.full_profile : currentCharacter.value.player_profile);
  const editableProfile = computed(() => editScope.value === 'full' ? currentCharacter.value.full_profile : currentCharacter.value.player_profile);
  const filteredCharacters = computed(() => {
    const keyword = searchKeyword.value.trim().toLowerCase();
    if (!keyword) return characters.value;
    return characters.value.filter((item) => `${item.character_id} ${item.display_name} ${item.developer_name || ''}`.toLowerCase().includes(keyword));
  });
  const templateStatusText = computed(() => {
    if (!templates.value.length) return '当前无角色模板';
    if (!activeTemplate.value) return '当前未应用角色模板';
    return `当前应用 ${activeTemplate.value.name}`;
  });

  function setStatus(text) {
    statusText.value = text;
  }

  function resetFieldInputs() {
    Object.keys(fieldInputs).forEach((key) => delete fieldInputs[key]);
  }

  function resetCurrentCharacter() {
    currentCharacter.value = createEmptyCharacter(selectedTemplateId.value);
  }

  async function loadTemplates() {
    if (!sessionId.value) return;
    const response = await templatesApi.listTemplates(sessionId.value).catch(() => ({ items: [] }));
    templates.value = (response?.items || []).map(normalizeTemplate);
    const nextActive = templates.value.find((item) => item.is_active)?.id;
    if (nextActive) selectedTemplateId.value = nextActive;
    else if (!templates.value.find((item) => item.id === selectedTemplateId.value)) selectedTemplateId.value = templates.value[0]?.id || '';
    if (!selectedCharacterId.value) resetCurrentCharacter();
  }

  async function loadCharacters() {
    if (!sessionId.value) return;
    loading.value = true;
    try {
      const response = await charactersApi.listCharacters(sessionId.value, searchKeyword.value.trim());
      characters.value = response?.items || [];
    } finally {
      loading.value = false;
    }
  }

  async function runSearch() {
    await loadCharacters();
  }

  async function selectCharacter(characterId) {
    if (!sessionId.value) return;
    const detail = await charactersApi.getCharacter(sessionId.value, characterId);
    currentCharacter.value = ensureCharacterShape(detail, selectedTemplateId.value);
    selectedCharacterId.value = currentCharacter.value.character_id;
    selectedTemplateId.value = currentCharacter.value.template_id || selectedTemplateId.value;
    mode.value = 'preview';
    resetFieldInputs();
    setStatus(`已加载角色 ${selectedCharacterId.value}`);
  }

  function createNewCharacter() {
    selectedCharacterId.value = '';
    resetCurrentCharacter();
    mode.value = 'edit';
    resetFieldInputs();
    setStatus(selectedTemplateId.value ? '正在创建新角色' : '当前存档尚未应用角色模板');
  }

  function getFieldValue(field, profile = displayProfile.value) {
    return getByPath(profile, field.path);
  }

  function getEditorValue(field) {
    const key = `${editScope.value}:${field.id}`;
    if (!(key in fieldInputs)) fieldInputs[key] = stringifyFieldValue(field.type, getFieldValue(field, editableProfile.value));
    return fieldInputs[key];
  }

  function updateEditorInput(field, rawValue) {
    const key = `${editScope.value}:${field.id}`;
    fieldInputs[key] = rawValue;
    if (!isBufferedField(field.type)) updateField(field, rawValue);
  }

  function updateField(field, rawValue) {
    const next = deepClone(currentCharacter.value);
    const profileKey = editScope.value === 'full' ? 'full_profile' : 'player_profile';
    setByPath(next[profileKey], field.path, parseFieldValue(field.type, rawValue));
    currentCharacter.value = ensureCharacterShape(next, selectedTemplateId.value);
  }

  function commitEditorValue(field) {
    const key = `${editScope.value}:${field.id}`;
    if (isBufferedField(field.type)) updateField(field, fieldInputs[key] ?? '');
  }

  function updateCharacterMeta(key, value) {
    currentCharacter.value = ensureCharacterShape({ ...currentCharacter.value, [key]: value }, selectedTemplateId.value);
  }

  async function saveCharacter() {
    if (!selectedTemplateId.value) throw new Error('当前存档尚未应用角色模板');
    const payload = ensureCharacterShape(currentCharacter.value, selectedTemplateId.value);
    if (!payload.character_id.trim()) throw new Error('角色 ID 不能为空');
    payload.template_id = selectedTemplateId.value;
    payload.session_id = sessionId.value;
    if (selectedCharacterId.value) await charactersApi.updateCharacter(selectedCharacterId.value, payload);
    else await charactersApi.importCharacters(payload);
    await loadCharacters();
    await selectCharacter(payload.character_id);
    setStatus(`已保存角色 ${payload.character_id}`);
  }

  async function deleteCurrentCharacter() {
    if (!selectedCharacterId.value || !confirmAction(`确认删除角色 ${selectedCharacterId.value} 吗？`)) return;
    await charactersApi.deleteCharacter(sessionId.value, selectedCharacterId.value);
    selectedCharacterId.value = '';
    resetCurrentCharacter();
    await loadCharacters();
    setStatus('已删除当前角色');
  }

  async function clearAllCharacters() {
    if (!sessionId.value || !confirmAction('确认删除当前会话下的全部角色吗？')) return;
    await charactersApi.clearAllCharacters(sessionId.value);
    selectedCharacterId.value = '';
    resetCurrentCharacter();
    await loadCharacters();
    setStatus('已删除全部角色');
  }

  async function applyToSession() {
    sessionStore.bootstrap();
    await storyApi.updateSessionContext({ session_id: sessionStore.currentSessionId, main_character_id: currentCharacter.value.character_id });
    setStatus(`已将 ${currentCharacter.value.character_id} 设为当前主角`);
  }

  async function importFromFiles(fileList, kind = 'character') {
    for (const file of Array.from(fileList || [])) {
      const payload = JSON.parse(await file.text());
      if (kind === 'template') {
        const template = { ...normalizeTemplate(payload), session_id: sessionId.value, is_active: false };
        try {
          await templatesApi.updateTemplate(template.id, template);
        } catch {
          await templatesApi.createTemplate(template);
        }
      } else {
        await charactersApi.importCharacters({ ...payload, session_id: payload.session_id || sessionId.value });
      }
    }
    if (kind === 'template') await loadTemplates();
    else await loadCharacters();
    setStatus(kind === 'template' ? '已导入角色模板' : '已导入角色数据');
  }

  function exportCurrentCharacter() {
    if (currentCharacter.value.character_id) downloadJson(currentCharacter.value, `${currentCharacter.value.character_id}.json`);
  }

  async function exportAllCharacters() {
    downloadJson(await charactersApi.exportAllCharacters(sessionId.value), 'characters.json');
  }

  function exportSelectedTemplate() {
    if (selectedTemplate.value) downloadJson(selectedTemplate.value, `${selectedTemplate.value.id}.json`);
  }

  async function activateSelectedTemplate() {
    if (!selectedTemplateId.value || !sessionId.value) return;
    await templatesApi.activateTemplate(sessionId.value, selectedTemplateId.value);
    await loadTemplates();
    setStatus(`已应用角色模板 ${selectedTemplateId.value}`);
  }

  function openTemplateEditor() {
    if (!selectedTemplate.value) return;
    templateEditorCreateMode.value = false;
    templateEditorId.value = selectedTemplate.value.id;
    templateEditorName.value = selectedTemplate.value.name;
    templateEditorConfig.value = JSON.stringify(selectedTemplate.value.config || {}, null, 2);
    templateEditorOpen.value = true;
  }

  function openTemplateCreator() {
    templateEditorCreateMode.value = true;
    templateEditorId.value = createTemplateId();
    templateEditorName.value = '新模板';
    templateEditorConfig.value = JSON.stringify({ tabs: [], fields: [] }, null, 2);
    templateEditorOpen.value = true;
  }

  function closeTemplateEditor() {
    templateEditorOpen.value = false;
  }

  async function saveTemplateEditor() {
    const templateId = templateEditorId.value.trim();
    if (!templateId) throw new Error('模板 ID 不能为空');
    const payload = {
      session_id: sessionId.value,
      id: templateId,
      template_name: templateEditorName.value.trim() || '未命名模板',
      template_json: safeParseJson(templateEditorConfig.value, selectedTemplate.value?.config || { tabs: [], fields: [] }),
    };
    if (templateEditorCreateMode.value) {
      await templatesApi.createTemplate(payload);
      selectedTemplateId.value = templateId;
      setStatus(`已创建模板 ${templateId}`);
    } else if (selectedTemplate.value) {
      await templatesApi.updateTemplate(selectedTemplate.value.id, payload);
      setStatus(`已更新模板 ${selectedTemplate.value.id}`);
    }
    templateEditorOpen.value = false;
    await loadTemplates();
  }

  async function deleteSelectedTemplate() {
    if (!selectedTemplate.value || !confirmAction(`确认删除模板 ${selectedTemplate.value.name} 吗？`)) return;
    await templatesApi.deleteTemplate(sessionId.value, selectedTemplate.value.id);
    if (selectedTemplateId.value === selectedTemplate.value.id) selectedTemplateId.value = '';
    await loadTemplates();
    resetCurrentCharacter();
    setStatus('已删除角色模板');
  }

  async function bootstrap() {
    sessionStore.bootstrap();
    await Promise.all([loadTemplates(), loadCharacters()]);
    if (characters.value[0]?.character_id) await selectCharacter(characters.value[0].character_id);
    else createNewCharacter();
  }

  watch(selectedTemplateId, (value) => {
    if (!selectedCharacterId.value) currentCharacter.value = ensureCharacterShape({ ...currentCharacter.value, template_id: value }, value);
  });

  return {
    activateSelectedTemplate,
    applyToSession,
    audienceMode,
    bootstrap,
    clearAllCharacters,
    closeTemplateEditor,
    commitEditorValue,
    createNewCharacter,
    currentCharacter,
    deleteCurrentCharacter,
    deleteSelectedTemplate,
    editScope,
    exportAllCharacters,
    exportCurrentCharacter,
    exportSelectedTemplate,
    filteredCharacters,
    getEditorValue,
    getFieldValue,
    importFromFiles,
    loading,
    mode,
    openTemplateCreator,
    openTemplateEditor,
    previewSections,
    runSearch,
    saveCharacter,
    saveTemplateEditor,
    searchKeyword,
    selectCharacter,
    selectedCharacterId,
    selectedTemplateId,
    statusText,
    templateEditorConfig,
    templateEditorCreateMode,
    templateEditorId,
    templateEditorName,
    templateEditorOpen,
    templateStatusText,
    templates,
    updateCharacterMeta,
    updateEditorInput,
  };
}
