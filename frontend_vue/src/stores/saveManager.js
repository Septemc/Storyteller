import { defineStore } from 'pinia';
import { useSessionStore } from './session';
import * as storyApi from '../services/modules/story';

function fallbackDisplayName(sessionId) {
  return sessionId || '未加载存档';
}

export const useSaveManagerStore = defineStore('saveManager', {
  state: () => ({
    modalOpen: false,
    renameOpen: false,
    selectedSaveId: '',
    renameValue: '',
    saves: [],
    currentDetail: null,
    currentDisplayName: '未加载存档',
    currentDisplayId: '--',
    loading: false,
    statusText: '',
  }),
  getters: {
    hasSelectedSave: (state) => Boolean(state.selectedSaveId),
    selectedSave(state) {
      return state.saves.find((item) => item.session_id === state.selectedSaveId) || null;
    },
  },
  actions: {
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
        this.setCurrentSave(detail?.display_name, sessionId);
      } catch {
        this.setCurrentSave(null, sessionId);
      }
    },
    async loadSaves() {
      this.loading = true;
      try {
        this.saves = await storyApi.savesList();
      } finally {
        this.loading = false;
      }
    },
    async selectSave(sessionId) {
      this.selectedSaveId = sessionId;
      if (!sessionId) {
        this.currentDetail = null;
        return;
      }
      this.currentDetail = await storyApi.saveDetail(sessionId);
    },
    async openModal() {
      this.modalOpen = true;
      await this.loadSaves();
      const sessionStore = useSessionStore();
      if (sessionStore.currentSessionId) {
        await this.selectSave(sessionStore.currentSessionId);
      }
    },
    closeModal() {
      this.modalOpen = false;
    },
    openRename() {
      if (!this.currentDetail?.session_id) return;
      this.renameValue = this.currentDetail.display_name || this.currentDetail.session_id;
      this.renameOpen = true;
    },
    closeRename() {
      this.renameOpen = false;
      this.renameValue = '';
    },
    async createSave() {
      const created = await storyApi.createSave();
      await this.loadSaves();
      await this.selectSave(created.session_id);
      return created;
    },
    async renameSelected() {
      if (!this.selectedSaveId || !this.renameValue.trim()) return;
      await storyApi.renameSave({
        session_id: this.selectedSaveId,
        display_name: this.renameValue.trim(),
      });
      this.closeRename();
      await this.loadSaves();
      await this.selectSave(this.selectedSaveId);
      const sessionStore = useSessionStore();
      if (sessionStore.currentSessionId === this.selectedSaveId) {
        this.setCurrentSave(this.currentDetail?.display_name, this.selectedSaveId);
      }
    },
    async deleteSelected() {
      if (!this.selectedSaveId) return;
      await storyApi.deleteSave(this.selectedSaveId);
      const deletedId = this.selectedSaveId;
      this.selectedSaveId = '';
      this.currentDetail = null;
      await this.loadSaves();
      const sessionStore = useSessionStore();
      if (sessionStore.currentSessionId === deletedId) {
        sessionStore.reset();
        await this.syncCurrentSession();
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
