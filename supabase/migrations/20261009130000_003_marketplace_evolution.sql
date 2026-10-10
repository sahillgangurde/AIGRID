-- ============================================================================
-- Migration: 20261009130000_003_marketplace_evolution.sql
-- Project: CreatorSphere AI
-- Description: Complete Marketplace Evolution:
--              1. Role expansion (admin, moderator) & signup protection.
--              2. Creator production capabilities, equipment & private contacts.
--              3. One-sided creator anonymity engine & secure views.
--              4. AI brief sessions, clarification messages & brief versioning.
--              5. Creator matching snapshot engine.
--              6. In-platform chat, soft-deletes, & contact censorship moderation.
--              7. Creator quotes, customer pricing & fee structure.
--              8. Formal project contracts & validated lifecycle state machine.
--              9. Idempotent payments, double-entry financial ledger & contact unlocks.
--              10. Verified project reviews & automatic rating recalculations.
--              11. Creator subscription tiers & entitlement tracking.
-- ============================================================================

-- ============================================================================
-- 1. USER ROLES & SIGNUP HARDENING
-- ============================================================================

-- Expand users.role check constraint to include admin and moderator
ALTER TABLE public.users DROP CONSTRAINT IF EXISTS users_role_check;
ALTER TABLE public.users ADD CONSTRAINT users_role_check 
    CHECK (role IN ('customer', 'creator', 'both', 'admin', 'moderator'));

-- Update handle_new_user to ensure self-signup can NEVER claim 'admin' or 'moderator'
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
DECLARE
    v_role TEXT;
BEGIN
    v_role := COALESCE(NEW.raw_user_meta_data->>'role', 'customer');
    -- Disallow self-assigning admin or moderator during public signup
    IF v_role NOT IN ('customer', 'creator', 'both') THEN
        v_role := 'customer';
    END IF;

    INSERT INTO public.users (id, email, full_name, avatar_url, role)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', split_part(NEW.email, '@', 1)),
        NEW.raw_user_meta_data->>'avatar_url',
        v_role
    )
    ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp;

-- ============================================================================
-- 2. CREATOR PROFILE EXPANSION & SEPARATION OF PRIVATE CONTACTS
-- ============================================================================

-- Add equipment, capabilities, service area, and visibility to creators
ALTER TABLE public.creators ADD COLUMN IF NOT EXISTS equipment TEXT[] DEFAULT '{}';
ALTER TABLE public.creators ADD COLUMN IF NOT EXISTS production_capabilities TEXT[] DEFAULT '{}';
ALTER TABLE public.creators ADD COLUMN IF NOT EXISTS preferred_project_types TEXT[] DEFAULT '{}';
ALTER TABLE public.creators ADD COLUMN IF NOT EXISTS service_area TEXT DEFAULT 'global';
ALTER TABLE public.creators ADD COLUMN IF NOT EXISTS profile_visibility TEXT NOT NULL DEFAULT 'public' 
    CHECK (profile_visibility IN ('public', 'unlisted', 'private'));
ALTER TABLE public.creators ADD COLUMN IF NOT EXISTS avatar_url TEXT;

-- Backfill creator avatar URLs from public.users preserving existing non-null avatars
UPDATE public.creators c
SET avatar_url = u.avatar_url
FROM public.users u
WHERE c.user_id = u.id 
  AND c.avatar_url IS NULL 
  AND u.avatar_url IS NOT NULL;

-- Separate private contact information into an isolated table
-- This prevents accidental identity/contact leakage during public creator discovery
CREATE TABLE IF NOT EXISTS public.creator_private_contacts (
    creator_id UUID PRIMARY KEY REFERENCES public.creators(id) ON DELETE CASCADE,
    legal_name TEXT,
    contact_email TEXT NOT NULL,
    phone_number TEXT,
    billing_address TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 3. ONE-SIDED CREATOR ANONYMITY ENGINE
-- ============================================================================

-- Forward-declare contact_unlocks table structure (defined in section 9)
CREATE TABLE IF NOT EXISTS public.contact_unlocks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    creator_id UUID NOT NULL REFERENCES public.creators(id) ON DELETE CASCADE,
    project_id UUID,
    payment_id UUID,
    unlocked_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'revoked', 'refunded')),
    UNIQUE (customer_id, creator_id)
);

-- Helper function: checks if a customer has unlocked a creator's contact details
CREATE OR REPLACE FUNCTION public.has_unlocked_creator(p_customer_id UUID, p_creator_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    IF p_customer_id IS NULL OR p_creator_id IS NULL THEN
        RETURN FALSE;
    END IF;
    RETURN EXISTS (
        SELECT 1 
        FROM public.contact_unlocks 
        WHERE customer_id = p_customer_id 
          AND creator_id = p_creator_id 
          AND status = 'active'
    );
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path = public, pg_temp;

-- Anonymous creator discovery view: Mask personal identity unless unlocked
DROP VIEW IF EXISTS public.anonymous_creators;
CREATE OR REPLACE VIEW public.anonymous_creators WITH (security_invoker = true) AS
SELECT 
    c.id,
    c.handle,
    CASE 
        WHEN auth.uid() IS NOT NULL AND public.has_unlocked_creator(auth.uid(), c.id) THEN c.display_name
        ELSE 'Creator ' || UPPER(SUBSTRING(c.id::text, 1, 6))
    END AS display_name,
    c.avatar_url,
    c.tagline,
    c.skills,
    c.tools,
    c.styles,
    c.content_types,
    c.equipment,
    c.production_capabilities,
    c.preferred_project_types,
    c.indicative_budget_min,
    c.indicative_budget_max,
    c.currency,
    c.availability,
    c.experience_years,
    c.service_area,
    c.rating,
    c.total_reviews,
    c.is_featured,
    c.profile_visibility
FROM public.creators c
WHERE c.profile_visibility = 'public';

-- ============================================================================
-- 4. AI REQUIREMENT COLLECTION & BRIEF GENERATION
-- ============================================================================

-- Enhance briefs with professional production fields
ALTER TABLE public.briefs ADD COLUMN IF NOT EXISTS deliverables TEXT[] DEFAULT '{}';
ALTER TABLE public.briefs ADD COLUMN IF NOT EXISTS required_equipment TEXT[] DEFAULT '{}';
ALTER TABLE public.briefs ADD COLUMN IF NOT EXISTS usage_rights TEXT DEFAULT 'commercial';
ALTER TABLE public.briefs ADD COLUMN IF NOT EXISTS max_revisions INT DEFAULT 2 CHECK (max_revisions >= 0);
ALTER TABLE public.briefs ADD COLUMN IF NOT EXISTS approved_at TIMESTAMPTZ;
ALTER TABLE public.briefs ADD COLUMN IF NOT EXISTS approved_by UUID REFERENCES public.users(id);

-- Interactive AI brief drafting sessions
CREATE TABLE IF NOT EXISTS public.brief_ai_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    brief_id UUID REFERENCES public.briefs(id) ON DELETE SET NULL,
    session_title TEXT NOT NULL DEFAULT 'AI Brief Assistant Session',
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'completed', 'abandoned')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- AI conversation messages (separating customer dialog from internal metadata)
CREATE TABLE IF NOT EXISTS public.brief_ai_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES public.brief_ai_sessions(id) ON DELETE CASCADE,
    sender_role TEXT NOT NULL CHECK (sender_role IN ('customer', 'assistant', 'system')),
    content TEXT NOT NULL,
    clarification_field TEXT,
    model_metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Versioned snapshots of generated briefs before customer approval
