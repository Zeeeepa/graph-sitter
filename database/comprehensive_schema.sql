-- =====================================================
-- COMPREHENSIVE CI/CD DATABASE SCHEMA
-- Consolidating and enhancing features from PRs 74, 75, 76, and 79
-- =====================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- =====================================================
-- MODULE 1: ORGANIZATIONS & USERS (Multi-tenant)
-- =====================================================

-- Organizations table - Core tenant isolation
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    codegen_org_id VARCHAR(100) NOT NULL UNIQUE,
    api_token_hash TEXT,
    settings JSONB DEFAULT '{}',
    subscription_tier VARCHAR(50) DEFAULT 'free',
    max_users INTEGER DEFAULT 10,
    max_repositories INTEGER DEFAULT 5,
    max_monthly_tasks INTEGER DEFAULT 1000,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_slug CHECK (slug ~ '^[a-z0-9-]+$'),
    CONSTRAINT valid_subscription_tier CHECK (subscription_tier IN ('free', 'pro', 'enterprise'))
);

-- Users table with external platform integration
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'member',
    external_ids JSONB DEFAULT '{}', -- GitHub, Linear, Slack IDs
    settings JSONB DEFAULT '{}',
    avatar_url TEXT,
    timezone VARCHAR(50) DEFAULT 'UTC',
    last_active_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(organization_id, email),
    CONSTRAINT valid_role CHECK (role IN ('owner', 'admin', 'member', 'viewer')),
    CONSTRAINT valid_email CHECK (email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- =====================================================
-- MODULE 2: PROJECTS & REPOSITORIES
-- =====================================================

-- Projects table for organizing repositories and work
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    repository_url VARCHAR(500),
    github_repo_id BIGINT,
    linear_project_id VARCHAR(100),
    slack_channel_id VARCHAR(100),
    status VARCHAR(50) DEFAULT 'active',
    settings JSONB DEFAULT '{}',
    owner_id UUID REFERENCES users(id) ON DELETE SET NULL,
    visibility VARCHAR(20) DEFAULT 'private',
    tags JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(organization_id, name),
    CONSTRAINT valid_status CHECK (status IN ('active', 'archived', 'suspended')),
    CONSTRAINT valid_visibility CHECK (visibility IN ('private', 'internal', 'public'))
);

-- Repositories table with comprehensive tracking
CREATE TABLE repositories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    full_name VARCHAR(500) NOT NULL, -- org/repo format
    provider VARCHAR(50) NOT NULL DEFAULT 'github',
    external_id VARCHAR(255) NOT NULL,
    clone_url TEXT,
    ssh_url TEXT,
    default_branch VARCHAR(255) DEFAULT 'main',
    description TEXT,
    language VARCHAR(100),
    languages JSONB DEFAULT '{}',
    size_kb INTEGER DEFAULT 0,
    stars_count INTEGER DEFAULT 0,
    forks_count INTEGER DEFAULT 0,
    open_issues_count INTEGER DEFAULT 0,
    analysis_config JSONB DEFAULT '{}',
    webhook_config JSONB DEFAULT '{}',
    sync_settings JSONB DEFAULT '{}',
    last_analyzed_at TIMESTAMP WITH TIME ZONE,
    last_synced_at TIMESTAMP WITH TIME ZONE,
    is_private BOOLEAN DEFAULT true,
    is_archived BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(organization_id, provider, external_id),
    CONSTRAINT valid_provider CHECK (provider IN ('github', 'gitlab', 'bitbucket'))
);

-- =====================================================
-- MODULE 3: TASK MANAGEMENT (Hierarchical)
-- =====================================================

-- Task types and status enums
CREATE TYPE task_type AS ENUM (
    'epic', 'feature', 'story', 'task', 'bug', 'research', 
    'documentation', 'testing', 'deployment', 'maintenance'
);

