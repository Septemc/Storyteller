import { reactive, ref, watch } from 'vue';
import * as settingsApi from '../services/modules/settings';
import { applyThemeSettings, DEFAULT_BACKGROUND, DEFAULT_THEME } from '../page_logic/theme-init.module';

const LLM_DRAFT_STORAGE_KEY = 'storyteller_llm_draft';

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function safeParseJson(text, fallback) {
  try {
    return JSON.parse(text || JSON.stringify(fallback));
  } catch {
    throw new Error('JSON 鏍煎紡鏃犳晥');
  }
}

function defaultLlmDraft() {
  return {
    id: '',
    name: '',
    base_url: '',
    api_key: '',
    stream: true,
    default_model: '',
  };
}

function loadStoredLlmDraft() {
  try {
    const raw = localStorage.getItem(LLM_DRAFT_STORAGE_KEY);
    if (!raw) return defaultLlmDraft();
    return { ...defaultLlmDraft(), ...JSON.parse(raw) };
  } catch {
    return defaultLlmDraft();
  }
}

function persistStoredLlmDraft(draft) {
  try {
    localStorage.setItem(LLM_DRAFT_STORAGE_KEY, JSON.stringify({
      name: draft.name,
      base_url: draft.base_url,
      api_key: draft.api_key,
      stream: draft.stream,
      default_model: draft.default_model,
    }));
  } catch {
  }
}

function clearStoredLlmDraft() {
  try {
    localStorage.removeItem(LLM_DRAFT_STORAGE_KEY);
  } catch {
  }
}

function normalizeGlobalSettings(response) {
  let localTheme = DEFAULT_THEME;
  let localBackground = DEFAULT_BACKGROUND;

  try {
    localTheme = localStorage.getItem('app_theme') || DEFAULT_THEME;
    localBackground = localStorage.getItem('app_bg') || DEFAULT_BACKGROUND;
  } catch {
  }

  const merged = {
    ui: {},
    text: {},
    summary: {},
    variables: {},
    text_opt: {},
    world_evolution: {},
    default_profiles: {},
    worldbook: {},
    ...(response || {}),
  };

  merged.ui = {
    theme: localTheme,
    background: localBackground,
    ...(merged.ui || {}),
  };

  if (localTheme) {
    merged.ui.theme = localTheme;
  }

  if (localBackground) {
    merged.ui.background = localBackground;
  }

  return merged;
}

