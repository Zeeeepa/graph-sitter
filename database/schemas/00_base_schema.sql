-- =============================================================================
-- BASE SCHEMA: Foundation for all modules
-- =============================================================================
-- This file contains the core database schema that serves as the foundation
-- for all other modules. It includes organizations, users, common types,
-- and utility functions.
-- =============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- =============================================================================
-- COMMON ENUMS AND TYPES
-- =============================================================================

-- User roles within organizations
CREATE TYPE user_role AS ENUM (
    'owner',
    'admin', 
    'member',
    'viewer'
);

-- General status types
CREATE TYPE status_type AS ENUM (
    'active',
    'inactive',
    'pending',
    'suspended',
    'deleted'
);

-- Priority levels
CREATE TYPE priority_level AS ENUM (
    'low',
    'normal', 
    'high',
    'urgent',
    'critical'
);

-- =============================================================================
-- CORE TABLES
-- =============================================================================

-- Organizations table - top-level tenant isolation
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) NOT NULL,
    description TEXT,
    settings JSONB DEFAULT '{}',
    status status_type DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT organizations_slug_unique UNIQUE (slug),
    CONSTRAINT organizations_name_not_empty CHECK (length(trim(name)) > 0),
    CONSTRAINT organizations_slug_format CHECK (slug ~ '^[a-z0-9-]+$')
);

-- Users table - user management with preferences
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    avatar_url TEXT,
    settings JSONB DEFAULT '{}',
    preferences JSONB DEFAULT '{}',
    status status_type DEFAULT 'active',
    last_active_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT users_email_unique UNIQUE (email),
    CONSTRAINT users_email_format CHECK (email ~ '^[^@]+@[^@]+\.[^@]+$'),
    CONSTRAINT users_name_not_empty CHECK (length(trim(name)) > 0)
);

-- Organization memberships - many-to-many relationship with roles
CREATE TABLE organization_memberships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role user_role NOT NULL DEFAULT 'member',
    permissions JSONB DEFAULT '{}',
    invited_by UUID REFERENCES users(id),
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT org_memberships_unique UNIQUE (organization_id, user_id)
);

-- =============================================================================
-- UTILITY FUNCTIONS
-- =============================================================================

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function to generate short UUIDs for display
CREATE OR REPLACE FUNCTION generate_short_id(prefix TEXT DEFAULT '')
RETURNS TEXT AS $$
BEGIN
    RETURN prefix || substring(replace(uuid_generate_v4()::text, '-', ''), 1, 8);
END;
$$ LANGUAGE plpgsql;

-- Function to validate JSON schema (basic validation)
CREATE OR REPLACE FUNCTION validate_json_schema(data JSONB, required_fields TEXT[])
RETURNS BOOLEAN AS $$
DECLARE
    field TEXT;
BEGIN
    FOREACH field IN ARRAY required_fields
    LOOP
        IF NOT (data ? field) THEN
            RETURN FALSE;
        END IF;
    END LOOP;
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- TRIGGERS
-- =============================================================================

-- Add updated_at triggers to all tables
CREATE TRIGGER organizations_updated_at 
    BEFORE UPDATE ON organizations 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER organization_memberships_updated_at 
    BEFORE UPDATE ON organization_memberships 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- INDEXES
-- =============================================================================

-- Organizations indexes
CREATE INDEX idx_organizations_slug ON organizations(slug);
CREATE INDEX idx_organizations_status ON organizations(status) WHERE deleted_at IS NULL;
CREATE INDEX idx_organizations_created_at ON organizations(created_at);

-- Users indexes  
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_status ON users(status) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_last_active ON users(last_active_at DESC);

-- Organization memberships indexes
CREATE INDEX idx_org_memberships_org_id ON organization_memberships(organization_id);
CREATE INDEX idx_org_memberships_user_id ON organization_memberships(user_id);
CREATE INDEX idx_org_memberships_role ON organization_memberships(role);

-- =============================================================================
-- VIEWS
-- =============================================================================

