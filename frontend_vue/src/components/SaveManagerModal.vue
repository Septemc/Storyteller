<template>
  <Teleport to="body">
    <transition name="save-drawer-fade">
      <div v-if="saveStore.modalOpen" class="save-drawer-backdrop" @click.self="saveStore.closeModal()">
        <transition name="save-drawer-slide">
          <aside v-if="saveStore.modalOpen" class="save-drawer-panel">
            <header class="save-drawer-header">
              <div>
                <div class="save-drawer-title">存档管理</div>
                <div class="save-drawer-subtitle">按故事、存档、分支、剧情片段管理当前叙事</div>
              </div>
              <div class="save-drawer-header-actions">
                <label class="dev-mode-toggle">
                  <input :checked="saveStore.developerMode" type="checkbox" @change="saveStore.setDeveloperMode($event.target.checked)">
                  <span>开发者模式</span>
                </label>
                <button class="modal-close-btn" aria-label="close" type="button" @click="saveStore.closeModal()">&times;</button>
              </div>
            </header>

            <div class="save-drawer-body">
              <section class="save-drawer-list">
                <div class="save-drawer-section-head">
                  <span>故事与存档</span>
                  <button class="btn-primary btn-small" type="button" @click="createStory">新建存档</button>
                </div>
                <div v-if="saveStore.loading" class="save-drawer-empty">正在加载存档...</div>
                <div v-else-if="!saveStore.storyGroups.length" class="save-drawer-empty">
                  <div class="empty-text">暂无存档</div>
                  <div class="empty-desc">点击“新建存档”创建新的故事。</div>
                </div>
                <div v-else class="save-drawer-list-items">
                  <button
                    v-for="group in saveStore.storyGroups"
                    :key="group.story_id"
                    type="button"
                    :class="['story-group-card', { active: saveStore.selectedStoryId === group.story_id }]"
                    @click="saveStore.selectStory(group.story_id)"
                  >
                    <div class="story-group-title-row">
                      <div class="story-group-title">{{ group.story_title || group.story_id }}</div>
                      <div class="story-group-badge">{{ group.branch_count }} 分支</div>
                    </div>
                    <div class="story-group-subtitle">{{ group.story_id }}</div>
                    <div class="story-group-meta">
                      <span>{{ group.total_word_count || 0 }} 字</span>
                      <span>{{ formatTime(group.updated_at) }}</span>
                    </div>
                    <div v-if="group.branches.length" class="story-branch-preview">
                      <div class="story-branch-preview-label">当前分支</div>
                      <div class="story-branch-preview-name">{{ activeBranchName(group) }}</div>
                      <div class="story-branch-preview-id">{{ activeBranchId(group) }}</div>
                    </div>
                  </button>
                </div>
              </section>

              <section class="save-drawer-detail">
                <div class="save-drawer-section-head"><span>当前详情</span></div>
                <div v-if="!saveStore.currentDetail" class="save-drawer-empty detail-empty"><div class="empty-text">选择一个故事查看分支详情</div></div>
                <template v-else>
                  <div class="save-detail-grid">
                    <div class="save-detail-card">
                      <div class="detail-label">故事</div>
                      <div class="detail-value strong">{{ saveStore.currentDetail.story_title || '--' }}</div>
                    </div>
                    <div class="save-detail-card">
                      <div class="detail-label">故事 ID</div>
                      <div class="detail-value mono">{{ saveStore.currentDetail.story_id || '--' }}</div>
                    </div>
                    <div class="save-detail-card">
                      <div class="detail-label">当前分支</div>
                      <div class="detail-value strong">{{ saveStore.currentDetail.branch_display_name || '--' }}</div>
                    </div>
                    <div class="save-detail-card">
                      <div class="detail-label">存档 / Session</div>
                      <div class="detail-value mono">{{ saveStore.currentDetail.session_id || '--' }}</div>
                    </div>
                    <div class="save-detail-card">
                      <div class="detail-label">推理强度</div>
                      <div class="detail-value">{{ saveStore.currentDetail.reasoning_strength || '--' }}</div>
                    </div>
                    <div class="save-detail-card">
                      <div class="detail-label">分支数</div>
                      <div class="detail-value">{{ saveStore.currentDetail.story_branch_count || 0 }}</div>
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

                  <div class="save-detail-actions split">
                    <div class="action-group">
                      <button class="btn-secondary btn-small" type="button" @click="saveStore.openRename('story')">重命名故事</button>
                      <button class="btn-primary btn-small" type="button" @click="createBranch">新建分支</button>
                    </div>
                    <div class="action-group">
                      <button class="btn-secondary btn-small" type="button" @click="saveStore.openRename('branch')">重命名分支</button>
                      <button class="btn-secondary btn-small danger-btn" type="button" @click="deleteSave">删除分支</button>
                      <button class="btn-primary btn-small" type="button" @click="saveStore.loadSelectedIntoSession()">载入当前</button>
                    </div>
                  </div>

                  <div class="save-detail-section branch-section">
                    <div class="save-list-title-row">
                      <div class="save-list-title">分支列表</div>
                      <div class="save-list-subtitle">点击切换分支；列表支持上下滚动</div>
                    </div>
                    <div v-if="!(saveStore.currentDetail.branches || []).length" class="save-drawer-empty compact-empty">当前故事还没有分支。</div>
                    <div v-else class="save-branch-list">
                      <button
                        v-for="branch in saveStore.currentDetail.branches || []"
                        :key="branch.branch_id"
                        type="button"
                        :class="['save-segment-item', 'branch-item', { active: saveStore.selectedSaveId === branch.session_id }]"
                        @click="saveStore.selectSave(branch.session_id, { storyId: saveStore.currentDetail.story_id })"
                      >
                        <div class="save-segment-title">{{ branch.display_name || branch.branch_type || '未命名分支' }}</div>
                        <div class="save-segment-meta">{{ branch.session_id }}</div>
                        <div class="branch-item-meta">
                          <span>{{ branch.branch_type || 'branch' }}</span>
                          <span>{{ branch.segment_count || 0 }} 段</span>
                          <span>{{ branch.reasoning_strength || 'low' }}</span>
                          <span>{{ branch.status || 'active' }}</span>
                        </div>
                      </button>
                    </div>
                  </div>

                  <div class="save-detail-section segment-section">
                    <div class="save-list-title">剧情片段</div>
                    <div v-if="!(saveStore.currentDetail.segments || []).length" class="save-drawer-empty compact-empty">当前分支还没有剧情片段。</div>
                    <div v-else class="save-segment-list">
                      <div v-for="segment in saveStore.currentDetail.segments || []" :key="segment.segment_id" class="save-segment-item">
                        <div class="save-segment-title">{{ segment.order_index }}. {{ truncate(segment.preview || '无内容') }}</div>
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

    <div v-if="saveStore.renameOpen" id="rename-save-modal" class="modal-overlay save-rename-overlay" @click.self="saveStore.closeRename()">
      <div class="modal-window save-rename-window">
        <div class="modal-header">
          <h3 class="modal-title">{{ saveStore.renameDialogTitle }}</h3>
          <button id="rename-modal-close" class="modal-close-btn" type="button" @click="saveStore.closeRename()">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-field-group">
            <label class="form-field-label">{{ saveStore.renameDialogLabel }}</label>
            <input id="rename-input" v-model="saveStore.renameValue" type="text" class="form-field-input" :placeholder="`输入新的${saveStore.renameDialogLabel}`" @keydown.enter="saveStore.renameSelected()">
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
  return value.length <= 96 ? value : `${value.slice(0, 96)}...`;
}

