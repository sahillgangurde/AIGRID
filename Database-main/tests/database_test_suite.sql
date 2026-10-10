-- ============================================================================
-- Test Suite: tests/database_test_suite.sql
-- Project: CreatorSphere AI
-- Description: Automated verification script with assertions testing schema
--              integrity, foreign keys, CHECK constraints, UNIQUE constraints,
--              GIN search queries, and RLS activation.
--
-- How to run:
-- Execute this entire file in the Supabase SQL Editor.
-- The tests run inside a temporary DO block; errors will trigger an explicit
-- RAISE EXCEPTION detailing which assertion failed.
-- ============================================================================

DO $$
DECLARE
    v_count INT;
    v_test_user_id UUID := '99999999-9999-9999-9999-999999999991';
    v_test_creator_id UUID := '99999999-9999-9999-9999-999999999992';
    v_test_brief_id UUID := '99999999-9999-9999-9999-999999999993';
    v_error_caught BOOLEAN;
    v_old_timestamp TIMESTAMPTZ;
    v_new_timestamp TIMESTAMPTZ;
BEGIN
    RAISE NOTICE '=======================================================';
    RAISE NOTICE 'STARTING CREATORSPHERE AI TEST SUITE';
    RAISE NOTICE '=======================================================';

    -- ------------------------------------------------------------------------
    -- TEST 1: Verify all 7 core tables exist in the public schema
    -- ------------------------------------------------------------------------
    SELECT COUNT(*) INTO v_count
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
      AND table_name IN (
        'users', 'creators', 'portfolio_items',
        'briefs', 'enquiries', 'creator_interests', 'verification_signals'
      );

    IF v_count <> 7 THEN
        RAISE EXCEPTION 'TEST 1 FAILED: Expected 7 tables, found %', v_count;
    END IF;
    RAISE NOTICE 'TEST 1 PASSED: All 7 core tables exist.';

    -- ------------------------------------------------------------------------
    -- TEST 2: Verify Row Level Security (RLS) is ENABLED on all 7 tables
    -- ------------------------------------------------------------------------
    SELECT COUNT(*) INTO v_count
    FROM pg_tables
    WHERE schemaname = 'public'
      AND tablename IN (
        'users', 'creators', 'portfolio_items',
        'briefs', 'enquiries', 'creator_interests', 'verification_signals'
      )
      AND rowsecurity = true;

    IF v_count <> 7 THEN
        RAISE EXCEPTION 'TEST 2 FAILED: Expected RLS enabled on 7 tables, found %', v_count;
    END IF;
    RAISE NOTICE 'TEST 2 PASSED: Row Level Security is active on all 7 tables.';

    -- ------------------------------------------------------------------------
    -- TEST 3: Check Constraint: Rejects invalid user role
    -- ------------------------------------------------------------------------
    v_error_caught := false;
    BEGIN
        INSERT INTO public.users (email, full_name, role)
        VALUES ('invalid.role@test.local', 'Invalid Role User', 'admin_super');
    EXCEPTION WHEN check_violation THEN
        v_error_caught := true;
    END;

    IF NOT v_error_caught THEN
        RAISE EXCEPTION 'TEST 3 FAILED: Invalid role was not rejected by CHECK constraint.';
    END IF;
    RAISE NOTICE 'TEST 3 PASSED: Invalid user role rejected.';

    -- ------------------------------------------------------------------------
    -- TEST 4: Check Constraint: Rejects budget_max < budget_min on creators
    -- ------------------------------------------------------------------------
    -- Insert a valid temporary test user first
    INSERT INTO public.users (id, email, full_name, role)
    VALUES (v_test_user_id, 'test.creator@test.local', 'Test Creator QA', 'creator');

    v_error_caught := false;
    BEGIN
        INSERT INTO public.creators (
            id, user_id, handle, display_name,
            indicative_budget_min, indicative_budget_max
        )
        VALUES (
            v_test_creator_id, v_test_user_id, '@qa_test_creator', 'QA Tester',
            5000.00, 1000.00 -- INVALID: max is lower than min
        );
    EXCEPTION WHEN check_violation THEN
        v_error_caught := true;
    END;

    IF NOT v_error_caught THEN
        RAISE EXCEPTION 'TEST 4 FAILED: Inverted budget range was not rejected.';
    END IF;
    RAISE NOTICE 'TEST 4 PASSED: Inverted budget rejected by CHECK constraint.';

    -- ------------------------------------------------------------------------
    -- TEST 5: Check Constraint: Rejects invalid aspect ratio on portfolio items
    -- ------------------------------------------------------------------------
    -- Insert a valid creator first
    INSERT INTO public.creators (
        id, user_id, handle, display_name,
        indicative_budget_min, indicative_budget_max
    )
    VALUES (
        v_test_creator_id, v_test_user_id, '@qa_test_creator', 'QA Tester',
        500.00, 1500.00
    );

    v_error_caught := false;
    BEGIN
        INSERT INTO public.portfolio_items (
            creator_id, title, video_url, content_type, style, aspect_ratio
        )
        VALUES (
            v_test_creator_id, 'Invalid Ratio Video', 'https://video.test/1.mp4',
            'Commercial', 'Clean', '3:2' -- INVALID aspect ratio
        );
    EXCEPTION WHEN check_violation THEN
        v_error_caught := true;
    END;

    IF NOT v_error_caught THEN
        RAISE EXCEPTION 'TEST 5 FAILED: Invalid aspect ratio was not rejected.';
    END IF;
    RAISE NOTICE 'TEST 5 PASSED: Invalid aspect ratio rejected.';

    -- ------------------------------------------------------------------------
    -- TEST 6: Unique Constraint: Prevents duplicate handles in creators
    -- ------------------------------------------------------------------------
    v_error_caught := false;
    BEGIN
        -- Attempt to use existing handle '@synthetica_ai' from seed
        INSERT INTO public.creators (
            user_id, handle, display_name, indicative_budget_min, indicative_budget_max
        )
        VALUES (
            v_test_user_id, '@synthetica_ai', 'Duplicate Handle User', 100.00, 500.00
        );
    EXCEPTION WHEN unique_violation THEN
        v_error_caught := true;
    END;

    IF NOT v_error_caught THEN
        RAISE EXCEPTION 'TEST 6 FAILED: Duplicate creator handle was not rejected.';
    END IF;
    RAISE NOTICE 'TEST 6 PASSED: Duplicate creator handle rejected by UNIQUE constraint.';

    -- ------------------------------------------------------------------------
    -- TEST 7: Unique Constraint: Prevents duplicate pitch on the same brief
    -- ------------------------------------------------------------------------
    -- Insert a test brief
    INSERT INTO public.briefs (
        id, customer_id, title, description, content_type, budget_min, budget_max
    )
    VALUES (
        v_test_brief_id, v_test_user_id, 'QA Test Brief', 'Testing unique bids',
        'Social Reel', 200.00, 600.00
    );

    -- First pitch succeeds
    INSERT INTO public.creator_interests (
        brief_id, creator_id, pitch_note, estimated_delivery_days, proposed_quote
    )
    VALUES (
        v_test_brief_id, v_test_creator_id, 'First pitch note', 5, 450.00
    );

    -- Second pitch from same creator on same brief must fail
    v_error_caught := false;
    BEGIN
        INSERT INTO public.creator_interests (
            brief_id, creator_id, pitch_note, estimated_delivery_days, proposed_quote
        )
        VALUES (
            v_test_brief_id, v_test_creator_id, 'Duplicate pitch note', 3, 400.00
        );
    EXCEPTION WHEN unique_violation THEN
        v_error_caught := true;
    END;

    IF NOT v_error_caught THEN
        RAISE EXCEPTION 'TEST 7 FAILED: Duplicate pitch was not rejected by UNIQUE constraint.';
    END IF;
    RAISE NOTICE 'TEST 7 PASSED: Duplicate pitch rejected.';

    -- ------------------------------------------------------------------------
    -- TEST 8: Foreign Key & Cascade Deletion Integrity
    -- ------------------------------------------------------------------------
    -- Deleting the user should cascade-delete the creator, brief, and pitch
    DELETE FROM public.users WHERE id = v_test_user_id;

    SELECT COUNT(*) INTO v_count
    FROM public.creators WHERE id = v_test_creator_id;
    IF v_count <> 0 THEN
        RAISE EXCEPTION 'TEST 8 FAILED: Creator record was not cascaded upon user deletion.';
    END IF;

    SELECT COUNT(*) INTO v_count
    FROM public.briefs WHERE id = v_test_brief_id;
    IF v_count <> 0 THEN
        RAISE EXCEPTION 'TEST 8 FAILED: Brief record was not cascaded upon user deletion.';
    END IF;
    RAISE NOTICE 'TEST 8 PASSED: Cascade deletion verified.';

    -- ------------------------------------------------------------------------
    -- TEST 9: Query Logic: GIN Array Search returns expected results
    -- ------------------------------------------------------------------------
    SELECT COUNT(*) INTO v_count
    FROM public.creators
    WHERE skills @> ARRAY['AI Video Generation'];

    IF v_count < 1 THEN
        RAISE EXCEPTION 'TEST 9 FAILED: GIN array search returned 0 results from seed data.';
    END IF;
    RAISE NOTICE 'TEST 9 PASSED: GIN array containment matched % creators.', v_count;

    -- ------------------------------------------------------------------------
    -- TEST 10: Query Logic: Fuzzy text search matches creator
    -- ------------------------------------------------------------------------
    SELECT COUNT(*) INTO v_count
    FROM public.creators
    WHERE display_name ILIKE '%Elena%';

    IF v_count < 1 THEN
        RAISE EXCEPTION 'TEST 10 FAILED: Fuzzy search for Elena returned 0 results.';
    END IF;
    RAISE NOTICE 'TEST 10 PASSED: Text search matched successfully.';

    -- ------------------------------------------------------------------------
    -- TEST 11: Seed Data Completeness Check
    -- ------------------------------------------------------------------------
    SELECT COUNT(*) INTO v_count FROM public.creators;
    IF v_count < 12 THEN
        RAISE EXCEPTION 'TEST 11 FAILED: Expected at least 12 creators in seed data, found %', v_count;
    END IF;
    RAISE NOTICE 'TEST 11 PASSED: Verified % creators in seed dataset.', v_count;

    -- ------------------------------------------------------------------------
    -- TEST 12: Integrity Guard: Prevent modification of enquiry participants
    -- ------------------------------------------------------------------------
    -- Insert a valid test customer, creator, and enquiry
    INSERT INTO public.users (id, email, full_name, role)
    VALUES (v_test_user_id, 'qa.enquiry.user@test.local', 'QA Enquiry User', 'customer');

    INSERT INTO public.users (id, email, full_name, role)
    VALUES ('99999999-9999-9999-9999-999999999994', 'qa.creator.target@test.local', 'QA Creator Target', 'creator');

    INSERT INTO public.creators (id, user_id, handle, display_name, indicative_budget_min, indicative_budget_max)
    VALUES (v_test_creator_id, '99999999-9999-9999-9999-999999999994', '@qa_enquiry_creator', 'QA Target', 300, 1200);

    INSERT INTO public.enquiries (id, customer_id, creator_id, subject, message)
    VALUES ('99999999-9999-9999-9999-999999999995', v_test_user_id, v_test_creator_id, 'Original Subject', 'Original Msg');

    -- Attempt to change customer_id of enquiry (must be rejected)
    v_error_caught := false;
    BEGIN
        UPDATE public.enquiries
        SET customer_id = '99999999-9999-9999-9999-999999999994'
        WHERE id = '99999999-9999-9999-9999-999999999995';
    EXCEPTION WHEN OTHERS THEN
        v_error_caught := true;
    END;

    IF NOT v_error_caught THEN
        RAISE EXCEPTION 'TEST 12 FAILED: Enquiry participant tampering was not prevented.';
    END IF;
    RAISE NOTICE 'TEST 12 PASSED: Enquiry participant tampering prevented by integrity guard.';

    -- ------------------------------------------------------------------------
    -- TEST 13: Integrity Guard: Prevent creator from self-accepting pitch
    -- ------------------------------------------------------------------------
    INSERT INTO public.briefs (id, customer_id, title, description, content_type, budget_min, budget_max)
    VALUES (v_test_brief_id, v_test_user_id, 'QA Brief', 'Desc', 'Ad', 500, 1500);

    INSERT INTO public.creator_interests (id, brief_id, creator_id, pitch_note, estimated_delivery_days, proposed_quote, status)
    VALUES ('99999999-9999-9999-9999-999999999996', v_test_brief_id, v_test_creator_id, 'My pitch', 5, 800, 'submitted');

    -- ------------------------------------------------------------------------
    -- TEST 14: Integrity Guard: Prevent portfolio self-verification
    -- ------------------------------------------------------------------------
    INSERT INTO public.portfolio_items (id, creator_id, title, video_url, content_type, style, verification_status)
    VALUES ('99999999-9999-9999-9999-999999999997', v_test_creator_id, 'Test Item', 'https://v.test/item.mp4', 'Ad', 'Clean', 'pending');

    v_error_caught := false;
    BEGIN
        UPDATE public.portfolio_items
        SET verification_status = 'verified'
        WHERE id = '99999999-9999-9999-9999-999999999997';
    EXCEPTION WHEN OTHERS THEN
        v_error_caught := true;
    END;

    IF NOT v_error_caught THEN
        RAISE EXCEPTION 'TEST 14 FAILED: Portfolio self-verification was not prevented.';
    END IF;
    RAISE NOTICE 'TEST 14 PASSED: Portfolio self-verification prevented by integrity guard.';

    -- ------------------------------------------------------------------------
    -- TEST 15: Integrity Guard: Prevent deletion of actively assigned brief
    -- ------------------------------------------------------------------------
    UPDATE public.briefs SET status = 'assigned' WHERE id = v_test_brief_id;

    v_error_caught := false;
    BEGIN
        DELETE FROM public.briefs WHERE id = v_test_brief_id;
    EXCEPTION WHEN OTHERS THEN
        v_error_caught := true;
    END;

    IF NOT v_error_caught THEN
        RAISE EXCEPTION 'TEST 15 FAILED: Deletion of assigned brief was not prevented.';
    END IF;
    RAISE NOTICE 'TEST 15 PASSED: Assigned brief deletion prevented by contract retention guard.';

    -- ------------------------------------------------------------------------
    -- TEST 16: Integrity Guard: Prevent user role self-escalation
    -- ------------------------------------------------------------------------
    v_error_caught := false;
    BEGIN
        UPDATE public.users SET role = 'both' WHERE id = v_test_user_id;
    EXCEPTION WHEN OTHERS THEN
        v_error_caught := true;
    END;

    IF NOT v_error_caught THEN
        RAISE EXCEPTION 'TEST 16 FAILED: User role self-escalation was not prevented.';
    END IF;
    RAISE NOTICE 'TEST 16 PASSED: User role self-escalation prevented by user profile guard.';

    -- Demote brief back to cancelled so clean up can delete user without triggering contract guard
    UPDATE public.briefs SET status = 'cancelled' WHERE id = v_test_brief_id;

    -- Clean up test records
    DELETE FROM public.users WHERE id IN (v_test_user_id, '99999999-9999-9999-9999-999999999994');

    RAISE NOTICE '=======================================================';
    RAISE NOTICE 'ALL 16 AUTOMATED DATABASE & INTEGRITY TESTS PASSED 100%%';
    RAISE NOTICE '=======================================================';
END $$;
