<template>
  <div v-if="open" id="font-settings-modal" class="modal-overlay">
    <div class="modal-window" style="max-width: 500px;">
      <div class="modal-header">
        <h3 class="modal-title">字体设置</h3>
        <button class="modal-close-btn" aria-label="关闭" @click="$emit('close')">&times;</button>
      </div>
      <div class="modal-body">
        <div class="typography-grid">
          <div class="typography-row typography-row--header">
            <div class="typography-col typography-col-label">区域</div>
            <div class="typography-col">字体样式</div>
            <div class="typography-col">字体大小</div>
            <div class="typography-col typography-col-sm">加粗</div>
          </div>

          <div v-for="zone in zones" :key="zone.key" class="typography-row">
            <div class="typography-col typography-col-label">{{ zone.label }}</div>
            <div class="typography-col">
              <select :value="modelValue[zone.key].family" class="form-select" @change="updateZone(zone.key, 'family', $event.target.value)">
                <option value="system-ui, -apple-system, 'Segoe UI', sans-serif">系统无衬线</option>
                <option value="'Noto Serif SC','Songti SC','SimSun',serif">书卷衬线</option>
                <option value="'PingFang SC','Hiragino Sans GB','Microsoft YaHei',sans-serif">中文印刷体</option>
                <option value="'JetBrains Mono','SF Mono','Consolas',monospace">等宽打字机</option>
                <option value="'LXGW WenKai','STKaiti','KaiTi',serif">手写楷体</option>
              </select>
            </div>
            <div class="typography-col">
              <select :value="modelValue[zone.key].size" class="form-select" @change="updateZone(zone.key, 'size', $event.target.value)">
                <option v-for="size in zone.sizes" :key="size" :value="size">{{ size }}</option>
              </select>
            </div>
            <div class="typography-col typography-col-sm">
              <input
                :checked="modelValue[zone.key].bold"
                type="checkbox"
                class="form-checkbox"
                @change="updateZone(zone.key, 'bold', $event.target.checked)"
              >
            </div>
          </div>
        </div>

        <div class="font-options-section" style="margin-top: 16px; padding-top: 16px; border-top: 1px solid var(--border-soft);">
          <label class="form-check" style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
            <input
              :checked="modelValue.bodyIndent"
              type="checkbox"
              class="form-checkbox"
              @change="$emit('update:modelValue', { ...modelValue, bodyIndent: $event.target.checked })"
            >
            <span>正文首行缩进两字符</span>
          </label>
        </div>

        <div class="small-text muted" style="margin-top:12px;">
          设置会自动同步到全局设置页面。
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn-secondary" @click="$emit('reset')">重置默认</button>
        <button class="btn-primary" @click="$emit('save')">保存设置</button>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  open: {
    type: Boolean,
    required: true,
  },
  modelValue: {
    type: Object,
    required: true,
  },
});

const emit = defineEmits(['update:modelValue', 'close', 'save', 'reset']);

const zones = [
  { key: 'thinking', label: '思考过程', sizes: ['11px', '12px', '13px', '14px', '15px', '16px'] },
  { key: 'body', label: '正文', sizes: ['12px', '13px', '14px', '15px', '16px', '18px', '20px'] },
  { key: 'summary', label: '总结', sizes: ['11px', '12px', '13px', '14px', '15px', '16px'] },
  { key: 'raw', label: '原文', sizes: ['11px', '12px', '13px', '14px', '15px', '16px'] },
  { key: 'stats', label: '统计面板', sizes: ['11px', '12px', '13px', '14px', '15px'] },
];

function updateZone(zoneKey, field, value) {
  emit('update:modelValue', {
    ...props.modelValue,
    [zoneKey]: {
      ...props.modelValue[zoneKey],
      [field]: value,
    },
  });
}
</script>
