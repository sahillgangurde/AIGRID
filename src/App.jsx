import React, { useState, useEffect, useRef } from 'react';
import { 
  Lock, Send, X, AlertTriangle 
} from 'lucide-react';

const DEFAULT_CREATORS = [
  {
    id: 'c1',
    alias: 'Studio Phantom',
    legalStatus: 'Aadhaar Verified',
    specialty: 'Hyper-realistic FLUX.1 commercials & cinematic sneakers',
    rating: '4.98',
    projects: 34,
    rate: '$45/hr compute',
    tools: ['FLUX.1', 'ComfyUI', 'Runway Gen-3'],
    image: '/assets/v1_06.jpg'
  },
  {
    id: 'c2',
    alias: 'Cipher Canvas',
    legalStatus: 'Passport Stamped',
    specialty: 'High-fashion editorial lookbooks & photoreal luxury apparel',
    rating: '5.00',
    projects: 51,
    rate: '$60/hr compute',
    tools: ['Midjourney v6', 'Magnific AI', 'Photoshop'],
    image: '/assets/v2_02.jpg'
  },
  {
    id: 'c3',
    alias: 'Elena Arch',
    legalStatus: 'Gov ID Verified',
    specialty: 'Cyber-brutalist architecture & monolithic CGI environments',
    rating: '4.95',
    projects: 28,
    rate: '$50/hr compute',
    tools: ['SDXL', 'ControlNet Depth', 'Topaz Gigapixel'],
    image: '/assets/v1_01.jpg'
  },
  {
    id: 'c4',
    alias: 'Vortex Motion',
    legalStatus: 'KYC Sealed',
    specialty: 'Short-form Instagram reels & dynamic product CGI simulation',
    rating: '4.92',
    projects: 42,
    rate: '$40/hr compute',
    tools: ['Runway Gen-3', 'Luma Dream Machine', 'After Effects'],
    image: '/assets/v2_00.jpg'
  }
];

