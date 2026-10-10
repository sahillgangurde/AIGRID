import {createFileRoute,Link} from '@tanstack/react-router';
import {useEffect,useRef,useState} from 'react';
import {Search,ArrowUpDown,Bookmark,List,LayoutGrid,MapPin,Star,X,ChevronDown,MessageCircle,Clapperboard,Briefcase,Sparkles} from 'lucide-react';
import {creators,pageHead,place,Creator} from '@/lib/hypear-data';
import {CreatorCard} from '@/components/hypear';import {AIBriefDialog} from '@/components/ai-brief-dialog';
import {EscrowTermsDialog} from '@/components/escrow-terms-dialog';
import {readTermsAgreement} from '@/lib/terms-agreement';
import { useScrollReveal } from '@/lib/use-scroll-reveal';





type DirectorySearch={q?:string;focus?:string};
function readDirectorySearch(search:Record<string,unknown>):DirectorySearch{const out:DirectorySearch={};if(typeof search['q']==='string')out.q=search['q'];if(typeof search['focus']==='string')out.focus=search['focus'];return out}
export const Route=createFileRoute('/creators/')({head:()=>pageHead('AI Filmmaker Directory','Search AI filmmakers by tool, country, availability and award history.'),validateSearch:readDirectorySearch,component:Directory});

