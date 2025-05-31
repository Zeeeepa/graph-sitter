-- =============================================================================
-- PROJECTS MODULE: Project and repository management
-- =============================================================================
-- This module handles project lifecycle management, repository tracking,
-- and cross-project analytics support.
-- =============================================================================

-- Project status enumeration
CREATE TYPE project_status AS ENUM (
    'planning',
    'active',
    'on_hold',
    'completed',
    'cancelled',
    'archived'
);

-- Repository types
CREATE TYPE repository_type AS ENUM (
    'git',
    'svn',
    'mercurial',
    'other'
);

-- =============================================================================
-- PROJECTS TABLE
-- =============================================================================

CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status project_status DEFAULT 'planning',
    priority priority_level DEFAULT 'normal',
    
    -- Project timeline
    start_date DATE,
    end_date DATE,
    estimated_hours INTEGER,
    actual_hours INTEGER DEFAULT 0,
    
    -- Project team
    project_manager_id UUID REFERENCES users(id),
    team_members UUID[] DEFAULT '{}',
    
    -- Configuration and metadata
    configuration JSONB DEFAULT '{}',
    goals TEXT[],
    tags VARCHAR(50)[],
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT projects_name_not_empty CHECK (length(trim(name)) > 0),
    CONSTRAINT projects_dates_valid CHECK (end_date IS NULL OR start_date IS NULL OR end_date >= start_date),
    CONSTRAINT projects_hours_positive CHECK (estimated_hours IS NULL OR estimated_hours > 0),
    CONSTRAINT projects_actual_hours_positive CHECK (actual_hours >= 0)
);

-- =============================================================================
-- REPOSITORIES TABLE
-- =============================================================================

CREATE TABLE repositories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    repository_type repository_type DEFAULT 'git',
    
    -- Repository details
    url TEXT NOT NULL,
    clone_url TEXT,
    ssh_url TEXT,
    default_branch VARCHAR(100) DEFAULT 'main',
    
    -- Repository status
    is_active BOOLEAN DEFAULT true,
    is_private BOOLEAN DEFAULT false,
    is_fork BOOLEAN DEFAULT false,
    
    -- Repository statistics
    size_kb BIGINT DEFAULT 0,
    language VARCHAR(50),
    languages JSONB DEFAULT '{}',
    topics VARCHAR(50)[] DEFAULT '{}',
    
    -- Analysis configuration
    analysis_enabled BOOLEAN DEFAULT true,
    analysis_config JSONB DEFAULT '{}',
    last_analyzed_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    external_id VARCHAR(255), -- GitHub/GitLab ID
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT repositories_name_not_empty CHECK (length(trim(name)) > 0),
    CONSTRAINT repositories_url_not_empty CHECK (length(trim(url)) > 0),
    CONSTRAINT repositories_size_positive CHECK (size_kb >= 0)
);

-- =============================================================================
-- REPOSITORY BRANCHES TABLE
-- =============================================================================

CREATE TABLE repository_branches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    repository_id UUID NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    
    -- Branch details
    commit_sha VARCHAR(40),
    commit_message TEXT,
    commit_author VARCHAR(255),
    commit_date TIMESTAMP WITH TIME ZONE,
    
    -- Branch status
    is_default BOOLEAN DEFAULT false,
    is_protected BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    
    -- Branch statistics
    commits_ahead INTEGER DEFAULT 0,
    commits_behind INTEGER DEFAULT 0,
    last_activity_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT repo_branches_name_not_empty CHECK (length(trim(name)) > 0),
    CONSTRAINT repo_branches_unique UNIQUE (repository_id, name),
    CONSTRAINT repo_branches_commits_positive CHECK (commits_ahead >= 0 AND commits_behind >= 0)
);

-- =============================================================================
-- PROJECT REPOSITORIES RELATIONSHIP TABLE
-- =============================================================================

CREATE TABLE project_repositories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    repository_id UUID NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    
    -- Relationship details
    role VARCHAR(50) DEFAULT 'primary', -- primary, secondary, dependency, etc.
    branch_name VARCHAR(255),
    path_prefix VARCHAR(500), -- For monorepos
    
    -- Configuration
    configuration JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT project_repositories_unique UNIQUE (project_id, repository_id)
);

-- =============================================================================
-- TRIGGERS
-- =============================================================================

-- Update timestamps
CREATE TRIGGER update_projects_updated_at 
    BEFORE UPDATE ON projects 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_repositories_updated_at 
    BEFORE UPDATE ON repositories 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_repository_branches_updated_at 
    BEFORE UPDATE ON repository_branches 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_project_repositories_updated_at 
    BEFORE UPDATE ON project_repositories 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- INDEXES
-- =============================================================================

-- Projects indexes
CREATE INDEX idx_projects_organization_id ON projects(organization_id);
CREATE INDEX idx_projects_status ON projects(status) WHERE deleted_at IS NULL;
CREATE INDEX idx_projects_priority ON projects(priority);
CREATE INDEX idx_projects_manager ON projects(project_manager_id);
CREATE INDEX idx_projects_dates ON projects(start_date, end_date);
CREATE INDEX idx_projects_tags ON projects USING GIN(tags);

