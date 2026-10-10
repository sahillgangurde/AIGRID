# CreatorSphere AI — Database Integration Handoff Guide

> **Target Audience**: Frontend Engineers, Backend Engineers, Full-Stack Developers, and Hackathon Teammates.  
> **Status**: Verified Locally (220 Automated Tests Passing) • Ready for Dev Supabase Deployment  
> **Version**: 2.0.0 (October 2026 — Marketplace Evolution)

---

## 1. What the Database Provides

The CreatorSphere AI database layer is a hardened **PostgreSQL 15+** architecture configured for **Supabase**. It provides:

1. **Relational Marketplace Foundations**: 24 interconnected tables and 2 secure views covering user roles, creator portfolios, AI brief sessions, in-platform chat, quote pricing, contracts, escrow payments, verified reviews, and subscriptions.
2. **One-Sided Anonymity**:
   - `anonymous_creators` view masks creator identities (`Creator XXXXXX`) during discovery and quoting.
   - Private contact details (`creator_private_contacts`) are securely revealed ONLY upon a verified payment unlock.
3. **In-Platform Chat & Content Moderation**:
   - Threaded messaging with participant pseudonym aliases.
   - Automated regex & AI moderation flagging prohibited contact info (`message_moderation_logs`).
   - Ordinary senders cannot self-clear moderation blocks or un-delete messages.
4. **Transparent & Fair Financial Engine**:
   - Private creator quotes (`project_quotes`) and customer presented pricing (`customer_quotes_view`).
   - Automated 15% platform fee calculation.
   - Idempotent payment processing (`payments`) and double-entry accounting ledger (`financial_ledger`).
5. **Contract Lifecycle Protection**:
   - Contract projects (`projects`) governed by strict DAG state-transition triggers preventing status skipping or retroactive fee tampering.
6. **Verified Reviews & Automatic Rating Updates**:
   - Single review per completed project (`reviews`).
   - Creator ratings and review counts automatically recalculated by database triggers upon review publication.

---

## 2. Table Summary

| # | Table Name | Business Domain | Access Rules & Key Triggers |
|---|---|---|---|
| 1 | **`public.users`** | Core account profiles (`auth.users`) | Guarded by `protect_user_profile` against role/email tampering. |
| 2 | **`public.creators`** | Public creator profiles & capabilities | Rating guarded by `protect_creator_reputation`. |
| 3 | **`public.portfolio_items`** | Showcase video samples | Guarded by `protect_portfolio_verification`. |
| 4 | **`public.briefs`** | Customer video requirements | Guarded by `prevent_active_brief_deletion`. |
| 5 | **`public.enquiries`** | Direct customer-creator messages | Guarded by `enforce_enquiry_status_transitions`. |
| 6 | **`public.creator_interests`** | Creator pitches & bids on briefs | Guarded by `enforce_pitch_update_rules`. |
| 7 | **`public.verification_signals`** | Badges & proof credentials | Protected against unauthorized self-awarding. |
| 8 | **`public.creator_private_contacts`** | Real names, emails, phones, addresses | Accessible ONLY via `has_unlocked_creator()` RLS gate. |
| 9 | **`public.contact_unlocks`** | Authorized contact unlocks | Created ONLY with verified payment or `service_role`. |
| 10 | **`public.brief_ai_sessions`** | AI brief drafting sessions | Private to session customer. |
| 11 | **`public.brief_ai_messages`** | Clarification chat messages | Private to session customer. |
| 12 | **`public.brief_revisions`** | Versioned brief snapshot history | Append-only revision records. |
| 13 | **`public.brief_matches`** | Explainable AI matching scores | Visible to brief customer. |
| 14 | **`public.chat_conversations`** | In-platform chat channels | Participant-scoped via `is_chat_participant()`. |
| 15 | **`public.chat_participants`** | Chat members with pseudonym aliases | UNIQUE(`conversation_id`, `user_id`). |
| 16 | **`public.chat_messages`** | Messages with moderation status | Guarded by `protect_chat_message_moderation`. |
| 17 | **`public.chat_attachments`** | Uploaded video files & storyboards | Restricted to conversation members. |
| 18 | **`public.message_moderation_logs`** | Contact information censorship log | Visible to moderators and message sender. |
| 19 | **`public.project_quotes`** | Creator proposals with fees | Guarded by `enforce_quote_pricing_integrity`. |
| 20 | **`public.projects`** | Binding contracts & state machine | Guarded by `enforce_project_status_transitions`. |
| 21 | **`public.payments`** | Gateway payments | Guarded by `protect_payment_state` (webhook only). |
| 22 | **`public.financial_ledger`** | Double-entry journal | Restricted to `admin` and `service_role`. |
| 23 | **`reviews`** | Verified completed project ratings | Guarded by `validate_and_apply_review`. |
| 24 | **`creator_subscriptions`** | Monetization tiers (`pro`, `agency`) | Guarded by `protect_creator_subscription_updates`. |
| V1 | **`anonymous_creators`** | Secure View for masked discovery | Public discovery. |
| V2 | **`customer_quotes_view`** | Secure View for customer pricing | Customer quote presentation. |

