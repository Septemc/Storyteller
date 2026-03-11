<template>
  <div :class="blockClasses">
    <div class="story-meta">{{ metaText }}</div>

    <div v-if="isAssistant && block.thinkingText" class="story-thinking-container" style="margin-bottom: 8px;">
      <button
        class="thinking-toggle"
        style="background: none; border: none; padding: 4px 8px; cursor: pointer; font-size: 11px; color: var(--text-secondary); display: flex; align-items: center; gap: 4px;"
        @click="thinkingOpen = !thinkingOpen"
      >
        <span class="toggle-icon">{{ thinkingOpen ? '▼' : '▶' }}</span>
        <span class="toggle-text">思考过程</span>
      </button>
      <div
        v-show="thinkingOpen"
        class="story-thinking"
        style="margin-top: 4px; padding: 8px 12px; background: rgba(0,0,0,0.05); border-radius: 8px; color: var(--text-secondary); font-style: italic;"
      >
        {{ block.thinkingText }}
      </div>
    </div>

    <div class="story-text">
      <p v-for="(paragraph, index) in paragraphs" :key="index">{{ paragraph }}</p>
    </div>

    <div
      v-if="isAssistant && block.summaryText"
      class="story-summary"
      style="margin-top: 8px; padding: 8px 12px; background: rgba(0,0,0,0.05); border-radius: 8px; color: var(--text-secondary); border-left: 3px solid var(--accent);"
    >
      总结 {{ block.summaryText }}
    </div>

    <div v-if="isAssistant" class="story-footer" style="display: flex; align-items: center; flex-wrap: wrap; gap: 8px; margin-top: 8px;">
      <button
        v-if="block.rawText"
        class="raw-text-link"
        style="background: none; border: none; padding: 4px 8px; cursor: pointer; font-size: 11px; color: var(--accent); text-decoration: underline; opacity: 0.7;"
        @click="$emit('show-raw-text', block)"
      >
        查看原文
      </button>

      <span v-if="block.stats" class="story-stats">
        <span class="story-stats-item">本段字数: {{ block.stats.paragraph_word_count || 0 }}</span>
        <span class="story-stats-divider">|</span>
        <span class="story-stats-item">累计字数: {{ block.stats.cumulative_word_count || 0 }}</span>
        <span class="story-stats-divider">|</span>
        <span class="story-stats-item">前端耗时: {{ formatDuration(block.stats.frontend_duration || 0) }}</span>
        <span class="story-stats-divider">|</span>
        <span class="story-stats-item">后端耗时: {{ formatDuration(block.stats.backend_duration || 0) }}</span>
      </span>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';

const props = defineProps({
  block: {
    type: Object,
    required: true,
  },
});

defineEmits(['show-raw-text']);

const thinkingOpen = ref(false);

const isAssistant = computed(() => props.block.type === 'assistant');

const blockClasses = computed(() => ({
  'story-block': true,
  'story-block-user': props.block.type === 'user',
  'story-block-assistant': props.block.type === 'assistant',
}));

const metaText = computed(() => {
  if (props.block.type === 'user') {
    return '用户输入';
  }
  return props.block.metaText || 'AI输出';
});

const paragraphs = computed(() => {
  const source = props.block.displayText || props.block.rawText || '';
  const rows = String(source)
    .split(/\n+/)
    .map((item) => item.trim())
    .filter(Boolean);
  return rows.length ? rows : [''];
});

function formatDuration(value) {
  const seconds = Number(value || 0);
  return `${seconds.toFixed(1)}s`;
}
</script>
