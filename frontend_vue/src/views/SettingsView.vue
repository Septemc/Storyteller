<template>
  <main class="settings-container settings-page">
    <aside class="settings-sidebar">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        :class="['settings-tab-btn', { active: activeTab === tab.id }]"
        @click="activeTab = tab.id"
      >
        {{ tab.label }}
      </button>
    </aside>

    <section class="settings-content-area">
      <div class="settings-header-actions">
        <span class="small-text muted">{{ statusText }}</span>
        <button class="btn-secondary btn-small" @click="resetCurrentTab">重置 / 重新加载</button>
        <button class="btn-primary btn-small" @click="saveCurrentTab">保存当前页</button>
      </div>

      <div v-show="activeTab === 'tab-ui'" class="tab-pane active">
        <h2 class="section-title">界面与显示</h2>
        <div class="settings-section">
          <label class="form-label">主题风格</label>
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
          <label class="form-label">后处理正则规则（JSON）</label>
          <textarea v-model="globalSettings.text.postprocessing_rules" class="form-textarea" rows="6"></textarea>
        </div>
      </div>

      <div v-show="activeTab === 'tab-memory'" class="tab-pane active">
        <h2 class="section-title">摘要与记忆</h2>
        <div class="settings-section">
          <label class="form-check"><input v-model="globalSettings.summary.enabled" type="checkbox"><span>启用自动剧情摘要</span></label>
        </div>
        <div class="half-grid">
          <div class="settings-section"><label class="form-label">摘要 Profile ID</label><input v-model="globalSettings.summary.profile_id" class="form-input"></div>
          <div class="settings-section"><label class="form-label">触发频率</label><input v-model.number="globalSettings.summary.frequency" class="form-input" type="number"></div>
        </div>
        <div class="settings-section">
          <label class="form-label">历史记忆检索配置（JSON）</label>
          <textarea :value="jsonText(globalSettings.summary.rag_config)" class="form-textarea" rows="8" @input="assignJson(globalSettings.summary, 'rag_config', $event.target.value)"></textarea>
        </div>
      </div>

      <div v-show="activeTab === 'tab-variables'" class="tab-pane active">
        <h2 class="section-title">变量思考</h2>
        <div class="settings-section">
          <label class="form-check"><input v-model="globalSettings.variables.enabled" type="checkbox"><span>启用变量追踪</span></label>
        </div>
        <div class="half-grid">
          <div class="settings-section"><label class="form-label">变量思考 Profile ID</label><input v-model="globalSettings.variables.profile_id" class="form-input"></div>
          <div class="settings-section"><label class="form-label">独立 API Config ID</label><input v-model="globalSettings.variables.api_config_id" class="form-input"></div>
        </div>
      </div>

      <div v-show="activeTab === 'tab-evolution'" class="tab-pane active">
        <h2 class="section-title">正文与演化</h2>
        <div class="settings-section">
          <label class="form-check"><input v-model="globalSettings.text_opt.enabled" type="checkbox"><span>启用文笔润色</span></label>
          <label class="form-label">润色 Profile ID</label>
          <input v-model="globalSettings.text_opt.profile_id" class="form-input">
        </div>
        <div class="settings-section">
          <label class="form-check"><input v-model="globalSettings.world_evolution.enabled" type="checkbox"><span>启用世界动态演化</span></label>
          <label class="form-label">演化逻辑 Profile ID</label>
          <input v-model="globalSettings.world_evolution.profile_id" class="form-input">
        </div>
        <div class="settings-section">
          <label class="form-label">全局默认 Profiles（JSON）</label>
          <textarea :value="jsonText(globalSettings.default_profiles)" class="form-textarea" rows="12" @input="assignJson(globalSettings, 'default_profiles', $event.target.value)"></textarea>
        </div>
      </div>

      <div v-show="activeTab === 'tab-presets'" class="tab-pane active">
        <h2 class="section-title">预设管理</h2>
        <div class="half-grid">
          <div class="settings-section">
            <label class="form-label">预设文件</label>
            <select v-model="selectedPresetId" class="form-select" @change="selectPreset(selectedPresetId)">
              <option v-for="preset in presets" :key="preset.id" :value="preset.id">{{ preset.name }}</option>
            </select>
            <div class="small-text muted section-tip">当前应用：{{ presetActiveId || '-' }}</div>
            <div class="toolbar-actions">
              <button class="btn-secondary btn-small" @click="createPreset">新建</button>
              <button class="btn-primary btn-small" @click="activatePreset">应用</button>
              <button class="btn-secondary btn-small danger-btn" @click="deletePreset">删除</button>
            </div>
          </div>
          <div class="settings-section">
            <label class="form-label">预设名称</label>
            <input v-model="presetDraft.name" class="form-input">
            <label class="form-label" style="margin-top: 12px;">版本</label>
            <input v-model.number="presetDraft.version" class="form-input" type="number">
          </div>
        </div>
        <div class="settings-section"><label class="form-label">Root（JSON）</label><textarea v-model="presetDraft.rootText" class="form-textarea" rows="14"></textarea></div>
        <div class="settings-section"><label class="form-label">Meta（JSON）</label><textarea v-model="presetDraft.metaText" class="form-textarea" rows="8"></textarea></div>
      </div>

      <div v-show="activeTab === 'tab-regex'" class="tab-pane active">
        <h2 class="section-title">正则管理</h2>
        <div class="half-grid">
          <div class="settings-section">
            <label class="form-label">配置文件</label>
            <select v-model="selectedRegexId" class="form-select" @change="selectRegex(selectedRegexId)">
              <option v-for="profile in regexProfiles" :key="profile.id" :value="profile.id">{{ profile.name }}</option>
            </select>
            <div class="small-text muted section-tip">当前应用：{{ activeRegexId || '-' }}</div>
            <div class="toolbar-actions">
              <button class="btn-secondary btn-small" @click="createRegex">新建</button>
              <button class="btn-primary btn-small" @click="activateRegex">应用</button>
              <button class="btn-secondary btn-small danger-btn" @click="deleteRegex">删除</button>
            </div>
          </div>
          <div class="settings-section"><label class="form-label">配置名称</label><input v-model="regexDraft.name" class="form-input"></div>
        </div>
        <div class="settings-section"><label class="form-label">配置 JSON</label><textarea v-model="regexDraft.configText" class="form-textarea" rows="18"></textarea></div>
      </div>

      <div v-show="activeTab === 'tab-api'" class="tab-pane active">
        <h2 class="section-title">API 配置</h2>
        <SettingsApiPane
          :active-config-id="activeLlm.config_id"
          :configs="llmConfigs"
          :draft="llmDraft"
          :loading-models="llmModelsLoading"
          :models="llmModels"
          :selected-config-id="selectedLlmId"
          @activate="activateSelectedLlm"
          @create="createLlmConfig"
          @delete="deleteLlmConfig"
          @fetch-models="fetchLlmModels"
          @select="selectedLlmId = $event"
          @update:draft="Object.assign(llmDraft, $event)"
        />
      </div>
    </section>
  </main>