CREATE TABLE IF NOT EXISTS public.brief_revisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    brief_id UUID NOT NULL REFERENCES public.briefs(id) ON DELETE CASCADE,
    revision_number INT NOT NULL CHECK (revision_number >= 1),
    snapshot_data JSONB NOT NULL,
    changed_by UUID NOT NULL REFERENCES public.users(id),
    change_summary TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (brief_id, revision_number)
);

-- ============================================================================
-- 5. CREATOR MATCHING SNAPSHOTS
-- ============================================================================

-- Storing explainable matching results
CREATE TABLE IF NOT EXISTS public.brief_matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    brief_id UUID NOT NULL REFERENCES public.briefs(id) ON DELETE CASCADE,
    creator_id UUID NOT NULL REFERENCES public.creators(id) ON DELETE CASCADE,
    match_score NUMERIC(5, 2) NOT NULL CHECK (match_score >= 0.00 AND match_score <= 100.00),
    match_reasons JSONB NOT NULL DEFAULT '[]'::jsonb,
    is_notified BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (brief_id, creator_id)
);

-- ============================================================================
-- 6. IN-PLATFORM CHAT & CONTACT MODERATION
-- ============================================================================

-- Chat conversations linked to project/brief
CREATE TABLE IF NOT EXISTS public.chat_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID,
    brief_id UUID REFERENCES public.briefs(id) ON DELETE SET NULL,
    created_by UUID NOT NULL REFERENCES public.users(id),
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'archived', 'blocked')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Conversation participants with anonymity aliases
CREATE TABLE IF NOT EXISTS public.chat_participants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES public.chat_conversations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('customer', 'creator', 'moderator', 'admin')),
    display_alias TEXT NOT NULL,
    joined_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_read_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (conversation_id, user_id)
);

-- Helper function to check conversation participation without RLS recursion
CREATE OR REPLACE FUNCTION public.is_chat_participant(p_conversation_id UUID, p_user_id UUID)
RETURNS BOOLEAN AS $$
    SELECT EXISTS (
        SELECT 1 
        FROM public.chat_participants 
        WHERE conversation_id = p_conversation_id AND user_id = p_user_id
    );
$$ LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public, pg_temp;

-- Chat messages with soft delete and moderation states
CREATE TABLE IF NOT EXISTS public.chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES public.chat_conversations(id) ON DELETE CASCADE,
    sender_id UUID NOT NULL REFERENCES public.users(id),
    content TEXT NOT NULL,
    moderation_status TEXT NOT NULL DEFAULT 'allowed' 
        CHECK (moderation_status IN ('allowed', 'blocked', 'redacted', 'awaiting_moderation', 'approved', 'appeal_submitted', 'appeal_resolved')),
    is_edited BOOLEAN NOT NULL DEFAULT false,
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- File attachments associated with messages
CREATE TABLE IF NOT EXISTS public.chat_attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID NOT NULL REFERENCES public.chat_messages(id) ON DELETE CASCADE,
    file_name TEXT NOT NULL,
    file_url TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size_bytes BIGINT NOT NULL CHECK (file_size_bytes > 0),
    is_scanned BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Moderation records and contact info censorship audit
CREATE TABLE IF NOT EXISTS public.message_moderation_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID NOT NULL REFERENCES public.chat_messages(id) ON DELETE CASCADE,
    flagged_by TEXT NOT NULL CHECK (flagged_by IN ('system_regex', 'ai_classifier', 'user_report', 'moderator')),
    detection_category TEXT NOT NULL CHECK (detection_category IN ('phone_number', 'email', 'social_handle', 'external_url', 'direct_solicitation', 'other')),
    redacted_snippet TEXT,
    moderation_decision TEXT NOT NULL CHECK (moderation_decision IN ('blocked', 'redacted', 'pending_review', 'cleared')),
    moderator_id UUID REFERENCES public.users(id),
    appeal_note TEXT,
    appeal_status TEXT CHECK (appeal_status IN ('pending', 'approved', 'rejected')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMPTZ
);

-- Guard: Ordinary users cannot bypass moderation or approve their own appeals
CREATE OR REPLACE FUNCTION public.protect_chat_message_moderation()
RETURNS TRIGGER AS $$
DECLARE
    v_user_role TEXT;
