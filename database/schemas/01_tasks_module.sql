-- =============================================================================
-- TASKS MODULE: Task Context, Execution Tracking, and Dependencies
-- =============================================================================
-- This module handles comprehensive task management including task definitions,
-- execution tracking, dependency management, workflow orchestration, and
-- resource monitoring. Consolidated from PRs 74, 75, 76.
-- =============================================================================

-- Task-specific enums
CREATE TYPE task_status AS ENUM (
    'draft',
    'pending',
    'assigned',
    'in_progress',
    'blocked',
    'review',
    'completed',
    'failed',
    'cancelled',
    'archived'
);

CREATE TYPE task_type AS ENUM (
    'code_analysis',
    'code_generation',
    'code_review',
    'testing',
    'deployment',
    'documentation',
    'research',
    'bug_fix',
    'feature_development',
    'optimization',
    'maintenance',
    'custom'
);

CREATE TYPE dependency_type AS ENUM (
    'blocks',
    'depends_on',
    'related_to',
    'subtask_of',
    'triggers',
    'conflicts_with'
);

CREATE TYPE workflow_type AS ENUM (
    'sequential',
    'parallel',
    'conditional',
    'dag',
    'pipeline',
    'custom'
);

CREATE TYPE execution_mode AS ENUM (
    'manual',
    'automatic',
    'scheduled',
    'triggered',
    'continuous'
);

-- =============================================================================
-- TASK DEFINITIONS AND TEMPLATES
-- =============================================================================

-- Task definitions for reusable task templates
CREATE TABLE task_definitions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Definition identification
    name VARCHAR(255) NOT NULL,
    description TEXT,
    task_type task_type NOT NULL,
    category VARCHAR(100),
    
    -- Task configuration
    default_config JSONB DEFAULT '{}',
    required_inputs JSONB DEFAULT '[]',
    expected_outputs JSONB DEFAULT '[]',
    
    -- Resource requirements
    estimated_duration_minutes INTEGER,
    cpu_requirements DECIMAL(5,2), -- CPU cores
    memory_requirements_mb INTEGER,
    storage_requirements_mb INTEGER,
    
    -- Execution configuration
    execution_mode execution_mode DEFAULT 'manual',
    retry_config JSONB DEFAULT '{}',
    timeout_minutes INTEGER DEFAULT 60,
    
    -- Template and scripting
    script_template TEXT,
    command_template TEXT,
    environment_config JSONB DEFAULT '{}',
    
    -- Validation and constraints
    validation_rules JSONB DEFAULT '{}',
    prerequisites JSONB DEFAULT '[]',
    
    -- Usage and versioning
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT true,
    usage_count INTEGER DEFAULT 0,
    
    -- Metadata
    tags VARCHAR(50)[],
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT task_definitions_name_org_unique UNIQUE (organization_id, name),
    CONSTRAINT task_definitions_name_not_empty CHECK (length(trim(name)) > 0),
    CONSTRAINT task_definitions_version_positive CHECK (version > 0)
);

-- =============================================================================
-- TASKS AND EXECUTION
-- =============================================================================

