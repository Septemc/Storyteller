import { defineStore } from 'pinia';
import * as storyApi from '../services/modules/story';
import { useSessionStore } from './session';
import { DEV_MODE_KEY, buildStoryTree, fallbackName, loadDeveloperMode, normalizeSave, pickSessionId } from './saveManager.utils';

export const useSaveManagerStore = defineStore('saveManager', {
  state: () => ({
    modalOpen: false,
    renameOpen: false,
    renameTargetType: 'session',
    renameTargetId: '',
    renameValue: '',
    selectedStoryId: '',
    selectedSaveId: '',
    saves: [],
    currentDetail: null,
    currentDisplayName: '未载入存档',
    currentDisplayId: '--',
    loading: false,
    developerMode: loadDeveloperMode(),
  }),
  getters: {
    storyTree(state) {
      return buildStoryTree(state.saves);
    },
    selectedStory(state) {
      return this.storyTree.find((item) => item.story_id === state.selectedStoryId) || null;
    },
    selectedSessionDetail(state) {
      if (!state.currentDetail?.branches?.length) return null;
      return state.currentDetail.branches.find((item) => item.session_id === state.selectedSaveId) || null;
    },
    renameDialogTitle(state) {
      return state.renameTargetType === 'story' ? '重命名故事' : '重命名 SessionState';
    },
    renameDialogLabel(state) {
      return state.renameTargetType === 'story' ? '故事名称' : 'SessionState 名称';
    },
  },
  actions: {
    setDeveloperMode(value) {
      this.developerMode = !!value;
      window.localStorage.setItem(DEV_MODE_KEY, this.developerMode ? '1' : '0');
    },
    setCurrentSave(displayName, sessionId) {
      this.currentDisplayId = sessionId || '--';
      this.currentDisplayName = displayName || fallbackName(sessionId);
    },
    mergeSave(detail) {
      if (!detail?.session_id) return;
      const payload = normalizeSave(detail);
      const current = this.saves.find((item) => item.session_id === detail.session_id);
      if (current) Object.assign(current, payload);
      else this.saves.unshift(payload);
    },
    async loadSaves() {
      this.loading = true;
      try {
        this.saves = (await storyApi.savesList()).map((item) => normalizeSave(item));
      } finally {
        this.loading = false;
      }
    },
    async syncCurrentSession() {
      const sessionStore = useSessionStore();
      if (!sessionStore.currentSessionId) {
        this.setCurrentSave('', '');
        return;
      }
      try {
        const detail = await storyApi.saveDetail(sessionStore.currentSessionId);
        this.currentDetail = detail;
        this.selectedSaveId = detail.session_id;
        this.selectedStoryId = detail.story_id || this.selectedStoryId;
        this.mergeSave(detail);
        this.setCurrentSave(detail.branch_display_name || detail.display_name, detail.session_id);
      } catch {
        this.setCurrentSave('', sessionStore.currentSessionId);
      }
    },
    async selectStory(storyId, preferredSessionId = '') {
      this.selectedStoryId = storyId;
      const story = this.storyTree.find((item) => item.story_id === storyId);
      const nextSessionId = pickSessionId(story, preferredSessionId || this.selectedSaveId);
      if (!nextSessionId) {
        this.selectedSaveId = '';
        this.currentDetail = null;
        return;
      }
      await this.selectSave(nextSessionId, storyId);
    },
    async selectSave(sessionId, storyId = '') {
      this.selectedSaveId = sessionId;
      if (storyId) this.selectedStoryId = storyId;
      this.currentDetail = sessionId ? await storyApi.saveDetail(sessionId) : null;
      if (this.currentDetail) {
        this.selectedStoryId = this.currentDetail.story_id || this.selectedStoryId;
        this.mergeSave(this.currentDetail);
      }
    },
    async openModal() {
      this.modalOpen = true;
      await this.loadSaves();
      const sessionStore = useSessionStore();
      const preferredSessionId = sessionStore.currentSessionId || this.saves[0]?.session_id || '';
      if (preferredSessionId) await this.selectSave(preferredSessionId);
      else if (this.storyTree[0]?.story_id) await this.selectStory(this.storyTree[0].story_id);
    },
    closeModal() {
      this.modalOpen = false;
      this.closeRename();
    },
    openRename(targetType = 'session') {
      this.renameTargetType = targetType;
      this.renameTargetId = targetType === 'story' ? this.currentDetail?.story_id || '' : this.selectedSaveId;
      this.renameValue = targetType === 'story'
        ? this.currentDetail?.story_title || ''
        : this.currentDetail?.branch_display_name || this.currentDetail?.display_name || this.selectedSaveId;
      this.renameOpen = Boolean(this.renameTargetId);
    },
    closeRename() {
      this.renameOpen = false;
      this.renameTargetType = 'session';
      this.renameTargetId = '';
      this.renameValue = '';
    },
    async createStory() {
      const created = await (storyApi.createStory?.() || storyApi.createSave());
      await this.loadSaves();
      await this.selectSave(created.session_id);
    },
    async createSessionState() {
      if (!this.selectedSaveId) return;
      const created = await storyApi.createBranch({ source_session_id: this.selectedSaveId });
      await this.loadSaves();
      await this.selectSave(created.session_id, created.story_id || this.selectedStoryId);
    },
    async renameSelected() {
      const nextValue = this.renameValue.trim();
      if (!nextValue) return;
      if (this.renameTargetType === 'story') {
        await storyApi.renameStory({ story_id: this.currentDetail.story_id, title: nextValue });
      } else {
        await storyApi.renameBranch({ session_id: this.selectedSaveId, display_name: nextValue });
      }
      this.closeRename();
      await this.loadSaves();
      if (this.selectedSaveId) await this.selectSave(this.selectedSaveId, this.selectedStoryId);
    },
    async deleteSelected() {
      if (!this.selectedSaveId) return;
      const deletedSessionId = this.selectedSaveId;
      const deletedStoryId = this.selectedStoryId;
      await storyApi.deleteSave(deletedSessionId);
      await this.loadSaves();
      const replacement = this.saves.find((item) => item.story_id === deletedStoryId) || this.saves[0] || null;
      const sessionStore = useSessionStore();
      if (sessionStore.currentSessionId === deletedSessionId) {
        if (replacement?.session_id) sessionStore.setSessionId(replacement.session_id);
        else sessionStore.reset();
        await this.syncCurrentSession();
      }
      if (replacement?.session_id) await this.selectSave(replacement.session_id, replacement.story_id);
      else {
        this.selectedSaveId = '';
        this.currentDetail = null;
      }
    },
    async loadSelectedIntoSession() {
      if (!this.selectedSaveId) return;
      useSessionStore().setSessionId(this.selectedSaveId);
      await this.syncCurrentSession();
      this.closeModal();
    },
  },
});
