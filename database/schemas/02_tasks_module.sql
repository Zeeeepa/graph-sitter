-- =============================================================================
-- TASKS MODULE SCHEMA
-- =============================================================================
-- This module handles task lifecycle management with flexible JSONB metadata,
-- execution tracking, resource usage monitoring, dependency management, and
-- workflow orchestration.
-- =============================================================================

-- =============================================================================
-- ENUMS
-- =============================================================================

CREATE TYPE task_status AS ENUM (
    'pending',
    'queued',
    'running',
    'paused',
    'completed',
    'failed',
    'cancelled',
    'timeout',
    'retrying'
);

CREATE TYPE task_type AS ENUM (
    'analysis',
    'generation',
    'refactoring',
    'testing',
    'deployment',
    'monitoring',
    'custom'
);

CREATE TYPE execution_environment AS ENUM (
    'local',
    'docker',
    'kubernetes',
    'cloud',
    'sandbox'
);

CREATE TYPE dependency_type AS ENUM (
    'hard',      -- Must complete before this task can start
    'soft',      -- Should complete before, but not required
    'resource',  -- Shares resources, coordinate execution
    'data'       -- Provides data input
);

-- =============================================================================
-- TASKS TABLES
-- =============================================================================

-- Task definitions - reusable task templates
CREATE TABLE task_definitions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Definition metadata
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) NOT NULL,
    description TEXT,
    version VARCHAR(20) DEFAULT '1.0.0',
    
    -- Task configuration
    task_type task_type NOT NULL,
    default_timeout_seconds INTEGER DEFAULT 3600,
    max_retries INTEGER DEFAULT 3,
    retry_delay_seconds INTEGER DEFAULT 60,
    
    -- Resource requirements
    cpu_limit DECIMAL(5,2), -- CPU cores
    memory_limit_mb INTEGER,
    disk_space_mb INTEGER,
    
    -- Execution configuration
    environment execution_environment DEFAULT 'local',
    docker_image VARCHAR(255),
    command_template TEXT,
    environment_variables JSONB DEFAULT '{}',
    
    -- Input/Output schema
    input_schema JSONB DEFAULT '{}',
    output_schema JSONB DEFAULT '{}',
    
    -- Metadata
    tags VARCHAR(50)[],
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE NULL,
    
    UNIQUE(organization_id, slug, version)
);

-- Task instances - actual task executions
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    repository_id UUID REFERENCES repositories(id) ON DELETE SET NULL,
    task_definition_id UUID REFERENCES task_definitions(id) ON DELETE SET NULL,
    
    -- Task identification
    name VARCHAR(255) NOT NULL,
    short_id VARCHAR(20) UNIQUE DEFAULT generate_short_id('TSK-'),
    
    -- Task configuration
    task_type task_type NOT NULL,
    status task_status DEFAULT 'pending',
    priority priority_level DEFAULT 'medium',
    
    -- Execution details
    command TEXT,
    arguments JSONB DEFAULT '{}',
    environment_variables JSONB DEFAULT '{}',
    working_directory TEXT,
    
    -- Resource allocation
    allocated_cpu DECIMAL(5,2),
    allocated_memory_mb INTEGER,
    allocated_disk_mb INTEGER,
    
    -- Timing
    timeout_seconds INTEGER DEFAULT 3600,
    scheduled_at TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Results
    exit_code INTEGER,
    output TEXT,
    error_output TEXT,
    result_data JSONB DEFAULT '{}',
    
    -- Retry logic
    max_retries INTEGER DEFAULT 3,
    retry_count INTEGER DEFAULT 0,
    retry_delay_seconds INTEGER DEFAULT 60,
    last_retry_at TIMESTAMP WITH TIME ZONE,
    
    -- Ownership
    created_by UUID REFERENCES users(id),
    assigned_to UUID REFERENCES users(id),
    
    -- Metadata
    tags VARCHAR(50)[],
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE NULL
);

-- Task dependencies - manage task execution order
CREATE TABLE task_dependencies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Dependency relationship
    dependent_task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    prerequisite_task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    dependency_type dependency_type DEFAULT 'hard',
    
    -- Dependency metadata
    description TEXT,
    is_satisfied BOOLEAN DEFAULT false,
    satisfied_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(dependent_task_id, prerequisite_task_id),
    CHECK (dependent_task_id != prerequisite_task_id)
);