-- Main tasks table
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    task_definition_id UUID REFERENCES task_definitions(id),
    
    -- Task identification
    name VARCHAR(255) NOT NULL,
    description TEXT,
    task_type task_type NOT NULL,
    
    -- Task hierarchy
    parent_task_id UUID REFERENCES tasks(id),
    root_task_id UUID REFERENCES tasks(id),
    task_level INTEGER DEFAULT 0,
    
    -- Task configuration
    configuration JSONB DEFAULT '{}',
    input_data JSONB DEFAULT '{}',
    output_data JSONB DEFAULT '{}',
    
    -- Status and progress
    status task_status DEFAULT 'draft',
    progress_percentage DECIMAL(5,2) DEFAULT 0,
    priority priority_level DEFAULT 'normal',
    
    -- Assignment and ownership
    assigned_to UUID REFERENCES users(id),
    created_by UUID REFERENCES users(id),
    assigned_at TIMESTAMP WITH TIME ZONE,
    
    -- Timing and scheduling
    scheduled_at TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    due_date TIMESTAMP WITH TIME ZONE,
    
    -- Duration tracking
    estimated_duration_minutes INTEGER,
    actual_duration_minutes INTEGER,
    
    -- Resource tracking
    cpu_usage_percent DECIMAL(5,2),
    memory_usage_mb INTEGER,
    storage_usage_mb INTEGER,
    
    -- Execution details
    execution_mode execution_mode DEFAULT 'manual',
    execution_environment JSONB DEFAULT '{}',
    execution_log TEXT,
    error_message TEXT,
    
    -- Retry and recovery
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    last_retry_at TIMESTAMP WITH TIME ZONE,
    
    -- Quality and validation
    quality_score DECIMAL(5,2),
    validation_results JSONB DEFAULT '{}',
    
    -- External references
    external_task_id VARCHAR(255),
    external_url TEXT,
    
    -- Metadata
    tags VARCHAR(50)[],
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT tasks_name_not_empty CHECK (length(trim(name)) > 0),
    CONSTRAINT tasks_progress_valid CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
    CONSTRAINT tasks_retry_count_valid CHECK (retry_count >= 0),
    CONSTRAINT tasks_level_valid CHECK (task_level >= 0)
);

-- Task dependencies for complex workflow management
CREATE TABLE task_dependencies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Dependency relationship
    source_task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    target_task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    
    -- Dependency details
    dependency_type dependency_type NOT NULL,
    description TEXT,
    
    -- Dependency configuration
    is_hard_dependency BOOLEAN DEFAULT true,
    delay_minutes INTEGER DEFAULT 0,
    condition_config JSONB DEFAULT '{}',
    
    -- Status tracking
    is_satisfied BOOLEAN DEFAULT false,
    satisfied_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT task_dependencies_unique UNIQUE (source_task_id, target_task_id, dependency_type),
    CONSTRAINT task_dependencies_no_self_reference CHECK (source_task_id != target_task_id)
);

-- =============================================================================
-- WORKFLOWS AND ORCHESTRATION
-- =============================================================================

-- Workflows for task orchestration
CREATE TABLE workflows (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Workflow identification
    name VARCHAR(255) NOT NULL,
    description TEXT,
    workflow_type workflow_type NOT NULL,
    
    -- Workflow configuration
    configuration JSONB DEFAULT '{}',
    execution_plan JSONB DEFAULT '{}',
    
    -- Workflow status
    status status_type DEFAULT 'active',
    is_template BOOLEAN DEFAULT false,
    
    -- Execution tracking
    execution_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    
    -- Timing configuration
    schedule_config JSONB DEFAULT '{}',
    timeout_minutes INTEGER DEFAULT 240,
    
    -- Triggers and conditions
    trigger_config JSONB DEFAULT '{}',
    conditions JSONB DEFAULT '{}',
    
    -- Metadata
    tags VARCHAR(50)[],
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT workflows_name_org_unique UNIQUE (organization_id, name),
    CONSTRAINT workflows_name_not_empty CHECK (length(trim(name)) > 0)
);

-- Workflow executions for tracking workflow runs
CREATE TABLE workflow_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Execution identification
    execution_name VARCHAR(255),
    execution_number INTEGER,
    
    -- Execution status
    status task_status DEFAULT 'pending',
    progress_percentage DECIMAL(5,2) DEFAULT 0,
    
    -- Timing
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_minutes INTEGER,
    
    -- Execution context
    trigger_source VARCHAR(100), -- manual, scheduled, event, api
    trigger_data JSONB DEFAULT '{}',
    execution_config JSONB DEFAULT '{}',
    
    -- Results and output
    output_data JSONB DEFAULT '{}',
    execution_log TEXT,
    error_message TEXT,
    
    -- Task tracking
    total_tasks INTEGER DEFAULT 0,
    completed_tasks INTEGER DEFAULT 0,
    failed_tasks INTEGER DEFAULT 0,
    
    -- Resource usage
    total_cpu_time_minutes DECIMAL(10,2),
    peak_memory_usage_mb INTEGER,
    total_storage_usage_mb INTEGER,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Workflow tasks for linking tasks to workflow executions
