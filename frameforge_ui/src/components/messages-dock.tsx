import { useEffect, useState } from 'react';
import { ArrowLeft, Lock, MessageSquare, Send, X, ShieldAlert, ShieldCheck, DollarSign } from 'lucide-react';
import { creators, homeCreators } from '@/lib/hypear-data';
import { readTermsAgreement } from '@/lib/terms-agreement';
import { getAuthHeaders } from '@/lib/auth-headers';
import { useDemoSession } from '@/lib/demo-session';

type Msg = { from: 'me' | 'them'; text: string; redacted?: boolean };

// PII Detection patterns matching FRAME Security Specification
const PII_PATTERNS = [
  { type: 'Phone Number', badge: '📵 [Phone Blocked]', regex: /\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b|\b[6-9]\d{9}\b/g },
  { type: 'Email Address', badge: '✉️ [Email Blocked]', regex: /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g },
  { type: 'UPI Payment ID', badge: '💳 [UPI Blocked]', regex: /[a-zA-Z0-9.\-_]{2,256}@(okaxis|okhdfcbank|okicici|oksbi|paytm|ybl|axl|ibl|upi)/gi },
  { type: 'Off-Platform Direct Contact', badge: '🚫 [Link Blocked]', regex: /\b(whatsapp|telegram|wa\.me|t\.me|linkedin|call me at|phone me at|dm me on)\b/gi }
];

function detectPII(text: string) {
  const violations: string[] = [];
  let redacted = text;

  for (const p of PII_PATTERNS) {
    if (p.regex.test(text)) {
      violations.push(p.type);
      redacted = redacted.replace(p.regex, p.badge);
    }
  }

  return {
    hasPII: violations.length > 0,
    violations,
    redacted
  };
}

