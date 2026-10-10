import { useEffect, useRef, useState } from 'react';

/**
 * Kinetic word cycle — replaces the pear in the pairing section.
 * Big display words (BRIEF → MATCH → ESCROW → DELIVER) rotate with a
 * slide-and-fade morph, editorial monospace kicker + a caption under the
 * active word. Pure CSS/JS, no external assets; respects reduced motion.
 */
const WORDS: { word: string; caption: string }[] = [
  { word: 'BRIEF', caption: 'The brand describes the work.' },
  { word: 'MATCH', caption: 'Verified creators are paired, explainably.' },
  { word: 'ESCROW', caption: 'Advance funds lock before work starts.' },
  { word: 'DELIVER', caption: 'C2PA-signed delivery, payout on approval.' },
];

const INTERVAL_MS = 2200;

export function KineticCycle() {
  const [index, setIndex] = useState(0);
  const [visible, setVisible] = useState(false);
  const host = useRef<HTMLDivElement>(null);

  // Reveal when scrolled into view; drive the rotation only while visible.
  useEffect(() => {
    const el = host.current;
    if (!el) return;
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduced) {
      setVisible(true);
      return; // static first word — no timer
    }
    const obs = new IntersectionObserver(
      entries => {
        entries.forEach(e => setVisible(e.isIntersecting));
      },
      { threshold: 0.4 }
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, []);

  useEffect(() => {
    if (!visible) return;
    const id = setInterval(() => setIndex(i => (i + 1) % WORDS.length), INTERVAL_MS);
    return () => clearInterval(id);
  }, [visible]);

  const current = WORDS[index] ?? WORDS[0] ?? { word: 'BRIEF', caption: 'The brand describes the work.' };

  return (
    <div
      ref={host}
      className="kinetic-cycle"
      role="img"
      aria-label={`The AiGrid flow: ${WORDS.map(w => w.word).join(', ')}`}
    >
      <div className="kinetic-rail" aria-hidden="true">
        {WORDS.map((w, i) => (
          <span key={w.word} className={i === index ? 'dot is-active' : 'dot'} />
        ))}
      </div>
      <div className="kinetic-stage" key={current.word}>
        <span className="kinetic-kicker">{`0${index + 1} — THE FLOW`}</span>
        <span className="kinetic-word">{current.word}</span>
        <span className="kinetic-caption">{current.caption}</span>
      </div>
    </div>
  );
}