CREATE TABLE workflow_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_execution_id UUID NOT NULL REFERENCES workflow_executions(id) ON DELETE CASCADE,
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    
    -- Task position in workflow
    step_number INTEGER NOT NULL,
    step_name VARCHAR(255),
    
    -- Execution order and dependencies
    execution_order INTEGER,
    depends_on_steps INTEGER[],
    
    -- Status and timing
    status task_status DEFAULT 'pending',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Configuration
    step_config JSONB DEFAULT '{}',
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT workflow_tasks_unique UNIQUE (workflow_execution_id, step_number),
    CONSTRAINT workflow_tasks_step_positive CHECK (step_number > 0)
);

-- =============================================================================
-- EXECUTION TRACKING AND MONITORING
-- =============================================================================

-- Task execution logs for detailed tracking
CREATE TABLE task_execution_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    
    -- Log entry details
    log_level VARCHAR(20) NOT NULL, -- DEBUG, INFO, WARN, ERROR, FATAL
    message TEXT NOT NULL,
    
    -- Context and source
    component VARCHAR(100),
    function_name VARCHAR(255),
    line_number INTEGER,
    
    -- Execution context
    execution_step VARCHAR(255),
    step_number INTEGER,
    
    -- Additional data
    log_data JSONB DEFAULT '{}',
    stack_trace TEXT,
    
    -- Timing
    logged_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Metadata
    metadata JSONB DEFAULT '{}'
);

-- Task resource usage tracking
CREATE TABLE task_resource_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    
    -- Resource metrics
    cpu_usage_percent DECIMAL(5,2),
    memory_usage_mb INTEGER,
    storage_usage_mb INTEGER,
    network_io_mb DECIMAL(10,2),
    
    -- System metrics
    load_average DECIMAL(5,2),
    disk_io_mb DECIMAL(10,2),
    
    -- Timing
    measured_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    measurement_duration_seconds INTEGER DEFAULT 60,
    
    -- Context
    measurement_source VARCHAR(100),
    
    -- Metadata
    metadata JSONB DEFAULT '{}'
);

-- Task notifications and alerts
CREATE TABLE task_notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Notification details
    notification_type VARCHAR(100) NOT NULL, -- status_change, deadline_approaching, error, completion
    title VARCHAR(255) NOT NULL,
    message TEXT,
    
    -- Recipients
    recipient_user_ids UUID[],
    recipient_channels JSONB DEFAULT '[]', -- slack, email, webhook
    
    -- Notification status
    status VARCHAR(50) DEFAULT 'pending', -- pending, sent, failed, cancelled
    sent_at TIMESTAMP WITH TIME ZONE,
    
    -- Configuration
    notification_config JSONB DEFAULT '{}',
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- TRIGGERS AND FUNCTIONS
-- =============================================================================

-- Update timestamps
CREATE TRIGGER update_task_definitions_updated_at 
    BEFORE UPDATE ON task_definitions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tasks_updated_at 
    BEFORE UPDATE ON tasks 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_task_dependencies_updated_at 
    BEFORE UPDATE ON task_dependencies 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_workflows_updated_at 
    BEFORE UPDATE ON workflows 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_workflow_executions_updated_at 
    BEFORE UPDATE ON workflow_executions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to check for circular dependencies
CREATE OR REPLACE FUNCTION check_circular_dependencies(
    p_source_task_id UUID,
    p_target_task_id UUID
) RETURNS BOOLEAN AS $$
DECLARE
    circular_found BOOLEAN := false;
BEGIN
    -- Use recursive CTE to check for circular dependencies
    WITH RECURSIVE dependency_chain AS (
        -- Base case: direct dependencies
        SELECT 
            source_task_id,
            target_task_id,
            1 as depth
        FROM task_dependencies 
        WHERE source_task_id = p_target_task_id
        
        UNION ALL
        
        -- Recursive case: follow the chain
        SELECT 
            td.source_task_id,
            td.target_task_id,
            dc.depth + 1
        FROM task_dependencies td
        JOIN dependency_chain dc ON td.source_task_id = dc.target_task_id
        WHERE dc.depth < 10 -- Prevent infinite recursion
    )
    SELECT EXISTS(
        SELECT 1 FROM dependency_chain 
        WHERE target_task_id = p_source_task_id
    ) INTO circular_found;
    
    RETURN circular_found;
