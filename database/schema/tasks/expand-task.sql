-- Expand a specific task with all its details and subtasks
-- Parameters: task_id

WITH RECURSIVE task_subtree AS (
    -- Base case: the specified task
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
        t.dependencies,
        t.metadata,
        t.created_at,
        t.updated_at,
        t.completed_at,
        0 as level,
        ARRAY[t.id] as path
    FROM tasks t
    WHERE t.id = $1::UUID
    
    UNION ALL
    
    -- Recursive case: all subtasks
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
        t.dependencies,
        t.metadata,
        t.created_at,
        t.updated_at,
        t.completed_at,
        ts.level + 1,
        ts.path || t.id
    FROM tasks t
    INNER JOIN task_subtree ts ON t.parent_task_id = ts.id
),
task_details AS (
    SELECT 
        ts.*,
        u_assigned.name as assigned_to_name,
        u_assigned.email as assigned_to_email,
        u_created.name as created_by_name,
        u_created.email as created_by_email,
        c.name as codebase_name,
        -- Count direct subtasks
        (SELECT COUNT(*) FROM tasks st WHERE st.parent_task_id = ts.id) as direct_subtask_count,
        -- Get affected files
        COALESCE(
            (SELECT ARRAY_AGG(
                JSON_BUILD_OBJECT(
                    'file_path', cf.file_path,
                    'operation_type', tf.operation_type,
                    'changes_summary', tf.changes_summary
                )
            ) FROM task_files tf 
            JOIN codebase_files cf ON tf.file_id = cf.id 
            WHERE tf.task_id = ts.id), 
            ARRAY[]::JSON[]
        ) as affected_files,
        -- Calculate progress for parent tasks
        CASE 
            WHEN (SELECT COUNT(*) FROM tasks st WHERE st.parent_task_id = ts.id) = 0 THEN 
                CASE ts.status 
                    WHEN 'completed' THEN 100
                    WHEN 'in_progress' THEN 50
                    ELSE 0
                END
            ELSE 
                COALESCE(
                    (SELECT ROUND(
                        (COUNT(*) FILTER (WHERE status = 'completed') * 100.0) / COUNT(*)
                    ) FROM tasks st WHERE st.parent_task_id = ts.id), 0
                )
        END as progress_percentage
    FROM task_subtree ts
    LEFT JOIN users u_assigned ON ts.assigned_to = u_assigned.id
    LEFT JOIN users u_created ON ts.created_by = u_created.id
    LEFT JOIN codebases c ON ts.id = $1::UUID AND EXISTS(SELECT 1 FROM tasks t2 WHERE t2.id = ts.id AND t2.codebase_id = c.id)
),
dependency_info AS (
    SELECT 
        td.*,
        -- Get dependency tasks info
        COALESCE(
            (SELECT ARRAY_AGG(
                JSON_BUILD_OBJECT(
                    'id', dep_task.id,
                    'title', dep_task.title,
                    'status', dep_task.status
                )
            ) FROM tasks dep_task 
            WHERE dep_task.id = ANY(
                SELECT jsonb_array_elements_text(td.dependencies)::UUID
            )), 
            ARRAY[]::JSON[]
        ) as dependency_tasks,
        -- Get tasks that depend on this task
        COALESCE(
            (SELECT ARRAY_AGG(
                JSON_BUILD_OBJECT(
                    'id', dependent_task.id,
                    'title', dependent_task.title,
                    'status', dependent_task.status
                )
            ) FROM tasks dependent_task 
            WHERE td.id::TEXT = ANY(
                SELECT jsonb_array_elements_text(dependent_task.dependencies)
            )), 
            ARRAY[]::JSON[]
        ) as dependent_tasks
    FROM task_details td
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
    estimated_duration,
    actual_duration,
    assigned_to,
    assigned_to_name,
    assigned_to_email,
    created_by,
    created_by_name,
    created_by_email,
    codebase_name,
    level,
    direct_subtask_count,
    affected_files,
    dependency_tasks,
    dependent_tasks,
    progress_percentage,
    dependencies,
    metadata,
    created_at,
    updated_at,
    completed_at,
    -- Add indentation for hierarchical display
    REPEAT('  ', level) || title as indented_title,
    -- Calculate if task is blocked by dependencies
    CASE 
        WHEN JSONB_ARRAY_LENGTH(dependencies) = 0 THEN FALSE
        ELSE EXISTS(
            SELECT 1 FROM tasks dep_task 
            WHERE dep_task.id = ANY(
                SELECT jsonb_array_elements_text(dependencies)::UUID
            ) AND dep_task.status != 'completed'
        )
    END as is_blocked
FROM dependency_info
ORDER BY path;

