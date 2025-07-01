-- =============================================================================
-- UNIFIED BASE SCHEMA: Consolidated Foundation for 7-Module System
-- =============================================================================
-- This schema consolidates the best elements from PRs 74, 75, 76 and provides
-- the foundation for all 7 modules: Task DB, Projects DB, Prompts DB, 
-- Codebase DB, Analytics DB, Events DB, and Learning DB.
-- =============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "btree_gist";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Set timezone and configuration
SET timezone = 'UTC';
SET default_text_search_config = 'pg_catalog.english';

-- =============================================================================
-- COMMON ENUMS AND TYPES
-- =============================================================================

-- User roles within organizations
CREATE TYPE user_role AS ENUM (
    'owner',
    'admin', 
    'member',
    'viewer',
    'guest'
);

-- General status types
CREATE TYPE status_type AS ENUM (
    'active',
    'inactive',
    'pending',
    'suspended',
    'deleted',
    'archived'
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
    'technical_debt',
    'architecture',
    'patterns'
);

-- Event sources for multi-platform integration
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
    'learning',
    'custom'
);

-- =============================================================================
-- CORE ORGANIZATIONAL TABLES
-- =============================================================================

-- Organizations table - top-level tenant isolation
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) NOT NULL,
    description TEXT,
    
    -- Organization configuration
    settings JSONB DEFAULT '{}',
    features JSONB DEFAULT '{}',
    limits JSONB DEFAULT '{}',
    
    -- Organization status and metadata
    status status_type DEFAULT 'active',
    tier VARCHAR(50) DEFAULT 'standard',
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT organizations_slug_unique UNIQUE (slug),
    CONSTRAINT organizations_name_not_empty CHECK (length(trim(name)) > 0),
    CONSTRAINT organizations_slug_format CHECK (slug ~ '^[a-z0-9-]+$')
);

-- Users table - comprehensive user management
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    username VARCHAR(100),
    
    -- User profile
    avatar_url TEXT,
    bio TEXT,
    location VARCHAR(255),
    timezone VARCHAR(100) DEFAULT 'UTC',
    
    -- User configuration
    settings JSONB DEFAULT '{}',
    preferences JSONB DEFAULT '{}',
    permissions JSONB DEFAULT '{}',
    
    -- User status and activity
    status status_type DEFAULT 'active',
    last_active_at TIMESTAMP WITH TIME ZONE,
    last_login_at TIMESTAMP WITH TIME ZONE,
    
    -- External integrations
    external_ids JSONB DEFAULT '{}', -- GitHub, Linear, Slack IDs
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT users_email_unique UNIQUE (email),
    CONSTRAINT users_username_unique UNIQUE (username),
    CONSTRAINT users_email_format CHECK (email ~ '^[^@]+@[^@]+\.[^@]+$'),
    CONSTRAINT users_name_not_empty CHECK (length(trim(name)) > 0)
);

-- Organization memberships - many-to-many with enhanced roles
CREATE TABLE organization_memberships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Role and permissions
    role user_role NOT NULL DEFAULT 'member',
    permissions JSONB DEFAULT '{}',
    custom_permissions JSONB DEFAULT '{}',
    
    -- Membership details
    title VARCHAR(255),
    department VARCHAR(255),
    invited_by UUID REFERENCES users(id),
    invitation_token VARCHAR(255),
    invitation_expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Status and timing
    status status_type DEFAULT 'active',
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_access_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT organization_memberships_unique UNIQUE (organization_id, user_id)
);

-- =============================================================================
-- SYSTEM CONFIGURATION AND METADATA
-- =============================================================================

