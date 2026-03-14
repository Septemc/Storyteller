import { STORAGE_KEYS } from '../../constants/storage';
import { request, toQuery } from '../http';

function sanitizeStoryErrorMessage(message) {
  const raw = String(message || '').trim();
  if (!raw) return 'generate failed, please retry';
  const lowered = raw.toLowerCase();
  if (lowered.includes('<!doctype html') || lowered.includes('<html') || lowered.includes('cloudflare') || lowered.includes('error code 520')) {
    return 'upstream model service is temporarily unavailable (HTTP 520); please retry later or switch base_url';
  }
  return raw.replace(/\s+/g, ' ').slice(0, 220);
}

export function generate(payload) {
  return request('/api/story/generate', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function generateStream(payload, handlers = {}) {
  const token = localStorage.getItem(STORAGE_KEYS.token);
  const headers = { 'Content-Type': 'application/json' };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const resp = await fetch('/api/story/generate_stream', {
    method: 'POST',
    headers,

    body: JSON.stringify(payload),
  });

  if (!resp.ok) {
    throw new Error(sanitizeStoryErrorMessage(await resp.text()));
  }

  const reader = resp.body.getReader();
  const decoder = new TextDecoder('utf-8');
  let buffer = '';

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const packets = buffer.split('\n\n');
    for (let i = 0; i < packets.length - 1; i += 1) {
      const chunk = packets[i];
      const event = chunk.match(/^event:\s*(.+)$/m)?.[1]?.trim();
      const dataRaw = chunk.match(/^data:\s*([\s\S]+)$/m)?.[1];
      if (!event || !dataRaw) continue;
      const data = JSON.parse(dataRaw);
      if (event === 'error' && data && typeof data.message === 'string') {
        data.message = sanitizeStoryErrorMessage(data.message);
      }
      if (event === 'empty' && data && typeof data.message === 'string') {
        data.message = sanitizeStoryErrorMessage(data.message);
      }
      handlers.onEvent?.(event, data);
    }
    buffer = packets[packets.length - 1];
  }
}

export function recent(params) {
  return request(`/api/story/recent${toQuery(params)}`);
}

export function updateFrontendDuration(payload) {
  return request('/api/story/update_frontend_duration', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function savesList() {
  return request('/api/story/saves/list');
}

export function saveDetail(sessionId) {
  return request(`/api/story/saves/detail${toQuery({ session_id: sessionId })}`);
}

export function createSave() {
  return request('/api/story/saves/create', { method: 'POST' });
}

export function renameSave(payload) {
  return request('/api/story/saves/rename', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function deleteSave(sessionId) {
  return request(`/api/story/saves/delete${toQuery({ session_id: sessionId })}`, {
    method: 'POST',
  });
}

export function deleteSegmentCascade(payload) {
  return request('/api/story/segments/delete_cascade', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function copySaveFromSegment(payload) {
  return request('/api/story/saves/copy_from_segment', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function stats() {
  return request('/api/story/stats');
}

export function updateSessionContext(payload) {
  return request('/api/session/context', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}
