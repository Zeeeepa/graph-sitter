-- Core Database Extensions for Comprehensive Task Management System
-- Extends the foundation from PR 47 with Events and Projects modules

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Create custom types for the extended system
CREATE TYPE event_source AS ENUM (
    'linear',
    'slack', 
    'github',
    'deployment',
    'system',
    'openevolve',
    'analytics',
    'task_engine',
    'workflow',
    'custom'
);

CREATE TYPE event_type AS ENUM (
    'issue_created',
    'issue_updated', 
    'issue_closed',
    'comment_added',
    'pr_opened',
    'pr_merged',
    'pr_closed',
    'commit_pushed',
    'deployment_started',
    'deployment_completed',
    'deployment_failed',
    'task_created',
    'task_started',
    'task_completed',
    'task_failed',
    'evaluation_started',
    'evaluation_completed',
    'workflow_triggered',
    'system_alert',
    'custom_event'
);

CREATE TYPE project_status AS ENUM (
    'active',
    'inactive', 
    'archived',
    'planning',
    'development',
    'testing',
    'production',
    'maintenance'
);

CREATE TYPE repository_type AS ENUM (
    'primary',
    'fork',
    'mirror',
    'archive',
    'template'
);

-- Projects Module - Top-level project organization
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Basic project information
    name VARCHAR(255) NOT NULL,
    description TEXT,
    slug VARCHAR(100) UNIQUE NOT NULL,
    
    -- Project metadata
    status project_status DEFAULT 'planning',
    priority INTEGER DEFAULT 0,
    
    -- Configuration
    settings JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    
    -- Ownership and access
    owner_id VARCHAR(255),
    team_ids JSONB DEFAULT '[]',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    archived_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT projects_name_length CHECK (char_length(name) >= 1),
    CONSTRAINT projects_slug_format CHECK (slug ~ '^[a-z0-9-]+$')
);

-- Enhanced repositories table with project association
CREATE TABLE repositories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    
    -- Repository identification
    full_name VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    owner VARCHAR(255) NOT NULL,
    
    -- Repository metadata
    description TEXT,
    language VARCHAR(100),
    languages JSONB DEFAULT '{}',
    
    -- Repository configuration
    type repository_type DEFAULT 'primary',
    is_private BOOLEAN DEFAULT false,
    is_fork BOOLEAN DEFAULT false,
    
    -- GitHub/Git metadata
    github_id BIGINT UNIQUE,
    clone_url VARCHAR(500),
    ssh_url VARCHAR(500),
    default_branch VARCHAR(100) DEFAULT 'main',
    
    -- Statistics
    stars_count INTEGER DEFAULT 0,
    forks_count INTEGER DEFAULT 0,
    size_kb INTEGER DEFAULT 0,
    
    -- Configuration and settings
    settings JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_analyzed_at TIMESTAMP WITH TIME ZONE,
    
    -- Indexes
    INDEX idx_repositories_project (project_id),
    INDEX idx_repositories_full_name (full_name),
    INDEX idx_repositories_owner (owner),
    INDEX idx_repositories_language (language),
    INDEX idx_repositories_github_id (github_id)
);

-- Enhanced codebases table with better tracking
CREATE TABLE codebases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    repository_id UUID REFERENCES repositories(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    
    -- Codebase identification
    branch VARCHAR(255) NOT NULL DEFAULT 'main',
    commit_sha VARCHAR(40) NOT NULL,
    
    -- Analysis metadata
    total_files INTEGER DEFAULT 0,
    total_functions INTEGER DEFAULT 0,
    total_classes INTEGER DEFAULT 0,
    total_lines INTEGER DEFAULT 0,
    languages JSONB DEFAULT '{}',
    
    -- Analysis timing
    analysis_started_at TIMESTAMP WITH TIME ZONE,
    analysis_completed_at TIMESTAMP WITH TIME ZONE,
    analysis_duration_ms INTEGER,
    
    -- Configuration
    analysis_config JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(repository_id, branch, commit_sha),
    INDEX idx_codebases_repository (repository_id),
    INDEX idx_codebases_project (project_id),
    INDEX idx_codebases_branch (branch),
    INDEX idx_codebases_commit (commit_sha)
);

-- Events Module - Comprehensive event tracking
CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Event identification
    source event_source NOT NULL,
    type event_type NOT NULL,
    
    -- Event associations
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    repository_id UUID REFERENCES repositories(id) ON DELETE SET NULL,
    codebase_id UUID REFERENCES codebases(id) ON DELETE SET NULL,
    
    -- External references
    external_id VARCHAR(255), -- GitHub PR ID, Linear issue ID, etc.
    external_url VARCHAR(1000),
    
    -- Event data
    title VARCHAR(500),
    description TEXT,
    event_data JSONB DEFAULT '{}',
    
    -- Event metadata
    actor_id VARCHAR(255),
    actor_name VARCHAR(255),
    actor_email VARCHAR(255),
    
    -- Timing and status
    occurred_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'pending',
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}',
    tags JSONB DEFAULT '[]',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes for efficient querying
    INDEX idx_events_source_type (source, type),
    INDEX idx_events_project (project_id),
    INDEX idx_events_repository (repository_id),
    INDEX idx_events_codebase (codebase_id),
    INDEX idx_events_external_id (external_id),
    INDEX idx_events_actor (actor_id),
    INDEX idx_events_occurred_at (occurred_at),
    INDEX idx_events_status (status),
    
    -- GIN indexes for JSONB fields
    INDEX idx_events_event_data_gin USING gin (event_data),
    INDEX idx_events_metadata_gin USING gin (metadata),
    INDEX idx_events_tags_gin USING gin (tags)
);

