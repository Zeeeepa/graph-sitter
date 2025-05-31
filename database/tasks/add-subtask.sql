-- Add Subtask Function
-- Creates a subtask under an existing parent task with proper hierarchy management

CREATE OR REPLACE FUNCTION add_subtask(
    p_parent_task_id UUID,
    p_title VARCHAR(500),
    p_description TEXT DEFAULT NULL,
    p_priority task_priority DEFAULT 'medium',
    p_context JSONB DEFAULT '{}',
    p_requirements JSONB DEFAULT '{}',
    p_affected_files JSONB DEFAULT '[]',
    p_assigned_to UUID DEFAULT NULL,
    p_due_date TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    p_order_index INTEGER DEFAULT NULL
) RETURNS JSONB AS $$
DECLARE
    new_task_id UUID;
    org_id UUID;
    codebase_id UUID;
    parent_priority task_priority;
    calculated_order INTEGER;
    subtask_result JSONB;
BEGIN
    -- Validate input
    IF p_title IS NULL OR LENGTH(TRIM(p_title)) = 0 THEN
        RAISE EXCEPTION 'Subtask title cannot be empty';
    END IF;
    
    -- Get parent task info and validate it exists
    SELECT organization_id, tasks.codebase_id, priority 
    INTO org_id, codebase_id, parent_priority
    FROM tasks WHERE id = p_parent_task_id;
    
    IF org_id IS NULL THEN
        RAISE EXCEPTION 'Parent task not found: %', p_parent_task_id;
    END IF;
    
    -- Validate assigned user exists if provided
    IF p_assigned_to IS NOT NULL THEN
        IF NOT EXISTS (SELECT 1 FROM users WHERE id = p_assigned_to AND organization_id = org_id) THEN
            RAISE EXCEPTION 'Assigned user not found or not in same organization';
        END IF;
    END IF;
    
    -- Calculate order index if not provided
    IF p_order_index IS NULL THEN
        SELECT COALESCE(MAX(order_index) + 1, 0) INTO calculated_order
        FROM task_subtasks WHERE parent_task_id = p_parent_task_id;
    ELSE
        calculated_order := p_order_index;
        
        -- Shift existing subtasks if necessary
        UPDATE task_subtasks 
        SET order_index = order_index + 1 
        WHERE parent_task_id = p_parent_task_id 
        AND order_index >= calculated_order;
    END IF;
    
    -- Inherit priority from parent if not explicitly set to something higher
    IF p_priority = 'medium' AND parent_priority IN ('high', 'critical') THEN
        p_priority := parent_priority;
    END IF;
    
    -- Create the subtask
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
        due_date
    ) VALUES (
        org_id,
        codebase_id,
        p_parent_task_id,
        p_title,
        p_description,
        p_priority,
        p_context,
        p_requirements,
        p_affected_files,
        p_assigned_to,
        p_due_date
    ) RETURNING id INTO new_task_id;
    
    -- Add to subtasks relationship
    INSERT INTO task_subtasks (parent_task_id, subtask_id, order_index)
    VALUES (p_parent_task_id, new_task_id, calculated_order);
    
    -- Log the creation
    INSERT INTO task_execution_log (task_id, event_type, event_data)
    VALUES (new_task_id, 'created_as_subtask', jsonb_build_object(
        'parent_task_id', p_parent_task_id,
        'title', p_title,
        'priority', p_priority,
        'order_index', calculated_order
    ));
    
    -- Log on parent task as well
    INSERT INTO task_execution_log (task_id, event_type, event_data)
    VALUES (p_parent_task_id, 'subtask_added', jsonb_build_object(
        'subtask_id', new_task_id,
        'subtask_title', p_title,
        'order_index', calculated_order
    ));
    
    -- Analyze task complexity
    PERFORM analyze_task_complexity(new_task_id);
    
    -- Update parent task complexity (subtasks affect parent complexity)
    PERFORM analyze_task_complexity(p_parent_task_id);
    
    -- Build result
    subtask_result := jsonb_build_object(
        'task_id', new_task_id,
        'parent_task_id', p_parent_task_id,
        'title', p_title,
        'status', 'pending',
        'priority', p_priority,
        'order_index', calculated_order,
        'organization_id', org_id,
        'created_at', NOW()
    );
    
    RETURN subtask_result;
END;
$$ LANGUAGE plpgsql;

-- Function to reorder subtasks
CREATE OR REPLACE FUNCTION reorder_subtasks(
    p_parent_task_id UUID,
    p_subtask_order JSONB -- Array of subtask IDs in desired order
) RETURNS BOOLEAN AS $$
DECLARE
    subtask_id UUID;
    new_order INTEGER := 0;