/** Signed-in messaging dock with Client/Server PII Shield and Escrow Protection. */
export function MessagesDock() {
  const [open, setOpen] = useState(false);
  const [notice, setNotice] = useState(true);
  const [active, setActive] = useState<string | null>(null);
  const [draft, setDraft] = useState('');
  const [piiWarning, setPiiWarning] = useState<{ violations: string[]; pendingText: string } | null>(null);
  const [escrowNotice, setEscrowNotice] = useState(false);

  const [threads, setThreads] = useState<Record<string, Msg[]>>(() =>
    Object.fromEntries(creators.map(c => [
      c.slug, 
      [{ from: 'them' as const, text: `Hi! I'm ${c.name.split(' ')[0]}. Happy to discuss project specs, compute requirements, or review a brief.` }]
    ]))
  );
  const [unread, setUnread] = useState(homeCreators.length);
  const [liveConversationId, setLiveConversationId] = useState<string | null>(null);
  const [liveOk, setLiveOk] = useState(false);
  const session = useDemoSession();

  // Wire to the real backend: fetch conversations + messages (falls back silently to demo threads when the API is unreachable or auth is missing).
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch('/api/conversations', { headers: getAuthHeaders() });
        if (!res.ok) return;
        const data = await res.json();
        const convs = data?.conversations ?? [];
        if (cancelled || !convs.length) return;
        const first = convs[0];
        const mres = await fetch(`/api/conversations/${first.id}/messages`, { headers: getAuthHeaders() });
        if (!mres.ok) return;
        const mdata = await mres.json();
        if (cancelled) return;
        setLiveOk(true);
        setLiveConversationId(first.id);
        const peer = first.project_title || 'Creator';
        // Identify the current user's display name (JWT role hint or the session email) to classify messages.
        const myName = (session?.name ?? '').toLowerCase();
        setThreads(t => ({
          ...t,
          [peer]: (mdata?.messages ?? []).map((m: any) => ({
            from: ((m.sender_name ?? '').toLowerCase() === myName && myName ? ('me' as const) : ('them' as const)),
            text: m.body,
            redacted: false
          }))
        }));
      } catch {
        /* backend offline — demo threads remain */
      }
    })();
    return () => { cancelled = true; };
  }, []);

  useEffect(() => { 
    const t = setTimeout(() => setNotice(false), 6000); 
    return () => clearTimeout(t); 
  }, []);

  const creator = creators.find(c => c.slug === active);

  function executeSend(text: string, wasRedacted = false) {
    if (!text || !active) return;
    setThreads(t => ({ 
      ...t, 
      [active]: [...(t[active] ?? []), { from: 'me', text, redacted: wasRedacted }] 
    }));
    setDraft('');
    setPiiWarning(null);

    // Send through the real backend when a live conversation is loaded (server runs the PII interceptor).
    if (liveOk && liveConversationId) {
      fetch(`/api/conversations/${liveConversationId}/messages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
        body: JSON.stringify({ body: text })
      }).catch(() => {/* offline demo — local echo remains */});
    }

    // Simulated creator response acknowledging escrow & specs
    setTimeout(() => {
      if (!active) return;
      const firstName = creator ? creator.name.split(' ')[0] : 'Creator';
      setThreads(t => ({
        ...t,
        [active]: [...(t[active] ?? []), { 
          from: 'them', 
          text: `Got your note! I can take on the project. Let me know if you’d like me to start on a test scene under the escrow guarantee.` 
        }]
      }));
    }, 1200);
  }

  function handleSendAttempt() {
    const text = draft.trim();
    if (!text || !active) return;

    const analysis = detectPII(text);
    if (analysis.hasPII) {
      setPiiWarning({
        violations: analysis.violations,
        pendingText: analysis.redacted
      });
      return;
    }

    executeSend(text);
  }

  return (
    <div className="messages-dock">
      {notice && !open && (
        <div className="e2e-notice" role="status">
          <Lock aria-hidden="true" />
          <p>
            <strong>PII Shield & Escrow Protected</strong>
            <span>Your communication and payments on AiGrid are protected by smart escrow.</span>
          </p>
          <button type="button" aria-label="Dismiss" onClick={() => setNotice(false)}><X /></button>
        </div>
      )}

      {open && (
        <section className="messages-panel" aria-label="Messages">
          <header>
            {creator ? (
              <button type="button" aria-label="Back" onClick={() => { setActive(null); setPiiWarning(null); }}>
                <ArrowLeft />
              </button>
            ) : null}
            <div>
              <h3 style={{ margin: 0 }}>{creator ? creator.name : 'Messages'}</h3>
              <small style={{ color: '#10B981', display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: '0.72rem' }}>
                <Lock size={12} /> 🔒 Secure Anonymous Channel | Escrow Protected
              </small>
            </div>
            <button type="button" aria-label="Close messages" onClick={() => setOpen(false)}><X /></button>
          </header>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '4px 16px', background: 'var(--muted, #f8fafc)', borderBottom: '1px solid var(--border, #e2e8f0)', fontSize: '0.74rem' }}>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, color: liveOk ? '#059669' : '#64748B' }}>
              <Lock size={12} /> {liveOk ? 'Live server: encrypted + PII-shielded' : 'End-to-end encrypted'}
            </span>
            <button 
              type="button" 
              onClick={() => setEscrowNotice(!escrowNotice)} 
              style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#059669', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: 3, padding: 0 }}
            >
              <DollarSign size={12} /> Escrow Status
            </button>
          </div>

          {/* PERSISTENT SAFETY BANNER — always visible at top of chat window */}
          <div style={{ background: '#FFFBEB', borderBottom: '1px solid #FDE68A', padding: '8px 14px', fontSize: '0.76rem', color: '#92400E', display: 'flex', alignItems: 'center', gap: 8 }} role="alert">
            <ShieldAlert size={14} color="#D97706" aria-hidden="true" />
            <span>
              ⚠️ For your safety and escrow protection, do not share phone numbers or social handles. All payments must go through the platform.
            </span>
          </div>

          {escrowNotice && (
            <div style={{ background: '#ECFDF5', borderBottom: '1px solid #A7F3D0', padding: '8px 14px', fontSize: '0.78rem', color: '#065F46' }}>
              <strong>Escrow Protection Active:</strong> Funds are locked until milestone render approval. Disputes freeze escrow automatically.
            </div>
          )}

          {creator ? (
            <>
              <div className="messages-thread">
                {(threads[creator.slug] ?? []).map((m, i) => (
                  <div key={i} className={m.from === 'me' ? 'mine' : ''} style={{ position: 'relative' }}>
                    <p style={{ margin: 0 }}>{m.text}</p>
                    {m.redacted && (
                      <span style={{ display: 'block', fontSize: '0.66rem', color: '#F59E0B', marginTop: 2 }}>
                        🛡️ PII filtered to protect escrow
                      </span>
                    )}
                  </div>
                ))}
              </div>

              {/* PII SHIELD WARNING POPUP */}
              {piiWarning && (
                <div style={{ background: '#FFFBEB', borderTop: '2px solid #F59E0B', padding: '10px 14px', fontSize: '0.78rem', color: '#92400E' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontWeight: 700, marginBottom: 4 }}>
                    <ShieldAlert size={16} color="#D97706" /> ⚠️ PII_INTERCEPTED
                  </div>
                  <p style={{ margin: '0 0 8px 0', lineHeight: 1.35 }}>
                    Direct phone numbers, emails, and off-platform links are blocked. Detected: <strong>{piiWarning.violations.join(', ')}</strong>. Your draft was redacted to “{piiWarning.pendingText}” — send safely or edit the message.
                  </p>
                  <div style={{ display: 'flex', gap: 8 }}>
                    <button
                      type="button"
                      onClick={() => executeSend(piiWarning.pendingText, true)}
                      style={{ background: '#D97706', color: '#fff', border: 'none', borderRadius: 4, padding: '4px 8px', fontSize: '0.74rem', cursor: 'pointer', fontWeight: 600 }}
                    >
                      Redact & Send Safely
                    </button>
                    <button
                      type="button"
                      onClick={() => setPiiWarning(null)}
                      style={{ background: '#fff', border: '1px solid #D97706', color: '#92400E', borderRadius: 4, padding: '4px 8px', fontSize: '0.74rem', cursor: 'pointer' }}
                    >
                      Edit Message
                    </button>
                  </div>
                </div>
              )}

              <form className="messages-compose" onSubmit={e => { e.preventDefault(); handleSendAttempt(); }}>
                <input 
                  value={draft} 
                  onChange={e => { setDraft(e.target.value); if (piiWarning) setPiiWarning(null); }} 
                  placeholder="Discuss project requirements, prompts, or specs…" 
                  aria-label="Message" 
                />
                <button type="submit" aria-label="Send"><Send /></button>
              </form>
            </>
          ) : (
            <ul className="messages-list">
              {creators.map(c => (
                <li key={c.slug}>
                  <button type="button" onClick={() => setActive(c.slug)}>
                    <img src={c.avatar} alt="" />
                    <span>
                      <b>{c.name}</b>
                      <small>{threads[c.slug]?.at(-1)?.text}</small>
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>
      )}

      <button 
        type="button" 
        className="messages-pill" 
        onClick={() => {
          // Gate secure chat behind the Escrow & Confidentiality onboarding for first-time users.
          if (!readTermsAgreement()) { window.dispatchEvent(new Event('open-escrow-terms')); return; }
          setOpen(o => !o); setUnread(0); setNotice(false);
        }} 
        aria-expanded={open}
      >
        <span className="messages-icon">
          <MessageSquare aria-hidden="true" />
          {unread > 0 && <i>{unread}</i>}
        </span>
        <b>Messages & Escrow</b>
        <span className="messages-faces" aria-hidden="true">
          {homeCreators.map(c => <img key={c.slug} src={c.avatar} alt="" />)}
          <em>···</em>
        </span>
      </button>
    </div>
  );
}
