-- =====================================================
-- TASKS DATABASE SCHEMA
-- Comprehensive task lifecycle management system
-- =====================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =====================================================
-- ENUMS AND TYPES
-- =====================================================

-- Task status enumeration
CREATE TYPE task_status_enum AS ENUM (
    'pending',
    'in_progress', 
    'blocked',
    'review',
    'testing',
    'completed',
    'cancelled',
    'archived'
);

-- Task priority enumeration
CREATE TYPE task_priority_enum AS ENUM (
    'critical',
    'high',
    'medium',
    'low',
    'backlog'
);

-- Dependency type enumeration
CREATE TYPE dependency_type_enum AS ENUM (
    'blocks',
    'depends_on',
    'related_to',
    'duplicates',
    'subtask_of'
);

-- File type enumeration
CREATE TYPE file_type_enum AS ENUM (
    'source_code',
    'documentation',
    'configuration',
    'test',
    'asset',
    'schema',
    'migration',
    'template'
);

-- Complexity level enumeration
CREATE TYPE complexity_level_enum AS ENUM (
    'trivial',
    'simple',
    'moderate',
    'complex',
    'very_complex'
);

-- =====================================================
-- CORE TABLES
-- =====================================================

-- Projects table
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    repository_url VARCHAR(500),
    default_branch VARCHAR(100) DEFAULT 'main',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'developer',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Main tasks table
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status task_status_enum NOT NULL DEFAULT 'pending',
    priority task_priority_enum NOT NULL DEFAULT 'medium',
    complexity_level complexity_level_enum,
    complexity_score INTEGER CHECK (complexity_score >= 0 AND complexity_score <= 100),
    estimated_hours DECIMAL(8,2) CHECK (estimated_hours >= 0),
    actual_hours DECIMAL(8,2) CHECK (actual_hours >= 0),
    progress_percentage INTEGER DEFAULT 0 CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
    
    -- Relationships
    assignee_id UUID REFERENCES users(id),
    project_id UUID REFERENCES projects(id) NOT NULL,
    parent_task_id UUID REFERENCES tasks(id),
    
    -- Metadata
    tags TEXT[],
    labels JSONB,
    custom_fields JSONB,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    due_date TIMESTAMP,
    
    -- Constraints
    CONSTRAINT valid_completion_date CHECK (
        (status = 'completed' AND completed_at IS NOT NULL) OR 
        (status != 'completed' AND completed_at IS NULL)
    ),
    CONSTRAINT valid_progress CHECK (
        (status = 'completed' AND progress_percentage = 100) OR
        (status != 'completed')
    )
);

-- Task dependencies
CREATE TABLE task_dependencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    depends_on_task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    dependency_type dependency_type_enum DEFAULT 'depends_on',
    description TEXT,
    is_critical BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    
    -- Prevent self-dependencies and duplicates
    CONSTRAINT no_self_dependency CHECK (task_id != depends_on_task_id),
    CONSTRAINT unique_dependency UNIQUE(task_id, depends_on_task_id, dependency_type)
);

-- Task files and artifacts
CREATE TABLE task_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    file_path VARCHAR(1000) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_type file_type_enum NOT NULL,
    content TEXT,
    content_hash VARCHAR(64),
    file_size_bytes BIGINT,
    mime_type VARCHAR(100),
    encoding VARCHAR(50) DEFAULT 'utf-8',
    
    -- Version control
    version INTEGER DEFAULT 1,
    is_current_version BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    metadata JSONB,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id)
);

-- Task comments and notes
CREATE TABLE task_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    author_id UUID REFERENCES users(id) NOT NULL,
    content TEXT NOT NULL,
    comment_type VARCHAR(50) DEFAULT 'general',
    is_internal BOOLEAN DEFAULT FALSE,
    parent_comment_id UUID REFERENCES task_comments(id),
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    edited_at TIMESTAMP
);

-- Task time tracking
CREATE TABLE task_time_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) NOT NULL,
    description TEXT,
    hours_worked DECIMAL(8,2) NOT NULL CHECK (hours_worked > 0),
    work_date DATE NOT NULL,
    start_time TIME,
    end_time TIME,
    is_billable BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    activity_type VARCHAR(100),
    metadata JSONB,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Task status history
CREATE TABLE task_status_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    from_status task_status_enum,
    to_status task_status_enum NOT NULL,
    changed_by UUID REFERENCES users(id) NOT NULL,
    reason TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Task assignments history
