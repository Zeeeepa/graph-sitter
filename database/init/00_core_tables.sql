-- Core Database Initialization
-- This file creates the foundational tables and types for the Graph-Sitter database system

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Create custom types
CREATE TYPE task_status AS ENUM (
    'pending',
    'in_progress', 
    'completed',
    'failed',
    'cancelled',
    'blocked'
);

CREATE TYPE task_priority AS ENUM (
    'low',
    'medium', 
    'high',
    'critical'
);

CREATE TYPE analysis_type AS ENUM (
    'complexity',
    'dependencies',
    'dead_code',
    'security',
    'performance',
    'maintainability',
    'documentation',
    'testing',
    'imports',
    'exports',
    'inheritance',
    'function_calls',
    'api_usage'
);

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
    'scala',
    'clojure',
    'haskell',
    'other'
);

CREATE TYPE prompt_type AS ENUM (
    'code_review',
    'bug_fix',
    'feature_implementation',
    'documentation',
    'testing',
    'refactoring',
    'security_audit',
    'performance_optimization',
    'api_design',
    'architecture_review'
);

-- Core organizations table
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    codegen_org_id VARCHAR(100) UNIQUE NOT NULL,
    api_token_hash VARCHAR(255),
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Core users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    github_username VARCHAR(100),
    linear_user_id VARCHAR(100),
    slack_user_id VARCHAR(100),
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Core repositories table
CREATE TABLE repositories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    full_name VARCHAR(500) NOT NULL, -- owner/repo format
    github_id BIGINT UNIQUE,
    default_branch VARCHAR(100) DEFAULT 'main',
    language language_type,
    description TEXT,
    is_private BOOLEAN DEFAULT false,
    webhook_url VARCHAR(500),
    settings JSONB DEFAULT '{}',
    last_analyzed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(organization_id, full_name)
);

-- Core codebases table (represents analyzed versions of repositories)
CREATE TABLE codebases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    repository_id UUID REFERENCES repositories(id) ON DELETE CASCADE,
    branch VARCHAR(100) NOT NULL,
    commit_sha VARCHAR(40) NOT NULL,
    analysis_version VARCHAR(20) DEFAULT '1.0',
    total_files INTEGER DEFAULT 0,
    total_lines INTEGER DEFAULT 0,
    total_functions INTEGER DEFAULT 0,
    total_classes INTEGER DEFAULT 0,
    languages JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    analysis_started_at TIMESTAMP WITH TIME ZONE,
    analysis_completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(repository_id, branch, commit_sha)
);

-- Audit log table for tracking all changes
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    table_name VARCHAR(100) NOT NULL,
    record_id UUID NOT NULL,
    action VARCHAR(20) NOT NULL, -- INSERT, UPDATE, DELETE
    old_values JSONB,
    new_values JSONB,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_organizations_codegen_org_id ON organizations(codegen_org_id);
CREATE INDEX idx_users_organization_id ON users(organization_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_repositories_organization_id ON repositories(organization_id);
CREATE INDEX idx_repositories_full_name ON repositories(full_name);
CREATE INDEX idx_repositories_github_id ON repositories(github_id);
CREATE INDEX idx_codebases_repository_id ON codebases(repository_id);
CREATE INDEX idx_codebases_branch ON codebases(branch);
CREATE INDEX idx_codebases_commit_sha ON codebases(commit_sha);
CREATE INDEX idx_audit_log_organization_id ON audit_log(organization_id);
CREATE INDEX idx_audit_log_table_record ON audit_log(table_name, record_id);
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at);

-- Create GIN indexes for JSONB columns
CREATE INDEX idx_organizations_settings ON organizations USING GIN(settings);
CREATE INDEX idx_users_preferences ON users USING GIN(preferences);
CREATE INDEX idx_repositories_settings ON repositories USING GIN(settings);
CREATE INDEX idx_codebases_metadata ON codebases USING GIN(metadata);
CREATE INDEX idx_codebases_languages ON codebases USING GIN(languages);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers to all tables
CREATE TRIGGER update_organizations_updated_at BEFORE UPDATE ON organizations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_repositories_updated_at BEFORE UPDATE ON repositories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_codebases_updated_at BEFORE UPDATE ON codebases
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create audit trigger function
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        INSERT INTO audit_log (table_name, record_id, action, old_values)
        VALUES (TG_TABLE_NAME, OLD.id, TG_OP, row_to_json(OLD));
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_log (table_name, record_id, action, old_values, new_values)
        VALUES (TG_TABLE_NAME, NEW.id, TG_OP, row_to_json(OLD), row_to_json(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'INSERT' THEN
        INSERT INTO audit_log (table_name, record_id, action, new_values)
        VALUES (TG_TABLE_NAME, NEW.id, TG_OP, row_to_json(NEW));
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Apply audit triggers (optional - can be enabled per table as needed)
-- CREATE TRIGGER audit_organizations AFTER INSERT OR UPDATE OR DELETE ON organizations
--     FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

-- Utility functions
CREATE OR REPLACE FUNCTION get_organization_by_codegen_id(codegen_org_id VARCHAR)
RETURNS UUID AS $$
DECLARE
    org_id UUID;
BEGIN
    SELECT id INTO org_id FROM organizations WHERE organizations.codegen_org_id = $1;
    RETURN org_id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_repository_by_full_name(org_id UUID, repo_full_name VARCHAR)
RETURNS UUID AS $$
DECLARE
    repo_id UUID;
BEGIN
    SELECT id INTO repo_id FROM repositories 
    WHERE organization_id = org_id AND full_name = repo_full_name;
    RETURN repo_id;
END;
$$ LANGUAGE plpgsql;

-- Health check function
CREATE OR REPLACE FUNCTION database_health_check()
RETURNS TABLE(
    component VARCHAR,
    status VARCHAR,
    details JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        'core_tables'::VARCHAR as component,
        'healthy'::VARCHAR as status,
        jsonb_build_object(
            'organizations_count', (SELECT COUNT(*) FROM organizations),
            'repositories_count', (SELECT COUNT(*) FROM repositories),
            'codebases_count', (SELECT COUNT(*) FROM codebases),
            'users_count', (SELECT COUNT(*) FROM users)
        ) as details;
END;
$$ LANGUAGE plpgsql;

-- Insert default organization if not exists
INSERT INTO organizations (name, codegen_org_id, settings) 
VALUES ('Default Organization', '323', '{"default": true}')
ON CONFLICT (codegen_org_id) DO NOTHING;

COMMENT ON TABLE organizations IS 'Core organizations using the Graph-Sitter system';
COMMENT ON TABLE users IS 'Users within organizations with their integration IDs';
COMMENT ON TABLE repositories IS 'GitHub repositories connected to the system';
COMMENT ON TABLE codebases IS 'Analyzed versions of repositories with metadata';
COMMENT ON TABLE audit_log IS 'Comprehensive audit trail for all database changes';

