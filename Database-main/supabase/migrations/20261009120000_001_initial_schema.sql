-- ============================================================================
-- Migration: 20261009120000_001_initial_schema.sql
-- Project: CreatorSphere AI
-- Description: Core database schema defining all 7 marketplace tables,
--              relationships, constraints, timestamps, and search indexes.
-- Hardening:   Strict search_path, execution privilege revocation from PUBLIC,
--              contract preservation triggers, reputation guards, and
--              status transition state machines.
-- ============================================================================

-- 1. EXTENSIONS & ENVIRONMENT COMPATIBILITY
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Standalone environment compatibility: Ensure auth schema & JWT helpers exist
-- when migrations run in fresh PostgreSQL instances outside Supabase Cloud.
-- In hosted Supabase, auth.uid() and auth.role() are system-provisioned;
-- this guarded block skips creation to prevent permission/ownership conflicts.
DO $do$
BEGIN
    -- 1. Create auth schema if missing (standalone PostgreSQL / local test engines only)
    IF NOT EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = 'auth') THEN
        CREATE SCHEMA auth;
    END IF;

    -- 2. Create auth.uid() stub only if not already provided by Supabase
    IF NOT EXISTS (
        SELECT 1 FROM pg_proc p
        JOIN pg_namespace n ON p.pronamespace = n.oid
        WHERE n.nspname = 'auth' AND p.proname = 'uid'
    ) THEN
        EXECUTE $fn$
            CREATE FUNCTION auth.uid()
            RETURNS UUID AS $f$
                SELECT NULLIF(current_setting('request.jwt.claim.sub', true), '')::uuid;
            $f$ LANGUAGE sql STABLE;
        $fn$;
    END IF;

    -- 3. Create auth.role() stub only if not already provided by Supabase
    IF NOT EXISTS (
        SELECT 1 FROM pg_proc p
        JOIN pg_namespace n ON p.pronamespace = n.oid
        WHERE n.nspname = 'auth' AND p.proname = 'role'
    ) THEN
        EXECUTE $fn$
            CREATE FUNCTION auth.role()
            RETURNS TEXT AS $f$
                SELECT NULLIF(current_setting('request.jwt.claim.role', true), '')::text;
            $f$ LANGUAGE sql STABLE;
        $fn$;
    END IF;
END $do$;

-- 2. HELPER FUNCTIONS & TRIGGERS
-- Automatic updated_at timestamp maintenance with secure search_path
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SET search_path = public, pg_temp;

-- 3. TABLE: users
-- Represents user accounts linked to Supabase Authentication.
-- Supports customers, creators, or users with both roles.
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'customer' CHECK (role IN ('customer', 'creator', 'both')),
    avatar_url TEXT,
    bio TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Trigger to sync new Supabase auth sign-ups into public.users automatically
-- Trigger to sync new Supabase auth sign-ups into public.users automatically
-- Hardened: Explicit SET search_path prevents search_path hijacking vulnerabilities
-- Hardened: Role input is strictly sanitized to valid roles ('customer', 'creator', 'both')
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
DECLARE
    v_role TEXT;
BEGIN
    v_role := COALESCE(NEW.raw_user_meta_data->>'role', 'customer');
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

-- Conditionally attach trigger to auth.users if the auth schema exists (Supabase environment)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'auth' AND table_name = 'users') THEN
        DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
        CREATE TRIGGER on_auth_user_created
            AFTER INSERT ON auth.users
            FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
    END IF;
END $$;

-- Guard 0: Protect user profile ownership, email, and role self-escalation
CREATE OR REPLACE FUNCTION public.protect_user_profile()
RETURNS TRIGGER AS $$
BEGIN
    IF COALESCE(current_setting('request.jwt.claim.role', true), '') <> 'service_role' THEN
        IF NEW.id <> OLD.id THEN
            RAISE EXCEPTION 'User id cannot be modified.';
        END IF;
        IF NEW.email <> OLD.email THEN
            RAISE EXCEPTION 'User email cannot be modified directly in public.users.';
        END IF;
        IF NEW.role <> OLD.role THEN
            RAISE EXCEPTION 'User role cannot be self-modified.';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SET search_path = public, pg_temp;

DROP TRIGGER IF EXISTS trg_protect_user_profile ON public.users;
CREATE TRIGGER trg_protect_user_profile
    BEFORE UPDATE ON public.users
    FOR EACH ROW EXECUTE FUNCTION public.protect_user_profile();

