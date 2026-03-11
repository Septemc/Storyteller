import { STORAGE_KEYS } from '../constants/storage';

const JSON_HEADERS = { 'Content-Type': 'application/json' };

export async function request(url, options = {}) {
  const token = localStorage.getItem(STORAGE_KEYS.token);
  const headers = {
    ...JSON_HEADERS,
    ...(options.headers || {}),
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const resp = await fetch(url, {
    ...options,
    headers,
  });

  let data = null;
  const contentType = resp.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    data = await resp.json().catch(() => null);
  } else {
    data = await resp.text().catch(() => '');
  }

  if (!resp.ok) {
    const rawDetail = data?.detail || data?.message || `${resp.status} ${resp.statusText}`;
    const detail =
      typeof rawDetail === 'string'
        ? rawDetail
        : Array.isArray(rawDetail) || (rawDetail && typeof rawDetail === 'object')
          ? JSON.stringify(rawDetail)
          : String(rawDetail);
    const error = new Error(detail);
    error.status = resp.status;
    error.data = data;
    throw error;
  }

  return data;
}

export function toQuery(params = {}) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && `${value}` !== '') {
      search.set(key, value);
    }
  });
  const qs = search.toString();
  return qs ? `?${qs}` : '';
}
