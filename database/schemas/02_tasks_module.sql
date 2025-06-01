-- =============================================================================
-- TASKS MODULE: Task lifecycle management and workflow orchestration
-- =============================================================================
-- This module handles task definitions, execution tracking, dependencies,
-- workflows, and resource monitoring.
-- =============================================================================

-- Task status enumeration
CREATE TYPE task_status AS ENUM (
    'pending',
    'running',
    'completed',
    'failed',
    'cancelled',
    'retrying',
    'paused'
);

-- Task types
CREATE TYPE task_type AS ENUM (
    'code_analysis',
    'code_generation',
    'testing',
    'deployment',
    'workflow',
    'notification',
    'custom'
);

-- Workflow execution types
CREATE TYPE workflow_execution_type AS ENUM (
    'sequential',
    'parallel',
    'conditional',
    'loop',
    'dag'
);

-- =============================================================================
-- TASK DEFINITIONS TABLE
-- =============================================================================

CREATE TABLE task_definitions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    task_type task_type NOT NULL,
    
    -- Template configuration
    default_configuration JSONB DEFAULT '{}',
    parameter_schema JSONB DEFAULT '{}', -- JSON Schema for validation
    
    -- Resource requirements
    cpu_cores DECIMAL(3,1) DEFAULT 1.0,
    memory_mb INTEGER DEFAULT 512,
    disk_mb INTEGER DEFAULT 1024,
    timeout_seconds INTEGER DEFAULT 3600,
    
    -- Retry configuration
    max_retries INTEGER DEFAULT 3,
    retry_delay_seconds INTEGER DEFAULT 60,
    retry_backoff_multiplier DECIMAL(3,2) DEFAULT 2.0,
    
    -- Metadata
    version VARCHAR(50) DEFAULT '1.0.0',
    tags VARCHAR(50)[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT task_definitions_name_not_empty CHECK (length(trim(name)) > 0),
    CONSTRAINT task_definitions_cpu_positive CHECK (cpu_cores > 0),
    CONSTRAINT task_definitions_memory_positive CHECK (memory_mb > 0),
    CONSTRAINT task_definitions_timeout_positive CHECK (timeout_seconds > 0),
    CONSTRAINT task_definitions_retries_positive CHECK (max_retries >= 0)
);

-- =============================================================================
-- TASKS TABLE
-- =============================================================================

CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    task_definition_id UUID REFERENCES task_definitions(id),
    
    -- Basic task information
    name VARCHAR(255) NOT NULL,
    description TEXT,
    task_type task_type NOT NULL,
    status task_status DEFAULT 'pending',
    priority priority_level DEFAULT 'normal',
    
    -- Execution details
    created_by UUID NOT NULL REFERENCES users(id),
    assigned_to UUID REFERENCES users(id),
    
    -- Scheduling
    scheduled_at TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Configuration and results
    configuration JSONB DEFAULT '{}',
    result JSONB,
    error_message TEXT,
    error_details JSONB,
    
    -- Retry logic
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    retry_delay_seconds INTEGER DEFAULT 60,
    next_retry_at TIMESTAMP WITH TIME ZONE,
    
    -- Resource tracking
    estimated_duration_seconds INTEGER,
    actual_duration_seconds INTEGER,
    cpu_usage_percent DECIMAL(5,2),
    memory_usage_mb INTEGER,
    
    -- Dependencies
    depends_on UUID[] DEFAULT '{}',
    blocks UUID[] DEFAULT '{}',
    
    -- Context
    project_id UUID REFERENCES projects(id),
    repository_id UUID REFERENCES repositories(id),
    workflow_id UUID, -- Will reference workflows table
    parent_task_id UUID REFERENCES tasks(id),
    
    -- Metadata
    tags VARCHAR(50)[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT tasks_name_not_empty CHECK (length(trim(name)) > 0),
    CONSTRAINT tasks_retries_positive CHECK (retry_count >= 0 AND max_retries >= 0),
    CONSTRAINT tasks_duration_positive CHECK (
        estimated_duration_seconds IS NULL OR estimated_duration_seconds > 0
    ),
    CONSTRAINT tasks_actual_duration_positive CHECK (
        actual_duration_seconds IS NULL OR actual_duration_seconds >= 0
    ),
    CONSTRAINT tasks_cpu_usage_valid CHECK (
        cpu_usage_percent IS NULL OR (cpu_usage_percent >= 0 AND cpu_usage_percent <= 100)
    ),
    CONSTRAINT tasks_memory_usage_positive CHECK (
        memory_usage_mb IS NULL OR memory_usage_mb >= 0
    )
);

-- =============================================================================
-- TASK DEPENDENCIES TABLE
-- =============================================================================

