-- ============================================================================
-- Query Suite: queries/marketplace_lifecycle.sql
-- Project: CreatorSphere AI
-- Description: Production SQL queries supporting complete marketplace lifecycle:
--              One-sided creator anonymity, AI brief generation, matching,
--              in-platform chat, quote pricing, contract lifecycle, payments,
--              contact unlocks, reviews, and subscription management.
-- Security:    Parameter-driven SQL ($1, $2, etc.) enforcing least-privilege RLS.
-- ============================================================================

-- ============================================================================
-- QUERY M1: Anonymous Creator Discovery (One-Sided Anonymity)
-- Returns anonymous pseudonyms for un-unlocked creators while displaying
-- verified skills, budget, and rating.
-- Parameters:
--   $1: skill_filter (TEXT, e.g. 'Runway Gen-3')
--   $2: max_budget (NUMERIC, e.g. 5000.00)
--   $3: limit (INT, default: 12)
--   $4: offset (INT, default: 0)
-- ============================================================================
SELECT 
    id,
    handle,
    display_name, -- Protected: shows 'Creator X' unless unlocked by customer
    tagline,
    skills,
    tools,
    styles,
    equipment,
    production_capabilities,
    indicative_budget_min,
    indicative_budget_max,
    currency,
    availability,
    rating,
    total_reviews,
    is_featured
FROM public.anonymous_creators
WHERE profile_visibility = 'public'
  AND ($1::text IS NULL OR skills @> ARRAY[$1::text])
  AND ($2::numeric IS NULL OR indicative_budget_min <= $2::numeric)
ORDER BY is_featured DESC, rating DESC
LIMIT $3 OFFSET $4;


-- ============================================================================
-- QUERY M2: Retrieve AI Brief Drafting Conversation History
-- Parameters:
--   $1: session_id (UUID)
--   $2: customer_id (UUID)
-- ============================================================================
SELECT 
    m.id,
    m.sender_role,
    m.content,
    m.clarification_field,
    m.created_at
FROM public.brief_ai_messages m
JOIN public.brief_ai_sessions s ON m.session_id = s.id
WHERE s.id = $1 AND s.customer_id = $2
ORDER BY m.created_at ASC;


-- ============================================================================
-- QUERY M3: Retrieve Matched Creators with Explainability for a Brief
-- Parameters:
--   $1: brief_id (UUID)
--   $2: customer_id (UUID)
-- ============================================================================
SELECT 
    bm.creator_id,
    ac.display_name,
    ac.rating,
    ac.total_reviews,
    bm.match_score,
    bm.match_reasons,
    ac.indicative_budget_min,
    ac.indicative_budget_max
FROM public.brief_matches bm
JOIN public.briefs b ON bm.brief_id = b.id
JOIN public.anonymous_creators ac ON bm.creator_id = ac.id
WHERE b.id = $1 AND b.customer_id = $2
ORDER BY bm.match_score DESC;


-- ============================================================================
-- QUERY M4: In-Platform Chat Messages with Censorship Filter
-- Only authorized participants see messages; blocked messages are filtered or flagged.
-- Parameters:
--   $1: conversation_id (UUID)
-- ============================================================================
SELECT 
    cm.id,
    cm.sender_id,
    cp.display_alias,
    cp.role AS participant_role,
    CASE 
        WHEN cm.moderation_status = 'blocked' THEN '[Message hidden by moderation policy: prohibited off-platform contact details detected]'
        ELSE cm.content
    END AS content,
    cm.moderation_status,
    cm.is_edited,
    cm.created_at
FROM public.chat_messages cm
JOIN public.chat_participants cp 
  ON cm.conversation_id = cp.conversation_id AND cm.sender_id = cp.user_id
WHERE cm.conversation_id = $1 
  AND cm.deleted_at IS NULL
ORDER BY cm.created_at ASC;


