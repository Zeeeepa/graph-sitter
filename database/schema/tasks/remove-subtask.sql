-- Remove a specific subtask
-- Parameters: subtask_id

WITH subtask_info AS (
    SELECT 
        t.id,
        t.parent_task_id,
        t.title,
        t.status,
        pt.title as parent_title
    FROM tasks t
    LEFT JOIN tasks pt ON t.parent_task_id = pt.id
    WHERE t.id = $1::UUID
    AND t.parent_task_id IS NOT NULL  -- Ensure it's actually a subtask
),
deletion_result AS (
    DELETE FROM tasks 
    WHERE id = $1::UUID
    AND parent_task_id IS NOT NULL  -- Safety check: only delete subtasks
    RETURNING id, title, status
)
SELECT 
    si.id,
    si.title,
    si.status,
    si.parent_task_id,
    si.parent_title,
    dr.id IS NOT NULL as deletion_successful,
    CASE 
        WHEN si.id IS NULL THEN 'Task not found or is not a subtask'
        WHEN dr.id IS NOT NULL THEN 'Subtask removed successfully'
        ELSE 'Failed to remove subtask'
    END as result_message
FROM subtask_info si
LEFT JOIN deletion_result dr ON si.id = dr.id;

