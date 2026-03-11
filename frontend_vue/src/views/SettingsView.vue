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
        <div class="settings-section half-grid">
          <div>
            <label class="form-label">主题</label>
            <select v-model="globalSettings.ui.theme" class="form-select">
              <option value="dark">深空（默认）</option>
              <option value="light">晨曦</option>
              <option value="cyberpunk">赛博霓虹</option>
              <option value="scroll">羊皮卷轴</option>
              <option value="forest">迷雾森林</option>
              <option value="abyss">猩红深渊</option>
              <option value="royal">皇家紫金</option>
              <option value="aurora">极光海岸</option>
              <option value="obsidian">曜石墨金</option>
              <option value="sakura">樱雾茶歇</option>
              <option value="glacier">冰川夜航</option>
              <option value="ember">余烬铜辉</option>
            </select>
          </div>
          <div>
            <label class="form-label">背景纹理</label>
            <select v-model="globalSettings.ui.background" class="form-select">
              <option value="grid">全息网格</option>
              <option value="noise">胶片噪点</option>
              <option value="plain">纯净虚空</option>
              <option value="runes">魔法力场</option>
              <option value="circuit">集成电路</option>
              <option value="aurora">极光流幕</option>
              <option value="paper">纸纤纹理</option>
              <option value="stardust">星尘夜幕</option>
              <option value="hex">蜂巢矩阵</option>
              <option value="waves">丝绸波纹</option>
            </select>
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
import { initThemePage } from '../page_logic/theme-init.module';

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

onMounted(async () => {
  document.title = 'Storyteller | 设置';
  document.body.setAttribute('data-page', 'settings');
  initThemePage();
  await bootstrap();
});
</script>
