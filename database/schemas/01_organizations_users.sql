-- =============================================================================
-- Organizations & Users Module Schema
-- =============================================================================
-- Multi-tenant architecture with row-level security and comprehensive
-- user management supporting external platform integrations.
-- =============================================================================

-- Organizations table - Core tenant isolation
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    settings JSONB DEFAULT '{}',
    status status_type DEFAULT 'active',
    
    -- Subscription and limits
    subscription_tier VARCHAR(50) DEFAULT 'free',
    max_users INTEGER DEFAULT 10,
    max_repositories INTEGER DEFAULT 5,
    
    -- Audit fields
    created_by VARCHAR(255),
    updated_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    is_deleted BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT organizations_name_not_empty CHECK (length(trim(name)) > 0),
    CONSTRAINT organizations_slug_format CHECK (slug ~ '^[a-z0-9-]+$'),
    CONSTRAINT valid_subscription_tier CHECK (subscription_tier IN ('free', 'pro', 'enterprise'))
);

-- Users table with external platform integration
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    avatar_url TEXT,
    
    -- Settings and preferences
    settings JSONB DEFAULT '{}',
    preferences JSONB DEFAULT '{}',
    status status_type DEFAULT 'active',
    
    -- External platform integration
    external_ids JSONB DEFAULT '{}', -- GitHub, Linear, Slack IDs
    
    -- Activity tracking
    last_active_at TIMESTAMP WITH TIME ZONE,
    
    -- Audit fields
    created_by VARCHAR(255),
    updated_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    is_deleted BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT users_email_format CHECK (email ~ '^[^@]+@[^@]+\.[^@]+$'),
    CONSTRAINT users_name_not_empty CHECK (length(trim(name)) > 0)
);

-- Organization memberships - Many-to-many with roles
CREATE TABLE organization_memberships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Role and permissions
    role user_role NOT NULL DEFAULT 'member',
    permissions JSONB DEFAULT '{}',
    
    -- Invitation tracking
    invited_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
    invited_at TIMESTAMP WITH TIME ZONE,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Audit fields
    created_by VARCHAR(255),
    updated_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    is_deleted BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    UNIQUE(organization_id, user_id)
);

-- =============================================================================
-- Indexes for Performance
-- =============================================================================

-- Organizations
CREATE INDEX idx_organizations_slug ON organizations(slug);
CREATE INDEX idx_organizations_status ON organizations(status);
CREATE INDEX idx_organizations_subscription ON organizations(subscription_tier);
CREATE INDEX idx_organizations_created_at ON organizations(created_at);
CREATE INDEX idx_organizations_settings_gin ON organizations USING gin (settings);

-- Users
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_users_last_active ON users(last_active_at);
CREATE INDEX idx_users_external_ids_gin ON users USING gin (external_ids);
CREATE INDEX idx_users_created_at ON users(created_at);

-- Organization Memberships
CREATE INDEX idx_memberships_org ON organization_memberships(organization_id);
CREATE INDEX idx_memberships_user ON organization_memberships(user_id);
CREATE INDEX idx_memberships_role ON organization_memberships(role);
CREATE INDEX idx_memberships_invited_by ON organization_memberships(invited_by_id);
CREATE INDEX idx_memberships_joined_at ON organization_memberships(joined_at);

-- =============================================================================
-- Row-Level Security Setup
-- =============================================================================

-- Enable RLS on all tables
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE organization_memberships ENABLE ROW LEVEL SECURITY;

-- RLS Policies for organizations (only accessible by members)
CREATE POLICY tenant_isolation_organizations ON organizations
    USING (id = current_setting('app.current_tenant', true)::UUID);

-- RLS Policies for users (only accessible by organization members)
CREATE POLICY tenant_isolation_users ON users 
    USING (
        EXISTS (
            SELECT 1 FROM organization_memberships om 
            WHERE om.user_id = users.id 
            AND om.organization_id = current_setting('app.current_tenant', true)::UUID
        )
    );

-- RLS Policies for organization memberships
CREATE POLICY tenant_isolation_memberships ON organization_memberships
    USING (organization_id = current_setting('app.current_tenant', true)::UUID);

-- =============================================================================
-- Security and Utility Functions
-- =============================================================================

-- Function to set current tenant context
CREATE OR REPLACE FUNCTION set_current_tenant(tenant_id UUID)
RETURNS void AS $$
BEGIN
    PERFORM set_config('app.current_tenant', tenant_id::text, true);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get current tenant
CREATE OR REPLACE FUNCTION get_current_tenant()
RETURNS UUID AS $$
BEGIN
    RETURN current_setting('app.current_tenant', true)::UUID;
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Function to validate user permissions
CREATE OR REPLACE FUNCTION user_has_permission(
    user_id UUID,
    required_role user_role
) RETURNS BOOLEAN AS $$
DECLARE
    user_role_val user_role;
    role_hierarchy INTEGER;
    required_hierarchy INTEGER;
BEGIN
    -- Get user role in current tenant
    SELECT role INTO user_role_val 
    FROM organization_memberships 
    WHERE user_id = user_has_permission.user_id 
    AND organization_id = get_current_tenant()
    AND is_deleted = FALSE;
    
    IF user_role_val IS NULL THEN
        RETURN FALSE;
    END IF;
    
    -- Define role hierarchy (higher number = more permissions)
    role_hierarchy := CASE user_role_val
        WHEN 'owner' THEN 4
        WHEN 'admin' THEN 3
        WHEN 'member' THEN 2
        WHEN 'viewer' THEN 1
        ELSE 0
    END;
    
    required_hierarchy := CASE required_role
        WHEN 'owner' THEN 4
        WHEN 'admin' THEN 3
        WHEN 'member' THEN 2
        WHEN 'viewer' THEN 1
        ELSE 0
    END;
    
    RETURN role_hierarchy >= required_hierarchy;