BEGIN
    -- Service role can perform any administrative update
    IF COALESCE(current_setting('request.jwt.claim.role', true), '') = 'service_role' THEN
        RETURN NEW;
    END IF;

    -- Look up caller's role in public.users
    SELECT role INTO v_user_role FROM public.users WHERE id = auth.uid();

    -- Immutability of message identity, conversation, and sender
    IF NEW.id <> OLD.id OR NEW.conversation_id <> OLD.conversation_id OR NEW.sender_id <> OLD.sender_id THEN
        RAISE EXCEPTION 'Message identity, conversation, and sender cannot be modified.';
    END IF;

    -- Ordinary participants cannot alter moderation_status or un-delete messages
    IF OLD.moderation_status <> NEW.moderation_status AND v_user_role NOT IN ('admin', 'moderator') THEN
        RAISE EXCEPTION 'Only platform moderators or administrators can modify message moderation status.';
    END IF;

    IF OLD.deleted_at IS NOT NULL AND NEW.deleted_at IS NULL AND v_user_role NOT IN ('admin', 'moderator') THEN
        RAISE EXCEPTION 'Deleted messages cannot be restored by ordinary users.';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp;

DROP TRIGGER IF EXISTS trg_protect_chat_message_moderation ON public.chat_messages;
CREATE TRIGGER trg_protect_chat_message_moderation
    BEFORE UPDATE ON public.chat_messages
    FOR EACH ROW EXECUTE FUNCTION public.protect_chat_message_moderation();

-- ============================================================================
-- 7. CREATOR QUOTES & CUSTOMER PRICING
-- ============================================================================

-- Quotes with separate creator quote and customer-facing price
CREATE TABLE IF NOT EXISTS public.project_quotes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    brief_id UUID NOT NULL REFERENCES public.briefs(id) ON DELETE CASCADE,
    creator_id UUID NOT NULL REFERENCES public.creators(id) ON DELETE CASCADE,
    creator_quote_amount NUMERIC(12, 2) NOT NULL CHECK (creator_quote_amount > 0),
    platform_fee_rate NUMERIC(5, 4) NOT NULL DEFAULT 0.1500 CHECK (platform_fee_rate >= 0 AND platform_fee_rate < 1.0),
    platform_fee_amount NUMERIC(12, 2) NOT NULL CHECK (platform_fee_amount >= 0),
    tax_amount NUMERIC(12, 2) NOT NULL DEFAULT 0.00 CHECK (tax_amount >= 0),
    customer_price_amount NUMERIC(12, 2) NOT NULL CHECK (customer_price_amount >= creator_quote_amount),
    currency VARCHAR(3) NOT NULL DEFAULT 'INR',
    scope_summary TEXT NOT NULL,
    deliverables TEXT[] NOT NULL DEFAULT '{}',
    estimated_delivery_days INT NOT NULL CHECK (estimated_delivery_days > 0),
    revision_count INT NOT NULL DEFAULT 2 CHECK (revision_count >= 0),
    valid_until TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL DEFAULT 'submitted' 
        CHECK (status IN ('submitted', 'under_review', 'presented_to_customer', 'accepted', 'declined', 'expired', 'withdrawn')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (brief_id, creator_id)
);

-- Guard: Enforce mathematical integrity of fees and customer price
CREATE OR REPLACE FUNCTION public.enforce_quote_pricing_integrity()
RETURNS TRIGGER AS $$
BEGIN
    -- Recompute fee and price deterministically
    NEW.platform_fee_amount := ROUND(NEW.creator_quote_amount * NEW.platform_fee_rate, 2);
    NEW.customer_price_amount := NEW.creator_quote_amount + NEW.platform_fee_amount + NEW.tax_amount;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SET search_path = public, pg_temp;

DROP TRIGGER IF EXISTS trg_enforce_quote_pricing_integrity ON public.project_quotes;
CREATE TRIGGER trg_enforce_quote_pricing_integrity
    BEFORE INSERT OR UPDATE ON public.project_quotes
    FOR EACH ROW EXECUTE FUNCTION public.enforce_quote_pricing_integrity();

-- Customer-facing view shielding creator's private quote and internal fee breakdown
DROP VIEW IF EXISTS public.customer_quotes_view;
CREATE OR REPLACE VIEW public.customer_quotes_view WITH (security_invoker = true) AS
SELECT 
    q.id,
    q.brief_id,
    q.creator_id,
    q.customer_price_amount,
    q.currency,
    q.scope_summary,
    q.deliverables,
    q.estimated_delivery_days,
    q.revision_count,
    q.valid_until,
    q.status,
    q.created_at
FROM public.project_quotes q
WHERE q.status IN ('presented_to_customer', 'accepted');

-- ============================================================================
-- 8. FORMAL PROJECT CONTRACTS & LIFECYCLE
-- ============================================================================

-- Contracts separate from casual enquiries
CREATE TABLE IF NOT EXISTS public.projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    brief_id UUID NOT NULL REFERENCES public.briefs(id) ON DELETE RESTRICT,
    quote_id UUID REFERENCES public.project_quotes(id) ON DELETE RESTRICT,
    customer_id UUID NOT NULL REFERENCES public.users(id) ON DELETE RESTRICT,
    creator_id UUID NOT NULL REFERENCES public.creators(id) ON DELETE RESTRICT,
    title TEXT NOT NULL,
    agreed_amount NUMERIC(12, 2) NOT NULL CHECK (agreed_amount > 0),
    creator_earnings NUMERIC(12, 2) NOT NULL CHECK (creator_earnings > 0),
    platform_fee NUMERIC(12, 2) NOT NULL CHECK (platform_fee >= 0),
    currency VARCHAR(3) NOT NULL DEFAULT 'INR',
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN (
        'draft', 'brief_approved', 'matching', 'negotiation', 
        'offer_accepted', 'awaiting_payment', 'in_progress', 
        'submitted', 'revision_requested', 'completed', 
        'cancelled', 'disputed'
    )),
    started_at TIMESTAMPTZ,
    deadline TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    cancelled_at TIMESTAMPTZ,
    cancellation_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- State transition validation for formal projects
CREATE OR REPLACE FUNCTION public.enforce_project_status_transitions()
RETURNS TRIGGER AS $$
DECLARE
    v_user_role TEXT;
