// assets/js/main.js
(function () {
  // =========================================
  // 1. DOM 元素获取
  // =========================================
  const storyLogEl = document.getElementById("story-log");
  const generateBtn = document.getElementById("generate-btn");
  const userInputEl = document.getElementById("user-input");
  const inputStatusEl = document.getElementById("input-status");

  const actionHistoryEl = document.getElementById("action-history");

  // 输入栏相关元素
  const inputBarEl = document.getElementById("input-bar");
  const inputCollapseToggleEl = document.getElementById("input-collapse-toggle"); // 左上角收起按钮
  const inputSizeToggleEl = document.getElementById("input-size-toggle");         // 右下角半屏按钮
  const actionSuggestionsEl = document.getElementById("action-suggestions");
  const actionSuggestionsToggleEl = document.getElementById("action-suggestions-toggle");

  // 实时计时器元素
  const storyTimerEl = document.getElementById("story-timer");
  const timerFrontendEl = document.getElementById("timer-frontend");
  const timerBackendEl = document.getElementById("timer-backend");

  // 右侧面板元素
  const dungeonNameEl = document.getElementById("dungeon-name");
  const dungeonNodeNameEl = document.getElementById("dungeon-node-name");
  const dungeonProgressEl = document.getElementById("dungeon-progress");

  const characterSummaryEl = document.getElementById("character-summary");
  const variableSummaryEconomyEl = document.getElementById("var-economy");
  const variableSummaryAbilityEl = document.getElementById("var-ability");
  const variableSummaryFactionEl = document.getElementById("var-faction");

  // =========================================
  // 2. SVG 图标定义 (用于 JS 动态切换)
  // =========================================

  // 半屏模式图标：四角向外 (展开)
  const iconExpandFull = `
    <svg viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7"/>
    </svg>`;

  // 半屏模式图标：四角向里 (收起/还原)
  const iconCollapseFull = `
    <svg viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M4 14h6v6M20 10h-6V4M14 10l7-7M10 14L3 21"/>
    </svg>`;

  // 底部栏折叠按钮：向下箭头 (收起)
  const iconChevronDown = `
    <svg viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <polyline points="6 9 12 15 18 9"></polyline>
    </svg>`;

  // 底部栏折叠按钮：向上箭头 (展开)
  const iconChevronUp = `
    <svg viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <polyline points="18 15 12 9 6 15"></polyline>
    </svg>`;

  // =========================================
  // 3. 状态变量
  // =========================================
  let currentSessionId = null;
  let totalWordCount = 0;
  let postprocessingRules = [];
  let regexConfig = {};

  // =========================================
  // 4. 会话管理逻辑
  // =========================================
  function generateSessionId() {
    const now = Date.now();
    const randomPart = Math.floor(Math.random() * 1e6)
      .toString()
      .padStart(6, "0");
    return "S_" + now + "_" + randomPart;
  }

  function ensureSession() {
    let savedId = window.localStorage.getItem("storyteller_session_id");
    if (!savedId) {
      savedId = generateSessionId();
      window.localStorage.setItem("storyteller_session_id", savedId);
    }
    currentSessionId = savedId;
    updateCurrentSaveDisplay(null, currentSessionId);
    ensureSessionInDB(currentSessionId);
  }

  async function ensureSessionInDB(sessionId) {
    try {
      const response = await fetch('/api/story/saves/detail?session_id=' + encodeURIComponent(sessionId));
      const data = await response.json();
      if (data.display_name && data.display_name !== sessionId) {
        updateCurrentSaveDisplay(data.display_name, sessionId);
      }
    } catch (err) {
      console.log('Session not in DB, will be created on first save');
    }
  }

  function resetSession() {
    currentSessionId = generateSessionId();
    window.localStorage.setItem("storyteller_session_id", currentSessionId);
    totalWordCount = 0;

    if (statTotalWordsEl) statTotalWordsEl.textContent = "0";
    if (storyLogEl) storyLogEl.innerHTML = "";

    updateCurrentSaveDisplay(null, currentSessionId);

    if (inputStatusEl) inputStatusEl.textContent = "已创建新存档。";

    if (actionHistoryEl) {
      actionHistoryEl.innerHTML = "";
      const placeholder = document.createElement("div");
      placeholder.className = "muted";
      placeholder.textContent = "暂无历史行动，等待你的第一次指令。";
      actionHistoryEl.appendChild(placeholder);
    }
  }

  function updateSessionLabel() {
    updateCurrentSaveDisplay(null, currentSessionId);
  }

  // =========================================
  // 5. UI 更新辅助函数
  // =========================================
  function appendStoryBlock(text, meta, type, stats, isLatest) {
    if (!storyLogEl) return;

    const block = document.createElement("div");
    block.className = "story-block" + (type === "user" ? " story-block-user" : " story-block-assistant");

    const metaEl = document.createElement("div");
    metaEl.className = "story-meta";
    if (type === "user") {
      metaEl.textContent = "用户输入";
    } else {
      const tags =
        meta && meta.tags && meta.tags.length ? " · " + meta.tags.join(", ") : "";
      const tone = meta && meta.tone ? "基调：" + meta.tone : "";
      const pacing = meta && meta.pacing ? "节奏：" + meta.pacing : "";
      const infoParts = [];
      if (tone) infoParts.push(tone);
      if (pacing) infoParts.push(pacing);
      metaEl.textContent = infoParts.join(" · ") + tags;
    }

    block.appendChild(metaEl);

    // 处理文本内容
    const processedText = extractMainContent(text);
    const thinkingText = extractThinking(text);
    const summaryText = extractSummary(text);

    // 添加思考过程（放在正文前面，默认折叠）
    if (thinkingText) {
      const thinkingContainer = document.createElement("div");
      thinkingContainer.className = "story-thinking-container";
      thinkingContainer.style.cssText = "margin-bottom: 8px;";
      
      const thinkingHeader = document.createElement("button");
      thinkingHeader.className = "thinking-toggle";
      thinkingHeader.style.cssText = "background: none; border: none; padding: 4px 8px; cursor: pointer; font-size: 11px; color: var(--text-secondary); display: flex; align-items: center; gap: 4px;";
      thinkingHeader.innerHTML = '<span class="toggle-icon">▶</span>';
      
      const toggleText = document.createElement("span");
      toggleText.className = "toggle-text";
      toggleText.textContent = "思考过程";
      thinkingHeader.appendChild(toggleText);
      
      const thinkingContent = document.createElement("div");
      thinkingContent.className = "story-thinking";
      thinkingContent.style.cssText = "margin-top: 4px; padding: 8px 12px; background: rgba(0,0,0,0.05); border-radius: 8px; color: var(--text-secondary); font-style: italic; display: none;";
      thinkingContent.textContent = thinkingText;
      
      thinkingHeader.addEventListener('click', function() {
        const isExpanded = thinkingContent.style.display === 'block';
        thinkingContent.style.display = isExpanded ? 'none' : 'block';
        thinkingHeader.querySelector('.toggle-icon').textContent = isExpanded ? '▶' : '▼';
      });
      
      thinkingContainer.appendChild(thinkingHeader);
      thinkingContainer.appendChild(thinkingContent);
      block.appendChild(thinkingContainer);
    }
    
    // 正文内容
    const textEl = document.createElement("div");
    textEl.className = "story-text";
    
    // 按段落分割并创建p元素，使首行缩进对每段生效
    const paragraphs = processedText.split(/\n+/);
    paragraphs.forEach(function(para) {
      if (para.trim()) {
        const p = document.createElement("p");
        p.textContent = para.trim();
        p.style.margin = "0 0 0.8em 0";
        textEl.appendChild(p);
      }
    });
    
    // 如果没有段落，直接设置文本
    if (textEl.children.length === 0) {
      textEl.textContent = processedText;
    }
    
    block.appendChild(textEl);

    // 添加内容总结（如果有，放在正文后面）
    if (summaryText) {
      const summaryEl = document.createElement("div");
      summaryEl.className = "story-summary";
      summaryEl.style.cssText = "margin-top: 8px; padding: 8px 12px; background: rgba(0,0,0,0.05); border-radius: 8px; color: var(--text-secondary); border-left: 3px solid var(--accent);";
      summaryEl.textContent = "📝 " + summaryText;
      block.appendChild(summaryEl);
    }

    // 添加"查看原文"链接和统计信息
    if (type !== "user" && text) {
      const footerEl = document.createElement("div");
      footerEl.className = "story-footer";
      footerEl.style.cssText = "display: flex; align-items: center; flex-wrap: wrap; gap: 8px; margin-top: 8px;";

      const rawTextLink = document.createElement("button");
      rawTextLink.className = "raw-text-link";
      rawTextLink.style.cssText = "background: none; border: none; padding: 4px 8px; cursor: pointer; font-size: 11px; color: var(--accent); text-decoration: underline; opacity: 0.7;";
      rawTextLink.textContent = "查看原文";
      rawTextLink.addEventListener('click', function() {
        showRawTextModal(text);
      });
      footerEl.appendChild(rawTextLink);

      // 添加统计信息
      if (stats) {
        const statsEl = document.createElement("span");
        statsEl.className = "story-stats";
        
        const wordCount = stats.paragraph_word_count || 0;
        const cumulativeCount = stats.cumulative_word_count || 0;
        const frontDuration = stats.frontend_duration || 0;
        const backDuration = stats.backend_duration || 0;

        statsEl.innerHTML = 
          '<span class="story-stats-item">本段字数：' + wordCount + '</span>' +
          '<span class="story-stats-divider">|</span>' +
          '<span class="story-stats-item">累计字数：' + cumulativeCount + '</span>' +
          '<span class="story-stats-divider">|</span>' +
          '<span class="story-stats-item">前端耗时：' + formatDuration(frontDuration) + '</span>' +
          '<span class="story-stats-divider">|</span>' +
          '<span class="story-stats-item">后端耗时：' + formatDuration(backDuration) + '</span>';
        
        footerEl.appendChild(statsEl);
      }

      block.appendChild(footerEl);
    }

    storyLogEl.appendChild(block);

    // 只从最新一条记录提取并更新行动选项
    if (type !== "user" && isLatest) {
      const actionOptions = extractActionOptions(text);
      if (actionOptions.length > 0) {
        updateActionSuggestions(actionOptions);
      } else {
        clearActionSuggestions();
      }
    }

    // 自动滚动到底部
    storyLogEl.scrollTop = storyLogEl.scrollHeight;
  }

  // 显示原文模态框
  function showRawTextModal(text) {
    // 移除已存在的模态框
    const existingModal = document.getElementById('raw-text-modal');
    if (existingModal) {
      existingModal.remove();
    }

    // 创建模态框
    const modal = document.createElement('div');
    modal.id = 'raw-text-modal';
    modal.style.cssText = 'position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 10000; display: flex; justify-content: center; align-items: center;';

    const modalContent = document.createElement('div');
    modalContent.style.cssText = 'background: var(--bg-elevated); border-radius: 12px; padding: 20px; max-width: 80%; max-height: 80%; width: 800px; display: flex; flex-direction: column; box-shadow: 0 10px 40px rgba(0,0,0,0.5);';

    const modalHeader = document.createElement('div');
    modalHeader.style.cssText = 'display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid var(--border-soft);';
    modalHeader.innerHTML = '<h3 style="margin: 0; color: var(--text-primary);">原文内容</h3>';

    const closeBtn = document.createElement('button');
    closeBtn.textContent = '×';
    closeBtn.style.cssText = 'background: none; border: none; font-size: 24px; cursor: pointer; color: var(--text-secondary); padding: 0; line-height: 1;';
    closeBtn.addEventListener('click', function() {
      modal.remove();
    });
    modalHeader.appendChild(closeBtn);

    const textContent = document.createElement('pre');
    textContent.className = 'raw-text-content';
    textContent.style.cssText = 'flex: 1; overflow: auto; margin: 0; padding: 16px; background: var(--bg-primary); border-radius: 8px; line-height: 1.6; white-space: pre-wrap; word-wrap: break-word; color: var(--text-primary);';
    textContent.textContent = text;

    modalContent.appendChild(modalHeader);
    modalContent.appendChild(textContent);
    modal.appendChild(modalContent);
    document.body.appendChild(modal);

    // 点击背景关闭
    modal.addEventListener('click', function(e) {
      if (e.target === modal) {
        modal.remove();
      }
    });

    // ESC键关闭
    document.addEventListener('keydown', function escHandler(e) {
      if (e.key === 'Escape') {
        modal.remove();
        document.removeEventListener('keydown', escHandler);
      }
    });
  }

  // 提取正文部分，过滤掉思考过程和行动选项
  function extractMainContent(text) {
    if (!text) return "";
    
    // 使用正则表达式匹配标签，更健壮地处理各种格式
    const bodyMatch = text.match(/<正文部分>([\s\S]*?)<\/正文部分>/);
    
    let mainContent = text;
    
    if (bodyMatch && bodyMatch[1]) {
      mainContent = bodyMatch[1];
    } else {
      const thinkingStart = text.indexOf('<思考过程>');
      if (thinkingStart > -1) {
        mainContent = text.substring(0, thinkingStart);
      } else {
        const contentCheckIndex = text.indexOf('<!-- content check:');
        mainContent = contentCheckIndex > -1 ? text.substring(0, contentCheckIndex) : text;
      }
    }
    
    // 清理残留的标签
    mainContent = mainContent
      .replace(/<\/?正文部分>/g, '')
      .replace(/<\/?思考过程>/g, '')
      .replace(/<\/?内容总结>/g, '')
      .replace(/<\/?行动选项>/g, '');
    
    // 应用后处理规则
    return applyPostprocessingRules(mainContent, postprocessingRules);
  }

  // 提取思考过程
  function extractThinking(text) {
    if (!text) return "";
    
    const thinkingMatch = text.match(/<思考过程>([\s\S]*?)<\/思考过程>/);
    if (thinkingMatch && thinkingMatch[1]) {
      return thinkingMatch[1];
    }
    
    // 兼容旧格式
    const contentCheckIndex = text.indexOf('<!-- content check:');
    if (contentCheckIndex > -1) {
      const optionsStart = text.indexOf('<行动选项>');
      const endIndex = optionsStart > -1 ? optionsStart : text.length;
      return text.substring(contentCheckIndex + 17, endIndex);
    }
    
    return "";
  }

  // 提取内容总结
  function extractSummary(text) {
    if (!text) return "";
    
    const summaryMatch = text.match(/<内容总结>([\s\S]*?)<\/内容总结>/);
    if (summaryMatch && summaryMatch[1]) {
      return summaryMatch[1];
    }
    
    return "";
  }

  // 获取后处理正则规则
  async function initPostprocessingRules() {
    try {
      const response = await fetch('/regex/active');
      if (response.ok) {
        const data = await response.json();
        regexConfig = data.config || {};
      }
    } catch (error) {
      console.warn('Failed to load regex config:', error);
    }
  }

  // 应用正则化规则处理文本
  function applyRegexRules(text, section) {
    if (!text || !regexConfig || !regexConfig.root) return text;
    
    let result = text;
    
    function processNode(node) {
      if (!node || node.enabled === false) return;
      
      if (node.kind === 'regex' && node.pattern) {
        const applyTo = node.apply_to || 'body';
        if (applyTo === 'all' || applyTo === section) {
          try {
            const regex = new RegExp(node.pattern, 'g');
            if (node.extract_group && node.extract_group > 0) {
              const match = regex.exec(result);
              if (match && match[node.extract_group]) {
                result = match[node.extract_group];
              }
            } else if (node.replacement !== undefined) {
              result = result.replace(regex, node.replacement);
            }
          } catch (error) {
            console.warn('Invalid regex rule:', node, error);
          }
        }
      }
      
      if (node.children && Array.isArray(node.children)) {
        node.children.forEach(processNode);
      }
    }
    
    processNode(regexConfig.root);
    return result;
  }

  // 应用后处理正则规则（旧版兼容）
  function applyPostprocessingRules(text, rules) {
    if (!text || !rules || !Array.isArray(rules)) return text;
    
    let processedText = text;
    
    rules.forEach(rule => {
      try {
        if (rule.pattern && rule.replacement !== undefined) {
          const regex = new RegExp(rule.pattern, 'g');
          processedText = processedText.replace(regex, rule.replacement);
        }
      } catch (error) {
        console.warn('Invalid regex rule:', rule, error);
      }
    });
    
    return processedText;
  }

  // 提取行动选项部分
  function extractActionOptions(text) {
    if (!text) return [];
    
    const optionsStart = text.indexOf('<行动选项>');
    const optionsEnd = text.indexOf('</行动选项>');
    
    if (optionsStart === -1 || optionsEnd === -1) {
      return [];
    }
    
    const optionsText = text.substring(optionsStart + 5, optionsEnd);
    const options = [];
    
    // 解析行动选项
    const lines = optionsText.split('\n');
    for (const line of lines) {
      const trimmedLine = line.trim();
      if (trimmedLine && trimmedLine.match(/^\d+:/)) {
        // 提取选项文本（去除数字和冒号）
        const optionText = trimmedLine.replace(/^\d+:/, '').trim();
        if (optionText) {
          options.push(optionText);
        }
      }
    }
    
    return options;
  }

  // 更新行动建议
  function updateActionSuggestions(options) {
    if (!actionSuggestionsEl) return;
    
    const suggestionsBody = document.getElementById('action-suggestions-body');
    if (!suggestionsBody) return;
    
    // 清空现有内容
    suggestionsBody.innerHTML = '';
    
    // 添加新的行动选项
    options.forEach((option, index) => {
      const chip = document.createElement('button');
      chip.type = 'button';
      chip.className = 'suggestion-chip';
      chip.setAttribute('data-suggest', option);
      chip.textContent = option;
      suggestionsBody.appendChild(chip);
    });
    
    // 重新绑定建议芯片的点击事件
    bindSuggestionChips();
  }

  // 清空行动建议
  function clearActionSuggestions() {
    if (!actionSuggestionsEl) return;
    
    const suggestionsBody = document.getElementById('action-suggestions-body');
    if (!suggestionsBody) return;
    
    suggestionsBody.innerHTML = '<div class="empty-suggestions" style="color: var(--text-secondary); font-size: 12px; padding: 8px; text-align: center;">暂无行动建议</div>';
  }

  function appendActionHistory(text) {
    if (!actionHistoryEl) return;

    const clean = text.trim();
    if (!clean) return;

    const firstChild = actionHistoryEl.firstElementChild;
    if (firstChild && firstChild.classList && firstChild.classList.contains("muted")) {
      actionHistoryEl.innerHTML = "";
    }

    const item = document.createElement("div");
    item.className = "action-history-item";
    item.textContent = clean;
    actionHistoryEl.appendChild(item);

    actionHistoryEl.scrollTop = actionHistoryEl.scrollHeight;
  }

  // =========================================
  // 6. 核心生成逻辑 (Fetch API)
  // =========================================
  async function generateStory() {
    if (!userInputEl) return;

    const userText = userInputEl.value.trim();
    if (!userText) {
      if (inputStatusEl) inputStatusEl.textContent = "请输入内容。";
      return;
    }
    if (!currentSessionId) {
      ensureSession();
    }

    // 提取行动选项并更新到建议区域
    const actionOptions = extractActionOptions(userText);
    if (actionOptions.length > 0) {
      updateActionSuggestions(actionOptions);
    }

    appendStoryBlock(userText, null, "user");
    appendActionHistory(userText);
    userInputEl.value = "";
    if (inputStatusEl) {
      inputStatusEl.textContent = "正在向后端请求剧情...";
    }

    if (generateBtn) {
      generateBtn.disabled = true;
    }

    // 发送后自动最小化输入栏
    if (inputBarEl && !inputBarEl.classList.contains("input-bar--collapsed")) {
      inputBarEl.classList.add("input-bar--collapsed");
      if (inputCollapseToggleEl) {
        inputCollapseToggleEl.innerHTML = iconChevronUp;
        inputCollapseToggleEl.setAttribute("aria-label", "展开输入栏");
      }
    }

    // 尝试使用流式生成，失败则回退到非流式
    try {
      await generateStoryStream(userText);
    } catch (err) {
      console.warn("流式生成失败，回退到非流式:", err);
      await generateStoryNonStream(userText);
    }
  }

  // 流式生成实现
  async function generateStoryStream(userText) {
    const frontStart = performance.now();
    let updateInterval;
    let storyText = "";
    let metaData = {};
    let backendDuration = 0;

    try {
      // 显示实时计时器
      if (storyTimerEl) {
        storyTimerEl.style.display = 'flex';
      }

      // 启动实时更新计时器
      updateInterval = setInterval(() => {
        const currentTime = performance.now();
        const durationFrontMs = currentTime - frontStart;
        if (timerFrontendEl) {
          timerFrontendEl.textContent = formatDuration(durationFrontMs);
        }
        if (timerBackendEl && backendDuration > 0) {
          timerBackendEl.textContent = formatDuration(backendDuration);
        }
      }, 100); // 每100ms更新一次

      const resp = await fetch("/api/story/generate_stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: currentSessionId,
          user_input: userText
        })
      });

      if (!resp.ok) {
        const text = await resp.text();
        throw new Error("请求失败：" + text);
      }

      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        
        // 处理SSE事件
        const lines = buffer.split("\n\n");
        for (let i = 0; i < lines.length - 1; i++) {
          const line = lines[i];
          if (!line) continue;

          const eventMatch = line.match(/^event: (\w+)/m);
          const dataMatch = line.match(/^data: (.+)/ms);

          if (eventMatch && dataMatch) {
            const event = eventMatch[1];
            const dataStr = dataMatch[1];

            try {
              const data = JSON.parse(dataStr);

              if (event === "dev_log") {
                // 开发者日志信息
                if (window.DevTools && typeof window.DevTools.logRequest === 'function') {
                  window.DevTools.logRequest(data);
                }
              } else if (event === "meta") {
                metaData = data;
                if (data.duration_ms) {
                  backendDuration = data.duration_ms;
                }
              } else if (event === "delta") {
                storyText += data.text || "";
                // 实时更新故事内容
                appendStoryBlockIncremental(data.text || "");
              } else if (event === "done") {
                // 完成处理
                break;
              } else if (event === "error") {
                throw new Error(data.message || "流式生成错误");
              }
            } catch (parseErr) {
              console.warn("解析SSE数据失败:", parseErr);
            }
          }
        }

        buffer = lines[lines.length - 1];
      }

      const frontEnd = performance.now();
      const durationFrontMs = frontEnd - frontStart;

      // 提取正文部分并计算字数
      const mainStoryText = extractMainContent(storyText);
      const wordCount = mainStoryText.length;
      const durationMs = metaData.duration_ms || backendDuration || 0;
      totalWordCount += wordCount;

      if (inputStatusEl) inputStatusEl.textContent = "已生成新剧情。";

      updateSidebarFromMeta(metaData);
      refreshSessionSummary();
      
      // 流式输出完毕后，重新加载最近5条交互记录进行渲染
      await loadRecentSegments();

      // 更新前端耗时到数据库
      try {
        const recentResp = await fetch(
          "/api/story/recent?session_id=" + encodeURIComponent(currentSessionId) + "&limit=1"
        );
        if (recentResp.ok) {
          const recentData = await recentResp.json();
          if (recentData.segments && recentData.segments.length > 0) {
            const latestSegment = recentData.segments[0];
            await fetch("/api/story/update_frontend_duration", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                segment_id: latestSegment.segment_id,
                frontend_duration: durationFrontMs
              })
            });
            // 更新完成后重新加载显示
            await loadRecentSegments();
          }
        }
      } catch (updateErr) {
        console.warn("更新前端耗时失败:", updateErr);
      }

      // 隐藏实时计时器
      if (storyTimerEl) {
        storyTimerEl.style.display = 'none';
      }
    } catch (err) {
      console.error("流式生成错误:", err);
      throw err;
    } finally {
      // 清除更新计时器
      if (updateInterval) {
        clearInterval(updateInterval);
      }
      if (generateBtn) {
        generateBtn.disabled = false;
        userInputEl.focus(); // 聚焦回输入框
      }
    }
  }

  // 非流式生成实现（回退方案）
  async function generateStoryNonStream(userText) {
    const frontStart = performance.now();
    let updateInterval;

    try {
      // 显示实时计时器
      if (storyTimerEl) {
        storyTimerEl.style.display = 'flex';
      }

      // 启动实时更新计时器
      updateInterval = setInterval(() => {
        const currentTime = performance.now();
        const durationFrontMs = currentTime - frontStart;
        if (timerFrontendEl) {
          timerFrontendEl.textContent = formatDuration(durationFrontMs);
        }
      }, 100); // 每100ms更新一次

      const resp = await fetch("/api/story/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: currentSessionId,
          user_input: userText
        })
      });

      const frontEnd = performance.now();
      const durationFrontMs = frontEnd - frontStart;

      if (!resp.ok) {
        const text = await resp.text();
        throw new Error("请求失败：" + text);
      }

      const data = await resp.json();

      // 记录开发者日志
      if (data.dev_log_info && window.DevTools && typeof window.DevTools.logRequest === 'function') {
        window.DevTools.logRequest(data.dev_log_info);
      }

      appendStoryBlock(data.story || "", data.meta || {}, "story");

      const meta = data.meta || {};
      // 提取正文部分并计算字数
      const mainStoryText = extractMainContent(data.story || "");
      const wordCount = mainStoryText.length;
      const durationMs = meta.duration_ms || 0;
      totalWordCount += wordCount;

      if (inputStatusEl) inputStatusEl.textContent = "已生成新剧情。";

      updateSidebarFromMeta(meta);
      refreshSessionSummary();

      // 更新前端耗时到数据库
      if (data.segment_id) {
        try {
          await fetch("/api/story/update_frontend_duration", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              segment_id: data.segment_id,
              frontend_duration: durationFrontMs
            })
          });
          // 更新完成后重新加载显示
          await loadRecentSegments();
        } catch (updateErr) {
          console.warn("更新前端耗时失败:", updateErr);
        }
      }

      // 隐藏实时计时器
      if (storyTimerEl) {
        storyTimerEl.style.display = 'none';
      }
    } catch (err) {
      console.error(err);
      if (inputStatusEl) inputStatusEl.textContent = "请求出错：" + err.message;
      throw err;
    } finally {
      // 清除更新计时器
      if (updateInterval) {
        clearInterval(updateInterval);
      }
      if (generateBtn) {
        generateBtn.disabled = false;
        userInputEl.focus(); // 聚焦回输入框
      }
    }
  }

  // 增量添加故事内容（用于流式显示）
  function appendStoryBlockIncremental(text) {
    if (!storyLogEl) return;

    let lastBlock = storyLogEl.lastElementChild;
    if (!lastBlock || !lastBlock.classList.contains("story-block")) {
      // 创建新的故事块
      lastBlock = document.createElement("div");
      lastBlock.className = "story-block";
      
      const metaEl = document.createElement("div");
      metaEl.className = "story-meta";
      metaEl.textContent = "AI 生成";
      
      const textEl = document.createElement("div");
      textEl.className = "story-text";
      textEl.textContent = text;
      
      lastBlock.appendChild(metaEl);
      lastBlock.appendChild(textEl);
      storyLogEl.appendChild(lastBlock);
    } else {
      // 更新现有故事块
      const textEl = lastBlock.querySelector(".story-text");
      if (textEl) {
        textEl.textContent += text;
      }
    }

    // 自动滚动到底部
    storyLogEl.scrollTop = storyLogEl.scrollHeight;
  }

  // 格式化时间为 XX.XXXs 格式
  function formatDuration(ms) {
    return (ms / 1000).toFixed(3) + "s";
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

    if (meta.main_character) {
      if (meta.main_character.ability_tier && variableSummaryAbilityEl) {
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
      const resp = await fetch(
        "/api/session/summary?session_id=" + encodeURIComponent(currentSessionId)
      );
      if (!resp.ok) return;
      const data = await resp.json();

      if (data.dungeon) {
        if (dungeonNameEl) dungeonNameEl.textContent = data.dungeon.name || "未命名";
        if (dungeonNodeNameEl)
          dungeonNodeNameEl.textContent = data.dungeon.current_node_name || "未知";
        if (dungeonProgressEl)
          dungeonProgressEl.textContent = data.dungeon.progress_hint || "未知";
      }

      if (data.characters && Array.isArray(data.characters) && data.characters.length) {
        if (characterSummaryEl) {
          characterSummaryEl.innerHTML = "";
          data.characters.forEach(function (ch) {
            const line = document.createElement("div");
            line.textContent =
              ch.character_id + " · " + (ch.name || "") + " · " + (ch.ability_tier || "");
            characterSummaryEl.appendChild(line);
          });
        }
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

  async function loadRecentSegments() {
    if (!currentSessionId || !storyLogEl) return;
    try {
      const resp = await fetch(
        "/api/story/recent?session_id=" + encodeURIComponent(currentSessionId) + "&limit=5"
      );
      if (!resp.ok) return;
      const data = await resp.json();

      if (data.segments && Array.isArray(data.segments) && data.segments.length > 0) {
        storyLogEl.innerHTML = "";
        
        const segmentsCount = data.segments.length;
        
        data.segments.forEach(function (segment, index) {
          if (segment.user_input) {
            appendStoryBlock(segment.user_input, null, "user");
          }
          const stats = {
            paragraph_word_count: segment.paragraph_word_count || 0,
            cumulative_word_count: segment.cumulative_word_count || 0,
            frontend_duration: segment.frontend_duration || 0,
            backend_duration: segment.backend_duration || 0
          };
          const isLatest = (index === segmentsCount - 1);
          appendStoryBlock(segment.text, null, "assistant", stats, isLatest);
        });
      } else {
        clearActionSuggestions();
      }
    } catch (err) {
      console.warn("加载最近故事片段失败：", err);
    }
  }

  // =========================================
  // 7. 交互事件绑定 (重点优化部分)
  // =========================================

  // (A) 绑定“下次行动建议”的展开/收起
  function bindActionSuggestionsToggle() {
    if (!actionSuggestionsEl || !actionSuggestionsToggleEl) return;

    actionSuggestionsToggleEl.addEventListener("click", function () {
      const isOpen = actionSuggestionsEl.classList.toggle("action-suggestions--open");

      // 更新文字提示，保持 "✨" 前缀
      if (isOpen) {
        actionSuggestionsToggleEl.textContent = "✨ 下次行动建议 (点击收起)";
      } else {
        actionSuggestionsToggleEl.textContent = "✨ 下次行动建议 (点击展开)";
      }
    });
  }

  // (B) 绑定点击建议 Chip 填入输入框
  function bindSuggestionChips() {
    if (!userInputEl) return;

    // 使用事件委托，或者重新获取DOM（如果Chips是动态生成的，这里假设是静态的）
    const chips = document.querySelectorAll(".suggestion-chip[data-suggest]");
    chips.forEach(function (chip) {
      chip.addEventListener("click", function () {
        // 获取完整句子
        const suggest = this.getAttribute("data-suggest") || this.textContent.trim();
        if (!suggest) return;

        // 简单的填入逻辑，如果输入框已有内容则换行追加
        if (!userInputEl.value) {
          userInputEl.value = suggest;
        } else {
          // 避免多次重复换行
          const prefix = userInputEl.value.trim();
          userInputEl.value = prefix + "\n" + suggest;
        }

        // 自动调整输入框高度并聚焦
        userInputEl.scrollTop = userInputEl.scrollHeight;
        userInputEl.focus();
      });
    });
  }

  // (C) 绑定底部输入栏的 折叠 与 半屏 逻辑
  function bindInputPanelEvents() {
    // 1. 左上角：折叠/展开 整个输入栏
    if (inputCollapseToggleEl && inputBarEl) {
      inputCollapseToggleEl.addEventListener("click", function () {
        const collapsed = inputBarEl.classList.toggle("input-bar--collapsed");

        // 【关键修复】：使用 innerHTML 替换 SVG，而不是 textContent
        inputCollapseToggleEl.innerHTML = collapsed ? iconChevronUp : iconChevronDown;
        inputCollapseToggleEl.setAttribute(
          "aria-label",
          collapsed ? "展开输入栏" : "收起输入栏"
        );

        // 如果在半屏模式下折叠，强制退出半屏，避免界面错乱
        if (collapsed && document.body.classList.contains("input-half-screen")) {
          document.body.classList.remove("input-half-screen");
          inputBarEl.classList.remove("input-bar--half-screen");

          if (inputSizeToggleEl) {
            // 重置半屏按钮图标为“展开”
            inputSizeToggleEl.innerHTML = iconExpandFull;
            inputSizeToggleEl.setAttribute("aria-label", "切换半屏模式");
            inputSizeToggleEl.setAttribute("title", "切换半屏专注模式");
          }
        }
      });
    }

    // 2. 右下角：切换 半屏/专注 模式
    if (inputSizeToggleEl && inputBarEl) {
      inputSizeToggleEl.addEventListener("click", function () {
        // 如果当前是折叠状态，先自动展开
        if (inputBarEl.classList.contains("input-bar--collapsed")) {
          inputBarEl.classList.remove("input-bar--collapsed");
          if (inputCollapseToggleEl) {
            inputCollapseToggleEl.innerHTML = iconChevronDown;
            inputCollapseToggleEl.setAttribute("aria-label", "收起输入栏");
          }
        }

        // 切换 Body 的 class
        const isHalf = document.body.classList.toggle("input-half-screen");

        // 【关键修复】：根据状态切换 SVG 图标
        if (isHalf) {
          inputBarEl.classList.add("input-bar--half-screen");
          inputSizeToggleEl.innerHTML = iconCollapseFull; // 显示“四角向内”
          inputSizeToggleEl.setAttribute("aria-label", "退出半屏模式");
          inputSizeToggleEl.setAttribute("title", "退出半屏专注模式");
        } else {
          inputBarEl.classList.remove("input-bar--half-screen");
          inputSizeToggleEl.innerHTML = iconExpandFull;   // 显示“四角向外”
          inputSizeToggleEl.setAttribute("aria-label", "切换半屏模式");
          inputSizeToggleEl.setAttribute("title", "切换半屏专注模式");
        }
      });
    }
  }

  function bindEvents() {
    if (generateBtn) {
      generateBtn.addEventListener("click", generateStory);
    }

    if (userInputEl) {
      userInputEl.addEventListener("keydown", function (e) {
        // Ctrl + Enter 快捷提交
        if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
          e.preventDefault();
          generateStory();
        }
      });
    }

    bindActionSuggestionsToggle();
    bindSuggestionChips();
    bindInputPanelEvents();
    bindFontSettingsModal();
    bindSubsectionToggles();
    bindPanelCollapse();
    
    window.onSaveLoaded = function(sessionId) {
      currentSessionId = sessionId;
      if (storyLogEl) {
        storyLogEl.innerHTML = '';
      }
      loadRecentSegments();
    };
  }

  // 子区块折叠/展开功能
  function bindSubsectionToggles() {
    const subsectionHeaders = document.querySelectorAll('.subsection-header');
    
    subsectionHeaders.forEach(function(header) {
      header.addEventListener('click', function() {
        const toggleId = this.getAttribute('data-toggle');
        const content = document.getElementById(toggleId);
        const icon = this.querySelector('.toggle-icon');
        
        if (content) {
          content.classList.toggle('collapsed');
        }
        if (icon) {
          icon.style.transform = content && content.classList.contains('collapsed') 
            ? 'rotate(-90deg)' 
            : 'rotate(0deg)';
        }
      });
    });
  }

  // 面板整体折叠功能
  function bindPanelCollapse() {
    const collapseBtns = document.querySelectorAll('.panel-collapse-btn');
    
    collapseBtns.forEach(function(btn) {
      btn.addEventListener('click', function(e) {
        e.stopPropagation();
        const panelType = this.getAttribute('data-panel');
        const panel = this.closest('.sidebar-section');
        const body = panel.querySelector('.sidebar-body');
        
        if (body) {
          body.classList.toggle('collapsed');
          this.classList.toggle('collapsed');
        }
      });
    });
  }

  // 字体设置弹窗相关逻辑
  function bindFontSettingsModal() {
    const fontSettingsBtn = document.getElementById('font-settings-btn');
    const fontSettingsModal = document.getElementById('font-settings-modal');
    const fontModalClose = document.getElementById('font-modal-close');
    const fontModalSave = document.getElementById('font-modal-save');
    const fontModalReset = document.getElementById('font-modal-reset');

    if (!fontSettingsModal) return;

    // 打开弹窗
    if (fontSettingsBtn) {
      fontSettingsBtn.addEventListener('click', function() {
        loadFontSettings();
        fontSettingsModal.style.display = 'flex';
      });
    }

    // 关闭弹窗
    if (fontModalClose) {
      fontModalClose.addEventListener('click', function() {
        fontSettingsModal.style.display = 'none';
      });
    }

    // 点击背景关闭
    fontSettingsModal.addEventListener('click', function(e) {
      if (e.target === fontSettingsModal) {
        fontSettingsModal.style.display = 'none';
      }
    });

    // 保存设置
    if (fontModalSave) {
      fontModalSave.addEventListener('click', function() {
        saveFontSettings();
        fontSettingsModal.style.display = 'none';
      });
    }

    // 重置默认
    if (fontModalReset) {
      fontModalReset.addEventListener('click', function() {
        resetFontSettings();
      });
    }
  }

  // 加载字体设置
  function loadFontSettings() {
    const zones = ['thinking', 'body', 'summary', 'raw', 'stats'];
    zones.forEach(function(zone) {
      const familyEl = document.getElementById('font-' + zone + '-family');
      const sizeEl = document.getElementById('font-' + zone + '-size');
      const boldEl = document.getElementById('font-' + zone + '-bold');
      
      if (familyEl) {
        const savedFamily = localStorage.getItem('app_font_' + zone + '_family');
        if (savedFamily) familyEl.value = savedFamily;
      }
      if (sizeEl) {
        const savedSize = localStorage.getItem('app_font_' + zone + '_size');
        if (savedSize) sizeEl.value = savedSize;
      }
      if (boldEl) {
        const savedBold = localStorage.getItem('app_font_' + zone + '_bold');
        boldEl.checked = savedBold === 'true';
      }
    });

    // 加载缩进设置
    const indentEl = document.getElementById('font-body-indent');
    if (indentEl) {
      const savedIndent = localStorage.getItem('app_font_body_indent');
      indentEl.checked = savedIndent === 'true';
    }
  }

  // 保存字体设置
  function saveFontSettings() {
    const zones = {
      thinking: { familyVar: '--font-thinking-family', sizeVar: '--font-thinking-size', boldVar: '--font-thinking-weight' },
      body: { familyVar: '--font-body-family', sizeVar: '--font-body-size', boldVar: '--font-body-weight' },
      summary: { familyVar: '--font-summary-family', sizeVar: '--font-summary-size', boldVar: '--font-summary-weight' },
      raw: { familyVar: '--font-raw-family', sizeVar: '--font-raw-size', boldVar: '--font-raw-weight' },
      stats: { familyVar: '--font-stats-family', sizeVar: '--font-stats-size', boldVar: '--font-stats-weight' }
    };

    Object.keys(zones).forEach(function(zone) {
      const familyEl = document.getElementById('font-' + zone + '-family');
      const sizeEl = document.getElementById('font-' + zone + '-size');
      const boldEl = document.getElementById('font-' + zone + '-bold');
      
      if (familyEl && sizeEl) {
        const family = familyEl.value;
        const size = sizeEl.value;
        const bold = boldEl ? boldEl.checked : false;
        
        localStorage.setItem('app_font_' + zone + '_family', family);
        localStorage.setItem('app_font_' + zone + '_size', size);
        localStorage.setItem('app_font_' + zone + '_bold', bold);
        
        document.documentElement.style.setProperty(zones[zone].familyVar, family);
        document.documentElement.style.setProperty(zones[zone].sizeVar, size);
        document.documentElement.style.setProperty(zones[zone].boldVar, bold ? 'bold' : 'normal');
      }
    });

    // 保存缩进设置
    const indentEl = document.getElementById('font-body-indent');
    if (indentEl) {
      const indent = indentEl.checked;
      localStorage.setItem('app_font_body_indent', indent);
      document.documentElement.style.setProperty('--font-body-indent', indent ? '2em' : '0');
    }

    // 同步到全局设置（如果存在）
    syncToGlobalSettings();
  }

  // 重置字体设置
  function resetFontSettings() {
    const defaults = {
      thinking: { family: 'system-ui, -apple-system, "Segoe UI", sans-serif', size: '12px', bold: false },
      body: { family: 'system-ui, -apple-system, "Segoe UI", sans-serif', size: '15px', bold: false },
      summary: { family: 'system-ui, -apple-system, "Segoe UI", sans-serif', size: '12px', bold: false },
      raw: { family: 'system-ui, -apple-system, "Segoe UI", sans-serif', size: '12px', bold: false },
      stats: { family: 'system-ui, -apple-system, "Segoe UI", sans-serif', size: '12px', bold: false }
    };

    Object.keys(defaults).forEach(function(zone) {
      const familyEl = document.getElementById('font-' + zone + '-family');
      const sizeEl = document.getElementById('font-' + zone + '-size');
      const boldEl = document.getElementById('font-' + zone + '-bold');
      
      if (familyEl) familyEl.value = defaults[zone].family;
      if (sizeEl) sizeEl.value = defaults[zone].size;
      if (boldEl) boldEl.checked = defaults[zone].bold;
    });

    // 重置缩进设置
    const indentEl = document.getElementById('font-body-indent');
    if (indentEl) {
      indentEl.checked = false;
    }
  }

  // 同步到全局设置
  function syncToGlobalSettings() {
    // 触发自定义事件，通知设置页面更新
    window.dispatchEvent(new CustomEvent('fontSettingsChanged'));
  }

  // 应用保存的字体设置
  function applySavedFontSettings() {
    const zones = {
      thinking: { familyVar: '--font-thinking-family', sizeVar: '--font-thinking-size', boldVar: '--font-thinking-weight' },
      body: { familyVar: '--font-body-family', sizeVar: '--font-body-size', boldVar: '--font-body-weight' },
      summary: { familyVar: '--font-summary-family', sizeVar: '--font-summary-size', boldVar: '--font-summary-weight' },
      raw: { familyVar: '--font-raw-family', sizeVar: '--font-raw-size', boldVar: '--font-raw-weight' },
      stats: { familyVar: '--font-stats-family', sizeVar: '--font-stats-size', boldVar: '--font-stats-weight' }
    };

    Object.keys(zones).forEach(function(zone) {
      const savedFamily = localStorage.getItem('app_font_' + zone + '_family');
      const savedSize = localStorage.getItem('app_font_' + zone + '_size');
      const savedBold = localStorage.getItem('app_font_' + zone + '_bold');
      
      if (savedFamily) {
        document.documentElement.style.setProperty(zones[zone].familyVar, savedFamily);
      }
      if (savedSize) {
        document.documentElement.style.setProperty(zones[zone].sizeVar, savedSize);
      }
      if (savedBold) {
        document.documentElement.style.setProperty(zones[zone].boldVar, savedBold === 'true' ? 'bold' : 'normal');
      }
    });

    // 应用缩进设置
    const savedIndent = localStorage.getItem('app_font_body_indent');
    if (savedIndent) {
      document.documentElement.style.setProperty('--font-body-indent', savedIndent === 'true' ? '2em' : '0');
    }
  }

  async function init() {
    ensureSession();
    bindEvents();
    applySavedFontSettings();
    await initPostprocessingRules();
    refreshSessionSummary();
    await loadRecentSegments();
  }

  // 确保 DOM 加载完成后执行
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", async () => {
      await init();
    });
  } else {
    init();
  }
})();