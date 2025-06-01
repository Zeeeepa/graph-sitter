-- Set task status and handle related updates
-- Parameters: task_id, new_status, user_id (optional for tracking who made the change)

WITH status_update AS (
    UPDATE tasks 
    SET 
        status = $2::TEXT,
        updated_at = NOW(),
        completed_at = CASE 
            WHEN $2::TEXT = 'completed' THEN NOW()
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
        parent_task_id,
        updated_at,
        completed_at,
        actual_duration,
        estimated_duration
),
parent_update AS (
    -- Update parent task progress if this is a subtask
    UPDATE tasks 
    SET updated_at = NOW()
    WHERE id = (SELECT parent_task_id FROM status_update WHERE parent_task_id IS NOT NULL)
    RETURNING id as parent_id, title as parent_title
),
task_stats AS (
    SELECT 
        su.*,
        pu.parent_id,
        pu.parent_title,
        -- Calculate new parent progress if applicable
        CASE 
            WHEN su.parent_task_id IS NOT NULL THEN
                COALESCE(
                    (SELECT ROUND(
                        (COUNT(*) FILTER (WHERE status = 'completed') * 100.0) / COUNT(*)
                    ) FROM tasks st WHERE st.parent_task_id = su.parent_task_id), 0
                )
            ELSE NULL
        END as parent_progress_percentage,
        -- Check if all dependencies are now met for dependent tasks
        COALESCE(
            (SELECT COUNT(*) FROM tasks dependent_task 
             WHERE su.id::TEXT = ANY(
                 SELECT jsonb_array_elements_text(dependent_task.dependencies)
             ) AND dependent_task.status = 'pending'), 0
        ) as unblocked_tasks_count
    FROM status_update su
    LEFT JOIN parent_update pu ON su.parent_task_id = pu.parent_id
)
SELECT 
    id,
    title,
    status,
    parent_task_id,
    parent_title,
    parent_progress_percentage,
    updated_at,
    completed_at,
    actual_duration,
    estimated_duration,
    unblocked_tasks_count,
    -- Status change validation and messages
    CASE 
        WHEN status = $2::TEXT THEN 'Status updated successfully'
        ELSE 'Failed to update status'
    END as result_message,
    -- Duration comparison if completed
    CASE 
        WHEN status = 'completed' AND estimated_duration IS NOT NULL THEN
            CASE 
                WHEN actual_duration <= estimated_duration THEN 'Completed on time'
                WHEN actual_duration <= estimated_duration * 1.2 THEN 'Completed slightly over estimate'
                ELSE 'Completed significantly over estimate'
            END
        ELSE NULL
    END as duration_assessment,
    -- Calculate variance from estimate
    CASE 
        WHEN status = 'completed' AND estimated_duration IS NOT NULL THEN
            ROUND(
                EXTRACT(EPOCH FROM (actual_duration - estimated_duration)) / 
                EXTRACT(EPOCH FROM estimated_duration) * 100
            )
        ELSE NULL
    END as duration_variance_percentage,
    -- Suggest next actions
    CASE 
        WHEN status = 'completed' AND unblocked_tasks_count > 0 THEN 
            'Task completed. ' || unblocked_tasks_count || ' dependent task(s) can now be started.'
        WHEN status = 'completed' AND parent_task_id IS NOT NULL THEN 
            'Subtask completed. Parent task progress: ' || COALESCE(parent_progress_percentage::TEXT || '%', 'unknown')
        WHEN status = 'in_progress' THEN 
            'Task started. Remember to update progress regularly.'
        WHEN status = 'failed' THEN 
            'Task failed. Consider creating follow-up tasks to address issues.'
        WHEN status = 'cancelled' THEN 
            'Task cancelled. Review if any cleanup tasks are needed.'
        ELSE 'Status updated.'
    END as next_actions
FROM task_stats;

