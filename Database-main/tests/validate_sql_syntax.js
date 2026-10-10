// ============================================================================
// Automated Validation & Static Analysis Test Runner
// Project: CreatorSphere AI
// File: tests/validate_sql_syntax.js
// Description: Validates repository structure, schema syntax, RLS coverage,
//              triggers, seed volume, queries, and secret exclusion.
// ============================================================================

const fs = require('fs');
const path = require('path');

const ROOT_DIR = path.resolve(__dirname, '..');

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
console.log('CREATORSPHERE AI - EXPANDED MARKETPLACE VALIDATION RUNNER');
console.log('================================================================\n');

// 1. FILE EXISTENCE SUITE
console.log('[SUITE 1] File Existence & Project Structure:');
const expectedFiles = [
    '.gitignore',
    'supabase/config.toml',
    'supabase/migrations/20261009120000_001_initial_schema.sql',
    'supabase/migrations/20261009120001_002_security_policies.sql',
    'supabase/migrations/20261009130000_003_marketplace_evolution.sql',
    'supabase/seed.sql',
    'queries/creator_search.sql',
    'queries/briefs_and_enquiries.sql',
    'queries/analytics_and_admin.sql',
    'queries/marketplace_lifecycle.sql',
    'tests/database_test_suite.sql',
    'tests/test_live_pg_execution.js',
    'tests/security_adversarial_test.js',
    'docs/INTEGRATION_HANDOFF.md',
    'docs/DATABASE_SECURITY_AUDIT.md',
    'docs/DATABASE_ARCHITECTURE.md',
    'docs/DATABASE_REQUIREMENTS_MATRIX.md',
    'docs/FINAL_DATABASE_AUDIT.md',
    'docs/BACKEND_INTEGRATION_GUIDE.md',
    'docs/PROJECT_COMPLETION_REPORT.md'
];

expectedFiles.forEach(fileRelPath => {
    const fullPath = path.join(ROOT_DIR, fileRelPath);
    assert(fs.existsSync(fullPath), `File exists: ${fileRelPath}`);
});

// 2. CORE & EXPANDED SCHEMA TABLES SUITE
console.log('\n[SUITE 2] Schema Definition & Tables:');
const schema001 = fs.readFileSync(path.join(ROOT_DIR, 'supabase/migrations/20261009120000_001_initial_schema.sql'), 'utf-8');
const schema003 = fs.readFileSync(path.join(ROOT_DIR, 'supabase/migrations/20261009130000_003_marketplace_evolution.sql'), 'utf-8');
const combinedSchema = schema001 + '\n' + schema003;

const allExpectedTables = [
    'users',
    'creators',
    'portfolio_items',
    'briefs',
    'enquiries',
    'creator_interests',
    'verification_signals',
    'creator_private_contacts',
    'contact_unlocks',
    'brief_ai_sessions',
    'brief_ai_messages',
    'brief_revisions',
    'brief_matches',
    'chat_conversations',
    'chat_participants',
    'chat_messages',
    'chat_attachments',
    'message_moderation_logs',
    'project_quotes',
    'projects',
    'payments',
    'financial_ledger',
    'reviews',
    'creator_subscriptions'
];

allExpectedTables.forEach(tableName => {
    const tableRegex = new RegExp(`CREATE TABLE IF NOT EXISTS public\\.${tableName}`, 'i');
    assert(tableRegex.test(combinedSchema), `Schema defines table: public.${tableName}`);
});

// Views
assert(schema003.includes('CREATE OR REPLACE VIEW public.anonymous_creators'), 'Secure view exists: anonymous_creators');
assert(schema003.includes('CREATE OR REPLACE VIEW public.customer_quotes_view'), 'Secure view exists: customer_quotes_view');

// Indexes
assert(schema001.includes('idx_creators_skills_gin'), 'GIN index exists for skills');
assert(schema001.includes('idx_creators_tools_gin'), 'GIN index exists for tools');
assert(schema001.includes('idx_creators_display_name_trgm'), 'Trigram index exists for creator names');
assert(schema003.includes('idx_creators_equipment_gin'), 'GIN index exists for creator equipment');
assert(schema003.includes('idx_chat_messages_convo'), 'Index exists for chat conversation messages');
assert(schema003.includes('idx_contact_unlocks_lookup'), 'Composite index exists for contact unlock lookup');

// Triggers & Guards
assert(schema001.includes('protect_user_profile'), 'Trigger guard exists for user profile ownership & role escalation');
assert(schema001.includes('protect_creator_reputation'), 'Trigger guard exists for creator reputation');
assert(schema001.includes('protect_portfolio_verification'), 'Trigger guard exists for portfolio verification status');
assert(schema001.includes('enforce_enquiry_status_transitions'), 'Trigger guard exists for enquiry status state machine');
assert(schema001.includes('enforce_pitch_update_rules'), 'Trigger guard exists for pitch status negotiation');
assert(schema003.includes('protect_chat_message_moderation'), 'Trigger guard exists for chat message moderation');
assert(schema003.includes('enforce_quote_pricing_integrity'), 'Trigger guard exists for quote pricing integrity');
assert(schema003.includes('enforce_project_status_transitions'), 'Trigger guard exists for project contract lifecycle');
assert(schema003.includes('protect_payment_state'), 'Trigger guard exists for payment state tampering');
assert(schema003.includes('protect_contact_unlock_creation'), 'Trigger guard exists for contact unlock creation');
assert(schema003.includes('validate_and_apply_review'), 'Trigger guard exists for verified review application');
assert(schema003.includes('protect_creator_subscription_updates'), 'Trigger guard exists for creator subscription updates');
assert(schema003.includes('Message identity, conversation, and sender cannot be modified'), 'Trigger guard enforces chat message identity & sender immutability');

