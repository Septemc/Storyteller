<template>
  <section class="sidebar-section devlog-panel">
    <div class="sidebar-header">
      <div class="sidebar-title">Agent Dev Log</div>
      <button class="panel-collapse-btn" aria-label="toggle developer log" @click="$emit('toggle')">
        <svg
          viewBox="0 0 24 24"
          width="16"
          height="16"
          stroke="currentColor"
          stroke-width="2"
          fill="none"
          :style="{ transform: open ? 'rotate(0deg)' : 'rotate(-90deg)' }"
        >
          <polyline points="6 9 12 15 18 9"></polyline>
        </svg>
      </button>
    </div>
    <div v-show="open" class="sidebar-body devlog-body">
      <div class="devlog-meta">
        <span>Strength: {{ log?.reasoningStrength || 'low' }}</span>
        <span>Entries: {{ entries.length }}</span>
        <button type="button" class="btn-secondary btn-small" @click="$emit('clear')">Clear</button>
      </div>
      <div v-if="!entries.length" class="muted small-text">No agent trace yet.</div>
      <details v-for="(entry, index) in entries" :key="`${index}-${entry.timestamp}`" class="devlog-entry" :open="index >= Math.max(entries.length - 2, 0)">
        <summary class="devlog-summary">
          <span class="devlog-kind">{{ entry.kind }}</span>
          <span class="devlog-title">{{ entry.title }}</span>
        </summary>
        <div v-if="entry.detail" class="devlog-detail">{{ entry.detail }}</div>
        <pre v-if="hasData(entry)" class="devlog-data">{{ formatData(entry.data) }}</pre>
      </details>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  log: {
    type: Object,
    default: null,
  },
  open: {
    type: Boolean,
    default: true,
  },
});

defineEmits(['toggle', 'clear']);

const entries = computed(() => props.log?.entries || []);

function hasData(entry) {
  return entry && entry.data && Object.keys(entry.data).length > 0;
}

function formatData(data) {
  return JSON.stringify(data, null, 2);
}
</script>

<style scoped>
.devlog-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 420px;
  overflow: auto;
}

.devlog-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  font-size: 12px;
  color: var(--text-secondary);
}

.devlog-entry {
  background: rgba(0, 0, 0, 0.04);
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 10px;
  padding: 8px 10px;
}

.devlog-summary {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 12px;
}

.devlog-kind {
  min-width: 72px;
  color: var(--accent);
  text-transform: uppercase;
}

.devlog-title {
  font-weight: 600;
}

.devlog-detail {
  margin-top: 8px;
  font-size: 12px;
  line-height: 1.5;
  color: var(--text-secondary);
  white-space: pre-wrap;
}

.devlog-data {
  margin: 8px 0 0;
  padding: 8px;
  background: rgba(0, 0, 0, 0.06);
  border-radius: 8px;
  overflow: auto;
  font-size: 11px;
  line-height: 1.45;
}
</style>
