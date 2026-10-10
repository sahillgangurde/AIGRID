import { useEffect, useState } from 'react';
import { Clock, ArrowUpRight } from 'lucide-react';
import { getAuthHeaders } from '@/lib/auth-headers';

type SubStatus = {
  role?: string;
  plan_code?: string;
  trial_active?: boolean;
  days_left?: number | null;
  is_listed?: boolean;
  expiring_soon?: boolean;
  show_banner?: boolean;
};

/**
 * Creator free-trial banner.
 * Fetches /api/subscriptions/me; shows:
 *  - "Free trial ends in X days" when ≤7 days remain
 *  - "Trial expired — listing paused. Upgrade to stay listed." when expired
 * Hidden for brands and errors (gracefully silent in demo mode).
 */
export function TrialBanner() {
  const [status, setStatus] = useState<SubStatus | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch('/api/subscriptions/me', { headers: getAuthHeaders() });
        if (!res.ok) return;
        const body = await res.json();
        if (body && body.role === 'creator') setStatus(body);
      } catch {
        /* silent — banner hidden in demo/unauthenticated mode */
      }
    })();
  }, []);

  if (!status) return null;

  const expired = status.is_listed === false && !status.trial_active;
  const expiring = status.show_banner;

  if (!expired && !expiring) return null;

  return (
    <div
      role="status"
      style={{
        background: expired ? '#FEF2F2' : '#FFFBEB',
        border: `1px solid ${expired ? '#FECACA' : '#FDE68A'}`,
        borderRadius: 10,
        padding: '12px 16px',
        margin: '16px 0',
        fontSize: '0.85rem',
        color: expired ? '#B91C1C' : '#92400E',
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        flexWrap: 'wrap',
      }}
    >
      <Clock size={16} />
      {expired ? (
        <>
          <span style={{ flex: 1 }}>
            <strong>Free trial expired</strong> — your listing is paused in the directory. Upgrade to stay discoverable.
          </span>
          <button
            onClick={() => {
              fetch('/api/subscriptions/upgrade', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
                body: JSON.stringify({ plan_code: 'pro_creator' }),
              })
                .then((r) => r.ok && window.location.reload())
                .catch(() => {});
            }}
            style={{
              background: '#B91C1C',
              color: '#fff',
              border: 'none',
              borderRadius: 8,
              padding: '7px 14px',
              fontWeight: 700,
              fontSize: '0.8rem',
              cursor: 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              gap: 6,
            }}
          >
            Upgrade plan <ArrowUpRight size={14} />
          </button>
        </>
      ) : (
        <span>
          <strong>Free trial ends in {status.days_left} {status.days_left === 1 ? 'day' : 'days'}.</strong> Upgrade to keep your listing active after expiry.
        </span>
      )}
    </div>
  );
}
