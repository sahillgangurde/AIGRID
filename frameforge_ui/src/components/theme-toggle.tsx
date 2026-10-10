import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import { Moon, Sun } from 'lucide-react';
import { Button } from '@/components/ui/button';

type Theme = 'light' | 'dark';
const storageKey = 'aigrid-theme';
const ThemeContext = createContext<{ theme: Theme; toggle: () => void }>({ theme: 'light', toggle: () => {} });

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>('light');
  useEffect(() => {
    try {
      setTheme(localStorage.getItem(storageKey) === 'dark' ? 'dark' : 'light');
    } catch { /* Storage may be unavailable in private browsing. */ }
  }, []);
  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark');
    document.documentElement.dataset['theme'] = theme;
  }, [theme]);
  function toggle() {
    const next = theme === 'light' ? 'dark' : 'light';
    setTheme(next);
    try { localStorage.setItem(storageKey, next); } catch { /* Keep the switch usable without storage. */ }
  }
  return <ThemeContext.Provider value={{ theme, toggle }}>{children}</ThemeContext.Provider>;
}

export function ThemeToggle() {
  const { theme, toggle } = useContext(ThemeContext);
  return <Button variant="ghost" className="theme-toggle" role="switch" aria-checked={theme === 'dark'} aria-label="Dark theme" title={theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'} onClick={toggle}>
    <Sun className="theme-sun" aria-hidden="true" />
    <Moon className="theme-moon" aria-hidden="true" />
    <span className="theme-thumb" aria-hidden="true" />
  </Button>;
}