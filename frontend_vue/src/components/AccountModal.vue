<template>
  <Teleport to="body">
    <div v-if="open" id="account-modal" class="modal-overlay" style="display: flex;" @click.self="emit('update:open', false)">
      <div class="modal-window account-manager-window">
        <div class="modal-header">
          <h3 class="modal-title">账号管理</h3>
          <button id="account-modal-close" class="modal-close-btn" aria-label="关闭" type="button" @click="emit('update:open', false)">&times;</button>
        </div>
        <div class="modal-body account-manager-body">
          <div class="account-sidebar">
            <div class="account-nav-item" :class="{ active: currentTab === 'profile' }" @click="currentTab = 'profile'">个人中心</div>
            <div class="account-nav-item" :class="{ active: currentTab === 'guide' }" @click="currentTab = 'guide'">使用指南</div>
            <div class="account-nav-item" :class="{ active: currentTab === 'settings' }" @click="currentTab = 'settings'">账户设置</div>
            <div class="account-nav-item" :class="{ active: currentTab === 'logout' }" @click="currentTab = 'logout'">退出登录</div>
          </div>

          <div class="account-content">
            <div v-show="currentTab === 'profile'" class="account-tab-pane active">
              <div class="account-section">
                <div class="account-section-title">基本资料</div>
                <div class="profile-card">
                  <div class="profile-avatar">
                    <div class="avatar-placeholder" id="profile-avatar">
                      <svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" stroke-width="1.5">
                        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                        <circle cx="12" cy="7" r="4"/>
                      </svg>
                    </div>
                  </div>
                  <div class="profile-info">
                    <div class="profile-name" id="profile-name">{{ profile.nickname || profile.username || '未登录' }}</div>
                    <div class="profile-role" id="profile-role">{{ profile.role || '-' }}</div>
                  </div>
                </div>
                <div class="profile-details">
                  <div class="profile-detail-item">
                    <span class="detail-label">用户名</span>
                    <span class="detail-value" id="profile-username">{{ profile.username || '-' }}</span>
                  </div>
                  <div class="profile-detail-item">
                    <span class="detail-label">昵称</span>
                    <span class="detail-value" id="profile-nickname">{{ profile.nickname || '-' }}</span>
                  </div>
                  <div class="profile-detail-item">
                    <span class="detail-label">邮箱</span>
                    <span class="detail-value" id="profile-email">{{ profile.email || '-' }}</span>
                  </div>
                  <div class="profile-detail-item">
                    <span class="detail-label">注册时间</span>
                    <span class="detail-value" id="profile-created">{{ formatDate(profile.created_at) }}</span>
                  </div>
                </div>
              </div>

              <div class="account-section">
                <div class="account-section-title">数据统计</div>
                <div class="stats-grid">
                  <div class="stat-card">
                    <div class="stat-value" id="stat-stories">{{ stats.stories }}</div>
                    <div class="stat-label">故事片段</div>
                  </div>
                  <div class="stat-card">
                    <div class="stat-value" id="stat-characters">{{ stats.characters }}</div>
                    <div class="stat-label">角色数量</div>
                  </div>
                  <div class="stat-card">
                    <div class="stat-value" id="stat-worldbook">{{ stats.worldbook }}</div>
                    <div class="stat-label">世界书条目</div>
                  </div>
                  <div class="stat-card">
                    <div class="stat-value" id="stat-words">{{ stats.words }}</div>
                    <div class="stat-label">总字数</div>
                  </div>
                </div>
              </div>
            </div>

            <div v-show="currentTab === 'guide'" class="account-tab-pane active">
              <div class="account-section">
                <div class="account-section-title">系统使用指南</div>
                <div class="guide-content">
                  <div class="guide-item">
                    <div class="guide-header"><span class="guide-title">快速入门</span></div>
                    <div class="guide-body">
                      <ul>
                        <li>剧情页负责推进故事与存档。</li>
                        <li>角色页负责角色维护与主角切换。</li>
                        <li>世界书与剧本页负责设定与剧情骨架。</li>
                        <li>设置页负责主题、预设、正则与 API 配置。</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div v-show="currentTab === 'settings'" class="account-tab-pane active">
              <div class="account-section">
                <div class="account-section-title">个人信息</div>
                <div class="settings-form">
                  <div class="form-group">
                    <label class="form-label">昵称</label>
                    <input v-model="profileForm.nickname" type="text" class="form-input" placeholder="输入昵称">
                  </div>
                  <div class="form-group">
                    <label class="form-label">邮箱</label>
                    <input v-model="profileForm.email" type="email" class="form-input" placeholder="输入邮箱">
                  </div>
                  <button class="btn-primary" type="button" @click="saveProfile">保存修改</button>
                </div>
              </div>

              <div class="account-section">
                <div class="account-section-title">安全设置</div>
                <div class="settings-form">
                  <div class="form-group">
                    <label class="form-label">当前密码</label>
                    <input v-model="passwordForm.current_password" type="password" class="form-input" placeholder="输入当前密码">
                  </div>
                  <div class="form-group">
                    <label class="form-label">新密码</label>
                    <input v-model="passwordForm.new_password" type="password" class="form-input" placeholder="输入新密码">
                  </div>
                  <button class="btn-primary" type="button" @click="savePassword">修改密码</button>
                </div>
              </div>

              <div v-if="message" class="small-text" :style="{ color: messageType === 'error' ? 'var(--danger)' : 'var(--accent)' }">{{ message }}</div>
            </div>

            <div v-show="currentTab === 'logout'" class="account-tab-pane active">
              <div class="logout-section">
                <div class="logout-title">退出当前账号</div>
                <div class="logout-desc">退出后将返回登录页。</div>
                <button class="btn-danger btn-large" type="button" @click="handleLogout">退出登录</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { reactive, ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import * as authApi from '../services/modules/auth';
import * as storyApi from '../services/modules/story';

const props = defineProps({
  open: {
    type: Boolean,
    default: false,
  },
  initialTab: {
    type: String,
    default: 'profile',
  },
});

const emit = defineEmits(['update:open']);
const router = useRouter();
const authStore = useAuthStore();
const currentTab = ref('profile');
const profile = reactive({});
const stats = reactive({
  stories: 0,
  characters: 0,
  worldbook: 0,
  words: 0,
});
const profileForm = reactive({
  nickname: '',
  email: '',
});
const passwordForm = reactive({
  current_password: '',
  new_password: '',
});
const message = ref('');
const messageType = ref('success');

function setMessage(text, type = 'success') {
  message.value = text;
  messageType.value = type;
}

function formatDate(value) {
  if (!value) return '-';
  try {
    return new Date(value).toLocaleString('zh-CN');
  } catch {
    return value;
  }
}

async function loadData() {
  if (!authStore.isAuthed) return;
  const [profileData, statsData] = await Promise.all([
    authApi.profile(),
    storyApi.stats().catch(() => null),
  ]);

  Object.assign(profile, profileData || {});
  profileForm.nickname = profileData?.nickname || '';
  profileForm.email = profileData?.email || '';
  stats.stories = statsData?.stories || 0;
  stats.characters = statsData?.characters || 0;
  stats.worldbook = statsData?.worldbook || 0;
  stats.words = statsData?.words || 0;
}

async function saveProfile() {
  try {
    const updated = await authApi.updateProfile({
      nickname: profileForm.nickname,
      email: profileForm.email,
    });
    authStore.user = updated;
    authStore.persist();
    Object.assign(profile, updated);
    setMessage('资料已更新');
  } catch (error) {
    setMessage(error.message, 'error');
  }
}

async function savePassword() {
  try {
    await authApi.updatePassword({ ...passwordForm });
    passwordForm.current_password = '';
    passwordForm.new_password = '';
    setMessage('密码已更新');
  } catch (error) {
    setMessage(error.message, 'error');
  }
}

async function handleLogout() {
  await authStore.logout();
  emit('update:open', false);
  router.push('/login');
}

watch(
  () => props.open,
  async (open) => {
    if (!open) return;
    currentTab.value = props.initialTab || 'profile';
    message.value = '';
    await loadData();
  },
  { immediate: true },
);

watch(
  () => props.initialTab,
  (tab) => {
    currentTab.value = tab || 'profile';
  },
);
</script>
