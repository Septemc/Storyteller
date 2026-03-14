import { computed, nextTick, reactive, ref, watch } from 'vue';
import * as storyApi from '../services/modules/story';
import { useSaveManagerStore } from '../stores/saveManager';
import { useSessionStore } from '../stores/session';

const FONT_STORAGE_KEY = 'storyteller_story_font_settings_v1';

function createDefaultFontSettings() {
  return {
    thinking: { family: 'system-ui, -apple-system, "Segoe UI", sans-serif', size: '12px', bold: false },
    body: { family: 'system-ui, -apple-system, "Segoe UI", sans-serif', size: '14px', bold: false },
    summary: { family: 'system-ui, -apple-system, "Segoe UI", sans-serif', size: '12px', bold: false },
    raw: { family: 'system-ui, -apple-system, "Segoe UI", sans-serif', size: '12px', bold: false },
    stats: { family: 'system-ui, -apple-system, "Segoe UI", sans-serif', size: '12px', bold: false },
    bodyIndent: false,
  };
}

function parseTaggedContent(text, tagName) {
  if (!text) return '';
  const match = String(text).match(new RegExp(`<${tagName}>([\\s\\S]*?)</${tagName}>`));
  return match?.[1]?.trim() || '';
}

function extractMainContent(text) {
  if (!text) return '';
  const story = parseTaggedContent(text, '正文部分');
  if (story) return story;
  return String(text)
    .replace(/<思考过程>[\s\S]*?<\/思考过程>/g, '')
    .replace(/<内容总结>[\s\S]*?<\/内容总结>/g, '')
    .replace(/<行动选项>[\s\S]*?<\/行动选项>/g, '')
    .trim();
}

function extractActionOptions(text) {
  const optionsText = parseTaggedContent(text, '行动选项');
  if (!optionsText) return [];

  return optionsText
    .split('\n')
    .map((line) =>
      line
        .trim()
        .replace(/^\d+[:：.、\s]+/, '')
        .replace(/^[-•]\s*/, '')
        .replace(/^[一二三四五六七八九十]+[.、\s]+/, '')
        .trim(),
    )
    .filter(Boolean);
}

function buildBlocks(segments) {
  const blocks = [];
  for (const segment of segments) {
    if (segment.user_input) {
      blocks.push({
        id: `${segment.segment_id}-user`,
        type: 'user',
        displayText: segment.user_input,
      });
    }

    blocks.push({
      id: segment.segment_id,
      segmentId: segment.segment_id,
      type: 'assistant',
      rawText: segment.text,
      displayText: extractMainContent(segment.text),
      thinkingText: parseTaggedContent(segment.text, '思考过程'),
      summaryText: parseTaggedContent(segment.text, '内容总结'),
      actionOptions: extractActionOptions(segment.text),
      stats: {
        paragraph_word_count: segment.paragraph_word_count,
        cumulative_word_count: segment.cumulative_word_count,
        frontend_duration: segment.frontend_duration,
        backend_duration: segment.backend_duration,
      },
      metaText: 'AI输出',
    });
  }
  return blocks;
}

