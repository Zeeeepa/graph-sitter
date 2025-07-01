-- =============================================================================
-- PROJECTS DATABASE SCHEMA: Project Management and Repository Tracking
-- =============================================================================
-- This database handles project management, repository tracking, cross-project
-- analytics, and team management functionality.
-- =============================================================================

-- Connect to projects_db
\c projects_db;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- Set timezone and configuration
SET timezone = 'UTC';
SET default_text_search_config = 'pg_catalog.english';

-- Grant all privileges to projects_user
GRANT ALL PRIVILEGES ON DATABASE projects_db TO projects_user;
GRANT ALL PRIVILEGES ON SCHEMA public TO projects_user;

-- Project-specific enums
CREATE TYPE project_status AS ENUM (
    'planning',
    'active',
    'on_hold',
    'completed',
    'cancelled',
    'archived'
);

CREATE TYPE project_visibility AS ENUM (
    'public',
    'internal',
    'private',
    'restricted'
);

CREATE TYPE repository_type AS ENUM (
    'git',
    'svn',
    'mercurial',
    'perforce',
    'other'
);

CREATE TYPE repository_status AS ENUM (
    'active',
    'archived',
    'deprecated',
    'migrated',
    'deleted'
);

CREATE TYPE team_role AS ENUM (
    'owner',
    'admin',
    'maintainer',
    'developer',
    'reviewer',
    'viewer'
);

CREATE TYPE priority_level AS ENUM (
    'low',
    'normal', 
    'high',
    'urgent',
    'critical'
);

-- =============================================================================
-- CORE REFERENCE TABLES
-- =============================================================================

-- Organizations table for multi-tenancy
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Users table for team management
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE,
    avatar_url TEXT,
    role VARCHAR(50) DEFAULT 'member',
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- PROJECTS MANAGEMENT
-- =============================================================================

-- Main projects table
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Project identification
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) NOT NULL,
    description TEXT,
    
    -- Project configuration
    status project_status DEFAULT 'planning',
    visibility project_visibility DEFAULT 'internal',
    priority priority_level DEFAULT 'normal',
    
    -- Project details
    objectives TEXT,
    requirements JSONB DEFAULT '{}',
    milestones JSONB DEFAULT '[]',
    
    -- Team and ownership
    owner_id UUID REFERENCES users(id),
    lead_id UUID REFERENCES users(id),
    team_size INTEGER DEFAULT 0,
    
    -- Timeline and planning
    start_date DATE,
    end_date DATE,
    estimated_hours INTEGER,
    actual_hours INTEGER,
    
    -- Budget and resources
    budget_allocated DECIMAL(12,2),
    budget_spent DECIMAL(12,2),
    resource_requirements JSONB DEFAULT '{}',
    
    -- Progress tracking
    progress_percentage DECIMAL(5,2) DEFAULT 0,
    completion_criteria JSONB DEFAULT '{}',
    
    -- External references
    external_project_id VARCHAR(255),
    external_url TEXT,
    documentation_url TEXT,
    
    -- Metadata
    tags VARCHAR(50)[],
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT projects_name_org_unique UNIQUE (organization_id, name),
    CONSTRAINT projects_slug_org_unique UNIQUE (organization_id, slug),
    CONSTRAINT projects_name_not_empty CHECK (length(trim(name)) > 0),
    CONSTRAINT projects_progress_valid CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
    CONSTRAINT projects_budget_valid CHECK (budget_allocated >= 0 AND budget_spent >= 0)
);

-- =============================================================================
-- REPOSITORY MANAGEMENT
-- =============================================================================

-- Repositories table for code repository tracking
CREATE TABLE repositories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Repository identification
    name VARCHAR(255) NOT NULL,
    full_name VARCHAR(500), -- e.g., "org/repo"
    description TEXT,
    
    -- Repository details
    repository_type repository_type DEFAULT 'git',
    status repository_status DEFAULT 'active',
    visibility project_visibility DEFAULT 'internal',
    
    -- Repository URLs and access
    clone_url TEXT NOT NULL,
    web_url TEXT,
    ssh_url TEXT,
    api_url TEXT,
    
    -- Repository metadata
    default_branch VARCHAR(100) DEFAULT 'main',
    language VARCHAR(50),
    languages JSONB DEFAULT '{}', -- Language breakdown
    
    -- Repository statistics
    size_kb INTEGER DEFAULT 0,
    stars_count INTEGER DEFAULT 0,
    forks_count INTEGER DEFAULT 0,
    issues_count INTEGER DEFAULT 0,
    pull_requests_count INTEGER DEFAULT 0,
    
    -- Repository configuration
    is_fork BOOLEAN DEFAULT false,
    is_template BOOLEAN DEFAULT false,
    is_archived BOOLEAN DEFAULT false,
    is_private BOOLEAN DEFAULT true,
    
    -- External integration
    external_repo_id VARCHAR(255),
    provider VARCHAR(50), -- github, gitlab, bitbucket, etc.
    provider_data JSONB DEFAULT '{}',
    
    -- Access and permissions
    access_token_encrypted TEXT,
    webhook_config JSONB DEFAULT '{}',
    
    -- Metadata
    topics VARCHAR(50)[],
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT repositories_name_org_unique UNIQUE (organization_id, name),
    CONSTRAINT repositories_name_not_empty CHECK (length(trim(name)) > 0),
    CONSTRAINT repositories_clone_url_not_empty CHECK (length(trim(clone_url)) > 0)
);

