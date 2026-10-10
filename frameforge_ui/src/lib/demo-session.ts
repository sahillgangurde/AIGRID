import { useSyncExternalStore } from 'react';

const KEY = 'aigrid-demo-user';

export type DemoRole = 'creator' | 'producer' | 'rep' | 'hirer' | 'both';

export type DemoSession = { email: string; name: string; provider: 'email' | 'google'; role?: DemoRole | undefined };

let current: DemoSession | null = null;
let loaded = false;
const listeners = new Set<() => void>();

function emit() {
  listeners.forEach(listener => listener());
}

function nameFromEmail(email: string) {
  const local = email.trim().split('@')[0] ?? '';
  const words = local.split(/[._\-+0-9]+/).filter(Boolean);
  const name = words.map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ').trim();
  return name || 'Creator';
}

function read(): DemoSession | null {
  if (typeof window === 'undefined') return null;
  if (!loaded) {
    loaded = true;
    try {
      const raw = window.localStorage.getItem(KEY);
      const data = raw ? (JSON.parse(raw) as Partial<DemoSession>) : null;
      current = data && typeof data.email === 'string' && data.email
        ? { email: data.email, name: typeof data.name === 'string' && data.name ? data.name : nameFromEmail(data.email), provider: data.provider === 'google' ? 'google' : 'email', role: typeof data.role === 'string' ? (data.role as DemoRole) : undefined }
        : null;
    } catch {
      current = null;
    }
  }
  return current;
}

export function readDemoSession() {
  return read();
}

/** Demo sign-in: accepts any input, keeps only the email locally, never the password. */
export function signIn(email: string, provider: DemoSession['provider'] = 'email'): DemoSession {
  const clean = String(email ?? '').trim();
  const session: DemoSession = { email: clean, name: nameFromEmail(clean), provider };
  current = session;
  loaded = true;
  try {
    window.localStorage.setItem(KEY, JSON.stringify(session));
  } catch {
    /* storage unavailable — the demo session still lives for this visit */
  }
  emit();
  return session;
}

/** One-time onboarding: remembers the path the visitor picked, only on their own browser. */
export function setRole(role: DemoRole) {
  if (!current) return;
  current = { ...current, role };
  try {
    window.localStorage.setItem(KEY, JSON.stringify(current));
  } catch {
    /* storage unavailable — the role still lives for this visit */
  }
  emit();
}

export function signOut() {
  current = null;
  loaded = true;
  try {
    window.localStorage.removeItem(KEY);
  } catch {
    /* nothing persisted, nothing to clear */
  }
  emit();
}

function onStorage(event: StorageEvent) {
  if (event.key === KEY) {
    current = event.newValue ? read() : null;
    loaded = true;
    emit();
  }
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  if (typeof window !== 'undefined') window.addEventListener('storage', onStorage);
  return () => {
    listeners.delete(listener);
    if (typeof window !== 'undefined') window.removeEventListener('storage', onStorage);
  };
}

export function useDemoSession() {
  return useSyncExternalStore(subscribe, read, () => null);
}
