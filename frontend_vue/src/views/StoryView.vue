<template>
  <main class="main-layout story-page">
    <div v-if="mobileDrawer" class="story-mobile-backdrop" @click="mobileDrawer = ''"></div>

    <aside :class="['side-panel side-panel-left story-mobile-drawer', { 'mobile-open': mobileDrawer === 'player' }]">
      <section class="sidebar-section player-panel">
        <div class="sidebar-header">
          <div class="sidebar-title">主角与玩家视角</div>
          <button class="panel-collapse-btn" aria-label="toggle" @click="togglePanel('player')">
            <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" :style="{ transform: panelOpen.player ? 'rotate(0deg)' : 'rotate(-90deg)' }"><polyline points="6 9 12 15 18 9"></polyline></svg>
          </button>
        </div>
        <div v-show="panelOpen.player" class="sidebar-body player-body">
          <div class="player-subsection">
            <div class="subsection-header" @click="toggleSection('player-stats')"><span class="subsection-title">主角数值与状态</span><svg class="toggle-icon" viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none" :style="{ transform: sectionOpen['player-stats'] ? 'rotate(0deg)' : 'rotate(-90deg)' }"><polyline points="6 9 12 15 18 9"></polyline></svg></div>
            <div v-show="sectionOpen['player-stats']" class="subsection-content">
              <div class="stats-grid">
                <div class="stat-item"><div class="stat-label">生命值</div><div class="stat-bar-container"><div class="stat-bar stat-bar-health" style="width:100%"></div></div><div class="stat-value">100/100</div></div>
                <div class="stat-item"><div class="stat-label">法力值</div><div class="stat-bar-container"><div class="stat-bar stat-bar-mana" style="width:100%"></div></div><div class="stat-value">100/100</div></div>
                <div class="stat-item"><div class="stat-label">体力值</div><div class="stat-bar-container"><div class="stat-bar stat-bar-stamina" style="width:100%"></div></div><div class="stat-value">100/100</div></div>
              </div>
              <div class="status-badges"><span class="status-badge status-normal">正常</span></div>
            </div>
          </div>
          <div class="player-subsection">
            <div class="subsection-header" @click="toggleSection('player-resources')"><span class="subsection-title">经济 / 资源</span><svg class="toggle-icon" viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none" :style="{ transform: sectionOpen['player-resources'] ? 'rotate(0deg)' : 'rotate(-90deg)' }"><polyline points="6 9 12 15 18 9"></polyline></svg></div>
            <div v-show="sectionOpen['player-resources']" class="subsection-content">
              <div class="resource-grid">
                <div class="resource-item"><span class="resource-icon">金</span><div class="resource-info"><div class="resource-name">金币</div><div class="resource-value">{{ sidebarState.gold }}</div></div></div>
                <div class="resource-item"><span class="resource-icon">钻</span><div class="resource-info"><div class="resource-name">钻石</div><div class="resource-value">{{ sidebarState.diamond }}</div></div></div>
              </div>
              <div class="resource-summary">{{ sidebarState.economy }}</div>
            </div>
          </div>
          <div class="player-subsection"><div class="subsection-header" @click="toggleSection('player-abilities')"><span class="subsection-title">能力评级</span><svg class="toggle-icon" viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none" :style="{ transform: sectionOpen['player-abilities'] ? 'rotate(0deg)' : 'rotate(-90deg)' }"><polyline points="6 9 12 15 18 9"></polyline></svg></div><div v-show="sectionOpen['player-abilities']" class="subsection-content"><div class="ability-summary">{{ sidebarState.ability }}</div></div></div>
          <div class="player-subsection"><div class="subsection-header" @click="toggleSection('player-factions')"><span class="subsection-title">势力 / 阵营</span><svg class="toggle-icon" viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none" :style="{ transform: sectionOpen['player-factions'] ? 'rotate(0deg)' : 'rotate(-90deg)' }"><polyline points="6 9 12 15 18 9"></polyline></svg></div><div v-show="sectionOpen['player-factions']" class="subsection-content"><div class="faction-summary">{{ sidebarState.faction }}</div></div></div>
          <div class="player-subsection"><div class="subsection-header" @click="toggleSection('action-history')"><span class="subsection-title">历史行动</span><svg class="toggle-icon" viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none" :style="{ transform: sectionOpen['action-history'] ? 'rotate(0deg)' : 'rotate(-90deg)' }"><polyline points="6 9 12 15 18 9"></polyline></svg></div><div v-show="sectionOpen['action-history']" class="subsection-content"><div v-if="!actionHistory.length" class="muted">暂无历史行动</div><div v-for="(item, index) in actionHistory" :key="index" class="action-history-item">{{ item }}</div></div></div>
        </div>
      </section>
    </aside>

    <section class="story-panel">
      <div class="panel-header">
        <div><div class="panel-title">故事进程</div></div>
        <div class="panel-header-right story-toolbar">
          <button class="btn-secondary btn-small story-mobile-toggle" @click="toggleMobileDrawer('player')">玩家视角</button>
          <button class="btn-secondary btn-small story-mobile-toggle" @click="toggleMobileDrawer('scene')">当前场景</button>
          <button class="btn-secondary btn-small" title="字体设置" @click="fontModalOpen = true">字体设置</button>
        </div>
      </div>
      <div ref="storyLogRef" class="story-log">
        <div v-if="!storyBlocks.length" class="placeholder-text story-empty">请输入你的第一条行动。</div>
        <StoryLogBlock v-for="block in storyBlocks" :key="block.id" :block="block" @show-raw-text="rawTextBlock = $event" />
      </div>
      <div v-show="timerVisible" class="story-timer">
        <span class="timer-item">前端耗时: {{ frontendDuration.toFixed(1) }}s</span>
        <span class="timer-divider">|</span>
        <span class="timer-item">后端耗时: {{ backendDuration.toFixed(1) }}s</span>
      </div>
    </section>

    <aside :class="['side-panel side-panel-right story-mobile-drawer', { 'mobile-open': mobileDrawer === 'scene' }]">
      <section class="sidebar-section scene-panel">
        <div class="sidebar-header">
          <div class="sidebar-title">当前场景与剧本</div>
          <button class="panel-collapse-btn" aria-label="toggle" @click="togglePanel('scene')"><svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" :style="{ transform: panelOpen.scene ? 'rotate(0deg)' : 'rotate(-90deg)' }"><polyline points="6 9 12 15 18 9"></polyline></svg></button>
        </div>
        <div v-show="panelOpen.scene" class="sidebar-body scene-body">
          <div class="scene-subsection"><div class="subsection-header" @click="toggleSection('scene-info')"><span class="subsection-title">场景信息</span><svg class="toggle-icon" viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none" :style="{ transform: sectionOpen['scene-info'] ? 'rotate(0deg)' : 'rotate(-90deg)' }"><polyline points="6 9 12 15 18 9"></polyline></svg></div><div v-show="sectionOpen['scene-info']" class="subsection-content"><div class="scene-name"><span class="scene-icon">景</span><span>{{ sidebarState.dungeonName }}</span></div><div class="scene-node"><span class="node-label">当前节点:</span><span>{{ sidebarState.dungeonNodeName }}</span></div><div class="scene-description">{{ sidebarState.sceneDescription }}</div></div></div>
          <div class="scene-subsection"><div class="subsection-header" @click="toggleSection('scene-progress')"><span class="subsection-title">剧情进度</span><svg class="toggle-icon" viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none" :style="{ transform: sectionOpen['scene-progress'] ? 'rotate(0deg)' : 'rotate(-90deg)' }"><polyline points="6 9 12 15 18 9"></polyline></svg></div><div v-show="sectionOpen['scene-progress']" class="subsection-content"><div class="progress-container"><div class="progress-bar-wrapper"><div class="progress-bar" :style="{ width: sidebarState.progressWidth }"></div></div><div class="progress-text">{{ sidebarState.progressText }}</div></div><div class="progress-hint">{{ sidebarState.progressHint }}</div></div></div>
        </div>
      </section>
      <section class="sidebar-section characters-panel">
        <div class="sidebar-header"><div class="sidebar-title">周围人物与势力</div><button class="panel-collapse-btn" aria-label="toggle" @click="togglePanel('characters')"><svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" :style="{ transform: panelOpen.characters ? 'rotate(0deg)' : 'rotate(-90deg)' }"><polyline points="6 9 12 15 18 9"></polyline></svg></button></div>
        <div v-show="panelOpen.characters" class="sidebar-body characters-body"><div class="characters-subsection"><div class="subsection-header" @click="toggleSection('npc-list')"><span class="subsection-title">NPC 列表</span><svg class="toggle-icon" viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none" :style="{ transform: sectionOpen['npc-list'] ? 'rotate(0deg)' : 'rotate(-90deg)' }"><polyline points="6 9 12 15 18 9"></polyline></svg></div><div v-show="sectionOpen['npc-list']" class="subsection-content"><div class="npc-grid"><div v-if="!sidebarState.npcs.length" class="muted small-text">暂无 NPC</div><div v-for="item in sidebarState.npcs" :key="item.character_id" class="npc-card"><div class="npc-name">{{ item.name || item.character_id }}</div><div class="small-text muted">{{ item.ability_tier || '未知' }}</div></div></div></div></div></div>
      </section>
      <section class="sidebar-section world-panel">
        <div class="sidebar-header"><div class="sidebar-title">地图与世界事件</div><button class="panel-collapse-btn" aria-label="toggle" @click="togglePanel('world')"><svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" :style="{ transform: panelOpen.world ? 'rotate(0deg)' : 'rotate(-90deg)' }"><polyline points="6 9 12 15 18 9"></polyline></svg></button></div>
        <div v-show="panelOpen.world" class="sidebar-body world-body"><div class="world-subsection"><div class="subsection-header" @click="toggleSection('event-markers')"><span class="subsection-title">事件标记</span><svg class="toggle-icon" viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none" :style="{ transform: sectionOpen['event-markers'] ? 'rotate(0deg)' : 'rotate(-90deg)' }"><polyline points="6 9 12 15 18 9"></polyline></svg></div><div v-show="sectionOpen['event-markers']" class="subsection-content"><div class="event-list"><div class="muted small-text">暂无进行中的事件</div></div></div></div></div>
      </section>
    </aside>
  </main>

  <footer :class="['input-bar', { 'input-bar--collapsed': inputCollapsed, 'input-bar--half-screen': inputHalfScreen }]">
    <div class="input-container">
      <div class="input-header-row">
        <div class="input-header-left">
          <button type="button" class="icon-button input-collapse-btn story-collapse-btn" aria-label="toggle" @click="inputCollapsed = !inputCollapsed">
            <svg viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" :style="{ transform: inputCollapsed ? 'rotate(180deg)' : 'rotate(0deg)' }"><polyline points="6 9 12 15 18 9"></polyline></svg>
          </button>
          <div class="input-header-desc">说书人控制台 · <span>{{ sessionLabel }}</span></div>
        </div>
      </div>
      <div v-show="!inputCollapsed" class="input-body">
        <div :class="['action-suggestions', { 'action-suggestions--open': actionSuggestionsOpen }]">
          <div class="action-suggestions-header"><button type="button" class="action-suggestions-toggle" @click="actionSuggestionsOpen = !actionSuggestionsOpen">下一次行动建议（点击{{ actionSuggestionsOpen ? '收起' : '展开' }}）</button></div>
          <div v-show="actionSuggestionsOpen" class="action-suggestions-body"><div v-if="!actionSuggestions.length" class="empty-suggestions">暂无行动建议</div><button v-for="(item, index) in actionSuggestions" :key="`${index}-${item}`" type="button" class="suggestion-chip" @click="useSuggestion(item)">{{ index + 1 }}. {{ item }}</button></div>
        </div>
        <div class="input-main">
          <div class="input-main-inner"><textarea v-model="userInput" class="input-textarea" rows="1" placeholder="请输入行动..." @keydown.ctrl.enter.prevent="submit"></textarea></div>
          <div class="input-actions story-input-actions"><div class="input-hint">Ctrl + Enter 发送</div><div class="story-input-controls"><select v-model="reasoningStrength" class="btn-secondary btn-small story-reasoning-select"><option v-for="item in reasoningOptions" :key="item.value" :value="item.value">{{ item.label }}</option></select><button class="btn-primary btn-small story-generate-btn" :disabled="isGenerating" @click="submit">{{ isGenerating ? '生成中...' : '生成下一段' }}</button></div></div>
          <div class="small-text input-status">{{ inputStatus }}</div>
        </div>
      </div>
    </div>
  </footer>

  <StoryFontSettingsModal v-model="fontSettings" :open="fontModalOpen" @close="fontModalOpen = false" @save="saveFontSettings" @reset="resetFontSettings" />
  <DeveloperLogWindow v-if="developerMode" :enabled="developerMode" :open="developerLogOpen" :logs="developerLogs" @toggle="developerLogOpen = !developerLogOpen" />
  <div v-if="rawTextBlock" class="modal-overlay"><div class="modal-window" style="max-width:900px;"><div class="modal-header"><h3 class="modal-title">原文</h3><button class="modal-close-btn" aria-label="close" @click="rawTextBlock = null">&times;</button></div><div class="modal-body story-raw-text">{{ rawTextBlock.rawText }}</div></div></div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue';
