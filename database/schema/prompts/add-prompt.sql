-- Add a new prompt to the system
-- Parameters: organization_id, title, description (optional), content, prompt_type, 
--            category (optional), tags (optional), created_by, metadata (optional)

WITH prompt_insertion AS (
    INSERT INTO prompts (
        organization_id,
        title,
        description,
        content,
        prompt_type,
        category,
        tags,
        created_by,
        metadata
    ) VALUES (
        $1::UUID,  -- organization_id
        $2::TEXT,  -- title
        $3::TEXT,  -- description (can be NULL)
        $4::TEXT,  -- content
        $5::TEXT,  -- prompt_type
        $6::TEXT,  -- category (can be NULL)
        COALESCE($7::TEXT[], ARRAY[]::TEXT[]),  -- tags (default empty array)
        $8::UUID,  -- created_by
        COALESCE($9::JSONB, '{}'::JSONB)  -- metadata (default empty object)
    )
    RETURNING 
        id,
        title,
        description,
        prompt_type,
        category,
        tags,
        version,
        is_active,
        created_at
),
version_creation AS (
    INSERT INTO prompt_versions (
        prompt_id,
        version,
        content,
        changes_summary,
        created_by
    )
    SELECT 
        pi.id,
        1,  -- Initial version
        $4::TEXT,  -- content
        'Initial version',
        $8::UUID  -- created_by
    FROM prompt_insertion pi
    RETURNING prompt_id, version
)
SELECT 
    pi.id,
    pi.title,
    pi.description,
    pi.prompt_type,
    pi.category,
    pi.tags,
    pi.version,
    pi.is_active,
    pi.created_at,
    vc.version as version_created,
    u.name as created_by_name,
    LENGTH($4::TEXT) as content_length,
    ARRAY_LENGTH(COALESCE($7::TEXT[], ARRAY[]::TEXT[]), 1) as tag_count,
    'Prompt created successfully' as result_message
FROM prompt_insertion pi
LEFT JOIN version_creation vc ON pi.id = vc.prompt_id
LEFT JOIN users u ON $8::UUID = u.id;

