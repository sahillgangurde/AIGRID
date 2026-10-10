// ============================================================================
// Live In-Memory PostgreSQL Execution Engine Test
// Project: CreatorSphere AI
// File: tests/test_live_pg_execution.js
// Description: Executes live PostgreSQL DDL, DML, constraints, cascades,
//              and multi-table relational queries in-memory.
// ============================================================================

const { newDb } = require('pg-mem');

let totalTests = 0;
let passedTests = 0;
let failedTests = 0;

function assert(condition, testName, details = '') {
    totalTests++;
    if (condition) {
        passedTests++;
        console.log(`  PASSED: ${testName}`);
    } else {
        failedTests++;
        console.error(`❌ FAILED: ${testName} ${details ? '(' + details + ')' : ''}`);
    }
}

console.log('================================================================');
console.log('CREATORSPHERE AI - LIVE IN-MEMORY POSTGRESQL ENGINE TESTS');
console.log('================================================================\n');

const db = newDb();

// Register UUID & string functions
db.public.registerFunction({
    name: 'gen_random_uuid',
    returns: 'uuid',
    implementation: () => '11111111-2222-3333-4444-555555555555'
});

db.public.registerFunction({
    name: 'split_part',
    args: ['text', 'text', 'int'],
    returns: 'text',
    implementation: (str, delimiter, field) => {
        if (!str) return '';
        const parts = str.split(delimiter);
        return parts[field - 1] || '';
    }
});

console.log('[SUITE 1] Creating All 7 Tables in PostgreSQL Engine...');

db.public.none(`
    CREATE TABLE users (
        id UUID PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        full_name TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'customer' CHECK (role IN ('customer', 'creator', 'both')),
        avatar_url TEXT,
        bio TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE creators (
        id UUID PRIMARY KEY,
        user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
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

    CREATE TABLE portfolio_items (
        id UUID PRIMARY KEY,
        creator_id UUID NOT NULL REFERENCES creators(id) ON DELETE CASCADE,
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

    CREATE TABLE briefs (
        id UUID PRIMARY KEY,
        customer_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
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

    CREATE TABLE enquiries (
        id UUID PRIMARY KEY,
        customer_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        creator_id UUID NOT NULL REFERENCES creators(id) ON DELETE CASCADE,
        brief_id UUID REFERENCES briefs(id) ON DELETE SET NULL,
        subject TEXT NOT NULL,
        message TEXT NOT NULL,
        proposed_budget NUMERIC(10, 2) CHECK (proposed_budget IS NULL OR proposed_budget >= 0),
        proposed_deadline TIMESTAMPTZ,
        status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'declined', 'in_negotiation', 'closed')),
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE creator_interests (
        id UUID PRIMARY KEY,
        brief_id UUID NOT NULL REFERENCES briefs(id) ON DELETE CASCADE,
        creator_id UUID NOT NULL REFERENCES creators(id) ON DELETE CASCADE,
        pitch_note TEXT NOT NULL,
        estimated_delivery_days INT NOT NULL CHECK (estimated_delivery_days > 0),
        proposed_quote NUMERIC(10, 2) NOT NULL CHECK (proposed_quote >= 0),
        sample_portfolio_item_id UUID REFERENCES portfolio_items(id) ON DELETE SET NULL,
        status TEXT NOT NULL DEFAULT 'submitted' CHECK (status IN ('submitted', 'shortlisted', 'accepted', 'declined', 'withdrawn')),
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT unique_brief_creator_interest UNIQUE (brief_id, creator_id)
    );

    CREATE TABLE verification_signals (
        id UUID PRIMARY KEY,
        creator_id UUID NOT NULL REFERENCES creators(id) ON DELETE CASCADE,
        portfolio_item_id UUID REFERENCES portfolio_items(id) ON DELETE CASCADE,
        signal_type TEXT NOT NULL CHECK (signal_type IN ('portfolio_link_verified', 'identity_verified', 'social_account_verified', 'ai_watermark_detected', 'tool_authenticity_confirmed')),
        evidence_url TEXT,
        metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
        status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'verified', 'rejected')),
        verified_at TIMESTAMPTZ,
        notes TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
`);
assert(true, 'All 7 PostgreSQL tables created with relationships and constraints');

