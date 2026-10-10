import {createFileRoute,Link} from '@tanstack/react-router';
import {useState} from 'react';
import {Button} from '@/components/ui/button';
import {pageHead} from '@/lib/hypear-data';
import {signIn, signOut, useDemoSession} from '@/lib/demo-session';
import {setStoredToken} from '@/lib/auth-headers';
export const Route=createFileRoute('/login')({head:()=>pageHead('Log in','Sign in to connect with AI-native creative talent.'),component:Login});
function Login(){const session=useDemoSession();const [resetTo,setResetTo]=useState('');const [authError,setAuthError]=useState('');return <main className="login-page"><div className="login-form">{session?<>
  <h1>You’re in</h1>
  <p>Signed in as <strong>{session.email}</strong>. This demo keeps that in your own browser only.</p>
  <div className="action-row"><Button asChild className="pill"><Link to="/creators">Browse creators</Link></Button><Button variant="outline" className="pill" onClick={()=>signOut()}>Sign out</Button></div>
</>:<>
  <h1>Welcome back</h1>
  <p>Don't have an account? <a href="/login?mode=signup">Sign up as a creator</a></p>
  <Button variant="outline" className="google-button" onClick={()=>signIn('guest@gmail.com','google')}>Continue with Google</Button>
  <div className="form-divider">or continue with email</div>
  <form onSubmit={async e=>{
    e.preventDefault();
    const form=e.currentTarget;
    const username=String(new FormData(form).get('email')??'').trim();
    const password=String(new FormData(form).get('password')??'');
    if(!username)return;
    setAuthError('');
    // Try the real backend first: JWT signup/login, then fall back to the local demo session.
    try {
      let res = await fetch('/api/auth/login', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({username, password}) });
      if (!res.ok && res.status === 401) {
        // Not registered on the backend yet — attempt a real signup so the account persists server-side.
        res = await fetch('/api/auth/signup', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({username, password, display_name: (username.split('@')[0] ?? '').replace(/[._\-]+/g,' ')||'Creator', role:'brand'}) });
      }
      if (res.ok) {
        const data = await res.json();
        setStoredToken(data.access_token ?? '');
      }
    } catch {/* backend offline — demo session remains the fallback */}
    setResetTo('');
    signIn(username);
  }}>
    <label>Email<input type="text" inputMode="email" name="email" required autoComplete="email" placeholder="you@example.com"/></label>
    <label>Password<input type="password" name="password" required autoComplete="current-password" placeholder="Enter any password"/></label>
    <Button type="button" variant="link" className="forgot-link" onClick={e=>{const form=(e.currentTarget as HTMLButtonElement).form;setResetTo(form?String(new FormData(form).get('email')??'').trim():'');}}>Forgot password?</Button>
    <Button type="submit" className="pill">Sign in</Button>
  </form>
  {resetTo&&<p className="form-notice" role="status">If {resetTo} has an account, a reset link is on its way.</p>}
  <p className="form-legal">By continuing you agree to our <Link to="/terms">Terms of Use</Link> and <Link to="/privacy">Privacy Policy</Link>.</p>
</>}</div></main>}
