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
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

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

-- Language types for code analysis
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
    'sql',
    'html',
    'css',
    'markdown',
    'yaml',
    'json',
    'xml',
    'shell',
    'dockerfile',
    'other'
);

-- Analysis types for comprehensive code analysis
CREATE TYPE analysis_type AS ENUM (
    'complexity',
    'dependencies',
    'dead_code',
    'security',
    'performance',
    'quality',
    'coverage',
    'documentation',
    'maintainability',
    'technical_debt'
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
    
    -- Billing and subscription info
    subscription_tier VARCHAR(50) DEFAULT 'free',
    subscription_status VARCHAR(50) DEFAULT 'active',
    
    -- Contact information
    contact_email VARCHAR(255),
    website_url TEXT,
    
    -- Configuration
    default_timezone VARCHAR(50) DEFAULT 'UTC',
    preferences JSONB DEFAULT '{}',
    
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
    
    -- User preferences and settings
    settings JSONB DEFAULT '{}',
    preferences JSONB DEFAULT '{}',
    
    -- Status and activity
    status status_type DEFAULT 'active',
    last_active_at TIMESTAMP WITH TIME ZONE,
    
    -- Authentication metadata
    auth_provider VARCHAR(50) DEFAULT 'email',
    external_id VARCHAR(255),
    
    -- Profile information
    bio TEXT,
    location VARCHAR(255),
    timezone VARCHAR(50) DEFAULT 'UTC',
    
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
    
    -- Permissions and access control
    permissions JSONB DEFAULT '{}',
    access_level INTEGER DEFAULT 1,
    
    -- Invitation metadata
    invited_by UUID REFERENCES users(id),
    invitation_token VARCHAR(255),
    invitation_expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Membership status
    status status_type DEFAULT 'active',
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT organization_memberships_unique UNIQUE (organization_id, user_id)
);

-- API keys and authentication tokens
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Key information
    name VARCHAR(255) NOT NULL,
    key_hash VARCHAR(255) NOT NULL UNIQUE,
    key_prefix VARCHAR(20) NOT NULL,
    
    -- Permissions and scope
    permissions JSONB DEFAULT '{}',
    scopes TEXT[] DEFAULT '{}',
    
    -- Usage tracking
    last_used_at TIMESTAMP WITH TIME ZONE,
    usage_count BIGINT DEFAULT 0,
    
    -- Expiration and status
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT api_keys_name_not_empty CHECK (length(trim(name)) > 0)
);

