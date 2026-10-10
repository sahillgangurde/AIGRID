import { useSyncExternalStore } from 'react';

const KEY = 'aigrid-escrow-terms-agreement';
const TERMS_VERSION = 'v1.0';

export type TermsAgreement = { acceptedAt: string; termsVersion: string; email?: string | undefined };

let current: TermsAgreement | null = null;
let loaded = false;
const listeners = new Set<() => void>();

function emit() {
  listeners.forEach(listener => listener());
}

function read(): TermsAgreement | null {
  if (typeof window === 'undefined') return null;
  if (!loaded) {
    loaded = true;
    try {
      const raw = window.localStorage.getItem(KEY);
      const data = raw ? (JSON.parse(raw) as Partial<TermsAgreement>) : null;
      current = data && typeof data.acceptedAt === 'string' && data.termsVersion === TERMS_VERSION
        ? { acceptedAt: data.acceptedAt, termsVersion: data.termsVersion, email: typeof data.email === 'string' ? data.email : undefined }
        : null;
    } catch {
      current = null;
    }
  }
  return current;
}

export function readTermsAgreement() {
  return read();
}

/** Records the user's Escrow & Confidentiality agreement (session + database). */
export function acceptTermsAgreement(email?: string): TermsAgreement {
  const agreement: TermsAgreement = { acceptedAt: new Date().toISOString(), termsVersion: TERMS_VERSION, email: email || undefined };
  current = agreement;
  loaded = true;
  try {
    window.localStorage.setItem(KEY, JSON.stringify(agreement));
  } catch {
    /* storage unavailable — agreement still lives for this visit */
  }
  emit();

  // Fire-and-forget database record; UI never blocks on this.
  try {
    fetch('/api/terms/accept', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: agreement.email,
        terms_version: agreement.termsVersion,
        accepted_at: agreement.acceptedAt
      })
    }).catch(() => {/* backend unavailable in offline demo mode */});
  } catch {
    /* network unavailable */
  }

  return agreement;
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

export function useTermsAgreement() {
  return useSyncExternalStore(subscribe, read, () => null);
}
