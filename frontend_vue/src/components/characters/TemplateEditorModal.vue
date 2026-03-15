<template>
  <Teleport to="body">
    <div v-if="open" class="modal-overlay" @click.self="$emit('close')">
      <div class="modal-window template-editor-window">
        <div class="modal-header">
          <h3 class="modal-title">{{ createMode ? '新建角色模板' : '编辑角色模板' }}</h3>
          <button class="modal-close-btn" type="button" aria-label="关闭" @click="$emit('close')">&times;</button>
        </div>
        <div class="modal-body template-editor-body">
          <div class="template-meta-grid">
            <div class="field-block">
              <label class="form-label">模板 ID</label>
              <input :value="templateId" class="form-input" :disabled="!createMode" @input="$emit('update:templateId', $event.target.value)">
            </div>
            <div class="field-block">
              <label class="form-label">模板名称</label>
              <input :value="name" class="form-input" @input="$emit('update:name', $event.target.value)">
            </div>
          </div>
          <div class="field-block">
            <label class="form-label">模板配置 JSON</label>
            <textarea
              :value="config"
              class="form-textarea template-json-editor"
              rows="18"
              spellcheck="false"
              @input="$emit('update:config', $event.target.value)"
            ></textarea>
          </div>
          <div class="small-text muted">模板编辑采用通用 JSON 方式，修改后将直接用于角色渲染与动态角色生成。</div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" type="button" @click="$emit('close')">取消</button>
          <button class="btn-primary" type="button" @click="$emit('save')">{{ createMode ? '创建模板' : '保存模板' }}</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
defineProps({
  open: { type: Boolean, default: false },
  createMode: { type: Boolean, default: false },
  templateId: { type: String, default: '' },
  name: { type: String, default: '' },
  config: { type: String, default: '{}' },
});

defineEmits(['close', 'save', 'update:name', 'update:config', 'update:templateId']);
</script>

<style scoped>
.template-editor-window { max-width: 820px; width: min(820px, calc(100vw - 32px)); }
.template-editor-body { display: flex; flex-direction: column; gap: 16px; }
.template-meta-grid { display: grid; grid-template-columns: 220px minmax(0, 1fr); gap: 12px; }
.template-json-editor { min-height: 380px; font-family: "Cascadia Code", "Consolas", monospace; font-size: 13px; }
.modal-footer { display: flex; justify-content: flex-end; gap: 10px; padding: 0 24px 24px; }
@media (max-width: 820px) { .template-meta-grid { grid-template-columns: 1fr; } }
</style>
