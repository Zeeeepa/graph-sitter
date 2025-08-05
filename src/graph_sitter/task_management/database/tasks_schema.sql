-- Advanced Task Management System Database Schema
-- Comprehensive schema for task management, workflow orchestration, and analytics

-- Enable UUID extension for PostgreSQL
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Task Management Tables

-- Core tasks table
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    task_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    priority INTEGER NOT NULL DEFAULT 3,
    
    -- Timing and scheduling
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    scheduled_at TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    deadline TIMESTAMP WITH TIME ZONE,
    estimated_duration_seconds INTEGER,
    actual_duration_seconds INTEGER,
    
    -- Execution configuration
    max_retries INTEGER NOT NULL DEFAULT 3,
    retry_count INTEGER NOT NULL DEFAULT 0,
    timeout_seconds INTEGER,
    
    -- Task relationships
    parent_task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    workflow_id UUID, -- Will reference workflows table
    
    -- Data and results
    input_data JSONB,
    output_data JSONB,
    error_info JSONB,
    execution_context JSONB,
    
    -- Integration fields
    codegen_agent_id VARCHAR(255),
    graph_sitter_config JSONB,
    contexten_workflow_id VARCHAR(255),
    
    -- Metadata
    created_by VARCHAR(255) NOT NULL DEFAULT 'system',
    tags TEXT[],
    labels JSONB,
    
    -- Constraints
    CONSTRAINT valid_status CHECK (status IN ('pending', 'queued', 'running', 'paused', 'completed', 'failed', 'cancelled', 'retrying')),
    CONSTRAINT valid_priority CHECK (priority BETWEEN 1 AND 5),
    CONSTRAINT valid_task_type CHECK (task_type IN ('code_analysis', 'code_generation', 'code_refactoring', 'workflow_orchestration', 'integration_task', 'evaluation_task', 'performance_optimization', 'custom'))
);

-- Task dependencies table
CREATE TABLE task_dependencies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    dependency_task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    dependency_type VARCHAR(20) NOT NULL DEFAULT 'completion',
    condition_expression TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    UNIQUE(task_id, dependency_task_id),
    CONSTRAINT valid_dependency_type CHECK (dependency_type IN ('completion', 'data', 'resource', 'conditional'))
);

-- Resource requirements table
CREATE TABLE task_resources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    cpu_cores INTEGER,
    memory_mb INTEGER,
    gpu_required BOOLEAN NOT NULL DEFAULT FALSE,
    disk_space_mb INTEGER,
    network_bandwidth VARCHAR(20),
    custom_resources JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Workflow Management Tables

-- Workflows table
CREATE TABLE workflows (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    version VARCHAR(20) NOT NULL DEFAULT '1.0.0',
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    
    -- Timing
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Configuration
    max_parallel_steps INTEGER NOT NULL DEFAULT 10,
    timeout_seconds INTEGER,
    retry_failed_steps BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Data and context
    context JSONB,
    results JSONB,
    error_info JSONB,
    
    -- Metadata
    created_by VARCHAR(255) NOT NULL DEFAULT 'system',
    tags TEXT[],
    labels JSONB,
    
    CONSTRAINT valid_workflow_status CHECK (status IN ('draft', 'ready', 'running', 'paused', 'completed', 'failed', 'cancelled'))
);

-- Workflow steps table
CREATE TABLE workflow_steps (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    step_type VARCHAR(20) NOT NULL,
    step_order INTEGER NOT NULL,
    
    -- Task configuration (for TASK steps)
    task_type VARCHAR(50),
    task_config JSONB,
    
    -- Condition configuration (for CONDITION steps)
    condition_expression TEXT,
    true_path_steps UUID[],
    false_path_steps UUID[],
    
    -- Parallel/Sequential configuration
    child_step_ids UUID[],
    
    -- Loop configuration
    loop_condition TEXT,
    max_iterations INTEGER,
    
    -- Wait configuration
    wait_duration_seconds INTEGER,
    wait_condition TEXT,
    
    -- Execution state
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    retry_count INTEGER NOT NULL DEFAULT 0,
    max_retries INTEGER NOT NULL DEFAULT 3,
    timeout_seconds INTEGER,
    
    -- Results
    output_data JSONB,
    error_info JSONB,
    
    -- Metadata
    tags TEXT[],
    labels JSONB,
    
    CONSTRAINT valid_step_type CHECK (step_type IN ('task', 'condition', 'parallel', 'sequential', 'loop', 'wait', 'webhook', 'custom')),
    CONSTRAINT valid_step_status CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled', 'skipped'))
);

