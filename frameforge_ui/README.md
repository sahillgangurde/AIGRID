# AiGrid — Where AI Creators Meet Brands

AiGrid is a marketplace-style web app that connects AI creators with brands. Discover exceptional AI creators, explore real creative work, and match your next campaign with the right talent.

Built with React 19, TanStack Start (SSR), Tailwind CSS v4 and shadcn/ui. Fully responsive, light/dark themes, presentation-only demo (no backend — sign-in is a local demo session).

## Features

### Home
- Cinematic hero with an auto-scrolling, swipeable **film wheel** — cards follow a curved path with velocity-based momentum (reduced-motion aware)
- **Count-up statistics** (Creators, Content traded, Briefs generated, Matchings) that replay on every visit
- Auto-sliding **AI tools marquee** (Adobe, Claude, OpenAI, Gemini, ElevenLabs, Kling, Suno, CapCut) — grayscale by default, brand colors on hover
- Scroll-driven **pear pairing animation** — two halves rotate and join into a whole fruit as you scroll
- Featured creators: Ananya Rao, Riddhi Shah, Kavya Iyer

### Discover — Reels Feed
- Instagram-style vertical reels with scroll-snap, keyboard navigation and arrow controls
- Play/pause, mute, like, comment, repost, save and share — all working as in-memory demo interactions

### AI Match — Creator Directory
- Nine creator profiles with filtering, sorting, list/grid views and saved creators
- Individual profile pages per creator

### Pricing
- Creator-only plans (Starter ₹0, Creator ₹999/mo, Studio ₹4,999/mo) with monthly/annual billing switch

### Accounts (demo)
- Sign up / sign in accepts any input — no database, unlimited sign-ins, only the email is kept in your own browser (never the password)
- **One-time onboarding** after sign-up: pick your path (Creator, Producer/EP, Rep/Agent, Hirer, Both) → "You're all set" screen with **Get verified** (creators) or **Hire Creator** (hirers)
- Signed-in header: **notification bell** with sample notifications + **profile menu** (Manage account, Dashboard, My Work, Profile, Notifications, Sign out)

### Design
- Black & white editorial theme with a minimal green accent (#5ABC7A)
- Apple-style animated **light/dark theme toggle**, persisted locally
- Reel Archivo for headings, monospace uppercase for labels

## Tech Stack

| Layer | Choice |
| --- | --- |
| Framework | TanStack Start v1 (React 19, SSR) |
| Styling | Tailwind CSS v4 + shadcn/ui |
| Icons | lucide-react |
| Tests | Vitest |
| Backend | None — presentation-only demo |

## Getting Started

```bash
bun install   # or npm install
bun dev       # start the dev server
bunx vitest run   # run the tests
```

## Project Structure

```text
src/
  routes/         # pages: home, discover, creators, pricing, login, legal
  components/     # header/footer, film wheel, reels feed, pear animation,
                  # account dialog, account menu, theme toggle, ui/ (shadcn)
  lib/            # data (creators, reels), demo session, motion helpers
  test/           # vitest suites for routing, motion, stats, session, theme
```

## Notes

- All creator names, prices and stats are demo data.
- Real account access lives on the original service; this app's sign-in is a local demo.
