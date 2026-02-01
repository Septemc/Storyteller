(function () {
    // === 1. 配置：字段类型定义 ===
    const FIELD_TYPES = {
        "text": { label: "文本", renderInput: "input" },
        "textarea": { label: "长文本", renderInput: "textarea" },
        "number": { label: "数值", renderInput: "number" },
        "stats_panel": { label: "属性面板", renderInput: "json" },
        "object_list": { label: "对象列表", renderInput: "json" },
        "relation_graph": { label: "关系图谱", renderInput: "json" },
        "image": { label: "图像 (URL/上传)", renderInput: "image" }
    };

    // === 2. 状态变量 ===
    let templatesList = [];
    let currentCharacterData = {};
    let designerState = { id: "", name: "", tabs: [], fields: [] };
    let isEditingNewCharacter = false; // 标记当前是否在创建新角色

    async function init() {
        console.log("Characters Module Initializing...");
        try {
            await loadTemplates();
            await loadCharacterList();
            setupEventListeners();
        } catch (err) {
            console.error("Initialization Failed:", err);
        }
    }

    // === 3.1. 导出功能工具函数 ===
    function downloadJSON(data, fileName) {
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = fileName;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    // === 3. 角色管理逻辑 ===
    async function loadCharacterList() {
        const listEl = document.getElementById("character-list");
        if (!listEl) return;

        try {
            const res = await fetch('/api/characters');
            const data = await res.json();
            listEl.innerHTML = "";

            (data.items || []).forEach(ch => {
                const li = document.createElement("li");
                li.className = "list-item";
                const name = getValueByPath(ch, "basic.name") || ch.character_id;
                li.textContent = `${name} (${ch.character_id})`;
                li.onclick = () => selectCharacter(ch.character_id);
                listEl.appendChild(li);
            });
        } catch (e) { console.error("Load list failed:", e); }
    }

    async function selectCharacter(id) {
        try {
            const res = await fetch(`/api/characters/${id}`);
            if (!res.ok) return;
            currentCharacterData = await res.json();

            document.getElementById("f-char-id").value = currentCharacterData.character_id;
            document.getElementById("f-char-type").value = currentCharacterData.type;
            document.getElementById("f-char-id").disabled = true;

            renderCharacterView();
            renderDynamicEditor();

            document.getElementById("view-mode-btn").click();
            document.getElementById("character-status").textContent = "已加载: " + id;
        } catch (e) { console.error("Select character failed:", e); }
    }

    // 修复“新建角色”点击无反应 (需求 2)
    function handleNewCharacter() {
        isEditingNewCharacter = true;
        const defaultTplId = document.getElementById("template-select").value || "system_default";

        // 初始化空白数据结构
        currentCharacterData = {
            character_id: "",
            type: "npc",
            template_id: defaultTplId,
            basic: { name: "新角色" },
            data: {}
        };

        // UI 状态切换
        document.getElementById("f-char-id").value = "";
        document.getElementById("f-char-id").disabled = false;
        document.getElementById("f-char-type").value = "npc";

        renderDynamicEditor();
        document.getElementById("edit-mode-btn").click();
        document.getElementById("right-panel-title").textContent = "新建角色";
        document.getElementById("f-char-id").focus();
    }

    // === 4. 设计器核心引擎 ===
    function openDesigner(isNew) {
        if (isNew) {
            designerState = { id: "tpl_" + Date.now(), name: "新模板", tabs: [], fields: [] };
        } else {
            const id = document.getElementById("template-select").value;
            const tpl = templatesList.find(t => t.id === id);
            if (!tpl) return alert("请先选择一个有效的模板");
            designerState = JSON.parse(JSON.stringify(tpl));
        }

        document.getElementById("design-tpl-id").value = designerState.id;
        document.getElementById("design-tpl-name").value = designerState.name;
        renderDesignerUI();
        document.getElementById("template-designer-modal").style.display = "flex";
    }

    function renderDesignerUI() {
        renderDesignerTabs();
        renderDesignerFields();
    }

    function renderDesignerTabs() {
        const container = document.getElementById("design-tabs-container");
        container.innerHTML = "";
        designerState.tabs.forEach((tab, index) => {
            const row = document.createElement("div");
            row.className = "designer-row";
            row.style.display = "flex";
            row.style.gap = "5px";
            row.style.marginBottom = "5px";

            row.innerHTML = `
                <input class="form-input tab-id-input" style="width:70px" value="${tab.id}" placeholder="ID">
                <input class="form-input tab-label-input" style="flex:1" value="${tab.label}" placeholder="标签名">
                <button class="btn-small btn-secondary del-tab-btn">×</button>
            `;

            row.querySelector(".tab-id-input").onchange = (e) => {
                const oldId = tab.id;
                tab.id = e.target.value;
                // 级联更新归属字段
                designerState.fields.forEach(f => { if (f.tab === oldId) f.tab = tab.id; });
                renderDesignerUI();
            };
            row.querySelector(".tab-label-input").onchange = (e) => tab.label = e.target.value;
            row.querySelector(".del-tab-btn").onclick = () => {
                designerState.tabs.splice(index, 1);
                renderDesignerUI();
            };
            container.appendChild(row);
        });
    }

    function renderDesignerFields() {
        const container = document.getElementById("design-fields-container");
        if (!container) return;
        container.innerHTML = "";

        designerState.fields.forEach((f, index) => {
            const card = document.createElement("div");
            card.className = "char-card";
            card.style.marginBottom = "10px";

            const tabOptions = designerState.tabs.map(t => `<option value="${t.id}" ${f.tab === t.id ? 'selected' : ''}>${t.label}</option>`).join('');
            const typeOptions = Object.entries(FIELD_TYPES).map(([k, v]) => `<option value="${k}" ${f.type === k ? 'selected' : ''}>${v.label}</option>`).join('');

            card.innerHTML = `
                <div style="display:grid; grid-template-columns: 1fr 1fr 1fr; gap:10px; margin-bottom:10px;">
                    <div>
                        <label class="small-text muted">内部 ID (不可重复)</label>
                        <input class="form-input f-id" value="${f.id || ''}" placeholder="f_name">
                    </div>
                    <div>
                        <label class="small-text muted">显示标签 (Label)</label>
                        <input class="form-input f-label" value="${f.label || ''}" placeholder="姓名">
                    </div>
                    <div>
                        <label class="small-text muted">渲染类型 (Type)</label>
                        <select class="form-select f-type">${typeOptions}</select>
                    </div>
                </div>
                <div style="display:grid; grid-template-columns: 1fr 1fr 1fr; gap:10px; margin-bottom:10px;">
                    <div>
                        <label class="small-text muted">归属标签 (Tab)</label>
                        <select class="form-select f-tab">${tabOptions}</select>
                    </div>
                    <div>
                        <label class="small-text muted">数据路径 (Path)</label>
                        <input class="form-input f-path" value="${f.path || ''}" placeholder="basic.name">
                    </div>
                    <div>
                        <label class="small-text muted">描述 (Desc)</label>
                        <input class="form-input f-desc" value="${f.desc || ''}" placeholder="请输入说明文本">
                    </div>
                </div>
                <div style="text-align:right;">
                    <button class="btn-small-inline del-field-btn" style="color:var(--danger)">删除此字段</button>
                </div>
            `;

            card.querySelector(".f-id").onchange = (e) => f.id = e.target.value;
            card.querySelector(".f-label").onchange = (e) => f.label = e.target.value;
            card.querySelector(".f-type").onchange = (e) => f.type = e.target.value;
            card.querySelector(".f-tab").onchange = (e) => f.tab = e.target.value;
            card.querySelector(".f-path").onchange = (e) => f.path = e.target.value;
            card.querySelector(".f-desc").onchange = (e) => f.desc = e.target.value;

            card.querySelector(".del-field-btn").onclick = () => {
                designerState.fields.splice(index, 1);
                renderDesignerUI();
            };
            container.appendChild(card);
        });
    }

    // === 5. 事件监听 ===
    function setupEventListeners() {
        // 模式切换
        const viewBtn = document.getElementById("view-mode-btn");
        const editBtn = document.getElementById("edit-mode-btn");
        if (viewBtn && editBtn) {
            viewBtn.onclick = () => {
                viewBtn.classList.add("active"); editBtn.classList.remove("active");
                document.getElementById("character-renderer").style.display = "block";
                document.getElementById("character-editor").style.display = "none";
                renderCharacterView();
            };
            editBtn.onclick = () => {
                editBtn.classList.add("active"); viewBtn.classList.remove("active");
                document.getElementById("character-renderer").style.display = "none";
                document.getElementById("character-editor").style.display = "block";
                renderDynamicEditor();
            };
        }

        // 角色详情操作
        document.getElementById("character-new-btn").onclick = handleNewCharacter;

        document.getElementById("character-save-btn").onclick = async () => {
            const charId = document.getElementById("f-char-id").value.trim();
            if (!charId) return alert("角色 ID 不能为空");

            currentCharacterData.character_id = charId;
            currentCharacterData.type = document.getElementById("f-char-type").value;

            // 根据是否是新角色选择 POST 或 PUT
            const method = isEditingNewCharacter ? 'POST' : 'PUT';
            const url = isEditingNewCharacter ? '/api/characters/import' : `/api/characters/${charId}`;

            // 如果是新建，后端 import 接口期望数组或单个对象
            const body = isEditingNewCharacter ? [currentCharacterData] : currentCharacterData;

            const res = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });

            if (res.ok) {
                alert("保存成功");
                isEditingNewCharacter = false;
                document.getElementById("f-char-id").disabled = true;
                loadCharacterList();
            }
        };

        // 导出功能绑定 (需求 1 & 3)
        document.getElementById("tpl-export-btn").onclick = () => {
            const tplId = document.getElementById("template-select").value;
            const tpl = templatesList.find(t => t.id === tplId);
            if (tpl) downloadJSON(tpl, `template_${tplId}.json`);
        };

        document.getElementById("character-export-single-btn").onclick = () => {
            if (!currentCharacterData.character_id || isEditingNewCharacter) return alert("请先选择或保存角色");
            downloadJSON(currentCharacterData, `char_${currentCharacterData.character_id}.json`);
        };

        document.getElementById("character-export-all-btn").onclick = async () => {
            try {
                const res = await fetch('/api/characters/export/all');
                const data = await res.json();
                downloadJSON(data, `all_characters_backup.json`);
            } catch (e) { alert("批量导出失败"); }
        };

        // 保存角色
        document.getElementById("character-save-btn").onclick = async () => {
            if (!currentCharacterData.character_id) return alert("请先选择或新建角色");
            const res = await fetch(`/api/characters/${currentCharacterData.character_id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(currentCharacterData)
            });
            if (res.ok) alert("角色保存成功");
        };

        // 删除角色 (需求 3)
        document.getElementById("character-delete-btn").onclick = async () => {
            const charId = currentCharacterData.character_id;
            if (!charId) return alert("请先选择角色");
            if (!confirm(`警告：确认要删除角色 [${charId}] 吗？此操作不可恢复。`)) return;

            const res = await fetch(`/api/characters/${charId}`, { method: 'DELETE' });
            if (res.ok) {
                alert("角色已删除");
                currentCharacterData = {};
                loadCharacterList();
                document.getElementById("character-renderer").innerHTML = "角色已删除";
            }
        };

        // 模板管理相关 (需求 4 & 5)
        document.getElementById("tpl-apply-btn").onclick = async () => {
            const tplId = document.getElementById("template-select").value;
            if (!currentCharacterData.character_id) return alert("请先选择一个角色以应用模板");
            if (!confirm(`确认将当前角色模板切换为 [${tplId}] 吗？`)) return;

            currentCharacterData.template_id = tplId;
            // 立即保存并重绘
            const res = await fetch(`/api/characters/${currentCharacterData.character_id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(currentCharacterData)
            });
            if (res.ok) {
                alert("模板应用成功");
                renderCharacterView();
                renderDynamicEditor();
            }
        };

        document.getElementById("tpl-delete-btn").onclick = async () => {
            const tplId = document.getElementById("template-select").value;
            if (tplId === "system_default") return alert("系统默认模板不能删除");
            if (!confirm(`强烈警告：确认要删除模板 [${tplId}] 吗？使用此模板的角色显示可能会受到影响。`)) return;

            const res = await fetch(`/api/templates/${tplId}`, { method: 'DELETE' });
            if (res.ok) {
                alert("模板已删除");
                loadTemplates();
            }
        };

        // 保存模板配置 (需求 1)
        document.getElementById("save-template-btn").onclick = async () => {
            designerState.id = document.getElementById("design-tpl-id").value;
            designerState.name = document.getElementById("design-tpl-name").value;

            if (!designerState.id || !designerState.name) return alert("ID 和名称不能为空");

            const isUpdate = templatesList.some(t => t.id === designerState.id);
            const url = isUpdate ? `/api/templates/${designerState.id}` : "/api/templates";
            const method = isUpdate ? "PUT" : "POST";

            const res = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    id: designerState.id,
                    name: designerState.name,
                    config: { tabs: designerState.tabs, fields: designerState.fields }
                })
            });

            if (res.ok) {
                alert("模板配置已保存");
                document.getElementById("template-designer-modal").style.display = "none";
                loadTemplates();
            } else {
                const err = await res.json();
                alert("保存失败: " + err.detail);
            }
        };

        // 其余导入按钮绑定
        const tplBtn = document.getElementById("template-import-btn");
        const tplInput = document.getElementById("template-import-file");
        if (tplBtn && tplInput) {
            tplBtn.onclick = () => tplInput.click();
            tplInput.onchange = (e) => {
                const file = e.target.files[0];
                if (file) handleTemplateImport(file);
            };
        }

        const charBtn = document.getElementById("character-import-btn");
        const charInput = document.getElementById("character-import-file");
        if (charBtn && charInput) {
            charBtn.onclick = () => charInput.click();
            charInput.onchange = (e) => {
                const file = e.target.files[0];
                if (file) handleCharacterBatchImport(file);
            };
        }

        document.getElementById("tpl-edit-btn").onclick = () => openDesigner(false);
        document.getElementById("tpl-new-btn").onclick = () => openDesigner(true);
        document.getElementById("close-designer-btn").onclick = () => {
            document.getElementById("template-designer-modal").style.display = "none";
        };

        document.getElementById("design-add-tab-btn").onclick = () => {
            designerState.tabs.push({ id: "tab_" + Date.now(), label: "新标签" });
            renderDesignerUI();
        };
        document.getElementById("design-add-field-btn").onclick = () => {
            designerState.fields.push({ id: "f_" + Date.now(), label: "新字段", type: "text", tab: designerState.tabs[0]?.id || "", path: "data.new" });
            renderDesignerUI();
        };
    }

    // === 6. 导入对齐校验 (需求 2) ===
    async function handleCharacterBatchImport(file) {
        const reader = new FileReader();
        reader.onload = async (e) => {
            try {
                const data = JSON.parse(e.target.result);
                const payload = Array.isArray(data) ? data : (data.entries || [data]);

                // 校验：获取当前模板的所有 Path
                const tplId = document.getElementById("template-select").value;
                const activeTpl = templatesList.find(t => t.id === tplId) || templatesList[0];
                const requiredPaths = activeTpl.fields.map(f => f.path);

                let mismatchCount = 0;
                let mismatchedFields = new Set();

                payload.forEach(char => {
                    requiredPaths.forEach(path => {
                        if (getValueByPath(char, path) === undefined) {
                            mismatchCount++;
                            mismatchedFields.add(path);
                        }
                    });
                });

                const res = await fetch('/api/characters/import', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(payload)
                });

                if (res.ok) {
                    if (mismatchCount > 0) {
                        alert(`导入成功，但存在数据对齐风险：\n有 ${mismatchCount} 处模板定义的字段在 JSON 中未找到。\n缺失路径参考: ${Array.from(mismatchedFields).slice(0,3).join(", ")}...\n这些字段在详情中将留空。`);
                    } else {
                        alert("导入成功，所有字段已对齐当前模板。");
                    }
                    loadCharacterList();
                }
            } catch (err) { alert("导入解析失败: " + err.message); }
        };
        reader.readAsText(file);
    }

    // === 工具函数与渲染辅助 ===
    function renderCharacterView() {
        const panel = document.getElementById("character-renderer");
        if (!panel) return;
        const tplId = currentCharacterData.template_id || "system_default";
        const tpl = templatesList.find(t => t.id === tplId) || templatesList[0];

        let html = `<div class="char-card"><h2>${getValueByPath(currentCharacterData, "basic.name") || "未命名"}</h2><p class="small-text muted">模板: ${tpl.name}</p></div>`;

        tpl.tabs.forEach(tab => {
            html += `<div class="char-card"><h3>${tab.label}</h3>`;
            const fields = tpl.fields.filter(f => f.tab === tab.id);
            fields.forEach(f => {
                const val = getValueByPath(currentCharacterData, f.path);

                // 处理图像展示
                if (f.type === 'image') {
                    html += `<p><strong>${f.label}:</strong><br>
                             <img src="${val || 'assets/img/placeholder.png'}" style="max-width:200px; border-radius:8px; margin-top:5px; border:1px solid var(--border-soft);">
                             </p>`;
                }
                // 处理描述展示 (desc)
                else if (val !== undefined) {
                    const descSpan = f.desc ? `<br><small class="muted">${f.desc}</small>` : "";
                    html += `<p><strong>${f.label}:</strong> ${typeof val === 'object' ? JSON.stringify(val) : val} ${descSpan}</p>`;
                }
            });
            html += `</div>`;
        });
        panel.innerHTML = html;
    }

    function renderDynamicEditor() {
        const nav = document.getElementById("editor-tabs-nav");
        const container = document.getElementById("editor-fields-container");
        if (!nav || !container) return;

        const tplId = currentCharacterData.template_id || "system_default";
        const tpl = templatesList.find(t => t.id === tplId) || templatesList[0];

        nav.innerHTML = "";
        container.innerHTML = "";

        tpl.tabs.forEach((tab, idx) => {
            // 1. 渲染 Tab 导航按钮
            const btn = document.createElement("button");
            btn.className = `tab-button ${idx === 0 ? 'active' : ''}`;
            btn.textContent = tab.label;
            btn.onclick = () => {
                document.querySelectorAll(".dyn-editor-section").forEach(s => s.style.display = 'none');
                document.getElementById(`edit-section-${tab.id}`).style.display = 'block';
                document.querySelectorAll(".tab-button").forEach(b => b.classList.remove("active"));
                btn.classList.add("active");
            };
            nav.appendChild(btn);

            // 2. 创建 Tab 内容面板
            const section = document.createElement("div");
            section.id = `edit-section-${tab.id}`;
            section.className = "dyn-editor-section";
            section.style.display = idx === 0 ? 'block' : 'none';

            // 3. 遍历并渲染属于该 Tab 的所有字段
            tpl.fields.filter(f => f.tab === tab.id).forEach(field => {
                const wrap = document.createElement("div");
                wrap.className = "settings-section";

                // 使用 field.desc 作为字段下方的辅助说明文字
                const descHtml = field.desc ? `<div class="small-text muted" style="margin-top:2px;">${field.desc}</div>` : "";

                // --- 核心插入点：根据 field.type 分支处理 ---
                if (field.type === 'image') {
                    // A. 图像类型处理逻辑
                    wrap.innerHTML = `
                        <label class="form-label">${field.label}</label>
                        <div style="display:flex; gap:8px;">
                            <input class="form-input img-path-input" 
                                   value="${getValueByPath(currentCharacterData, field.path) || ''}" 
                                   placeholder="请输入图片 URL 地址...">
                            <button class="btn-small btn-secondary" onclick="alert('上传功能开发中，请先使用 URL 地址')">上传</button>
                        </div>
                        ${descHtml}
                    `;

                    // 绑定图像路径更新
                    wrap.querySelector(".img-path-input").onchange = (e) => {
                        setValueByPath(currentCharacterData, field.path, e.target.value);
                    };
                }
                else {
                    // B. 通用类型处理逻辑 (文本、长文本、数值等)
                    wrap.innerHTML = `<label class="form-label">${field.label}</label>`;

                    // 根据 FIELD_TYPES 配置决定渲染标签 [cite: 184-185]
                    const inputType = FIELD_TYPES[field.type]?.renderInput || 'input';
                    const input = document.createElement(inputType === 'textarea' ? 'textarea' : 'input');

                    input.className = "form-input";
                    if (inputType === 'number') input.type = 'number'; // 支持数值类型

                    let currentVal = getValueByPath(currentCharacterData, field.path);
                    input.value = typeof currentVal === 'object' ? JSON.stringify(currentVal) : (currentVal || "");

                    // 绑定数据更新逻辑
                    input.onchange = (e) => {
                        let v = e.target.value;
                        // 如果是数值类型或 JSON 类型，进行转换
                        if (inputType === 'number') v = parseFloat(v) || 0;
                        if (inputType === 'json') { try { v = JSON.parse(v); } catch(err) {} }

                        setValueByPath(currentCharacterData, field.path, v);
                    };

                    wrap.appendChild(input);
                    if (field.desc) {
                        const descDiv = document.createElement("div");
                        descDiv.className = "small-text muted";
                        descDiv.style.marginTop = "2px";
                        descDiv.textContent = field.desc;
                        wrap.appendChild(descDiv);
                    }
                }

                section.appendChild(wrap);
            });

            container.appendChild(section);
        });
    }

    // === 工具函数：多级路径读写 ===
    function getValueByPath(obj, path) {
        if (!path) return undefined;
        return path.split('.').reduce((o, i) => (o ? o[i] : undefined), obj);
    }

    function setValueByPath(obj, path, value) {
        const parts = path.split('.');
        const last = parts.pop();
        const target = parts.reduce((o, i) => {
            if (!o[i]) o[i] = {};
            return o[i];
        }, obj);
        target[last] = value;
    }

    async function loadTemplates() {
        const res = await fetch('/api/templates/list');
        const data = await res.json();
        templatesList = (data.items || []).map(t => ({...t.config, id: t.id, name: t.name}));
        const el = document.getElementById("template-select");
        if (el) el.innerHTML = templatesList.map(t => `<option value="${t.id}">${t.name}</option>`).join('');
    }

    async function handleTemplateImport(file) {
        const reader = new FileReader();
        reader.onload = async (e) => {
            const config = JSON.parse(e.target.result);
            const res = await fetch('/api/templates', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({id: config.id, name: config.name, config: config})
            });
            if (res.ok) { alert("模板导入成功"); loadTemplates(); }
        };
        reader.readAsText(file);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else { init(); }
})();