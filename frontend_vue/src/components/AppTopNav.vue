<template>
  <header class="top-nav">
    <div class="mobile-nav-bar">
      <button class="mobile-nav-trigger" type="button" aria-label="打开导航菜单" @click="mobileMenuOpen = true">
        <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 7h16M4 12h16M4 17h16"/></svg>
      </button>
      <button class="mobile-save-trigger" type="button" @click="openSaveManager">
        <span class="mobile-save-name">{{ saveStore.currentDisplayName }}</span>
        <span class="mobile-save-id">{{ saveStore.currentDisplayId }}</span>
      </button>
    </div>

    <div class="nav-left">
      <span class="app-title">Storyteller</span>
      <span class="app-subtitle">{{ subtitle }}</span>
    </div>

    <div class="nav-center">
      <div class="current-save-info" @click="openSaveManager">
        <div class="save-name">{{ saveStore.currentDisplayName }}</div>
        <div class="save-id">{{ saveStore.currentDisplayId }}</div>
      </div>
    </div>

    <nav class="nav-links">
      <RouterLink v-for="item in navItems" :key="item.to" :to="item.to" class="nav-link">{{ item.label }}</RouterLink>
      <div class="nav-user-info">
        <div class="nav-user-wrapper" id="nav-user-wrapper" @click.stop="toggleUserMenu">
          <span class="nav-username">{{ authStore.username || '未登录' }}</span>
          <button v-if="authStore.isAuthed" class="nav-logout-btn" title="退出登录" type="button" @click.stop="logout">
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
          </button>
          <div v-if="authStore.isAuthed && userMenuOpen" class="nav-user-dropdown" id="nav-user-dropdown">
            <button class="dropdown-item" type="button" @click="openAccount('profile')">个人中心</button>
            <button class="dropdown-item" type="button" @click="openAccount('guide')">使用指南</button>
            <button class="dropdown-item" type="button" @click="openAccount('settings')">账户设置</button>
            <button class="dropdown-item danger" type="button" @click="logout">退出登录</button>
          </div>
        </div>
        <RouterLink v-if="!authStore.isAuthed" to="/login" class="nav-login-link">登录</RouterLink>
      </div>
    </nav>

    <SaveManagerModal />
    <AccountModal v-model:open="accountOpen" :initial-tab="accountTab" />
  </header>

  <div v-if="mobileMenuOpen" class="mobile-nav-backdrop" @click="closeMobileMenu"></div>
  <aside :class="['mobile-nav-drawer', { open: mobileMenuOpen }]">
    <div class="mobile-nav-header">
      <div>
        <div class="mobile-nav-title">Storyteller</div>
        <div class="mobile-nav-subtitle">{{ subtitle }}</div>
      </div>
      <button class="mobile-nav-close" type="button" aria-label="关闭导航菜单" @click="closeMobileMenu">×</button>
    </div>
    <button class="mobile-nav-save" type="button" @click="openSaveManager">
      <span>{{ saveStore.currentDisplayName }}</span>
      <small>{{ saveStore.currentDisplayId }}</small>
    </button>
    <nav class="mobile-nav-links">
      <RouterLink v-for="item in navItems" :key="`mobile-${item.to}`" :to="item.to" class="mobile-nav-link" @click="closeMobileMenu">{{ item.label }}</RouterLink>
    </nav>
    <div class="mobile-nav-actions">
      <button v-if="authStore.isAuthed" class="mobile-nav-action" type="button" @click="openAccount('profile')">个人中心</button>
      <button v-if="authStore.isAuthed" class="mobile-nav-action" type="button" @click="openAccount('guide')">使用指南</button>
      <button v-if="authStore.isAuthed" class="mobile-nav-action" type="button" @click="openAccount('settings')">账户设置</button>
      <button v-if="authStore.isAuthed" class="mobile-nav-action danger" type="button" @click="logout">退出登录</button>
      <RouterLink v-else to="/login" class="mobile-nav-link login" @click="closeMobileMenu">登录</RouterLink>
    </div>
  </aside>
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
const mobileMenuOpen = ref(false);
const accountOpen = ref(false);
const accountTab = ref('profile');
const navItems = [{ to: '/story', label: '剧情' }, { to: '/characters', label: '角色' }, { to: '/worldbook', label: '世界书' }, { to: '/dungeon', label: '剧本' }, { to: '/settings', label: '设置' }];
const subtitleMap = { story: '交互式剧情控制台', 'story-root': '交互式剧情控制台', characters: '角色信息管理', worldbook: '世界书与设定', dungeon: '剧本与副本编排', settings: '系统设置中心' };
const subtitle = computed(() => subtitleMap[route.name] || '叙事引擎工作台');

