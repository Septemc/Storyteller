export const settingsTabs = [
  { id: 'tab-ui', label: '界面与显示' },
  { id: 'tab-memory', label: '摘要与记忆' },
  { id: 'tab-variables', label: '变量思考' },
  { id: 'tab-evolution', label: '正文与演化' },
  { id: 'tab-presets', label: '预设管理' },
  { id: 'tab-regex', label: '正则管理' },
  { id: 'tab-api', label: 'API 配置' },
];

export const jsonText = (value) => JSON.stringify(value || {}, null, 2);

export function assignJson(target, key, text) {
  try { target[key] = JSON.parse(text || '{}'); } catch {}
}
