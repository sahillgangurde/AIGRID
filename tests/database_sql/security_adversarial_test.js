// ============================================================================
// Adversarial Security & Penetration Testing Suite
// Project: CreatorSphere AI
// File: tests/security_adversarial_test.js
// Description: Live PostgreSQL adversarial penetration simulations validating
//              database guards, triggers, CHECK constraints, RLS, one-sided
//              anonymity, chat moderation, quotes, contracts, and payments.
// Engine:      PGlite (PostgreSQL 18 WebAssembly Engine in Node.js)
// ============================================================================

const fs = require('fs');
const path = require('path');
const { PGlite } = require('@electric-sql/pglite');

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

async function runAdversarialAudit() {
    console.log('================================================================');
    console.log('CREATORSPHERE AI - EXPANDED ADVERSARIAL PENETRATION & HARDENING AUDIT');
    console.log('Engine: Real PostgreSQL 18 Engine (PGlite)');
    console.log('================================================================\n');

    const db = new PGlite();

    // 1. Load Migrations 001, 002, 003
    console.log('[STEP 1] Executing Migrations (001, 002, 003)...');
    let m1 = fs.readFileSync(
        path.join(ROOT_DIR, 'supabase/migrations/20261009120000_001_initial_schema.sql'),
        'utf-8'
    )
        .replace(/CREATE EXTENSION IF NOT EXISTS "uuid-ossp";/g, '-- extension uuid-ossp')
        .replace(/CREATE EXTENSION IF NOT EXISTS "pg_trgm";/g, '-- extension pg_trgm')
        .replace(/CREATE INDEX IF NOT EXISTS idx_creators_display_name_trgm[^;]+;/g, '-- trigram index')
        .replace(/CREATE INDEX IF NOT EXISTS idx_creators_handle_trgm[^;]+;/g, '-- trigram index');

    let m2 = fs.readFileSync(
        path.join(ROOT_DIR, 'supabase/migrations/20261009120001_002_security_policies.sql'),
        'utf-8'
    );

    let m3 = fs.readFileSync(
        path.join(ROOT_DIR, 'supabase/migrations/20261009130000_003_marketplace_evolution.sql'),
        'utf-8'
    );

    await db.exec(m1);
    await db.exec(m2);
    await db.exec(m3);
    console.log('  Migrations 001, 002, and 003 executed successfully in PostgreSQL engine.\n');

    // Identities
    const USER_CUSTOMER_A = '00000000-0000-0000-0000-000000000001';
    const USER_CUSTOMER_B = '00000000-0000-0000-0000-000000000002';
    const USER_CREATOR_A  = '00000000-0000-0000-0000-000000000101';
    const USER_CREATOR_B  = '00000000-0000-0000-0000-000000000102';

    const CREATOR_PROFILE_A = '00000000-0000-0000-0001-000000000001';
    const CREATOR_PROFILE_B = '00000000-0000-0000-0001-000000000002';

    const PORTFOLIO_ITEM_A = '00000000-0000-0000-0002-000000000001';
    const BRIEF_A          = '00000000-0000-0000-0003-000000000001';
    const BRIEF_ASSIGNED   = '00000000-0000-0000-0003-000000000002';

    // Seed baseline test accounts
    await db.exec(`
        INSERT INTO public.users (id, email, full_name, role, avatar_url) VALUES 
        ('${USER_CUSTOMER_A}', 'custA@test.local', 'Customer Alice', 'customer', 'https://avatar.test/custA.png'),
        ('${USER_CUSTOMER_B}', 'custB@test.local', 'Customer Bob', 'customer', 'https://avatar.test/custB.png'),
        ('${USER_CREATOR_A}',  'creatA@test.local', 'Creator Alex', 'creator', 'https://avatar.test/alex.png'),
        ('${USER_CREATOR_B}',  'creatB@test.local', 'Creator Bella', 'creator', 'https://avatar.test/bella.png');

        INSERT INTO public.creators (id, user_id, handle, display_name, indicative_budget_min, indicative_budget_max, rating, total_reviews, is_featured, avatar_url) VALUES
        ('${CREATOR_PROFILE_A}', '${USER_CREATOR_A}', '@alex_creates', 'Alex Creates', 500, 2000, 4.50, 10, false, 'https://avatar.test/alex.png'),
        ('${CREATOR_PROFILE_B}', '${USER_CREATOR_B}', '@bella_cuts', 'Bella Cuts', 300, 1500, 4.80, 25, false, 'https://avatar.test/bella.png');

        INSERT INTO public.portfolio_items (id, creator_id, title, video_url, content_type, style, verification_status) VALUES
        ('${PORTFOLIO_ITEM_A}', '${CREATOR_PROFILE_A}', 'Sample Video', 'https://video.test/original.mp4', 'Ad', 'Clean', 'pending');

        INSERT INTO public.briefs (id, customer_id, title, description, content_type, budget_min, budget_max, status) VALUES
        ('${BRIEF_A}', '${USER_CUSTOMER_A}', 'Trail Shoe Commercial', 'High energy edit', 'Product Commercial', 1000, 3000, 'open'),
        ('${BRIEF_ASSIGNED}', '${USER_CUSTOMER_A}', 'Contracted Commercial', 'In production', 'Product Commercial', 2000, 5000, 'assigned');
    `);

    // Create test roles for real RLS enforcement
    await db.exec(`
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
                CREATE ROLE authenticated;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
                CREATE ROLE anon;
            END IF;
        END $$;
        GRANT USAGE ON SCHEMA public, auth TO authenticated, anon;
        GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
        GRANT SELECT ON ALL TABLES IN SCHEMA public TO anon;
        GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;
        GRANT ALL ON ALL FUNCTIONS IN SCHEMA public, auth TO authenticated, anon;
    `);

    // Helper to simulate calling with user context or service_role
    async function setJwtContext(userId, role = 'authenticated') {
        if (role === 'service_role') {
            await db.exec(`
                RESET ROLE;
                SELECT set_config('request.jwt.claim.sub', '', false);
                SELECT set_config('request.jwt.claim.role', 'service_role', false);
            `);
        } else if (role === 'anon') {
            await db.exec(`
                SET ROLE anon;
                SELECT set_config('request.jwt.claim.sub', '', false);
                SELECT set_config('request.jwt.claim.role', 'anon', false);
            `);
        } else {
            await db.exec(`
                SET ROLE authenticated;
                SELECT set_config('request.jwt.claim.sub', '${userId || ''}', false);
                SELECT set_config('request.jwt.claim.role', '${role}', false);
            `);
        }
    }

    // =========================================================================
    // SUITE 1: Creator Profile Metrics & Ownership Guard
    // =========================================================================
    console.log('[SUITE 1] Adversarial Attack: Creator Profile Metrics & Ownership:');
    await setJwtContext(USER_CREATOR_A);

    await db.exec(`
        UPDATE public.creators 
        SET rating = 5.00, total_reviews = 9999, is_featured = true 
        WHERE id = '${CREATOR_PROFILE_A}';
    `);

    const creatorCheck = await db.query(`SELECT rating, total_reviews, is_featured FROM public.creators WHERE id = '${CREATOR_PROFILE_A}';`);
    assert(Number(creatorCheck.rows[0].rating) === 4.50, 'Rating self-elevation blocked (remained 4.50)');
    assert(creatorCheck.rows[0].total_reviews === 10, 'Fake reviews injection blocked (remained 10)');
    assert(creatorCheck.rows[0].is_featured === false, 'Featured status forgery blocked (remained false)');

    await db.exec(`UPDATE public.creators SET bio = 'Legitimate Bio Update' WHERE id = '${CREATOR_PROFILE_A}';`);
    const bioCheck = await db.query(`SELECT bio FROM public.creators WHERE id = '${CREATOR_PROFILE_A}';`);
    assert(bioCheck.rows[0].bio === 'Legitimate Bio Update', 'Legitimate profile bio edit allowed');

    let takeoverFailed = false;
    try {
        await db.exec(`UPDATE public.creators SET user_id = '${USER_CUSTOMER_A}' WHERE id = '${CREATOR_PROFILE_A}';`);
    } catch (e) {
        takeoverFailed = true;
    }
    assert(takeoverFailed, 'Creator user_id reassignment attack blocked');

    // =========================================================================
    // SUITE 2: User Role Escalation & Identity Tampering
    // =========================================================================
    console.log('\n[SUITE 2] Adversarial Attack: User Role Escalation & Identity Tampering:');
    let roleEscalationFailed = false;
    try {
        await db.exec(`UPDATE public.users SET role = 'admin' WHERE id = '${USER_CREATOR_A}';`);
    } catch (e) {
        roleEscalationFailed = true;
    }
    assert(roleEscalationFailed, 'User role self-escalation blocked by protect_user_profile trigger');

    let emailTamperFailed = false;
    try {
        await db.exec(`UPDATE public.users SET email = 'hacked@evil.corp' WHERE id = '${USER_CREATOR_A}';`);
    } catch (e) {
        emailTamperFailed = true;
    }
    assert(emailTamperFailed, 'User direct email manipulation blocked by protect_user_profile trigger');

    // Email Privacy Guard: Anonymous harvesting attempt
    await setJwtContext(null, 'anon');
    const anonUsers = await db.query('SELECT email FROM public.users;');
    assert(anonUsers.rows.length === 0, 'Anonymous users cannot harvest emails from public.users (0 rows via RLS)');

    // Email Privacy Guard: Customer B attempting to read Customer A private email
    await setJwtContext(USER_CUSTOMER_B);
    const custBReadsA = await db.query(`SELECT email FROM public.users WHERE id = '${USER_CUSTOMER_A}';`);
    assert(custBReadsA.rows.length === 0, 'Customer B cannot read Customer A private email (0 rows via RLS)');

    // Email Privacy Guard: Customer B attempting to read Creator A private email from public.users
    const custBReadsCreator = await db.query(`SELECT email FROM public.users WHERE id = '${USER_CREATOR_A}';`);
    assert(custBReadsCreator.rows.length === 0, 'Customer B cannot read Creator A private email from public.users (0 rows via RLS)');

    // Legitimate Profile Access: Customer A reading own profile and email
    await setJwtContext(USER_CUSTOMER_A);
    const ownProfile = await db.query(`SELECT email, full_name FROM public.users WHERE id = '${USER_CUSTOMER_A}';`);
    assert(ownProfile.rows.length === 1 && ownProfile.rows[0].email === 'custA@test.local', 'Customer A can legitimately read own profile and email');

    // Restore creator context for subsequent suites
    await setJwtContext(USER_CREATOR_A);

    // =========================================================================
    // SUITE 3: Portfolio Item Self-Verification
    // =========================================================================
    console.log('\n[SUITE 3] Adversarial Attack: Portfolio Item Self-Verification:');
    let selfVerifyFailed = false;
    try {
        await db.exec(`UPDATE public.portfolio_items SET verification_status = 'verified' WHERE id = '${PORTFOLIO_ITEM_A}';`);
    } catch (e) {
        selfVerifyFailed = true;
    }
    assert(selfVerifyFailed, 'Portfolio self-verification update blocked by protect_portfolio_verification trigger');

    await setJwtContext(null, 'service_role');
    await db.exec(`UPDATE public.portfolio_items SET verification_status = 'verified' WHERE id = '${PORTFOLIO_ITEM_A}';`);
    await setJwtContext(USER_CREATOR_A);
    await db.exec(`UPDATE public.portfolio_items SET video_url = 'https://video.test/tampered.mp4' WHERE id = '${PORTFOLIO_ITEM_A}';`);
    const urlTamperCheck = await db.query(`SELECT verification_status FROM public.portfolio_items WHERE id = '${PORTFOLIO_ITEM_A}';`);
    assert(urlTamperCheck.rows[0].verification_status === 'pending', 'Video URL tampering on verified item automatically resets status to pending');

    // =========================================================================
    // SUITE 4: Enquiry Participant & Status Tampering
    // =========================================================================
    console.log('\n[SUITE 4] Adversarial Attack: Enquiry Participant & Status Tampering:');
    await setJwtContext(USER_CUSTOMER_A);
    const ENQUIRY_ID = '00000000-0000-0000-0004-000000000001';
    await db.exec(`
        INSERT INTO public.enquiries (id, customer_id, creator_id, subject, message, proposed_budget, status)
        VALUES ('${ENQUIRY_ID}', '${USER_CUSTOMER_A}', '${CREATOR_PROFILE_A}', 'Need Commercial', 'Initial quote enquiry', 1200.00, 'pending');
    `);

    let enqHijackFailed = false;
    try {
        await db.exec(`UPDATE public.enquiries SET customer_id = '${USER_CUSTOMER_B}' WHERE id = '${ENQUIRY_ID}';`);
    } catch (e) {
        enqHijackFailed = true;
    }
    assert(enqHijackFailed, 'Enquiry participant hijacking blocked by immutable fields trigger');

    let selfAcceptFailed = false;
    try {
        await db.exec(`UPDATE public.enquiries SET status = 'accepted' WHERE id = '${ENQUIRY_ID}';`);
    } catch (e) {
        selfAcceptFailed = true;
    }
    assert(selfAcceptFailed, 'Customer self-acceptance of pending enquiry blocked by status state machine');

    let messageTamperFailed = false;
    try {
        await db.exec(`UPDATE public.enquiries SET message = 'Tampered message body' WHERE id = '${ENQUIRY_ID}';`);
    } catch (e) {
        messageTamperFailed = true;
    }
    assert(messageTamperFailed, 'Enquiry initial message alteration blocked by immutability trigger');

    // =========================================================================
    // SUITE 5: Creator Bids & Negotiation Guard
    // =========================================================================
    console.log('\n[SUITE 5] Adversarial Attack: Creator Bids & Negotiation Guard:');
    await setJwtContext(USER_CREATOR_A);
    const PITCH_ID = '00000000-0000-0000-0005-000000000001';
    await db.exec(`
        INSERT INTO public.creator_interests (id, brief_id, creator_id, pitch_note, estimated_delivery_days, proposed_quote, status)
        VALUES ('${PITCH_ID}', '${BRIEF_A}', '${CREATOR_PROFILE_A}', 'I can deliver in 5 days', 5, 1200.00, 'submitted');
    `);

    let creatorSelfAcceptFailed = false;
    try {
        await db.exec(`UPDATE public.creator_interests SET status = 'accepted' WHERE id = '${PITCH_ID}';`);
    } catch (e) {
        creatorSelfAcceptFailed = true;
    }
    assert(creatorSelfAcceptFailed, 'Creator self-acceptance of pitch blocked by negotiation guard');

    await setJwtContext(USER_CUSTOMER_A);
    await db.exec(`UPDATE public.creator_interests SET proposed_quote = 50.00, status = 'accepted' WHERE id = '${PITCH_ID}';`);
    const quoteCheck = await db.query(`SELECT proposed_quote, status FROM public.creator_interests WHERE id = '${PITCH_ID}';`);
    assert(Number(quoteCheck.rows[0].proposed_quote) === 1200.00, 'Customer price-slashing attack blocked (quote remained $1200.00)');
    assert(quoteCheck.rows[0].status === 'accepted', 'Customer allowed to legitimately accept pitch at original quote');

    let revertAcceptedFailed = false;
    try {
        await db.exec(`UPDATE public.creator_interests SET status = 'submitted' WHERE id = '${PITCH_ID}';`);
    } catch (e) {
        revertAcceptedFailed = true;
    }
    assert(revertAcceptedFailed, 'Reverting accepted binding pitch agreement blocked');

    // =========================================================================
    // SUITE 6: Brief Contract Loss & Transition Guards
    // =========================================================================
    console.log('\n[SUITE 6] Adversarial Attack: Brief Contract Loss & Transition Guards:');
    let deleteAssignedFailed = false;
    try {
        await db.exec(`DELETE FROM public.briefs WHERE id = '${BRIEF_ASSIGNED}';`);
        const assignedCheck = await db.query(`SELECT status FROM public.briefs WHERE id = '${BRIEF_ASSIGNED}';`);
        if (assignedCheck.rows.length === 1) {
            deleteAssignedFailed = true; // blocked from deletion
        }
    } catch (e) {
        deleteAssignedFailed = true;
    }
    assert(deleteAssignedFailed, 'Premature deletion of actively assigned brief blocked by contract preservation guard');

    let invalidDemotionFailed = false;
    try {
        await db.exec(`UPDATE public.briefs SET status = 'draft' WHERE id = '${BRIEF_ASSIGNED}';`);
    } catch (e) {
        invalidDemotionFailed = true;
    }
    assert(invalidDemotionFailed, 'Demoting actively assigned brief back to draft blocked');

    // =========================================================================
    // SUITE 7: Schema Constraints Rejection Tests
    // =========================================================================
    console.log('\n[SUITE 7] Schema Constraints Rejection Tests:');
    let invertedBudgetFailed = false;
    try {
        await db.exec(`
            INSERT INTO public.briefs (customer_id, title, description, content_type, budget_min, budget_max, status)
            VALUES ('${USER_CUSTOMER_A}', 'Bad Budget', 'Desc', 'Ad', 5000, 2000, 'open');
        `);
    } catch (e) {
        invertedBudgetFailed = true;
    }
    assert(invertedBudgetFailed, 'Inverted budget range (min > max) rejected by CHECK constraint');

    let invalidAspectFailed = false;
    try {
        await db.exec(`
            INSERT INTO public.portfolio_items (creator_id, title, video_url, content_type, style, aspect_ratio)
            VALUES ('${CREATOR_PROFILE_A}', 'Bad Aspect', 'https://video.test/bad.mp4', 'Ad', 'Clean', '3:2');
        `);
    } catch (e) {
        invalidAspectFailed = true;
    }
    assert(invalidAspectFailed, 'Invalid aspect ratio (3:2) rejected by CHECK constraint');

    let dupPitchFailed = false;
    try {
        await db.exec(`
            INSERT INTO public.creator_interests (brief_id, creator_id, pitch_note, estimated_delivery_days, proposed_quote, status)
            VALUES ('${BRIEF_A}', '${CREATOR_PROFILE_A}', 'Duplicate pitch', 5, 1500, 'submitted');
        `);
    } catch (e) {
        dupPitchFailed = true;
    }
    assert(dupPitchFailed, 'Duplicate pitch on same brief blocked by UNIQUE(brief_id, creator_id) constraint');

    // =========================================================================
    // SUITE 8: One-Sided Anonymity & Creator Private Contacts (Marketplace Evolution)
    // =========================================================================
    console.log('\n[SUITE 8] Adversarial Attack: One-Sided Anonymity & Private Contacts:');
    // Seed private contact for Creator A
    await setJwtContext(null, 'service_role');
    await db.exec(`
        INSERT INTO public.creator_private_contacts (creator_id, legal_name, contact_email, phone_number, billing_address)
        VALUES ('${CREATOR_PROFILE_A}', 'Alex Creates LLC', 'alex@direct-agency.test', '+1-555-999-8888', '100 Studio Way, Austin TX')
        ON CONFLICT (creator_id) DO NOTHING;
    `);

    // Customer B queries anonymous_creators: should see masked pseudonym
    await setJwtContext(USER_CUSTOMER_B);
    const anonView = await db.query(`SELECT display_name FROM public.anonymous_creators WHERE id = '${CREATOR_PROFILE_A}';`);
    assert(anonView.rows[0].display_name.startsWith('Creator '), `Locked creator name is masked in anonymous view (found: ${anonView.rows[0].display_name})`);

    // Customer B attempts to read private contacts: should return 0 rows (blocked by RLS)
    const privateContactB = await db.query(`SELECT * FROM public.creator_private_contacts WHERE creator_id = '${CREATOR_PROFILE_A}';`);
    assert(privateContactB.rows.length === 0, 'Customer B cannot read Creator A private contact details (0 rows via RLS)');

    // Seed verified unlock for Customer A
    await setJwtContext(null, 'service_role');
    await db.exec(`
        INSERT INTO public.contact_unlocks (customer_id, creator_id, status)
        VALUES ('${USER_CUSTOMER_A}', '${CREATOR_PROFILE_A}', 'active')
        ON CONFLICT (customer_id, creator_id) DO UPDATE SET status = 'active';
    `);

    // Customer A queries private contacts: should succeed!
    await setJwtContext(USER_CUSTOMER_A);
    const privateContactA = await db.query(`SELECT contact_email FROM public.creator_private_contacts WHERE creator_id = '${CREATOR_PROFILE_A}';`);
    assert(privateContactA.rows.length === 1 && privateContactA.rows[0].contact_email === 'alex@direct-agency.test', 'Unlocked Customer A can read Creator A private contact details');

    // Regression: Anonymous visitors can discover public creators
    await setJwtContext(null, 'anon');
    const anonDiscover = await db.query(`SELECT id, handle, display_name, avatar_url FROM public.anonymous_creators;`);
    assert(anonDiscover.rows.length >= 2, 'Anonymous visitors can discover public creators');

    // Regression: Authenticated customers can discover public creators
    await setJwtContext(USER_CUSTOMER_B);
    const custDiscover = await db.query(`SELECT id, handle, display_name, avatar_url FROM public.anonymous_creators;`);
    assert(custDiscover.rows.length >= 2, 'Authenticated customers can discover public creators');

    // Regression: Public creator avatar URLs are returned correctly
    assert(anonDiscover.rows.some(r => r.avatar_url === 'https://avatar.test/alex.png') &&
           custDiscover.rows.some(r => r.avatar_url === 'https://avatar.test/alex.png'),
           'Public creator avatar URLs are returned correctly');

    // Regression: Creator search queries execute successfully without joining public.users
    const searchQ1 = await db.query(`
        SELECT c.id, c.handle, c.display_name, c.avatar_url
        FROM public.creators c
        ORDER BY c.rating DESC;
    `);
    assert(searchQ1.rows.length >= 2 && searchQ1.rows[0].avatar_url !== null, 'Creator search queries execute without public.users join');

    // Regression: Non-public creator profiles remain hidden
    await setJwtContext(null, 'service_role');
    const HIDDEN_CREATOR = '00000000-0000-0000-0001-000000000099';
    const HIDDEN_USER = '00000000-0000-0000-0000-000000000199';
    await db.exec(`
        INSERT INTO public.users (id, email, full_name, role) VALUES ('${HIDDEN_USER}', 'hidden@test.local', 'Hidden Creator', 'creator') ON CONFLICT DO NOTHING;
        INSERT INTO public.creators (id, user_id, handle, display_name, profile_visibility, avatar_url)
        VALUES ('${HIDDEN_CREATOR}', '${HIDDEN_USER}', '@hidden_one', 'Hidden One', 'private', 'https://avatar.test/hidden.png')
        ON CONFLICT DO NOTHING;
    `);
    await setJwtContext(null, 'anon');
    const hiddenAnon = await db.query(`SELECT id FROM public.anonymous_creators WHERE id = '${HIDDEN_CREATOR}';`);
    assert(hiddenAnon.rows.length === 0, 'Non-public creator profiles remain hidden from anonymous visitors');
    await setJwtContext(USER_CUSTOMER_B);
    const hiddenCust = await db.query(`SELECT id FROM public.anonymous_creators WHERE id = '${HIDDEN_CREATOR}';`);
    assert(hiddenCust.rows.length === 0, 'Non-public creator profiles remain hidden from authenticated customers');

    // =========================================================================
    // SUITE 9: In-Platform Chat Access & Moderation Tampering
    // =========================================================================
    console.log('\n[SUITE 9] Adversarial Attack: In-Platform Chat & Moderation Tampering:');
    const CONVO_ID = '00000000-0000-0000-0011-000000000001';
    const MSG_BLOCKED = '00000000-0000-0000-0013-000000000099';

    await setJwtContext(null, 'service_role');
    await db.exec(`
        INSERT INTO public.chat_conversations (id, created_by, status)
        VALUES ('${CONVO_ID}', '${USER_CUSTOMER_A}', 'active')
        ON CONFLICT (id) DO NOTHING;

        INSERT INTO public.chat_participants (conversation_id, user_id, role, display_alias)
        VALUES 
        ('${CONVO_ID}', '${USER_CUSTOMER_A}', 'customer', 'Alice'),
        ('${CONVO_ID}', '${USER_CREATOR_A}', 'creator', 'Creator #A')
        ON CONFLICT (conversation_id, user_id) DO NOTHING;

        INSERT INTO public.chat_messages (id, conversation_id, sender_id, content, moderation_status)
        VALUES ('${MSG_BLOCKED}', '${CONVO_ID}', '${USER_CREATOR_A}', 'Text me on +1-555-1234', 'blocked')
        ON CONFLICT (id) DO NOTHING;

        INSERT INTO public.chat_attachments (id, message_id, file_name, file_url, file_type, file_size_bytes)
        VALUES ('00000000-0000-0000-0014-000000000001', '${MSG_BLOCKED}', 'storyboard.pdf', 'https://cdn.test/storyboard.pdf', 'application/pdf', 1048576)
        ON CONFLICT (id) DO NOTHING;
    `);

    // Customer B (not participant) attempts to read conversation messages
    await setJwtContext(USER_CUSTOMER_B);
    const eavesdropCheck = await db.query(`SELECT * FROM public.chat_messages WHERE conversation_id = '${CONVO_ID}';`);
    assert(eavesdropCheck.rows.length === 0, 'Unrelated Customer B cannot read conversation messages (0 rows via RLS)');

    // Customer B attempts to read conversation attachments
    const eavesdropAttach = await db.query(`SELECT * FROM public.chat_attachments WHERE message_id = '${MSG_BLOCKED}';`);
    assert(eavesdropAttach.rows.length === 0, 'Unrelated Customer B cannot read conversation attachments (0 rows via RLS)');

    // Sender (Creator A) can legitimately attach a file to their own message
    await setJwtContext(USER_CREATOR_A);
    const ATTACH_LEGIT = '00000000-0000-0000-0014-000000000002';
    await db.exec(`
        INSERT INTO public.chat_attachments (id, message_id, file_name, file_url, file_type, file_size_bytes)
        VALUES ('${ATTACH_LEGIT}', '${MSG_BLOCKED}', 'proposal_script.pdf', 'https://cdn.test/script.pdf', 'application/pdf', 524288);
    `);
    const attachCheck = await db.query(`SELECT id FROM public.chat_attachments WHERE id = '${ATTACH_LEGIT}';`);
    assert(attachCheck.rows.length === 1, 'Sender can attach file to own chat message via INSERT policy');

    // Customer B (unrelated user) cannot insert attachments into Creator A message
    await setJwtContext(USER_CUSTOMER_B);
    let forgeAttachBlocked = false;
    try {
        await db.exec(`
            INSERT INTO public.chat_attachments (id, message_id, file_name, file_url, file_type, file_size_bytes)
            VALUES ('00000000-0000-0000-0014-000000000099', '${MSG_BLOCKED}', 'exploit.exe', 'https://cdn.test/exploit.exe', 'application/octet-stream', 1024);
        `);
    } catch (e) {
        forgeAttachBlocked = true;
    }
    assert(forgeAttachBlocked, 'Unrelated user cannot attach files to another user message (blocked by RLS WITH CHECK)');

    // Conversation participant Customer A cannot attach files to Creator A's message
    await setJwtContext(USER_CUSTOMER_A);
    let crossSenderAttachBlocked = false;
    try {
        await db.exec(`
            INSERT INTO public.chat_attachments (id, message_id, file_name, file_url, file_type, file_size_bytes)
            VALUES ('00000000-0000-0000-0014-000000000098', '${MSG_BLOCKED}', 'tamper.pdf', 'https://cdn.test/tamper.pdf', 'application/pdf', 2048);
        `);
    } catch (e) {
        crossSenderAttachBlocked = true;
    }
    assert(crossSenderAttachBlocked, 'Conversation participant cannot attach files to another user message');

    // Conversation participant Customer A cannot delete Creator A's attachment
    let crossDeleteBlocked = false;
    try {
        const delRes = await db.query(`DELETE FROM public.chat_attachments WHERE id = '${ATTACH_LEGIT}' RETURNING id;`);
        if (delRes.rows.length === 0) crossDeleteBlocked = true;
    } catch (e) {
        crossDeleteBlocked = true;
    }
    assert(crossDeleteBlocked, 'Conversation participant cannot delete another participant attachment');

    // Attaching files to a soft-deleted message is blocked
    const MSG_DELETED = '00000000-0000-0000-0013-000000000098';
    await setJwtContext(null, 'service_role');
    await db.exec(`
        INSERT INTO public.chat_messages (id, conversation_id, sender_id, content, moderation_status, deleted_at)
        VALUES ('${MSG_DELETED}', '${CONVO_ID}', '${USER_CREATOR_A}', 'Old deleted note', 'allowed', CURRENT_TIMESTAMP)
        ON CONFLICT (id) DO NOTHING;
    `);
    await setJwtContext(USER_CREATOR_A);
    let attachToDeletedBlocked = false;
    try {
        await db.exec(`
            INSERT INTO public.chat_attachments (id, message_id, file_name, file_url, file_type, file_size_bytes)
            VALUES ('00000000-0000-0000-0014-000000000097', '${MSG_DELETED}', 'late.pdf', 'https://cdn.test/late.pdf', 'application/pdf', 1024);
        `);
    } catch (e) {
        attachToDeletedBlocked = true;
    }
    assert(attachToDeletedBlocked, 'Sender cannot attach file to a soft-deleted message');

    // Creator A (sender) legitimately deletes their own attachment
    const legitimateDelete = await db.query(`DELETE FROM public.chat_attachments WHERE id = '${ATTACH_LEGIT}' RETURNING id;`);
    assert(legitimateDelete.rows.length === 1, 'Sender can legitimately delete own message attachment');

    // Creator A (sender) attempts to reassign message sender or conversation
    await setJwtContext(USER_CREATOR_A);
    let reassignFailed = false;
    try {
        await db.exec(`UPDATE public.chat_messages SET sender_id = '${USER_CUSTOMER_A}' WHERE id = '${MSG_BLOCKED}';`);
    } catch (e) {
        reassignFailed = true;
    }
    assert(reassignFailed, 'Sender cannot reassign message sender_id or impersonate other participant');

    // Creator A (sender) attempts to unblock their own message
    let unblockFailed = false;
    try {
        await db.exec(`UPDATE public.chat_messages SET moderation_status = 'allowed' WHERE id = '${MSG_BLOCKED}';`);
    } catch (e) {
        unblockFailed = true;
    }
    assert(unblockFailed, 'Ordinary sender cannot self-unblock message flagged by moderation trigger');

    // =========================================================================
    // SUITE 10: Creator Quote Pricing Integrity & Masking
    // =========================================================================
    console.log('\n[SUITE 10] Adversarial Attack: Creator Quote Pricing Integrity:');
    const QUOTE_ID = '00000000-0000-0000-0015-000000000001';
    await setJwtContext(null, 'service_role');
    await db.exec(`
        INSERT INTO public.project_quotes (
            id, brief_id, creator_id, creator_quote_amount, platform_fee_rate, platform_fee_amount,
            tax_amount, customer_price_amount, scope_summary, estimated_delivery_days, valid_until, status
        )
        VALUES (
            '${QUOTE_ID}', '${BRIEF_A}', '${CREATOR_PROFILE_A}', 2000.00, 0.1500, 300.00,
            0.00, 2300.00, 'Scope details', 7, CURRENT_TIMESTAMP + INTERVAL '7 days', 'presented_to_customer'
        )
        ON CONFLICT (id) DO NOTHING;
    `);

    // Creator updates quote amount: trigger should automatically recalculate customer_price_amount
    await setJwtContext(USER_CREATOR_A);
    await db.exec(`UPDATE public.project_quotes SET creator_quote_amount = 3000.00 WHERE id = '${QUOTE_ID}';`);
    const quotePriceCheck = await db.query(`SELECT platform_fee_amount, customer_price_amount FROM public.project_quotes WHERE id = '${QUOTE_ID}';`);
    assert(Number(quotePriceCheck.rows[0].platform_fee_amount) === 450.00, 'Platform fee automatically computed at 15% ($450.00)');
    assert(Number(quotePriceCheck.rows[0].customer_price_amount) === 3450.00, 'Customer price automatically computed as quote + fee ($3450.00)');

    // Cross-Tenant View Isolation: Customer A sees presented quote for their brief
    await setJwtContext(USER_CUSTOMER_A);
    const custAQuotes = await db.query(`SELECT * FROM public.customer_quotes_view WHERE brief_id = '${BRIEF_A}';`);
    assert(custAQuotes.rows.length === 1, 'Customer A can view presented quotes for own brief via customer_quotes_view');
    assert(Number(custAQuotes.rows[0].customer_price_amount) === 3450.00, 'Customer quotes view presents computed price to customer');

    // Customer B (different customer) cannot see quotes for Customer A's brief via customer_quotes_view
    await setJwtContext(USER_CUSTOMER_B);
    const custBQuotes = await db.query(`SELECT * FROM public.customer_quotes_view WHERE brief_id = '${BRIEF_A}';`);
    assert(custBQuotes.rows.length === 0, 'Customer B cannot read Customer A quotes via customer_quotes_view (cross-tenant leak prevented by security_invoker)');

    // =========================================================================
    // SUITE 11: Formal Project Contract Lifecycle State Machine
    // =========================================================================
    console.log('\n[SUITE 11] Adversarial Attack: Project Contract Lifecycle:');
    const PROJ_ID = '00000000-0000-0000-0016-000000000099';
    await setJwtContext(null, 'service_role');
    await db.exec(`
        INSERT INTO public.projects (
            id, brief_id, customer_id, creator_id, title, agreed_amount, creator_earnings,
            platform_fee, currency, status
        )
        VALUES (
            '${PROJ_ID}', '${BRIEF_A}', '${USER_CUSTOMER_A}', '${CREATOR_PROFILE_A}',
            'Active Contract', 3450.00, 3000.00, 450.00, 'USD', 'in_progress'
        )
        ON CONFLICT (id) DO NOTHING;
    `);

    // Customer attempts invalid state transition from in_progress directly to draft
    await setJwtContext(USER_CUSTOMER_A);
    let invalidDemotionProj = false;
    try {
        await db.exec(`UPDATE public.projects SET status = 'draft' WHERE id = '${PROJ_ID}';`);
    } catch (e) {
        invalidDemotionProj = true;
    }
    assert(invalidDemotionProj, 'Demoting active project back to draft rejected by state machine trigger');

    // Customer attempts to modify financial terms on active contract
    let termsAlterFailed = false;
    try {
        await db.exec(`UPDATE public.projects SET agreed_amount = 500.00 WHERE id = '${PROJ_ID}';`);
    } catch (e) {
        termsAlterFailed = true;
    }
    assert(termsAlterFailed, 'Modifying agreed financial terms on active project contract blocked');

    // Creator updates status to submitted: valid transition!
    await setJwtContext(USER_CREATOR_A);
    await db.exec(`UPDATE public.projects SET status = 'submitted' WHERE id = '${PROJ_ID}';`);
    const projStateCheck = await db.query(`SELECT status FROM public.projects WHERE id = '${PROJ_ID}';`);
    assert(projStateCheck.rows[0].status === 'submitted', 'Legitimate project progression to submitted state allowed');

    // =========================================================================
    // SUITE 12: Payment State Forgery & Contact Unlock Protection
    // =========================================================================
    console.log('\n[SUITE 12] Adversarial Attack: Payment State & Unlock Tampering:');
    const PAY_ID = '00000000-0000-0000-0017-000000000099';
    await setJwtContext(null, 'service_role');
    await db.exec(`
        INSERT INTO public.payments (
            id, customer_id, provider, amount, currency, status, idempotency_key
        )
        VALUES ('${PAY_ID}', '${USER_CUSTOMER_A}', 'stripe', 3450.00, 'USD', 'pending', 'idem_test_999')
        ON CONFLICT (id) DO NOTHING;
    `);

    // Customer attempts to mark payment as succeeded directly
    await setJwtContext(USER_CUSTOMER_A);
    let fakePaySuccess = false;
    try {
        await db.exec(`UPDATE public.payments SET status = 'succeeded' WHERE id = '${PAY_ID}';`);
    } catch (e) {
        fakePaySuccess = true;
    }
    assert(fakePaySuccess, 'Customer marking payment as succeeded blocked by protect_payment_state trigger');

    // Customer attempts to create contact unlock with pending payment
    let fakeUnlockFailed = false;
    try {
        await db.exec(`
            INSERT INTO public.contact_unlocks (customer_id, creator_id, payment_id, status)
            VALUES ('${USER_CUSTOMER_B}', '${CREATOR_PROFILE_B}', '${PAY_ID}', 'active');
        `);
    } catch (e) {
        fakeUnlockFailed = true;
    }
    assert(fakeUnlockFailed, 'Creating contact unlock with unverified payment blocked by trigger');

    // =========================================================================
    // SUITE 13: Verified Reviews & Anti-Self-Review Guard
    // =========================================================================
    console.log('\n[SUITE 13] Adversarial Attack: Verified Reviews Guard:');
    // PROJ_ID is currently 'submitted', not 'completed'
    await setJwtContext(USER_CUSTOMER_A);
    let prematureReviewFailed = false;
    try {
        await db.exec(`
            INSERT INTO public.reviews (project_id, customer_id, creator_id, rating, review_text)
            VALUES ('${PROJ_ID}', '${USER_CUSTOMER_A}', '${CREATOR_PROFILE_A}', 5.00, 'Premature review before completion');
        `);
    } catch (e) {
        prematureReviewFailed = true;
    }
    assert(prematureReviewFailed, 'Submitting review on non-completed project rejected by validate_and_apply_review');

    // Complete project legitimately via service_role, then submit review
    await setJwtContext(null, 'service_role');
    await db.exec(`UPDATE public.projects SET status = 'completed' WHERE id = '${PROJ_ID}';`);
    await setJwtContext(USER_CUSTOMER_A);
    await db.exec(`
        INSERT INTO public.reviews (project_id, customer_id, creator_id, rating, review_text)
        VALUES ('${PROJ_ID}', '${USER_CUSTOMER_A}', '${CREATOR_PROFILE_A}', 5.00, 'Outstanding delivery, highly recommended!');
    `);

    const ratingCheck = await db.query(`SELECT rating, total_reviews FROM public.creators WHERE id = '${CREATOR_PROFILE_A}';`);
    assert(Number(ratingCheck.rows[0].rating) === 5.00, 'Legitimate published review automatically updated creator rating in creators table');

    // =========================================================================
    // SUITE 14: Creator Subscription Entitlements
    // =========================================================================
    console.log('\n[SUITE 14] Adversarial Attack: Creator Subscription Entitlements:');
    await setJwtContext(null, 'service_role');
    await db.exec(`
        INSERT INTO public.creator_subscriptions (creator_id, tier, status)
        VALUES ('${CREATOR_PROFILE_A}', 'free', 'active')
        ON CONFLICT (id) DO NOTHING;
    `);

    // Creator attempts to self-upgrade tier directly (blocked by trigger protect_creator_subscription_updates)
    await setJwtContext(USER_CREATOR_A);
    let subUpgradeFailed = false;
    try {
        await db.exec(`UPDATE public.creator_subscriptions SET tier = 'agency' WHERE creator_id = '${CREATOR_PROFILE_A}';`);
    } catch (e) {
        subUpgradeFailed = true;
    }
    await setJwtContext(null, 'service_role');
    const tierCheck = await db.query(`SELECT tier FROM public.creator_subscriptions WHERE creator_id = '${CREATOR_PROFILE_A}';`);
    assert(subUpgradeFailed || tierCheck.rows[0].tier === 'free', 'Creator self-upgrading subscription tier blocked by trigger/RLS (tier remained free)');

    // Summary
    console.log('\n================================================================');
    console.log(`SUMMARY: ${passedTests} / ${totalTests} ADVERSARIAL PENETRATION ATTACKS MITIGATED (${failedTests} FAILED)`);
    console.log('================================================================\n');

    if (failedTests > 0) {
        process.exit(1);
    }
}

runAdversarialAudit().catch(err => {
    console.error('Adversarial Test Suite Error:', err);
    process.exit(1);
});
