-- Remove a codebase and all associated data
-- Parameters: codebase_id

WITH codebase_info AS (
    SELECT 
        c.id,
        c.name,
        c.organization_id,
        (SELECT COUNT(*) FROM codebase_files cf WHERE cf.codebase_id = c.id) as file_count,
        (SELECT COUNT(*) FROM code_symbols cs 
         JOIN codebase_files cf ON cs.file_id = cf.id 
         WHERE cf.codebase_id = c.id) as symbol_count,
        (SELECT COUNT(*) FROM tasks t WHERE t.codebase_id = c.id) as task_count,
        (SELECT COUNT(*) FROM analysis_runs ar WHERE ar.codebase_id = c.id) as analysis_run_count
    FROM codebases c
    WHERE c.id = $1::UUID
),
cleanup_stats AS (
    -- Clean up related data and collect statistics
    SELECT 
        ci.*,
        -- Delete analysis data
        (DELETE FROM code_metrics cm 
         WHERE cm.analysis_run_id IN (
             SELECT ar.id FROM analysis_runs ar WHERE ar.codebase_id = $1::UUID
         ) RETURNING cm.id) as deleted_metrics,
        (DELETE FROM dead_code_analysis dca 
         WHERE dca.analysis_run_id IN (
             SELECT ar.id FROM analysis_runs ar WHERE ar.codebase_id = $1::UUID
         ) RETURNING dca.id) as deleted_dead_code,
        (DELETE FROM dependency_analysis da 
         WHERE da.analysis_run_id IN (
             SELECT ar.id FROM analysis_runs ar WHERE ar.codebase_id = $1::UUID
         ) RETURNING da.id) as deleted_dependencies,
        (DELETE FROM impact_analysis ia 
         WHERE ia.analysis_run_id IN (
             SELECT ar.id FROM analysis_runs ar WHERE ar.codebase_id = $1::UUID
         ) RETURNING ia.id) as deleted_impacts,
        (DELETE FROM analysis_runs ar WHERE ar.codebase_id = $1::UUID RETURNING ar.id) as deleted_analysis_runs
    FROM codebase_info ci
),
task_cleanup AS (
    -- Update tasks to remove codebase reference (don't delete tasks)
    UPDATE tasks 
    SET 
        codebase_id = NULL,
        updated_at = NOW()
    WHERE codebase_id = $1::UUID
    RETURNING id
),
deletion_result AS (
    -- Delete the codebase (cascades to files and symbols)
    DELETE FROM codebases 
    WHERE id = $1::UUID
    RETURNING id, name
)
SELECT 
    ci.id,
    ci.name,
    ci.file_count,
    ci.symbol_count,
    ci.task_count,
    ci.analysis_run_count,
    dr.id IS NOT NULL as deletion_successful,
    COUNT(tc.id) as tasks_updated,
    CASE 
        WHEN ci.id IS NULL THEN 'Codebase not found'
        WHEN dr.id IS NOT NULL THEN 'Codebase and all associated data removed successfully'
        ELSE 'Failed to remove codebase'
    END as result_message,
    JSON_BUILD_OBJECT(
        'files_deleted', ci.file_count,
        'symbols_deleted', ci.symbol_count,
        'tasks_updated', COUNT(tc.id),
        'analysis_runs_deleted', ci.analysis_run_count
    ) as cleanup_summary
FROM codebase_info ci
LEFT JOIN deletion_result dr ON ci.id = dr.id
LEFT JOIN task_cleanup tc ON TRUE
GROUP BY ci.id, ci.name, ci.file_count, ci.symbol_count, ci.task_count, ci.analysis_run_count, dr.id;

