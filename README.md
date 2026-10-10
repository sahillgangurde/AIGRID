# ⚡ AIGRID • AI Content Creator Marketplace
### Cryptographically Verified, AI-Native Creative Marketplace Architecture
*Built for the Kampus.VC AI Content Creator Marketplace Challenge*

---

## 🚀 Live Servers & Local Access

Both servers are active, compiled, and configured:

| Component | URL | Status | Details |
| :--- | :--- | :--- | :--- |
| **Frontend Web App** | [http://localhost:5173/](http://localhost:5173/) | **ONLINE** | React 19 + Cyber-Luxe Glassmorphic Interface |
| **FastAPI Backend Gateway** | [http://127.0.0.1:8000/](http://127.0.0.1:8000/) | **ONLINE** | Python 3.14 + AST Guard + C2PA + Brief LLM Engine |
| **Interactive API Docs** | [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) | **ONLINE** | OpenAPI Swagger Documentation |

---

## 🏆 Hackathon Evaluation Alignment (100 Points + Bonus Credits)

| Hackathon Criterion | Weight | What Judges Look For | AuraForge Feature Implementation |
| :--- | :---: | :--- | :--- |
| **Creator Profiles & AI Portfolios** | **30%** | Rich profiles showcasing AI work, tools/models, skills, specialization, and workflows | Dedicated Creator Profiles displaying full toolchains (Runway Gen-3, Flux.1, ComfyUI, Kling), skills, specializations, video & still portfolio galleries, prompt snippets, and ComfyUI DAG inspector. |
| **Brief Definition** | **20%** | Clearly capture content type, style, format/aspect ratio, and commercial-use requirements | Complete **Brand Briefs Hub** capturing all 5 dimensions with dynamic GPU compute milestone calculations. |
| **Discovery & Filtering** | **25%** | Search and filtering by skills, tools, attributes; sensible empty handling | Real-time search bar, 5 categorical dropdown filters, verified-only toggle, active filter chips, and **top-rated fallback recommendations** when filters yield 0 exact matches. |
| **User Experience** | **15%** | Easy flows for creators and brands; clear portfolio viewing | Cyber-luxe interface, video playback modals, one-click sandbox testing, and seamless brief-to-escrow transitions. |
| **Presentation & Demo** | **10%** | Working prototype demonstrated clearly | Live React 19 + FastAPI microservice architecture with instant mock and test pipelines. |
| **BONUS: Verification Signals** | **+5 Pts** | Visible trust indicators for tools, workflows, past work | Visible badges on creator cards: **Tool Certified Badges**, **AST-Audited DAG Badges**, and **Past Client Track Records** (e.g. 51 Projects • 4.99 Rating). |
| **BONUS: AI-Assisted Brief Builder** | **+5 Pts** | Transform rough idea into complete structured creative brief | **Prompt-to-Brief LLM Engine** (`/api/briefs/ai-generate`) that takes rough ideas (e.g. "15s sneaker ad for TikTok") and outputs structured aspect ratios, tools, skills, milestones & budgets. |

---

## 🛠️ The Core Modules Implemented

1. **Creators & Portfolios Hub (`/api/creators/search`):**
   - Rich profiles featuring AI Filmmakers, Virtual Human animators, Product designers, and Game artists.
   - Exact toolchains: Runway Gen-3 Alpha, FLUX.1 Dev, ComfyUI, Kling AI, Midjourney v6, Hedra AI, Topaz Video AI.
   - Granular skills: Temporal Consistency, Camera Motion Control, Audio-Driven Lip Sync, LoRA Training.
   - Video & still portfolio gallery with modal viewer, prompt excerpts, and C2PA certification.
   - **Creator Verification Signals**: Visible tool mastery, audited workflow badges, and past delivery records.

2. **Brand Briefs Hub & AI-Assisted Brief Builder (`/api/briefs/ai-generate`):**
   - **AI-Assisted Brief Builder**: Transforms raw ideas into structured briefs with content type, style, 9:16/16:9 ratios, recommended AI tools, budget, and milestone splits.
   - **Active Briefs Feed**: Published campaign briefs with status, required stack, and proposals count.
   - **Manual Brief Composer**: Complete form capturing all 5 dimensions for full brand control.

3. **Zero-Leakage "Try-Before-You-Buy" Sandbox (`/api/sandbox/render-preview`):**
   - Brands test creator LoRAs directly in the browser before commissioning.
   - Model weights (`.safetensors`) remain isolated in ephemeral RAM.
   - Outputs watermarked demo grids with frequency-domain steganography.

4. **Proof-of-Workflow & AST Guard (`/api/workflow/verify-comfy`):**
   - Parses arbitrary ComfyUI JSON DAGs.
   - Enforces an AST safety whitelist (blocks malicious nodes like `exec`, `eval`, disk read).
   - Generates deterministic **SHA-256 workflow fingerprints**.

5. **C2PA Provenance Vault (`/api/provenance/sign-c2pa`):**
   - Synthesizes ISO 21000-22 JUMBF assertion manifests and digital watermark tokens.
   - Embeds X.509 cryptographic signatures validating chain-of-custody.

6. **Dynamic Compute-Aware Escrow (`/api/escrow/calculate`):**
   - Calculates GPU compute overhead based on hardware tier (H100 SXM5, A100, A10G) and steps.
   - Automated milestone release: 30% upfront for GPU allocation; 70% settlement upon cryptographic verification.

7. **Architecture & Data Model Deliverable Note:**
   - In-app interactive view (`Data Model Note` tab) and full written specification in [`DATA_MODEL_AND_ARCHITECTURE.md`](file:///c:/Users/Sahil%20Gangurde/OneDrive/Desktop/AI%20CONTENT%20CREATOR/DATA_MODEL_AND_ARCHITECTURE.md).

---

## 🎬 3-Minute Hackathon Demo Script for Judges

1. **Step 1: Open [http://localhost:5173/](http://localhost:5173/) (Creators & Portfolios)**
   - Point out the rich creator cards (e.g. Julian Mercer - AI Filmmaking, Maya Chen - Virtual Avatars).
   - Show the **Creator Verification Signals** (*"Runway Certified Director"*, *"AST-Audited DAG"*, *"51 Projects • 4.99 Rating"*).
   - Demonstrate the **Multi-Attribute Filters**: select `Tool: Runway Gen-3 Alpha` or `Aspect Ratio: 9:16 (Vertical)`.
   - Click a portfolio card to open the **AI Portfolio Modal**: show the video player, prompt excerpt, tools used, and C2PA signature.

2. **Step 2: Brand Briefs & AI Builder Tab**
   - Click **"Brand Briefs & AI Builder"** in the top navbar.
   - Click an inspiration chip (e.g., *"15-second kinetic sneaker ad for TikTok with neon liquid splashes"*).
   - Click **"⚡ Generate Structured Brief with AI"**.
   - Show how the AI engine automatically structures:
     - Content Type: `Social Video Commercial`
     - Aspect Ratio: `9:16 (Vertical Reels/TikTok)`
     - AI Toolchain: `Runway Gen-3 Alpha, Kling AI, Flux.1 Dev, Topaz Video AI`
     - Required Skills: `Temporal Consistency, Camera Motion Control, Audio Sync`
     - Milestones: `30% Sandbox Test, 40% First Cut, 30% 4K Master & C2PA Provenance`
   - Click **"Publish Brief"** and view it in the **Active Campaigns** feed!

3. **Step 3: Try-Before-Buy Sandbox**
   - Click **"Try-Before-Buy"** in the top navbar.
   - Run a sandboxed preview test to show zero model weight leakage and anti-theft demo watermarking.

4. **Step 4: Workflow Inspector & C2PA Provenance**
   - Show the ComfyUI DAG node graph and AST security scan generating a SHA-256 fingerprint.
   - Sign the C2PA manifest to show the ISO 21000-22 digital authenticity certificate.

5. **Step 5: Data Model Deliverable Note**
   - Click **"Data Model Note"** to showcase the TypeScript schemas for `CreatorProfile` and `CreativeBrief` and the 100-point evaluation criteria alignment!

---

## 🛠️ How to Restart Servers

```bash
# Terminal 1: Backend
python -m uvicorn server.main:app --host 127.0.0.1 --port 8000

# Terminal 2: Frontend
npm run dev
```
