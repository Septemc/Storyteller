import { request } from '../http';

export function register(payload) {
  return request('/api/auth/register', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function login(payload) {
  return request('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function me() {
  return request('/api/auth/me');
}

export function profile() {
  return request('/api/auth/profile');
}

export function updateMe(payload) {
  return request('/api/auth/me', {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}

export function updateProfile(payload) {
  return request('/api/auth/profile', {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}

export function changePassword(payload) {
  return request('/api/auth/change-password', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function updatePassword(payload) {
  return request('/api/auth/password', {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}

export function checkUsername(username) {
  return request(`/api/auth/check-username/${encodeURIComponent(username)}`);
}

export function logout() {
  return request('/api/auth/logout', {
    method: 'POST',
  });
}
