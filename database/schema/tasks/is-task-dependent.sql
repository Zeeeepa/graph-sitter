-- Check if a task has dependencies and if they are met
-- Parameters: task_id

WITH task_dependencies AS (
    SELECT 
        t.id,
        t.title,
        t.status,
        t.dependencies,
        JSONB_ARRAY_LENGTH(COALESCE(t.dependencies, '[]'::JSONB)) as dependency_count
    FROM tasks t
    WHERE t.id = $1::UUID
),
dependency_details AS (
    SELECT 
        td.*,
        COALESCE(
            (SELECT ARRAY_AGG(
                JSON_BUILD_OBJECT(
                    'id', dep_task.id,
                    'title', dep_task.title,
                    'status', dep_task.status,
                    'completed_at', dep_task.completed_at,
                    'is_completed', dep_task.status = 'completed'
                ) ORDER BY dep_task.created_at
            ) FROM tasks dep_task 
            WHERE dep_task.id = ANY(
                SELECT jsonb_array_elements_text(td.dependencies)::UUID
            )), 
            ARRAY[]::JSON[]
        ) as dependency_tasks
    FROM task_dependencies td
),
dependency_analysis AS (
    SELECT 
        dd.*,
        -- Count completed dependencies
        COALESCE(
            (SELECT COUNT(*) FROM tasks dep_task 
             WHERE dep_task.id = ANY(
                 SELECT jsonb_array_elements_text(dd.dependencies)::UUID
             ) AND dep_task.status = 'completed'), 0
        ) as completed_dependencies,
        -- Count pending/in-progress dependencies
        COALESCE(
            (SELECT COUNT(*) FROM tasks dep_task 
             WHERE dep_task.id = ANY(
                 SELECT jsonb_array_elements_text(dd.dependencies)::UUID
             ) AND dep_task.status IN ('pending', 'in_progress')), 0
        ) as pending_dependencies,
        -- Count failed dependencies
        COALESCE(
            (SELECT COUNT(*) FROM tasks dep_task 
             WHERE dep_task.id = ANY(
                 SELECT jsonb_array_elements_text(dd.dependencies)::UUID
             ) AND dep_task.status = 'failed'), 0
        ) as failed_dependencies
    FROM dependency_details dd
)
SELECT 
    id,
    title,
    status,
    dependency_count,
    completed_dependencies,
    pending_dependencies,
    failed_dependencies,
    dependency_tasks,
    -- Main result: are dependencies met?
    CASE 
        WHEN dependency_count = 0 THEN TRUE
        WHEN failed_dependencies > 0 THEN FALSE
        WHEN completed_dependencies = dependency_count THEN TRUE
        ELSE FALSE
    END as dependencies_met,
    -- Can the task be started?
    CASE 
        WHEN dependency_count = 0 THEN TRUE
        WHEN failed_dependencies > 0 THEN FALSE
        WHEN completed_dependencies = dependency_count THEN TRUE
        ELSE FALSE
    END as can_start,
    -- Blocking status
    CASE 
        WHEN dependency_count = 0 THEN 'NO_DEPENDENCIES'
        WHEN failed_dependencies > 0 THEN 'BLOCKED_BY_FAILED'
        WHEN pending_dependencies > 0 THEN 'BLOCKED_BY_PENDING'
        WHEN completed_dependencies = dependency_count THEN 'READY'
        ELSE 'UNKNOWN'
    END as blocking_status,
    -- Progress percentage of dependencies
    CASE 
        WHEN dependency_count = 0 THEN 100
        ELSE ROUND((completed_dependencies * 100.0) / dependency_count)
    END as dependency_progress_percentage,
    -- Estimated time until dependencies are met (simplified)
    CASE 
        WHEN dependency_count = 0 OR completed_dependencies = dependency_count THEN INTERVAL '0'
        WHEN pending_dependencies > 0 THEN 
            COALESCE(
                (SELECT AVG(estimated_duration) FROM tasks dep_task 
                 WHERE dep_task.id = ANY(
                     SELECT jsonb_array_elements_text(dependencies)::UUID
                 ) AND dep_task.status IN ('pending', 'in_progress')),
                INTERVAL '1 day'
            )
        ELSE NULL
    END as estimated_wait_time
FROM dependency_analysis;