export default function App() {
  const [activeView, setActiveView] = useState('home'); // 'home' | 'creators' | 'workspace'
  const [briefModalOpen, setBriefModalOpen] = useState(false);
  const [piiModalOpen, setPiiModalOpen] = useState(false);
  const [piiWarningDetails, setPiiWarningDetails] = useState('');
  const [toast, setToast] = useState(null);
  const [liveCreators, setLiveCreators] = useState(DEFAULT_CREATORS);

  // Brief Form State
  const [briefTitle, setBriefTitle] = useState('');
  const [briefDesc, setBriefDesc] = useState('');
  const [briefBudget, setBriefBudget] = useState('$2k-$5k');
  const [briefDeadline, setBriefDeadline] = useState('');
  const [briefBrand, setBriefBrand] = useState('Puma Innovation Lab');
  const [briefEmail, setBriefEmail] = useState('creative@puma.com');

  // Project & Escrow State
  const [finalReleased, setFinalReleased] = useState(false);
  const [disputeActive, setDisputeActive] = useState(false);

  // Chat State
  const [chatInput, setChatInput] = useState('');
  const [chatMessages, setChatMessages] = useState([
    {
      id: 1,
      sender: 'system',
      text: '🔒 Secure Anonymous Channel active. Direct phone, email, and off-platform links are blocked to protect your $4,500 escrow deposit.',
      isSystem: true
    },
    {
      id: 2,
      sender: 'Studio Phantom',
      text: 'Hello! I reviewed your brief for the Cyber-Puma commercial. The custom FLUX.1 LoRA fine-tuning with dynamic neon physics is ready for kickoff.',
      isIncoming: true
    }
  ]);
  const messagesEndRef = useRef(null);

  const showToast = (msg) => {
    setToast(msg);
    setTimeout(() => setToast(null), 3500);
  };

  // Fetch Live Creators from Backend API on Mount
  useEffect(() => {
    fetch('/api/creators')
      .then(res => res.json())
      .then(data => {
        if (data && Array.isArray(data.creators) && data.creators.length > 0) {
          const mapped = data.creators.slice(0, 8).map(c => ({
            id: c.id,
            alias: c.name || 'Studio Creator',
            legalStatus: c.compliance_tier === 'COMMERCIAL_NON_BRANDED' ? 'ZK-Verified' : 'C2PA Stamped',
            specialty: c.specialty || 'Generative commercial production',
            rating: c.rating ? Number(c.rating).toFixed(2) : '4.95',
            projects: c.completed_projects || 24,
            rate: `$${c.hourly_compute_rate || 45}/hr compute`,
            tools: c.tools && c.tools.length > 0 ? c.tools.slice(0, 3) : ['FLUX.1', 'ComfyUI'],
            image: c.avatar || '/assets/v1_06.jpg'
          }));
          setLiveCreators(mapped);
        }
      })
      .catch(() => {
        // Fallback to default curated creators if backend is offline
        setLiveCreators(DEFAULT_CREATORS);
      });
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  // PII Interceptor & Chat Handler (Handles Continuous & Spaced Evasions)
  const handleSendMessage = (e) => {
    if (e) e.preventDefault();
    const text = chatInput.trim();
    if (!text) return;

    // Direct patterns
    const rawPhonePattern = /\b\d{10}\b|\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b/;
    const emailPattern = /\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b/;
    const upiPattern = /\b[a-zA-Z0-9._-]{3,256}@(upi|paytm|phonepe|gpay|ybl|okhdfcbank)\b/;
    const bypassPattern = /\b(whatsapp|telegram|call me|text me|dm me|reach me at|my number|phone number)\b/i;

    // Spaced Evasion Check: e.g. "9 8 7 6 5 4 3 2 1 0" or "5 5 5 5 5 5 5 5 5 5"
    const digitsOnly = text.replace(/\D/g, '');
    const hasSpacedDigits = digitsOnly.length >= 10 && digitsOnly.length <= 13;

    if (rawPhonePattern.test(text) || hasSpacedDigits || emailPattern.test(text) || upiPattern.test(text) || bypassPattern.test(text)) {
      setPiiWarningDetails(
        (rawPhonePattern.test(text) || hasSpacedDigits) ? 'Personal phone numbers and contact sequences are blocked.' :
        emailPattern.test(text) ? 'Email addresses are blocked.' :
        upiPattern.test(text) ? 'Direct UPI handles are blocked.' :
        'Off-platform contact references are blocked.'
      );
      setPiiModalOpen(true);
      return;
    }

    setChatMessages(prev => [
      ...prev,
      {
        id: Date.now(),
        sender: 'You (Puma Brand)',
        text: text,
        isOutgoing: true
      }
    ]);
    setChatInput('');
  };

  // Live Post Brief to Backend Database
  const handlePostBrief = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch('/api/briefs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: briefTitle || 'Commercial Campaign Brief',
          description: briefDesc || 'High-energy commercial deliverable',
          budget_min: 2000,
          budget_max: 5000,
          brand_name: briefBrand || 'Brand Partner',
          brand_email: briefEmail || 'brand@example.com'
        })
      });

      if (res.ok) {
        showToast(`✓ Brief "${briefTitle || 'New Campaign'}" successfully saved to database!`);
      } else {
        showToast(`✓ Brief "${briefTitle || 'New Campaign'}" posted!`);
      }
    } catch {
      showToast(`✓ Brief "${briefTitle || 'New Campaign'}" posted!`);
    }

    setBriefModalOpen(false);
    setActiveView('workspace');
  };

  // Release 70% Final Deliverable via Backend Payout
  const handleReleaseFinal = async () => {
    setFinalReleased(true);
    try {
      await fetch('/api/finance/payout/demo-release', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ amount: 3150, recipient_alias: 'Studio Phantom' })
      });
    } catch {
      // Graceful offline fallback
    }
    showToast('✓ Milestone 2 ($3,150) settled & released to Studio Phantom!');
  };

  return (
    <div className="app-container">
      {/* Toast Notification */}
      {toast && <div className="toast-notice">{toast}</div>}

      {/* Primary Navigation */}
      <nav className="navbar">
        <div className="navbar-inner">
          <div className="nav-brand" onClick={() => setActiveView('home')}>
            <span className="nav-brand-title">Hypear AI</span>
          </div>

          <div className="nav-links">
            <button 
              className={`nav-link ${activeView === 'home' ? 'active' : ''}`}
              onClick={() => setActiveView('home')}
            >
              How it works
            </button>
            <button 
              className={`nav-link ${activeView === 'creators' ? 'active' : ''}`}
              onClick={() => setActiveView('creators')}
            >
              Browse creators
            </button>
            <button 
              className={`nav-link ${activeView === 'workspace' ? 'active' : ''}`}
              onClick={() => setActiveView('workspace')}
            >
              Project & Chat
            </button>
          </div>

          <div className="nav-actions">
            <button className="btn-forest" onClick={() => setBriefModalOpen(true)}>
              Post a brief
            </button>
          </div>
        </div>
      </nav>

      {/* VIEW 1: HOME / LANDING */}
      {activeView === 'home' && (
        <main>
          {/* Hero Section */}
          <section className="hero-section">
            <div>
              <h1 className="hero-title">
                The AI-native<br />creative marketplace.
              </h1>
              <p className="hero-subtitle">
                Brands find their next campaign. AI-creators find their next job. AI pairs them.
              </p>
              
              <div className="hero-cta-group">
                <button className="btn-forest" onClick={() => setBriefModalOpen(true)}>
                  Hire a creator
                </button>
                <button className="btn-outline" onClick={() => setActiveView('creators')}>
                  Browse creators
                </button>
              </div>

              <div className="hero-stats">
                <div className="stat-item">
                  <span className="stat-number">189</span>
                  <span className="stat-label">Creators</span>
                </div>
                <div className="stat-item">
                  <span className="stat-number">933</span>
                  <span className="stat-label">Projects Published</span>
                </div>
                <div className="stat-item">
                  <span className="stat-number">128</span>
                  <span className="stat-label">Brands</span>
                </div>
              </div>
            </div>

            <div className="hero-image-wrapper">
              <img 
                src="/assets/crops/pear_hero.jpg" 
                alt="Hypear Creative" 
                className="hero-pear-img"
                onError={(e) => {
                  e.target.src = 'https://images.unsplash.com/photo-1544717305-2782549b5136?auto=format&fit=crop&w=600&q=80';
                }}
              />
            </div>
          </section>

          {/* Brand Logo Ticker */}
          <div className="brand-ticker">
            <div className="ticker-track">
              {['VERTEX', 'LUMEN', 'ATLAS', 'HALCYON', 'FORMA', 'MONARCH', 'QUILL & CO.', 'NORTHWIND', 'VERTEX', 'LUMEN', 'ATLAS', 'HALCYON', 'FORMA'].map((b, i) => (
                <span key={i} className="ticker-item">{b}</span>
              ))}
            </div>
          </div>

          {/* The Pairing Section */}
          <section className="section-wrapper">
            <div className="section-tag">The Pairing</div>
            <h2 className="section-heading">Brands and creators, paired</h2>
            <p className="section-desc">
              Every pairing starts with a pear — browse real work, find your fit, and collaborate directly with anonymous privacy and smart escrow protection.
            </p>

            <div className="creators-grid">
              {liveCreators.slice(0, 3).map(c => (
                <div key={c.id} className="creator-card">
                  <img 
                    src={c.image} 
                    alt={c.alias} 
                    className="creator-card-img" 
                    onError={(e) => { e.target.src = 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=500&q=80'; }}
                  />
                  <div className="creator-card-body">
                    <div className="creator-meta-header">
                      <span className="creator-alias">{c.alias}</span>
                      <span className="creator-rating">★ {c.rating}</span>
                    </div>
                    <p className="creator-specialty">{c.specialty}</p>
                    <div className="creator-tags">
                      {c.tools.map((t, idx) => (
                        <span key={idx} className="tag-pill">{t}</span>
                      ))}
                    </div>
                    <div className="creator-card-footer">
                      <span className="creator-rate">{c.rate}</span>
                      <button 
                        className="btn-forest" 
                        style={{ padding: '8px 16px', fontSize: '0.8rem' }}
                        onClick={() => setActiveView('workspace')}
                      >
                        Start Project
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </main>
      )}

      {/* VIEW 2: BROWSE CREATORS */}
      {activeView === 'creators' && (
        <main className="section-wrapper">
          <div className="section-tag">Certified Talent</div>
          <h1 className="section-heading">Meet the creators who deliver</h1>
          <p className="section-desc">
            AI-native creators with verified portfolios and zero-knowledge identity vaults. Review their work, check ratings, and hire directly.
          </p>

          <div className="creators-grid" style={{ marginTop: 36 }}>
            {liveCreators.map(c => (
              <div key={c.id} className="creator-card">
                <img 
                  src={c.image} 
                  alt={c.alias} 
                  className="creator-card-img" 
                  onError={(e) => { e.target.src = 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=500&q=80'; }}
                />
                <div className="creator-card-body">
                  <div className="creator-meta-header">
                    <span className="creator-alias">{c.alias}</span>
                    <span className="creator-rating">★ {c.rating} ({c.projects} projects)</span>
                  </div>
                  <p className="creator-specialty">{c.specialty}</p>
                  <div className="creator-tags">
                    {c.tools.map((t, idx) => (
                      <span key={idx} className="tag-pill">{t}</span>
                    ))}
                  </div>
                  <div className="creator-card-footer">
                    <span className="creator-rate">{c.rate}</span>
                    <button 
                      className="btn-forest" 
                      style={{ padding: '8px 16px', fontSize: '0.8rem' }}
                      onClick={() => {
                        showToast(`Opened project channel with ${c.alias}`);
                        setActiveView('workspace');
                      }}
                    >
                      Hire & Chat
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </main>
      )}

      {/* VIEW 3: PROJECT & CHAT WORKSPACE */}
      {activeView === 'workspace' && (
        <main className="workspace-container">
          <div className="workspace-card">
            {/* Workspace Header */}
            <div className="workspace-header">
              <div>
                <h2 className="project-title">Cyber-Puma • 15s High-Energy Commercial</h2>
                <div className="project-parties">
                  Brand: <strong>Puma Innovation Lab</strong> • Creator: <strong>Studio Phantom (Pseudonym Masked)</strong>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <span className="escrow-badge">
                  <Lock size={14} /> $4,500.00 Escrow Protected
                </span>
                {disputeActive && (
                  <span style={{ background: '#FEE2E2', color: '#DC2626', padding: '6px 12px', borderRadius: 999, fontSize: '0.78rem', fontWeight: 700 }}>
                    Escrow Frozen in Dispute
                  </span>
                )}
              </div>
            </div>

            {/* Milestones Strip */}
            <div className="milestones-strip">
              <div className="milestone-node completed">
                <span className="milestone-check">✓</span>
                <span>Milestone 1: 30% Upfront Kickoff ($1,350 Released)</span>
              </div>
              <div style={{ color: '#D1D5DB' }}>──</div>
              <div className={`milestone-node ${finalReleased ? 'completed' : ''}`}>
                <span className="milestone-check">{finalReleased ? '✓' : '2'}</span>
                <span>Milestone 2: 70% Final Master Delivery ($3,150)</span>
              </div>

              <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
                <button 
                  className="btn-outline" 
                  style={{ padding: '6px 14px', fontSize: '0.78rem' }}
                  disabled={finalReleased}
                  onClick={handleReleaseFinal}
                >
                  {finalReleased ? '✓ Milestone 2 Settled' : 'Release 70% Final'}
                </button>
                <button 
                  className="btn-outline" 
                  style={{ padding: '6px 14px', fontSize: '0.78rem', color: '#DC2626', borderColor: '#FCA5A5' }}
                  onClick={() => {
                    setDisputeActive(!disputeActive);
                    showToast(disputeActive ? 'Escrow unfrozen.' : 'Escrow FROZEN pending arbitration!');
                  }}
                >
                  {disputeActive ? 'Unfreeze Escrow' : 'Freeze Escrow'}
                </button>
              </div>
            </div>

            {/* Chat Thread */}
            <div className="chat-thread">
              {chatMessages.map(m => (
                <div 
                  key={m.id} 
                  className={`bubble ${m.isSystem ? 'bubble-system' : (m.isOutgoing ? 'bubble-sent' : 'bubble-received')}`}
                >
                  {!m.isSystem && <div className="bubble-author">{m.sender}</div>}
                  <div>{m.text}</div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>

            {/* Chat Input */}
            <form className="chat-composer" onSubmit={handleSendMessage}>
              <input 
                type="text" 
                className="chat-input-clean" 
                placeholder="Type a message to Studio Phantom... (Test sharing phone or email to see the shield)"
                value={chatInput}
                onChange={e => setChatInput(e.target.value)}
              />
              <button type="submit" className="btn-forest">
                <span>Send</span> <Send size={14} />
              </button>
            </form>
          </div>
        </main>
      )}

      {/* POST A BRIEF MODAL */}
      {briefModalOpen && (
        <div className="modal-backdrop">
          <div className="modal-content">
            <div className="modal-inner-header">
              <div>
                <h3 className="modal-heading">What are you working on?</h3>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: 4 }}>
                  One paragraph is enough to start. AI will match you with certified creators.
                </p>
              </div>
              <button className="modal-close-btn" onClick={() => setBriefModalOpen(false)}>
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handlePostBrief} className="modal-inner-body">
              <div>
                <label className="form-label-clean">Brief title</label>
                <input 
                  type="text" 
                  className="form-input-clean" 
                  placeholder="e.g. 15s High-Energy Cyberpunk Commercial for Sneakers"
                  value={briefTitle}
                  onChange={e => setBriefTitle(e.target.value)}
                  required
                />
              </div>

              <div>
                <label className="form-label-clean">Describe the project</label>
                <textarea 
                  className="form-input-clean" 
                  rows={4}
                  placeholder="What are you making, and what role would the AI creator play? e.g. We need fluid neon sole physics and custom LoRA fine-tuning for an upcoming launch."
                  value={briefDesc}
                  onChange={e => setBriefDesc(e.target.value)}
                  required
                />
              </div>

              <div className="form-row">
                <div>
                  <label className="form-label-clean">Budget</label>
                  <select 
                    className="form-input-clean"
                    value={briefBudget}
                    onChange={e => setBriefBudget(e.target.value)}
                  >
                    <option value="$1k-$2k">$1k - $2k</option>
                    <option value="$2k-$5k">$2k - $5k</option>
                    <option value="$5k-$10k">$5k - $10k</option>
                    <option value="$10k+">$10k+ Enterprise</option>
                  </select>
                </div>

                <div>
                  <label className="form-label-clean">Needed by (optional)</label>
                  <input 
                    type="date" 
                    className="form-input-clean" 
                    value={briefDeadline}
                    onChange={e => setBriefDeadline(e.target.value)}
                  />
                </div>
              </div>

              <div className="form-row">
                <div>
                  <label className="form-label-clean">Brand name</label>
                  <input 
                    type="text" 
                    className="form-input-clean" 
                    value={briefBrand}
                    onChange={e => setBriefBrand(e.target.value)}
                    required
                  />
                </div>
                <div>
                  <label className="form-label-clean">Work email</label>
                  <input 
                    type="email" 
                    className="form-input-clean" 
                    value={briefEmail}
                    onChange={e => setBriefEmail(e.target.value)}
                    required
                  />
                </div>
              </div>

              <div style={{ marginTop: 8, display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
                <button type="button" className="btn-outline" onClick={() => setBriefModalOpen(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-forest">
                  Continue & Post Brief
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* PII WARNING MODAL */}
      {piiModalOpen && (
        <div className="modal-backdrop">
          <div className="modal-content" style={{ maxWidth: 460 }}>
            <div className="modal-inner-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <AlertTriangle size={24} color="#DC2626" />
                <h3 className="modal-heading" style={{ fontSize: '1.4rem' }}>Direct Contact Blocked</h3>
              </div>
              <button className="modal-close-btn" onClick={() => setPiiModalOpen(false)}>
                <X size={20} />
              </button>
            </div>

            <div className="modal-inner-body">
              <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
                {piiWarningDetails}
              </p>
              <div style={{ background: '#FEF2F2', border: '1px solid #FCA5A5', padding: '14px 18px', borderRadius: 12, fontSize: '0.85rem', color: '#991B1B' }}>
                Hypear protects your $4,500 escrow and C2PA provenance by keeping communication within the platform. Please do not share personal phone numbers, emails, or off-platform handles.
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 8 }}>
                <button className="btn-forest" onClick={() => setPiiModalOpen(false)}>
                  I Understand
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="footer-clean">
        <div className="footer-inner">
          <div>
            <strong>Hypear AI</strong> • The platform for AI creators.
          </div>
          <div style={{ display: 'flex', gap: 20 }}>
            <span>How it works</span>
            <span>Terms</span>
            <span>Privacy</span>
            <span>© 2026 Hypear AI. All rights reserved.</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
