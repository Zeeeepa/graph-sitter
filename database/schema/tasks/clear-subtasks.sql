-- Clear all subtasks for a given parent task
-- Parameters: parent_task_id

WITH deleted_subtasks AS (
    DELETE FROM tasks 
    WHERE parent_task_id = $1::UUID
    RETURNING id, title, status
)
SELECT 
    COUNT(*) as deleted_count,
    ARRAY_AGG(id) as deleted_task_ids,
    ARRAY_AGG(title) as deleted_titles
FROM deleted_subtasks;

