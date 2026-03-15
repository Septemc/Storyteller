export const DEFAULT_TEMPLATE = {
  id: '',
  name: '未命名模板',
  description: '',
  config: {
    tabs: [
      { id: 'tab_basic', label: '基础信息' },
      { id: 'tab_knowledge', label: '见闻设定' },
      { id: 'tab_secrets', label: '秘密过往' },
      { id: 'tab_attributes', label: '数值属性' },
      { id: 'tab_relations', label: '人际关系' },
      { id: 'tab_items', label: '物品与能力' },
    ],
    fields: [
      { id: 'f_name', label: '姓名', path: 'tab_basic.f_name', tab: 'tab_basic', type: 'text', desc: '角色姓名' },
      { id: 'f_identity', label: '身份', path: 'tab_basic.f_identity', tab: 'tab_basic', type: 'text', desc: '社会身份' },
      { id: 'f_desc', label: '简介', path: 'tab_knowledge.f_desc', tab: 'tab_knowledge', type: 'textarea', desc: '角色简介' },
    ],
  },
};

const BUFFERED_TYPES = new Set(['json', 'textarea_json']);
const TEMPLATE_TYPES = new Set(['text', 'textarea', 'object_list', 'stats_panel', 'json', 'relation_graph']);

export function deepClone(value) {
  return JSON.parse(JSON.stringify(value));
}

export function normalizeTemplate(template) {
  const next = deepClone(template || DEFAULT_TEMPLATE);
  const config =
    next.config && typeof next.config === 'object'
      ? next.config
      : next.template_json && typeof next.template_json === 'object'
        ? next.template_json
        : { tabs: next.tabs || [], fields: next.fields || [] };
  next.id = next.id || next.template_id || DEFAULT_TEMPLATE.id;
  next.name = next.name || next.template_name || DEFAULT_TEMPLATE.name;
  next.description = next.description || '';
  next.session_id = next.session_id || '';
  next.is_active = Boolean(next.is_active);
  next.config = {
    tabs: Array.isArray(config.tabs) && config.tabs.length ? config.tabs : deepClone(DEFAULT_TEMPLATE.config.tabs),
    fields: normalizeFields(Array.isArray(config.fields) && config.fields.length ? config.fields : deepClone(DEFAULT_TEMPLATE.config.fields)),
  };
  return next;
}

export function normalizeFields(fields) {
  return (fields || []).map((field) => ({
    ...field,
    type: TEMPLATE_TYPES.has(field?.type) ? field.type : 'json',
  }));
}

export function createEmptyCharacter(templateId = DEFAULT_TEMPLATE.id) {
  return {
    session_id: '',
    character_id: '',
    template_id: templateId,
    type: 'npc',
    source_type: 'manual',
    status: 'active',
    story_id: null,
    full_profile: { character_id: '', template_id: templateId, type: 'npc' },
    player_profile: { character_id: '', template_id: templateId, type: 'npc' },
    meta: {},
  };
}

export function ensureCharacterShape(raw, templateId = DEFAULT_TEMPLATE.id) {
  const character = deepClone(raw || createEmptyCharacter(templateId));
  character.character_id = character.character_id || '';
  character.session_id = character.session_id || '';
  character.template_id = character.template_id || templateId;
  character.type = character.type || 'npc';
  character.source_type = character.source_type || 'manual';
  character.status = character.status || 'active';
  character.full_profile = normalizeProfile(character.full_profile, character);
  character.player_profile = normalizeProfile(character.player_profile, character);
  return character;
}

export function normalizeProfile(profile, character) {
  const next = profile && typeof profile === 'object' ? deepClone(profile) : {};
  next.character_id = next.character_id || character.character_id || '';
  next.template_id = next.template_id || character.template_id;
  next.type = next.type || character.type || 'npc';
  return next;
}

export function getByPath(target, path) {
  return String(path || '')
    .split('.')
    .filter(Boolean)
    .reduce((acc, key) => (acc && typeof acc === 'object' ? acc[key] : undefined), target);
}

export function setByPath(target, path, value) {
  const keys = String(path || '').split('.').filter(Boolean);
  let current = target;
  keys.slice(0, -1).forEach((key) => {
    if (!current[key] || typeof current[key] !== 'object' || Array.isArray(current[key])) current[key] = {};
    current = current[key];
  });
  if (keys.length) current[keys[keys.length - 1]] = value;
}

export function parseFieldValue(type, value) {
  if (type === 'number') return value === '' ? null : Number(value);
  if (type === 'json' || type === 'textarea_json') return JSON.parse(value || '{}');
  if (type === 'tags') return String(value || '').split(',').map((item) => item.trim()).filter(Boolean);
  return value;
}

export function stringifyFieldValue(type, value) {
  if (type === 'json' || type === 'textarea_json') return JSON.stringify(value ?? {}, null, 2);
  if (type === 'tags') return Array.isArray(value) ? value.join(', ') : '';
  if (Array.isArray(value) || (value && typeof value === 'object')) return JSON.stringify(value, null, 2);
  return value == null ? '' : String(value);
}

export function isBufferedField(type) {
  return BUFFERED_TYPES.has(type);
}

export function downloadJson(data, fileName) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = fileName;
  anchor.click();
  URL.revokeObjectURL(url);
}

export function safeParseJson(value, fallback = {}) {
  try {
    return JSON.parse(String(value || '').trim() || '{}');
  } catch {
    return fallback;
  }
}

export function confirmAction(message) {
  return typeof window === 'undefined' || typeof window.confirm !== 'function' ? true : window.confirm(message);
}

export function createTemplateId() {
  return `tpl_${Date.now().toString(36)}`;
}