-- Event aggregations for analytics
CREATE TABLE event_aggregations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Aggregation scope
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    repository_id UUID REFERENCES repositories(id) ON DELETE CASCADE,
    
    -- Aggregation metadata
    aggregation_type VARCHAR(100) NOT NULL, -- daily, weekly, monthly
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Aggregated data
    event_counts JSONB DEFAULT '{}', -- counts by source and type
    metrics JSONB DEFAULT '{}',
    summary JSONB DEFAULT '{}',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(project_id, repository_id, aggregation_type, period_start),
    INDEX idx_event_aggregations_project (project_id),
    INDEX idx_event_aggregations_repository (repository_id),
    INDEX idx_event_aggregations_period (period_start, period_end),
    INDEX idx_event_aggregations_type (aggregation_type)
);

-- Project analytics and metrics
CREATE TABLE project_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    
    -- Analytics period
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Repository metrics
    total_repositories INTEGER DEFAULT 0,
    active_repositories INTEGER DEFAULT 0,
    
    -- Code metrics
    total_lines_of_code BIGINT DEFAULT 0,
    total_files INTEGER DEFAULT 0,
    total_commits INTEGER DEFAULT 0,
    
    -- Activity metrics
    total_events INTEGER DEFAULT 0,
    unique_contributors INTEGER DEFAULT 0,
    
    -- Quality metrics
    average_complexity DECIMAL(10,4),
    test_coverage DECIMAL(5,2),
    
    -- Detailed metrics
    language_distribution JSONB DEFAULT '{}',
    activity_trends JSONB DEFAULT '{}',
    quality_trends JSONB DEFAULT '{}',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(project_id, period_start, period_end),
    INDEX idx_project_analytics_project (project_id),
    INDEX idx_project_analytics_period (period_start, period_end)
);

-- Cross-project relationships and dependencies
CREATE TABLE project_dependencies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Dependency relationship
    source_project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    target_project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    
    -- Dependency metadata
    dependency_type VARCHAR(100) NOT NULL, -- code, data, service, workflow
    description TEXT,
    
    -- Dependency strength and criticality
    strength VARCHAR(50) DEFAULT 'medium', -- weak, medium, strong
    criticality VARCHAR(50) DEFAULT 'medium', -- low, medium, high, critical
    
    -- Configuration
    metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(source_project_id, target_project_id, dependency_type),
    INDEX idx_project_deps_source (source_project_id),
    INDEX idx_project_deps_target (target_project_id),
    INDEX idx_project_deps_type (dependency_type),
    
    -- Prevent self-dependencies
    CONSTRAINT no_self_dependency CHECK (source_project_id != target_project_id)
);

-- Functions for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for automatic timestamp updates
CREATE TRIGGER update_projects_updated_at 
    BEFORE UPDATE ON projects 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_repositories_updated_at 
    BEFORE UPDATE ON repositories 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_project_dependencies_updated_at 
    BEFORE UPDATE ON project_dependencies 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create views for common queries
CREATE VIEW active_projects AS
SELECT 
    p.*,
    COUNT(r.id) as repository_count,
    COUNT(DISTINCT e.id) as recent_event_count
FROM projects p
LEFT JOIN repositories r ON p.id = r.project_id
LEFT JOIN events e ON p.id = e.project_id 
    AND e.occurred_at > NOW() - INTERVAL '30 days'
WHERE p.status = 'active'
GROUP BY p.id;

CREATE VIEW project_summary AS
SELECT 
    p.id,
    p.name,
    p.status,
    p.created_at,
    COUNT(DISTINCT r.id) as repository_count,
    COUNT(DISTINCT c.id) as codebase_count,
    COUNT(DISTINCT e.id) as total_events,
    MAX(e.occurred_at) as last_activity
FROM projects p
LEFT JOIN repositories r ON p.id = r.project_id
LEFT JOIN codebases c ON p.id = c.project_id
LEFT JOIN events e ON p.id = e.project_id
GROUP BY p.id, p.name, p.status, p.created_at;

-- Comments for documentation
COMMENT ON TABLE projects IS 'Top-level project organization and management';
COMMENT ON TABLE repositories IS 'Repository information with project association';
COMMENT ON TABLE codebases IS 'Codebase analysis results and metadata';
COMMENT ON TABLE events IS 'Comprehensive event tracking across all systems';
COMMENT ON TABLE event_aggregations IS 'Pre-computed event aggregations for analytics';
COMMENT ON TABLE project_analytics IS 'Project-level analytics and metrics';
COMMENT ON TABLE project_dependencies IS 'Cross-project relationships and dependencies';

COMMENT ON COLUMN events.source IS 'Source system that generated the event';
COMMENT ON COLUMN events.type IS 'Specific type of event within the source system';
COMMENT ON COLUMN events.event_data IS 'Flexible JSON storage for event-specific data';
COMMENT ON COLUMN events.external_id IS 'ID in the external system (GitHub PR #, Linear issue ID, etc.)';

