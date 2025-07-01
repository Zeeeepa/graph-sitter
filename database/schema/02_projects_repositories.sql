-- =====================================================
-- Projects & Repositories Module
-- Project lifecycle management and repository tracking
-- =====================================================

-- Projects table for organizing repositories and work
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    settings JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'active',
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

-- Repository branches tracking
CREATE TABLE repository_branches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    repository_id UUID NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    commit_sha VARCHAR(40),
    is_default BOOLEAN DEFAULT false,
    is_protected BOOLEAN DEFAULT false,
    last_commit_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(repository_id, name)
);

-- Repository collaborators and permissions
CREATE TABLE repository_collaborators (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    repository_id UUID NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    permission_level VARCHAR(20) NOT NULL DEFAULT 'read',
    added_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(repository_id, user_id),
    CONSTRAINT valid_permission CHECK (permission_level IN ('read', 'write', 'admin'))
);

-- Repository analysis results
CREATE TABLE repository_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    repository_id UUID NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    branch_name VARCHAR(255) NOT NULL,
    commit_sha VARCHAR(40) NOT NULL,
    analysis_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    results JSONB DEFAULT '{}',
    metrics JSONB DEFAULT '{}',
    error_details JSONB,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER,
    
    CONSTRAINT valid_analysis_status CHECK (status IN ('pending', 'running', 'completed', 'failed'))
);

-- Repository webhooks management
CREATE TABLE repository_webhooks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    repository_id UUID NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    webhook_url TEXT NOT NULL,
    secret_hash VARCHAR(255),
    events JSONB NOT NULL DEFAULT '[]',
    is_active BOOLEAN DEFAULT true,
    external_webhook_id VARCHAR(255),
    last_delivery_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- Row-Level Security
-- =====================================================

ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE repositories ENABLE ROW LEVEL SECURITY;
ALTER TABLE repository_branches ENABLE ROW LEVEL SECURITY;
ALTER TABLE repository_collaborators ENABLE ROW LEVEL SECURITY;
ALTER TABLE repository_analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE repository_webhooks ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY tenant_isolation_projects ON projects
    USING (organization_id = get_current_tenant());

CREATE POLICY tenant_isolation_repositories ON repositories
    USING (organization_id = get_current_tenant());

CREATE POLICY tenant_isolation_repository_branches ON repository_branches
    USING (organization_id = get_current_tenant());

CREATE POLICY tenant_isolation_repository_collaborators ON repository_collaborators
    USING (organization_id = get_current_tenant());

CREATE POLICY tenant_isolation_repository_analyses ON repository_analyses
    USING (organization_id = get_current_tenant());

CREATE POLICY tenant_isolation_repository_webhooks ON repository_webhooks
    USING (organization_id = get_current_tenant());

-- =====================================================
-- Indexes for Performance
-- =====================================================

-- Projects
CREATE INDEX idx_projects_org_status ON projects(organization_id, status);
CREATE INDEX idx_projects_owner ON projects(owner_id);
CREATE INDEX idx_projects_visibility ON projects(visibility);
CREATE INDEX idx_projects_tags ON projects USING GIN (tags);

-- Repositories
CREATE INDEX idx_repositories_org_project ON repositories(organization_id, project_id);
CREATE INDEX idx_repositories_provider_external ON repositories(provider, external_id);
CREATE INDEX idx_repositories_full_name ON repositories(full_name);
CREATE INDEX idx_repositories_language ON repositories(language);
CREATE INDEX idx_repositories_last_analyzed ON repositories(last_analyzed_at);
CREATE INDEX idx_repositories_analysis_config ON repositories USING GIN (analysis_config);

-- Repository Branches
CREATE INDEX idx_repo_branches_repo ON repository_branches(repository_id);
CREATE INDEX idx_repo_branches_default ON repository_branches(repository_id, is_default) WHERE is_default = true;
CREATE INDEX idx_repo_branches_protected ON repository_branches(repository_id, is_protected) WHERE is_protected = true;

-- Repository Collaborators
CREATE INDEX idx_repo_collaborators_repo ON repository_collaborators(repository_id);
CREATE INDEX idx_repo_collaborators_user ON repository_collaborators(user_id);
CREATE INDEX idx_repo_collaborators_permission ON repository_collaborators(repository_id, permission_level);

-- Repository Analyses
CREATE INDEX idx_repo_analyses_repo_status ON repository_analyses(repository_id, status);
CREATE INDEX idx_repo_analyses_type_started ON repository_analyses(analysis_type, started_at);
CREATE INDEX idx_repo_analyses_commit ON repository_analyses(repository_id, commit_sha);

-- Repository Webhooks
CREATE INDEX idx_repo_webhooks_repo_active ON repository_webhooks(repository_id, is_active);
CREATE INDEX idx_repo_webhooks_external_id ON repository_webhooks(external_webhook_id);

-- =====================================================
-- Functions for Repository Management
-- =====================================================

-- Function to get repository statistics
CREATE OR REPLACE FUNCTION get_repository_stats(repo_id UUID)
RETURNS JSONB AS $$
DECLARE
    stats JSONB;
