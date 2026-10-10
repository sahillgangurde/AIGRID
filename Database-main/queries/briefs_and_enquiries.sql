-- ============================================================================
-- Query Suite: queries/briefs_and_enquiries.sql
-- Project: CreatorSphere AI
-- Description: Parameterized production queries for briefs, enquiries,
--              job matching, and pitch proposals.
-- Security:    Uses strictly parameterized SQL ($1, $2, etc.) to prevent SQL injection.
-- ============================================================================

-- ============================================================================
-- QUERY 11: Save / Post a New AI-Assisted Customer Project Brief
-- Parameters:
--   $1: customer_id (UUID)
--   $2: title (TEXT)
--   $3: description (TEXT)
--   $4: ai_summary (TEXT)
--   $5: target_audience (TEXT)
--   $6: content_type (TEXT)
--   $7: preferred_style (TEXT)
--   $8: aspect_ratio (TEXT: '16:9', '9:16', '1:1', etc.)
--   $9: duration_seconds_target (INT)
--   $10: budget_min (NUMERIC)
--   $11: budget_max (NUMERIC)
--   $12: currency (VARCHAR(3))
--   $13: deadline (TIMESTAMPTZ)
--   $14: commercial_use_required (BOOLEAN)
--   $15: required_skills (TEXT[])
--   $16: preferred_tools (TEXT[])
-- ============================================================================
INSERT INTO public.briefs (
    customer_id,
    title,
    description,
    ai_summary,
    target_audience,
    content_type,
    preferred_style,
    aspect_ratio,
    duration_seconds_target,
    budget_min,
    budget_max,
    currency,
    deadline,
    commercial_use_required,
    required_skills,
    preferred_tools,
    status
)
VALUES (
    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, 'open'
)
RETURNING id, title, status, created_at;


-- ============================================================================
-- QUERY 12: Retrieve All Briefs for a Specific Customer (With Pitch Counts)
-- Parameter:
--   $1: customer_id (UUID)
-- ============================================================================
SELECT 
    b.id,
    b.title,
    b.content_type,
    b.preferred_style,
    b.budget_min,
    b.budget_max,
    b.currency,
    b.deadline,
    b.status,
    b.created_at,
    COUNT(ci.id) AS total_pitches_received,
    COUNT(CASE WHEN ci.status = 'shortlisted' THEN 1 END) AS shortlisted_count
FROM public.briefs b
LEFT JOIN public.creator_interests ci ON ci.brief_id = b.id
WHERE b.customer_id = $1
GROUP BY b.id
ORDER BY b.created_at DESC;


-- ============================================================================
-- QUERY 13: Create a Direct Customer-to-Creator Enquiry
-- Parameters:
--   $1: customer_id (UUID)
--   $2: creator_id (UUID)
--   $3: brief_id (UUID or NULL)
--   $4: subject (TEXT)
--   $5: message (TEXT)
--   $6: proposed_budget (NUMERIC or NULL)
--   $7: proposed_deadline (TIMESTAMPTZ or NULL)
-- ============================================================================
INSERT INTO public.enquiries (
    customer_id,
    creator_id,
    brief_id,
    subject,
    message,
    proposed_budget,
    proposed_deadline,
    status
)
VALUES (
    $1, $2, $3, $4, $5, $6, $7, 'pending'
)
RETURNING id, subject, status, created_at;


-- ============================================================================
-- QUERY 14: Retrieve Relevant Project Opportunities for a Creator (AI Match)
-- Parameter:
--   $1: creator_id (UUID)
-- ============================================================================
WITH target_creator AS (
    SELECT id, skills, tools, indicative_budget_min
    FROM public.creators
    WHERE id = $1
)
SELECT 
    b.id AS brief_id,
    b.title,
    b.description,
    b.ai_summary,
    b.content_type,
    b.preferred_style,
    b.budget_min,
    b.budget_max,
    b.currency,
    b.deadline,
    b.required_skills,
    u.full_name AS customer_name,
    cardinality(ARRAY(
        SELECT unnest(b.required_skills)
        INTERSECT
        SELECT unnest(tc.skills)
    )) AS matching_skills_count,
    (
        SELECT ci.status 
        FROM public.creator_interests ci 
        WHERE ci.brief_id = b.id AND ci.creator_id = tc.id
    ) AS existing_application_status
FROM public.briefs b
CROSS JOIN target_creator tc
LEFT JOIN public.users u ON b.customer_id = u.id
WHERE 
    b.status = 'open'
    AND b.required_skills && tc.skills
    AND b.budget_max >= tc.indicative_budget_min
ORDER BY matching_skills_count DESC, b.created_at DESC;


-- ============================================================================
-- QUERY 15: Record Creator Interest / Submit Pitch on a Project Brief
-- Parameters:
--   $1: brief_id (UUID)
--   $2: creator_id (UUID)
--   $3: pitch_note (TEXT)
--   $4: estimated_delivery_days (INT)
--   $5: proposed_quote (NUMERIC)
--   $6: sample_portfolio_item_id (UUID or NULL)
-- ============================================================================
INSERT INTO public.creator_interests (
    brief_id,
    creator_id,
    pitch_note,
    estimated_delivery_days,
    proposed_quote,
    sample_portfolio_item_id,
    status
)
VALUES (
    $1, $2, $3, $4, $5, $6, 'submitted'
)
ON CONFLICT (brief_id, creator_id) DO UPDATE SET
    pitch_note = EXCLUDED.pitch_note,
    estimated_delivery_days = EXCLUDED.estimated_delivery_days,
    proposed_quote = EXCLUDED.proposed_quote,
    sample_portfolio_item_id = EXCLUDED.sample_portfolio_item_id,
    status = 'submitted',
    updated_at = CURRENT_TIMESTAMP
RETURNING id, brief_id, creator_id, status, created_at;


-- ============================================================================
-- QUERY 16: Creator Inbox / Received Enquiries
-- Parameter:
--   $1: creator_user_id (UUID - auth.uid())
-- ============================================================================
SELECT 
    e.id AS enquiry_id,
    e.subject,
    e.message,
    e.proposed_budget,
    e.proposed_deadline,
    e.status,
    e.created_at,
    u.full_name AS customer_name,
    u.email AS customer_email,
    b.title AS related_brief_title
FROM public.enquiries e
LEFT JOIN public.users u ON e.customer_id = u.id
JOIN public.creators c ON e.creator_id = c.id
LEFT JOIN public.briefs b ON e.brief_id = b.id
WHERE c.user_id = $1
ORDER BY e.created_at DESC;
