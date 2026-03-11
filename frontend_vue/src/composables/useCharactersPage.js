import { computed, reactive, ref, watch } from 'vue';
import * as charactersApi from '../services/modules/characters';
import * as storyApi from '../services/modules/story';
import * as templatesApi from '../services/modules/templates';
import { useSessionStore } from '../stores/session';

const DEFAULT_TEMPLATE = {
  id: 'system_default',
  name: '默认模板',
  description: '',
  config: {
    tabs: [
      { id: 'tab_basic', label: '基础信息' },
      { id: 'tab_knowledge', label: '知识设定' },
      { id: 'tab_attributes', label: '属性数值' },
      { id: 'tab_relations', label: '关系网络' },
      { id: 'tab_items', label: '物品清单' },
    ],
    fields: [
      { id: 'f_name', label: '名称', tab: 'tab_basic', path: 'tab_basic.name', type: 'text' },
      { id: 'f_nickname', label: '称号', tab: 'tab_basic', path: 'tab_basic.nickname', type: 'text' },
      { id: 'f_profile', label: '人物简介', tab: 'tab_basic', path: 'tab_basic.profile', type: 'textarea' },
      { id: 'f_knowledge', label: '世界知识', tab: 'tab_knowledge', path: 'tab_knowledge', type: 'json' },
      { id: 'f_attributes', label: '属性', tab: 'tab_attributes', path: 'tab_attributes', type: 'json' },
      { id: 'f_relations', label: '关系', tab: 'tab_relations', path: 'tab_relations', type: 'json' },
      { id: 'f_items', label: '物品', tab: 'tab_items', path: 'tab_items', type: 'json' },
    ],
  },
};

const BUFFERED_FIELD_TYPES = new Set(['json', 'textarea_json']);

function deepClone(value) {
  return JSON.parse(JSON.stringify(value));
}

function normalizeTemplate(template) {
  const next = deepClone(template || DEFAULT_TEMPLATE);
  next.id = next.id || DEFAULT_TEMPLATE.id;
  next.name = next.name || DEFAULT_TEMPLATE.name;
  next.description = next.description || '';
  next.config = next.config || {};
  next.config.tabs = Array.isArray(next.config.tabs) && next.config.tabs.length ? next.config.tabs : deepClone(DEFAULT_TEMPLATE.config.tabs);
  next.config.fields =
    Array.isArray(next.config.fields) && next.config.fields.length ? next.config.fields : deepClone(DEFAULT_TEMPLATE.config.fields);
  return next;
}

function ensureCharacterShape(raw = {}) {
  const character = deepClone(raw || {});
  character.character_id = character.character_id || '';
  character.type = character.type || 'npc';
  character.template_id = character.template_id || DEFAULT_TEMPLATE.id;

  const objectTabs = ['tab_basic', 'tab_knowledge', 'tab_secrets', 'tab_attributes', 'tab_relations', 'tab_fortune'];
  const arrayTabs = ['tab_equipment', 'tab_items', 'tab_skills'];

  objectTabs.forEach((key) => {
    if (!character[key] || typeof character[key] !== 'object' || Array.isArray(character[key])) {
      character[key] = {};
    }
  });
  arrayTabs.forEach((key) => {
    if (!Array.isArray(character[key])) {
      character[key] = [];
    }
  });
  return character;
}

function getByPath(target, path) {
  return String(path || '')
    .split('.')
    .filter(Boolean)
    .reduce((acc, key) => (acc == null ? undefined : acc[key]), target);
}

function setByPath(target, path, value) {
  const keys = String(path || '').split('.').filter(Boolean);
  if (!keys.length) return;

  let current = target;
  keys.slice(0, -1).forEach((key, index) => {
    if (current[key] == null || typeof current[key] !== 'object') {
      const nextKey = keys[index + 1];
      current[key] = /^\d+$/.test(nextKey) ? [] : {};
    }
    current = current[key];
  });
  current[keys[keys.length - 1]] = value;
}

function parseEditorValue(fieldType, value) {
  if (fieldType === 'number') {
    return value === '' ? null : Number(value);
  }
  if (fieldType === 'json' || fieldType === 'textarea_json') {
    return JSON.parse(value || '{}');
  }
  if (fieldType === 'tags') {
    return String(value || '')
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean);
  }
  return value;
}

function stringifyFieldValue(fieldType, value) {
  if (fieldType === 'json' || fieldType === 'textarea_json') {
    return JSON.stringify(value ?? {}, null, 2);
  }
  if (fieldType === 'tags') {
    return Array.isArray(value) ? value.join(', ') : '';
  }
  return value == null ? '' : String(value);
}

function downloadJson(data, fileName) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = fileName;
  anchor.click();
  URL.revokeObjectURL(url);
}

function canConfirm() {
  return typeof window !== 'undefined' && typeof window.confirm === 'function';
}