CREATE TABLE task_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id),
    assigned_by UUID REFERENCES users(id) NOT NULL,
    assignment_type VARCHAR(50) DEFAULT 'assignee',
    is_active BOOLEAN DEFAULT TRUE,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    unassigned_at TIMESTAMP,
    notes TEXT
);

-- Task templates for recurring tasks
CREATE TABLE task_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    title_template VARCHAR(255) NOT NULL,
    description_template TEXT,
    default_priority task_priority_enum DEFAULT 'medium',
    default_complexity_level complexity_level_enum,
    estimated_hours DECIMAL(8,2),
    
    -- Template configuration
    tags TEXT[],
    labels JSONB,
    file_templates JSONB,
    
    -- Metadata
    project_id UUID REFERENCES projects(id),
    created_by UUID REFERENCES users(id),
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

-- Primary lookup indexes
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_priority ON tasks(priority);
CREATE INDEX idx_tasks_assignee ON tasks(assignee_id);
CREATE INDEX idx_tasks_project ON tasks(project_id);
CREATE INDEX idx_tasks_parent ON tasks(parent_task_id);
CREATE INDEX idx_tasks_created_at ON tasks(created_at);
CREATE INDEX idx_tasks_due_date ON tasks(due_date);

-- Composite indexes for common queries
CREATE INDEX idx_tasks_project_status ON tasks(project_id, status);
CREATE INDEX idx_tasks_assignee_status ON tasks(assignee_id, status);
CREATE INDEX idx_tasks_status_priority ON tasks(status, priority);

-- Dependency indexes
CREATE INDEX idx_task_dependencies_task ON task_dependencies(task_id);
CREATE INDEX idx_task_dependencies_depends_on ON task_dependencies(depends_on_task_id);

-- File indexes
CREATE INDEX idx_task_files_task ON task_files(task_id);
CREATE INDEX idx_task_files_type ON task_files(file_type);
CREATE INDEX idx_task_files_path ON task_files(file_path);

-- Comment indexes
CREATE INDEX idx_task_comments_task ON task_comments(task_id);
CREATE INDEX idx_task_comments_author ON task_comments(author_id);
CREATE INDEX idx_task_comments_created ON task_comments(created_at);

-- Time tracking indexes
CREATE INDEX idx_time_entries_task ON task_time_entries(task_id);
CREATE INDEX idx_time_entries_user ON task_time_entries(user_id);
CREATE INDEX idx_time_entries_date ON task_time_entries(work_date);

-- History indexes
CREATE INDEX idx_status_history_task ON task_status_history(task_id);
CREATE INDEX idx_status_history_created ON task_status_history(created_at);

-- Full-text search indexes
CREATE INDEX idx_tasks_title_search ON tasks USING gin(to_tsvector('english', title));
CREATE INDEX idx_tasks_description_search ON tasks USING gin(to_tsvector('english', description));

-- JSONB indexes
CREATE INDEX idx_tasks_labels ON tasks USING gin(labels);
CREATE INDEX idx_tasks_custom_fields ON tasks USING gin(custom_fields);

-- =====================================================
-- TRIGGERS AND FUNCTIONS
-- =====================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at trigger to relevant tables
CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_task_files_updated_at BEFORE UPDATE ON task_files
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_task_comments_updated_at BEFORE UPDATE ON task_comments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to track status changes
CREATE OR REPLACE FUNCTION track_task_status_change()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO task_status_history (task_id, from_status, to_status, changed_by)
        VALUES (NEW.id, OLD.status, NEW.status, NEW.assignee_id);
        
        -- Update completion timestamp
        IF NEW.status = 'completed' THEN
            NEW.completed_at = CURRENT_TIMESTAMP;
            NEW.progress_percentage = 100;
        ELSIF OLD.status = 'completed' AND NEW.status != 'completed' THEN
            NEW.completed_at = NULL;
        END IF;
        
        -- Update started timestamp
        IF OLD.status = 'pending' AND NEW.status = 'in_progress' THEN
            NEW.started_at = CURRENT_TIMESTAMP;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER track_task_status_change_trigger
    BEFORE UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION track_task_status_change();

