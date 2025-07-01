-- Update a single task's status with minimal side effects
-- Parameters: task_id, new_status

UPDATE tasks 
SET 
    status = $2::TEXT,
    updated_at = NOW(),
    completed_at = CASE 
        WHEN $2::TEXT = 'completed' AND status != 'completed' THEN NOW()
        WHEN $2::TEXT != 'completed' THEN NULL
        ELSE completed_at
    END,
    actual_duration = CASE 
        WHEN $2::TEXT = 'completed' AND status != 'completed' THEN 
            NOW() - created_at
        ELSE actual_duration
    END
WHERE id = $1::UUID
RETURNING 
    id,
    title,
    status,
    updated_at,
    completed_at,
    actual_duration,
    estimated_duration,
    CASE 
        WHEN status = $2::TEXT THEN 'Status updated successfully'
        ELSE 'Failed to update status'
    END as result_message;