-- ============================================================================
-- QUERY M5: Creator Submits Private Project Quote
-- Parameters:
--   $1: brief_id (UUID)
--   $2: creator_id (UUID)
--   $3: creator_quote_amount (NUMERIC)
--   $4: platform_fee_rate (NUMERIC, default: 0.1500)
--   $5: scope_summary (TEXT)
--   $6: deliverables (TEXT[])
--   $7: estimated_delivery_days (INT)
--   $8: valid_days (INT, e.g. 14)
-- ============================================================================
INSERT INTO public.project_quotes (
    brief_id, creator_id, creator_quote_amount, platform_fee_rate,
    platform_fee_amount, tax_amount, customer_price_amount,
    scope_summary, deliverables, estimated_delivery_days, valid_until, status
)
VALUES (
    $1, $2, $3, COALESCE($4, 0.1500),
    ROUND($3 * COALESCE($4, 0.1500), 2), 0.00,
    $3 + ROUND($3 * COALESCE($4, 0.1500), 2),
    $5, $6, $7, CURRENT_TIMESTAMP + ($8 || ' days')::INTERVAL, 'under_review'
)
ON CONFLICT (brief_id, creator_id) DO UPDATE SET
    creator_quote_amount = EXCLUDED.creator_quote_amount,
    scope_summary = EXCLUDED.scope_summary,
    deliverables = EXCLUDED.deliverables,
    estimated_delivery_days = EXCLUDED.estimated_delivery_days,
    status = 'under_review'
RETURNING id, customer_price_amount, status, created_at;


-- ============================================================================
-- QUERY M6: Customer Views Presented Quotes (Creator Quote Masked)
-- Parameters:
--   $1: brief_id (UUID)
-- ============================================================================
SELECT 
    v.id AS quote_id,
    v.brief_id,
    v.creator_id,
    ac.display_name AS creator_alias,
    v.customer_price_amount,
    v.currency,
    v.scope_summary,
    v.deliverables,
    v.estimated_delivery_days,
    v.valid_until,
    v.status
FROM public.customer_quotes_view v
JOIN public.anonymous_creators ac ON v.creator_id = ac.id
WHERE v.brief_id = $1;


-- ============================================================================
-- QUERY M7: Customer Accepts Quote & Creates Formal Contract
-- Parameters:
--   $1: quote_id (UUID)
--   $2: customer_id (UUID)
-- ============================================================================
WITH accepted_quote AS (
    UPDATE public.project_quotes
    SET status = 'accepted'
    WHERE id = $1
      AND brief_id IN (SELECT id FROM public.briefs WHERE customer_id = $2)
    RETURNING id, brief_id, creator_id, customer_price_amount, creator_quote_amount, platform_fee_amount, currency
)
INSERT INTO public.projects (
    brief_id, quote_id, customer_id, creator_id, title,
    agreed_amount, creator_earnings, platform_fee, currency, status
)
SELECT 
    aq.brief_id, aq.id, $2, aq.creator_id, 
    'CreatorSphere Contract: Brief ' || substring(aq.brief_id::text, 1, 8),
    aq.customer_price_amount, aq.creator_quote_amount, aq.platform_fee_amount, aq.currency,
    'offer_accepted'
FROM accepted_quote aq
RETURNING id, status, agreed_amount, created_at;


-- ============================================================================
-- QUERY M8: Verify Contact Unlock & Retrieve Creator Private Contacts
-- Parameters:
--   $1: customer_id (UUID)
--   $2: creator_id (UUID)
-- ============================================================================
SELECT 
    c.id AS creator_id,
    c.handle,
    cpc.legal_name,
    cpc.contact_email,
    cpc.phone_number,
    cpc.billing_address,
    cu.unlocked_at,
    cu.status AS unlock_status
FROM public.creators c
JOIN public.creator_private_contacts cpc ON c.id = cpc.creator_id
JOIN public.contact_unlocks cu ON c.id = cu.creator_id AND cu.customer_id = $1
WHERE c.id = $2 AND cu.status = 'active';


-- ============================================================================
-- QUERY M9: Submit Verified Review on Completed Project
-- Parameters:
--   $1: project_id (UUID)
--   $2: customer_id (UUID)
--   $3: creator_id (UUID)
--   $4: rating (NUMERIC, 1.00 - 5.00)
--   $5: review_text (TEXT)
-- ============================================================================
INSERT INTO public.reviews (
    project_id, customer_id, creator_id, rating, review_text, moderation_status
)
VALUES (
    $1, $2, $3, $4, $5, 'published'
)
RETURNING id, rating, moderation_status, created_at;


-- ============================================================================
-- QUERY M10: Admin Financial Ledger Reconciliation Audit
-- ============================================================================
SELECT 
    p.id AS payment_id,
    p.customer_id,
    p.amount AS total_charged,
    p.currency,
    p.status AS payment_status,
    fl.entry_type,
    fl.account,
    fl.amount AS ledger_amount,
    fl.created_at AS booked_at
FROM public.payments p
JOIN public.financial_ledger fl ON p.id = fl.payment_id
ORDER BY fl.created_at DESC;
