<template>
  <Teleport to="body">
    <div v-if="saveStore.modalOpen" id="save-manager-modal" class="modal-overlay" @click.self="saveStore.closeModal()">
      <div class="modal-window save-manager-window">
        <div class="modal-header">
          <h3 class="modal-title">存档管理</h3>
          <button id="save-manager-close" class="modal-close-btn" aria-label="关闭" type="button" @click="saveStore.closeModal()">&times;</button>
        </div>
        <div class="modal-body save-manager-body">
          <div class="save-list-panel">
            <div class="save-list-header">
              <span class="save-list-title">所有存档</span>
              <button id="new-save-btn" class="btn-primary btn-small" type="button" @click="createSave">
                <svg viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none" style="margin-right: 4px;">
                  <line x1="12" y1="5" x2="12" y2="19"></line>
                  <line x1="5" y1="12" x2="19" y2="12"></line>
                </svg>
                新建存档
              </button>
            </div>
            <div class="save-list" id="save-list">
              <div v-if="!saveStore.saves.length" class="save-list-empty">
                <div class="empty-icon">📂</div>
                <div class="empty-text">暂无存档</div>
              </div>
              <button
                v-for="save in saveStore.saves"
                :key="save.session_id"
                class="save-list-item"
                :class="{ active: save.session_id === saveStore.selectedSaveId }"
                type="button"
                @click="saveStore.selectSave(save.session_id)"
              >
                <div class="save-item-title">{{ save.display_name || save.session_id }}</div>
                <div class="save-item-meta">{{ save.session_id }}</div>
              </button>
            </div>
          </div>

          <div class="save-detail-panel">
            <div class="save-detail-header">
              <span class="save-detail-title">存档详情</span>
            </div>
            <div class="save-detail-content" id="save-detail-content">
              <div v-if="!saveStore.currentDetail" class="save-detail-empty">
                <div class="empty-icon">📄</div>
                <div class="empty-text">选择一个存档查看详情</div>
              </div>
              <template v-else>
                <div class="save-detail-item">
                  <div class="detail-label">显示名称</div>
                  <div class="detail-value">{{ saveStore.currentDetail.display_name || saveStore.currentDetail.session_id }}</div>
                </div>
                <div class="save-detail-item">
                  <div class="detail-label">会话 ID</div>
                  <div class="detail-value">{{ saveStore.currentDetail.session_id }}</div>
                </div>
                <div class="save-detail-item">
                  <div class="detail-label">段落数</div>
                  <div class="detail-value">{{ saveStore.currentDetail.segment_count }}</div>
                </div>
                <div class="save-detail-item">
                  <div class="detail-label">总字数</div>
                  <div class="detail-value">{{ saveStore.currentDetail.total_word_count }}</div>
                </div>
                <div class="save-detail-actions">
                  <button class="btn-secondary btn-small" type="button" @click="saveStore.openRename()">重命名</button>
                  <button class="btn-secondary btn-small" style="color: var(--danger);" type="button" @click="deleteSave">删除</button>
                </div>
                <div class="save-segment-list">
                  <div class="save-list-title">最近内容</div>
                  <div
                    v-for="segment in saveStore.currentDetail.segments || []"
                    :key="segment.segment_id"
                    class="save-segment-item"
                  >
                    <div class="save-segment-title">{{ segment.order_index }}. {{ truncate(segment.user_input || segment.content_story || '无内容') }}</div>
                    <div class="save-segment-meta">{{ segment.segment_id }}</div>
                  </div>
                </div>
              </template>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button id="save-manager-cancel" class="btn-secondary" type="button" @click="saveStore.closeModal()">关闭</button>
          <button id="load-save-btn" class="btn-primary" :disabled="!saveStore.hasSelectedSave" type="button" @click="saveStore.loadSelectedIntoSession()">加载存档</button>
        </div>
      </div>
    </div>

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
  if (value.length <= 64) return value;
  return `${value.slice(0, 64)}...`;
}

async function createSave() {
  await saveStore.createSave();
}

async function deleteSave() {
  await saveStore.deleteSelected();
}
</script>