export function useCharactersPage() {
  const sessionStore = useSessionStore();

  const loading = ref(false);
  const statusText = ref('');
  const searchKeyword = ref('');
  const mode = ref('preview');
  const templates = ref([deepClone(DEFAULT_TEMPLATE)]);
  const selectedTemplateId = ref(DEFAULT_TEMPLATE.id);
  const characters = ref([]);
  const selectedCharacterId = ref('');
  const currentCharacter = ref(ensureCharacterShape());
  const designerOpen = ref(false);
  const designerState = reactive(normalizeTemplate(DEFAULT_TEMPLATE));
  const designerSourceId = ref('');
  const editorValues = reactive({});

  const activeTemplate = computed(() => {
    return templates.value.find((item) => item.id === selectedTemplateId.value) || templates.value[0] || DEFAULT_TEMPLATE;
  });

  const filteredCharacters = computed(() => {
    const keyword = searchKeyword.value.trim().toLowerCase();
    if (!keyword) return characters.value;
    return characters.value.filter((item) => {
      const name = item.basic?.name || item.basic?.f_name || '';
      return `${item.character_id} ${name}`.toLowerCase().includes(keyword);
    });
  });

  const previewSections = computed(() => {
    const template = activeTemplate.value?.config || DEFAULT_TEMPLATE.config;
    const tabs = template.tabs?.length ? template.tabs : DEFAULT_TEMPLATE.config.tabs;
    const fields = template.fields?.length ? template.fields : DEFAULT_TEMPLATE.config.fields;
    return tabs.map((tab) => ({
      ...tab,
      fields: fields.filter((field) => field.tab === tab.id),
    }));
  });

  function syncEditorValues() {
    Object.keys(editorValues).forEach((key) => delete editorValues[key]);
    for (const section of previewSections.value) {
      for (const field of section.fields) {
        editorValues[field.id] = stringifyFieldValue(field.type, getByPath(currentCharacter.value, field.path));
      }
    }
  }

  async function loadTemplates() {
    try {
      const response = await templatesApi.listTemplates();
      const items = (response?.items || []).map(normalizeTemplate);
      templates.value = items.length ? items : [deepClone(DEFAULT_TEMPLATE)];
    } catch {
      templates.value = [deepClone(DEFAULT_TEMPLATE)];
    }

    if (!templates.value.find((item) => item.id === DEFAULT_TEMPLATE.id)) {
      templates.value = [deepClone(DEFAULT_TEMPLATE), ...templates.value];
    }
    if (!templates.value.find((item) => item.id === selectedTemplateId.value)) {
      selectedTemplateId.value = templates.value[0]?.id || DEFAULT_TEMPLATE.id;
    }
  }

  async function loadCharacters() {
    loading.value = true;
    try {
      const response = await charactersApi.listCharacters(searchKeyword.value.trim());
      characters.value = response?.items || [];

      if (selectedCharacterId.value && !characters.value.find((item) => item.character_id === selectedCharacterId.value)) {
        selectedCharacterId.value = '';
      }
    } finally {
      loading.value = false;
    }
  }

  async function selectCharacter(characterId) {
    const detail = await charactersApi.getCharacter(characterId);
    currentCharacter.value = ensureCharacterShape(detail);
    selectedCharacterId.value = currentCharacter.value.character_id;
    selectedTemplateId.value = currentCharacter.value.template_id || DEFAULT_TEMPLATE.id;
    mode.value = 'preview';
    statusText.value = `已加载角色 ${selectedCharacterId.value}`;
    syncEditorValues();
  }

  function createNewCharacter() {
    selectedCharacterId.value = '';
    currentCharacter.value = ensureCharacterShape({
      type: 'npc',
      template_id: selectedTemplateId.value || DEFAULT_TEMPLATE.id,
      tab_basic: {
        name: '新角色',
      },
    });
    mode.value = 'edit';
    statusText.value = '正在创建新角色';
    syncEditorValues();
  }

  async function saveCharacter() {
    const payload = ensureCharacterShape(currentCharacter.value);
    const characterId = payload.character_id.trim();
    if (!characterId) {
      throw new Error('角色 ID 不能为空');
    }

    payload.character_id = characterId;
    payload.template_id = selectedTemplateId.value || DEFAULT_TEMPLATE.id;

    if (selectedCharacterId.value) {
      await charactersApi.updateCharacter(selectedCharacterId.value, payload);
      statusText.value = `已保存角色 ${characterId}`;
    } else {
      await charactersApi.importCharacters(payload);
      statusText.value = `已创建角色 ${characterId}`;
    }

    await loadCharacters();
    await selectCharacter(characterId);
  }

  async function deleteCurrentCharacter() {
    if (!selectedCharacterId.value) return;
    if (canConfirm() && !window.confirm(`确认删除角色 ${selectedCharacterId.value} 吗？`)) {
      return;
    }

    await charactersApi.deleteCharacter(selectedCharacterId.value);
    statusText.value = `已删除角色 ${selectedCharacterId.value}`;
    selectedCharacterId.value = '';
    currentCharacter.value = ensureCharacterShape({ template_id: selectedTemplateId.value });
    await loadCharacters();
    syncEditorValues();
  }

  async function clearAllCharacters() {
    if (canConfirm() && !window.confirm('确认清空全部角色吗？')) {
      return;
    }

    await charactersApi.clearAllCharacters();
    selectedCharacterId.value = '';
    currentCharacter.value = ensureCharacterShape({ template_id: selectedTemplateId.value });
    await loadCharacters();
    statusText.value = '已清空全部角色';
    syncEditorValues();
  }

  async function applyToSession() {
    if (!currentCharacter.value.character_id) return;
    sessionStore.bootstrap();
    await storyApi.updateSessionContext({
      session_id: sessionStore.currentSessionId,
      main_character_id: currentCharacter.value.character_id,
    });
    statusText.value = `已应用到存档 ${sessionStore.currentSessionId}`;
  }

  function updateField(field, rawValue) {
    const next = deepClone(currentCharacter.value);
    const parsed = parseEditorValue(field.type, rawValue);
    setByPath(next, field.path, parsed);
    currentCharacter.value = ensureCharacterShape(next);
    editorValues[field.id] = stringifyFieldValue(field.type, getByPath(currentCharacter.value, field.path));
  }

  function getEditorValue(field) {
    if (!(field.id in editorValues)) {
      editorValues[field.id] = stringifyFieldValue(field.type, getByPath(currentCharacter.value, field.path));
    }
    return editorValues[field.id];
  }

  function updateEditorInput(field, rawValue) {
    editorValues[field.id] = rawValue;
    if (!BUFFERED_FIELD_TYPES.has(field.type)) {
      updateField(field, rawValue);
    }
  }

  function commitEditorValue(field) {
    if (!BUFFERED_FIELD_TYPES.has(field.type)) {
      return;
    }
    updateField(field, editorValues[field.id] ?? '');
  }

  function openDesigner(createBlank = false) {
    const source = createBlank
      ? {
          id: `tpl_${Date.now()}`,
          name: '新模板',
          description: '',
          config: deepClone(DEFAULT_TEMPLATE.config),
        }
      : normalizeTemplate(activeTemplate.value || DEFAULT_TEMPLATE);

    designerSourceId.value = createBlank ? '' : source.id;
    Object.assign(designerState, normalizeTemplate(source));
    designerOpen.value = true;
  }

  function closeDesigner() {
    designerOpen.value = false;
  }

  function addDesignerTab() {
    designerState.config.tabs.push({
      id: `tab_${Date.now()}`,
      label: '新标签',
    });
  }

  function addDesignerField() {
    designerState.config.fields.push({
      id: `field_${Date.now()}`,
      label: '新字段',
      tab: designerState.config.tabs[0]?.id || 'tab_basic',
      path: 'tab_basic.new_field',
      type: 'text',
    });
  }

  async function saveDesigner() {
    const payload = normalizeTemplate({
      id: designerState.id,
      name: designerState.name,
      description: designerState.description || '',
      config: designerState.config,
    });

    if (!payload.id.trim()) {
      throw new Error('模板 ID 不能为空');
    }

    if (designerSourceId.value) {
      await templatesApi.updateTemplate(designerSourceId.value, payload);
    } else {
      await templatesApi.createTemplate(payload);
    }
    await loadTemplates();
    selectedTemplateId.value = payload.id;
    closeDesigner();
  }

  async function deleteCurrentTemplate() {
    if (!selectedTemplateId.value || selectedTemplateId.value === DEFAULT_TEMPLATE.id) return;
    if (canConfirm() && !window.confirm(`确认删除模板 ${selectedTemplateId.value} 吗？`)) {
      return;
    }

    await templatesApi.deleteTemplate(selectedTemplateId.value);
    await loadTemplates();
    selectedTemplateId.value = DEFAULT_TEMPLATE.id;
  }

  function exportCurrentCharacter() {
    if (!currentCharacter.value.character_id) return;
    downloadJson(currentCharacter.value, `${currentCharacter.value.character_id}.json`);
  }

  async function exportAllCharacters() {
    const data = await charactersApi.exportAllCharacters();
    downloadJson(data, 'characters.json');
  }

  async function importFromFiles(fileList) {
    const files = Array.from(fileList || []);
    for (const file of files) {
      const text = await file.text();
      const payload = JSON.parse(text);
      await charactersApi.importCharacters(payload);
    }
    await loadCharacters();
    statusText.value = '导入完成';
  }

  function updateCharacterMeta(key, value) {
    currentCharacter.value = ensureCharacterShape({
      ...currentCharacter.value,
      [key]: value,
    });
    if (key === 'template_id') {
      selectedTemplateId.value = value || DEFAULT_TEMPLATE.id;
    }
    syncEditorValues();
  }

  async function bootstrap() {
    await Promise.all([loadTemplates(), loadCharacters()]);
    if (characters.value[0]) {
      await selectCharacter(characters.value[0].character_id);
    } else {
      createNewCharacter();
    }
  }

  watch(selectedTemplateId, (templateId) => {
    if (!selectedCharacterId.value && currentCharacter.value.template_id !== templateId) {
      updateCharacterMeta('template_id', templateId);
    }
  });

  watch(previewSections, syncEditorValues, { deep: true });

  return {
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
    updateField,
  };
}
