(function () {
  // --- UI 元素引用 ---
  // Tabs
  const tabButtons = document.querySelectorAll('.settings-tab-btn');
  const tabPanes = document.querySelectorAll('.tab-pane');

  // Visual Selectors
  const themeOptions = document.querySelectorAll('#theme-grid .visual-option');
  const bgOptions = document.querySelectorAll('#bg-grid .visual-option');

  // Form Fields
  const postprocessingRulesEl = document.getElementById("postprocessing-rules");
  const summaryEnabledEl = document.getElementById("summary-enabled");
  const summaryProfileIdEl = document.getElementById("summary-profile-id");
  const summaryFrequencyEl = document.getElementById("summary-frequency");
  const summaryRagConfigEl = document.getElementById("summary-rag-config");
  const variablesEnabledEl = document.getElementById("variables-enabled");
  const variablesProfileIdEl = document.getElementById("variables-profile-id");
  const variablesApiConfigIdEl = document.getElementById("variables-api-config-id");
  const alignmentStrictEl = document.getElementById("alignment-strict");
  const alignmentRuleIdEl = document.getElementById("alignment-rule-id");
  const textoptEnabledEl = document.getElementById("textopt-enabled");
  const textoptProfileIdEl = document.getElementById("textopt-profile-id");
  const worldEvolutionEnabledEl = document.getElementById("world-evolution-enabled");
  const worldEvolutionProfileIdEl = document.getElementById("world-evolution-profile-id");
  const defaultProfilesEl = document.getElementById("default-profiles");

  // Typography Fields
  const fontUiFamilyEl = document.getElementById("font-ui-family");
  const fontUiSizeEl = document.getElementById("font-ui-size");
  const fontStoryFamilyEl = document.getElementById("font-story-family");
  const fontStorySizeEl = document.getElementById("font-story-size");
  const fontConsoleFamilyEl = document.getElementById("font-console-family");
  const fontConsoleSizeEl = document.getElementById("font-console-size");
  const fontCharFamilyEl = document.getElementById("font-char-family");
  const fontCharSizeEl = document.getElementById("font-char-size");
  const fontWorldFamilyEl = document.getElementById("font-world-family");
  const fontWorldSizeEl = document.getElementById("font-world-size");
  const fontDungeonFamilyEl = document.getElementById("font-dungeon-family");
  const fontDungeonSizeEl = document.getElementById("font-dungeon-size");

  const DEFAULT_FONT_SIZE = "14px";

  // 字体分区配置
  const FONT_ZONES = {
    ui: {
      familyVar: "--font-ui-family",
      sizeVar: "--font-ui-size",
      familyEl: fontUiFamilyEl,
      sizeEl: fontUiSizeEl,
      storageFamilyKey: "app_font_ui_family",
      storageSizeKey: "app_font_ui_size"
    },
    story: {
      familyVar: "--font-story-family",
      sizeVar: "--font-story-size",
      familyEl: fontStoryFamilyEl,
      sizeEl: fontStorySizeEl,
      storageFamilyKey: "app_font_story_family",
      storageSizeKey: "app_font_story_size"
    },
    console: {
      familyVar: "--font-console-family",
      sizeVar: "--font-console-size",
      familyEl: fontConsoleFamilyEl,
      sizeEl: fontConsoleSizeEl,
      storageFamilyKey: "app_font_console_family",
      storageSizeKey: "app_font_console_size"
    },
    character: {
      familyVar: "--font-char-family",
      sizeVar: "--font-char-size",
      familyEl: fontCharFamilyEl,
      sizeEl: fontCharSizeEl,
      storageFamilyKey: "app_font_char_family",
      storageSizeKey: "app_font_char_size"
    },
    world: {
      familyVar: "--font-world-family",
      sizeVar: "--font-world-size",
      familyEl: fontWorldFamilyEl,
      sizeEl: fontWorldSizeEl,
      storageFamilyKey: "app_font_world_family",
      storageSizeKey: "app_font_world_size"
    },
    dungeon: {
      familyVar: "--font-dungeon-family",
      sizeVar: "--font-dungeon-size",
      familyEl: fontDungeonFamilyEl,
      sizeEl: fontDungeonSizeEl,
      storageFamilyKey: "app_font_dungeon_family",
      storageSizeKey: "app_font_dungeon_size"
    }
  };


  // Actions
  const loadBtn = document.getElementById("settings-load-btn");
  const saveBtn = document.getElementById("settings-save-btn");
  const statusEl = document.getElementById("settings-status");

  // State
  let currentSettings = {};

  // --- 1. 核心逻辑：应用主题 ---
  function applyVisuals(theme, bg) {
    if (theme) {
      document.documentElement.setAttribute('data-theme', theme);
      localStorage.setItem('app_theme', theme);
      themeOptions.forEach(opt => {
        if (opt.dataset.value === theme) opt.classList.add('selected');
        else opt.classList.remove('selected');
      });
    }

    if (bg) {
      document.body.classList.forEach(cls => {
        if (cls.startsWith('bg-')) document.body.classList.remove(cls);
      });
      document.body.classList.add(`bg-${bg}`);
      localStorage.setItem('app_bg', bg);
      bgOptions.forEach(opt => {
        if (opt.dataset.value === bg) opt.classList.add('selected');
        else opt.classList.remove('selected');
      });
    }
  }

  function applyZoneFont(zoneName, family, size) {
    const zone = FONT_ZONES[zoneName];
    if (!zone) return;

    if (family) {
      document.documentElement.style.setProperty(zone.familyVar, family);
      localStorage.setItem(zone.storageFamilyKey, family);
      if (zone.familyEl) zone.familyEl.value = family;
    }
    if (size) {
      document.documentElement.style.setProperty(zone.sizeVar, size);
      localStorage.setItem(zone.storageSizeKey, size);
      if (zone.sizeEl) zone.sizeEl.value = size;
    }
  }

  function applyTypography(typographyConfig) {
    const cfg = typographyConfig || {};
    Object.keys(FONT_ZONES).forEach(zoneName => {
      const zone = FONT_ZONES[zoneName];
      if (!zone) return;
      const savedFamily = (cfg[zoneName] && cfg[zoneName].family) || localStorage.getItem(zone.storageFamilyKey) || (zone.familyEl && zone.familyEl.options.length ? zone.familyEl.options[0].value : "system-ui, -apple-system, 'Segoe UI', sans-serif");
      const savedSize = (cfg[zoneName] && cfg[zoneName].size) || localStorage.getItem(zone.storageSizeKey) || DEFAULT_FONT_SIZE;
      applyZoneFont(zoneName, savedFamily, savedSize);
    });
  }

  // --- 2. 交互逻辑：Tab 切换 ---
  function switchTab(targetId) {
    tabButtons.forEach(btn => {
      if (btn.dataset.target === targetId) btn.classList.add('active');
      else btn.classList.remove('active');
    });
    tabPanes.forEach(pane => {
      if (pane.id === targetId) pane.classList.add('active');
      else pane.classList.remove('active');
    });
  }

  // --- 3. 数据处理：填充表单 ---
  function populateForm(settings) {
    currentSettings = settings;
    const ui = settings.ui || {};
    applyVisuals(ui.theme || 'dark', ui.background || 'grid');
    applyTypography(ui.typography || {});

    postprocessingRulesEl.value = JSON.stringify(settings.text && settings.text.post_processing_rules ? settings.text.post_processing_rules : [], null, 2);

    const summary = settings.summary || {};
    summaryEnabledEl.checked = !!summary.enabled;
    summaryProfileIdEl.value = summary.profile_id || "";
    summaryFrequencyEl.value = summary.scene_frequency || 1;
    summaryRagConfigEl.value = JSON.stringify(summary.rag_config || {}, null, 2);

    const variables = settings.variables || {};
    variablesEnabledEl.checked = !!variables.enabled;
    variablesProfileIdEl.value = variables.profile_id || "";
    variablesApiConfigIdEl.value = variables.api_config_id || "";
    alignmentStrictEl.checked = !!variables.alignment_strict;
    alignmentRuleIdEl.value = variables.alignment_rule_id || "";

    const textopt = settings.text_opt || {};
    textoptEnabledEl.checked = !!textopt.enabled;
    textoptProfileIdEl.value = textopt.profile_id || "";

    const evolution = settings.world_evolution || {};
    worldEvolutionEnabledEl.checked = !!evolution.enabled;
    worldEvolutionProfileIdEl.value = evolution.profile_id || "";

    const defaults = settings.default_profiles || {};
    defaultProfilesEl.value = JSON.stringify(defaults, null, 2);
  }

  // --- 4. 数据处理：收集表单 ---
  function collectForm() {
    const activeThemeEl = document.querySelector('#theme-grid .visual-option.selected');
    const activeBgEl = document.querySelector('#bg-grid .visual-option.selected');
    const themeVal = activeThemeEl ? activeThemeEl.dataset.value : 'dark';
    const bgVal = activeBgEl ? activeBgEl.dataset.value : 'grid';

    const safeParse = (el, name) => {
      try {
        return el.value.trim() ? JSON.parse(el.value) : (name === 'rules' ? [] : {});
      } catch (e) {
        alert(`${name} JSON 格式错误，请检查！`);
        throw e;
      }
    };

    let postRules, ragConfig, defaultProfiles;
    try {
      postRules = safeParse(postprocessingRulesEl, 'rules');
      ragConfig = safeParse(summaryRagConfigEl, 'rag');
      defaultProfiles = safeParse(defaultProfilesEl, 'profiles');
    } catch (e) {
      return null;
    }

    const typography = {};
    Object.keys(FONT_ZONES).forEach(zoneName => {
      const zone = FONT_ZONES[zoneName];
      if (!zone || !zone.familyEl || !zone.sizeEl) return;
      typography[zoneName] = {
        family: zone.familyEl.value,
        size: zone.sizeEl.value
      };
    });

    return {
      ui: {
        theme: themeVal,
        background: bgVal,
        typography
      },
      text: {
        post_processing_rules: postRules
      },
      summary: {
        enabled: summaryEnabledEl.checked,
        profile_id: summaryProfileIdEl.value.trim(),
        scene_frequency: parseInt(summaryFrequencyEl.value || "1", 10),
        rag_config: ragConfig
      },
      variables: {
        enabled: variablesEnabledEl.checked,
        profile_id: variablesProfileIdEl.value.trim(),
        api_config_id: variablesApiConfigIdEl.value.trim(),
        alignment_strict: alignmentStrictEl.checked,
        alignment_rule_id: alignmentRuleIdEl.value.trim()
      },
      text_opt: {
        enabled: textoptEnabledEl.checked,
        profile_id: textoptProfileIdEl.value.trim()
      },
      world_evolution: {
        enabled: worldEvolutionEnabledEl.checked,
        profile_id: worldEvolutionProfileIdEl.value.trim()
      },
      default_profiles: defaultProfiles
    };
  }

  // --- 5. API 交互 ---
  async function loadSettings() {
    statusEl.textContent = "加载中...";
    try {
      const resp = await fetch("/api/settings/global");
      if (!resp.ok) throw new Error("HTTP " + resp.status);
      const data = await resp.json();
      populateForm(data);
      statusEl.textContent = "已加载";
      setTimeout(() => statusEl.textContent = "就绪", 2000);
    } catch (err) {
      console.error(err);
      statusEl.textContent = "加载失败";
    }
  }

  async function saveSettings() {
    const settings = collectForm();
    if (!settings) return;

    applyVisuals(settings.ui.theme, settings.ui.background);
    applyTypography(settings.ui.typography || {});

    statusEl.textContent = "保存中...";
    try {
      const resp = await fetch("/api/settings/global", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(settings)
      });
      if (!resp.ok) throw new Error("HTTP " + resp.status);
      statusEl.textContent = "保存成功";
      setTimeout(() => statusEl.textContent = "就绪", 2000);
    } catch (err) {
      console.error(err);
      statusEl.textContent = "保存失败";
    }
  }

  // --- 6. 事件绑定 ---
  function bindEvents() {
    tabButtons.forEach(btn => {
      btn.addEventListener('click', () => switchTab(btn.dataset.target));
    });

    themeOptions.forEach(opt => {
      opt.addEventListener('click', () => {
        applyVisuals(opt.dataset.value, null);
      });
    });

    bgOptions.forEach(opt => {
      opt.addEventListener('click', () => {
        applyVisuals(null, opt.dataset.value);
      });
    });

    // 字体相关绑定
    [fontUiFamilyEl, fontUiSizeEl, fontStoryFamilyEl, fontStorySizeEl,
     fontConsoleFamilyEl, fontConsoleSizeEl, fontCharFamilyEl, fontCharSizeEl,
     fontWorldFamilyEl, fontWorldSizeEl, fontDungeonFamilyEl, fontDungeonSizeEl].forEach(el => {
       if(el) {
         el.addEventListener('change', () => applyTypography(collectForm()?.ui?.typography));
       }
    });

    loadBtn.addEventListener("click", loadSettings);
    saveBtn.addEventListener("click", saveSettings);
  }

  // --- 初始化 ---
  function init() {
    bindEvents();
    loadSettings();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();

/* =========================================================
 * 预设管理 + API配置（大模型） - 本次重构新增
 * ========================================================= */
(function () {
  // --- 小工具 ---
  const $ = (id) => document.getElementById(id);
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

  function nowId(prefix) {
    return prefix + "_" + Math.random().toString(16).slice(2, 10);
  }

  function setText(el, text) {
    if (!el) return;
    el.textContent = text;
  }

  async function safeJson(resp) {
    const ct = (resp.headers.get("content-type") || "").toLowerCase();
    if (ct.includes("application/json")) return await resp.json();
    const t = await resp.text();
    try { return JSON.parse(t); } catch (e) { return { raw: t }; }
  }

  // =========================================================
  // A) 预设管理
  // =========================================================
  const presetSelectEl = $("preset-select");
  const presetActiveHintEl = $("preset-active-hint");
  const presetStatusEl = $("preset-status"); // 可能不存在，已做兼容处理

  const presetCreateBtn = $("preset-create-btn");
  const presetSetActiveBtn = $("preset-set-active-btn");
  const presetSaveBtn = $("preset-save-btn");
  const presetDeleteBtn = $("preset-delete-btn");

  const presetImportFileEl = $("preset-import-file");
  const presetImportNameEl = $("preset-import-name");
  const presetImportBtn = $("preset-import-btn");
  const presetExportBtn = $("preset-export-btn");

  const presetTreeEl = $("preset-tree");
  const addGroupBtn = $("preset-add-group-btn");
  const addPromptBtn = $("preset-add-prompt-btn");
  const deleteNodeBtn = $("preset-delete-node-btn");

  // 编辑器字段
  const nodeTitleEl = $("preset-node-title");
  const nodeEnabledEl = $("preset-node-enabled");
  const nodeIdentifierEl = $("preset-node-identifier");
  const nodeOrderEl = $("preset-node-order");

  const nodePromptFieldsEl = $("preset-node-prompt-fields");
  const nodeRoleEl = $("preset-node-role");
  const nodeContentEl = $("preset-node-content");
  const nodeHintEl = $("preset-node-hint");

  const nodeDepthEl = $("preset-node-depth");
  const nodePositionEl = $("preset-node-position");
  const nodeSystemPromptEl = $("preset-node-system-prompt");
  const nodeMarkerEl = $("preset-node-marker");
  const nodeOverridesEl = $("preset-node-overrides");
  const nodeTriggersEl = $("preset-node-triggers");
  const promptOnlyTogglesEl = $("prompt-only-toggles");
  const editorContainerEl = $("preset-node-editor-container");

  let presetsOverview = [];
  let activePresetId = null;
  let currentPreset = null;  // full preset
  let selectedNodeId = null;
  let parentMap = {}; // nodeId -> parentId

  function buildParentMap(node, parentId) {
    if (!node || typeof node !== "object") return;
    if (node.id) parentMap[node.id] = parentId || null;
    if (node.kind === "group" && Array.isArray(node.children)) {
      for (const ch of node.children) buildParentMap(ch, node.id);
    }
  }

  function findNode(node, id) {
    if (!node || typeof node !== "object") return null;
    if (node.id === id) return node;
    if (node.children && Array.isArray(node.children)) {
      for (const ch of node.children) {
        const found = findNode(ch, id);
        if (found) return found;
      }
    }
    return null;
  }

  function findParent(node, id) {
    const pid = parentMap[id];
    if (!pid) return null;
    return findNode(node, pid);
  }

  function renderTree() {
    if (!presetTreeEl) return;

    if (!currentPreset || !currentPreset.root) {
        presetTreeEl.innerHTML = '<div style="padding:20px; text-align:center; color:#666;">暂无数据或未加载</div>';
        return;
    }

    presetTreeEl.innerHTML = "";
    parentMap = {};
    buildParentMap(currentPreset.root, null);

    const root = currentPreset.root;

    function renderNode(node, depth) {
      if (!node) return;

      const row = document.createElement("div");
      row.className = "config-tree-node";
      if (selectedNodeId && node.id === selectedNodeId) {
          row.classList.add("selected");
      }
      if (node.enabled === false) {
          row.classList.add("disabled");
      }

      row.style.paddingLeft = (depth * 18 + 8) + "px";

      const toggleLabel = document.createElement("label");
      toggleLabel.className = "toggle-switch";
      toggleLabel.style.transform = "scale(0.7)";
      toggleLabel.style.margin = "0";
      toggleLabel.onclick = (e) => e.stopPropagation();

      const input = document.createElement("input");
      input.type = "checkbox";
      input.checked = node.enabled !== false;
      input.onchange = () => {
          node.enabled = input.checked;
          if (selectedNodeId === node.id && nodeEnabledEl) {
              nodeEnabledEl.checked = input.checked;
          }
          renderTree();
      };

      const slider = document.createElement("span");
      slider.className = "slider";
      toggleLabel.appendChild(input);
      toggleLabel.appendChild(slider);

      const icon = document.createElement("span");
      icon.className = "tree-icon";
      icon.textContent = node.kind === "group" ? "📁" : "📝";

      const titleDiv = document.createElement("div");
      titleDiv.className = "tree-title";
      titleDiv.textContent = node.title || node.identifier || "未命名";

      if (node.kind === "prompt") {
          const infoDiv = document.createElement("span");
          infoDiv.className = "small-text muted";
          infoDiv.style.fontSize = "11px";
          infoDiv.style.marginLeft = "auto";
          infoDiv.textContent = `#${node.injection_order || 0}`;
          row.appendChild(toggleLabel);
          row.appendChild(icon);
          row.appendChild(titleDiv);
          row.appendChild(infoDiv);
      } else {
          row.appendChild(toggleLabel);
          row.appendChild(icon);
          row.appendChild(titleDiv);
      }

      row.addEventListener("click", () => {
        selectedNodeId = node.id;
        renderTree();
        syncEditor();
      });

      presetTreeEl.appendChild(row);

      if (node.kind === "group" && Array.isArray(node.children)) {
        node.children.forEach(child => {
            if(child) renderNode(child, depth + 1);
        });
      }
    }

    renderNode(root, 0);
  }

  function syncEditor() {
    const container = editorContainerEl;
    const hint = nodeHintEl;

    if (!currentPreset || !selectedNodeId) {
      if(container) container.style.display = "none";
      if(hint) hint.style.display = "flex";
      return;
    }

    const node = findNode(currentPreset.root, selectedNodeId);
    if (!node) {
      console.warn("选中的节点 ID 在树中未找到:", selectedNodeId);
      return;
    }

    if(container) container.style.display = "flex";
    if(hint) hint.style.display = "none";

    // 回显通用数据
    if(nodeTitleEl) nodeTitleEl.value = node.title || node.name || "";
    if(nodeIdentifierEl) nodeIdentifierEl.value = node.identifier || "";
    if(nodeEnabledEl) nodeEnabledEl.checked = node.enabled !== false;

    const isGroup = node.kind === "group" || Array.isArray(node.children);

    const promptFields = $("preset-node-prompt-fields");
    const groupHint = $("prompt-bool-fields");

    if (isGroup) {
      if(promptFields) promptFields.style.display = "none";
      if(groupHint) groupHint.style.display = "flex";
    } else {
      if(promptFields) promptFields.style.display = "flex";
      if(groupHint) groupHint.style.display = "none";

      if(nodeContentEl) nodeContentEl.value = node.content || "";
      if(nodeRoleEl) nodeRoleEl.value = node.role || "system";
      if(nodePositionEl) nodePositionEl.value = node.injection_position || 0;
      if(nodeOrderEl) nodeOrderEl.value = node.injection_order || 0;
      if(nodeDepthEl) nodeDepthEl.value = node.injection_depth || 0;

      if(nodeSystemPromptEl) nodeSystemPromptEl.checked = !!node.system_prompt;
      if(nodeMarkerEl) nodeMarkerEl.checked = !!node.marker;
      if(nodeOverridesEl) nodeOverridesEl.checked = !!node.forbid_overrides;

      if(nodeTriggersEl) nodeTriggersEl.value = (node.injection_trigger || []).join(", ");
    }
  }

  function bindPresetEditorEvents() {
    const updateNode = (key, val) => {
      const node = selectedNodeId ? findNode(currentPreset.root, selectedNodeId) : null;
      if (!node) return;
      node[key] = val;
      if (key === 'title' || key === 'identifier' || key === 'enabled') renderTree();
    };

    if(nodeTitleEl) nodeTitleEl.addEventListener("input", () => updateNode('title', nodeTitleEl.value));
    if(nodeIdentifierEl) nodeIdentifierEl.addEventListener("input", () => updateNode('identifier', nodeIdentifierEl.value));
    if(nodeContentEl) nodeContentEl.addEventListener("input", () => updateNode('content', nodeContentEl.value));

    if(nodeOrderEl) nodeOrderEl.addEventListener("change", () => updateNode('injection_order', parseInt(nodeOrderEl.value) || 0));
    if(nodeDepthEl) nodeDepthEl.addEventListener("change", () => updateNode('injection_depth', parseInt(nodeDepthEl.value) || 0));

    if(nodeRoleEl) nodeRoleEl.addEventListener("change", () => updateNode('role', nodeRoleEl.value));
    if(nodePositionEl) nodePositionEl.addEventListener("change", () => updateNode('injection_position', nodePositionEl.value));

    if(nodeEnabledEl) nodeEnabledEl.addEventListener("change", () => {
      updateNode('enabled', nodeEnabledEl.checked);
    });
    if(nodeSystemPromptEl) nodeSystemPromptEl.addEventListener("change", () => updateNode('system_prompt', nodeSystemPromptEl.checked));
    if(nodeMarkerEl) nodeMarkerEl.addEventListener("change", () => updateNode('marker', nodeMarkerEl.checked));
    if(nodeOverridesEl) nodeOverridesEl.addEventListener("change", () => updateNode('forbid_overrides', nodeOverridesEl.checked));

    if(nodeTriggersEl) nodeTriggersEl.addEventListener("change", () => {
      const val = nodeTriggersEl.value;
      const arr = val.split(/[,，]/).map(s => s.trim()).filter(s => s);
      updateNode('injection_trigger', arr);
    });
  }

  function addChildNode(kind) {
    if (!currentPreset) return;
    const root = currentPreset.root;

    let parent = root;
    if (selectedNodeId) {
      const node = findNode(root, selectedNodeId);
      if (node && node.kind === "group") parent = node;
      else {
        const p = findParent(root, selectedNodeId);
        if (p && p.kind === "group") parent = p;
      }
    }
    parent.children = Array.isArray(parent.children) ? parent.children : [];
    if (kind === "group") {
      parent.children.push({
        id: nowId("node"),
        kind: "group",
        title: "新模块",
        enabled: true,
        children: []
      });
    } else {
      parent.children.push({
        id: nowId("node"),
        kind: "prompt",
        title: "新提示词",
        enabled: true,
        role: "system",
        content: ""
      });
    }
    renderTree();
  }

  function deleteSelectedNode() {
    if (!currentPreset || !selectedNodeId) return;
    const root = currentPreset.root;
    if (root.id === selectedNodeId) {
      alert("Root 节点不可删除。");
      return;
    }
    const parent = findParent(root, selectedNodeId);
    if (!parent || parent.kind !== "group") return;

    parent.children = (parent.children || []).filter(ch => ch.id !== selectedNodeId);
    selectedNodeId = parent.id;
    renderTree();
    syncEditor();
  }

  async function loadPresetsOverview() {
    if (presetStatusEl) setText(presetStatusEl, "加载中...");
    const resp = await fetch("/api/presets");
    const data = await safeJson(resp);
    presetsOverview = data.presets || [];
    activePresetId = data.active ? data.active.preset_id : null;

    if (presetSelectEl) {
      presetSelectEl.innerHTML = "";
      for (const p of presetsOverview) {
        const opt = document.createElement("option");
        opt.value = p.id;
        opt.textContent = p.name + (p.is_default ? " (默认)" : "");
        presetSelectEl.appendChild(opt);
      }
      if (activePresetId) presetSelectEl.value = activePresetId;
    }

    // 查找当前预设的名称
    const currentPreset = presetsOverview.find(p => p.id === activePresetId);
    const presetName = currentPreset ? (currentPreset.name + (currentPreset.is_default ? " (默认)" : "")) : activePresetId || "-";
    
    if (presetActiveHintEl) setText(presetActiveHintEl, "当前：" + presetName);
    if (presetStatusEl) setText(presetStatusEl, "就绪");

    const toLoad = (presetSelectEl && presetSelectEl.value) ? presetSelectEl.value : (presetsOverview[0] && presetsOverview[0].id);
    if (toLoad) await loadPresetDetail(toLoad);
  }

  async function loadPresetDetail(presetId) {
    if (!presetId) return;
    if (presetStatusEl) setText(presetStatusEl, "加载预设...");
    const resp = await fetch("/api/presets/" + encodeURIComponent(presetId));
    if (!resp.ok) {
      if (presetStatusEl) setText(presetStatusEl, "加载失败");
      return;
    }
    currentPreset = await resp.json();
    selectedNodeId = currentPreset && currentPreset.root ? currentPreset.root.id : null;
    renderTree();
    syncEditor();
    if (presetStatusEl) setText(presetStatusEl, "就绪");
  }

  async function savePreset() {
    if (!currentPreset) return;
    if (presetStatusEl) setText(presetStatusEl, "保存中...");
    const resp = await fetch("/api/presets/" + encodeURIComponent(currentPreset.id), {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        id: currentPreset.id,
        name: currentPreset.name,
        version: currentPreset.version || 1,
        root: currentPreset.root,
        meta: currentPreset.meta || {}
      })
    });
    if (!resp.ok) {
      const t = await resp.text();
      if (presetStatusEl) setText(presetStatusEl, "保存失败：" + t);
      return;
    }
    if (presetStatusEl) setText(presetStatusEl, "保存成功");
    await sleep(800);
    await loadPresetsOverview();
  }

  async function createPreset() {
    const name = prompt("新预设名称：", "新预设");
    if (!name) return;
    if (presetStatusEl) setText(presetStatusEl, "创建中...");
    const resp = await fetch("/api/presets?name=" + encodeURIComponent(name), { method: "POST" });
    if (!resp.ok) {
      if (presetStatusEl) setText(presetStatusEl, "创建失败");
      return;
    }
    const p = await resp.json();
    if (presetStatusEl) setText(presetStatusEl, "创建成功");
    await loadPresetsOverview();
    if (presetSelectEl) presetSelectEl.value = p.id;
    await loadPresetDetail(p.id);
  }

  async function setActivePreset() {
    if (!presetSelectEl) return;
    const pid = presetSelectEl.value;
    if (!pid) return;
    const resp = await fetch("/api/presets/active", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ preset_id: pid })
    });
    if (!resp.ok) {
      const t = await resp.text();
      if (presetStatusEl) setText(presetStatusEl, "设为当前失败：" + t);
      return;
    }
    const data = await resp.json();
    activePresetId = data.preset_id;
    
    // 查找当前预设的名称
    const currentPreset = presetsOverview.find(p => p.id === activePresetId);
    const presetName = currentPreset ? (currentPreset.name + (currentPreset.is_default || data.is_default ? " (默认)" : "")) : activePresetId || "-";
    
    if (presetActiveHintEl) setText(presetActiveHintEl, "当前：" + presetName);
    if (presetStatusEl) setText(presetStatusEl, "已设为当前");
    
    // 确保下拉选择框的选中状态正确
    if (presetSelectEl.value !== activePresetId) {
      presetSelectEl.value = activePresetId;
    }
  }

  async function deletePreset() {
    if (!presetSelectEl) return;
    const pid = presetSelectEl.value;
    if (!pid) return;
    
    const presetToDelete = presetsOverview.find(p => p.id === pid);
    if (presetToDelete && presetToDelete.is_default) {
      alert("默认预设不可删除！");
      return;
    }
    
    if (!confirm("确认删除该预设？")) return;

    if (presetStatusEl) setText(presetStatusEl, "删除中...");
    const resp = await fetch("/api/presets/" + encodeURIComponent(pid), { method: "DELETE" });
    if (!resp.ok) {
      const t = await resp.text();
      if (presetStatusEl) setText(presetStatusEl, "删除失败：" + t);
      return;
    }
    if (presetStatusEl) setText(presetStatusEl, "已删除");
    await loadPresetsOverview();
  }

  async function importPreset() {
    const f = presetImportFileEl && presetImportFileEl.files ? presetImportFileEl.files[0] : null;
    if (!f) {
      alert("请先选择一个 JSON 文件。");
      return;
    }
    if (presetStatusEl) setText(presetStatusEl, "导入中...");
    const text = await f.text();
    let payload;
    try { payload = JSON.parse(text); } catch (e) { alert("JSON 解析失败"); return; }

    const nameHint = (presetImportNameEl && presetImportNameEl.value.trim()) ? presetImportNameEl.value.trim() : ("导入_" + f.name.replace(/\.json$/i, ""));
    const resp = await fetch("/api/presets/import", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ payload, name_hint: nameHint })
    });
    if (!resp.ok) {
      const t = await resp.text();
      if (presetStatusEl) setText(presetStatusEl, "导入失败：" + t);
      return;
    }
    const p = await resp.json();
    if (presetStatusEl) setText(presetStatusEl, "导入成功");
    await loadPresetsOverview();
    if (presetSelectEl) presetSelectEl.value = p.id;
    await loadPresetDetail(p.id);
  }

  async function exportPreset() {
    if (!currentPreset) return;
    const resp = await fetch("/api/presets/export/" + encodeURIComponent(currentPreset.id));
    if (!resp.ok) {
      // 如果后端没实现 export 接口，可以直接导出 currentPreset
      const blob = new Blob([JSON.stringify(currentPreset, null, 2)], { type: "application/json" });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = (currentPreset.name || "preset") + ".json";
      a.click();
      URL.revokeObjectURL(a.href);
      return;
    }
    const data = await resp.json();
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = (data.name || "preset") + ".json";
    a.click();
    URL.revokeObjectURL(a.href);
  }

  // 绑定事件
  if (presetSelectEl) {
    presetSelectEl.addEventListener("change", async () => {
      await loadPresetDetail(presetSelectEl.value);
    });
  }
  presetCreateBtn && presetCreateBtn.addEventListener("click", createPreset);
  presetSetActiveBtn && presetSetActiveBtn.addEventListener("click", setActivePreset);
  presetSaveBtn && presetSaveBtn.addEventListener("click", savePreset);
  presetDeleteBtn && presetDeleteBtn.addEventListener("click", deletePreset);
  presetImportBtn && presetImportBtn.addEventListener("click", importPreset);
  presetExportBtn && presetExportBtn.addEventListener("click", exportPreset);

  addGroupBtn && addGroupBtn.addEventListener("click", () => addChildNode("group"));
  addPromptBtn && addPromptBtn.addEventListener("click", () => addChildNode("prompt"));
  deleteNodeBtn && deleteNodeBtn.addEventListener("click", deleteSelectedNode);
  bindPresetEditorEvents();

  // =========================================================
  // B) API配置（LLM Config）
  // =========================================================
  const llmListEl = $("llm-config-list");
  const llmActiveHintEl = $("llm-active-hint");
  const llmStatusEl = $("llm-status");

  const llmNewBtn = $("llm-new-btn");
  const llmSetActiveBtn = $("llm-set-active-btn");
  const llmSaveBtn = $("llm-save-btn");
  const llmDeleteBtn = $("llm-delete-btn");

  const llmNameEl = $("llm-name");
  const llmBaseUrlEl = $("llm-base-url");
  const llmApiKeyEl = $("llm-api-key");
  const llmStreamEl = $("llm-stream");
  const llmModelSelectEl = $("llm-model-select");
  const llmRefreshModelsBtn = $("llm-refresh-models-btn");
  const llmDefaultModelEl = $("llm-default-model");

  let llmConfigs = [];
  let llmActive = { config_id: null, model: null };
  let selectedConfigId = null;

  function renderLLMList() {
    if (!llmListEl) return;
    llmListEl.innerHTML = "";
    for (const cfg of llmConfigs) {
      const row = document.createElement("div");
      row.className = "list-item" + (cfg.id === selectedConfigId ? " active" : "");
      row.style.display = "flex";
      row.style.alignItems = "center";
      row.style.gap = "10px";

      const left = document.createElement("div");
      left.style.flex = "1";
      const name = document.createElement("div");
      name.textContent = cfg.name || cfg.id;
      const sub = document.createElement("div");
      sub.className = "small-text muted";
      sub.textContent = (cfg.base_url || "") + (cfg.stream ? " · stream" : " · non-stream");
      left.appendChild(name);
      left.appendChild(sub);

      const badge = document.createElement("div");
      badge.className = "small-text";
      if (llmActive && llmActive.config_id === cfg.id) {
        badge.textContent = "当前";
      } else {
        badge.textContent = "";
      }

      row.appendChild(left);
      row.appendChild(badge);

      row.addEventListener("click", () => {
        selectedConfigId = cfg.id;
        fillLLMEditor(cfg);
        renderLLMList();
      });

      llmListEl.appendChild(row);
    }
    if (llmActiveHintEl) setText(llmActiveHintEl, "当前：" + (llmActive && llmActive.config_id ? llmActive.config_id : "-") + (llmActive && llmActive.model ? (" / " + llmActive.model) : ""));
  }

  function getSelectedCfg() {
    if (!selectedConfigId) return null;
    return llmConfigs.find(c => c.id === selectedConfigId) || null;
  }

  function fillLLMEditor(cfg) {
    if (!cfg) return;
    llmNameEl && (llmNameEl.value = cfg.name || "");
    llmBaseUrlEl && (llmBaseUrlEl.value = cfg.base_url || "");
    llmApiKeyEl && (llmApiKeyEl.value = cfg.api_key || "");
    llmStreamEl && (llmStreamEl.checked = cfg.stream !== false);
    llmDefaultModelEl && (llmDefaultModelEl.value = cfg.default_model || "");
  }

  function collectLLMEditor() {
    const selectedCfg = getSelectedCfg();
    // 返回新对象，不修改 llmConfigs 数组中的原对象
    // 这样判断 isNewConfig 时才能正确检测 base_url 是否为空
    return {
      id: selectedCfg ? selectedCfg.id : nowId("llm"),
      name: llmNameEl ? llmNameEl.value.trim() : (selectedCfg ? selectedCfg.name : "未命名配置"),
      base_url: llmBaseUrlEl ? llmBaseUrlEl.value.trim() : (selectedCfg ? selectedCfg.base_url : ""),
      api_key: llmApiKeyEl ? llmApiKeyEl.value.trim() : (selectedCfg ? selectedCfg.api_key : ""),
      stream: llmStreamEl ? !!llmStreamEl.checked : true,
      default_model: llmDefaultModelEl ? llmDefaultModelEl.value.trim() : (selectedCfg ? selectedCfg.default_model : null)
    };
  }

  async function loadLLMConfigs() {
    if (llmStatusEl) setText(llmStatusEl, "加载中...");
    const resp = await fetch("/api/llm/configs");
    const data = await safeJson(resp);
    llmConfigs = data.configs || [];
    llmActive = data.active || { config_id: null, model: null };

    selectedConfigId = (llmActive && llmActive.config_id) ? llmActive.config_id : (llmConfigs[0] && llmConfigs[0].id);
    renderLLMList();
    const cfg = getSelectedCfg();
    if (cfg) fillLLMEditor(cfg);

    if (llmStatusEl) setText(llmStatusEl, "就绪");
  }

  async function saveLLMCfg() {
    const cfg = collectLLMEditor();
    if (!cfg.base_url || !cfg.api_key) {
      alert("请填写 base_url 与 api_key。");
      return;
    }
    if (llmStatusEl) setText(llmStatusEl, "保存中...");
    
    // 检查配置是否已存在于数据库中
    // 通过检查 llmConfigs 数组中是否有相同 ID 的配置且该配置有 base_url
    // 新创建的配置 base_url 为空，已保存的配置有 base_url
    const existingConfig = llmConfigs.find(c => c.id === cfg.id);
    const isNewConfig = !existingConfig || !existingConfig.base_url;
    
    const method = isNewConfig ? "POST" : "PUT";
    const url = method === "PUT" ? ("/api/llm/configs/" + encodeURIComponent(cfg.id)) : "/api/llm/configs";
    
    const resp = await fetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(cfg)
    });
    if (!resp.ok) {
      const t = await resp.text();
      if (llmStatusEl) setText(llmStatusEl, "保存失败：" + t);
      return;
    }
    const saved = await resp.json();
    llmConfigs = llmConfigs.filter(c => c.id !== saved.id);
    llmConfigs.push(saved);
    selectedConfigId = saved.id;
    renderLLMList();
    if (llmStatusEl) setText(llmStatusEl, "保存成功");
  }

  async function createLLMCfg() {
    const cfg = {
      id: nowId("llm"),
      name: "新配置",
      base_url: "",
      api_key: "",
      stream: true,
      default_model: ""
    };
    llmConfigs.push(cfg);
    selectedConfigId = cfg.id;
    renderLLMList();
    fillLLMEditor(cfg);
    if (llmStatusEl) setText(llmStatusEl, "已创建（未保存）");
  }

  async function deleteLLMCfg() {
    const cfg = getSelectedCfg();
    if (!cfg) return;
    if (!confirm("确认删除该配置？")) return;
    if (llmStatusEl) setText(llmStatusEl, "删除中...");
    const resp = await fetch("/api/llm/configs/" + encodeURIComponent(cfg.id), { method: "DELETE" });
    if (!resp.ok) {
      const t = await resp.text();
      if (llmStatusEl) setText(llmStatusEl, "删除失败：" + t);
      return;
    }
    llmConfigs = llmConfigs.filter(c => c.id !== cfg.id);
    selectedConfigId = (llmConfigs[0] && llmConfigs[0].id) || null;
    renderLLMList();
    if (getSelectedCfg()) fillLLMEditor(getSelectedCfg());
    if (llmStatusEl) setText(llmStatusEl, "已删除");
  }

  async function setActiveLLM() {
    const cfg = getSelectedCfg();
    if (!cfg) return;

    const model = llmModelSelectEl ? llmModelSelectEl.value : null;
    if (llmStatusEl) setText(llmStatusEl, "设为当前...");
    const resp = await fetch("/api/llm/active", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ config_id: cfg.id, model })
    });
    if (!resp.ok) {
      const t = await resp.text();
      if (llmStatusEl) setText(llmStatusEl, "失败：" + t);
      return;
    }
    llmActive = await resp.json();
    renderLLMList();
    if (llmStatusEl) setText(llmStatusEl, "已设为当前");
  }

  async function refreshModels() {
    const base_url = llmBaseUrlEl ? llmBaseUrlEl.value.trim() : "";
    const api_key = llmApiKeyEl ? llmApiKeyEl.value.trim() : "";
    if (!base_url || !api_key) {
      alert("请先填写 base_url 与 api_key。");
      return;
    }
    if (llmStatusEl) setText(llmStatusEl, "检索模型中...");
    const resp = await fetch("/api/llm/models/list", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ base_url, api_key })
    });
    if (!resp.ok) {
      const t = await resp.text();
      if (llmStatusEl) setText(llmStatusEl, "检索失败：" + t);
      return;
    }
    const data = await resp.json();
    const models = data.models || [];

    if (llmModelSelectEl) {
      llmModelSelectEl.innerHTML = "";
      for (const m of models) {
        const opt = document.createElement("option");
        opt.value = m;
        opt.textContent = m;
        llmModelSelectEl.appendChild(opt);
      }

      // 优先：active model / default_model
      const cfg = getSelectedCfg();
      const prefer = (llmActive && llmActive.model) || (cfg && cfg.default_model) || (models[0] || "");
      if (prefer && models.includes(prefer)) llmModelSelectEl.value = prefer;
    }

    if (llmStatusEl) setText(llmStatusEl, "模型已更新（共 " + models.length + " 个）");
  }

  llmNewBtn && llmNewBtn.addEventListener("click", createLLMCfg);
  llmSaveBtn && llmSaveBtn.addEventListener("click", saveLLMCfg);
  llmDeleteBtn && llmDeleteBtn.addEventListener("click", deleteLLMCfg);
  llmSetActiveBtn && llmSetActiveBtn.addEventListener("click", setActiveLLM);
  llmRefreshModelsBtn && llmRefreshModelsBtn.addEventListener("click", refreshModels);

  // =========================================================
  // Init
  // =========================================================
  function initPresetAndLLM() {
    const hasPresetArea = !!$("tab-presets");
    const hasLLMArea = !!$("tab-api");

    if (hasPresetArea) loadPresetsOverview().catch(console.error);
    if (hasLLMArea) loadLLMConfigs().catch(console.error);
  }

  // 确保DOM加载完成后再执行
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initPresetAndLLM);
  } else {
    initPresetAndLLM();
  }
})();