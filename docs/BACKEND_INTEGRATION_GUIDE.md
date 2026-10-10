# CreatorSphere AI — Backend & Frontend Integration Guide

This guide is designed for engineering teammates integrating the PostgreSQL database with the **Next.js (App Router)** and **TypeScript** application.

---

## 1. Setup & Environment Variables

Install the official Supabase JavaScript client:
```bash
npm install @supabase/supabase-js
```

Create `.env.local` in your Next.js project root:
```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project-id.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9... # Backend/Webhooks ONLY!
```

---

## 2. Supabase Client Initialization

Create `lib/supabaseClient.ts`:

```typescript
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

// Client for browser / React Server Components with RLS enforcement
export const supabase = createClient(supabaseUrl, supabaseAnonKey);

// Administrative client for trusted backend webhooks (Stripe / AI processing)
export const supabaseAdmin = createClient(
  supabaseUrl, 
  process.env.SUPABASE_SERVICE_ROLE_KEY!,
  { auth: { persistSession: false } }
);
```

---

## 3. TypeScript Interfaces

```typescript
export interface User {
  id: string;
  email: string;
  full_name: string;
  role: 'customer' | 'creator' | 'both' | 'admin' | 'moderator';
  avatar_url: string | null;
  bio: string | null;
  created_at: string;
  updated_at: string;
}

export interface AnonymousCreator {
  id: string;
  handle: string;
  display_name: string; // Masked as 'Creator XXXXXX' unless unlocked by customer
  tagline: string | null;
  skills: string[];
  tools: string[];
  styles: string[];
  content_types: string[];
  equipment: string[];
  production_capabilities: string[];
  indicative_budget_min: number;
  indicative_budget_max: number;
  currency: string;
  availability: 'available' | 'busy' | 'unavailable';
  rating: number;
  total_reviews: number;
  is_featured: boolean;
}

export interface CreatorPrivateContact {
  creator_id: string;
  legal_name: string | null;
  contact_email: string;
  phone_number: string | null;
  billing_address: string | null;
  created_at: string;
}

export interface BriefAiSession {
  id: string;
  customer_id: string;
  brief_id: string | null;
  session_title: string;
  status: 'active' | 'completed' | 'abandoned';
  created_at: string;
}

export interface BriefAiMessage {
  id: string;
  session_id: string;
  sender_role: 'customer' | 'assistant' | 'system';
  content: string;
  clarification_field: string | null;
  model_metadata: Record<string, any>;
  created_at: string;
}

export interface ChatConversation {
  id: string;
  project_id: string | null;
  brief_id: string | null;
  created_by: string;
  status: 'active' | 'archived' | 'blocked';
  created_at: string;
}

export interface ChatMessage {
  id: string;
  conversation_id: string;
  sender_id: string;
  content: string;
  moderation_status: 'allowed' | 'blocked' | 'redacted' | 'awaiting_moderation' | 'approved' | 'appeal_submitted' | 'appeal_resolved';
  is_edited: boolean;
  deleted_at: string | null;
  created_at: string;
}

export interface ProjectQuote {
  id: string;
  brief_id: string;
  creator_id: string;
  creator_quote_amount: number;
  platform_fee_rate: number;
  platform_fee_amount: number;
  tax_amount: number;
  customer_price_amount: number;
  currency: string;
  scope_summary: string;
  deliverables: string[];
  estimated_delivery_days: number;
  revision_count: number;
  valid_until: string;
  status: 'submitted' | 'under_review' | 'presented_to_customer' | 'accepted' | 'declined' | 'expired' | 'withdrawn';
}

export interface ProjectContract {
  id: string;
  brief_id: string;
  quote_id: string;
  customer_id: string;
  creator_id: string;
  title: string;
  agreed_amount: number;
  creator_earnings: number;
  platform_fee: number;
  currency: string;
  status: 'draft' | 'brief_approved' | 'matching' | 'negotiation' | 'offer_accepted' | 'awaiting_payment' | 'in_progress' | 'submitted' | 'revision_requested' | 'completed' | 'cancelled' | 'disputed';
  started_at: string | null;
  completed_at: string | null;
}

export interface PaymentRecord {
  id: string;
  project_id: string | null;
  quote_id: string | null;
  customer_id: string;
  provider: 'stripe' | 'razorpay' | 'mock_gateway';
  provider_payment_intent_id: string | null;
  amount: number;
  currency: string;
  status: 'pending' | 'requires_action' | 'succeeded' | 'failed' | 'refunded' | 'disputed';
  idempotency_key: string;
}

export interface ProjectReview {
  id: string;
  project_id: string;
  customer_id: string;
  creator_id: string;
  rating: number; // 1.00 - 5.00
  review_text: string;
  moderation_status: 'published' | 'flagged' | 'hidden';
  created_at: string;
}
```

