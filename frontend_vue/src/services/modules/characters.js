import { request, toQuery } from '../http';

export function listCharacters(sessionId, q = '') {
  return request(`/api/characters${toQuery({ session_id: sessionId, q })}`);
}

export function getCharacter(sessionId, characterId) {
  return request(`/api/characters/${encodeURIComponent(characterId)}${toQuery({ session_id: sessionId })}`);
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

export function deleteCharacter(sessionId, characterId) {
  return request(`/api/characters/${encodeURIComponent(characterId)}${toQuery({ session_id: sessionId })}`, {
    method: 'DELETE',
  });
}

export function clearAllCharacters(sessionId) {
  return request(`/api/characters/clear_all${toQuery({ session_id: sessionId })}`, {
    method: 'DELETE',
  });
}

export function exportAllCharacters(sessionId) {
  return request(`/api/characters/export/all${toQuery({ session_id: sessionId })}`);
}

