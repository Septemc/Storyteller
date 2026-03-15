<template>
  <Teleport to="body">
    <button
      v-if="enabled && !open"
      type="button"
      class="devlog-fab"
      :style="fabStyle"
      @pointerdown="beginDrag"
      @click="handleFabClick"
    >
      <span class="devlog-fab-dot"></span>
      <span class="devlog-fab-text">{{ isMobile ? '开发者' : 'Dev' }}</span>
    </button>

    <aside v-if="enabled && open" class="devlog-drawer">
      <header class="devlog-header">
        <div>
          <div class="devlog-title">Agent Dev Log</div>
          <div class="devlog-subtitle">按剧情片段保留，最新记录显示在最上方。</div>
        </div>
        <button type="button" class="devlog-close" @click="$emit('toggle')">收起</button>
      </header>

      <div v-if="!normalizedLogs.length" class="devlog-empty">当前还没有可展示的 Agent Dev Log。</div>

      <div v-else class="devlog-list">
        <article v-for="(item, index) in normalizedLogs" :key="item.segmentId || `live-${index}`" class="devlog-card">
          <header class="devlog-card-head">
            <div class="devlog-card-title-row">
              <div class="devlog-card-title">剧情片段 {{ item.segmentId || 'live' }}</div>
              <span class="devlog-chip">{{ formatStrength(item.log.reasoningStrength) }}</span>
            </div>
            <div class="devlog-card-meta">
              <span>{{ item.log.entries?.length || 0 }} steps</span>
              <span v-if="item.log.bindings?.storyTitle">{{ item.log.bindings.storyTitle }}</span>
              <span v-if="item.log.bindings?.branchId">{{ item.log.bindings.branchId }}</span>
            </div>
          </header>

          <section class="devlog-section">
            <div class="devlog-section-title">Skill Timeline</div>
            <details v-for="(entry, entryIndex) in item.log.entries || []" :key="`${item.segmentId}-${entryIndex}`" class="devlog-entry" :open="index === 0 && entryIndex >= Math.max((item.log.entries || []).length - 2, 0)">
              <summary class="devlog-entry-summary"><strong>{{ entry.title }}</strong><span class="devlog-entry-kind">{{ entry.kind }}</span></summary>
              <div v-if="entry.detail" class="devlog-entry-detail">{{ entry.detail }}</div>
              <pre v-if="hasData(entry.data)" class="devlog-pre">{{ formatJson(entry.data) }}</pre>
            </details>
          </section>

          <section class="devlog-section"><div class="devlog-section-title">Retrievals</div><pre class="devlog-pre">{{ formatJson(item.log.developer?.retrievals || {}) }}</pre></section>
          <section class="devlog-section"><div class="devlog-section-title">Context Package</div><pre class="devlog-pre">{{ formatJson(item.log.developer?.contextPackage || {}) }}</pre></section>
          <section class="devlog-section"><div class="devlog-section-title">Message Package</div><pre class="devlog-pre">{{ formatJson(item.log.developer?.messagePackage || {}) }}</pre></section>
          <section v-if="hasData(item.log.developer?.writeback)" class="devlog-section"><div class="devlog-section-title">Writeback</div><pre class="devlog-pre">{{ formatJson(item.log.developer?.writeback || {}) }}</pre></section>
        </article>
      </div>
    </aside>
  </Teleport>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';

const props = defineProps({ enabled: { type: Boolean, default: false }, open: { type: Boolean, default: false }, logs: { type: Array, default: () => [] } });
const emit = defineEmits(['toggle']);
const fabPos = ref({ x: 22, y: 24 });
const dragState = ref({ active: false, moved: false, startX: 0, startY: 0, offsetX: 0, offsetY: 0 });
const isMobile = ref(false);

const normalizedLogs = computed(() => (props.logs || []).filter((item) => item?.log).map((item) => ({ segmentId: item.segmentId || item.log?.segmentId || '', log: item.log })));
const fabStyle = computed(() => ({ right: `${fabPos.value.x}px`, bottom: `${fabPos.value.y}px` }));

function syncViewport() { isMobile.value = window.innerWidth <= 720; }
function hasData(data) { if (!data) return false; if (Array.isArray(data)) return data.length > 0; if (typeof data === 'object') return Object.keys(data).length > 0; return Boolean(data); }
function formatJson(data) { return JSON.stringify(data, null, 2); }
function formatStrength(value) { return ({ low: '低', medium: '中', high: '高', ultra: '超高' }[value] || value || '低'); }

function beginDrag(event) {
  dragState.value = { active: true, moved: false, startX: event.clientX, startY: event.clientY, offsetX: fabPos.value.x, offsetY: fabPos.value.y };
  event.currentTarget?.setPointerCapture?.(event.pointerId);
}

