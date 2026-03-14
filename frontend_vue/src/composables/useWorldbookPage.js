import { computed, ref } from 'vue';
import * as worldbookApi from '../services/modules/worldbook';
import * as settingsApi from '../services/modules/settings';

const META_STORAGE_KEY = 'storyteller_worldbook_meta_v2';
const APPLIED_WORLD_IDS_STORAGE_KEY = 'storyteller_applied_world_ids_v1';
const CATEGORY_SWITCH_STORAGE_KEY = 'storyteller_worldbook_category_switches_v1';
const LEGACY_WORLDBOOK_STORAGE_KEY = 'st_worldbooks_data';

function readJson(storageKey, fallback) {
  try {
    const raw = localStorage.getItem(storageKey);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

function writeJson(storageKey, value) {
  localStorage.setItem(storageKey, JSON.stringify(value));
}

function readMetaMap() {
  const current = readJson(META_STORAGE_KEY, {});
  if (current && typeof current === 'object' && Object.keys(current).length) {
    return current;
  }

  const legacyWorlds = readJson(LEGACY_WORLDBOOK_STORAGE_KEY, []);
  if (!Array.isArray(legacyWorlds) || !legacyWorlds.length) {
    return {};
  }

  const migrated = legacyWorlds.reduce((result, world) => {
    const worldId = String(world?.id || '').trim();
    if (!worldId) return result;
    const name = String(world?.name || '').trim();
    const description = String(world?.description || '').trim();
    if (!name && !description) return result;

    result[worldId] = {
      name: name || worldId,
      description,
    };
    return result;
  }, {});

  if (Object.keys(migrated).length) {
    writeMetaMap(migrated);
  }
  return migrated;
}

function writeMetaMap(map) {
  writeJson(META_STORAGE_KEY, map);
}

function readAppliedWorldIds() {
  const value = readJson(APPLIED_WORLD_IDS_STORAGE_KEY, []);
  return Array.isArray(value) ? value.filter(Boolean) : [];
}

function writeAppliedWorldIds(ids) {
  writeJson(APPLIED_WORLD_IDS_STORAGE_KEY, ids);
}

function readCategorySwitchMap() {
  const value = readJson(CATEGORY_SWITCH_STORAGE_KEY, {});
  return value && typeof value === 'object' ? value : {};
}

function writeCategorySwitchMap(map) {
  writeJson(CATEGORY_SWITCH_STORAGE_KEY, map);
}

function normalizeServerWorldbookSettings(response) {
  const worldbook = response && typeof response.worldbook === 'object' ? response.worldbook : {};
  return {
    activeWorldbookId: String(worldbook.active_worldbook_id || '').trim(),
    categorySwitches: worldbook.category_switches && typeof worldbook.category_switches === 'object'
      ? worldbook.category_switches
      : {},
  };
}

function normalizeAppliedWorldIds(ids, validWorldIds = []) {
  const validSet = new Set(validWorldIds.filter(Boolean));
  const normalized = Array.isArray(ids) ? ids.filter((id) => validSet.has(id)) : [];
  if (!normalized.length) return [];
  return [normalized[normalized.length - 1]];
}

function normalizeEntry(item = {}) {
  const meta = item.meta && typeof item.meta === 'object' ? item.meta : {};
  const enabled = item.enabled !== undefined ? Boolean(item.enabled) : meta.enabled !== false;
  const disable = item.disable !== undefined ? Boolean(item.disable) : Boolean(meta.disable ?? item.disabled);

  return {
    worldbook_id: item.worldbook_id || '',
    entry_id: item.entry_id || item.id || '',
    category: item.category || item.module || '',
    title: item.title || item.comment || item.name || '',
    content: item.content || item.text || '',
    importance: Number(item.importance ?? 0.5),
    tags: Array.isArray(item.tags)
      ? item.tags
      : Array.isArray(item.key)
        ? item.key.filter(Boolean)
        : String(item.tags || item.key || '')
            .split(',')
            .map((value) => value.trim())
            .filter(Boolean),
    canonical: Boolean(item.canonical),
    enabled,
    disable,
    meta,
  };
}

function createEmptyImportedWorld(name, description = '') {
  return {
    name: name || '未命名世界书',
    description: description || '',
    categories: {},
    categoryMeta: {},
  };
}

function ensureImportedCategory(world, categoryName) {
  const safeCategory = categoryName || '未分类';
  if (!world.categories[safeCategory]) {
    world.categories[safeCategory] = [];
  }
  if (!world.categoryMeta[safeCategory]) {
    world.categoryMeta[safeCategory] = { description: '' };
  }
}

function pushImportedEntry(world, categoryName, source) {
  const normalized = normalizeEntry(source);
  const safeCategory = categoryName || normalized.category || '未分类';
  ensureImportedCategory(world, safeCategory);
  world.categories[safeCategory].push({
    entry_id: normalized.entry_id,
    category: safeCategory,
    title: normalized.title || '未命名条目',
    content: normalized.content || '',
    tags: normalized.tags,
    importance: normalized.importance,
    canonical: normalized.canonical,
    enabled: normalized.enabled,
    disable: normalized.disable,
    meta: {
      ...normalized.meta,
      enabled: normalized.enabled,
      disable: normalized.disable,
    },
  });
}

function normalizeImportedWorlds(raw, fileName = 'worldbook') {
  const baseName = String(fileName || 'worldbook').replace(/\.[^.]+$/, '') || 'worldbook';
  const result = [];

  if (raw && typeof raw === 'object' && !Array.isArray(raw) && raw.entries && typeof raw.entries === 'object' && !Array.isArray(raw.entries)) {
    const world = createEmptyImportedWorld(raw.name || raw.title || baseName, raw.description || raw.comment || '');
    Object.values(raw.entries).forEach((item) => {
      const category = Array.isArray(item?.key) && item.key.length ? item.key[0] : item?.category || '未分类';
      pushImportedEntry(world, category, item);
    });
    result.push(world);
    return result;
  }

  if (raw && typeof raw === 'object' && !Array.isArray(raw) && (raw.categories || raw.modules)) {
    const world = createEmptyImportedWorld(raw.name || raw.title || baseName, raw.description || raw.summary || '');
    const container = raw.categories || raw.modules;

    if (Array.isArray(container)) {
      container.forEach((categoryObject) => {
        const categoryName = categoryObject?.name || categoryObject?.title || '未命名模块';
        ensureImportedCategory(world, categoryName);
        if (categoryObject?.description) {
          world.categoryMeta[categoryName].description = String(categoryObject.description);
        }
        const entries = categoryObject?.entries || categoryObject?.items || [];
        if (Array.isArray(entries)) {
          entries.forEach((item) => pushImportedEntry(world, categoryName, item));
        }
      });
    } else {
      Object.entries(container).forEach(([categoryName, value]) => {
        ensureImportedCategory(world, categoryName);
        if (value && typeof value === 'object' && !Array.isArray(value) && typeof value.description === 'string') {
          world.categoryMeta[categoryName].description = value.description;
        }
        const entries =
          value && typeof value === 'object' && !Array.isArray(value) && Array.isArray(value.entries)
            ? value.entries
            : Array.isArray(value)
              ? value
              : [];
        entries.forEach((item) => pushImportedEntry(world, categoryName, item));
      });
    }

    result.push(world);
    return result;
  }

  if (raw && typeof raw === 'object' && Array.isArray(raw.worlds)) {
    raw.worlds.forEach((worldItem, index) => {
      const world = createEmptyImportedWorld(worldItem.name || `${baseName}-${index + 1}`, worldItem.description || worldItem.summary || '');
      const container = worldItem.categories || worldItem.modules;
      if (!container) {
        result.push(world);
        return;
      }

      if (Array.isArray(container)) {
        container.forEach((categoryObject) => {
          const categoryName = categoryObject?.name || categoryObject?.title || '未命名模块';
          ensureImportedCategory(world, categoryName);
          if (categoryObject?.description) {
            world.categoryMeta[categoryName].description = String(categoryObject.description);
          }
          const entries = categoryObject?.entries || categoryObject?.items || [];
          if (Array.isArray(entries)) {
            entries.forEach((item) => pushImportedEntry(world, categoryName, item));
          }
        });
      } else {
        Object.entries(container).forEach(([categoryName, value]) => {
          ensureImportedCategory(world, categoryName);
          if (value && typeof value === 'object' && !Array.isArray(value) && typeof value.description === 'string') {
            world.categoryMeta[categoryName].description = value.description;
          }
          const entries =
            value && typeof value === 'object' && !Array.isArray(value) && Array.isArray(value.entries)
              ? value.entries
              : Array.isArray(value)
                ? value
                : [];
          entries.forEach((item) => pushImportedEntry(world, categoryName, item));
        });
      }

      result.push(world);
    });
    return result;
  }

  if (Array.isArray(raw)) {
    const world = createEmptyImportedWorld(baseName, '');
    raw.forEach((item) => {
      if (!item || typeof item !== 'object') return;
      pushImportedEntry(world, item.category || item.module || '未分类', item);
    });
    result.push(world);
    return result;
  }

  if (raw && typeof raw === 'object' && (raw.title || raw.content || raw.text)) {
    const world = createEmptyImportedWorld(baseName, '');
    pushImportedEntry(world, raw.category || raw.module || '未分类', raw);
    result.push(world);
    return result;
  }

  const world = createEmptyImportedWorld(baseName, '');
  pushImportedEntry(world, '默认模块', {
    title: '原始数据',
    content: JSON.stringify(raw, null, 2),
    tags: [],
    meta: {},
  });
  result.push(world);
  return result;
}

function buildEntriesForImport(world) {
  const entries = [];
  Object.entries(world.categories || {}).forEach(([categoryName, categoryEntries]) => {
    if (!Array.isArray(categoryEntries)) return;
    categoryEntries.forEach((item) => {
      const normalized = normalizeEntry(item);
      entries.push({
        entry_id: normalized.entry_id || undefined,
        category: categoryName,
        title: normalized.title || '未命名条目',
        content: normalized.content || '',
        tags: normalized.tags,
        importance: normalized.importance,
        canonical: normalized.canonical,
        meta: {
          ...normalized.meta,
          enabled: normalized.enabled,
          disable: normalized.disable,
        },
      });
    });
  });
  return entries;
}

function flattenImportedWorlds(worlds, targetCategory = '') {
  const entries = [];
  worlds.forEach((world) => {
    Object.entries(world.categories || {}).forEach(([categoryName, categoryEntries]) => {
      if (!Array.isArray(categoryEntries)) return;
      categoryEntries.forEach((item) => {
        const normalized = normalizeEntry(item);
        entries.push({
          entry_id: normalized.entry_id || undefined,
          category: targetCategory || categoryName || normalized.category || '未分类',
          title: normalized.title || '未命名条目',
          content: normalized.content || '',
          tags: normalized.tags,
          importance: normalized.importance,
          canonical: normalized.canonical,
          meta: {
            ...normalized.meta,
            enabled: normalized.enabled,
            disable: normalized.disable,
          },
        });
      });
    });
  });
  return entries;
}

function groupEntries(items) {
  const worldsMap = new Map();
  for (const rawItem of items || []) {
    const item = normalizeEntry(rawItem);
    if (!item.worldbook_id) continue;

    if (!worldsMap.has(item.worldbook_id)) {
      worldsMap.set(item.worldbook_id, {
        id: item.worldbook_id,
        entries: [],
        categories: {},
      });
    }

    const world = worldsMap.get(item.worldbook_id);
    const category = item.category || '未分类';
    if (!world.categories[category]) {
      world.categories[category] = [];
    }
    world.entries.push(item);
    world.categories[category].push(item);
  }
  return [...worldsMap.values()];
}

function downloadJson(data, fileName) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = fileName;
  anchor.click();
  URL.revokeObjectURL(url);
}

function confirmAction(message) {
  if (typeof window !== 'undefined' && typeof window.confirm === 'function') {
    return window.confirm(message);
  }
  return true;
}

export function useWorldbookPage() {
  const worlds = ref([]);
  const loadingWorlds = ref(false);
  const selectedWorldId = ref('');
  const appliedWorldIds = ref(readAppliedWorldIds());
  const categorySwitchMap = ref(readCategorySwitchMap());
  const selectedCategory = ref('');
  const selectedEntryId = ref('');
  const mode = ref('preview');
  const searchKeyword = ref('');
  const useSemanticSearch = ref(false);
  const detailDraft = ref({
    worldbook_id: '',
    entry_id: '',
    category: '',
    title: '',
    content: '',
    importance: 0.5,
    tags: [],
    canonical: false,
    meta: {},
  });
  const metaText = ref('{}');
  const statusText = ref('');
  const metaMap = ref(readMetaMap());
  const expandedCategoryKeys = ref({});
  let loadWorldsRequestId = 0;

  const selectedWorld = computed(() => worlds.value.find((item) => item.id === selectedWorldId.value) || null);
  const selectedWorldApplied = computed(() => appliedWorldIds.value.includes(selectedWorldId.value));
  const worldStats = computed(() => {
    const totalEntries = worlds.value.reduce((sum, world) => sum + (world.entries?.length || 0), 0);
    const totalModules = worlds.value.reduce((sum, world) => sum + Object.keys(world.categories || {}).length, 0);
    return {
      totalWorlds: worlds.value.length,
      totalEntries,
      totalModules,
    };
  });
  const worldOptions = computed(() =>
    worlds.value.map((world) => ({
      id: world.id,
      name: metaMap.value[world.id]?.name || world.id,
      description: metaMap.value[world.id]?.description || '',
      count: world.entries.length,
      applied: appliedWorldIds.value.includes(world.id),
    })),
  );
  const appliedWorldSummary = computed(() => {
    if (!appliedWorldIds.value.length) {
      return '尚未启用任何世界书';
    }
    return appliedWorldIds.value
      .map((id) => metaMap.value[id]?.name || worldOptions.value.find((world) => world.id === id)?.name || id)
      .join(' / ');
  });
  const selectedEntry = computed(() => {
    if (!selectedWorld.value || !selectedEntryId.value) return null;
    return selectedWorld.value.entries.find((item) => item.entry_id === selectedEntryId.value) || null;
  });
  const currentDetailTitle = computed(() => {
    if (selectedEntry.value) return selectedEntry.value.title;
    if (selectedCategory.value) return selectedCategory.value;
    if (selectedWorld.value) return metaMap.value[selectedWorld.value.id]?.name || selectedWorld.value.id;
    return '内容预览';
  });
  const selectedWorldDescription = computed(() => {
    const world = selectedWorld.value;
    if (!world) return '';

    const savedDescription = metaMap.value[world.id]?.description?.trim();
    if (savedDescription) {
      return savedDescription;
    }

    const entryCount = world.entries?.length || 0;
    const moduleCount = Object.keys(world.categories || {}).length;
    return `当前世界书包含 ${entryCount} 条条目，${moduleCount} 个模块。`;
  });
  const selectedWorldStatsText = computed(() => {
    const world = selectedWorld.value;
    if (!world) return '';
    const entryCount = world.entries?.length || 0;
    const moduleCount = Object.keys(world.categories || {}).length;
    const enabledText = selectedWorldApplied.value ? '已启用' : '未启用';
    return `${entryCount} 条 / ${moduleCount} 个模块 / ${enabledText}`;
  });
  const selectedWorldModules = computed(() => {
    const world = selectedWorld.value;
    if (!world) return [];

    const keyword = searchKeyword.value.trim().toLowerCase();
    const categoryNames = Object.keys(world.categories || {}).sort((left, right) => left.localeCompare(right, 'zh-Hans-CN'));

    return categoryNames
      .map((categoryName) => {
        const categoryKey = `${world.id}::${categoryName}`;
        const categoryEnabled = categorySwitchMap.value[categoryKey] !== false;
        const sourceEntries = Array.isArray(world.categories[categoryName]) ? world.categories[categoryName] : [];
        const filteredEntries = sourceEntries.filter((entry) => {
          if (!keyword) return true;
          const haystack = `${entry.title} ${entry.content} ${(entry.tags || []).join(' ')} ${categoryName}`.toLowerCase();
          return haystack.includes(keyword);
        });
        if (!filteredEntries.length && keyword) {
          return null;
        }

        return {
          key: categoryKey,
          name: categoryName,
          description: '',
          enabled: categoryEnabled,
          effectiveEnabled: selectedWorldApplied.value && categoryEnabled,
          isExpanded: expandedCategoryKeys.value[categoryKey] ?? (selectedCategory.value === categoryName || !!keyword),
          count: filteredEntries.length,
          entries: filteredEntries.map((entry) => {
            const entryEnabled = entry.enabled !== false && entry.disable !== true;
            return {
              ...entry,
              enabled: entryEnabled,
              effectiveEnabled: selectedWorldApplied.value && categoryEnabled && entryEnabled,
            };
          }),
        };
      })
      .filter(Boolean);
  });

  function syncDraftFromEntry(entry) {
    const normalized = normalizeEntry(entry);
    detailDraft.value = {
      ...normalized,
      category: normalized.category || '',
    };
    metaText.value = JSON.stringify(detailDraft.value.meta || {}, null, 2);
  }

  function syncDraftForScope(worldId, category = '') {
    detailDraft.value = {
      worldbook_id: worldId || '',
      entry_id: '',
      category: category || '',
      title: '',
      content: '',
      importance: 0.5,
      tags: [],
      canonical: false,
      meta: {},
    };
    metaText.value = '{}';
  }

  async function persistWorldbookStateToServer() {
    const currentSettings = await settingsApi.getGlobalSettings().catch(() => ({}));
    const nextSettings = {
      ...(currentSettings || {}),
      worldbook: {
        ...((currentSettings && currentSettings.worldbook) || {}),
        active_worldbook_id: appliedWorldIds.value[0] || '',
        category_switches: { ...categorySwitchMap.value },
      },
    };
    await settingsApi.putGlobalSettings(nextSettings);
  }

  function persistAppliedWorldIds() {
    writeAppliedWorldIds(appliedWorldIds.value);
    return persistWorldbookStateToServer();
  }

  function persistCategorySwitchMap() {
    writeCategorySwitchMap(categorySwitchMap.value);
    return persistWorldbookStateToServer();
  }

  function setWorldApplied(worldId, enabled) {
    appliedWorldIds.value = enabled && worldId ? [worldId] : [];
    void persistAppliedWorldIds();
    statusText.value = enabled ? `已启用世界书 ${metaMap.value[worldId]?.name || worldId}` : `已停用世界书 ${metaMap.value[worldId]?.name || worldId}`;
  }

  function toggleSelectedWorldApplied(enabled) {
    if (!selectedWorldId.value) return;
    setWorldApplied(selectedWorldId.value, enabled);
  }

  function setCategoryEnabled(categoryName, enabled) {
    if (!selectedWorldId.value) return;
    categorySwitchMap.value = {
      ...categorySwitchMap.value,
      [`${selectedWorldId.value}::${categoryName}`]: enabled,
    };
    void persistCategorySwitchMap();
    statusText.value = enabled ? `已启用模块 ${categoryName}` : `已停用模块 ${categoryName}`;
  }

  function toggleCategoryExpanded(categoryName) {
    if (!selectedWorldId.value) return;
    const key = `${selectedWorldId.value}::${categoryName}`;
    expandedCategoryKeys.value = {
      ...expandedCategoryKeys.value,
      [key]: !(expandedCategoryKeys.value[key] ?? false),
    };
  }

  function updateLocalEntry(worldId, entryId, updater) {
    const world = worlds.value.find((item) => item.id === worldId);
    if (!world) return null;

    let updatedEntry = null;
    Object.keys(world.categories || {}).forEach((categoryName) => {
      world.categories[categoryName] = world.categories[categoryName].map((entry) => {
        if (entry.entry_id !== entryId) return entry;
        updatedEntry = updater(entry);
        return updatedEntry;
      });
    });
    world.entries = world.entries.map((entry) => {
      if (entry.entry_id !== entryId) return entry;
      return updatedEntry || updater(entry);
    });
    return updatedEntry;
  }

  async function toggleEntryEnabled(entry, enabled) {
    const payload = {
      worldbook_id: entry.worldbook_id,
      entries: [
        {
          entry_id: entry.entry_id,
          category: entry.category || '未分类',
          title: entry.title,
          content: entry.content,
          importance: Number(entry.importance || 0.5),
          tags: entry.tags || [],
          canonical: Boolean(entry.canonical),
          meta: {
            ...(entry.meta || {}),
            enabled,
            disable: !enabled,
          },
        },
      ],
    };

    await worldbookApi.importWorldbook(payload, false);
    const updatedEntry = updateLocalEntry(entry.worldbook_id, entry.entry_id, (current) => ({
      ...current,
      enabled,
      disable: !enabled,
      meta: {
        ...(current.meta || {}),
        enabled,
        disable: !enabled,
      },
    }));

    if (selectedEntryId.value === entry.entry_id && updatedEntry) {
      syncDraftFromEntry(updatedEntry);
    }

    statusText.value = enabled ? `已启用条目 ${entry.title}` : `已停用条目 ${entry.title}`;
  }

  async function loadWorlds(keyword = searchKeyword.value.trim()) {
    const requestId = ++loadWorldsRequestId;
    loadingWorlds.value = true;

    try {
      let nextWorlds = [];

      if (useSemanticSearch.value && keyword) {
        const result = await worldbookApi.semanticSearchWorldbook({
          query: keyword,
          top_k: 100,
          use_hybrid: true,
        });
        nextWorlds = groupEntries(result.results || []);
      } else {
        let page = 1;
        let totalPages = 1;
        const collected = [];

        do {
          const result = await worldbookApi.listWorldbook({
            page,
            page_size: 1000,
            keyword,
          });
          collected.push(...(result.items || []));
          totalPages = Number(result.total_pages || 1);
          page += 1;
        } while (page <= totalPages);

        nextWorlds = groupEntries(collected);
      }

      if (requestId !== loadWorldsRequestId) {
        return;
      }

      worlds.value = nextWorlds;

      const validWorldIds = worlds.value.map((item) => item.id);
      appliedWorldIds.value = normalizeAppliedWorldIds(appliedWorldIds.value, validWorldIds);
      void persistAppliedWorldIds();

      if (!selectedWorldId.value && worlds.value[0]) {
        selectedWorldId.value = worlds.value[0].id;
      }
      if (selectedWorldId.value && !worlds.value.find((item) => item.id === selectedWorldId.value)) {
        selectedWorldId.value = worlds.value[0]?.id || '';
        selectedCategory.value = '';
        selectedEntryId.value = '';
      }
    } finally {
      if (requestId === loadWorldsRequestId) {
        loadingWorlds.value = false;
      }
    }
  }

  async function applySelection(worldId, category = '', entryId = '') {
    selectedWorldId.value = worldId || '';
    selectedCategory.value = category || '';
    selectedEntryId.value = entryId || '';

    if (!selectedWorldId.value) {
      syncDraftForScope('', '');
      return;
    }

    if (entryId) {
      const detail = await worldbookApi.getWorldbookEntry(entryId);
      syncDraftFromEntry(detail);
      return;
    }

    syncDraftForScope(selectedWorldId.value, selectedCategory.value);
  }

  function createWorldbook() {
    const newId = `W${Math.random().toString(36).slice(2, 9)}`;
    metaMap.value = {
      ...metaMap.value,
      [newId]: {
        name: newId,
        description: '',
      },
    };
    writeMetaMap(metaMap.value);
    selectedWorldId.value = newId;
    selectedCategory.value = '';
    selectedEntryId.value = '';
    syncDraftForScope(newId, '');
    mode.value = 'edit';
    statusText.value = `已创建世界书草稿 ${newId}`;
  }

  function updateWorldMeta(field, value) {
    if (!selectedWorldId.value) return;
    metaMap.value = {
      ...metaMap.value,
      [selectedWorldId.value]: {
        ...(metaMap.value[selectedWorldId.value] || { name: selectedWorldId.value, description: '' }),
        [field]: value,
      },
    };
    writeMetaMap(metaMap.value);
  }

  function createCategory() {
    if (!selectedWorldId.value) return;
    const name = window.prompt('输入模块名称');
    if (!name) return;
    selectedCategory.value = name;
    selectedEntryId.value = '';
    expandedCategoryKeys.value = {
      ...expandedCategoryKeys.value,
      [`${selectedWorldId.value}::${name}`]: true,
    };
    syncDraftForScope(selectedWorldId.value, name);
    mode.value = 'edit';
    statusText.value = `已创建模块草稿 ${name}`;
  }

  function createEntry() {
    if (!selectedWorldId.value) return;
    detailDraft.value = {
      worldbook_id: selectedWorldId.value,
      entry_id: '',
      category: selectedCategory.value || '未分类',
      title: '新条目',
      content: '',
      importance: 0.5,
      tags: [],
      canonical: false,
      meta: {},
    };
    metaText.value = '{}';
    selectedEntryId.value = '';
    mode.value = 'edit';
  }

  function updateMetaText(value) {
    metaText.value = value;
  }

  async function saveDetail() {
    if (!detailDraft.value.worldbook_id) {
      throw new Error('请先选择世界书');
    }
    if (!detailDraft.value.title.trim()) {
      throw new Error('条目标题不能为空');
    }

    let parsedMeta = {};
    try {
      parsedMeta = JSON.parse(metaText.value || '{}');
    } catch {
      throw new Error('Meta JSON 格式无效');
    }

    const payload = {
      worldbook_id: detailDraft.value.worldbook_id,
      entries: [
        {
          entry_id: detailDraft.value.entry_id || undefined,
          category: detailDraft.value.category || '未分类',
          title: detailDraft.value.title.trim(),
          content: detailDraft.value.content,
          importance: Number(detailDraft.value.importance || 0.5),
          tags: detailDraft.value.tags,
          canonical: Boolean(detailDraft.value.canonical),
          meta: parsedMeta,
        },
      ],
    };

    const result = await worldbookApi.importWorldbook(payload, false);
    await loadWorlds();

    const targetWorldId = result.worldbook_id || detailDraft.value.worldbook_id;
    selectedWorldId.value = targetWorldId;
    const refreshedWorld = worlds.value.find((item) => item.id === targetWorldId);
    const matchingEntry =
      refreshedWorld?.entries.find(
        (item) =>
          item.entry_id === detailDraft.value.entry_id ||
          (item.title === detailDraft.value.title.trim() && (item.category || '未分类') === (detailDraft.value.category || '未分类')),
      ) || null;

    if (matchingEntry) {
      await applySelection(targetWorldId, matchingEntry.category, matchingEntry.entry_id);
    } else {
      await applySelection(targetWorldId, detailDraft.value.category || '', '');
    }

    statusText.value = `已保存 ${detailDraft.value.title.trim()}`;
    mode.value = 'preview';
  }

  async function deleteSelection() {
    if (selectedEntryId.value) {
      if (!confirmAction(`确认删除条目 ${selectedEntryId.value} 吗？`)) return;
      await worldbookApi.deleteWorldbookEntry(selectedEntryId.value);
      statusText.value = `已删除条目 ${selectedEntryId.value}`;
    } else if (selectedCategory.value) {
      if (!confirmAction(`确认删除模块 ${selectedCategory.value} 吗？`)) return;
      await worldbookApi.deleteWorldbookCategory(selectedCategory.value, selectedWorldId.value);
      statusText.value = `已删除模块 ${selectedCategory.value}`;
    } else {
      return deleteWorldbook();
    }

    selectedCategory.value = '';
    selectedEntryId.value = '';
    await loadWorlds();
    await applySelection(selectedWorldId.value || worlds.value[0]?.id || '');
  }

  async function deleteWorldbook() {
    if (!selectedWorldId.value) return;
    if (!confirmAction(`确认删除世界书 ${selectedWorldId.value} 吗？`)) return;

    const deletingWorldId = selectedWorldId.value;
    await worldbookApi.deleteAllWorldbook(deletingWorldId);
    delete metaMap.value[deletingWorldId];
    writeMetaMap(metaMap.value);

    appliedWorldIds.value = appliedWorldIds.value.filter((id) => id !== deletingWorldId);
    void persistAppliedWorldIds();

    selectedWorldId.value = '';
    selectedCategory.value = '';
    selectedEntryId.value = '';
    statusText.value = `已删除世界书 ${deletingWorldId}`;

    await loadWorlds();
    const nextWorldId = worlds.value[0]?.id || '';
    await applySelection(nextWorldId);
  }

  async function importFiles(fileList, importMode = 'world') {
    const file = Array.from(fileList || [])[0];
    if (!file) return;
    const parsed = JSON.parse(await file.text());
    const importedWorlds = normalizeImportedWorlds(parsed, file.name);

    if (!importedWorlds.length) {
      throw new Error('未识别到可用的世界书结构');
    }

    if (importMode === 'world') {
      const importedIds = [];
      for (const world of importedWorlds) {
        const entries = buildEntriesForImport(world);
        if (!entries.length) continue;
        const result = await worldbookApi.importWorldbook({ entries }, false);
        importedIds.push(result.worldbook_id);
        metaMap.value = {
          ...metaMap.value,
          [result.worldbook_id]: {
            name: world.name || result.worldbook_id,
            description: world.description || '',
          },
        };
      }
      writeMetaMap(metaMap.value);
      selectedWorldId.value = importedIds[0] || '';
      statusText.value = importedIds.length ? `已导入 ${importedIds.length} 本世界书` : '导入完成，但没有可用条目';
    } else if (importMode === 'category') {
      if (!selectedWorldId.value) {
        throw new Error('请先选择目标世界书');
      }
      const entries = flattenImportedWorlds(importedWorlds);
      if (!entries.length) {
        throw new Error('导入文件中没有可用模块条目');
      }
      await worldbookApi.importWorldbook(
        {
          worldbook_id: selectedWorldId.value,
          entries,
        },
        false,
      );
      statusText.value = `已导入 ${entries.length} 条模块内容`;
    } else {
      if (!selectedWorldId.value) {
        throw new Error('请先选择目标世界书');
      }
      const entries = flattenImportedWorlds(importedWorlds, selectedCategory.value || '');
      if (!entries.length) {
        throw new Error('导入文件中没有可用条目');
      }
      await worldbookApi.importWorldbook(
        {
          worldbook_id: selectedWorldId.value,
          entries,
        },
        false,
      );
      statusText.value = `已导入 ${entries.length} 条条目`;
    }

    await loadWorlds();
    await applySelection(selectedWorldId.value || worlds.value[0]?.id || '');
  }

  function exportCurrentWorld() {
    if (!selectedWorld.value) return;
    downloadJson(
      {
        worldbook_id: selectedWorld.value.id,
        name: metaMap.value[selectedWorld.value.id]?.name || selectedWorld.value.id,
        description: metaMap.value[selectedWorld.value.id]?.description || '',
        entries: selectedWorld.value.entries,
      },
      `${selectedWorld.value.id}.json`,
    );
  }

  function exportCurrentSelection() {
    if (selectedEntry.value) {
      downloadJson(selectedEntry.value, `${selectedEntry.value.entry_id}.json`);
      return;
    }
    if (selectedCategory.value && selectedWorld.value?.categories[selectedCategory.value]) {
      downloadJson(
        {
          category: selectedCategory.value,
          entries: selectedWorld.value.categories[selectedCategory.value],
        },
        `${selectedCategory.value}.json`,
      );
      return;
    }
    exportCurrentWorld();
  }

  async function bootstrap() {
    const settingsResponse = await settingsApi.getGlobalSettings().catch(() => ({}));
    const serverState = normalizeServerWorldbookSettings(settingsResponse);
    if (serverState.activeWorldbookId) {
      appliedWorldIds.value = [serverState.activeWorldbookId];
    }
    categorySwitchMap.value = {
      ...categorySwitchMap.value,
      ...serverState.categorySwitches,
    };

    await loadWorlds();
    if (appliedWorldIds.value[0] && worlds.value.find((item) => item.id === appliedWorldIds.value[0])) {
      selectedWorldId.value = appliedWorldIds.value[0];
    } else if (!selectedWorldId.value && worlds.value[0]) {
      selectedWorldId.value = worlds.value[0].id;
    }
    if (selectedWorldId.value) {
      await applySelection(selectedWorldId.value);
    }
    statusText.value = `已加载 ${worldStats.value.totalWorlds} 本世界书，共 ${worldStats.value.totalEntries} 条条目`;
  }

  return {
    appliedWorldIds,
    appliedWorldSummary,
    bootstrap,
    createCategory,
    createEntry,
    createWorldbook,
    currentDetailTitle,
    deleteSelection,
    deleteWorldbook,
    detailDraft,
    exportCurrentSelection,
    exportCurrentWorld,
    importFiles,
    loadingWorlds,
    loadWorlds,
    metaMap,
    metaText,
    mode,
    saveDetail,
    searchKeyword,
    selectedCategory,
    selectedEntry,
    selectedEntryId,
    selectedWorld,
    selectedWorldApplied,
    selectedWorldId,
    selectedWorldModules,
    setCategoryEnabled,
    statusText,
    toggleCategoryExpanded,
    toggleEntryEnabled,
    toggleSelectedWorldApplied,
    updateMetaText,
    updateWorldMeta,
    useSemanticSearch,
    selectedWorldDescription,
    selectedWorldStatsText,
    worldOptions,
    worldStats,
    worlds,
    applySelection,
  };
}




