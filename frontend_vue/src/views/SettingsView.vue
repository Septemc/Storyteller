<template>
  <main class="settings-container">
    <aside class="settings-sidebar">
      <button v-for="tab in tabs" :key="tab.id" :class="['settings-tab-btn', { active: activeTab === tab.id }]" @click="activeTab = tab.id">
        <span class="icon">{{ tab.icon }}</span> {{ tab.label }}
      </button>
    </aside>

    <section class="settings-content-area">
      <div class="settings-header-actions">
        <span id="settings-status" class="small-text muted">{{ statusText }}</span>
        <button id="settings-load-btn" class="btn-secondary btn-small" @click="resetCurrentTab">重置/加载</button>
        <button id="settings-save-btn" class="btn-primary btn-small" @click="saveCurrentTab">保存更改</button>
      </div>

      <div v-show="activeTab === 'tab-ui'" id="tab-ui" class="tab-pane active">
        <h2 class="section-title">主题风格</h2>
        <div class="settings-section">
          <label class="form-label">背景主题</label>
          <div class="theme-card-grid">
            <button
              v-for="theme in themeOptions"
              :key="theme.value"
              type="button"
              :class="['theme-option-card', { active: globalSettings.ui.theme === theme.value }]"
              @click="globalSettings.ui.theme = theme.value"
            >
              <span class="theme-option-preview" :style="{ background: theme.preview }">
                <span
                  v-for="(chip, index) in theme.chips"
                  :key="`${theme.value}-${index}`"
                  class="theme-option-chip"
                  :style="{ background: chip }"
                />
              </span>
              <span class="theme-option-name">{{ theme.label }}</span>
              <span class="theme-option-desc">{{ theme.description }}</span>
            </button>
          </div>
        </div>
        <div class="settings-section">
          <label class="form-label">背景纹理</label>
          <div class="theme-card-grid texture-grid">
            <button
              v-for="background in backgroundOptions"
              :key="background.value"
              type="button"
              :class="['theme-option-card', 'texture-option-card', { active: globalSettings.ui.background === background.value }]"
              @click="globalSettings.ui.background = background.value"
            >
              <span class="theme-option-preview texture-preview" :style="{ backgroundImage: background.preview }" />
              <span class="theme-option-name">{{ background.label }}</span>
              <span class="theme-option-desc">{{ background.description }}</span>
            </button>
          </div>
        </div>
        <div class="settings-section">
          <label class="form-label">后处理正则规则 (JSON)</label>
          <textarea v-model="globalSettings.text.postprocessing_rules" id="postprocessing-rules" class="form-textarea" rows="6"></textarea>
        </div>
      </div>

      <div v-show="activeTab === 'tab-memory'" id="tab-memory" class="tab-pane active">
        <h2 class="section-title">摘要与记忆</h2>
        <div class="settings-section">
          <label class="form-check"><input v-model="globalSettings.summary.enabled" id="summary-enabled" type="checkbox"><span>启用自动剧情摘要</span></label>
        </div>
        <div class="half-grid">
          <div class="settings-section"><label class="form-label">摘要 Profile ID</label><input v-model="globalSettings.summary.profile_id" id="summary-profile-id" class="form-input"></div>
          <div class="settings-section"><label class="form-label">触发频率</label><input v-model.number="globalSettings.summary.frequency" id="summary-frequency" class="form-input" type="number"></div>
        </div>
        <div class="settings-section">
          <label class="form-label">历史记忆检索策略 (JSON)</label>
          <textarea :value="jsonText(globalSettings.summary.rag_config)" id="summary-rag-config" class="form-textarea" rows="8" @input="assignJson(globalSettings.summary, 'rag_config', $event.target.value)"></textarea>
        </div>
      </div>

      <div v-show="activeTab === 'tab-variables'" id="tab-variables" class="tab-pane active">
        <h2 class="section-title">变量思考</h2>
        <div class="settings-section">
          <label class="form-check"><input v-model="globalSettings.variables.enabled" id="variables-enabled" type="checkbox"><span>启用变量追踪</span></label>
        </div>
        <div class="half-grid">
          <div class="settings-section"><label class="form-label">变量思考 Profile ID</label><input v-model="globalSettings.variables.profile_id" id="variables-profile-id" class="form-input"></div>
          <div class="settings-section"><label class="form-label">独立 API Config ID</label><input v-model="globalSettings.variables.api_config_id" id="variables-api-config-id" class="form-input"></div>
        </div>
      </div>

      <div v-show="activeTab === 'tab-evolution'" id="tab-evolution" class="tab-pane active">
        <h2 class="section-title">正文与演化</h2>
        <div class="settings-section">
          <label class="form-check"><input v-model="globalSettings.text_opt.enabled" id="textopt-enabled" type="checkbox"><span>启用文笔润色</span></label>
          <label class="form-label">润色 Profile ID</label>
          <input v-model="globalSettings.text_opt.profile_id" id="textopt-profile-id" class="form-input">
        </div>
        <div class="settings-section">
          <label class="form-check"><input v-model="globalSettings.world_evolution.enabled" id="world-evolution-enabled" type="checkbox"><span>启用世界动态演化</span></label>
          <label class="form-label">演化逻辑 Profile ID</label>
          <input v-model="globalSettings.world_evolution.profile_id" id="world-evolution-profile-id" class="form-input">
        </div>
        <div class="settings-section">
          <label class="form-label">Global Default Profiles (JSON)</label>
          <textarea :value="jsonText(globalSettings.default_profiles)" id="default-profiles" class="form-textarea" rows="12" @input="assignJson(globalSettings, 'default_profiles', $event.target.value)"></textarea>
        </div>
      </div>

      <div v-show="activeTab === 'tab-presets'" id="tab-presets" class="tab-pane active">
        <h2 class="section-title">预设管理</h2>
        <div class="half-grid">
          <div class="settings-section">
            <label class="form-label">预设文件</label>
            <select v-model="selectedPresetId" id="preset-select" class="form-select" @change="selectPreset(selectedPresetId)">
              <option v-for="preset in presets" :key="preset.id" :value="preset.id">{{ preset.name }}</option>
            </select>
            <div class="small-text muted" style="margin-top: 8px;">当前应用：{{ presetActiveId || '-' }}</div>
            <div class="toolbar-actions" style="display: flex; gap: 8px; margin-top: 10px;">
              <button id="preset-create-btn" class="btn-secondary btn-small" @click="createPreset">新建</button>
              <button id="preset-set-active-btn" class="btn-primary btn-small" @click="activatePreset">应用</button>
              <button id="preset-delete-btn" class="btn-secondary btn-small" style="color: var(--danger);" @click="deletePreset">删除</button>
            </div>
          </div>
          <div class="settings-section">
            <label class="form-label">预设名称</label>
            <input v-model="presetDraft.name" class="form-input">
            <label class="form-label" style="margin-top: 12px;">版本</label>
            <input v-model.number="presetDraft.version" class="form-input" type="number">
          </div>
        </div>
        <div class="settings-section">
          <label class="form-label">Root (JSON)</label>
          <textarea v-model="presetDraft.rootText" class="form-textarea" rows="14"></textarea>
        </div>
        <div class="settings-section">
          <label class="form-label">Meta (JSON)</label>
          <textarea v-model="presetDraft.metaText" class="form-textarea" rows="8"></textarea>
        </div>
      </div>

      <div v-show="activeTab === 'tab-regex'" id="tab-regex" class="tab-pane active">
        <h2 class="section-title">正则管理</h2>
        <div class="half-grid">
          <div class="settings-section">
            <label class="form-label">配置文件</label>
            <select v-model="selectedRegexId" class="form-select" @change="selectRegex(selectedRegexId)">
              <option v-for="profile in regexProfiles" :key="profile.id" :value="profile.id">{{ profile.name }}</option>
            </select>
            <div class="small-text muted" style="margin-top: 8px;">当前应用：{{ activeRegexId || '-' }}</div>
            <div class="toolbar-actions" style="display: flex; gap: 8px; margin-top: 10px;">
              <button class="btn-secondary btn-small" @click="createRegex">新建</button>
              <button class="btn-primary btn-small" @click="activateRegex">应用</button>
              <button class="btn-secondary btn-small" style="color: var(--danger);" @click="deleteRegex">删除</button>
            </div>
          </div>
          <div class="settings-section">
            <label class="form-label">配置名称</label>
            <input v-model="regexDraft.name" class="form-input">
          </div>
        </div>
        <div class="settings-section">
          <label class="form-label">配置 JSON</label>
          <textarea v-model="regexDraft.configText" class="form-textarea" rows="18"></textarea>
        </div>
      </div>

      <div v-show="activeTab === 'tab-api'" id="tab-api" class="tab-pane active">
        <h2 class="section-title">API 配置</h2>
        <div class="settings-section">
          <div class="toolbar-actions" style="display: flex; gap: 8px; margin-bottom: 10px;">
            <button class="btn-secondary btn-small" @click="createLlmConfig">新建配置</button>
            <button class="btn-secondary btn-small" style="color: var(--danger);" @click="deleteLlmConfig">删除配置</button>
          </div>
          <select v-model="selectedLlmId" class="form-select" @change="syncSelectedLlm">
            <option v-for="config in llmConfigs" :key="config.id" :value="config.id">{{ config.name }}</option>
          </select>
          <div class="small-text muted" style="margin-top: 8px;">当前激活：{{ activeLlm.config_id || '-' }} / {{ activeLlm.model || '-' }}</div>
        </div>
        <div class="half-grid">
          <div class="settings-section"><label class="form-label">名称</label><input v-model="llmDraft.name" class="form-input"></div>
          <div class="settings-section"><label class="form-label">默认模型</label><input v-model="llmDraft.default_model" class="form-input"></div>
        </div>
        <div class="settings-section"><label class="form-label">Base URL</label><input v-model="llmDraft.base_url" class="form-input"></div>
        <div class="settings-section"><label class="form-label">API Key</label><input v-model="llmDraft.api_key" class="form-input"></div>
        <div class="settings-section"><label class="form-check"><input v-model="llmDraft.stream" type="checkbox"><span>启用流式输出</span></label></div>
      </div>
    </section>
  </main>