-- System configuration for global settings
CREATE TABLE system_configuration (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    config_key VARCHAR(255) UNIQUE NOT NULL,
    config_value JSONB NOT NULL,
    description TEXT,
    
    -- Configuration metadata
    category VARCHAR(100) DEFAULT 'general',
    is_sensitive BOOLEAN DEFAULT false,
    is_readonly BOOLEAN DEFAULT false,
    is_system BOOLEAN DEFAULT false,
    
    -- Validation and constraints
    validation_schema JSONB DEFAULT '{}',
    allowed_values JSONB DEFAULT '[]',
    
    -- Versioning
    version INTEGER DEFAULT 1,
    previous_value JSONB,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Database metadata and schema versioning
CREATE TABLE database_metadata (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    schema_version VARCHAR(20) NOT NULL DEFAULT '1.0.0',
    initialized_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_migration_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Migration tracking
    migration_history JSONB DEFAULT '[]',
    pending_migrations JSONB DEFAULT '[]',
    
    -- System configuration
    configuration JSONB DEFAULT '{}',
    features_enabled JSONB DEFAULT '[]',
    
    -- System information
    database_name VARCHAR(255),
    database_size_mb BIGINT,
    total_tables INTEGER,
    total_indexes INTEGER,
    
    -- Performance metrics
    query_performance JSONB DEFAULT '{}',
    index_usage JSONB DEFAULT '{}',
    connection_stats JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Schema migrations tracking
CREATE TABLE schema_migrations (
    id SERIAL PRIMARY KEY,
    version VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    module VARCHAR(100),
    
    -- Migration details
    migration_type VARCHAR(50) DEFAULT 'schema', -- schema, data, index
    sql_checksum VARCHAR(64),
    execution_time_ms INTEGER,
    
    -- Status tracking
    status VARCHAR(50) DEFAULT 'pending', -- pending, running, completed, failed, rolled_back
    error_message TEXT,
    rollback_sql TEXT,
    
    -- Metadata
    applied_by VARCHAR(255),
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    rolled_back_at TIMESTAMP WITH TIME ZONE
);

-- =============================================================================
-- AUDIT AND MONITORING TABLES
-- =============================================================================

-- Comprehensive audit log for all changes
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Audit metadata
    table_name VARCHAR(255) NOT NULL,
    record_id UUID NOT NULL,
    operation VARCHAR(20) NOT NULL, -- INSERT, UPDATE, DELETE, TRUNCATE
    
    -- Change tracking
    old_values JSONB,
    new_values JSONB,
    changed_fields JSONB DEFAULT '[]',
    change_summary TEXT,
    
    -- Actor information
    actor_id UUID REFERENCES users(id),
    actor_type VARCHAR(100), -- user, system, api, migration
    actor_name VARCHAR(255),
    session_id VARCHAR(255),
    
    -- Request context
    request_id VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    
    -- Context and metadata
    context JSONB DEFAULT '{}',
    tags JSONB DEFAULT '[]',
    
    -- Timing
    occurred_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Performance monitoring and metrics
CREATE TABLE performance_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Metric identification
    metric_name VARCHAR(255) NOT NULL,
    metric_type VARCHAR(100) NOT NULL, -- query, transaction, system, custom
    module VARCHAR(100), -- tasks, projects, analytics, etc.
    
    -- Metric data
    value DECIMAL(15,6) NOT NULL,
    unit VARCHAR(50),
    threshold_warning DECIMAL(15,6),
    threshold_critical DECIMAL(15,6),
    
    -- Context and dimensions
    context JSONB DEFAULT '{}',
    dimensions JSONB DEFAULT '{}',
    tags JSONB DEFAULT '[]',
    
    -- Timing and aggregation
    measured_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    aggregation_period VARCHAR(50), -- instant, 1m, 5m, 1h, 1d
    
    -- Metadata
    metadata JSONB DEFAULT '{}'
);

-- System health monitoring
CREATE TABLE health_checks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Health check identification
    check_name VARCHAR(255) NOT NULL,
    check_type VARCHAR(100) NOT NULL, -- database, service, integration
    module VARCHAR(100),
    
    -- Health status
    status VARCHAR(50) NOT NULL, -- healthy, warning, critical, unknown
    message TEXT,
    details JSONB DEFAULT '{}',
    
    -- Metrics
    response_time_ms INTEGER,
    success_rate DECIMAL(5,2),
    
    -- Timing
    checked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    next_check_at TIMESTAMP WITH TIME ZONE,
    
    -- Configuration
    check_interval_seconds INTEGER DEFAULT 300,
    timeout_seconds INTEGER DEFAULT 30,
    
    -- Metadata
    metadata JSONB DEFAULT '{}'
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

-- Function to create audit log entries
CREATE OR REPLACE FUNCTION create_audit_log_entry()
RETURNS TRIGGER AS $$
DECLARE
    old_data JSONB;
    new_data JSONB;
    changed_fields JSONB := '[]'::JSONB;
BEGIN
    -- Handle different operations
    IF TG_OP = 'DELETE' THEN
        old_data := to_jsonb(OLD);
        new_data := NULL;
    ELSIF TG_OP = 'INSERT' THEN
        old_data := NULL;
        new_data := to_jsonb(NEW);
    ELSIF TG_OP = 'UPDATE' THEN
        old_data := to_jsonb(OLD);
        new_data := to_jsonb(NEW);
        
        -- Identify changed fields
        SELECT jsonb_agg(key) INTO changed_fields
        FROM jsonb_each(old_data) old_kv
        JOIN jsonb_each(new_data) new_kv ON old_kv.key = new_kv.key
        WHERE old_kv.value IS DISTINCT FROM new_kv.value;
    END IF;
    
    -- Insert audit log entry
    INSERT INTO audit_log (
        table_name,
        record_id,
        operation,
        old_values,
        new_values,
        changed_fields,
        actor_type
    ) VALUES (
        TG_TABLE_NAME,
        COALESCE(NEW.id, OLD.id),
        TG_OP,
        old_data,
        new_data,
        changed_fields,
        'system'
    );
    
    RETURN COALESCE(NEW, OLD);
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
    slow_queries INTEGER;
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
    
    -- Check for slow queries (> 1 second)
    SELECT COUNT(*) INTO slow_queries
    FROM pg_stat_activity 
    WHERE state = 'active' 
    AND query_start < NOW() - INTERVAL '1 second';
    
    -- Build result
    result := jsonb_build_object(
        'status', CASE 
            WHEN slow_queries > 10 THEN 'critical'
            WHEN slow_queries > 5 THEN 'warning'
            ELSE 'healthy'
        END,
        'timestamp', NOW(),
        'database_name', current_database(),
        'database_size_mb', db_size_mb,
        'tables_count', table_count,
        'indexes_count', index_count,
        'active_connections', active_connections,
        'slow_queries', slow_queries,
        'modules_status', jsonb_build_object(
            'base_schema', true,
            'tasks', EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'tasks'),
            'projects', EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'projects'),
            'analytics', EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'analysis_runs'),
            'prompts', EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'prompt_templates'),
            'events', EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'events'),
            'learning', EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'learning_models')
        )
    );
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- TRIGGERS FOR AUTOMATIC TIMESTAMP UPDATES
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

