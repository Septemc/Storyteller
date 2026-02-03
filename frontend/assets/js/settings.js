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
  const fontUiFamilyEl      = document.getElementById("font-ui-family");
  const fontUiSizeEl        = document.getElementById("font-ui-size");
  const fontStoryFamilyEl   = document.getElementById("font-story-family");
  const fontStorySizeEl     = document.getElementById("font-story-size");
  const fontConsoleFamilyEl = document.getElementById("font-console-family");
  const fontConsoleSizeEl   = document.getElementById("font-console-size");
  const fontCharFamilyEl    = document.getElementById("font-char-family");
  const fontCharSizeEl      = document.getElementById("font-char-size");
  const fontWorldFamilyEl   = document.getElementById("font-world-family");
  const fontWorldSizeEl     = document.getElementById("font-world-size");
  const fontDungeonFamilyEl = document.getElementById("font-dungeon-family");
  const fontDungeonSizeEl   = document.getElementById("font-dungeon-size");

  const DEFAULT_FONT_SIZE = "14px";

  // 字体分区配置：对应 CSS 变量 & localStorage key
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
    // 1. 设置 Data Theme + 本地存储
    if (theme) {
      document.documentElement.setAttribute('data-theme', theme);
      localStorage.setItem('app_theme', theme);

      // 更新 UI 选择状态
      themeOptions.forEach(opt => {
        if (opt.dataset.value === theme) opt.classList.add('selected');
        else opt.classList.remove('selected');
      });
    }

    // 2. 设置 Background Class + 本地存储
    if (bg) {
      // 移除旧的 bg-* 类
      document.body.classList.forEach(cls => {
        if (cls.startsWith('bg-')) document.body.classList.remove(cls);
      });
      document.body.classList.add(`bg-${bg}`);
      localStorage.setItem('app_bg', bg);

      // 更新 UI 选择状态
      bgOptions.forEach(opt => {
        if (opt.dataset.value === bg) opt.classList.add('selected');
        else opt.classList.remove('selected');
      });
    }
  }

  // 单个分区：应用字体到 CSS 变量 + localStorage + 下拉框
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

  // 从设置 / localStorage / 默认值中综合应用 6 组字体
  function applyTypography(typographyConfig) {
    const cfg = typographyConfig || {};

    Object.keys(FONT_ZONES).forEach(zoneName => {
      const zone = FONT_ZONES[zoneName];
      if (!zone) return;

      const savedFamily =
        (cfg[zoneName] && cfg[zoneName].family) ||
        localStorage.getItem(zone.storageFamilyKey) ||
        (zone.familyEl && zone.familyEl.options.length
          ? zone.familyEl.options[0].value
          : "system-ui, -apple-system, 'Segoe UI', sans-serif");

      const savedSize =
        (cfg[zoneName] && cfg[zoneName].size) ||
        localStorage.getItem(zone.storageSizeKey) ||
        DEFAULT_FONT_SIZE;

      applyZoneFont(zoneName, savedFamily, savedSize);
    });
  }



  // --- 2. 交互逻辑：Tab 切换 ---
  function switchTab(targetId) {
    // 按钮状态
    tabButtons.forEach(btn => {
      if (btn.dataset.target === targetId) btn.classList.add('active');
      else btn.classList.remove('active');
    });
    // 面板显隐
    tabPanes.forEach(pane => {
      if (pane.id === targetId) pane.classList.add('active');
      else pane.classList.remove('active');
    });
  }

  // --- 3. 数据处理：填充表单 ---
  function populateForm(settings) {
    currentSettings = settings; // Cache
    const ui = settings.ui || {};

    // 统一通过 applyVisuals 应用主题和背景（内部会同步到 localStorage）
    applyVisuals(ui.theme || 'dark', ui.background || 'grid');

    // 应用字体分区设置
    applyTypography(ui.typography || {});

    
// 填充文本域
    postprocessingRulesEl.value = JSON.stringify(
      settings.text && settings.text.post_processing_rules ? settings.text.post_processing_rules : [],
      null, 2
    );

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
    // 获取当前选中的 theme 和 bg
    const activeThemeEl = document.querySelector('#theme-grid .visual-option.selected');
    const activeBgEl = document.querySelector('#bg-grid .visual-option.selected');

    const themeVal = activeThemeEl ? activeThemeEl.dataset.value : 'dark';
    const bgVal = activeBgEl ? activeBgEl.dataset.value : 'grid';

    // JSON 安全解析助手
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
      return null; // 停止保存
    }

    // 收集字体分区配置
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
    if (!settings) return; // JSON 错误已弹窗

    // 在前端立即应用主题 / 背景 / 字体（会同时写入 localStorage）
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
    // Tabs
    tabButtons.forEach(btn => {
      btn.addEventListener('click', () => switchTab(btn.dataset.target));
    });

    // Visual Selectors (Theme)
    themeOptions.forEach(opt => {
      opt.addEventListener('click', () => {
        applyVisuals(opt.dataset.value, null); // 仅切换主题
      });
    });

    // Visual Selectors (Background)
    bgOptions.forEach(opt => {
      opt.addEventListener('click', () => {
        applyVisuals(null, opt.dataset.value); // 仅切换背景
      });
    });

    // 字体：系统界面
    if (fontUiFamilyEl) {
      fontUiFamilyEl.addEventListener('change', () => {
        applyZoneFont('ui', fontUiFamilyEl.value, null);
      });
    }
    if (fontUiSizeEl) {
      fontUiSizeEl.addEventListener('change', () => {
        applyZoneFont('ui', null, fontUiSizeEl.value);
      });
    }

    // 字体：剧情正文
    if (fontStoryFamilyEl) {
      fontStoryFamilyEl.addEventListener('change', () => {
        applyZoneFont('story', fontStoryFamilyEl.value, null);
      });
    }
    if (fontStorySizeEl) {
      fontStorySizeEl.addEventListener('change', () => {
        applyZoneFont('story', null, fontStorySizeEl.value);
      });
    }

    // 字体：叙事控制台
    if (fontConsoleFamilyEl) {
      fontConsoleFamilyEl.addEventListener('change', () => {
        applyZoneFont('console', fontConsoleFamilyEl.value, null);
      });
    }
    if (fontConsoleSizeEl) {
      fontConsoleSizeEl.addEventListener('change', () => {
        applyZoneFont('console', null, fontConsoleSizeEl.value);
      });
    }

    // 字体：角色详情
    if (fontCharFamilyEl) {
      fontCharFamilyEl.addEventListener('change', () => {
        applyZoneFont('character', fontCharFamilyEl.value, null);
      });
    }
    if (fontCharSizeEl) {
      fontCharSizeEl.addEventListener('change', () => {
        applyZoneFont('character', null, fontCharSizeEl.value);
      });
    }

    // 字体：世界书内容预览
    if (fontWorldFamilyEl) {
      fontWorldFamilyEl.addEventListener('change', () => {
        applyZoneFont('world', fontWorldFamilyEl.value, null);
      });
    }
    if (fontWorldSizeEl) {
      fontWorldSizeEl.addEventListener('change', () => {
        applyZoneFont('world', null, fontWorldSizeEl.value);
      });
    }

    // 字体：副本预览
    if (fontDungeonFamilyEl) {
      fontDungeonFamilyEl.addEventListener('change', () => {
        applyZoneFont('dungeon', fontDungeonFamilyEl.value, null);
      });
    }
    if (fontDungeonSizeEl) {
      fontDungeonSizeEl.addEventListener('change', () => {
        applyZoneFont('dungeon', null, fontDungeonSizeEl.value);
      });
    }

    // Buttons
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