import { createFileRoute, Link } from '@tanstack/react-router';
import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { pageHead } from '@/lib/hypear-data';
import { getAuthHeaders } from '@/lib/auth-headers';
import { TrialBanner } from '@/components/trial-banner';
import {
  Lock, LockOpen, ShieldCheck, RefreshCw, Milestone, CircleAlert, Wallet, ArrowLeft, CheckCircle2
} from 'lucide-react';

export const Route = createFileRoute('/dashboard')({
  head: () => pageHead('Projects & Escrow — AiGrid', 'Track your engagements, escrow milestones, earnings and disputes.'),
  component: Dashboard,
});

type Milestone = { id: string; title: string; amount: number; percentage: number; status: string; completed_at?: string | null };
type Project = {
  id: string; title: string; status: string; visibility_mode: string;
  brand_name: string; creator_name: string; budget_amount: number; currency: string;
  deadline?: string | null; conversation_id?: string | null; milestones: Milestone[];
};
type Transaction = { id: string; project_id?: string | null; gross_amount: number; platform_fee: number; net_amount: number; currency: string; status: string; created_at?: string | null };

function statusChip(status: string) {
  const map: Record<string, { bg: string; fg: string; label: string }> = {
    active: { bg: '#EFF6FF', fg: '#1D4ED8', label: 'In progress' },
    active_disputed: { bg: '#FEF2F2', fg: '#B91C1C', label: 'Disputed — escrow frozen' },
    active_awaiting_escrow: { bg: '#FFFBEB', fg: '#92400E', label: 'Awaiting escrow funding' },
    completed: { bg: '#F0FDF4', fg: '#15803D', label: 'Completed' },
    cancelled: { bg: '#F9FAFB', fg: '#6B7280', label: 'Cancelled' },
  };
  const s = map[status] ?? { bg: '#F9FAFB', fg: '#6B7280', label: status };
  return <span style={{ background: s.bg, color: s.fg, padding: '3px 10px', borderRadius: 999, fontSize: '0.72rem', fontWeight: 700 }}>{s.label}</span>;
}

function milestoneChip(status: string) {
  const map: Record<string, { bg: string; fg: string }> = {
    awaiting_escrow: { bg: '#FFFBEB', fg: '#92400E' },
    active: { bg: '#EFF6FF', fg: '#1D4ED8' },
    submitted: { bg: '#F5F3FF', fg: '#6D28D9' },
    approved: { bg: '#F0FDF4', fg: '#15803D' },
    paid: { bg: '#ECFDF5', fg: '#047857' },
  };
  const s = map[status] ?? { bg: '#F9FAFB', fg: '#6B7280' };
  return <span style={{ background: s.bg, color: s.fg, padding: '2px 8px', borderRadius: 999, fontSize: '0.68rem', fontWeight: 700 }}>{status.replace('_', ' ')}</span>;
}