CREATE TABLE task_dependencies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    depends_on_task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    dependency_type VARCHAR(50) DEFAULT 'completion', -- completion, success, failure
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT task_dependencies_unique UNIQUE (task_id, depends_on_task_id),
    CONSTRAINT task_dependencies_no_self_reference CHECK (task_id != depends_on_task_id),
    CONSTRAINT task_dependencies_type_valid CHECK (
        dependency_type IN ('completion', 'success', 'failure')
    )
);

-- =============================================================================
-- WORKFLOWS TABLE
-- =============================================================================

CREATE TABLE workflows (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Workflow configuration
    execution_type workflow_execution_type DEFAULT 'sequential',
    configuration JSONB DEFAULT '{}',
    
    -- Workflow status
    status task_status DEFAULT 'pending',
    current_step INTEGER DEFAULT 0,
    total_steps INTEGER DEFAULT 0,
    
    -- Execution details
    created_by UUID NOT NULL REFERENCES users(id),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Results
    result JSONB,
    error_message TEXT,
    
    -- Context
    project_id UUID REFERENCES projects(id),
    repository_id UUID REFERENCES repositories(id),
    parent_workflow_id UUID REFERENCES workflows(id),
    
    -- Metadata
    version VARCHAR(50) DEFAULT '1.0.0',
    tags VARCHAR(50)[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT workflows_name_not_empty CHECK (length(trim(name)) > 0),
    CONSTRAINT workflows_steps_positive CHECK (total_steps >= 0),
    CONSTRAINT workflows_current_step_valid CHECK (current_step >= 0 AND current_step <= total_steps)
);

-- Add foreign key reference from tasks to workflows
ALTER TABLE tasks ADD CONSTRAINT tasks_workflow_fk 
    FOREIGN KEY (workflow_id) REFERENCES workflows(id);

-- =============================================================================
-- WORKFLOW STEPS TABLE
-- =============================================================================

CREATE TABLE workflow_steps (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    step_order INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Step configuration
    step_type VARCHAR(100) NOT NULL, -- analysis, quality_gate, testing, build, deployment, etc.
    configuration JSONB DEFAULT '{}',
    
    -- Dependencies within workflow
    depends_on_steps UUID[] DEFAULT '{}',
    
    -- Conditional execution
    condition_expression TEXT, -- Expression to evaluate for conditional execution
    
    -- Status tracking
    status task_status DEFAULT 'pending',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    result JSONB,
    error_message TEXT,
    
    -- Retry configuration
    max_retries INTEGER DEFAULT 3,
    retry_count INTEGER DEFAULT 0,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT workflow_steps_name_not_empty CHECK (length(trim(name)) > 0),
    CONSTRAINT workflow_steps_order_positive CHECK (step_order > 0),
    CONSTRAINT workflow_steps_unique_order UNIQUE (workflow_id, step_order),
    CONSTRAINT workflow_steps_retries_positive CHECK (retry_count >= 0 AND max_retries >= 0)
);

-- =============================================================================
-- TASK EXECUTION LOGS TABLE
-- =============================================================================

CREATE TABLE task_execution_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    execution_number INTEGER DEFAULT 1,
    
    -- Log details
    log_level VARCHAR(20) DEFAULT 'info', -- debug, info, warning, error, critical
    message TEXT NOT NULL,
    details JSONB,
    
    -- Context
    component VARCHAR(100), -- Which component generated the log
    function_name VARCHAR(100),
    line_number INTEGER,
    
    -- Timestamp
    logged_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT task_logs_level_valid CHECK (
        log_level IN ('debug', 'info', 'warning', 'error', 'critical')
    ),
    CONSTRAINT task_logs_message_not_empty CHECK (length(trim(message)) > 0),
    CONSTRAINT task_logs_execution_positive CHECK (execution_number > 0)
);

-- =============================================================================
-- TASK RESOURCE USAGE TABLE
-- =============================================================================

CREATE TABLE task_resource_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    
    -- Resource measurements
    cpu_usage_percent DECIMAL(5,2),
    memory_usage_mb INTEGER,
    disk_usage_mb INTEGER,
    network_io_mb DECIMAL(10,2),
    
    -- Timing
    measured_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    duration_seconds INTEGER,
    
    -- Metadata
    measurement_source VARCHAR(100), -- system, docker, kubernetes, etc.
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT resource_usage_cpu_valid CHECK (
        cpu_usage_percent IS NULL OR (cpu_usage_percent >= 0 AND cpu_usage_percent <= 100)
    ),
    CONSTRAINT resource_usage_memory_positive CHECK (
        memory_usage_mb IS NULL OR memory_usage_mb >= 0
    ),
    CONSTRAINT resource_usage_disk_positive CHECK (
        disk_usage_mb IS NULL OR disk_usage_mb >= 0
    ),
    CONSTRAINT resource_usage_duration_positive CHECK (
        duration_seconds IS NULL OR duration_seconds >= 0
    )
);