---

## 4. Next.js Integration Patterns

### 4.1 Anonymous Creator Discovery (Server Action)
```typescript
'use server';

import { supabase } from '@/lib/supabaseClient';
import { AnonymousCreator } from '@/types/database';

export async function getAnonymousCreators(filters: {
  skill?: string;
  maxBudget?: number;
  limit?: number;
  offset?: number;
}): Promise<AnonymousCreator[]> {
  let query = supabase
    .from('anonymous_creators')
    .select('*')
    .order('is_featured', { ascending: false })
    .order('rating', { ascending: false })
    .range(filters.offset || 0, (filters.offset || 0) + (filters.limit || 12) - 1);

  if (filters.skill) {
    query = query.contains('skills', [filters.skill]);
  }
  if (filters.maxBudget) {
    query = query.lte('indicative_budget_min', filters.maxBudget);
  }

  const { data, error } = await query;
  if (error) throw new Error(error.message);
  return data as AnonymousCreator[];
}
```

---

### 4.2 Interactive AI Brief Chat Session
```typescript
'use server';

import { supabase } from '@/lib/supabaseClient';

export async function sendAiBriefMessage(sessionId: string, userMessage: string) {
  // 1. Record customer message
  const { error: insertErr } = await supabase
    .from('brief_ai_messages')
    .insert({
      session_id: sessionId,
      sender_role: 'customer',
      content: userMessage
    });
  if (insertErr) throw new Error(insertErr.message);

  // 2. Call your LLM backend (e.g. Gemini 1.5 Pro) to analyze and reply
  // ... LLM call here ...
  const aiReply = "Got it! For product commercials, 9:16 vertical video works best for Instagram Reels. What duration are you aiming for?";

  // 3. Save assistant message
  const { data: reply, error: replyErr } = await supabase
    .from('brief_ai_messages')
    .insert({
      session_id: sessionId,
      sender_role: 'assistant',
      content: aiReply,
      clarification_field: 'duration_seconds'
    })
    .select()
    .single();

  if (replyErr) throw new Error(replyErr.message);
  return reply;
}
```

---

### 4.3 In-Platform Messaging with Real-Time Moderation
```typescript
'use server';

import { supabase } from '@/lib/supabaseClient';

export async function sendChatMessage(conversationId: string, content: string) {
  // 1. Regex check for contact information leakage (emails, phone numbers)
  const phoneRegex = /(\+?\d{1,4}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}/g;
  const emailRegex = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g;

  const hasPhone = phoneRegex.test(content);
  const hasEmail = emailRegex.test(content);
  const isFlagged = hasPhone || hasEmail;

  // 2. Insert message with moderation status
  const { data: message, error } = await supabase
    .from('chat_messages')
    .insert({
      conversation_id: conversationId,
      content: content,
      moderation_status: isFlagged ? 'blocked' : 'allowed'
    })
    .select()
    .single();

  if (error) throw new Error(error.message);

  // 3. If flagged, record moderation log entry
  if (isFlagged) {
    await supabase.from('message_moderation_logs').insert({
      message_id: message.id,
      flagged_by: 'system_regex',
      detection_category: hasEmail ? 'email' : 'phone_number',
      redacted_snippet: content,
      moderation_decision: 'blocked'
    });
  }

  return message;
}
```

