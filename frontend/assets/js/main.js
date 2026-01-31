(function () {
  const storyLogEl = document.getElementById("story-log");
  const generateBtn = document.getElementById("generate-btn");
  const userInputEl = document.getElementById("user-input");
  const inputStatusEl = document.getElementById("input-status");
  const sessionLabelEl = document.getElementById("session-label");
  const newSessionBtn = document.getElementById("new-session-btn");

  const statWordsEl = document.getElementById("stat-words");
  const statDurationEl = document.getElementById("stat-duration");
  const statDurationFrontEl = document.getElementById("stat-duration-front");
  const statTotalWordsEl = document.getElementById("stat-total-words");

  const dungeonNameEl = document.getElementById("dungeon-name");
  const dungeonNodeNameEl = document.getElementById("dungeon-node-name");
  const dungeonProgressEl = document.getElementById("dungeon-progress");

  const characterSummaryEl = document.getElementById("character-summary");
  const variableSummaryEconomyEl = document.getElementById("var-economy");
  const variableSummaryAbilityEl = document.getElementById("var-ability");
  const variableSummaryFactionEl = document.getElementById("var-faction");

  let currentSessionId = null;
  let totalWordCount = 0;

  function ensureSession() {
    const cached = window.localStorage.getItem("novel_session_id");
    if (cached) {
      currentSessionId = cached;
    } else {
      currentSessionId = generateSessionId();
      window.localStorage.setItem("novel_session_id", currentSessionId);
    }
    updateSessionLabel();
  }

  function generateSessionId() {
    const rand = Math.floor(Math.random() * 1e6);
    return "S_" + Date.now().toString() + "_" + rand.toString();
  }

  function resetSession() {
    currentSessionId = generateSessionId();
    window.localStorage.setItem("novel_session_id", currentSessionId);
    totalWordCount = 0;
    statTotalWordsEl.textContent = "0";
    storyLogEl.innerHTML = "";
    updateSessionLabel();
    inputStatusEl.textContent = "已创建新会话。";
  }

  function updateSessionLabel() {
    if (!sessionLabelEl) return;
    sessionLabelEl.textContent = "当前会话 ID：" + currentSessionId;
  }

  function appendStoryBlock(text, meta, type) {
    const block = document.createElement("div");
    block.className = "story-block" + (type === "user" ? " story-block-user" : "");

    const metaEl = document.createElement("div");
    metaEl.className = "story-meta";
    if (type === "user") {
      metaEl.textContent = "玩家输入";
    } else {
      const tags = (meta && meta.tags && meta.tags.length) ? " · " + meta.tags.join(", ") : "";
      const tone = meta && meta.tone ? "基调：" + meta.tone : "";
      const pacing = meta && meta.pacing ? "节奏：" + meta.pacing : "";
      const infoParts = [];
      if (tone) infoParts.push(tone);
      if (pacing) infoParts.push(pacing);
      metaEl.textContent = infoParts.join(" · ") + tags;
    }

    const textEl = document.createElement("div");
    textEl.className = "story-text";
    textEl.textContent = text;

    block.appendChild(metaEl);
    block.appendChild(textEl);
    storyLogEl.appendChild(block);

    storyLogEl.scrollTop = storyLogEl.scrollHeight;
  }

  async function generateStory() {
    const userText = userInputEl.value.trim();
    if (!userText) {
      inputStatusEl.textContent = "请输入内容。";
      return;
    }
    if (!currentSessionId) {
      ensureSession();
    }

    appendStoryBlock(userText, null, "user");
    userInputEl.value = "";
    inputStatusEl.textContent = "正在向后端请求剧情...";

    generateBtn.disabled = true;

    const frontStart = performance.now();

    try {
      const resp = await fetch("/api/story/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: currentSessionId,
          user_input: userText
        })
      });

      const frontEnd = performance.now();
      const durationFrontMs = Math.round(frontEnd - frontStart);

      if (!resp.ok) {
        const text = await resp.text();
        throw new Error("请求失败：" + text);
      }

      const data = await resp.json();

      appendStoryBlock(data.story || "", data.meta || {}, "story");

      const meta = data.meta || {};
      const wordCount = meta.word_count || (data.story ? data.story.length : 0);
      const durationMs = meta.duration_ms || 0;
      totalWordCount += wordCount;

      statWordsEl.textContent = String(wordCount);
      statDurationEl.textContent = durationMs + " ms";
      statDurationFrontEl.textContent = durationFrontMs + " ms";
      statTotalWordsEl.textContent = String(totalWordCount);

      inputStatusEl.textContent = "已生成新剧情。";

      updateSidebarFromMeta(meta);
      refreshSessionSummary();
    } catch (err) {
      console.error(err);
      inputStatusEl.textContent = "请求出错：" + err.message;
    } finally {
      generateBtn.disabled = false;
    }
  }

  function updateSidebarFromMeta(meta) {
    if (!meta) return;
    if (meta.dungeon_name && dungeonNameEl) {
      dungeonNameEl.textContent = meta.dungeon_name;
    }
    if (meta.dungeon_node_name && dungeonNodeNameEl) {
      dungeonNodeNameEl.textContent = meta.dungeon_node_name;
    }
    if (meta.dungeon_progress_hint && dungeonProgressEl) {
      dungeonProgressEl.textContent = meta.dungeon_progress_hint;
    }
    if (meta.main_character && variableSummaryAbilityEl) {
      if (meta.main_character.ability_tier) {
        variableSummaryAbilityEl.textContent = meta.main_character.ability_tier;
      }
      if (meta.main_character.economy_summary && variableSummaryEconomyEl) {
        variableSummaryEconomyEl.textContent = meta.main_character.economy_summary;
      }
    }
  }

  async function refreshSessionSummary() {
    if (!currentSessionId) return;
    try {
      const resp = await fetch("/api/session/summary?session_id=" + encodeURIComponent(currentSessionId));
      if (!resp.ok) return;
      const data = await resp.json();

      if (data.dungeon) {
        if (dungeonNameEl) dungeonNameEl.textContent = data.dungeon.name || "未命名";
        if (dungeonNodeNameEl) dungeonNodeNameEl.textContent = data.dungeon.current_node_name || "未知";
        if (dungeonProgressEl) dungeonProgressEl.textContent = data.dungeon.progress_hint || "未知";
      }

      if (data.characters && Array.isArray(data.characters) && data.characters.length) {
        characterSummaryEl.innerHTML = "";
        data.characters.forEach(function (ch) {
          const line = document.createElement("div");
          line.textContent = ch.character_id + " · " + (ch.name || "") + " · " + (ch.ability_tier || "");
          characterSummaryEl.appendChild(line);
        });
      }

      if (data.variables && data.variables.main_character) {
        const v = data.variables.main_character;
        if (v.economy_summary && variableSummaryEconomyEl) {
          variableSummaryEconomyEl.textContent = v.economy_summary;
        }
        if (v.ability_summary && variableSummaryAbilityEl) {
          variableSummaryAbilityEl.textContent = v.ability_summary;
        }
      }

      if (data.variables && data.variables.faction_summary && variableSummaryFactionEl) {
        variableSummaryFactionEl.textContent = data.variables.faction_summary;
      }
    } catch (err) {
      console.warn("刷新会话摘要失败：", err);
    }
  }

  function bindEvents() {
    generateBtn.addEventListener("click", generateStory);
    userInputEl.addEventListener("keydown", function (e) {
      if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
        e.preventDefault();
        generateStory();
      }
    });
    newSessionBtn.addEventListener("click", function () {
      resetSession();
    });
  }

  function init() {
    ensureSession();
    bindEvents();
    refreshSessionSummary();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