END;
$$ LANGUAGE plpgsql;

-- Function to get organization statistics
CREATE OR REPLACE FUNCTION get_organization_stats(org_id UUID)
RETURNS JSONB AS $$
DECLARE
    stats JSONB;
BEGIN
    SELECT jsonb_build_object(
        'total_users', COUNT(DISTINCT om.user_id),
        'active_users', COUNT(DISTINCT om.user_id) FILTER (WHERE u.status = 'active'),
        'roles', jsonb_object_agg(om.role, role_count)
    ) INTO stats
    FROM organization_memberships om
    JOIN users u ON om.user_id = u.id
    JOIN (
        SELECT role, COUNT(*) as role_count
        FROM organization_memberships
        WHERE organization_id = org_id AND is_deleted = FALSE
        GROUP BY role
    ) role_counts ON om.role = role_counts.role
    WHERE om.organization_id = org_id AND om.is_deleted = FALSE;
    
    RETURN stats;
END;
$$ LANGUAGE plpgsql;

-- Function to check if user can access organization
CREATE OR REPLACE FUNCTION user_can_access_organization(
    user_id UUID,
    org_id UUID
) RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS(
        SELECT 1 FROM organization_memberships
        WHERE user_id = user_can_access_organization.user_id
        AND organization_id = org_id
        AND is_deleted = FALSE
    );
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- Triggers for Automatic Updates
-- =============================================================================

-- Apply update triggers
CREATE TRIGGER update_organizations_updated_at 
    BEFORE UPDATE ON organizations 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_memberships_updated_at 
    BEFORE UPDATE ON organization_memberships 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Apply audit triggers
CREATE TRIGGER audit_organizations 
    AFTER INSERT OR UPDATE OR DELETE ON organizations
    FOR EACH ROW EXECUTE FUNCTION create_audit_log();

CREATE TRIGGER audit_users 
    AFTER INSERT OR UPDATE OR DELETE ON users
    FOR EACH ROW EXECUTE FUNCTION create_audit_log();

CREATE TRIGGER audit_memberships 
    AFTER INSERT OR UPDATE OR DELETE ON organization_memberships
    FOR EACH ROW EXECUTE FUNCTION create_audit_log();

-- =============================================================================
-- Views for Common Queries
-- =============================================================================

-- Organization summary view
CREATE VIEW organization_summary AS
SELECT 
    o.id,
    o.name,
    o.slug,
    o.status,
    o.subscription_tier,
    COUNT(DISTINCT om.user_id) as total_users,
    COUNT(DISTINCT om.user_id) FILTER (WHERE u.status = 'active') as active_users,
    o.created_at,
    o.updated_at
FROM organizations o
LEFT JOIN organization_memberships om ON o.id = om.organization_id AND om.is_deleted = FALSE
LEFT JOIN users u ON om.user_id = u.id
WHERE o.is_deleted = FALSE
GROUP BY o.id;

-- User membership view
CREATE VIEW user_memberships AS
SELECT 
    u.id as user_id,
    u.name as user_name,
    u.email,
    u.status as user_status,
    o.id as organization_id,
    o.name as organization_name,
    o.slug as organization_slug,
    om.role,
    om.joined_at,
    om.permissions
FROM users u
JOIN organization_memberships om ON u.id = om.user_id
JOIN organizations o ON om.organization_id = o.id
WHERE u.is_deleted = FALSE 
AND om.is_deleted = FALSE 
AND o.is_deleted = FALSE;

-- =============================================================================
-- Sample Data and Comments
-- =============================================================================

-- Insert sample organization for development
INSERT INTO organizations (name, slug, description, subscription_tier) VALUES
('Graph-Sitter Development', 'graph-sitter-dev', 'Development organization for graph-sitter project', 'pro');

-- Comments for documentation
COMMENT ON TABLE organizations IS 'Multi-tenant organizations with subscription management';
COMMENT ON TABLE users IS 'Users with external platform integration support';
COMMENT ON TABLE organization_memberships IS 'User-organization relationships with role-based access';

COMMENT ON FUNCTION set_current_tenant IS 'Set current tenant context for RLS';
COMMENT ON FUNCTION get_current_tenant IS 'Get current tenant context';
COMMENT ON FUNCTION user_has_permission IS 'Check if user has required permission level';
COMMENT ON FUNCTION get_organization_stats IS 'Get organization usage statistics';
COMMENT ON FUNCTION user_can_access_organization IS 'Check if user can access organization';

-- Log completion
INSERT INTO audit_log (
    table_name,
    record_id,
    operation,
    new_values,
    actor_id,
    actor_type,
    context
) VALUES (
    'organizations',
    (SELECT id FROM organizations WHERE slug = 'graph-sitter-dev'),
    'SCHEMA_CREATED',
    jsonb_build_object(
        'module', 'organizations_users',
        'tables_created', ARRAY['organizations', 'users', 'organization_memberships'],
        'features', ARRAY['multi_tenant', 'rls', 'external_integration', 'role_based_access']
    ),
    'system',
    'schema_migration',
    jsonb_build_object(
        'schema_file', '01_organizations_users.sql',
        'timestamp', NOW()
    )
);

-- Final status
DO $$
BEGIN
    RAISE NOTICE 'Organizations & Users module schema created successfully!';
    RAISE NOTICE 'Tables: organizations, users, organization_memberships';
    RAISE NOTICE 'Features: Multi-tenant RLS, Role-based access, External platform integration';
END $$;