const TOOL_LIMIT=8;
function Directory(){
 const {q,focus}=Route.useSearch();
 const [query,setQuery]=useState(q??'');
 const inputRef=useRef<HTMLInputElement>(null);
 useEffect(()=>{if(focus==='search')inputRef.current?.focus()},[focus]);
 const [allCreators,setAllCreators]=useState<Creator[]>(creators);
 const [briefOpen,setBriefOpen]=useState(false);
 const [termsOpen,setTermsOpen]=useState(false);
 const [tools,setTools]=useState<string[]>([]);
 const [country,setCountry]=useState('');
 const [available,setAvailable]=useState(false);
 const [awards,setAwards]=useState(false);
 const [producers,setProducers]=useState(false);
 const [sort,setSort]=useState('rated');
 const [view,setView]=useState<'list'|'grid'>('list');
 const [saved,setSaved]=useState<string[]>([]);
 const [showSaved,setShowSaved]=useState(false);
 const [toolQuery,setToolQuery]=useState('');
 const [showAllTools,setShowAllTools]=useState(false);
 const [openTools,setOpenTools]=useState(true);
 const [openCountry,setOpenCountry]=useState(true);
 const [openAvail,setOpenAvail]=useState(true);
 useScrollReveal([]);

 useEffect(()=>{
  fetch('/api/creators')
   .then(r=>r.json())
   .then(data=>{
    if(data?.creators&&Array.isArray(data.creators)){
     const dbList:Creator[]=data.creators.map((c:any)=>({
      slug:c.handle?c.handle.replace('@',''):c.id,
      name:c.name,
      title:c.specialty||'AI Filmmaker • Creative Director',
      location:'Global',
      country:'Worldwide',
      image:c.sample_works?.[0]?.image_url||c.avatar,
      avatar:c.avatar,
      reply:'2h',
      projects:c.completed_projects||5,
      specialties:[c.specialty,...(c.skills||[])].slice(0,3).filter(Boolean),
      industries:['Brand campaign visuals','AI Cinema'],
      bio:c.bio,
      tools:c.tools&&c.tools.length?c.tools:['Runway','ComfyUI'],
      rate:c.hourly_compute_rate||50,
      rating:c.rating||4.9,
      saved:12,
      awards:c.c2pa_certified||false,
      available:true,
      producer:false
     }));
     setAllCreators(prev=>{
      const slugs=new Set(prev.map(p=>p.slug));
      const additions=dbList.filter(d=>!slugs.has(d.slug));
      return [...prev,...additions];
     });
    }
   }).catch(()=>{});
 },[]);

 const counts=new Map<string,number>();
 allCreators.forEach(c=>c.tools.forEach(t=>counts.set(t,(counts.get(t)??0)+1)));
 const ranked=[...counts.entries()].sort((a,b)=>b[1]-a[1]||a[0].localeCompare(b[0]));
 const shown=(showAllTools?ranked:ranked.slice(0,TOOL_LIMIT)).filter(([t])=>t.toLowerCase().includes(toolQuery.toLowerCase()));
 const hidden=(showAllTools?0:ranked.length-TOOL_LIMIT);

 const toggleTool=(t:string)=>setTools(p=>p.includes(t)?p.filter(x=>x!==t):[...p,t]);
 const toggleSaved=(s:string)=>setSaved(p=>p.includes(s)?p.filter(x=>x!==s):[...p,s]);

 const rows=allCreators.filter(c=>(`${c.name} ${c.title} ${c.bio}`.toLowerCase().includes(query.toLowerCase()))
  &&(!tools.length||tools.every(t=>c.tools.includes(t)))
  &&(!country||c.country===country)
  &&(!available||c.available)
  &&(!awards||c.awards)
  &&(!producers||c.producer)
  &&(!showSaved||saved.includes(c.slug)))
  .sort((a,b)=>sort==='rated'?b.rating-a.rating||b.saved-a.saved:sort==='saved'?b.saved-a.saved:sort==='name'?a.name.localeCompare(b.name):(a.rate??1e9)-(b.rate??1e9));

 const tags=[...tools.map(t=>({label:t,clear:()=>toggleTool(t)})),...(country?[{label:country,clear:()=>setCountry('')}]:[]),...(available?[{label:'Available now',clear:()=>setAvailable(false)}]:[]),...(awards?[{label:'Award winners',clear:()=>setAwards(false)}]:[]),...(producers?[{label:'Producers & agents',clear:()=>setProducers(false)}]:[]),...(showSaved?[{label:'Saved only',clear:()=>setShowSaved(false)}]:[])];

 return <main className="directory page-container">
  <div className="directory-head">
   <div>
    <p className="eyebrow">Directory • The filmmakers</p>
    <h1>AI Filmmaker Directory</h1>
    <p className="page-intro"><strong>{allCreators.length > 9 ? allCreators.length : '1,053'}</strong> filmmakers building with Runway, Sora, Veo, ComfyUI and Midjourney.</p>
   </div>
   <button type="button" onClick={()=>{ if (!readTermsAgreement()) { setTermsOpen(true); } else { setBriefOpen(true); } }} className="brief-cta" style={{background:'none',border:'none',cursor:'pointer',font:'inherit',color:'inherit',display:'inline-flex',alignItems:'center',gap:6}}>
    <Sparkles size={16}/> Not sure who? Send a brief →
   </button>
  </div>
  <div className="directory-layout">
   <aside className="directory-filters">
    <section className={'filter-group'+(openTools?'':' closed')}>
     <button onClick={()=>setOpenTools(!openTools)} aria-expanded={openTools}>Tools<ChevronDown/></button>
     {openTools&&<><div className="search-field tool-search"><Search size={15}/><input value={toolQuery} onChange={e=>setToolQuery(e.target.value)} placeholder="Search..."/></div>
      <div className="tool-list">{shown.map(([t,n])=><label className="tool-option" key={t}><input type="checkbox" checked={tools.includes(t)} onChange={()=>toggleTool(t)}/>{t}<span>{n}</span></label>)}
      {!shown.length&&<p className="tool-empty">No tools match “{toolQuery}”.</p>}
      {hidden>0&&<button className="tool-more-link" onClick={()=>setShowAllTools(true)}>Show {hidden} more</button>}
      {showAllTools&&ranked.length>TOOL_LIMIT&&<button className="tool-more-link" onClick={()=>setShowAllTools(false)}>Show less</button>}</div></>}
    </section>
    <section className={'filter-group'+(openCountry?'':' closed')}>
     <button onClick={()=>setOpenCountry(!openCountry)} aria-expanded={openCountry}>Country<ChevronDown/></button>
     {openCountry&&<select className="filter-select" value={country} onChange={e=>setCountry(e.target.value)}><option value="">All countries</option>{[...new Set(creators.map(c=>c.country))].sort().map(o=><option key={o}>{o}</option>)}</select>}
    </section>
    <section className={'filter-group'+(openAvail?'':' closed')}>
     <button onClick={()=>setOpenAvail(!openAvail)} aria-expanded={openAvail}>Availability<ChevronDown/></button>
     {openAvail&&<label className="tool-option"><input type="checkbox" checked={available} onChange={()=>setAvailable(!available)}/>Available now<span>{creators.filter(c=>c.available).length}</span></label>}
    </section>
   </aside>
   <div className="directory-results">
    <div className="results-controls">
     <div className="search-field"><Search size={17}/><input ref={inputRef} value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search by name or headline..."/></div>
     <div className="sort-field"><ArrowUpDown/><select value={sort} onChange={e=>setSort(e.target.value)} aria-label="Sort filmmakers"><option value="rated">Highest rated</option><option value="saved">Most saved</option><option value="name">Name A–Z</option><option value="rate">Rate: low to high</option></select><ChevronDown/></div>
     <div className="view-switch"><button aria-pressed={view==='list'} aria-label="List view" onClick={()=>setView('list')}><List/></button><button aria-pressed={view==='grid'} aria-label="Grid view" onClick={()=>setView('grid')}><LayoutGrid/></button></div>
     <button className="saved-toggle" aria-pressed={showSaved} onClick={()=>setShowSaved(!showSaved)}><Bookmark/>Saved{saved.length?` (${saved.length})`:''}</button>
    </div>
    <div className="chip-row">
     <button className="chip" aria-pressed={!producers&&!awards} onClick={()=>{setProducers(false);setAwards(false)}}><Clapperboard/>Filmmakers</button>
     <button className="chip" aria-pressed={producers} onClick={()=>setProducers(!producers)}><Briefcase/>+ Producers & agents</button>
     <button className="chip" aria-pressed={available} onClick={()=>setAvailable(!available)}><i/>Available now</button>
     <button className="chip" aria-pressed={awards} onClick={()=>setAwards(!awards)}>Award winners</button>
    </div>
    <div className="active-filters">{tags.length?<>Filters:{tags.map(t=><button className="filter-tag" key={t.label} onClick={t.clear}>{t.label}<X/></button>)}</>:<span>Filters: none</span>}<span className="result-count">{rows.length}{tags.length?` of ${creators.length}`:''} filmmakers</span></div>
    {view==='list'?<div className="filmmaker-table"><div className="filmmaker-head"><span>Name</span><span>Tools</span><span>Location • Rate</span><span>Status</span></div>
     {rows.map(c=><div className="filmmaker-row" key={c.slug}>
      <div className="fm-name"><img src={c.avatar} alt=""/><div><Link to="/creators/$slug" params={{slug:c.slug}}>{c.name}</Link><span>{c.title}</span></div></div>
      <div className="fm-tools">{c.tools.slice(0,3).map(t=><button className="tool-pill" key={t} onClick={()=>toggleTool(t)}>{t}</button>)}{c.tools.length>3&&<span className="tool-more">+{c.tools.length-3}</span>}</div>
      <div className="fm-loc"><span><MapPin/>{place(c)}</span>{c.rate?<span>${c.rate}/hr</span>:<span>—</span>}</div>
      <div className="fm-status"><span><Bookmark/>{c.saved}</span><span><Star/>{c.rating.toFixed(1)}</span><span className={c.available?'is-available':'is-busy'}>{c.available?<><i/>Available</>:<>Booked</>}</span><button className="fm-save" aria-pressed={saved.includes(c.slug)} aria-label={`Save ${c.name}`} onClick={()=>toggleSaved(c.slug)}><Bookmark/></button></div>
     </div>)}
    </div>:<div className="creator-grid">{rows.map(c=><CreatorCard key={c.slug} creator={c}/>)}</div>}
    {!rows.length&&<div className="empty-state"><h2>No filmmakers found</h2><p>Try another search or specialization.</p></div>}
   </div>
  </div>
  <Link to="/login" className="chat-fab" aria-label="Message the team"><MessageCircle/></Link>
  <AIBriefDialog open={briefOpen} onOpenChange={setBriefOpen} />
 <EscrowTermsDialog open={termsOpen} onOpenChange={setTermsOpen} onAgreed={()=>setBriefOpen(true)} />
 </main>;
}
