<template>
  <div v-if="open" class="modal-overlay">
    <div class="modal-window font-modal">
      <div class="modal-header">
        <h3 class="modal-title">字体设置</h3>
        <button class="modal-close-btn" aria-label="关闭" @click="$emit('close')">&times;</button>
      </div>
      <div class="modal-body font-modal-body">
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
            <div class="typography-col typography-col-sm"><input :checked="modelValue[zone.key].bold" type="checkbox" class="form-checkbox" @change="updateZone(zone.key, 'bold', $event.target.checked)"></div>
          </div>
        </div>

        <div class="font-options-section">
          <label class="form-check font-indent-check">
            <input :checked="modelValue.bodyIndent" type="checkbox" class="form-checkbox" @change="$emit('update:modelValue', { ...modelValue, bodyIndent: $event.target.checked })">
            <span>正文首行缩进两个字符</span>
          </label>
        </div>

        <div class="small-text muted">这里的设置会同步到全局样式，并即时影响剧情正文的展示效果。</div>
      </div>
      <div class="modal-footer font-modal-footer">
        <button class="btn-secondary" @click="$emit('reset')">重置默认</button>
        <button class="btn-primary" @click="$emit('save')">保存设置</button>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({ open: { type: Boolean, required: true }, modelValue: { type: Object, required: true } });
const emit = defineEmits(['update:modelValue', 'close', 'save', 'reset']);
const zones = [
  { key: 'thinking', label: '思考过程', sizes: ['11px', '12px', '13px', '14px', '15px', '16px'] },
  { key: 'body', label: '正文', sizes: ['12px', '13px', '14px', '15px', '16px', '18px', '20px'] },
  { key: 'summary', label: '总结', sizes: ['11px', '12px', '13px', '14px', '15px', '16px'] },
  { key: 'raw', label: '原文', sizes: ['11px', '12px', '13px', '14px', '15px', '16px'] },
  { key: 'stats', label: '统计面板', sizes: ['11px', '12px', '13px', '14px', '15px'] },
];

function updateZone(zoneKey, field, value) {
  emit('update:modelValue', { ...props.modelValue, [zoneKey]: { ...props.modelValue[zoneKey], [field]: value } });
}
</script>

<style scoped>
.font-modal{max-width:680px;width:min(680px,calc(100vw - 24px))}
.font-modal-body{display:flex;flex-direction:column;gap:14px}
.typography-grid{display:flex;flex-direction:column;gap:10px}
.typography-row{display:grid;grid-template-columns:1.1fr 2fr 1fr .5fr;gap:10px;align-items:center;padding:10px 12px;border:1px solid var(--border-soft);border-radius:16px;background:color-mix(in srgb,var(--bg-elevated-alt) 72%,transparent)}
.typography-row--header{background:transparent;border:0;padding:0 4px;font-size:12px;color:var(--text-secondary)}
.typography-col-label{font-weight:700}
.typography-col-sm{display:flex;justify-content:center}
.font-options-section{padding-top:14px;border-top:1px solid var(--border-soft)}
.font-indent-check{display:flex;align-items:center;gap:8px}
.font-modal-footer{display:flex;justify-content:flex-end;gap:10px}
@media (max-width:720px){.font-modal{width:calc(100vw - 16px);max-width:none;max-height:calc(100dvh - 16px);margin:8px}.font-modal-body{padding-right:2px}.typography-row{grid-template-columns:1fr;gap:8px;padding:12px}.typography-row--header{display:none}.typography-col{display:flex;flex-direction:column;gap:6px}.typography-col::before{content:'';font-size:12px;color:var(--text-secondary)}.typography-col:nth-child(1)::before{content:'区域'}.typography-col:nth-child(2)::before{content:'字体样式'}.typography-col:nth-child(3)::before{content:'字体大小'}.typography-col:nth-child(4)::before{content:'加粗'}.typography-col-sm{justify-content:flex-start}.font-modal-footer{position:sticky;bottom:0;background:color-mix(in srgb,var(--bg-elevated) 96%,transparent);padding-top:12px;flex-direction:column}.font-modal-footer .btn-secondary,.font-modal-footer .btn-primary{width:100%}}
</style>
