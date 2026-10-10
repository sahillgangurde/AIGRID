-- ============================================================================
-- Migration: 20261010000000_004_secure_marketplace_triggers.sql
-- Project: CreatorGrid (CreatorSphere AI / FRAME)
-- Description: Phase 1 & 2 Security Automation & Triggers:
--              1. Confidential Brand Mode: is_confidential flags & masked_brand_name.
--              2. Automated Contact Unlock Trigger: on payment status = 'succeeded'.
--              3. Database-Level POSIX Regex Chat Interception & Moderation Logging.
-- Hardening:   Strict search_path, SECURITY DEFINER encapsulation, idempotent triggers.
-- ============================================================================

-- ============================================================================
-- 1. CONFIDENTIAL BRAND MODE SCHEMA ALIGNMENT
-- ============================================================================

-- A. Support is_confidential on public.briefs (Core schema)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'briefs') THEN
        ALTER TABLE public.briefs 
            ADD COLUMN IF NOT EXISTS is_confidential BOOLEAN NOT NULL DEFAULT false,
            ADD COLUMN IF NOT EXISTS masked_brand_name TEXT DEFAULT 'Confidential Brand Partner';
        
        -- Backfill existing confidential briefs
        UPDATE public.briefs 
        SET masked_brand_name = 'Confidential Brand Partner' 
        WHERE masked_brand_name IS NULL;
    END IF;
END $$;

-- B. Support is_confidential on public.creative_briefs (Master / Unified schema if present)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'creative_briefs') THEN
        ALTER TABLE public.creative_briefs 
            ADD COLUMN IF NOT EXISTS is_confidential BOOLEAN NOT NULL DEFAULT false,
            ADD COLUMN IF NOT EXISTS masked_brand_name TEXT DEFAULT 'Confidential Brand Partner';

        UPDATE public.creative_briefs
        SET is_confidential = (confidentiality_requirements = 'confidential')
        WHERE confidentiality_requirements IS NOT NULL;
    END IF;
END $$;

-- C. Support is_confidential on public.brand_profiles
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'brand_profiles') THEN
        ALTER TABLE public.brand_profiles 
            ADD COLUMN IF NOT EXISTS is_confidential BOOLEAN NOT NULL DEFAULT false,
            ADD COLUMN IF NOT EXISTS masked_brand_name TEXT DEFAULT 'Confidential Brand Partner';
    END IF;
END $$;

-- D. Support is_confidential on public.users
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'users') THEN
        ALTER TABLE public.users 
            ADD COLUMN IF NOT EXISTS is_confidential BOOLEAN NOT NULL DEFAULT false;
    END IF;
END $$;

-- E. Helper trigger: Auto-populate masked_brand_name when brief is marked confidential
CREATE OR REPLACE FUNCTION public.handle_brief_confidentiality()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_confidential = true AND (NEW.masked_brand_name IS NULL OR TRIM(NEW.masked_brand_name) = '') THEN
        NEW.masked_brand_name := 'Confidential Brand Partner';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SET search_path = public, pg_temp;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'briefs') THEN
        DROP TRIGGER IF EXISTS trg_handle_brief_confidentiality ON public.briefs;
        CREATE TRIGGER trg_handle_brief_confidentiality
            BEFORE INSERT OR UPDATE ON public.briefs
            FOR EACH ROW EXECUTE FUNCTION public.handle_brief_confidentiality();
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'creative_briefs') THEN
        DROP TRIGGER IF EXISTS trg_handle_creative_brief_confidentiality ON public.creative_briefs;
        CREATE TRIGGER trg_handle_creative_brief_confidentiality
            BEFORE INSERT OR UPDATE ON public.creative_briefs
            FOR EACH ROW EXECUTE FUNCTION public.handle_brief_confidentiality();
    END IF;
END $$;


-- ============================================================================
-- 2. AUTOMATED CONTACT UNLOCK TRIGGER ON ADVANCE PAYMENT
-- ============================================================================

-- Automatically provisions an active record in public.contact_unlocks
-- when a payment status transitions to 'succeeded'.
CREATE OR REPLACE FUNCTION public.trg_auto_unlock_contact_on_payment()
RETURNS TRIGGER AS $$
DECLARE
    v_creator_id UUID;
    v_customer_id UUID;
    v_project_id UUID;
