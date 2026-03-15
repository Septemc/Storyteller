import { request } from '../http';

export function getGlobalSettings() {
  return request('/api/settings/global');
}

export function putGlobalSettings(payload) {
  return request('/api/settings/global', {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}

export function listPresets() {
  return request('/api/presets');
}

export function getPreset(presetId) {
  return request(`/api/presets/${encodeURIComponent(presetId)}`);
}

export function createPreset(name) {
  return request(`/api/presets?name=${encodeURIComponent(name)}`, {
    method: 'POST',
  });
}

export function updatePreset(presetId, payload) {
  return request(`/api/presets/${encodeURIComponent(presetId)}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}

export function deletePreset(presetId) {
  return request(`/api/presets/${encodeURIComponent(presetId)}`, {
    method: 'DELETE',
  });
}

export function setActivePreset(presetId) {
  return request('/api/presets/active', {
    method: 'PUT',
    body: JSON.stringify({ preset_id: presetId }),
  });
}

export function listLlmConfigs() {
  return request('/api/llm/configs');
}

export function getLlmConfigModels(configId) {
  return request(`/api/llm/configs/${encodeURIComponent(configId)}/models`);
}

export function createLlmConfig(payload) {
  return request('/api/llm/configs', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function updateLlmConfig(configId, payload) {
  return request(`/api/llm/configs/${encodeURIComponent(configId)}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}

export function deleteLlmConfig(configId) {
  return request(`/api/llm/configs/${encodeURIComponent(configId)}`, {
    method: 'DELETE',
  });
}

export function setActiveLlm(payload) {
  return request('/api/llm/active', {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}

export function listLlmModels(payload) {
  return request('/api/llm/models/list', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function listRegexProfiles() {
  return request('/regex/profiles');
}

export function getActiveRegex() {
  return request('/regex/active');
}

export function getRegexProfile(profileId) {
  return request(`/regex/profiles/${encodeURIComponent(profileId)}`);
}

export function setActiveRegex(profileId) {
  return request(`/regex/active?profile_id=${encodeURIComponent(profileId)}`, {
    method: 'PUT',
  });
}

export function createRegexProfile(payload) {
  return request('/regex/profiles', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function updateRegexProfile(profileId, payload) {
  return request(`/regex/profiles/${encodeURIComponent(profileId)}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}

export function deleteRegexProfile(profileId) {
  return request(`/regex/profiles/${encodeURIComponent(profileId)}`, {
    method: 'DELETE',
  });
}
