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
    
    CONSTRAINT organization_memberships_unique UNIQUE (organization_id, user_id)
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
$$ language 'plpgsql';

-- =============================================================================
-- TRIGGERS
-- =============================================================================

-- Triggers for updating updated_at timestamps
CREATE TRIGGER update_organizations_updated_at 
    BEFORE UPDATE ON organizations 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_organization_memberships_updated_at 
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
CREATE INDEX idx_users_last_active ON users(last_active_at);

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

-- Organization members view
CREATE VIEW organization_members AS
SELECT 
    om.organization_id,
    om.user_id,
    om.role,
    om.permissions,
    om.joined_at,
    u.name as user_name,
    u.email as user_email,
    o.name as organization_name
FROM organization_memberships om
JOIN users u ON om.user_id = u.id
JOIN organizations o ON om.organization_id = o.id
WHERE u.deleted_at IS NULL AND o.deleted_at IS NULL;

-- =============================================================================
-- INITIAL DATA
-- =============================================================================

-- Insert default organization
INSERT INTO organizations (name, slug, description) VALUES 
('Default Organization', 'default', 'Default organization for system initialization');

-- =============================================================================
-- SCHEMA MIGRATION TRACKING
-- =============================================================================

CREATE TABLE schema_migrations (
    id SERIAL PRIMARY KEY,
    version VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Record this migration
INSERT INTO schema_migrations (version, description) VALUES 
('00_base_schema', 'Base schema with organizations, users, and common types');

