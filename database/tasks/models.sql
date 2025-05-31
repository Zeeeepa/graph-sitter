-- Tasks Module Database Schema
-- Comprehensive task management system with hierarchical support and complexity analysis

-- Main tasks table
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    codebase_id UUID REFERENCES codebases(id) ON DELETE SET NULL,
    parent_task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    
    -- Task identification
    title VARCHAR(500) NOT NULL,
    description TEXT,
    task_type VARCHAR(100) DEFAULT 'general',
    
    -- Task metadata
    status task_status DEFAULT 'pending',
    priority task_priority DEFAULT 'medium',
    complexity_score INTEGER CHECK (complexity_score >= 1 AND complexity_score <= 10),
    estimated_hours DECIMAL(5,2),
    actual_hours DECIMAL(5,2),
    
    -- Assignment and tracking
    assigned_to UUID REFERENCES users(id) ON DELETE SET NULL,
    codegen_task_id VARCHAR(100), -- Reference to Codegen API task
    linear_issue_id VARCHAR(100),
    github_issue_number INTEGER,
    
    -- Context and requirements
    requirements JSONB DEFAULT '{}',
    context JSONB DEFAULT '{}',
    acceptance_criteria JSONB DEFAULT '[]',
    affected_files JSONB DEFAULT '[]',
    
    -- Dependencies and relationships
    depends_on JSONB DEFAULT '[]', -- Array of task IDs this task depends on
    blocks JSONB DEFAULT '[]', -- Array of task IDs this task blocks
    
    -- Timing
    due_date TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    tags JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Subtasks relationship table (for explicit hierarchical relationships)
CREATE TABLE task_subtasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    parent_task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    subtask_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    order_index INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(parent_task_id, subtask_id)
);

-- Task dependencies table (for complex dependency management)
CREATE TABLE task_dependencies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    depends_on_task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    dependency_type VARCHAR(50) DEFAULT 'blocks', -- blocks, requires, suggests
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(task_id, depends_on_task_id),
    CHECK(task_id != depends_on_task_id) -- Prevent self-dependencies
);

-- Task files table (tracks files generated or modified by tasks)
CREATE TABLE task_files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    file_path VARCHAR(1000) NOT NULL,
    file_type VARCHAR(50), -- source, test, config, documentation
    action VARCHAR(20) NOT NULL, -- created, modified, deleted
    content_hash VARCHAR(64),
    size_bytes INTEGER,
    lines_added INTEGER DEFAULT 0,
    lines_removed INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Task execution log (tracks task progress and events)
CREATE TABLE task_execution_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL, -- status_change, assignment, comment, file_change
    event_data JSONB DEFAULT '{}',
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    codegen_agent_id VARCHAR(100),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Task complexity analysis table
CREATE TABLE task_complexity_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    
    -- Complexity metrics
    cyclomatic_complexity INTEGER,
    cognitive_complexity INTEGER,
    estimated_effort_hours DECIMAL(5,2),
    risk_level VARCHAR(20) DEFAULT 'medium', -- low, medium, high, critical
    
    -- Analysis factors
    factors JSONB DEFAULT '{}', -- What contributes to complexity
    recommendations JSONB DEFAULT '[]', -- Suggestions for reducing complexity
    
    -- Dependencies impact
    dependency_count INTEGER DEFAULT 0,
    affected_components JSONB DEFAULT '[]',
    
    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    analyzer_version VARCHAR(20) DEFAULT '1.0'
);