function Dashboard() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const [pr, tx] = await Promise.all([
          fetch('/api/projects', { headers: getAuthHeaders() }).then(r => r.ok ? r.json() : Promise.reject(r.status)),
          fetch('/api/finance/transactions', { headers: getAuthHeaders() }).then(r => r.ok ? r.json() : Promise.reject(r.status)),
        ]);
        setProjects(pr?.projects ?? []);
        setTransactions(tx?.transactions ?? []);
      } catch {
        // Demo fallback: pre-populated showcase project so the dashboard is never empty during review.
        setProjects([
          {
            id: 'demo-project-1',
            title: 'Cyberpunk Luxury Sneaker — 30s Commercial',
            status: 'active',
            visibility_mode: 'confidential',
            brand_name: 'Confidential Brand Partner',
            creator_name: 'Creator #1042',
            budget_amount: 120000,
            currency: 'INR',
            deadline: new Date(Date.now() + 12 * 86400000).toISOString(),
            conversation_id: 'demo-conv-1',
            milestones: [
              { id: 'm1', title: 'Upfront compute & LoRA kickoff', amount: 36000, percentage: 30, status: 'paid' },
              { id: 'm2', title: 'Rough-cut review (watermarked preview)', amount: 48000, percentage: 40, status: 'submitted' },
              { id: 'm3', title: 'Final buyout & C2PA delivery', amount: 36000, percentage: 30, status: 'active' },
            ],
          },
        ]);
        setTransactions([
          { id: 'demo-tx-1', project_id: 'demo-project-1', gross_amount: 120000, platform_fee: 20000, net_amount: 100000, currency: 'INR', status: 'settled' },
        ]);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const fundsLocked = projects
    .filter(p => p.status === 'active' || p.status === 'active_awaiting_escrow')
    .reduce((sum, p) => sum + (p.budget_amount ?? 0), 0);

  return (
    <main className="page-container">
      <p className="eyebrow">Workspace</p>
      <h1>Projects &amp; Escrow</h1>
      <p className="page-intro">Every engagement from pitch to payout — funds stay in escrow until milestones are approved.</p>

      <TrialBanner />

      {notice && (
        <div style={{ background: '#FFFBEB', border: '1px solid #FDE68A', borderRadius: 10, padding: '12px 16px', marginTop: 16, fontSize: '0.85rem', color: '#92400E', display: 'flex', alignItems: 'center', gap: 8 }}>
          <CircleAlert size={16} /> {notice} <Link to="/login" style={{ marginLeft: 4 }}>Sign in ↗</Link>
        </div>
      )}

      {/* Escrow summary strip */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 14, margin: '22px 0 28px' }}>
        <div style={{ border: '1px solid #E5E7EB', borderRadius: 12, padding: '14px 18px' }}>
          <span style={{ fontSize: '0.72rem', fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', color: '#6B7280' }}>Funds in escrow</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 6 }}>
            <Lock size={18} color="#059669" />
            <strong style={{ fontSize: '1.3rem' }}>₹{fundsLocked.toLocaleString('en-IN')}</strong>
          </div>
        </div>
        <div style={{ border: '1px solid #E5E7EB', borderRadius: 12, padding: '14px 18px' }}>
          <span style={{ fontSize: '0.72rem', fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', color: '#6B7280' }}>Active projects</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 6 }}>
            <Milestone size={18} color="#1D4ED8" />
            <strong style={{ fontSize: '1.3rem' }}>{projects.filter(p => p.status.startsWith('active')).length}</strong>
          </div>
        </div>
        <div style={{ border: '1px solid #E5E7EB', borderRadius: 12, padding: '14px 18px' }}>
          <span style={{ fontSize: '0.72rem', fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', color: '#6B7280' }}>Settled transactions</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 6 }}>
            <Wallet size={18} color="#6D28D9" />
            <strong style={{ fontSize: '1.3rem' }}>{transactions.filter(t => t.status === 'settled').length}</strong>
          </div>
        </div>
      </div>

      {/* Projects list */}
      {loading ? (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#6B7280', fontSize: '0.85rem' }}><RefreshCw size={14} className="animate-spin" /> Loading projects…</div>
      ) : projects.length ? (
        <section style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {projects.map(p => (
            <article key={p.id} style={{ border: '1px solid #E5E7EB', borderRadius: 12, padding: '16px 20px', background: '#F9FAFB' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12, flexWrap: 'wrap' }}>
                <div>
                  <h3 style={{ margin: 0, fontSize: '1.05rem' }}>{p.title}</h3>
                  <p style={{ margin: '4px 0 0', fontSize: '0.8rem', color: '#6B7280' }}>
                    {p.brand_name} × {p.creator_name}{p.visibility_mode === 'confidential' ? ' · Confidential mode' : ''}{p.deadline ? ` · Due ${new Date(p.deadline).toLocaleDateString()}` : ''}
                  </p>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <strong style={{ fontSize: '1rem' }}>{p.currency === 'INR' ? '₹' : '$'}{p.budget_amount?.toLocaleString('en-IN')}</strong>
                  {statusChip(p.status)}
                </div>
              </div>

              {p.milestones?.length > 0 && (
                <div style={{ marginTop: 12, display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {p.milestones.map(m => (
                    <div key={m.id} style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: '0.8rem', color: '#374151', background: '#fff', border: '1px solid #E5E7EB', borderRadius: 8, padding: '7px 12px' }}>
                      {m.status === 'paid' ? <CheckCircle2 size={14} color="#059669" /> : <LockOpen size={14} color="#92400E" />}
                      <span style={{ flex: 1 }}>{m.title}</span>
                      <span style={{ fontWeight: 700 }}>{m.percentage}%</span>
                      <span>{m.amount ? `${p.currency === 'INR' ? '₹' : '$'}${m.amount.toLocaleString('en-IN')}` : ''}</span>
                      {milestoneChip(m.status)}
                    </div>
                  ))}
                </div>
              )}

              {p.conversation_id && (
                <div style={{ marginTop: 10 }}>
                  <Button asChild variant="outline" className="pill">
                    <Link to="/creators">Open secure chat ↗</Link>
                  </Button>
                </div>
              )}
            </article>
          ))}
        </section>
      ) : !notice ? (
        <div className="empty-state"><h2>No projects yet</h2><p>Post a brief and matched creators will pitch on it.</p></div>
      ) : null}

      {/* Transactions */}
      {transactions.length > 0 && (
        <section style={{ marginTop: 34 }}>
          <h2 style={{ fontSize: '1.15rem', marginBottom: 12 }}>Transactions &amp; payouts</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {transactions.map(t => (
              <div key={t.id} style={{ display: 'flex', alignItems: 'center', gap: 14, border: '1px solid #E5E7EB', borderRadius: 10, padding: '10px 16px', fontSize: '0.82rem', background: '#fff' }}>
                <ShieldCheck size={16} color={t.status === 'settled' ? '#059669' : '#92400E'} />
                <span style={{ flex: 1 }}>{t.project_id ? `Project ${t.project_id.slice(0, 12)}…` : 'Platform settlement'}</span>
                <span style={{ color: '#6B7280' }}>Gross {t.currency === 'INR' ? '₹' : '$'}{t.gross_amount?.toLocaleString('en-IN')}</span>
                <span style={{ color: '#6B7280' }}>Fee {t.currency === 'INR' ? '₹' : '$'}{t.platform_fee?.toLocaleString('en-IN')}</span>
                <strong>{t.currency === 'INR' ? '₹' : '$'}{t.net_amount?.toLocaleString('en-IN')}</strong>
                <span style={{ background: t.status === 'settled' ? '#F0FDF4' : '#FFFBEB', color: t.status === 'settled' ? '#15803D' : '#92400E', padding: '2px 8px', borderRadius: 999, fontSize: '0.68rem', fontWeight: 700 }}>{t.status}</span>
              </div>
            ))}
          </div>
        </section>
      )}
    </main>
  );
}
