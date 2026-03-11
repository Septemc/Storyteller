import { request, toQuery } from '../http';

export function listWorldbook(params = {}) {
  return request(`/api/worldbook/list${toQuery(params)}`);
}

export function importWorldbook(entries, syncEmbeddings = false, worldbookId = undefined) {
  return request(`/api/worldbook/import${toQuery({ sync_embeddings: syncEmbeddings })}`, {
    method: 'POST',
    body: JSON.stringify(Array.isArray(entries) ? { entries, worldbook_id: worldbookId } : entries),
  });
}

export function getWorldbookEntry(entryId) {
  return request(`/api/worldbook/${encodeURIComponent(entryId)}`);
}

export function semanticSearchWorldbook(payload) {
  return request('/api/worldbook/semantic_search', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function deleteWorldbookEntry(entryId) {
  return request(`/api/worldbook/${encodeURIComponent(entryId)}`, {
    method: 'DELETE',
  });
}

export function deleteWorldbookCategory(category, worldbookId = undefined) {
  return request(`/api/worldbook/category${toQuery({ category, worldbook_id: worldbookId })}`, {
    method: 'DELETE',
  });
}

export function deleteAllWorldbook(worldbookId = undefined) {
  return request(`/api/worldbook/all${toQuery({ confirm: true, worldbook_id: worldbookId })}`, {
    method: 'DELETE',
  });
}