CREATE TRIGGER update_system_configuration_updated_at 
    BEFORE UPDATE ON system_configuration 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_database_metadata_updated_at 
    BEFORE UPDATE ON database_metadata 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- INDEXES FOR OPTIMAL PERFORMANCE
-- =============================================================================

-- Organizations indexes
CREATE INDEX idx_organizations_slug ON organizations(slug);
CREATE INDEX idx_organizations_status ON organizations(status) WHERE deleted_at IS NULL;
CREATE INDEX idx_organizations_created_at ON organizations(created_at);
CREATE INDEX idx_organizations_tier ON organizations(tier);

-- Users indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_status ON users(status) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_last_active ON users(last_active_at);
CREATE INDEX idx_users_external_ids_gin USING gin (external_ids);

-- Organization memberships indexes
CREATE INDEX idx_org_memberships_org_id ON organization_memberships(organization_id);
CREATE INDEX idx_org_memberships_user_id ON organization_memberships(user_id);
CREATE INDEX idx_org_memberships_role ON organization_memberships(role);
CREATE INDEX idx_org_memberships_status ON organization_memberships(status);

-- System configuration indexes
CREATE INDEX idx_system_config_key ON system_configuration(config_key);
CREATE INDEX idx_system_config_category ON system_configuration(category);
CREATE INDEX idx_system_config_sensitive ON system_configuration(is_sensitive);

