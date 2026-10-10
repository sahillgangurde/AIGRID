const KEY = 'aigrid-jwt';

/** Returns Authorization headers when a real (backend-issued) JWT exists in this session. */
export function getAuthHeaders(): Record<string, string> {
  if (typeof window === 'undefined') return {};
  try {
    const token = window.sessionStorage.getItem(KEY);
    return token ? { Authorization: `Bearer ${token}` } : {};
  } catch {
    return {};
  }
}

export function setStoredToken(token: string) {
  try {
    window.sessionStorage.setItem(KEY, token);
  } catch {
    /* storage unavailable — unauthenticated demo mode continues */
  }
}
