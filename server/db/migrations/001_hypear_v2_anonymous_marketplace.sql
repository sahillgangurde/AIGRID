-- ============================================================
-- Hypear AI v2.0 — Database Migrations
-- Phase 1: Anonymous Marketplace Schema
-- Run ONCE on your PostgreSQL database before starting the server
-- Date: October 2026
-- ============================================================

-- 1. Extensions (required for pgvector and UUID generation)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgcrypto;
-- For vector similarity search (Phase 5):
-- CREATE EXTENSION IF NOT EXISTS vector;


-- 2. Alter existing 'profiles' table
--    These columns are added by SQLAlchemy's create_all() if using SQLite.
--    For PostgreSQL with existing data, run these explicitly:

ALTER TABLE profiles
    ADD COLUMN IF NOT EXISTS masked_alias VARCHAR(100),
    ADD COLUMN IF NOT EXISTS anonymous_mode BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS pii_violation_count INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS fcm_token TEXT;

-- Index for alias lookup
CREATE INDEX IF NOT EXISTS idx_profiles_masked_alias
    ON profiles(masked_alias)
    WHERE masked_alias IS NOT NULL;


-- 3. Alter existing 'projects' table
ALTER TABLE projects
    ADD COLUMN IF NOT EXISTS nda_required BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS identity_revealed BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS advance_locked_amount FLOAT DEFAULT 0.0;


-- 4. Alter existing 'transactions' table (new disputed status)
--    No ALTER needed — status is a VARCHAR, new values work automatically.
--    Document new valid statuses:
--    pending | held_in_escrow | released | refunded | disputed | split_pending | demo_completed


-- 5. New table: pii_vaults
--    NOTE: SQLAlchemy create_all() will create this automatically.
--    This is for manual PostgreSQL setup verification only.
CREATE TABLE IF NOT EXISTS pii_vaults (
    id              VARCHAR(36) PRIMARY KEY,
    profile_id      VARCHAR(36) NOT NULL UNIQUE REFERENCES profiles(id) ON DELETE CASCADE,
    real_name_encrypted  TEXT,
    real_email_encrypted TEXT,
    real_phone_encrypted TEXT,
    kyc_provider    VARCHAR(50),
    kyc_reference   VARCHAR(100),
    kyc_status      VARCHAR(30) DEFAULT 'not_started',
    verified_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_pii_vaults_profile_id ON pii_vaults(profile_id);


-- 6. New table: pii_intercept_events
CREATE TABLE IF NOT EXISTS pii_intercept_events (
    id              VARCHAR(36) PRIMARY KEY,
    message_id      VARCHAR(36) REFERENCES messages(id) ON DELETE CASCADE,
    sender_id       VARCHAR(36) NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    conversation_id VARCHAR(36) REFERENCES conversations(id) ON DELETE CASCADE,
    pii_type        VARCHAR(50) NOT NULL,
    was_blocked     BOOLEAN DEFAULT TRUE,
    raw_match_hash  VARCHAR(64),
    detected_at     TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_pii_events_sender_id ON pii_intercept_events(sender_id);
CREATE INDEX IF NOT EXISTS idx_pii_events_detected_at ON pii_intercept_events(detected_at);


-- 7. New table: disputes
CREATE TABLE IF NOT EXISTS disputes (
    id              VARCHAR(36) PRIMARY KEY,
    project_id      VARCHAR(36) NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    filed_by_id     VARCHAR(36) NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    against_id      VARCHAR(36) NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    reason          VARCHAR(100) NOT NULL,
    description     TEXT NOT NULL,
    evidence_urls   TEXT DEFAULT '[]',
    status          VARCHAR(30) DEFAULT 'open',
    arbitrator_id   VARCHAR(36) REFERENCES profiles(id) ON DELETE SET NULL,
    resolution_notes TEXT,
    escrow_action   VARCHAR(30),
    resolved_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT disallow_self_dispute CHECK (filed_by_id != against_id)
);
CREATE INDEX IF NOT EXISTS idx_disputes_project_id ON disputes(project_id);
CREATE INDEX IF NOT EXISTS idx_disputes_status ON disputes(status);


-- 8. New table: compute_escrow_sessions
CREATE TABLE IF NOT EXISTS compute_escrow_sessions (
    id                      VARCHAR(36) PRIMARY KEY,
    brand_id                VARCHAR(36) NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    creator_id              VARCHAR(36) NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    brief_id                VARCHAR(36) REFERENCES creative_briefs(id) ON DELETE SET NULL,
    gpu_tier                VARCHAR(20) NOT NULL,
    gpu_cost_per_hour_usd   FLOAT NOT NULL,
    allocated_hours         FLOAT DEFAULT 1.0,
    used_hours              FLOAT DEFAULT 0.0,
    total_locked_usd        FLOAT NOT NULL,
    total_locked_inr        FLOAT NOT NULL DEFAULT 0.0,
    payment_reference       VARCHAR(100),
    status                  VARCHAR(30) DEFAULT 'locked',
    started_at              TIMESTAMPTZ DEFAULT NOW(),
    expires_at              TIMESTAMPTZ,
    completed_at            TIMESTAMPTZ,
    created_at              TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_compute_escrow_brand ON compute_escrow_sessions(brand_id);
CREATE INDEX IF NOT EXISTS idx_compute_escrow_creator ON compute_escrow_sessions(creator_id);


-- 9. New table: nda_agreements
CREATE TABLE IF NOT EXISTS nda_agreements (
    id                      VARCHAR(36) PRIMARY KEY,
    project_id              VARCHAR(36) NOT NULL UNIQUE REFERENCES projects(id) ON DELETE CASCADE,
    brand_id                VARCHAR(36) NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    creator_id              VARCHAR(36) NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    template_version        VARCHAR(20) DEFAULT 'v1.0',
    brand_signed_at         TIMESTAMPTZ,
    creator_signed_at       TIMESTAMPTZ,
    brand_ip_hash           VARCHAR(64),
    creator_ip_hash         VARCHAR(64),
    pdf_s3_url              TEXT,
    docusign_envelope_id    VARCHAR(100),
    status                  VARCHAR(30) DEFAULT 'pending',
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW()
);


-- 10. New table: creator_embeddings
CREATE TABLE IF NOT EXISTS creator_embeddings (
    id                  VARCHAR(36) PRIMARY KEY,
    creator_id          VARCHAR(36) NOT NULL UNIQUE REFERENCES profiles(id) ON DELETE CASCADE,
    embedding_vector    TEXT NOT NULL,
    input_text_hash     VARCHAR(64),
    model_version       VARCHAR(50) DEFAULT 'text-embedding-3-small',
    last_updated        TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_creator_embeddings_creator ON creator_embeddings(creator_id);


-- ============================================================
-- Verification Query — run after migration to confirm tables
-- ============================================================
-- SELECT table_name FROM information_schema.tables
-- WHERE table_schema = 'public'
-- AND table_name IN (
--     'pii_vaults', 'pii_intercept_events', 'disputes',
--     'compute_escrow_sessions', 'nda_agreements', 'creator_embeddings'
-- )
-- ORDER BY table_name;
-- Expected: 6 rows