-- Function to prevent circular dependencies
CREATE OR REPLACE FUNCTION prevent_circular_dependency()
RETURNS TRIGGER AS $$
BEGIN
    -- Check for direct circular dependency
    IF EXISTS (
        SELECT 1 FROM task_dependencies 
        WHERE task_id = NEW.depends_on_task_id 
        AND depends_on_task_id = NEW.task_id
    ) THEN
        RAISE EXCEPTION 'Circular dependency detected: Task % already depends on Task %', 
            NEW.depends_on_task_id, NEW.task_id;
    END IF;
    
    -- Check for indirect circular dependencies using recursive CTE
    WITH RECURSIVE dependency_chain AS (
        SELECT depends_on_task_id as task_id, 1 as depth
        FROM task_dependencies 
        WHERE task_id = NEW.depends_on_task_id
        
        UNION ALL
        
        SELECT td.depends_on_task_id, dc.depth + 1
        FROM task_dependencies td
        JOIN dependency_chain dc ON td.task_id = dc.task_id
        WHERE dc.depth < 10 -- Prevent infinite recursion
    )
    SELECT 1 FROM dependency_chain WHERE task_id = NEW.task_id;
    
    IF FOUND THEN
        RAISE EXCEPTION 'Circular dependency chain detected involving tasks % and %', 
            NEW.task_id, NEW.depends_on_task_id;
    END IF;
    
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER prevent_circular_dependency_trigger
    BEFORE INSERT OR UPDATE ON task_dependencies
    FOR EACH ROW EXECUTE FUNCTION prevent_circular_dependency();

-- =====================================================
-- VIEWS FOR COMMON QUERIES
-- =====================================================

-- Task summary view with calculated fields
CREATE VIEW task_summary AS
SELECT 
    t.id,
    t.title,
    t.status,
    t.priority,
    t.complexity_level,
    t.progress_percentage,
    t.estimated_hours,
    t.actual_hours,
    COALESCE(te.total_logged_hours, 0) as total_logged_hours,
    t.created_at,
    t.due_date,
    u.username as assignee_username,
    p.name as project_name,
    (SELECT COUNT(*) FROM task_dependencies WHERE depends_on_task_id = t.id) as blocking_count,
    (SELECT COUNT(*) FROM task_dependencies WHERE task_id = t.id) as dependency_count,
    (SELECT COUNT(*) FROM tasks WHERE parent_task_id = t.id) as subtask_count,
    CASE 
        WHEN t.due_date < CURRENT_DATE AND t.status NOT IN ('completed', 'cancelled') THEN 'overdue'
        WHEN t.due_date <= CURRENT_DATE + INTERVAL '3 days' AND t.status NOT IN ('completed', 'cancelled') THEN 'due_soon'
        ELSE 'on_track'
    END as due_status
FROM tasks t
LEFT JOIN users u ON t.assignee_id = u.id
LEFT JOIN projects p ON t.project_id = p.id
LEFT JOIN (
    SELECT task_id, SUM(hours_worked) as total_logged_hours
    FROM task_time_entries
    GROUP BY task_id
) te ON t.id = te.task_id;

-- Project dashboard view
CREATE VIEW project_dashboard AS
SELECT 
    p.id,
    p.name,
    COUNT(t.id) as total_tasks,
    COUNT(CASE WHEN t.status = 'completed' THEN 1 END) as completed_tasks,
    COUNT(CASE WHEN t.status = 'in_progress' THEN 1 END) as in_progress_tasks,
    COUNT(CASE WHEN t.status = 'blocked' THEN 1 END) as blocked_tasks,
    ROUND(
        COUNT(CASE WHEN t.status = 'completed' THEN 1 END) * 100.0 / 
        NULLIF(COUNT(t.id), 0), 2
    ) as completion_percentage,
    SUM(t.estimated_hours) as total_estimated_hours,
    SUM(COALESCE(te.total_logged_hours, 0)) as total_logged_hours,
    COUNT(CASE WHEN t.due_date < CURRENT_DATE AND t.status NOT IN ('completed', 'cancelled') THEN 1 END) as overdue_tasks
FROM projects p
LEFT JOIN tasks t ON p.id = t.project_id
LEFT JOIN (
    SELECT task_id, SUM(hours_worked) as total_logged_hours
    FROM task_time_entries
    GROUP BY task_id
) te ON t.id = te.task_id
GROUP BY p.id, p.name;

-- User workload view
CREATE VIEW user_workload AS
SELECT 
    u.id,
    u.username,
    u.full_name,
    COUNT(t.id) as assigned_tasks,
    COUNT(CASE WHEN t.status = 'in_progress' THEN 1 END) as active_tasks,
    COUNT(CASE WHEN t.priority = 'critical' THEN 1 END) as critical_tasks,
    SUM(t.estimated_hours) as total_estimated_hours,
    SUM(COALESCE(te.total_logged_hours, 0)) as total_logged_hours,
    ROUND(AVG(t.complexity_score), 2) as avg_complexity_score