END;
$$ LANGUAGE plpgsql;

-- Function to validate task dependencies
CREATE OR REPLACE FUNCTION validate_task_dependency()
RETURNS TRIGGER AS $$
BEGIN
    -- Check for circular dependencies
    IF check_circular_dependencies(NEW.source_task_id, NEW.target_task_id) THEN
        RAISE EXCEPTION 'Circular dependency detected between tasks % and %', 
            NEW.source_task_id, NEW.target_task_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to validate dependencies
CREATE TRIGGER validate_dependency_before_insert
    BEFORE INSERT ON task_dependencies
    FOR EACH ROW EXECUTE FUNCTION validate_task_dependency();

-- Function to update task hierarchy
CREATE OR REPLACE FUNCTION update_task_hierarchy()
RETURNS TRIGGER AS $$
BEGIN
    -- Update task level based on parent
    IF NEW.parent_task_id IS NOT NULL THEN
        SELECT task_level + 1, COALESCE(root_task_id, id)
        INTO NEW.task_level, NEW.root_task_id
        FROM tasks 
        WHERE id = NEW.parent_task_id;
    ELSE
        NEW.task_level := 0;
        NEW.root_task_id := NEW.id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to maintain task hierarchy
CREATE TRIGGER update_task_hierarchy_on_insert
    BEFORE INSERT ON tasks
    FOR EACH ROW EXECUTE FUNCTION update_task_hierarchy();