BEGIN
    IF COALESCE(current_setting('request.jwt.claim.role', true), '') = 'service_role' THEN
        RETURN NEW;
    END IF;

    -- Immutability of core contract participants
    IF NEW.id <> OLD.id OR NEW.brief_id <> OLD.brief_id OR NEW.customer_id <> OLD.customer_id OR NEW.creator_id <> OLD.creator_id THEN
        RAISE EXCEPTION 'Contract identity and participants cannot be modified once created.';
    END IF;

    -- Financial terms cannot be modified after offer acceptance
    IF OLD.status IN ('offer_accepted', 'awaiting_payment', 'in_progress', 'completed') THEN
        IF NEW.agreed_amount <> OLD.agreed_amount OR NEW.creator_earnings <> OLD.creator_earnings OR NEW.platform_fee <> OLD.platform_fee THEN
            RAISE EXCEPTION 'Financial terms cannot be modified on an accepted or active contract.';
        END IF;
    END IF;

    -- Valid state transitions
    IF OLD.status = NEW.status THEN
        RETURN NEW;
    END IF;

    IF OLD.status = 'draft' AND NEW.status NOT IN ('brief_approved', 'cancelled') THEN
        RAISE EXCEPTION 'Draft project can only transition to brief_approved or cancelled.';
    ELSIF OLD.status = 'brief_approved' AND NEW.status NOT IN ('matching', 'cancelled') THEN
        RAISE EXCEPTION 'Approved brief can only transition to matching or cancelled.';
    ELSIF OLD.status = 'matching' AND NEW.status NOT IN ('negotiation', 'cancelled') THEN
        RAISE EXCEPTION 'Matching project can only transition to negotiation or cancelled.';
    ELSIF OLD.status = 'negotiation' AND NEW.status NOT IN ('offer_accepted', 'cancelled') THEN
        RAISE EXCEPTION 'Negotiation project can only transition to offer_accepted or cancelled.';
    ELSIF OLD.status = 'offer_accepted' AND NEW.status NOT IN ('awaiting_payment', 'cancelled') THEN
        RAISE EXCEPTION 'Accepted offer can only transition to awaiting_payment or cancelled.';
    ELSIF OLD.status = 'awaiting_payment' AND NEW.status NOT IN ('in_progress', 'cancelled') THEN
        RAISE EXCEPTION 'Project awaiting payment can only transition to in_progress or cancelled.';
    ELSIF OLD.status = 'in_progress' AND NEW.status NOT IN ('submitted', 'disputed', 'cancelled') THEN
        RAISE EXCEPTION 'Active project in_progress can only transition to submitted, disputed, or cancelled.';
    ELSIF OLD.status = 'submitted' AND NEW.status NOT IN ('revision_requested', 'completed', 'disputed') THEN
        RAISE EXCEPTION 'Submitted project can only transition to revision_requested, completed, or disputed.';
    ELSIF OLD.status = 'revision_requested' AND NEW.status NOT IN ('submitted', 'disputed', 'cancelled') THEN
        RAISE EXCEPTION 'Project under revision can only transition to submitted, disputed, or cancelled.';
    ELSIF OLD.status = 'completed' THEN
        RAISE EXCEPTION 'Completed projects cannot change state.';
    ELSIF OLD.status = 'cancelled' THEN
        RAISE EXCEPTION 'Cancelled projects cannot be reopened.';
    ELSIF OLD.status = 'disputed' AND NEW.status NOT IN ('completed', 'cancelled') THEN
        RAISE EXCEPTION 'Disputed project can only be resolved by admin to completed or cancelled.';
    END IF;

    -- Timestamp maintenance
    IF NEW.status = 'in_progress' AND OLD.status <> 'in_progress' THEN
        NEW.started_at := CURRENT_TIMESTAMP;
    ELSIF NEW.status = 'completed' AND OLD.status <> 'completed' THEN
        NEW.completed_at := CURRENT_TIMESTAMP;
    ELSIF NEW.status = 'cancelled' AND OLD.status <> 'cancelled' THEN
        NEW.cancelled_at := CURRENT_TIMESTAMP;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp;

DROP TRIGGER IF EXISTS trg_enforce_project_status_transitions ON public.projects;
CREATE TRIGGER trg_enforce_project_status_transitions
    BEFORE UPDATE ON public.projects
    FOR EACH ROW EXECUTE FUNCTION public.enforce_project_status_transitions();

-- ============================================================================
-- 9. PAYMENTS, FINANCIAL LEDGER & CONTACT UNLOCKS
-- ============================================================================

-- Idempotent payment attempts and confirmations
CREATE TABLE IF NOT EXISTS public.payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES public.projects(id) ON DELETE RESTRICT,
    quote_id UUID REFERENCES public.project_quotes(id) ON DELETE RESTRICT,
    customer_id UUID NOT NULL REFERENCES public.users(id),
    provider TEXT NOT NULL CHECK (provider IN ('stripe', 'razorpay', 'mock_gateway')),
    provider_payment_intent_id TEXT UNIQUE,
    amount NUMERIC(12, 2) NOT NULL CHECK (amount > 0),
    currency VARCHAR(3) NOT NULL DEFAULT 'INR',
    status TEXT NOT NULL DEFAULT 'pending' 
        CHECK (status IN ('pending', 'requires_action', 'succeeded', 'failed', 'refunded', 'disputed')),
    idempotency_key TEXT UNIQUE NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Double-entry financial audit ledger