function formatTime(value) {
  if (!value) return '刚刚';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return `${date.getFullYear()}-${`${date.getMonth() + 1}`.padStart(2, '0')}-${`${date.getDate()}`.padStart(2, '0')}`;
}

function activeBranchName(group) {
  const branch = group.branches.find((item) => item.session_id === group.selected_session_id) || group.branches[0];
  return branch?.branch_display_name || branch?.display_name || branch?.session_id || '--';
}

function activeBranchId(group) {
  const branch = group.branches.find((item) => item.session_id === group.selected_session_id) || group.branches[0];
  return branch?.session_id || '--';
}

async function createStory() {
  await saveStore.createStory();
}

async function createBranch() {
  await saveStore.createBranch();
}

async function deleteSave() {
  await saveStore.deleteSelected();
}
</script>

<style scoped>
.save-drawer-backdrop { position: fixed; inset: 0; z-index: 2000; display: flex; justify-content: flex-end; background: rgba(26, 20, 8, 0.18); backdrop-filter: blur(6px); }
.save-drawer-panel {
  --save-paper-bg: #f8f1e3;
  --save-paper-alt: #eadcbf;
  --save-paper-card: #fbf5e8;
  --save-paper-card-strong: #f6ebd3;
  --save-paper-border: #ccb07a;
  --save-paper-accent: #b06f46;
  --save-paper-text: #5a3d26;
  --save-paper-text-soft: #94744b;
  width: min(1180px, 96vw);
  height: 100vh;
  background: linear-gradient(180deg, #fbf6ea 0%, #f6eedf 100%);
  border-left: 1px solid var(--save-paper-border);
  box-shadow: -20px 0 48px rgba(62, 41, 18, 0.14);
  display: flex;
  flex-direction: column;
  color: var(--save-paper-text);
}
.save-drawer-header { display: flex; align-items: center; justify-content: space-between; padding: 18px 22px 14px; border-bottom: 1px solid var(--save-paper-border); background: linear-gradient(180deg, #efe4c8 0%, #eadfc2 100%); }
.save-drawer-header-actions { display: flex; align-items: center; gap: 14px; }
.save-drawer-title { font-size: 24px; font-weight: 700; color: var(--save-paper-text); }
.save-drawer-subtitle { margin-top: 4px; font-size: 12px; color: var(--save-paper-text-soft); }
.dev-mode-toggle { display: flex; align-items: center; gap: 8px; font-size: 13px; color: var(--save-paper-text-soft); }
.save-drawer-body { flex: 1; min-height: 0; display: grid; grid-template-columns: 360px 1fr; gap: 18px; padding: 20px; }
.save-drawer-list, .save-drawer-detail { min-height: 0; border: 1px solid var(--save-paper-border); border-radius: 18px; background: linear-gradient(180deg, var(--save-paper-bg) 0%, #f9f2e4 100%); overflow: hidden; display: flex; flex-direction: column; }
.save-drawer-section-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 14px 18px; border-bottom: 1px solid var(--save-paper-border); background: linear-gradient(180deg, var(--save-paper-alt) 0%, #e7dbbd 100%); font-size: 16px; font-weight: 700; color: var(--save-paper-text); }
.save-drawer-list-items, .save-detail-section { overflow: auto; }
.save-drawer-list-items { padding: 12px; display: flex; flex-direction: column; gap: 12px; }
.story-group-card { width: 100%; border: 1px solid var(--save-paper-border); border-radius: 16px; padding: 14px; background: linear-gradient(180deg, #f4ead2 0%, #f7efdf 100%); text-align: left; color: var(--save-paper-text); }
.story-group-card.active { border-color: var(--save-paper-accent); box-shadow: 0 0 0 1px rgba(176, 111, 70, 0.28); }
.story-group-title-row { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.story-group-title { font-weight: 700; font-size: 16px; }
.story-group-badge { padding: 4px 10px; border-radius: 999px; background: #edd8b2; color: var(--save-paper-accent); font-size: 12px; font-weight: 700; }
.story-group-subtitle, .save-item-id, .detail-value.mono, .save-segment-meta, .story-branch-preview-id { font-family: 'JetBrains Mono', monospace; font-size: 12px; color: var(--save-paper-text-soft); }
.story-group-subtitle { margin-top: 6px; }
.story-group-meta { margin-top: 10px; display: flex; align-items: center; justify-content: space-between; gap: 12px; font-size: 12px; color: var(--save-paper-text-soft); }
.story-branch-preview { margin-top: 12px; padding: 10px 12px; border: 1px solid var(--save-paper-border); border-radius: 14px; background: linear-gradient(180deg, #fcf7ec 0%, #f8f1e3 100%); }
.story-branch-preview-label { margin-bottom: 4px; font-size: 12px; color: var(--save-paper-text-soft); }
.story-branch-preview-name { font-weight: 700; }
.story-branch-preview-id { margin-top: 4px; }
.save-drawer-empty { flex: 1; display: flex; flex-direction: column; justify-content: center; align-items: center; gap: 10px; padding: 24px; color: var(--save-paper-text-soft); text-align: center; }
.compact-empty { min-height: 120px; }
.detail-empty { min-height: 280px; }
.empty-text { font-size: 18px; color: var(--save-paper-text); }
.empty-desc { font-size: 13px; }
.save-detail-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; padding: 12px 14px; }
.save-detail-card { padding: 10px 12px; border: 1px solid var(--save-paper-border); border-radius: 14px; background: linear-gradient(180deg, var(--save-paper-card-strong) 0%, var(--save-paper-card) 100%); min-height: 78px; }
.detail-label { margin-bottom: 6px; font-size: 11px; color: var(--save-paper-text-soft); }
.detail-value { font-size: 13px; line-height: 1.4; word-break: break-all; }
.detail-value.strong { font-weight: 700; }
.save-detail-actions { display: flex; gap: 10px; padding: 0 14px 12px; flex-wrap: wrap; }
.save-detail-actions.split { justify-content: space-between; }
.action-group { display: flex; gap: 10px; flex-wrap: wrap; }
.danger-btn { color: var(--danger); }
.save-detail-section { min-height: 0; padding: 0 14px 12px; }
.branch-section { flex: 0 0 200px; padding-bottom: 10px; }
.segment-section { flex: 1 1 auto; min-height: 220px; }
.save-list-title-row { display: flex; align-items: baseline; justify-content: space-between; gap: 12px; margin-bottom: 12px; }
.save-list-title { font-size: 14px; font-weight: 700; color: var(--save-paper-text); }
.save-list-subtitle { font-size: 12px; color: var(--save-paper-text-soft); }
.save-branch-list { max-height: 180px; overflow: auto; display: flex; flex-direction: column; gap: 8px; padding-right: 4px; }
.save-segment-list { display: flex; flex-direction: column; gap: 8px; margin-top: 10px; overflow: auto; }
.save-segment-item { padding: 10px 12px; border: 1px solid var(--save-paper-border); border-radius: 14px; background: linear-gradient(180deg, #f8efd9 0%, #f9f2e3 100%); }
.branch-item { width: 100%; text-align: left; color: var(--save-paper-text); }
.branch-item.active { border-color: var(--save-paper-accent); box-shadow: 0 0 0 1px rgba(176, 111, 70, 0.28); }
.save-segment-title { line-height: 1.45; font-size: 13px; }
.branch-item-meta { margin-top: 8px; display: flex; gap: 10px; flex-wrap: wrap; font-size: 11px; color: var(--save-paper-text-soft); }
.save-drawer-fade-enter-active, .save-drawer-fade-leave-active, .save-drawer-slide-enter-active, .save-drawer-slide-leave-active { transition: all 0.22s ease; }
.save-drawer-fade-enter-from, .save-drawer-fade-leave-to { opacity: 0; }
.save-drawer-slide-enter-from, .save-drawer-slide-leave-to { transform: translateX(24px); opacity: 0; }
.save-rename-overlay { z-index: 2200; }
.save-rename-window { max-width: 420px; }
@media (max-width: 900px) {
  .save-drawer-panel { width: 100vw; }
  .save-drawer-body { grid-template-columns: 1fr; }
  .save-detail-grid { grid-template-columns: 1fr; }
  .save-detail-actions.split { justify-content: flex-start; }
  .save-list-title-row { flex-direction: column; align-items: flex-start; }
}
@media (max-width: 1320px) {
  .save-detail-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
</style>
