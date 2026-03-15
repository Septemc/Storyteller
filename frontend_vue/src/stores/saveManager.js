import { defineStore } from 'pinia';
import * as storyApi from '../services/modules/story';
import { useSessionStore } from './session';

const DEV_MODE_KEY = 'storyteller_developer_mode_v1';

function fallbackDisplayName(sessionId) {
  return sessionId || '未加载分支';
}

function loadDeveloperMode() {
  try {
    return window.localStorage.getItem(DEV_MODE_KEY) === '1';
  } catch {
    return false;
  }
}

function normalizeSave(item = {}) {
  return {
    session_id: item.session_id || '',
    display_name: item.display_name || item.session_id || '',
    updated_at: item.updated_at || null,
    created_at: item.created_at || null,
    segment_count: item.segment_count ?? 0,
    total_word_count: item.total_word_count ?? 0,
    story_id: item.story_id || `session:${item.session_id || 'unknown'}`,
    story_title: item.story_title || item.display_name || item.session_id || '未命名故事',
    branch_id: item.branch_id || null,
    branch_display_name: item.branch_display_name || item.branch_type || item.display_name || item.session_id || '未命名分支',
    branch_type: item.branch_type || null,
    branch_status: item.branch_status || null,
    parent_branch_id: item.parent_branch_id || null,
    reasoning_strength: item.reasoning_strength || null,
  };
}

function pickPreferredSession(group, selectedSaveId) {
  if (!group?.branches?.length) return '';
  if (selectedSaveId && group.branches.some((item) => item.session_id === selectedSaveId)) {
    return selectedSaveId;
  }
  return group.branches[0]?.session_id || '';
}

