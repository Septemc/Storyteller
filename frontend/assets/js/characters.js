(function () {
  // === DOM 元素获取 ===
  const listEl = document.getElementById("character-list");
  const newBtn = document.getElementById("character-new-btn");
  const saveBtn = document.getElementById("character-save-btn");
  const statusEl = document.getElementById("character-status");
  const searchEl = document.getElementById("character-search");

  // 导入相关 DOM
  const importInput = document.getElementById("character-import-file");
  const importBtn = document.getElementById("character-import-btn"); // 对应HTML里 onclick 触发的按钮
  const importStatusEl = document.getElementById("import-status");

  // 视图切换相关 DOM
  const viewModeBtn = document.getElementById("view-mode-btn");
  const editModeBtn = document.getElementById("edit-mode-btn");
  const rendererPanel = document.getElementById("character-renderer");
  const editorPanel = document.getElementById("character-editor");

  // 编辑器 Inputs
  const idEl = document.getElementById("character-id");
  const typeEl = document.getElementById("character-type");
  const basicJsonEl = document.getElementById("character-basic-json");
  const knowledgeJsonEl = document.getElementById("character-knowledge-json");
  const secretsJsonEl = document.getElementById("character-secrets-json");
  const attributesJsonEl = document.getElementById("character-attributes-json");
  const relationsJsonEl = document.getElementById("character-relations-json");
  const equipmentJsonEl = document.getElementById("character-equipment-json");
  const itemsJsonEl = document.getElementById("character-items-json");
  const skillsJsonEl = document.getElementById("character-skills-json");
  const fortuneJsonEl = document.getElementById("character-fortune-json");

  const tabButtons = document.querySelectorAll(".tab-button");
  const tabContents = document.querySelectorAll(".tab-content");

  let currentCharacterId = null;

  // === 1. 列表加载逻辑 ===
  async function loadCharacterList() {
    const params = new URLSearchParams();
    const q = searchEl.value.trim();
    if (q) params.set("q", q);
    try {
      const resp = await fetch("/api/characters?" + params.toString());
      if (!resp.ok) {
        throw new Error("HTTP " + resp.status);
      }
      const data = await resp.json();
      const items = data.items || [];
      listEl.innerHTML = "";
      items.forEach(function (ch) {
        const li = document.createElement("li");
        li.className = "list-item";
        li.dataset.characterId = ch.character_id;
        if (ch.character_id === currentCharacterId) li.classList.add("active");

        // 尝试解析名字
        let name = "";
        if (ch.basic) {
          try {
            const basicObj = typeof ch.basic === "string" ? JSON.parse(ch.basic) : ch.basic;
            name = basicObj.name || "";
          } catch (e) {}
        }

        const leftSpan = document.createElement("span");
        leftSpan.textContent = ch.character_id + (name ? " · " + name : "");

        const rightSpan = document.createElement("span");
        rightSpan.className = "small-text muted";
        rightSpan.textContent = ch.type || "";

        li.appendChild(leftSpan);
        li.appendChild(rightSpan);

        li.addEventListener("click", function () {
          selectCharacter(ch.character_id);
        });

        listEl.appendChild(li);
      });
    } catch (err) {
      console.error(err);
      listEl.innerHTML = "";
      const li = document.createElement("li");
      li.textContent = "加载失败：" + err.message;
      listEl.appendChild(li);
    }
  }

  // === 2. 选择角色 (同时触发 编辑器填充 和 视图渲染) ===
  async function selectCharacter(characterId) {
    currentCharacterId = characterId;
    statusEl.textContent = "加载角色 " + characterId + "...";

    // 更新列表高亮
    const lis = listEl.querySelectorAll(".list-item");
    lis.forEach(function (li) {
      li.classList.toggle("active", li.dataset.characterId === characterId);
    });

    try {
      const resp = await fetch("/api/characters/" + encodeURIComponent(characterId));
      if (!resp.ok) {
        throw new Error("HTTP " + resp.status);
      }
      const data = await resp.json();

      // 1. 填充编辑器 (Raw JSON)
      populateCharacterEditor(data);
      // 2. 渲染预览视图 (HTML)
      renderCharacterView(data);

      statusEl.textContent = "已加载。";
    } catch (err) {
      console.error(err);
      statusEl.textContent = "加载失败：" + err.message;
      // 出错时清空预览区
      rendererPanel.innerHTML = '<div class="placeholder-text" style="padding:20px; color:var(--danger);">加载失败</div>';
    }
  }

  // === 3. 填充编辑器逻辑 ===
  function populateCharacterEditor(ch) {
    idEl.value = ch.character_id || "";
    typeEl.value = ch.type || "npc";

    const setJson = (el, val) => {
        // 如果后端传回来的已经是对象，直接 stringify
        // 如果是 JSON 字符串，先 parse 再 stringify 格式化，或者直接放进去
        let obj = val;
        if (typeof val === 'string' && val.trim()) {
            try { obj = JSON.parse(val); } catch(e) { obj = {}; }
        }
        el.value = JSON.stringify(obj || {}, null, 2);
    };

    setJson(basicJsonEl, ch.basic);
    setJson(knowledgeJsonEl, ch.knowledge);
    setJson(secretsJsonEl, ch.secrets);
    setJson(attributesJsonEl, ch.attributes);
    setJson(relationsJsonEl, ch.relations);
    setJson(equipmentJsonEl, ch.equipment || []); // 数组默认值
    setJson(itemsJsonEl, ch.items || []);
    setJson(skillsJsonEl, ch.skills || []);
    setJson(fortuneJsonEl, ch.fortune);
  }

  // === 4. 渲染预览视图逻辑 (核心新功能) ===
  function renderCharacterView(data) {
    // 辅助解析：确保拿到的是对象
    const parse = (val) => {
        try {
            return (typeof val === 'string' && val) ? JSON.parse(val) : (val || {});
        } catch (e) { return {}; }
    };

    const basic = parse(data.basic);
    const knowledge = parse(data.knowledge);
    const attributes = parse(data.attributes);
    const relations = parse(data.relations);
    const equipment = parse(data.equipment); // 可能是数组
    const skills = parse(data.skills);       // 可能是数组

    // 头部信息
    let html = `
        <div style="padding-bottom: 10px; border-bottom: 1px solid var(--border-soft); margin-bottom: 16px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <h2 style="margin: 0; color: var(--accent); font-size: 18px;">
                    ${basic.name || '未命名'} <span style="font-size:0.6em; color:var(--text-secondary);">(${data.character_id})</span>
                </h2>
                <span class="tag-item" style="background:var(--bg-elevated); border-color:var(--border-soft); color:var(--text-secondary);">
                    ${data.type.toUpperCase()}
                </span>
            </div>
            <div class="small-text" style="margin-top: 6px; color: var(--text-primary);">
                ${basic.identity || '未知身份'} | ${basic.ability_tier || '未知境界'}
            </div>
            <div style="margin-top: 8px; font-style: italic; color: var(--text-secondary); font-size: 13px;">
                "${basic.short_description || '暂无描述'}"
            </div>
        </div>
    `;

    // 1. 性格与见闻
    html += `<div class="char-card">
        <h3>📝 性格与见闻</h3>
        <div class="kv-row"><span class="kv-label">性格:</span><span class="kv-value">${knowledge.personality || '-'}</span></div>
        <div class="kv-row"><span class="kv-label">外貌:</span><span class="kv-value">${knowledge.appearance || '-'}</span></div>
        <div class="kv-row"><span class="kv-label">内心:</span><span class="kv-value">${knowledge.inner_thoughts || '-'}</span></div>
        <div class="kv-row"><span class="kv-label">当前目标:</span><span class="kv-value">${knowledge.goals?.current_motivation || '-'}</span></div>
        <div style="margin-top:8px;"><strong>背景:</strong> <p style="margin-top:4px; color:var(--text-secondary);">${knowledge.background || '-'}</p></div>
    </div>`;

    // 2. 核心属性 (Grid展示)
    if (attributes.core_stats) {
        html += `<div class="char-card">
            <h3>📊 核心属性</h3>
            <div class="stats-grid">
                ${Object.entries(attributes.core_stats).map(([k,v]) => `
                    <div class="stat-box">
                        <div class="stat-label">${k.toUpperCase()}</div>
                        <div class="stat-val">${v}</div>
                    </div>
                `).join('')}
            </div>
        </div>`;
    }

    // 3. 关系网 (Table展示)
    if (relations && Object.keys(relations).length > 0) {
        html += `<div class="char-card">
            <h3>🕸 人际关系</h3>
            <table class="nested-table">
                <thead><tr><th style="width:20%">对象</th><th style="width:30%">类型</th><th>描述</th></tr></thead>
                <tbody>
                    ${Object.entries(relations).map(([target, info]) => `
                        <tr>
                            <td><strong>${target}</strong><br><span class="small-text muted">好感:${info.like || 0}</span></td>
                            <td>${info.relation_type}</td>
                            <td class="small-text">${info.description}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>`;
    }

    // 4. 战力概览 (Tag Cloud)
    html += `<div class="char-card">
        <h3>⚔️ 战力概览</h3>
        <div style="margin-bottom:8px;">
            <div class="small-text muted" style="margin-bottom:4px;">装备</div>
            <div class="tag-cloud">
                ${Array.isArray(equipment) && equipment.length ? equipment.map(e => `<span class="tag-item">${e.name}</span>`).join('') : '<span class="small-text muted">无</span>'}
            </div>
        </div>
        <div>
            <div class="small-text muted" style="margin-bottom:4px;">技能</div>
            <ul style="padding-left:18px; margin:0; font-size:13px; color:var(--text-secondary);">
                ${Array.isArray(skills) && skills.length ? skills.map(s => `<li><strong style="color:var(--text-primary)">${s.name}</strong>: ${s.description}</li>`).join('') : '<li class="muted">无</li>'}
            </ul>
        </div>
    </div>`;

    rendererPanel.innerHTML = html;
  }

  // === 5. 批量导入逻辑 ===
  async function importCharacterData(file) {
    if (!file) return;
    importStatusEl.textContent = "读取中...";
    try {
        const text = await file.text();
        // 尝试解析，看是否符合格式
        const json = JSON.parse(text);

        importStatusEl.textContent = "上传中...";
        const res = await fetch('/api/characters/import', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(json)
        });

        if (res.ok) {
            const result = await res.json();
            importStatusEl.textContent = "导入成功";
            importStatusEl.style.color = "var(--accent)";
            loadCharacterList(); // 刷新列表
        } else {
            const errMsg = await res.text();
            throw new Error("HTTP " + res.status + " " + errMsg);
        }
    } catch (e) {
        console.error(e);
        importStatusEl.textContent = "失败: " + e.message;
        importStatusEl.style.color = "var(--danger)";
    }
    importInput.value = ''; // 清空以允许重复上传
  }

  // === 基础功能：清除编辑器 ===
  function clearCharacterEditor() {
    idEl.value = "";
    typeEl.value = "npc";
    const inputs = [basicJsonEl, knowledgeJsonEl, secretsJsonEl, attributesJsonEl, relationsJsonEl, equipmentJsonEl, itemsJsonEl, skillsJsonEl, fortuneJsonEl];
    inputs.forEach(el => el.value = "");
    rendererPanel.innerHTML = '<div class="placeholder-text" style="padding:20px;">请选择角色或填入数据...</div>';
  }

  function newCharacter() {
    currentCharacterId = null;
    clearCharacterEditor();
    const lis = listEl.querySelectorAll(".list-item");
    lis.forEach(li => li.classList.remove("active"));

    // 自动切换到编辑模式
    editModeBtn.click();
    statusEl.textContent = "新角色编辑中...";
  }

  // === 基础功能：收集数据 ===
  function collectCharacterFromEditor() {
    const parse = (el, name) => {
        try { return el.value.trim() ? JSON.parse(el.value) : (name === 'equipment' || name === 'items' || name === 'skills' ? [] : {}); }
        catch (e) { statusEl.textContent = name + " JSON 解析失败"; return null; }
    };

    const data = {
      character_id: idEl.value.trim(),
      type: typeEl.value,
      basic: parse(basicJsonEl, 'basic'),
      knowledge: parse(knowledgeJsonEl, 'knowledge'),
      secrets: parse(secretsJsonEl, 'secrets'),
      attributes: parse(attributesJsonEl, 'attributes'),
      relations: parse(relationsJsonEl, 'relations'),
      equipment: parse(equipmentJsonEl, 'equipment'),
      items: parse(itemsJsonEl, 'items'),
      skills: parse(skillsJsonEl, 'skills'),
      fortune: parse(fortuneJsonEl, 'fortune')
    };

    // 简单校验是否有解析失败
    for (let key in data) { if (data[key] === null) return null; }
    return data;
  }

  async function saveCharacter() {
    const ch = collectCharacterFromEditor();
    if (!ch) return; // 解析失败已在 collect 中提示
    if (!ch.character_id) {
      statusEl.textContent = "请填写角色编号。";
      return;
    }

    statusEl.textContent = "正在保存...";
    try {
      const method = currentCharacterId ? "PUT" : "POST";
      const url = method === "PUT"
          ? "/api/characters/" + encodeURIComponent(ch.character_id)
          : "/api/characters";

      const resp = await fetch(url, {
        method: method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(ch)
      });
      if (!resp.ok) throw new Error(await resp.text());

      statusEl.textContent = "保存成功。";
      currentCharacterId = ch.character_id;
      loadCharacterList();
      // 保存后自动刷新预览视图
      renderCharacterView(ch);
    } catch (err) {
      console.error(err);
      statusEl.textContent = "保存失败：" + err.message;
    }
  }

  function switchTab(tabId) {
    tabButtons.forEach(btn => btn.classList.toggle("active", btn.dataset.tab === tabId));
    tabContents.forEach(content => content.classList.toggle("hidden", content.id !== tabId));
  }

  // === 事件绑定 ===
  function bindEvents() {
    newBtn.addEventListener("click", newCharacter);
    saveBtn.addEventListener("click", saveCharacter);
    searchEl.addEventListener("input", () => loadCharacterList());

    // 标签页切换
    tabButtons.forEach(btn => btn.addEventListener("click", () => switchTab(btn.dataset.tab)));

    // 导入事件
    if(importInput) {
        importInput.addEventListener("change", (e) => importCharacterData(e.target.files[0]));
    }

    // 视图模式切换
    if(viewModeBtn && editModeBtn) {
        viewModeBtn.addEventListener("click", () => {
            viewModeBtn.classList.add("active");
            editModeBtn.classList.remove("active");
            rendererPanel.style.display = "block";
            editorPanel.style.display = "none";
            // 切换回预览时，尝试用当前编辑器里的内容渲染一下（所见即所得）
            const tempCh = collectCharacterFromEditor();
            if(tempCh) renderCharacterView(tempCh);
        });

        editModeBtn.addEventListener("click", () => {
            editModeBtn.classList.add("active");
            viewModeBtn.classList.remove("active");
            rendererPanel.style.display = "none";
            editorPanel.style.display = "block";
        });
    }
  }

  function init() {
    bindEvents();
    loadCharacterList();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();