function onPointerMove(event) {
  if (!dragState.value.active) return;
  const dx = dragState.value.startX - event.clientX;
  const dy = dragState.value.startY - event.clientY;
  if (Math.abs(dx) > 4 || Math.abs(dy) > 4) dragState.value.moved = true;
  const maxRight = Math.max(12, window.innerWidth - 72);
  const maxBottom = Math.max(12, window.innerHeight - 72);
  fabPos.value = { x: Math.min(Math.max(12, dragState.value.offsetX + dx), maxRight), y: Math.min(Math.max(12, dragState.value.offsetY + dy), maxBottom) };
}

function onPointerUp() { dragState.value.active = false; }
function handleFabClick() { if (!dragState.value.moved) emit('toggle'); }

onMounted(() => {
  syncViewport();
  window.addEventListener('resize', syncViewport);
  window.addEventListener('pointermove', onPointerMove);
  window.addEventListener('pointerup', onPointerUp);
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', syncViewport);
  window.removeEventListener('pointermove', onPointerMove);
  window.removeEventListener('pointerup', onPointerUp);
});
</script>

<style scoped>
.devlog-fab{position:fixed;z-index:2100;width:64px;height:64px;border:1px solid var(--border-soft);border-radius:999px;background:color-mix(in srgb,var(--bg-elevated) 94%,transparent);box-shadow:0 16px 40px rgba(0,0,0,.18);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:3px;touch-action:none;user-select:none}
.devlog-fab-dot{width:8px;height:8px;border-radius:999px;background:var(--accent)}.devlog-fab-text{font-size:11px;font-weight:700}
.devlog-drawer{position:fixed;top:18px;right:18px;bottom:18px;width:min(380px,calc(100vw - 36px));z-index:2200;border:1px solid var(--border-soft);border-radius:22px;background:color-mix(in srgb,var(--bg-elevated) 96%,transparent);box-shadow:0 18px 48px rgba(0,0,0,.2);display:flex;flex-direction:column;overflow:hidden}
.devlog-header{padding:16px 16px 14px;border-bottom:1px solid var(--border-soft);display:flex;align-items:flex-start;justify-content:space-between;gap:12px}.devlog-title{font-size:18px;font-weight:700}.devlog-subtitle{margin-top:4px;font-size:12px;color:var(--text-secondary)}.devlog-close{border:1px solid var(--border-soft);border-radius:999px;background:transparent;padding:6px 12px;font-size:12px}
.devlog-empty{padding:24px 18px;color:var(--text-secondary);font-size:13px}.devlog-list{flex:1;min-height:0;overflow:auto;padding:14px;display:flex;flex-direction:column;gap:14px}.devlog-card{border:1px solid var(--border-soft);border-radius:16px;background:color-mix(in srgb,var(--bg-elevated-alt) 74%,transparent);padding:12px;display:flex;flex-direction:column;gap:12px}.devlog-card-head{display:flex;flex-direction:column;gap:6px}.devlog-card-title-row{display:flex;align-items:center;justify-content:space-between;gap:10px}.devlog-card-title{font-size:13px;font-weight:700;line-height:1.5;word-break:break-word}.devlog-chip{border-radius:999px;background:rgba(0,0,0,.06);padding:2px 8px;font-size:11px;color:var(--text-secondary)}.devlog-card-meta{display:flex;flex-wrap:wrap;gap:8px;font-size:11px;color:var(--text-secondary)}
.devlog-section{display:flex;flex-direction:column;gap:8px}.devlog-section-title{font-size:12px;font-weight:700}.devlog-entry{border-top:1px solid var(--border-soft);padding-top:8px}.devlog-entry:first-of-type{border-top:0;padding-top:0}.devlog-entry-summary{cursor:pointer;display:flex;align-items:center;justify-content:space-between;gap:10px;font-size:12px}.devlog-entry-kind{color:var(--text-secondary);text-transform:uppercase;font-size:10px}.devlog-entry-detail{margin-top:8px;white-space:pre-wrap;font-size:12px;line-height:1.6;color:var(--text-secondary)}.devlog-pre{margin:0;white-space:pre-wrap;word-break:break-word;font-size:11px;line-height:1.55;background:rgba(0,0,0,.05);border-radius:10px;padding:10px;max-height:220px;overflow:auto}
@media (max-width:720px){.devlog-fab{width:72px;height:72px}.devlog-fab-text{font-size:14px}.devlog-drawer{top:10px;right:10px;left:10px;bottom:10px;width:auto}}
</style>