export function useSettingsPage() {
  const activeTab = ref('tab-ui');
  const statusText = ref('灏辩华');

  const globalSettings = reactive({
    ui: {},
    text: {},
    summary: {},
    variables: {},
    text_opt: {},
    world_evolution: {},
    default_profiles: {},
    worldbook: {},
  });

  const presets = ref([]);
  const selectedPresetId = ref('');
  const presetActiveId = ref('');
  const presetDraft = reactive({
    id: '',
    name: '',
    version: 1,
    rootText: '{}',
    metaText: '{}',
  });

  const regexProfiles = ref([]);
  const selectedRegexId = ref('');
  const activeRegexId = ref('');
  const regexDraft = reactive({
    id: '',
    name: '',
    configText: '{}',
  });

  const llmConfigs = ref([]);
  const activeLlm = ref({ config_id: '', model: '' });
  const selectedLlmId = ref('');
  const llmDraft = reactive(loadStoredLlmDraft());

  async function loadGlobalSettings() {
    const response = await settingsApi.getGlobalSettings();
    Object.assign(globalSettings, normalizeGlobalSettings(response));
    applyThemeSettings(globalSettings.ui);
  }

  async function loadPresets() {
    const response = await settingsApi.listPresets();
    presets.value = response?.presets || [];
    presetActiveId.value = response?.active?.preset_id || '';
    if (!selectedPresetId.value) {
      selectedPresetId.value = presetActiveId.value || presets.value[0]?.id || '';
    }
    if (selectedPresetId.value) {
      await selectPreset(selectedPresetId.value);
    }
  }

  async function selectPreset(presetId) {
    if (!presetId) return;
    selectedPresetId.value = presetId;
    const detail = await settingsApi.getPreset(presetId);
    presetDraft.id = detail.id;
    presetDraft.name = detail.name;
    presetDraft.version = detail.version;
    presetDraft.rootText = JSON.stringify(detail.root || {}, null, 2);
    presetDraft.metaText = JSON.stringify(detail.meta || {}, null, 2);
  }

  async function loadRegexProfiles() {
    regexProfiles.value = await settingsApi.listRegexProfiles();
    const active = await settingsApi.getActiveRegex();
    activeRegexId.value = active?.id || '';
    selectedRegexId.value = selectedRegexId.value || activeRegexId.value || regexProfiles.value[0]?.id || '';
    if (selectedRegexId.value) {
      await selectRegex(selectedRegexId.value);
    }
  }

  async function selectRegex(profileId) {
    if (!profileId) return;
    selectedRegexId.value = profileId;
    const detail = await settingsApi.getRegexProfile(profileId);
    regexDraft.id = detail.id;
    regexDraft.name = detail.name;
    regexDraft.configText = JSON.stringify(detail.config || {}, null, 2);
  }

  async function loadLlmConfigs() {
    const response = await settingsApi.listLlmConfigs();
    llmConfigs.value = response?.configs || [];
    activeLlm.value = response?.active || { config_id: '', model: '' };
    selectedLlmId.value = selectedLlmId.value || activeLlm.value.config_id || llmConfigs.value[0]?.id || '';

    const current = llmConfigs.value.find((item) => item.id === selectedLlmId.value);
    if (current) {
      Object.assign(llmDraft, current);
      persistStoredLlmDraft(llmDraft);
      return;
    }

    Object.assign(llmDraft, loadStoredLlmDraft());
  }

  async function saveGlobalSettings() {
    await settingsApi.putGlobalSettings(clone(globalSettings));
    applyThemeSettings(globalSettings.ui);
    statusText.value = '全局设置已保存';
  }

  async function savePreset() {
    if (!selectedPresetId.value) return;
    await settingsApi.updatePreset(selectedPresetId.value, {
      id: presetDraft.id,
      name: presetDraft.name,
      version: Number(presetDraft.version || 1),
      root: safeParseJson(presetDraft.rootText, {}),
      meta: safeParseJson(presetDraft.metaText, {}),
    });
    await loadPresets();
    statusText.value = '预设已保存';
  }

  async function saveRegex() {
    if (!selectedRegexId.value) return;
    await settingsApi.updateRegexProfile(selectedRegexId.value, {
      name: regexDraft.name,
      config: safeParseJson(regexDraft.configText, {}),
    });
    await loadRegexProfiles();
    statusText.value = '正则配置已保存';
  }

  async function saveApiConfig() {
    const payload = clone(llmDraft);
    if (!payload.name?.trim()) {
      payload.name = '未命名配置';
    }

    payload.name = String(payload.name || '').trim();
    payload.base_url = String(payload.base_url || '').trim();
    payload.api_key = String(payload.api_key || '').trim();
    payload.default_model = String(payload.default_model || '').trim();

    if (!payload.base_url) {
      statusText.value = '请先填写 Base URL';
      return;
    }

    if (!payload.api_key) {
      statusText.value = '请先填写 API Key';
      return;
    }

    if (!payload.default_model) {
      statusText.value = '请先填写默认模型';
      return;
    }

    let targetConfigId = selectedLlmId.value;

    if (!targetConfigId) {
      const created = await settingsApi.createLlmConfig(payload);
      targetConfigId = created?.id || '';
    } else {
      await settingsApi.updateLlmConfig(targetConfigId, payload);
    }

    if (!targetConfigId) {
      await loadLlmConfigs();
      targetConfigId = llmConfigs.value.find((item) => item.name === payload.name && item.base_url === payload.base_url)?.id || '';
    }

    if (!targetConfigId) {
      throw new Error('配置已提交，但未能确认配置 ID');
    }

    selectedLlmId.value = targetConfigId;
    llmDraft.id = targetConfigId;

    await settingsApi.setActiveLlm({
      config_id: targetConfigId,
      model: payload.default_model,
    });
    await loadLlmConfigs();
    activeLlm.value = {
      config_id: targetConfigId,
      model: payload.default_model,
    };
    clearStoredLlmDraft();
    statusText.value = `API 配置已保存并激活：${payload.name} / ${payload.default_model}`;
  }

  const saveHandlers = {
    'tab-ui': saveGlobalSettings,
    'tab-memory': saveGlobalSettings,
    'tab-variables': saveGlobalSettings,
    'tab-evolution': saveGlobalSettings,
    'tab-presets': savePreset,
    'tab-regex': saveRegex,
    'tab-api': saveApiConfig,
  };

  async function saveCurrentTab(tabId = activeTab.value) {
    const handler = saveHandlers[tabId];
    if (!handler) return;
    try {
      await handler();
    } catch (error) {
      statusText.value = error?.message || '保存失败';
      throw error;
    }
  }

  async function resetCurrentTab() {
    if (['tab-ui', 'tab-memory', 'tab-variables', 'tab-evolution'].includes(activeTab.value)) {
      await loadGlobalSettings();
      return;
    }
    if (activeTab.value === 'tab-presets' && selectedPresetId.value) {
      await selectPreset(selectedPresetId.value);
      return;
    }
    if (activeTab.value === 'tab-regex' && selectedRegexId.value) {
      await selectRegex(selectedRegexId.value);
      return;
    }
    if (activeTab.value === 'tab-api') {
      await loadLlmConfigs();
    }
  }

  async function createPreset() {
    const created = await settingsApi.createPreset('新预设');
    selectedPresetId.value = created.id;
    await loadPresets();
  }

  async function deletePreset() {
    if (!selectedPresetId.value) return;
    await settingsApi.deletePreset(selectedPresetId.value);
    selectedPresetId.value = '';
    await loadPresets();
  }

  async function activatePreset() {
    if (!selectedPresetId.value) return;
    await settingsApi.setActivePreset(selectedPresetId.value);
    presetActiveId.value = selectedPresetId.value;
    statusText.value = `宸插簲鐢ㄩ璁?${selectedPresetId.value}`;
  }

  async function createRegex() {
    const created = await settingsApi.createRegexProfile({ name: '新正则' });
    selectedRegexId.value = created.id;
    await loadRegexProfiles();
  }

  async function deleteRegex() {
    if (!selectedRegexId.value) return;
    await settingsApi.deleteRegexProfile(selectedRegexId.value);
    selectedRegexId.value = '';
    await loadRegexProfiles();
  }

  async function activateRegex() {
    if (!selectedRegexId.value) return;
    await settingsApi.setActiveRegex(selectedRegexId.value);
    activeRegexId.value = selectedRegexId.value;
    statusText.value = `宸插簲鐢ㄦ鍒?${selectedRegexId.value}`;
  }

  async function createLlmConfig() {
    Object.assign(llmDraft, defaultLlmDraft(), { name: '新配置' });
    selectedLlmId.value = '';
    persistStoredLlmDraft(llmDraft);
    statusText.value = '请填写配置后点击保存';
  }

  async function deleteLlmConfig() {
    if (!selectedLlmId.value) return;
    await settingsApi.deleteLlmConfig(selectedLlmId.value);
    selectedLlmId.value = '';
    Object.assign(llmDraft, loadStoredLlmDraft());
    await loadLlmConfigs();
  }

  async function bootstrap() {
    await Promise.all([loadGlobalSettings(), loadPresets(), loadRegexProfiles(), loadLlmConfigs()]);
  }

  watch(
    llmDraft,
    () => {
      if (!selectedLlmId.value || llmDraft.name || llmDraft.base_url || llmDraft.api_key || llmDraft.default_model) {
        persistStoredLlmDraft(llmDraft);
      }
    },
    { deep: true },
  );

  return {
    activeLlm,
    activeRegexId,
    activeTab,
    activatePreset,
    activateRegex,
    bootstrap,
    createLlmConfig,
    createPreset,
    createRegex,
    deleteLlmConfig,
    deletePreset,
    deleteRegex,
    globalSettings,
    llmConfigs,
    llmDraft,
    presetActiveId,
    presetDraft,
    presets,
    regexDraft,
    regexProfiles,
    resetCurrentTab,
    saveCurrentTab,
    selectPreset,
    selectRegex,
    selectedLlmId,
    selectedPresetId,
    selectedRegexId,
    statusText,
  };
}