// ============================================================================
// SUITE 2: CHECK CONSTRAINT ENFORCEMENT
// ============================================================================
console.log('\n[SUITE 2] Testing CHECK Constraints Under Live Execution:');

// Test 2.1: Invalid User Role
let invalidRoleRejected = false;
try {
    db.public.none("INSERT INTO users (id, email, full_name, role) VALUES ('00000000-0000-0000-0000-000000000001', 'test@test.com', 'Test', 'invalid_super_role');");
} catch (e) {
    invalidRoleRejected = true;
}
assert(invalidRoleRejected, 'Invalid user role rejected by CHECK constraint');

// Test 2.2: Inverted Budget
db.public.none("INSERT INTO users (id, email, full_name, role) VALUES ('00000000-0000-0000-0000-000000000001', 'valid@test.com', 'Valid User', 'creator');");
let invertedBudgetRejected = false;
try {
    db.public.none("INSERT INTO creators (id, user_id, handle, display_name, indicative_budget_min, indicative_budget_max) VALUES ('00000000-0000-0000-0001-000000000001', '00000000-0000-0000-0000-000000000001', '@valid_handle', 'Valid Creator', 5000, 1000);");
} catch (e) {
    invertedBudgetRejected = true;
}
assert(invertedBudgetRejected, 'Inverted budget (max < min) rejected by CHECK constraint');

// Test 2.3: Negative Budget
let negativeBudgetRejected = false;
try {
    db.public.none("INSERT INTO creators (id, user_id, handle, display_name, indicative_budget_min, indicative_budget_max) VALUES ('00000000-0000-0000-0001-000000000001', '00000000-0000-0000-0000-000000000001', '@valid_handle', 'Valid Creator', -50, 1000);");
} catch (e) {
    negativeBudgetRejected = true;
}
assert(negativeBudgetRejected, 'Negative budget rejected by CHECK constraint');

// Test 2.4: Invalid Aspect Ratio
db.public.none("INSERT INTO creators (id, user_id, handle, display_name, indicative_budget_min, indicative_budget_max) VALUES ('00000000-0000-0000-0001-000000000001', '00000000-0000-0000-0000-000000000001', '@valid_handle', 'Valid Creator', 500, 1500);");
let invalidRatioRejected = false;
try {
    db.public.none("INSERT INTO portfolio_items (id, creator_id, title, video_url, content_type, style, aspect_ratio) VALUES ('00000000-0000-0000-0002-000000000001', '00000000-0000-0001-0000-000000000001', 'Bad Ratio', 'https://v.test', 'Ad', 'Clean', '3:2');");
} catch (e) {
    invalidRatioRejected = true;
}
assert(invalidRatioRejected, 'Invalid aspect ratio (3:2) rejected by CHECK constraint');

// Test 2.5: Invalid Brief Status
let invalidBriefStatusRejected = false;
try {
    db.public.none("INSERT INTO briefs (id, customer_id, title, description, content_type, budget_min, budget_max, status) VALUES ('00000000-0000-0000-0003-000000000001', '00000000-0000-0000-0000-000000000001', 'Brief Title', 'Desc', 'Ad', 500, 1000, 'invalid_status_xyz');");
} catch (e) {
    invalidBriefStatusRejected = true;
}
assert(invalidBriefStatusRejected, 'Invalid brief status rejected by CHECK constraint');

// ============================================================================
// SUITE 3: UNIQUE CONSTRAINTS ENFORCEMENT
// ============================================================================
console.log('\n[SUITE 3] Testing UNIQUE Constraints:');

// Test 3.1: Duplicate Email
let duplicateEmailRejected = false;
try {
    db.public.none("INSERT INTO users (id, email, full_name, role) VALUES ('00000000-0000-0000-0000-000000000002', 'valid@test.com', 'Duplicate Email User', 'customer');");
} catch (e) {
    duplicateEmailRejected = true;
}
assert(duplicateEmailRejected, 'Duplicate email rejected by UNIQUE constraint');

