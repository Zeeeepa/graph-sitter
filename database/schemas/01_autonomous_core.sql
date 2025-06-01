-- =============================================================================
-- AUTONOMOUS DEVELOPMENT CORE SCHEMA
-- =============================================================================
-- Simplified, single-user focused database schema for intelligent autonomous
-- software development with comprehensive learning and self-improvement capabilities
-- =============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "btree_gist";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- =============================================================================
-- CORE ENUMS AND TYPES
-- =============================================================================

-- Priority levels for tasks and issues
CREATE TYPE priority_level AS ENUM (
    'low',
    'normal', 
    'high',
    'urgent',
    'critical'
);

-- Status types for various entities
CREATE TYPE status_type AS ENUM (
    'active',
    'inactive',
    'pending',
    'completed',
    'failed',
    'cancelled'
);

-- Programming languages for code analysis
CREATE TYPE language_type AS ENUM (
    'python',
    'typescript', 
    'javascript',
    'java',
    'cpp',
    'rust',
    'go',
    'php',
    'ruby',
    'swift',
    'kotlin',
    'csharp',
    'sql',
    'html',
    'css',
    'markdown',
    'yaml',
    'json',
    'xml',
    'shell',
    'dockerfile',
    'other'
);

-- Analysis types for comprehensive code analysis
CREATE TYPE analysis_type AS ENUM (
    'complexity',
    'dependencies',
    'dead_code',
    'security',
    'performance',
    'quality',
    'coverage',
    'documentation',
    'maintainability',
    'technical_debt',
    'full_codebase'
);

-- =============================================================================
-- CORE SYSTEM TABLES
-- =============================================================================

-- System configuration - centralized settings management
CREATE TABLE system_configuration (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    config_key VARCHAR(255) UNIQUE NOT NULL,
    config_value JSONB NOT NULL,
    description TEXT,
    category VARCHAR(100) DEFAULT 'general',
    is_sensitive BOOLEAN DEFAULT false,
    is_readonly BOOLEAN DEFAULT false,
    validation_schema JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Codebases - track repositories and projects
CREATE TABLE codebases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    repository_url VARCHAR(500),
    local_path TEXT,
    primary_language language_type,
    
    -- Repository metadata
    github_repo_id BIGINT,
    default_branch VARCHAR(100) DEFAULT 'main',
    
    -- Integration settings
    linear_project_id VARCHAR(100),
    slack_channel_id VARCHAR(100),
    
    -- Analysis tracking
    last_analyzed_at TIMESTAMP WITH TIME ZONE,
    analysis_status VARCHAR(50) DEFAULT 'pending',
    
    -- Configuration
    settings JSONB DEFAULT '{}',
    
    -- Status and lifecycle
    status status_type DEFAULT 'active',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT codebases_name_not_empty CHECK (length(trim(name)) > 0)
);

-- Tasks - autonomous task management and execution
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    codebase_id UUID REFERENCES codebases(id) ON DELETE CASCADE,
    parent_task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    
    -- Task identification
    title VARCHAR(500) NOT NULL,
    description TEXT,
    task_type VARCHAR(100) NOT NULL, -- 'feature', 'bug', 'refactor', 'test', 'docs', 'analysis', 'optimization'
    
    -- Priority and scheduling
    priority priority_level DEFAULT 'normal',
    status status_type DEFAULT 'pending',
    
    -- Execution tracking
    codegen_task_id VARCHAR(100),
    estimated_hours DECIMAL(5,2),
    actual_hours DECIMAL(5,2),
    
    -- Dependencies and relationships
    dependencies JSONB DEFAULT '[]', -- Array of task IDs
    blocks JSONB DEFAULT '[]', -- Tasks this blocks
    
    -- Context and metadata
    context JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    
    -- Timing
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    due_date TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT tasks_title_not_empty CHECK (length(trim(title)) > 0)
);

-- Task executions - track autonomous task execution
CREATE TABLE task_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    
    -- Execution metadata
    codegen_execution_id VARCHAR(100),
    agent_type VARCHAR(100), -- 'codegen', 'contexten', 'graph_sitter'
    
    -- Execution details
    status status_type NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER,
    
    -- Results and logging
    result JSONB DEFAULT '{}',
    logs TEXT,
    error_message TEXT,
    
    -- Performance metrics
    metrics JSONB DEFAULT '{}',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Codegen agents - AI agent management and tracking
CREATE TABLE codegen_agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    agent_type VARCHAR(100) NOT NULL, -- 'general', 'reviewer', 'tester', 'analyzer', 'optimizer'
    
    -- Configuration
    configuration JSONB DEFAULT '{}',
    capabilities JSONB DEFAULT '[]',
    
    -- Status and usage
    is_active BOOLEAN DEFAULT true,
    last_used_at TIMESTAMP WITH TIME ZONE,
    usage_stats JSONB DEFAULT '{}',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Agent tasks - track AI agent interactions
