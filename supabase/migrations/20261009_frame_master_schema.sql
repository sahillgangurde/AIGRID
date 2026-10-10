-- ============================================================================
-- FRAME — AI Creator Marketplace Master PostgreSQL Schema & RLS Policies
-- Compatible with Supabase PostgreSQL, Row Level Security (RLS), and Triggers
-- ============================================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- A. IDENTITY AND PROFILES
-- ============================================================================

-- Table: profiles
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username TEXT UNIQUE NOT NULL,
    normalized_username TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    avatar_url TEXT,
    bio TEXT,
    role TEXT NOT NULL CHECK (role IN ('creator', 'brand', 'admin')),
    account_status TEXT NOT NULL DEFAULT 'active' CHECK (account_status IN ('active', 'suspended', 'pending_review')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Reserved usernames table & validation
CREATE TABLE IF NOT EXISTS reserved_usernames (
    username TEXT PRIMARY KEY
);

INSERT INTO reserved_usernames (username) VALUES
('admin'), ('root'), ('system'), ('frame'), ('support'), ('moderator'), ('official'), ('api'), ('auth'), ('security')
ON CONFLICT DO NOTHING;

CREATE OR REPLACE FUNCTION check_username_allowed()
RETURNS TRIGGER AS $$
BEGIN
    NEW.normalized_username := LOWER(TRIM(NEW.username));
    
    -- Format validation: alphanumeric + underscores/hyphens, 3-30 chars
    IF NOT (NEW.normalized_username ~ '^[a-z0-9_-]{3,30}$') THEN
        RAISE EXCEPTION 'Username must be 3-30 characters and contain only lowercase letters, numbers, underscores, and hyphens.';
    END IF;

    -- Check reserved names
    IF EXISTS (SELECT 1 FROM reserved_usernames WHERE username = NEW.normalized_username) THEN
        RAISE EXCEPTION 'Username is reserved by the platform.';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_normalize_username ON profiles;
CREATE TRIGGER trigger_normalize_username
    BEFORE INSERT OR UPDATE OF username ON profiles
    FOR EACH ROW
    EXECUTE FUNCTION check_username_allowed();

-- Table: creator_profiles
CREATE TABLE IF NOT EXISTS creator_profiles (
    user_id UUID PRIMARY KEY REFERENCES profiles(id) ON DELETE CASCADE,
    specializations TEXT[] NOT NULL DEFAULT '{}',
    skills TEXT[] NOT NULL DEFAULT '{}',
    industries TEXT[] NOT NULL DEFAULT '{}',
    ai_tools TEXT[] NOT NULL DEFAULT '{}',
    ai_models TEXT[] NOT NULL DEFAULT '{}',
    workflow_description TEXT,
    experience_years NUMERIC(4,1) DEFAULT 1.0,
    supported_content_types TEXT[] NOT NULL DEFAULT '{}',
    supported_platforms TEXT[] NOT NULL DEFAULT '{}',
    aspect_ratios TEXT[] NOT NULL DEFAULT '{}',
    minimum_budget NUMERIC(12,2) DEFAULT 0.0,
    maximum_budget NUMERIC(12,2),
    availability_status TEXT NOT NULL DEFAULT 'available' CHECK (availability_status IN ('available', 'busy', 'unavailable')),
    accepting_projects BOOLEAN NOT NULL DEFAULT true,
    profile_visibility TEXT NOT NULL DEFAULT 'public' CHECK (profile_visibility IN ('public', 'private', 'unlisted')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Table: brand_profiles
CREATE TABLE IF NOT EXISTS brand_profiles (
    user_id UUID PRIMARY KEY REFERENCES profiles(id) ON DELETE CASCADE,
    brand_name TEXT NOT NULL,
    public_alias TEXT NOT NULL,
    visibility_mode TEXT NOT NULL DEFAULT 'public' CHECK (visibility_mode IN ('public', 'confidential')),
    industry TEXT,
    organization_details JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- B. PORTFOLIO AND FEED
-- ============================================================================

-- Table: portfolio_items
CREATE TABLE IF NOT EXISTS portfolio_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creator_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    content_type TEXT NOT NULL,
    media_path TEXT NOT NULL,
    thumbnail_path TEXT,
    skills TEXT[] NOT NULL DEFAULT '{}',
    industries TEXT[] NOT NULL DEFAULT '{}',
    style_tags TEXT[] NOT NULL DEFAULT '{}',
    ai_tools TEXT[] NOT NULL DEFAULT '{}',
    ai_models TEXT[] NOT NULL DEFAULT '{}',
    workflow JSONB,
    aspect_ratio TEXT NOT NULL DEFAULT '16:9',
    creator_role TEXT,
    visibility TEXT NOT NULL DEFAULT 'public' CHECK (visibility_mode IN ('public', 'unlisted', 'private', 'requires_approval')),
    evidence_status TEXT NOT NULL DEFAULT 'unverified' CHECK (evidence_status IN ('unverified', 'ast_verified', 'c2pa_signed', 'disputed')),
    rights_status TEXT NOT NULL DEFAULT 'creator_owned' CHECK (rights_status IN ('creator_owned', 'client_licensed', 'public_domain', 'restricted')),
    published_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Table: feed_posts
CREATE TABLE IF NOT EXISTS feed_posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creator_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    portfolio_item_id UUID REFERENCES portfolio_items(id) ON DELETE SET NULL,
    caption TEXT,
    media_path TEXT NOT NULL,
    thumbnail_path TEXT,
    content_type TEXT NOT NULL,
    style_tags TEXT[] NOT NULL DEFAULT '{}',
    ai_tools TEXT[] NOT NULL DEFAULT '{}',
    ai_models TEXT[] NOT NULL DEFAULT '{}',
    visibility TEXT NOT NULL DEFAULT 'public' CHECK (visibility IN ('public', 'private', 'restricted')),
    moderation_status TEXT NOT NULL DEFAULT 'approved' CHECK (moderation_status IN ('pending', 'approved', 'flagged', 'removed')),
    published_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Table: likes
CREATE TABLE IF NOT EXISTS likes (
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    post_id UUID NOT NULL REFERENCES feed_posts(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, post_id)
);

-- Table: saves
CREATE TABLE IF NOT EXISTS saves (
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    post_id UUID NOT NULL REFERENCES feed_posts(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, post_id)
);

-- Table: follows
CREATE TABLE IF NOT EXISTS follows (
    follower_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    followed_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (follower_id, followed_id),
    CONSTRAINT disallow_self_follow CHECK (follower_id <> followed_id)
);

-- ============================================================================
-- C. VERIFICATION AND ACHIEVEMENTS
-- ============================================================================

-- Table: verification_records
CREATE TABLE IF NOT EXISTS verification_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    verification_type TEXT NOT NULL,
    provider_reference TEXT,
    status TEXT NOT NULL DEFAULT 'not_started' CHECK (status IN ('not_started', 'pending', 'verified', 'failed', 'needs_review')),
    is_demo BOOLEAN NOT NULL DEFAULT true,
    verified_at TIMESTAMPTZ,
    last_updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Table: achievement_definitions
CREATE TABLE IF NOT EXISTS achievement_definitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    eligibility_rules JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Table: user_achievements
CREATE TABLE IF NOT EXISTS user_achievements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    achievement_id UUID NOT NULL REFERENCES achievement_definitions(id) ON DELETE CASCADE,
    earned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    evidence_reference TEXT,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'revoked', 'under_review')),
    UNIQUE (user_id, achievement_id)
);

-- Table: trust_events
CREATE TABLE IF NOT EXISTS trust_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creator_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    project_id UUID,
    event_type TEXT NOT NULL CHECK (event_type IN ('project_completed_on_time', 'project_completed_late', 'repeat_client_hired', 'documented_milestone_sealed', 'client_dispute_filed', 'client_dispute_resolved')),
    event_status TEXT NOT NULL DEFAULT 'verified' CHECK (event_status IN ('pending', 'verified', 'disputed', 'rejected')),
    evidence_reference TEXT,
    reviewed_by UUID REFERENCES profiles(id),
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- D. BRIEFS AND MATCHING
-- ============================================================================

-- Table: creative_briefs
CREATE TABLE IF NOT EXISTS creative_briefs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    brand_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    objective TEXT NOT NULL,
    industry TEXT,
    target_audience TEXT,
    description TEXT,
    deliverables TEXT[] NOT NULL DEFAULT '{}',
    content_types TEXT[] NOT NULL DEFAULT '{}',
    creative_style TEXT,
    platforms TEXT[] NOT NULL DEFAULT '{}',
    aspect_ratios TEXT[] NOT NULL DEFAULT '{}',
    resolution_requirements TEXT,
    video_duration INT DEFAULT 30,
    quantity INT DEFAULT 1,
    budget_min NUMERIC(12,2) NOT NULL DEFAULT 0.0,
    budget_max NUMERIC(12,2) NOT NULL DEFAULT 0.0,
    currency TEXT NOT NULL DEFAULT 'INR',
    deadline TIMESTAMPTZ,
    revision_requirements TEXT,
    commercial_use_requirements TEXT,
    usage_territory TEXT DEFAULT 'Worldwide',
    license_duration TEXT DEFAULT '1 Year',
    exclusivity_requirements TEXT,
    confidentiality_requirements TEXT DEFAULT 'public' CHECK (confidentiality_requirements IN ('public', 'confidential')),
    acceptance_criteria TEXT,
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('draft', 'open', 'in_review', 'awarded', 'completed', 'closed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Table: match_results
CREATE TABLE IF NOT EXISTS match_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    brief_id UUID NOT NULL REFERENCES creative_briefs(id) ON DELETE CASCADE,
    creator_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    match_score NUMERIC(5,2) NOT NULL,
    component_scores JSONB NOT NULL DEFAULT '{}'::jsonb,
    match_reasons TEXT[] NOT NULL DEFAULT '{}',
    compatibility_gaps TEXT[] NOT NULL DEFAULT '{}',
    rights_status TEXT NOT NULL DEFAULT 'clear',
    calculated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (brief_id, creator_id)
);

-- ============================================================================
-- E. SHORTLISTS
-- ============================================================================

-- Table: shortlists
CREATE TABLE IF NOT EXISTS shortlists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    brief_id UUID REFERENCES creative_briefs(id) ON DELETE SET NULL,
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Table: shortlist_items
CREATE TABLE IF NOT EXISTS shortlist_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shortlist_id UUID NOT NULL REFERENCES shortlists(id) ON DELETE CASCADE,
    creator_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (shortlist_id, creator_id)
);

