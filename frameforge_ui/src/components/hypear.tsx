import { Link, useRouterState } from '@tanstack/react-router';
import { useState, useEffect } from 'react';
import { ArrowUpRight, Menu, X, Instagram, Linkedin, Youtube } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { creators, place } from '@/lib/hypear-data';
import { AccountDialog } from '@/components/account-dialog';
import { AccountMenu } from '@/components/account-menu';
import { ThemeToggle } from '@/components/theme-toggle';
import { useDemoSession } from '@/lib/demo-session';
import { AIBriefDialog } from '@/components/ai-brief-dialog';
import { EscrowTermsDialog } from '@/components/escrow-terms-dialog';
import { readTermsAgreement } from '@/lib/terms-agreement';

export function Header(){
  const home = useRouterState({ select: s => s.location.pathname === '/' });
  const [open, setOpen] = useState(false);
  const [accountOpen, setAccountOpen] = useState(false);
  const [briefOpen, setBriefOpen] = useState(false);
  const [termsOpen, setTermsOpen] = useState(false);
  const session = useDemoSession();

  useEffect(() => {
    const handler = () => {
      // Escrow & Confidentiality onboarding gate: first-time users must agree before posting a brief / secure deal.
      if (!readTermsAgreement()) { setTermsOpen(true); return; }
      setBriefOpen(true);
    };
    window.addEventListener('open-ai-brief', handler);
    return () => window.removeEventListener('open-ai-brief', handler);
  }, []);

  return (
    <>
      <header className={home ? "site-header reel-header" : "site-header"}>
        <Link to="/" className="wordmark">AiGrid</Link>
        <nav className={open ? 'site-nav is-open' : 'site-nav'} aria-label="Main navigation">
          {home ? (
            <>
              <Link to="/discover" onClick={() => setOpen(false)}>Discover</Link>
              <Link to="/pricing" onClick={() => setOpen(false)}>Pricing</Link>
              <Link to="/creators" onClick={() => setOpen(false)}>AI match</Link>
              <button 
                type="button" 
                onClick={() => { setOpen(false); if (!readTermsAgreement()) { setTermsOpen(true); } else { setBriefOpen(true); } }}
                style={{ background: 'none', border: 'none', cursor: 'pointer', font: 'inherit', color: 'inherit', padding: '0 4px', display: 'inline-flex', alignItems: 'center' }}
              >
                AI brief
              </button>
              <Link to="/how-it-works" onClick={() => setOpen(false)}>Contact</Link>
            </>
          ) : (
            <>
              <Link to="/how-it-works" onClick={() => setOpen(false)}>How it works</Link>
              <Link to="/creators" onClick={() => setOpen(false)}>Browse creators</Link>
              <button 
                type="button" 
                onClick={() => { setOpen(false); if (!readTermsAgreement()) { setTermsOpen(true); } else { setBriefOpen(true); } }}
                style={{ background: 'none', border: 'none', cursor: 'pointer', font: 'inherit', color: 'inherit', padding: '0 4px', display: 'inline-flex', alignItems: 'center' }}
              >
                AI brief
              </button>
              <Link to="/pricing" onClick={() => setOpen(false)}>Pricing</Link>
              <a href="/login">Become a creator</a>
            </>
          )}
        </nav>
        <div className="reel-header-actions">
          <ThemeToggle/>
          {session ? <AccountMenu session={session}/> : <Button variant={home ? 'default' : 'ghost'} onClick={() => setAccountOpen(true)}>{home ? 'Sign up / Sign in' : 'Log in'}</Button>}
        </div>
        <Button variant="ghost" size="icon" className="mobile-menu" aria-label={open ? 'Close menu' : 'Open menu'} onClick={() => setOpen(!open)}>
          {open ? <X/> : <Menu/>}
        </Button>
      </header>
      <AccountDialog open={accountOpen} onOpenChange={setAccountOpen}/>
      <EscrowTermsDialog
        open={termsOpen}
        onOpenChange={setTermsOpen}
        onAgreed={() => setBriefOpen(true)}
        userEmail={session?.email}
      />
      <AIBriefDialog open={briefOpen} onOpenChange={setBriefOpen}/>
    </>
  );
}
const footerGroups = [
  { title: 'Discover', links: [['Explore Creators', '/creators'], ['AI Match', '/creators'], ['Creative Feed', '/discover'], ['Categories', '/creators'], ['Featured Work', '/creators']] },
  { title: 'For Creators', links: [['Join as Creator', '/login'], ['Build Your Portfolio', '/how-it-works'], ['Find Campaigns', '/how-it-works'], ['Collaborations', '/creators'], ['Creator Guidelines', '/how-it-works']] },
  { title: 'For Brands', links: [['Find Creators', '/creators'], ['Create a Campaign', '/how-it-works'], ['How It Works', '/how-it-works'], ['Project Management', '/how-it-works'], ['Brand Guidelines', '/how-it-works']] },
  { title: 'Company', links: [['About AiGrid', '/how-it-works'], ['Contact', '/how-it-works'], ['Help Center', '/how-it-works'], ['Privacy Policy', '/privacy'], ['Terms of Service', '/terms']] },
] as const;
// Official AIgrid profile URLs have not been supplied; never imply ownership of unrelated accounts.
const footerSocials = [
  { name: 'Instagram', href: 'https://www.instagram.com/', Icon: Instagram },
  { name: 'LinkedIn', href: 'https://www.linkedin.com/', Icon: Linkedin },
  { name: 'YouTube', href: 'https://www.youtube.com/', Icon: Youtube },
];
export function Footer() {
  return <footer className="site-footer reel-footer" aria-label="AIgrid footer">
    <div className="footer-inner">
      <div className="footer-columns">
        <div className="footer-brand">
          <Link to="/" className="wordmark">AiGrid</Link>
          <p className="footer-tagline">Where AI Creators Meet Brands.</p>
          <p>Connecting creative talent with ambitious brands. Discover AI creators, explore their work, and bring your next idea to life.</p>
        </div>
        {footerGroups.map(group => <nav key={group.title} aria-label={`Footer ${group.title}`}>
          <h2>{group.title}</h2>
          {group.links.map(([label, path]) => <Link key={label} to={path}>{label}</Link>)}
        </nav>)}
      </div>
      <div className="footer-campaign">
        <p>Have a campaign in mind?<br/><span>Find the right AI creator.</span></p>
        <Button asChild className="footer-campaign-button"><Link to="/creators">Explore creators <ArrowUpRight aria-hidden="true"/></Link></Button>
      </div>
      <div className="footer-bottom">
        <p className="copyright">© 2026 AiGrid. All rights reserved.</p>
        <nav className="footer-legal" aria-label="Footer legal"><Link to="/privacy">Privacy Policy</Link><Link to="/terms">Terms of Service</Link></nav>
        <div className="footer-socials">{footerSocials.map(({name, href, Icon}) => <Button key={name} asChild variant="ghost" size="icon"><a href={href} target="_blank" rel="noreferrer" aria-label={`Open ${name}`} title={name}><Icon aria-hidden="true"/></a></Button>)}</div>
      </div>
    </div>
  </footer>;
}
export function Actions(){return <div className="action-row"><Button asChild className="pill"><Link to="/creators">Hire a creator</Link></Button><Button asChild variant="outline" className="pill"><Link to="/login">Become a creator</Link></Button></div>}
export function CreatorCard({creator}:{creator:typeof creators[number]}){return <Link to="/creators/$slug" params={{slug:creator.slug}} className="creator-card"><div className="creator-image"><img src={creator.image} alt={`${creator.name}'s creative portfolio`} loading="lazy"/><span className="availability"><i/> Available</span>{creator.reply&&<span className="reply">Replies in {creator.reply}</span>}</div><div className="creator-info"><div className="creator-name"><img src={creator.avatar} alt=""/><h3>{creator.name}</h3><ArrowUpRight/></div><div className="tags">{creator.specialties.map(s=><span key={s}>{s}</span>)}</div><p className="location">{place(creator)}</p><p className="creator-bio">{creator.bio}</p><div className="creator-bottom"><span>{creator.projects} projects</span><span>View profile →</span></div></div></Link>}
export function Steps({steps}:{steps:string[][]}){return <ol className={"steps steps-animated"}>{steps.map(([title,text],i)=><li key={title} style={{'--step-i':i} as React.CSSProperties}><span className={"step-number"}>{`0${i+1}`}</span><div><h3>{title}</h3><p>{text}</p></div></li>)}</ol>}
export function StartSection(){return <section className="start-section"><p className="eyebrow">Ready to start?</p><h2>The marketplace for<br/>AI-native creators</h2><Actions/></section>}
