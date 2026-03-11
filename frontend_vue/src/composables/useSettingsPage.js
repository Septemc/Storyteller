import { reactive, ref } from 'vue';
import * as settingsApi from '../services/modules/settings';

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function safeParseJson(text, fallback) {
  try {
    return JSON.parse(text || JSON.stringify(fallback));
  } catch {
    throw new Error('JSON 格式无效');
  }
}

export function useSettingsPage() {
  const activeTab = ref('tab-ui');
  const statusText = ref('就绪');

  const globalSettings = reactive({
    ui: {},
    text: {},
    summary: {},
    variables: {},
    text_opt: {},
    world_evolution: {},
    default_profiles: {},
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
  const llmDraft = reactive({
    id: '',
    name: '',
    base_url: '',
    api_key: '',
    stream: true,
    default_model: '',
  });

  async function loadGlobalSettings() {
    const response = await settingsApi.getGlobalSettings();
    Object.assign(globalSettings, {
      ui: {},
      text: {},
      summary: {},
      variables: {},
      text_opt: {},
      world_evolution: {},
      default_profiles: {},
      ...(response || {}),
    });
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
    }
  }

  async function saveGlobalSettings() {
    await settingsApi.putGlobalSettings(clone(globalSettings));
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
    if (!selectedLlmId.value) return;
    await settingsApi.updateLlmConfig(selectedLlmId.value, clone(llmDraft));
    await settingsApi.setActiveLlm({
      config_id: selectedLlmId.value,
      model: llmDraft.default_model,
    });
    await loadLlmConfigs();
    statusText.value = 'API 配置已保存';
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
    await handler();
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
    statusText.value = `已应用预设 ${selectedPresetId.value}`;
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
    statusText.value = `已应用正则 ${selectedRegexId.value}`;
  }

  async function createLlmConfig() {
    const created = await settingsApi.createLlmConfig({
      name: '新配置',
      base_url: '',
      api_key: '',
      stream: true,
      default_model: '',
    });
    selectedLlmId.value = created.id;
    await loadLlmConfigs();
  }

  async function deleteLlmConfig() {
    if (!selectedLlmId.value) return;
    await settingsApi.deleteLlmConfig(selectedLlmId.value);
    selectedLlmId.value = '';
    await loadLlmConfigs();
  }

  async function bootstrap() {
    await Promise.all([loadGlobalSettings(), loadPresets(), loadRegexProfiles(), loadLlmConfigs()]);
  }

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
