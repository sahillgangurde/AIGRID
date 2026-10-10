const KEY = 'aigrid-jwt';

export function getStoredToken(): string {
  if (typeof window === 'undefined') return '';
  try {
    return window.localStorage.getItem(KEY) || window.sessionStorage.getItem(KEY) || '';
  } catch {
    return '';
  }
}

/** Returns Authorization headers when a real (backend-issued) JWT exists in this session. */
export function getAuthHeaders(): Record<string, string> {
  const token = getStoredToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export function setStoredToken(token: string) {
  try {
    if (token) {
      window.localStorage.setItem(KEY, token);
      window.sessionStorage.setItem(KEY, token);
    } else {
      window.localStorage.removeItem(KEY);
      window.sessionStorage.removeItem(KEY);
    }
  } catch {
    /* storage unavailable */
  }
}

