-- Update a subtask by ID
-- Parameters: subtask_id, title (optional), description (optional), status (optional), 
--            priority (optional), assigned_to (optional), complexity_score (optional)

WITH subtask_validation AS (
    SELECT 
        t.id,
        t.parent_task_id,
        t.title as current_title,
        t.status as current_status
    FROM tasks t
    WHERE t.id = $1::UUID
    AND t.parent_task_id IS NOT NULL  -- Ensure it's actually a subtask
),
update_result AS (
    UPDATE tasks 
    SET 
        title = COALESCE($2::TEXT, title),
        description = COALESCE($3::TEXT, description),
        status = COALESCE($4::TEXT, status),
        priority = COALESCE($5::INTEGER, priority),
        assigned_to = CASE 
            WHEN $6::UUID IS NOT NULL THEN $6::UUID
            WHEN $6::TEXT = 'NULL' THEN NULL  -- Allow explicit NULL assignment
            ELSE assigned_to
        END,
        complexity_score = COALESCE($7::INTEGER, complexity_score),
        updated_at = NOW(),
        completed_at = CASE 
            WHEN COALESCE($4::TEXT, status) = 'completed' AND status != 'completed' THEN NOW()
            WHEN COALESCE($4::TEXT, status) != 'completed' THEN NULL
            ELSE completed_at
        END
    WHERE id = $1::UUID
    AND parent_task_id IS NOT NULL  -- Safety check: only update subtasks
    RETURNING 
        id,
        parent_task_id,
        title,
        description,
        status,
        priority,
        assigned_to,
        complexity_score,
        updated_at,
        completed_at
)
SELECT 
    sv.id,
    sv.parent_task_id,
    sv.current_title,
    sv.current_status,
    ur.id IS NOT NULL as update_successful,
    ur.title as new_title,
    ur.status as new_status,
    ur.priority as new_priority,
    ur.assigned_to as new_assigned_to,
    ur.complexity_score as new_complexity_score,
    ur.updated_at,
    u.name as assigned_to_name,
    pt.title as parent_task_title,
    CASE 
        WHEN sv.id IS NULL THEN 'Task not found or is not a subtask'
        WHEN ur.id IS NOT NULL THEN 'Subtask updated successfully'
        ELSE 'Failed to update subtask'
    END as result_message
FROM subtask_validation sv
LEFT JOIN update_result ur ON sv.id = ur.id
LEFT JOIN users u ON ur.assigned_to = u.id
LEFT JOIN tasks pt ON ur.parent_task_id = pt.id;

