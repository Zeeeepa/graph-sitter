-- Sync and track changes in an active codebase for incremental analysis
-- Parameters: codebase_id, file_changes (JSONB array of file change objects)

WITH codebase_validation AS (
    SELECT 
        c.id,
        c.name,
        c.last_analyzed_at,
        c.analysis_status
    FROM codebases c
    WHERE c.id = $1::UUID
),
change_processing AS (
    SELECT 
        cv.*,
        change_data.value as file_change,
        (change_data.value->>'file_path')::TEXT as file_path,
        (change_data.value->>'operation')::TEXT as operation,  -- 'create', 'modify', 'delete', 'move'
        (change_data.value->>'content_hash')::TEXT as new_content_hash,
        (change_data.value->>'file_size')::BIGINT as new_file_size,
        (change_data.value->>'last_modified')::TIMESTAMP WITH TIME ZONE as new_last_modified
    FROM codebase_validation cv
    CROSS JOIN JSONB_ARRAY_ELEMENTS(COALESCE($2::JSONB, '[]'::JSONB)) as change_data
),
file_updates AS (
    -- Handle file creates and updates
    INSERT INTO codebase_files (
        codebase_id,
        file_path,
        file_name,
        file_extension,
        file_size,
        content_hash,
        last_modified,
        is_deleted,
        metadata
    )
    SELECT 
        cp.id,
        cp.file_path,
        SPLIT_PART(cp.file_path, '/', -1) as file_name,
        CASE 
            WHEN cp.file_path ~ '\.' THEN 
                '.' || SPLIT_PART(cp.file_path, '.', -1)
            ELSE NULL
        END as file_extension,
        cp.new_file_size,
        cp.new_content_hash,
        cp.new_last_modified,
        FALSE,
        JSON_BUILD_OBJECT(
            'sync_operation', cp.operation,
            'sync_timestamp', NOW()
        )
    FROM change_processing cp
    WHERE cp.operation IN ('create', 'modify')
    ON CONFLICT (codebase_id, file_path) 
    DO UPDATE SET
        file_size = EXCLUDED.file_size,
        content_hash = EXCLUDED.content_hash,
        last_modified = EXCLUDED.last_modified,
        is_deleted = FALSE,
        metadata = COALESCE(codebase_files.metadata, '{}'::JSONB) || EXCLUDED.metadata,
        updated_at = NOW()
    RETURNING id, file_path, 'updated' as action
),
file_deletions AS (
    -- Handle file deletions
    UPDATE codebase_files 
    SET 
        is_deleted = TRUE,
        updated_at = NOW(),
        metadata = COALESCE(metadata, '{}'::JSONB) || JSON_BUILD_OBJECT(
            'deleted_at', NOW(),
            'sync_operation', 'delete'
        )
    FROM change_processing cp
    WHERE codebase_files.codebase_id = cp.id
    AND codebase_files.file_path = cp.file_path
    AND cp.operation = 'delete'
    RETURNING id, file_path, 'deleted' as action
),
symbol_cleanup AS (
    -- Mark symbols in deleted files as stale
    UPDATE code_symbols 
    SET 
        metadata = COALESCE(metadata, '{}'::JSONB) || JSON_BUILD_OBJECT(
            'stale', TRUE,
            'stale_reason', 'file_deleted',
            'stale_timestamp', NOW()
        ),
        updated_at = NOW()
    FROM file_deletions fd
    WHERE code_symbols.file_id = fd.id
    RETURNING code_symbols.id, 'marked_stale' as action
),
dependency_cleanup AS (
    -- Mark dependencies involving deleted symbols as stale
    UPDATE symbol_dependencies 
    SET 
        metadata = COALESCE(metadata, '{}'::JSONB) || JSON_BUILD_OBJECT(
            'stale', TRUE,
            'stale_reason', 'symbol_deleted',
            'stale_timestamp', NOW()
        )
    FROM symbol_cleanup sc
    WHERE symbol_dependencies.source_symbol_id = sc.id
    OR symbol_dependencies.target_symbol_id = sc.id
    RETURNING symbol_dependencies.id, 'marked_stale' as action
),
incremental_analysis AS (
    -- Create an incremental analysis run for the changes
    INSERT INTO analysis_runs (
        codebase_id,
        analysis_type,
        status,
        started_at,
        metadata
    )
    SELECT 
        cv.id,
        'incremental',
        'completed',
        NOW(),
        JSON_BUILD_OBJECT(
            'trigger', 'sync_changes',
            'changes_processed', JSONB_ARRAY_LENGTH(COALESCE($2::JSONB, '[]'::JSONB)),
            'files_updated', (SELECT COUNT(*) FROM file_updates),
            'files_deleted', (SELECT COUNT(*) FROM file_deletions),
            'symbols_marked_stale', (SELECT COUNT(*) FROM symbol_cleanup)
        )
    FROM codebase_validation cv
    WHERE EXISTS(SELECT 1 FROM change_processing)
    RETURNING id, analysis_type, metadata
),
codebase_status_update AS (
    -- Update codebase analysis status
    UPDATE codebases 
    SET 
        last_analyzed_at = NOW(),
        analysis_status = CASE 
            WHEN EXISTS(SELECT 1 FROM file_deletions) OR 
                 EXISTS(SELECT 1 FROM file_updates WHERE action = 'updated') THEN 'needs_analysis'
            ELSE analysis_status
        END,
        updated_at = NOW()
    WHERE id = $1::UUID
    RETURNING id, analysis_status, last_analyzed_at
),
change_summary AS (
    SELECT 
        COUNT(*) FILTER (WHERE cp.operation = 'create') as files_created,
        COUNT(*) FILTER (WHERE cp.operation = 'modify') as files_modified,
        COUNT(*) FILTER (WHERE cp.operation = 'delete') as files_deleted,
        COUNT(*) FILTER (WHERE cp.operation = 'move') as files_moved,
        COUNT(*) as total_changes
    FROM change_processing cp
)
SELECT 
    cv.id as codebase_id,
    cv.name as codebase_name,
    cv.last_analyzed_at as previous_analysis,
    csu.last_analyzed_at as current_analysis,
    csu.analysis_status,
    
    -- Change statistics
    cs.files_created,
    cs.files_modified,
    cs.files_deleted,
    cs.files_moved,
    cs.total_changes,
    
    -- Processing results
    COALESCE((SELECT COUNT(*) FROM file_updates), 0) as files_updated_in_db,
    COALESCE((SELECT COUNT(*) FROM file_deletions), 0) as files_deleted_in_db,
    COALESCE((SELECT COUNT(*) FROM symbol_cleanup), 0) as symbols_marked_stale,
    COALESCE((SELECT COUNT(*) FROM dependency_cleanup), 0) as dependencies_marked_stale,
    
    -- Analysis run info
    ia.id as analysis_run_id,
    ia.analysis_type,
    ia.metadata as analysis_metadata,
    
    -- File change details
    COALESCE(
        (SELECT ARRAY_AGG(
            JSON_BUILD_OBJECT(
                'file_path', fu.file_path,
                'action', fu.action
            )
        ) FROM file_updates fu), 
        ARRAY[]::JSON[]
    ) as updated_files,
    
    COALESCE(
        (SELECT ARRAY_AGG(
            JSON_BUILD_OBJECT(
                'file_path', fd.file_path,
                'action', fd.action
            )
        ) FROM file_deletions fd), 
        ARRAY[]::JSON[]
    ) as deleted_files,
    
    -- Status and recommendations
    CASE 
        WHEN cv.id IS NULL THEN 'Codebase not found'
        WHEN cs.total_changes = 0 THEN 'No changes to process'
        WHEN cs.total_changes > 0 THEN 'Changes synchronized successfully'
        ELSE 'Sync completed with warnings'
    END as result_message,
    
    CASE 
        WHEN cs.files_deleted > 0 OR cs.files_modified > 10 THEN 'Full analysis recommended'
        WHEN cs.files_modified > 0 THEN 'Incremental analysis recommended'
        ELSE 'No further analysis needed'
    END as recommendation,
    
    -- Sync metadata
    NOW() as sync_timestamp,
    EXTRACT(EPOCH FROM (NOW() - cv.last_analyzed_at)) / 3600 as hours_since_last_analysis
    
FROM codebase_validation cv
LEFT JOIN codebase_status_update csu ON cv.id = csu.id
LEFT JOIN incremental_analysis ia ON cv.id = ia.codebase_id
CROSS JOIN change_summary cs;

