(function () {
  const dungeonListEl = document.getElementById("dungeon-list");
  const newBtn = document.getElementById("dungeon-new-btn");
  const saveBtn = document.getElementById("dungeon-save-btn");
  const statusEl = document.getElementById("dungeon-status");

  const dungeonIdEl = document.getElementById("dungeon-id");
  const dungeonNameEl = document.getElementById("dungeon-name-input");
  const dungeonDescriptionEl = document.getElementById("dungeon-description");
  const dungeonLevelMinEl = document.getElementById("dungeon-level-min");
  const dungeonLevelMaxEl = document.getElementById("dungeon-level-max");
  const dungeonGlobalRulesEl = document.getElementById("dungeon-global-rules");
  const addNodeBtn = document.getElementById("dungeon-add-node-btn");
  const nodesContainerEl = document.getElementById("dungeon-nodes-container");

  let currentDungeonId = null;
  let dungeonCache = {};

  async function loadDungeonList() {
    try {
      const resp = await fetch("/api/dungeon/list");
      if (!resp.ok) {
        throw new Error("HTTP " + resp.status);
      }
      const data = await resp.json();
      const items = data.items || [];
      dungeonListEl.innerHTML = "";
      items.forEach(function (dun) {
        const li = document.createElement("li");
        li.className = "list-item";
        li.dataset.dungeonId = dun.dungeon_id;

        const leftSpan = document.createElement("span");
        leftSpan.textContent = dun.dungeon_id + " · " + (dun.name || "");

        const rightSpan = document.createElement("span");
        rightSpan.className = "small-text muted";
        rightSpan.textContent = "等级 " + (dun.level_min || "-") + "-" + (dun.level_max || "-");

        li.appendChild(leftSpan);
        li.appendChild(rightSpan);

        li.addEventListener("click", function () {
          selectDungeon(dun.dungeon_id);
        });

        dungeonListEl.appendChild(li);
      });
    } catch (err) {
      console.error(err);
      dungeonListEl.innerHTML = "";
      const li = document.createElement("li");
      li.textContent = "加载失败：" + err.message;
      dungeonListEl.appendChild(li);
    }
  }

  function clearDungeonEditor() {
    dungeonIdEl.value = "";
    dungeonNameEl.value = "";
    dungeonDescriptionEl.value = "";
    dungeonLevelMinEl.value = 1;
    dungeonLevelMaxEl.value = 5;
    dungeonGlobalRulesEl.value = "";
    nodesContainerEl.innerHTML = "";
  }

  function newDungeon() {
    currentDungeonId = null;
    clearDungeonEditor();
    statusEl.textContent = "新副本编辑中...";
    const liNodes = dungeonListEl.querySelectorAll(".list-item");
    liNodes.forEach(function (li) {
      li.classList.remove("active");
    });
  }

  async function selectDungeon(dungeonId) {
    currentDungeonId = dungeonId;
    statusEl.textContent = "加载副本 " + dungeonId + "...";

    const liNodes = dungeonListEl.querySelectorAll(".list-item");
    liNodes.forEach(function (li) {
      li.classList.toggle("active", li.dataset.dungeonId === dungeonId);
    });

    if (dungeonCache[dungeonId]) {
      populateDungeonEditor(dungeonCache[dungeonId]);
      statusEl.textContent = "已加载。";
      return;
    }

    try {
      const resp = await fetch("/api/dungeon/" + encodeURIComponent(dungeonId));
      if (!resp.ok) {
        throw new Error("HTTP " + resp.status);
      }
      const data = await resp.json();
      dungeonCache[dungeonId] = data;
      populateDungeonEditor(data);
      statusEl.textContent = "已加载。";
    } catch (err) {
      console.error(err);
      statusEl.textContent = "加载失败：" + err.message;
    }
  }

  function populateDungeonEditor(dun) {
    dungeonIdEl.value = dun.dungeon_id || "";
    dungeonNameEl.value = dun.name || "";
    dungeonDescriptionEl.value = dun.description || "";
    dungeonLevelMinEl.value = dun.level_min || 1;
    dungeonLevelMaxEl.value = dun.level_max || 5;
    dungeonGlobalRulesEl.value = JSON.stringify(dun.global_rules || {}, null, 2);

    nodesContainerEl.innerHTML = "";
    const nodes = dun.nodes || [];
    nodes.sort(function (a, b) {
      return (a.index || 0) - (b.index || 0);
    });
    nodes.forEach(function (node) {
      const nodeEl = createNodeBlock(node);
      nodesContainerEl.appendChild(nodeEl);
    });
  }

  function createNodeBlock(node) {
    const wrapper = document.createElement("div");
    wrapper.className = "node-block";

    const header = document.createElement("div");
    header.className = "node-header";

    const titleSpan = document.createElement("span");
    titleSpan.textContent =
      (node.index || 0) + " · " + (node.node_id || "") + " · " + (node.name || "");

    const btnGroup = document.createElement("div");

    const upBtn = document.createElement("button");
    upBtn.textContent = "上移";
    upBtn.className = "btn-small btn-secondary";
    upBtn.addEventListener("click", function () {
      moveNodeBlock(wrapper, -1);
    });

    const downBtn = document.createElement("button");
    downBtn.textContent = "下移";
    downBtn.className = "btn-small btn-secondary";
    downBtn.addEventListener("click", function () {
      moveNodeBlock(wrapper, 1);
    });

    const removeBtn = document.createElement("button");
    removeBtn.textContent = "删除";
    removeBtn.className = "btn-small";
    removeBtn.addEventListener("click", function () {
      nodesContainerEl.removeChild(wrapper);
    });

    btnGroup.appendChild(upBtn);
    btnGroup.appendChild(downBtn);
    btnGroup.appendChild(removeBtn);

    header.appendChild(titleSpan);
    header.appendChild(btnGroup);

    const body = document.createElement("div");
    body.className = "small-text";

    const idInput = document.createElement("input");
    idInput.className = "form-input";
    idInput.placeholder = "节点 ID";
    idInput.value = node.node_id || "";
    idInput.dataset.field = "node_id";

    const nameInput = document.createElement("input");
    nameInput.className = "form-input";
    nameInput.placeholder = "节点名称";
    nameInput.value = node.name || "";
    nameInput.dataset.field = "name";

    const indexInput = document.createElement("input");
    indexInput.className = "form-input";
    indexInput.type = "number";
    indexInput.placeholder = "节点顺序";
    indexInput.value = node.index || 0;
    indexInput.dataset.field = "index";

    const progressInput = document.createElement("input");
    progressInput.className = "form-input";
    progressInput.type = "number";
    progressInput.placeholder = "进度百分比";
    progressInput.value = node.progress_percent || 0;
    progressInput.dataset.field = "progress_percent";

    const entryConditionsTextarea = document.createElement("textarea");
    entryConditionsTextarea.className = "form-textarea";
    entryConditionsTextarea.rows = 2;
    entryConditionsTextarea.placeholder = "进入条件（JSON 数组）";
    entryConditionsTextarea.value = JSON.stringify(node.entry_conditions || [], null, 0);
    entryConditionsTextarea.dataset.field = "entry_conditions";

    const exitConditionsTextarea = document.createElement("textarea");
    exitConditionsTextarea.className = "form-textarea";
    exitConditionsTextarea.rows = 2;
    exitConditionsTextarea.placeholder = "退出条件（JSON 数组）";
    exitConditionsTextarea.value = JSON.stringify(node.exit_conditions || [], null, 0);
    exitConditionsTextarea.dataset.field = "exit_conditions";

    const summaryReqTextarea = document.createElement("textarea");
    summaryReqTextarea.className = "form-textarea";
    summaryReqTextarea.rows = 2;
    summaryReqTextarea.placeholder = "总结要求（自然语言）";
    summaryReqTextarea.value = node.summary_requirements || "";
    summaryReqTextarea.dataset.field = "summary_requirements";

    const storyReqTextarea = document.createElement("textarea");
    storyReqTextarea.className = "form-textarea";
    storyReqTextarea.rows = 3;
    storyReqTextarea.placeholder = "剧情要求（JSON）";
    storyReqTextarea.value = JSON.stringify(node.story_requirements || {}, null, 0);
    storyReqTextarea.dataset.field = "story_requirements";

    const branchTextarea = document.createElement("textarea");
    branchTextarea.className = "form-textarea";
    branchTextarea.rows = 2;
    branchTextarea.placeholder = "分支映射（JSON）";
    branchTextarea.value = JSON.stringify(node.branching || {}, null, 0);
    branchTextarea.dataset.field = "branching";

    const group1 = document.createElement("div");
    group1.className = "half-grid";
    group1.appendChild(idInput);
    group1.appendChild(nameInput);

    const group2 = document.createElement("div");
    group2.className = "half-grid";
    group2.appendChild(indexInput);
    group2.appendChild(progressInput);

    body.appendChild(group1);
    body.appendChild(group2);

    const label1 = document.createElement("div");
    label1.className = "small-text";
    label1.textContent = "进入条件";
    body.appendChild(label1);
    body.appendChild(entryConditionsTextarea);

    const label2 = document.createElement("div");
    label2.className = "small-text";
    label2.textContent = "退出条件";
    body.appendChild(label2);
    body.appendChild(exitConditionsTextarea);

    const label3 = document.createElement("div");
    label3.className = "small-text";
    label3.textContent = "总结要求";
    body.appendChild(label3);
    body.appendChild(summaryReqTextarea);

    const label4 = document.createElement("div");
    label4.className = "small-text";
    label4.textContent = "剧情要求";
    body.appendChild(label4);
    body.appendChild(storyReqTextarea);

    const label5 = document.createElement("div");
    label5.className = "small-text";
    label5.textContent = "分支映射";
    body.appendChild(label5);
    body.appendChild(branchTextarea);

    wrapper.appendChild(header);
    wrapper.appendChild(body);

    return wrapper;
  }

  function moveNodeBlock(block, delta) {
    const nodes = Array.prototype.slice.call(nodesContainerEl.children);
    const index = nodes.indexOf(block);
    if (index === -1) return;
    const newIndex = index + delta;
    if (newIndex < 0 || newIndex >= nodes.length) return;

    nodesContainerEl.removeChild(block);
    if (delta > 0 && newIndex === nodes.length) {
      nodesContainerEl.appendChild(block);
    } else {
      nodesContainerEl.insertBefore(block, nodesContainerEl.children[newIndex]);
    }
  }

  function collectDungeonFromEditor() {
    const dungeonId = dungeonIdEl.value.trim();
    const name = dungeonNameEl.value.trim();
    const description = dungeonDescriptionEl.value;
    const levelMin = parseInt(dungeonLevelMinEl.value || "1", 10);
    const levelMax = parseInt(dungeonLevelMaxEl.value || "5", 10);

    let globalRules = {};
    if (dungeonGlobalRulesEl.value.trim()) {
      try {
        globalRules = JSON.parse(dungeonGlobalRulesEl.value);
      } catch (e) {
        statusEl.textContent = "全局规则 JSON 解析失败。";
      }
    }

    const nodesDom = Array.prototype.slice.call(nodesContainerEl.children);
    const nodes = nodesDom.map(function (block, index) {
      const inputs = block.querySelectorAll("[data-field]");
      const node = { index: index + 1 };
      inputs.forEach(function (el) {
        const field = el.dataset.field;
        if (!field) return;
        if (field === "node_id") node.node_id = el.value.trim();
        if (field === "name") node.name = el.value.trim();
        if (field === "index") node.index = parseInt(el.value || String(index + 1), 10);
        if (field === "progress_percent") node.progress_percent = parseInt(el.value || "0", 10);
        if (field === "entry_conditions") {
          try {
            node.entry_conditions = el.value.trim() ? JSON.parse(el.value) : [];
          } catch (e) {
            node.entry_conditions = [];
          }
        }
        if (field === "exit_conditions") {
          try {
            node.exit_conditions = el.value.trim() ? JSON.parse(el.value) : [];
          } catch (e) {
            node.exit_conditions = [];
          }
        }
        if (field === "summary_requirements") {
          node.summary_requirements = el.value;
        }
        if (field === "story_requirements") {
          try {
            node.story_requirements = el.value.trim() ? JSON.parse(el.value) : {};
          } catch (e) {
            node.story_requirements = {};
          }
        }
        if (field === "branching") {
          try {
            node.branching = el.value.trim() ? JSON.parse(el.value) : {};
          } catch (e) {
            node.branching = {};
          }
        }
      });
      return node;
    });

    return {
      dungeon_id: dungeonId,
      name: name,
      description: description,
      level_min: levelMin,
      level_max: levelMax,
      global_rules: globalRules,
      nodes: nodes
    };
  }

  async function saveDungeon() {
    const dun = collectDungeonFromEditor();
    if (!dun.dungeon_id) {
      statusEl.textContent = "请填写副本 ID。";
      return;
    }
    statusEl.textContent = "正在保存副本...";
    try {
      const resp = await fetch("/api/dungeon/" + encodeURIComponent(dun.dungeon_id), {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(dun)
      });
      if (!resp.ok) {
        const t = await resp.text();
        throw new Error("HTTP " + resp.status + " " + t);
      }
      statusEl.textContent = "保存成功。";
      dungeonCache[dun.dungeon_id] = dun;
      loadDungeonList();
    } catch (err) {
      console.error(err);
      statusEl.textContent = "保存失败：" + err.message;
    }
  }

  function bindEvents() {
    newBtn.addEventListener("click", newDungeon);
    saveBtn.addEventListener("click", saveDungeon);
    addNodeBtn.addEventListener("click", function () {
      const node = {
        node_id: "",
        name: "",
        index: nodesContainerEl.children.length + 1,
        progress_percent: 0,
        entry_conditions: [],
        exit_conditions: [],
        summary_requirements: "",
        story_requirements: {},
        branching: {}
      };
      const nodeEl = createNodeBlock(node);
      nodesContainerEl.appendChild(nodeEl);
    });
  }

  function init() {
    bindEvents();
    loadDungeonList();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
