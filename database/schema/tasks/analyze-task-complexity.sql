-- Analyze task complexity based on various factors
-- Parameters: task_id

WITH task_analysis AS (
    SELECT 
        t.id,
        t.title,
        t.description,
        t.task_type,
        t.complexity_score,
        -- Count subtasks
        (SELECT COUNT(*) FROM tasks st WHERE st.parent_task_id = t.id) as subtask_count,
        -- Count affected files
        (SELECT COUNT(*) FROM task_files tf WHERE tf.task_id = t.id) as affected_files_count,
        -- Calculate description complexity (word count, special keywords)
        CASE 
            WHEN LENGTH(t.description) > 1000 THEN 3
            WHEN LENGTH(t.description) > 500 THEN 2
            ELSE 1
        END as description_complexity,
        -- Task type complexity weights
        CASE t.task_type
            WHEN 'analysis' THEN 1
            WHEN 'documentation' THEN 1
            WHEN 'bug_fix' THEN 2
            WHEN 'feature' THEN 3
            WHEN 'refactor' THEN 4
            ELSE 2
        END as type_complexity,
        -- Check for complexity keywords in description
        CASE 
            WHEN t.description ~* '(complex|difficult|challenging|major|significant|extensive|comprehensive)' THEN 2
            WHEN t.description ~* '(simple|easy|minor|small|quick|basic)' THEN -1
            ELSE 0
        END as keyword_complexity
    FROM tasks t
    WHERE t.id = $1::UUID
),
complexity_calculation AS (
    SELECT 
        *,
        -- Calculate overall complexity score
        GREATEST(1, LEAST(10, 
            type_complexity + 
            description_complexity + 
            keyword_complexity + 
            CASE 
                WHEN subtask_count > 5 THEN 3
                WHEN subtask_count > 2 THEN 2
                WHEN subtask_count > 0 THEN 1
                ELSE 0
            END +
            CASE 
                WHEN affected_files_count > 10 THEN 3
                WHEN affected_files_count > 5 THEN 2
                WHEN affected_files_count > 0 THEN 1
                ELSE 0
            END
        )) as calculated_complexity
    FROM task_analysis
)
SELECT 
    id,
    title,
    task_type,
    complexity_score as current_complexity,
    calculated_complexity as suggested_complexity,
    subtask_count,
    affected_files_count,
    description_complexity,
    type_complexity,
    keyword_complexity,
    CASE 
        WHEN calculated_complexity <= 3 THEN 'Low'
        WHEN calculated_complexity <= 6 THEN 'Medium'
        WHEN calculated_complexity <= 8 THEN 'High'
        ELSE 'Very High'
    END as complexity_level,
    -- Estimated duration based on complexity
    CASE 
        WHEN calculated_complexity <= 3 THEN INTERVAL '2 hours'
        WHEN calculated_complexity <= 6 THEN INTERVAL '1 day'
        WHEN calculated_complexity <= 8 THEN INTERVAL '3 days'
        ELSE INTERVAL '1 week'
    END as estimated_duration
FROM complexity_calculation;

