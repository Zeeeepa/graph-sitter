-- Update an existing prompt and create a new version if content changes
-- Parameters: prompt_id, title (optional), description (optional), content (optional), 
--            prompt_type (optional), category (optional), tags (optional), 
--            is_active (optional), updated_by, changes_summary (optional)

WITH prompt_validation AS (
    SELECT 
        p.id,
        p.title as current_title,
        p.content as current_content,
        p.version as current_version,
        p.organization_id
    FROM prompts p
    WHERE p.id = $1::UUID
),
content_changed AS (
    SELECT 
        pv.*,
        CASE 
            WHEN $3::TEXT IS NOT NULL AND $3::TEXT != pv.current_content THEN TRUE
            ELSE FALSE
        END as content_updated
    FROM prompt_validation pv
),
new_version_creation AS (
    INSERT INTO prompt_versions (
        prompt_id,
        version,
        content,
        changes_summary,
        created_by
    )
    SELECT 
        cc.id,
        cc.current_version + 1,
        $3::TEXT,
        COALESCE($10::TEXT, 'Content updated'),
        $9::UUID
    FROM content_changed cc
    WHERE cc.content_updated = TRUE
    RETURNING prompt_id, version, created_at
),
prompt_update AS (
    UPDATE prompts 
    SET 
        title = COALESCE($2::TEXT, title),
        description = COALESCE($3::TEXT, description),
        prompt_type = COALESCE($5::TEXT, prompt_type),
        category = COALESCE($6::TEXT, category),
        tags = COALESCE($7::TEXT[], tags),
        is_active = COALESCE($8::BOOLEAN, is_active),
        version = CASE 
            WHEN cc.content_updated THEN current_version + 1
            ELSE version
        END,
        usage_count = CASE 
            WHEN $8::BOOLEAN = TRUE AND is_active = FALSE THEN usage_count + 1
            ELSE usage_count
        END,
        updated_at = NOW()
    FROM content_changed cc
    WHERE prompts.id = $1::UUID
    AND cc.id = prompts.id
    RETURNING 
        id,
        title,
        description,
        prompt_type,
        category,
        tags,
        version,
        is_active,
        usage_count,
        updated_at
)
SELECT 
    pv.id,
    pv.current_title,
    pv.current_version,
    cc.content_updated,
    pu.id IS NOT NULL as update_successful,
    pu.title as new_title,
    pu.prompt_type as new_prompt_type,
    pu.category as new_category,
    pu.tags as new_tags,
    pu.version as new_version,
    pu.is_active as new_is_active,
    pu.usage_count as new_usage_count,
    pu.updated_at,
    nvc.version as version_created,
    nvc.created_at as version_created_at,
    u.name as updated_by_name,
    -- Calculate what changed
    ARRAY_REMOVE(ARRAY[
        CASE WHEN $2::TEXT IS NOT NULL AND $2::TEXT != pv.current_title THEN 'title' END,
        CASE WHEN $3::TEXT IS NOT NULL THEN 'description' END,
        CASE WHEN cc.content_updated THEN 'content' END,
        CASE WHEN $5::TEXT IS NOT NULL THEN 'prompt_type' END,
        CASE WHEN $6::TEXT IS NOT NULL THEN 'category' END,
        CASE WHEN $7::TEXT[] IS NOT NULL THEN 'tags' END,
        CASE WHEN $8::BOOLEAN IS NOT NULL THEN 'is_active' END
    ], NULL) as fields_changed,
    CASE 
        WHEN pv.id IS NULL THEN 'Prompt not found'
        WHEN pu.id IS NOT NULL AND cc.content_updated THEN 'Prompt updated successfully with new version created'
        WHEN pu.id IS NOT NULL THEN 'Prompt updated successfully'
        ELSE 'Failed to update prompt'
    END as result_message
FROM prompt_validation pv
LEFT JOIN content_changed cc ON pv.id = cc.id
LEFT JOIN prompt_update pu ON pv.id = pu.id
LEFT JOIN new_version_creation nvc ON pv.id = nvc.prompt_id
LEFT JOIN users u ON $9::UUID = u.id;

