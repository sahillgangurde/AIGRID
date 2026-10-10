# CreatorSphere AI — Open Product Decisions & Business Rules

This document outlines key open commercial, legal, and operational business decisions that must be resolved by product leadership and founders.

To maintain engineering velocity without making unauthorized commercial commitments, the database schema and application services use safe, configurable defaults.

---

## Decision A: Platform Fee Model & Take Rate

- **The Question**: What platform take rate should CreatorSphere AI charge, and should the fee be fixed, tiered by creator subscription status, or sliding based on transaction volume?
- **Why It Matters**: Directly dictates platform unit economics, marketplace liquidity, creator retention, and competitiveness against platforms like Upwork (10%) or Fiverr (20%).
- **The Options**:
  1. *Flat Percentage*: A standard 15% platform take rate charged on all transactions.
  2. *Tiered by Subscription*: 15% for Free tier creators, reduced to 8%–10% for Pro or Agency subscribers.
  3. *Split Fee*: 10% charged to the creator + 5% client processing fee charged to the customer.
- **Current Implementation Assumption**: Configurable default rate of **15.00%** (`0.1500`) stored as a column on `public.project_quotes.platform_fee_rate`.
- **Risks of Each Option**:
  - A flat 15% may deter top-tier cinematic creators who demand higher margins.
  - A split fee complicates customer checkout display.