---

## 3. How to Apply Migrations to Supabase Cloud

When deploying to your cloud Supabase project:

1. **Open Supabase Web Console** -> Select project -> Click **SQL Editor** (`>_`).
2. **Execute Migration 001**:
   - File: [`supabase/migrations/20261009120000_001_initial_schema.sql`](file:///c:/Users/MAHIR/OneDrive/Desktop/Database/supabase/migrations/20261009120000_001_initial_schema.sql).
   - Creates initial 7 tables, functions, triggers, and GIN indexes.
3. **Execute Migration 002**:
   - File: [`supabase/migrations/20261009120001_002_security_policies.sql`](file:///c:/Users/MAHIR/OneDrive/Desktop/Database/supabase/migrations/20261009120001_002_security_policies.sql).
   - Enables RLS policies for initial schema.
4. **Execute Migration 003**:
   - File: [`supabase/migrations/20261009130000_003_marketplace_evolution.sql`](file:///c:/Users/MAHIR/OneDrive/Desktop/Database/supabase/migrations/20261009130000_003_marketplace_evolution.sql).
   - Creates the 17 new marketplace tables, 2 views, chat moderation triggers, quotes, contracts, and ledger.
5. **Execute Seed Data**:
   - File: [`supabase/seed.sql`](file:///c:/Users/MAHIR/OneDrive/Desktop/Database/supabase/seed.sql).
   - Populates complete marketplace seed data across all 24 tables.

---

## 4. Query Reference for Teammates

All production queries are organized across 4 dedicated files:
- [`queries/creator_search.sql`](file:///c:/Users/MAHIR/OneDrive/Desktop/Database/queries/creator_search.sql): Marketplace creator search with GIN array filtering.
- [`queries/briefs_and_enquiries.sql`](file:///c:/Users/MAHIR/OneDrive/Desktop/Database/queries/briefs_and_enquiries.sql): Briefs, creator pitches, and 1-to-1 enquiries.
- [`queries/analytics_and_admin.sql`](file:///c:/Users/MAHIR/OneDrive/Desktop/Database/queries/analytics_and_admin.sql): Admin KPIs, top skills in demand, and audit logs.
- [`queries/marketplace_lifecycle.sql`](file:///c:/Users/MAHIR/OneDrive/Desktop/Database/queries/marketplace_lifecycle.sql): Complete marketplace queries M1–M10 (anonymous discovery, chat messages, quotes, contracts, contact unlocks, and reviews).

---

## 5. Local Testing & Verification

Run all test suites locally:
```powershell
npm test
# Or on Windows PowerShell:
npm.cmd test
```
Result: **220 automated tests passing across 4 suites**:
- **117** static schema and SQL syntax assertions (`validate_sql_syntax.js`).
- **19** real PostgreSQL 18 engine execution & DDL tests (`test_live_pg_execution.js`).
- **38** adversarial penetration and hardening tests (`security_adversarial_test.js`).
- **46** full marketplace application lifecycle tests (`marketplace_integration_test.js`).

Detailed guides:
- [INTEGRATION_TEST_REPORT.md](file:///c:/Users/MAHIR/OneDrive/Desktop/Database/docs/INTEGRATION_TEST_REPORT.md)
- [BACKEND_INTEGRATION_GUIDE.md](file:///c:/Users/MAHIR/OneDrive/Desktop/Database/docs/BACKEND_INTEGRATION_GUIDE.md)
- [PRODUCT_DECISIONS_REQUIRED.md](file:///c:/Users/MAHIR/OneDrive/Desktop/Database/docs/PRODUCT_DECISIONS_REQUIRED.md)
