import { defineStore } from 'pinia';
import { STORAGE_KEYS } from '../constants/storage';

function createSessionId() {
  const now = Date.now();
  const rand = Math.random().toString(36).slice(2, 8).toUpperCase();
  return `S_${now}_${rand}`;
}

export const useSessionStore = defineStore('session', {
  state: () => ({
    currentSessionId: '',
  }),
  actions: {
    bootstrap() {
      const cached = localStorage.getItem(STORAGE_KEYS.sessionId);
      this.currentSessionId = cached || createSessionId();
      localStorage.setItem(STORAGE_KEYS.sessionId, this.currentSessionId);
    },
    setSessionId(sessionId) {
      this.currentSessionId = sessionId;
      localStorage.setItem(STORAGE_KEYS.sessionId, sessionId);
    },
    reset() {
      this.setSessionId(createSessionId());
    },
  },
});