CREATE TYPE task_status AS ENUM (
    'backlog', 'todo', 'in_progress', 'in_review', 
    'testing', 'done', 'cancelled', 'blocked'
);

CREATE TYPE task_priority AS ENUM (
    'critical', 'high', 'medium', 'low', 'none'
);

-- Main tasks table with hierarchical support
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    parent_task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    codegen_task_id VARCHAR(100),
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

-- Task dependencies
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

-- =====================================================
-- MODULE 4: CI/CD PIPELINES
-- =====================================================

-- Pipeline definitions
CREATE TABLE pipelines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
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
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
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
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
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

-- =====================================================
-- MODULE 5: CODEGEN SDK INTEGRATION
-- =====================================================

-- Codegen agents
CREATE TABLE codegen_agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
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

-- =====================================================
-- MODULE 6: PLATFORM INTEGRATIONS
-- =====================================================

-- GitHub integrations
CREATE TABLE github_integrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
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
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
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
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
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
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
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
-- MODULE 7: ANALYTICS & LEARNING
-- =====================================================

-- System metrics
CREATE TABLE system_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    metric_name VARCHAR(255) NOT NULL,
    metric_type VARCHAR(100) NOT NULL, -- 'performance', 'usage', 'cost', 'quality'
    value DECIMAL(15,6) NOT NULL,
    unit VARCHAR(50),
    context JSONB DEFAULT '{}',
    tags JSONB DEFAULT '[]',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Learning patterns
CREATE TABLE learning_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    pattern_type VARCHAR(100) NOT NULL, -- 'success', 'failure', 'optimization'
    pattern_data JSONB NOT NULL,
    confidence_score DECIMAL(3,2) DEFAULT 0.5,
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Audit logs for security tracking
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id UUID,
    details JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- PERFORMANCE INDEXES
-- =====================================================

-- Organizations
CREATE INDEX idx_organizations_slug ON organizations(slug);
CREATE INDEX idx_organizations_codegen_org_id ON organizations(codegen_org_id);

-- Users
CREATE INDEX idx_users_org_email ON users(organization_id, email);
CREATE INDEX idx_users_org_role ON users(organization_id, role);
CREATE INDEX idx_users_external_ids ON users USING GIN (external_ids);

-- Projects
CREATE INDEX idx_projects_org_status ON projects(organization_id, status);
CREATE INDEX idx_projects_owner ON projects(owner_id);
CREATE INDEX idx_projects_tags ON projects USING GIN (tags);

-- Repositories
CREATE INDEX idx_repositories_org_project ON repositories(organization_id, project_id);
CREATE INDEX idx_repositories_provider_external ON repositories(provider, external_id);
CREATE INDEX idx_repositories_full_name ON repositories(full_name);

-- Tasks
CREATE INDEX idx_tasks_org_project ON tasks(organization_id, project_id);
CREATE INDEX idx_tasks_parent ON tasks(parent_task_id);
CREATE INDEX idx_tasks_assignee_status ON tasks(assignee_id, status);
CREATE INDEX idx_tasks_external_refs ON tasks USING GIN (external_refs);

-- Pipelines
CREATE INDEX idx_pipelines_org_project ON pipelines(organization_id, project_id);
CREATE INDEX idx_pipeline_executions_status ON pipeline_executions(status, started_at);

-- Codegen Agents
CREATE INDEX idx_codegen_agents_org_type ON codegen_agents(organization_id, agent_type);
CREATE INDEX idx_agent_tasks_status ON agent_tasks(status, created_at);

-- Integrations
CREATE INDEX idx_github_integrations_org ON github_integrations(organization_id);
CREATE INDEX idx_linear_integrations_org ON linear_integrations(organization_id);
CREATE INDEX idx_slack_integrations_org ON slack_integrations(organization_id);
CREATE INDEX idx_integration_events_type_processed ON integration_events(integration_type, processed);

