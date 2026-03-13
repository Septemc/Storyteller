import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useSettingsPage } from '../useSettingsPage';

vi.mock('../../services/modules/settings', () => ({
  getGlobalSettings: vi.fn(),
  putGlobalSettings: vi.fn(),
  listPresets: vi.fn(),
  getPreset: vi.fn(),
  createPreset: vi.fn(),
  updatePreset: vi.fn(),
  deletePreset: vi.fn(),
  setActivePreset: vi.fn(),
  listLlmConfigs: vi.fn(),
  createLlmConfig: vi.fn(),
  updateLlmConfig: vi.fn(),
  deleteLlmConfig: vi.fn(),
  setActiveLlm: vi.fn(),
  listLlmModels: vi.fn(),
  listRegexProfiles: vi.fn(),
  getActiveRegex: vi.fn(),
  getRegexProfile: vi.fn(),
  setActiveRegex: vi.fn(),
  createRegexProfile: vi.fn(),
  updateRegexProfile: vi.fn(),
  deleteRegexProfile: vi.fn(),
}));

describe('useSettingsPage', () => {
  beforeEach(async () => {
    vi.resetModules();
    vi.clearAllMocks();
    localStorage.clear();

    const settingsApi = await import('../../services/modules/settings');
    settingsApi.getGlobalSettings.mockResolvedValue({
      ui: { theme: 'dark' },
      text: {},
      summary: {},
      variables: {},
      text_opt: {},
      world_evolution: {},
      default_profiles: {},
    });
    settingsApi.listPresets.mockResolvedValue({
      presets: [{ id: 'preset_1', name: '测试预设' }],
      active: { preset_id: 'preset_1' },
    });
    settingsApi.getPreset.mockResolvedValue({
      id: 'preset_1',
      name: '测试预设',
      version: 1,
      root: {},
      meta: {},
    });
    settingsApi.listRegexProfiles.mockResolvedValue([{ id: 'regex_1', name: '测试正则' }]);
    settingsApi.getActiveRegex.mockResolvedValue({ id: 'regex_1' });
    settingsApi.getRegexProfile.mockResolvedValue({
      id: 'regex_1',
      name: '测试正则',
      config: {},
    });
    settingsApi.listLlmConfigs.mockResolvedValue({
      configs: [{ id: 'llm_1', name: '测试配置', base_url: '', api_key: '', stream: true, default_model: 'gpt-test' }],
      active: { config_id: 'llm_1', model: 'gpt-test' },
    });
  });

  it('dispatches save by active tab', async () => {
    const settingsApi = await import('../../services/modules/settings');
    const page = useSettingsPage();

    await page.bootstrap();

    page.activeTab.value = 'tab-ui';
    await page.saveCurrentTab();
    expect(settingsApi.putGlobalSettings).toHaveBeenCalledTimes(1);
    expect(settingsApi.updatePreset).not.toHaveBeenCalled();

    page.activeTab.value = 'tab-presets';
    page.presetDraft.name = '已修改预设';
    await page.saveCurrentTab();
    expect(settingsApi.updatePreset).toHaveBeenCalledWith(
      'preset_1',
      expect.objectContaining({ name: '已修改预设' }),
    );

    page.activeTab.value = 'tab-regex';
    page.regexDraft.name = '已修改正则';
    await page.saveCurrentTab();
    expect(settingsApi.updateRegexProfile).toHaveBeenCalledWith(
      'regex_1',
      expect.objectContaining({ name: '已修改正则' }),
    );

    page.activeTab.value = 'tab-api';
    page.llmDraft.name = '已修改配置';
    await page.saveCurrentTab();
    expect(settingsApi.updateLlmConfig).toHaveBeenCalledWith(
      'llm_1',
      expect.objectContaining({ name: '已修改配置' }),
    );
    expect(settingsApi.setActiveLlm).toHaveBeenCalledWith({
      config_id: 'llm_1',
      model: 'gpt-test',
    });
  });

  it('syncs theme settings to localStorage and document', async () => {
    const settingsApi = await import('../../services/modules/settings');
    const page = useSettingsPage();

    await page.bootstrap();

    expect(document.documentElement.getAttribute('data-theme')).toBe('scroll');

    page.globalSettings.ui.theme = 'snow';
    page.globalSettings.ui.background = 'blueprint';
    await page.saveCurrentTab('tab-ui');

    expect(settingsApi.putGlobalSettings).toHaveBeenCalled();
    expect(localStorage.getItem('app_theme')).toBe('snow');
    expect(localStorage.getItem('app_bg')).toBe('blueprint');
    expect(document.documentElement.getAttribute('data-theme')).toBe('snow');
    expect(document.body.className).toContain('bg-blueprint');
  });
});
