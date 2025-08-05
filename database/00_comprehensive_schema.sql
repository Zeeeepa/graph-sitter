-- =====================================================
-- COMPREHENSIVE DATABASE SCHEMA FOR GRAPH-SITTER
-- Autonomous CI/CD System with Codegen SDK Integration
-- =====================================================
-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "btree_gist";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- =====================================================
-- MODULE 1: CORE SYSTEM TABLES
-- =====================================================
-- Organizations table
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    codegen_org_id VARCHAR(100) NOT NULL UNIQUE,
    api_token_hash TEXT,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Projects table
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    repository_url VARCHAR(500),
    github_repo_id BIGINT,
    linear_project_id VARCHAR(100),
    slack_channel_id VARCHAR(100),
    status VARCHAR(50) DEFAULT 'active',
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(organization_id, name)
);

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    github_username VARCHAR(100),
    linear_user_id VARCHAR(100),
    slack_user_id VARCHAR(100),
    role VARCHAR(50) DEFAULT 'developer',
    permissions JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(organization_id, email)
);

-- =====================================================
-- MODULE 2: TASK MANAGEMENT SYSTEM
-- =====================================================
-- Task definitions
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    parent_task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    codegen_task_id VARCHAR(100),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    type VARCHAR(100) NOT NULL, -- 'feature', 'bug', 'refactor', 'test', 'docs', 'ci_cd'
    priority INTEGER DEFAULT 3, -- 1=highest, 5=lowest
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'in_progress', 'completed', 'failed', 'cancelled'
    assigned_to UUID REFERENCES users(id),
    created_by UUID REFERENCES users(id),
    estimated_hours DECIMAL(5,2),
    actual_hours DECIMAL(5,2),
    dependencies JSONB DEFAULT '[]', -- Array of task IDs
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    due_date TIMESTAMP WITH TIME ZONE
);

-- Task execution logs
CREATE TABLE task_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    codegen_execution_id VARCHAR(100),
    status VARCHAR(50) NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    logs TEXT,
    result JSONB,
    metrics JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Task dependencies
CREATE TABLE task_dependencies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    depends_on_task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    dependency_type VARCHAR(50) DEFAULT 'blocks', -- 'blocks', 'relates_to', 'subtask'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(task_id, depends_on_task_id)
);

-- =====================================================
-- MODULE 3: CI/CD PIPELINE MANAGEMENT
-- =====================================================
-- Pipeline definitions
CREATE TABLE pipelines (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    type VARCHAR(100) NOT NULL, -- 'build', 'test', 'deploy', 'analysis', 'security'
    trigger_events JSONB DEFAULT '[]', -- Array of trigger events
    configuration JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(project_id, name)
);

-- Pipeline executions
CREATE TABLE pipeline_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pipeline_id UUID NOT NULL REFERENCES pipelines(id) ON DELETE CASCADE,
    task_id UUID REFERENCES tasks(id),
    trigger_event VARCHAR(100),
    trigger_data JSONB,
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'running', 'success', 'failure', 'cancelled'
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    logs TEXT,
    artifacts JSONB DEFAULT '{}',
    metrics JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Pipeline steps
CREATE TABLE pipeline_steps (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pipeline_id UUID NOT NULL REFERENCES pipelines(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    step_order INTEGER NOT NULL,
    type VARCHAR(100) NOT NULL, -- 'command', 'codegen_task', 'webhook', 'condition'
    configuration JSONB NOT NULL,
    timeout_seconds INTEGER DEFAULT 3600,
    retry_count INTEGER DEFAULT 0,
    is_critical BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(pipeline_id, step_order)
);

-- Step executions
CREATE TABLE step_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pipeline_execution_id UUID NOT NULL REFERENCES pipeline_executions(id) ON DELETE CASCADE,
    pipeline_step_id UUID NOT NULL REFERENCES pipeline_steps(id) ON DELETE CASCADE,
    status VARCHAR(50) DEFAULT 'pending',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    exit_code INTEGER,
    stdout TEXT,
    stderr TEXT,
    artifacts JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- MODULE 4: CODEGEN SDK INTEGRATION
-- =====================================================
-- Codegen agents
CREATE TABLE codegen_agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    agent_type VARCHAR(100) NOT NULL, -- 'general', 'reviewer', 'tester', 'deployer'
    configuration JSONB DEFAULT '{}',
    capabilities JSONB DEFAULT '[]', -- Array of capabilities
    is_active BOOLEAN DEFAULT true,
    last_used_at TIMESTAMP WITH TIME ZONE,
    usage_stats JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(organization_id, name)
);

