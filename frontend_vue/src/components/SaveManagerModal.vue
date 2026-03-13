<template>
  <Teleport to="body">
    <transition name="save-drawer-fade">
      <div v-if="saveStore.modalOpen" class="save-drawer-backdrop" @click.self="saveStore.closeModal()">
        <transition name="save-drawer-slide">
          <aside v-if="saveStore.modalOpen" class="save-drawer-panel">
            <header class="save-drawer-header">
              <div>
                <div class="save-drawer-title">存档管理</div>
                <div class="save-drawer-subtitle">点击顶部存档区块即可打开这里</div>
              </div>
              <button class="modal-close-btn" aria-label="关闭" type="button" @click="saveStore.closeModal()">&times;</button>
            </header>

            <div class="save-drawer-body">
              <section class="save-drawer-list">
                <div class="save-drawer-section-head">
                  <span>所有存档</span>
                  <button class="btn-primary btn-small" type="button" @click="createSave">新建存档</button>
                </div>

                <div v-if="saveStore.loading" class="save-drawer-empty">正在加载存档…</div>

                <div v-else-if="!saveStore.saves.length" class="save-drawer-empty">
                  <div class="empty-icon">📁</div>
                  <div class="empty-text">暂无存档</div>
                  <div class="empty-desc">点击“新建存档”创建一个新的会话存档。</div>
                </div>

                <div v-else class="save-drawer-list-items">
                  <button
                    v-for="item in saveStore.saves"
                    :key="item.session_id"
                    type="button"
                    :class="['save-drawer-list-item', { active: saveStore.selectedSaveId === item.session_id }]"
                    @click="saveStore.selectSave(item.session_id)"
                  >
                    <div class="save-item-main">
                      <div class="save-item-name">{{ item.display_name || item.session_id }}</div>
                      <div class="save-item-id">{{ item.session_id }}</div>
                    </div>
                    <div class="save-item-meta">
                      <span>{{ item.segment_count || 0 }} 段</span>
                      <span>{{ item.total_word_count || 0 }} 字</span>
                    </div>
                  </button>
                </div>
              </section>

              <section class="save-drawer-detail">
                <div class="save-drawer-section-head">
                  <span>存档详情</span>
                </div>

                <div v-if="!saveStore.currentDetail" class="save-drawer-empty detail-empty">
                  <div class="empty-icon">🗂️</div>
                  <div class="empty-text">选择一个存档查看详情</div>
                </div>

                <template v-else>
                  <div class="save-detail-grid">
                    <div class="save-detail-card">
                      <div class="detail-label">显示名称</div>
                      <div class="detail-value strong">{{ saveStore.currentDetail.display_name || saveStore.currentDetail.session_id }}</div>
                    </div>
                    <div class="save-detail-card">
                      <div class="detail-label">会话 ID</div>
                      <div class="detail-value mono">{{ saveStore.currentDetail.session_id }}</div>
                    </div>
                    <div class="save-detail-card">
                      <div class="detail-label">段落数</div>
                      <div class="detail-value">{{ saveStore.currentDetail.segment_count }}</div>
                    </div>
                    <div class="save-detail-card">
                      <div class="detail-label">总字数</div>
                      <div class="detail-value">{{ saveStore.currentDetail.total_word_count }}</div>
                    </div>
                  </div>

                  <div class="save-detail-actions">
                    <button class="btn-secondary btn-small" type="button" @click="saveStore.openRename()">重命名</button>
                    <button class="btn-secondary btn-small danger-btn" type="button" @click="deleteSave">删除</button>
                    <button class="btn-primary btn-small" type="button" @click="saveStore.loadSelectedIntoSession()">加载到当前</button>
                  </div>

                  <div class="save-detail-segments">
                    <div class="save-list-title">最近内容</div>
                    <div v-if="!(saveStore.currentDetail.segments || []).length" class="save-drawer-empty compact-empty">
                      当前存档还没有剧情段落。
                    </div>
                    <div v-else class="save-segment-list">
                      <div
                        v-for="segment in saveStore.currentDetail.segments || []"
                        :key="segment.segment_id"
                        class="save-segment-item"
                      >
                        <div class="save-segment-title">{{ segment.order_index }}. {{ truncate(segment.preview || segment.user_input || segment.content_story || '无内容') }}</div>
                        <div class="save-segment-meta">{{ segment.segment_id }}</div>
                      </div>
                    </div>
                  </div>
                </template>
              </section>
            </div>
          </aside>
        </transition>
      </div>
    </transition>

    <div v-if="saveStore.renameOpen" id="rename-save-modal" class="modal-overlay" @click.self="saveStore.closeRename()">
      <div class="modal-window" style="max-width: 400px;">
        <div class="modal-header">
          <h3 class="modal-title">重命名存档</h3>
          <button id="rename-modal-close" class="modal-close-btn" aria-label="关闭" type="button" @click="saveStore.closeRename()">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-field-group">
            <label class="form-field-label">存档名称</label>
            <input id="rename-input" v-model="saveStore.renameValue" type="text" class="form-field-input" placeholder="输入新的存档名称">
          </div>
        </div>
        <div class="modal-footer">
          <button id="rename-cancel" class="btn-secondary" type="button" @click="saveStore.closeRename()">取消</button>
          <button id="rename-confirm" class="btn-primary" type="button" @click="saveStore.renameSelected()">确认</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { useSaveManagerStore } from '../stores/saveManager';

