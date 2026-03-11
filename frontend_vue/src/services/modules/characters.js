import { request, toQuery } from '../http';

export function listCharacters(q = '') {
  return request(`/api/characters${toQuery({ q })}`);
}

export function getCharacter(characterId) {
  return request(`/api/characters/${encodeURIComponent(characterId)}`);
}

export function importCharacters(payload) {
  return request('/api/characters/import', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function updateCharacter(characterId, payload) {
  return request(`/api/characters/${encodeURIComponent(characterId)}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}

export function deleteCharacter(characterId) {
  return request(`/api/characters/${encodeURIComponent(characterId)}`, {
    method: 'DELETE',
  });
}

export function clearAllCharacters() {
  return request('/api/characters/clear_all', {
    method: 'DELETE',
  });
}

export function exportAllCharacters() {
  return request('/api/characters/export/all');
}

