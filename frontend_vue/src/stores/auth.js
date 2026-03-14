import { defineStore } from 'pinia';
import { STORAGE_KEYS } from '../constants/storage';
import * as authApi from '../services/modules/auth';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: '',
    user: null,
    loading: false,
  }),
  getters: {
    isAuthed: (state) => Boolean(state.token),
    username: (state) => state.user?.nickname || state.user?.username || '游客',
  },
  actions: {
    bootstrap() {
      try {
        const token = localStorage.getItem(STORAGE_KEYS.token) || '';
        const userRaw = localStorage.getItem(STORAGE_KEYS.user);
        this.token = token;
        this.user = userRaw ? JSON.parse(userRaw) : null;
      } catch {
        this.token = '';
        this.user = null;
        localStorage.removeItem(STORAGE_KEYS.token);
        localStorage.removeItem(STORAGE_KEYS.user);
      }
    },
    persist() {
      if (this.token) {
        localStorage.setItem(STORAGE_KEYS.token, this.token);
      } else {
        localStorage.removeItem(STORAGE_KEYS.token);
      }
      if (this.user) {
        localStorage.setItem(STORAGE_KEYS.user, JSON.stringify(this.user));
      } else {
        localStorage.removeItem(STORAGE_KEYS.user);
      }
    },
    clear() {
      this.token = '';
      this.user = null;
      this.persist();
    },
    async login(payload) {
      this.loading = true;
      try {
        const result = await authApi.login(payload);
        this.token = result.access_token;
        this.user = {
          user_id: result.user_id,
          username: result.username,
          role: result.role,
          nickname: result.username,
        };
        this.persist();
        await this.fetchMe();
      } finally {
        this.loading = false;
      }
    },
    async register(payload) {
      this.loading = true;
      try {
        await authApi.register(payload);
        await this.login({
          username: payload.username,
          password: payload.password,
        });
      } finally {
        this.loading = false;
      }
    },
    async fetchMe() {
      if (!this.token) return null;
      try {
        const me = await authApi.me();
        this.user = me;
        this.persist();
        return me;
      } catch {
        this.clear();
        return null;
      }
    },
    async logout() {
      try {
        await authApi.logout();
      } catch {
      } finally {
        this.clear();
      }
    },
  },
});