import DeveloperLogWindow from '../components/story/DeveloperLogWindow.vue';
import StoryFontSettingsModal from '../components/story/StoryFontSettingsModal.vue';
import StoryLogBlock from '../components/story/StoryLogBlock.vue';
import { useStoryPage } from '../composables/useStoryPage';
import { initThemePage } from '../page_logic/theme-init.module';

const { actionHistory, actionSuggestions, actionSuggestionsOpen, backendDuration, bootstrap, developerLogs, developerLogOpen, developerMode, fontModalOpen, fontSettings, frontendDuration, inputCollapsed, inputStatus, isGenerating, panelOpen, rawTextBlock, reasoningOptions, reasoningStrength, saveFontSettings, resetFontSettings, sectionOpen, sessionLabel, sidebarState, storyBlocks, storyLogRef, submit, timerVisible, togglePanel, toggleSection, useSuggestion, userInput } = useStoryPage();
const mobileDrawer = ref('');
const toggleMobileDrawer = (name) => { mobileDrawer.value = mobileDrawer.value === name ? '' : name; };

watch(storyBlocks, () => { mobileDrawer.value = ''; });

onMounted(async () => {
  document.title = 'Storyteller | 剧情';
  document.body.setAttribute('data-page', 'index');
  initThemePage();
  await bootstrap();
});
</script>

