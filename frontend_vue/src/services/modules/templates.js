import { request } from '../http';

export function listTemplates(sessionId) {
  return request(`/api/templates/list?session_id=${encodeURIComponent(sessionId)}`);
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

export function activateTemplate(sessionId, templateId) {
  return request(`/api/templates/${encodeURIComponent(templateId)}/activate?session_id=${encodeURIComponent(sessionId)}`, {
    method: 'POST',
  });
}

export function deleteTemplate(sessionId, templateId) {
  return request(`/api/templates/${encodeURIComponent(templateId)}?session_id=${encodeURIComponent(sessionId)}`, {
    method: 'DELETE',
  });
}
