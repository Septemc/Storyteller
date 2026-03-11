(function() {
  const API_BASE = '/api';
  
  const Auth = {
    getToken() {
      return localStorage.getItem('auth_token');
    },
    
    setToken(token) {
      localStorage.setItem('auth_token', token);
    },
    
    getUser() {
      const user = localStorage.getItem('auth_user');
      return user ? JSON.parse(user) : null;
    },
    
    setUser(user) {
      localStorage.setItem('auth_user', JSON.stringify(user));
    },
    
    clearAuth() {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('auth_user');
    },
    
    isLoggedIn() {
      return !!this.getToken();
    },
    
    async apiRequest(endpoint, options = {}) {
      const token = this.getToken();
      const headers = {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        ...options.headers
      };
      
      const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers
      });
      
      if (response.status === 401) {
        this.clearAuth();
        window.location.href = 'login.html';
        throw new Error('登录已过期');
      }
      
      const data = await response.json().catch(() => ({}));
      
      if (!response.ok) {
        throw new Error(data.detail || '请求失败');
      }
      
      return data;
    },
    
    async checkAuth() {
      if (!this.getToken()) {
        return null;
      }
      
      try {
        const user = await this.apiRequest('/auth/me');
        this.setUser(user);
        return user;
      } catch (err) {
        this.clearAuth();
        return null;
      }
    },
    
    async logout() {
      try {
        await this.apiRequest('/auth/logout', { method: 'POST' });
      } catch (err) {
        // ignore
      }
      this.clearAuth();
      window.location.href = 'login.html';
    },
    
    updateUserUI(userEl, logoutBtn) {
      const user = this.getUser();
      if (user) {
        if (userEl) {
          userEl.textContent = user.nickname || user.username;
          userEl.title = `用户: ${user.username}\n角色: ${user.role}`;
        }
        if (logoutBtn) {
          logoutBtn.style.display = '';
        }
      } else {
        if (userEl) {
          userEl.textContent = '游客';
          userEl.title = '未登录';
        }
        if (logoutBtn) {
          logoutBtn.style.display = 'none';
        }
      }
    }
  };
  
  window.Auth = Auth;
})();