-- =============================================================================
-- PROJECT-REPOSITORY RELATIONSHIPS
-- =============================================================================

-- Many-to-many relationship between projects and repositories
CREATE TABLE project_repositories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    repository_id UUID NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    
    -- Relationship details
    role VARCHAR(100) DEFAULT 'primary', -- primary, secondary, dependency, fork
    description TEXT,
    
    -- Configuration
    is_primary BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    
    -- Integration settings
    sync_enabled BOOLEAN DEFAULT true,
    webhook_enabled BOOLEAN DEFAULT false,
    ci_cd_enabled BOOLEAN DEFAULT false,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT project_repositories_unique UNIQUE (project_id, repository_id)
);

-- =============================================================================
-- TEAM MANAGEMENT
-- =============================================================================

-- Project team members
CREATE TABLE project_teams (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Team role and permissions
    role team_role NOT NULL,
    permissions JSONB DEFAULT '{}',
    
    -- Participation details
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    left_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    
    -- Contribution tracking
    commits_count INTEGER DEFAULT 0,
    issues_created INTEGER DEFAULT 0,
    pull_requests_created INTEGER DEFAULT 0,
    reviews_completed INTEGER DEFAULT 0,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT project_teams_unique UNIQUE (project_id, user_id)
);

-- Repository collaborators
CREATE TABLE repository_collaborators (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    repository_id UUID NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Collaboration details
    role team_role NOT NULL,
    permissions JSONB DEFAULT '{}',
    
    -- Access details
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    revoked_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    
    -- Activity tracking
    last_commit_at TIMESTAMP WITH TIME ZONE,
    last_access_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT repository_collaborators_unique UNIQUE (repository_id, user_id)
);

-- =============================================================================
-- PROJECT ANALYTICS AND TRACKING
-- =============================================================================

-- Project milestones
CREATE TABLE project_milestones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    
    -- Milestone details
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Timeline
    due_date DATE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Progress tracking
    progress_percentage DECIMAL(5,2) DEFAULT 0,
    is_completed BOOLEAN DEFAULT false,
    
    -- Deliverables
    deliverables JSONB DEFAULT '[]',
    acceptance_criteria JSONB DEFAULT '[]',
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT project_milestones_name_project_unique UNIQUE (project_id, name),
    CONSTRAINT project_milestones_progress_valid CHECK (progress_percentage >= 0 AND progress_percentage <= 100)
);

-- Project activity log
CREATE TABLE project_activities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id),
    
    -- Activity details
    activity_type VARCHAR(100) NOT NULL,
    description TEXT,
    
    -- Activity data
    activity_data JSONB DEFAULT '{}',
    
    -- References
    reference_type VARCHAR(100), -- milestone, repository, team, etc.
    reference_id UUID,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- INDEXES FOR OPTIMAL PERFORMANCE
-- =============================================================================

-- Projects indexes
CREATE INDEX idx_projects_org_id ON projects(organization_id);
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_visibility ON projects(visibility);
CREATE INDEX idx_projects_owner_id ON projects(owner_id);
CREATE INDEX idx_projects_lead_id ON projects(lead_id);
CREATE INDEX idx_projects_priority ON projects(priority);
CREATE INDEX idx_projects_start_date ON projects(start_date);
CREATE INDEX idx_projects_end_date ON projects(end_date);

-- Repositories indexes
CREATE INDEX idx_repositories_org_id ON repositories(organization_id);
CREATE INDEX idx_repositories_status ON repositories(status);
CREATE INDEX idx_repositories_type ON repositories(repository_type);
CREATE INDEX idx_repositories_visibility ON repositories(visibility);
CREATE INDEX idx_repositories_provider ON repositories(provider);
CREATE INDEX idx_repositories_language ON repositories(language);
CREATE INDEX idx_repositories_last_activity ON repositories(last_activity_at);

