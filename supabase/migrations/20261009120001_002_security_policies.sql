-- ============================================================================
-- Migration: 20261009120001_002_security_policies.sql
-- Project: CreatorSphere AI
-- Description: Hardened Row Level Security (RLS) policies protecting
--              private customer briefs, direct enquiries, creator editing rights,
--              pitch negotiation integrity, and trust badge verification.
-- ============================================================================

-- 1. ENABLE ROW LEVEL SECURITY ON ALL TABLES
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.creators ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.portfolio_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.briefs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.enquiries ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.creator_interests ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.verification_signals ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- 2. POLICIES: users
-- ============================================================================

-- Users can only view their own profile; private email and account details are protected
DROP POLICY IF EXISTS "Users profiles are viewable by everyone" ON public.users;
DROP POLICY IF EXISTS "Users can view own profile" ON public.users;
CREATE POLICY "Users can view own profile"
    ON public.users FOR SELECT
    USING (auth.uid() = id);

-- Authenticated users can insert their own profile during sign-up
DROP POLICY IF EXISTS "Users can insert their own profile" ON public.users;
CREATE POLICY "Users can insert their own profile"
    ON public.users FOR INSERT
    WITH CHECK (auth.uid() = id);

-- Users can only modify their own account profile
DROP POLICY IF EXISTS "Users can update their own profile" ON public.users;
CREATE POLICY "Users can update their own profile"
    ON public.users FOR UPDATE
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

-- ============================================================================
-- 3. POLICIES: creators
-- ============================================================================

-- Creator profiles are publicly discoverable in the marketplace search
DROP POLICY IF EXISTS "Creator profiles are publicly viewable" ON public.creators;
CREATE POLICY "Creator profiles are publicly viewable"
    ON public.creators FOR SELECT
    USING (true);

-- Authenticated creators can create their own profile
DROP POLICY IF EXISTS "Users can create their own creator profile" ON public.creators;
CREATE POLICY "Users can create their own creator profile"
    ON public.creators FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Creators can only update their own profile (reputation fields protected by database trigger)
DROP POLICY IF EXISTS "Creators can update their own profile" ON public.creators;
CREATE POLICY "Creators can update their own profile"
    ON public.creators FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Creators can delete their own profile
DROP POLICY IF EXISTS "Creators can delete their own profile" ON public.creators;
CREATE POLICY "Creators can delete their own profile"
    ON public.creators FOR DELETE
    USING (auth.uid() = user_id);

-- ============================================================================
-- 4. POLICIES: portfolio_items
-- ============================================================================

-- Portfolio samples are public for showcase and customer evaluation
DROP POLICY IF EXISTS "Portfolio items are publicly viewable" ON public.portfolio_items;
CREATE POLICY "Portfolio items are publicly viewable"
    ON public.portfolio_items FOR SELECT
    USING (true);

-- Creators can insert portfolio items with unverified/pending status (cannot self-verify)
DROP POLICY IF EXISTS "Creators can insert their own portfolio items" ON public.portfolio_items;
CREATE POLICY "Creators can insert their own portfolio items"
    ON public.portfolio_items FOR INSERT
    WITH CHECK (
        verification_status IN ('unverified', 'pending')
        AND creator_id IN (
            SELECT id FROM public.creators WHERE user_id = auth.uid()
        )
    );

-- Creators can update their portfolio items but cannot self-award 'verified' status
DROP POLICY IF EXISTS "Creators can update their own portfolio items" ON public.portfolio_items;
CREATE POLICY "Creators can update their own portfolio items"
    ON public.portfolio_items FOR UPDATE
    USING (
        creator_id IN (
            SELECT id FROM public.creators WHERE user_id = auth.uid()
        )
    )
    WITH CHECK (
        creator_id IN (
            SELECT id FROM public.creators WHERE user_id = auth.uid()
        )
        AND verification_status IN ('unverified', 'pending')
    );

-- Creators can delete their own portfolio items
DROP POLICY IF EXISTS "Creators can delete their own portfolio items" ON public.portfolio_items;
CREATE POLICY "Creators can delete their own portfolio items"
    ON public.portfolio_items FOR DELETE
    USING (
        creator_id IN (
            SELECT id FROM public.creators WHERE user_id = auth.uid()
        )
    );

-- ============================================================================
-- 5. POLICIES: briefs
-- ============================================================================

-- Public/creators can only see 'open' or 'in_review' briefs.
-- Customers can see ALL of their own briefs (including 'draft' and 'cancelled').
DROP POLICY IF EXISTS "Briefs visibility policy" ON public.briefs;
CREATE POLICY "Briefs visibility policy"
    ON public.briefs FOR SELECT
    USING (
        status IN ('open', 'in_review')
        OR (auth.uid() IS NOT NULL AND customer_id = auth.uid())
    );

-- Authenticated customers can create briefs linked to their user id
DROP POLICY IF EXISTS "Customers can create briefs" ON public.briefs;
CREATE POLICY "Customers can create briefs"
    ON public.briefs FOR INSERT
    WITH CHECK (
        auth.uid() IS NOT NULL AND customer_id = auth.uid()
    );

-- Customers can only update their own briefs
DROP POLICY IF EXISTS "Customers can update their own briefs" ON public.briefs;
CREATE POLICY "Customers can update their own briefs"
    ON public.briefs FOR UPDATE
    USING (customer_id = auth.uid())
    WITH CHECK (customer_id = auth.uid());

