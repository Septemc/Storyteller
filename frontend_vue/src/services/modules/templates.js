import { request } from '../http';

export function listTemplates() {
  return request('/api/templates/list');
}

export function createTemplate(payload) {
  return request('/api/templates', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function updateTemplate(templateId, payload) {
  return request(`/api/templates/${encodeURIComponent(templateId)}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}

export function deleteTemplate(templateId) {
  return request(`/api/templates/${encodeURIComponent(templateId)}`, {
    method: 'DELETE',
  });
}