CREATE TABLE IF NOT EXISTS public.financial_ledger (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    payment_id UUID NOT NULL REFERENCES public.payments(id) ON DELETE RESTRICT,
    entry_type TEXT NOT NULL CHECK (entry_type IN ('payment_received', 'platform_fee', 'creator_payout', 'refund', 'dispute_hold')),
    account TEXT NOT NULL CHECK (account IN ('escrow_holding', 'platform_revenue', 'creator_payable')),
    amount NUMERIC(12, 2) NOT NULL CHECK (amount > 0),
    currency VARCHAR(3) NOT NULL DEFAULT 'INR',
    reference_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Link payment and project foreign keys in contact_unlocks if not already linked
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_contact_unlocks_payment'
    ) THEN
        ALTER TABLE public.contact_unlocks 
            ADD CONSTRAINT fk_contact_unlocks_payment 
            FOREIGN KEY (payment_id) REFERENCES public.payments(id) ON DELETE RESTRICT;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_contact_unlocks_project'
    ) THEN
        ALTER TABLE public.contact_unlocks 
            ADD CONSTRAINT fk_contact_unlocks_project 
            FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE SET NULL;
    END IF;
END $$;

-- Guard: Payments cannot be marked as succeeded by client; unlocks require verified payment
CREATE OR REPLACE FUNCTION public.protect_payment_state()
RETURNS TRIGGER AS $$
BEGIN
    IF COALESCE(current_setting('request.jwt.claim.role', true), '') <> 'service_role' THEN
        IF NEW.status = 'succeeded' AND OLD.status <> 'succeeded' THEN
            RAISE EXCEPTION 'Payments can only be confirmed as succeeded by trusted backend webhooks.';
        END IF;
        IF NEW.amount <> OLD.amount THEN
            RAISE EXCEPTION 'Payment amount cannot be altered once initiated.';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp;

DROP TRIGGER IF EXISTS trg_protect_payment_state ON public.payments;
CREATE TRIGGER trg_protect_payment_state
    BEFORE UPDATE ON public.payments
    FOR EACH ROW EXECUTE FUNCTION public.protect_payment_state();

-- Guard: Contact unlocks can ONLY be created by service_role or with succeeded payment
CREATE OR REPLACE FUNCTION public.protect_contact_unlock_creation()
RETURNS TRIGGER AS $$
DECLARE
    v_pay_status TEXT;
BEGIN
    IF COALESCE(current_setting('request.jwt.claim.role', true), '') = 'service_role' THEN
        RETURN NEW;
    END IF;

    IF NEW.payment_id IS NULL THEN
        RAISE EXCEPTION 'Contact unlock requires a verified payment reference.';
    END IF;

    SELECT status INTO v_pay_status FROM public.payments WHERE id = NEW.payment_id;
    IF v_pay_status <> 'succeeded' THEN
        RAISE EXCEPTION 'Cannot unlock contact details: payment status is %, expected succeeded.', v_pay_status;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp;

DROP TRIGGER IF EXISTS trg_protect_contact_unlock_creation ON public.contact_unlocks;
CREATE TRIGGER trg_protect_contact_unlock_creation
    BEFORE INSERT OR UPDATE ON public.contact_unlocks
    FOR EACH ROW EXECUTE FUNCTION public.protect_contact_unlock_creation();

-- ============================================================================
-- 10. VERIFIED REVIEWS & REPUTATION SYSTEM
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE RESTRICT UNIQUE,
    customer_id UUID NOT NULL REFERENCES public.users(id) ON DELETE RESTRICT,
    creator_id UUID NOT NULL REFERENCES public.creators(id) ON DELETE RESTRICT,
    rating NUMERIC(3, 2) NOT NULL CHECK (rating >= 1.00 AND rating <= 5.00),
    review_text TEXT NOT NULL CHECK (LENGTH(TRIM(review_text)) >= 10),
    moderation_status TEXT NOT NULL DEFAULT 'published' 
        CHECK (moderation_status IN ('published', 'flagged', 'hidden')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Validation & auto-recalculation of creator rating
CREATE OR REPLACE FUNCTION public.validate_and_apply_review()
RETURNS TRIGGER AS $$
DECLARE
    v_proj_status TEXT;
    v_proj_cust UUID;
    v_proj_creat UUID;
    v_avg_rating NUMERIC(3, 2);
    v_count INT;
BEGIN
    -- Verify project status is completed
    SELECT status, customer_id, creator_id 
    INTO v_proj_status, v_proj_cust, v_proj_creat
    FROM public.projects 
    WHERE id = NEW.project_id;

    IF v_proj_status <> 'completed' THEN
        RAISE EXCEPTION 'Reviews can only be submitted for completed projects (current status: %).', v_proj_status;
    END IF;

    -- Ensure reviewer is actual project customer and cannot review self
    IF NEW.customer_id <> v_proj_cust THEN
        RAISE EXCEPTION 'Only the customer on the completed project can submit a review.';
    END IF;

    IF NEW.creator_id <> v_proj_creat THEN
        RAISE EXCEPTION 'Review creator_id must match the completed project creator.';
    END IF;

    -- Auto-recalculate creator's rating and review count
    SELECT ROUND(AVG(rating), 2), COUNT(*)
    INTO v_avg_rating, v_count
    FROM public.reviews
    WHERE creator_id = NEW.creator_id 
      AND moderation_status = 'published';

    UPDATE public.creators
    SET rating = COALESCE(v_avg_rating, NEW.rating),
        total_reviews = v_count
    WHERE id = NEW.creator_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp;

-- Allow reputation updates when called via review trigger (pg_trigger_depth > 1) or service_role
CREATE OR REPLACE FUNCTION public.protect_creator_reputation()
RETURNS TRIGGER AS $$
BEGIN
    IF COALESCE(current_setting('request.jwt.claim.role', true), '') <> 'service_role' AND pg_trigger_depth() <= 1 THEN
        NEW.rating = OLD.rating;
        NEW.total_reviews = OLD.total_reviews;
        NEW.is_featured = OLD.is_featured;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SET search_path = public, pg_temp;

DROP TRIGGER IF EXISTS trg_validate_and_apply_review ON public.reviews;
CREATE TRIGGER trg_validate_and_apply_review
    AFTER INSERT OR UPDATE ON public.reviews
    FOR EACH ROW EXECUTE FUNCTION public.validate_and_apply_review();

-- ============================================================================
-- 11. CREATOR SUBSCRIPTIONS & ENTITLEMENTS
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.creator_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creator_id UUID NOT NULL REFERENCES public.creators(id) ON DELETE CASCADE,
    tier TEXT NOT NULL DEFAULT 'free' CHECK (tier IN ('free', 'starter', 'pro', 'agency')),
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'past_due', 'cancelled', 'expired')),
    provider_subscription_id TEXT UNIQUE,
    billing_cycle TEXT NOT NULL DEFAULT 'monthly' CHECK (billing_cycle IN ('monthly', 'yearly')),
    current_period_start TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    current_period_end TIMESTAMPTZ,
    cancel_at_period_end BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Guard: Ordinary creators cannot self-elevate subscription tier or status