BEGIN
    -- Only trigger on transition to 'succeeded'
    IF NEW.status = 'succeeded' AND (OLD.status IS NULL OR OLD.status <> 'succeeded') THEN
        v_customer_id := NEW.customer_id;
        v_project_id := NEW.project_id;

        -- 1. Attempt to derive creator_id from associated project
        IF v_project_id IS NOT NULL THEN
            SELECT p.creator_id, p.customer_id 
            INTO v_creator_id, v_customer_id
            FROM public.projects p
            WHERE p.id = v_project_id;
        END IF;

        -- 2. Fallback: derive creator_id from project quote if project is not yet linked
        IF v_creator_id IS NULL AND NEW.quote_id IS NOT NULL THEN
            SELECT q.creator_id 
            INTO v_creator_id
            FROM public.project_quotes q
            WHERE q.id = NEW.quote_id;
        END IF;

        -- 3. Fallback: check metadata payload for creator_id
        IF v_creator_id IS NULL AND NEW.metadata IS NOT NULL AND NEW.metadata ? 'creator_id' THEN
            BEGIN
                v_creator_id := (NEW.metadata->>'creator_id')::uuid;
            EXCEPTION WHEN OTHERS THEN
                v_creator_id := NULL;
            END;
        END IF;

        -- If creator and customer are resolved, provision or activate contact unlock
        IF v_creator_id IS NOT NULL AND v_customer_id IS NOT NULL THEN
            INSERT INTO public.contact_unlocks (
                customer_id,
                creator_id,
                project_id,
                payment_id,
                status,
                unlocked_at
            ) VALUES (
                v_customer_id,
                v_creator_id,
                v_project_id,
                NEW.id,
                'active',
                CURRENT_TIMESTAMP
            )
            ON CONFLICT (customer_id, creator_id) DO UPDATE 
            SET status = 'active',
                payment_id = EXCLUDED.payment_id,
                project_id = COALESCE(EXCLUDED.project_id, public.contact_unlocks.project_id),
                unlocked_at = CURRENT_TIMESTAMP;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp;

-- Attach trigger to public.payments
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'payments') THEN
        DROP TRIGGER IF EXISTS trg_auto_unlock_contact_on_payment ON public.payments;
        CREATE TRIGGER trg_auto_unlock_contact_on_payment
            AFTER UPDATE OF status ON public.payments
            FOR EACH ROW EXECUTE FUNCTION public.trg_auto_unlock_contact_on_payment();

        -- Also handle payments inserted directly as succeeded (e.g. backend sync)
        DROP TRIGGER IF EXISTS trg_auto_unlock_contact_on_insert ON public.payments;
        CREATE TRIGGER trg_auto_unlock_contact_on_insert
            AFTER INSERT ON public.payments
            FOR EACH ROW 
            WHEN (NEW.status = 'succeeded')
            EXECUTE FUNCTION public.trg_auto_unlock_contact_on_payment();
    END IF;
END $$;


-- ============================================================================
-- 3. DATABASE-LEVEL CHAT PII INTERCEPTION & MODERATION TRIGGER
-- ============================================================================

-- POSIX Regex Patterns:
--  - Indian 10-digit mobile: [6-9][0-9]{9}
--  - International / standard phones: +?[0-9]{1,3}[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}
--  - Email addresses: [a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}
--  - UPI IDs: [a-zA-Z0-9._-]{3,}@(upi|paytm|phonepe|gpay|okaxis|okhdfcbank|ybl|ibl|oksbi|okicici)
--  - Social handles: @[a-zA-Z0-9_.]{3,30}
--  - External bypass keywords: whatsapp|wa\.me|telegram|t\.me|linkedin|call me|dm me

CREATE OR REPLACE FUNCTION public.intercept_chat_message_pii()
RETURNS TRIGGER AS $$
DECLARE
    v_has_violation BOOLEAN := false;
    v_cleaned TEXT;