-- Workflow step dependencies
CREATE TABLE workflow_step_dependencies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    step_id UUID NOT NULL REFERENCES workflow_steps(id) ON DELETE CASCADE,
    dependency_step_id UUID NOT NULL REFERENCES workflow_steps(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    UNIQUE(step_id, dependency_step_id)
);

-- Add foreign key for workflow_id in tasks table
ALTER TABLE tasks ADD CONSTRAINT fk_tasks_workflow 
    FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE SET NULL;

-- Performance and Monitoring Tables

-- Task execution metrics
CREATE TABLE task_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    metric_name VARCHAR(100) NOT NULL,
    metric_value NUMERIC,
    metric_unit VARCHAR(20),
    metric_type VARCHAR(20) NOT NULL DEFAULT 'gauge',
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    CONSTRAINT valid_metric_type CHECK (metric_type IN ('counter', 'gauge', 'histogram', 'timer'))
);

-- System performance metrics
CREATE TABLE system_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_name VARCHAR(100) NOT NULL,
    metric_value NUMERIC NOT NULL,
    metric_unit VARCHAR(20),
    component VARCHAR(50),
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    metadata JSONB
);

-- Resource usage tracking
CREATE TABLE resource_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    workflow_id UUID REFERENCES workflows(id) ON DELETE CASCADE,
    cpu_usage_percent NUMERIC(5,2),
    memory_usage_mb INTEGER,
    disk_io_mb INTEGER,
    network_io_mb INTEGER,
    gpu_usage_percent NUMERIC(5,2),
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    duration_seconds INTEGER
);

-- Integration and External System Tables

-- Integration configurations
CREATE TABLE integrations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'disconnected',
    config JSONB NOT NULL,
    credentials JSONB, -- Encrypted credentials
    
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_health_check TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT valid_integration_status CHECK (status IN ('disconnected', 'connecting', 'connected', 'error', 'disabled')),
    CONSTRAINT valid_integration_type CHECK (type IN ('codegen', 'graph_sitter', 'contexten', 'custom'))
);

-- Integration metrics
CREATE TABLE integration_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    integration_id UUID NOT NULL REFERENCES integrations(id) ON DELETE CASCADE,
    total_requests INTEGER NOT NULL DEFAULT 0,
    successful_requests INTEGER NOT NULL DEFAULT 0,
    failed_requests INTEGER NOT NULL DEFAULT 0,
    average_response_time_ms NUMERIC(10,2),
    last_request_at TIMESTAMP WITH TIME ZONE,
    last_error TEXT,
    uptime_percentage NUMERIC(5,2),
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Evaluation and Analytics Tables

-- Task evaluations
CREATE TABLE task_evaluations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    evaluation_type VARCHAR(50) NOT NULL,
    score NUMERIC(5,2),
    max_score NUMERIC(5,2) NOT NULL DEFAULT 100,
    criteria JSONB,
    feedback TEXT,
    evaluator VARCHAR(100),
    evaluated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    CONSTRAINT valid_score CHECK (score >= 0 AND score <= max_score)
);

-- Workflow evaluations
CREATE TABLE workflow_evaluations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    evaluation_type VARCHAR(50) NOT NULL,
    overall_score NUMERIC(5,2),
    efficiency_score NUMERIC(5,2),
    reliability_score NUMERIC(5,2),
    performance_score NUMERIC(5,2),
    criteria JSONB,
    recommendations TEXT[],
    evaluator VARCHAR(100),
    evaluated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Analytics reports
CREATE TABLE analytics_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_type VARCHAR(50) NOT NULL,
    report_name VARCHAR(255) NOT NULL,
    time_period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    time_period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    data JSONB NOT NULL,
    insights TEXT[],
    recommendations TEXT[],
    generated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    generated_by VARCHAR(100)
);

-- Audit and Logging Tables

-- Task audit log
CREATE TABLE task_audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    action VARCHAR(50) NOT NULL,
    old_values JSONB,
    new_values JSONB,
    changed_by VARCHAR(255),
    changed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT
);