-- Analytics
CREATE INDEX idx_system_metrics_org_type ON system_metrics(organization_id, metric_type, timestamp);
CREATE INDEX idx_learning_patterns_org_type ON learning_patterns(organization_id, pattern_type);
CREATE INDEX idx_audit_logs_org_action ON audit_logs(organization_id, action, created_at);

-- =====================================================
-- UTILITY FUNCTIONS
-- =====================================================

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply update triggers
CREATE TRIGGER update_organizations_updated_at 
    BEFORE UPDATE ON organizations 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_projects_updated_at 
    BEFORE UPDATE ON projects 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_repositories_updated_at 
    BEFORE UPDATE ON repositories 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tasks_updated_at 
    BEFORE UPDATE ON tasks 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_pipelines_updated_at 
    BEFORE UPDATE ON pipelines 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_codegen_agents_updated_at 
    BEFORE UPDATE ON codegen_agents 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- System health check function
CREATE OR REPLACE FUNCTION get_system_health()
RETURNS JSONB AS $$
DECLARE
    result JSONB := '{}';
    table_count INTEGER;
    active_tasks INTEGER;
    recent_executions INTEGER;
BEGIN
    -- Count tables
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables 
    WHERE table_schema = 'public';
    
    -- Count active tasks
    SELECT COUNT(*) INTO active_tasks
    FROM tasks 
    WHERE status IN ('in_progress', 'in_review');
    
    -- Count recent pipeline executions
    SELECT COUNT(*) INTO recent_executions
    FROM pipeline_executions 
    WHERE created_at >= NOW() - INTERVAL '24 hours';
    
    -- Build result
    result := jsonb_build_object(
        'status', 'healthy',
        'timestamp', NOW(),
        'database_tables', table_count,
        'active_tasks', active_tasks,
        'recent_executions', recent_executions,
        'modules', jsonb_build_object(
            'organizations', true,
            'projects', true,
            'tasks', true,
            'pipelines', true,
            'agents', true,
            'integrations', true,
            'analytics', true
        )
    );
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Data cleanup function
CREATE OR REPLACE FUNCTION cleanup_old_data(retention_days INTEGER DEFAULT 90)
RETURNS JSONB AS $$
DECLARE
    deleted_count INTEGER := 0;
    result JSONB;
BEGIN
    -- Clean up old audit logs
    DELETE FROM audit_logs 
    WHERE created_at < NOW() - INTERVAL '1 day' * retention_days;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Clean up old system metrics
    DELETE FROM system_metrics 
    WHERE timestamp < NOW() - INTERVAL '1 day' * retention_days;
    
    -- Clean up processed integration events
    DELETE FROM integration_events 
    WHERE processed = true AND created_at < NOW() - INTERVAL '1 day' * (retention_days / 3);
    
    result := jsonb_build_object(
        'status', 'completed',
        'timestamp', NOW(),
        'deleted_audit_logs', deleted_count,
        'retention_days', retention_days
    );
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Insert initial data
INSERT INTO organizations (name, slug, codegen_org_id) VALUES 
('Default Organization', 'default', '323');

-- Comments for documentation
COMMENT ON TABLE organizations IS 'Multi-tenant organization management with Codegen SDK integration';
COMMENT ON TABLE tasks IS 'Hierarchical task management with unlimited nesting and dependency tracking';
COMMENT ON TABLE pipelines IS 'CI/CD pipeline definitions and execution tracking';
COMMENT ON TABLE codegen_agents IS 'Codegen SDK agent management and capability tracking';
COMMENT ON TABLE learning_patterns IS 'Continuous learning patterns for system improvement';

-- Schema version tracking
CREATE TABLE schema_migrations (
    id SERIAL PRIMARY KEY,
    version VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

INSERT INTO schema_migrations (version, description) VALUES 
('comprehensive_v1.0.0', 'Comprehensive CI/CD schema consolidating PRs 74, 75, 76, and 79');