-- Task execution logs - detailed execution tracking
CREATE TABLE task_execution_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    
    -- Log entry details
    level severity_level DEFAULT 'info',
    message TEXT NOT NULL,
    details JSONB DEFAULT '{}',
    
    -- Context
    component VARCHAR(100), -- Which component generated the log
    phase VARCHAR(50),      -- setup, execution, cleanup, etc.
    
    -- Timing
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Metadata
    metadata JSONB DEFAULT '{}'
);

-- Task resource usage - monitor resource consumption
CREATE TABLE task_resource_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    
    -- Resource metrics
    cpu_usage_percent DECIMAL(5,2),
    memory_usage_mb INTEGER,
    disk_usage_mb INTEGER,
    network_in_mb DECIMAL(10,2),
    network_out_mb DECIMAL(10,2),
    
    -- Timing
    measured_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Additional metrics
    metrics JSONB DEFAULT '{}'
);

-- Workflows - orchestrate multiple tasks
CREATE TABLE workflows (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    
    -- Workflow metadata
    name VARCHAR(255) NOT NULL,
    short_id VARCHAR(20) UNIQUE DEFAULT generate_short_id('WF-'),
    description TEXT,
    
    -- Workflow configuration
    status task_status DEFAULT 'pending',
    priority priority_level DEFAULT 'medium',
    
    -- Execution strategy
    execution_strategy VARCHAR(50) DEFAULT 'sequential', -- sequential, parallel, dag
    max_parallel_tasks INTEGER DEFAULT 1,
    
    -- Timing
    scheduled_at TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Results
    result_data JSONB DEFAULT '{}',
    
    -- Ownership
    created_by UUID REFERENCES users(id),
    
    -- Metadata
    tags VARCHAR(50)[],
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE NULL
);

-- Workflow tasks - tasks within workflows
CREATE TABLE workflow_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    
    -- Execution order
    execution_order INTEGER NOT NULL,
    
    -- Conditional execution
    condition_expression TEXT, -- JSON logic expression
    skip_on_failure BOOLEAN DEFAULT false,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(workflow_id, task_id),
    UNIQUE(workflow_id, execution_order)
);

-- =============================================================================
-- INDEXES
-- =============================================================================

-- Task definitions indexes
CREATE INDEX idx_task_definitions_organization_id ON task_definitions(organization_id);
CREATE INDEX idx_task_definitions_slug ON task_definitions(slug);
CREATE INDEX idx_task_definitions_task_type ON task_definitions(task_type);
CREATE INDEX idx_task_definitions_environment ON task_definitions(environment);
CREATE INDEX idx_task_definitions_created_at ON task_definitions(created_at);
CREATE INDEX idx_task_definitions_deleted_at ON task_definitions(deleted_at) WHERE deleted_at IS NULL;

-- GIN indexes for JSONB and array fields
CREATE INDEX idx_task_definitions_tags ON task_definitions USING GIN(tags);
CREATE INDEX idx_task_definitions_metadata ON task_definitions USING GIN(metadata);
CREATE INDEX idx_task_definitions_input_schema ON task_definitions USING GIN(input_schema);
CREATE INDEX idx_task_definitions_output_schema ON task_definitions USING GIN(output_schema);

