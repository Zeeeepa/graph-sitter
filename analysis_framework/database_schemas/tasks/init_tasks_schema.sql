-- Tasks Database Schema
-- Manages task workflow, execution, and tracking for codebase analysis

-- Task management and workflow tracking
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    task_type VARCHAR(100) NOT NULL, -- 'analysis', 'generation', 'validation', 'monitoring'
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed', 'cancelled'
    priority INTEGER DEFAULT 5, -- 1-10 scale, 1 = highest priority
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_by VARCHAR(255),
    assigned_to VARCHAR(255),
    parent_task_id UUID REFERENCES tasks(id),
    codebase_id UUID, -- References codebase.repositories.id
    configuration JSONB, -- Task-specific configuration parameters
    metadata JSONB, -- Additional task metadata
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    timeout_seconds INTEGER DEFAULT 3600,
    tags TEXT[], -- Task categorization tags
    dependencies UUID[], -- Array of task IDs this task depends on
    
    CONSTRAINT valid_priority CHECK (priority >= 1 AND priority <= 10),
    CONSTRAINT valid_status CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    CONSTRAINT valid_task_type CHECK (task_type IN ('analysis', 'generation', 'validation', 'monitoring', 'cleanup'))
);

-- Task execution history and audit trail
CREATE TABLE IF NOT EXISTS task_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    execution_number INTEGER NOT NULL, -- Incremental execution counter
    status VARCHAR(50) NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    resource_usage JSONB, -- CPU, memory, disk usage metrics
    logs TEXT, -- Execution logs
    output JSONB, -- Structured execution output
    error_details JSONB, -- Detailed error information
    environment_info JSONB, -- Execution environment details
    
    UNIQUE(task_id, execution_number)
);

-- Task dependencies and relationships
CREATE TABLE IF NOT EXISTS task_dependencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dependent_task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    dependency_task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    dependency_type VARCHAR(50) NOT NULL DEFAULT 'blocks', -- 'blocks', 'triggers', 'optional'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(dependent_task_id, dependency_task_id),
    CONSTRAINT no_self_dependency CHECK (dependent_task_id != dependency_task_id),
    CONSTRAINT valid_dependency_type CHECK (dependency_type IN ('blocks', 'triggers', 'optional'))
);

-- Task scheduling and recurring tasks
CREATE TABLE IF NOT EXISTS task_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_template_id UUID NOT NULL REFERENCES tasks(id),
    schedule_name VARCHAR(255) NOT NULL,
    cron_expression VARCHAR(100), -- Cron-style scheduling
    interval_seconds INTEGER, -- Alternative to cron for simple intervals
    is_active BOOLEAN DEFAULT true,
    next_run_at TIMESTAMP WITH TIME ZONE,
    last_run_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    timezone VARCHAR(50) DEFAULT 'UTC',
    max_instances INTEGER DEFAULT 1, -- Maximum concurrent instances
    
    CONSTRAINT schedule_definition CHECK (
        (cron_expression IS NOT NULL AND interval_seconds IS NULL) OR
        (cron_expression IS NULL AND interval_seconds IS NOT NULL)
    )
);

-- Task templates for reusable task definitions
CREATE TABLE IF NOT EXISTS task_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    task_type VARCHAR(100) NOT NULL,
    default_configuration JSONB,
    parameter_schema JSONB, -- JSON schema for validating parameters
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    version VARCHAR(50) DEFAULT '1.0.0',
    tags TEXT[]
);

-- Task queues for organizing and prioritizing work
CREATE TABLE IF NOT EXISTS task_queues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    max_concurrent_tasks INTEGER DEFAULT 5,
    priority_weight DECIMAL(3,2) DEFAULT 1.0, -- Queue priority multiplier
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    configuration JSONB -- Queue-specific settings
);

-- Task queue assignments
CREATE TABLE IF NOT EXISTS task_queue_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    queue_id UUID NOT NULL REFERENCES task_queues(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    priority_override INTEGER, -- Override task priority for this queue
    
    UNIQUE(task_id, queue_id)
);