<style scoped>
.story-empty{color:var(--text-secondary);padding:20px}.story-raw-text{white-space:pre-wrap;font-family:var(--font-raw-family);font-size:var(--font-raw-size);font-weight:var(--font-raw-weight)}
.story-mobile-backdrop,.story-mobile-drawer{display:none}.story-toolbar{gap:8px}.story-mobile-toggle{display:none}.story-input-actions{display:flex;justify-content:space-between;align-items:center;gap:12px}.story-input-controls{display:flex;align-items:center;gap:8px;margin-left:auto}.story-reasoning-select{min-width:92px}.story-generate-btn{white-space:nowrap}
@media (max-width:900px){.story-mobile-backdrop{display:block;position:fixed;inset:0;background:rgba(6,10,16,.42);backdrop-filter:blur(5px);z-index:18}.story-mobile-drawer,.side-panel-left.story-mobile-drawer,.side-panel-right.story-mobile-drawer{display:block !important;position:fixed !important;top:calc(var(--top-nav-height) + 10px);bottom:calc(132px + env(safe-area-inset-bottom,0px));width:min(84vw,340px);z-index:19;overflow:auto;transition:transform .22s ease,opacity .22s ease;opacity:0;pointer-events:none}.side-panel-left.story-mobile-drawer{left:10px !important;right:auto !important;transform:translateX(-108%)}.side-panel-right.story-mobile-drawer{right:10px !important;left:auto !important;transform:translateX(108%)}.story-mobile-drawer.mobile-open{transform:translateX(0) !important;opacity:1;pointer-events:auto}.story-mobile-drawer .sidebar-section{display:flex !important;min-height:100%;background:var(--bg-elevated);border:1px solid var(--border-soft);border-radius:20px;box-shadow:0 20px 36px rgba(0,0,0,.18)}.story-mobile-toggle{display:inline-flex}.story-collapse-btn{width:32px;height:32px;min-height:32px;padding:0}.story-input-actions{align-items:flex-end}.story-input-controls{justify-content:flex-end}.story-reasoning-select{min-width:86px}.story-generate-btn{padding-inline:14px}}
</style>
