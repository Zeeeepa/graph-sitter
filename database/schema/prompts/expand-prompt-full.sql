-- Get full prompt details including content and version history
-- Parameters: prompt_id

WITH prompt_details AS (
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
        p.metadata,
        u_created.name as created_by_name,
        u_created.email as created_by_email,
        o.name as organization_name
    FROM prompts p
    LEFT JOIN users u_created ON p.created_by = u_created.id
    LEFT JOIN organizations o ON p.organization_id = o.id
    WHERE p.id = $1::UUID
),
current_content AS (
    SELECT 
        pv.content,
        pv.created_at as content_created_at,
        u.name as content_created_by_name
    FROM prompt_versions pv
    LEFT JOIN users u ON pv.created_by = u.id
    WHERE pv.prompt_id = $1::UUID
    AND pv.version = (
        SELECT MAX(version) FROM prompt_versions WHERE prompt_id = $1::UUID
    )
),
version_history AS (
    SELECT 
        ARRAY_AGG(
            JSON_BUILD_OBJECT(
                'version', pv.version,
                'changes_summary', pv.changes_summary,
                'created_by', u.name,
                'created_at', pv.created_at,
                'content_length', LENGTH(pv.content)
            ) ORDER BY pv.version DESC
        ) as versions
    FROM prompt_versions pv
    LEFT JOIN users u ON pv.created_by = u.id
    WHERE pv.prompt_id = $1::UUID
),
usage_stats AS (
    SELECT 
        -- Calculate usage statistics (this would be enhanced with actual usage tracking)
        pd.usage_count,
        CASE 
            WHEN pd.usage_count = 0 THEN 'Never used'
            WHEN pd.usage_count < 5 THEN 'Rarely used'
            WHEN pd.usage_count < 20 THEN 'Occasionally used'
            WHEN pd.usage_count < 50 THEN 'Frequently used'
            ELSE 'Heavily used'
        END as usage_category,
        -- Calculate age
        EXTRACT(EPOCH FROM (NOW() - pd.created_at)) / 86400 as age_days,
        -- Calculate last update age
        EXTRACT(EPOCH FROM (NOW() - pd.updated_at)) / 86400 as last_update_days
    FROM prompt_details pd
),
related_prompts AS (
    SELECT 
        ARRAY_AGG(
            JSON_BUILD_OBJECT(
                'id', rp.id,
                'title', rp.title,
                'prompt_type', rp.prompt_type,
                'similarity_reason', 
                CASE 
                    WHEN rp.category = pd.category THEN 'Same category'
                    WHEN rp.prompt_type = pd.prompt_type THEN 'Same type'
                    WHEN rp.tags && pd.tags THEN 'Shared tags'
                    ELSE 'Related'
                END
            ) ORDER BY rp.usage_count DESC
        ) FILTER (WHERE rp.id IS NOT NULL) as related
    FROM prompt_details pd
    LEFT JOIN prompts rp ON (
        rp.organization_id = (SELECT organization_id FROM prompts WHERE id = $1::UUID)
        AND rp.id != pd.id
        AND rp.is_active = TRUE
        AND (
            rp.category = pd.category OR
            rp.prompt_type = pd.prompt_type OR
            rp.tags && pd.tags
        )
    )
    LIMIT 5
)
SELECT 
    -- Basic prompt information
    pd.id,
    pd.title,
    pd.description,
    pd.prompt_type,
    pd.category,
    pd.tags,
    pd.version,
    pd.is_active,
    pd.usage_count,
    pd.metadata,
    pd.created_by_name,
    pd.created_by_email,
    pd.organization_name,
    pd.created_at,
    pd.updated_at,
    
    -- Current content
    cc.content,
    LENGTH(cc.content) as content_length,
    cc.content_created_at,
    cc.content_created_by_name,
    
    -- Version information
    vh.versions,
    COALESCE(ARRAY_LENGTH(vh.versions, 1), 0) as version_count,
    
    -- Usage statistics
    us.usage_category,
    us.age_days,
    us.last_update_days,
    
    -- Related prompts
    rp.related as related_prompts,
    
    -- Content analysis
    ARRAY_LENGTH(STRING_TO_ARRAY(cc.content, E'\n'), 1) as line_count,
    ARRAY_LENGTH(STRING_TO_ARRAY(cc.content, ' '), 1) as word_count,
    
    -- Status indicators
    CASE 
        WHEN pd.is_active THEN '✅ Active'
        ELSE '❌ Inactive'
    END as status_label,
    
    CASE 
        WHEN us.age_days < 7 THEN '🆕 New'
        WHEN us.last_update_days < 7 THEN '🔄 Recently Updated'
        WHEN us.last_update_days > 90 THEN '⏰ Stale'
        ELSE '📝 Current'
    END as freshness_label,
    
    -- Existence confirmation
    pd.id IS NOT NULL as exists
    
FROM prompt_details pd
LEFT JOIN current_content cc ON TRUE
LEFT JOIN version_history vh ON TRUE
LEFT JOIN usage_stats us ON TRUE
LEFT JOIN related_prompts rp ON TRUE

UNION ALL

-- Return a row indicating non-existence if prompt not found
SELECT 
    $1::UUID as id,
    NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    FALSE as exists
WHERE NOT EXISTS(SELECT 1 FROM prompts WHERE id = $1::UUID);