BEGIN
    v_cleaned := NEW.content;

    -- 1. Scan & Redact Email Addresses
    IF v_cleaned ~* '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}' THEN
        v_has_violation := true;
        v_cleaned := regexp_replace(
            v_cleaned, 
            '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', 
            '✉️ [Email Blocked]', 
            'gi'
        );
    END IF;

    -- 2. Scan & Redact UPI IDs
    IF v_cleaned ~* '[a-zA-Z0-9._-]{3,}@(upi|paytm|phonepe|gpay|okaxis|okhdfcbank|ybl|ibl|oksbi|okicici)' THEN
        v_has_violation := true;
        v_cleaned := regexp_replace(
            v_cleaned, 
            '[a-zA-Z0-9._-]{3,}@(upi|paytm|phonepe|gpay|okaxis|okhdfcbank|ybl|ibl|oksbi|okicici)', 
            '💳 [UPI Blocked]', 
            'gi'
        );
    END IF;

    -- 3. Scan & Redact Indian & International Phone Numbers
    IF v_cleaned ~* '(^|[^0-9])([6-9][0-9]{9})([^0-9]|$)' OR 
       v_cleaned ~* '(\+?[0-9]{1,3}[\s.-]?)?\(?[0-9]{3}\)?[\s.-]?[0-9]{3}[\s.-]?[0-9]{4}' THEN
        v_has_violation := true;
        v_cleaned := regexp_replace(
            v_cleaned, 
            '(^|[^0-9])([6-9][0-9]{9})([^0-9]|$)', 
            '\1📵 [Phone Blocked]\3', 
            'g'
        );
        v_cleaned := regexp_replace(
            v_cleaned, 
            '(\+?[0-9]{1,3}[\s.-]?)?\(?[0-9]{3}\)?[\s.-]?[0-9]{3}[\s.-]?[0-9]{4}', 
            '📵 [Phone Blocked]', 
            'g'
        );
    END IF;

    -- 4. Scan & Redact External Platform Evasion Links & Keywords
    IF v_cleaned ~* '(whatsapp|wa\.me|telegram|t\.me|linkedin\.com)' THEN
        v_has_violation := true;
        v_cleaned := regexp_replace(
            v_cleaned, 
            '(whatsapp|wa\.me|telegram|t\.me|linkedin\.com)', 
            '🚫 [External App Blocked]', 
            'gi'
        );
    END IF;

    -- If violations detected, apply redacted content and update status
    IF v_has_violation THEN
        NEW.content := v_cleaned;
        NEW.moderation_status := 'redacted';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp;

-- After-trigger: record moderation log audit trail
CREATE OR REPLACE FUNCTION public.log_chat_moderation_event()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.moderation_status = 'redacted' AND (OLD IS NULL OR OLD.moderation_status <> 'redacted') THEN
        IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'message_moderation_logs') THEN
            INSERT INTO public.message_moderation_logs (
                message_id,
                flagged_by,
                detection_category,
                redacted_snippet,
                moderation_decision,
                created_at
            ) VALUES (
                NEW.id,
                'system_regex',
                'other',
                SUBSTRING(NEW.content, 1, 200),
                'redacted',
                CURRENT_TIMESTAMP
            );
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp;

-- Attach triggers to public.chat_messages
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'chat_messages') THEN
        DROP TRIGGER IF EXISTS trg_intercept_chat_message_pii ON public.chat_messages;
        CREATE TRIGGER trg_intercept_chat_message_pii
            BEFORE INSERT OR UPDATE OF content ON public.chat_messages
            FOR EACH ROW EXECUTE FUNCTION public.intercept_chat_message_pii();

        DROP TRIGGER IF EXISTS trg_log_chat_moderation_event ON public.chat_messages;
        CREATE TRIGGER trg_log_chat_moderation_event
            AFTER INSERT OR UPDATE OF moderation_status ON public.chat_messages
            FOR EACH ROW EXECUTE FUNCTION public.log_chat_moderation_event();
    END IF;
END $$;

-- Also support unified public.messages if present
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'messages') THEN
        -- Add moderation_status column if missing
        ALTER TABLE public.messages ADD COLUMN IF NOT EXISTS moderation_status TEXT NOT NULL DEFAULT 'allowed';

        DROP TRIGGER IF EXISTS trg_intercept_unified_message_pii ON public.messages;
        CREATE TRIGGER trg_intercept_unified_message_pii
            BEFORE INSERT OR UPDATE OF body ON public.messages
            FOR EACH ROW 
            WHEN (NEW.body ~* '([0-9]{10}|@[a-zA-Z0-9._%+-]+|whatsapp|telegram)')
            EXECUTE FUNCTION public.intercept_chat_message_pii();
    END IF;
END $$;