BEGIN
    -- Validate parent task exists
    IF NOT EXISTS (SELECT 1 FROM tasks WHERE id = p_parent_task_id) THEN
        RAISE EXCEPTION 'Parent task not found: %', p_parent_task_id;
    END IF;
    
    -- Update order for each subtask
    FOR subtask_id IN SELECT jsonb_array_elements_text(p_subtask_order)::UUID
    LOOP
        UPDATE task_subtasks 
        SET order_index = new_order
        WHERE parent_task_id = p_parent_task_id 
        AND subtask_id = subtask_id;
        
        new_order := new_order + 1;
    END LOOP;
    
    -- Log the reordering
    INSERT INTO task_execution_log (task_id, event_type, event_data)
    VALUES (p_parent_task_id, 'subtasks_reordered', jsonb_build_object(
        'new_order', p_subtask_order
    ));
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Function to move subtask to different parent
CREATE OR REPLACE FUNCTION move_subtask(
    p_subtask_id UUID,
    p_new_parent_id UUID,
    p_order_index INTEGER DEFAULT NULL
) RETURNS BOOLEAN AS $$
DECLARE
    old_parent_id UUID;
    org_id UUID;
    new_org_id UUID;
    calculated_order INTEGER;
BEGIN
    -- Get current parent and validate subtask exists
    SELECT parent_task_id INTO old_parent_id 
    FROM tasks WHERE id = p_subtask_id;
    
    IF old_parent_id IS NULL THEN
        RAISE EXCEPTION 'Subtask not found or is not a subtask: %', p_subtask_id;
    END IF;
    
    -- Validate new parent exists and is in same organization
    SELECT organization_id INTO org_id FROM tasks WHERE id = old_parent_id;
    SELECT organization_id INTO new_org_id FROM tasks WHERE id = p_new_parent_id;
    
    IF new_org_id IS NULL THEN
        RAISE EXCEPTION 'New parent task not found: %', p_new_parent_id;
    END IF;
    
    IF org_id != new_org_id THEN
        RAISE EXCEPTION 'Cannot move subtask between different organizations';
    END IF;
    
    -- Calculate order index for new parent
    IF p_order_index IS NULL THEN
        SELECT COALESCE(MAX(order_index) + 1, 0) INTO calculated_order
        FROM task_subtasks WHERE parent_task_id = p_new_parent_id;
    ELSE
        calculated_order := p_order_index;
        
        -- Shift existing subtasks in new parent
        UPDATE task_subtasks 
        SET order_index = order_index + 1 
        WHERE parent_task_id = p_new_parent_id 
        AND order_index >= calculated_order;
    END IF;
    
    -- Remove from old parent
    DELETE FROM task_subtasks 
    WHERE parent_task_id = old_parent_id AND subtask_id = p_subtask_id;
    
    -- Update task parent
    UPDATE tasks 
    SET parent_task_id = p_new_parent_id 
    WHERE id = p_subtask_id;
    
    -- Add to new parent
    INSERT INTO task_subtasks (parent_task_id, subtask_id, order_index)
    VALUES (p_new_parent_id, p_subtask_id, calculated_order);
    
    -- Compact order indexes in old parent
    UPDATE task_subtasks 
    SET order_index = subquery.new_order
    FROM (
        SELECT subtask_id, ROW_NUMBER() OVER (ORDER BY order_index) - 1 as new_order
        FROM task_subtasks 
        WHERE parent_task_id = old_parent_id
    ) subquery
    WHERE task_subtasks.subtask_id = subquery.subtask_id
    AND task_subtasks.parent_task_id = old_parent_id;
    
    -- Log the move
    INSERT INTO task_execution_log (task_id, event_type, event_data)
    VALUES (p_subtask_id, 'moved_to_new_parent', jsonb_build_object(
        'old_parent_id', old_parent_id,
        'new_parent_id', p_new_parent_id,
        'new_order_index', calculated_order
    ));
    
    -- Update complexity for both old and new parents
    PERFORM analyze_task_complexity(old_parent_id);
    PERFORM analyze_task_complexity(p_new_parent_id);
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Example usage:
-- SELECT add_subtask('parent-task-uuid', 'Create user model', 'Define user data structure', 'medium');
-- SELECT reorder_subtasks('parent-task-uuid', '["subtask1-uuid", "subtask2-uuid", "subtask3-uuid"]');
-- SELECT move_subtask('subtask-uuid', 'new-parent-uuid', 0);

COMMENT ON FUNCTION add_subtask IS 'Creates a subtask with proper hierarchy management and order indexing';
COMMENT ON FUNCTION reorder_subtasks IS 'Reorders subtasks within a parent task';
COMMENT ON FUNCTION move_subtask IS 'Moves a subtask to a different parent task';