const closeMobileMenu = () => { mobileMenuOpen.value = false; };
const closeUserMenu = () => { userMenuOpen.value = false; };
const toggleUserMenu = () => { if (authStore.isAuthed) userMenuOpen.value = !userMenuOpen.value; };
const openSaveManager = async () => { closeMobileMenu(); await saveStore.openModal(); };
function openAccount(tab) { accountTab.value = tab; accountOpen.value = true; closeMobileMenu(); closeUserMenu(); }
async function logout() { closeMobileMenu(); closeUserMenu(); await authStore.logout(); router.push('/login'); }
function handleOutsideClick(event) { if (!event.target.closest('#nav-user-wrapper')) closeUserMenu(); }
function handleEscape(event) { if (event.key === 'Escape') { closeMobileMenu(); closeUserMenu(); } }

watch(() => route.fullPath, () => { closeMobileMenu(); closeUserMenu(); });
watch(() => sessionStore.currentSessionId, () => { saveStore.syncCurrentSession(); });

onMounted(async () => {
  await saveStore.syncCurrentSession();
  document.addEventListener('click', handleOutsideClick);
  document.addEventListener('keydown', handleEscape);
});

onBeforeUnmount(() => {
  document.removeEventListener('click', handleOutsideClick);
  document.removeEventListener('keydown', handleEscape);
});
</script>

<style scoped>
.mobile-nav-bar,.mobile-nav-backdrop,.mobile-nav-drawer{display:none}
.nav-user-dropdown{display:flex;flex-direction:column;gap:6px;padding:8px}.dropdown-item{border:0;background:transparent;color:inherit;text-align:left;padding:8px 10px;border-radius:10px;cursor:pointer}.dropdown-item:hover{background:var(--accent-soft)}.dropdown-item.danger{color:var(--danger)}
@media (max-width: 900px){
  .mobile-nav-bar{display:grid;grid-template-columns:auto minmax(0,1fr);gap:10px;align-items:center;width:100%}
  .nav-left,.nav-center,.nav-links{display:none}
  .mobile-nav-trigger,.mobile-nav-close{width:42px;height:42px;border:1px solid var(--border-soft);border-radius:14px;background:var(--bg-elevated);color:var(--text-primary)}
  .mobile-save-trigger,.mobile-nav-save{display:flex;flex-direction:column;align-items:flex-start;gap:2px;width:100%;padding:10px 14px;border:1px solid color-mix(in srgb,var(--accent) 18%,var(--border-soft));border-radius:16px;background:linear-gradient(135deg,color-mix(in srgb,var(--bg-elevated-alt) 96%,transparent),color-mix(in srgb,var(--accent-soft) 55%,var(--bg-elevated) 45%));color:var(--text-primary)}
  .mobile-save-name,.mobile-nav-save span{font-weight:700;max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.mobile-save-id,.mobile-nav-save small{font-size:11px;color:var(--text-secondary)}
  .mobile-nav-backdrop{display:block;position:fixed;inset:0;background:rgba(8,10,16,.48);backdrop-filter:blur(6px);z-index:79}
  .mobile-nav-drawer{display:flex;position:fixed;top:0;left:0;bottom:0;width:min(86vw,340px);padding:calc(env(safe-area-inset-top,0px) + 14px) 14px calc(env(safe-area-inset-bottom,0px) + 14px);flex-direction:column;gap:14px;background:linear-gradient(180deg,color-mix(in srgb,var(--bg-elevated) 98%,transparent),color-mix(in srgb,var(--bg-main) 92%,transparent));border-right:1px solid color-mix(in srgb,var(--accent) 20%,var(--border-soft));box-shadow:24px 0 48px rgba(0,0,0,.28);transform:translateX(-102%);transition:transform .22s ease;z-index:80}
  .mobile-nav-drawer.open{transform:translateX(0)}
  .mobile-nav-header{display:flex;align-items:flex-start;justify-content:space-between;gap:12px}.mobile-nav-title{font-size:22px;font-weight:800}.mobile-nav-subtitle{font-size:12px;color:var(--text-secondary);line-height:1.5}
  .mobile-nav-links,.mobile-nav-actions{display:flex;flex-direction:column;gap:8px}.mobile-nav-link,.mobile-nav-action{display:flex;align-items:center;min-height:46px;padding:0 14px;border:1px solid var(--border-soft);border-radius:16px;background:var(--bg-elevated-alt);color:var(--text-primary)}.mobile-nav-link.router-link-active{background:linear-gradient(135deg,var(--accent),color-mix(in srgb,var(--accent),white 18%));color:#fff;border-color:transparent}.mobile-nav-action.danger{color:var(--danger)}
}
</style>