-- Project repositories indexes
CREATE INDEX idx_project_repositories_project_id ON project_repositories(project_id);
CREATE INDEX idx_project_repositories_repository_id ON project_repositories(repository_id);
CREATE INDEX idx_project_repositories_is_primary ON project_repositories(is_primary);

-- Team indexes
CREATE INDEX idx_project_teams_project_id ON project_teams(project_id);
CREATE INDEX idx_project_teams_user_id ON project_teams(user_id);
CREATE INDEX idx_project_teams_role ON project_teams(role);
CREATE INDEX idx_project_teams_is_active ON project_teams(is_active);

CREATE INDEX idx_repository_collaborators_repository_id ON repository_collaborators(repository_id);
CREATE INDEX idx_repository_collaborators_user_id ON repository_collaborators(user_id);
CREATE INDEX idx_repository_collaborators_role ON repository_collaborators(role);

-- Milestones and activities indexes
CREATE INDEX idx_project_milestones_project_id ON project_milestones(project_id);
CREATE INDEX idx_project_milestones_due_date ON project_milestones(due_date);
CREATE INDEX idx_project_milestones_completed ON project_milestones(is_completed);

CREATE INDEX idx_project_activities_project_id ON project_activities(project_id);
CREATE INDEX idx_project_activities_user_id ON project_activities(user_id);
CREATE INDEX idx_project_activities_type ON project_activities(activity_type);
CREATE INDEX idx_project_activities_created_at ON project_activities(created_at);

-- GIN indexes for JSONB fields
CREATE INDEX idx_projects_metadata_gin USING gin (metadata);
CREATE INDEX idx_repositories_metadata_gin USING gin (metadata);
CREATE INDEX idx_repositories_languages_gin USING gin (languages);

-- =============================================================================
-- VIEWS FOR COMMON QUERIES
-- =============================================================================

-- Active projects view
CREATE VIEW active_projects AS
SELECT 
    p.*,
    o.name as organization_name,
    u1.name as owner_name,
    u2.name as lead_name,
    COUNT(pt.user_id) as team_members_count,
    COUNT(pr.repository_id) as repositories_count
FROM projects p
JOIN organizations o ON p.organization_id = o.id
LEFT JOIN users u1 ON p.owner_id = u1.id
LEFT JOIN users u2 ON p.lead_id = u2.id
LEFT JOIN project_teams pt ON p.id = pt.project_id AND pt.is_active = true
LEFT JOIN project_repositories pr ON p.id = pr.project_id AND pr.is_active = true
WHERE p.status IN ('planning', 'active')
AND p.deleted_at IS NULL
GROUP BY p.id, o.name, u1.name, u2.name;

-- Project repository summary
CREATE VIEW project_repository_summary AS
SELECT 
    p.id as project_id,
    p.name as project_name,
    r.id as repository_id,
    r.name as repository_name,
    r.full_name,
    r.language,
    r.size_kb,
    pr.role as repository_role,
    pr.is_primary
FROM projects p
JOIN project_repositories pr ON p.id = pr.project_id
JOIN repositories r ON pr.repository_id = r.id
WHERE p.deleted_at IS NULL
AND r.deleted_at IS NULL
AND pr.is_active = true;

-- Team analytics view
CREATE VIEW team_analytics AS
SELECT 
    p.id as project_id,
    p.name as project_name,
    COUNT(pt.user_id) as total_members,
    COUNT(CASE WHEN pt.role IN ('owner', 'admin') THEN 1 END) as admin_count,
    COUNT(CASE WHEN pt.role = 'developer' THEN 1 END) as developer_count,
    SUM(pt.commits_count) as total_commits,
    SUM(pt.issues_created) as total_issues,
    SUM(pt.pull_requests_created) as total_prs
FROM projects p
LEFT JOIN project_teams pt ON p.id = pt.project_id AND pt.is_active = true
WHERE p.deleted_at IS NULL
GROUP BY p.id, p.name;

-- Grant permissions to projects_user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO projects_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO projects_user;
GRANT USAGE ON SCHEMA public TO projects_user;

-- Insert default organization
INSERT INTO organizations (name, slug, description) VALUES 
('Default Organization', 'default', 'Default organization for project management');

-- Insert default admin user
INSERT INTO users (organization_id, name, email, role) VALUES 
((SELECT id FROM organizations WHERE slug = 'default'), 'Projects Admin', 'admin@projects.local', 'admin');

-- Final status message
DO $$
BEGIN
    RAISE NOTICE '🏗️ Projects Database initialized successfully!';
    RAISE NOTICE 'Features: Project management, Repository tracking, Team management, Cross-project analytics';
    RAISE NOTICE 'Timestamp: %', NOW();
END $$;