export function useStoryPage() {
  const sessionStore = useSessionStore();
  const saveStore = useSaveManagerStore();

  const storyLogRef = ref(null);
  const userInput = ref('');
  const inputStatus = ref('');
  const storyBlocks = ref([]);
  const rawTextBlock = ref(null);
  const fontModalOpen = ref(false);
  const inputCollapsed = ref(false);
  const inputHalfScreen = ref(false);
  const actionSuggestionsOpen = ref(false);
  const isGenerating = ref(false);
  const timerVisible = ref(false);
  const frontendDuration = ref(0);
  const backendDuration = ref(0);
  const fontSettings = ref(createDefaultFontSettings());

  const panelOpen = reactive({
    player: true,
    scene: true,
    characters: true,
    world: true,
  });

  const sectionOpen = reactive({
    'player-stats': true,
    'player-resources': true,
    'player-abilities': true,
    'player-factions': true,
    'player-inventory': true,
    'player-buffs': true,
    'action-history': true,
    'scene-info': true,
    'scene-quests': true,
    'scene-environment': true,
    'scene-progress': true,
    'scene-interact': true,
    'scene-challenge': true,
    'npc-list': true,
    'enemy-list': true,
    'faction-distribution': true,
    'social-relations': true,
    'party-info': true,
    'faction-quests': true,
    'area-map': true,
    'world-map': true,
    'event-markers': true,
    'quick-travel': true,
    'exploration-progress': true,
    'event-calendar': true,
  });

  const sidebarState = reactive({
    economy: '未知',
    ability: '未知',
    faction: '未知',
    gold: '0',
    diamond: '0',
    dungeonName: '暂无',
    dungeonNodeName: '暂无',
    sceneDescription: '暂无场景描述',
    questName: '暂无任务',
    weather: '晴朗',
    time: '白天',
    progressText: '0%',
    progressHint: '暂无进度提示',
    progressWidth: '0%',
    npcs: [],
  });

  const sessionLabel = computed(() => saveStore.currentDisplayName || sessionStore.currentSessionId || 'Ready');
  const actionSuggestions = computed(() => {
    const latestAssistant = [...storyBlocks.value].reverse().find((item) => item.type === 'assistant');
    return latestAssistant?.actionOptions?.length ? latestAssistant.actionOptions : [];
  });
  const actionHistory = computed(() =>
    storyBlocks.value.filter((item) => item.type === 'user').map((item) => item.displayText).slice(-8),
  );

  function applyFontSettings(settings) {
    const root = document.documentElement;
    root.style.setProperty('--font-thinking-family', settings.thinking.family);
    root.style.setProperty('--font-thinking-size', settings.thinking.size);
    root.style.setProperty('--font-thinking-weight', settings.thinking.bold ? '700' : '400');
    root.style.setProperty('--font-body-family', settings.body.family);
    root.style.setProperty('--font-body-size', settings.body.size);
    root.style.setProperty('--font-body-weight', settings.body.bold ? '700' : '400');
    root.style.setProperty('--font-summary-family', settings.summary.family);
    root.style.setProperty('--font-summary-size', settings.summary.size);
    root.style.setProperty('--font-summary-weight', settings.summary.bold ? '700' : '400');
    root.style.setProperty('--font-raw-family', settings.raw.family);
    root.style.setProperty('--font-raw-size', settings.raw.size);
    root.style.setProperty('--font-raw-weight', settings.raw.bold ? '700' : '400');
    root.style.setProperty('--font-stats-family', settings.stats.family);
    root.style.setProperty('--font-stats-size', settings.stats.size);
    root.style.setProperty('--font-stats-weight', settings.stats.bold ? '700' : '400');
    root.style.setProperty('--story-body-text-indent', settings.bodyIndent ? '2em' : '0');
  }

  function loadFontSettings() {
    try {
      const cached = window.localStorage.getItem(FONT_STORAGE_KEY);
      if (cached) {
        fontSettings.value = { ...createDefaultFontSettings(), ...JSON.parse(cached) };
      }
    } catch {
      fontSettings.value = createDefaultFontSettings();
    }
    applyFontSettings(fontSettings.value);
  }

  function saveFontSettings() {
    window.localStorage.setItem(FONT_STORAGE_KEY, JSON.stringify(fontSettings.value));
    applyFontSettings(fontSettings.value);
    fontModalOpen.value = false;
  }

  function resetFontSettings() {
    fontSettings.value = createDefaultFontSettings();
    applyFontSettings(fontSettings.value);
  }

  async function scrollToBottom() {
    await nextTick();
    if (storyLogRef.value) {
      storyLogRef.value.scrollTop = storyLogRef.value.scrollHeight;
    }
  }

  async function refreshStory() {
    const response = await storyApi.recent({
      session_id: sessionStore.currentSessionId,
      limit: 80,
    });
    storyBlocks.value = buildBlocks(response?.segments || []);
    await scrollToBottom();
  }

  async function refreshSummary() {
    const summary = await storyApi.updateSessionContext({
      session_id: sessionStore.currentSessionId,
    });

    sidebarState.dungeonName = summary?.dungeon?.name || '暂无';
    sidebarState.dungeonNodeName = summary?.dungeon?.current_node_name || '暂无';
    sidebarState.progressHint = summary?.dungeon?.progress_hint || '暂无进度提示';

    const mainCharacter = summary?.variables?.main_character || {};
    sidebarState.economy = mainCharacter?.economy_summary || summary?.variables?.faction_summary || '未知';
    sidebarState.ability = mainCharacter?.ability_tier || '未知';
    sidebarState.faction = summary?.variables?.faction_summary || '未知';
    sidebarState.npcs = (summary?.characters || []).filter((item) => item.character_id !== mainCharacter?.character_id);
  }

  async function bootstrap() {
    sessionStore.bootstrap();
    saveStore.setCurrentSave(null, sessionStore.currentSessionId);
    loadFontSettings();
    await Promise.allSettled([saveStore.syncCurrentSession(), refreshStory(), refreshSummary()]);
  }

  async function submit() {
    const input = userInput.value.trim();
    if (!input || isGenerating.value) {
      return;
    }

    isGenerating.value = true;
    timerVisible.value = true;
    frontendDuration.value = 0;
    backendDuration.value = 0;
    inputStatus.value = '生成中...';

    const startedAt = performance.now();
    const pendingUserBlock = {
      id: `pending-user-${Date.now()}`,
      type: 'user',
      displayText: input,
    };
    const pendingAssistantBlock = {
      id: `pending-assistant-${Date.now()}`,
      type: 'assistant',
      displayText: '',
      rawText: '',
      thinkingText: '',
      summaryText: '',
      actionOptions: [],
      stats: null,
      metaText: 'AI输出',
    };

    storyBlocks.value = [...storyBlocks.value, pendingUserBlock, pendingAssistantBlock];
    userInput.value = '';
    await scrollToBottom();

    try {
      await storyApi.generateStream(
        {
          session_id: sessionStore.currentSessionId,
          user_input: input,
        },
        {
          onEvent(event, data) {
            if (event === 'delta') {
              pendingAssistantBlock.rawText += data.text || '';
              pendingAssistantBlock.displayText = extractMainContent(pendingAssistantBlock.rawText) || pendingAssistantBlock.rawText;
              pendingAssistantBlock.thinkingText = parseTaggedContent(pendingAssistantBlock.rawText, '思考过程');
              pendingAssistantBlock.summaryText = parseTaggedContent(pendingAssistantBlock.rawText, '内容总结');
              pendingAssistantBlock.actionOptions = extractActionOptions(pendingAssistantBlock.rawText);
              scrollToBottom();
            }
            if (event === 'meta') {
              backendDuration.value = Number((data?.duration_ms || 0) / 1000);
            }
            if (event === 'error') {
              throw new Error(data?.message || '??????????');
            }
            if (event === 'empty') {
              throw new Error(data?.message || '???????????????????');
            }
          },
        },
      );

      frontendDuration.value = (performance.now() - startedAt) / 1000;
      await refreshStory();
      await refreshSummary();

      const lastAssistant = [...storyBlocks.value].reverse().find((item) => item.type === 'assistant' && item.segmentId);
      if (lastAssistant?.segmentId) {
        try {
          await storyApi.updateFrontendDuration({
            segment_id: lastAssistant.segmentId,
            frontend_duration: frontendDuration.value,
          });
        } catch {
          // ignore telemetry failure
        }
      }

      inputStatus.value = '生成完成';
    } catch (error) {
      storyBlocks.value = storyBlocks.value.filter((item) => !String(item.id).startsWith('pending-'));
      inputStatus.value = error?.message || '生成失败';
    } finally {
      isGenerating.value = false;
    }
  }

  function useSuggestion(text) {
    userInput.value = text;
  }

  function togglePanel(name) {
    panelOpen[name] = !panelOpen[name];
  }

  function toggleSection(name) {
    sectionOpen[name] = !sectionOpen[name];
  }

  watch(
    fontSettings,
    (value) => {
      applyFontSettings(value);
    },
    { deep: true },
  );

  return {
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
    refreshStory,
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
  };
}