</template>

<script setup>
import { onMounted, watch } from 'vue';
import SettingsApiPane from '../components/settings/SettingsApiPane.vue';
import { useSettingsPage } from '../composables/useSettingsPage';
import { BACKGROUND_OPTIONS, THEME_OPTIONS, applyThemeSettings, initThemePage } from '../page_logic/theme-init.module';
import { assignJson, jsonText, settingsTabs as tabs } from '../page_logic/settings-view.module';
import '../styles/settings-view.css';

const state = useSettingsPage();
const { activeLlm, activeRegexId, activeTab, activatePreset, activateRegex, activateSelectedLlm, bootstrap, createLlmConfig, createPreset, createRegex, deleteLlmConfig, deletePreset, deleteRegex, fetchLlmModels, globalSettings, llmConfigs, llmDraft, llmModels, llmModelsLoading, presetActiveId, presetDraft, presets, regexDraft, regexProfiles, resetCurrentTab, saveCurrentTab, selectPreset, selectRegex, selectedLlmId, selectedPresetId, selectedRegexId, statusText } = state;
const themeOptions = THEME_OPTIONS;
const backgroundOptions = BACKGROUND_OPTIONS;

watch(() => [globalSettings.ui?.theme, globalSettings.ui?.background], ([theme, background]) => {
  if (!theme && !background) return;
  applyThemeSettings({ theme, background });
}, { immediate: true });

onMounted(async () => {
  document.title = 'Storyteller | 设置';
  document.body.setAttribute('data-page', 'settings');
  initThemePage();
  await bootstrap();
});
</script>
