(function() {
  let selectedSaveId = null;
  let currentSaveData = null;
  let isToggleBtnVisible = false;

  function init() {
    bindSaveInfoToggle();
    bindSaveManagerModal();
    loadCurrentSaveInfo();
  }

  function bindSaveInfoToggle() {
    const saveInfo = document.getElementById('current-save-info');
    const toggleBtn = document.getElementById('save-manager-toggle-btn');
    const saveManagerModal = document.getElementById('save-manager-modal');

    if (!saveInfo) return;

    saveInfo.addEventListener('click', function(e) {
      if (e.target.closest('.save-manager-toggle-btn')) {
        return;
      }
      
      if (isToggleBtnVisible) {
        hideToggleBtn();
      } else {
        showToggleBtn();
      }
    });

    if (toggleBtn) {
      toggleBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        if (saveManagerModal) {
          loadSaveList();
          saveManagerModal.style.display = 'flex';
        }
        hideToggleBtn();
      });
    }

    document.addEventListener('click', function(e) {
      if (isToggleBtnVisible) {
        if (!saveInfo.contains(e.target) && !toggleBtn.contains(e.target)) {
          hideToggleBtn();
        }
      }
    });

    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' && isToggleBtnVisible) {
        hideToggleBtn();
      }
    });
  }

  function showToggleBtn() {
    const toggleBtn = document.getElementById('save-manager-toggle-btn');
    const saveInfo = document.getElementById('current-save-info');
    
    if (toggleBtn) {
      toggleBtn.classList.add('visible');
      isToggleBtnVisible = true;
    }
    
    if (saveInfo) {
      saveInfo.classList.add('shimmer');
    }
  }

  function hideToggleBtn() {
    const toggleBtn = document.getElementById('save-manager-toggle-btn');
    const saveInfo = document.getElementById('current-save-info');
    
    if (toggleBtn) {
      toggleBtn.classList.remove('visible');
      isToggleBtnVisible = false;
    }
    
    if (saveInfo) {
      saveInfo.classList.remove('shimmer');
    }
  }

  function bindSaveManagerModal() {
    const saveManagerModal = document.getElementById('save-manager-modal');
    const saveManagerClose = document.getElementById('save-manager-close');
    const saveManagerCancel = document.getElementById('save-manager-cancel');
    const loadSaveBtn = document.getElementById('load-save-btn');
    const newSaveBtn = document.getElementById('new-save-btn');

    if (!saveManagerModal) return;

    if (saveManagerClose) {
      saveManagerClose.addEventListener('click', function() {
        saveManagerModal.style.display = 'none';
      });
    }

    if (saveManagerCancel) {
      saveManagerCancel.addEventListener('click', function() {
        saveManagerModal.style.display = 'none';
      });
    }

    saveManagerModal.addEventListener('click', function(e) {
      if (e.target === saveManagerModal) {
        saveManagerModal.style.display = 'none';
      }
    });

    if (loadSaveBtn) {
      loadSaveBtn.addEventListener('click', function() {
        if (selectedSaveId) {
          loadSave(selectedSaveId);
          saveManagerModal.style.display = 'none';
        }
      });
    }

    if (newSaveBtn) {
      newSaveBtn.addEventListener('click', function() {
        createNewSave();
      });
    }

    bindRenameModal();
  }

  function bindRenameModal() {
    const renameModal = document.getElementById('rename-save-modal');
    const renameModalClose = document.getElementById('rename-modal-close');
    const renameCancel = document.getElementById('rename-cancel');
    const renameConfirm = document.getElementById('rename-confirm');
    const renameInput = document.getElementById('rename-input');

    if (!renameModal) return;

    if (renameModalClose) {
      renameModalClose.addEventListener('click', function() {
        renameModal.style.display = 'none';
      });
    }

    if (renameCancel) {
      renameCancel.addEventListener('click', function() {
        renameModal.style.display = 'none';
      });
    }

    if (renameConfirm) {
      renameConfirm.addEventListener('click', function() {
        const newName = renameInput.value.trim();
        if (newName && selectedSaveId) {
          renameSave(selectedSaveId, newName);
          renameModal.style.display = 'none';
        }
      });
    }

    renameModal.addEventListener('click', function(e) {
      if (e.target === renameModal) {
        renameModal.style.display = 'none';
      }
    });
  }

  async function loadCurrentSaveInfo() {
    let sessionId = localStorage.getItem('storyteller_session_id');
    if (!sessionId) {
      updateCurrentSaveDisplay(null, null);
      return;
    }

    try {
      const response = await fetch('/api/story/saves/detail?session_id=' + encodeURIComponent(sessionId));
      const data = await response.json();
      if (data.display_name && data.display_name !== sessionId) {
        updateCurrentSaveDisplay(data.display_name, sessionId);
      } else {
        updateCurrentSaveDisplay(null, sessionId);
      }
    } catch (err) {
      updateCurrentSaveDisplay(null, sessionId);
    }
  }

  async function loadSaveList() {
    const saveList = document.getElementById('save-list');
    if (!saveList) return;

    try {
      const response = await fetch('/api/story/saves/list');
      const saves = await response.json();

      if (saves.length === 0) {
        saveList.innerHTML = `
          <div class="save-list-empty">
            <div class="empty-icon">📂</div>
            <div class="empty-text">暂无存档</div>
          </div>
        `;
        return;
      }

      saveList.innerHTML = saves.map(save => `
        <div class="save-item" data-session-id="${save.session_id}">
          <div class="save-item-header">
            <div class="save-item-name">${escapeHtml(save.display_name)}</div>
            <div class="save-item-segments">${save.segment_count} 段</div>
          </div>
          <div class="save-item-id">${save.session_id}</div>
          <div class="save-item-meta">
            <span>📝 ${save.total_word_count} 字</span>
            <span>🕐 ${formatDate(save.updated_at)}</span>
          </div>
        </div>
      `).join('');

      saveList.querySelectorAll('.save-item').forEach(item => {
        item.addEventListener('click', function() {
          selectSave(this.dataset.sessionId);
        });
      });

    } catch (err) {
      console.error('加载存档列表失败:', err);
      saveList.innerHTML = `
        <div class="save-list-empty">
          <div class="empty-icon">⚠️</div>
          <div class="empty-text">加载失败</div>
        </div>
      `;
    }
  }

  async function selectSave(sessionId) {
    selectedSaveId = sessionId;

    document.querySelectorAll('.save-item').forEach(item => {
      item.classList.toggle('selected', item.dataset.sessionId === sessionId);
    });

    const loadSaveBtn = document.getElementById('load-save-btn');
    if (loadSaveBtn) {
      loadSaveBtn.disabled = false;
    }

    await loadSaveDetail(sessionId);
  }

  async function loadSaveDetail(sessionId) {
    const detailContent = document.getElementById('save-detail-content');
    if (!detailContent) {
      console.error('找不到存档详情容器元素');
      return;
    }

    detailContent.innerHTML = `
      <div class="save-detail-empty">
        <div class="empty-icon">⏳</div>
        <div class="empty-text">加载中...</div>
      </div>
    `;

    try {
      const response = await fetch(`/api/story/saves/detail?session_id=${encodeURIComponent(sessionId)}`);
      
      if (!response.ok) {
        throw new Error(`HTTP错误: ${response.status}`);
      }
      
      const detail = await response.json();
      
      if (!detail) {
        throw new Error('返回数据为空');
      }

      currentSaveData = detail;

      const segmentsHtml = detail.segments && detail.segments.length > 0 
        ? detail.segments.map(seg => `
            <div class="segment-item" title="${escapeHtml(seg.preview || '') || '(无预览)'}">
              <span class="segment-index">#${seg.index || 0}</span>
              <span class="segment-preview">${escapeHtml(seg.preview) || '(无预览)'}</span>
              <span class="segment-words">${seg.word_count || 0}字</span>
            </div>
          `).join('')
        : '<div class="empty-text" style="padding: 12px; text-align: center; color: var(--text-secondary);">暂无分段</div>';

      detailContent.innerHTML = `
        <div class="save-detail-info">
          <div class="save-detail-section">
            <div class="save-detail-section-title">基本信息</div>
            <div class="save-detail-row">
              <span class="save-detail-label">存档名称</span>
              <span class="save-detail-value">${escapeHtml(detail.display_name || '未命名')}</span>
            </div>
            <div class="save-detail-row">
              <span class="save-detail-label">存档 ID</span>
              <span class="save-detail-value">${detail.session_id || '--'}</span>
            </div>
            <div class="save-detail-row">
              <span class="save-detail-label">分段数量</span>
              <span class="save-detail-value">${detail.segment_count || 0} 段</span>
            </div>
            <div class="save-detail-row">
              <span class="save-detail-label">总字数</span>
              <span class="save-detail-value">${detail.total_word_count || 0} 字</span>
            </div>
            <div class="save-detail-row">
              <span class="save-detail-label">最后更新</span>
              <span class="save-detail-value">${formatDate(detail.updated_at)}</span>
            </div>
          </div>
          
          <div class="save-detail-section">
            <div class="save-detail-section-title">分段列表</div>
            <div class="segment-list">
              ${segmentsHtml}
            </div>
          </div>
        </div>
      `;

      const detailHeader = document.querySelector('.save-detail-header');
      if (detailHeader) {
        let actionsContainer = detailHeader.querySelector('.save-detail-header-actions');
        if (!actionsContainer) {
          actionsContainer = document.createElement('div');
          actionsContainer.className = 'save-detail-header-actions';
          detailHeader.appendChild(actionsContainer);
        }
        actionsContainer.innerHTML = `
          <button class="btn-secondary" id="rename-save-btn">重命名</button>
          <button class="btn-secondary" id="delete-save-btn" style="color: var(--accent); border-color: var(--accent);">删除</button>
        `;
      }

      const renameBtn = document.getElementById('rename-save-btn');
      if (renameBtn) {
        renameBtn.addEventListener('click', function() {
          openRenameModal(detail.display_name);
        });
      }

      const deleteBtn = document.getElementById('delete-save-btn');
      if (deleteBtn) {
        deleteBtn.addEventListener('click', function() {
          if (confirm('确定要删除此存档吗？此操作不可恢复。')) {
            deleteSave(sessionId);
          }
        });
      }

    } catch (err) {
      console.error('加载存档详情失败:', err);
      detailContent.innerHTML = `
        <div class="save-detail-empty">
          <div class="empty-icon">⚠️</div>
          <div class="empty-text">加载失败</div>
          <div class="empty-subtext" style="font-size: 11px; color: var(--text-secondary); margin-top: 8px;">${escapeHtml(err.message || '未知错误')}</div>
        </div>
      `;
    }
  }

  function openRenameModal(currentName) {
    const renameModal = document.getElementById('rename-save-modal');
    const renameInput = document.getElementById('rename-input');
    
    if (renameModal && renameInput) {
      renameInput.value = currentName;
      renameModal.style.display = 'flex';
      renameInput.focus();
    }
  }

  async function renameSave(sessionId, newName) {
    try {
      const response = await fetch('/api/story/saves/rename', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, display_name: newName })
      });

      const result = await response.json();
      if (result.success) {
        loadSaveList();
        loadSaveDetail(sessionId);
        let currentSessionId = localStorage.getItem('storyteller_session_id');
        if (currentSessionId === sessionId) {
          updateCurrentSaveDisplay(newName, sessionId);
        }
      }
    } catch (err) {
      console.error('重命名失败:', err);
    }
  }

  async function createNewSave() {
    try {
      const response = await fetch('/api/story/saves/create', { method: 'POST' });
      const result = await response.json();
      
      if (result.success) {
        loadSaveList();
        selectSave(result.session_id);
      }
    } catch (err) {
      console.error('创建存档失败:', err);
    }
  }

  async function deleteSave(sessionId) {
    try {
      const response = await fetch(`/api/story/saves/delete?session_id=${encodeURIComponent(sessionId)}`, {
        method: 'POST'
      });

      const result = await response.json();
      if (result.success) {
        selectedSaveId = null;
        loadSaveList();
        
        const detailContent = document.getElementById('save-detail-content');
        if (detailContent) {
          detailContent.innerHTML = `
            <div class="save-detail-empty">
              <div class="empty-icon">📄</div>
              <div class="empty-text">选择一个存档查看详情</div>
            </div>
          `;
        }

        const actionsContainer = document.querySelector('.save-detail-header-actions');
        if (actionsContainer) {
          actionsContainer.innerHTML = '';
        }

        const loadSaveBtn = document.getElementById('load-save-btn');
        if (loadSaveBtn) {
          loadSaveBtn.disabled = true;
        }
      }
    } catch (err) {
      console.error('删除存档失败:', err);
    }
  }

  function loadSave(sessionId) {
    localStorage.setItem('storyteller_session_id', sessionId);
    updateCurrentSaveDisplay(null, sessionId);
    
    if (typeof window.onSaveLoaded === 'function') {
      window.onSaveLoaded(sessionId);
    } else {
      window.location.reload();
    }
  }

  window.saveManagerLoadSave = function(sessionId) {
    loadSave(sessionId);
  };

  window.updateCurrentSaveDisplay = updateCurrentSaveDisplay;

  function updateCurrentSaveDisplay(displayName, sessionId) {
    const saveNameEl = document.getElementById('current-save-name');
    const saveIdEl = document.getElementById('current-save-id');
    
    if (saveNameEl) {
      saveNameEl.textContent = displayName || sessionId || '未加载存档';
    }
    if (saveIdEl) {
      saveIdEl.textContent = sessionId || '--';
    }
  }

  function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  function formatDate(dateStr) {
    if (!dateStr) return '--';
    try {
      const date = new Date(dateStr);
      return date.toLocaleString('zh-CN', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateStr;
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