-- Create indexes for performance
CREATE INDEX idx_tasks_organization_id ON tasks(organization_id);
CREATE INDEX idx_tasks_codebase_id ON tasks(codebase_id);
CREATE INDEX idx_tasks_parent_task_id ON tasks(parent_task_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_priority ON tasks(priority);
CREATE INDEX idx_tasks_assigned_to ON tasks(assigned_to);
CREATE INDEX idx_tasks_codegen_task_id ON tasks(codegen_task_id);
CREATE INDEX idx_tasks_linear_issue_id ON tasks(linear_issue_id);
CREATE INDEX idx_tasks_due_date ON tasks(due_date);
CREATE INDEX idx_tasks_created_at ON tasks(created_at);

CREATE INDEX idx_task_subtasks_parent ON task_subtasks(parent_task_id);
CREATE INDEX idx_task_subtasks_child ON task_subtasks(subtask_id);

CREATE INDEX idx_task_dependencies_task ON task_dependencies(task_id);
CREATE INDEX idx_task_dependencies_depends ON task_dependencies(depends_on_task_id);

CREATE INDEX idx_task_files_task_id ON task_files(task_id);
CREATE INDEX idx_task_files_path ON task_files(file_path);
CREATE INDEX idx_task_files_type ON task_files(file_type);

CREATE INDEX idx_task_execution_log_task_id ON task_execution_log(task_id);
CREATE INDEX idx_task_execution_log_event_type ON task_execution_log(event_type);
CREATE INDEX idx_task_execution_log_timestamp ON task_execution_log(timestamp);

CREATE INDEX idx_task_complexity_task_id ON task_complexity_analysis(task_id);

-- GIN indexes for JSONB columns
CREATE INDEX idx_tasks_requirements ON tasks USING GIN(requirements);
CREATE INDEX idx_tasks_context ON tasks USING GIN(context);
CREATE INDEX idx_tasks_acceptance_criteria ON tasks USING GIN(acceptance_criteria);
CREATE INDEX idx_tasks_affected_files ON tasks USING GIN(affected_files);
CREATE INDEX idx_tasks_tags ON tasks USING GIN(tags);
CREATE INDEX idx_tasks_metadata ON tasks USING GIN(metadata);

-- Text search index for task titles and descriptions
CREATE INDEX idx_tasks_text_search ON tasks USING GIN(to_tsvector('english', title || ' ' || COALESCE(description, '')));

-- Apply updated_at trigger
CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Task management functions

-- Add a new task
CREATE OR REPLACE FUNCTION add_task(
    p_title VARCHAR,
    p_priority task_priority DEFAULT 'medium',
    p_context JSONB DEFAULT '{}',
    p_organization_id UUID DEFAULT NULL,
    p_codebase_id UUID DEFAULT NULL,
    p_parent_task_id UUID DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    new_task_id UUID;
    org_id UUID;
BEGIN
    -- Get organization ID if not provided
    IF p_organization_id IS NULL THEN
        SELECT id INTO org_id FROM organizations WHERE codegen_org_id = '323' LIMIT 1;
    ELSE
        org_id := p_organization_id;
    END IF;
    
    INSERT INTO tasks (
        organization_id, codebase_id, parent_task_id, title, priority, context
    ) VALUES (
        org_id, p_codebase_id, p_parent_task_id, p_title, p_priority, p_context
    ) RETURNING id INTO new_task_id;
    
    -- Log the creation
    INSERT INTO task_execution_log (task_id, event_type, event_data)
    VALUES (new_task_id, 'created', jsonb_build_object('title', p_title, 'priority', p_priority));
    
    RETURN new_task_id;
END;
$$ LANGUAGE plpgsql;

-- Add a subtask
CREATE OR REPLACE FUNCTION add_subtask(
    p_parent_task_id UUID,
    p_title VARCHAR,
    p_priority task_priority DEFAULT 'medium',
    p_context JSONB DEFAULT '{}'
) RETURNS UUID AS $$
DECLARE
    new_task_id UUID;
    org_id UUID;
    codebase_id UUID;
BEGIN
    -- Get parent task info
    SELECT organization_id, tasks.codebase_id INTO org_id, codebase_id
    FROM tasks WHERE id = p_parent_task_id;
    
    IF org_id IS NULL THEN
        RAISE EXCEPTION 'Parent task not found: %', p_parent_task_id;
    END IF;
    
    -- Create the subtask
    INSERT INTO tasks (
        organization_id, codebase_id, parent_task_id, title, priority, context
    ) VALUES (
        org_id, codebase_id, p_parent_task_id, p_title, p_priority, p_context
    ) RETURNING id INTO new_task_id;
    
    -- Add to subtasks relationship
    INSERT INTO task_subtasks (parent_task_id, subtask_id)
    VALUES (p_parent_task_id, new_task_id);
    
    -- Log the creation
    INSERT INTO task_execution_log (task_id, event_type, event_data)
    VALUES (new_task_id, 'created_as_subtask', 
            jsonb_build_object('parent_task_id', p_parent_task_id, 'title', p_title));
    
    RETURN new_task_id;
END;
$$ LANGUAGE plpgsql;

-- Set task status
CREATE OR REPLACE FUNCTION set_task_status(
    p_task_id UUID,
    p_status task_status,
    p_user_id UUID DEFAULT NULL
) RETURNS BOOLEAN AS $$
DECLARE
    old_status task_status;
BEGIN
    -- Get current status
    SELECT status INTO old_status FROM tasks WHERE id = p_task_id;
    
    IF old_status IS NULL THEN
        RAISE EXCEPTION 'Task not found: %', p_task_id;
    END IF;
    
    -- Update status
    UPDATE tasks SET 
        status = p_status,
        started_at = CASE WHEN p_status = 'in_progress' AND started_at IS NULL THEN NOW() ELSE started_at END,
        completed_at = CASE WHEN p_status = 'completed' THEN NOW() ELSE NULL END
    WHERE id = p_task_id;
    
    -- Log the status change
    INSERT INTO task_execution_log (task_id, event_type, event_data, user_id)
    VALUES (p_task_id, 'status_change', 
            jsonb_build_object('old_status', old_status, 'new_status', p_status), p_user_id);
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Analyze task complexity
CREATE OR REPLACE FUNCTION analyze_task_complexity(p_task_id UUID) 
RETURNS JSONB AS $$
DECLARE
    task_record RECORD;
    complexity_score INTEGER;
    risk_level VARCHAR(20);
    factors JSONB;
    result JSONB;
BEGIN
    -- Get task details
    SELECT * INTO task_record FROM tasks WHERE id = p_task_id;
    
    IF task_record IS NULL THEN
        RAISE EXCEPTION 'Task not found: %', p_task_id;
    END IF;
    
    -- Calculate complexity based on various factors
    complexity_score := 1;
    factors := '{}';
    
    -- Factor in description length
    IF LENGTH(task_record.description) > 500 THEN
        complexity_score := complexity_score + 1;
        factors := factors || '{"description_length": "high"}';
    END IF;
    
    -- Factor in number of affected files
    IF jsonb_array_length(task_record.affected_files) > 5 THEN
        complexity_score := complexity_score + 2;
        factors := factors || '{"affected_files": "many"}';
    END IF;
    
    -- Factor in dependencies
    SELECT COUNT(*) INTO complexity_score FROM task_dependencies WHERE task_id = p_task_id;
    IF complexity_score > 3 THEN
        complexity_score := complexity_score + 1;
        factors := factors || '{"dependencies": "high"}';
    END IF;
    
    -- Determine risk level
    CASE 
        WHEN complexity_score <= 2 THEN risk_level := 'low';
        WHEN complexity_score <= 5 THEN risk_level := 'medium';
        WHEN complexity_score <= 8 THEN risk_level := 'high';
        ELSE risk_level := 'critical';
    END CASE;
    
    -- Store analysis
    INSERT INTO task_complexity_analysis (
        task_id, cognitive_complexity, risk_level, factors
    ) VALUES (
        p_task_id, complexity_score, risk_level, factors
    ) ON CONFLICT (task_id) DO UPDATE SET
        cognitive_complexity = EXCLUDED.cognitive_complexity,
        risk_level = EXCLUDED.risk_level,
        factors = EXCLUDED.factors,
        analyzed_at = NOW();
    
    -- Update task complexity score
    UPDATE tasks SET complexity_score = complexity_score WHERE id = p_task_id;
    
    result := jsonb_build_object(
        'complexity_score', complexity_score,
        'risk_level', risk_level,
        'factors', factors
    );
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Get task hierarchy (with all subtasks)
CREATE OR REPLACE FUNCTION expand_all_tasks(p_task_id UUID)
RETURNS TABLE(
    task_id UUID,
    title VARCHAR,
    status task_status,
    priority task_priority,
    level INTEGER,
    path TEXT
) AS $$
WITH RECURSIVE task_hierarchy AS (
    -- Base case: the root task
    SELECT 
        t.id as task_id,
        t.title,
        t.status,
        t.priority,
        0 as level,
        t.title as path
    FROM tasks t
    WHERE t.id = p_task_id
    
    UNION ALL
    
    -- Recursive case: subtasks
    SELECT 
        t.id as task_id,
        t.title,
        t.status,
        t.priority,
        th.level + 1,
        th.path || ' > ' || t.title
    FROM tasks t
    INNER JOIN task_hierarchy th ON t.parent_task_id = th.task_id
)
SELECT * FROM task_hierarchy ORDER BY level, title;
$$ LANGUAGE sql;

-- Check if task has dependencies that are not completed
CREATE OR REPLACE FUNCTION is_task_dependent(p_task_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    blocked_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO blocked_count
    FROM task_dependencies td
    JOIN tasks t ON td.depends_on_task_id = t.id
    WHERE td.task_id = p_task_id 
    AND t.status NOT IN ('completed', 'cancelled');
    
    RETURN blocked_count > 0;
END;
$$ LANGUAGE plpgsql;

-- Find next available task for a user
CREATE OR REPLACE FUNCTION find_next_task(
    p_user_id UUID DEFAULT NULL,
    p_priority task_priority DEFAULT NULL
) RETURNS TABLE(
    task_id UUID,
    title VARCHAR,
    priority task_priority,
    complexity_score INTEGER,
    estimated_hours DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.id,
        t.title,
        t.priority,
        t.complexity_score,
        t.estimated_hours
    FROM tasks t
    WHERE t.status = 'pending'
    AND (p_user_id IS NULL OR t.assigned_to = p_user_id OR t.assigned_to IS NULL)
    AND (p_priority IS NULL OR t.priority = p_priority)
    AND NOT is_task_dependent(t.id)
    ORDER BY 
        CASE t.priority 
            WHEN 'critical' THEN 1
            WHEN 'high' THEN 2
            WHEN 'medium' THEN 3
            WHEN 'low' THEN 4
        END,
        t.created_at
    LIMIT 10;
END;
$$ LANGUAGE plpgsql;

-- Clear all subtasks of a task
CREATE OR REPLACE FUNCTION clear_subtasks(p_task_id UUID)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Delete all subtasks recursively
    WITH RECURSIVE subtask_tree AS (
        SELECT id FROM tasks WHERE parent_task_id = p_task_id
        UNION ALL
        SELECT t.id FROM tasks t
        INNER JOIN subtask_tree st ON t.parent_task_id = st.id
    )
    DELETE FROM tasks WHERE id IN (SELECT id FROM subtask_tree);
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Log the operation
    INSERT INTO task_execution_log (task_id, event_type, event_data)
    VALUES (p_task_id, 'subtasks_cleared', 
            jsonb_build_object('deleted_count', deleted_count));
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- List tasks with filters
CREATE OR REPLACE FUNCTION list_tasks(
    p_organization_id UUID DEFAULT NULL,
    p_status task_status DEFAULT NULL,
    p_priority task_priority DEFAULT NULL,
    p_assigned_to UUID DEFAULT NULL,
    p_limit INTEGER DEFAULT 50,
    p_offset INTEGER DEFAULT 0
) RETURNS TABLE(
    task_id UUID,
    title VARCHAR,
    status task_status,
    priority task_priority,
    assigned_to UUID,
    created_at TIMESTAMP WITH TIME ZONE,
    subtask_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.id,
        t.title,
        t.status,
        t.priority,
        t.assigned_to,
        t.created_at,
        (SELECT COUNT(*) FROM tasks st WHERE st.parent_task_id = t.id) as subtask_count
    FROM tasks t
    WHERE (p_organization_id IS NULL OR t.organization_id = p_organization_id)
    AND (p_status IS NULL OR t.status = p_status)
    AND (p_priority IS NULL OR t.priority = p_priority)
    AND (p_assigned_to IS NULL OR t.assigned_to = p_assigned_to)
    ORDER BY t.created_at DESC
    LIMIT p_limit OFFSET p_offset;
END;
$$ LANGUAGE plpgsql;

COMMENT ON TABLE tasks IS 'Main tasks table with hierarchical support and comprehensive metadata';
COMMENT ON TABLE task_subtasks IS 'Explicit parent-child relationships between tasks';
COMMENT ON TABLE task_dependencies IS 'Complex dependency relationships between tasks';
COMMENT ON TABLE task_files IS 'Files created, modified, or deleted by tasks';
COMMENT ON TABLE task_execution_log IS 'Comprehensive log of all task-related events';
COMMENT ON TABLE task_complexity_analysis IS 'Automated complexity analysis for tasks';