export const useSaveManagerStore = defineStore('saveManager', {
  state: () => ({
    modalOpen: false,
    renameOpen: false,
    renameTargetType: 'branch',
    renameTargetId: '',
    selectedStoryId: '',
    selectedSaveId: '',
    renameValue: '',
    saves: [],
    currentDetail: null,
    currentDisplayName: '未加载分支',
    currentDisplayId: '--',
    loading: false,
    statusText: '',
    developerMode: loadDeveloperMode(),
  }),
  getters: {
    hasSelectedSave: (state) => Boolean(state.selectedSaveId),
    selectedSave(state) {
      return state.saves.find((item) => item.session_id === state.selectedSaveId) || null;
    },
    storyGroups(state) {
      const groups = new Map();
      for (const rawItem of state.saves) {
        const item = normalizeSave(rawItem);
        const storyId = item.story_id;
        if (!groups.has(storyId)) {
          groups.set(storyId, {
            story_id: storyId,
            story_title: item.story_title,
            branch_count: 0,
            total_word_count: 0,
            updated_at: item.updated_at || null,
            branches: [],
          });
        }
        const group = groups.get(storyId);
        group.story_title = item.story_title || group.story_title;
        group.branch_count += 1;
        group.total_word_count += item.total_word_count || 0;
        group.updated_at = [group.updated_at, item.updated_at].filter(Boolean).sort().reverse()[0] || group.updated_at;
        group.branches.push(item);
      }
      return [...groups.values()]
        .map((group) => ({
          ...group,
          branches: group.branches.sort((left, right) => `${right.updated_at || ''}`.localeCompare(`${left.updated_at || ''}`)),
          selected_session_id: pickPreferredSession(group, state.selectedSaveId),
        }))
        .sort((left, right) => `${right.updated_at || ''}`.localeCompare(`${left.updated_at || ''}`));
    },
    selectedStory(state) {
      return this.storyGroups.find((item) => item.story_id === state.selectedStoryId) || null;
    },
    selectedBranchSummary(state) {
      if (state.currentDetail?.branches?.length) {
        return state.currentDetail.branches.find((item) => item.session_id === state.selectedSaveId) || null;
      }
      return state.saves.find((item) => item.session_id === state.selectedSaveId) || null;
    },
    renameDialogTitle(state) {
      return state.renameTargetType === 'story' ? '重命名故事' : '重命名分支';
    },
    renameDialogLabel(state) {
      return state.renameTargetType === 'story' ? '故事名称' : '分支名称';
    },
  },
  actions: {
    setDeveloperMode(value) {
      this.developerMode = !!value;
      window.localStorage.setItem(DEV_MODE_KEY, this.developerMode ? '1' : '0');
    },
    ensureSaveInList(detail) {
      if (!detail?.session_id) return;
      const payload = normalizeSave(detail);
      const existing = this.saves.find((item) => item.session_id === detail.session_id);
      if (existing) {
        Object.assign(existing, payload);
        return;
      }
      this.saves.unshift(payload);
    },
    setCurrentSave(displayName, sessionId) {
      this.currentDisplayId = sessionId || '--';
      this.currentDisplayName = displayName || fallbackDisplayName(sessionId);
    },
    async syncCurrentSession() {
      const sessionStore = useSessionStore();
      const sessionId = sessionStore.currentSessionId;
      if (!sessionId) {
        this.setCurrentSave(null, null);
        return;
      }
      try {
        const detail = await storyApi.saveDetail(sessionId);
        this.currentDetail = detail;
        this.selectedSaveId = sessionId;
        this.selectedStoryId = detail?.story_id || this.selectedStoryId;
        this.ensureSaveInList(detail);
        this.setCurrentSave(detail?.branch_display_name || detail?.display_name, sessionId);
      } catch {
        this.setCurrentSave(null, sessionId);
      }
    },
    async loadSaves() {
      this.loading = true;
      try {
        this.saves = (await storyApi.savesList()).map((item) => normalizeSave(item));
      } finally {
        this.loading = false;
      }
    },
    async selectStory(storyId, preferredSessionId = '') {
      this.selectedStoryId = storyId;
      const group = this.storyGroups.find((item) => item.story_id === storyId);
      const nextSessionId = preferredSessionId || pickPreferredSession(group, this.selectedSaveId);
      if (nextSessionId) {
        await this.selectSave(nextSessionId, { storyId });
        return;
      }
      this.selectedSaveId = '';
      this.currentDetail = null;
    },
    async selectSave(sessionId, options = {}) {
      this.selectedSaveId = sessionId;
      if (options.storyId) {
        this.selectedStoryId = options.storyId;
      }
      this.currentDetail = sessionId ? await storyApi.saveDetail(sessionId) : null;
      if (this.currentDetail) {
        this.selectedStoryId = this.currentDetail.story_id || this.selectedStoryId;
        this.ensureSaveInList(this.currentDetail);
      }
    },
    async openModal() {
      this.modalOpen = true;
      await this.loadSaves();
      const sessionStore = useSessionStore();
      const nextId = sessionStore.currentSessionId || this.saves[0]?.session_id;
      if (nextId) {
        await this.selectSave(nextId);
        return;
      }
      if (this.storyGroups[0]?.story_id) {
        await this.selectStory(this.storyGroups[0].story_id);
      }
    },
    closeModal() {
      this.modalOpen = false;
      this.closeRename();
    },
    openRename(targetType = 'branch') {
      if (targetType === 'story') {
        if (!this.currentDetail?.story_id) return;
        this.renameTargetType = 'story';
        this.renameTargetId = this.currentDetail.story_id;
        this.renameValue = this.currentDetail.story_title || '';
      } else {
        if (!this.currentDetail?.session_id) return;
        this.renameTargetType = 'branch';
        this.renameTargetId = this.currentDetail.session_id;
        this.renameValue = this.currentDetail.branch_display_name || this.currentDetail.display_name || this.currentDetail.session_id;
      }
      this.renameOpen = true;
    },
    closeRename() {
      this.renameOpen = false;
      this.renameTargetType = 'branch';
      this.renameTargetId = '';
      this.renameValue = '';
    },
    async createStory() {
      const created = await (storyApi.createStory?.() || storyApi.createSave());
      await this.loadSaves();
      await this.selectSave(created.session_id);
      this.setCurrentSave(this.currentDetail?.branch_display_name || this.currentDetail?.display_name, created.session_id);
      return created;
    },
    async createBranch() {
      if (!this.selectedSaveId) return null;
      const created = await storyApi.createBranch({ source_session_id: this.selectedSaveId });
      await this.loadSaves();
      await this.selectSave(created.session_id, { storyId: created.story_id || this.selectedStoryId });
      return created;
    },
    async renameSelected() {
      const nextValue = this.renameValue.trim();
      if (!nextValue) return;
      if (this.renameTargetType === 'story') {
        if (!this.currentDetail?.story_id) return;
        await storyApi.renameStory({ story_id: this.currentDetail.story_id, title: nextValue });
      } else {
        if (!this.selectedSaveId) return;
        await storyApi.renameBranch({ session_id: this.selectedSaveId, display_name: nextValue });
      }
      this.closeRename();
      await this.loadSaves();
      if (this.selectedSaveId) {
        await this.selectSave(this.selectedSaveId, { storyId: this.selectedStoryId });
      }
      const sessionStore = useSessionStore();
      if (sessionStore.currentSessionId === this.selectedSaveId) {
        this.setCurrentSave(this.currentDetail?.branch_display_name || this.currentDetail?.display_name, this.selectedSaveId);
      }
    },
    async deleteSelected() {
      if (!this.selectedSaveId) return;
      const deletedId = this.selectedSaveId;
      const deletedStoryId = this.selectedStoryId;
      await storyApi.deleteSave(this.selectedSaveId);
      this.selectedSaveId = '';
      this.currentDetail = null;
      await this.loadSaves();
      const sessionStore = useSessionStore();
      const nextInSameStory = this.saves.find((item) => item.story_id === deletedStoryId);
      const fallback = nextInSameStory || this.saves[0] || null;
      if (sessionStore.currentSessionId === deletedId) {
        if (fallback?.session_id) {
          sessionStore.setSessionId(fallback.session_id);
          await this.syncCurrentSession();
        } else {
          sessionStore.reset();
          await this.syncCurrentSession();
        }
      }
      if (fallback?.session_id) {
        await this.selectSave(fallback.session_id, { storyId: fallback.story_id });
      }
    },
    async loadSelectedIntoSession() {
      if (!this.selectedSaveId) return;
      const sessionStore = useSessionStore();
      sessionStore.setSessionId(this.selectedSaveId);
      await this.syncCurrentSession();
      this.closeModal();
    },
  },
});
