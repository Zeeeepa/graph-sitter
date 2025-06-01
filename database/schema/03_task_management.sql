-- =====================================================
-- Task Management Module
-- Hierarchical task structures with unlimited nesting
-- =====================================================

-- Task types enumeration
CREATE TYPE task_type AS ENUM (
    'epic', 'feature', 'story', 'task', 'bug', 'research', 
    'documentation', 'testing', 'deployment', 'maintenance'
);

-- Task status enumeration
CREATE TYPE task_status AS ENUM (
    'backlog', 'todo', 'in_progress', 'in_review', 
    'testing', 'done', 'cancelled', 'blocked'
);

-- Task priority enumeration
CREATE TYPE task_priority AS ENUM (
    'critical', 'high', 'medium', 'low', 'none'
);

-- Main tasks table with hierarchical support
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    parent_task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    type task_type NOT NULL DEFAULT 'task',
    status task_status NOT NULL DEFAULT 'backlog',
    priority task_priority NOT NULL DEFAULT 'medium',
    assignee_id UUID REFERENCES users(id) ON DELETE SET NULL,
    reporter_id UUID REFERENCES users(id) ON DELETE SET NULL,
    external_refs JSONB DEFAULT '{}', -- Linear, GitHub issue refs
    metadata JSONB DEFAULT '{}',
    labels JSONB DEFAULT '[]',
    estimated_effort INTEGER, -- story points or hours
    actual_effort INTEGER,
    progress_percentage INTEGER DEFAULT 0,
    due_date TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_progress CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
    CONSTRAINT valid_effort CHECK (estimated_effort >= 0 AND actual_effort >= 0),
    CONSTRAINT no_self_parent CHECK (id != parent_task_id)
);

-- Task dependencies using adjacency list pattern
CREATE TABLE task_dependencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    dependent_task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    dependency_task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    dependency_type VARCHAR(50) DEFAULT 'blocks',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    
    UNIQUE(dependent_task_id, dependency_task_id),
    CONSTRAINT no_self_dependency CHECK (dependent_task_id != dependency_task_id),
    CONSTRAINT valid_dependency_type CHECK (dependency_type IN ('blocks', 'relates_to', 'duplicates', 'subtask_of'))
);

-- Materialized path for efficient hierarchy queries
CREATE TABLE task_hierarchy_paths (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    ancestor_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    depth INTEGER NOT NULL,
    path TEXT NOT NULL, -- materialized path like '/uuid1/uuid2/uuid3'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(task_id, ancestor_id),
    CONSTRAINT valid_depth CHECK (depth >= 0)
);

-- Task comments and activity
CREATE TABLE task_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    comment_type VARCHAR(50) DEFAULT 'comment',
    metadata JSONB DEFAULT '{}',
    edited_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_comment_type CHECK (comment_type IN ('comment', 'status_change', 'assignment', 'system'))
);

-- Task attachments
CREATE TABLE task_attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_size INTEGER NOT NULL,
    mime_type VARCHAR(100),
    storage_path TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_file_size CHECK (file_size > 0)
);

-- Task time tracking
CREATE TABLE task_time_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    description TEXT,
    duration_minutes INTEGER NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    ended_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_duration CHECK (duration_minutes > 0),
    CONSTRAINT valid_time_range CHECK (ended_at IS NULL OR ended_at > started_at)
);

-- Task watchers/subscribers
CREATE TABLE task_watchers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    notification_preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(task_id, user_id)
);

-- =====================================================
-- Row-Level Security
-- =====================================================

ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_dependencies ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_hierarchy_paths ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_attachments ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_time_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_watchers ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY tenant_isolation_tasks ON tasks
    USING (organization_id = get_current_tenant());

CREATE POLICY tenant_isolation_task_dependencies ON task_dependencies
    USING (organization_id = get_current_tenant());

CREATE POLICY tenant_isolation_task_hierarchy_paths ON task_hierarchy_paths
    USING (organization_id = get_current_tenant());

