<template>
  <main class="main-layout">
    <aside class="side-panel side-panel-left">
      <section class="sidebar-section player-panel">
        <div class="sidebar-header">
          <div class="sidebar-title">主角与玩家视角</div>
          <button class="panel-collapse-btn" aria-label="收起/展开" @click="togglePanel('player')">
            <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" :style="{ transform: panelOpen.player ? 'rotate(0deg)' : 'rotate(-90deg)' }"><polyline points="6 9 12 15 18 9"></polyline></svg>
          </button>
        </div>
        <div v-show="panelOpen.player" class="sidebar-body player-body">
          <div class="player-subsection">
            <div class="subsection-header" @click="toggleSection('player-stats')">
              <span class="subsection-title">主角数值与状态</span>
              <svg class="toggle-icon" viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none" :style="{ transform: sectionOpen['player-stats'] ? 'rotate(0deg)' : 'rotate(-90deg)' }"><polyline points="6 9 12 15 18 9"></polyline></svg>
            </div>
            <div v-show="sectionOpen['player-stats']" class="subsection-content">
              <div class="stats-grid">
                <div class="stat-item">
                  <div class="stat-label">生命值</div>
                  <div class="stat-bar-container"><div class="stat-bar stat-bar-health" style="width: 100%"></div></div>
                  <div class="stat-value">100/100</div>
                </div>
                <div class="stat-item">
                  <div class="stat-label">魔法值</div>
                  <div class="stat-bar-container"><div class="stat-bar stat-bar-mana" style="width: 100%"></div></div>
                  <div class="stat-value">100/100</div>
                </div>
                <div class="stat-item">
                  <div class="stat-label">体力值</div>
                  <div class="stat-bar-container"><div class="stat-bar stat-bar-stamina" style="width: 100%"></div></div>
                  <div class="stat-value">100/100</div>
                </div>
              </div>
              <div class="status-badges"><span class="status-badge status-normal">正常</span></div>
            </div>
          </div>

          <div class="player-subsection">
            <div class="subsection-header" @click="toggleSection('player-resources')">
              <span class="subsection-title">经济/资源</span>
              <svg class="toggle-icon" viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none" :style="{ transform: sectionOpen['player-resources'] ? 'rotate(0deg)' : 'rotate(-90deg)' }"><polyline points="6 9 12 15 18 9"></polyline></svg>
            </div>
            <div v-show="sectionOpen['player-resources']" class="subsection-content">
              <div class="resource-grid">
                <div class="resource-item">
                  <span class="resource-icon">💰</span>
                  <div class="resource-info"><div class="resource-name">金币</div><div id="resource-gold" class="resource-value">{{ sidebarState.gold }}</div></div>
                </div>
                <div class="resource-item">
                  <span class="resource-icon">💎</span>
                  <div class="resource-info"><div class="resource-name">钻石</div><div id="resource-diamond" class="resource-value">{{ sidebarState.diamond }}</div></div>
                </div>
              </div>
              <div id="var-economy" class="resource-summary">{{ sidebarState.economy }}</div>
            </div>
          </div>

          <div class="player-subsection">
            <div class="subsection-header" @click="toggleSection('player-abilities')">
              <span class="subsection-title">能力评级</span>
              <svg class="toggle-icon" viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none" :style="{ transform: sectionOpen['player-abilities'] ? 'rotate(0deg)' : 'rotate(-90deg)' }"><polyline points="6 9 12 15 18 9"></polyline></svg>
            </div>
            <div v-show="sectionOpen['player-abilities']" class="subsection-content">
              <div id="var-ability" class="ability-summary">{{ sidebarState.ability }}</div>
              <div class="ability-stars"><span class="star">★</span><span class="star">★</span><span class="star">★</span><span class="star">★</span><span class="star">★</span></div>
            </div>
          </div>

          <div class="player-subsection">
            <div class="subsection-header" @click="toggleSection('player-factions')">
              <span class="subsection-title">势力/阵营</span>
              <svg class="toggle-icon" viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none" :style="{ transform: sectionOpen['player-factions'] ? 'rotate(0deg)' : 'rotate(-90deg)' }"><polyline points="6 9 12 15 18 9"></polyline></svg>
            </div>
            <div v-show="sectionOpen['player-factions']" class="subsection-content">
              <div id="var-faction" class="faction-summary">{{ sidebarState.faction }}</div>
            </div>
          </div>

          <div class="player-subsection">
            <div class="subsection-header" @click="toggleSection('player-inventory')">
              <span class="subsection-title">物品栏</span>
              <svg class="toggle-icon" viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none" :style="{ transform: sectionOpen['player-inventory'] ? 'rotate(0deg)' : 'rotate(-90deg)' }"><polyline points="6 9 12 15 18 9"></polyline></svg>
            </div>
            <div v-show="sectionOpen['player-inventory']" class="subsection-content">
              <div class="inventory-grid">
                <div class="inventory-slot empty"></div>
                <div class="inventory-slot empty"></div>
                <div class="inventory-slot empty"></div>
                <div class="inventory-slot empty"></div>
              </div>
            </div>
          </div>

          <div class="player-subsection">
            <div class="subsection-header" @click="toggleSection('player-buffs')">
              <span class="subsection-title">Buff/Debuff</span>
              <svg class="toggle-icon" viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none" :style="{ transform: sectionOpen['player-buffs'] ? 'rotate(0deg)' : 'rotate(-90deg)' }"><polyline points="6 9 12 15 18 9"></polyline></svg>
            </div>
            <div v-show="sectionOpen['player-buffs']" class="subsection-content"><div class="buff-list"><div class="muted small-text">暂无生效效果</div></div></div>
          </div>

          <div class="player-subsection">
            <div class="subsection-header" @click="toggleSection('action-history')">
              <span class="subsection-title">历史行动</span>
              <svg class="toggle-icon" viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none" :style="{ transform: sectionOpen['action-history'] ? 'rotate(0deg)' : 'rotate(-90deg)' }"><polyline points="6 9 12 15 18 9"></polyline></svg>
            </div>
            <div v-show="sectionOpen['action-history']" id="action-history" class="subsection-content">
              <div v-if="!actionHistory.length" class="muted">暂无历史行动</div>
              <div v-for="(item, index) in actionHistory" :key="index" class="action-history-item">{{ item }}</div>
            </div>
          </div>
        </div>
      </section>
    </aside>

    <section class="story-panel">
      <div class="panel-header">
        <div><div class="panel-title">故事进程</div></div>
        <div class="panel-header-right"><button id="font-settings-btn" class="btn-secondary" title="字体设置" @click="fontModalOpen = true">字体设置</button></div>
      </div>
      <div id="story-log" ref="storyLogRef" class="story-log">
        <div v-if="!storyBlocks.length" class="placeholder-text" style="color: var(--text-secondary); padding: 20px;">请输入你的第一条行动。</div>
        <StoryLogBlock v-for="block in storyBlocks" :key="block.id" :block="block" @show-raw-text="rawTextBlock = $event" />
      </div>
      <div v-show="timerVisible" id="story-timer" class="story-timer">
        <span class="timer-item">前端耗时：<span id="timer-frontend">{{ frontendDuration.toFixed(1) }}s</span></span>
        <span class="timer-divider">|</span>
        <span class="timer-item">后端耗时：<span id="timer-backend">{{ backendDuration.toFixed(1) }}s</span></span>
      </div>
    </section>

    <aside class="side-panel side-panel-right">
      <section class="sidebar-section scene-panel">
        <div class="sidebar-header">
          <div class="sidebar-title">当前场景与剧本</div>
          <button class="panel-collapse-btn" aria-label="收起/展开" @click="togglePanel('scene')">
            <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" :style="{ transform: panelOpen.scene ? 'rotate(0deg)' : 'rotate(-90deg)' }"><polyline points="6 9 12 15 18 9"></polyline></svg>
          </button>
        </div>
        <div v-show="panelOpen.scene" class="sidebar-body scene-body">
          <div class="scene-subsection">
            <div class="subsection-header" @click="toggleSection('scene-info')">
              <span class="subsection-title">场景信息</span>
              <svg class="toggle-icon" viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none" :style="{ transform: sectionOpen['scene-info'] ? 'rotate(0deg)' : 'rotate(-90deg)' }"><polyline points="6 9 12 15 18 9"></polyline></svg>
            </div>
            <div v-show="sectionOpen['scene-info']" id="scene-info" class="subsection-content">
              <div class="scene-name"><span class="scene-icon">📍</span><span id="dungeon-name">{{ sidebarState.dungeonName }}</span></div>
              <div class="scene-node"><span class="node-label">当前节点：</span><span id="dungeon-node-name">{{ sidebarState.dungeonNodeName }}</span></div>
              <div id="scene-description" class="scene-description">{{ sidebarState.sceneDescription }}</div>
            </div>
          </div>

          <div class="scene-subsection">
            <div class="subsection-header" @click="toggleSection('scene-quests')">
              <span class="subsection-title">任务目标</span>
              <svg class="toggle-icon" viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none" :style="{ transform: sectionOpen['scene-quests'] ? 'rotate(0deg)' : 'rotate(-90deg)' }"><polyline points="6 9 12 15 18 9"></polyline></svg>
            </div>
            <div v-show="sectionOpen['scene-quests']" class="subsection-content">
              <div class="quest-list"><div class="quest-item quest-main"><span class="quest-type">主线</span><span class="quest-name">{{ sidebarState.questName }}</span></div></div>
            </div>
          </div>

          <div class="scene-subsection">
            <div class="subsection-header" @click="toggleSection('scene-environment')">
              <span class="subsection-title">环境状态</span>
              <svg class="toggle-icon" viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none" :style="{ transform: sectionOpen['scene-environment'] ? 'rotate(0deg)' : 'rotate(-90deg)' }"><polyline points="6 9 12 15 18 9"></polyline></svg>
            </div>
            <div v-show="sectionOpen['scene-environment']" class="subsection-content">
              <div class="environment-grid">
                <div class="env-item"><span class="env-icon">🌤️</span><span id="env-weather" class="env-value">{{ sidebarState.weather }}</span></div>
                <div class="env-item"><span class="env-icon">🕐</span><span id="env-time" class="env-value">{{ sidebarState.time }}</span></div>
              </div>
            </div>
          </div>

          <div class="scene-subsection">
            <div class="subsection-header" @click="toggleSection('scene-progress')">
              <span class="subsection-title">剧本进度</span>
              <svg class="toggle-icon" viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none" :style="{ transform: sectionOpen['scene-progress'] ? 'rotate(0deg)' : 'rotate(-90deg)' }"><polyline points="6 9 12 15 18 9"></polyline></svg>
            </div>
            <div v-show="sectionOpen['scene-progress']" class="subsection-content">
              <div class="progress-container">
                <div class="progress-bar-wrapper"><div id="dungeon-progress-bar" class="progress-bar" :style="{ width: sidebarState.progressWidth }"></div></div>
                <div id="dungeon-progress" class="progress-text">{{ sidebarState.progressText }}</div>
              </div>
              <div id="dungeon-progress-hint" class="progress-hint">{{ sidebarState.progressHint }}</div>
            </div>
          </div>

          <div class="scene-subsection">
            <div class="subsection-header" @click="toggleSection('scene-interact')">
              <span class="subsection-title">场景互动点</span>
              <svg class="toggle-icon" viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none" :style="{ transform: sectionOpen['scene-interact'] ? 'rotate(0deg)' : 'rotate(-90deg)' }"><polyline points="6 9 12 15 18 9"></polyline></svg>
            </div>
            <div v-show="sectionOpen['scene-interact']" class="subsection-content"><div class="interact-list"><div class="muted small-text">暂无可互动元素</div></div></div>
          </div>

          <div class="scene-subsection">
            <div class="subsection-header" @click="toggleSection('scene-challenge')">
              <span class="subsection-title">挑战信息</span>
              <svg class="toggle-icon" viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none" :style="{ transform: sectionOpen['scene-challenge'] ? 'rotate(0deg)' : 'rotate(-90deg)' }"><polyline points="6 9 12 15 18 9"></polyline></svg>
            </div>
            <div v-show="sectionOpen['scene-challenge']" class="subsection-content"><div class="challenge-info"><div class="muted small-text">暂无挑战信息</div></div></div>
          </div>
        </div>
      </section>

      <section class="sidebar-section characters-panel">
        <div class="sidebar-header">
          <div class="sidebar-title">周围人物与势力</div>
          <button class="panel-collapse-btn" aria-label="收起/展开" @click="togglePanel('characters')">
            <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" :style="{ transform: panelOpen.characters ? 'rotate(0deg)' : 'rotate(-90deg)' }"><polyline points="6 9 12 15 18 9"></polyline></svg>
          </button>
        </div>
        <div v-show="panelOpen.characters" class="sidebar-body characters-body">
          <div class="characters-subsection">
            <div class="subsection-header" @click="toggleSection('npc-list')">
              <span class="subsection-title">NPC列表</span>
              <svg class="toggle-icon" viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none" :style="{ transform: sectionOpen['npc-list'] ? 'rotate(0deg)' : 'rotate(-90deg)' }"><polyline points="6 9 12 15 18 9"></polyline></svg>
            </div>
            <div v-show="sectionOpen['npc-list']" id="npc-list" class="subsection-content">
              <div class="npc-grid">
                <div v-if="!sidebarState.npcs.length" class="muted small-text">暂无NPC</div>
                <div v-for="item in sidebarState.npcs" :key="item.character_id" class="npc-card">
                  <div class="npc-name">{{ item.name || item.character_id }}</div>
                  <div class="small-text muted">{{ item.ability_tier || '未知' }}</div>
                </div>
              </div>
            </div>
          </div>
          <div class="characters-subsection"><div class="subsection-header" @click="toggleSection('enemy-list')"><span class="subsection-title">敌对目标</span><svg class="toggle-icon" viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none" :style="{ transform: sectionOpen['enemy-list'] ? 'rotate(0deg)' : 'rotate(-90deg)' }"><polyline points="6 9 12 15 18 9"></polyline></svg></div><div v-show="sectionOpen['enemy-list']" class="subsection-content"><div class="enemy-grid"><div class="muted small-text">暂无敌对目标</div></div></div></div>
          <div class="characters-subsection"><div class="subsection-header" @click="toggleSection('faction-distribution')"><span class="subsection-title">势力分布</span><svg class="toggle-icon" viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none" :style="{ transform: sectionOpen['faction-distribution'] ? 'rotate(0deg)' : 'rotate(-90deg)' }"><polyline points="6 9 12 15 18 9"></polyline></svg></div><div v-show="sectionOpen['faction-distribution']" class="subsection-content"><div class="faction-list"><div class="muted small-text">暂无势力信息</div></div></div></div>
          <div class="characters-subsection"><div class="subsection-header" @click="toggleSection('social-relations')"><span class="subsection-title">社交关系</span><svg class="toggle-icon" viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none" :style="{ transform: sectionOpen['social-relations'] ? 'rotate(0deg)' : 'rotate(-90deg)' }"><polyline points="6 9 12 15 18 9"></polyline></svg></div><div v-show="sectionOpen['social-relations']" class="subsection-content"><div class="relation-list"><div class="muted small-text">暂无社交关系</div></div></div></div>
          <div class="characters-subsection"><div class="subsection-header" @click="toggleSection('party-info')"><span class="subsection-title">队伍信息</span><svg class="toggle-icon" viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none" :style="{ transform: sectionOpen['party-info'] ? 'rotate(0deg)' : 'rotate(-90deg)' }"><polyline points="6 9 12 15 18 9"></polyline></svg></div><div v-show="sectionOpen['party-info']" class="subsection-content"><div class="party-status"><div class="muted small-text">当前为单人模式</div></div></div></div>
          <div class="characters-subsection"><div class="subsection-header" @click="toggleSection('faction-quests')"><span class="subsection-title">势力任务</span><svg class="toggle-icon" viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none" :style="{ transform: sectionOpen['faction-quests'] ? 'rotate(0deg)' : 'rotate(-90deg)' }"><polyline points="6 9 12 15 18 9"></polyline></svg></div><div v-show="sectionOpen['faction-quests']" class="subsection-content"><div class="faction-quest-list"><div class="muted small-text">暂无可接任务</div></div></div></div>
        </div>
      </section>

      <section class="sidebar-section world-panel">
        <div class="sidebar-header">
          <div class="sidebar-title">地图与世界事件</div>
          <button class="panel-collapse-btn" aria-label="收起/展开" @click="togglePanel('world')">
            <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" :style="{ transform: panelOpen.world ? 'rotate(0deg)' : 'rotate(-90deg)' }"><polyline points="6 9 12 15 18 9"></polyline></svg>
          </button>
        </div>
        <div v-show="panelOpen.world" class="sidebar-body world-body">
          <div class="world-subsection"><div class="subsection-header" @click="toggleSection('area-map')"><span class="subsection-title">区域地图</span><svg class="toggle-icon" viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none" :style="{ transform: sectionOpen['area-map'] ? 'rotate(0deg)' : 'rotate(-90deg)' }"><polyline points="6 9 12 15 18 9"></polyline></svg></div><div v-show="sectionOpen['area-map']" class="subsection-content"><div class="map-container"><div class="map-placeholder"><span class="map-icon">🗺️</span><span class="map-text">点击展开地图</span></div></div></div></div>
          <div class="world-subsection"><div class="subsection-header" @click="toggleSection('world-map')"><span class="subsection-title">世界地图</span><svg class="toggle-icon" viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none" :style="{ transform: sectionOpen['world-map'] ? 'rotate(0deg)' : 'rotate(-90deg)' }"><polyline points="6 9 12 15 18 9"></polyline></svg></div><div v-show="sectionOpen['world-map']" class="subsection-content"><div class="world-map-btn"><button class="btn-secondary btn-small">查看世界地图</button></div></div></div>
          <div class="world-subsection"><div class="subsection-header" @click="toggleSection('event-markers')"><span class="subsection-title">事件标记</span><svg class="toggle-icon" viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none" :style="{ transform: sectionOpen['event-markers'] ? 'rotate(0deg)' : 'rotate(-90deg)' }"><polyline points="6 9 12 15 18 9"></polyline></svg></div><div v-show="sectionOpen['event-markers']" class="subsection-content"><div class="event-list"><div class="muted small-text">暂无进行中的事件</div></div></div></div>
          <div class="world-subsection"><div class="subsection-header" @click="toggleSection('quick-travel')"><span class="subsection-title">快速旅行</span><svg class="toggle-icon" viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none" :style="{ transform: sectionOpen['quick-travel'] ? 'rotate(0deg)' : 'rotate(-90deg)' }"><polyline points="6 9 12 15 18 9"></polyline></svg></div><div v-show="sectionOpen['quick-travel']" class="subsection-content"><div class="travel-list"><div class="muted small-text">暂无已发现地点</div></div></div></div>
          <div class="world-subsection"><div class="subsection-header" @click="toggleSection('exploration-progress')"><span class="subsection-title">探索进度</span><svg class="toggle-icon" viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none" :style="{ transform: sectionOpen['exploration-progress'] ? 'rotate(0deg)' : 'rotate(-90deg)' }"><polyline points="6 9 12 15 18 9"></polyline></svg></div><div v-show="sectionOpen['exploration-progress']" class="subsection-content"><div class="exploration-stats"><div class="exploration-item"><span class="exploration-label">已探索区域</span><span class="exploration-value">0/0</span></div><div class="exploration-item"><span class="exploration-label">隐藏地点</span><span class="exploration-value">0/0</span></div></div></div></div>
          <div class="world-subsection"><div class="subsection-header" @click="toggleSection('event-calendar')"><span class="subsection-title">事件日历</span><svg class="toggle-icon" viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none" :style="{ transform: sectionOpen['event-calendar'] ? 'rotate(0deg)' : 'rotate(-90deg)' }"><polyline points="6 9 12 15 18 9"></polyline></svg></div><div v-show="sectionOpen['event-calendar']" class="subsection-content"><div class="calendar-list"><div class="muted small-text">暂无即将发生的事件</div></div></div></div>
        </div>
      </section>
    </aside>
  </main>

  <footer :class="['input-bar', { 'input-bar--collapsed': inputCollapsed, 'input-bar--half-screen': inputHalfScreen }]" id="input-bar">
    <div class="input-container">
      <div class="input-header-row">
        <div class="input-header-left">
          <button type="button" class="icon-button input-collapse-btn" id="input-collapse-toggle" aria-label="收起/展开" @click="inputCollapsed = !inputCollapsed">
            <svg viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round" :style="{ transform: inputCollapsed ? 'rotate(180deg)' : 'rotate(0deg)' }"><polyline points="6 9 12 15 18 9"></polyline></svg>
          </button>
          <div class="input-header-desc">Storyteller Console · <span id="session-label-inline">{{ sessionLabel }}</span></div>
        </div>
        <div class="input-header-actions">
          <button v-show="inputCollapsed" id="generate-btn-collapsed" class="btn-primary btn-small" @click="submit">{{ isGenerating ? '生成中' : '发送' }}</button>
        </div>
      </div>

      <div v-show="!inputCollapsed" id="input-body" class="input-body">
        <div id="action-suggestions" :class="['action-suggestions', { 'action-suggestions--open': actionSuggestionsOpen }]">
          <div class="action-suggestions-header">
            <button type="button" id="action-suggestions-toggle" class="action-suggestions-toggle" @click="actionSuggestionsOpen = !actionSuggestionsOpen">
              ✨ 下次行动建议 (点击{{ actionSuggestionsOpen ? '收起' : '展开' }})
            </button>
          </div>
          <div v-show="actionSuggestionsOpen" id="action-suggestions-body" class="action-suggestions-body">
            <div v-if="!actionSuggestions.length" class="empty-suggestions" style="color: var(--text-secondary); font-size: 12px; padding: 8px; text-align: center;">暂无行动建议</div>
            <button v-for="(item, index) in actionSuggestions" :key="`${index}-${item}`" type="button" class="suggestion-chip" :data-suggest="item" @click="useSuggestion(item)">
              {{ index + 1 }}. {{ item }}
            </button>
          </div>
        </div>

        <div class="input-main">
          <div class="input-main-inner">
            <textarea
              id="user-input"
              v-model="userInput"
              class="input-textarea"
              rows="1"
              placeholder="请输入行动"
              @keydown.ctrl.enter.prevent="submit"
            ></textarea>
            <button type="button" class="input-size-toggle" id="input-size-toggle" aria-label="切换半屏模式" title="切换半屏专注模式" @click="inputHalfScreen = !inputHalfScreen">
              <svg viewBox="0 0 24 24"><path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>
            </button>
          </div>
          <div class="input-actions">
            <div id="input-hint" class="input-hint">Ctrl + Enter 发送</div>
            <button id="generate-btn" class="btn-primary btn-small" :disabled="isGenerating" @click="submit">{{ isGenerating ? '生成中...' : '生成下一段' }}</button>
          </div>
          <div id="input-status" class="small-text input-status" style="text-align: right;">{{ inputStatus }}</div>
        </div>
      </div>
    </div>
  </footer>

  <StoryFontSettingsModal
    v-model="fontSettings"
    :open="fontModalOpen"
    @close="fontModalOpen = false"
    @save="saveFontSettings"
    @reset="resetFontSettings"
  />

  <div v-if="rawTextBlock" id="raw-text-modal" class="modal-overlay">
    <div class="modal-window" style="max-width: 900px;">
      <div class="modal-header">
        <h3 class="modal-title">原文</h3>
        <button class="modal-close-btn" aria-label="关闭" @click="rawTextBlock = null">&times;</button>
      </div>
      <div class="modal-body" style="white-space: pre-wrap; font-family: var(--font-raw-family); font-size: var(--font-raw-size); font-weight: var(--font-raw-weight);">
        {{ rawTextBlock.rawText }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue';
import StoryFontSettingsModal from '../components/story/StoryFontSettingsModal.vue';
import StoryLogBlock from '../components/story/StoryLogBlock.vue';
import { useStoryPage } from '../composables/useStoryPage';
import { initThemePage } from '../page_logic/theme-init.module';

const {
  actionHistory,
  actionSuggestions,
  actionSuggestionsOpen,
  backendDuration,
  bootstrap,
  fontModalOpen,
  fontSettings,
  frontendDuration,
  inputCollapsed,
  inputHalfScreen,
  inputStatus,
  isGenerating,
  panelOpen,
  rawTextBlock,
  saveFontSettings,
  resetFontSettings,
  sectionOpen,
  sessionLabel,
  sidebarState,
  storyBlocks,
  storyLogRef,
  submit,
  timerVisible,
  togglePanel,
  toggleSection,
  useSuggestion,
  userInput,
} = useStoryPage();

onMounted(async () => {
  document.title = 'Storyteller | 剧情';
  document.body.setAttribute('data-page', 'index');
  initThemePage();
  await bootstrap();
});
</script>
