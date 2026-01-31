(function () {
  const themeSelect = document.getElementById("theme-select");
  const backgroundSelect = document.getElementById("background-select");
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
  const loadBtn = document.getElementById("settings-load-btn");
  const saveBtn = document.getElementById("settings-save-btn");
  const statusEl = document.getElementById("settings-status");

  function applyTheme(theme) {
    if (theme === "light") {
      document.documentElement.style.setProperty("--bg-main", "#f5f7ff");
      document.documentElement.style.setProperty("--bg-elevated", "#ffffff");
      document.documentElement.style.setProperty("--bg-elevated-alt", "#f0f3ff");
      document.documentElement.style.setProperty("--text-primary", "#151824");
      document.documentElement.style.setProperty("--text-secondary", "#6b7085");
    } else {
      document.documentElement.style.removeProperty("--bg-main");
      document.documentElement.style.removeProperty("--bg-elevated");
      document.documentElement.style.removeProperty("--bg-elevated-alt");
      document.documentElement.style.removeProperty("--text-primary");
      document.documentElement.style.removeProperty("--text-secondary");
    }
  }

  function populateForm(settings) {
    const ui = settings.ui || {};
    themeSelect.value = ui.theme || "dark";
    backgroundSelect.value = ui.background || "grid";
    postprocessingRulesEl.value = JSON.stringify(
      settings.text && settings.text.post_processing_rules
        ? settings.text.post_processing_rules
        : [],
      null,
      2
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

    applyTheme(themeSelect.value);
  }

  function collectForm() {
    let postRules = [];
    let ragConfig = {};
    let defaultProfiles = {};
    try {
      postRules = postprocessingRulesEl.value.trim()
        ? JSON.parse(postprocessingRulesEl.value)
        : [];
    } catch (e) {
      statusEl.textContent = "正文正则规则 JSON 解析失败。";
    }
    try {
      ragConfig = summaryRagConfigEl.value.trim()
        ? JSON.parse(summaryRagConfigEl.value)
        : {};
    } catch (e) {
      statusEl.textContent = "RAG 配置 JSON 解析失败。";
    }
    try {
      defaultProfiles = defaultProfilesEl.value.trim()
        ? JSON.parse(defaultProfilesEl.value)
        : {};
    } catch (e) {
      statusEl.textContent = "默认 Profile 映射 JSON 解析失败。";
    }

    const settings = {
      ui: {
        theme: themeSelect.value,
        background: backgroundSelect.value
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

    return settings;
  }

  async function loadSettings() {
    statusEl.textContent = "正在从后端加载设置...";
    try {
      const resp = await fetch("/api/settings/global");
      if (!resp.ok) {
        throw new Error("HTTP " + resp.status);
      }
      const data = await resp.json();
      populateForm(data);
      statusEl.textContent = "已加载。";
    } catch (err) {
      console.error(err);
      statusEl.textContent = "加载失败：" + err.message;
    }
  }

  async function saveSettings() {
    const settings = collectForm();
    statusEl.textContent = "正在保存设置...";
    try {
      const resp = await fetch("/api/settings/global", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(settings)
      });
      if (!resp.ok) {
        const t = await resp.text();
        throw new Error("HTTP " + resp.status + " " + t);
      }
      statusEl.textContent = "保存成功。";
    } catch (err) {
      console.error(err);
      statusEl.textContent = "保存失败：" + err.message;
    }
  }

  function bindEvents() {
    loadBtn.addEventListener("click", function () {
      loadSettings();
    });
    saveBtn.addEventListener("click", function () {
      saveSettings();
    });
    themeSelect.addEventListener("change", function () {
      applyTheme(themeSelect.value);
    });
  }

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
