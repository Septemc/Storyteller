export function initLoginPageModule() {
  (function() {
        const API_BASE = '/api';
        
        function getToken() {
          return localStorage.getItem('auth_token');
        }
        
        function setToken(token) {
          localStorage.setItem('auth_token', token);
        }
        
        function getUser() {
          const user = localStorage.getItem('auth_user');
          return user ? JSON.parse(user) : null;
        }
        
        function setUser(user) {
          localStorage.setItem('auth_user', JSON.stringify(user));
        }
        
        function clearAuth() {
          localStorage.removeItem('auth_token');
          localStorage.removeItem('auth_user');
        }
        
        async function apiRequest(endpoint, options = {}) {
          const token = getToken();
          const headers = {
            'Content-Type': 'application/json',
            ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
            ...options.headers
          };
          
          const response = await fetch(`${API_BASE}${endpoint}`, {
            ...options,
            headers
          });
          
          const data = await response.json().catch(() => ({}));
          
          if (!response.ok) {
            throw new Error(data.detail || '请求失败');
          }
          
          return data;
        }
        
        const tabs = document.querySelectorAll('.auth-tab');
        const forms = document.querySelectorAll('.auth-form');
        
        tabs.forEach(tab => {
          tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            forms.forEach(f => f.classList.remove('active'));
            tab.classList.add('active');
            document.getElementById(`${tab.dataset.tab}-form`).classList.add('active');
          });
        });
        
        document.querySelectorAll('.password-toggle-btn').forEach(btn => {
          btn.addEventListener('click', () => {
            const input = document.getElementById(btn.dataset.target);
            const isPassword = input.type === 'password';
            input.type = isPassword ? 'text' : 'password';
            btn.innerHTML = isPassword
              ? '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>'
              : '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>';
          });
        });
        
        const loginForm = document.getElementById('login-form');
        const loginError = document.getElementById('login-error');
        const loginBtn = document.getElementById('login-btn');
        
        loginForm.addEventListener('submit', async (e) => {
          e.preventDefault();
          loginError.classList.remove('show');
          loginBtn.disabled = true;
          loginBtn.textContent = '登录中...';
          
          try {
            const formData = new FormData(loginForm);
            const data = await apiRequest('/auth/login', {
              method: 'POST',
              body: JSON.stringify({
                username: formData.get('username'),
                password: formData.get('password')
              })
            });
            
            setToken(data.access_token);
            setUser({
              user_id: data.user_id,
              username: data.username,
              role: data.role
            });
            
            window.location.href = '/story';
          } catch (err) {
            loginError.textContent = err.message;
            loginError.classList.add('show');
          } finally {
            loginBtn.disabled = false;
            loginBtn.textContent = '登录';
          }
        });
        
        const registerForm = document.getElementById('register-form');
        const registerError = document.getElementById('register-error');
        const registerBtn = document.getElementById('register-btn');
        
        registerForm.addEventListener('submit', async (e) => {
          e.preventDefault();
          registerError.classList.remove('show');
          
          const formData = new FormData(registerForm);
          const password = formData.get('password');
          const confirm = formData.get('confirm');
          
          if (password !== confirm) {
            registerError.textContent = '两次输入的密码不一致';
            registerError.classList.add('show');
            return;
          }
          
          registerBtn.disabled = true;
          registerBtn.textContent = '注册中...';
          
          try {
            const data = await apiRequest('/auth/register', {
              method: 'POST',
              body: JSON.stringify({
                username: formData.get('username'),
                email: formData.get('email') || null,
                password: password
              })
            });
            
            setToken(data.access_token || '');
            setUser(data.user);
            
            const loginData = await apiRequest('/auth/login', {
              method: 'POST',
              body: JSON.stringify({
                username: formData.get('username'),
                password: password
              })
            });
            
            setToken(loginData.access_token);
            setUser({
              user_id: loginData.user_id,
              username: loginData.username,
              role: loginData.role
            });
            
            window.location.href = '/story';
          } catch (err) {
            registerError.textContent = err.message;
            registerError.classList.add('show');
          } finally {
            registerBtn.disabled = false;
            registerBtn.textContent = '注册';
          }
        });
        
        document.getElementById('guest-btn').addEventListener('click', () => {
          clearAuth();
          window.location.href = '/story';
        });
        
        (async function checkAuth() {
          const token = getToken();
          if (token) {
            try {
              const user = await apiRequest('/auth/me');
              setUser(user);
              window.location.href = '/story';
            } catch (err) {
              clearAuth();
            }
          }
        })();
      })();
}