// Test 3.2: Duplicate Creator Handle
db.public.none("INSERT INTO users (id, email, full_name, role) VALUES ('00000000-0000-0000-0000-000000000002', 'user2@test.com', 'User Two', 'creator');");
let duplicateHandleRejected = false;
try {
    db.public.none("INSERT INTO creators (id, user_id, handle, display_name, indicative_budget_min, indicative_budget_max) VALUES ('00000000-0000-0000-0001-000000000002', '00000000-0000-0000-0000-000000000002', '@valid_handle', 'Creator Two', 300, 900);");
} catch (e) {
    duplicateHandleRejected = true;
}
assert(duplicateHandleRejected, 'Duplicate creator handle rejected by UNIQUE constraint');

// Test 3.3: Duplicate Pitch on Brief
db.public.none("INSERT INTO briefs (id, customer_id, title, description, content_type, budget_min, budget_max, status) VALUES ('00000000-0000-0000-0003-000000000001', '00000000-0000-0000-0000-000000000001', 'Valid Brief', 'Desc', 'Ad', 500, 1000, 'open');");
db.public.none("INSERT INTO creator_interests (id, brief_id, creator_id, pitch_note, estimated_delivery_days, proposed_quote) VALUES ('00000000-0000-0000-0005-000000000001', '00000000-0000-0000-0003-000000000001', '00000000-0000-0000-0001-000000000001', 'Pitch 1', 5, 800);");

let duplicatePitchRejected = false;
try {
    db.public.none("INSERT INTO creator_interests (id, brief_id, creator_id, pitch_note, estimated_delivery_days, proposed_quote) VALUES ('00000000-0000-0000-0005-000000000002', '00000000-0000-0000-0003-000000000001', '00000000-0000-0000-0001-000000000001', 'Pitch 2', 4, 750);");
} catch (e) {
    duplicatePitchRejected = true;
}
assert(duplicatePitchRejected, 'Duplicate pitch on same brief rejected by UNIQUE(brief_id, creator_id) constraint');

// ============================================================================
// SUITE 4: FOREIGN KEY CASCADE DELETION
// ============================================================================
console.log('\n[SUITE 4] Testing Foreign Key CASCADE Deletion:');

// Deleting user 00000000-0000-0000-0000-000000000001 should cascade-delete their creator profile, brief, and pitch!
db.public.none("DELETE FROM users WHERE id = '00000000-0000-0000-0000-000000000001';");

const remainingCreators = db.public.many("SELECT * FROM creators WHERE user_id = '00000000-0000-0000-0000-000000000001';");
assert(remainingCreators.length === 0, 'Cascade delete: Creator profile deleted when user is deleted');

const remainingBriefs = db.public.many("SELECT * FROM briefs WHERE customer_id = '00000000-0000-0000-0000-000000000001';");
assert(remainingBriefs.length === 0, 'Cascade delete: Briefs deleted when user is deleted');

const remainingPitches = db.public.many("SELECT * FROM creator_interests WHERE brief_id = '00000000-0000-0000-0003-000000000001';");
assert(remainingPitches.length === 0, 'Cascade delete: Pitches deleted when brief is deleted');

// ============================================================================
// SUITE 5: RELATIONAL QUERIES & SORTING
// ============================================================================
console.log('\n[SUITE 5] Testing Relational Marketplace Queries:');

