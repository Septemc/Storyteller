import { request } from '../http';

export function listScripts() {
  return request('/api/scripts');
}

export function getScript(scriptId) {
  return request(`/api/scripts/${encodeURIComponent(scriptId)}`);
}

export function upsertScript(scriptId, payload) {
  return request(`/api/scripts/${encodeURIComponent(scriptId)}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}

export function deleteScript(scriptId) {
  return request(`/api/scripts/${encodeURIComponent(scriptId)}`, {
    method: 'DELETE',
  });
}

export function listDungeons() {
  return request('/api/dungeon/list');
}

export function getDungeon(dungeonId) {
  return request(`/api/dungeon/${encodeURIComponent(dungeonId)}`);
}

export function upsertDungeon(dungeonId, payload) {
  return request(`/api/dungeon/${encodeURIComponent(dungeonId)}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}

export function deleteDungeon(dungeonId) {
  return request(`/api/dungeon/${encodeURIComponent(dungeonId)}`, {
    method: 'DELETE',
  });
}