-- Agent tasks (Codegen SDK interactions)
CREATE TABLE agent_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES codegen_agents(id) ON DELETE CASCADE,
    task_id UUID REFERENCES tasks(id),
    codegen_task_id VARCHAR(100) UNIQUE,
    prompt TEXT NOT NULL,
    context JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed'
    priority INTEGER DEFAULT 3,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    result JSONB,
    error_message TEXT,
    tokens_used INTEGER,
    cost_estimate DECIMAL(10,4),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Agent capabilities
CREATE TABLE agent_capabilities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES codegen_agents(id) ON DELETE CASCADE,
    capability_name VARCHAR(100) NOT NULL,
    capability_config JSONB DEFAULT '{}',
    is_enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(agent_id, capability_name)
);

-- =====================================================
-- MODULE 5: INTEGRATION MANAGEMENT
-- =====================================================
-- GitHub integrations
CREATE TABLE github_integrations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    repository_owner VARCHAR(100) NOT NULL,
    repository_name VARCHAR(100) NOT NULL,
    installation_id BIGINT,
    webhook_secret VARCHAR(255),
    access_token_hash TEXT,
    permissions JSONB DEFAULT '{}',
    last_sync_at TIMESTAMP WITH TIME ZONE,
    sync_status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(project_id, repository_owner, repository_name)
);

-- Linear integrations
CREATE TABLE linear_integrations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    team_id VARCHAR(100) NOT NULL,
    api_key_hash TEXT,
    webhook_secret VARCHAR(255),
    sync_settings JSONB DEFAULT '{}',
    last_sync_at TIMESTAMP WITH TIME ZONE,
    sync_status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(project_id, team_id)
);

-- Slack integrations
CREATE TABLE slack_integrations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    workspace_id VARCHAR(100) NOT NULL,
    channel_id VARCHAR(100),
    bot_token_hash TEXT,
    webhook_url_hash TEXT,
    notification_settings JSONB DEFAULT '{}',
    last_sync_at TIMESTAMP WITH TIME ZONE,
    sync_status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(project_id, workspace_id, channel_id)
);

-- Integration events
CREATE TABLE integration_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    integration_type VARCHAR(50) NOT NULL, -- 'github', 'linear', 'slack'
    integration_id UUID NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB NOT NULL,
    processed BOOLEAN DEFAULT false,
    processed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- MODULE 6: ANALYTICS AND MONITORING
-- =====================================================
-- System metrics
CREATE TABLE system_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,4),
    metric_unit VARCHAR(50),
    dimensions JSONB DEFAULT '{}',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Performance analytics
CREATE TABLE performance_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id),
    metric_type VARCHAR(100) NOT NULL, -- 'task_completion', 'pipeline_success', 'agent_performance'
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    metrics JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Audit logs
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id UUID,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Error tracking
CREATE TABLE error_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    error_type VARCHAR(100) NOT NULL,
    error_message TEXT NOT NULL,
    stack_trace TEXT,
    context JSONB DEFAULT '{}',
    severity VARCHAR(20) DEFAULT 'error', -- 'debug', 'info', 'warning', 'error', 'critical'
    resolved BOOLEAN DEFAULT false,
    resolved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- MODULE 7: LEARNING AND OPTIMIZATION
-- =====================================================
-- Learning patterns
CREATE TABLE learning_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    pattern_type VARCHAR(100) NOT NULL, -- 'task_optimization', 'error_prevention', 'performance_improvement'
    pattern_data JSONB NOT NULL,
    confidence_score DECIMAL(3,2), -- 0.00 to 1.00
    usage_count INTEGER DEFAULT 0,
    success_rate DECIMAL(3,2),
    last_applied_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Optimization suggestions