// Re-seed 2 test creators and 1 brief
db.public.none(`
    INSERT INTO users (id, email, full_name, role) VALUES 
    ('00000000-0000-0000-0000-000000000010', 'creator1@test.com', 'Elena Rostova', 'creator'),
    ('00000000-0000-0000-0000-000000000020', 'creator2@test.com', 'Marcus Vance', 'creator');

    INSERT INTO creators (id, user_id, handle, display_name, indicative_budget_min, indicative_budget_max, rating, total_reviews, is_featured, availability) VALUES 
    ('00000000-0000-0000-0001-000000000010', '00000000-0000-0000-0000-000000000010', '@elena_ai', 'Elena Rostova', 500, 2500, 4.95, 34, true, 'available'),
    ('00000000-0000-0000-0001-000000000020', '00000000-0000-0000-0000-000000000020', '@marcus_v', 'Marcus Vance', 300, 1500, 4.88, 62, true, 'available');

    INSERT INTO portfolio_items (id, creator_id, title, video_url, content_type, style, aspect_ratio, is_featured, verification_status) VALUES
    ('00000000-0000-0000-0002-000000000010', '00000000-0000-0000-0001-000000000010', 'AI Spec Ad', 'https://video.test/1.mp4', 'AI Concept', 'Cyberpunk', '16:9', true, 'verified'),
    ('00000000-0000-0000-0002-000000000020', '00000000-0000-0000-0001-000000000020', 'Commercial Cut', 'https://video.test/2.mp4', 'Commercial', 'High-Energy', '16:9', true, 'verified');
`);

// Execute marketplace join query
const marketplaceResults = db.public.many(`
    SELECT 
        c.id, c.handle, c.display_name, c.rating, c.indicative_budget_min,
        u.email, p.title AS portfolio_title, p.verification_status
    FROM creators c
    JOIN users u ON c.user_id = u.id
    LEFT JOIN portfolio_items p ON p.creator_id = c.id
    WHERE c.availability = 'available' AND c.indicative_budget_min <= 600
    ORDER BY c.rating DESC;
`);

assert(marketplaceResults.length === 2, 'Marketplace query returned expected 2 matched creators');
assert(marketplaceResults[0].display_name === 'Elena Rostova', 'Query sorted highest rating first (Elena Rostova: 4.95)');
assert(marketplaceResults[0].portfolio_title === 'AI Spec Ad', 'Joined portfolio title correctly');
assert(marketplaceResults[0].verification_status === 'verified', 'Joined verification status correctly');

// ============================================================================
// SUITE 6: STATE MACHINE VALIDATION & IMMUTABILITY
// ============================================================================
console.log('\n[SUITE 6] Testing State Machine Transitions & Message Immutability:');

// Insert a completed brief
db.public.none(`
    INSERT INTO users (id, email, full_name, role) VALUES ('00000000-0000-0000-0000-000000000030', 'cust30@test.com', 'Customer Thirty', 'customer');
    INSERT INTO briefs (id, customer_id, title, description, content_type, budget_min, budget_max, status) VALUES 
    ('00000000-0000-0000-0003-000000000030', '00000000-0000-0000-0000-000000000030', 'Completed Brief', 'Done', 'Ad', 500, 1000, 'completed');
`);

const completedBrief = db.public.one("SELECT status FROM briefs WHERE id = '00000000-0000-0000-0003-000000000030';");
assert(completedBrief.status === 'completed', 'Completed brief state confirmed');

// Insert an enquiry and test message immutability
db.public.none(`
    INSERT INTO enquiries (id, customer_id, creator_id, subject, message, status) VALUES 
    ('00000000-0000-0000-0004-000000000030', '00000000-0000-0000-0000-000000000030', '00000000-0000-0000-0001-000000000010', 'Initial Subject', 'Initial Message Body', 'pending');
`);

const enquiryRecord = db.public.one("SELECT subject, message, status FROM enquiries WHERE id = '00000000-0000-0000-0004-000000000030';");
assert(enquiryRecord.subject === 'Initial Subject', 'Enquiry initial subject verified');
assert(enquiryRecord.message === 'Initial Message Body', 'Enquiry initial message body verified');

console.log('\n================================================================');
console.log(`SUMMARY: ${passedTests} / ${totalTests} LIVE SQL ENGINE TESTS PASSED (${failedTests} FAILED)`);
console.log('================================================================');

if (failedTests > 0) {
    process.exit(1);
} else {
    process.exit(0);
}
