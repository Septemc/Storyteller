<template>
  <div class="api-pane">
    <div class="api-list-card">
      <div class="api-pane-title">API 配置列表</div>
      <div class="api-toolbar">
        <button class="btn-secondary btn-small" @click="$emit('create')">新建配置</button>
        <button class="btn-secondary btn-small danger-btn" :disabled="!selectedConfigId" @click="$emit('delete')">删除配置</button>
      </div>
      <div class="api-list-shell">
        <button
          v-for="config in configs"
          :key="config.id"
          :class="['api-list-item', { active: selectedConfigId === config.id }]"
          @click="$emit('select', config.id)"
        >
          <div class="api-list-head">
            <span class="api-name">{{ config.name }}</span>
            <span v-if="activeConfigId === config.id" class="api-active-chip">当前激活</span>
          </div>
          <div class="api-meta">{{ config.default_model || '未设置默认模型' }}</div>
          <div class="api-meta">{{ config.base_url }}</div>
        </button>
        <div v-if="!configs.length" class="muted api-empty">当前还没有保存任何 API 配置</div>
      </div>
    </div>

    <div class="api-editor-card">
      <div class="api-pane-title">当前配置详情</div>
      <div class="api-editor-grid">
        <div class="settings-section">
          <label class="form-label">配置名称</label>
          <input :value="draft.name" class="form-input" @input="$emit('update:draft', { name: $event.target.value })">
        </div>
        <div class="settings-section">
          <label class="form-label">当前状态</label>
          <div class="api-status-line">{{ statusLabel }}</div>
        </div>
      </div>
      <div class="settings-section">
        <label class="form-label">Base URL</label>
        <input :value="draft.base_url" class="form-input" placeholder="https://api.example.com/v1" @input="$emit('update:draft', { base_url: $event.target.value })">
      </div>
      <div class="settings-section">
        <label class="form-label">API Key</label>
        <input :value="draft.api_key" class="form-input" placeholder="sk-..." @input="$emit('update:draft', { api_key: $event.target.value })">
      </div>
      <div class="api-editor-grid">
        <div class="settings-section">
          <label class="form-label">默认模型</label>
          <input
            v-if="!models.length"
            :value="draft.default_model"
            class="form-input"
            placeholder="先检索可用模型"
            @input="$emit('update:draft', { default_model: $event.target.value })"
          >
          <select v-else :value="draft.default_model" class="form-select" @change="$emit('update:draft', { default_model: $event.target.value })">
            <option value="">请选择默认模型</option>
            <option v-for="model in models" :key="model" :value="model">{{ model }}</option>
          </select>
        </div>
        <div class="settings-section">
          <label class="form-check">
            <input :checked="draft.stream" type="checkbox" @change="$emit('update:draft', { stream: $event.target.checked })">
            <span>启用流式输出</span>
          </label>
        </div>
      </div>
      <div class="api-toolbar">
        <button class="btn-secondary btn-small" :disabled="loadingModels" @click="$emit('fetch-models')">
          {{ loadingModels ? '正在检索模型...' : '检索可用模型' }}
        </button>
        <button class="btn-primary btn-small" :disabled="!selectedConfigId && !draft.base_url" @click="$emit('activate')">设为当前激活</button>
      </div>
      <div class="settings-section">
        <label class="form-label">可用模型</label>
        <div class="models-shell">
          <button
            v-for="model in models"
            :key="model"
            :class="['model-chip', { active: draft.default_model === model }]"
            @click="$emit('update:draft', { default_model: model })"
          >
            {{ model }}
          </button>
          <div v-if="!models.length" class="muted api-empty">点击“检索可用模型”后，这里会显示当前 API 可用的模型列表。</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  activeConfigId: { type: String, default: '' },
  configs: { type: Array, default: () => [] },
  draft: { type: Object, required: true },
  loadingModels: { type: Boolean, default: false },
  models: { type: Array, default: () => [] },
  selectedConfigId: { type: String, default: '' },
});

defineEmits(['activate', 'create', 'delete', 'fetch-models', 'select', 'update:draft']);

const statusLabel = computed(() => {
  if (!props.configs.length) return '当前没有已保存配置';
  if (!props.selectedConfigId) return '正在编辑新配置';
  return props.activeConfigId === props.selectedConfigId ? '当前配置已激活' : '当前配置未激活';
});
</script>

<style scoped>
.api-pane { display: grid; grid-template-columns: 320px minmax(0, 1fr); gap: 16px; min-height: 0; }
.api-list-card, .api-editor-card { display: flex; flex-direction: column; gap: 14px; padding: 16px; border: 1px solid var(--border-soft); border-radius: 18px; background: color-mix(in srgb, var(--bg-elevated) 94%, transparent); box-shadow: var(--shadow-soft); min-height: 0; }
.api-pane-title { font-size: 16px; font-weight: 700; }
.api-toolbar { display: flex; gap: 8px; flex-wrap: wrap; }
.api-list-shell, .models-shell { display: flex; flex-direction: column; gap: 10px; min-height: 0; }
.api-list-shell { overflow: auto; }
.api-list-item { width: 100%; text-align: left; padding: 12px; border: 1px solid var(--border-soft); border-radius: 14px; background: rgba(255,255,255,0.03); display: flex; flex-direction: column; gap: 6px; transition: border-color 0.18s ease, transform 0.18s ease; }
.api-list-item:hover { transform: translateY(-1px); border-color: color-mix(in srgb, var(--accent) 38%, var(--border-soft)); }
.api-list-item.active { border-color: var(--accent); box-shadow: 0 0 0 1px color-mix(in srgb, var(--accent) 28%, transparent); }
.api-list-head { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
.api-name { font-weight: 700; }
.api-active-chip { padding: 2px 8px; border-radius: 999px; background: color-mix(in srgb, var(--accent) 18%, transparent); color: var(--accent); font-size: 12px; }
.api-meta { color: var(--text-secondary); font-size: 12px; overflow-wrap: anywhere; }
.api-editor-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.api-status-line { min-height: 40px; display: flex; align-items: center; padding: 0 12px; border: 1px solid var(--border-soft); border-radius: 12px; color: var(--text-secondary); background: rgba(255,255,255,0.04); }
.models-shell { border: 1px dashed var(--border-soft); border-radius: 14px; padding: 12px; min-height: 90px; }
.model-chip { padding: 8px 12px; border: 1px solid var(--border-soft); border-radius: 999px; background: rgba(255,255,255,0.04); text-align: left; }
.model-chip.active { border-color: var(--accent); color: var(--accent); }
.api-empty { padding: 10px 0; }
.danger-btn { color: var(--danger); }
@media (max-width: 1080px) { .api-pane { grid-template-columns: 1fr; } .api-editor-grid { grid-template-columns: 1fr; } }
</style>