-- ============================================================================
-- F. COLLABORATIONS
-- ============================================================================

-- Table: collaborations
CREATE TABLE IF NOT EXISTS collaborations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID,
    initiator_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    invitee_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'rejected', 'withdrawn', 'completed')),
    roles TEXT[] NOT NULL DEFAULT '{}',
    attribution_details TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT disallow_self_collab CHECK (initiator_id <> invitee_id)
);

-- ============================================================================
-- G. PORTFOLIO PUBLICATION APPROVALS
-- ============================================================================

-- Table: portfolio_approval_requests
CREATE TABLE IF NOT EXISTS portfolio_approval_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID,
    creator_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    client_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    portfolio_item_id UUID REFERENCES portfolio_items(id) ON DELETE SET NULL,
    requested_media_scope TEXT NOT NULL,
    requested_metadata_scope TEXT NOT NULL,
    requested_platforms TEXT[] NOT NULL DEFAULT '{}',
    embargo_until TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'pending_approval' CHECK (status IN ('draft', 'pending_approval', 'changes_requested', 'approved', 'rejected', 'expired', 'revoked')),
    decision_notes TEXT,
    decided_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- H. PROJECTS AND MILESTONES
-- ============================================================================

-- Table: projects
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    brand_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    creator_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    brief_id UUID REFERENCES creative_briefs(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'in_discussion' CHECK (status IN ('draft', 'contacted', 'in_discussion', 'in_production', 'submitted_for_review', 'revision_requested', 'delivered', 'cancelled', 'disputed')),
    visibility_mode TEXT NOT NULL DEFAULT 'public' CHECK (visibility_mode IN ('public', 'confidential')),
    budget_amount NUMERIC(12,2) NOT NULL DEFAULT 0.0,
    currency TEXT NOT NULL DEFAULT 'INR',
    start_date TIMESTAMPTZ DEFAULT NOW(),
    deadline TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Table: project_milestones
CREATE TABLE IF NOT EXISTS project_milestones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    due_date TIMESTAMPTZ,
    amount NUMERIC(12,2) DEFAULT 0.0,
    percentage INT DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'submitted', 'approved', 'rejected')),
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- I. MESSAGING
-- ============================================================================

