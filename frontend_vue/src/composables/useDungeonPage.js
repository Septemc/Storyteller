import { computed, ref } from 'vue';
import * as dungeonApi from '../services/modules/dungeon';
import * as storyApi from '../services/modules/story';
import { useSessionStore } from '../stores/session';

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function emptyDungeon(id = '') {
  return {
    dungeon_id: id,
    name: '',
    description: '',
    level_min: 1,
    level_max: 5,
    global_rules: {},
    nodes: [],
  };
}

function emptyScript(id = '') {
  return {
    script_id: id,
    name: '',
    description: '',
    dungeon_ids: [],
    meta: {},
  };
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

export function useDungeonPage() {
  const sessionStore = useSessionStore();
  const scripts = ref([]);
  const dungeons = ref([]);
  const selectedScriptId = ref('');
  const selectedDungeonId = ref('');
  const selectedNodeId = ref('');
  const mode = ref('preview');
  const searchKeyword = ref('');
  const statusText = ref('当前剧本：未加载');
  const scriptDraft = ref(emptyScript());
  const dungeonDraft = ref(emptyDungeon());

  const selectedScript = computed(() => scripts.value.find((item) => item.script_id === selectedScriptId.value) || null);
  const selectedDungeon = computed(() => dungeons.value.find((item) => item.dungeon_id === selectedDungeonId.value) || null);
  const selectedNode = computed(() => selectedDungeon.value?.nodes.find((item) => item.node_id === selectedNodeId.value) || null);
  const detailTitle = computed(() => selectedNode.value?.name || selectedDungeon.value?.name || selectedScript.value?.name || '内容预览');
  const filteredNodes = computed(() => {
    const keyword = searchKeyword.value.trim().toLowerCase();
    if (!selectedDungeon.value) return [];
    if (!keyword) return selectedDungeon.value.nodes || [];
    return (selectedDungeon.value.nodes || []).filter((node) => `${node.node_id} ${node.name}`.toLowerCase().includes(keyword));
  });

  async function loadScripts() {
    const response = await dungeonApi.listScripts();
    scripts.value = response?.items || [];
  }

  async function loadDungeons() {
    const response = await dungeonApi.listDungeons();
    const items = response?.items || response?.dungeons || [];
    const details = await Promise.all(items.map((item) => dungeonApi.getDungeon(item.dungeon_id)));
    dungeons.value = details;
  }

  async function selectScript(scriptId) {
    if (!scriptId) return;
    selectedScriptId.value = scriptId;
    const detail = await dungeonApi.getScript(scriptId);
    scriptDraft.value = clone(detail);

    const firstDungeonId = detail.dungeon_ids?.[0] || '';
    if (firstDungeonId) {
      await selectDungeon(firstDungeonId);
    } else {
      selectedDungeonId.value = '';
      selectedNodeId.value = '';
      dungeonDraft.value = emptyDungeon();
    }
    mode.value = 'preview';
  }

  async function selectDungeon(dungeonId) {
    if (!dungeonId) return;
    selectedDungeonId.value = dungeonId;
    dungeonDraft.value = clone(await dungeonApi.getDungeon(dungeonId));
    selectedNodeId.value = '';
  }

  function selectNode(nodeId) {
    selectedNodeId.value = nodeId;
  }

  async function applyScript() {
    if (!selectedDungeonId.value) return;
    sessionStore.bootstrap();
    await storyApi.updateSessionContext({
      session_id: sessionStore.currentSessionId,
      current_script_id: selectedScriptId.value || undefined,
      current_dungeon_id: selectedDungeonId.value,
      current_node_id: selectedNodeId.value || undefined,
    });
    statusText.value = `当前剧本：${selectedScript.value?.name || selectedDungeon.value?.name || selectedDungeonId.value}`;
  }

  function createScript() {
    const scriptId = `script_${Date.now()}`;
    scriptDraft.value = emptyScript(scriptId);
    selectedScriptId.value = '';
    mode.value = 'edit';
    statusText.value = `已创建剧本草稿 ${scriptId}`;
  }

  function createDungeon() {
    const dungeonId = `dungeon_${Date.now()}`;
    dungeonDraft.value = emptyDungeon(dungeonId);
    if (!scriptDraft.value.script_id) {
      scriptDraft.value = emptyScript(`script_${Date.now()}`);
    }
    selectedDungeonId.value = '';
    selectedNodeId.value = '';
    mode.value = 'edit';
    statusText.value = `已创建副本草稿 ${dungeonId}`;
  }

  function createNode() {
    dungeonDraft.value.nodes.push({
      node_id: `node_${Date.now()}`,
      name: '新节点',
      index: dungeonDraft.value.nodes.length,
      progress_percent: 0,
      entry_conditions: [],
      exit_conditions: [],
      summary_requirements: '',
      story_requirements: {},
      branching: {},
    });
    selectedNodeId.value = dungeonDraft.value.nodes[dungeonDraft.value.nodes.length - 1].node_id;
    mode.value = 'edit';
  }

  async function saveDetail() {
    if (!dungeonDraft.value.dungeon_id.trim()) {
      throw new Error('副本 ID 不能为空');
    }
    if (!scriptDraft.value.script_id.trim()) {
      throw new Error('剧本 ID 不能为空');
    }

    const savedDungeon = await dungeonApi.upsertDungeon(dungeonDraft.value.dungeon_id, dungeonDraft.value);
    dungeonDraft.value = clone(savedDungeon);
    selectedDungeonId.value = savedDungeon.dungeon_id;

    if (!scriptDraft.value.dungeon_ids.includes(selectedDungeonId.value)) {
      scriptDraft.value.dungeon_ids = [...scriptDraft.value.dungeon_ids, selectedDungeonId.value];
    }

    const savedScript = await dungeonApi.upsertScript(scriptDraft.value.script_id, scriptDraft.value);
    scriptDraft.value = clone(savedScript);
    selectedScriptId.value = savedScript.script_id;

    await Promise.all([loadScripts(), loadDungeons()]);
    await selectScript(selectedScriptId.value);
    statusText.value = '保存完成';
    mode.value = 'preview';
  }

  async function deleteCurrent() {
    if (selectedNodeId.value) {
      if (!confirmAction(`确认删除节点 ${selectedNodeId.value} 吗？`)) return;
      dungeonDraft.value.nodes = dungeonDraft.value.nodes.filter((item) => item.node_id !== selectedNodeId.value);
      selectedNodeId.value = '';
      statusText.value = '节点已移除，保存后生效';
      return;
    }

    if (selectedDungeonId.value) {
      if (!confirmAction(`确认删除副本 ${selectedDungeonId.value} 吗？`)) return;
      await dungeonApi.deleteDungeon(selectedDungeonId.value);
      if (scriptDraft.value.dungeon_ids.includes(selectedDungeonId.value)) {
        scriptDraft.value.dungeon_ids = scriptDraft.value.dungeon_ids.filter((item) => item !== selectedDungeonId.value);
        if (selectedScriptId.value) {
          await dungeonApi.upsertScript(selectedScriptId.value, scriptDraft.value);
        }
      }
      selectedDungeonId.value = '';
      selectedNodeId.value = '';
      dungeonDraft.value = emptyDungeon();
      await Promise.all([loadScripts(), loadDungeons()]);
      if (selectedScriptId.value) {
        await selectScript(selectedScriptId.value);
      }
      statusText.value = '副本已删除';
      return;
    }

    if (selectedScriptId.value) {
      if (!confirmAction(`确认删除剧本 ${selectedScriptId.value} 吗？`)) return;
      await dungeonApi.deleteScript(selectedScriptId.value);
      selectedScriptId.value = '';
      scriptDraft.value = emptyScript();
      dungeonDraft.value = emptyDungeon();
      await loadScripts();
      statusText.value = '剧本已删除';
    }
  }

  async function importJson(fileList, importMode = 'script') {
    const file = Array.from(fileList || [])[0];
    if (!file) return;
    const parsed = JSON.parse(await file.text());

    if (importMode === 'node') {
      const node = clone(parsed);
      dungeonDraft.value.nodes.push(node);
      selectedNodeId.value = node.node_id;
      mode.value = 'edit';
      statusText.value = `已导入节点 ${node.node_id}`;
      return;
    }

    if (parsed.nodes || importMode === 'dungeon') {
      dungeonDraft.value = clone(parsed);
      selectedDungeonId.value = parsed.dungeon_id || '';
      mode.value = 'edit';
      statusText.value = `已导入副本 ${parsed.dungeon_id || ''}`;
      return;
    }

    if (parsed.dungeon_ids || importMode === 'script') {
      scriptDraft.value = clone(parsed);
      selectedScriptId.value = parsed.script_id || '';
      mode.value = 'edit';
      statusText.value = `已导入剧本 ${parsed.script_id || ''}`;
    }
  }

  function exportCurrent() {
    if (selectedNode.value) {
      downloadJson(selectedNode.value, `${selectedNode.value.node_id}.json`);
      return;
    }
    if (selectedDungeonId.value) {
      downloadJson(dungeonDraft.value, `${dungeonDraft.value.dungeon_id || 'dungeon'}.json`);
      return;
    }
    if (selectedScriptId.value) {
      downloadJson(scriptDraft.value, `${scriptDraft.value.script_id || 'script'}.json`);
    }
  }

  async function bootstrap() {
    await Promise.all([loadScripts(), loadDungeons()]);
    if (scripts.value[0]) {
      await selectScript(scripts.value[0].script_id);
    } else {
      scriptDraft.value = emptyScript();
      dungeonDraft.value = emptyDungeon();
    }
  }

  return {
    applyScript,
    bootstrap,
    createDungeon,
    createNode,
    createScript,
    deleteCurrent,
    detailTitle,
    dungeonDraft,
    exportCurrent,
    filteredNodes,
    importJson,
    mode,
    saveDetail,
    scriptDraft,
    scripts,
    searchKeyword,
    selectDungeon,
    selectedDungeon,
    selectedDungeonId,
    selectNode,
    selectedNode,
    selectedNodeId,
    selectScript,
    selectedScript,
    selectedScriptId,
    statusText,
  };
}
