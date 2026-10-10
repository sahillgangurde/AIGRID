import { createClient } from '@supabase/supabase-js';
import { setStoredToken } from './auth-headers';

const supabaseUrl =
  import.meta.env.VITE_SUPABASE_URL ||
  import.meta.env.NEXT_PUBLIC_SUPABASE_URL ||
  'https://your-project-id.supabase.co';

const supabaseAnonKey =
  import.meta.env.VITE_SUPABASE_ANON_KEY ||
  import.meta.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ||
  'placeholder-anon-key';

export const isSupabaseConfigured = Boolean(
  supabaseUrl &&
    !supabaseUrl.includes('your-project-id') &&
    supabaseAnonKey &&
    !supabaseAnonKey.includes('placeholder')
);

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: true,
  },
});

/**
 * Initiates real Google OAuth flow via Supabase.
 */
export async function signInWithGoogle(redirectTo?: string) {
  if (!isSupabaseConfigured) {
    console.warn('[Supabase] VITE_SUPABASE_URL or VITE_SUPABASE_ANON_KEY not configured yet.');
  }

  const origin = typeof window !== 'undefined' ? window.location.origin : 'http://localhost:3000';
  const target = redirectTo || `${origin}/login`;

  const { data, error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: {
      redirectTo: target,
      queryParams: {
        access_type: 'offline',
        prompt: 'consent',
      },
    },
  });

  if (error) {
    throw error;
  }
  return data;
}

/**
 * Synchronizes Supabase Google session user with the local persistent SQLite backend.
 */
export async function syncSupabaseUserWithBackend(user: {
  email?: string | null;
  user_metadata?: Record<string, unknown> | null;
  id?: string;
}): Promise<{ access_token?: string; user?: Record<string, unknown> } | null> {
  const email = user.email?.trim();
  if (!email) return null;

  const displayName = String(
    user.user_metadata?.full_name ||
      user.user_metadata?.name ||
      email.split('@')[0].replace(/[._\-]+/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
  );
  const avatarUrl = String(user.user_metadata?.avatar_url || user.user_metadata?.picture || '');

  try {
    const res = await fetch('/api/auth/google-sync', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email,
        display_name: displayName,
        avatar_url: avatarUrl || undefined,
        google_id: user.id,
        role: 'creator',
      }),
    });

    if (res.ok) {
      const data = await res.json();
      if (data.access_token) {
        setStoredToken(data.access_token);
      }
      return data;
    }
  } catch (err) {
    console.warn('[Supabase Sync] Backend SQLite sync failed, continuing:', err);
  }
  return null;
}

/**
 * Signs out from Supabase Auth.
 */
export async function signOutSupabase() {
  try {
    const { error } = await supabase.auth.signOut();
    if (error) {
      console.error('[Supabase] Sign-out error:', error.message);
    }
  } catch (err) {
    console.warn('[Supabase] Local sign-out ignored:', err);
  }
}