</template>

<script setup>
import { onMounted, watch } from 'vue';
import { useSettingsPage } from '../composables/useSettingsPage';
import {
  applyThemeSettings,
  BACKGROUND_OPTIONS,
  initThemePage,
  THEME_OPTIONS,
} from '../page_logic/theme-init.module';

const tabs = [
  { id: 'tab-ui', icon: '配', label: '界面与显示' },
  { id: 'tab-memory', icon: '忆', label: '摘要与记忆' },
  { id: 'tab-variables', icon: '变', label: '变量思考' },
  { id: 'tab-evolution', icon: '演', label: '正文与演化' },
  { id: 'tab-presets', icon: '预', label: '预设管理' },
  { id: 'tab-regex', icon: '则', label: '正则管理' },
  { id: 'tab-api', icon: 'API', label: 'API 配置' },
];

const {
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
} = useSettingsPage();

const themeOptions = THEME_OPTIONS;
const backgroundOptions = BACKGROUND_OPTIONS;

function jsonText(value) {
  return JSON.stringify(value || {}, null, 2);
}

function assignJson(target, key, text) {
  try {
    target[key] = JSON.parse(text || '{}');
  } catch {
    // keep current state until json becomes valid
  }
}

function syncSelectedLlm() {
  const current = llmConfigs.value.find((item) => item.id === selectedLlmId.value);
  if (current) {
    Object.assign(llmDraft, current);
  }
}

