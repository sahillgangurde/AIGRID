import {useEffect,useRef} from 'react';
import {ChevronLeft,ChevronRight} from 'lucide-react';
import {Button} from '@/components/ui/button';
import creator0 from '@/assets/creator-0.jpg.asset.json';
import creator2 from '@/assets/creator-2.jpg.asset.json';
import creator4 from '@/assets/creator-4.jpg.asset.json';
import {FILM_STEP,loopPosition,swipeVelocity} from '@/lib/film-wheel-motion';
// Films showcased on the platform wheel — all by creators listed on AiGrid.
const films=[
 {title:'Editorial Campaign — Monsoon Streets',author:'Creator #1042',image:creator0.url},
 {title:'Brand Lookbook — Studio Portraits',author:'Creator #1087',image:creator2.url},
 {title:'AI Short — Neon Bakery Reel',author:'Creator #1126',image:creator4.url},
];
export function FilmWheel({onFilmChange}:{onFilmChange:(author:string)=>void}){
 const viewport=useRef<HTMLDivElement>(null);
 const motion=useRef({velocity:0,dragging:false,lastY:0,lastTime:0,moved:0,pauseUntil:0});
 useEffect(()=>{
  const el=viewport.current;if(!el)return;
  const cycle=FILM_STEP*films.length;
  el.scrollTop=cycle*2;
  const reduced=window.matchMedia('(prefers-reduced-motion: reduce)');
   const cards=Array.from(el.querySelectorAll<HTMLElement>('.scrolling-film'));
   let frame=0,last=performance.now(),author='',autoRemainder=0;
  const tick=(now:number)=>{
   const dt=Math.min(now-last,32);last=now;const m=motion.current;
   if(!m.dragging){
    el.scrollTop+=m.velocity*dt;
    m.velocity*=Math.pow(.96,dt/16);
    if(!reduced.matches&&now>m.pauseUntil&&Math.abs(m.velocity)<.05){autoRemainder+=dt*.018;const pixels=Math.floor(autoRemainder);el.scrollTop+=pixels;autoRemainder-=pixels;}
   }
   el.scrollTop=loopPosition(el.scrollTop,cycle);
    const center=el.clientHeight/2;
    const curveWidth=Math.min(100,el.clientWidth*.16);
    for(const card of cards){
     const slide=card.parentElement;if(!slide)continue;
     const relativeY=slide.offsetTop+card.offsetHeight/2-el.scrollTop-center;
     const progress=Math.max(-1.4,Math.min(1.4,relativeY/Math.max(center,1)));
     const x=curveWidth*progress*progress;
     card.style.transform=`translateX(${x}px) rotate(${progress*18}deg)`;
    }
   const index=((Math.round(el.scrollTop/FILM_STEP)%films.length)+films.length)%films.length;
   const current=films[index];if(current&&current.author!==author){author=current.author;onFilmChange(author);}
   frame=requestAnimationFrame(tick);
  };
  const wheel=(e:WheelEvent)=>{e.preventDefault();const delta=e.deltaY*(e.deltaMode===1?16:e.deltaMode===2?el.clientHeight:1);motion.current.pauseUntil=performance.now()+1200;motion.current.velocity=swipeVelocity(delta,80);el.scrollTop+=delta;};
  el.addEventListener('wheel',wheel,{passive:false});frame=requestAnimationFrame(tick);
  return()=>{cancelAnimationFrame(frame);el.removeEventListener('wheel',wheel);};
 },[onFilmChange]);
 const step=(direction:number)=>{const el=viewport.current;if(!el)return;motion.current.pauseUntil=performance.now()+1200;motion.current.velocity=direction*.8;};
 return <div className="reel-wheel moving-wheel"><div className="wheel-line"/>
  <div ref={viewport} className="film-scroll" aria-label="Scrolling film wheel" tabIndex={0}
   onKeyDown={e=>{if(e.key==='ArrowDown'||e.key==='ArrowUp'){e.preventDefault();step(e.key==='ArrowDown'?1:-1);}}}
   onPointerDown={e=>{if(e.button!==0)return;const m=motion.current;m.dragging=true;m.velocity=0;m.lastY=e.clientY;m.lastTime=performance.now();m.moved=0;e.currentTarget.setPointerCapture(e.pointerId);}}
   onPointerMove={e=>{const m=motion.current;if(!m.dragging)return;const now=performance.now();const delta=m.lastY-e.clientY;e.currentTarget.scrollTop+=delta;m.velocity=swipeVelocity(delta,now-m.lastTime);m.moved+=Math.abs(delta);m.lastY=e.clientY;m.lastTime=now;}}
   onPointerUp={e=>{const m=motion.current;m.dragging=false;m.pauseUntil=performance.now()+1000;if(e.currentTarget.hasPointerCapture(e.pointerId))e.currentTarget.releasePointerCapture(e.pointerId);}}
   onPointerCancel={()=>{motion.current.dragging=false;motion.current.velocity=0;}}
   onClickCapture={e=>{if(motion.current.moved>6){e.preventDefault();e.stopPropagation();}}}>
   <div className="film-track">{Array.from({length:5},(_,copy)=>films.map((film,index)=><div className="film-slide" key={`${copy}-${index}`}><a className={`reel-film scrolling-film film-kind-${index}`} href="/creators" draggable={false}>{film.image&&<img src={film.image} alt={film.title} draggable={false}/>}<div className="reel-film-body"><div className="film-meta"><span>0{index+1} / 03</span><span className="film-badge">Featured</span><span>{film.image?'Portfolio':'Vote planned'}</span></div><h3>{film.title}</h3><div className="film-author"><span>{film.author.charAt(0).toUpperCase()}</span>{film.author}</div></div></a></div>))}</div>
  </div><div className="wheel-controls"><Button variant="outline" size="icon" aria-label="Previous film" onClick={()=>step(-1)}><ChevronLeft/></Button><Button size="icon" aria-label="Next film" onClick={()=>step(1)}><ChevronRight/></Button></div>
 </div>;
}