-- Customers can only delete non-contractual briefs (cannot delete assigned or completed briefs)
DROP POLICY IF EXISTS "Customers can delete their own briefs" ON public.briefs;
CREATE POLICY "Customers can delete their own briefs"
    ON public.briefs FOR DELETE
    USING (
        customer_id = auth.uid() 
        AND status IN ('draft', 'open', 'cancelled')
    );

-- ============================================================================
-- 6. POLICIES: enquiries
-- ============================================================================

-- Strictly private: Only the customer who sent it OR the recipient creator can read it
DROP POLICY IF EXISTS "Enquiries viewable by sender or recipient" ON public.enquiries;
CREATE POLICY "Enquiries viewable by sender or recipient"
    ON public.enquiries FOR SELECT
    USING (
        customer_id = auth.uid()
        OR creator_id IN (
            SELECT id FROM public.creators WHERE user_id = auth.uid()
        )
    );

-- Customers can send enquiries with pending status (cannot send enquiries to themselves)
DROP POLICY IF EXISTS "Customers can send enquiries" ON public.enquiries;
CREATE POLICY "Customers can send enquiries"
    ON public.enquiries FOR INSERT
    WITH CHECK (
        customer_id = auth.uid()
        AND status = 'pending'
        AND creator_id NOT IN (
            SELECT id FROM public.creators WHERE user_id = auth.uid()
        )
    );

-- Both participants can update status or messages with ownership lockdown
DROP POLICY IF EXISTS "Enquiry participants can update" ON public.enquiries;
CREATE POLICY "Enquiry participants can update"
    ON public.enquiries FOR UPDATE
    USING (
        customer_id = auth.uid()
        OR creator_id IN (
            SELECT id FROM public.creators WHERE user_id = auth.uid()
        )
    )
    WITH CHECK (
        customer_id = auth.uid()
        OR creator_id IN (
            SELECT id FROM public.creators WHERE user_id = auth.uid()
        )
    );

-- ============================================================================
-- 7. POLICIES: creator_interests
-- ============================================================================

-- The creator who pitched can see it; the customer who owns the brief can see all pitches
DROP POLICY IF EXISTS "Creator interests viewable by creator or brief owner" ON public.creator_interests;
CREATE POLICY "Creator interests viewable by creator or brief owner"
    ON public.creator_interests FOR SELECT
    USING (
        creator_id IN (
            SELECT id FROM public.creators WHERE user_id = auth.uid()
        )
        OR brief_id IN (
            SELECT id FROM public.briefs WHERE customer_id = auth.uid()
        )
    );

-- Creators can submit pitch interest on open customer briefs (cannot pitch on their own briefs)
DROP POLICY IF EXISTS "Creators can submit pitch interest" ON public.creator_interests;
CREATE POLICY "Creators can submit pitch interest"
    ON public.creator_interests FOR INSERT
    WITH CHECK (
        status = 'submitted'
        AND creator_id IN (
            SELECT id FROM public.creators WHERE user_id = auth.uid()
        )
        AND brief_id IN (
            SELECT id FROM public.briefs 
            WHERE status = 'open' AND customer_id <> auth.uid()
        )
    );

-- Hardened Creator Update: Creators can only edit their pending pitch or withdraw it
DROP POLICY IF EXISTS "Creators can update their pending pitch" ON public.creator_interests;
CREATE POLICY "Creators can update their pending pitch"
    ON public.creator_interests FOR UPDATE
    USING (
        creator_id IN (
            SELECT id FROM public.creators WHERE user_id = auth.uid()
        )
        AND status IN ('submitted', 'withdrawn')
    )
    WITH CHECK (
        creator_id IN (
            SELECT id FROM public.creators WHERE user_id = auth.uid()
        )
        AND status IN ('submitted', 'withdrawn')
    );

-- Hardened Customer Update: Brief owners can update pitch status (shortlist, accept, decline)
DROP POLICY IF EXISTS "Brief owners can update pitch status" ON public.creator_interests;
CREATE POLICY "Brief owners can update pitch status"
    ON public.creator_interests FOR UPDATE
    USING (
        brief_id IN (
            SELECT id FROM public.briefs WHERE customer_id = auth.uid()
        )
    )
    WITH CHECK (
        brief_id IN (
            SELECT id FROM public.briefs WHERE customer_id = auth.uid()
        )
        AND status IN ('submitted', 'shortlisted', 'accepted', 'declined')
    );

-- ============================================================================
-- 8. POLICIES: verification_signals
-- ============================================================================

-- Verified signals are publicly visible to build trust; pending signals visible only to the creator
DROP POLICY IF EXISTS "Verified signals viewable publicly, pending by creator" ON public.verification_signals;
CREATE POLICY "Verified signals viewable publicly, pending by creator"
    ON public.verification_signals FOR SELECT
    USING (
        status = 'verified'
        OR creator_id IN (
            SELECT id FROM public.creators WHERE user_id = auth.uid()
        )
    );

-- Hardened Submission: Creators can ONLY submit verification evidence with status = 'pending'
-- Self-approval is strictly impossible at the database level!
DROP POLICY IF EXISTS "Creators can submit verification evidence" ON public.verification_signals;
CREATE POLICY "Creators can submit verification evidence"
    ON public.verification_signals FOR INSERT
    WITH CHECK (
        status = 'pending'
        AND verified_at IS NULL
        AND creator_id IN (
            SELECT id FROM public.creators WHERE user_id = auth.uid()
        )
    );

-- Note: No UPDATE or DELETE policy is granted to ordinary users on verification_signals.
-- Only administrative service_role calls or trusted backend reviewers can approve verification signals.