CREATE OR REPLACE FUNCTION public.protect_creator_subscription_updates()
RETURNS TRIGGER AS $$
BEGIN
    IF COALESCE(current_setting('request.jwt.claim.role', true), '') <> 'service_role' THEN
        IF NEW.tier <> OLD.tier OR NEW.status <> OLD.status THEN
            RAISE EXCEPTION 'Subscription tiers and status can only be updated by service_role billing webhooks.';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp;

DROP TRIGGER IF EXISTS trg_protect_creator_subscription_updates ON public.creator_subscriptions;
CREATE TRIGGER trg_protect_creator_subscription_updates
    BEFORE UPDATE ON public.creator_subscriptions
    FOR EACH ROW EXECUTE FUNCTION public.protect_creator_subscription_updates();

-- ============================================================================
-- 12. HIGH-PERFORMANCE INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_creators_equipment_gin ON public.creators USING gin (equipment);
CREATE INDEX IF NOT EXISTS idx_creators_capabilities_gin ON public.creators USING gin (production_capabilities);
CREATE INDEX IF NOT EXISTS idx_briefs_deliverables_gin ON public.briefs USING gin (deliverables);

CREATE INDEX IF NOT EXISTS idx_brief_ai_messages_session ON public.brief_ai_messages (session_id);
CREATE INDEX IF NOT EXISTS idx_brief_revisions_brief ON public.brief_revisions (brief_id);
CREATE INDEX IF NOT EXISTS idx_brief_matches_brief ON public.brief_matches (brief_id);
CREATE INDEX IF NOT EXISTS idx_brief_matches_creator ON public.brief_matches (creator_id);