watch(selectedLlmId, syncSelectedLlm);

watch(
  () => [globalSettings.ui?.theme, globalSettings.ui?.background],
  ([theme, background]) => {
    if (!theme && !background) return;
    applyThemeSettings({ theme, background });
  },
  { immediate: true },
);

onMounted(async () => {
  document.title = 'Storyteller | 设置';
  document.body.setAttribute('data-page', 'settings');
  initThemePage();
  await bootstrap();
});
</script>

<style scoped>
.theme-card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 14px;
}

.theme-option-card {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 10px;
  width: 100%;
  padding: 14px;
  border: 1px solid var(--border-soft);
  border-radius: 16px;
  background: color-mix(in srgb, var(--bg-elevated) 94%, transparent);
  color: var(--text-primary);
  box-shadow: var(--shadow-soft);
  transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
  text-align: left;
}

.theme-option-card:hover {
  transform: translateY(-1px);
  border-color: color-mix(in srgb, var(--accent) 42%, var(--border-soft));
}

.theme-option-card.active {
  border-color: var(--accent);
  box-shadow: 0 0 0 1px color-mix(in srgb, var(--accent) 28%, transparent), var(--shadow-soft);
}

.theme-option-preview {
  position: relative;
  display: flex;
  align-items: flex-end;
  gap: 6px;
  width: 100%;
  height: 84px;
  padding: 10px;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid color-mix(in srgb, var(--border-soft) 72%, transparent);
}

.theme-option-chip {
  width: 18px;
  height: 18px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.35);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.12);
}

.theme-option-name {
  font-size: 15px;
  font-weight: 700;
}

.theme-option-desc {
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 1.55;
}

.texture-grid {
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
}

.texture-preview {
  background-color: color-mix(in srgb, var(--bg-elevated-alt) 82%, white 18%);
  background-size: 22px 22px, 22px 22px, cover;
}
</style>