// 3. ROW LEVEL SECURITY (RLS) SUITE
console.log('\n[SUITE 3] Security Policies & RLS Coverage:');
const rls002 = fs.readFileSync(path.join(ROOT_DIR, 'supabase/migrations/20261009120001_002_security_policies.sql'), 'utf-8');
const combinedRLS = rls002 + '\n' + schema003;

allExpectedTables.forEach(tableName => {
    const rlsRegex = new RegExp(`ALTER TABLE public\\.${tableName} ENABLE ROW LEVEL SECURITY;`, 'i');
    assert(rlsRegex.test(combinedRLS), `RLS enabled on table: public.${tableName}`);
});

// Check Critical RLS Rules
assert(rls002.includes("status = 'pending'") && rls002.includes("verified_at IS NULL"), 'Verification signal badge forgery blocked at RLS level');
assert(rls002.includes("verification_status IN ('unverified', 'pending')"), 'Portfolio self-verification blocked at RLS level');
assert(schema003.includes('public.has_unlocked_creator(auth.uid(), creator_id)'), 'Creator private contacts protected by has_unlocked_creator RLS');
assert(schema003.includes("moderation_status = 'allowed'"), 'Chat messages require allowed moderation status on insert');
assert(schema003.includes("status IN ('presented_to_customer', 'accepted')"), 'Private creator quotes masked from customer until presented');

// 4. SEED DATA QUALITY & VOLUME SUITE
console.log('\n[SUITE 4] Seed Data Quality & Volume:');
const seedContent = fs.readFileSync(path.join(ROOT_DIR, 'supabase/seed.sql'), 'utf-8');

const creatorMatches = seedContent.match(/'00000000-0000-0000-0001-0000000000\d{2}'/g);
const creatorCount = creatorMatches ? new Set(creatorMatches).size : 0;
assert(creatorCount >= 12, `Seed contains at least 12 creator profiles (found: ${creatorCount})`);

assert(seedContent.includes('public.creator_private_contacts'), 'Seed populates creator private contact details');
assert(seedContent.includes('public.brief_ai_sessions'), 'Seed populates AI brief conversation session');
assert(seedContent.includes('public.chat_messages'), 'Seed populates in-platform chat messages');
assert(seedContent.includes('public.message_moderation_logs'), 'Seed populates message moderation log');
assert(seedContent.includes('public.project_quotes'), 'Seed populates project quote with pricing breakdown');
assert(seedContent.includes('public.projects'), 'Seed populates formal contract projects');
assert(seedContent.includes('public.contact_unlocks'), 'Seed populates verified contact unlock');
assert(seedContent.includes('public.reviews'), 'Seed populates verified project review');
assert(seedContent.includes('public.creator_subscriptions'), 'Seed populates creator subscriptions');

// 5. QUERY INTEGRITY SUITE
console.log('\n[SUITE 5] Query Suite Verification:');
const searchQueries = fs.readFileSync(path.join(ROOT_DIR, 'queries/creator_search.sql'), 'utf-8');
const briefQueries = fs.readFileSync(path.join(ROOT_DIR, 'queries/briefs_and_enquiries.sql'), 'utf-8');
const lifecycleQueries = fs.readFileSync(path.join(ROOT_DIR, 'queries/marketplace_lifecycle.sql'), 'utf-8');

assert(searchQueries.includes('QUERY 1: Retrieve All Active Creators'), 'Query 1 defined');
assert(searchQueries.includes('QUERY 2: Search Creators by Name'), 'Query 2 defined');
assert(briefQueries.includes('QUERY 11: Save / Post a New AI-Assisted Customer Project Brief'), 'Query 11 defined');
assert(lifecycleQueries.includes('QUERY M1: Anonymous Creator Discovery'), 'Query M1 defined: Anonymous Creator Discovery');
assert(lifecycleQueries.includes('QUERY M4: In-Platform Chat Messages'), 'Query M4 defined: In-Platform Chat Messages');
assert(lifecycleQueries.includes('QUERY M6: Customer Views Presented Quotes'), 'Query M6 defined: Customer Presented Quotes');
assert(lifecycleQueries.includes('QUERY M7: Customer Accepts Quote & Creates Formal Contract'), 'Query M7 defined: Formal Contract Initialization');
assert(lifecycleQueries.includes('QUERY M8: Verify Contact Unlock & Retrieve Creator Private Contacts'), 'Query M8 defined: Unlocked Private Contact Retrieval');
assert(lifecycleQueries.includes('QUERY M9: Submit Verified Review'), 'Query M9 defined: Verified Review Submission');

// 6. SECRETS & GIT SAFETY SUITE
console.log('\n[SUITE 6] Security & Secret Exclusion:');
const gitignoreContent = fs.readFileSync(path.join(ROOT_DIR, '.gitignore'), 'utf-8');
assert(gitignoreContent.includes('.env'), '.gitignore excludes .env files');
assert(gitignoreContent.includes('*.key'), '.gitignore excludes private keys');
assert(gitignoreContent.includes('credentials.json'), '.gitignore excludes credentials.json');

const allSqlFiles = [schema001, rls002, schema003, seedContent, searchQueries, briefQueries, lifecycleQueries];
const containsServiceKey = allSqlFiles.some(content => content.includes('service_role') && content.includes('eyJ'));
assert(!containsServiceKey, 'No leaked service-role keys or JWT tokens found in codebase');

console.log('\n================================================================');
console.log(`SUMMARY: ${passedTests} / ${totalTests} ASSERTIONS PASSED (${failedTests} FAILED)`);
console.log('================================================================');

if (failedTests > 0) {
    process.exit(1);
}