-- Audit log indexes
CREATE INDEX idx_audit_log_table_name ON audit_log(table_name);
CREATE INDEX idx_audit_log_record_id ON audit_log(record_id);
CREATE INDEX idx_audit_log_operation ON audit_log(operation);
CREATE INDEX idx_audit_log_actor_id ON audit_log(actor_id);
CREATE INDEX idx_audit_log_occurred_at ON audit_log(occurred_at);
CREATE INDEX idx_audit_log_composite ON audit_log(table_name, occurred_at DESC);

-- Performance metrics indexes
CREATE INDEX idx_performance_metrics_name ON performance_metrics(metric_name);
CREATE INDEX idx_performance_metrics_type ON performance_metrics(metric_type);
CREATE INDEX idx_performance_metrics_module ON performance_metrics(module);
CREATE INDEX idx_performance_metrics_measured_at ON performance_metrics(measured_at);
CREATE INDEX idx_performance_metrics_composite ON performance_metrics(metric_name, measured_at DESC);

-- Health checks indexes
CREATE INDEX idx_health_checks_name ON health_checks(check_name);
CREATE INDEX idx_health_checks_type ON health_checks(check_type);
CREATE INDEX idx_health_checks_status ON health_checks(status);
CREATE INDEX idx_health_checks_checked_at ON health_checks(checked_at);

-- GIN indexes for JSONB fields
CREATE INDEX idx_organizations_settings_gin USING gin (settings);
CREATE INDEX idx_users_preferences_gin USING gin (preferences);
CREATE INDEX idx_audit_log_context_gin USING gin (context);
CREATE INDEX idx_performance_metrics_context_gin USING gin (context);

-- =============================================================================
-- VIEWS FOR COMMON QUERIES
-- =============================================================================

-- Active organizations view
CREATE VIEW active_organizations AS
SELECT * FROM organizations 
WHERE status = 'active' AND deleted_at IS NULL;

-- Active users view
CREATE VIEW active_users AS
SELECT * FROM users 
WHERE status = 'active' AND deleted_at IS NULL;

-- Organization members view with enhanced details
CREATE VIEW organization_members AS
SELECT 
    om.organization_id,
    om.user_id,
    om.role,
    om.permissions,
    om.title,
    om.department,
    om.joined_at,
    om.last_access_at,
    u.name as user_name,
    u.email as user_email,
    u.username,
    u.last_active_at as user_last_active,
    o.name as organization_name,
    o.slug as organization_slug
FROM organization_memberships om
JOIN users u ON om.user_id = u.id
JOIN organizations o ON om.organization_id = o.id
WHERE u.deleted_at IS NULL 
AND o.deleted_at IS NULL 
AND om.status = 'active';

-- System health overview
CREATE VIEW system_health_overview AS
SELECT 
    'database' as component,
    CASE 
        WHEN COUNT(*) FILTER (WHERE status = 'critical') > 0 THEN 'critical'
        WHEN COUNT(*) FILTER (WHERE status = 'warning') > 0 THEN 'warning'
        ELSE 'healthy'
    END as overall_status,
    COUNT(*) as total_checks,
    COUNT(*) FILTER (WHERE status = 'healthy') as healthy_checks,
    COUNT(*) FILTER (WHERE status = 'warning') as warning_checks,
    COUNT(*) FILTER (WHERE status = 'critical') as critical_checks,
    MAX(checked_at) as last_check_time
FROM health_checks
WHERE checked_at >= NOW() - INTERVAL '1 hour';

-- =============================================================================
-- INITIAL DATA AND CONFIGURATION
-- =============================================================================

-- Insert initial database metadata
INSERT INTO database_metadata (
    schema_version,
    database_name,
    configuration,
    features_enabled
) VALUES (
    '1.0.0',
    current_database(),
    jsonb_build_object(
        'modules', ARRAY['tasks', 'projects', 'prompts', 'codebase', 'analytics', 'events', 'learning'],
        'features', ARRAY['openevolve_integration', 'workflow_management', 'real_time_analytics', 'continuous_learning'],
        'performance_targets', jsonb_build_object(
            'query_response_time_ms', 100,
            'concurrent_users', 1000,
            'data_retention_days', 365,
            'analytics_refresh_interval_minutes', 15
        )
    ),
    ARRAY['audit_logging', 'performance_monitoring', 'health_checks', 'multi_tenant', 'real_time_events']
);

