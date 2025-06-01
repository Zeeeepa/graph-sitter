-- List tasks with filtering and pagination
-- Parameters: organization_id, status_filter (optional), assigned_to (optional), codebase_id (optional), 
--            task_type (optional), limit (optional), offset (optional)

WITH filtered_tasks AS (
    SELECT 
        t.id,
        t.parent_task_id,
        t.title,
        t.description,
        t.task_type,
        t.status,
        t.priority,
        t.complexity_score,
        t.estimated_duration,
        t.actual_duration,
        t.assigned_to,
        t.created_by,
        t.codebase_id,
        t.created_at,
        t.updated_at,
        t.completed_at,
        u_assigned.name as assigned_to_name,
        u_assigned.email as assigned_to_email,
        u_created.name as created_by_name,
        c.name as codebase_name,
        -- Count subtasks
        (SELECT COUNT(*) FROM tasks st WHERE st.parent_task_id = t.id) as subtask_count,
        -- Count affected files
        (SELECT COUNT(*) FROM task_files tf WHERE tf.task_id = t.id) as affected_files_count,
        -- Check if dependencies are met
        CASE 
            WHEN JSONB_ARRAY_LENGTH(COALESCE(t.dependencies, '[]'::JSONB)) = 0 THEN TRUE
            ELSE NOT EXISTS(
                SELECT 1 FROM tasks dep_task 
                WHERE dep_task.id = ANY(
                    SELECT jsonb_array_elements_text(t.dependencies)::UUID
                ) AND dep_task.status != 'completed'
            )
        END as dependencies_met,
        -- Calculate progress for parent tasks
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
        END as progress_percentage
    FROM tasks t
    LEFT JOIN users u_assigned ON t.assigned_to = u_assigned.id
    LEFT JOIN users u_created ON t.created_by = u_created.id
    LEFT JOIN codebases c ON t.codebase_id = c.id
    WHERE t.organization_id = $1::UUID
    AND ($2::TEXT IS NULL OR t.status = $2::TEXT)
    AND ($3::UUID IS NULL OR t.assigned_to = $3::UUID)
    AND ($4::UUID IS NULL OR t.codebase_id = $4::UUID)
    AND ($5::TEXT IS NULL OR t.task_type = $5::TEXT)
),
task_summary AS (
    SELECT 
        COUNT(*) as total_count,
        COUNT(*) FILTER (WHERE status = 'pending') as pending_count,
        COUNT(*) FILTER (WHERE status = 'in_progress') as in_progress_count,
        COUNT(*) FILTER (WHERE status = 'completed') as completed_count,
        COUNT(*) FILTER (WHERE status = 'failed') as failed_count,
        COUNT(*) FILTER (WHERE status = 'cancelled') as cancelled_count,
        COUNT(*) FILTER (WHERE dependencies_met = FALSE) as blocked_count,
        AVG(complexity_score) as avg_complexity,
        AVG(progress_percentage) as avg_progress
    FROM filtered_tasks
)
SELECT 
    -- Task details
    ft.id,
    ft.parent_task_id,
    ft.title,
    ft.description,
    ft.task_type,
    ft.status,
    ft.priority,
    ft.complexity_score,
    ft.estimated_duration,
    ft.actual_duration,
    ft.assigned_to,
    ft.assigned_to_name,
    ft.assigned_to_email,
    ft.created_by,
    ft.created_by_name,
    ft.codebase_id,
    ft.codebase_name,
    ft.subtask_count,
    ft.affected_files_count,
    ft.dependencies_met,
    ft.progress_percentage,
    ft.created_at,
    ft.updated_at,
    ft.completed_at,
    -- Summary statistics (same for all rows)
    ts.total_count,
    ts.pending_count,
    ts.in_progress_count,
    ts.completed_count,
    ts.failed_count,
    ts.cancelled_count,
    ts.blocked_count,
    ROUND(ts.avg_complexity, 1) as avg_complexity,
    ROUND(ts.avg_progress, 1) as avg_progress,
    -- Status indicators
    CASE 
        WHEN ft.status = 'completed' THEN '✅'
        WHEN ft.status = 'in_progress' THEN '🔄'
        WHEN ft.status = 'failed' THEN '❌'
        WHEN ft.status = 'cancelled' THEN '🚫'
        WHEN ft.dependencies_met = FALSE THEN '🔒'
        ELSE '⏳'
    END as status_icon,
    -- Priority indicator
    CASE 
        WHEN ft.priority >= 8 THEN '🔴 High'
        WHEN ft.priority >= 5 THEN '🟡 Medium'
        ELSE '🟢 Low'
    END as priority_label
FROM filtered_tasks ft
CROSS JOIN task_summary ts
ORDER BY 
    ft.priority DESC,
    ft.created_at ASC
LIMIT COALESCE($6::INTEGER, 50)
OFFSET COALESCE($7::INTEGER, 0);