-- =============================================================================
-- TRIGGERS
-- =============================================================================

-- Update timestamps
CREATE TRIGGER update_task_definitions_updated_at 
    BEFORE UPDATE ON task_definitions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tasks_updated_at 
    BEFORE UPDATE ON tasks 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_workflows_updated_at 
    BEFORE UPDATE ON workflows 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_workflow_steps_updated_at 
    BEFORE UPDATE ON workflow_steps 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- INDEXES
-- =============================================================================

-- Task definitions indexes
CREATE INDEX idx_task_definitions_org_id ON task_definitions(organization_id);
CREATE INDEX idx_task_definitions_type ON task_definitions(task_type);
CREATE INDEX idx_task_definitions_active ON task_definitions(is_active) WHERE deleted_at IS NULL;

-- Tasks indexes
CREATE INDEX idx_tasks_organization_id ON tasks(organization_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_priority ON tasks(priority);
CREATE INDEX idx_tasks_created_by ON tasks(created_by);
CREATE INDEX idx_tasks_assigned_to ON tasks(assigned_to);
CREATE INDEX idx_tasks_scheduled_at ON tasks(scheduled_at);
CREATE INDEX idx_tasks_project_id ON tasks(project_id);
CREATE INDEX idx_tasks_repository_id ON tasks(repository_id);
CREATE INDEX idx_tasks_workflow_id ON tasks(workflow_id);
CREATE INDEX idx_tasks_parent_task_id ON tasks(parent_task_id);
CREATE INDEX idx_tasks_depends_on ON tasks USING GIN(depends_on);
CREATE INDEX idx_tasks_tags ON tasks USING GIN(tags);

-- Task dependencies indexes
CREATE INDEX idx_task_dependencies_task_id ON task_dependencies(task_id);
CREATE INDEX idx_task_dependencies_depends_on ON task_dependencies(depends_on_task_id);
CREATE INDEX idx_task_dependencies_type ON task_dependencies(dependency_type);

-- Workflows indexes
CREATE INDEX idx_workflows_organization_id ON workflows(organization_id);
CREATE INDEX idx_workflows_status ON workflows(status);
CREATE INDEX idx_workflows_created_by ON workflows(created_by);
CREATE INDEX idx_workflows_project_id ON workflows(project_id);
CREATE INDEX idx_workflows_repository_id ON workflows(repository_id);

-- Workflow steps indexes
CREATE INDEX idx_workflow_steps_workflow_id ON workflow_steps(workflow_id);
CREATE INDEX idx_workflow_steps_order ON workflow_steps(workflow_id, step_order);
CREATE INDEX idx_workflow_steps_status ON workflow_steps(status);

-- Task execution logs indexes
CREATE INDEX idx_task_logs_task_id ON task_execution_logs(task_id);
CREATE INDEX idx_task_logs_level ON task_execution_logs(log_level);
CREATE INDEX idx_task_logs_logged_at ON task_execution_logs(logged_at);

-- Task resource usage indexes
CREATE INDEX idx_resource_usage_task_id ON task_resource_usage(task_id);
CREATE INDEX idx_resource_usage_measured_at ON task_resource_usage(measured_at);

-- =============================================================================
-- VIEWS
-- =============================================================================

-- Ready tasks view
CREATE VIEW ready_tasks AS
SELECT t.*
FROM tasks t
WHERE t.status = 'pending'
  AND (t.scheduled_at IS NULL OR t.scheduled_at <= CURRENT_TIMESTAMP)
  AND NOT EXISTS (
      SELECT 1 FROM task_dependencies td
      JOIN tasks dt ON td.depends_on_task_id = dt.id
      WHERE td.task_id = t.id
        AND (
          (td.dependency_type = 'completion' AND dt.status NOT IN ('completed', 'failed', 'cancelled'))
          OR (td.dependency_type = 'success' AND dt.status != 'completed')
          OR (td.dependency_type = 'failure' AND dt.status != 'failed')
        )
  );

-- Task summary view
CREATE VIEW task_summary AS
SELECT 
    t.id,
    t.name,
    t.task_type,
    t.status,
    t.priority,
    t.created_by,
    u.name as created_by_name,
    t.assigned_to,
    au.name as assigned_to_name,
    t.created_at,
    t.started_at,
    t.completed_at,
    CASE 
        WHEN t.completed_at IS NOT NULL AND t.started_at IS NOT NULL 
        THEN EXTRACT(EPOCH FROM (t.completed_at - t.started_at))
        ELSE NULL 
    END as duration_seconds,
    p.name as project_name,
    r.name as repository_name
FROM tasks t
JOIN users u ON t.created_by = u.id
LEFT JOIN users au ON t.assigned_to = au.id
LEFT JOIN projects p ON t.project_id = p.id
LEFT JOIN repositories r ON t.repository_id = r.id;

-- Workflow progress view
CREATE VIEW workflow_progress AS
SELECT 
    w.id,
    w.name,
    w.status,
    w.current_step,
    w.total_steps,
    CASE 
        WHEN w.total_steps > 0 
        THEN ROUND((w.current_step::DECIMAL / w.total_steps) * 100, 2)
        ELSE 0 
    END as progress_percent,
    w.created_at,
    w.started_at,
    w.completed_at,
    COUNT(ws.id) as actual_steps,
    COUNT(CASE WHEN ws.status = 'completed' THEN 1 END) as completed_steps,
    COUNT(CASE WHEN ws.status = 'failed' THEN 1 END) as failed_steps
FROM workflows w
LEFT JOIN workflow_steps ws ON w.id = ws.workflow_id
GROUP BY w.id, w.name, w.status, w.current_step, w.total_steps, 
         w.created_at, w.started_at, w.completed_at;

-- =============================================================================
-- FUNCTIONS
-- =============================================================================

-- Function to check if task dependencies are satisfied
CREATE OR REPLACE FUNCTION are_task_dependencies_satisfied(task_uuid UUID)
RETURNS BOOLEAN AS $$
DECLARE
    unsatisfied_count INTEGER;
BEGIN
    SELECT COUNT(*)
    INTO unsatisfied_count
    FROM task_dependencies td
    JOIN tasks dt ON td.depends_on_task_id = dt.id
    WHERE td.task_id = task_uuid
      AND (
        (td.dependency_type = 'completion' AND dt.status NOT IN ('completed', 'failed', 'cancelled'))
        OR (td.dependency_type = 'success' AND dt.status != 'completed')
        OR (td.dependency_type = 'failure' AND dt.status != 'failed')
      );
    
    RETURN unsatisfied_count = 0;
END;
$$ LANGUAGE plpgsql;

-- Function to detect circular dependencies
CREATE OR REPLACE FUNCTION detect_circular_dependency(task_uuid UUID, depends_on_uuid UUID)
RETURNS BOOLEAN AS $$
WITH RECURSIVE dependency_chain AS (
    -- Base case: direct dependency
    SELECT depends_on_task_id as task_id, 1 as depth
    FROM task_dependencies 
    WHERE task_id = depends_on_uuid
    
    UNION ALL
    
    -- Recursive case: follow the chain
    SELECT td.depends_on_task_id, dc.depth + 1
    FROM task_dependencies td
    JOIN dependency_chain dc ON td.task_id = dc.task_id
    WHERE dc.depth < 100 -- Prevent infinite recursion
)
SELECT EXISTS (
    SELECT 1 FROM dependency_chain 
    WHERE task_id = task_uuid
);
$$ LANGUAGE sql;

-- Function to get task statistics
CREATE OR REPLACE FUNCTION get_task_statistics(org_uuid UUID DEFAULT NULL)
RETURNS JSONB AS $$
DECLARE
    result JSONB;
    total_tasks INTEGER;
    completed_tasks INTEGER;
    failed_tasks INTEGER;
    avg_duration DECIMAL;
BEGIN
    SELECT 
        COUNT(*),
        COUNT(CASE WHEN status = 'completed' THEN 1 END),
        COUNT(CASE WHEN status = 'failed' THEN 1 END),
        AVG(actual_duration_seconds)
    INTO total_tasks, completed_tasks, failed_tasks, avg_duration
    FROM tasks
    WHERE (org_uuid IS NULL OR organization_id = org_uuid);
    
    result := jsonb_build_object(
        'total_tasks', COALESCE(total_tasks, 0),
        'completed_tasks', COALESCE(completed_tasks, 0),
        'failed_tasks', COALESCE(failed_tasks, 0),
        'success_rate', CASE 
            WHEN total_tasks > 0 
            THEN ROUND((completed_tasks::DECIMAL / total_tasks) * 100, 2)
            ELSE 0 
        END,
        'average_duration_seconds', COALESCE(avg_duration, 0),
        'calculated_at', CURRENT_TIMESTAMP
    );
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Record this migration
INSERT INTO schema_migrations (version, description) VALUES 
('02_tasks_module', 'Tasks module with task management, workflows, and execution tracking');

