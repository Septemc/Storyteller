(function () {
  let regexProfiles = [];
  let currentRegexId = null;
  let currentRegexConfig = null;
  let selectedNodeId = null;

  const regexSelect = document.getElementById('regex-select');
  const regexActiveHint = document.getElementById('regex-active-hint');
  const regexTree = document.getElementById('regex-tree');
  const regexNodeEditor = document.getElementById('regex-node-editor-container');
  const regexNodeEmptyHint = document.getElementById('regex-node-empty-hint');

  const regexCreateBtn = document.getElementById('regex-create-btn');
  const regexSetActiveBtn = document.getElementById('regex-set-active-btn');
  const regexSaveBtn = document.getElementById('regex-save-btn');
  const regexDeleteBtn = document.getElementById('regex-delete-btn');
  const regexImportBtn = document.getElementById('regex-import-btn');
  const regexExportBtn = document.getElementById('regex-export-btn');
  const regexImportFile = document.getElementById('regex-import-file');
  const regexImportName = document.getElementById('regex-import-name');

  const regexAddGroupBtn = document.getElementById('regex-add-group-btn');
  const regexAddRuleBtn = document.getElementById('regex-add-rule-btn');
  const regexDeleteNodeBtn = document.getElementById('regex-delete-node-btn');

  const regexNodeEnabled = document.getElementById('regex-node-enabled');
  const regexNodeTitle = document.getElementById('regex-node-title');
  const regexNodeIdentifier = document.getElementById('regex-node-identifier');
  const regexNodePattern = document.getElementById('regex-node-pattern');
  const regexNodeReplacement = document.getElementById('regex-node-replacement');
  const regexNodeExtractGroup = document.getElementById('regex-node-extract-group');
  const regexNodeApplyTo = document.getElementById('regex-node-apply-to');
  const regexNodeDescription = document.getElementById('regex-node-description');

  async function loadRegexProfiles() {
    try {
      const resp = await fetch('/regex/profiles');
      if (!resp.ok) throw new Error('Failed to load regex profiles');
      regexProfiles = await resp.json();
      renderRegexSelect();
      await loadActiveRegex();
    } catch (err) {
      console.error('Load regex profiles error:', err);
    }
  }

  async function loadActiveRegex() {
    try {
      const resp = await fetch('/regex/active');
      if (!resp.ok) throw new Error('Failed to load active regex');
      const data = await resp.json();
      currentRegexId = data.id;
      currentRegexConfig = data.config;
      regexActiveHint.textContent = data.name + (data.is_default ? ' (默认)' : '');
      if (regexSelect) {
        regexSelect.value = data.id;
      }
      renderRegexTree();
    } catch (err) {
      console.error('Load active regex error:', err);
    }
  }

  function renderRegexSelect() {
    if (!regexSelect) return;
    regexSelect.innerHTML = '';
    regexProfiles.forEach(function (p) {
      const opt = document.createElement('option');
      opt.value = p.id;
      opt.textContent = p.name + (p.is_default ? ' (默认)' : '');
      if (p.id === currentRegexId) opt.selected = true;
      regexSelect.appendChild(opt);
    });
  }

  function renderRegexTree() {
    if (!regexTree || !currentRegexConfig) return;
    const root = currentRegexConfig.root;
    if (!root) {
      regexTree.innerHTML = '<div class="empty-hint"><div class="empty-hint-icon">📭</div><div class="empty-hint-subtitle">无规则</div></div>';
      return;
    }
    regexTree.innerHTML = '';
    renderTreeNode(root, regexTree, 0);
  }

  function renderTreeNode(node, container, depth) {
    const el = document.createElement('div');
    el.className = 'config-tree-node' + (node.enabled === false ? ' disabled' : '');
    el.style.paddingLeft = (depth * 16 + 8) + 'px';
    el.dataset.nodeId = node.id;

    const icon = node.kind === 'group' ? '📁' : '🔧';
    const title = node.title || node.name || '未命名';

    el.innerHTML = '<span class="tree-icon">' + icon + '</span><span class="tree-title">' + title + '</span>';

    el.addEventListener('click', function (e) {
      e.stopPropagation();
      selectNode(node.id);
    });

    container.appendChild(el);

    if (node.children && Array.isArray(node.children)) {
      node.children.forEach(function (child) {
        renderTreeNode(child, container, depth + 1);
      });
    }
  }

  function selectNode(nodeId) {
    selectedNodeId = nodeId;
    const node = findNode(currentRegexConfig.root, nodeId);
    if (!node) return;

    if (regexNodeEditor) regexNodeEditor.style.display = 'flex';
    if (regexNodeEmptyHint) regexNodeEmptyHint.style.display = 'none';

    if (regexNodeEnabled) regexNodeEnabled.checked = node.enabled !== false;
    if (regexNodeTitle) regexNodeTitle.value = node.title || '';
    if (regexNodeIdentifier) regexNodeIdentifier.value = node.identifier || '';

    const isGroup = node.kind === 'group' || Array.isArray(node.children);
    const ruleFields = document.getElementById('regex-node-rule-fields');
    const groupHint = document.getElementById('regex-group-hint');

    if (isGroup) {
      if (ruleFields) ruleFields.style.display = 'none';
      if (groupHint) groupHint.style.display = 'flex';
    } else {
      if (ruleFields) ruleFields.style.display = 'flex';
      if (groupHint) groupHint.style.display = 'none';

      if (regexNodePattern) regexNodePattern.value = node.pattern || '';
      if (regexNodeReplacement) regexNodeReplacement.value = node.replacement || '';
      if (regexNodeExtractGroup) regexNodeExtractGroup.value = node.extract_group || 0;
      if (regexNodeApplyTo) regexNodeApplyTo.value = node.apply_to || 'body';
      if (regexNodeDescription) regexNodeDescription.value = node.description || '';
    }

    document.querySelectorAll('.config-tree-node').forEach(function (n) {
      n.classList.remove('selected');
    });
    document.querySelector('.config-tree-node[data-node-id="' + nodeId + '"]')?.classList.add('selected');
  }

  function findNode(root, nodeId) {
    if (!root) return null;
    if (root.id === nodeId) return root;
    if (root.children) {
      for (const child of root.children) {
        const found = findNode(child, nodeId);
        if (found) return found;
      }
    }
    return null;
  }

  function collectNodeChanges() {
    if (!selectedNodeId) return null;
    const node = findNode(currentRegexConfig.root, selectedNodeId);
    if (!node) return null;

    node.enabled = regexNodeEnabled ? regexNodeEnabled.checked : true;
    node.title = regexNodeTitle ? regexNodeTitle.value : '';
    node.identifier = regexNodeIdentifier ? regexNodeIdentifier.value : '';

    const isGroup = node.kind === 'group' || Array.isArray(node.children);
    if (!isGroup) {
      node.pattern = regexNodePattern ? regexNodePattern.value : '';
      node.replacement = regexNodeReplacement ? regexNodeReplacement.value : '';
      node.extract_group = regexNodeExtractGroup ? parseInt(regexNodeExtractGroup.value) || 0 : 0;
      node.apply_to = regexNodeApplyTo ? regexNodeApplyTo.value : 'body';
      node.description = regexNodeDescription ? regexNodeDescription.value : '';
    }

    return node;
  }

  async function loadSelectedRegex() {
    if (!regexSelect) return;
    const profileId = regexSelect.value;
    if (!profileId) return;

    try {
      const resp = await fetch('/regex/profiles/' + profileId);
      if (!resp.ok) throw new Error('Failed to load regex profile');
      const data = await resp.json();
      currentRegexId = data.id;
      currentRegexConfig = data.config;
      renderRegexTree();
      clearNodeEditor();
    } catch (err) {
      console.error('Load regex profile error:', err);
    }
  }

  function clearNodeEditor() {
    selectedNodeId = null;
    if (regexNodeEditor) regexNodeEditor.style.display = 'none';
    if (regexNodeEmptyHint) regexNodeEmptyHint.style.display = 'flex';
  }

  async function createRegexProfile() {
    const name = prompt('请输入新正则化配置名称：', '新正则化配置');
    if (!name) return;

    try {
      const resp = await fetch('/regex/profiles', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name })
      });
      if (!resp.ok) throw new Error('Failed to create regex profile');
      const data = await resp.json();
      await loadRegexProfiles();
      regexSelect.value = data.id;
      await loadSelectedRegex();
    } catch (err) {
      console.error('Create regex profile error:', err);
      alert('创建失败：' + err.message);
    }
  }

  async function saveRegexProfile() {
    if (!currentRegexId || !currentRegexConfig) return;

    const profile = regexProfiles.find(function (p) { return p.id === currentRegexId; });
    if (profile && profile.is_default) {
      alert('默认正则化配置不可修改！');
      return;
    }

    try {
      const resp = await fetch('/regex/profiles/' + currentRegexId, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ config: currentRegexConfig })
      });
      if (!resp.ok) throw new Error('Failed to save regex profile');
      alert('保存成功！');
    } catch (err) {
      console.error('Save regex profile error:', err);
      alert('保存失败：' + err.message);
    }
  }

  async function deleteRegexProfile() {
    if (!currentRegexId) return;

    const profile = regexProfiles.find(function (p) { return p.id === currentRegexId; });
    if (profile && profile.is_default) {
      alert('默认正则化配置不可删除！');
      return;
    }

    if (!confirm('确定要删除此正则化配置吗？')) return;

    try {
      const resp = await fetch('/regex/profiles/' + currentRegexId, {
        method: 'DELETE'
      });
      if (!resp.ok) throw new Error('Failed to delete regex profile');
      await loadRegexProfiles();
    } catch (err) {
      console.error('Delete regex profile error:', err);
      alert('删除失败：' + err.message);
    }
  }

  async function setActiveRegex() {
    if (!currentRegexId) return;

    try {
      const resp = await fetch('/regex/active?profile_id=' + encodeURIComponent(currentRegexId), {
        method: 'PUT'
      });
      if (!resp.ok) throw new Error('Failed to set active regex');
      const data = await resp.json();
      const profile = regexProfiles.find(function (p) { return p.id === currentRegexId; });
      regexActiveHint.textContent = (profile ? profile.name : currentRegexId) + (data.is_default || (profile && profile.is_default) ? ' (默认)' : '');
      alert('已应用为当前正则化配置！');
    } catch (err) {
      console.error('Set active regex error:', err);
      alert('应用失败：' + err.message);
    }
  }

  function addGroup() {
    if (!currentRegexConfig || !currentRegexConfig.root) return;

    const newGroup = {
      id: 'node_' + Date.now().toString(36),
      kind: 'group',
      title: '新规则组',
      identifier: 'group_' + Date.now().toString(36),
      enabled: true,
      children: [],
      injection_order: 0
    };

    currentRegexConfig.root.children.push(newGroup);
    renderRegexTree();
    selectNode(newGroup.id);
  }

  function addRule() {
    if (!currentRegexConfig || !currentRegexConfig.root) return;

    const parentId = selectedNodeId;
    let parent = currentRegexConfig.root;
    if (parentId) {
      const found = findNode(currentRegexConfig.root, parentId);
      if (found && found.kind === 'group') {
        parent = found;
      }
    }

    const newRule = {
      id: 'node_' + Date.now().toString(36),
      kind: 'regex',
      title: '新规则',
      identifier: 'rule_' + Date.now().toString(36),
      enabled: true,
      pattern: '',
      replacement: '',
      extract_group: 0,
      apply_to: 'body',
      description: '',
      meta: {}
    };

    if (!parent.children) parent.children = [];
    parent.children.push(newRule);
    renderRegexTree();
    selectNode(newRule.id);
  }

  function deleteNode() {
    if (!selectedNodeId || !currentRegexConfig || !currentRegexConfig.root) return;

    function removeFromParent(parent, nodeId) {
      if (!parent.children) return false;
      const idx = parent.children.findIndex(function (c) { return c.id === nodeId; });
      if (idx > -1) {
        parent.children.splice(idx, 1);
        return true;
      }
      for (const child of parent.children) {
        if (removeFromParent(child, nodeId)) return true;
      }
      return false;
    }

    removeFromParent(currentRegexConfig.root, selectedNodeId);
    renderRegexTree();
    clearNodeEditor();
  }

  async function importRegex() {
    const file = regexImportFile ? regexImportFile.files[0] : null;
    if (!file) {
      alert('请先选择文件');
      return;
    }

    const reader = new FileReader();
    reader.onload = async function (e) {
      try {
        const config = JSON.parse(e.target.result);
        const name = (regexImportName && regexImportName.value) || config.name || '导入的正则化';

        const resp = await fetch('/regex/profiles', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: name, config: config })
        });
        if (!resp.ok) throw new Error('Failed to import regex profile');
        await loadRegexProfiles();
        alert('导入成功！');
      } catch (err) {
        console.error('Import regex error:', err);
        alert('导入失败：' + err.message);
      }
    };
    reader.readAsText(file);
  }

  function exportRegex() {
    if (!currentRegexConfig) return;

    const blob = new Blob([JSON.stringify(currentRegexConfig, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = (currentRegexConfig.name || 'regex') + '.json';
    a.click();
    URL.revokeObjectURL(url);
  }

  function bindEvents() {
    if (regexSelect) {
      regexSelect.addEventListener('change', loadSelectedRegex);
    }

    if (regexCreateBtn) {
      regexCreateBtn.addEventListener('click', createRegexProfile);
    }
    if (regexSetActiveBtn) {
      regexSetActiveBtn.addEventListener('click', setActiveRegex);
    }
    if (regexSaveBtn) {
      regexSaveBtn.addEventListener('click', saveRegexProfile);
    }
    if (regexDeleteBtn) {
      regexDeleteBtn.addEventListener('click', deleteRegexProfile);
    }

    if (regexAddGroupBtn) {
      regexAddGroupBtn.addEventListener('click', addGroup);
    }
    if (regexAddRuleBtn) {
      regexAddRuleBtn.addEventListener('click', addRule);
    }
    if (regexDeleteNodeBtn) {
      regexDeleteNodeBtn.addEventListener('click', deleteNode);
    }

    if (regexImportBtn) {
      regexImportBtn.addEventListener('click', importRegex);
    }
    if (regexExportBtn) {
      regexExportBtn.addEventListener('click', exportRegex);
    }

    [regexNodeTitle, regexNodeIdentifier, regexNodePattern, regexNodeReplacement, 
     regexNodeExtractGroup, regexNodeApplyTo, regexNodeDescription].forEach(function (el) {
      if (el) {
        el.addEventListener('change', collectNodeChanges);
        el.addEventListener('input', collectNodeChanges);
      }
    });

    if (regexNodeEnabled) {
      regexNodeEnabled.addEventListener('change', function () {
        collectNodeChanges();
        renderRegexTree();
      });
    }
  }

  async function init() {
    bindEvents();
    await loadRegexProfiles();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