CREATE TABLE agent_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES codegen_agents(id) ON DELETE CASCADE,
    task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
    
    -- Task details
    codegen_task_id VARCHAR(100) UNIQUE,
    prompt TEXT NOT NULL,
    context JSONB DEFAULT '{}',
    
    -- Execution
    status status_type DEFAULT 'pending',
    priority priority_level DEFAULT 'normal',
    
    -- Results
    result JSONB DEFAULT '{}',
    error_message TEXT,
    
    -- Performance tracking
    tokens_used INTEGER,
    cost_estimate DECIMAL(10,4),
    
    -- Timing
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- AUDIT AND MONITORING
-- =============================================================================

-- Audit log - comprehensive change tracking
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- What changed
    table_name VARCHAR(255) NOT NULL,
    record_id UUID NOT NULL,
    operation VARCHAR(20) NOT NULL, -- INSERT, UPDATE, DELETE
    
    -- Change details
    old_values JSONB,
    new_values JSONB,
    changed_fields JSONB DEFAULT '[]',
    
    -- Context
    context JSONB DEFAULT '{}',
    session_id VARCHAR(255),
    
    -- Timing
    occurred_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Performance metrics - system performance tracking
CREATE TABLE performance_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Metric identification
    metric_name VARCHAR(255) NOT NULL,
    metric_type VARCHAR(100) NOT NULL, -- 'system', 'task', 'agent', 'codebase'
    
    -- Metric data
    value DECIMAL(15,6) NOT NULL,
    unit VARCHAR(50),
    
    -- Context and dimensions
    context JSONB DEFAULT '{}',
    dimensions JSONB DEFAULT '{}',
    
    -- Timing
    measured_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- UTILITY FUNCTIONS
-- =============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function to get system health overview
CREATE OR REPLACE FUNCTION get_system_health()
RETURNS JSONB AS $$
DECLARE
    result JSONB;
    active_codebases INTEGER;
    pending_tasks INTEGER;
    active_agents INTEGER;
    recent_executions INTEGER;
BEGIN
    -- Count active entities
    SELECT COUNT(*) INTO active_codebases FROM codebases WHERE status = 'active';
    SELECT COUNT(*) INTO pending_tasks FROM tasks WHERE status = 'pending';
    SELECT COUNT(*) INTO active_agents FROM codegen_agents WHERE is_active = true;
    SELECT COUNT(*) INTO recent_executions 
    FROM task_executions 
    WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours';
    
    -- Build health report
    result := jsonb_build_object(
        'status', 'healthy',
        'timestamp', CURRENT_TIMESTAMP,
        'active_codebases', active_codebases,
        'pending_tasks', pending_tasks,
        'active_agents', active_agents,
        'recent_executions', recent_executions,
        'database_size_mb', pg_database_size(current_database()) / 1024 / 1024
    );
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- TRIGGERS
-- =============================================================================

-- Auto-update timestamps
CREATE TRIGGER update_system_configuration_updated_at 
    BEFORE UPDATE ON system_configuration 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_codebases_updated_at 
    BEFORE UPDATE ON codebases 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tasks_updated_at 
    BEFORE UPDATE ON tasks 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_codegen_agents_updated_at 
    BEFORE UPDATE ON codegen_agents 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- INDEXES FOR PERFORMANCE
-- =============================================================================

-- System configuration indexes
CREATE INDEX idx_system_config_key ON system_configuration(config_key);
CREATE INDEX idx_system_config_category ON system_configuration(category);

-- Codebase indexes
CREATE INDEX idx_codebases_name ON codebases(name);
CREATE INDEX idx_codebases_status ON codebases(status);
CREATE INDEX idx_codebases_language ON codebases(primary_language);
CREATE INDEX idx_codebases_last_analyzed ON codebases(last_analyzed_at);

