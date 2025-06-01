-- Expand all tasks with their subtasks in a hierarchical structure
-- Parameters: organization_id (optional), codebase_id (optional), status_filter (optional)

WITH RECURSIVE task_hierarchy AS (
    -- Base case: root tasks (no parent)
    SELECT 
        t.id,
        t.parent_task_id,
        t.title,
        t.description,
        t.task_type,
        t.status,
        t.priority,
        t.complexity_score,
        t.assigned_to,
        t.created_by,
        t.created_at,
        t.updated_at,
        t.completed_at,
        u_assigned.name as assigned_to_name,
        u_created.name as created_by_name,
        0 as level,
        ARRAY[t.id] as path,
        t.title as full_path
    FROM tasks t
    LEFT JOIN users u_assigned ON t.assigned_to = u_assigned.id
    LEFT JOIN users u_created ON t.created_by = u_created.id
    WHERE t.parent_task_id IS NULL
    AND ($1::UUID IS NULL OR t.organization_id = $1::UUID)
    AND ($2::UUID IS NULL OR t.codebase_id = $2::UUID)
    AND ($3::TEXT IS NULL OR t.status = $3::TEXT)
    
    UNION ALL
    
    -- Recursive case: subtasks
    SELECT 
        t.id,
        t.parent_task_id,
        t.title,
        t.description,
        t.task_type,
        t.status,
        t.priority,
        t.complexity_score,
        t.assigned_to,
        t.created_by,
        t.created_at,
        t.updated_at,
        t.completed_at,
        u_assigned.name as assigned_to_name,
        u_created.name as created_by_name,
        th.level + 1,
        th.path || t.id,
        th.full_path || ' > ' || t.title
    FROM tasks t
    LEFT JOIN users u_assigned ON t.assigned_to = u_assigned.id
    LEFT JOIN users u_created ON t.created_by = u_created.id
    INNER JOIN task_hierarchy th ON t.parent_task_id = th.id
    WHERE ($3::TEXT IS NULL OR t.status = $3::TEXT)
),
task_stats AS (
    SELECT 
        th.*,
        -- Count direct subtasks
        (SELECT COUNT(*) FROM tasks st WHERE st.parent_task_id = th.id) as direct_subtask_count,
        -- Count all descendant tasks
        (SELECT COUNT(*) FROM task_hierarchy th2 WHERE th.id = ANY(th2.path) AND th2.id != th.id) as total_subtask_count,
        -- Count affected files
        (SELECT COUNT(*) FROM task_files tf WHERE tf.task_id = th.id) as affected_files_count,
        -- Calculate completion percentage for parent tasks
        CASE 
            WHEN (SELECT COUNT(*) FROM tasks st WHERE st.parent_task_id = th.id) = 0 THEN 
                CASE th.status 
                    WHEN 'completed' THEN 100
                    WHEN 'in_progress' THEN 50
                    ELSE 0
                END
            ELSE 
                COALESCE(
                    (SELECT ROUND(
                        (COUNT(*) FILTER (WHERE status = 'completed') * 100.0) / COUNT(*)
                    ) FROM tasks st WHERE st.parent_task_id = th.id), 0
                )
        END as completion_percentage
    FROM task_hierarchy th
)
SELECT 
    id,
    parent_task_id,
    title,
    description,
    task_type,
    status,
    priority,
    complexity_score,
    assigned_to,
    assigned_to_name,
    created_by,
    created_by_name,
    level,
    full_path,
    direct_subtask_count,
    total_subtask_count,
    affected_files_count,
    completion_percentage,
    created_at,
    updated_at,
    completed_at,
    -- Add indentation for display
    REPEAT('  ', level) || title as indented_title
FROM task_stats
ORDER BY path;

