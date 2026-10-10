import {useEffect,useState} from 'react';
import {homeStats,countAtProgress} from '@/lib/home-stats';
export function HomeStats(){
 const [progress,setProgress]=useState(0);
 useEffect(()=>{
  if(window.matchMedia('(prefers-reduced-motion: reduce)').matches){setProgress(1);return;}
  let frame=0;const start=performance.now();
  const tick=(now:number)=>{const next=Math.min(1,(now-start)/1800);setProgress(next);if(next<1)frame=requestAnimationFrame(tick);};
  frame=requestAnimationFrame(tick);return()=>cancelAnimationFrame(frame);
 },[]);
 return <dl className="reel-stats">{homeStats.map(({value,label})=><div key={label}><dd aria-label={value.toLocaleString('en-US')}><span aria-hidden="true">{countAtProgress(value,progress).toLocaleString('en-US')}</span></dd><dt>{label}</dt></div>)}</dl>;
}