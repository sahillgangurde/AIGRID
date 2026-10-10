import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";

const plans = [
  { name: "Starter", sub: "Start showing your AI films", monthly: 0, credits: "3 portfolio uploads", cta: "Start free", features: ["Public creator profile", "Up to 3 films", "Appear in the directory", "Community access"] },
  { name: "Creator", sub: "For working AI filmmakers", monthly: 999, credits: "Unlimited uploads + 10 brief pitches /mo", cta: "Upgrade", featured: true, features: ["Verified creator badge", "Pitch on brand briefs", "Profile analytics", "Priority directory placement", "Direct brand messages"] },
  { name: "Studio", sub: "For teams and serious creators", monthly: 4999, credits: "Unlimited pitches + 5 team seats", cta: "Upgrade to Studio", features: ["Everything in Creator", "Team workspace", "Featured spotlight each month", "Custom profile link", "Dedicated support"] },
];

export const Route = createFileRoute("/pricing")({
  head: () => ({ meta: [
    { title: "Creator Pricing — AiGrid" },
    { name: "description", content: "Plans for AI filmmakers: show your work, get verified and pitch on brand briefs." },
    { property: "og:title", content: "Creator Pricing — AiGrid" },
    { property: "og:description", content: "Choose a creator plan to show your work and win brand briefs." },
    { property: "og:type", content: "website" },
    { name: "twitter:card", content: "summary" },
  ] }),
  component: Pricing,
});

function Pricing() {
  const [yearly, setYearly] = useState(false);
  const fmt = (m: number) => m === 0 ? "₹0" : `₹${Math.round(yearly ? m * 10 / 12 : m).toLocaleString("en-IN")}`;
  return <section className="pricing">
    <h1>Choose your creator plan</h1>
    <p>For creators only. Upgrade or downgrade any time.</p>
    <div className="billing-toggle">
      <button aria-pressed={!yearly} onClick={() => setYearly(false)}>Monthly</button>
      <button aria-pressed={yearly} onClick={() => setYearly(true)}>Annually<em>Save 17%</em></button>
    </div>
    <div className="plans">{plans.map(p => <article key={p.name} className={p.featured ? "plan featured" : "plan"}>
      <h2>{p.name}</h2><p className="sub">{p.sub}</p>
      <p className="price">{fmt(p.monthly)}<small>/mo</small></p>
      <div className="credit">{p.credits}</div>
      <a className="cta" href="/login">{p.cta}</a>
      <ul>{p.features.map(f => <li key={f}>{f}</li>)}</ul>
    </article>)}</div>
  </section>;
}
