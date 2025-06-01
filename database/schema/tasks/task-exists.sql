-- Check if a task exists and return basic information
-- Parameters: task_id

SELECT 
    t.id,
    t.title,
    t.description,
    t.task_type,
    t.status,
    t.priority,
    t.complexity_score,
    t.parent_task_id,
    t.organization_id,
    t.codebase_id,
    t.assigned_to,
    t.created_by,
    t.created_at,
    t.updated_at,
    t.completed_at,
    -- Additional computed fields
    u_assigned.name as assigned_to_name,
    u_created.name as created_by_name,
    c.name as codebase_name,
    o.name as organization_name,
    pt.title as parent_task_title,
    -- Task metrics
    (SELECT COUNT(*) FROM tasks st WHERE st.parent_task_id = t.id) as subtask_count,
    (SELECT COUNT(*) FROM task_files tf WHERE tf.task_id = t.id) as affected_files_count,
    JSONB_ARRAY_LENGTH(COALESCE(t.dependencies, '[]'::JSONB)) as dependency_count,
    -- Status checks
    CASE 
        WHEN JSONB_ARRAY_LENGTH(COALESCE(t.dependencies, '[]'::JSONB)) = 0 THEN TRUE
        ELSE NOT EXISTS(
            SELECT 1 FROM tasks dep_task 
            WHERE dep_task.id = ANY(
                SELECT jsonb_array_elements_text(t.dependencies)::UUID
            ) AND dep_task.status != 'completed'
        )
    END as dependencies_met,
    -- Age calculation
    EXTRACT(EPOCH FROM (NOW() - t.created_at)) / 86400 as age_days,
    -- Duration information
    CASE 
        WHEN t.status = 'completed' AND t.completed_at IS NOT NULL THEN
            t.completed_at - t.created_at
        WHEN t.status IN ('in_progress', 'pending') THEN
            NOW() - t.created_at
        ELSE NULL
    END as current_duration,
    -- Progress calculation for parent tasks
    CASE 
        WHEN (SELECT COUNT(*) FROM tasks st WHERE st.parent_task_id = t.id) = 0 THEN 
            CASE t.status 
                WHEN 'completed' THEN 100
                WHEN 'in_progress' THEN 50
                ELSE 0
            END
        ELSE 
            COALESCE(
                (SELECT ROUND(
                    (COUNT(*) FILTER (WHERE status = 'completed') * 100.0) / COUNT(*)
                ) FROM tasks st WHERE st.parent_task_id = t.id), 0
            )
    END as progress_percentage,
    -- Existence confirmation
    TRUE as exists
FROM tasks t
LEFT JOIN users u_assigned ON t.assigned_to = u_assigned.id
LEFT JOIN users u_created ON t.created_by = u_created.id
LEFT JOIN codebases c ON t.codebase_id = c.id
LEFT JOIN organizations o ON t.organization_id = o.id
LEFT JOIN tasks pt ON t.parent_task_id = pt.id
WHERE t.id = $1::UUID

UNION ALL

-- Return a row indicating non-existence if task not found
SELECT 
    $1::UUID as id,
    NULL as title,
    NULL as description,
    NULL as task_type,
    NULL as status,
    NULL as priority,
    NULL as complexity_score,
    NULL as parent_task_id,
    NULL as organization_id,
    NULL as codebase_id,
    NULL as assigned_to,
    NULL as created_by,
    NULL as created_at,
    NULL as updated_at,
    NULL as completed_at,
    NULL as assigned_to_name,
    NULL as created_by_name,
    NULL as codebase_name,
    NULL as organization_name,
    NULL as parent_task_title,
    NULL as subtask_count,
    NULL as affected_files_count,
    NULL as dependency_count,
    NULL as dependencies_met,
    NULL as age_days,
    NULL as current_duration,
    NULL as progress_percentage,
    FALSE as exists
WHERE NOT EXISTS(SELECT 1 FROM tasks WHERE id = $1::UUID);

