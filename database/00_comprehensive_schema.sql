-- =====================================================
-- 🚀 Comprehensive CI/CD Database Schema
-- 7-Module Database Architecture for graph-sitter
-- =====================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- =====================================================
-- MODULE 1: ORGANIZATIONS
-- =====================================================

CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    slug VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true
);

CREATE TABLE organization_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'member',
    permissions JSONB DEFAULT '{}',
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    UNIQUE(organization_id, user_id)
);

-- =====================================================
-- MODULE 2: PROJECTS
-- =====================================================

CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) NOT NULL,
    description TEXT,
    repository_url VARCHAR(500),
    default_branch VARCHAR(100) DEFAULT 'main',
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    UNIQUE(organization_id, slug)
);

CREATE TABLE repositories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    full_name VARCHAR(500) NOT NULL,
    clone_url VARCHAR(500) NOT NULL,
    default_branch VARCHAR(100) DEFAULT 'main',
    language VARCHAR(50),
    framework VARCHAR(100),
    metadata JSONB DEFAULT '{}',
    last_analyzed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(project_id, full_name)
);

-- =====================================================
-- MODULE 3: TASKS & WORKFLOWS
-- =====================================================

CREATE TABLE task_definitions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    task_type VARCHAR(100) NOT NULL,
    template JSONB NOT NULL,
    default_config JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true
);

CREATE TABLE workflows (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    trigger_config JSONB NOT NULL,
    steps JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true
);

CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id UUID REFERENCES workflows(id) ON DELETE SET NULL,
    task_definition_id UUID REFERENCES task_definitions(id) ON DELETE SET NULL,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    priority INTEGER DEFAULT 5,
    config JSONB DEFAULT '{}',
    context JSONB DEFAULT '{}',
    result JSONB,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE task_dependencies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    depends_on_task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    dependency_type VARCHAR(50) DEFAULT 'blocking',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(task_id, depends_on_task_id)
);

-- =====================================================
-- MODULE 4: PIPELINES & AGENTS
-- =====================================================

CREATE TABLE pipelines (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    pipeline_type VARCHAR(100) NOT NULL,
    config JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true
);

CREATE TABLE pipeline_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pipeline_id UUID NOT NULL REFERENCES pipelines(id) ON DELETE CASCADE,
    trigger_event JSONB,
    status VARCHAR(50) NOT NULL DEFAULT 'running',
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    result JSONB,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    agent_type VARCHAR(100) NOT NULL,
    capabilities JSONB DEFAULT '[]',
    config JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'active',
    last_active_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true
);

CREATE TABLE agent_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'assigned',
    result JSONB,
    UNIQUE(agent_id, task_id)
);

-- =====================================================
-- MODULE 5: INTEGRATIONS
-- =====================================================

CREATE TABLE integrations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    integration_type VARCHAR(100) NOT NULL,
    config JSONB NOT NULL,
    credentials JSONB,
    status VARCHAR(50) DEFAULT 'active',
    last_sync_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true
);

CREATE TABLE integration_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    integration_id UUID NOT NULL REFERENCES integrations(id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB NOT NULL,
    processed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE webhooks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    integration_id UUID NOT NULL REFERENCES integrations(id) ON DELETE CASCADE,
    url VARCHAR(500) NOT NULL,
    secret VARCHAR(255),
    events JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- MODULE 6: ANALYTICS & METRICS
-- =====================================================

CREATE TABLE analysis_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    repository_id UUID REFERENCES repositories(id) ON DELETE SET NULL,
    run_type VARCHAR(100) NOT NULL,
    commit_sha VARCHAR(40),
    branch VARCHAR(255),
    config JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'running',
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    result JSONB,
    error_message TEXT
);

CREATE TABLE metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_run_id UUID NOT NULL REFERENCES analysis_runs(id) ON DELETE CASCADE,
    metric_type VARCHAR(100) NOT NULL,
    metric_name VARCHAR(255) NOT NULL,
    metric_value NUMERIC,
    metric_data JSONB,
    file_path VARCHAR(1000),
    function_name VARCHAR(255),
    class_name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE performance_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    metric_type VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    value NUMERIC NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- MODULE 7: CONTINUOUS LEARNING
-- =====================================================

CREATE TABLE learning_models (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    model_type VARCHAR(100) NOT NULL,
    version VARCHAR(50) NOT NULL,
    config JSONB NOT NULL,
    training_data_source JSONB,
    performance_metrics JSONB,
    status VARCHAR(50) DEFAULT 'training',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true
);

