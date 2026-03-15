<template>
  <div class="field-block">
    <label class="form-label">{{ field.label }}</label>
    <template v-if="editable">
      <input
        v-if="field.type === 'text'"
        :value="editorValue"
        class="form-input"
        type="text"
        @input="$emit('update', $event.target.value)"
        @blur="$emit('commit')"
      >
      <textarea
        v-else-if="field.type === 'textarea'"
        :value="editorValue"
        class="form-textarea"
        rows="5"
        @input="$emit('update', $event.target.value)"
        @blur="$emit('commit')"
      ></textarea>
      <textarea
        v-else
        :value="editorValue"
        class="form-textarea code-editor"
        rows="6"
        spellcheck="false"
        @input="$emit('update', $event.target.value)"
        @blur="$emit('commit')"
      ></textarea>
    </template>
    <div v-else class="field-preview">
      <div v-if="field.type === 'text'" class="rendered-value">{{ textValue }}</div>
      <div v-else-if="field.type === 'textarea'" class="rendered-value multiline">{{ textValue }}</div>
      <div v-else-if="field.type === 'object_list'" class="object-list">
        <div v-if="!listItems.length" class="muted">未知</div>
        <div v-for="(item, index) in listItems" :key="index" class="object-card">
          <div v-for="row in item" :key="row.key" class="kv-row">
            <span class="kv-key">{{ row.key }}</span>
            <span class="kv-value">{{ row.value }}</span>
          </div>
        </div>
      </div>
      <div v-else-if="field.type === 'stats_panel'" class="stats-grid">
        <div v-if="!objectEntries.length" class="muted">未知</div>
        <div v-for="row in objectEntries" :key="row.key" class="stat-card">
          <div class="stat-label">{{ row.key }}</div>
          <div class="stat-value">{{ row.value }}</div>
        </div>
      </div>
      <div v-else-if="field.type === 'relation_graph'" class="relation-list">
        <div v-if="!objectEntries.length" class="muted">未知</div>
        <div v-for="row in objectEntries" :key="row.key" class="relation-card">
          <div class="relation-target">{{ row.key }}</div>
          <div class="relation-desc">{{ row.value }}</div>
        </div>
      </div>
      <div v-else class="json-panel">
        <div v-if="!objectEntries.length" class="muted">未知</div>
        <div v-for="row in objectEntries" :key="row.key" class="kv-row">
          <span class="kv-key">{{ row.key }}</span>
          <span class="kv-value">{{ row.value }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  editable: { type: Boolean, default: false },
  editorValue: { type: String, default: '' },
  field: { type: Object, required: true },
  playerMode: { type: Boolean, default: false },
  value: { type: null, default: null },
});

defineEmits(['commit', 'update']);

const normalized = computed(() => normalizeValue(props.value));
const textValue = computed(() => {
  const value = normalized.value;
  if (props.playerMode && isUnknown(value)) return '未知';
  if (typeof value === 'string') return value || '未知';
  if (value == null) return '未知';
  return JSON.stringify(value, null, 2);
});
const objectEntries = computed(() => {
  const value = normalized.value;
  if (props.playerMode && isUnknown(value)) return [];
  if (!value || typeof value !== 'object' || Array.isArray(value)) return [];
  return Object.entries(value).map(([key, item]) => ({ key, value: stringifyItem(item) }));
});
const listItems = computed(() => {
  const value = normalized.value;
  if (props.playerMode && isUnknown(value)) return [];
  if (!Array.isArray(value)) return [];
  return value.map((item) => {
    if (item && typeof item === 'object') {
      return Object.entries(item).map(([key, entry]) => ({ key, value: stringifyItem(entry) }));
    }
    return [{ key: 'value', value: stringifyItem(item) }];
  });
});

function normalizeValue(value) {
  if (typeof value !== 'string') return value;
  const text = value.trim();
  if (!text) return value;
  if ((text.startsWith('{') && text.endsWith('}')) || (text.startsWith('[') && text.endsWith(']'))) {
    try {
      return JSON.parse(text);
    } catch {
      return value;
    }
  }
  return value;
}

function stringifyItem(value) {
  if (value == null || value === '') return '未知';
  if (typeof value === 'string') return value;
  return JSON.stringify(value, null, 2);
}

function isUnknown(value) {
  return value == null || value === '' || value === '未知';
}
</script>

<style scoped>
.field-preview { min-height: 42px; }
.rendered-value { min-height: 42px; padding: 10px 12px; border: 1px solid var(--border-soft); border-radius: 12px; background: rgba(255, 255, 255, 0.04); }
.multiline { white-space: pre-wrap; overflow-wrap: anywhere; }
.object-list, .json-panel, .relation-list { display: flex; flex-direction: column; gap: 8px; }
.object-card, .relation-card, .stat-card { border: 1px solid var(--border-soft); border-radius: 12px; padding: 10px 12px; background: rgba(255, 255, 255, 0.04); }
.kv-row { display: grid; grid-template-columns: 108px minmax(0, 1fr); gap: 10px; align-items: start; padding: 4px 0; }
.kv-key, .stat-label, .relation-target { color: var(--text-secondary); font-size: 12px; font-weight: 700; }
.kv-value, .relation-desc { white-space: pre-wrap; overflow-wrap: anywhere; }
.stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; }
.stat-value { font-size: 22px; font-weight: 700; line-height: 1.1; }
.code-editor { font-family: "Cascadia Code", "Consolas", monospace; font-size: 13px; }
</style>
