-- ============================================================================
-- Query Suite: queries/analytics_and_admin.sql
-- Project: CreatorSphere AI
-- Description: Analytics and administrative queries for monitoring marketplace
--              health, top skills in demand, creator earnings, and verification status.
-- ============================================================================

-- ============================================================================
-- QUERY A1: Marketplace Overview KPIs
-- ============================================================================
SELECT 
    (SELECT COUNT(*) FROM public.users) AS total_users,
    (SELECT COUNT(*) FROM public.creators) AS total_creators,
    (SELECT COUNT(*) FROM public.creators WHERE availability = 'available') AS available_creators,
    (SELECT COUNT(*) FROM public.portfolio_items) AS total_portfolio_items,
    (SELECT COUNT(*) FROM public.briefs) AS total_briefs,
    (SELECT COUNT(*) FROM public.briefs WHERE status = 'open') AS open_briefs,
    (SELECT COUNT(*) FROM public.enquiries) AS total_enquiries,
    (SELECT COUNT(*) FROM public.creator_interests) AS total_pitches,
    (SELECT COUNT(*) FROM public.verification_signals WHERE status = 'verified') AS verified_signals;


-- ============================================================================
-- QUERY A2: Top 10 Creator Skills in Marketplace
-- ============================================================================
SELECT 
    skill_name,
    COUNT(*) AS creator_count
FROM (
    SELECT unnest(skills) AS skill_name
    FROM public.creators
) s
GROUP BY skill_name
ORDER BY creator_count DESC
LIMIT 10;


-- ============================================================================
-- QUERY A3: Top In-Demand Tools
-- ============================================================================
SELECT 
    tool_name,
    COUNT(*) AS usage_count
FROM (
    SELECT unnest(tools) AS tool_name
    FROM public.creators
) t
GROUP BY tool_name
ORDER BY usage_count DESC
LIMIT 10;


-- ============================================================================
-- QUERY A4: Creator Verification Audit & Trust Review
-- ============================================================================
SELECT 
    c.id AS creator_id,
    c.handle,
    c.display_name,
    v.signal_type,
    v.status AS verification_status,
    v.evidence_url,
    v.metadata,
    v.verified_at,
    v.notes
FROM public.verification_signals v
JOIN public.creators c ON v.creator_id = c.id
ORDER BY v.status ASC, v.created_at DESC;
