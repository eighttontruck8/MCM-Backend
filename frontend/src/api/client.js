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
  if (response.status === 401 && retryOnUnauthorized) {
    if (await refreshAuth()) return apiRequest(path, options, false);
    clearAuth();
    if (window.location.pathname !== '/login') {
      window.location.replace('/login?reason=auth-required');
    }
    throw new ApiError(401, {
      error: { code: 'AUTHENTICATION_REQUIRED', message: '서비스 이용은 로그인이 필요합니다.' },
    });
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

export async function signupCustomer({ name, phone, email, password }) {
  const tokens = await apiRequest(
    '/api/v1/auth/signup',
    { method: 'POST', body: JSON.stringify({ name, phone, email, password }) },
    false,
  );
  saveAuth(tokens);
  return tokens;
}

export async function signupStaff({ name, email, password, storeId, signupCode }) {
  return apiRequest(
    '/api/v1/auth/staff/signup',
    {
      method: 'POST',
      body: JSON.stringify({
        name,
        email,
        password,
        store_id: storeId,
        signup_code: signupCode,
      }),
    },
    false,
  );
}

export function requestPasswordReset(email) {
  return apiRequest(
    '/api/v1/auth/password-reset/request',
    { method: 'POST', body: JSON.stringify({ email }) },
    false,
  );
}

export function confirmPasswordReset(resetToken, newPassword) {
  return apiRequest(
    '/api/v1/auth/password-reset/confirm',
    { method: 'POST', body: JSON.stringify({ reset_token: resetToken, new_password: newPassword }) },
    false,
  );
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

export async function createOrResumeDemoCheckin() {
  try {
    return await apiRequest('/api/v1/check-ins/demo', { method: 'POST' });
  } catch (error) {
    if (error.code === 'ACTIVE_CHECKIN_EXISTS' && error.details?.checkin_id) {
      return fetchCheckin(error.details.checkin_id);
    }
    throw error;
  }
}

export function setShoppingMode(checkinId, shoppingMode) {
  return apiRequest(`/api/v1/check-ins/${encodeURIComponent(checkinId)}/shopping-mode`, {
    method: 'PATCH',
    body: JSON.stringify({ shopping_mode: shoppingMode }),
  });
}

export function createServiceRequest(checkinId, consent, visitPurpose) {
  return apiRequest(`/api/v1/check-ins/${encodeURIComponent(checkinId)}/service-request`, {
    method: 'POST',
    body: JSON.stringify({ consent, visit_purpose: visitPurpose }),
  });
}

export function fetchStaffVisits(storeId, status = 'WAITING_FOR_STAFF') {
  const query = new URLSearchParams({ status });
  return apiRequest(`/api/v1/staff/stores/${encodeURIComponent(storeId)}/visits?${query}`);
}

export function claimStaffVisit(checkinId) {
  return apiRequest(`/api/v1/staff/check-ins/${encodeURIComponent(checkinId)}/claim`, { method: 'POST' });
}

export function updateStaffVisitStatus(checkinId, status) {
  return apiRequest(`/api/v1/staff/check-ins/${encodeURIComponent(checkinId)}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  });
}

export function fetchStaffCustomer(customerId) {
  return apiRequest(`/api/v1/staff/customers/${encodeURIComponent(customerId)}`);
}

export function openRealtime(path) {
  const accessToken = getAccessToken();
  if (!accessToken) throw new Error('실시간 연결에 필요한 로그인이 만료되었습니다.');
  const url = new URL(`${API_BASE_URL}${path}`);
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
  url.searchParams.set('token', accessToken);
  return new WebSocket(url);
}

export function fetchMyProfile() {
  return apiRequest('/api/v1/customers/me');
}

export function fetchProducts(storeId = 'S001', inStock = true) {
  const query = new URLSearchParams({ store_id: storeId, in_stock: String(inStock) });
  return apiRequest(`/api/v1/products?${query}`, {}, false);
}

export function fetchRecommendations() {
  return apiRequest('/api/v1/customers/me/recommendations');
}

export function createLookbook(checkinId) {
  return apiRequest(`/api/v1/check-ins/${encodeURIComponent(checkinId)}/lookbook`, { method: 'POST' });
}

export function fetchWishlist() {
  return apiRequest('/api/v1/customers/me/wishlist');
}

export function addWishlistItem(productId) {
  return apiRequest(`/api/v1/customers/me/wishlist/${encodeURIComponent(productId)}`, { method: 'POST' });
}

export function removeWishlistItem(productId) {
  return apiRequest(`/api/v1/customers/me/wishlist/${encodeURIComponent(productId)}`, { method: 'DELETE' });
}

export function fetchPurchases() {
  return apiRequest('/api/v1/customers/me/purchases');
}
