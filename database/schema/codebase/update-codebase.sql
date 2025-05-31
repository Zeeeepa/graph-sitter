-- Update an existing codebase
-- Parameters: codebase_id, name (optional), repository_url (optional), repository_path (optional),
--            language (optional), branch (optional), analysis_status (optional), metadata (optional)

WITH codebase_validation AS (
    SELECT 
        c.id,
        c.name as current_name,
        c.analysis_status as current_status,
        c.organization_id
    FROM codebases c
    WHERE c.id = $1::UUID
),
update_result AS (
    UPDATE codebases 
    SET 
        name = COALESCE($2::TEXT, name),
        repository_url = COALESCE($3::TEXT, repository_url),
        repository_path = COALESCE($4::TEXT, repository_path),
        language = COALESCE($5::TEXT, language),
        branch = COALESCE($6::TEXT, branch),
        analysis_status = COALESCE($7::TEXT, analysis_status),
        metadata = CASE 
            WHEN $8::JSONB IS NOT NULL THEN 
                COALESCE(metadata, '{}'::JSONB) || $8::JSONB
            ELSE metadata
        END,
        updated_at = NOW(),
        last_analyzed_at = CASE 
            WHEN $7::TEXT = 'completed' AND analysis_status != 'completed' THEN NOW()
            ELSE last_analyzed_at
        END
    WHERE id = $1::UUID
    RETURNING 
        id,
        name,
        repository_url,
        repository_path,
        language,
        branch,
        analysis_status,
        metadata,
        updated_at,
        last_analyzed_at
)
SELECT 
    cv.id,
    cv.current_name,
    cv.current_status,
    ur.id IS NOT NULL as update_successful,
    ur.name as new_name,
    ur.repository_url as new_repository_url,
    ur.repository_path as new_repository_path,
    ur.language as new_language,
    ur.branch as new_branch,
    ur.analysis_status as new_analysis_status,
    ur.metadata as new_metadata,
    ur.updated_at,
    ur.last_analyzed_at,
    -- Calculate what changed
    ARRAY_REMOVE(ARRAY[
        CASE WHEN $2::TEXT IS NOT NULL AND $2::TEXT != cv.current_name THEN 'name' END,
        CASE WHEN $3::TEXT IS NOT NULL THEN 'repository_url' END,
        CASE WHEN $4::TEXT IS NOT NULL THEN 'repository_path' END,
        CASE WHEN $5::TEXT IS NOT NULL THEN 'language' END,
        CASE WHEN $6::TEXT IS NOT NULL THEN 'branch' END,
        CASE WHEN $7::TEXT IS NOT NULL AND $7::TEXT != cv.current_status THEN 'analysis_status' END,
        CASE WHEN $8::JSONB IS NOT NULL THEN 'metadata' END
    ], NULL) as fields_changed,
    CASE 
        WHEN cv.id IS NULL THEN 'Codebase not found'
        WHEN ur.id IS NOT NULL THEN 'Codebase updated successfully'
        ELSE 'Failed to update codebase'
    END as result_message,
    -- Get file and symbol counts
    (SELECT COUNT(*) FROM codebase_files cf WHERE cf.codebase_id = cv.id AND cf.is_deleted = FALSE) as file_count,
    (SELECT COUNT(*) FROM code_symbols cs 
     JOIN codebase_files cf ON cs.file_id = cf.id 
     WHERE cf.codebase_id = cv.id AND cf.is_deleted = FALSE) as symbol_count
FROM codebase_validation cv
LEFT JOIN update_result ur ON cv.id = ur.id;