CREATE POLICY tenant_isolation_task_comments ON task_comments
    USING (organization_id = get_current_tenant());

CREATE POLICY tenant_isolation_task_attachments ON task_attachments
    USING (organization_id = get_current_tenant());

CREATE POLICY tenant_isolation_task_time_entries ON task_time_entries
    USING (organization_id = get_current_tenant());

CREATE POLICY tenant_isolation_task_watchers ON task_watchers
    USING (organization_id = get_current_tenant());

-- =====================================================
-- Indexes for Performance
-- =====================================================

-- Tasks
CREATE INDEX idx_tasks_org_project ON tasks(organization_id, project_id);
CREATE INDEX idx_tasks_org_status ON tasks(organization_id, status);
CREATE INDEX idx_tasks_org_assignee ON tasks(organization_id, assignee_id);
CREATE INDEX idx_tasks_org_parent ON tasks(organization_id, parent_task_id);
CREATE INDEX idx_tasks_type_status ON tasks(type, status);
CREATE INDEX idx_tasks_priority_due ON tasks(priority, due_date);
CREATE INDEX idx_tasks_external_refs ON tasks USING GIN (external_refs);
CREATE INDEX idx_tasks_labels ON tasks USING GIN (labels);
CREATE INDEX idx_tasks_search ON tasks USING GIN (to_tsvector('english', title || ' ' || COALESCE(description, '')));

-- Task Dependencies
CREATE INDEX idx_task_deps_dependent ON task_dependencies(dependent_task_id);
CREATE INDEX idx_task_deps_dependency ON task_dependencies(dependency_task_id);
CREATE INDEX idx_task_deps_type ON task_dependencies(dependency_type);

-- Task Hierarchy Paths
CREATE INDEX idx_task_hierarchy_task ON task_hierarchy_paths(task_id);
CREATE INDEX idx_task_hierarchy_ancestor ON task_hierarchy_paths(ancestor_id);
CREATE INDEX idx_task_hierarchy_depth ON task_hierarchy_paths(depth);
CREATE INDEX idx_task_hierarchy_path ON task_hierarchy_paths(path);

-- Task Comments
CREATE INDEX idx_task_comments_task_created ON task_comments(task_id, created_at);
CREATE INDEX idx_task_comments_user ON task_comments(user_id);
CREATE INDEX idx_task_comments_type ON task_comments(comment_type);

-- Task Time Entries
CREATE INDEX idx_task_time_entries_task ON task_time_entries(task_id);
CREATE INDEX idx_task_time_entries_user_started ON task_time_entries(user_id, started_at);

-- Task Watchers
CREATE INDEX idx_task_watchers_task ON task_watchers(task_id);
CREATE INDEX idx_task_watchers_user ON task_watchers(user_id);

-- =====================================================
-- Functions for Task Management
-- =====================================================

-- Function to rebuild hierarchy paths for a task
CREATE OR REPLACE FUNCTION rebuild_task_hierarchy_paths(task_id UUID)
RETURNS void AS $$
DECLARE
    current_task_id UUID := task_id;
    current_depth INTEGER := 0;
    path_text TEXT := '';
    ancestor_id UUID;
BEGIN
    -- Delete existing paths for this task
    DELETE FROM task_hierarchy_paths WHERE task_hierarchy_paths.task_id = rebuild_task_hierarchy_paths.task_id;
    
    -- Build path from root to current task
    WHILE current_task_id IS NOT NULL LOOP
        path_text := '/' || current_task_id || path_text;
        
        -- Insert path entry for each ancestor
        FOR ancestor_id IN 
            SELECT unnest(string_to_array(trim(leading '/' from path_text), '/'))::UUID
        LOOP
            IF ancestor_id != rebuild_task_hierarchy_paths.task_id THEN
                INSERT INTO task_hierarchy_paths (
                    organization_id, task_id, ancestor_id, depth, path
                ) VALUES (
                    get_current_tenant(),
                    rebuild_task_hierarchy_paths.task_id,
                    ancestor_id,
                    current_depth,
                    path_text
                ) ON CONFLICT (task_id, ancestor_id) DO NOTHING;
            END IF;
        END LOOP;
        
        -- Move to parent
        SELECT parent_task_id INTO current_task_id 
        FROM tasks 
        WHERE id = current_task_id;
        
        current_depth := current_depth + 1;
        
        -- Prevent infinite loops
        IF current_depth > 50 THEN
            RAISE EXCEPTION 'Task hierarchy too deep (possible cycle detected)';
        END IF;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Function to check for circular dependencies