CREATE INDEX IF NOT EXISTS idx_chat_participants_user ON public.chat_participants (user_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_convo ON public.chat_messages (conversation_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_sender ON public.chat_messages (sender_id);
CREATE INDEX IF NOT EXISTS idx_message_moderation_logs_msg ON public.message_moderation_logs (message_id);

CREATE INDEX IF NOT EXISTS idx_project_quotes_brief ON public.project_quotes (brief_id);
CREATE INDEX IF NOT EXISTS idx_project_quotes_creator ON public.project_quotes (creator_id);
CREATE INDEX IF NOT EXISTS idx_projects_customer ON public.projects (customer_id);
CREATE INDEX IF NOT EXISTS idx_projects_creator ON public.projects (creator_id);
CREATE INDEX IF NOT EXISTS idx_projects_status ON public.projects (status);

CREATE INDEX IF NOT EXISTS idx_payments_customer ON public.payments (customer_id);
CREATE INDEX IF NOT EXISTS idx_payments_project ON public.payments (project_id);
CREATE INDEX IF NOT EXISTS idx_contact_unlocks_lookup ON public.contact_unlocks (customer_id, creator_id);
CREATE INDEX IF NOT EXISTS idx_reviews_creator ON public.reviews (creator_id);
CREATE INDEX IF NOT EXISTS idx_creator_subs_creator ON public.creator_subscriptions (creator_id);

-- Attach updated_at triggers
DROP TRIGGER IF EXISTS trg_creator_private_contacts_updated_at ON public.creator_private_contacts;
CREATE TRIGGER trg_creator_private_contacts_updated_at BEFORE UPDATE ON public.creator_private_contacts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trg_brief_ai_sessions_updated_at ON public.brief_ai_sessions;
CREATE TRIGGER trg_brief_ai_sessions_updated_at BEFORE UPDATE ON public.brief_ai_sessions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trg_chat_conversations_updated_at ON public.chat_conversations;
CREATE TRIGGER trg_chat_conversations_updated_at BEFORE UPDATE ON public.chat_conversations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trg_chat_messages_updated_at ON public.chat_messages;
CREATE TRIGGER trg_chat_messages_updated_at BEFORE UPDATE ON public.chat_messages FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trg_project_quotes_updated_at ON public.project_quotes;
CREATE TRIGGER trg_project_quotes_updated_at BEFORE UPDATE ON public.project_quotes FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trg_projects_updated_at ON public.projects;
CREATE TRIGGER trg_projects_updated_at BEFORE UPDATE ON public.projects FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trg_payments_updated_at ON public.payments;
CREATE TRIGGER trg_payments_updated_at BEFORE UPDATE ON public.payments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trg_reviews_updated_at ON public.reviews;
CREATE TRIGGER trg_reviews_updated_at BEFORE UPDATE ON public.reviews FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trg_creator_subscriptions_updated_at ON public.creator_subscriptions;
CREATE TRIGGER trg_creator_subscriptions_updated_at BEFORE UPDATE ON public.creator_subscriptions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 13. ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================================================

ALTER TABLE public.creator_private_contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.brief_ai_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.brief_ai_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.brief_revisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.brief_matches ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_participants ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_attachments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.message_moderation_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.project_quotes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.financial_ledger ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.contact_unlocks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.creator_subscriptions ENABLE ROW LEVEL SECURITY;

-- A. creator_private_contacts
DROP POLICY IF EXISTS "Creator can manage own private contact" ON public.creator_private_contacts;
CREATE POLICY "Creator can manage own private contact"
    ON public.creator_private_contacts FOR ALL
    USING (creator_id IN (SELECT id FROM public.creators WHERE user_id = auth.uid()))
    WITH CHECK (creator_id IN (SELECT id FROM public.creators WHERE user_id = auth.uid()));

DROP POLICY IF EXISTS "Customer can read unlocked creator contact" ON public.creator_private_contacts;
CREATE POLICY "Customer can read unlocked creator contact"
    ON public.creator_private_contacts FOR SELECT
    USING (public.has_unlocked_creator(auth.uid(), creator_id));

-- B. brief_ai_sessions & messages
DROP POLICY IF EXISTS "Customer can access own brief AI sessions" ON public.brief_ai_sessions;
CREATE POLICY "Customer can access own brief AI sessions"
    ON public.brief_ai_sessions FOR ALL
    USING (customer_id = auth.uid())
    WITH CHECK (customer_id = auth.uid());

DROP POLICY IF EXISTS "Customer can access own brief AI messages" ON public.brief_ai_messages;
CREATE POLICY "Customer can access own brief AI messages"
    ON public.brief_ai_messages FOR ALL
    USING (session_id IN (SELECT id FROM public.brief_ai_sessions WHERE customer_id = auth.uid()))
    WITH CHECK (session_id IN (SELECT id FROM public.brief_ai_sessions WHERE customer_id = auth.uid()));

-- C. brief_revisions & brief_matches
DROP POLICY IF EXISTS "Brief owner can access brief revisions" ON public.brief_revisions;
CREATE POLICY "Brief owner can access brief revisions"
    ON public.brief_revisions FOR ALL
    USING (brief_id IN (SELECT id FROM public.briefs WHERE customer_id = auth.uid()))
    WITH CHECK (brief_id IN (SELECT id FROM public.briefs WHERE customer_id = auth.uid()));

DROP POLICY IF EXISTS "Brief owner and matched creator can see match" ON public.brief_matches;
CREATE POLICY "Brief owner and matched creator can see match"
    ON public.brief_matches FOR SELECT
    USING (
        brief_id IN (SELECT id FROM public.briefs WHERE customer_id = auth.uid())
        OR creator_id IN (SELECT id FROM public.creators WHERE user_id = auth.uid())
    );

-- D. chat_conversations & participants
DROP POLICY IF EXISTS "Participants can view conversation" ON public.chat_conversations;
CREATE POLICY "Participants can view conversation"
    ON public.chat_conversations FOR SELECT
    USING (
        public.is_chat_participant(id, auth.uid())
    );

DROP POLICY IF EXISTS "Participants can view other participants in conversation" ON public.chat_participants;
CREATE POLICY "Participants can view other participants in conversation"
    ON public.chat_participants FOR SELECT
    USING (
        public.is_chat_participant(conversation_id, auth.uid())
    );

-- E. chat_messages & attachments
DROP POLICY IF EXISTS "Participants can read messages in conversation" ON public.chat_messages;
CREATE POLICY "Participants can read messages in conversation"
    ON public.chat_messages FOR SELECT
    USING (
        public.is_chat_participant(conversation_id, auth.uid())
        AND (deleted_at IS NULL OR sender_id = auth.uid())
    );

DROP POLICY IF EXISTS "Participants can post messages with allowed moderation status" ON public.chat_messages;
CREATE POLICY "Participants can post messages with allowed moderation status"
    ON public.chat_messages FOR INSERT
    WITH CHECK (
        sender_id = auth.uid()
        AND moderation_status = 'allowed'
        AND public.is_chat_participant(conversation_id, auth.uid())
    );

DROP POLICY IF EXISTS "Sender can edit or soft-delete message" ON public.chat_messages;
CREATE POLICY "Sender can edit or soft-delete message"
    ON public.chat_messages FOR UPDATE
    USING (sender_id = auth.uid())
    WITH CHECK (sender_id = auth.uid());

DROP POLICY IF EXISTS "Participants can view attachments" ON public.chat_attachments;
CREATE POLICY "Participants can view attachments"
    ON public.chat_attachments FOR SELECT
    USING (
        message_id IN (
            SELECT cm.id FROM public.chat_messages cm
            JOIN public.chat_participants cp ON cm.conversation_id = cp.conversation_id
            WHERE cp.user_id = auth.uid()
        )
    );

DROP POLICY IF EXISTS "Sender can attach files to own message" ON public.chat_attachments;
CREATE POLICY "Sender can attach files to own message"
    ON public.chat_attachments FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.chat_messages cm
            JOIN public.chat_participants cp ON cm.conversation_id = cp.conversation_id
            WHERE cm.id = chat_attachments.message_id
              AND cm.sender_id = auth.uid()
              AND cp.user_id = auth.uid()
              AND cm.deleted_at IS NULL
        )
    );

DROP POLICY IF EXISTS "Sender can delete own message attachments" ON public.chat_attachments;
CREATE POLICY "Sender can delete own message attachments"
    ON public.chat_attachments FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM public.chat_messages cm
            JOIN public.chat_participants cp ON cm.conversation_id = cp.conversation_id
            WHERE cm.id = chat_attachments.message_id
              AND cm.sender_id = auth.uid()
              AND cp.user_id = auth.uid()
        )
    );

-- F. message_moderation_logs (Admin/moderator only)
DROP POLICY IF EXISTS "Moderators can view moderation logs" ON public.message_moderation_logs;
CREATE POLICY "Moderators can view moderation logs"
    ON public.message_moderation_logs FOR SELECT
    USING (
        EXISTS (SELECT 1 FROM public.users WHERE id = auth.uid() AND role IN ('admin', 'moderator'))
    );

-- G. project_quotes
DROP POLICY IF EXISTS "Creator can manage own quotes" ON public.project_quotes;
CREATE POLICY "Creator can manage own quotes"
    ON public.project_quotes FOR ALL
    USING (creator_id IN (SELECT id FROM public.creators WHERE user_id = auth.uid()))
    WITH CHECK (creator_id IN (SELECT id FROM public.creators WHERE user_id = auth.uid()));

