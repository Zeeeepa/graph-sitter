-- List prompt titles with filtering and search capabilities
-- Parameters: organization_id, prompt_type (optional), category (optional), 
--            is_active (optional), search_term (optional), limit (optional), offset (optional)

WITH filtered_prompts AS (
    SELECT 
        p.id,
        p.title,
        p.description,
        p.prompt_type,
        p.category,
        p.tags,
        p.version,
        p.is_active,
        p.usage_count,
        p.created_at,
        p.updated_at,
        u.name as created_by_name,
        -- Calculate content length from latest version
        COALESCE(
            (SELECT LENGTH(pv.content) 
             FROM prompt_versions pv 
             WHERE pv.prompt_id = p.id 
             ORDER BY pv.version DESC 
             LIMIT 1), 0
        ) as content_length,
        -- Search relevance score
        CASE 
            WHEN $5::TEXT IS NULL THEN 1
            ELSE (
                CASE WHEN p.title ILIKE '%' || $5::TEXT || '%' THEN 10 ELSE 0 END +
                CASE WHEN p.description ILIKE '%' || $5::TEXT || '%' THEN 5 ELSE 0 END +
                CASE WHEN p.category ILIKE '%' || $5::TEXT || '%' THEN 3 ELSE 0 END +
                CASE WHEN $5::TEXT = ANY(p.tags) THEN 8 ELSE 0 END +
                CASE WHEN EXISTS(
                    SELECT 1 FROM prompt_versions pv 
                    WHERE pv.prompt_id = p.id 
                    AND pv.content ILIKE '%' || $5::TEXT || '%'
                ) THEN 2 ELSE 0 END
            )
        END as relevance_score
    FROM prompts p
    LEFT JOIN users u ON p.created_by = u.id
    WHERE p.organization_id = $1::UUID
    AND ($2::TEXT IS NULL OR p.prompt_type = $2::TEXT)
    AND ($3::TEXT IS NULL OR p.category = $3::TEXT)
    AND ($4::BOOLEAN IS NULL OR p.is_active = $4::BOOLEAN)
    AND ($5::TEXT IS NULL OR (
        p.title ILIKE '%' || $5::TEXT || '%' OR
        p.description ILIKE '%' || $5::TEXT || '%' OR
        p.category ILIKE '%' || $5::TEXT || '%' OR
        $5::TEXT = ANY(p.tags) OR
        EXISTS(
            SELECT 1 FROM prompt_versions pv 
            WHERE pv.prompt_id = p.id 
            AND pv.content ILIKE '%' || $5::TEXT || '%'
        )
    ))
),
prompt_summary AS (
    SELECT 
        COUNT(*) as total_count,
        COUNT(*) FILTER (WHERE is_active = TRUE) as active_count,
        COUNT(*) FILTER (WHERE is_active = FALSE) as inactive_count,
        COUNT(DISTINCT prompt_type) as type_count,
        COUNT(DISTINCT category) as category_count,
        AVG(usage_count) as avg_usage_count,
        SUM(usage_count) as total_usage_count
    FROM filtered_prompts
)
SELECT 
    -- Prompt details
    fp.id,
    fp.title,
    fp.description,
    fp.prompt_type,
    fp.category,
    fp.tags,
    fp.version,
    fp.is_active,
    fp.usage_count,
    fp.content_length,
    fp.created_by_name,
    fp.created_at,
    fp.updated_at,
    fp.relevance_score,
    -- Summary statistics (same for all rows)
    ps.total_count,
    ps.active_count,
    ps.inactive_count,
    ps.type_count,
    ps.category_count,
    ROUND(ps.avg_usage_count, 1) as avg_usage_count,
    ps.total_usage_count,
    -- Status indicators
    CASE 
        WHEN fp.is_active THEN '✅ Active'
        ELSE '❌ Inactive'
    END as status_label,
    -- Usage indicator
    CASE 
        WHEN fp.usage_count = 0 THEN '🆕 New'
        WHEN fp.usage_count >= ps.avg_usage_count THEN '🔥 Popular'
        ELSE '📝 Used'
    END as usage_label,
    -- Content size indicator
    CASE 
        WHEN fp.content_length < 100 THEN '📄 Short'
        WHEN fp.content_length < 500 THEN '📃 Medium'
        WHEN fp.content_length < 2000 THEN '📋 Long'
        ELSE '📚 Very Long'
    END as size_label
FROM filtered_prompts fp
CROSS JOIN prompt_summary ps
WHERE ($5::TEXT IS NULL OR fp.relevance_score > 0)
ORDER BY 
    CASE WHEN $5::TEXT IS NOT NULL THEN fp.relevance_score END DESC,
    fp.usage_count DESC,
    fp.updated_at DESC
LIMIT COALESCE($6::INTEGER, 50)
OFFSET COALESCE($7::INTEGER, 0);

