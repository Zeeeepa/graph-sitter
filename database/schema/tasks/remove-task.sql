-- Remove a task and optionally handle its subtasks
-- Parameters: task_id, handle_subtasks ('delete', 'promote', 'reassign')

WITH task_info AS (
    SELECT 
        t.id,
        t.title,
        t.status,
        t.parent_task_id,
        (SELECT COUNT(*) FROM tasks st WHERE st.parent_task_id = t.id) as subtask_count
    FROM tasks t
    WHERE t.id = $1::UUID
),
subtask_handling AS (
    -- Handle subtasks based on the strategy
    UPDATE tasks 
    SET 
        parent_task_id = CASE 
            WHEN $2::TEXT = 'promote' THEN (SELECT parent_task_id FROM task_info)
            WHEN $2::TEXT = 'reassign' THEN (SELECT parent_task_id FROM task_info)
            ELSE parent_task_id  -- No change for 'delete' strategy
        END,
        updated_at = NOW()
    WHERE parent_task_id = $1::UUID
    AND $2::TEXT IN ('promote', 'reassign')
    RETURNING id, title
),
subtask_deletion AS (
    -- Delete subtasks if strategy is 'delete'
    DELETE FROM tasks 
    WHERE parent_task_id = $1::UUID
    AND $2::TEXT = 'delete'
    RETURNING id, title
),
main_task_deletion AS (
    DELETE FROM tasks 
    WHERE id = $1::UUID
    RETURNING id, title, status
)
SELECT 
    ti.id,
    ti.title,
    ti.status,
    ti.subtask_count,
    $2::TEXT as subtask_strategy,
    mtd.id IS NOT NULL as deletion_successful,
    COALESCE(
        (SELECT COUNT(*) FROM subtask_handling), 0
    ) as subtasks_promoted,
    COALESCE(
        (SELECT COUNT(*) FROM subtask_deletion), 0
    ) as subtasks_deleted,
    CASE 
        WHEN ti.id IS NULL THEN 'Task not found'
        WHEN mtd.id IS NOT NULL THEN 'Task removed successfully'
        ELSE 'Failed to remove task'
    END as result_message,
    CASE 
        WHEN $2::TEXT = 'promote' AND ti.subtask_count > 0 THEN 
            'Subtasks promoted to parent level'
        WHEN $2::TEXT = 'delete' AND ti.subtask_count > 0 THEN 
            'All subtasks deleted'
        WHEN $2::TEXT = 'reassign' AND ti.subtask_count > 0 THEN 
            'Subtasks reassigned to parent'
        WHEN ti.subtask_count = 0 THEN 
            'No subtasks to handle'
        ELSE 'Unknown subtask handling strategy'
    END as subtask_handling_message
FROM task_info ti
LEFT JOIN main_task_deletion mtd ON ti.id = mtd.id;