CREATE OR REPLACE FUNCTION check_circular_dependency(
    dependent_id UUID,
    dependency_id UUID
) RETURNS BOOLEAN AS $$
DECLARE
    has_cycle BOOLEAN := false;
BEGIN
    -- Check if adding this dependency would create a cycle
    WITH RECURSIVE dependency_chain AS (
        -- Start with the proposed dependency
        SELECT dependency_id as task_id, 1 as depth
        
        UNION ALL
        
        -- Follow the chain of dependencies
        SELECT td.dependency_task_id, dc.depth + 1
        FROM dependency_chain dc
        JOIN task_dependencies td ON dc.task_id = td.dependent_task_id
        WHERE dc.depth < 50 -- Prevent infinite recursion
    )
    SELECT EXISTS(
        SELECT 1 FROM dependency_chain 
        WHERE task_id = dependent_id
    ) INTO has_cycle;
    
    RETURN has_cycle;
END;
$$ LANGUAGE plpgsql;

-- Function to get task descendants
CREATE OR REPLACE FUNCTION get_task_descendants(task_id UUID)
RETURNS TABLE(descendant_id UUID, depth INTEGER) AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE task_tree AS (
        -- Start with the given task
        SELECT id, 0 as depth
        FROM tasks
        WHERE id = task_id AND organization_id = get_current_tenant()
        
        UNION ALL
        
        -- Get all children recursively
        SELECT t.id, tt.depth + 1
        FROM tasks t
        JOIN task_tree tt ON t.parent_task_id = tt.id
        WHERE t.organization_id = get_current_tenant()
        AND tt.depth < 50 -- Prevent infinite recursion
    )
    SELECT id, depth FROM task_tree WHERE depth > 0;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate task completion percentage
CREATE OR REPLACE FUNCTION calculate_task_completion(task_id UUID)
RETURNS INTEGER AS $$
DECLARE
    total_subtasks INTEGER;
    completed_subtasks INTEGER;
    completion_percentage INTEGER;
BEGIN
    -- Count total and completed subtasks
    SELECT 
        COUNT(*),
        COUNT(*) FILTER (WHERE status = 'done')
    INTO total_subtasks, completed_subtasks
    FROM tasks
    WHERE parent_task_id = task_id 
    AND organization_id = get_current_tenant();
    
    -- If no subtasks, return current progress
    IF total_subtasks = 0 THEN
        SELECT progress_percentage INTO completion_percentage
        FROM tasks 
        WHERE id = task_id;
        RETURN COALESCE(completion_percentage, 0);
    END IF;
    
    -- Calculate percentage based on subtasks
    completion_percentage := (completed_subtasks * 100) / total_subtasks;
    
    -- Update the task's progress
    UPDATE tasks 
    SET progress_percentage = completion_percentage,
        updated_at = NOW()
    WHERE id = task_id;
    
    RETURN completion_percentage;
END;
$$ LANGUAGE plpgsql;

-- Function to get task statistics
CREATE OR REPLACE FUNCTION get_task_stats(task_id UUID)
RETURNS JSONB AS $$
DECLARE
    stats JSONB;
