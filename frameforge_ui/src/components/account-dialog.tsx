import { useEffect, useState } from 'react';
import { useNavigate } from '@tanstack/react-router';
import { ArrowRight, Check, Eye, EyeOff } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { setRole, signIn, signOut, useDemoSession, type DemoRole } from '@/lib/demo-session';

const roles: { id: DemoRole; title: string; text: string }[] = [
  { id: 'creator', title: "I'm a Creator", text: 'Showcase work, get discovered, win awards.' },
  { id: 'producer', title: "I'm a Producer / EP", text: 'Run productions and staff projects. No reel needed.' },
  { id: 'rep', title: "I'm a Rep / Agent", text: 'Represent creators and connect them with producers.' },
  { id: 'hirer', title: "I'm a Hirer", text: 'Post jobs, find AI talent for projects.' },
  { id: 'both', title: 'Both', text: 'Create work and hire other creators.' },
];

export function AccountDialog({ open, onOpenChange }: { open: boolean; onOpenChange: (open: boolean) => void }) {
  const session = useDemoSession();
  const navigate = useNavigate();
  const [mode, setMode] = useState<'login' | 'signup' | 'forgot' | 'onboard' | 'done'>('login');
  const [visible, setVisible] = useState(false);
  const [resetTo, setResetTo] = useState('');
  const [email, setEmail] = useState('');
  function switchMode(next: typeof mode) { setMode(next); setResetTo(''); setVisible(false); }
  function close() { onOpenChange(false); }
  useEffect(() => { if (!open) switchMode('login'); }, [open]);
  /** After a fresh sign-up, show the one-time path picker unless this browser already picked one. */
  function afterSignIn() {
    if (!readRole()) switchMode('onboard');
    else close();
  }
  function readRole() {
    try {
      const raw = window.localStorage.getItem('aigrid-demo-user');
      return raw ? (JSON.parse(raw) as { role?: string }).role : undefined;
    } catch { return undefined; }
  }
  const isCreatorPath = session?.role === 'creator' || session?.role === 'both';
  return <Dialog open={open} onOpenChange={next => { onOpenChange(next); if (!next) { switchMode('login'); setEmail(''); } }}>
    <DialogContent className="account-dialog">
      {mode === 'onboard' || mode === 'done' ? (
        <div className="account-dialog-body onboard-body">
          <div className="onboard-top">
            <span className="onboard-step">Step {mode === 'onboard' ? '1 of 2' : '2 of 2'}</span>
            <Button variant="link" onClick={close}>Skip for now (Esc)</Button>
          </div>
          <div className="onboard-progress" aria-hidden="true"><i style={{ width: mode === 'onboard' ? '50%' : '100%' }} /></div>
          {mode === 'onboard' ? <>
            <DialogTitle>Welcome — what brings you here?</DialogTitle>
            <DialogDescription>Pick the path that fits. You can change this later.</DialogDescription>
            <div className="onboard-roles">
              {roles.map(role => <button key={role.id} type="button" className="onboard-role" onClick={() => { setRole(role.id); switchMode('done'); }}>
                <strong>{role.title}</strong>
                <span>{role.text}</span>
              </button>)}
            </div>
          </> : <>
            <div className="onboard-done">
              <span className="onboard-check" aria-hidden="true"><Check /></span>
              <DialogTitle>You’re all set.</DialogTitle>
              <DialogDescription>{isCreatorPath ? 'Get verified to start getting discovered, votes, and awards.' : 'Find the right AI creator for your next project.'}</DialogDescription>
            </div>
            <div className="onboard-actions">
              <Button variant="outline" onClick={() => switchMode('onboard')}>← Back</Button>
              <Button className="account-submit" onClick={() => { const to = isCreatorPath ? '/pricing' : '/creators'; close(); navigate({ to }); }}>{isCreatorPath ? 'Get verified' : 'Hire Creator'} <ArrowRight aria-hidden="true" /></Button>
            </div>
          </>}
        </div>
      ) : (
        <div className="account-dialog-body">
          <DialogTitle>{mode === 'login' ? 'Sign in to AiGrid' : mode === 'signup' ? 'Create your account' : 'Forgot password?'}</DialogTitle>
          <DialogDescription>{mode === 'login' ? 'Welcome back! Please sign in to continue' : mode === 'signup' ? 'Join the filmmaking community' : 'Enter your email to reset your password'}</DialogDescription>
          {session && mode !== 'forgot' && <p className="account-notice" role="status">Signed in as {session.email}. <Button type="button" variant="link" onClick={() => signOut()}>Sign out</Button></p>}
          {mode !== 'forgot' && <><Button variant="outline" className="account-google" onClick={() => { signIn('guest@gmail.com', 'google'); afterSignIn(); }}><span className="google-letter" aria-hidden="true">G</span>Continue with Google</Button><div className="account-divider"><span>or</span></div></>}
          <form key={mode} onSubmit={event => {
            event.preventDefault();
            const value = email.trim();
            if (!value) return;
            if (mode === 'forgot') { setResetTo(value); return; }
            signIn(value);
            if (mode === 'signup') afterSignIn();
            else close();
          }}>
            <label htmlFor="account-email">Email address</label>
            <input id="account-email" name="email" type="text" inputMode="email" autoComplete="email" placeholder="Enter your email address" required value={email} onChange={event => setEmail(event.target.value)} />
            {mode !== 'forgot' && <><div className="account-password-label"><label htmlFor="account-password">Password</label>{mode === 'login' && <Button type="button" variant="link" onClick={() => switchMode('forgot')}>Forgot password?</Button>}</div><div className="account-password"><input id="account-password" name="password" type={visible ? 'text' : 'password'} autoComplete={mode === 'signup' ? 'new-password' : 'current-password'} placeholder={mode === 'signup' ? 'Create a password' : 'Enter your password'} required /><Button type="button" variant="ghost" size="icon" aria-label={visible ? 'Hide password' : 'Show password'} onClick={() => setVisible(!visible)}>{visible ? <EyeOff /> : <Eye />}</Button></div></>}
            <Button type="submit" className="account-submit">{mode === 'login' ? 'Sign in' : mode === 'signup' ? 'Sign up' : 'Reset password'}<ArrowRight aria-hidden="true" /></Button>
          </form>
          {resetTo && <p className="account-notice" role="status">If {resetTo} has an account, a reset link is on its way.</p>}
        </div>
      )}
      {mode !== 'onboard' && mode !== 'done' && <div className="account-dialog-bottom">{mode === 'forgot' ? <Button variant="link" onClick={() => switchMode('login')}>Back to sign in</Button> : <><span>{mode === 'login' ? 'Don’t have an account?' : 'Already have an account?'}</span><Button variant="link" onClick={() => switchMode(mode === 'login' ? 'signup' : 'login')}>{mode === 'login' ? 'Sign up' : 'Sign in'}</Button></>}</div>}
    </DialogContent>
  </Dialog>;
}
