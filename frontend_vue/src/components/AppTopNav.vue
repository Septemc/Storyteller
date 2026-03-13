<template>
  <header class="top-nav">
    <div class="nav-left">
      <span class="app-title">Storyteller</span>
      <span class="app-subtitle">{{ subtitle }}</span>
    </div>

    <div class="nav-center">
      <div class="current-save-info" id="current-save-info" @click="openSaveManager">
        <div class="save-name" id="current-save-name">{{ saveStore.currentDisplayName }}</div>
        <div class="save-id" id="current-save-id">{{ saveStore.currentDisplayId }}</div>
      </div>
    </div>

    <nav class="nav-links">
      <RouterLink to="/story" class="nav-link">剧情</RouterLink>
      <RouterLink to="/characters" class="nav-link">角色</RouterLink>
      <RouterLink to="/worldbook" class="nav-link">世界书</RouterLink>
      <RouterLink to="/dungeon" class="nav-link">剧本</RouterLink>
      <RouterLink to="/settings" class="nav-link">设置</RouterLink>

      <div class="nav-user-info">
        <div class="nav-user-wrapper" id="nav-user-wrapper" @click.stop="toggleUserMenu">
          <span class="nav-username" id="nav-username">{{ authStore.username }}</span>
          <button
            v-if="authStore.isAuthed"
            class="nav-logout-btn"
            id="nav-logout-btn"
            title="退出登录"
            type="button"
            @click.stop="logout"
          >
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
              <polyline points="16 17 21 12 16 7"/>
              <line x1="21" y1="12" x2="9" y2="12"/>
            </svg>
          </button>

          <div v-if="authStore.isAuthed && userMenuOpen" class="nav-user-dropdown" id="nav-user-dropdown">
            <div class="dropdown-item" data-action="profile" @click="openAccount('profile')">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                <circle cx="12" cy="7" r="4"/>
              </svg>
              <span>个人中心</span>
            </div>
            <div class="dropdown-divider"></div>
            <div class="dropdown-item" data-action="guide" @click="openAccount('guide')">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
                <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
              </svg>
              <span>使用指南</span>
            </div>
            <div class="dropdown-divider"></div>
            <div class="dropdown-item" data-action="settings" @click="openAccount('settings')">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="3"/>
                <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
              </svg>
              <span>账户设置</span>
            </div>
            <div class="dropdown-divider"></div>
            <div class="dropdown-item danger" data-action="logout" @click="logout">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
                <polyline points="16 17 21 12 16 7"/>
                <line x1="21" y1="12" x2="9" y2="12"/>
              </svg>
              <span>退出登录</span>
            </div>
          </div>
        </div>

        <RouterLink v-if="!authStore.isAuthed" to="/login" class="nav-login-link" id="nav-login-link">登录</RouterLink>
      </div>
    </nav>

    <SaveManagerModal />
    <AccountModal v-model:open="accountOpen" :initial-tab="accountTab" />
  </header>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import { useSaveManagerStore } from '../stores/saveManager';
import { useSessionStore } from '../stores/session';
import AccountModal from './AccountModal.vue';
import SaveManagerModal from './SaveManagerModal.vue';

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const saveStore = useSaveManagerStore();
const sessionStore = useSessionStore();
const userMenuOpen = ref(false);
const accountOpen = ref(false);
const accountTab = ref('profile');

const subtitleMap = {
  story: '说书人·剧情控制台',
  'story-root': '说书人·剧情控制台',
  characters: '说书人·角色档案',
  worldbook: '说书人·世界书管理',
  dungeon: '说书人·剧本编排',
  settings: '说书人·系统设置',
};

const subtitle = computed(() => subtitleMap[route.name] || '说书人·叙事工作台');

function closeUserMenu() {
  userMenuOpen.value = false;
}

function toggleUserMenu() {
  if (!authStore.isAuthed) return;
  userMenuOpen.value = !userMenuOpen.value;
}

async function openSaveManager() {
  await saveStore.openModal();
}

function openAccount(tab) {
  accountTab.value = tab;
  accountOpen.value = true;
  closeUserMenu();
}

async function logout() {
  closeUserMenu();
  await authStore.logout();
  router.push('/login');
}

function handleOutsideClick(event) {
  if (!event.target.closest('#nav-user-wrapper')) {
    closeUserMenu();
  }
}

watch(
  () => route.fullPath,
  () => {
    closeUserMenu();
  },
);

watch(
  () => sessionStore.currentSessionId,
  () => {
    saveStore.syncCurrentSession();
  },
);

onMounted(async () => {
  await saveStore.syncCurrentSession();
  document.addEventListener('click', handleOutsideClick);
});

onBeforeUnmount(() => {
  document.removeEventListener('click', handleOutsideClick);
});
</script>
