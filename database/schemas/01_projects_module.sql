-- =============================================================================
-- PROJECTS MODULE SCHEMA
-- =============================================================================
-- This module handles top-level project organization, repository management,
-- and cross-project analytics and reporting.
-- =============================================================================

-- =============================================================================
-- ENUMS
-- =============================================================================

CREATE TYPE project_status AS ENUM (
    'planning',
    'active',
    'on_hold',
    'completed',
    'cancelled',
    'archived'
);

CREATE TYPE repository_status AS ENUM (
    'active',
    'inactive',
    'archived',
    'error'
);

CREATE TYPE repository_visibility AS ENUM (
    'public',
    'private',
    'internal'
);

-- =============================================================================
-- PROJECTS TABLES
-- =============================================================================

-- Projects - top-level project organization
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) NOT NULL,
    description TEXT,
    status project_status DEFAULT 'planning',
    priority priority_level DEFAULT 'medium',
    
    -- Project metadata
    goals TEXT[],
    tags VARCHAR(50)[],
    
    -- Timeline
    start_date DATE,
    target_end_date DATE,
    actual_end_date DATE,
    
    -- Ownership
    owner_id UUID REFERENCES users(id),
    team_members UUID[],
    
    -- Configuration
    settings JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE NULL,
    
    UNIQUE(organization_id, slug)
);

-- Repositories - repository management and configuration
CREATE TABLE repositories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Repository identification
    name VARCHAR(255) NOT NULL,
    full_name VARCHAR(500) NOT NULL, -- e.g., "org/repo"
    external_id VARCHAR(100), -- GitHub/GitLab ID
    
    -- Repository details
    description TEXT,
    url TEXT NOT NULL,
    clone_url TEXT,
    ssh_url TEXT,
    default_branch VARCHAR(100) DEFAULT 'main',
    
    -- Status and visibility
    status repository_status DEFAULT 'active',
    visibility repository_visibility DEFAULT 'private',
    
    -- Repository metrics
    size_kb BIGINT DEFAULT 0,
    language VARCHAR(50),
    languages JSONB DEFAULT '{}', -- Language breakdown
    
    -- Configuration
    config JSONB DEFAULT '{}', -- Repository-specific configuration
    webhook_config JSONB DEFAULT '{}',
    
    -- Analysis settings
    analysis_enabled BOOLEAN DEFAULT true,
    analysis_config JSONB DEFAULT '{}',
    
    -- Timestamps
    last_analyzed_at TIMESTAMP WITH TIME ZONE,
    last_commit_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE NULL,
    
    UNIQUE(organization_id, full_name)
);

-- Repository branches - track important branches
CREATE TABLE repository_branches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    repository_id UUID NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    
    name VARCHAR(255) NOT NULL,
    commit_sha VARCHAR(40),
    is_default BOOLEAN DEFAULT false,
    is_protected BOOLEAN DEFAULT false,
    
    -- Branch metadata
    ahead_by INTEGER DEFAULT 0,
    behind_by INTEGER DEFAULT 0,
    last_commit_message TEXT,
    last_commit_author VARCHAR(255),
    last_commit_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(repository_id, name)
);

-- Project repository relationships (many-to-many)
CREATE TABLE project_repositories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    repository_id UUID NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    
    -- Relationship metadata
    role VARCHAR(50) DEFAULT 'primary', -- primary, dependency, fork, etc.
    importance priority_level DEFAULT 'medium',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(project_id, repository_id)
);

-- =============================================================================
-- INDEXES
-- =============================================================================

-- Projects indexes
CREATE INDEX idx_projects_organization_id ON projects(organization_id);
CREATE INDEX idx_projects_slug ON projects(slug);
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_priority ON projects(priority);
CREATE INDEX idx_projects_owner_id ON projects(owner_id);
CREATE INDEX idx_projects_start_date ON projects(start_date);
CREATE INDEX idx_projects_target_end_date ON projects(target_end_date);
CREATE INDEX idx_projects_created_at ON projects(created_at);
CREATE INDEX idx_projects_deleted_at ON projects(deleted_at) WHERE deleted_at IS NULL;

-- GIN indexes for array and JSONB fields
CREATE INDEX idx_projects_tags ON projects USING GIN(tags);
CREATE INDEX idx_projects_team_members ON projects USING GIN(team_members);
CREATE INDEX idx_projects_settings ON projects USING GIN(settings);
CREATE INDEX idx_projects_metadata ON projects USING GIN(metadata);