-- 4. TABLE: creators
-- Marketplace creator profiles with specialized video skills, tools, and budgets.
CREATE TABLE IF NOT EXISTS public.creators (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    handle TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    tagline TEXT,
    bio TEXT,
    skills TEXT[] NOT NULL DEFAULT '{}',
    tools TEXT[] NOT NULL DEFAULT '{}',
    styles TEXT[] NOT NULL DEFAULT '{}',
    content_types TEXT[] NOT NULL DEFAULT '{}',
    indicative_budget_min NUMERIC(10, 2) NOT NULL DEFAULT 0.00 CHECK (indicative_budget_min >= 0),
    indicative_budget_max NUMERIC(10, 2) NOT NULL DEFAULT 0.00 CHECK (indicative_budget_max >= indicative_budget_min),
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    availability TEXT NOT NULL DEFAULT 'available' CHECK (availability IN ('available', 'busy', 'unavailable')),
    experience_years INT NOT NULL DEFAULT 1 CHECK (experience_years >= 0),
    location TEXT,
    website_url TEXT,
    rating NUMERIC(3, 2) NOT NULL DEFAULT 5.00 CHECK (rating >= 0 AND rating <= 5.00),
    total_reviews INT NOT NULL DEFAULT 0 CHECK (total_reviews >= 0),
    is_featured BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 5. TABLE: portfolio_items
-- Showcase video samples with metadata, aspect ratios, and verification status.
CREATE TABLE IF NOT EXISTS public.portfolio_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creator_id UUID NOT NULL REFERENCES public.creators(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    video_url TEXT NOT NULL,
    thumbnail_url TEXT,
    content_type TEXT NOT NULL,
    style TEXT NOT NULL,
    aspect_ratio TEXT NOT NULL DEFAULT '16:9' CHECK (aspect_ratio IN ('16:9', '9:16', '1:1', '4:5', '21:9')),
    duration_seconds INT CHECK (duration_seconds IS NULL OR duration_seconds > 0),
    tools_used TEXT[] NOT NULL DEFAULT '{}',
    is_featured BOOLEAN NOT NULL DEFAULT false,
    view_count INT NOT NULL DEFAULT 0 CHECK (view_count >= 0),
    verification_status TEXT NOT NULL DEFAULT 'unverified' CHECK (verification_status IN ('unverified', 'pending', 'verified', 'rejected')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 6. TABLE: briefs
-- Video project briefs posted by customers (with AI-generated summaries and filters).
CREATE TABLE IF NOT EXISTS public.briefs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    ai_summary TEXT,
    target_audience TEXT,
    content_type TEXT NOT NULL,
    preferred_style TEXT,
    aspect_ratio TEXT NOT NULL DEFAULT '16:9' CHECK (aspect_ratio IN ('16:9', '9:16', '1:1', '4:5', '21:9')),
    duration_seconds_target INT CHECK (duration_seconds_target IS NULL OR duration_seconds_target > 0),
    budget_min NUMERIC(10, 2) NOT NULL DEFAULT 0.00 CHECK (budget_min >= 0),
    budget_max NUMERIC(10, 2) NOT NULL DEFAULT 0.00 CHECK (budget_max >= budget_min),
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    deadline TIMESTAMPTZ,
    commercial_use_required BOOLEAN NOT NULL DEFAULT true,
    required_skills TEXT[] NOT NULL DEFAULT '{}',
    preferred_tools TEXT[] NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('draft', 'open', 'in_review', 'assigned', 'completed', 'cancelled')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 7. TABLE: enquiries
-- Direct customer-to-creator communication and project quotes.
CREATE TABLE IF NOT EXISTS public.enquiries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    creator_id UUID NOT NULL REFERENCES public.creators(id) ON DELETE CASCADE,
    brief_id UUID REFERENCES public.briefs(id) ON DELETE SET NULL,
    subject TEXT NOT NULL,
    message TEXT NOT NULL,
    proposed_budget NUMERIC(10, 2) CHECK (proposed_budget IS NULL OR proposed_budget >= 0),
    proposed_deadline TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'declined', 'in_negotiation', 'closed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 8. TABLE: creator_interests
-- Creators pitching / expressing interest in open customer briefs.
CREATE TABLE IF NOT EXISTS public.creator_interests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    brief_id UUID NOT NULL REFERENCES public.briefs(id) ON DELETE CASCADE,
    creator_id UUID NOT NULL REFERENCES public.creators(id) ON DELETE CASCADE,
    pitch_note TEXT NOT NULL,
    estimated_delivery_days INT NOT NULL CHECK (estimated_delivery_days > 0),
    proposed_quote NUMERIC(10, 2) NOT NULL CHECK (proposed_quote >= 0),
    sample_portfolio_item_id UUID REFERENCES public.portfolio_items(id) ON DELETE SET NULL,
    status TEXT NOT NULL DEFAULT 'submitted' CHECK (status IN ('submitted', 'shortlisted', 'accepted', 'declined', 'withdrawn')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_brief_creator_interest UNIQUE (brief_id, creator_id)
);

-- 9. TABLE: verification_signals
-- Trust, authentic identity, and portfolio verification evidence.
CREATE TABLE IF NOT EXISTS public.verification_signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creator_id UUID NOT NULL REFERENCES public.creators(id) ON DELETE CASCADE,
    portfolio_item_id UUID REFERENCES public.portfolio_items(id) ON DELETE CASCADE,
    signal_type TEXT NOT NULL CHECK (signal_type IN ('portfolio_link_verified', 'identity_verified', 'social_account_verified', 'ai_watermark_detected', 'tool_authenticity_confirmed')),
    evidence_url TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'verified', 'rejected')),
    verified_at TIMESTAMPTZ,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 10. HARDENING TRIGGERS: INTEGRITY GUARDS & STATE MACHINES
-- ============================================================================

-- Guard A: Protect creator reputation metrics (rating, total_reviews, is_featured)
-- Prevents ordinary creators from modifying their own ratings, reviews, feature status, or IDs
CREATE OR REPLACE FUNCTION public.protect_creator_reputation()
RETURNS TRIGGER AS $$
BEGIN
    IF COALESCE(current_setting('request.jwt.claim.role', true), '') <> 'service_role' THEN
        IF NEW.id <> OLD.id THEN
            RAISE EXCEPTION 'Creator id cannot be modified.';
        END IF;
        IF NEW.user_id <> OLD.user_id THEN
            RAISE EXCEPTION 'Creator user_id cannot be modified.';
        END IF;
        NEW.rating := OLD.rating;
        NEW.total_reviews := OLD.total_reviews;
        NEW.is_featured := OLD.is_featured;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SET search_path = public, pg_temp;

DROP TRIGGER IF EXISTS trg_protect_creator_reputation ON public.creators;
CREATE TRIGGER trg_protect_creator_reputation
    BEFORE UPDATE ON public.creators
    FOR EACH ROW EXECUTE FUNCTION public.protect_creator_reputation();

-- Guard A2: Protect portfolio verification status from self-awarding and tampering
CREATE OR REPLACE FUNCTION public.protect_portfolio_verification()
RETURNS TRIGGER AS $$
BEGIN
    IF COALESCE(current_setting('request.jwt.claim.role', true), '') <> 'service_role' THEN
        IF NEW.id <> OLD.id THEN
            RAISE EXCEPTION 'Portfolio id cannot be modified.';
        END IF;
        IF NEW.creator_id <> OLD.creator_id THEN
            RAISE EXCEPTION 'Portfolio creator_id cannot be modified.';
        END IF;
        IF OLD.verification_status <> 'verified' AND NEW.verification_status = 'verified' THEN
            RAISE EXCEPTION 'Creators are forbidden from self-verifying portfolio items.';
        END IF;
        -- If video_url is altered on an already verified item, reset verification_status to pending
        IF OLD.verification_status = 'verified' AND NEW.video_url <> OLD.video_url THEN
            NEW.verification_status := 'pending';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SET search_path = public, pg_temp;

DROP TRIGGER IF EXISTS trg_protect_portfolio_verification ON public.portfolio_items;
CREATE TRIGGER trg_protect_portfolio_verification
    BEFORE UPDATE ON public.portfolio_items
    FOR EACH ROW EXECUTE FUNCTION public.protect_portfolio_verification();

-- Guard B: Protect enquiry participant integrity (immutable participants & initial message)
CREATE OR REPLACE FUNCTION public.protect_enquiry_immutable_fields()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.id <> OLD.id THEN
        RAISE EXCEPTION 'Enquiry id cannot be modified.';
    END IF;
    IF NEW.customer_id <> OLD.customer_id OR NEW.creator_id <> OLD.creator_id OR NEW.brief_id IS DISTINCT FROM OLD.brief_id THEN
        RAISE EXCEPTION 'Enquiry participants and linked briefs cannot be modified after creation.';
    END IF;
    IF NEW.subject <> OLD.subject OR NEW.message <> OLD.message THEN
        RAISE EXCEPTION 'Enquiry subject and initial message cannot be altered. Update negotiation status or parameters instead.';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SET search_path = public, pg_temp;

DROP TRIGGER IF EXISTS trg_protect_enquiry_immutable_fields ON public.enquiries;
CREATE TRIGGER trg_protect_enquiry_immutable_fields
    BEFORE UPDATE ON public.enquiries
    FOR EACH ROW EXECUTE FUNCTION public.protect_enquiry_immutable_fields();

-- Guard B2: Enforce enquiry status transition state machine
CREATE OR REPLACE FUNCTION public.enforce_enquiry_status_transitions()
RETURNS TRIGGER AS $$
DECLARE
    v_is_customer BOOLEAN;
    v_is_creator BOOLEAN;
BEGIN
    -- Caller role check
    v_is_customer := (auth.uid() = OLD.customer_id);
    v_is_creator := EXISTS (
        SELECT 1 FROM public.creators c 
        WHERE c.id = OLD.creator_id AND c.user_id = auth.uid()
    );

    -- Terminal states cannot transition to other states
    IF OLD.status IN ('declined', 'closed') AND NEW.status <> OLD.status THEN
        RAISE EXCEPTION 'Cannot modify enquiry in terminal state %.', OLD.status;
    END IF;

    -- Accepted agreements cannot be reverted to unaccepted states
    IF OLD.status = 'accepted' AND NEW.status NOT IN ('accepted', 'closed') THEN
        RAISE EXCEPTION 'Accepted enquiry represents a binding agreement and cannot be reverted to %.', NEW.status;
    END IF;

    -- Customer cannot accept their own pending enquiry
    IF v_is_customer AND NOT v_is_creator THEN
        IF OLD.status = 'pending' AND NEW.status = 'accepted' THEN
            RAISE EXCEPTION 'Customers cannot self-accept their own pending enquiry.';
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SET search_path = public, pg_temp;

DROP TRIGGER IF EXISTS trg_enforce_enquiry_status_transitions ON public.enquiries;
CREATE TRIGGER trg_enforce_enquiry_status_transitions
    BEFORE UPDATE ON public.enquiries
    FOR EACH ROW EXECUTE FUNCTION public.enforce_enquiry_status_transitions();

-- Guard C: Enforce creator interest status transition state machine & immutability
CREATE OR REPLACE FUNCTION public.enforce_pitch_update_rules()
RETURNS TRIGGER AS $$
DECLARE
    v_is_brief_owner BOOLEAN;
    v_is_creator BOOLEAN;
BEGIN
    -- Ownership immutability
    IF NEW.id <> OLD.id THEN
        RAISE EXCEPTION 'Pitch id cannot be modified.';
    END IF;
    IF NEW.brief_id <> OLD.brief_id OR NEW.creator_id <> OLD.creator_id THEN
        RAISE EXCEPTION 'Pitch brief_id and creator_id cannot be modified.';
    END IF;

    -- Check role of caller
    v_is_brief_owner := EXISTS (
        SELECT 1 FROM public.briefs b 
        WHERE b.id = OLD.brief_id AND b.customer_id = auth.uid()
    );
    v_is_creator := EXISTS (
        SELECT 1 FROM public.creators c 
        WHERE c.id = OLD.creator_id AND c.user_id = auth.uid()
    );

    -- State Machine Validation
    IF OLD.status = 'accepted' AND NEW.status <> 'accepted' THEN
        RAISE EXCEPTION 'An accepted pitch represents a binding agreement and cannot be reverted to %.', NEW.status;
    END IF;

    IF OLD.status IN ('declined', 'withdrawn') AND NEW.status <> OLD.status THEN
        RAISE EXCEPTION 'Cannot update pitch from terminal state % to %.', OLD.status, NEW.status;
    END IF;

    -- If caller is the creator
    IF v_is_creator AND NOT v_is_brief_owner THEN
        IF NEW.status IN ('accepted', 'shortlisted') AND OLD.status NOT IN ('accepted', 'shortlisted') THEN
            RAISE EXCEPTION 'Creators are forbidden from self-accepting or shortlisting their own pitch.';
        END IF;
    END IF;

    -- If caller is the customer (brief owner)
    IF v_is_brief_owner AND NOT v_is_creator THEN
        NEW.proposed_quote := OLD.proposed_quote;
        NEW.pitch_note := OLD.pitch_note;
        NEW.estimated_delivery_days := OLD.estimated_delivery_days;
        NEW.sample_portfolio_item_id := OLD.sample_portfolio_item_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SET search_path = public, pg_temp;

DROP TRIGGER IF EXISTS trg_enforce_pitch_update_rules ON public.creator_interests;
CREATE TRIGGER trg_enforce_pitch_update_rules
    BEFORE UPDATE ON public.creator_interests
    FOR EACH ROW EXECUTE FUNCTION public.enforce_pitch_update_rules();

-- Guard D: Prevent deletion of actively assigned or completed briefs (Contract Loss Prevention)
CREATE OR REPLACE FUNCTION public.prevent_active_brief_deletion()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status IN ('assigned', 'completed') THEN
        RAISE EXCEPTION 'Cannot delete brief %: brief is actively assigned or completed. Contract audit records must be preserved.', OLD.id;
    END IF;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql SET search_path = public, pg_temp;

DROP TRIGGER IF EXISTS trg_prevent_active_brief_deletion ON public.briefs;
CREATE TRIGGER trg_prevent_active_brief_deletion
    BEFORE DELETE ON public.briefs
    FOR EACH ROW EXECUTE FUNCTION public.prevent_active_brief_deletion();

-- Guard E: Enforce Brief Status Transition Rules & Ownership Immutability
CREATE OR REPLACE FUNCTION public.enforce_brief_status_transitions()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.id <> OLD.id THEN
        RAISE EXCEPTION 'Brief id cannot be modified.';
    END IF;
    IF NEW.customer_id <> OLD.customer_id THEN
        RAISE EXCEPTION 'Brief customer_id is immutable.';
    END IF;
    IF OLD.status = 'completed' AND NEW.status <> 'completed' THEN
        RAISE EXCEPTION 'Completed briefs cannot be reopened or modified.';
    END IF;
    IF OLD.status = 'cancelled' AND NEW.status <> 'cancelled' THEN
        RAISE EXCEPTION 'Cancelled briefs cannot be reopened.';
    END IF;
    IF OLD.status = 'assigned' AND NEW.status IN ('draft', 'open') THEN
        RAISE EXCEPTION 'An assigned brief cannot be demoted back to %.', NEW.status;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SET search_path = public, pg_temp;

DROP TRIGGER IF EXISTS trg_enforce_brief_status_transitions ON public.briefs;
CREATE TRIGGER trg_enforce_brief_status_transitions
    BEFORE UPDATE ON public.briefs
    FOR EACH ROW EXECUTE FUNCTION public.enforce_brief_status_transitions();

-- 11. ATTACH AUTOMATIC UPDATED_AT TRIGGERS
DROP TRIGGER IF EXISTS trg_users_updated_at ON public.users;
CREATE TRIGGER trg_users_updated_at BEFORE UPDATE ON public.users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trg_creators_updated_at ON public.creators;
CREATE TRIGGER trg_creators_updated_at BEFORE UPDATE ON public.creators FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trg_portfolio_items_updated_at ON public.portfolio_items;
CREATE TRIGGER trg_portfolio_items_updated_at BEFORE UPDATE ON public.portfolio_items FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trg_briefs_updated_at ON public.briefs;
CREATE TRIGGER trg_briefs_updated_at BEFORE UPDATE ON public.briefs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trg_enquiries_updated_at ON public.enquiries;
CREATE TRIGGER trg_enquiries_updated_at BEFORE UPDATE ON public.enquiries FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trg_creator_interests_updated_at ON public.creator_interests;
CREATE TRIGGER trg_creator_interests_updated_at BEFORE UPDATE ON public.creator_interests FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS trg_verification_signals_updated_at ON public.verification_signals;
CREATE TRIGGER trg_verification_signals_updated_at BEFORE UPDATE ON public.verification_signals FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 12. HIGH-PERFORMANCE INDEXES
CREATE INDEX IF NOT EXISTS idx_creators_skills_gin ON public.creators USING gin (skills);
CREATE INDEX IF NOT EXISTS idx_creators_tools_gin ON public.creators USING gin (tools);
CREATE INDEX IF NOT EXISTS idx_creators_styles_gin ON public.creators USING gin (styles);
CREATE INDEX IF NOT EXISTS idx_creators_content_types_gin ON public.creators USING gin (content_types);

CREATE INDEX IF NOT EXISTS idx_creators_display_name_trgm ON public.creators USING gin (display_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_creators_handle_trgm ON public.creators USING gin (handle gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_creators_availability ON public.creators (availability);
CREATE INDEX IF NOT EXISTS idx_creators_budget ON public.creators (indicative_budget_min, indicative_budget_max);
CREATE INDEX IF NOT EXISTS idx_creators_rating ON public.creators (rating DESC);

CREATE INDEX IF NOT EXISTS idx_portfolio_items_creator_id ON public.portfolio_items (creator_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_items_content_type ON public.portfolio_items (content_type);
CREATE INDEX IF NOT EXISTS idx_portfolio_items_style ON public.portfolio_items (style);
CREATE INDEX IF NOT EXISTS idx_portfolio_items_tools_gin ON public.portfolio_items USING gin (tools_used);

CREATE INDEX IF NOT EXISTS idx_briefs_customer_id ON public.briefs (customer_id);
CREATE INDEX IF NOT EXISTS idx_briefs_status ON public.briefs (status);
CREATE INDEX IF NOT EXISTS idx_briefs_skills_gin ON public.briefs USING gin (required_skills);

CREATE INDEX IF NOT EXISTS idx_enquiries_customer_id ON public.enquiries (customer_id);
CREATE INDEX IF NOT EXISTS idx_enquiries_creator_id ON public.enquiries (creator_id);
CREATE INDEX IF NOT EXISTS idx_enquiries_brief_id ON public.enquiries (brief_id);
CREATE INDEX IF NOT EXISTS idx_enquiries_status ON public.enquiries (status);

CREATE INDEX IF NOT EXISTS idx_creator_interests_brief_id ON public.creator_interests (brief_id);
CREATE INDEX IF NOT EXISTS idx_creator_interests_creator_id ON public.creator_interests (creator_id);
CREATE INDEX IF NOT EXISTS idx_creator_interests_status ON public.creator_interests (status);
CREATE INDEX IF NOT EXISTS idx_creator_interests_sample_portfolio_item_id ON public.creator_interests (sample_portfolio_item_id);

CREATE INDEX IF NOT EXISTS idx_verification_signals_creator_id ON public.verification_signals (creator_id);
CREATE INDEX IF NOT EXISTS idx_verification_signals_portfolio_item_id ON public.verification_signals (portfolio_item_id);
CREATE INDEX IF NOT EXISTS idx_verification_signals_status ON public.verification_signals (status);

-- 13. EXECUTION PRIVILEGE REVOCATIONS & LEAST-PRIVILEGE HARDENING
REVOKE ALL ON FUNCTION public.handle_new_user() FROM PUBLIC;
REVOKE ALL ON FUNCTION public.update_updated_at_column() FROM PUBLIC;
REVOKE ALL ON FUNCTION public.protect_user_profile() FROM PUBLIC;
REVOKE ALL ON FUNCTION public.protect_creator_reputation() FROM PUBLIC;
REVOKE ALL ON FUNCTION public.protect_portfolio_verification() FROM PUBLIC;
REVOKE ALL ON FUNCTION public.protect_enquiry_immutable_fields() FROM PUBLIC;
REVOKE ALL ON FUNCTION public.enforce_enquiry_status_transitions() FROM PUBLIC;
REVOKE ALL ON FUNCTION public.enforce_pitch_update_rules() FROM PUBLIC;
REVOKE ALL ON FUNCTION public.prevent_active_brief_deletion() FROM PUBLIC;
REVOKE ALL ON FUNCTION public.enforce_brief_status_transitions() FROM PUBLIC;

-- Grant execution to authenticated role if it exists (Supabase environment)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
        GRANT EXECUTE ON FUNCTION public.update_updated_at_column() TO authenticated;
        GRANT EXECUTE ON FUNCTION public.protect_user_profile() TO authenticated;
        GRANT EXECUTE ON FUNCTION public.protect_creator_reputation() TO authenticated;
        GRANT EXECUTE ON FUNCTION public.protect_portfolio_verification() TO authenticated;
        GRANT EXECUTE ON FUNCTION public.protect_enquiry_immutable_fields() TO authenticated;
        GRANT EXECUTE ON FUNCTION public.enforce_enquiry_status_transitions() TO authenticated;
        GRANT EXECUTE ON FUNCTION public.enforce_pitch_update_rules() TO authenticated;
        GRANT EXECUTE ON FUNCTION public.prevent_active_brief_deletion() TO authenticated;
        GRANT EXECUTE ON FUNCTION public.enforce_brief_status_transitions() TO authenticated;
    END IF;
END $$;
