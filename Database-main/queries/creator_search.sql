-- ============================================================================
-- Query Suite: queries/creator_search.sql
-- Project: CreatorSphere AI
-- Description: Parameterized, production-ready PostgreSQL queries for creator
--              discovery, multi-parameter filtering, full-text search,
--              and portfolio showcases.
-- Security:    Uses strictly parameterized SQL ($1, $2, etc.) to prevent SQL injection.
-- ============================================================================

-- ============================================================================
-- QUERY 1: Retrieve All Active Creators (Paginated with sorting)
-- Parameters:
--   $1: limit (INT, default: 12)
--   $2: offset (INT, default: 0)
-- ============================================================================
SELECT 
    c.id,
    c.handle,
    c.display_name,
    c.tagline,
    c.skills,
    c.tools,
    c.styles,
    c.content_types,
    c.indicative_budget_min,
    c.indicative_budget_max,
    c.currency,
    c.availability,
    c.rating,
    c.total_reviews,
    c.is_featured,
    c.avatar_url,
    (
        SELECT COUNT(*) 
        FROM public.portfolio_items p 
        WHERE p.creator_id = c.id
    ) AS portfolio_count
FROM public.creators c
ORDER BY c.is_featured DESC, c.rating DESC, c.total_reviews DESC
LIMIT $1 OFFSET $2;


-- ============================================================================
-- QUERY 2: Search Creators by Name or Handle (Fuzzy Match & Ranking)
-- Parameter:
--   $1: search_term (TEXT, e.g. 'Elena')
-- ============================================================================
SELECT 
    c.id,
    c.handle,
    c.display_name,
    c.tagline,
    c.skills,
    c.availability,
    c.rating,
    c.avatar_url,
    similarity(c.display_name, $1) AS match_score
FROM public.creators c
WHERE 
    c.display_name ILIKE '%' || $1 || '%'
    OR c.handle ILIKE '%' || $1 || '%'
ORDER BY match_score DESC, c.rating DESC;


-- ============================================================================
-- QUERY 3: Filter by Skills (Array Containment)
-- Parameter:
--   $1: required_skills (TEXT[], e.g. ARRAY['AI Video Generation'])
-- ============================================================================
SELECT 
    c.id,
    c.handle,
    c.display_name,
    c.skills,
    c.indicative_budget_min,
    c.indicative_budget_max,
    c.availability,
    c.rating
FROM public.creators c
WHERE c.skills @> $1
ORDER BY c.rating DESC;


-- ============================================================================
-- QUERY 4: Filter by Tools (Array Overlap)
-- Parameter:
--   $1: target_tools (TEXT[], e.g. ARRAY['Blender', 'Cinema 4D'])
-- ============================================================================
SELECT 
    c.id,
    c.handle,
    c.display_name,
    c.tools,
    c.availability,
    c.rating
FROM public.creators c
WHERE c.tools && $1
ORDER BY c.rating DESC;


-- ============================================================================
-- QUERY 5: Filter by Content Type (Array Overlap)
-- Parameter:
--   $1: target_content_types (TEXT[], e.g. ARRAY['Product Commercial'])
-- ============================================================================
SELECT 
    c.id,
    c.handle,
    c.display_name,
    c.content_types,
    c.indicative_budget_min,
    c.indicative_budget_max,
    c.rating
FROM public.creators c
WHERE c.content_types && $1
ORDER BY c.rating DESC;


-- ============================================================================
-- QUERY 6: Filter by Style (Array Overlap)
-- Parameter:
--   $1: target_styles (TEXT[], e.g. ARRAY['Cyberpunk', 'Sci-Fi Surrealism'])
-- ============================================================================
SELECT 
    c.id,
    c.handle,
    c.display_name,
    c.styles,
    c.rating,
    c.availability
FROM public.creators c
WHERE c.styles && $1
ORDER BY c.rating DESC;