FROM users u
LEFT JOIN tasks t ON u.id = t.assignee_id AND t.status NOT IN ('completed', 'cancelled')
LEFT JOIN (
    SELECT task_id, SUM(hours_worked) as total_logged_hours
    FROM task_time_entries
    GROUP BY task_id
) te ON t.id = te.task_id
GROUP BY u.id, u.username, u.full_name;

-- =====================================================
-- SAMPLE DATA FOR TESTING
-- =====================================================

-- Insert sample projects
INSERT INTO projects (name, description, repository_url) VALUES
('Graph-Sitter Core', 'Core graph-sitter parsing engine', 'https://github.com/example/graph-sitter-core'),
('Analytics Dashboard', 'Code analytics and visualization dashboard', 'https://github.com/example/analytics-dashboard'),
('API Gateway', 'Microservices API gateway', 'https://github.com/example/api-gateway');

-- Insert sample users
INSERT INTO users (username, email, full_name, role) VALUES
('alice.dev', 'alice@example.com', 'Alice Developer', 'senior_developer'),
('bob.eng', 'bob@example.com', 'Bob Engineer', 'developer'),
('carol.lead', 'carol@example.com', 'Carol Lead', 'tech_lead'),
('david.pm', 'david@example.com', 'David Manager', 'project_manager');

-- =====================================================
-- PERFORMANCE MONITORING
-- =====================================================

-- Function to analyze task completion trends
CREATE OR REPLACE FUNCTION get_completion_trends(
    project_id_param UUID DEFAULT NULL,
    days_back INTEGER DEFAULT 30
)
RETURNS TABLE (
    date DATE,
    completed_tasks INTEGER,
    total_hours DECIMAL,
    avg_complexity DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        DATE(t.completed_at) as date,
        COUNT(*)::INTEGER as completed_tasks,
        SUM(t.actual_hours)::DECIMAL as total_hours,
        ROUND(AVG(t.complexity_score), 2)::DECIMAL as avg_complexity
    FROM tasks t
    WHERE t.status = 'completed'
        AND t.completed_at >= CURRENT_DATE - INTERVAL '1 day' * days_back
        AND (project_id_param IS NULL OR t.project_id = project_id_param)
    GROUP BY DATE(t.completed_at)
    ORDER BY date;
END;
$$ LANGUAGE plpgsql;

-- Function to identify bottlenecks
CREATE OR REPLACE FUNCTION identify_bottlenecks()
RETURNS TABLE (
    task_id UUID,
    title VARCHAR,
    days_in_status INTEGER,
    blocking_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.id as task_id,
        t.title,
        (CURRENT_DATE - DATE(t.updated_at))::INTEGER as days_in_status,
        COUNT(td.task_id) as blocking_count
    FROM tasks t
    LEFT JOIN task_dependencies td ON t.id = td.depends_on_task_id
    WHERE t.status IN ('blocked', 'in_progress')
        AND t.updated_at < CURRENT_TIMESTAMP - INTERVAL '3 days'
    GROUP BY t.id, t.title, t.updated_at
    HAVING COUNT(td.task_id) > 0
    ORDER BY blocking_count DESC, days_in_status DESC;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- COMMENTS AND DOCUMENTATION
-- =====================================================

COMMENT ON TABLE tasks IS 'Core task management table with comprehensive lifecycle tracking';
COMMENT ON TABLE task_dependencies IS 'Manages complex task dependency relationships with circular dependency prevention';
COMMENT ON TABLE task_files IS 'Stores task-related files and artifacts with version control';
COMMENT ON TABLE task_time_entries IS 'Time tracking for accurate project estimation and billing';
COMMENT ON TABLE task_status_history IS 'Audit trail for all task status changes';

COMMENT ON COLUMN tasks.complexity_score IS 'Algorithmic complexity score (0-100) for estimation and planning';
COMMENT ON COLUMN tasks.progress_percentage IS 'Manual progress tracking (0-100%)';
COMMENT ON COLUMN task_files.content_hash IS 'SHA-256 hash for file integrity verification';
COMMENT ON COLUMN task_dependencies.is_critical IS 'Indicates if dependency is on critical path';

-- =====================================================
-- GRANTS AND PERMISSIONS
-- =====================================================

-- Create roles for different access levels
-- CREATE ROLE task_admin;
-- CREATE ROLE task_manager;
-- CREATE ROLE task_developer;
-- CREATE ROLE task_viewer;

-- Grant appropriate permissions
-- GRANT ALL ON ALL TABLES IN SCHEMA public TO task_admin;
-- GRANT SELECT, INSERT, UPDATE ON tasks, task_comments, task_time_entries TO task_developer;
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO task_viewer;