-- Repositories indexes
CREATE INDEX idx_repositories_project_id ON repositories(project_id);
CREATE INDEX idx_repositories_organization_id ON repositories(organization_id);
CREATE INDEX idx_repositories_name ON repositories(name);
CREATE INDEX idx_repositories_full_name ON repositories(full_name);
CREATE INDEX idx_repositories_external_id ON repositories(external_id);
CREATE INDEX idx_repositories_status ON repositories(status);
CREATE INDEX idx_repositories_visibility ON repositories(visibility);
CREATE INDEX idx_repositories_language ON repositories(language);
CREATE INDEX idx_repositories_analysis_enabled ON repositories(analysis_enabled);
CREATE INDEX idx_repositories_last_analyzed_at ON repositories(last_analyzed_at);
CREATE INDEX idx_repositories_last_commit_at ON repositories(last_commit_at);
CREATE INDEX idx_repositories_created_at ON repositories(created_at);
CREATE INDEX idx_repositories_deleted_at ON repositories(deleted_at) WHERE deleted_at IS NULL;

-- GIN indexes for JSONB fields
CREATE INDEX idx_repositories_languages ON repositories USING GIN(languages);
CREATE INDEX idx_repositories_config ON repositories USING GIN(config);
CREATE INDEX idx_repositories_webhook_config ON repositories USING GIN(webhook_config);
CREATE INDEX idx_repositories_analysis_config ON repositories USING GIN(analysis_config);

-- Repository branches indexes
CREATE INDEX idx_repository_branches_repository_id ON repository_branches(repository_id);
CREATE INDEX idx_repository_branches_name ON repository_branches(name);
CREATE INDEX idx_repository_branches_is_default ON repository_branches(is_default);
CREATE INDEX idx_repository_branches_is_protected ON repository_branches(is_protected);
CREATE INDEX idx_repository_branches_last_commit_at ON repository_branches(last_commit_at);

-- Project repositories indexes
CREATE INDEX idx_project_repositories_project_id ON project_repositories(project_id);
CREATE INDEX idx_project_repositories_repository_id ON project_repositories(repository_id);
CREATE INDEX idx_project_repositories_role ON project_repositories(role);
CREATE INDEX idx_project_repositories_importance ON project_repositories(importance);

-- =============================================================================
-- TRIGGERS
-- =============================================================================

CREATE TRIGGER trigger_projects_updated_at
    BEFORE UPDATE ON projects
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_repositories_updated_at
    BEFORE UPDATE ON repositories
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_repository_branches_updated_at
    BEFORE UPDATE ON repository_branches
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- VIEWS
-- =============================================================================

-- Project summary view with repository counts
CREATE VIEW project_summary AS
SELECT 
    p.*,
    COUNT(pr.repository_id) as repository_count,
    COUNT(CASE WHEN r.status = 'active' THEN 1 END) as active_repository_count,
    MAX(r.last_commit_at) as latest_commit_at,
    ARRAY_AGG(DISTINCT r.language) FILTER (WHERE r.language IS NOT NULL) as languages_used
FROM projects p
LEFT JOIN project_repositories pr ON p.id = pr.project_id
LEFT JOIN repositories r ON pr.repository_id = r.id AND r.deleted_at IS NULL
WHERE p.deleted_at IS NULL
GROUP BY p.id;

-- Repository summary view with project information
CREATE VIEW repository_summary AS
SELECT 
    r.*,
    p.name as project_name,
    p.slug as project_slug,
    p.status as project_status,
    COUNT(rb.id) as branch_count,
    COUNT(CASE WHEN rb.is_protected THEN 1 END) as protected_branch_count
FROM repositories r
LEFT JOIN project_repositories pr ON r.id = pr.repository_id
LEFT JOIN projects p ON pr.project_id = p.id AND p.deleted_at IS NULL
LEFT JOIN repository_branches rb ON r.id = rb.repository_id
WHERE r.deleted_at IS NULL
GROUP BY r.id, p.name, p.slug, p.status;

-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON TABLE projects IS 'Top-level project organization with goals, timelines, and team management';
COMMENT ON TABLE repositories IS 'Repository management with configuration, metrics, and analysis settings';
COMMENT ON TABLE repository_branches IS 'Track important repository branches with commit information';
COMMENT ON TABLE project_repositories IS 'Many-to-many relationship between projects and repositories';

COMMENT ON VIEW project_summary IS 'Project overview with repository counts and latest activity';
COMMENT ON VIEW repository_summary IS 'Repository overview with project context and branch information';

