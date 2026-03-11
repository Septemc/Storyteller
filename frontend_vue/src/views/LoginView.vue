<template>

  <div class="auth-container">
    <div class="auth-card">
      <div class="auth-logo">
        <h1>Storyteller</h1>
        <p>说书人 · 互动叙事平台</p>
      </div>
      
      <div class="auth-tabs">
        <button class="auth-tab active" data-tab="login">登录</button>
        <button class="auth-tab" data-tab="register">注册</button>
      </div>
      
      <form class="auth-form active" id="login-form">
        <div class="form-group">
          <label for="login-username">用户名</label>
          <input type="text" id="login-username" name="username" placeholder="请输入用户名" required autocomplete="username">
        </div>
        
        <div class="form-group">
          <label for="login-password">密码</label>
          <div class="password-toggle">
            <input type="password" id="login-password" name="password" placeholder="请输入密码" required autocomplete="current-password">
            <button type="button" class="password-toggle-btn" data-target="login-password">
              <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                <circle cx="12" cy="12" r="3"/>
              </svg>
            </button>
          </div>
        </div>
        
        <div class="form-error" id="login-error"></div>
        
        <button type="submit" class="auth-btn" id="login-btn">登录</button>
        
        <div class="guest-login">
          <button type="button" class="guest-btn" id="guest-btn">以游客身份继续</button>
        </div>
      </form>
      
      <form class="auth-form" id="register-form">
        <div class="form-group">
          <label for="register-username">用户名</label>
          <input type="text" id="register-username" name="username" placeholder="请输入用户名（至少3位）" required minlength="3" autocomplete="username">
        </div>
        
        <div class="form-group">
          <label for="register-email">邮箱（选填）</label>
          <input type="email" id="register-email" name="email" placeholder="请输入邮箱地址" autocomplete="email">
        </div>
        
        <div class="form-group">
          <label for="register-password">密码</label>
          <div class="password-toggle">
            <input type="password" id="register-password" name="password" placeholder="请输入密码（至少6位）" required minlength="6" autocomplete="new-password">
            <button type="button" class="password-toggle-btn" data-target="register-password">
              <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                <circle cx="12" cy="12" r="3"/>
              </svg>
            </button>
          </div>
        </div>
        
        <div class="form-group">
          <label for="register-confirm">确认密码</label>
          <div class="password-toggle">
            <input type="password" id="register-confirm" name="confirm" placeholder="请再次输入密码" required autocomplete="new-password">
            <button type="button" class="password-toggle-btn" data-target="register-confirm">
              <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                <circle cx="12" cy="12" r="3"/>
              </svg>
            </button>
          </div>
        </div>
        
        <div class="form-error" id="register-error"></div>
        
        <button type="submit" class="auth-btn" id="register-btn">注册</button>
      </form>
    </div>
  </div>
  
  

</template>

<script setup>
import { onMounted } from 'vue';
import { initThemePage } from '../page_logic/theme-init.module';
import { initLoginPageModule } from '../page_logic/login-inline.module';

onMounted(() => {
  document.title = '?? | Storyteller';
  document.body.setAttribute('data-page', 'login');
  initThemePage();
  initLoginPageModule();
});
</script>
<style scoped>
.auth-container {
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      background: var(--bg-primary);
      padding: 20px;
    }
    
    .auth-card {
      width: 100%;
      max-width: 420px;
      background: var(--bg-elevated-alt);
      border-radius: 12px;
      padding: 40px;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
      border: 1px solid var(--border-soft);
    }
    
    .auth-logo {
      text-align: center;
      margin-bottom: 30px;
    }
    
    .auth-logo h1 {
      font-size: 28px;
      color: var(--text-primary);
      margin: 0 0 8px 0;
    }
    
    .auth-logo p {
      color: var(--text-secondary);
      margin: 0;
      font-size: 14px;
    }
    
    .auth-tabs {
      display: flex;
      margin-bottom: 30px;
      border-bottom: 1px solid var(--border-color);
    }
    
    .auth-tab {
      flex: 1;
      padding: 12px;
      text-align: center;
      cursor: pointer;
      color: var(--text-primary);
      border-bottom: 2px solid transparent;
      transition: all 0.2s;
      background: none;
      border-top: none;
      border-left: none;
      border-right: none;
      font-size: 15px;
      font-weight: 500;
    }
    
    .auth-tab:hover {
      color: var(--text-primary);
    }
    
    .auth-tab.active {
      color: var(--accent-color);
      border-bottom-color: var(--accent-color);
    }
    
    .auth-form {
      display: none;
    }
    
    .auth-form.active {
      display: block;
    }
    
    .form-group {
      margin-bottom: 20px;
    }
    
    .form-group label {
      display: block;
      margin-bottom: 8px;
      color: var(--text-secondary);
      font-size: 14px;
    }
    
    .form-group input {
      width: 100%;
      padding: 12px 16px;
      background: var(--bg-elevated);
      border: 1px solid var(--border-soft);
      border-radius: 8px;
      color: var(--text-primary);
      font-size: 15px;
      transition: border-color 0.2s;
      box-sizing: border-box;
    }
    
    .form-group input:focus {
      outline: none;
      border-color: var(--accent-color);
    }
    
    .form-group input::placeholder {
      color: var(--text-muted);
    }
    
    .form-error {
      color: #ef4444;
      font-size: 13px;
      margin-top: 8px;
      display: none;
    }
    
    .form-error.show {
      display: block;
    }
    
    .auth-btn {
      width: 100%;
      padding: 14px;
      background: var(--accent-color);
      color: var(--text-primary);
      border: none;
      border-radius: 8px;
      font-size: 16px;
      cursor: pointer;
      transition: opacity 0.2s;
      font-weight: 500;
    }
    
    .auth-btn:hover {
      opacity: 0.9;
    }
    
    .auth-btn:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
    
    .auth-footer {
      text-align: center;
      margin-top: 24px;
      color: var(--text-secondary);
      font-size: 13px;
    }
    
    .auth-footer a {
      color: var(--accent-color);
      text-decoration: none;
    }
    
    .auth-footer a:hover {
      text-decoration: underline;
    }
    
    .password-toggle {
      position: relative;
    }
    
    .password-toggle input {
      padding-right: 44px;
    }
    
    .password-toggle-btn {
      position: absolute;
      right: 12px;
      top: 50%;
      transform: translateY(-50%);
      background: none;
      border: none;
      color: var(--text-secondary);
      cursor: pointer;
      padding: 4px;
    }
    
    .password-toggle-btn:hover {
      color: var(--text-primary);
    }
    
    .guest-login {
      margin-top: 20px;
      padding-top: 20px;
      border-top: 1px solid var(--border-color);
      text-align: center;
    }
    
    .guest-btn {
      background: transparent;
      border: 1px solid var(--border-color);
      color: var(--text-secondary);
      padding: 12px 24px;
      border-radius: 8px;
      cursor: pointer;
      transition: all 0.2s;
    }
    
    .guest-btn:hover {
      border-color: var(--accent-color);
      color: var(--accent-color);
    }
</style>
