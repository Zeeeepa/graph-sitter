-- Bulk update tasks with filtering criteria
-- Parameters: organization_id, status_filter (optional), assigned_to_filter (optional),
--            new_status (optional), new_assigned_to (optional), new_priority (optional)

WITH filtered_tasks AS (
    SELECT 
        t.id,
        t.title,
        t.status as current_status,
        t.assigned_to as current_assigned_to,
        t.priority as current_priority
    FROM tasks t
    WHERE t.organization_id = $1::UUID
    AND ($2::TEXT IS NULL OR t.status = $2::TEXT)
    AND ($3::UUID IS NULL OR t.assigned_to = $3::UUID)
),
update_result AS (
    UPDATE tasks 
    SET 
        status = COALESCE($4::TEXT, status),
        assigned_to = CASE 
            WHEN $5::UUID IS NOT NULL THEN $5::UUID
            WHEN $5::TEXT = 'NULL' THEN NULL
            ELSE assigned_to
        END,
        priority = COALESCE($6::INTEGER, priority),
        updated_at = NOW(),
        completed_at = CASE 
            WHEN COALESCE($4::TEXT, status) = 'completed' AND status != 'completed' THEN NOW()
            WHEN COALESCE($4::TEXT, status) != 'completed' THEN NULL
            ELSE completed_at
        END
    WHERE id IN (SELECT id FROM filtered_tasks)
    RETURNING 
        id,
        title,
        status,
        assigned_to,
        priority,
        updated_at
)
SELECT 
    COUNT(ft.id) as total_tasks_matched,
    COUNT(ur.id) as tasks_updated,
    COUNT(ur.id) FILTER (WHERE $4::TEXT IS NOT NULL) as status_updates,
    COUNT(ur.id) FILTER (WHERE $5::UUID IS NOT NULL OR $5::TEXT = 'NULL') as assignment_updates,
    COUNT(ur.id) FILTER (WHERE $6::INTEGER IS NOT NULL) as priority_updates,
    ARRAY_AGG(
        JSON_BUILD_OBJECT(
            'id', ur.id,
            'title', ur.title,
            'new_status', ur.status,
            'new_assigned_to', ur.assigned_to,
            'new_priority', ur.priority
        ) ORDER BY ur.title
    ) FILTER (WHERE ur.id IS NOT NULL) as updated_tasks,
    CASE 
        WHEN COUNT(ur.id) = 0 THEN 'No tasks were updated'
        WHEN COUNT(ur.id) = COUNT(ft.id) THEN 'All matching tasks updated successfully'
        ELSE 'Some tasks updated, some failed'
    END as result_message
FROM filtered_tasks ft
LEFT JOIN update_result ur ON ft.id = ur.id;