-- Insert default system configuration
INSERT INTO system_configuration (config_key, config_value, description, category) VALUES
-- Core system settings
('system.name', '"Comprehensive CI/CD Platform"', 'System display name', 'system'),
('system.version', '"1.0.0"', 'Current system version', 'system'),
('system.maintenance_mode', 'false', 'Enable maintenance mode', 'system'),

-- Performance settings
('performance.query_timeout_ms', '30000', 'Default query timeout', 'performance'),
('performance.connection_pool_size', '20', 'Database connection pool size', 'performance'),
('performance.max_concurrent_requests', '1000', 'Maximum concurrent requests', 'performance'),

-- Module-specific settings
('tasks.max_concurrent_executions', '50', 'Maximum concurrent task executions', 'tasks'),
('tasks.default_timeout_ms', '300000', 'Default timeout for task execution', 'tasks'),
('analytics.retention_days', '365', 'Data retention period for analytics', 'analytics'),
('analytics.aggregation_interval_hours', '1', 'Interval for analytics aggregation', 'analytics'),
('prompts.cache_ttl_seconds', '3600', 'Cache TTL for prompt templates', 'prompts'),
('events.batch_size', '1000', 'Batch size for event processing', 'events'),
('events.processing_interval_seconds', '60', 'Interval for event processing', 'events'),
('learning.model_update_interval_hours', '24', 'Interval for model updates', 'learning'),
('learning.feedback_aggregation_threshold', '100', 'Minimum feedback for model updates', 'learning'),

-- OpenEvolve integration
('openevolve.enabled', 'true', 'Enable OpenEvolve integration', 'openevolve'),
('openevolve.evaluation_timeout_ms', '30000', 'Timeout for OpenEvolve evaluations', 'openevolve'),
('openevolve.max_generations', '100', 'Maximum generations for evolution', 'openevolve'),
('openevolve.learning_rate', '0.01', 'Learning rate for model adaptation', 'openevolve');

-- Record this migration
INSERT INTO schema_migrations (version, description, module) VALUES 
('00_unified_base_schema', 'Unified base schema consolidating PRs 74, 75, 76 with 7-module support', 'base');

-- Insert initial health check
INSERT INTO health_checks (check_name, check_type, status, message) VALUES
('database_initialization', 'database', 'healthy', 'Base schema initialized successfully');

-- =============================================================================
-- COMMENTS FOR DOCUMENTATION
-- =============================================================================

COMMENT ON TABLE organizations IS 'Multi-tenant organization management with enhanced configuration';
COMMENT ON TABLE users IS 'Comprehensive user management with external integrations';
COMMENT ON TABLE organization_memberships IS 'Organization membership with role-based access control';
COMMENT ON TABLE system_configuration IS 'System-wide configuration settings with validation';
COMMENT ON TABLE database_metadata IS 'Database schema version and system metadata';
COMMENT ON TABLE schema_migrations IS 'Schema migration tracking with rollback support';
COMMENT ON TABLE audit_log IS 'Comprehensive audit trail for all database changes';
COMMENT ON TABLE performance_metrics IS 'System performance monitoring and metrics collection';
COMMENT ON TABLE health_checks IS 'System health monitoring and alerting';

COMMENT ON FUNCTION update_updated_at_column IS 'Automatically update updated_at timestamp on record changes';
COMMENT ON FUNCTION create_audit_log_entry IS 'Create comprehensive audit log entries for all changes';
COMMENT ON FUNCTION database_health_check IS 'Comprehensive database health check with module status';

-- Final status message
DO $$
BEGIN
    RAISE NOTICE '🗄️ Unified Base Schema initialized successfully!';
    RAISE NOTICE 'Schema version: 1.0.0';
    RAISE NOTICE 'Modules supported: 7 (Tasks, Projects, Prompts, Codebase, Analytics, Events, Learning)';
    RAISE NOTICE 'Features: Multi-tenant, Audit logging, Performance monitoring, Health checks';
    RAISE NOTICE 'Database: %', current_database();
    RAISE NOTICE 'Timestamp: %', NOW();
END $$;

