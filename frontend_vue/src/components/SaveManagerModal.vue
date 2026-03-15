<template>
  <Teleport to="body">
    <transition name="save-drawer-fade">
      <div v-if="saveStore.modalOpen" class="save-drawer-backdrop" @click.self="saveStore.closeModal()">
        <aside class="save-drawer-panel">
          <header class="save-drawer-header">
            <div>
              <h2 class="save-drawer-title">存档管理</h2>
              <p class="save-drawer-subtitle">按 Story、SessionState、StorySegment 管理当前故事链路。</p>
            </div>
            <div class="save-drawer-header-actions">
              <label class="dev-mode-toggle">
                <input :checked="saveStore.developerMode" type="checkbox" @change="saveStore.setDeveloperMode($event.target.checked)">
                <span>开发者模式</span>
              </label>
              <button class="modal-close-btn" type="button" aria-label="关闭" @click="saveStore.closeModal()">&times;</button>
            </div>
          </header>

          <div class="save-drawer-body">
            <section class="save-pane save-pane-left">
              <div class="save-pane-head">
                <span>Story 列表</span>
                <button class="btn-primary btn-small" type="button" @click="saveStore.createStory()">新建 Story</button>
              </div>
              <div v-if="saveStore.loading" class="save-pane-empty">正在加载存档...</div>
              <div v-else-if="!saveStore.storyTree.length" class="save-pane-empty">
                <div class="empty-title">暂无故事</div>
                <div class="empty-text">点击“新建 Story”创建第一条故事线。</div>
              </div>
              <div v-else class="story-list">
                <button
                  v-for="story in saveStore.storyTree"
                  :key="story.story_id"
                  type="button"
                  :class="['story-card', { active: saveStore.selectedStoryId === story.story_id }]"
                  @click="saveStore.selectStory(story.story_id)"
                >
                  <div class="story-card-top">
                    <strong>{{ story.story_title || story.story_id }}</strong>
                    <span class="story-badge">{{ story.session_count }} 个会话</span>
                  </div>
                  <div class="story-meta mono">{{ story.story_id }}</div>
                  <div class="story-meta-row">
                    <span>{{ story.total_word_count || 0 }} 字</span>
                    <span>{{ formatTime(story.updated_at) }}</span>
                  </div>
                </button>
              </div>
            </section>

            <section class="save-pane save-pane-right">
              <div v-if="!saveStore.currentDetail" class="save-pane-empty">
                <div class="empty-title">未选择 SessionState</div>
                <div class="empty-text">从左侧选择一个 Story，然后查看其下的 SessionState 与剧情片段。</div>
              </div>
              <template v-else>
                <div class="save-pane-head">
                  <span>当前详情</span>
                  <button class="btn-primary btn-small" type="button" @click="saveStore.loadSelectedIntoSession()">载入当前会话</button>
                </div>

                <div class="detail-grid">
                  <div class="detail-card"><span>Story</span><strong>{{ saveStore.currentDetail.story_title || '--' }}</strong></div>
                  <div class="detail-card"><span>Story ID</span><div class="mono">{{ saveStore.currentDetail.story_id || '--' }}</div></div>
                  <div class="detail-card"><span>SessionState</span><strong>{{ sessionName }}</strong></div>
                  <div class="detail-card"><span>Session ID</span><div class="mono">{{ saveStore.currentDetail.session_id || '--' }}</div></div>
                  <div class="detail-card"><span>剧情片段数</span><strong>{{ saveStore.currentDetail.segment_count || 0 }}</strong></div>
                  <div class="detail-card"><span>总字数</span><strong>{{ saveStore.currentDetail.total_word_count || 0 }}</strong></div>
                </div>

                <div class="detail-actions">
                  <button class="btn-secondary btn-small" type="button" @click="saveStore.openRename('story')">重命名 Story</button>
                  <button class="btn-secondary btn-small" type="button" @click="saveStore.openRename('session')">重命名 SessionState</button>
                  <button class="btn-primary btn-small" type="button" @click="saveStore.createSessionState()">新建 SessionState</button>
                  <button class="btn-secondary btn-small danger-btn" type="button" @click="saveStore.deleteSelected()">删除 SessionState</button>
                </div>

                <div class="detail-columns">
                  <section class="detail-panel">
                    <div class="panel-head">
                      <span>SessionState 列表</span>
                      <small>同一 Story 下的多个会话分支</small>
                    </div>
                    <div v-if="!sessionList.length" class="panel-empty">当前 Story 暂无 SessionState。</div>
                    <div v-else class="item-list">
                      <button
                        v-for="session in sessionList"
                        :key="session.session_id"
                        type="button"
                        :class="['item-card', { active: saveStore.selectedSaveId === session.session_id }]"
                        @click="saveStore.selectSave(session.session_id, saveStore.currentDetail.story_id)"
                      >
                        <strong>{{ session.branch_display_name || session.display_name || session.session_id }}</strong>
                        <div class="mono">{{ session.session_id }}</div>
                        <div class="item-meta-row">
                          <span>{{ session.segment_count || 0 }} 段</span>
                          <span>{{ session.total_word_count || 0 }} 字</span>
                          <span>{{ formatTime(session.updated_at) }}</span>
                        </div>
                      </button>
                    </div>
                  </section>

                  <section class="detail-panel">
                    <div class="panel-head">
                      <span>StorySegment 列表</span>
                      <small>当前 SessionState 的剧情片段</small>
                    </div>
                    <div v-if="!segmentList.length" class="panel-empty">当前 SessionState 暂无剧情片段。</div>
                    <div v-else class="item-list">
                      <div v-for="segment in segmentList" :key="segment.segment_id" class="item-card segment-card">
                        <strong>{{ segment.order_index }}. {{ truncate(segment.preview) }}</strong>
                        <div class="mono">{{ segment.segment_id }}</div>
                        <div class="item-meta-row">
                          <span>{{ segment.word_count || 0 }} 字</span>
                          <span>{{ formatTime(segment.created_at) }}</span>
                        </div>
                      </div>
                    </div>
                  </section>
                </div>
              </template>
            </section>
          </div>
        </aside>
      </div>
    </transition>

    <div v-if="saveStore.renameOpen" class="modal-overlay save-rename-overlay" @click.self="saveStore.closeRename()">
      <div class="modal-window save-rename-window">
        <div class="modal-header">
          <h3 class="modal-title">{{ saveStore.renameDialogTitle }}</h3>
          <button class="modal-close-btn" type="button" @click="saveStore.closeRename()">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-field-group">
            <label class="form-field-label">{{ saveStore.renameDialogLabel }}</label>
            <input v-model="saveStore.renameValue" class="form-field-input" type="text" @keydown.enter="saveStore.renameSelected()">
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" type="button" @click="saveStore.closeRename()">取消</button>
          <button class="btn-primary" type="button" @click="saveStore.renameSelected()">确认</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue';
import { useSaveManagerStore } from '../stores/saveManager';
import '../styles/save-manager-modal.css';

const saveStore = useSaveManagerStore();

const sessionList = computed(() => saveStore.currentDetail?.branches || []);
const segmentList = computed(() => saveStore.currentDetail?.segments || []);
const sessionName = computed(() => {
  return saveStore.currentDetail?.branch_display_name || saveStore.currentDetail?.display_name || '--';
});

function truncate(text = '') {
  const value = String(text || '').trim();
  return value.length > 96 ? `${value.slice(0, 96)}...` : value || '无预览内容';
}

function formatTime(value) {
  if (!value) return '刚刚';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return `${date.getFullYear()}-${`${date.getMonth() + 1}`.padStart(2, '0')}-${`${date.getDate()}`.padStart(2, '0')}`;
}
</script>
