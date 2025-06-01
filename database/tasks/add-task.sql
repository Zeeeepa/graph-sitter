-- Add Task Function
-- Creates a new task with comprehensive metadata and validation

CREATE OR REPLACE FUNCTION add_task(
    p_title VARCHAR(500),
    p_description TEXT DEFAULT NULL,
    p_priority task_priority DEFAULT 'medium',
    p_context JSONB DEFAULT '{}',
    p_requirements JSONB DEFAULT '{}',
    p_affected_files JSONB DEFAULT '[]',
    p_organization_id UUID DEFAULT NULL,
    p_codebase_id UUID DEFAULT NULL,
    p_parent_task_id UUID DEFAULT NULL,
    p_assigned_to UUID DEFAULT NULL,
    p_due_date TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    p_tags JSONB DEFAULT '[]'
) RETURNS JSONB AS $$
DECLARE
    new_task_id UUID;
    org_id UUID;
    task_result JSONB;
BEGIN
    -- Validate input
    IF p_title IS NULL OR LENGTH(TRIM(p_title)) = 0 THEN
        RAISE EXCEPTION 'Task title cannot be empty';
    END IF;
    
    -- Get organization ID if not provided
    IF p_organization_id IS NULL THEN
        SELECT id INTO org_id FROM organizations WHERE codegen_org_id = '323' LIMIT 1;
        IF org_id IS NULL THEN
            RAISE EXCEPTION 'No default organization found';
        END IF;
    ELSE
        org_id := p_organization_id;
    END IF;
    
    -- Validate parent task exists if provided
    IF p_parent_task_id IS NOT NULL THEN
        IF NOT EXISTS (SELECT 1 FROM tasks WHERE id = p_parent_task_id AND organization_id = org_id) THEN
            RAISE EXCEPTION 'Parent task not found or not in same organization';
        END IF;
    END IF;
    
    -- Validate codebase exists if provided
    IF p_codebase_id IS NOT NULL THEN
        IF NOT EXISTS (SELECT 1 FROM codebases WHERE id = p_codebase_id) THEN
            RAISE EXCEPTION 'Codebase not found';
        END IF;
    END IF;
    
    -- Validate assigned user exists if provided
    IF p_assigned_to IS NOT NULL THEN
        IF NOT EXISTS (SELECT 1 FROM users WHERE id = p_assigned_to AND organization_id = org_id) THEN
            RAISE EXCEPTION 'Assigned user not found or not in same organization';
        END IF;
    END IF;
    
    -- Create the task
    INSERT INTO tasks (
        organization_id,
        codebase_id,
        parent_task_id,
        title,
        description,
        priority,
        context,
        requirements,
        affected_files,
        assigned_to,
        due_date,
        tags
    ) VALUES (
        org_id,
        p_codebase_id,
        p_parent_task_id,
        p_title,
        p_description,
        p_priority,
        p_context,
        p_requirements,
        p_affected_files,
        p_assigned_to,
        p_due_date,
        p_tags
    ) RETURNING id INTO new_task_id;
    
    -- Add to subtasks relationship if this is a subtask
    IF p_parent_task_id IS NOT NULL THEN
        INSERT INTO task_subtasks (parent_task_id, subtask_id, order_index)
        VALUES (p_parent_task_id, new_task_id, 
                COALESCE((SELECT MAX(order_index) + 1 FROM task_subtasks WHERE parent_task_id = p_parent_task_id), 0));
    END IF;
    
    -- Log the creation
    INSERT INTO task_execution_log (task_id, event_type, event_data)
    VALUES (new_task_id, 'created', jsonb_build_object(
        'title', p_title,
        'priority', p_priority,
        'parent_task_id', p_parent_task_id,
        'assigned_to', p_assigned_to
    ));
    
    -- Analyze task complexity
    PERFORM analyze_task_complexity(new_task_id);
    
    -- Build result
    task_result := jsonb_build_object(
        'task_id', new_task_id,
        'title', p_title,
        'status', 'pending',
        'priority', p_priority,
        'organization_id', org_id,
        'created_at', NOW()
    );
    
    RETURN task_result;
END;
$$ LANGUAGE plpgsql;

-- Example usage:
-- SELECT add_task('Implement user authentication', 'Add JWT-based authentication system', 'high', 
--                 '{"framework": "FastAPI", "database": "PostgreSQL"}',
--                 '{"security": "JWT tokens", "endpoints": ["/login", "/register"]}',
--                 '["src/auth/models.py", "src/auth/routes.py"]');

COMMENT ON FUNCTION add_task IS 'Creates a new task with comprehensive validation and automatic complexity analysis';

