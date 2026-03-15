import { reactive, ref, watch } from 'vue';
import * as settingsApi from '../services/modules/settings';
import { applyThemeSettings, DEFAULT_BACKGROUND, DEFAULT_THEME } from '../page_logic/theme-init.module';

const LLM_DRAFT_STORAGE_KEY = 'storyteller_llm_draft';
const clone = (value) => JSON.parse(JSON.stringify(value));

function safeParseJson(text, fallback) {
  try {
    return JSON.parse(text || JSON.stringify(fallback));
  } catch {
    throw new Error('JSON 格式无效');
  }
}

function defaultLlmDraft() {
  return { id: '', name: '', base_url: '', api_key: '', stream: true, default_model: '' };
}

function loadStoredLlmDraft() {
  try {
    const raw = localStorage.getItem(LLM_DRAFT_STORAGE_KEY);
    return raw ? { ...defaultLlmDraft(), ...JSON.parse(raw) } : defaultLlmDraft();
  } catch {
    return defaultLlmDraft();
  }
}

function persistStoredLlmDraft(draft) {
  try { localStorage.setItem(LLM_DRAFT_STORAGE_KEY, JSON.stringify(draft)); } catch {}
}

function normalizeGlobalSettings(response) {
  const theme = localStorage.getItem('app_theme') || DEFAULT_THEME;
  const background = localStorage.getItem('app_bg') || DEFAULT_BACKGROUND;
  const merged = { ui: {}, text: {}, summary: {}, variables: {}, text_opt: {}, world_evolution: {}, default_profiles: {}, worldbook: {}, ...(response || {}) };
  merged.ui = { theme, background, ...(merged.ui || {}) };
  return merged;
}