-- System events log
CREATE TABLE system_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(50) NOT NULL,
    event_name VARCHAR(255) NOT NULL,
    severity VARCHAR(20) NOT NULL DEFAULT 'info',
    message TEXT,
    data JSONB,
    source VARCHAR(100),
    occurred_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    CONSTRAINT valid_severity CHECK (severity IN ('debug', 'info', 'warning', 'error', 'critical'))
);

-- Indexes for Performance

-- Task indexes
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_type ON tasks(task_type);
CREATE INDEX idx_tasks_priority ON tasks(priority);
CREATE INDEX idx_tasks_created_at ON tasks(created_at);
CREATE INDEX idx_tasks_scheduled_at ON tasks(scheduled_at);
CREATE INDEX idx_tasks_workflow_id ON tasks(workflow_id);
CREATE INDEX idx_tasks_parent_task_id ON tasks(parent_task_id);
CREATE INDEX idx_tasks_tags ON tasks USING GIN(tags);
CREATE INDEX idx_tasks_labels ON tasks USING GIN(labels);

-- Workflow indexes
CREATE INDEX idx_workflows_status ON workflows(status);
CREATE INDEX idx_workflows_created_at ON workflows(created_at);
CREATE INDEX idx_workflows_tags ON workflows USING GIN(tags);

-- Workflow step indexes
CREATE INDEX idx_workflow_steps_workflow_id ON workflow_steps(workflow_id);
CREATE INDEX idx_workflow_steps_status ON workflow_steps(status);
CREATE INDEX idx_workflow_steps_type ON workflow_steps(step_type);
CREATE INDEX idx_workflow_steps_order ON workflow_steps(workflow_id, step_order);

-- Metrics indexes
CREATE INDEX idx_task_metrics_task_id ON task_metrics(task_id);
CREATE INDEX idx_task_metrics_recorded_at ON task_metrics(recorded_at);
CREATE INDEX idx_task_metrics_name ON task_metrics(metric_name);

CREATE INDEX idx_system_metrics_recorded_at ON system_metrics(recorded_at);
CREATE INDEX idx_system_metrics_name ON system_metrics(metric_name);
CREATE INDEX idx_system_metrics_component ON system_metrics(component);

-- Resource usage indexes
CREATE INDEX idx_resource_usage_task_id ON resource_usage(task_id);
CREATE INDEX idx_resource_usage_workflow_id ON resource_usage(workflow_id);
CREATE INDEX idx_resource_usage_recorded_at ON resource_usage(recorded_at);

-- Integration indexes
CREATE INDEX idx_integrations_type ON integrations(type);
CREATE INDEX idx_integrations_status ON integrations(status);

-- Evaluation indexes
CREATE INDEX idx_task_evaluations_task_id ON task_evaluations(task_id);
CREATE INDEX idx_task_evaluations_type ON task_evaluations(evaluation_type);
CREATE INDEX idx_task_evaluations_evaluated_at ON task_evaluations(evaluated_at);

CREATE INDEX idx_workflow_evaluations_workflow_id ON workflow_evaluations(workflow_id);
CREATE INDEX idx_workflow_evaluations_type ON workflow_evaluations(evaluation_type);

-- Audit indexes
CREATE INDEX idx_task_audit_log_task_id ON task_audit_log(task_id);
CREATE INDEX idx_task_audit_log_changed_at ON task_audit_log(changed_at);
CREATE INDEX idx_system_events_occurred_at ON system_events(occurred_at);
CREATE INDEX idx_system_events_type ON system_events(event_type);
CREATE INDEX idx_system_events_severity ON system_events(severity);

-- Triggers for automatic timestamp updates

-- Update tasks.updated_at on changes
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_tasks_updated_at 
    BEFORE UPDATE ON tasks 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_workflows_updated_at 
    BEFORE UPDATE ON workflows 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_integrations_updated_at 
    BEFORE UPDATE ON integrations 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for task audit logging