CREATE TABLE optimization_suggestions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id),
    suggestion_type VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    impact_score DECIMAL(3,2), -- 0.00 to 1.00
    effort_estimate INTEGER, -- hours
    implementation_data JSONB,
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'approved', 'implemented', 'rejected'
    created_by_agent UUID REFERENCES codegen_agents(id),
    reviewed_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Knowledge base
CREATE TABLE knowledge_base (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    content_type VARCHAR(50) DEFAULT 'markdown', -- 'markdown', 'code', 'json'
    tags JSONB DEFAULT '[]',
    category VARCHAR(100),
    source VARCHAR(100), -- 'manual', 'auto_generated', 'learned'
    confidence_score DECIMAL(3,2),
    usage_count INTEGER DEFAULT 0,
    last_accessed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- OPENEVOLVE INTEGRATION MODULE
-- =====================================================
-- OpenEvolve evaluations
CREATE TABLE openevolve_evaluations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    evaluation_id VARCHAR(255) UNIQUE NOT NULL,
    target_type VARCHAR(100) NOT NULL, -- 'task', 'pipeline', 'system'
    target_id UUID NOT NULL,
    evaluation_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    results JSONB DEFAULT '{}',
    metrics JSONB DEFAULT '{}',
    improvement_suggestions JSONB DEFAULT '[]',
    effectiveness_score DECIMAL(5,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Pattern analysis results
CREATE TABLE pattern_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    analysis_type VARCHAR(100) NOT NULL,
    data_source VARCHAR(100) NOT NULL,
    time_range_start TIMESTAMP WITH TIME ZONE NOT NULL,
    time_range_end TIMESTAMP WITH TIME ZONE NOT NULL,
    patterns_detected JSONB DEFAULT '[]',
    insights JSONB DEFAULT '{}',
    recommendations JSONB DEFAULT '[]',
    confidence_score DECIMAL(5,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Self-healing incidents
CREATE TABLE self_healing_incidents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    incident_type VARCHAR(100) NOT NULL,
    severity VARCHAR(50) NOT NULL,
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    detection_method VARCHAR(100),
    resolution_method VARCHAR(100),
    resolution_steps JSONB DEFAULT '[]',
    effectiveness_score DECIMAL(5,2),
    manual_intervention_required BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================
-- Core system indexes
CREATE INDEX idx_projects_org_id ON projects(organization_id);
CREATE INDEX idx_users_org_id ON users(organization_id);
CREATE INDEX idx_users_email ON users(email);

-- Task management indexes
CREATE INDEX idx_tasks_org_id ON tasks(organization_id);
CREATE INDEX idx_tasks_project_id ON tasks(project_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_assigned_to ON tasks(assigned_to);
CREATE INDEX idx_tasks_created_at ON tasks(created_at);
CREATE INDEX idx_task_executions_task_id ON task_executions(task_id);
CREATE INDEX idx_task_executions_status ON task_executions(status);

-- Pipeline indexes
CREATE INDEX idx_pipelines_project_id ON pipelines(project_id);
CREATE INDEX idx_pipeline_executions_pipeline_id ON pipeline_executions(pipeline_id);
CREATE INDEX idx_pipeline_executions_status ON pipeline_executions(status);
CREATE INDEX idx_pipeline_executions_created_at ON pipeline_executions(created_at);

-- Codegen SDK indexes
CREATE INDEX idx_codegen_agents_org_id ON codegen_agents(organization_id);
CREATE INDEX idx_agent_tasks_agent_id ON agent_tasks(agent_id);
CREATE INDEX idx_agent_tasks_status ON agent_tasks(status);
CREATE INDEX idx_agent_tasks_codegen_task_id ON agent_tasks(codegen_task_id);

-- Integration indexes
CREATE INDEX idx_github_integrations_project_id ON github_integrations(project_id);
CREATE INDEX idx_linear_integrations_project_id ON linear_integrations(project_id);
CREATE INDEX idx_slack_integrations_project_id ON slack_integrations(project_id);
CREATE INDEX idx_integration_events_type ON integration_events(integration_type);
CREATE INDEX idx_integration_events_processed ON integration_events(processed);

-- Analytics indexes
CREATE INDEX idx_system_metrics_org_id ON system_metrics(organization_id);
CREATE INDEX idx_system_metrics_timestamp ON system_metrics(timestamp);
CREATE INDEX idx_performance_analytics_org_id ON performance_analytics(organization_id);
CREATE INDEX idx_audit_logs_org_id ON audit_logs(organization_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);

-- Learning indexes
CREATE INDEX idx_learning_patterns_org_id ON learning_patterns(organization_id);
CREATE INDEX idx_optimization_suggestions_org_id ON optimization_suggestions(organization_id);
CREATE INDEX idx_knowledge_base_org_id ON knowledge_base(organization_id);
CREATE INDEX idx_knowledge_base_tags ON knowledge_base USING GIN(tags);

-- OpenEvolve indexes
CREATE INDEX idx_openevolve_evaluations_org_id ON openevolve_evaluations(organization_id);
CREATE INDEX idx_openevolve_evaluations_target ON openevolve_evaluations(target_type, target_id);
CREATE INDEX idx_pattern_analysis_org_id ON pattern_analysis(organization_id);
CREATE INDEX idx_self_healing_incidents_org_id ON self_healing_incidents(organization_id);

-- Full-text search indexes
CREATE INDEX idx_tasks_title_search ON tasks USING GIN(to_tsvector('english', title));
CREATE INDEX idx_tasks_description_search ON tasks USING GIN(to_tsvector('english', description));
CREATE INDEX idx_knowledge_base_content_search ON knowledge_base USING GIN(to_tsvector('english', content));

-- =====================================================
-- TRIGGERS FOR AUTOMATIC UPDATES
-- =====================================================
-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers to relevant tables
CREATE TRIGGER update_organizations_updated_at BEFORE UPDATE ON organizations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_pipelines_updated_at BEFORE UPDATE ON pipelines FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_codegen_agents_updated_at BEFORE UPDATE ON codegen_agents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_github_integrations_updated_at BEFORE UPDATE ON github_integrations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_linear_integrations_updated_at BEFORE UPDATE ON linear_integrations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_slack_integrations_updated_at BEFORE UPDATE ON slack_integrations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_learning_patterns_updated_at BEFORE UPDATE ON learning_patterns FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_optimization_suggestions_updated_at BEFORE UPDATE ON optimization_suggestions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_knowledge_base_updated_at BEFORE UPDATE ON knowledge_base FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- UTILITY FUNCTIONS
-- =====================================================
-- Function to get system health
CREATE OR REPLACE FUNCTION get_system_health()
RETURNS JSONB AS $$
DECLARE
    result JSONB;
BEGIN
    SELECT jsonb_build_object(
        'organizations', (SELECT COUNT(*) FROM organizations),
        'projects', (SELECT COUNT(*) FROM projects),
        'tasks', jsonb_build_object(
            'total', (SELECT COUNT(*) FROM tasks),
            'pending', (SELECT COUNT(*) FROM tasks WHERE status = 'pending'),
            'in_progress', (SELECT COUNT(*) FROM tasks WHERE status = 'in_progress'),
            'completed', (SELECT COUNT(*) FROM tasks WHERE status = 'completed'),
            'failed', (SELECT COUNT(*) FROM tasks WHERE status = 'failed')
        ),
        'pipelines', jsonb_build_object(
            'total', (SELECT COUNT(*) FROM pipelines),
            'active', (SELECT COUNT(*) FROM pipelines WHERE is_active = true)
        ),
        'agents', jsonb_build_object(
            'total', (SELECT COUNT(*) FROM codegen_agents),
            'active', (SELECT COUNT(*) FROM codegen_agents WHERE is_active = true)
        ),
        'learning_patterns', (SELECT COUNT(*) FROM learning_patterns WHERE is_active = true),
        'openevolve_evaluations', jsonb_build_object(
            'total', (SELECT COUNT(*) FROM openevolve_evaluations),
            'pending', (SELECT COUNT(*) FROM openevolve_evaluations WHERE status = 'pending'),
            'completed', (SELECT COUNT(*) FROM openevolve_evaluations WHERE status = 'completed')
        ),
        'self_healing_incidents', jsonb_build_object(
            'total', (SELECT COUNT(*) FROM self_healing_incidents),
            'resolved', (SELECT COUNT(*) FROM self_healing_incidents WHERE resolved_at IS NOT NULL)
        ),
        'timestamp', NOW()
    ) INTO result;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Function to clean up old data
CREATE OR REPLACE FUNCTION cleanup_old_data(retention_days INTEGER DEFAULT 90)
RETURNS JSONB AS $$
DECLARE
    deleted_count INTEGER := 0;
    result JSONB;
BEGIN
    -- Clean up old task executions
    DELETE FROM task_executions WHERE created_at < NOW() - INTERVAL '1 day' * retention_days;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Clean up old pipeline executions
    DELETE FROM pipeline_executions WHERE created_at < NOW() - INTERVAL '1 day' * retention_days;
    
    -- Clean up old system metrics
    DELETE FROM system_metrics WHERE created_at < NOW() - INTERVAL '1 day' * retention_days;
    
    -- Clean up old audit logs
    DELETE FROM audit_logs WHERE created_at < NOW() - INTERVAL '1 day' * retention_days;
    
    -- Clean up old error logs that are resolved
    DELETE FROM error_logs WHERE resolved = true AND created_at < NOW() - INTERVAL '1 day' * retention_days;
    
    result := jsonb_build_object(
        'status', 'completed',
        'retention_days', retention_days,
        'records_deleted', deleted_count,
        'timestamp', NOW()
    );
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- INITIAL DATA
-- =====================================================
-- Insert default organization (will be updated with actual values)
INSERT INTO organizations (name, codegen_org_id, settings) VALUES 
('Graph-Sitter Organization', '323', jsonb_build_object(
    'continuous_learning_enabled', true,
    'openevolve_enabled', true,
    'self_healing_enabled', true,
    'analytics_enabled', true
));

-- Insert default project
INSERT INTO projects (organization_id, name, description, repository_url, status) VALUES 
((SELECT id FROM organizations WHERE codegen_org_id = '323'), 
 'Graph-Sitter Core', 
 'Core graph-sitter CI/CD and continuous learning system',
 'https://github.com/Zeeeepa/graph-sitter',
 'active');

-- Insert default admin user
INSERT INTO users (organization_id, email, name, role) VALUES 
((SELECT id FROM organizations WHERE codegen_org_id = '323'),
 'admin@graph-sitter.com',
 'System Administrator',
 'admin');

-- Insert default Codegen agent
INSERT INTO codegen_agents (organization_id, name, description, agent_type, capabilities) VALUES 
((SELECT id FROM organizations WHERE codegen_org_id = '323'),
 'Primary Codegen Agent',
 'Main agent for code generation and analysis tasks',
 'general',
 '["code_generation", "code_analysis", "testing", "documentation", "refactoring"]'::jsonb);

-- =====================================================
-- COMMENTS FOR DOCUMENTATION
-- =====================================================
COMMENT ON TABLE organizations IS 'Top-level organizations with Codegen SDK integration';
COMMENT ON TABLE projects IS 'Projects within organizations with repository and integration settings';
COMMENT ON TABLE tasks IS 'Task management with hierarchical structure and dependencies';
COMMENT ON TABLE pipelines IS 'CI/CD pipeline definitions and configurations';
COMMENT ON TABLE codegen_agents IS 'Codegen SDK agents with capabilities and usage tracking';
COMMENT ON TABLE openevolve_evaluations IS 'OpenEvolve integration for continuous learning and system evolution';
COMMENT ON TABLE learning_patterns IS 'Machine learning patterns for system optimization';
COMMENT ON TABLE self_healing_incidents IS 'Self-healing system incidents and resolutions';

-- =====================================================
-- SCHEMA VERSION TRACKING
-- =====================================================
CREATE TABLE schema_versions (
    id SERIAL PRIMARY KEY,
    version VARCHAR(50) NOT NULL,
    description TEXT,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

INSERT INTO schema_versions (version, description) VALUES 
('1.0.0', 'Comprehensive CI/CD schema with 7 modules: Core, Tasks, Pipelines, Codegen SDK, Integrations, Analytics, Learning & OpenEvolve');