export function useSettingsPage() {
  const activeTab = ref('tab-ui');
  const statusText = ref('就绪');
  const globalSettings = reactive({ ui: {}, text: {}, summary: {}, variables: {}, text_opt: {}, world_evolution: {}, default_profiles: {}, worldbook: {} });
  const presets = ref([]);
  const selectedPresetId = ref('');
  const presetActiveId = ref('');
  const presetDraft = reactive({ id: '', name: '', version: 1, rootText: '{}', metaText: '{}' });
  const regexProfiles = ref([]);
  const selectedRegexId = ref('');
  const activeRegexId = ref('');
  const regexDraft = reactive({ id: '', name: '', configText: '{}' });
  const llmConfigs = ref([]);
  const activeLlm = ref({ config_id: '', model: '' });
  const selectedLlmId = ref('');
  const llmDraft = reactive(loadStoredLlmDraft());
  const llmModels = ref([]);
  const llmModelsLoading = ref(false);

  async function loadGlobalSettings() {
    Object.assign(globalSettings, normalizeGlobalSettings(await settingsApi.getGlobalSettings()));
    applyThemeSettings(globalSettings.ui);
  }

  async function loadPresets() {
    const response = await settingsApi.listPresets();
    presets.value = response?.presets || [];
    presetActiveId.value = response?.active?.preset_id || '';
    selectedPresetId.value = selectedPresetId.value || presetActiveId.value || presets.value[0]?.id || '';
    if (selectedPresetId.value) await selectPreset(selectedPresetId.value);
  }

  async function selectPreset(presetId) {
    if (!presetId) return;
    selectedPresetId.value = presetId;
    const detail = await settingsApi.getPreset(presetId);
    Object.assign(presetDraft, { id: detail.id, name: detail.name, version: detail.version, rootText: JSON.stringify(detail.root || {}, null, 2), metaText: JSON.stringify(detail.meta || {}, null, 2) });
  }

  async function loadRegexProfiles() {
    regexProfiles.value = await settingsApi.listRegexProfiles();
    activeRegexId.value = (await settingsApi.getActiveRegex())?.id || '';
    selectedRegexId.value = selectedRegexId.value || activeRegexId.value || regexProfiles.value[0]?.id || '';
    if (selectedRegexId.value) await selectRegex(selectedRegexId.value);
  }

  async function selectRegex(profileId) {
    if (!profileId) return;
    selectedRegexId.value = profileId;
    const detail = await settingsApi.getRegexProfile(profileId);
    Object.assign(regexDraft, { id: detail.id, name: detail.name, configText: JSON.stringify(detail.config || {}, null, 2) });
  }

  async function loadLlmConfigs() {
    const response = await settingsApi.listLlmConfigs();
    llmConfigs.value = response?.configs || [];
    activeLlm.value = response?.active || { config_id: '', model: '' };
    selectedLlmId.value = selectedLlmId.value || activeLlm.value.config_id || llmConfigs.value[0]?.id || '';
    syncSelectedLlm(selectedLlmId.value);
  }

  function syncSelectedLlm(configId = selectedLlmId.value) {
    const current = llmConfigs.value.find((item) => item.id === configId);
    llmModels.value = [];
    Object.assign(llmDraft, current || loadStoredLlmDraft());
    persistStoredLlmDraft(llmDraft);
  }

  async function fetchLlmModels() {
    llmModelsLoading.value = true;
    try {
      const response = selectedLlmId.value
        ? await settingsApi.getLlmConfigModels(selectedLlmId.value)
        : await settingsApi.listLlmModels({ base_url: llmDraft.base_url, api_key: llmDraft.api_key });
      llmModels.value = response?.models || [];
      if (!llmDraft.default_model && llmModels.value[0]) llmDraft.default_model = llmModels.value[0];
      statusText.value = `已检索到 ${llmModels.value.length} 个可用模型`;
    } finally {
      llmModelsLoading.value = false;
    }
  }

  async function saveGlobalSettings() {
    await settingsApi.putGlobalSettings(clone(globalSettings));
    applyThemeSettings(globalSettings.ui);
    statusText.value = '全局设置已保存';
  }

  async function savePreset() {
    if (!selectedPresetId.value) return;
    await settingsApi.updatePreset(selectedPresetId.value, { id: presetDraft.id, name: presetDraft.name, version: Number(presetDraft.version || 1), root: safeParseJson(presetDraft.rootText, {}), meta: safeParseJson(presetDraft.metaText, {}) });
    await loadPresets();
    statusText.value = '预设已保存';
  }

  async function saveRegex() {
    if (!selectedRegexId.value) return;
    await settingsApi.updateRegexProfile(selectedRegexId.value, { name: regexDraft.name, config: safeParseJson(regexDraft.configText, {}) });
    await loadRegexProfiles();
    statusText.value = '正则配置已保存';
  }

  async function saveApiConfig() {
    const payload = clone(llmDraft);
    payload.name = String(payload.name || '').trim() || '未命名配置';
    payload.base_url = String(payload.base_url || '').trim();
    payload.api_key = String(payload.api_key || '').trim();
    payload.default_model = String(payload.default_model || '').trim();
    if (!payload.base_url) throw new Error('请先填写 Base URL');
    if (!payload.api_key) throw new Error('请先填写 API Key');
    const configId = selectedLlmId.value || (await settingsApi.createLlmConfig(payload))?.id || '';
    if (selectedLlmId.value) await settingsApi.updateLlmConfig(configId, payload);
    selectedLlmId.value = configId;
    llmDraft.id = configId;
    await loadLlmConfigs();
    statusText.value = `API 配置已保存：${payload.name}`;
  }

  async function activateSelectedLlm() {
    await saveApiConfig();
    if (!selectedLlmId.value) return;
    await settingsApi.setActiveLlm({ config_id: selectedLlmId.value, model: llmDraft.default_model });
    activeLlm.value = { config_id: selectedLlmId.value, model: llmDraft.default_model };
    await loadLlmConfigs();
    statusText.value = `已激活 API 配置：${llmDraft.name} / ${llmDraft.default_model || '-'}`;
  }

  async function resetCurrentTab() {
    if (['tab-ui', 'tab-memory', 'tab-variables', 'tab-evolution'].includes(activeTab.value)) return loadGlobalSettings();
    if (activeTab.value === 'tab-presets' && selectedPresetId.value) return selectPreset(selectedPresetId.value);
    if (activeTab.value === 'tab-regex' && selectedRegexId.value) return selectRegex(selectedRegexId.value);
    if (activeTab.value === 'tab-api') return loadLlmConfigs();
  }

  async function saveCurrentTab(tabId = activeTab.value) {
    const saveHandlers = { 'tab-ui': saveGlobalSettings, 'tab-memory': saveGlobalSettings, 'tab-variables': saveGlobalSettings, 'tab-evolution': saveGlobalSettings, 'tab-presets': savePreset, 'tab-regex': saveRegex, 'tab-api': saveApiConfig };
    const handler = saveHandlers[tabId];
    if (!handler) return;
    try {
      await handler();
    } catch (error) {
      statusText.value = error?.message || '保存失败';
      throw error;
    }
  }

  async function createPreset() { selectedPresetId.value = (await settingsApi.createPreset('新预设')).id; await loadPresets(); }
  async function deletePreset() { if (!selectedPresetId.value) return; await settingsApi.deletePreset(selectedPresetId.value); selectedPresetId.value = ''; await loadPresets(); }
  async function activatePreset() { if (!selectedPresetId.value) return; await settingsApi.setActivePreset(selectedPresetId.value); presetActiveId.value = selectedPresetId.value; statusText.value = `已应用预设：${selectedPresetId.value}`; }
  async function createRegex() { selectedRegexId.value = (await settingsApi.createRegexProfile({ name: '新正则' })).id; await loadRegexProfiles(); }
  async function deleteRegex() { if (!selectedRegexId.value) return; await settingsApi.deleteRegexProfile(selectedRegexId.value); selectedRegexId.value = ''; await loadRegexProfiles(); }
  async function activateRegex() { if (!selectedRegexId.value) return; await settingsApi.setActiveRegex(selectedRegexId.value); activeRegexId.value = selectedRegexId.value; statusText.value = `已应用正则：${selectedRegexId.value}`; }
  async function createLlmConfig() { Object.assign(llmDraft, defaultLlmDraft(), { name: '新配置' }); selectedLlmId.value = ''; llmModels.value = []; persistStoredLlmDraft(llmDraft); statusText.value = '请填写 API 配置并保存'; }
  async function deleteLlmConfig() { if (!selectedLlmId.value) return; await settingsApi.deleteLlmConfig(selectedLlmId.value); selectedLlmId.value = ''; Object.assign(llmDraft, loadStoredLlmDraft()); await loadLlmConfigs(); statusText.value = '已删除 API 配置'; }
  async function bootstrap() { await Promise.all([loadGlobalSettings(), loadPresets(), loadRegexProfiles(), loadLlmConfigs()]); }

  watch(selectedLlmId, (value) => syncSelectedLlm(value));
  watch(llmDraft, () => persistStoredLlmDraft(llmDraft), { deep: true });

  return {
    activeLlm, activeRegexId, activeTab, activatePreset, activateRegex, activateSelectedLlm, bootstrap, createLlmConfig,
    createPreset, createRegex, deleteLlmConfig, deletePreset, deleteRegex, fetchLlmModels, globalSettings, llmConfigs,
    llmDraft, llmModels, llmModelsLoading, presetActiveId, presetDraft, presets, regexDraft, regexProfiles,
    resetCurrentTab, saveCurrentTab, selectPreset, selectRegex, selectedLlmId, selectedPresetId, selectedRegexId,
    statusText, syncSelectedLlm,
  };
}