-- Task notifications and alerts
CREATE TABLE IF NOT EXISTS task_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    notification_type VARCHAR(50) NOT NULL, -- 'completion', 'failure', 'delay', 'retry'
    recipient VARCHAR(255) NOT NULL, -- Email, user ID, webhook URL
    delivery_method VARCHAR(50) NOT NULL, -- 'email', 'webhook', 'slack', 'linear'
    message TEXT,
    sent_at TIMESTAMP WITH TIME ZONE,
    delivery_status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'sent', 'failed'
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_notification_type CHECK (notification_type IN ('completion', 'failure', 'delay', 'retry', 'started')),
    CONSTRAINT valid_delivery_method CHECK (delivery_method IN ('email', 'webhook', 'slack', 'linear', 'discord')),
    CONSTRAINT valid_delivery_status CHECK (delivery_status IN ('pending', 'sent', 'failed'))
);

-- Indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at);
CREATE INDEX IF NOT EXISTS idx_tasks_codebase_id ON tasks(codebase_id);
CREATE INDEX IF NOT EXISTS idx_tasks_task_type ON tasks(task_type);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);
CREATE INDEX IF NOT EXISTS idx_tasks_assigned_to ON tasks(assigned_to);
CREATE INDEX IF NOT EXISTS idx_tasks_parent_task_id ON tasks(parent_task_id);

CREATE INDEX IF NOT EXISTS idx_task_executions_task_id ON task_executions(task_id);
CREATE INDEX IF NOT EXISTS idx_task_executions_started_at ON task_executions(started_at);
CREATE INDEX IF NOT EXISTS idx_task_executions_status ON task_executions(status);

CREATE INDEX IF NOT EXISTS idx_task_dependencies_dependent ON task_dependencies(dependent_task_id);
CREATE INDEX IF NOT EXISTS idx_task_dependencies_dependency ON task_dependencies(dependency_task_id);

CREATE INDEX IF NOT EXISTS idx_task_schedules_next_run ON task_schedules(next_run_at) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_task_schedules_active ON task_schedules(is_active);

CREATE INDEX IF NOT EXISTS idx_task_queue_assignments_queue ON task_queue_assignments(queue_id);
CREATE INDEX IF NOT EXISTS idx_task_queue_assignments_task ON task_queue_assignments(task_id);

CREATE INDEX IF NOT EXISTS idx_task_notifications_task_id ON task_notifications(task_id);
CREATE INDEX IF NOT EXISTS idx_task_notifications_delivery_status ON task_notifications(delivery_status);

-- Triggers for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_task_schedules_updated_at BEFORE UPDATE ON task_schedules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_task_templates_updated_at BEFORE UPDATE ON task_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Views for common queries
CREATE OR REPLACE VIEW active_tasks AS
SELECT * FROM tasks 
WHERE status IN ('pending', 'running')
ORDER BY priority ASC, created_at ASC;

CREATE OR REPLACE VIEW failed_tasks AS
SELECT t.*, te.error_details, te.logs
FROM tasks t
LEFT JOIN task_executions te ON t.id = te.task_id
WHERE t.status = 'failed'
ORDER BY t.updated_at DESC;

CREATE OR REPLACE VIEW task_execution_summary AS
SELECT 
    t.id,
    t.name,
    t.task_type,
    t.status,
    COUNT(te.id) as execution_count,
    AVG(te.duration_seconds) as avg_duration_seconds,
    MAX(te.completed_at) as last_execution,
    SUM(CASE WHEN te.status = 'failed' THEN 1 ELSE 0 END) as failure_count
FROM tasks t
LEFT JOIN task_executions te ON t.id = te.task_id
GROUP BY t.id, t.name, t.task_type, t.status;

-- Sample data for testing
INSERT INTO task_templates (name, description, task_type, default_configuration, parameter_schema) VALUES
('codebase_analysis', 'Comprehensive codebase analysis', 'analysis', 
 '{"include_metrics": true, "include_dependencies": true, "include_quality": true}',
 '{"type": "object", "properties": {"repo_url": {"type": "string"}, "language": {"type": "string"}}}'),
('dependency_analysis', 'Analyze code dependencies', 'analysis',
 '{"depth": 5, "include_external": true}',
 '{"type": "object", "properties": {"codebase_id": {"type": "string"}}}'),
('quality_metrics', 'Calculate code quality metrics', 'analysis',
 '{"metrics": ["complexity", "maintainability", "coverage"]}',
 '{"type": "object", "properties": {"file_patterns": {"type": "array"}}}');

INSERT INTO task_queues (name, description, max_concurrent_tasks, priority_weight) VALUES
('analysis_queue', 'Queue for codebase analysis tasks', 3, 1.0),
('generation_queue', 'Queue for code generation tasks', 2, 1.2),
('monitoring_queue', 'Queue for monitoring and health check tasks', 5, 0.8);