CREATE OR REPLACE FUNCTION log_task_changes()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'UPDATE' THEN
        INSERT INTO task_audit_log (task_id, action, old_values, new_values, changed_by)
        VALUES (
            NEW.id,
            'UPDATE',
            row_to_json(OLD),
            row_to_json(NEW),
            current_user
        );
        RETURN NEW;
    ELSIF TG_OP = 'INSERT' THEN
        INSERT INTO task_audit_log (task_id, action, new_values, changed_by)
        VALUES (
            NEW.id,
            'INSERT',
            row_to_json(NEW),
            current_user
        );
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO task_audit_log (task_id, action, old_values, changed_by)
        VALUES (
            OLD.id,
            'DELETE',
            row_to_json(OLD),
            current_user
        );
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ language 'plpgsql';

CREATE TRIGGER task_audit_trigger
    AFTER INSERT OR UPDATE OR DELETE ON tasks
    FOR EACH ROW
    EXECUTE FUNCTION log_task_changes();

-- Views for common queries

-- Active tasks view
CREATE VIEW active_tasks AS
SELECT 
    t.*,
    EXTRACT(EPOCH FROM (NOW() - t.started_at)) as running_duration_seconds,
    CASE 
        WHEN t.deadline IS NOT NULL AND t.deadline < NOW() THEN true 
        ELSE false 
    END as is_overdue
FROM tasks t
WHERE t.status IN ('running', 'queued', 'paused');

-- Task performance summary view
CREATE VIEW task_performance_summary AS
SELECT 
    t.task_type,
    t.status,
    COUNT(*) as task_count,
    AVG(t.actual_duration_seconds) as avg_duration_seconds,
    MIN(t.actual_duration_seconds) as min_duration_seconds,
    MAX(t.actual_duration_seconds) as max_duration_seconds,
    AVG(CASE WHEN t.status = 'completed' THEN 1.0 ELSE 0.0 END) as success_rate,
    AVG(t.retry_count) as avg_retry_count
FROM tasks t
WHERE t.completed_at >= NOW() - INTERVAL '30 days'
GROUP BY t.task_type, t.status;

-- Workflow execution summary view
CREATE VIEW workflow_execution_summary AS
SELECT 
    w.id,
    w.name,
    w.status,
    COUNT(ws.id) as total_steps,
    COUNT(CASE WHEN ws.status = 'completed' THEN 1 END) as completed_steps,
    COUNT(CASE WHEN ws.status = 'failed' THEN 1 END) as failed_steps,
    COUNT(CASE WHEN ws.status = 'running' THEN 1 END) as running_steps,
    EXTRACT(EPOCH FROM (COALESCE(w.completed_at, NOW()) - w.started_at)) as execution_duration_seconds,
    w.created_at,
    w.started_at,
    w.completed_at
FROM workflows w
LEFT JOIN workflow_steps ws ON w.id = ws.workflow_id
GROUP BY w.id, w.name, w.status, w.created_at, w.started_at, w.completed_at;

-- System health view
CREATE VIEW system_health AS
SELECT 
    'tasks' as component,
    COUNT(*) as total_count,
    COUNT(CASE WHEN status = 'running' THEN 1 END) as active_count,
    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_count,
    AVG(CASE WHEN status = 'completed' THEN 1.0 ELSE 0.0 END) as success_rate
FROM tasks
WHERE created_at >= NOW() - INTERVAL '24 hours'

UNION ALL

SELECT 
    'workflows' as component,
    COUNT(*) as total_count,
    COUNT(CASE WHEN status = 'running' THEN 1 END) as active_count,
    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_count,
    AVG(CASE WHEN status = 'completed' THEN 1.0 ELSE 0.0 END) as success_rate
FROM workflows
WHERE created_at >= NOW() - INTERVAL '24 hours';

-- Comments for documentation
COMMENT ON TABLE tasks IS 'Core tasks table storing all task information and execution state';
COMMENT ON TABLE workflows IS 'Workflow definitions and execution state';
COMMENT ON TABLE workflow_steps IS 'Individual steps within workflows';
COMMENT ON TABLE task_metrics IS 'Performance and execution metrics for tasks';
COMMENT ON TABLE system_metrics IS 'System-wide performance metrics';
COMMENT ON TABLE integrations IS 'External system integration configurations';
COMMENT ON TABLE task_evaluations IS 'Quality and effectiveness evaluations for tasks';
COMMENT ON TABLE analytics_reports IS 'Generated analytics reports and insights';

-- Grant permissions (adjust as needed for your environment)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO task_management_app;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO task_management_app;

