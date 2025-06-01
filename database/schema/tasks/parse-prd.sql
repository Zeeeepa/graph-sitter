-- Parse a Product Requirements Document (PRD) and extract tasks
-- Parameters: organization_id, codebase_id (optional), prd_content, created_by

WITH prd_analysis AS (
    SELECT 
        $1::UUID as organization_id,
        $2::UUID as codebase_id,
        $3::TEXT as prd_content,
        $4::UUID as created_by,
        -- Extract sections using regex patterns
        REGEXP_SPLIT_TO_ARRAY($3::TEXT, '\n(?=##?\s)') as sections
),
section_parsing AS (
    SELECT 
        pa.*,
        section_text,
        ROW_NUMBER() OVER() as section_order,
        -- Identify section type
        CASE 
            WHEN section_text ~* '^##?\s*(requirements?|features?|functionality)' THEN 'requirements'
            WHEN section_text ~* '^##?\s*(tasks?|todo|work items?)' THEN 'tasks'
            WHEN section_text ~* '^##?\s*(bugs?|issues?|fixes?)' THEN 'bugs'
            WHEN section_text ~* '^##?\s*(tests?|testing|qa)' THEN 'testing'
            WHEN section_text ~* '^##?\s*(docs?|documentation)' THEN 'documentation'
            WHEN section_text ~* '^##?\s*(api|endpoints?)' THEN 'api'
            WHEN section_text ~* '^##?\s*(ui|frontend|interface)' THEN 'ui'
            WHEN section_text ~* '^##?\s*(backend|server)' THEN 'backend'
            WHEN section_text ~* '^##?\s*(database|db|schema)' THEN 'database'
            ELSE 'general'
        END as section_type,
        -- Extract title
        TRIM(REGEXP_REPLACE(
            SPLIT_PART(section_text, E'\n', 1), 
            '^##?\s*', '', 'g'
        )) as section_title
    FROM prd_analysis pa,
    UNNEST(pa.sections) as section_text
    WHERE TRIM(section_text) != ''
),
task_extraction AS (
    SELECT 
        sp.*,
        task_line,
        ROW_NUMBER() OVER(PARTITION BY sp.section_order ORDER BY task_line) as task_order,
        -- Clean up task text
        TRIM(REGEXP_REPLACE(task_line, '^[-*+]\s*', '')) as clean_task_text,
        -- Determine task priority from text
        CASE 
            WHEN task_line ~* '(critical|urgent|high priority|must have)' THEN 9
            WHEN task_line ~* '(important|should have|medium priority)' THEN 6
            WHEN task_line ~* '(nice to have|low priority|could have)' THEN 3
            ELSE 5
        END as extracted_priority,
        -- Determine complexity from text
        CASE 
            WHEN task_line ~* '(complex|difficult|major|significant|extensive)' THEN 8
            WHEN task_line ~* '(moderate|medium|standard)' THEN 5
            WHEN task_line ~* '(simple|easy|minor|small|quick)' THEN 2
            ELSE 4
        END as extracted_complexity
    FROM section_parsing sp,
    UNNEST(STRING_TO_ARRAY(sp.section_text, E'\n')) as task_line
    WHERE task_line ~* '^\s*[-*+]\s+.+'  -- Lines that start with bullet points
    AND TRIM(task_line) != ''
),
task_categorization AS (
    SELECT 
        te.*,
        -- Map section types to task types
        CASE te.section_type
            WHEN 'bugs' THEN 'bug_fix'
            WHEN 'testing' THEN 'testing'
            WHEN 'documentation' THEN 'documentation'
            WHEN 'api' THEN 'feature'
            WHEN 'ui' THEN 'feature'
            WHEN 'backend' THEN 'feature'
            WHEN 'database' THEN 'feature'
            ELSE 'feature'
        END as task_type,
        -- Generate estimated duration based on complexity and type
        CASE 
            WHEN te.extracted_complexity <= 3 THEN INTERVAL '4 hours'
            WHEN te.extracted_complexity <= 6 THEN INTERVAL '1 day'
            WHEN te.extracted_complexity <= 8 THEN INTERVAL '3 days'
            ELSE INTERVAL '1 week'
        END as estimated_duration
    FROM task_extraction te
    WHERE LENGTH(TRIM(te.clean_task_text)) > 10  -- Filter out very short tasks
),
inserted_tasks AS (
    INSERT INTO tasks (
        organization_id,
        codebase_id,
        title,
        description,
        task_type,
        priority,
        complexity_score,
        estimated_duration,
        created_by,
        metadata
    )
    SELECT 
        tc.organization_id,
        tc.codebase_id,
        -- Use first 100 chars as title
        LEFT(tc.clean_task_text, 100),
        -- Full text as description with context
        'From PRD Section: ' || tc.section_title || E'\n\n' || tc.clean_task_text,
        tc.task_type,
        tc.extracted_priority,
        tc.extracted_complexity,
        tc.estimated_duration,
        tc.created_by,
        JSON_BUILD_OBJECT(
            'source', 'prd_parsing',
            'section_type', tc.section_type,
            'section_title', tc.section_title,
            'section_order', tc.section_order,
            'task_order', tc.task_order,
            'original_text', tc.clean_task_text
        )
    FROM task_categorization tc
    RETURNING id, title, task_type, priority, complexity_score
)
SELECT 
    COUNT(*) as total_tasks_created,
    COUNT(*) FILTER (WHERE task_type = 'feature') as feature_tasks,
    COUNT(*) FILTER (WHERE task_type = 'bug_fix') as bug_fix_tasks,
    COUNT(*) FILTER (WHERE task_type = 'documentation') as documentation_tasks,
    COUNT(*) FILTER (WHERE task_type = 'testing') as testing_tasks,
    COUNT(*) FILTER (WHERE priority >= 8) as high_priority_tasks,
    COUNT(*) FILTER (WHERE priority >= 5 AND priority < 8) as medium_priority_tasks,
    COUNT(*) FILTER (WHERE priority < 5) as low_priority_tasks,
    ROUND(AVG(complexity_score), 1) as avg_complexity,
    ARRAY_AGG(
        JSON_BUILD_OBJECT(
            'id', id,
            'title', title,
            'type', task_type,
            'priority', priority,
            'complexity', complexity_score
        ) ORDER BY priority DESC, title
    ) as created_tasks
FROM inserted_tasks;