---

### 4.4 Webhook Handler: Payment Confirmation & Contact Unlock
```typescript
// app/api/webhooks/stripe/route.ts
import { NextResponse } from 'next/server';
import { supabaseAdmin } from '@/lib/supabaseClient';

export async function POST(req: Request) {
  const body = await req.json();
  const { payment_intent_id, project_id, customer_id, creator_id, amount } = body;

  // 1. Confirm payment state via service_role client
  const { data: payment, error: payErr } = await supabaseAdmin
    .from('payments')
    .update({ status: 'succeeded' })
    .eq('provider_payment_intent_id', payment_intent_id)
    .select()
    .single();

  if (payErr) return NextResponse.json({ error: payErr.message }, { status: 400 });

  // 2. Record double-entry ledger entries
  await supabaseAdmin.from('financial_ledger').insert([
    {
      payment_id: payment.id,
      entry_type: 'payment_received',
      account: 'escrow_holding',
      amount: amount
    },
    {
      payment_id: payment.id,
      entry_type: 'platform_fee',
      account: 'platform_revenue',
      amount: amount * 0.15
    }
  ]);

  // 3. Unlock creator private contacts
  await supabaseAdmin.from('contact_unlocks').insert({
    customer_id: customer_id,
    creator_id: creator_id,
    project_id: project_id,
    payment_id: payment.id,
    status: 'active'
  });

  // 4. Advance project contract to in_progress
  await supabaseAdmin
    .from('projects')
    .update({ status: 'in_progress' })
    .eq('id', project_id);

  return NextResponse.json({ success: true });
}
```

---

### 4.5 Submitting Verified Project Review
```typescript
'use server';

import { supabase } from '@/lib/supabaseClient';

export async function submitProjectReview(params: {
  projectId: string;
  creatorId: string;
  rating: number;
  reviewText: string;
}) {
  const { data, error } = await supabase
    .from('reviews')
    .insert({
      project_id: params.projectId,
      creator_id: params.creatorId,
      rating: params.rating,
      review_text: params.reviewText,
      moderation_status: 'published'
    })
    .select()
    .single();

  if (error) throw new Error(error.message);
  // Note: creator.rating and total_reviews are automatically recalculated by database trigger!
  return data;
}
```

---

## 5. Reusable Application Services (`services/`)

The repository includes tested, framework-agnostic application services that can be imported directly into Next.js Route Handlers, Express controllers, or background workers:

1. **`services/moderation_engine.js` (`ModerationEngine`)**:
   - Multi-layered deterministic pattern detection for phone numbers, email addresses, obfuscated text, messaging handles, and off-platform payment links.
   - Contextual allowlist (`drive.google.com`, `frame.io`, `figma.com`, etc.) and false-positive prevention.
2. **`services/ai_brief_service.js` (`AiBriefService`)**:
   - AI conversational dialogue tracker, requirement extraction, and mandatory customer sign-off enforcement.
3. **`services/creator_matching_service.js` (`CreatorMatchingService`)**:
   - Multi-criteria recommendation engine matching skills, budgets, and styles with transparent explainability reasons.
4. **`services/quote_service.js` (`QuoteService`)**:
   - Creator quote submission, configurable platform fee markup (default 15%), customer-facing pseudonym presentation, and quote acceptance.
5. **`services/payment_webhook_service.js` (`PaymentWebhookService`)**:
   - Cryptographic HMAC-SHA256 signature verification, idempotency checking, double-entry financial ledger accounting (`escrow_holding`, `platform_revenue`), and verified contact unlock activation.
6. **`services/project_lifecycle_service.js` (`ProjectLifecycleService`)**:
   - Enforces DAG contract state machine transitions across all 12 project statuses (`offer_accepted` -> `in_progress` -> `submitted` -> `completed`).
7. **`services/review_service.js` (`ReviewService`)**:
   - Submits verified reviews on completed projects and verifies automatic creator rating recalculation.