const saveStore = useSaveManagerStore();

function truncate(text) {
  const value = `${text || ''}`.trim();
  if (value.length <= 96) return value;
  return `${value.slice(0, 96)}...`;
}

async function createSave() {
  await saveStore.createSave();
}

async function deleteSave() {
  await saveStore.deleteSelected();
}
</script>

<style scoped>
.save-drawer-backdrop {
  position: fixed;
  inset: 0;
  z-index: 2000;
  display: flex;
  justify-content: flex-end;
  background: rgba(10, 14, 24, 0.22);
  backdrop-filter: blur(6px);
}

.save-drawer-panel {
  width: min(860px, 92vw);
  height: 100vh;
  background: var(--bg-elevated);
  border-left: 1px solid var(--border-soft);
  box-shadow: -20px 0 48px rgba(0, 0, 0, 0.16);
  display: flex;
  flex-direction: column;
}

.save-drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 22px 24px 18px;
  border-bottom: 1px solid var(--border-soft);
  background: color-mix(in srgb, var(--bg-elevated-alt) 92%, transparent);
}

.save-drawer-title {
  font-size: 28px;
  font-weight: 700;
}

.save-drawer-subtitle {
  margin-top: 6px;
  font-size: 13px;
  color: var(--text-secondary);
}

.save-drawer-body {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 18px;
  padding: 20px;
}

.save-drawer-list,
.save-drawer-detail {
  min-height: 0;
  border: 1px solid var(--border-soft);
  border-radius: 18px;
  background: color-mix(in srgb, var(--bg-elevated) 96%, transparent);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.save-drawer-section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 18px;
  border-bottom: 1px solid var(--border-soft);
  background: color-mix(in srgb, var(--bg-elevated-alt) 92%, transparent);
  font-size: 18px;
  font-weight: 700;
}

.save-drawer-list-items,
.save-detail-segments {
  overflow: auto;
}

.save-drawer-list-items {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.save-drawer-list-item {
  width: 100%;
  padding: 14px;
  border: 1px solid var(--border-soft);
  border-radius: 14px;
  background: color-mix(in srgb, var(--bg-elevated-alt) 74%, transparent);
  text-align: left;
  color: var(--text-primary);
}

.save-drawer-list-item.active {
  border-color: var(--accent);
  box-shadow: 0 0 0 1px color-mix(in srgb, var(--accent) 26%, transparent);
}

.save-item-name,
.detail-value.strong {
  font-weight: 700;
}

.save-item-id,
.detail-value.mono,
.save-segment-meta {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  color: var(--text-secondary);
}

.save-item-meta {
  margin-top: 8px;
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: var(--text-secondary);
}

.save-drawer-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 10px;
  padding: 24px;
  color: var(--text-secondary);
  text-align: center;
}

.compact-empty {
  min-height: 120px;
}

.detail-empty {
  min-height: 280px;
}

.empty-icon {
  font-size: 32px;
}

.empty-text {
  font-size: 18px;
  color: var(--text-primary);
}

.empty-desc {
  font-size: 13px;
}

.save-detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  padding: 16px;
}

.save-detail-card {
  padding: 14px;
  border: 1px solid var(--border-soft);
  border-radius: 14px;
  background: color-mix(in srgb, var(--bg-elevated-alt) 72%, transparent);
}

.detail-label {
  margin-bottom: 8px;
  font-size: 12px;
  color: var(--text-secondary);
}

.detail-value {
  font-size: 16px;
  line-height: 1.5;
  word-break: break-all;
}

.save-detail-actions {
  display: flex;
  gap: 10px;
  padding: 0 16px 16px;
}

.danger-btn {
  color: var(--danger);
}

.save-detail-segments {
  flex: 1;
  min-height: 0;
  padding: 0 16px 16px;
}

.save-segment-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 12px;
}

.save-segment-item {
  padding: 12px 14px;
  border: 1px solid var(--border-soft);
  border-radius: 14px;
  background: color-mix(in srgb, var(--bg-elevated-alt) 68%, transparent);
}

.save-segment-title {
  line-height: 1.6;
}

.save-drawer-fade-enter-active,
.save-drawer-fade-leave-active,
.save-drawer-slide-enter-active,
.save-drawer-slide-leave-active {
  transition: all 0.22s ease;
}

.save-drawer-fade-enter-from,
.save-drawer-fade-leave-to {
  opacity: 0;
}

.save-drawer-slide-enter-from,
.save-drawer-slide-leave-to {
  transform: translateX(24px);
  opacity: 0;
}

@media (max-width: 900px) {
  .save-drawer-panel {
    width: 100vw;
  }

  .save-drawer-body {
    grid-template-columns: 1fr;
  }

  .save-detail-grid {
    grid-template-columns: 1fr;
  }
}
</style>
