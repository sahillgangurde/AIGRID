import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { ThemeProvider, ThemeToggle } from '@/components/theme-toggle';

beforeEach(() => { localStorage.clear(); document.documentElement.classList.remove('dark'); });
afterEach(cleanup);
describe('Website theme selection', () => {
  it('switches the whole website between light and dark', () => {
    render(<ThemeProvider><ThemeToggle /></ThemeProvider>);
    const toggle = screen.getByRole('switch', { name: 'Dark theme' });
    expect(document.documentElement.dataset['theme']).toBe('light');
    fireEvent.click(toggle);
    expect(document.documentElement.classList.contains('dark')).toBe(true);
    expect(toggle).toHaveAttribute('aria-checked', 'true');
    fireEvent.click(toggle);
    expect(document.documentElement.classList.contains('dark')).toBe(false);
    expect(toggle).toHaveAttribute('aria-checked', 'false');
  });
  it('remembers the chosen dark theme on the next visit', async () => {
    const first = render(<ThemeProvider><ThemeToggle /></ThemeProvider>);
    fireEvent.click(screen.getByRole('switch'));
    expect(localStorage.getItem('aigrid-theme')).toBe('dark');
    first.unmount();
    render(<ThemeProvider><ThemeToggle /></ThemeProvider>);
    await waitFor(() => expect(screen.getByRole('switch')).toHaveAttribute('aria-checked', 'true'));
    expect(document.documentElement.dataset['theme']).toBe('dark');
  });
});