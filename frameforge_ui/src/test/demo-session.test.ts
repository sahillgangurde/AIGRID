import { beforeEach, describe, expect, it } from 'vitest';
import { readDemoSession, setRole, signIn, signOut } from '@/lib/demo-session';

const KEY = 'aigrid-demo-user';

beforeEach(() => {
  localStorage.clear();
  signOut();
});

describe('demo sign-in', () => {
  it('accepts any input and keeps only the email', () => {
    const session = signIn('  sujaltandel@gmail.com  ');
    expect(session.email).toBe('sujaltandel@gmail.com');
    expect(session.name).toBe('Sujaltandel');
    expect(readDemoSession()?.email).toBe('sujaltandel@gmail.com');
    expect(localStorage.getItem(KEY)).not.toContain('password');
  });

  it('builds a readable name from an email with separators and digits', () => {
    expect(signIn('sujal.tandel2024@gmail.com').name).toBe('Sujal Tandel');
  });

  it('lets a visitor sign in again and again, replacing the previous session', () => {
    signIn('first@gmail.com');
    signIn('second@gmail.com');
    expect(readDemoSession()?.email).toBe('second@gmail.com');
    signOut();
    expect(readDemoSession()).toBeNull();
    expect(localStorage.getItem(KEY)).toBeNull();
  });

  it('remembers the chosen path once, so onboarding never repeats', () => {
    signIn('sujal@gmail.com');
    expect(readDemoSession()?.role).toBeUndefined();
    setRole('creator');
    expect(readDemoSession()?.role).toBe('creator');
    expect(localStorage.getItem(KEY)).toContain('"role":"creator"');
    setRole('hirer');
    expect(readDemoSession()?.role).toBe('hirer');
  });
});
