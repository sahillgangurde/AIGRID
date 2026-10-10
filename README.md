# ⚡ AiGrid • AI Content Creator Marketplace
### The Right AI Creator. For The Work That Matters.
*Built for the Kampus.VC AI Content Creator Marketplace Challenge*

---

## 🚀 Live Servers & Local Access

Both servers are active, compiled, and production-ready:

| Component | URL | Status | Details |
| :--- | :--- | :--- | :--- |
| **Frontend Web App** | [http://localhost:3000/](http://localhost:3000/) | **ONLINE** | TanStack Start (React 19) + Vite + Editorial Cinema UI |
| **FastAPI Backend Gateway** | [http://127.0.0.1:8000/](http://127.0.0.1:8000/) | **ONLINE** | Python 3.12+ + PII Shield + C2PA + AST Guard Engine |
| **Interactive API Docs** | [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) | **ONLINE** | OpenAPI Swagger Documentation |

---

## 🏆 Hackathon Evaluation Alignment (100 Points + Bonus Credits)

| Hackathon Criterion | Weight | What Judges Look For | AiGrid Feature Implementation |
| :--- | :---: | :--- | :--- |
| **Creator Profiles & AI Portfolios** | **30%** | Rich profiles showcasing AI work, tools/models, skills, specialization, and workflows | Dedicated Creator Profiles (`/creators/ananya-rao`) displaying verified toolchains (Runway Gen-3, Flux.1 Dev, ComfyUI, Kling), skills, specializations, video & still portfolio galleries, prompt snippets, and generation metadata drawer (model, seed, steps). |
| **Brief Definition** | **20%** | Clearly capture content type, style, format/aspect ratio, and commercial-use requirements | **AI-Powered Brief Assistant** modal capturing all 5 dimensions (format, style, stack, timeline, commercial terms) with automatic compute milestone splits. |
| **Discovery & Filtering** | **25%** | Search and filtering by skills, tools, attributes; sensible empty handling | Real-time search bar, specialized tool chips (Runway, Midjourney, ComfyUI, Kling), category filters, and interactive creator cards with trust scores and response times. |
| **User Experience** | **15%** | Easy flows for creators and brands; clear portfolio viewing | Award-winning editorial motion design, rotating 3D Film Wheel, Discover vertical video feed (`/discover`), and smooth modal viewers. |
| **Presentation & Demo** | **10%** | Working prototype demonstrated clearly | Live TanStack Start (React 19) + FastAPI microservice architecture with passing test suites (`83 passed`). |
| **BONUS: Verification Signals** | **+5 Pts** | Visible trust indicators for tools, workflows, past work | Visible badges on creator cards: **Trust Score (94/100 Verified)**, **C2PA Provenance Signed**, and hourly compute rates (`$45/hr`). |
| **BONUS: AI-Assisted Brief Builder** | **+5 Pts** | Transform rough idea into complete structured creative brief | **Prompt-to-Brief LLM Engine** (`/api/briefs/ai-generate`) that takes rough ideas (e.g. "30s futuristic electric car commercial in neon cyberpunk rain") and outputs structured aspect ratios, recommended tools, skills, milestones & budgets. |

---

## 🛠️ The Core Modules Implemented

1. **Creators & Portfolios Hub (`/creators` & `/api/creators`):**
   - Rich profiles featuring AI Filmmakers and Directors (Ananya Rao, Riddhi Shah, Kavya Iyer, Sujal Tandel, Mahir Khan).
   - Exact toolchains: Runway Gen-3 Alpha, FLUX.1 Dev, ComfyUI LoRAs, Kling AI, Midjourney v6, ElevenLabs, Suno.
   - Granular specializations: Editorial & lookbook, Brand campaign visuals, Motion graphics, Short-form video (Reels/TikTok).
   - Cryptographic C2PA provenance badges and metadata inspection drawer.

2. **AI Brief Assistant (`/api/briefs/ai-generate`):**
   - Transforms natural language prompts into complete commercial briefs.
   - Outputs: Content type, 9:16 vertical & 16:9 cinema ratios, recommended AI pipelines, milestone budgets, and C2PA buyout terms.
   - Gated by mutual Confidentiality and Escrow agreements.

3. **Secure Messaging & Anti-Leakage PII Shield (`messages-dock`):**
   - Floating dark-mode anonymous communication channel with escrow protection.
   - Real-time client & server interception of phone numbers, WhatsApp links, and off-platform payment IDs.
   - Intercepted messages display visible warning toast and redacted badges (`📵 [Phone Blocked]`).

4. **Projects & Milestone Escrow Workspace (`/dashboard`):**
   - Full visibility into project lifecycle: pitch, milestone funding, draft review, and buyout.
   - Active metrics: Funds in Escrow (₹1,20,000 locked), Active Projects, and 98% Trust Rating.
   - Milestones: 30% Upfront Compute (Paid), 40% Rough Cut Review (Watermarked Preview), 30% Final Buyout & C2PA.

5. **Discover Continuous Video Feed (`/discover`):**
   - Full-screen vertical motion study reel with audio controls, creator attribution, and direct project commissioning.

6. **Automated Test Suite:**
   - 83 comprehensive pytest test cases validating backend security, escrow math, and PII interception:
   ```bash
   python -m pytest tests/ -v
   # Result: 83 passed in ~2.5s
   ```

---

## 🎬 3-Minute Hackathon Demo Script for Judges

1. **Step 1: Open [http://localhost:3000/](http://localhost:3000/) (Homepage)**
   - Show the **AiGrid** hero wordmark, live counter metrics, and rotating **Film Wheel**.
   - Scroll past the verified AI tool marquee (Midjourney, Runway, Kling, Adobe Firefly, CapCut).

2. **Step 2: AI Brief Assistant**
   - Click **"AI brief"** in the top navbar.
   - Enter: `"30s futuristic electric car commercial in neon cyberpunk rain"`.
   - Click **"Generate with AI"** to showcase instant multi-format brief expansion and milestone allocation.

3. **Step 3: Creator Directory & Profile ([http://localhost:3000/creators](http://localhost:3000/creators))**
   - Filter by `Runway` or `Editorial`.
   - Click **Ananya Rao** (`/creators/ananya-rao`): showcase **Trust Score (94/100)**, **C2PA Signed** badge, and inspect model generation metadata (Flux.1 Dev, seed, steps).

4. **Step 4: Anti-Leakage Secure Messaging**
   - Click **"Message"** to open the chat dock.
   - Type `"Call me on 9876543210 or wa.me/link"` and press Send.
   - Show the live interception toast: `⚠️ PII_INTERCEPTED` and automatic redaction to `📵 [Phone Blocked]`.

5. **Step 5: Projects & Escrow Workspace ([http://localhost:3000/dashboard](http://localhost:3000/dashboard))**
   - Review the ₹1,20,000 escrow vault, milestone releases, and C2PA delivery approvals.

---

## 🛠️ How to Run Locally

```bash
# Terminal 1: Python Backend
python -m uvicorn server.main:app --host 127.0.0.1 --port 8000

# Terminal 2: Frontend UI
npm run dev
# (Runs on http://localhost:3000/)
```