-- Repositories indexes
CREATE INDEX idx_repositories_organization_id ON repositories(organization_id);
CREATE INDEX idx_repositories_name ON repositories(name);
CREATE INDEX idx_repositories_url ON repositories(url);
CREATE INDEX idx_repositories_type ON repositories(repository_type);
CREATE INDEX idx_repositories_language ON repositories(language);
CREATE INDEX idx_repositories_active ON repositories(is_active) WHERE deleted_at IS NULL;
CREATE INDEX idx_repositories_analysis ON repositories(analysis_enabled, last_analyzed_at);
CREATE INDEX idx_repositories_external_id ON repositories(external_id);

-- Repository branches indexes
CREATE INDEX idx_repo_branches_repository_id ON repository_branches(repository_id);
CREATE INDEX idx_repo_branches_name ON repository_branches(name);
CREATE INDEX idx_repo_branches_default ON repository_branches(is_default) WHERE is_default = true;
CREATE INDEX idx_repo_branches_activity ON repository_branches(last_activity_at);

-- Project repositories indexes
CREATE INDEX idx_project_repos_project_id ON project_repositories(project_id);
CREATE INDEX idx_project_repos_repository_id ON project_repositories(repository_id);
CREATE INDEX idx_project_repos_role ON project_repositories(role);

-- =============================================================================
-- VIEWS
-- =============================================================================

-- Active projects view
CREATE VIEW active_projects AS
SELECT 
    p.*,
    u.name as manager_name,
    u.email as manager_email,
    o.name as organization_name
FROM projects p
LEFT JOIN users u ON p.project_manager_id = u.id
JOIN organizations o ON p.organization_id = o.id
WHERE p.status IN ('planning', 'active') AND p.deleted_at IS NULL;

-- Repository overview view
CREATE VIEW repository_overview AS
SELECT 
    r.*,
    o.name as organization_name,
    COUNT(rb.id) as branch_count,
    MAX(rb.last_activity_at) as last_branch_activity
FROM repositories r
JOIN organizations o ON r.organization_id = o.id
LEFT JOIN repository_branches rb ON r.id = rb.repository_id AND rb.is_active = true
WHERE r.deleted_at IS NULL
GROUP BY r.id, o.name;

-- Project repository summary view
CREATE VIEW project_repository_summary AS
SELECT 
    p.id as project_id,
    p.name as project_name,
    p.status as project_status,
    COUNT(pr.repository_id) as repository_count,
    array_agg(r.name ORDER BY pr.role, r.name) as repository_names,
    array_agg(r.language ORDER BY pr.role, r.name) as repository_languages
FROM projects p
LEFT JOIN project_repositories pr ON p.id = pr.project_id
LEFT JOIN repositories r ON pr.repository_id = r.id AND r.deleted_at IS NULL
WHERE p.deleted_at IS NULL
GROUP BY p.id, p.name, p.status;

-- =============================================================================
-- FUNCTIONS
-- =============================================================================

-- Function to get project statistics
CREATE OR REPLACE FUNCTION get_project_statistics(project_uuid UUID)
RETURNS JSONB AS $$
DECLARE
    result JSONB;
    repo_count INTEGER;
    total_size_kb BIGINT;
    languages TEXT[];
BEGIN
    -- Get repository statistics for the project
    SELECT 
        COUNT(r.id),
        COALESCE(SUM(r.size_kb), 0),
        array_agg(DISTINCT r.language) FILTER (WHERE r.language IS NOT NULL)
    INTO repo_count, total_size_kb, languages
    FROM project_repositories pr
    JOIN repositories r ON pr.repository_id = r.id
    WHERE pr.project_id = project_uuid AND r.deleted_at IS NULL;
    
    result := jsonb_build_object(
        'repository_count', COALESCE(repo_count, 0),
        'total_size_kb', COALESCE(total_size_kb, 0),
        'languages', COALESCE(languages, ARRAY[]::TEXT[]),
        'calculated_at', CURRENT_TIMESTAMP
    );
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Function to update repository statistics
CREATE OR REPLACE FUNCTION update_repository_statistics(repo_uuid UUID, stats JSONB)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE repositories 
    SET 
        size_kb = COALESCE((stats->>'size_kb')::BIGINT, size_kb),
        language = COALESCE(stats->>'primary_language', language),
        languages = COALESCE(stats->'languages', languages),
        topics = COALESCE(
            ARRAY(SELECT jsonb_array_elements_text(stats->'topics')), 
            topics
        ),
        updated_at = CURRENT_TIMESTAMP
    WHERE id = repo_uuid AND deleted_at IS NULL;
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- Record this migration
INSERT INTO schema_migrations (version, description) VALUES 
('01_projects_module', 'Projects module with project and repository management');