-- System configuration table
CREATE TABLE system_configuration (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    config_key VARCHAR(255) UNIQUE NOT NULL,
    config_value JSONB NOT NULL,
    description TEXT,
    
    -- Configuration metadata
    category VARCHAR(100) DEFAULT 'general',
    is_sensitive BOOLEAN DEFAULT false,
    is_readonly BOOLEAN DEFAULT false,
    
    -- Validation
    validation_schema JSONB DEFAULT '{}',
    
    -- Timing
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Audit log table for tracking changes
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Audit metadata
    table_name VARCHAR(255) NOT NULL,
    record_id UUID NOT NULL,
    operation VARCHAR(20) NOT NULL, -- INSERT, UPDATE, DELETE
    
    -- Change tracking
    old_values JSONB,
    new_values JSONB,
    changed_fields JSONB DEFAULT '[]',
    
    -- Actor information
    actor_id UUID REFERENCES users(id),
    actor_type VARCHAR(100),
    session_id VARCHAR(255),
    
    -- Context
    context JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    
    -- Timing
    occurred_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Performance metrics table
CREATE TABLE performance_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Metric identification
    metric_name VARCHAR(255) NOT NULL,
    metric_type VARCHAR(100) NOT NULL, -- query, transaction, system, custom
    
    -- Metric data
    value DECIMAL(15,6) NOT NULL,
    unit VARCHAR(50),
    
    -- Context
    context JSONB DEFAULT '{}',
    tags JSONB DEFAULT '[]',
    
    -- Timing
    measured_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
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

-- Function to generate API key
CREATE OR REPLACE FUNCTION generate_api_key()
RETURNS TEXT AS $$
DECLARE
    key_chars TEXT := 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    result TEXT := '';
    i INTEGER;
BEGIN
    FOR i IN 1..32 LOOP
        result := result || substr(key_chars, floor(random() * length(key_chars) + 1)::integer, 1);
    END LOOP;
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Function for database health check
CREATE OR REPLACE FUNCTION database_health_check()
RETURNS JSONB AS $$
DECLARE
    result JSONB := '{}';
    table_count INTEGER;
    index_count INTEGER;
    db_size_mb BIGINT;
    active_connections INTEGER;
BEGIN
    -- Count tables
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables 
    WHERE table_schema = 'public';
    
    -- Count indexes
    SELECT COUNT(*) INTO index_count
    FROM pg_indexes 
    WHERE schemaname = 'public';
    
    -- Get database size
    SELECT pg_database_size(current_database()) / 1024 / 1024 INTO db_size_mb;
    
    -- Get active connections
    SELECT COUNT(*) INTO active_connections
    FROM pg_stat_activity 
    WHERE state = 'active';
    
    -- Build result
    result := jsonb_build_object(
        'status', 'healthy',
        'timestamp', CURRENT_TIMESTAMP,
        'database_name', current_database(),
        'tables_count', table_count,
        'indexes_count', index_count,
        'database_size_mb', db_size_mb,
        'active_connections', active_connections,
        'modules', jsonb_build_object(
            'base', true,
            'projects', EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'projects'),
            'tasks', EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'tasks'),
            'analytics', EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'analysis_runs'),
            'prompts', EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'prompt_templates'),
            'events', EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'events'),
            'openevolve', EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'evaluations')
        )
    );
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

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

CREATE TRIGGER update_api_keys_updated_at 
    BEFORE UPDATE ON api_keys 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_system_configuration_updated_at 
    BEFORE UPDATE ON system_configuration 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- INDEXES
-- =============================================================================

-- Organizations indexes
CREATE INDEX idx_organizations_slug ON organizations(slug);
CREATE INDEX idx_organizations_status ON organizations(status) WHERE deleted_at IS NULL;
CREATE INDEX idx_organizations_created_at ON organizations(created_at);
CREATE INDEX idx_organizations_subscription ON organizations(subscription_tier, subscription_status);

-- Users indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_status ON users(status) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_last_active ON users(last_active_at);
CREATE INDEX idx_users_auth_provider ON users(auth_provider, external_id);

-- Organization memberships indexes
CREATE INDEX idx_org_memberships_org_id ON organization_memberships(organization_id);
CREATE INDEX idx_org_memberships_user_id ON organization_memberships(user_id);
CREATE INDEX idx_org_memberships_role ON organization_memberships(role);
CREATE INDEX idx_org_memberships_status ON organization_memberships(status);

-- API keys indexes
CREATE INDEX idx_api_keys_organization ON api_keys(organization_id);
CREATE INDEX idx_api_keys_user ON api_keys(user_id);
CREATE INDEX idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_active ON api_keys(is_active) WHERE is_active = true;
CREATE INDEX idx_api_keys_expires ON api_keys(expires_at) WHERE expires_at IS NOT NULL;

-- System configuration indexes
CREATE INDEX idx_system_config_key ON system_configuration(config_key);
CREATE INDEX idx_system_config_category ON system_configuration(category);

-- Audit log indexes
CREATE INDEX idx_audit_log_table ON audit_log(table_name);
CREATE INDEX idx_audit_log_record ON audit_log(record_id);
CREATE INDEX idx_audit_log_operation ON audit_log(operation);
CREATE INDEX idx_audit_log_actor ON audit_log(actor_id);
CREATE INDEX idx_audit_log_occurred_at ON audit_log(occurred_at);

