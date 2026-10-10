import { useEffect, useRef, useState } from 'react';
import { Link } from '@tanstack/react-router';
import { Bookmark, ChevronDown, ChevronUp, Heart, MessageCircle, MoreHorizontal, Pause, Play, Repeat2, Send, Volume2, VolumeX, ArrowDownToLine } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { discoverReels } from '@/lib/discover-data';

export function DiscoverFeed() {
  const feed = useRef<HTMLDivElement>(null);
  const videos = useRef<(HTMLVideoElement | null)[]>([]);
  const [active, setActive] = useState(0);
  const [muted, setMuted] = useState(true);
  const [paused, setPaused] = useState(false);
  const [liked, setLiked] = useState<string[]>([]);
  const [saved, setSaved] = useState<string[]>([]);
  const [followed, setFollowed] = useState<string[]>([]);
  const [reposted, setReposted] = useState<string[]>([]);
  const [dialog, setDialog] = useState<'comments' | 'share' | 'more' | null>(null);
  const [comments, setComments] = useState<Record<string, string[]>>({});
  const [draft, setDraft] = useState('');
  const [copied, setCopied] = useState(false);
  const reel = discoverReels[active];
  const toggle = (id: string, setter: React.Dispatch<React.SetStateAction<string[]>>) => setter(previous => previous.includes(id) ? previous.filter(value => value !== id) : [...previous, id]);
  const move = (direction: number) => {
    const element = feed.current;
    if (!element) return;
    const next = Math.max(0, Math.min(discoverReels.length - 1, active + direction));
    element.scrollTo({ top: element.clientHeight * next, behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth' });
  };
  useEffect(() => {
    videos.current.forEach((video, index) => {
      if (!video) return;
      video.muted = muted;
      if (index === active && !paused && !dialog) void video.play().catch(() => setPaused(true));
      else video.pause();
    });
  }, [active, muted, paused, dialog]);
  useEffect(() => {
    const visibility = () => { if (document.hidden) videos.current.forEach(video => video?.pause()); else setPaused(true); };
    document.addEventListener('visibilitychange', visibility);
    return () => document.removeEventListener('visibilitychange', visibility);
  }, []);
  if (!reel) return null;
  return <main className="discover-page" aria-label="Discover reels">
    <div className="discover-heading"><h1>Discover</h1><span>Creative feed <i/> {String(active + 1).padStart(2, '0')} / {String(discoverReels.length).padStart(2, '0')}</span></div>
    <div ref={feed} className="discover-feed" tabIndex={0} aria-label="Reels feed" onScroll={event => {
      const element = event.currentTarget;
      const next = Math.round(element.scrollTop / element.clientHeight);
      if (next !== active) { setActive(Math.max(0, Math.min(discoverReels.length - 1, next))); setPaused(false); }
    }} onKeyDown={event => {
      if (event.target !== event.currentTarget) return;
      if (event.key === 'ArrowDown' || event.key === 'ArrowUp') { event.preventDefault(); move(event.key === 'ArrowDown' ? 1 : -1); }
      if (event.key === ' ') { event.preventDefault(); setPaused(value => !value); }
    }}>
      {discoverReels.map((item, index) => <article className="discover-slide" key={item.id} aria-label={`Reel by ${item.creator.name}`}>
        <div className="discover-identity">
          <div className="discover-author"><Link to="/creators/$slug" params={{slug: item.creator.slug}}><img src={item.creator.avatar} alt=""/>{item.creator.name}</Link><span>·</span><Button variant="ghost" onClick={() => toggle(item.creator.slug, setFollowed)} aria-pressed={followed.includes(item.creator.slug)}>{followed.includes(item.creator.slug) ? 'Following' : 'Follow'}</Button></div>
          <p>{item.caption}</p><p className="discover-tags">{item.tags}</p>
        </div>
        <div className="discover-video">
          <video ref={element => { videos.current[index] = element; }} src={item.video} poster={item.creator.image} loop muted playsInline preload={index === active ? 'auto' : 'metadata'} aria-label={`${item.creator.name} creative motion study`}/>
          <Button className="discover-play" variant="ghost" aria-label={paused ? 'Play reel' : 'Pause reel'} onClick={() => setPaused(value => !value)}>{paused ? <Play/> : <Pause/>}</Button>
          <Button className="discover-sound" variant="ghost" size="icon" aria-label={muted ? 'Unmute reel' : 'Mute reel'} onClick={() => setMuted(value => !value)}>{muted ? <VolumeX/> : <Volume2/>}</Button>
          <span className="discover-video-label">AIgrid / motion studies</span>
        </div>
        <div className="discover-social">
          <Button asChild variant="ghost" size="icon" aria-label="Download reel" title="Download reel"><a href={item.video} download="creative-study.webm"><ArrowDownToLine/></a></Button>
          <div><Button variant="ghost" size="icon" aria-label={`Like ${item.creator.name}'s reel`} aria-pressed={liked.includes(item.id)} title="Like" onClick={() => toggle(item.id, setLiked)}><Heart className={liked.includes(item.id) ? 'is-filled' : ''}/></Button><span>{item.likes + Number(liked.includes(item.id))}</span></div>
          <div><Button variant="ghost" size="icon" aria-label="Comments" title="Comments" onClick={() => {setActive(index);setDialog('comments');}}><MessageCircle/></Button><span>{comments[item.id]?.length ?? 0}</span></div>
          <div><Button variant="ghost" size="icon" aria-label="Repost reel" title="Repost" aria-pressed={reposted.includes(item.id)} onClick={() => toggle(item.id, setReposted)}><Repeat2/></Button><span>{Number(reposted.includes(item.id))}</span></div>
          <Button variant="ghost" size="icon" aria-label="Share reel" title="Share" onClick={() => {setCopied(false);setDialog('share');}}><Send/></Button>
          <Button variant="ghost" size="icon" aria-label="Save reel" title="Save" aria-pressed={saved.includes(item.id)} onClick={() => toggle(item.id, setSaved)}><Bookmark className={saved.includes(item.id) ? 'is-filled' : ''}/></Button>
          <Button variant="ghost" size="icon" aria-label="More options" title="More options" onClick={() => setDialog('more')}><MoreHorizontal/></Button>
          <Link to="/creators/$slug" params={{slug:item.creator.slug}} className="discover-avatar" aria-label={`View ${item.creator.name}`}><img src={item.creator.avatar} alt=""/></Link>
        </div>
      </article>)}
    </div>
    <div className="discover-arrows"><Button variant="ghost" size="icon" aria-label="Previous reel" title="Previous reel" disabled={active === 0} onClick={() => move(-1)}><ChevronUp/></Button><Button variant="ghost" size="icon" aria-label="Next reel" title="Next reel" disabled={active === discoverReels.length - 1} onClick={() => move(1)}><ChevronDown/></Button></div>
    <Dialog open={dialog !== null} onOpenChange={open => {if (!open) setDialog(null);}}><DialogContent className="discover-dialog"><DialogTitle>{dialog === 'comments' ? 'Comments' : dialog === 'share' ? 'Share this reel' : 'Reel options'}</DialogTitle><DialogDescription>{reel.creator.name} · Creative motion study</DialogDescription>
      {dialog === 'comments' && <><div className="discover-comments">{(comments[reel.id] ?? []).length ? comments[reel.id]?.map((comment, index) => <p key={index}><strong>You</strong>{comment}</p>) : <p>No comments yet.</p>}</div><form onSubmit={event => {event.preventDefault();if (!draft.trim()) return;setComments(previous => ({...previous,[reel.id]:[...previous[reel.id] ?? [],draft.trim()]}));setDraft('');}}><input aria-label="Add a comment" placeholder="Add a comment…" value={draft} onChange={event => setDraft(event.target.value)}/><Button type="submit" size="icon" aria-label="Post comment" disabled={!draft.trim()}><Send/></Button></form></>}
      {dialog === 'share' && <Button onClick={async () => {try {await navigator.clipboard.writeText(`${window.location.origin}/discover`);setCopied(true);} catch {setCopied(false);}}}>{copied ? 'Link copied' : 'Copy link'}</Button>}
      {dialog === 'more' && <><Button asChild variant="outline"><Link to="/creators/$slug" params={{slug:reel.creator.slug}}>View creator</Link></Button><Button variant="outline" onClick={() => {toggle(reel.id,setSaved);setDialog(null);}}>{saved.includes(reel.id) ? 'Remove from saved' : 'Save reel'}</Button></>}
    </DialogContent></Dialog>
  </main>;
}