import { Link } from '@tanstack/react-router';
import { ArrowUpRight } from 'lucide-react';

export function SectionBar() {
  return (
    <nav className="section-bar" aria-label="Site sections">
      <Link className="section-item" to="/discover">
        <span className="section-number">01</span>
        <h3>Discover<ArrowUpRight /></h3>
        <p>Browse films, reels and portfolios from AI filmmakers.</p>
      </Link>
      <Link className="section-item" to="/how-it-works">
        <span className="section-number">02</span>
        <h3>How it works<ArrowUpRight /></h3>
        <p>From the first brief to the finished film, in four steps.</p>
      </Link>
      <Link className="section-item" to="/creators" search={{ focus: 'search' }}>
        <span className="section-number">03</span>
        <h3>Search creator<ArrowUpRight /></h3>
        <p>Filter by specialization, industry and availability.</p>
      </Link>
      <Link className="section-item" to="/login">
        <span className="section-number">04</span>
        <h3>Become creator<ArrowUpRight /></h3>
        <p>Build your portfolio and start receiving brand briefs.</p>
      </Link>
    </nav>
  );
}