-- Performance metrics indexes
CREATE INDEX idx_performance_metrics_name ON performance_metrics(metric_name);
CREATE INDEX idx_performance_metrics_type ON performance_metrics(metric_type);
CREATE INDEX idx_performance_metrics_measured_at ON performance_metrics(measured_at);

-- GIN indexes for JSONB fields
CREATE INDEX idx_organizations_settings_gin USING gin (settings);
CREATE INDEX idx_users_preferences_gin USING gin (preferences);
CREATE INDEX idx_org_memberships_permissions_gin USING gin (permissions);
CREATE INDEX idx_audit_log_context_gin USING gin (context);
CREATE INDEX idx_performance_metrics_context_gin USING gin (context);

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
WHERE u.deleted_at IS NULL AND o.deleted_at IS NULL AND om.status = 'active';

-- System health view
CREATE VIEW system_health AS
SELECT 
    'base_schema' as module,
    'active' as status,
    jsonb_build_object(
        'organizations_count', (SELECT COUNT(*) FROM organizations WHERE deleted_at IS NULL),
        'users_count', (SELECT COUNT(*) FROM users WHERE deleted_at IS NULL),
        'active_memberships', (SELECT COUNT(*) FROM organization_memberships WHERE status = 'active'),
        'api_keys_count', (SELECT COUNT(*) FROM api_keys WHERE is_active = true)
    ) as metrics,
    CURRENT_TIMESTAMP as last_checked;

-- =============================================================================
-- INITIAL DATA
-- =============================================================================

-- Insert default system configuration
INSERT INTO system_configuration (config_key, config_value, description, category) VALUES
('system.version', '"1.0.0"', 'System version', 'system'),
('system.maintenance_mode', 'false', 'System maintenance mode', 'system'),
('openevolve.enabled', 'true', 'Enable OpenEvolve integration', 'openevolve'),
('openevolve.evaluation_timeout_ms', '30000', 'Timeout for OpenEvolve evaluations', 'openevolve'),
('openevolve.max_generations', '100', 'Maximum generations for evolution', 'openevolve'),
('analytics.retention_days', '365', 'Data retention period for analytics', 'analytics'),
('analytics.aggregation_interval_hours', '24', 'Interval for analytics aggregation', 'analytics'),
('tasks.max_concurrent_executions', '50', 'Maximum concurrent task executions', 'tasks'),
('tasks.default_timeout_ms', '300000', 'Default timeout for task execution', 'tasks'),
('prompts.cache_ttl_seconds', '3600', 'Cache TTL for prompt templates', 'prompts'),
('prompts.max_variants', '10', 'Maximum variants per prompt for A/B testing', 'prompts'),
('events.batch_size', '1000', 'Batch size for event processing', 'events'),
('events.processing_interval_seconds', '60', 'Interval for event processing', 'events'),
('codegen.org_id', '""', 'Codegen organization ID', 'codegen'),
('codegen.token', '""', 'Codegen API token', 'codegen'),
('autogenlib.enabled', 'true', 'Enable autogenlib integration', 'autogenlib');

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
('00_base_schema', 'Comprehensive base schema with organizations, users, and system configuration');

-- =============================================================================
-- COMMENTS FOR DOCUMENTATION
-- =============================================================================

COMMENT ON TABLE organizations IS 'Top-level tenant isolation for multi-organization support';
COMMENT ON TABLE users IS 'User management with authentication and preferences';
COMMENT ON TABLE organization_memberships IS 'Many-to-many relationship between organizations and users with roles';
COMMENT ON TABLE api_keys IS 'API authentication keys for programmatic access';
COMMENT ON TABLE system_configuration IS 'System-wide configuration settings';
COMMENT ON TABLE audit_log IS 'Comprehensive audit trail for all database changes';
COMMENT ON TABLE performance_metrics IS 'System performance monitoring and metrics';

COMMENT ON FUNCTION update_updated_at_column IS 'Trigger function to automatically update updated_at timestamps';
COMMENT ON FUNCTION generate_api_key IS 'Generate secure random API keys';
COMMENT ON FUNCTION database_health_check IS 'Comprehensive database health check function';