-- Function to check if task dependencies are satisfied
CREATE OR REPLACE FUNCTION are_task_dependencies_satisfied(p_task_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    unsatisfied_count INTEGER;
BEGIN
    SELECT COUNT(*)
    INTO unsatisfied_count
    FROM task_dependencies td
    JOIN tasks t ON td.target_task_id = t.id
    WHERE td.source_task_id = p_task_id
    AND td.is_hard_dependency = true
    AND (
        td.is_satisfied = false 
        OR t.status NOT IN ('completed')
    );
    
    RETURN unsatisfied_count = 0;
END;
$$ LANGUAGE plpgsql;

-- Function to update dependency satisfaction
CREATE OR REPLACE FUNCTION update_dependency_satisfaction()
RETURNS TRIGGER AS $$
BEGIN
    -- Update dependencies when task status changes to completed
    IF NEW.status = 'completed' AND OLD.status != 'completed' THEN
        UPDATE task_dependencies 
        SET 
            is_satisfied = true,
            satisfied_at = NOW()
        WHERE target_task_id = NEW.id
        AND is_satisfied = false;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update dependency satisfaction
CREATE TRIGGER update_dependency_satisfaction_on_completion
    AFTER UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION update_dependency_satisfaction();

-- =============================================================================
-- INDEXES FOR OPTIMAL PERFORMANCE
-- =============================================================================

-- Task definitions indexes
CREATE INDEX idx_task_definitions_org_id ON task_definitions(organization_id);
CREATE INDEX idx_task_definitions_type ON task_definitions(task_type);
CREATE INDEX idx_task_definitions_active ON task_definitions(is_active) WHERE deleted_at IS NULL;
CREATE INDEX idx_task_definitions_usage ON task_definitions(usage_count DESC);

-- Tasks indexes
CREATE INDEX idx_tasks_org_id ON tasks(organization_id);
CREATE INDEX idx_tasks_definition_id ON task_definitions(id);
CREATE INDEX idx_tasks_parent_id ON tasks(parent_task_id);
CREATE INDEX idx_tasks_root_id ON tasks(root_task_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_priority ON tasks(priority);
CREATE INDEX idx_tasks_assigned_to ON tasks(assigned_to);
CREATE INDEX idx_tasks_created_by ON tasks(created_by);
CREATE INDEX idx_tasks_scheduled_at ON tasks(scheduled_at);
CREATE INDEX idx_tasks_due_date ON tasks(due_date);
CREATE INDEX idx_tasks_status_priority ON tasks(status, priority);
CREATE INDEX idx_tasks_active ON tasks(status) WHERE status IN ('pending', 'assigned', 'in_progress');

-- Task dependencies indexes
CREATE INDEX idx_task_dependencies_source ON task_dependencies(source_task_id);
CREATE INDEX idx_task_dependencies_target ON task_dependencies(target_task_id);
CREATE INDEX idx_task_dependencies_type ON task_dependencies(dependency_type);
CREATE INDEX idx_task_dependencies_satisfied ON task_dependencies(is_satisfied);

-- Workflows indexes
CREATE INDEX idx_workflows_org_id ON workflows(organization_id);
CREATE INDEX idx_workflows_type ON workflows(workflow_type);
CREATE INDEX idx_workflows_status ON workflows(status) WHERE deleted_at IS NULL;
CREATE INDEX idx_workflows_template ON workflows(is_template);

-- Workflow executions indexes
CREATE INDEX idx_workflow_executions_workflow_id ON workflow_executions(workflow_id);
CREATE INDEX idx_workflow_executions_org_id ON workflow_executions(organization_id);
CREATE INDEX idx_workflow_executions_status ON workflow_executions(status);
CREATE INDEX idx_workflow_executions_started_at ON workflow_executions(started_at);

-- Workflow tasks indexes
CREATE INDEX idx_workflow_tasks_execution_id ON workflow_tasks(workflow_execution_id);
CREATE INDEX idx_workflow_tasks_task_id ON workflow_tasks(task_id);
CREATE INDEX idx_workflow_tasks_step_number ON workflow_tasks(step_number);
CREATE INDEX idx_workflow_tasks_status ON workflow_tasks(status);

-- Execution logs indexes
CREATE INDEX idx_task_execution_logs_task_id ON task_execution_logs(task_id);
CREATE INDEX idx_task_execution_logs_level ON task_execution_logs(log_level);
CREATE INDEX idx_task_execution_logs_logged_at ON task_execution_logs(logged_at);
CREATE INDEX idx_task_execution_logs_component ON task_execution_logs(component);

-- Resource usage indexes
CREATE INDEX idx_task_resource_usage_task_id ON task_resource_usage(task_id);
CREATE INDEX idx_task_resource_usage_measured_at ON task_resource_usage(measured_at);

-- Notifications indexes
CREATE INDEX idx_task_notifications_task_id ON task_notifications(task_id);
CREATE INDEX idx_task_notifications_org_id ON task_notifications(organization_id);
CREATE INDEX idx_task_notifications_type ON task_notifications(notification_type);
CREATE INDEX idx_task_notifications_status ON task_notifications(status);

-- GIN indexes for JSONB fields
CREATE INDEX idx_task_definitions_config_gin USING gin (default_config);
CREATE INDEX idx_tasks_configuration_gin USING gin (configuration);
CREATE INDEX idx_tasks_metadata_gin USING gin (metadata);
CREATE INDEX idx_workflows_config_gin USING gin (configuration);

-- =============================================================================
-- VIEWS FOR COMMON QUERIES
-- =============================================================================

-- Active tasks view
CREATE VIEW active_tasks AS
SELECT 
    t.*,
    td.name as definition_name,
    td.task_type as definition_type,
    u1.name as assigned_to_name,
    u2.name as created_by_name,
    o.name as organization_name
FROM tasks t
LEFT JOIN task_definitions td ON t.task_definition_id = td.id
LEFT JOIN users u1 ON t.assigned_to = u1.id
LEFT JOIN users u2 ON t.created_by = u2.id
JOIN organizations o ON t.organization_id = o.id
WHERE t.status IN ('pending', 'assigned', 'in_progress', 'blocked', 'review')
AND t.deleted_at IS NULL;

-- Task hierarchy view
CREATE VIEW task_hierarchy AS
WITH RECURSIVE task_tree AS (
    -- Root tasks
    SELECT 
        id,
        name,
        parent_task_id,
        task_level,
        ARRAY[id] as path,
        name as full_path
    FROM tasks 
    WHERE parent_task_id IS NULL
    
    UNION ALL
    
    -- Child tasks
    SELECT 
        t.id,
        t.name,
        t.parent_task_id,
        t.task_level,
        tt.path || t.id,
        tt.full_path || ' > ' || t.name
    FROM tasks t
    JOIN task_tree tt ON t.parent_task_id = tt.id
)
SELECT * FROM task_tree;

-- Task dependency graph view
CREATE VIEW task_dependency_graph AS
SELECT 
    td.id,
    td.dependency_type,
    td.is_satisfied,
    s.id as source_task_id,
    s.name as source_task_name,
    s.status as source_status,
    t.id as target_task_id,
    t.name as target_task_name,
    t.status as target_status
FROM task_dependencies td
JOIN tasks s ON td.source_task_id = s.id
JOIN tasks t ON td.target_task_id = t.id;

-- Workflow execution summary
CREATE VIEW workflow_execution_summary AS
SELECT 
    we.id,
    we.workflow_id,
    w.name as workflow_name,
    we.status,
    we.started_at,
    we.completed_at,
    we.duration_minutes,
    we.total_tasks,
    we.completed_tasks,
    we.failed_tasks,
    ROUND(
        CASE 
            WHEN we.total_tasks > 0 
            THEN (we.completed_tasks::DECIMAL / we.total_tasks) * 100 
            ELSE 0 
        END, 2
    ) as completion_percentage
FROM workflow_executions we
JOIN workflows w ON we.workflow_id = w.id;

-- =============================================================================
-- INITIAL DATA AND CONFIGURATION
-- =============================================================================

-- Insert default task definitions
INSERT INTO task_definitions (
    organization_id,
    name,
    description,
    task_type,
    default_config,
    estimated_duration_minutes,
    execution_mode
) VALUES 
(
    (SELECT id FROM organizations WHERE slug = 'default' LIMIT 1),
    'Code Analysis',
    'Analyze codebase for quality, complexity, and issues',
    'code_analysis',
    '{"analysis_types": ["complexity", "quality", "security"], "output_format": "json"}',
    30,
    'automatic'
),
(
    (SELECT id FROM organizations WHERE slug = 'default' LIMIT 1),
    'Code Review',
    'Review code changes for quality and best practices',
    'code_review',
    '{"review_criteria": ["style", "logic", "performance"], "auto_approve_threshold": 0.8}',
    45,
    'manual'
),
(
    (SELECT id FROM organizations WHERE slug = 'default' LIMIT 1),
    'Unit Testing',
    'Generate and execute unit tests for code components',
    'testing',
    '{"test_framework": "pytest", "coverage_threshold": 80}',
    60,
    'automatic'
);

-- Record this migration
INSERT INTO schema_migrations (version, description, module) VALUES 
('01_tasks_module', 'Tasks module for comprehensive task management and workflow orchestration', 'tasks');

-- =============================================================================
-- COMMENTS FOR DOCUMENTATION
-- =============================================================================

COMMENT ON TABLE task_definitions IS 'Reusable task templates with configuration and resource requirements';
COMMENT ON TABLE tasks IS 'Main tasks table with comprehensive tracking and hierarchy support';
COMMENT ON TABLE task_dependencies IS 'Task dependency management with circular dependency prevention';
COMMENT ON TABLE workflows IS 'Workflow definitions for task orchestration';
COMMENT ON TABLE workflow_executions IS 'Workflow execution tracking with progress and resource monitoring';
COMMENT ON TABLE workflow_tasks IS 'Links between workflow executions and individual tasks';
COMMENT ON TABLE task_execution_logs IS 'Detailed execution logging for debugging and monitoring';
COMMENT ON TABLE task_resource_usage IS 'Resource usage tracking for performance optimization';
COMMENT ON TABLE task_notifications IS 'Task notification and alerting system';

COMMENT ON FUNCTION check_circular_dependencies IS 'Check for circular dependencies in task relationships';
COMMENT ON FUNCTION are_task_dependencies_satisfied IS 'Check if all dependencies for a task are satisfied';

-- Final status message
DO $$
BEGIN
    RAISE NOTICE '📋 Tasks Module initialized successfully!';
    RAISE NOTICE 'Features: Task definitions, Dependency management, Workflow orchestration, Resource tracking';
    RAISE NOTICE 'Default task types: Code Analysis, Code Review, Unit Testing';
    RAISE NOTICE 'Capabilities: Circular dependency detection, Hierarchy management, Resource monitoring';
    RAISE NOTICE 'Timestamp: %', NOW();
END $$;

