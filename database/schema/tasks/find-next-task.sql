-- Find the next task to work on based on priority, dependencies, and assignment
-- Parameters: organization_id, assigned_to (optional), codebase_id (optional)

WITH available_tasks AS (
    SELECT 
        t.id,
        t.title,
        t.description,
        t.task_type,
        t.status,
        t.priority,
        t.complexity_score,
        t.estimated_duration,
        t.assigned_to,
        t.created_at,
        t.dependencies,
        u.name as assigned_to_name,
        c.name as codebase_name,
        -- Check if all dependencies are completed
        CASE 
            WHEN JSONB_ARRAY_LENGTH(t.dependencies) = 0 THEN TRUE
            ELSE NOT EXISTS(
                SELECT 1 FROM tasks dep_task 
                WHERE dep_task.id = ANY(
                    SELECT jsonb_array_elements_text(t.dependencies)::UUID
                ) AND dep_task.status != 'completed'
            )
        END as dependencies_met,
        -- Calculate task age in days
        EXTRACT(EPOCH FROM (NOW() - t.created_at)) / 86400 as age_days,
        -- Count subtasks
        (SELECT COUNT(*) FROM tasks st WHERE st.parent_task_id = t.id) as subtask_count
    FROM tasks t
    LEFT JOIN users u ON t.assigned_to = u.id
    LEFT JOIN codebases c ON t.codebase_id = c.id
    WHERE t.organization_id = $1::UUID
    AND t.status IN ('pending', 'in_progress')
    AND ($2::UUID IS NULL OR t.assigned_to = $2::UUID OR t.assigned_to IS NULL)
    AND ($3::UUID IS NULL OR t.codebase_id = $3::UUID)
    AND t.parent_task_id IS NULL  -- Only root tasks for now
),
scored_tasks AS (
    SELECT 
        *,
        -- Calculate priority score (higher is better)
        (
            -- Base priority
            priority * 10 +
            -- Dependency bonus (ready tasks get priority)
            CASE WHEN dependencies_met THEN 20 ELSE -50 END +
            -- Age bonus (older tasks get slight priority)
            LEAST(age_days * 0.5, 10) +
            -- Complexity penalty (simpler tasks preferred for quick wins)
            CASE 
                WHEN complexity_score <= 3 THEN 5
                WHEN complexity_score <= 6 THEN 0
                ELSE -5
            END +
            -- Assignment bonus (assigned tasks get priority)
            CASE WHEN assigned_to IS NOT NULL THEN 15 ELSE 0 END +
            -- Task type priority
            CASE task_type
                WHEN 'bug_fix' THEN 10
                WHEN 'feature' THEN 5
                WHEN 'refactor' THEN 3
                WHEN 'documentation' THEN 1
                ELSE 0
            END
        ) as priority_score
    FROM available_tasks
    WHERE dependencies_met = TRUE  -- Only show tasks that can actually be worked on
),
recommended_tasks AS (
    SELECT 
        *,
        ROW_NUMBER() OVER (ORDER BY priority_score DESC, created_at ASC) as rank
    FROM scored_tasks
)
SELECT 
    id,
    title,
    description,
    task_type,
    status,
    priority,
    complexity_score,
    estimated_duration,
    assigned_to,
    assigned_to_name,
    codebase_name,
    subtask_count,
    age_days,
    priority_score,
    rank,
    created_at,
    CASE 
        WHEN rank = 1 THEN 'RECOMMENDED'
        WHEN rank <= 3 THEN 'HIGH_PRIORITY'
        WHEN rank <= 10 THEN 'MEDIUM_PRIORITY'
        ELSE 'LOW_PRIORITY'
    END as recommendation_level,
    -- Provide reasoning for the recommendation
    CASE 
        WHEN assigned_to IS NOT NULL THEN 'Assigned to user'
        WHEN priority >= 8 THEN 'High priority task'
        WHEN task_type = 'bug_fix' THEN 'Bug fix - high impact'
        WHEN complexity_score <= 3 THEN 'Quick win - low complexity'
        WHEN age_days > 7 THEN 'Aging task needs attention'
        ELSE 'Standard priority'
    END as recommendation_reason
FROM recommended_tasks
ORDER BY rank
LIMIT 10;

