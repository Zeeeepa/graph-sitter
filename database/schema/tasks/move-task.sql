-- Move a task to a different parent or make it a root task
-- Parameters: task_id, new_parent_id (NULL to make it a root task)

WITH task_validation AS (
    SELECT 
        t.id,
        t.title,
        t.parent_task_id as old_parent_id,
        $2::UUID as new_parent_id,
        -- Validate that we're not creating a circular dependency
        CASE 
            WHEN $2::UUID IS NULL THEN TRUE  -- Moving to root is always safe
            WHEN $2::UUID = t.id THEN FALSE  -- Can't be parent of itself
            ELSE NOT EXISTS(
                WITH RECURSIVE parent_chain AS (
                    SELECT id, parent_task_id, 1 as level
                    FROM tasks 
                    WHERE id = $2::UUID
                    
                    UNION ALL
                    
                    SELECT t2.id, t2.parent_task_id, pc.level + 1
                    FROM tasks t2
                    INNER JOIN parent_chain pc ON t2.id = pc.parent_task_id
                    WHERE pc.level < 10  -- Prevent infinite recursion
                )
                SELECT 1 FROM parent_chain WHERE id = t.id
            )
        END as is_valid_move,
        -- Check if new parent exists and is in same organization
        CASE 
            WHEN $2::UUID IS NULL THEN TRUE
            ELSE EXISTS(
                SELECT 1 FROM tasks parent_task 
                WHERE parent_task.id = $2::UUID 
                AND parent_task.organization_id = t.organization_id
            )
        END as parent_exists
    FROM tasks t
    WHERE t.id = $1::UUID
),
move_result AS (
    UPDATE tasks 
    SET 
        parent_task_id = $2::UUID,
        updated_at = NOW()
    WHERE id = $1::UUID
    AND EXISTS(
        SELECT 1 FROM task_validation tv 
        WHERE tv.id = $1::UUID 
        AND tv.is_valid_move = TRUE 
        AND tv.parent_exists = TRUE
    )
    RETURNING id, parent_task_id, title, updated_at
)
SELECT 
    tv.id,
    tv.title,
    tv.old_parent_id,
    tv.new_parent_id,
    tv.is_valid_move,
    tv.parent_exists,
    mr.id IS NOT NULL as move_successful,
    CASE 
        WHEN NOT tv.is_valid_move THEN 'Invalid move: would create circular dependency'
        WHEN NOT tv.parent_exists THEN 'Invalid move: parent task does not exist or is in different organization'
        WHEN mr.id IS NOT NULL THEN 'Task moved successfully'
        ELSE 'Move failed for unknown reason'
    END as result_message,
    mr.updated_at as moved_at
FROM task_validation tv
LEFT JOIN move_result mr ON tv.id = mr.id;

