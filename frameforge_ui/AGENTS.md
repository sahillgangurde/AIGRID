<!-- LOVABLE:BEGIN -->
> [!IMPORTANT]
> This project is connected to [Lovable](https://lovable.dev). Avoid rewriting
> published git history — force pushing, or rebasing/amending/squashing commits
> that are already pushed — as it rewrites history on Lovable's side and the
> user will likely lose their project history.
>
> Commits you push to the connected branch sync back to Lovable and show up in
> the editor, so keep the branch in a working state.
<!-- LOVABLE:END -->

- Keep shared Hypear navigation and footer in the root layout and content in leaf routes, so every page shares consistent navigation.
- Let the shared header choose the screenshot-matched home navigation by route, keeping navigation ownership in the root layout.
- Store downloaded reference media as asset pointers, so large media is served outside the source bundle.
- Keep this website recreation presentation-only; real account access lives on the original service, while the in-app sign-in runs as a local demo session.
- Keep film-wheel motion in a dedicated client component with tested motion helpers, so animation and swipe handling remain separate from home content.
- Animate home statistics in a dedicated client component using shared tested totals, so visits replay the count-up without changing the displayed figures.
- Keep the homepage entry-point bar in a dedicated component with one link per section, so section navigation stays separate from page content.
- Keep the AI-tool marquee in its own component using original logo asset pointers and CSS grayscale, so hover restores brand colors without altering section navigation.
- Keep filmmaker directory data in the shared data module with one place-formatting helper, so cards, profiles and the directory show the same details.
- Keep account-dialog presentation in a shared component opened by the root-owned header; the demo sign-in accepts any input and stores only the email locally, never the password.
- Keep theme selection in a root-owned provider with semantic CSS overrides and a shared header switch; persist only the display preference locally so every page and portaled dialog inherits the same theme.
- Keep the scroll-driven pear assembly in a dedicated client component with tested motion helpers and reusable cropped asset pointers; isolate its transforms from homepage content and honor reduced motion.
- Keep Discover reels in a dedicated client component with shared media data and session-only interactions, so the presentation-only feed needs no database and stays separate from the creator directory.
- Keep the signed-in header controls (notification bell + avatar dropdown) in a dedicated account-menu component, so the root-owned header stays lean and notifications remain sample, in-memory data.
- Keep post-signup onboarding (role picker + all-set step) inside the account dialog, driven by the demo-session role flag, so it appears exactly once per browser.
