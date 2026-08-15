const DEFAULT_API_BASE_URL = 'http://127.0.0.1:8000';
const ACCESS_TOKEN_KEY = 'mjourney_access_token';
const REFRESH_TOKEN_KEY = 'mjourney_refresh_token';
const AUTH_USER_KEY = 'mjourney_auth_user';

export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE_URL).replace(/\/$/, '');

export class ApiError extends Error {
  constructor(status, payload) {
    const error = payload?.error;
    super(error?.message || '서버 요청을 처리하지 못했습니다.');
    this.name = 'ApiError';
    this.status = status;
    this.code = error?.code || 'API_REQUEST_FAILED';
    this.details = error?.details ?? null;
    this.requestId = error?.request_id ?? null;
  }
}

function authStorage() {
  if (window.localStorage.getItem(REFRESH_TOKEN_KEY)) return window.localStorage;
  return window.sessionStorage;
}

export function getAccessToken() {
  return window.sessionStorage.getItem(ACCESS_TOKEN_KEY) || window.localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken() {
  return authStorage().getItem(REFRESH_TOKEN_KEY);
}

export function getAuthUser() {
  const rawUser = authStorage().getItem(AUTH_USER_KEY);
  if (!rawUser) return null;
  try {
    return JSON.parse(rawUser);
  } catch {
    clearAuth();
    return null;
  }
}

export function saveAuth(tokens, remember = false) {
  clearAuth();
  const storage = remember ? window.localStorage : window.sessionStorage;
  storage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
  storage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
  storage.setItem(AUTH_USER_KEY, JSON.stringify(tokens.user));
}

export function clearAuth() {
  for (const storage of [window.localStorage, window.sessionStorage]) {
    storage.removeItem(ACCESS_TOKEN_KEY);
    storage.removeItem(REFRESH_TOKEN_KEY);
    storage.removeItem(AUTH_USER_KEY);
  }
}

async function parseResponse(response) {
  if (response.status === 204) return null;
  const payload = await response.json().catch(() => null);
  if (!response.ok) throw new ApiError(response.status, payload);
  return payload;
}

async function refreshAuth() {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return false;
  const remember = authStorage() === window.localStorage;
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  if (!response.ok) {
    clearAuth();
    return false;
  }
  saveAuth(await response.json(), remember);
  return true;
}

async function apiRequest(path, options = {}, retryOnUnauthorized = true) {
  const headers = new Headers(options.headers);
  if (options.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json');
  const accessToken = getAccessToken();
  if (accessToken) headers.set('Authorization', `Bearer ${accessToken}`);

  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
  if (response.status === 401 && retryOnUnauthorized && await refreshAuth()) {
    return apiRequest(path, options, false);
  }
  return parseResponse(response);
}

export async function login(email, password, remember = false) {
  const tokens = await apiRequest(
    '/api/v1/auth/login',
    { method: 'POST', body: JSON.stringify({ email, password }) },
    false,
  );
  saveAuth(tokens, remember);
  return tokens;
}

export function fetchEntryTag(tagToken) {
  return apiRequest(`/api/v1/entry-tags/${encodeURIComponent(tagToken)}`, {}, false);
}

export function fetchCheckin(checkinId) {
  return apiRequest(`/api/v1/check-ins/${encodeURIComponent(checkinId)}`);
}

export async function createOrResumeCheckin(tagToken) {
  try {
    return await apiRequest('/api/v1/check-ins', {
      method: 'POST',
      body: JSON.stringify({ tag_token: tagToken }),
    });
  } catch (error) {
    if (error instanceof ApiError && error.code === 'ACTIVE_CHECKIN_EXISTS' && error.details?.checkin_id) {
      const checkin = await fetchCheckin(error.details.checkin_id);
      return { ...checkin, resumed: true };
    }
    throw error;
  }
}
