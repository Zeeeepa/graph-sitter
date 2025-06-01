-- Generate task files associations based on task description and codebase analysis
-- Parameters: task_id

WITH task_info AS (
    SELECT 
        t.id,
        t.title,
        t.description,
        t.task_type,
        t.codebase_id,
        c.name as codebase_name
    FROM tasks t
    LEFT JOIN codebases c ON t.codebase_id = c.id
    WHERE t.id = $1::UUID
),
relevant_files AS (
    SELECT DISTINCT
        cf.id as file_id,
        cf.file_path,
        cf.file_name,
        cf.file_extension,
        ti.id as task_id,
        -- Determine operation type based on task description and file analysis
        CASE 
            WHEN ti.description ~* ('create.*' || cf.file_name) OR 
                 ti.description ~* ('add.*' || cf.file_name) OR
                 ti.description ~* ('new.*' || cf.file_name) THEN 'create'
            WHEN ti.description ~* ('delete.*' || cf.file_name) OR 
                 ti.description ~* ('remove.*' || cf.file_name) THEN 'delete'
            WHEN ti.description ~* ('move.*' || cf.file_name) OR 
                 ti.description ~* ('rename.*' || cf.file_name) THEN 'move'
            ELSE 'modify'
        END as operation_type,
        -- Calculate relevance score
        (
            -- File name mentioned in title/description
            CASE WHEN ti.title ~* cf.file_name OR ti.description ~* cf.file_name THEN 50 ELSE 0 END +
            -- File extension relevance
            CASE 
                WHEN ti.task_type = 'documentation' AND cf.file_extension IN ('.md', '.rst', '.txt') THEN 30
                WHEN ti.task_type IN ('feature', 'bug_fix', 'refactor') AND cf.file_extension IN ('.py', '.js', '.ts', '.java', '.cpp', '.c') THEN 30
                WHEN cf.file_extension IN ('.sql') AND ti.description ~* 'database|schema|migration' THEN 40
                WHEN cf.file_extension IN ('.json', '.yaml', '.yml') AND ti.description ~* 'config|setting' THEN 25
                ELSE 0
            END +
            -- Path relevance based on keywords
            CASE 
                WHEN ti.description ~* 'test' AND cf.file_path ~* 'test|spec' THEN 20
                WHEN ti.description ~* 'api' AND cf.file_path ~* 'api|endpoint|route' THEN 20
                WHEN ti.description ~* 'ui|frontend' AND cf.file_path ~* 'ui|frontend|component|view' THEN 20
                WHEN ti.description ~* 'backend|server' AND cf.file_path ~* 'backend|server|service' THEN 20
                WHEN ti.description ~* 'database|db' AND cf.file_path ~* 'database|db|model|schema' THEN 20
                ELSE 0
            END +
            -- Symbol relevance (if symbols exist in the file that match task description)
            COALESCE((
                SELECT COUNT(*) * 10
                FROM code_symbols cs 
                WHERE cs.file_id = cf.id 
                AND (ti.description ~* cs.name OR ti.title ~* cs.name)
            ), 0)
        ) as relevance_score,
        -- Generate changes summary based on task type and description
        CASE 
            WHEN ti.task_type = 'bug_fix' THEN 'Fix bug: ' || COALESCE(SUBSTRING(ti.description FROM 1 FOR 100), 'Bug fix')
            WHEN ti.task_type = 'feature' THEN 'Add feature: ' || COALESCE(SUBSTRING(ti.description FROM 1 FOR 100), 'New feature')
            WHEN ti.task_type = 'refactor' THEN 'Refactor: ' || COALESCE(SUBSTRING(ti.description FROM 1 FOR 100), 'Code refactoring')
            WHEN ti.task_type = 'documentation' THEN 'Update documentation: ' || COALESCE(SUBSTRING(ti.description FROM 1 FOR 100), 'Documentation update')
            ELSE 'Modify: ' || COALESCE(SUBSTRING(ti.description FROM 1 FOR 100), 'Code changes')
        END as changes_summary
    FROM task_info ti
    CROSS JOIN codebase_files cf
    WHERE cf.codebase_id = ti.codebase_id
    AND cf.is_deleted = FALSE
),
filtered_files AS (
    SELECT *
    FROM relevant_files
    WHERE relevance_score > 0
),
inserted_task_files AS (
    INSERT INTO task_files (task_id, file_id, operation_type, changes_summary)
    SELECT 
        task_id,
        file_id,
        operation_type,
        changes_summary
    FROM filtered_files
    WHERE relevance_score >= 20  -- Only include files with significant relevance
    ON CONFLICT (task_id, file_id) DO UPDATE SET
        operation_type = EXCLUDED.operation_type,
        changes_summary = EXCLUDED.changes_summary
    RETURNING task_id, file_id, operation_type
)
SELECT 
    rf.file_path,
    rf.file_name,
    rf.operation_type,
    rf.changes_summary,
    rf.relevance_score,
    CASE 
        WHEN itf.file_id IS NOT NULL THEN 'ADDED'
        WHEN rf.relevance_score >= 20 THEN 'ELIGIBLE'
        ELSE 'LOW_RELEVANCE'
    END as status
FROM filtered_files rf
LEFT JOIN inserted_task_files itf ON rf.file_id = itf.file_id
ORDER BY rf.relevance_score DESC, rf.file_path;

