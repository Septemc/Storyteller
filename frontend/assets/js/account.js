(function() {
  const AccountManager = {
    modal: null,
    currentTab: 'profile',
    
    init() {
      this.createModalHTML();
      this.modal = document.getElementById('account-modal');
      this.bindEvents();
      this.initAuthUI();
    },
    
    createModalHTML() {
      if (document.getElementById('account-modal')) return;
      
      const modalHTML = `
        <div id="account-modal" class="modal-overlay" style="display: none;">
          <div class="modal-window account-manager-window">
            <div class="modal-header">
              <h3 class="modal-title">账号管理</h3>
              <button id="account-modal-close" class="modal-close-btn" aria-label="关闭">&times;</button>
            </div>
            <div class="modal-body account-manager-body">
              <div class="account-sidebar">
                <div class="account-nav-item active" data-tab="profile">
                  <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                    <circle cx="12" cy="7" r="4"/>
                  </svg>
                  <span>个人中心</span>
                </div>
                <div class="account-nav-item" data-tab="guide">
                  <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
                    <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
                  </svg>
                  <span>使用指南</span>
                </div>
                <div class="account-nav-item" data-tab="settings">
                  <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="3"/>
                    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
                  </svg>
                  <span>账户设置</span>
                </div>
                <div class="account-nav-item" data-tab="logout">
                  <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
                    <polyline points="16 17 21 12 16 7"/>
                    <line x1="21" y1="12" x2="9" y2="12"/>
                  </svg>
                  <span>退出登录</span>
                </div>
              </div>
              <div class="account-content">
                <div class="account-tab-pane active" id="tab-profile">
                  <div class="account-section">
                    <div class="account-section-title">基本资料</div>
                    <div class="profile-card">
                      <div class="profile-avatar">
                        <div class="avatar-placeholder" id="profile-avatar">
                          <svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="currentColor" stroke-width="1.5">
                            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                            <circle cx="12" cy="7" r="4"/>
                          </svg>
                        </div>
                      </div>
                      <div class="profile-info">
                        <div class="profile-name" id="profile-name">加载中...</div>
                        <div class="profile-role" id="profile-role">-</div>
                      </div>
                    </div>
                    <div class="profile-details">
                      <div class="profile-detail-item">
                        <span class="detail-label">用户名</span>
                        <span class="detail-value" id="profile-username">-</span>
                      </div>
                      <div class="profile-detail-item">
                        <span class="detail-label">昵称</span>
                        <span class="detail-value" id="profile-nickname">-</span>
                      </div>
                      <div class="profile-detail-item">
                        <span class="detail-label">邮箱</span>
                        <span class="detail-value" id="profile-email">-</span>
                      </div>
                      <div class="profile-detail-item">
                        <span class="detail-label">注册时间</span>
                        <span class="detail-value" id="profile-created">-</span>
                      </div>
                    </div>
                  </div>
                  <div class="account-section">
                    <div class="account-section-title">账户状态</div>
                    <div class="status-grid">
                      <div class="status-item">
                        <div class="status-icon success">
                          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                            <polyline points="22 4 12 14.01 9 11.01"/>
                          </svg>
                        </div>
                        <div class="status-info">
                          <div class="status-label">账户状态</div>
                          <div class="status-value" id="profile-status">正常</div>
                        </div>
                      </div>
                      <div class="status-item">
                        <div class="status-icon info">
                          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="10"/>
                            <line x1="12" y1="16" x2="12" y2="12"/>
                            <line x1="12" y1="8" x2="12.01" y2="8"/>
                          </svg>
                        </div>
                        <div class="status-info">
                          <div class="status-label">角色权限</div>
                          <div class="status-value" id="profile-role-type">-</div>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div class="account-section">
                    <div class="account-section-title">数据统计</div>
                    <div class="stats-grid">
                      <div class="stat-card">
                        <div class="stat-value" id="stat-stories">0</div>
                        <div class="stat-label">故事片段</div>
                      </div>
                      <div class="stat-card">
                        <div class="stat-value" id="stat-characters">0</div>
                        <div class="stat-label">角色数量</div>
                      </div>
                      <div class="stat-card">
                        <div class="stat-value" id="stat-worldbook">0</div>
                        <div class="stat-label">世界书条目</div>
                      </div>
                      <div class="stat-card">
                        <div class="stat-value" id="stat-words">0</div>
                        <div class="stat-label">总字数</div>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div class="account-tab-pane" id="tab-guide">
                  <div class="account-section">
                    <div class="account-section-title">系统使用指南</div>
                    <div class="guide-content">
                      <div class="guide-item">
                        <div class="guide-header">
                          <span class="guide-icon">📖</span>
                          <span class="guide-title">快速入门</span>
                        </div>
                        <div class="guide-body">
                          <p>欢迎使用 Storyteller 说书人系统！这是一个强大的互动式故事创作平台。</p>
                          <ul>
                            <li><strong>剧情页面</strong>：在此输入您的行动，AI将根据您的选择推进故事发展。</li>
                            <li><strong>角色页面</strong>：创建和管理故事中的角色，定义他们的属性和背景。</li>
                            <li><strong>世界书</strong>：构建故事的世界观，添加地点、事件、设定等信息。</li>
                            <li><strong>剧本</strong>：创建预设的剧情剧本，引导故事走向特定方向。</li>
                          </ul>
                        </div>
                      </div>
                      <div class="guide-item">
                        <div class="guide-header">
                          <span class="guide-icon">⚙️</span>
                          <span class="guide-title">设置说明</span>
                        </div>
                        <div class="guide-body">
                          <ul>
                            <li><strong>API配置</strong>：配置大语言模型的API地址和密钥，支持OpenAI兼容接口。</li>
                            <li><strong>预设管理</strong>：创建和管理提示词预设，控制AI的写作风格和行为。</li>
                            <li><strong>主题设置</strong>：自定义界面主题、字体和排版样式。</li>
                          </ul>
                        </div>
                      </div>
                      <div class="guide-item">
                        <div class="guide-header">
                          <span class="guide-icon">❓</span>
                          <span class="guide-title">常见问题</span>
                        </div>
                        <div class="guide-body">
                          <p><strong>Q: 如何开始一个新的故事？</strong></p>
                          <p>A: 点击右上角的"存档管理"按钮，创建新存档即可开始新故事。</p>
                          <p><strong>Q: AI生成的内容不符合预期怎么办？</strong></p>
                          <p>A: 可以尝试修改预设提示词，或者在输入中更详细地描述您想要的情节走向。</p>
                          <p><strong>Q: 如何保存我的进度？</strong></p>
                          <p>A: 系统会自动保存您的所有操作，您也可以在存档管理中手动创建存档。</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div class="account-tab-pane" id="tab-settings">
                  <div class="account-section">
                    <div class="account-section-title">个人信息</div>
                    <div class="settings-form">
                      <div class="form-group">
                        <label class="form-label">昵称</label>
                        <input type="text" id="settings-nickname" class="form-input" placeholder="输入昵称">
                      </div>
                      <div class="form-group">
                        <label class="form-label">邮箱</label>
                        <input type="email" id="settings-email" class="form-input" placeholder="输入邮箱">
                      </div>
                      <button class="btn-primary" id="save-profile-btn">保存修改</button>
                    </div>
                  </div>
                  <div class="account-section">
                    <div class="account-section-title">安全设置</div>
                    <div class="settings-form">
                      <div class="form-group">
                        <label class="form-label">当前密码</label>
                        <input type="password" id="current-password" class="form-input" placeholder="输入当前密码">
                      </div>
                      <div class="form-group">
                        <label class="form-label">新密码</label>
                        <input type="password" id="new-password" class="form-input" placeholder="输入新密码">
                      </div>
                      <div class="form-group">
                        <label class="form-label">确认新密码</label>
                        <input type="password" id="confirm-password" class="form-input" placeholder="再次输入新密码">
                      </div>
                      <button class="btn-primary" id="change-password-btn">修改密码</button>
                    </div>
                  </div>
                  <div class="account-section">
                    <div class="account-section-title">通知偏好</div>
                    <div class="settings-form">
                      <div class="form-check-group">
                        <label class="form-check">
                          <input type="checkbox" id="notify-system" checked>
                          <span>系统通知</span>
                        </label>
                        <label class="form-check">
                          <input type="checkbox" id="notify-update">
                          <span>更新提醒</span>
                        </label>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div class="account-tab-pane" id="tab-logout">
                  <div class="logout-section">
                    <div class="logout-icon">
                      <svg viewBox="0 0 24 24" width="64" height="64" fill="none" stroke="currentColor" stroke-width="1.5">
                        <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
                        <polyline points="16 17 21 12 16 7"/>
                        <line x1="21" y1="12" x2="9" y2="12"/>
                      </svg>
                    </div>
                    <div class="logout-title">确认退出登录</div>
                    <div class="logout-desc">退出后需要重新登录才能使用完整功能。</div>
                    <button class="btn-danger btn-large" id="logout-confirm-btn">确认退出</button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      `;
      
      document.body.insertAdjacentHTML('beforeend', modalHTML);
    },
    
    bindEvents() {
      const userWrapper = document.getElementById('nav-user-wrapper');
      const dropdown = document.getElementById('nav-user-dropdown');
      const loginLink = document.getElementById('nav-login-link');
      
      if (userWrapper && dropdown) {
        const items = dropdown.querySelectorAll('.dropdown-item');
        items.forEach(item => {
          item.addEventListener('click', (e) => {
            e.stopPropagation();
            const action = item.dataset.action;
            this.handleDropdownAction(action);
          });
        });
      }
      
      if (loginLink) {
        loginLink.addEventListener('click', (e) => {
          e.preventDefault();
          window.location.href = 'login.html';
        });
      }
      
      const closeBtn = document.getElementById('account-modal-close');
      if (closeBtn) {
        closeBtn.addEventListener('click', () => this.closeModal());
      }
      
      if (this.modal) {
        this.modal.addEventListener('click', (e) => {
          if (e.target === this.modal) {
            this.closeModal();
          }
        });
      }
      
      const navItems = document.querySelectorAll('.account-nav-item');
      navItems.forEach(item => {
        item.addEventListener('click', () => {
          const tab = item.dataset.tab;
          this.switchTab(tab);
        });
      });
      
      const logoutConfirmBtn = document.getElementById('logout-confirm-btn');
      if (logoutConfirmBtn) {
        logoutConfirmBtn.addEventListener('click', () => this.handleLogout());
      }
      
      const saveProfileBtn = document.getElementById('save-profile-btn');
      if (saveProfileBtn) {
        saveProfileBtn.addEventListener('click', () => this.saveProfile());
      }
      
      const changePasswordBtn = document.getElementById('change-password-btn');
      if (changePasswordBtn) {
        changePasswordBtn.addEventListener('click', () => this.changePassword());
      }
    },
    
    initAuthUI() {
      const userWrapper = document.getElementById('nav-user-wrapper');
      const loginLink = document.getElementById('nav-login-link');
      
      if (typeof Auth !== 'undefined') {
        const user = Auth.getUser();
        if (user) {
          if (userWrapper) userWrapper.style.display = '';
          if (loginLink) loginLink.style.display = 'none';
        } else {
          if (userWrapper) userWrapper.style.display = 'none';
          if (loginLink) loginLink.style.display = '';
        }
      }
    },
    
    handleDropdownAction(action) {
      if (action === 'logout') {
        this.handleLogout();
      } else {
        this.openModal(action);
      }
    },
    
    openModal(tab = 'profile') {
      if (this.modal) {
        this.modal.style.display = 'flex';
        this.switchTab(tab);
        this.loadUserData();
        this.loadUserStats();
      }
    },
    
    closeModal() {
      if (this.modal) {
        this.modal.style.display = 'none';
      }
    },
    
    switchTab(tab) {
      this.currentTab = tab;
      
      const navItems = document.querySelectorAll('.account-nav-item');
      navItems.forEach(item => {
        if (item.dataset.tab === tab) {
          item.classList.add('active');
        } else {
          item.classList.remove('active');
        }
      });
      
      const panes = document.querySelectorAll('.account-tab-pane');
      panes.forEach(pane => {
        if (pane.id === `tab-${tab}`) {
          pane.classList.add('active');
        } else {
          pane.classList.remove('active');
        }
      });
    },
    
    async loadUserData() {
      if (typeof Auth === 'undefined') return;
      
      const user = Auth.getUser();
      if (!user) return;
      
      const profileName = document.getElementById('profile-name');
      const profileRole = document.getElementById('profile-role');
      const profileUsername = document.getElementById('profile-username');
      const profileNickname = document.getElementById('profile-nickname');
      const profileEmail = document.getElementById('profile-email');
      const profileCreated = document.getElementById('profile-created');
      const profileRoleType = document.getElementById('profile-role-type');
      
      if (profileName) profileName.textContent = user.nickname || user.username || '未知用户';
      if (profileRole) profileRole.textContent = this.getRoleName(user.role);
      if (profileUsername) profileUsername.textContent = user.username || '-';
      if (profileNickname) profileNickname.textContent = user.nickname || '-';
      if (profileEmail) profileEmail.textContent = user.email || '-';
      if (profileCreated) profileCreated.textContent = user.created_at ? this.formatDate(user.created_at) : '-';
      if (profileRoleType) profileRoleType.textContent = this.getRoleName(user.role);
      
      const settingsNickname = document.getElementById('settings-nickname');
      const settingsEmail = document.getElementById('settings-email');
      
      if (settingsNickname) settingsNickname.value = user.nickname || '';
      if (settingsEmail) settingsEmail.value = user.email || '';
    },
    
    async loadUserStats() {
      try {
        const token = typeof Auth !== 'undefined' ? Auth.getToken() : null;
        const headers = {
          'Content-Type': 'application/json'
        };
        if (token) {
          headers['Authorization'] = `Bearer ${token}`;
        }
        
        const response = await fetch('/api/story/stats', { headers });
        if (response.ok) {
          const data = await response.json();
          
          const statStories = document.getElementById('stat-stories');
          const statCharacters = document.getElementById('stat-characters');
          const statWorldbook = document.getElementById('stat-worldbook');
          const statWords = document.getElementById('stat-words');
          
          if (statStories) statStories.textContent = data.stories || 0;
          if (statCharacters) statCharacters.textContent = data.characters || 0;
          if (statWorldbook) statWorldbook.textContent = data.worldbook || 0;
          if (statWords) statWords.textContent = this.formatNumber(data.words || 0);
        }
      } catch (error) {
        console.error('加载统计数据失败:', error);
      }
    },
    
    async saveProfile() {
      const nickname = document.getElementById('settings-nickname')?.value;
      const email = document.getElementById('settings-email')?.value;
      
      try {
        const token = typeof Auth !== 'undefined' ? Auth.getToken() : null;
        const headers = {
          'Content-Type': 'application/json'
        };
        if (token) {
          headers['Authorization'] = `Bearer ${token}`;
        }
        
        const response = await fetch('/api/auth/profile', {
          method: 'PUT',
          headers,
          body: JSON.stringify({ nickname, email })
        });
        
        if (response.ok) {
          const data = await response.json();
          if (typeof Auth !== 'undefined') {
            Auth.setUser(data);
          }
          this.loadUserData();
          alert('保存成功！');
        } else {
          const error = await response.json();
          alert('保存失败: ' + (error.detail || '未知错误'));
        }
      } catch (error) {
        console.error('保存个人资料失败:', error);
        alert('保存失败，请稍后重试');
      }
    },
    
    async changePassword() {
      const currentPassword = document.getElementById('current-password')?.value;
      const newPassword = document.getElementById('new-password')?.value;
      const confirmPassword = document.getElementById('confirm-password')?.value;
      
      if (!currentPassword || !newPassword || !confirmPassword) {
        alert('请填写所有密码字段');
        return;
      }
      
      if (newPassword !== confirmPassword) {
        alert('两次输入的新密码不一致');
        return;
      }
      
      if (newPassword.length < 6) {
        alert('密码长度至少6位');
        return;
      }
      
      try {
        const token = typeof Auth !== 'undefined' ? Auth.getToken() : null;
        const headers = {
          'Content-Type': 'application/json'
        };
        if (token) {
          headers['Authorization'] = `Bearer ${token}`;
        }
        
        const response = await fetch('/api/auth/password', {
          method: 'PUT',
          headers,
          body: JSON.stringify({ 
            current_password: currentPassword, 
            new_password: newPassword 
          })
        });
        
        if (response.ok) {
          alert('密码修改成功！');
          document.getElementById('current-password').value = '';
          document.getElementById('new-password').value = '';
          document.getElementById('confirm-password').value = '';
        } else {
          const error = await response.json();
          alert('修改失败: ' + (error.detail || '未知错误'));
        }
      } catch (error) {
        console.error('修改密码失败:', error);
        alert('修改失败，请稍后重试');
      }
    },
    
    handleLogout() {
      if (confirm('确定要退出登录吗？')) {
        if (typeof Auth !== 'undefined') {
          Auth.logout();
        } else {
          localStorage.removeItem('auth_token');
          localStorage.removeItem('auth_user');
          window.location.href = 'login.html';
        }
      }
    },
    
    getRoleName(role) {
      const roleMap = {
        'admin': '管理员',
        'user': '普通用户',
        'guest': '游客'
      };
      return roleMap[role] || role || '普通用户';
    },
    
    formatDate(dateStr) {
      const date = new Date(dateStr);
      return date.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      });
    },
    
    formatNumber(num) {
      if (num >= 10000) {
        return (num / 10000).toFixed(1) + '万';
      }
      return num.toString();
    }
  };
  
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => AccountManager.init());
  } else {
    AccountManager.init();
  }
  
  window.AccountManager = AccountManager;
})();