CREATE TABLE training_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID NOT NULL REFERENCES learning_models(id) ON DELETE CASCADE,
    session_type VARCHAR(100) NOT NULL,
    training_data JSONB NOT NULL,
    hyperparameters JSONB DEFAULT '{}',
    results JSONB,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    status VARCHAR(50) DEFAULT 'running'
);

CREATE TABLE pattern_recognition (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    pattern_type VARCHAR(100) NOT NULL,
    pattern_data JSONB NOT NULL,
    confidence_score NUMERIC(5,4),
    occurrences INTEGER DEFAULT 1,
    last_seen_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE adaptations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID NOT NULL REFERENCES learning_models(id) ON DELETE CASCADE,
    adaptation_type VARCHAR(100) NOT NULL,
    trigger_pattern_id UUID REFERENCES pattern_recognition(id) ON DELETE SET NULL,
    adaptation_data JSONB NOT NULL,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    effectiveness_score NUMERIC(5,4),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

-- Organizations
CREATE INDEX idx_organizations_slug ON organizations(slug);
CREATE INDEX idx_organization_members_org_user ON organization_members(organization_id, user_id);

-- Projects
CREATE INDEX idx_projects_org_slug ON projects(organization_id, slug);
CREATE INDEX idx_repositories_project ON repositories(project_id);
CREATE INDEX idx_repositories_full_name ON repositories(full_name);

-- Tasks & Workflows
CREATE INDEX idx_tasks_project ON tasks(project_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_workflow ON tasks(workflow_id);
CREATE INDEX idx_task_dependencies_task ON task_dependencies(task_id);
CREATE INDEX idx_workflows_project ON workflows(project_id);

-- Pipelines & Agents
CREATE INDEX idx_pipelines_project ON pipelines(project_id);
CREATE INDEX idx_pipeline_runs_pipeline ON pipeline_runs(pipeline_id);
CREATE INDEX idx_pipeline_runs_status ON pipeline_runs(status);
CREATE INDEX idx_agents_org ON agents(organization_id);
CREATE INDEX idx_agent_tasks_agent ON agent_tasks(agent_id);
CREATE INDEX idx_agent_tasks_task ON agent_tasks(task_id);

-- Integrations
CREATE INDEX idx_integrations_org ON integrations(organization_id);
CREATE INDEX idx_integration_events_integration ON integration_events(integration_id);
CREATE INDEX idx_integration_events_status ON integration_events(status);
CREATE INDEX idx_webhooks_integration ON webhooks(integration_id);

-- Analytics
CREATE INDEX idx_analysis_runs_project ON analysis_runs(project_id);
CREATE INDEX idx_analysis_runs_status ON analysis_runs(status);
CREATE INDEX idx_metrics_analysis_run ON metrics(analysis_run_id);
CREATE INDEX idx_metrics_type_name ON metrics(metric_type, metric_name);
CREATE INDEX idx_performance_data_project ON performance_data(project_id);
CREATE INDEX idx_performance_data_timestamp ON performance_data(timestamp);

-- Learning
CREATE INDEX idx_learning_models_org ON learning_models(organization_id);
CREATE INDEX idx_training_sessions_model ON training_sessions(model_id);
CREATE INDEX idx_pattern_recognition_org ON pattern_recognition(organization_id);
CREATE INDEX idx_pattern_recognition_type ON pattern_recognition(pattern_type);
CREATE INDEX idx_adaptations_model ON adaptations(model_id);

-- Full-text search indexes
CREATE INDEX idx_projects_name_gin ON projects USING gin(name gin_trgm_ops);
CREATE INDEX idx_tasks_name_gin ON tasks USING gin(name gin_trgm_ops);
CREATE INDEX idx_tasks_description_gin ON tasks USING gin(description gin_trgm_ops);

-- =====================================================
-- TRIGGERS FOR UPDATED_AT
-- =====================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply to all tables with updated_at
CREATE TRIGGER update_organizations_updated_at BEFORE UPDATE ON organizations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_repositories_updated_at BEFORE UPDATE ON repositories FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_task_definitions_updated_at BEFORE UPDATE ON task_definitions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_workflows_updated_at BEFORE UPDATE ON workflows FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_pipelines_updated_at BEFORE UPDATE ON pipelines FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_agents_updated_at BEFORE UPDATE ON agents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_integrations_updated_at BEFORE UPDATE ON integrations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_webhooks_updated_at BEFORE UPDATE ON webhooks FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_learning_models_updated_at BEFORE UPDATE ON learning_models FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_pattern_recognition_updated_at BEFORE UPDATE ON pattern_recognition FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- VIEWS FOR COMMON QUERIES
-- =====================================================

-- Active projects with repository count
CREATE VIEW active_projects_summary AS
SELECT 
    p.id,
    p.organization_id,
    p.name,
    p.slug,
    p.description,
    COUNT(r.id) as repository_count,
    p.created_at,
    p.updated_at
FROM projects p
LEFT JOIN repositories r ON p.id = r.project_id
WHERE p.is_active = true
GROUP BY p.id, p.organization_id, p.name, p.slug, p.description, p.created_at, p.updated_at;

-- Task status summary by project
CREATE VIEW task_status_summary AS
SELECT 
    project_id,
    status,
    COUNT(*) as task_count,
    AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) as avg_duration_seconds
FROM tasks
WHERE started_at IS NOT NULL
GROUP BY project_id, status;

-- Recent pipeline runs with success rate
CREATE VIEW pipeline_performance AS
SELECT 
    p.id as pipeline_id,
    p.name,
    p.project_id,
    COUNT(pr.id) as total_runs,
    COUNT(CASE WHEN pr.status = 'success' THEN 1 END) as successful_runs,
    ROUND(
        COUNT(CASE WHEN pr.status = 'success' THEN 1 END)::numeric / 
        NULLIF(COUNT(pr.id), 0) * 100, 2
    ) as success_rate_percent,
    AVG(pr.duration_seconds) as avg_duration_seconds
FROM pipelines p
LEFT JOIN pipeline_runs pr ON p.id = pr.pipeline_id
WHERE pr.created_at >= NOW() - INTERVAL '30 days'
GROUP BY p.id, p.name, p.project_id;

-- =====================================================
-- INITIAL DATA SETUP
-- =====================================================

-- Insert default organization (can be customized)
INSERT INTO organizations (name, slug, description) 
VALUES ('Default Organization', 'default', 'Default organization for graph-sitter CI/CD system')
ON CONFLICT (slug) DO NOTHING;

-- Insert default task definitions
INSERT INTO task_definitions (organization_id, name, description, task_type, template) 
SELECT 
    o.id,
    'Code Analysis',
    'Analyze codebase for metrics and patterns',
    'analysis',
    '{"steps": ["checkout", "analyze", "report"], "timeout": 300}'
FROM organizations o WHERE o.slug = 'default'
ON CONFLICT DO NOTHING;

INSERT INTO task_definitions (organization_id, name, description, task_type, template)
SELECT 
    o.id,
    'PR Review',
    'Automated pull request review and feedback',
    'review',
    '{"steps": ["fetch_pr", "analyze_changes", "generate_feedback"], "timeout": 600}'
FROM organizations o WHERE o.slug = 'default'
ON CONFLICT DO NOTHING;

-- =====================================================
-- COMMENTS AND DOCUMENTATION
-- =====================================================

COMMENT ON TABLE organizations IS 'Core organizations using the CI/CD system';
COMMENT ON TABLE projects IS 'Projects within organizations, can contain multiple repositories';
COMMENT ON TABLE repositories IS 'Individual code repositories associated with projects';
COMMENT ON TABLE tasks IS 'Individual tasks that can be executed by agents or pipelines';
COMMENT ON TABLE workflows IS 'Defined workflows that orchestrate multiple tasks';
COMMENT ON TABLE pipelines IS 'CI/CD pipelines for automated execution';
COMMENT ON TABLE agents IS 'AI agents capable of executing tasks';
COMMENT ON TABLE integrations IS 'External service integrations (GitHub, Linear, Slack, etc.)';
COMMENT ON TABLE learning_models IS 'Machine learning models for continuous improvement';
COMMENT ON TABLE pattern_recognition IS 'Identified patterns for system optimization';

-- =====================================================
-- SCHEMA VERSION TRACKING
-- =====================================================

CREATE TABLE schema_migrations (
    version VARCHAR(50) PRIMARY KEY,
    description TEXT,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

INSERT INTO schema_migrations (version, description) 
VALUES ('1.0.0', 'Initial comprehensive 7-module schema implementation');