DROP POLICY IF EXISTS "Brief owner can view presented quotes" ON public.project_quotes;
CREATE POLICY "Brief owner can view presented quotes"
    ON public.project_quotes FOR SELECT
    USING (
        brief_id IN (SELECT id FROM public.briefs WHERE customer_id = auth.uid())
        AND status IN ('presented_to_customer', 'accepted')
    );

DROP POLICY IF EXISTS "Brief owner can accept or decline quote" ON public.project_quotes;
CREATE POLICY "Brief owner can accept or decline quote"
    ON public.project_quotes FOR UPDATE
    USING (
        brief_id IN (SELECT id FROM public.briefs WHERE customer_id = auth.uid())
        AND status IN ('presented_to_customer', 'accepted', 'declined')
    )
    WITH CHECK (
        brief_id IN (SELECT id FROM public.briefs WHERE customer_id = auth.uid())
        AND status IN ('presented_to_customer', 'accepted', 'declined')
    );

-- H. projects
DROP POLICY IF EXISTS "Project participants can view project" ON public.projects;
CREATE POLICY "Project participants can view project"
    ON public.projects FOR SELECT
    USING (
        customer_id = auth.uid()
        OR creator_id IN (SELECT id FROM public.creators WHERE user_id = auth.uid())
    );

DROP POLICY IF EXISTS "Customer can update project terms" ON public.projects;
CREATE POLICY "Customer can update project terms"
    ON public.projects FOR UPDATE
    USING (customer_id = auth.uid())
    WITH CHECK (customer_id = auth.uid());

DROP POLICY IF EXISTS "Creator can update project submission" ON public.projects;
CREATE POLICY "Creator can update project submission"
    ON public.projects FOR UPDATE
    USING (creator_id IN (SELECT id FROM public.creators WHERE user_id = auth.uid()))
    WITH CHECK (creator_id IN (SELECT id FROM public.creators WHERE user_id = auth.uid()));

-- I. payments & financial_ledger
DROP POLICY IF EXISTS "Customer can view own payments" ON public.payments;
CREATE POLICY "Customer can view own payments"
    ON public.payments FOR SELECT
    USING (customer_id = auth.uid());

DROP POLICY IF EXISTS "Customer can update own pending payments" ON public.payments;
CREATE POLICY "Customer can update own pending payments"
    ON public.payments FOR UPDATE
    USING (customer_id = auth.uid() AND status IN ('pending', 'requires_action'))
    WITH CHECK (customer_id = auth.uid());

-- Financial ledger is restricted exclusively to service_role or admin
DROP POLICY IF EXISTS "Admin can view financial ledger" ON public.financial_ledger;
CREATE POLICY "Admin can view financial ledger"
    ON public.financial_ledger FOR SELECT
    USING (
        EXISTS (SELECT 1 FROM public.users WHERE id = auth.uid() AND role = 'admin')
    );

-- J. contact_unlocks
DROP POLICY IF EXISTS "Unlocked parties can view unlock status" ON public.contact_unlocks;
CREATE POLICY "Unlocked parties can view unlock status"
    ON public.contact_unlocks FOR SELECT
    USING (
        customer_id = auth.uid()
        OR creator_id IN (SELECT id FROM public.creators WHERE user_id = auth.uid())
    );

-- K. reviews
DROP POLICY IF EXISTS "Published reviews are publicly viewable" ON public.reviews;
CREATE POLICY "Published reviews are publicly viewable"
    ON public.reviews FOR SELECT
    USING (moderation_status = 'published');

DROP POLICY IF EXISTS "Customer can submit review on completed project" ON public.reviews;
CREATE POLICY "Customer can submit review on completed project"
    ON public.reviews FOR INSERT
    WITH CHECK (customer_id = auth.uid());

-- L. creator_subscriptions
DROP POLICY IF EXISTS "Creator can view own subscription" ON public.creator_subscriptions;
CREATE POLICY "Creator can view own subscription"
    ON public.creator_subscriptions FOR SELECT
    USING (creator_id IN (SELECT id FROM public.creators WHERE user_id = auth.uid()));

-- ============================================================================
-- 14. LEAST-PRIVILEGE PERMISSIONS & GRANTS
-- ============================================================================

REVOKE ALL ON FUNCTION public.has_unlocked_creator(UUID, UUID) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.is_chat_participant(UUID, UUID) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.protect_chat_message_moderation() FROM PUBLIC;
REVOKE ALL ON FUNCTION public.enforce_quote_pricing_integrity() FROM PUBLIC;
REVOKE ALL ON FUNCTION public.enforce_project_status_transitions() FROM PUBLIC;
REVOKE ALL ON FUNCTION public.protect_payment_state() FROM PUBLIC;
REVOKE ALL ON FUNCTION public.protect_contact_unlock_creation() FROM PUBLIC;
REVOKE ALL ON FUNCTION public.validate_and_apply_review() FROM PUBLIC;
REVOKE ALL ON FUNCTION public.protect_creator_subscription_updates() FROM PUBLIC;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
        GRANT EXECUTE ON FUNCTION public.has_unlocked_creator(UUID, UUID) TO authenticated;
        GRANT EXECUTE ON FUNCTION public.is_chat_participant(UUID, UUID) TO authenticated;
        GRANT EXECUTE ON FUNCTION public.protect_chat_message_moderation() TO authenticated;
        GRANT EXECUTE ON FUNCTION public.enforce_quote_pricing_integrity() TO authenticated;
        GRANT EXECUTE ON FUNCTION public.enforce_project_status_transitions() TO authenticated;
        GRANT EXECUTE ON FUNCTION public.protect_payment_state() TO authenticated;
        GRANT EXECUTE ON FUNCTION public.protect_contact_unlock_creation() TO authenticated;
        GRANT EXECUTE ON FUNCTION public.validate_and_apply_review() TO authenticated;
        GRANT EXECUTE ON FUNCTION public.protect_creator_subscription_updates() TO authenticated;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
        GRANT EXECUTE ON FUNCTION public.has_unlocked_creator(UUID, UUID) TO anon;
        GRANT EXECUTE ON FUNCTION public.is_chat_participant(UUID, UUID) TO anon;
    END IF;
END $$;