BEGIN
    SELECT jsonb_build_object(
        'total_subtasks', COUNT(DISTINCT t.id),
        'completed_subtasks', COUNT(DISTINCT t.id) FILTER (WHERE t.status = 'done'),
        'total_dependencies', COUNT(DISTINCT td.id),
        'blocked_dependencies', COUNT(DISTINCT td.id) FILTER (WHERE dep_task.status != 'done'),
        'total_comments', COUNT(DISTINCT tc.id),
        'total_time_logged', COALESCE(SUM(tte.duration_minutes), 0),
        'watchers_count', COUNT(DISTINCT tw.id)
    ) INTO stats
    FROM tasks main_task
    LEFT JOIN tasks t ON main_task.id = t.parent_task_id
    LEFT JOIN task_dependencies td ON main_task.id = td.dependent_task_id
    LEFT JOIN tasks dep_task ON td.dependency_task_id = dep_task.id
    LEFT JOIN task_comments tc ON main_task.id = tc.task_id
    LEFT JOIN task_time_entries tte ON main_task.id = tte.task_id
    LEFT JOIN task_watchers tw ON main_task.id = tw.task_id
    WHERE main_task.id = task_id 
    AND main_task.organization_id = get_current_tenant();
    
    RETURN stats;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- Triggers
-- =====================================================

-- Update timestamp triggers
CREATE TRIGGER update_tasks_updated_at 
    BEFORE UPDATE ON tasks 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger to maintain hierarchy paths
CREATE OR REPLACE FUNCTION maintain_task_hierarchy()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' OR (TG_OP = 'UPDATE' AND OLD.parent_task_id IS DISTINCT FROM NEW.parent_task_id) THEN
        -- Rebuild hierarchy paths for the affected task
        PERFORM rebuild_task_hierarchy_paths(NEW.id);
        
        -- Also rebuild for all descendants
        PERFORM rebuild_task_hierarchy_paths(descendant_id)
        FROM get_task_descendants(NEW.id);
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER maintain_task_hierarchy_trigger
    AFTER INSERT OR UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION maintain_task_hierarchy();

-- Trigger to prevent circular dependencies
CREATE OR REPLACE FUNCTION prevent_circular_dependencies()
RETURNS TRIGGER AS $$
BEGIN
    IF check_circular_dependency(NEW.dependent_task_id, NEW.dependency_task_id) THEN
        RAISE EXCEPTION 'Adding this dependency would create a circular dependency';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER prevent_circular_dependencies_trigger
    BEFORE INSERT OR UPDATE ON task_dependencies
    FOR EACH ROW EXECUTE FUNCTION prevent_circular_dependencies();

-- Trigger to auto-update parent task completion
CREATE OR REPLACE FUNCTION update_parent_completion()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'UPDATE' AND OLD.status IS DISTINCT FROM NEW.status THEN
        IF NEW.parent_task_id IS NOT NULL THEN
            PERFORM calculate_task_completion(NEW.parent_task_id);
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_parent_completion_trigger
    AFTER UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION update_parent_completion();

-- Audit triggers
CREATE TRIGGER audit_tasks 
    AFTER INSERT OR UPDATE OR DELETE ON tasks
    FOR EACH ROW EXECUTE FUNCTION create_audit_log();

-- =====================================================
-- Views for Common Queries
-- =====================================================

-- Task summary view with aggregated data
CREATE VIEW task_summary AS
SELECT 
    t.id,
    t.organization_id,
    t.title,
    t.type,
    t.status,
    t.priority,
    t.assignee_id,
    u.name as assignee_name,
    t.parent_task_id,
    parent.title as parent_title,
    t.progress_percentage,
    t.estimated_effort,
    t.actual_effort,
    t.due_date,
    COUNT(DISTINCT subtasks.id) as subtask_count,
    COUNT(DISTINCT tc.id) as comment_count,
    COALESCE(SUM(tte.duration_minutes), 0) as total_time_logged,
    t.created_at,
    t.updated_at
FROM tasks t
LEFT JOIN users u ON t.assignee_id = u.id
LEFT JOIN tasks parent ON t.parent_task_id = parent.id
LEFT JOIN tasks subtasks ON t.id = subtasks.parent_task_id
LEFT JOIN task_comments tc ON t.id = tc.task_id
LEFT JOIN task_time_entries tte ON t.id = tte.task_id
GROUP BY t.id, u.id, parent.id;

