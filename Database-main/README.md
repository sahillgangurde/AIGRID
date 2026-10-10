# CreatorSphere AI — Database Architecture & Engineering Guide

> **CreatorSphere AI**: An AI-powered video creator marketplace connecting customers needing high-impact videos with skilled creators across AI generation, 3D animation, editing, product ads, cinematic films, and social reels.

This repository contains the complete PostgreSQL database component designed for **Supabase**, including versioned SQL migrations, a rich fictional seed dataset, parameterized application queries, Row Level Security (RLS) policies, automated test suites, and backend integration patterns for Next.js.

---

## Table of Contents

1. [Architecture & Technology Stack](#1-architecture--technology-stack)
2. [Folder Structure](#2-folder-structure)
3. [Database Schema (24 Tables & 2 Views)](#3-database-schema-24-tables--2-views)
4. [Step-by-Step Supabase Setup](#4-step-by-step-supabase-setup)
5. [Running Migrations & Seed Data](#5-running-migrations--seed-data)
6. [Core Application Queries](#6-core-application-queries)
7. [Security & Row Level Security (RLS)](#7-security--row-level-security-rls)
8. [Automated Testing & Verification (239 Tests Passing)](#8-automated-testing--verification)
9. [Backend Integration for Teammates](#9-backend-integration-for-teammates)
10. [Documentation Map](#10-documentation-map)

---

## 1. Architecture & Technology Stack

- **Database Engine**: PostgreSQL 15+ hosted on [Supabase](https://supabase.com).
- **Authentication**: Native Supabase Authentication (`auth.users`) with automated profile synchronization and role self-escalation protection.
- **Search & Filtering**: PostgreSQL `TEXT[]` arrays with **Generalized Inverted Indexes (GIN)** for instant array containment (`@>`) and overlap (`&&`) filtering, plus `pg_trgm` for fuzzy text matching on names and handles.
- **One-Sided Anonymity**: Pseudonym masking (`anonymous_creators`) protects creator identities until customer payment is confirmed.
- **In-Platform Moderation**: Multi-layered deterministic regex and contextual censorship against off-platform contact sharing (`message_moderation_logs`).
- **Access Control**: Granular Row Level Security (RLS) policies enabled across 100% of tables with non-recursive security helper functions.
- **Frontend / Backend Compatibility**: Fully typed for Next.js App Router and TypeScript.

---

## 2. Folder Structure

```text
Database/
├── .env.example                               # Safe environment variables template
├── .gitignore                                 # Protection against committing secrets, credentials & backend code
├── README.md                                  # Master database documentation (this file)
├── package.json                               # Database test runner & dependencies (PGlite, pg-mem)
├── package-lock.json                          # Dependency lockfile
│
├── supabase/
│   ├── config.toml                            # Supabase CLI configuration
│   ├── seed.sql                               # 12+ realistic fictional creators & complete marketplace seed data
│   └── migrations/
│       ├── 20261009120000_001_initial_schema.sql         # Core 7 tables, constraints, triggers & GIN indexes
│       ├── 20261009120001_002_security_policies.sql      # Row Level Security (RLS) access control policies
│       └── 20261009130000_003_marketplace_evolution.sql # 16 new tables, 2 views, chat, quotes, contracts & ledger
│
├── queries/
│   ├── creator_search.sql                     # Discovery, search, and multi-criteria filter queries
│   ├── briefs_and_enquiries.sql               # Project briefs, bids, creator jobs, and direct inbox
│   ├── analytics_and_admin.sql                # Marketplace KPIs, top skills in demand, and audit queries
│   └── marketplace_lifecycle.sql              # Anonymity, chat, quotes, contracts, unlocks & reviews (M1–M10)
│
├── tests/
│   ├── database_test_suite.sql                # SQL assertion suite for Supabase Cloud SQL Editor (16 assertions)
│   ├── validate_sql_syntax.js                 # Automated local static validation runner (117 assertions)
│   ├── test_live_pg_execution.js              # Real PostgreSQL engine clean install & DDL tests (19 tests)
│   └── security_adversarial_test.js           # Real PostgreSQL 18 adversarial penetration suite (38 attacks)
│
└── docs/
    ├── DATABASE_ARCHITECTURE.md               # Detailed data dictionary & Mermaid ERD diagram
    ├── DATABASE_REQUIREMENTS_MATRIX.md        # Traceability matrix for all 10 marketplace requirements
    ├── DATABASE_SECURITY_AUDIT.md             # Security audit log & forensic vulnerability findings
    ├── FINAL_DATABASE_AUDIT.md                # Independent database audit report
    ├── PROJECT_COMPLETION_REPORT.md           # Engineering verification & testing audit report
    ├── BACKEND_INTEGRATION_GUIDE.md           # TypeScript & Next.js integration guide (backend handoff)
    ├── INTEGRATION_HANDOFF.md                 # Developer setup & integration guide (backend handoff)
    ├── INTEGRATION_TEST_REPORT.md             # Integration test execution report (backend handoff)
    └── PRODUCT_DECISIONS_REQUIRED.md          # Open business decisions (A through I) requiring founder input

Note on Backend Application Files:
The companion backend application services (`services/`) and cross-boundary integration test
(`tests/marketplace_integration_test.js`) are maintained locally for backend repository integration
and are ignored by Git in this dedicated database deliverable repository.
```

---

## 3. Database Schema (24 Tables & 2 Views)

| # | Table / View | Purpose | Key Relationships / Integrity Rules |
|---|---|---|---|
| 1 | **`users`** | Base account profiles synced from `auth.users`. Roles: `customer`, `creator`, `both`, `admin`, `moderator`. | Parent of `creators`, `briefs`, `enquiries`. Guarded by `protect_user_profile`. |
| 2 | **`creators`** | Public creator profiles with skills, equipment, and production capabilities. | 1:1 with `users`. Rating guarded by `protect_creator_reputation`. |
| 3 | **`portfolio_items`** | Showcase video samples with aspect ratios and verification status. | Belongs to `creators`. Guarded by `protect_portfolio_verification`. |
| 4 | **`briefs`** | Customer video project requests with AI summaries and deliverables. | Belongs to `users`. Guarded by `prevent_active_brief_deletion`. |
| 5 | **`enquiries`** | Direct 1-to-1 customer-to-creator communications. | Links customer and creator. Guarded by `enforce_enquiry_status_transitions`. |
| 6 | **`creator_interests`** | Creator pitches and bids submitted on open briefs. | UNIQUE(`brief_id`, `creator_id`). Guarded by `enforce_pitch_update_rules`. |
| 7 | **`verification_signals`** | Proof of authentic identity, portfolio ownership, and software badges. | Links to `creators` and `portfolio_items`. |
| 8 | **`creator_private_contacts`**| Isolated private emails, phone numbers, and legal billing details. | 1:1 with `creators`. Protected by `has_unlocked_creator()` RLS gate. |
| 9 | **`contact_unlocks`** | Audit gatekeeper tracking authorized contact access post-payment. | UNIQUE(`customer_id`, `creator_id`). Guarded by `protect_contact_unlock_creation`. |
| 10 | **`brief_ai_sessions`** | Interactive AI brief drafting sessions between customer and assistant. | Belongs to customer. Isolated by RLS. |
| 11 | **`brief_ai_messages`** | Conversational messages and token metadata within AI brief sessions. | Belongs to `brief_ai_sessions`. |
| 12 | **`brief_revisions`** | Versioned snapshot history of generated brief specifications. | UNIQUE(`brief_id`, `revision_number`). |
| 13 | **`brief_matches`** | Explainable AI matching scores linking briefs and candidate creators. | UNIQUE(`brief_id`, `creator_id`). CHECK `0 <= match_score <= 100`. |
| 14 | **`chat_conversations`** | In-platform discussion threads linked to briefs or active contracts. | Participant isolation via `is_chat_participant()`. |
| 15 | **`chat_participants`** | Conversation participants with pseudonym display aliases. | UNIQUE(`conversation_id`, `user_id`). |
| 16 | **`chat_messages`** | Thread messages with soft deletes and moderation censorship states. | Guarded by `protect_chat_message_moderation`. |
| 17 | **`chat_attachments`** | Uploaded video references, storyboards, and scripts with scanning flag. | Belongs to `chat_messages`. |
| 18 | **`message_moderation_logs`** | Security audit records of prohibited contact sharing attempts. | Tracks detection category, redacted text, and appeal notes. |
| 19 | **`project_quotes`** | Creator proposals with automated 15% platform take rate computation. | Guarded by `enforce_quote_pricing_integrity`. |
| 20 | **`projects`** | Formal contracts with state machine transition protections. | Guarded by `enforce_project_status_transitions`. |
| 21 | **`payments`** | Idempotent transaction records across payment gateways. | Guarded by `protect_payment_state` (only `service_role` confirms success). |
| 22 | **`financial_ledger`** | Double-entry journal for escrow balances, platform fees, and payouts. | Restricted to `admin` and `service_role`. |
| 23 | **`reviews`** | Verified completed project ratings with automated score recalculation. | UNIQUE(`project_id`). Guarded by `validate_and_apply_review`. |
| 24 | **`creator_subscriptions`** | Tiered creator monetization plans (`free`, `starter`, `pro`, `agency`). | Guarded by `protect_creator_subscription_updates`. |
| V1 | **`anonymous_creators`** | Secure View masking creator identity as `'Creator XXXXXX'` until unlocked. | Secure discovery layer. |
| V2 | **`customer_quotes_view`** | Secure View presenting consolidated customer price while masking net take. | Secure customer quote presentation. |

For detailed documentation, refer to [DATABASE_ARCHITECTURE.md](file:///c:/Users/MAHIR/OneDrive/Desktop/Database/docs/DATABASE_ARCHITECTURE.md).

---

## 4. Step-by-Step Supabase Setup

Setting up your cloud PostgreSQL database on Supabase:

1. **Sign Up / Log In**: Navigate to [https://supabase.com](https://supabase.com).
2. **Create New Project**:
   * Name: `CreatorSphere AI`.
   * Database Password: Store securely in your password manager.
   * Region: Geographically closest to your audience.
   * Plan: **Free tier**.
3. **Locate the SQL Editor**: Click on the **SQL Editor** (`>_`) icon in the left navigation sidebar.

---

## 5. Running Migrations & Seed Data

Apply the complete database in sequential order:

### Step 1: Initial Schema
1. Open [`supabase/migrations/20261009120000_001_initial_schema.sql`](file:///c:/Users/MAHIR/OneDrive/Desktop/Database/supabase/migrations/20261009120000_001_initial_schema.sql).
2. Copy and execute in the Supabase SQL Editor.

### Step 2: Security Policies
1. Open [`supabase/migrations/20261009120001_002_security_policies.sql`](file:///c:/Users/MAHIR/OneDrive/Desktop/Database/supabase/migrations/20261009120001_002_security_policies.sql).
2. Copy and execute in the Supabase SQL Editor.

### Step 3: Marketplace Evolution
1. Open [`supabase/migrations/20261009130000_003_marketplace_evolution.sql`](file:///c:/Users/MAHIR/OneDrive/Desktop/Database/supabase/migrations/20261009130000_003_marketplace_evolution.sql).
2. Copy and execute in the Supabase SQL Editor.

### Step 4: Seed Data
1. Open [`supabase/seed.sql`](file:///c:/Users/MAHIR/OneDrive/Desktop/Database/supabase/seed.sql).
2. Copy and execute in the Supabase SQL Editor.

---

## 6. Core Application Queries

Production queries are organized across 4 dedicated files in [`queries/`](file:///c:/Users/MAHIR/OneDrive/Desktop/Database/queries/):
- `queries/creator_search.sql`: Discovery, search, and multi-criteria GIN filter queries.
- `queries/briefs_and_enquiries.sql`: Project briefs, bids, creator opportunities, and direct inbox.
- `queries/analytics_and_admin.sql`: Platform KPIs, skills in demand, and audit reporting.
- `queries/marketplace_lifecycle.sql`: Complete marketplace lifecycle queries (M1–M10) covering anonymous discovery, chat filtering, quotes, contracts, contact unlocks, reviews, and ledger audits.

---

## 7. Security & Row Level Security (RLS)

- **100% RLS Coverage**: Enabled across all 24 tables.
- **One-Sided Anonymity**: Creators remain anonymous during discovery. Private contacts are locked behind verified payment unlock records.
- **Anti-Self-Escalation**: Triggers prevent users from self-promoting to `admin` or `moderator`.
- **Payment Verification**: Contact unlocking is strictly gated by verified `succeeded` payments confirmed via backend webhooks.

---

## 8. Automated Testing & Verification

### Database Automated Test Suite (193 Tests):
Execute the complete database verification suite locally:
```powershell
npm test
# Note: On Windows PowerShell with strict execution policy, run:
npm.cmd test
```

### Test Suite Breakdown:
1. **Static Analysis & Schema Integrity** (`tests/validate_sql_syntax.js`):
   - **117 / 117 assertions passed (0 failed)**.
   - Validates all 24 tables, GIN/trigram indexes, triggers, constraints, RLS policies, seed records, queries, and secret exclusion.
2. **PostgreSQL Relational Engine & Constraints** (`tests/test_live_pg_execution.js` via `pg-mem`):
   - **19 / 19 tests passed (0 failed)**.
   - Validates live DDL execution, foreign keys, CHECK violations, CASCADE deletions, and joins in an in-memory SQL engine.
3. **Adversarial Penetration & Security Hardening Suite** (`tests/security_adversarial_test.js` via `PGlite`):
   - **57 / 57 attacks mitigated (0 failed)**.
   - Boots an isolated PostgreSQL 18 engine, applies Migrations 001, 002, and 003, and simulates live penetration attacks against roles, triggers, anonymity masking, chat censorship, attachment authorization and participant separation, quotes cross-tenant isolation, contracts, and payments.
4. **Supabase Cloud SQL Editor Assertions** (`tests/database_test_suite.sql`):
   - **16 pure SQL assertions** executable directly inside the Supabase SQL Editor without Node.js.

### Companion Backend Integration Suite (46 Tests):
When running in an environment with the companion backend services (`services/`), execute:
```powershell
npm run test:all
# Or on Windows PowerShell:
npm.cmd run test:all
```
This runs the full **239 automated tests** (193 database tests + 46 backend integration tests in `tests/marketplace_integration_test.js`).

---

## 8.1 Developer Quickstart (Fresh Workstation Setup)

To recreate and verify the database on a fresh computer:

1. **Prerequisites**: Node.js v18.0.0+ (or v20+) and npm installed.
2. **Clone & Install Dependencies**:
   ```bash
   git clone https://github.com/localhost3k11/Database-.git
   cd Database-
   npm install
   ```
3. **Run Database Verification**:
   ```bash
   npm test
   ```
4. **Deploy to Hosted Supabase (`CreatorSphere-Dev`)**:
   ```bash
   supabase login
   supabase link --project-ref <your-project-id>
   supabase db push
   ```


---

## 9. Backend Integration for Teammates

Refer to [BACKEND_INTEGRATION_GUIDE.md](file:///c:/Users/MAHIR/OneDrive/Desktop/Database/docs/BACKEND_INTEGRATION_GUIDE.md) and [INTEGRATION_TEST_REPORT.md](file:///c:/Users/MAHIR/OneDrive/Desktop/Database/docs/INTEGRATION_TEST_REPORT.md) for:
- Full TypeScript interfaces for all 24 tables and 2 views.
- Next.js Server Action code snippets for anonymous discovery, AI brief drafting, in-platform chat, quotes, webhooks, and reviews.
- Production-ready service classes in `services/`.

---

## 10. Documentation Map

- [DATABASE_ARCHITECTURE.md](file:///c:/Users/MAHIR/OneDrive/Desktop/Database/docs/DATABASE_ARCHITECTURE.md): Complete data dictionary for 24 tables, 2 views, and Mermaid ERD.
- [DATABASE_REQUIREMENTS_MATRIX.md](file:///c:/Users/MAHIR/OneDrive/Desktop/Database/docs/DATABASE_REQUIREMENTS_MATRIX.md): Traceability matrix for all 10 marketplace specifications.
- [DATABASE_SECURITY_AUDIT.md](file:///c:/Users/MAHIR/OneDrive/Desktop/Database/docs/DATABASE_SECURITY_AUDIT.md): Forensic security audit log and penetration test evidence.
- [BACKEND_INTEGRATION_GUIDE.md](file:///c:/Users/MAHIR/OneDrive/Desktop/Database/docs/BACKEND_INTEGRATION_GUIDE.md): TypeScript and Next.js integration guide.
- [INTEGRATION_HANDOFF.md](file:///c:/Users/MAHIR/OneDrive/Desktop/Database/docs/INTEGRATION_HANDOFF.md): Teammate step-by-step setup guide.
- [PRODUCT_DECISIONS_REQUIRED.md](file:///c:/Users/MAHIR/OneDrive/Desktop/Database/docs/PRODUCT_DECISIONS_REQUIRED.md): Open business decisions (A through I) requiring founder input.
- [INTEGRATION_TEST_REPORT.md](file:///c:/Users/MAHIR/OneDrive/Desktop/Database/docs/INTEGRATION_TEST_REPORT.md): Comprehensive integration test suite report (216/216 passing).
- [FINAL_DATABASE_AUDIT.md](file:///c:/Users/MAHIR/OneDrive/Desktop/Database/docs/FINAL_DATABASE_AUDIT.md): Independent database audit report.
- [PROJECT_COMPLETION_REPORT.md](file:///c:/Users/MAHIR/OneDrive/Desktop/Database/docs/PROJECT_COMPLETION_REPORT.md): Final engineering verification report.

# Database
AI Content Creation
