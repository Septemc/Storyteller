/**
 * 开发者工具模块
 * 用于记录和显示发送给AI的请求内容
 */

(function() {
  'use strict';

  let developerModeEnabled = false;
  let devPanelVisible = false;
  let currentRequestLog = null;
  let requestHistory = [];

  const DEV_MODE_KEY = 'developer_mode_enabled';

  function init() {
    developerModeEnabled = localStorage.getItem(DEV_MODE_KEY) === 'true';
    
    if (developerModeEnabled && document.body.dataset.page === 'index') {
      createDevFloatingBall();
    }
    
    updateDevModeUI();
  }

  function setDeveloperMode(enabled) {
    developerModeEnabled = enabled;
    localStorage.setItem(DEV_MODE_KEY, enabled ? 'true' : 'false');
    
    if (enabled && document.body.dataset.page === 'index') {
      if (!document.getElementById('dev-floating-ball')) {
        createDevFloatingBall();
      }
    } else {
      removeDevFloatingBall();
    }
    
    updateDevModeUI();
  }

  function isDeveloperMode() {
    return developerModeEnabled;
  }

  function updateDevModeUI() {
    const checkbox = document.getElementById('developer-mode-enabled');
    if (checkbox) {
      checkbox.checked = developerModeEnabled;
    }
  }

  function createDevFloatingBall() {
    if (document.getElementById('dev-floating-ball')) return;

    const ball = document.createElement('div');
    ball.id = 'dev-floating-ball';
    ball.innerHTML = `
      <div class="dev-ball-icon" title="开发者工具">
        <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 2L2 7l10 5 10-5-10-5z"/>
          <path d="M2 17l10 5 10-5"/>
          <path d="M2 12l10 5 10-5"/>
        </svg>
      </div>
      <div class="dev-panel" id="dev-panel">
        <div class="dev-panel-header">
          <span class="dev-panel-title">开发者日志</span>
          <div class="dev-panel-actions">
            <button class="dev-btn dev-btn-clear" id="dev-clear-btn" title="清空日志">清空</button>
            <button class="dev-btn dev-btn-collapse" id="dev-collapse-btn" title="收起">收起</button>
          </div>
        </div>
        <div class="dev-panel-resize-handle" id="dev-resize-handle"></div>
        <div class="dev-panel-content" id="dev-panel-content">
          <div class="dev-empty-state">
            <div class="dev-empty-text">暂无请求记录</div>
            <div class="dev-empty-hint">点击"生成下一段"后将显示发送给AI的内容</div>
          </div>
        </div>
      </div>
    `;

    const style = document.createElement('style');
    style.textContent = `
      #dev-floating-ball {
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 9999;
        font-family: var(--font-family, 'Microsoft YaHei', sans-serif);
      }

      .dev-ball-icon {
        width: 48px;
        height: 48px;
        background: linear-gradient(135deg, var(--accent) 0%, rgba(78, 140, 255, 0.85) 100%);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        box-shadow: 0 4px 15px rgba(78, 140, 255, 0.3);
        transition: all 0.3s ease;
        color: #fff;
      }

      .dev-ball-icon:hover {
        transform: scale(1.1);
        box-shadow: 0 6px 20px rgba(78, 140, 255, 0.4);
      }

      .dev-panel {
        position: absolute;
        bottom: 60px;
        right: 0;
        width: 500px;
        min-width: 300px;
        max-width: 800px;
        height: 450px;
        min-height: 200px;
        max-height: 80vh;
        background: var(--bg-elevated);
        border: 1px solid var(--border-soft);
        border-radius: var(--radius-md);
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
        display: none;
        flex-direction: column;
        overflow: hidden;
        resize: both;
      }

      .dev-panel.visible {
        display: flex;
      }

      .dev-panel-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 16px;
        background: var(--bg-elevated-alt);
        border-bottom: 1px solid var(--border-soft);
        cursor: move;
      }

      .dev-panel-title {
        font-size: 13px;
        font-weight: 600;
        color: var(--text-primary);
      }

      .dev-panel-actions {
        display: flex;
        gap: 8px;
      }

      .dev-btn {
        background: var(--bg-elevated-alt);
        border: 1px solid var(--border-soft);
        cursor: pointer;
        font-size: 11px;
        padding: 4px 10px;
        border-radius: var(--radius-sm);
        transition: all 0.2s;
        color: var(--text-primary);
      }

      .dev-btn:hover {
        background: var(--accent);
        border-color: var(--accent);
        color: #fff;
      }

      .dev-panel-resize-handle {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        cursor: ns-resize;
        background: transparent;
      }

      .dev-panel-content {
        flex: 1;
        overflow-y: auto;
        padding: 12px;
        font-size: 13px;
        color: var(--text-primary);
        background: var(--bg-elevated);
      }

      .dev-empty-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 100%;
        color: var(--text-secondary);
      }

      .dev-empty-text {
        font-size: 14px;
        margin-bottom: 8px;
      }

      .dev-empty-hint {
        font-size: 12px;
        opacity: 0.7;
      }

      .dev-log-entry {
        background: var(--bg-elevated-alt);
        border-radius: var(--radius-sm);
        margin-bottom: 12px;
        overflow: hidden;
        border: 1px solid var(--border-soft);
      }

      .dev-log-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 12px;
        background: var(--accent-soft);
        cursor: pointer;
        transition: background 0.2s;
      }

      .dev-log-header:hover {
        background: var(--accent);
        color: #fff;
      }

      .dev-log-header:hover .dev-log-time {
        color: rgba(255, 255, 255, 0.8);
      }

      .dev-log-time {
        font-size: 11px;
        color: var(--text-secondary);
      }

      .dev-log-body {
        padding: 12px;
        display: none;
      }

      .dev-log-body.expanded {
        display: block;
      }

      .dev-log-section {
        margin-bottom: 16px;
      }

      .dev-log-section:last-child {
        margin-bottom: 0;
      }

      .dev-log-section-title {
        font-size: 12px;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 8px;
        padding-bottom: 6px;
        border-bottom: 1px solid var(--border-soft);
      }

      .dev-log-section-content {
        background: var(--bg-elevated);
        border-radius: var(--radius-sm);
        padding: 10px;
        font-size: 12px;
        white-space: pre-wrap;
        word-break: break-all;
        max-height: 300px;
        overflow-y: auto;
        color: var(--text-primary);
        line-height: 1.6;
        border: 1px solid var(--border-soft);
      }

      .dev-section-toggle {
        cursor: pointer;
        user-select: none;
      }

      .dev-section-toggle:hover {
        color: var(--accent);
      }
    `;

    document.head.appendChild(style);
    document.body.appendChild(ball);

    const ballIcon = ball.querySelector('.dev-ball-icon');
    const panel = ball.querySelector('#dev-panel');
    const collapseBtn = ball.querySelector('#dev-collapse-btn');
    const clearBtn = ball.querySelector('#dev-clear-btn');

    ballIcon.addEventListener('click', () => {
      devPanelVisible = !devPanelVisible;
      panel.classList.toggle('visible', devPanelVisible);
      collapseBtn.textContent = devPanelVisible ? '收起' : '展开';
    });

    collapseBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      devPanelVisible = false;
      panel.classList.remove('visible');
      collapseBtn.textContent = '展开';
    });

    clearBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      clearRequestHistory();
    });

    makeDraggable(ball, panel);
    makeResizable(panel);
  }

  function removeDevFloatingBall() {
    const ball = document.getElementById('dev-floating-ball');
    if (ball) {
      ball.remove();
    }
  }

  function makeDraggable(ball, panel) {
    const header = panel.querySelector('.dev-panel-header');
    let isDragging = false;
    let startX, startY, startRight, startBottom;

    header.addEventListener('mousedown', (e) => {
      if (e.target.closest('.dev-btn')) return;
      isDragging = true;
      startX = e.clientX;
      startY = e.clientY;
      startRight = parseInt(getComputedStyle(ball).right) || 20;
      startBottom = parseInt(getComputedStyle(ball).bottom) || 20;
      e.preventDefault();
    });

    document.addEventListener('mousemove', (e) => {
      if (!isDragging) return;
      const deltaX = startX - e.clientX;
      const deltaY = startY - e.clientY;
      ball.style.right = (startRight + deltaX) + 'px';
      ball.style.bottom = (startBottom + deltaY) + 'px';
    });

    document.addEventListener('mouseup', () => {
      isDragging = false;
    });
  }

  function makeResizable(panel) {
    const handle = panel.querySelector('#dev-resize-handle');
    let isResizing = false;
    let startY, startHeight;

    handle.addEventListener('mousedown', (e) => {
      isResizing = true;
      startY = e.clientY;
      startHeight = panel.offsetHeight;
      e.preventDefault();
      e.stopPropagation();
    });

    document.addEventListener('mousemove', (e) => {
      if (!isResizing) return;
      const deltaY = startY - e.clientY;
      const newHeight = Math.min(Math.max(startHeight + deltaY, 200), window.innerHeight * 0.8);
      panel.style.height = newHeight + 'px';
    });

    document.addEventListener('mouseup', () => {
      isResizing = false;
    });
  }

  function logRequest(requestData) {
    if (!developerModeEnabled) return;

    const logEntry = {
      timestamp: new Date().toISOString(),
      id: Date.now(),
      userInput: requestData.userInput || '',
      fullPrompt: requestData.fullPrompt || ''
    };

    requestHistory.unshift(logEntry);
    if (requestHistory.length > 20) {
      requestHistory.pop();
    }

    currentRequestLog = logEntry;
    updateDevPanelContent();
  }

  function updateDevPanelContent() {
    const content = document.getElementById('dev-panel-content');
    if (!content) return;

    if (requestHistory.length === 0) {
      content.innerHTML = `
        <div class="dev-empty-state">
          <div class="dev-empty-text">暂无请求记录</div>
          <div class="dev-empty-hint">点击"生成下一段"后将显示发送给AI的内容</div>
        </div>
      `;
      return;
    }

    let html = '';
    requestHistory.forEach((log, index) => {
      const time = new Date(log.timestamp).toLocaleTimeString();
      html += `
        <div class="dev-log-entry" data-log-id="${log.id}">
          <div class="dev-log-header" onclick="window.DevTools.toggleLogEntry(${log.id})">
            <span>请求 #${requestHistory.length - index} - ${time}</span>
            <span class="dev-log-time">${log.userInput ? log.userInput.substring(0, 30) + (log.userInput.length > 30 ? '...' : '') : '无输入'}</span>
          </div>
          <div class="dev-log-body" id="log-body-${log.id}">
            ${renderLogContent(log)}
          </div>
        </div>
      `;
    });

    content.innerHTML = html;

    if (currentRequestLog) {
      const body = document.getElementById(`log-body-${currentRequestLog.id}`);
      if (body) {
        body.classList.add('expanded');
      }
    }
  }

  function renderLogContent(log) {
    let html = '';

    if (log.userInput) {
      html += `
        <div class="dev-log-section">
          <div class="dev-log-section-title dev-section-toggle">用户输入</div>
          <div class="dev-log-section-content">${escapeHtml(log.userInput)}</div>
        </div>
      `;
    }

    if (log.fullPrompt) {
      html += `
        <div class="dev-log-section">
          <div class="dev-log-section-title dev-section-toggle">发送给AI的完整内容</div>
          <div class="dev-log-section-content">${escapeHtml(log.fullPrompt)}</div>
        </div>
      `;
    }

    return html || '<div class="dev-empty-state"><div class="dev-empty-text">无内容</div></div>';
  }

  function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  function toggleLogEntry(logId) {
    const body = document.getElementById(`log-body-${logId}`);
    if (body) {
      body.classList.toggle('expanded');
    }
  }

  function clearRequestHistory() {
    requestHistory = [];
    currentRequestLog = null;
    updateDevPanelContent();
  }

  window.DevTools = {
    init,
    setDeveloperMode,
    isDeveloperMode,
    logRequest,
    toggleLogEntry,
    clearRequestHistory
  };

  document.addEventListener('DOMContentLoaded', init);

})();
