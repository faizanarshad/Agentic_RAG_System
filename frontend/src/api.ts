export const API_BASE = 'http://localhost:8000';

export const fetchBackend = async (endpoint: string, options?: RequestInit) => {
  const response = await fetch(`${API_BASE}${endpoint}`, options);
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: response.statusText }));
    const detail = errorData.detail;
    throw new Error(typeof detail === 'string' ? detail : detail?.message || response.statusText);
  }
  return response.json();
};