-- ============================================================================
-- QUERY 7: Filter by Availability Status
-- Parameter:
--   $1: target_availability (TEXT: 'available', 'busy', 'unavailable')
-- ============================================================================
SELECT 
    c.id,
    c.handle,
    c.display_name,
    c.availability,
    c.rating,
    c.experience_years
FROM public.creators c
WHERE c.availability = $1
ORDER BY c.rating DESC;


-- ============================================================================
-- QUERY 8: Filter by Indicative Budget Range
-- Parameters:
--   $1: customer_max_budget (NUMERIC)
--   $2: customer_min_budget (NUMERIC)
-- ============================================================================
SELECT 
    c.id,
    c.handle,
    c.display_name,
    c.indicative_budget_min,
    c.indicative_budget_max,
    c.currency,
    c.rating
FROM public.creators c
WHERE c.indicative_budget_min <= $1
  AND c.indicative_budget_max >= $2
ORDER BY c.indicative_budget_min ASC;


-- ============================================================================
-- QUERY 9: Combined Multi-Parameter Marketplace Filter (AI Matching Engine)
-- Parameters:
--   $1: target_availability (TEXT: 'available')
--   $2: min_rating (NUMERIC: 4.80)
--   $3: max_budget (NUMERIC: 3000.00)
--   $4: skills_filter (TEXT[]: ARRAY['Fast Pacing Editing'])
--   $5: tools_filter (TEXT[]: ARRAY['Adobe Premiere Pro'])
-- ============================================================================
SELECT 
    c.id,
    c.handle,
    c.display_name,
    c.skills,
    c.tools,
    c.indicative_budget_min,
    c.indicative_budget_max,
    c.availability,
    c.rating,
    c.total_reviews,
    c.avatar_url
FROM public.creators c
WHERE 
    c.availability = $1
    AND c.rating >= $2
    AND c.indicative_budget_min <= $3
    AND c.skills && $4
    AND c.tools && $5
ORDER BY c.rating DESC, c.total_reviews DESC;


-- ============================================================================
-- QUERY 10: Retrieve Creator Profile with Full Portfolio & Verification Badges
-- Parameter:
--   $1: creator_id (UUID)
-- ============================================================================
SELECT 
    c.id AS creator_id,
    c.handle,
    c.display_name,
    c.bio,
    c.skills,
    c.tools,
    c.styles,
    c.rating,
    c.website_url,
    c.avatar_url,
    p.id AS portfolio_id,
    p.title AS portfolio_title,
    p.video_url,
    p.thumbnail_url,
    p.content_type,
    p.style AS portfolio_style,
    p.aspect_ratio,
    p.duration_seconds,
    p.tools_used,
    p.verification_status,
    v.signal_type,
    v.status AS signal_status
FROM public.creators c
LEFT JOIN public.portfolio_items p ON p.creator_id = c.id
LEFT JOIN public.verification_signals v ON v.creator_id = c.id AND v.portfolio_item_id = p.id
WHERE c.id = $1
ORDER BY p.is_featured DESC, p.created_at DESC;


-- ============================================================================
-- QUERY 17: Empty Search Fallback (Relaxed Similar Creators Recommender)
-- When a hyper-specific filter yields 0 rows, relax the strict requirements
-- to suggest the closest top-rated creators in the same general domain.
-- Parameter:
--   $1: target_skills (TEXT[])
-- ============================================================================
WITH matched_creators AS (
    SELECT id FROM public.creators
    WHERE skills @> $1
)
SELECT 
    c.id,
    c.handle,
    c.display_name,
    c.tagline,
    c.skills,
    c.rating,
    c.availability,
    'Top Rated Alternative' AS recommendation_reason
FROM public.creators c
WHERE NOT EXISTS (SELECT 1 FROM matched_creators)
  AND c.availability = 'available'
ORDER BY c.rating DESC, c.total_reviews DESC
LIMIT 4;