BEGIN
    SELECT jsonb_build_object(
        'total_branches', COUNT(DISTINCT rb.id),
        'protected_branches', COUNT(DISTINCT rb.id) FILTER (WHERE rb.is_protected = true),
        'total_collaborators', COUNT(DISTINCT rc.id),
        'recent_analyses', COUNT(DISTINCT ra.id) FILTER (WHERE ra.started_at > NOW() - INTERVAL '30 days'),
        'last_analysis', MAX(ra.completed_at)
    ) INTO stats
    FROM repositories r
    LEFT JOIN repository_branches rb ON r.id = rb.repository_id
    LEFT JOIN repository_collaborators rc ON r.id = rc.repository_id
    LEFT JOIN repository_analyses ra ON r.id = ra.repository_id
    WHERE r.id = repo_id AND r.organization_id = get_current_tenant();
    
    RETURN stats;
END;
$$ LANGUAGE plpgsql;

-- Function to check repository access
CREATE OR REPLACE FUNCTION user_can_access_repository(
    user_id UUID,
    repo_id UUID,
    required_permission VARCHAR(20) DEFAULT 'read'
) RETURNS BOOLEAN AS $$
DECLARE
    user_permission VARCHAR(20);
    is_project_owner BOOLEAN := false;
    user_role VARCHAR(50);
BEGIN
    -- Check if user is organization admin/owner
    SELECT role INTO user_role 
    FROM users 
    WHERE id = user_id AND organization_id = get_current_tenant();
    
    IF user_role IN ('owner', 'admin') THEN
        RETURN true;
    END IF;
    
    -- Check if user is project owner
    SELECT EXISTS(
        SELECT 1 FROM repositories r
        JOIN projects p ON r.project_id = p.id
        WHERE r.id = repo_id AND p.owner_id = user_id
    ) INTO is_project_owner;
    
    IF is_project_owner THEN
        RETURN true;
    END IF;
    
    -- Check direct repository collaboration
    SELECT permission_level INTO user_permission
    FROM repository_collaborators
    WHERE repository_id = repo_id AND user_id = user_can_access_repository.user_id;
    
    IF user_permission IS NULL THEN
        RETURN false;
    END IF;
    
    -- Check permission hierarchy
    RETURN CASE 
        WHEN required_permission = 'read' THEN user_permission IN ('read', 'write', 'admin')
        WHEN required_permission = 'write' THEN user_permission IN ('write', 'admin')
        WHEN required_permission = 'admin' THEN user_permission = 'admin'
        ELSE false
    END;
END;
$$ LANGUAGE plpgsql;

-- Function to sync repository metadata
CREATE OR REPLACE FUNCTION sync_repository_metadata(repo_id UUID, metadata JSONB)
RETURNS void AS $$
BEGIN
    UPDATE repositories SET
        description = COALESCE(metadata->>'description', description),
        language = COALESCE(metadata->>'language', language),
        size_kb = COALESCE((metadata->>'size')::INTEGER, size_kb),
        stars_count = COALESCE((metadata->>'stargazers_count')::INTEGER, stars_count),
        forks_count = COALESCE((metadata->>'forks_count')::INTEGER, forks_count),
        open_issues_count = COALESCE((metadata->>'open_issues_count')::INTEGER, open_issues_count),
        is_private = COALESCE((metadata->>'private')::BOOLEAN, is_private),
        is_archived = COALESCE((metadata->>'archived')::BOOLEAN, is_archived),
        last_synced_at = NOW(),
        updated_at = NOW()
    WHERE id = repo_id AND organization_id = get_current_tenant();
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- Triggers
-- =====================================================

-- Update timestamp triggers
CREATE TRIGGER update_projects_updated_at 
    BEFORE UPDATE ON projects 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_repositories_updated_at 
    BEFORE UPDATE ON repositories 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_repository_branches_updated_at 
    BEFORE UPDATE ON repository_branches 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_repository_webhooks_updated_at 
    BEFORE UPDATE ON repository_webhooks 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Audit triggers
CREATE TRIGGER audit_projects 
    AFTER INSERT OR UPDATE OR DELETE ON projects
    FOR EACH ROW EXECUTE FUNCTION create_audit_log();

CREATE TRIGGER audit_repositories 
    AFTER INSERT OR UPDATE OR DELETE ON repositories
    FOR EACH ROW EXECUTE FUNCTION create_audit_log();

-- =====================================================
-- Views for Common Queries
-- =====================================================

-- Repository summary view
CREATE VIEW repository_summary AS
SELECT 
    r.id,
    r.organization_id,
    r.name,
    r.full_name,
    r.provider,
    r.language,
    r.is_private,
    r.is_archived,
    p.name as project_name,
    p.status as project_status,
    COUNT(DISTINCT rb.id) as branch_count,
    COUNT(DISTINCT rc.id) as collaborator_count,
    r.last_analyzed_at,
    r.created_at,
    r.updated_at
FROM repositories r
LEFT JOIN projects p ON r.project_id = p.id
LEFT JOIN repository_branches rb ON r.id = rb.repository_id
LEFT JOIN repository_collaborators rc ON r.id = rc.repository_id
GROUP BY r.id, p.id;

