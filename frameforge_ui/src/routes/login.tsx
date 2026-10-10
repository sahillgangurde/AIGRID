import { createFileRoute, Link } from '@tanstack/react-router';
import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { pageHead } from '@/lib/hypear-data';
import { signIn, signOut, useDemoSession } from '@/lib/demo-session';
import { setStoredToken } from '@/lib/auth-headers';
import { supabase, isSupabaseConfigured, signInWithGoogle, signOutSupabase, syncSupabaseUserWithBackend } from '@/lib/supabase';

export const Route = createFileRoute('/login')({
  head: () => pageHead('Log in', 'Sign in to connect with AI-native creative talent.'),
  component: Login,
});

function Login() {
  const session = useDemoSession();
  const [resetTo, setResetTo] = useState('');
  const [authError, setAuthError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Sync Supabase Google session if redirected back from OAuth
  useEffect(() => {
    let isMounted = true;

    async function handleUserSync(user: { email?: string; user_metadata?: Record<string, unknown>; id?: string }) {
      if (!user.email) return;
      await syncSupabaseUserWithBackend(user);
      if (isMounted) {
        signIn(user.email, 'google');
      }
      if (typeof window !== 'undefined' && window.location.hash.includes('access_token')) {
        window.history.replaceState(null, '', window.location.pathname + window.location.search);
      }
    }

    if (isSupabaseConfigured) {
      supabase.auth.getSession().then(({ data: { session: currentSession } }) => {
        if (currentSession?.user) {
          handleUserSync(currentSession.user);
        }
      });

      const {
        data: { subscription },
      } = supabase.auth.onAuthStateChange(async (event, currentSession) => {
        if ((event === 'SIGNED_IN' || event === 'USER_UPDATED') && currentSession?.user) {
          handleUserSync(currentSession.user);
        }
      });

      return () => {
        isMounted = false;
        subscription.unsubscribe();
      };
    }
  }, []);

  const handleGoogleSignIn = async () => {
    setIsSubmitting(true);
    setAuthError('');
    try {
      if (isSupabaseConfigured) {
        await signInWithGoogle();
      } else {
        // Instant interactive fallback for local dev when cloud Supabase keys aren't configured yet
        const inputEmail = window.prompt(
          'Enter your Google email to test instant backend sync (Supabase cloud keys are optional in local dev):',
          'creator@gmail.com'
        );
        if (!inputEmail) {
          setIsSubmitting(false);
          return;
        }

        const email = inputEmail.trim();
        const displayName = email.split('@')[0].replace(/[._\-]+/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

        try {
          const res = await fetch('/api/auth/google-sync', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              email,
              display_name: displayName,
              role: 'creator',
            }),
          });
          if (res.ok) {
            const data = await res.json();
            if (data.access_token) {
              setStoredToken(data.access_token);
            }
          }
        } catch (err) {
          console.warn('Backend offline, continuing in client session:', err);
        }

        signIn(email, 'google');
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Google sign-in failed.';
      setAuthError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSignOut = async () => {
    await signOutSupabase();
    setStoredToken('');
    signOut();
  };

  return (
    <main className="login-page">
      <div className="login-form">
        {session ? (
          <>
            <h1>You’re in</h1>
            <p>
              Signed in as <strong>{session.email}</strong> via {session.provider === 'google' ? 'Google' : 'Email'}.
            </p>
            <div className="action-row">
              <Button asChild className="pill">
                <Link to="/creators">Browse creators</Link>
              </Button>
              <Button variant="outline" className="pill" onClick={handleSignOut}>
                Sign out
              </Button>
            </div>
          </>
        ) : (
          <>
            <h1>Welcome back</h1>
            <p>
              Don't have an account? <a href="/login?mode=signup">Sign up as a creator</a>
            </p>

            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                padding: '6px 12px',
                borderRadius: '999px',
                fontSize: '11px',
                fontWeight: 500,
                backgroundColor: isSupabaseConfigured ? 'rgba(16, 185, 129, 0.1)' : 'rgba(245, 158, 11, 0.1)',
                color: isSupabaseConfigured ? '#10b981' : '#f59e0b',
                border: `1px solid ${isSupabaseConfigured ? 'rgba(16, 185, 129, 0.2)' : 'rgba(245, 158, 11, 0.2)'}`,
                margin: '16px auto 0',
                width: 'fit-content',
              }}
            >
              <span
                style={{
                  width: '6px',
                  height: '6px',
                  borderRadius: '50%',
                  backgroundColor: isSupabaseConfigured ? '#10b981' : '#f59e0b',
                  display: 'inline-block',
                }}
              />
              {isSupabaseConfigured
                ? 'Supabase Google OAuth Active'
                : 'Local SQLite Persistent Ready (Paste Supabase keys in .env for Cloud OAuth)'}
            </div>

            <Button
              variant="outline"
              className="google-button"
              disabled={isSubmitting}
              onClick={handleGoogleSignIn}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" style={{ marginRight: '8px' }}>
                <path
                  fill="#4285F4"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                />
                <path
                  fill="#34A853"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
                />
                <path
                  fill="#EA4335"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
                />
              </svg>
              Continue with Google
            </Button>

            <div className="form-divider">or continue with email</div>

            <form
              onSubmit={async (e) => {
                e.preventDefault();
                const form = e.currentTarget;
                const username = String(new FormData(form).get('email') ?? '').trim();
                const password = String(new FormData(form).get('password') ?? '');
                if (!username) return;
                setAuthError('');
                try {
                  let res = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password }),
                  });
                  if (!res.ok && res.status === 401) {
                    res = await fetch('/api/auth/signup', {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({
                        username,
                        password,
                        display_name: (username.split('@')[0] ?? '').replace(/[._\-]+/g, ' ') || 'Creator',
                        role: 'brand',
                      }),
                    });
                  }
                  if (res.ok) {
                    const data = await res.json();
                    setStoredToken(data.access_token ?? '');
                  }
                } catch {
                  /* backend offline — demo session remains the fallback */
                }
                setResetTo('');
                signIn(username);
              }}
            >
              <label>
                Email
                <input
                  type="text"
                  inputMode="email"
                  name="email"
                  required
                  autoComplete="email"
                  placeholder="you@example.com"
                />
              </label>
              <label>
                Password
                <input
                  type="password"
                  name="password"
                  required
                  autoComplete="current-password"
                  placeholder="Enter any password"
                />
              </label>
              <Button
                type="button"
                variant="link"
                className="forgot-link"
                onClick={(e) => {
                  const form = (e.currentTarget as HTMLButtonElement).form;
                  setResetTo(form ? String(new FormData(form).get('email') ?? '').trim() : '');
                }}
              >
                Forgot password?
              </Button>
              <Button type="submit" className="pill">
                Sign in
              </Button>
            </form>

            {authError && (
              <p className="form-notice" style={{ color: '#ef4444' }} role="alert">
                {authError}
              </p>
            )}
            {resetTo && (
              <p className="form-notice" role="status">
                If {resetTo} has an account, a reset link is on its way.
              </p>
            )}
            <p className="form-legal">
              By continuing you agree to our <Link to="/terms">Terms of Use</Link> and{' '}
              <Link to="/privacy">Privacy Policy</Link>.
            </p>
          </>
        )}
      </div>
    </main>
  );
}