-- Active organizations view
CREATE VIEW active_organizations AS
SELECT * FROM organizations 
WHERE status = 'active' AND deleted_at IS NULL;

-- Active users view
CREATE VIEW active_users AS
SELECT * FROM users 
WHERE status = 'active' AND deleted_at IS NULL;

-- Organization members view with user details
CREATE VIEW organization_members AS
SELECT 
    om.organization_id,
    om.user_id,
    om.role,
    om.permissions,
    om.joined_at,
    u.email,
    u.name,
    u.avatar_url,
    u.last_active_at
FROM organization_memberships om
JOIN users u ON om.user_id = u.id
WHERE u.deleted_at IS NULL;

-- =============================================================================
-- SECURITY FUNCTIONS
-- =============================================================================

-- Function to check if user has permission in organization
CREATE OR REPLACE FUNCTION user_has_org_permission(
    user_id_param UUID,
    org_id_param UUID,
    required_role user_role DEFAULT 'member'
)
RETURNS BOOLEAN AS $$
DECLARE
    user_role_val user_role;
    role_hierarchy INTEGER;
    required_hierarchy INTEGER;
BEGIN
    -- Get user's role in organization
    SELECT role INTO user_role_val
    FROM organization_memberships om
    JOIN users u ON om.user_id = u.id
    WHERE om.user_id = user_id_param 
    AND om.organization_id = org_id_param
    AND u.status = 'active'
    AND u.deleted_at IS NULL;
    
    IF user_role_val IS NULL THEN
        RETURN FALSE;
    END IF;
    
    -- Define role hierarchy (higher number = more permissions)
    role_hierarchy := CASE user_role_val
        WHEN 'viewer' THEN 1
        WHEN 'member' THEN 2
        WHEN 'admin' THEN 3
        WHEN 'owner' THEN 4
    END;
    
    required_hierarchy := CASE required_role
        WHEN 'viewer' THEN 1
        WHEN 'member' THEN 2
        WHEN 'admin' THEN 3
        WHEN 'owner' THEN 4
    END;
    
    RETURN role_hierarchy >= required_hierarchy;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =============================================================================
-- AUDIT FUNCTIONS
-- =============================================================================

-- Function to log organization changes
CREATE OR REPLACE FUNCTION log_organization_change()
RETURNS TRIGGER AS $$
BEGIN
    -- This can be extended to log to an audit table
    -- For now, just ensure proper data validation
    IF TG_OP = 'UPDATE' THEN
        -- Prevent changing slug if organization has dependencies
        IF OLD.slug != NEW.slug THEN
            -- Add validation logic here if needed
            NULL;
        END IF;
    END IF;
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Add audit trigger to organizations
CREATE TRIGGER organizations_audit_trigger
    BEFORE UPDATE OR DELETE ON organizations
    FOR EACH ROW EXECUTE FUNCTION log_organization_change();

-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON TABLE organizations IS 'Top-level tenant isolation for multi-tenant architecture';
COMMENT ON TABLE users IS 'User accounts with preferences and settings';
COMMENT ON TABLE organization_memberships IS 'Many-to-many relationship between users and organizations with roles';

COMMENT ON COLUMN organizations.slug IS 'URL-friendly unique identifier for the organization';
COMMENT ON COLUMN organizations.settings IS 'Organization-specific configuration and settings';
COMMENT ON COLUMN users.preferences IS 'User-specific preferences and UI settings';
COMMENT ON COLUMN organization_memberships.permissions IS 'Additional permissions beyond the base role';

-- =============================================================================
-- INITIAL DATA
-- =============================================================================

-- Create system user for automated operations
INSERT INTO users (id, email, name, status) VALUES 
('00000000-0000-0000-0000-000000000001', 'system@graph-sitter.com', 'System User', 'active')
ON CONFLICT (email) DO NOTHING;

-- Create default organization if none exists
INSERT INTO organizations (id, name, slug, description) VALUES 
('00000000-0000-0000-0000-000000000001', 'Default Organization', 'default', 'Default organization for initial setup')
ON CONFLICT (slug) DO NOTHING;

