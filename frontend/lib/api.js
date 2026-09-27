export const API_BASE = (process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000').replace(/\/$/, '');

// Fired when the API reports that the session is missing or expired; AuthProvider redirects to sign-in
export const AUTH_REQUIRED_EVENT = 'aidocumentagent:auth-required';

export const fetchBackend = async (endpoint, options = {}) => {
  // credentials: 'include' sends the HttpOnly session cookie with every API call
  const response = await fetch(`${API_BASE}${endpoint}`, { credentials: 'include', ...options });
  if (response.status === 401 && typeof window !== 'undefined' && !endpoint.startsWith('/auth/')) {
    window.dispatchEvent(new Event(AUTH_REQUIRED_EVENT));
  }
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: response.statusText }));
    const detail = errorData.detail;
    throw new Error(typeof detail === 'string' ? detail : detail?.message || response.statusText);
  }
  return response.status === 204 ? null : response.json();
};

export const jsonRequest = (method, body) => ({
  method,
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body),
});
