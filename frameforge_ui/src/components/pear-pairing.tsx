import { useEffect, useRef } from 'react';
import cut from '@/assets/pear-cut-clean.png.asset.json';
import whole from '@/assets/pear-whole-clean.png.asset.json';
import { pearPose, pearProgress } from '@/lib/pear-motion';

export function PearPairing() {
  const scene = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = scene.current;
    if (!el) return;
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
    let frame = 0;
    const update = () => {
      frame = 0;
      const progress = reduced.matches ? 1 : pearProgress(el.getBoundingClientRect().top, window.innerHeight);
      const pose = pearPose(progress);
      el.style.setProperty('--pear-gap', `${pose.separation}%`);
      el.style.setProperty('--pear-left-angle', `${pose.leftAngle}deg`);
      el.style.setProperty('--pear-right-angle', `${pose.rightAngle}deg`);
      el.style.setProperty('--pear-right-turn', `${pose.rightTurn}deg`);
      el.style.setProperty('--pear-turn', `${pose.turn}deg`);
      el.style.setProperty('--pear-left-opacity', `${pose.leftOpacity}`);
      el.dataset['progress'] = progress.toFixed(3);
    };
    const schedule = () => { if (!frame) frame = requestAnimationFrame(update); };
    update();
    window.addEventListener('scroll', schedule, { passive: true });
    window.addEventListener('resize', schedule);
    reduced.addEventListener('change', schedule);
    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener('scroll', schedule);
      window.removeEventListener('resize', schedule);
      reduced.removeEventListener('change', schedule);
    };
  }, []);
  return <div ref={scene} className="pear-pairing" role="img" aria-label="Two pear halves rotate together and join into one whole pear as you scroll">
    <div className="pear-piece pear-left"><div className="pear-turn"><img className="pear-face pear-cut-face" src={cut.url} alt=""/><img className="pear-face pear-skin-face" src={whole.url} alt=""/></div></div>
    <div className="pear-piece pear-right"><img src={whole.url} alt=""/></div>
  </div>;
}