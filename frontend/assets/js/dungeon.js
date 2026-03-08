(function () {
  // ====== 常量 & 状态 ======
  const STORAGE_KEY = 'st_scripts_data';
  const APPLIED_KEY = 'st_applied_script_id';

  const state = {
    scripts: [],
    appliedScriptId: localStorage.getItem(APPLIED_KEY) || null,
    currentScriptId: null,
    currentSelection: null, // { type: 'script'|'dungeon'|'node', scriptId, dungeonId?, nodeId? }
    isEditMode: false,
    keyword: '',
    importMode: null        // 'script' | 'dungeon' | 'node'
  };

  // ====== DOM 缓存 ======
  const els = {
    selector: document.getElementById('dungeon-selector'),
    appliedInfo: document.getElementById('applied-dungeon-info'),
    treeRoot: document.getElementById('tree-root'),
    detailPanel: document.getElementById('detail-panel'),
    detailTitle: document.getElementById('detail-title'),

    // 顶部操作 (Script Level)
    btnApply: document.getElementById('btn-apply-script'),
    btnNewScript: document.getElementById('btn-new-dungeon'), // 注意：HTML ID 是 btn-new-dungeon，实际功能是新建剧本
    btnImportScript: document.getElementById('btn-import-script'),
    btnExportScript: document.getElementById('btn-export-script'),
    btnDeleteScript: document.getElementById('btn-delete-dungeon'),

    // 工具栏操作 (Dungeon/Node Level)
    searchInput: document.getElementById('search-keyword'),
    btnSearch: document.getElementById('btn-search'),
    btnCreateDungeon: document.getElementById('btn-create-dungeon'),
    btnCreateNode: document.getElementById('btn-create-node'),
    btnImportDungeon: document.getElementById('btn-import-dungeon'),
    btnImportNode: document.getElementById('btn-import-node'),
    btnDeleteNode: document.getElementById('btn-delete-node'),

    fileInput: document.getElementById('file-input-hidden'),

    // 详情页操作
    modePreview: document.getElementById('mode-preview'),
    modeEdit: document.getElementById('mode-edit'),
    btnSave: document.getElementById('btn-save-detail'),
    btnExportCurrent: document.getElementById('btn-export-current')
  };

  // ====== 初始化 ======
  function init() {
    initAuthUI();
    loadData();
    bindEvents();
    refreshUI();
  }
  
  function initAuthUI() {
    const usernameEl = document.getElementById('nav-username');
    const logoutBtn = document.getElementById('nav-logout-btn');
    const loginLink = document.getElementById('nav-login-link');
    
    if (typeof Auth !== 'undefined') {
      Auth.updateUserUI(usernameEl, logoutBtn);
      
      if (logoutBtn) {
        logoutBtn.addEventListener('click', () => Auth.logout());
      }
      
      const user = Auth.getUser();
      if (user && loginLink) {
        loginLink.style.display = 'none';
      }
    }
  }

  // ====== 数据持久化 ======
  function loadData() {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      try {
        state.scripts = JSON.parse(raw);
      } catch (e) {
        console.warn('剧本数据解析失败:', e);
        state.scripts = [];
      }
    }

    // 确保有默认选中
    if (state.scripts.length > 0) {
      // 优先选中已应用的，否则选中第一个
      const appliedExists = state.appliedScriptId && getScriptById(state.appliedScriptId);
      state.currentScriptId = appliedExists ? state.appliedScriptId : state.scripts[0].script_id;
    } else {
      state.currentScriptId = null;
    }
  }

  let syncTimer = null;

  function saveData() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state.scripts));
    if (state.appliedScriptId) {
      localStorage.setItem(APPLIED_KEY, state.appliedScriptId);
    } else {
      localStorage.removeItem(APPLIED_KEY);
    }
    
    // 防抖同步到后端：编辑停止 2 秒后自动同步
    clearTimeout(syncTimer);
    syncTimer = setTimeout(() => {
      syncSessionStateToBackend();
    }, 2000);
  }

  async function syncSessionStateToBackend() {
    const sessionId = getCurrentSessionId();
    if (!sessionId || !state.appliedScriptId) return;

    const script = getScriptById(state.appliedScriptId);
    if (!script) return;

    try {
      // 1. 同步脚本元数据到 /api/scripts/{script_id}
      const scriptPayload = toDungeonPayload(script);
      const dungeonIds = script.dungeons.map(d => d.dungeon_id);
      
      await fetch(`/api/scripts/${script.script_id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          script_id: script.script_id,
          name: script.name || '',
          description: script.description || '',
          dungeon_ids: dungeonIds,
          meta: {}
        })
      });

      // 2. 同步所有副本到后端
      await syncScriptToBackend(script);

      // 3. 更新会话状态，包括 current_script_id
      const target = getAppliedDungeonAndNode(script);
      
      await fetch('/api/session/context', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          current_script_id: script.script_id,
          current_dungeon_id: target.dungeonId,
          current_node_id: target.nodeId
        })
      });
    } catch (error) {
      console.error('后端同步失败:', error);
    }
  }

  // ====== 工具函数 ======
  function getScriptById(id) {
    return state.scripts.find(s => String(s.script_id) === String(id));
  }

  function getCurrentSessionId() {
    return localStorage.getItem('storyteller_session_id');
  }

  function generateId(prefix = 'ID_') {
    return prefix + Math.random().toString(36).slice(2, 8).toUpperCase();
  }

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text == null ? '' : String(text);
    return div.innerHTML;
  }

  function toDungeonPayload(dungeon) {
    return {
      dungeon_id: dungeon.dungeon_id,
      name: dungeon.name || '未命名副本',
      description: dungeon.description || '',
      level_min: 1,
      level_max: 5,
      global_rules: dungeon.global_rules || {},
      nodes: (dungeon.nodes || []).map((node, idx) => ({
        node_id: node.node_id,
        name: node.name || `节点${idx + 1}`,
        index: Number.isFinite(node.index) ? node.index : (idx + 1),
        progress_percent: Number.isFinite(node.progress_percent) ? node.progress_percent : 0,
        entry_conditions: node.entry_conditions || [],
        exit_conditions: node.exit_conditions || [],
        summary_requirements: node.summary_requirements || '',
        story_requirements: node.story_requirements || {},
        branching: node.branching || {}
      }))
    };
  }

  async function syncScriptToBackend(script) {
    const dungeons = script.dungeons || [];
    for (const dungeon of dungeons) {
      const payload = toDungeonPayload(dungeon);
      const resp = await fetch(`/api/dungeon/${encodeURIComponent(dungeon.dungeon_id)}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (!resp.ok) {
        const txt = await resp.text();
        throw new Error(`同步剧本失败(${dungeon.name || dungeon.dungeon_id}): HTTP ${resp.status} ${txt}`);
      }
    }
  }

  function getAppliedDungeonAndNode(script) {
    const sel = state.currentSelection;
    const dungeons = script.dungeons || [];
    if (!dungeons.length) {
      return { dungeonId: null, nodeId: null };
    }

    let dungeon = null;
    if (sel && (sel.type === 'dungeon' || sel.type === 'node') && sel.dungeonId) {
      dungeon = dungeons.find(d => d.dungeon_id === sel.dungeonId) || null;
    }
    if (!dungeon) {
      dungeon = dungeons[0];
    }

    let nodeId = null;
    if (sel && sel.type === 'node' && sel.nodeId) {
      const hit = (dungeon.nodes || []).find(n => n.node_id === sel.nodeId);
      nodeId = hit ? hit.node_id : null;
    }
    if (!nodeId && dungeon.nodes && dungeon.nodes.length) {
      nodeId = dungeon.nodes[0].node_id;
    }

    return { dungeonId: dungeon.dungeon_id, nodeId };
  }

  async function applyScriptToCurrentSession(script) {
    const sessionId = getCurrentSessionId();
    if (!sessionId) {
      throw new Error('未检测到当前存档，请先在剧情页创建或加载存档');
    }

    await syncScriptToBackend(script);
    const target = getAppliedDungeonAndNode(script);

    const resp = await fetch('/api/session/context', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        current_dungeon_id: target.dungeonId,
        current_node_id: target.nodeId
      })
    });
    if (!resp.ok) {
      const txt = await resp.text();
      throw new Error(`写入会话上下文失败: HTTP ${resp.status} ${txt}`);
    }
  }

  // ====== UI 渲染 ======
  function refreshUI() {
    renderSelector();
    renderTree();
    updateAppliedText();
    renderDetail();
    updateModeButtons();
  }

  function renderSelector() {
    els.selector.innerHTML = '';
    if (state.scripts.length === 0) {
      const opt = document.createElement('option');
      opt.textContent = '暂无剧本';
      els.selector.add(opt);
      els.selector.disabled = true;
      return;
    }
    els.selector.disabled = false;
    state.scripts.forEach(s => {
      const opt = document.createElement('option');
      opt.value = s.script_id;
      opt.textContent = s.name || s.script_id;
      els.selector.add(opt);
    });
    els.selector.value = state.currentScriptId || '';
  }

  function updateAppliedText() {
    const cur = getScriptById(state.appliedScriptId);
    els.appliedInfo.textContent = cur ? `当前应用：${cur.name}` : '当前应用：未加载';
  }

  function renderTree() {
    els.treeRoot.innerHTML = '';
    const script = getScriptById(state.currentScriptId);
    if (!script) return;

    // 1. 剧本根节点 (Level 1)
    const rootContainer = document.createElement('div');
    rootContainer.className = 'tree-level-1-container expanded';

    const rootHeader = document.createElement('div');
    rootHeader.className = 'tree-header-1';
    rootHeader.innerHTML = `📚 ${escapeHtml(script.name)}`;
    if (state.currentSelection?.type === 'script') rootHeader.classList.add('selected');

    rootHeader.onclick = () => selectNode('script', { scriptId: script.script_id });
    rootContainer.appendChild(rootHeader);

    // 2. 副本/章节层级 (Level 2)
    const dungeons = script.dungeons || [];
    const kw = (state.keyword || '').toLowerCase();

    dungeons.forEach(dun => {
      // 搜索过滤逻辑：如果关键词存在，且匹配了节点名或剧情要求，则显示该节点
      // 如果副本名匹配，也显示
      let nodes = dun.nodes || [];
      const dunNameMatch = dun.name.toLowerCase().includes(kw);

      let filteredNodes = nodes;
      if (kw && !dunNameMatch) {
         filteredNodes = nodes.filter(n =>
           (n.name || '').toLowerCase().includes(kw) ||
           (n.summary_requirements || '').toLowerCase().includes(kw)
         );
         // 如果副本名不匹配，且过滤后没有子节点，则隐藏整个副本
         if (filteredNodes.length === 0) return;
      }

      const dunContainer = document.createElement('div');
      dunContainer.className = 'tree-level-2-container expanded';

      const dunHeader = document.createElement('div');
      dunHeader.className = 'tree-node tree-header-2';
      dunHeader.innerHTML = `📂 ${escapeHtml(dun.name)}`;
      if (state.currentSelection?.type === 'dungeon' && state.currentSelection.dungeonId === dun.dungeon_id) {
        dunHeader.classList.add('selected');
      }
      dunHeader.onclick = (e) => {
        e.stopPropagation();
        selectNode('dungeon', { scriptId: script.script_id, dungeonId: dun.dungeon_id });
      };

      const nodesContainer = document.createElement('div');
      nodesContainer.className = 'tree-children-2';

      // 3. 节点层级 (Level 3)
      filteredNodes.forEach(node => {
        const nodeItem = document.createElement('div');
        nodeItem.className = 'tree-node tree-item-3';
        nodeItem.innerHTML = `📄 <span style="opacity:0.6;font-size:0.9em;">[${node.index}]</span> ${escapeHtml(node.name)}`;
        if (state.currentSelection?.type === 'node' && state.currentSelection.nodeId === node.node_id) {
          nodeItem.classList.add('selected');
        }
        nodeItem.onclick = (e) => {
          e.stopPropagation();
          selectNode('node', { scriptId: script.script_id, dungeonId: dun.dungeon_id, nodeId: node.node_id });
        };
        nodesContainer.appendChild(nodeItem);
      });

      dunContainer.appendChild(dunHeader);
      dunContainer.appendChild(nodesContainer);
      rootContainer.appendChild(dunContainer);
    });

    els.treeRoot.appendChild(rootContainer);
  }

  function selectNode(type, params) {
    state.currentSelection = { type, ...params };
    state.isEditMode = false;
    refreshUI();
  }

  function renderDetail() {
    const sel = state.currentSelection;
    if (!sel) {
      els.detailPanel.innerHTML = '<div class="placeholder-text">请从左侧选择剧本、副本或节点。</div>';
      els.detailTitle.textContent = '内容预览';
      return;
    }

    const script = getScriptById(sel.scriptId);
    if (!script) return; // 容错

    let html = '';
    let title = '';

    if (sel.type === 'script') {
      title = `剧本：${script.name}`;
      if (state.isEditMode) {
        html = `
          <div class="settings-section">
            <label class="form-label">剧本名称</label>
            <input id="edit-s-name" class="form-input" value="${escapeHtml(script.name)}">
          </div>
          <div class="settings-section">
            <label class="form-label">世界观设定 (World View)</label>
            <textarea id="edit-s-view" class="form-textarea" style="height:120px;">${escapeHtml(script.description || '')}</textarea>
          </div>
          <div class="settings-section">
            <label class="form-label">主基调 (Tone)</label>
            <input id="edit-s-tone" class="form-input" value="${escapeHtml(script.tone || '')}">
          </div>
        `;
      } else {
        html = `
          <div class="render-box">
            <div style="margin-bottom:10px;"><strong>世界观：</strong></div>
            <div style="white-space:pre-wrap; margin-bottom:15px; color:var(--text-secondary);">${escapeHtml(script.description || '（暂无设定）')}</div>
            <div><strong>基调：</strong> ${escapeHtml(script.tone || '未设定')}</div>
            <div style="margin-top:10px; font-size:0.9em; color:var(--text-muted);">共包含 ${script.dungeons?.length || 0} 个章节/副本。</div>
          </div>`;
      }
    }
    else if (sel.type === 'dungeon') {
      const dun = script.dungeons.find(d => d.dungeon_id === sel.dungeonId);
      if (!dun) return;
      title = `副本：${dun.name}`;

      if (state.isEditMode) {
        html = `
          <div class="settings-section">
            <label class="form-label">副本名称</label>
            <input id="edit-d-name" class="form-input" value="${escapeHtml(dun.name)}">
          </div>
          <div class="settings-section">
            <label class="form-label">副本描述 / 简介</label>
            <textarea id="edit-d-desc" class="form-textarea" style="height:80px;">${escapeHtml(dun.description || '')}</textarea>
          </div>
          <div class="settings-section">
            <label class="form-label">全局规则 (JSON)</label>
            <textarea id="edit-d-rules" class="form-textarea" style="font-family:monospace; font-size:12px;">${JSON.stringify(dun.global_rules || {}, null, 2)}</textarea>
            <div class="small-text muted">例如：{"allow_death": false, "time_limit": "20 turns"}</div>
          </div>
        `;
      } else {
        html = `
          <div class="render-box">
            <p><strong>简介：</strong></p>
            <p>${escapeHtml(dun.description || '无描述')}</p>
            <hr style="border:0; border-top:1px solid var(--border-soft); margin:10px 0;">
            <p><strong>全局规则：</strong></p>
            <pre style="background:rgba(0,0,0,0.2); padding:8px; border-radius:4px;">${escapeHtml(JSON.stringify(dun.global_rules || {}, null, 2))}</pre>
          </div>`;
      }
    }
    else if (sel.type === 'node') {
      const dun = script.dungeons.find(d => d.dungeon_id === sel.dungeonId);
      const node = dun ? dun.nodes.find(n => n.node_id === sel.nodeId) : null;
      if (!node) return;

      const sr = node.story_requirements || {};
      title = `节点：${node.name}`;

      if (state.isEditMode) {
        html = `
          <div class="settings-section half-grid">
            <div><label class="form-label">节点名称</label><input id="edit-n-name" class="form-input" value="${escapeHtml(node.name)}"></div>
            <div><label class="form-label">剧情序号 (Index)</label><input type="number" id="edit-n-index" class="form-input" value="${node.index}"></div>
          </div>
          <div class="settings-section">
            <label class="form-label">剧情要求 / 概览 (Summary Requirements)</label>
            <textarea id="edit-n-summary" class="form-textarea" style="height:120px;">${escapeHtml(node.summary_requirements)}</textarea>
          </div>
          <div class="settings-section half-grid">
            <div><label class="form-label">悲剧强度 (Tragedy)</label><input id="edit-n-tragedy" class="form-input" value="${escapeHtml(sr.tragedy_level || '')}"></div>
            <div><label class="form-label">积极强度 (Positive)</label><input id="edit-n-positive" class="form-input" value="${escapeHtml(sr.positive_level || '')}"></div>
          </div>
          <div class="settings-section">
            <label class="form-label">补充笔记 (Extra Notes)</label>
            <textarea id="edit-n-notes" class="form-textarea" style="height:60px;">${escapeHtml(sr.extra_notes || '')}</textarea>
          </div>
          <div class="settings-section">
            <label class="form-label">分支选项 (JSON, 可选)</label>
            <textarea id="edit-n-branch" class="form-textarea" style="font-family:monospace; height:60px;">${JSON.stringify(node.branching || {}, null, 2)}</textarea>
          </div>
        `;
      } else {
        html = `
          <div class="render-box">
            <h4>📜 剧情大纲</h4>
            <div style="white-space:pre-wrap; margin-bottom:15px;">${escapeHtml(node.summary_requirements || '（暂无详细要求）')}</div>
            
            <div class="half-grid" style="background:rgba(255,255,255,0.05); padding:10px; border-radius:4px; margin-bottom:10px;">
              <div><strong>悲剧：</strong>${escapeHtml(sr.tragedy_level || '未设定')}</div>
              <div><strong>积极：</strong>${escapeHtml(sr.positive_level || '未设定')}</div>
            </div>
            
            <p><strong>笔记：</strong>${escapeHtml(sr.extra_notes || '无')}</p>
            ${Object.keys(node.branching || {}).length ? `<p><strong>分支逻辑：</strong>已配置</p>` : ''}
          </div>`;
      }
    }

    els.detailTitle.textContent = title;
    els.detailPanel.innerHTML = html;
  }

  function updateModeButtons() {
    const hasSel = !!state.currentSelection;
    els.modePreview.disabled = !hasSel;
    els.modeEdit.disabled = !hasSel;
    els.btnSave.disabled = !state.isEditMode;

    els.modePreview.classList.toggle('active', !state.isEditMode);
    els.modeEdit.classList.toggle('active', state.isEditMode);
  }

  // ====== 核心逻辑实现 ======
  function bindEvents() {
    // 1. 顶部剧本切换
    els.selector.onchange = () => {
      state.currentScriptId = els.selector.value;
      selectNode('script', { scriptId: state.currentScriptId });
    };

    // 2. 应用当前剧本
    els.btnApply.onclick = async () => {
      if (!state.currentScriptId) return alert('请先选择一个剧本。');
      const script = getScriptById(state.currentScriptId);
      if (!script) return alert('当前剧本不存在。');

      try {
        await applyScriptToCurrentSession(script);
        state.appliedScriptId = state.currentScriptId;
        saveData();
        updateAppliedText();
        alert(`已应用剧本「${script.name}」到当前存档。`);
      } catch (err) {
        console.error('[剧本应用失败]:', err);
        alert(`应用失败：${err.message}`);
      }
    };

    // 3. 新建剧本
    els.btnNewScript.onclick = () => {
      const name = prompt('请输入新剧本名称：', '新剧本');
      if (!name) return;
      const script = {
        script_id: generateId('SCR_'),
        name,
        description: '',
        tone: '',
        dungeons: []
      };
      state.scripts.push(script);
      state.currentScriptId = script.script_id;
      selectNode('script', { scriptId: script.script_id });
      saveData();
      refreshUI();
    };

    // 4. 删除剧本
    els.btnDeleteScript.onclick = () => {
      if (!state.currentScriptId) return;
      const script = getScriptById(state.currentScriptId);
      if (!confirm(`确定要彻底删除剧本「${script.name}」吗？此操作不可恢复。`)) return;

      state.scripts = state.scripts.filter(s => s.script_id !== state.currentScriptId);

      // 重置选中状态
      if (state.appliedScriptId === state.currentScriptId) state.appliedScriptId = null;
      state.currentScriptId = state.scripts.length > 0 ? state.scripts[0].script_id : null;
      state.currentSelection = null;

      saveData();
      refreshUI();
    };

    // ====== 导入功能群 ======

    // 触发导入剧本 (Top Bar)
    els.btnImportScript.onclick = () => {
      state.importMode = 'script';
      els.fileInput.value = ''; // 清空以允许重复选择
      els.fileInput.click();
    };

    // 触发导入副本 (Toolbar)
    els.btnImportDungeon.onclick = () => {
      if (!state.currentScriptId) return alert('请先新建或选择一个剧本，才能导入副本。');
      state.importMode = 'dungeon';
      els.fileInput.value = '';
      els.fileInput.click();
    };

    // 触发导入节点 (Toolbar)
    els.btnImportNode.onclick = () => {
      if (!state.currentSelection || state.currentSelection.type !== 'dungeon') {
        return alert('请先在左侧选择一个副本，以便将节点导入其中。');
      }
      state.importMode = 'node';
      els.fileInput.value = '';
      els.fileInput.click();
    };

    // 统一处理文件选择
    els.fileInput.onchange = (e) => {
      const file = e.target.files[0];
      if (!file) return;

      const reader = new FileReader();
      reader.onload = (evt) => {
        try {
          const raw = JSON.parse(evt.target.result);

          if (state.importMode === 'script') {
            const script = normalizeScriptImport(raw, file.name);
            state.scripts.push(script);
            state.currentScriptId = script.script_id;
            selectNode('script', { scriptId: script.script_id });
            alert(`剧本导入成功：${script.name}`);

          } else if (state.importMode === 'dungeon') {
            const script = getScriptById(state.currentScriptId);
            // 支持导入单个副本对象，或者包含 chapters 数组的结构
            const dungeonsToAdd = normalizeDungeonImport(raw);
            if (dungeonsToAdd.length === 0) throw new Error('未识别到有效的副本数据');

            script.dungeons.push(...dungeonsToAdd);
            alert(`成功导入 ${dungeonsToAdd.length} 个副本到当前剧本。`);

            // 自动展开新导入的第一个副本
            const lastId = dungeonsToAdd[dungeonsToAdd.length-1].dungeon_id;
            selectNode('dungeon', { scriptId: script.script_id, dungeonId: lastId });

          } else if (state.importMode === 'node') {
            const script = getScriptById(state.currentScriptId);
            const dun = script.dungeons.find(d => d.dungeon_id === state.currentSelection.dungeonId);

            const nodesToAdd = normalizeNodeImport(raw);
            if (nodesToAdd.length === 0) throw new Error('未识别到有效的节点数据');

            // 自动重新编号 index
            const baseIndex = dun.nodes.length;
            nodesToAdd.forEach((n, i) => { n.index = baseIndex + i + 1; });

            dun.nodes.push(...nodesToAdd);
            alert(`成功导入 ${nodesToAdd.length} 个节点。`);
          }

          saveData();
          refreshUI();

        } catch (err) {
          console.error(err);
          alert('导入失败：文件格式不正确或无法解析。\n错误信息：' + err.message);
        }
      };
      reader.readAsText(file);
    };

    // ====== 导出功能群 ======
    els.btnExportScript.onclick = () => {
      const script = getScriptById(state.currentScriptId);
      if (script) downloadJson(script, script.name);
    };

    els.btnExportCurrent.onclick = () => {
      const sel = state.currentSelection;
      if (!sel) return;

      const s = getScriptById(sel.scriptId);
      if (sel.type === 'script') {
        downloadJson(s, s.name);
      } else if (sel.type === 'dungeon') {
        const d = s.dungeons.find(d => d.dungeon_id === sel.dungeonId);
        downloadJson(d, d ? d.name : 'dungeon');
      } else if (sel.type === 'node') {
        const d = s.dungeons.find(d => d.dungeon_id === sel.dungeonId);
        const n = d.nodes.find(n => n.node_id === sel.nodeId);
        downloadJson(n, n ? n.name : 'node');
      }
    };

    // ====== 新建功能群 ======

    // 新建副本 (Toolbar)
    els.btnCreateDungeon.onclick = () => {
      if (!state.currentScriptId) return alert('请先创建或选择一个剧本。');
      const script = getScriptById(state.currentScriptId);

      openInputModal('新建副本', '副本名称', (val) => {
        const newDungeon = {
          dungeon_id: generateId('DUN_'),
          name: val,
          description: '',
          global_rules: {},
          nodes: []
        };
        script.dungeons.push(newDungeon);
        saveData();
        selectNode('dungeon', { scriptId: script.script_id, dungeonId: newDungeon.dungeon_id });
      });
    };

    // 新建节点 (Toolbar)
    els.btnCreateNode.onclick = () => {
      const sel = state.currentSelection;
      if (!sel || (sel.type !== 'dungeon' && sel.type !== 'node')) {
        return alert('请先选择一个副本，才能创建节点。');
      }

      const script = getScriptById(sel.scriptId);
      // 即使当前选中的是 node，也找到它所属的 dungeon
      const dungeonId = sel.dungeonId;
      const dungeon = script.dungeons.find(d => d.dungeon_id === dungeonId);

      openInputModal('新建节点', '节点名称', (val) => {
        const newNode = {
          node_id: generateId('NODE_'),
          index: dungeon.nodes.length + 1,
          name: val,
          summary_requirements: '',
          story_requirements: { tragedy_level: '无', positive_level: '无' },
          branching: {}
        };
        dungeon.nodes.push(newNode);
        saveData();
        selectNode('node', { scriptId: script.script_id, dungeonId: dungeon.dungeon_id, nodeId: newNode.node_id });
      });
    };

    // 删除 (Toolbar - 通用删除，针对 Dungeon 和 Node)
    els.btnDeleteNode.onclick = () => {
      const sel = state.currentSelection;
      if (!sel || sel.type === 'script') return alert('请选择要删除的副本或节点。删除剧本请使用顶部按钮。');

      const script = getScriptById(sel.scriptId);

      if (sel.type === 'dungeon') {
         const d = script.dungeons.find(d => d.dungeon_id === sel.dungeonId);
         if (!confirm(`确认删除副本「${d.name}」及其所有节点？`)) return;

         script.dungeons = script.dungeons.filter(d => d.dungeon_id !== sel.dungeonId);
         selectNode('script', { scriptId: script.script_id });

      } else if (sel.type === 'node') {
         const d = script.dungeons.find(d => d.dungeon_id === sel.dungeonId);
         const n = d.nodes.find(n => n.node_id === sel.nodeId);
         if (!confirm(`确认删除节点「${n.name}」？`)) return;

         d.nodes = d.nodes.filter(n => n.node_id !== sel.nodeId);
         // 删除后回到副本视图
         selectNode('dungeon', { scriptId: script.script_id, dungeonId: d.dungeon_id });
      }

      saveData();
    };

    // 保存修改 (Detail)
    els.btnSave.onclick = () => {
      if (!state.isEditMode || !state.currentSelection) return;
      const sel = state.currentSelection;
      const s = getScriptById(sel.scriptId);

      if (sel.type === 'script') {
        s.name = document.getElementById('edit-s-name').value;
        s.description = document.getElementById('edit-s-view').value;
        s.tone = document.getElementById('edit-s-tone').value;
      }
      else if (sel.type === 'dungeon') {
        const d = s.dungeons.find(dun => dun.dungeon_id === sel.dungeonId);
        d.name = document.getElementById('edit-d-name').value;
        d.description = document.getElementById('edit-d-desc').value;
        try {
          d.global_rules = JSON.parse(document.getElementById('edit-d-rules').value || '{}');
        } catch (e) { alert('全局规则 JSON 格式错误，未保存该字段。'); }
      }
      else if (sel.type === 'node') {
        const d = s.dungeons.find(dun => dun.dungeon_id === sel.dungeonId);
        const n = d.nodes.find(node => node.node_id === sel.nodeId);
        n.name = document.getElementById('edit-n-name').value;
        n.index = parseInt(document.getElementById('edit-n-index').value) || 0;
        n.summary_requirements = document.getElementById('edit-n-summary').value;
        n.story_requirements = {
          tragedy_level: document.getElementById('edit-n-tragedy').value,
          positive_level: document.getElementById('edit-n-positive').value,
          extra_notes: document.getElementById('edit-n-notes').value
        };
        try {
          n.branching = JSON.parse(document.getElementById('edit-n-branch').value || '{}');
        } catch (e) { alert('分支选项 JSON 格式错误，未保存该字段。'); }
      }

      state.isEditMode = false;
      saveData();
      refreshUI();
    };

    els.modePreview.onclick = () => { state.isEditMode = false; renderDetail(); updateModeButtons(); };
    els.modeEdit.onclick = () => { state.isEditMode = true; renderDetail(); updateModeButtons(); };

    // 搜索回车支持
    els.searchInput.onkeydown = (e) => { if (e.key === 'Enter') refreshUI(); };
    els.btnSearch.onclick = refreshUI;
  }

  // ====== 数据适配与规范化 ======

  // 1. 导入整个剧本
  function normalizeScriptImport(raw, fileName) {
    const baseScript = {
      script_id: generateId('SCR_'),
      name: raw.name || raw.script_meta?.script_title || fileName.replace('.json', ''),
      description: raw.description || raw.script_meta?.world_view || '',
      tone: raw.tone || raw.script_meta?.main_tone || '',
      dungeons: []
    };

    // 尝试寻找 dungeons 数组或 chapters 数组
    const rawChapters = raw.dungeons || raw.chapters || (Array.isArray(raw) ? raw : []);
    baseScript.dungeons = normalizeDungeonImport(rawChapters);

    return baseScript;
  }

  // 2. 导入副本 (返回 Dungeon 数组)
  function normalizeDungeonImport(raw) {
    let list = [];
    if (Array.isArray(raw)) list = raw;
    else if (typeof raw === 'object') {
      // 可能是 Script 对象，取其 dungeons；也可能是单个 Dungeon 对象
      if (raw.dungeons || raw.chapters) list = raw.dungeons || raw.chapters;
      else list = [raw]; // 单个对象视为一个副本
    }

    return list.map(ch => ({
      dungeon_id: ch.dungeon_id || ch.chapter_id || generateId('DUN_'),
      name: ch.name || ch.title || '未命名副本',
      description: ch.description || '',
      global_rules: ch.global_rules || {},
      nodes: normalizeNodeImport(ch.nodes || [])
    }));
  }

  // 3. 导入节点 (返回 Node 数组)
  function normalizeNodeImport(raw) {
    if (!Array.isArray(raw)) return [];

    return raw.map((n, idx) => ({
      node_id: n.node_id || generateId('NODE_'),
      index: n.index !== undefined ? n.index : idx + 1,
      name: n.name || '未命名节点',
      summary_requirements: n.summary_requirements || '',
      story_requirements: {
        tragedy_level: n.story_requirements?.tragedy_level || n.tragedy_level || '无',
        positive_level: n.story_requirements?.positive_level || n.positive_level || '无',
        extra_notes: n.story_requirements?.extra_notes || n.extra_notes || ''
      },
      branching: n.branching || {}
    }));
  }

  function downloadJson(obj, name) {
    const blob = new Blob([JSON.stringify(obj, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = (name || 'data').replace(/[\\\/:*?"<>|]/g, '_') + '.json';
    a.click();
    URL.revokeObjectURL(url);
  }

  // 简单的输入框 Modal，用于新建命名
  function openInputModal(title, placeholder, onConfirm) {
    const oldName = prompt(title + '\n请输入' + placeholder + '：');
    if (oldName && oldName.trim()) {
      onConfirm(oldName.trim());
    }
  }

  init();
})();