-- Table: conversations
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_by UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    conversation_type TEXT NOT NULL DEFAULT 'direct' CHECK (conversation_type IN ('direct', 'project', 'collaboration')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Table: conversation_participants
CREATE TABLE IF NOT EXISTS conversation_participants (
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_read_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (conversation_id, user_id)
);

-- Table: messages
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    sender_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    body TEXT NOT NULL,
    attachment_reference TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    edited_at TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ
);

-- ============================================================================
-- J. FINANCIAL RECORDS
-- ============================================================================

-- Table: transactions
CREATE TABLE IF NOT EXISTS transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    brand_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    creator_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    gross_amount NUMERIC(12,2) NOT NULL,
    platform_fee NUMERIC(12,2) NOT NULL,
    net_amount NUMERIC(12,2) NOT NULL,
    currency TEXT NOT NULL DEFAULT 'INR',
    status TEXT NOT NULL DEFAULT 'demo_completed' CHECK (status IN ('pending', 'held_in_escrow', 'released', 'refunded', 'disputed', 'demo_completed')),
    provider_reference TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Table: payout_records
CREATE TABLE IF NOT EXISTS payout_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creator_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    transaction_id UUID REFERENCES transactions(id) ON DELETE SET NULL,
    amount NUMERIC(12,2) NOT NULL,
    currency TEXT NOT NULL DEFAULT 'INR',
    status TEXT NOT NULL DEFAULT 'demo_settled' CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'demo_settled')),
    provider_reference TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Table: subscriptions
CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    plan_code TEXT NOT NULL CHECK (plan_code IN ('free_creator', 'pro_creator', 'studio_brand', 'enterprise_brand')),
    status TEXT NOT NULL DEFAULT 'demo_active' CHECK (status IN ('active', 'past_due', 'cancelled', 'demo_active')),
    billing_provider TEXT DEFAULT 'demo_provider',
    provider_subscription_reference TEXT,
    current_period_start TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    current_period_end TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '30 days'),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- K. ADMINISTRATION AND MODERATION
-- ============================================================================

-- Table: reports
CREATE TABLE IF NOT EXISTS reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reporter_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    target_type TEXT NOT NULL CHECK (target_type IN ('profile', 'post', 'brief', 'message')),
    target_id UUID NOT NULL,
    reason TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'under_review', 'resolved', 'dismissed')),
    reviewed_by UUID REFERENCES profiles(id),
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Table: audit_logs
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_id UUID REFERENCES profiles(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id UUID,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- INDEXES FOR HIGH-PERFORMANCE SEARCH & FILTERING
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_profiles_username ON profiles(normalized_username);
CREATE INDEX IF NOT EXISTS idx_creator_specializations ON creator_profiles USING GIN (specializations);
CREATE INDEX IF NOT EXISTS idx_creator_skills ON creator_profiles USING GIN (skills);
CREATE INDEX IF NOT EXISTS idx_creator_tools ON creator_profiles USING GIN (ai_tools);
CREATE INDEX IF NOT EXISTS idx_feed_posts_creator ON feed_posts(creator_id);
CREATE INDEX IF NOT EXISTS idx_feed_posts_published ON feed_posts(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_briefs_status ON creative_briefs(status);
CREATE INDEX IF NOT EXISTS idx_projects_brand ON projects(brand_id);
CREATE INDEX IF NOT EXISTS idx_projects_creator ON projects(creator_id);
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id, created_at ASC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_actor ON audit_logs(actor_id);

-- ============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================================================

ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE creator_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE brand_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE portfolio_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE feed_posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE likes ENABLE ROW LEVEL SECURITY;
ALTER TABLE saves ENABLE ROW LEVEL SECURITY;
ALTER TABLE follows ENABLE ROW LEVEL SECURITY;
ALTER TABLE verification_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_achievements ENABLE ROW LEVEL SECURITY;
ALTER TABLE trust_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE creative_briefs ENABLE ROW LEVEL SECURITY;
ALTER TABLE shortlists ENABLE ROW LEVEL SECURITY;
ALTER TABLE shortlist_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE collaborations ENABLE ROW LEVEL SECURITY;
ALTER TABLE portfolio_approval_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE project_milestones ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversation_participants ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE payout_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- 1. Profiles: Public read, self update only
CREATE POLICY "Public profiles are viewable by everyone" 
ON profiles FOR SELECT USING (true);

CREATE POLICY "Users can update their own profile" 
ON profiles FOR UPDATE USING (auth.uid() = id);

-- 2. Brand Profiles: Confidential details hidden from unauthorized users
CREATE POLICY "Brand profiles viewable with confidentiality check"
ON brand_profiles FOR SELECT USING (
    visibility_mode = 'public' 
    OR auth.uid() = user_id 
    OR EXISTS (
        SELECT 1 FROM projects WHERE brand_id = brand_profiles.user_id AND creator_id = auth.uid()
    )
);

-- 3. Confidential Briefs: Accessible only by owning brand and matched/assigned creators
CREATE POLICY "Creative briefs access policy"
ON creative_briefs FOR SELECT USING (
    confidentiality_requirements = 'public'
    OR auth.uid() = brand_id
    OR EXISTS (
        SELECT 1 FROM match_results WHERE brief_id = creative_briefs.id AND creator_id = auth.uid()
    )
    OR EXISTS (
        SELECT 1 FROM projects WHERE brief_id = creative_briefs.id AND creator_id = auth.uid()
    )
);

-- 4. Projects: Participants only
CREATE POLICY "Projects accessible by participants"
ON projects FOR SELECT USING (
    auth.uid() = brand_id OR auth.uid() = creator_id
);

-- 5. Messages: Conversation participants only
CREATE POLICY "Messages accessible by conversation participants"
ON messages FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM conversation_participants 
        WHERE conversation_id = messages.conversation_id AND user_id = auth.uid()
    )
);

CREATE POLICY "Messages insertable by conversation participants"
ON messages FOR INSERT WITH CHECK (
    auth.uid() = sender_id AND
    EXISTS (
        SELECT 1 FROM conversation_participants 
        WHERE conversation_id = messages.conversation_id AND user_id = auth.uid()
    )
);

-- 6. Financial records: Only participants
CREATE POLICY "Transactions viewable by project participants"
ON transactions FOR SELECT USING (
    auth.uid() = brand_id OR auth.uid() = creator_id
);

-- 7. Audit logs: Admins only
CREATE POLICY "Audit logs viewable only by admins"
ON audit_logs FOR SELECT USING (
    EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'admin')
);
