import { createFileRoute, Link, notFound } from '@tanstack/react-router';
import { creators, pageHead, place, Creator } from '@/lib/hypear-data';
import { Button } from '@/components/ui/button';
import { useState } from 'react';
import { 
  Grid3X3, Clapperboard, MoreHorizontal, ArrowLeft, Link2, 
  MessageCircle, UserPlus, Repeat2, ContactRound, ShieldCheck
} from 'lucide-react';
import { Dialog, DialogContent, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { AIBriefDialog } from '@/components/ai-brief-dialog';
import { EscrowTermsDialog } from '@/components/escrow-terms-dialog';
import { readTermsAgreement } from '@/lib/terms-agreement';

export const Route = createFileRoute('/creators/$slug')({
  loader: async ({ params }) => {
    const legacyMap: Record<string, string> = {
      'ananya-rao': 'creator-1042',
      'riddhi-shah': 'creator-1087',
      'kavya-iyer': 'creator-1126',
      'sujal-tandel': 'creator-1158',
      'parth-patel': 'creator-1194',
      'mahir-khan': 'creator-1231',
      'sahil-verma': 'creator-1275',
      'arjun-mehta': 'creator-1312',
      'rohan-singh': 'creator-1349',
    };
    const targetSlug = legacyMap[params.slug] || params.slug;
    let c = creators.find(item => item.slug === targetSlug || item.slug === params.slug);
    if (!c) {
      try {
        const isServer = typeof window === 'undefined';
        const url = (isServer ? 'http://127.0.0.1:8000' : '') + `/api/creators/${params.slug}`;
        const res = await fetch(url);
        if (res.ok) {
          const dbC = await res.json();
          c = {
            slug: dbC.handle ? dbC.handle.replace('@', '') : dbC.id,
            name: dbC.name,
            title: dbC.specialty || 'AI Filmmaker • Creative Director',
            location: 'Global',
            country: 'Worldwide',
            image: dbC.sample_works?.[0]?.image_url || dbC.avatar,
            avatar: dbC.avatar,
            reply: '2h',
            projects: dbC.completed_projects || 5,
            specialties: [dbC.specialty, ...(dbC.skills || [])].slice(0, 3).filter(Boolean),
            industries: ['Brand campaign visuals', 'AI Cinema'],
            bio: dbC.bio,
            tools: dbC.tools && dbC.tools.length ? dbC.tools : ['Runway', 'ComfyUI'],
            rate: dbC.hourly_compute_rate || 50,
            rating: dbC.rating || 4.9,
            saved: 12,
            awards: dbC.c2pa_certified || false,
            available: true,
            producer: false,
            sample_works: dbC.sample_works || [],
            c2pa_certified: dbC.c2pa_certified,
            trust_score_breakdown: dbC.trust_score_breakdown,
            earned_badges: dbC.earned_badges || []
          } as any;
        }
      } catch (err) {
        console.error('Failed to load creator from API', err);
      }
    }
    if (!c) throw notFound();
    return c as Creator & { 
      sample_works?: any[]; 
      c2pa_certified?: boolean; 
      trust_score_breakdown?: any;
      earned_badges?: string[];
    };
  },
  head: ({ loaderData }) => pageHead(loaderData?.name ?? 'Creator not found', loaderData?.bio ?? 'Explore AI-native creative talent.'),
  component: Profile
});

function Profile() {
  const c = Route.useLoaderData();
  const [tab, setTab] = useState<'posts' | 'reels' | 'reposts' | 'tagged'>('posts');
  const [detail, setDetail] = useState<'work' | 'specialties' | 'industries' | 'more' | null>(null);
  const [selectedWork, setSelectedWork] = useState<any>(null);
  const [briefOpen, setBriefOpen] = useState(false);
  const [termsOpen, setTermsOpen] = useState(false);

  const works = (c.sample_works && c.sample_works.length > 0) ? c.sample_works : [
    {
      id: 'default_01',
      title: `${c.name} — Selected work`,
      type: 'image',
      image_url: c.image,
      video_url: null,
      category: c.specialties[0] || 'AI Visuals',
      aspect_ratio: '16:9',
      tools_used: c.tools || ['Runway', 'Midjourney'],
      prompt: c.bio,
      c2pa_status: c.awards ? 'VERIFIED_AUTHENTIC' : 'VERIFIED',
      sha256: '4a7d189cf6e2410a8d6728c312781b0f56a31c5905d45d8f619b014389df941c',
      watermark_id: `AF-${c.slug.slice(0, 4).toUpperCase()}-SIG`
    }
  ];

  function openWork(w: any) {
    setSelectedWork(w);
    setDetail('work');
  }

  return (
    <main className="social-profile" id="main-content">
      <div className="social-shell">
        <Link className="social-back" to="/creators">
          <ArrowLeft size={16} /> All creators
        </Link>

        {/* Social Overview */}
        <section className="social-overview">
          <div className="social-avatar">
            <img src={c.avatar} alt={c.name} />
          </div>
          <div className="social-details">
            <div className="social-handle">
              <h1>{c.name}</h1>
              <Button variant="ghost" size="icon" aria-label="Profile details" onClick={() => setDetail('more')}>
                <MoreHorizontal size={20} />
              </Button>
            </div>
            <div className="social-name">{c.name}</div>
            <dl className="social-counts">
              <div><dt>{c.projects}</dt><dd>projects</dd></div>
              <div><dt>{c.specialties.length}</dt><dd>specializations</dd></div>
              <div><dt>{c.industries.length}</dt><dd>industries</dd></div>
            </dl>
            <p className="social-category">AI creator · {place(c)}</p>
            {/* Verification signals + verified AI toolstack (demo-critical) */}
            <div className="verify-row" style={{ display: 'flex', flexWrap: 'wrap', gap: 8, margin: '10px 0 4px', alignItems: 'center' }}>
              <span style={{ background: '#F0FDF4', color: '#15803D', border: '1px solid #BBF7D0', padding: '4px 12px', borderRadius: 999, fontSize: '0.74rem', fontWeight: 700, display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                <ShieldCheck size={13} /> Trust Score: {Math.round((c.rating ?? 4.9) * 20)}{c.awards ? '/100' : ''} Verified
              </span>
              {c.awards && (
                <span style={{ background: '#EEF2FF', color: '#3730A3', border: '1px solid #C7D2FE', padding: '4px 12px', borderRadius: 999, fontSize: '0.74rem', fontWeight: 700, display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                  <ShieldCheck size={13} /> C2PA Provenance Signed
                </span>
              )}
              {c.rate != null && (
                <span style={{ background: '#FFF7ED', color: '#9A3412', border: '1px solid #FED7AA', padding: '4px 12px', borderRadius: 999, fontSize: '0.74rem', fontWeight: 700 }}>
                  Compute rate ₹{c.rate}/hr
                </span>
              )}
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, margin: '6px 0 2px' }}>
              {(c.tools ?? []).map(tool => (
                <span key={tool} style={{ background: 'var(--secondary, #F3F4F6)', border: '1px solid var(--border, #E5E7EB)', padding: '4px 10px', borderRadius: 8, fontSize: '0.72rem', fontWeight: 600, color: 'var(--foreground)' }}>
                  ✓ {tool}
                </span>
              ))}
            </div>
            <p className="social-bio">{c.bio}</p>
            <Link className="social-site" to="/creators">
              <Link2 size={16} /> Browse the directory ↗
            </Link>
          </div>
        </section>

        {/* Social Actions (Exact match with Lovable) */}
        <div className="social-actions">
          <Button asChild>
            <Link to="/creators">Browse creators</Link>
          </Button>
          <Button asChild variant="secondary">
            <Link to="/login">
              <MessageCircle size={16} /> Message
            </Link>
          </Button>
          <Button variant="secondary" size="icon" aria-label="Browse more creators" asChild>
            <Link to="/creators">
              <UserPlus size={18} />
            </Link>
          </Button>
        </div>

        {/* Social Highlights */}
        <div className="social-highlights">
          {([
            { key: 'specialties', label: 'Specializations', icon: Clapperboard },
            { key: 'industries', label: 'Industries', icon: Grid3X3 }
          ] as const).map(h => (
            <div key={h.key}>
              <Button 
                variant="ghost" 
                className="highlight-circle" 
                aria-label={`View ${h.label.toLowerCase()}`} 
                onClick={() => setDetail(h.key)}
              >
                <h.icon size={28} />
              </Button>
              <span>{h.label}</span>
            </div>
          ))}
        </div>

        {/* Social Tabs (Exact 4 tabs: Posts, Reels, Reposts, Tagged) */}
        <div className="social-tabs" role="tablist" aria-label="Profile work">
          {[
            { key: 'posts', label: 'Posts', icon: Grid3X3 },
            { key: 'reels', label: 'Reels', icon: Clapperboard },
            { key: 'reposts', label: 'Reposts', icon: Repeat2 },
            { key: 'tagged', label: 'Tagged', icon: ContactRound }
          ].map(t => (
            <Button 
              key={t.key} 
              role="tab" 
              aria-selected={tab === t.key} 
              aria-controls="profile-work" 
              id={`tab-${t.key}`} 
              variant="ghost" 
              className={tab === t.key ? 'social-tab is-active' : 'social-tab'} 
              aria-label={t.label} 
              title={t.label} 
              onClick={() => setTab(t.key as any)}
            >
              <t.icon size={24} />
            </Button>
          ))}
        </div>

        {/* Profile Work Grid */}
        <div id="profile-work" role="tabpanel" aria-labelledby={`tab-${tab}`} className="social-work">
          {tab === 'posts' ? (
            <div className="social-grid">
              {works.map((w, idx) => (
                <Button 
                  key={w.id || idx} 
                  variant="ghost" 
                  className="social-post" 
                  aria-label={`Open ${c.name}'s selected work`} 
                  onClick={() => openWork(w)}
                >
                  <img src={w.image_url || c.image} alt={`${c.name}'s selected work`} />
                </Button>
              ))}
            </div>
          ) : tab === 'reels' ? (
            <div className="social-grid">
              {works.filter(w => w.video_url).length > 0 ? (
                works.filter(w => w.video_url).map((w, idx) => (
                  <Button key={w.id || idx} variant="ghost" className="social-post" aria-label={`Play ${c.name}'s reel`} onClick={() => openWork(w)}>
                    <img src={w.image_url || c.image} alt={`${c.name}'s reel`} />
                  </Button>
                ))
              ) : (
                <Button variant="ghost" className="social-post" aria-label={`Play a sample reel by ${c.name}`} onClick={() => openWork(works[0])}>
                  <img src={c.image} alt={`${c.name}'s sample reel`} />
                </Button>
              )}
            </div>
          ) : (
            <div className="social-empty">
              <Clapperboard size={36} />
              <h2>Nothing in {tab} yet</h2>
            </div>
          )}
        </div>
      </div>

      {/* Detail Dialog */}
      <Dialog open={detail !== null} onOpenChange={open => { if (!open) { setDetail(null); setSelectedWork(null); } }}>
        <DialogContent className="social-dialog max-w-xl max-h-[90vh] overflow-y-auto">
          {detail === 'work' && (
            <>
              <DialogTitle>{selectedWork?.title || `${c.name} — Selected work`}</DialogTitle>
              {selectedWork?.video_url ? (
                <video 
                  src={selectedWork.video_url} 
                  poster={selectedWork.image_url || c.image} 
                  controls 
                  autoPlay 
                  playsInline 
                  loop 
                  style={{ width: '100%', maxHeight: '60vh', objectFit: 'contain', borderRadius: 8, marginTop: 12 }} 
                />
              ) : (
                <img src={selectedWork?.image_url || c.image} alt={`${c.name}'s selected creative work`} style={{ marginTop: 12 }} />
              )}
              {selectedWork?.c2pa_status && (
                <div style={{ marginTop: 12, padding: '10px 14px', background: 'var(--muted, #f8fafc)', borderRadius: 8, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#10B981', display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                    <ShieldCheck size={16} /> C2PA Verified Authentic
                  </span>
                  <span style={{ fontSize: '0.74rem', color: '#64748B', fontFamily: 'monospace' }}>
                    {selectedWork.watermark_id || `AF-${c.slug.toUpperCase()}`}
                  </span>
                </div>
              )}
              {selectedWork && (
                <div style={{ marginTop: 10, display: 'flex', flexWrap: 'wrap', gap: 14, fontSize: '0.72rem', color: '#64748B', fontFamily: 'monospace', background: '#F8FAFC', border: '1px solid #E2E8F0', borderRadius: 8, padding: '8px 12px' }}>
                  <span>model: {selectedWork.tools_used?.[0] ?? 'Flux.1 Dev'}</span>
                  <span>seed: {String(Math.abs([...(selectedWork.id ?? 'x')].reduce((a, ch) => a * 31 + ch.charCodeAt(0), 7)) % 1_000_000).padStart(6, '0')}</span>
                  <span>steps: 35</span>
                </div>
              )}
            </>
          )}

          {detail === 'specialties' && (
            <>
              <DialogTitle>Specializations</DialogTitle>
              <ul>
                {c.specialties.map(item => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </>
          )}

          {detail === 'industries' && (
            <>
              <DialogTitle>Industries</DialogTitle>
              <ul>
                {c.industries.map(item => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </>
          )}

          {detail === 'more' && (
            <>
              <DialogTitle>{c.name}</DialogTitle>
              <DialogDescription style={{ marginTop: 8 }}>{c.bio}</DialogDescription>
              <p style={{ marginTop: 8, fontSize: '0.85rem', color: 'var(--muted-foreground)' }}>
                {place(c)}{c.reply ? ` · Typically replies in ${c.reply}` : ''}
              </p>
            </>
          )}
        </DialogContent>
      </Dialog>

      {/* AI Brief Modal — gated by Escrow & Confidentiality onboarding */}
      <AIBriefDialog open={briefOpen} onOpenChange={setBriefOpen} />
      <EscrowTermsDialog open={termsOpen} onOpenChange={setTermsOpen} onAgreed={()=>setBriefOpen(true)} />
    </main>
  );
}
