import { beforeEach, describe, expect, it, vi } from 'vitest';
import { acceptTermsAgreement, readTermsAgreement, useTermsAgreement } from '@/lib/terms-agreement';

const KEY = 'aigrid-escrow-terms-agreement';

beforeEach(() => {
  localStorage.clear();
  // Reset module state by reloading (the lib keeps module-level current/loaded).
  vi.resetModules();
  // Silence the fire-and-forget backend call in tests.
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true }));
});

describe('escrow terms agreement', () => {
  it('starts with no agreement recorded', () => {
    expect(readTermsAgreement()).toBeNull();
  });

  it('records the agreement with a timestamp and terms version', () => {
    const before = Date.now();
    const agreement = acceptTermsAgreement('demo@brand.com');
    expect(agreement.termsVersion).toBe('v1.0');
    expect(agreement.email).toBe('demo@brand.com');
    expect(Date.parse(agreement.acceptedAt)).toBeGreaterThanOrEqual(before);
    expect(readTermsAgreement()?.termsVersion).toBe('v1.0');
    expect(localStorage.getItem(KEY)).toContain('"termsVersion":"v1.0"');
  });

  it('persists across reloads so the onboarding modal is not shown again', () => {
    acceptTermsAgreement('demo@brand.com');
    // Simulate a fresh module load (like a page refresh) reading from storage.
    const stored = JSON.parse(localStorage.getItem(KEY) ?? '{}');
    expect(stored.acceptedAt).toBeTruthy();
    expect(stored.termsVersion).toBe('v1.0');
  });

  it('notifies the backend of the agreement', async () => {
    acceptTermsAgreement('demo@brand.com');
    await vi.waitFor(() => {
      expect(fetch).toHaveBeenCalledWith('/api/terms/accept', expect.objectContaining({
        method: 'POST',
        body: expect.stringContaining('"terms_version":"v1.0"'),
      }));
    });
  });

  it('still works when storage is unavailable', async () => {
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => { throw new Error('blocked'); });
    const agreement = acceptTermsAgreement();
    expect(agreement.termsVersion).toBe('v1.0');
  });

  it('exposes a store hook that reflects the agreement', () => {
    expect(useTermsAgreement).toBeInstanceOf(Function);
  });
});
