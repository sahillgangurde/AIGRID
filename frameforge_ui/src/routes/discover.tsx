import { createFileRoute } from '@tanstack/react-router';
import { DiscoverFeed } from '@/components/discover-feed';

export const Route = createFileRoute('/discover')({
  head: () => ({ meta: [
    { title: 'Discover creative reels — AiGrid' },
    { name: 'description', content: 'Explore creative motion studies, discover AI creators, and connect with the talent behind the work.' },
    { property: 'og:title', content: 'Discover creative reels — AiGrid' },
    { property: 'og:description', content: 'Explore creative motion studies and discover the AI creators behind the work.' },
    { property: 'og:type', content: 'website' },
    { name: 'twitter:card', content: 'summary_large_image' },
  ] }),
  component: DiscoverFeed,
});