-- Tasks indexes
CREATE INDEX idx_tasks_organization_id ON tasks(organization_id);
CREATE INDEX idx_tasks_project_id ON tasks(project_id);
CREATE INDEX idx_tasks_repository_id ON tasks(repository_id);
CREATE INDEX idx_tasks_task_definition_id ON tasks(task_definition_id);
CREATE INDEX idx_tasks_short_id ON tasks(short_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_task_type ON tasks(task_type);
CREATE INDEX idx_tasks_priority ON tasks(priority);
CREATE INDEX idx_tasks_created_by ON tasks(created_by);
CREATE INDEX idx_tasks_assigned_to ON tasks(assigned_to);
CREATE INDEX idx_tasks_scheduled_at ON tasks(scheduled_at);
CREATE INDEX idx_tasks_started_at ON tasks(started_at);
CREATE INDEX idx_tasks_completed_at ON tasks(completed_at);
CREATE INDEX idx_tasks_created_at ON tasks(created_at);
CREATE INDEX idx_tasks_deleted_at ON tasks(deleted_at) WHERE deleted_at IS NULL;

-- Composite indexes for common queries
CREATE INDEX idx_tasks_status_priority ON tasks(status, priority);
CREATE INDEX idx_tasks_status_scheduled_at ON tasks(status, scheduled_at);
CREATE INDEX idx_tasks_project_status ON tasks(project_id, status);

-- GIN indexes for JSONB and array fields
CREATE INDEX idx_tasks_tags ON tasks USING GIN(tags);
CREATE INDEX idx_tasks_metadata ON tasks USING GIN(metadata);
CREATE INDEX idx_tasks_arguments ON tasks USING GIN(arguments);
CREATE INDEX idx_tasks_result_data ON tasks USING GIN(result_data);

-- Task dependencies indexes
CREATE INDEX idx_task_dependencies_dependent_task_id ON task_dependencies(dependent_task_id);
CREATE INDEX idx_task_dependencies_prerequisite_task_id ON task_dependencies(prerequisite_task_id);
CREATE INDEX idx_task_dependencies_dependency_type ON task_dependencies(dependency_type);
CREATE INDEX idx_task_dependencies_is_satisfied ON task_dependencies(is_satisfied);

-- Task execution logs indexes
CREATE INDEX idx_task_execution_logs_task_id ON task_execution_logs(task_id);
CREATE INDEX idx_task_execution_logs_level ON task_execution_logs(level);
CREATE INDEX idx_task_execution_logs_timestamp ON task_execution_logs(timestamp);
CREATE INDEX idx_task_execution_logs_component ON task_execution_logs(component);
CREATE INDEX idx_task_execution_logs_phase ON task_execution_logs(phase);

-- Composite index for log queries
CREATE INDEX idx_task_execution_logs_task_timestamp ON task_execution_logs(task_id, timestamp);

-- Task resource usage indexes
CREATE INDEX idx_task_resource_usage_task_id ON task_resource_usage(task_id);
CREATE INDEX idx_task_resource_usage_measured_at ON task_resource_usage(measured_at);

-- Composite index for resource queries
CREATE INDEX idx_task_resource_usage_task_measured ON task_resource_usage(task_id, measured_at);

-- Workflows indexes
CREATE INDEX idx_workflows_organization_id ON workflows(organization_id);
CREATE INDEX idx_workflows_project_id ON workflows(project_id);
CREATE INDEX idx_workflows_short_id ON workflows(short_id);
CREATE INDEX idx_workflows_status ON workflows(status);
CREATE INDEX idx_workflows_priority ON workflows(priority);
CREATE INDEX idx_workflows_created_by ON workflows(created_by);
CREATE INDEX idx_workflows_scheduled_at ON workflows(scheduled_at);
CREATE INDEX idx_workflows_started_at ON workflows(started_at);
CREATE INDEX idx_workflows_completed_at ON workflows(completed_at);
CREATE INDEX idx_workflows_created_at ON workflows(created_at);
CREATE INDEX idx_workflows_deleted_at ON workflows(deleted_at) WHERE deleted_at IS NULL;

-- GIN indexes for workflows
CREATE INDEX idx_workflows_tags ON workflows USING GIN(tags);
CREATE INDEX idx_workflows_metadata ON workflows USING GIN(metadata);
CREATE INDEX idx_workflows_result_data ON workflows USING GIN(result_data);

-- Workflow tasks indexes
CREATE INDEX idx_workflow_tasks_workflow_id ON workflow_tasks(workflow_id);
CREATE INDEX idx_workflow_tasks_task_id ON workflow_tasks(task_id);
CREATE INDEX idx_workflow_tasks_execution_order ON workflow_tasks(execution_order);

-- =============================================================================
-- TRIGGERS
-- =============================================================================

CREATE TRIGGER trigger_task_definitions_updated_at
    BEFORE UPDATE ON task_definitions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_tasks_updated_at
    BEFORE UPDATE ON tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_workflows_updated_at
    BEFORE UPDATE ON workflows
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- VIEWS
-- =============================================================================

-- Task summary view with dependency and resource information
CREATE VIEW task_summary AS
SELECT 
    t.*,
    td.name as definition_name,
    td.version as definition_version,
    COUNT(dep_out.id) as dependent_tasks_count,
    COUNT(dep_in.id) as prerequisite_tasks_count,
    COUNT(CASE WHEN dep_in.is_satisfied = false THEN 1 END) as unsatisfied_prerequisites,
    AVG(ru.cpu_usage_percent) as avg_cpu_usage,
    AVG(ru.memory_usage_mb) as avg_memory_usage,
    MAX(ru.measured_at) as last_resource_measurement
FROM tasks t
LEFT JOIN task_definitions td ON t.task_definition_id = td.id
LEFT JOIN task_dependencies dep_out ON t.id = dep_out.dependent_task_id
LEFT JOIN task_dependencies dep_in ON t.id = dep_in.prerequisite_task_id
LEFT JOIN task_resource_usage ru ON t.id = ru.task_id
WHERE t.deleted_at IS NULL
GROUP BY t.id, td.name, td.version;

-- Workflow summary view
CREATE VIEW workflow_summary AS
SELECT 
    w.*,
    COUNT(wt.task_id) as total_tasks,
    COUNT(CASE WHEN t.status = 'completed' THEN 1 END) as completed_tasks,
    COUNT(CASE WHEN t.status = 'failed' THEN 1 END) as failed_tasks,
    COUNT(CASE WHEN t.status = 'running' THEN 1 END) as running_tasks,
    MIN(t.started_at) as first_task_started,
    MAX(t.completed_at) as last_task_completed
FROM workflows w
LEFT JOIN workflow_tasks wt ON w.id = wt.workflow_id
LEFT JOIN tasks t ON wt.task_id = t.id AND t.deleted_at IS NULL
WHERE w.deleted_at IS NULL
GROUP BY w.id;

-- =============================================================================
-- FUNCTIONS
-- =============================================================================

-- Function to check if all task dependencies are satisfied
CREATE OR REPLACE FUNCTION are_task_dependencies_satisfied(task_uuid UUID)
RETURNS BOOLEAN AS $$
DECLARE
    unsatisfied_count INTEGER;
BEGIN
    SELECT COUNT(*)
    INTO unsatisfied_count
    FROM task_dependencies td
    WHERE td.dependent_task_id = task_uuid
    AND td.dependency_type = 'hard'
    AND td.is_satisfied = false;
    
    RETURN unsatisfied_count = 0;
END;
$$ LANGUAGE plpgsql;

-- Function to mark dependencies as satisfied when prerequisite task completes
CREATE OR REPLACE FUNCTION mark_dependencies_satisfied()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'completed' AND OLD.status != 'completed' THEN
        UPDATE task_dependencies
        SET is_satisfied = true, satisfied_at = CURRENT_TIMESTAMP
        WHERE prerequisite_task_id = NEW.id
        AND is_satisfied = false;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically mark dependencies as satisfied
CREATE TRIGGER trigger_mark_dependencies_satisfied
    AFTER UPDATE ON tasks
    FOR EACH ROW
    EXECUTE FUNCTION mark_dependencies_satisfied();

-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON TABLE task_definitions IS 'Reusable task templates with configuration and resource requirements';
COMMENT ON TABLE tasks IS 'Task instances with execution tracking and flexible metadata';
COMMENT ON TABLE task_dependencies IS 'Task dependency management for workflow orchestration';
COMMENT ON TABLE task_execution_logs IS 'Detailed execution logs for debugging and monitoring';
COMMENT ON TABLE task_resource_usage IS 'Resource consumption monitoring for optimization';
COMMENT ON TABLE workflows IS 'Workflow orchestration with multiple task coordination';
COMMENT ON TABLE workflow_tasks IS 'Tasks within workflows with execution order';

COMMENT ON VIEW task_summary IS 'Task overview with dependencies and resource usage';
COMMENT ON VIEW workflow_summary IS 'Workflow progress and task completion status';

COMMENT ON FUNCTION are_task_dependencies_satisfied(UUID) IS 'Check if all hard dependencies for a task are satisfied';
COMMENT ON FUNCTION mark_dependencies_satisfied() IS 'Automatically mark dependencies as satisfied when prerequisite tasks complete';