- **Dependent Code & Schema**:
  - `public.project_quotes` (`platform_fee_rate`, `platform_fee_amount`).
  - Trigger `public.enforce_quote_pricing_integrity()`.
  - [`services/quote_service.js`](file:///c:/Users/MAHIR/OneDrive/Desktop/Database/services/quote_service.js).

---

## Decision B: Initial Payment Structure (Milestone vs Full Escrow)

- **The Question**: Is the customer charged the full contract amount up front into platform escrow, or is payment split into milestones (e.g. 50% upfront deposit to unlock contact, 50% upon final delivery)?
- **Why It Matters**: Impacts customer checkout friction and financial risk during creative iterations.
- **The Options**:
  1. *Full Escrow*: 100% of the project price is authorized and captured before project initiation (`in_progress`).
  2. *Milestone Escrow*: 50% initial milestone deposit captures contact unlock and pre-production; remaining 50% captured upon delivery.
  3. *Contact-Unlock Fee Only*: Customer pays a small access fee ($29), with project payment handled separately.
- **Current Implementation Assumption**: Full agreed contract amount (`agreed_amount`) is charged via payment intent before advancing the project to `in_progress`.
- **Risks**:
  - Full escrow requires high customer trust for multi-thousand dollar contracts.
  - Milestone deposits require managing secondary authorization failures when final work is submitted.
- **Dependent Code & Schema**:
  - `public.projects` (`agreed_amount`, `status`).
  - `public.payments` (`amount`, `status`).
  - [`services/payment_webhook_service.js`](file:///c:/Users/MAHIR/OneDrive/Desktop/Database/services/payment_webhook_service.js).

---

## Decision C: Initial Payment Refundability & Cooling-Off Period

- **The Question**: Under what conditions is an initial payment refundable if the customer cancels before work starts?
- **Why It Matters**: Protects customers against unresponsive creators while protecting creators against frivolous cancellations.
- **The Options**:
  1. *100% Refundable Before Pre-Production*: Full refund if cancelled within 24 hours and before the creator begins filming.
  2. *Non-Refundable Platform Fee*: The creator share is refunded, but platform booking fees ($50) are retained.
  3. *Grace Period*: 48-hour cooling-off window.
- **Current Implementation Assumption**: Admin or service role can issue refunds (`charge.refunded` webhook), updating payment status to `refunded` and booking reversing entries in `financial_ledger`.
- **Risks**:
  - Permitting unconditional refunds after contact details have been unlocked creates an exploit vector where customers get creator contacts for free and negotiate off-platform.
- **Dependent Code & Schema**:
  - `public.financial_ledger` (`entry_type = 'refund'`).
  - `public.payments` (`status = 'refunded'`).
  - [`services/payment_webhook_service.js`](file:///c:/Users/MAHIR/OneDrive/Desktop/Database/services/payment_webhook_service.js).

---

## Decision D: Mid-Project Refund Calculations

- **The Question**: If a project is cancelled or disputed after rough cuts are delivered, how are funds split?
- **Why It Matters**: High-cost video productions involve irreversible labor (filming, location rental, rendering compute).
- **The Options**:
  1. *Prorated Milestone Split*: Creator receives payment for completed storyboard/rough cuts; remainder refunded.
  2. *Discretionary Platform Arbitration*: Admin manual determination based on chat logs and deliverables.
  3. *Kill-Fee Clause*: Guaranteed 30% creator kill-fee once project is marked `in_progress`.
- **Current Implementation Assumption**: Projects entering `disputed` status require administrator resolution to transition to either `completed` or `cancelled`.
- **Risks**:
  - Lack of a defined kill-fee policy leads to creator dissatisfaction on complex video shoots.
- **Dependent Code & Schema**:
  - `public.projects` (status: `disputed`).
  - Trigger `public.enforce_project_status_transitions()`.
  - [`services/project_lifecycle_service.js`](file:///c:/Users/MAHIR/OneDrive/Desktop/Database/services/project_lifecycle_service.js).

---

## Decision E: Creator Compensation Upon Client Cancellation

- **The Question**: If a client abruptly cancels an active project without creator fault, does the creator receive compensation?
- **Why It Matters**: Legal liability under creative services contracts.
- **The Options**:
  1. *Full Agreed Payout*: Creator receives full contracted earnings if client cancels unilaterally.
  2. *Time & Expense Incurred*: Payout based on logged hours or equipment receipts.
  3. *Zero Compensation (Buyer-Favored)*: Full refund to customer (creates extreme creator flight risk).
- **Current Implementation Assumption**: Cancellation is enforced by contract status transition rules; compensation payout requires admin ledger entry.
- **Dependent Code & Schema**:
  - `public.financial_ledger` (`entry_type = 'creator_payout'`).

---

## Decision F: Contact-Unlock Behavior Post-Refund or Dispute

- **The Question**: When a project is refunded, should the `contact_unlocks` record be marked `revoked`, and what legal terms govern off-platform interactions?
- **Why It Matters**: Technical access can be revoked in the database, but information already displayed on screen cannot be un-seen or un-copied.
- **The Options**:
  1. *Automated Revocation*: Set `contact_unlocks.status = 'revoked'`, terminating future database queries for private contacts.
  2. *Preserved for Legal Records*: Keep unlock record active with an audit flag so the parties can resolve ongoing IP or NDA issues.
- **Current Implementation Assumption**: `public.contact_unlocks` supports status `'revoked'` and `'refunded'`.
- **Risks**:
  - Revocation provides a false sense of data eradication if the customer already exported or emailed the creator.
- **Dependent Code & Schema**:
  - `public.contact_unlocks` (`status IN ('active', 'revoked', 'refunded')`).
  - Function `public.has_unlocked_creator()`.

---

## Decision G: Creator Subscription Pricing & Entitlement Quotas

- **The Question**: What features are gated behind paid creator subscriptions (`starter`, `pro`, `agency`) versus the free plan?
- **Why It Matters**: Core SaaS revenue stream alongside marketplace transaction take rates.
- **The Options**:
  1. *Pitch Limits*: Free: 5 pitches/month; Pro ($29/mo): 30 pitches/month; Agency ($99/mo): Unlimited.
  2. *Take Rate Discount*: Pro subscribers pay 8% platform fee instead of 15%.
  3. *Featured Profile Placement*: Higher algorithm ranking in `brief_matches`.
- **Current Implementation Assumption**: `public.creator_subscriptions` tracks `tier IN ('free', 'starter', 'pro', 'agency')` and `billing_cycle`, but does not enforce arbitrary quotas without product confirmation.
- **Dependent Code & Schema**:
  - `public.creator_subscriptions`.
  - Trigger `public.protect_creator_subscription_updates()`.

---

## Decision H: Tax Calculation & Invoicing Responsibility

- **The Question**: Is CreatorSphere AI responsible for collecting and remitting GST/VAT, or are creators considered independent contractors responsible for their own taxes?
- **Why It Matters**: International tax compliance (Stripe Tax, Avalara, IRS 1099-K, Indian GST e-invoicing).
- **The Options**:
  1. *Merchant of Record (MoR)*: Platform collects tax from customers and remits directly (e.g. Paddle / FastSpring model).
  2. *Pure Marketplace / Platform Intermediary*: Platform charges tax only on its 15% platform fee service; creator issues direct invoice to customer.
- **Current Implementation Assumption**: `tax_amount` defaults to `0.00` on quotes.
- **Dependent Code & Schema**:
  - `public.project_quotes.tax_amount`.
  - `public.payments.currency`.

---

## Decision I: Contractual Role of the Platform

- **The Question**: Does the platform enter the contract as a party (tri-partite agreement), or is the project contract strictly between customer and creator?
- **Why It Matters**: IP ownership transfer warranties and indemnification against copyright infringement in AI-generated video assets.
- **The Options**:
  1. *Bilateral Contract*: Contract is between Customer and Creator; Platform is an escrow agent and facilitator.
  2. *Tripartite Agreement*: Platform guarantees work quality and holds copyright licenses temporarily.
- **Current Implementation Assumption**: `public.projects` explicitly stores `customer_id` and `creator_id` as direct principals.
- **Dependent Code & Schema**:
  - `public.projects` (`customer_id`, `creator_id`, `usage_rights`).
