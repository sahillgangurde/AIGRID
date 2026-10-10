import { useEffect } from 'react';

/**
 * Scroll-reveal: elements with the 'reveal' class fade in as they enter the viewport.
 * Runs once after mount; safe for SPA route changes (re-runs per call).
 * Honors prefers-reduced-motion via CSS (see styles.css).
 */
export function useScrollReveal(deps: unknown[] = []) {
  useEffect(() => {
    const elements = Array.from(document.querySelectorAll<HTMLElement>('.reveal:not(.is-visible)'));
    if (!elements.length) return;

    if (typeof IntersectionObserver === 'undefined') {
      // Very old browsers: show everything immediately.
      elements.forEach(el => el.classList.add('is-visible'));
      return;
    }

    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.08, rootMargin: '0px 0px -40px 0px' });

    elements.forEach(el => observer.observe(el));
    return () => observer.disconnect();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
}
