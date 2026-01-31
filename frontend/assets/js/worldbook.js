(function () {
  const fileInput = document.getElementById("worldbook-file-input");
  const importBtn = document.getElementById("worldbook-import-btn");
  const importStatusEl = document.getElementById("worldbook-import-status");

  const searchKeywordEl = document.getElementById("worldbook-search-keyword");
  const searchCategoryEl = document.getElementById("worldbook-search-category");
  const searchBtn = document.getElementById("worldbook-search-btn");

  const tableBodyEl = document.getElementById("worldbook-table-body");
  const pageInfoEl = document.getElementById("worldbook-page-info");
  const prevPageBtn = document.getElementById("worldbook-prev-page");
  const nextPageBtn = document.getElementById("worldbook-next-page");

  const detailEl = document.getElementById("worldbook-detail");

  let currentPage = 1;
  let lastKeyword = "";
  let lastCategory = "";

  async function importWorldbook() {
    const file = fileInput.files[0];
    if (!file) {
      importStatusEl.textContent = "请选择 JSON 文件。";
      return;
    }

    importStatusEl.textContent = "正在读取文件...";
    try {
      const text = await file.text();
      let jsonData;
      try {
        jsonData = JSON.parse(text);
      } catch (e) {
        importStatusEl.textContent = "文件不是合法的 JSON。";
        return;
      }

      importStatusEl.textContent = "正在上传至后端...";
      const resp = await fetch("/api/worldbook/import", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(jsonData)
      });

      if (!resp.ok) {
        const msg = await resp.text();
        throw new Error("HTTP " + resp.status + " " + msg);
      }

      importStatusEl.textContent = "导入成功。";
      currentPage = 1;
      loadWorldbookList();
    } catch (err) {
      console.error(err);
      importStatusEl.textContent = "导入失败：" + err.message;
    }
  }

  async function loadWorldbookList() {
    const keyword = searchKeywordEl.value.trim();
    const category = searchCategoryEl.value;
    lastKeyword = keyword;
    lastCategory = category;

    const params = new URLSearchParams();
    params.set("page", String(currentPage));
    if (keyword) params.set("keyword", keyword);
    if (category) params.set("category", category);

    try {
      const resp = await fetch("/api/worldbook/list?" + params.toString());
      if (!resp.ok) {
        throw new Error("HTTP " + resp.status);
      }
      const data = await resp.json();

      const entries = data.items || [];
      tableBodyEl.innerHTML = "";
      entries.forEach(function (entry) {
        const tr = document.createElement("tr");
        tr.dataset.entryId = entry.entry_id;

        const tdId = document.createElement("td");
        tdId.textContent = entry.entry_id;

        const tdCat = document.createElement("td");
        tdCat.textContent = entry.category;

        const tdTitle = document.createElement("td");
        tdTitle.textContent = entry.title;

        const tdImp = document.createElement("td");
        tdImp.textContent = typeof entry.importance === "number" ? entry.importance.toFixed(2) : "";

        tr.appendChild(tdId);
        tr.appendChild(tdCat);
        tr.appendChild(tdTitle);
        tr.appendChild(tdImp);

        tr.addEventListener("click", function () {
          loadWorldbookDetail(entry.entry_id);
        });

        tableBodyEl.appendChild(tr);
      });

      const page = data.page || currentPage;
      const totalPages = data.total_pages || page;
      currentPage = page;
      pageInfoEl.textContent = "第 " + page + " 页 / 共 " + totalPages + " 页";

      prevPageBtn.disabled = page <= 1;
      nextPageBtn.disabled = page >= totalPages;
    } catch (err) {
      console.error(err);
      tableBodyEl.innerHTML = "";
      const tr = document.createElement("tr");
      const td = document.createElement("td");
      td.colSpan = 4;
      td.textContent = "加载失败：" + err.message;
      tr.appendChild(td);
      tableBodyEl.appendChild(tr);
    }
  }

  async function loadWorldbookDetail(entryId) {
    detailEl.textContent = "加载中：" + entryId + "...";
    try {
      const resp = await fetch("/api/worldbook/" + encodeURIComponent(entryId));
      if (!resp.ok) {
        throw new Error("HTTP " + resp.status);
      }
      const data = await resp.json();

      const content = data.content || "";
      const tags = data.tags || [];
      const meta = data.meta || {};

      const html = [
        "<div><strong>ID：</strong>" + escapeHtml(data.entry_id || "") + "</div>",
        "<div><strong>类别：</strong>" + escapeHtml(data.category || "") + "</div>",
        "<div><strong>标题：</strong>" + escapeHtml(data.title || "") + "</div>",
        "<div><strong>标签：</strong>" + escapeHtml(tags.join(", ")) + "</div>",
        "<div><strong>重要度：</strong>" + (typeof data.importance === "number" ? data.importance.toFixed(2) : "") + "</div>",
        "<hr>",
        "<div><strong>内容：</strong></div>",
        "<pre class=\"small-text\">" + escapeHtml(content) + "</pre>",
        "<hr>",
        "<div><strong>元信息：</strong></div>",
        "<pre class=\"small-text\">" + escapeHtml(JSON.stringify(meta, null, 2)) + "</pre>"
      ].join("\n");

      detailEl.innerHTML = html;
    } catch (err) {
      console.error(err);
      detailEl.textContent = "详情加载失败：" + err.message;
    }
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function bindEvents() {
    importBtn.addEventListener("click", importWorldbook);
    searchBtn.addEventListener("click", function () {
      currentPage = 1;
      loadWorldbookList();
    });
    prevPageBtn.addEventListener("click", function () {
      if (currentPage > 1) {
        currentPage -= 1;
        loadWorldbookList();
      }
    });
    nextPageBtn.addEventListener("click", function () {
      currentPage += 1;
      loadWorldbookList();
    });
  }

  function init() {
    bindEvents();
    loadWorldbookList();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