-- Task indexes
CREATE INDEX idx_tasks_codebase ON tasks(codebase_id);
CREATE INDEX idx_tasks_parent ON tasks(parent_task_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_priority ON tasks(priority);
CREATE INDEX idx_tasks_type ON tasks(task_type);
CREATE INDEX idx_tasks_created_at ON tasks(created_at);

-- Task execution indexes
CREATE INDEX idx_task_executions_task ON task_executions(task_id);
CREATE INDEX idx_task_executions_status ON task_executions(status);
CREATE INDEX idx_task_executions_agent ON task_executions(agent_type);
CREATE INDEX idx_task_executions_created_at ON task_executions(created_at);

-- Agent indexes
CREATE INDEX idx_codegen_agents_type ON codegen_agents(agent_type);
CREATE INDEX idx_codegen_agents_active ON codegen_agents(is_active);
CREATE INDEX idx_agent_tasks_agent ON agent_tasks(agent_id);
CREATE INDEX idx_agent_tasks_status ON agent_tasks(status);
CREATE INDEX idx_agent_tasks_codegen_id ON agent_tasks(codegen_task_id);

-- Audit and monitoring indexes
CREATE INDEX idx_audit_log_table ON audit_log(table_name);
CREATE INDEX idx_audit_log_record ON audit_log(record_id);
CREATE INDEX idx_audit_log_occurred_at ON audit_log(occurred_at);
CREATE INDEX idx_performance_metrics_name ON performance_metrics(metric_name);
CREATE INDEX idx_performance_metrics_type ON performance_metrics(metric_type);
CREATE INDEX idx_performance_metrics_measured_at ON performance_metrics(measured_at);

-- JSONB indexes for efficient querying
CREATE INDEX idx_tasks_dependencies_gin USING gin (dependencies);
CREATE INDEX idx_tasks_metadata_gin USING gin (metadata);
CREATE INDEX idx_codebases_settings_gin USING gin (settings);
CREATE INDEX idx_agent_tasks_context_gin USING gin (context);
CREATE INDEX idx_performance_metrics_context_gin USING gin (context);

-- Full-text search indexes
CREATE INDEX idx_tasks_title_search ON tasks USING gin(to_tsvector('english', title));
CREATE INDEX idx_tasks_description_search ON tasks USING gin(to_tsvector('english', description));

-- =============================================================================
-- INITIAL CONFIGURATION
-- =============================================================================

-- Insert essential system configuration
INSERT INTO system_configuration (config_key, config_value, description, category) VALUES
-- System settings
('system.version', '"1.0.0"', 'System version', 'system'),
('system.maintenance_mode', 'false', 'System maintenance mode', 'system'),
('system.max_concurrent_tasks', '10', 'Maximum concurrent task executions', 'system'),

-- Codegen SDK settings
('codegen.org_id', '""', 'Codegen organization ID', 'codegen'),
('codegen.token', '""', 'Codegen API token', 'codegen'),
('codegen.default_timeout_ms', '300000', 'Default timeout for Codegen tasks', 'codegen'),

-- OpenEvolve settings
('openevolve.enabled', 'true', 'Enable OpenEvolve integration', 'openevolve'),
('openevolve.evaluation_timeout_ms', '30000', 'Timeout for evaluations', 'openevolve'),
('openevolve.max_generations', '100', 'Maximum evolution generations', 'openevolve'),

-- Analytics settings
('analytics.retention_days', '365', 'Data retention period', 'analytics'),
('analytics.aggregation_interval_hours', '24', 'Analytics aggregation interval', 'analytics'),

-- Autogenlib settings
('autogenlib.enabled', 'true', 'Enable autogenlib integration', 'autogenlib'),
('autogenlib.cache_ttl_seconds', '3600', 'Cache TTL for generated code', 'autogenlib'),

-- Contexten settings
('contexten.github_enabled', 'true', 'Enable GitHub integration', 'contexten'),
('contexten.linear_enabled', 'true', 'Enable Linear integration', 'contexten'),
('contexten.slack_enabled', 'true', 'Enable Slack integration', 'contexten');

-- Create default agents
INSERT INTO codegen_agents (name, description, agent_type, configuration, capabilities) VALUES
('General Assistant', 'Primary autonomous development agent', 'general', 
 '{"model": "claude-3-5-sonnet", "temperature": 0.1}',
 '["code_generation", "code_review", "testing", "documentation"]'),
 
('Code Reviewer', 'Specialized code review and quality assurance agent', 'reviewer',
 '{"model": "claude-3-5-sonnet", "temperature": 0.0, "focus": "quality"}',
 '["code_review", "security_analysis", "performance_analysis"]'),
 
('Test Generator', 'Automated test generation and validation agent', 'tester',
 '{"model": "claude-3-5-sonnet", "temperature": 0.2, "focus": "testing"}',
 '["test_generation", "test_validation", "coverage_analysis"]'),
 
('Code Analyzer', 'Deep code analysis and optimization agent', 'analyzer',
 '{"model": "claude-3-5-sonnet", "temperature": 0.0, "focus": "analysis"}',
 '["complexity_analysis", "dependency_analysis", "dead_code_detection"]'),
 
('Performance Optimizer', 'Performance analysis and optimization agent', 'optimizer',
 '{"model": "claude-3-5-sonnet", "temperature": 0.1, "focus": "performance"}',
 '["performance_analysis", "optimization_suggestions", "bottleneck_detection"]');

-- =============================================================================
-- COMMENTS FOR DOCUMENTATION
-- =============================================================================

COMMENT ON TABLE system_configuration IS 'Centralized system configuration for autonomous development';
COMMENT ON TABLE codebases IS 'Repository and project tracking for autonomous development';
COMMENT ON TABLE tasks IS 'Autonomous task management and execution tracking';
COMMENT ON TABLE task_executions IS 'Detailed execution logs for autonomous tasks';
COMMENT ON TABLE codegen_agents IS 'AI agent management and configuration';
COMMENT ON TABLE agent_tasks IS 'AI agent task execution tracking';
COMMENT ON TABLE audit_log IS 'Comprehensive audit trail for system changes';
COMMENT ON TABLE performance_metrics IS 'System performance monitoring and optimization';

COMMENT ON FUNCTION update_updated_at_column IS 'Automatically update timestamp on record changes';
COMMENT ON FUNCTION get_system_health IS 'Get comprehensive system health overview';

