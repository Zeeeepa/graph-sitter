-- Update a task by ID with comprehensive field updates
-- Parameters: task_id, title (optional), description (optional), status (optional), 
--            priority (optional), assigned_to (optional), complexity_score (optional),
--            estimated_duration (optional), dependencies (optional)

WITH task_validation AS (
    SELECT 
        t.id,
        t.title as current_title,
        t.status as current_status,
        t.organization_id
    FROM tasks t
    WHERE t.id = $1::UUID
),
dependency_validation AS (
    SELECT 
        tv.*,
        -- Validate that all dependency task IDs exist and are in the same organization
        CASE 
            WHEN $9::JSONB IS NULL THEN TRUE
            WHEN JSONB_ARRAY_LENGTH($9::JSONB) = 0 THEN TRUE
            ELSE NOT EXISTS(
                SELECT 1 FROM (
                    SELECT jsonb_array_elements_text($9::JSONB)::UUID as dep_id
                ) deps
                LEFT JOIN tasks dep_task ON deps.dep_id = dep_task.id
                WHERE dep_task.id IS NULL 
                OR dep_task.organization_id != tv.organization_id
                OR dep_task.id = tv.id  -- Can't depend on itself
            )
        END as dependencies_valid
    FROM task_validation tv
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
        estimated_duration = COALESCE($8::INTERVAL, estimated_duration),
        dependencies = CASE 
            WHEN $9::JSONB IS NOT NULL AND dv.dependencies_valid THEN $9::JSONB
            ELSE dependencies
        END,
        updated_at = NOW(),
        completed_at = CASE 
            WHEN COALESCE($4::TEXT, status) = 'completed' AND status != 'completed' THEN NOW()
            WHEN COALESCE($4::TEXT, status) != 'completed' THEN NULL
            ELSE completed_at
        END,
        actual_duration = CASE 
            WHEN COALESCE($4::TEXT, status) = 'completed' AND status != 'completed' THEN 
                NOW() - created_at
            ELSE actual_duration
        END
    FROM dependency_validation dv
    WHERE tasks.id = $1::UUID
    AND dv.id = tasks.id
    AND dv.dependencies_valid = TRUE
    RETURNING 
        id,
        title,
        description,
        status,
        priority,
        assigned_to,
        complexity_score,
        estimated_duration,
        dependencies,
        updated_at,
        completed_at,
        actual_duration
)
SELECT 
    tv.id,
    tv.current_title,
    tv.current_status,
    dv.dependencies_valid,
    ur.id IS NOT NULL as update_successful,
    ur.title as new_title,
    ur.status as new_status,
    ur.priority as new_priority,
    ur.assigned_to as new_assigned_to,
    ur.complexity_score as new_complexity_score,
    ur.estimated_duration as new_estimated_duration,
    ur.dependencies as new_dependencies,
    ur.updated_at,
    ur.completed_at,
    ur.actual_duration,
    u.name as assigned_to_name,
    u.email as assigned_to_email,
    -- Calculate what changed
    ARRAY_REMOVE(ARRAY[
        CASE WHEN $2::TEXT IS NOT NULL AND $2::TEXT != tv.current_title THEN 'title' END,
        CASE WHEN $3::TEXT IS NOT NULL THEN 'description' END,
        CASE WHEN $4::TEXT IS NOT NULL AND $4::TEXT != tv.current_status THEN 'status' END,
        CASE WHEN $5::INTEGER IS NOT NULL THEN 'priority' END,
        CASE WHEN $6::UUID IS NOT NULL OR $6::TEXT = 'NULL' THEN 'assigned_to' END,
        CASE WHEN $7::INTEGER IS NOT NULL THEN 'complexity_score' END,
        CASE WHEN $8::INTERVAL IS NOT NULL THEN 'estimated_duration' END,
        CASE WHEN $9::JSONB IS NOT NULL THEN 'dependencies' END
    ], NULL) as fields_changed,
    CASE 
        WHEN tv.id IS NULL THEN 'Task not found'
        WHEN NOT dv.dependencies_valid THEN 'Invalid dependencies: some dependency tasks do not exist or are in different organization'
        WHEN ur.id IS NOT NULL THEN 'Task updated successfully'
        ELSE 'Failed to update task'
    END as result_message,
    -- Duration assessment if completed
    CASE 
        WHEN ur.status = 'completed' AND ur.estimated_duration IS NOT NULL AND ur.actual_duration IS NOT NULL THEN
            CASE 
                WHEN ur.actual_duration <= ur.estimated_duration THEN 'Completed on time'
                WHEN ur.actual_duration <= ur.estimated_duration * 1.2 THEN 'Completed slightly over estimate'
                ELSE 'Completed significantly over estimate'
            END
        ELSE NULL
    END as duration_assessment
FROM task_validation tv
LEFT JOIN dependency_validation dv ON tv.id = dv.id
LEFT JOIN update_result ur ON tv.id = ur.id
LEFT JOIN users u ON ur.assigned_to = u.id;

