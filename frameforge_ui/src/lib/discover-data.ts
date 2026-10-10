import pear from '@/assets/discover-pear.webm.asset.json';
import editorial from '@/assets/discover-editorial.webm.asset.json';
import brandWorld from '@/assets/discover-brand-world.webm.asset.json';
import { homeCreators } from '@/lib/hypear-data';

export const discoverReels = homeCreators.map((creator, index) => ({
  id: `reel-${creator.slug}`,
  creator,
  video: [pear.url, editorial.url, brandWorld.url][index] ?? pear.url,
  caption: [
    'A study in form, texture and movement. A new perspective on the everyday.',
    'Small details. A whole new world. Exploring the space between nature and design.',
    'Two worlds, one story. Creative connections in motion.',
  ][index] ?? 'Creative connections in motion.',
  likes: [168, 246, 93][index] ?? 0,
  tags: '#AIcreativity #Motion #VisualStorytelling',
}));