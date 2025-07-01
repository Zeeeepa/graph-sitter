-- =============================================================================
-- Database Extensions and Initial Setup
-- =============================================================================
-- This script sets up the required PostgreSQL extensions and basic
-- configuration for the graph-sitter comprehensive database system.
-- =============================================================================

-- Set timezone and text search configuration
SET timezone = 'UTC';
SET default_text_search_config = 'pg_catalog.english';

-- Enable required PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp"
    SCHEMA public
    VERSION "1.1";

CREATE EXTENSION IF NOT EXISTS "pg_trgm"
    SCHEMA public
    VERSION "1.6";

CREATE EXTENSION IF NOT EXISTS "btree_gin"
    SCHEMA public
    VERSION "1.3";

CREATE EXTENSION IF NOT EXISTS "btree_gist"
    SCHEMA public
    VERSION "1.7";

CREATE EXTENSION IF NOT EXISTS "pg_stat_statements"
    SCHEMA public
    VERSION "1.10";

-- Create schemas for better organization
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS monitoring;
CREATE SCHEMA IF NOT EXISTS migrations;

-- Set search path to include all schemas
ALTER DATABASE CURRENT SET search_path = public, analytics, monitoring, migrations;

-- Create common enums used across modules
CREATE TYPE user_role AS ENUM (
    'owner',
    'admin', 
    'member',
    'viewer'
);

CREATE TYPE status_type AS ENUM (
    'active',
    'inactive',
    'pending',
    'suspended',
    'deleted'
);

CREATE TYPE priority_level AS ENUM (
    'low',
    'normal', 
    'high',
    'urgent',
    'critical'
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
    'custom'
);

CREATE TYPE event_type AS ENUM (
    'issue_created',
    'issue_updated', 
    'issue_closed',
    'comment_added',
    'pr_opened',
    'pr_merged',
    'pr_closed',
    'commit_pushed',
    'deployment_started',
    'deployment_completed',
    'deployment_failed',
    'task_created',
    'task_started',
    'task_completed',
    'task_failed',
    'evaluation_started',
    'evaluation_completed',
    'workflow_triggered',
    'system_alert',
    'custom_event'
);

-- Create database metadata table
CREATE TABLE database_metadata (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    schema_version VARCHAR(20) NOT NULL DEFAULT '1.0.0',
    initialized_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_migration_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    migration_history JSONB DEFAULT '[]',
    configuration JSONB DEFAULT '{}',
    
    -- System information
    database_name VARCHAR(255),
    database_size_mb BIGINT,
    total_tables INTEGER,
    total_indexes INTEGER,
    
    -- Performance metrics
    query_performance JSONB DEFAULT '{}',
    index_usage JSONB DEFAULT '{}',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert initial metadata
INSERT INTO database_metadata (
    schema_version,
    database_name,
    configuration
) VALUES (
    '1.0.0',
    current_database(),
    jsonb_build_object(
        'modules', ARRAY['organizations', 'projects', 'tasks', 'analytics', 'prompts', 'events', 'learning'],
        'features', ARRAY['multi_tenant', 'audit_logging', 'performance_monitoring', 'openevolve_integration'],
        'performance_targets', jsonb_build_object(
            'query_response_time_ms', 1000,
            'concurrent_operations', 1000,
            'data_retention_days', 365
        )
    )
);

-- Create system configuration table
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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for system configuration
CREATE INDEX idx_system_config_key ON system_configuration(config_key);
CREATE INDEX idx_system_config_category ON system_configuration(category);

-- Insert default system configuration
INSERT INTO system_configuration (config_key, config_value, description, category) VALUES
('database.query_timeout_ms', '30000', 'Default query timeout in milliseconds', 'database'),
('database.connection_pool_size', '20', 'Database connection pool size', 'database'),
('database.slow_query_threshold_ms', '1000', 'Threshold for slow query logging', 'database'),
('analytics.retention_days', '365', 'Data retention period for analytics', 'analytics'),
('analytics.aggregation_interval_hours', '24', 'Interval for analytics aggregation', 'analytics'),
('tasks.max_concurrent_executions', '50', 'Maximum concurrent task executions', 'tasks'),
('tasks.default_timeout_ms', '300000', 'Default timeout for task execution', 'tasks'),
('prompts.cache_ttl_seconds', '3600', 'Cache TTL for prompt templates', 'prompts'),
('prompts.max_variants', '10', 'Maximum variants per prompt for A/B testing', 'prompts'),
('events.batch_size', '1000', 'Batch size for event processing', 'events'),
('events.processing_interval_seconds', '60', 'Interval for event processing', 'events'),
('learning.pattern_detection_threshold', '0.8', 'Threshold for pattern detection', 'learning'),
('learning.optimization_interval_hours', '168', 'Interval for system optimization', 'learning');

-- Create audit log table for tracking changes
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
    actor_id VARCHAR(255),
    actor_type VARCHAR(100),
    session_id VARCHAR(255),
    
    -- Context
    context JSONB DEFAULT '{}',
    
    -- Timing
    occurred_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for audit log
CREATE INDEX idx_audit_log_table ON audit_log(table_name);
CREATE INDEX idx_audit_log_record ON audit_log(record_id);
CREATE INDEX idx_audit_log_operation ON audit_log(operation);
CREATE INDEX idx_audit_log_actor ON audit_log(actor_id);
CREATE INDEX idx_audit_log_occurred_at ON audit_log(occurred_at);

-- Create performance monitoring table
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
    measured_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance metrics
CREATE INDEX idx_performance_metrics_name ON performance_metrics(metric_name);
CREATE INDEX idx_performance_metrics_type ON performance_metrics(metric_type);
CREATE INDEX idx_performance_metrics_measured_at ON performance_metrics(measured_at);
CREATE INDEX idx_performance_metrics_context_gin USING gin (context);

-- Create function for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create function for audit logging
CREATE OR REPLACE FUNCTION create_audit_log()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_log (
        table_name,
        record_id,
        operation,
        old_values,
        new_values,
        changed_fields,
        actor_id,
        context
    ) VALUES (
        TG_TABLE_NAME,
        COALESCE(NEW.id, OLD.id),
        TG_OP,
        CASE WHEN TG_OP = 'DELETE' THEN to_jsonb(OLD) ELSE NULL END,
        CASE WHEN TG_OP = 'INSERT' THEN to_jsonb(NEW) 
             WHEN TG_OP = 'UPDATE' THEN to_jsonb(NEW) 
             ELSE NULL END,
        CASE WHEN TG_OP = 'UPDATE' THEN 
            (SELECT array_agg(key) FROM jsonb_each(to_jsonb(NEW)) WHERE to_jsonb(NEW) ->> key IS DISTINCT FROM to_jsonb(OLD) ->> key)
        ELSE NULL END,
        current_setting('app.current_user_id', true),
        jsonb_build_object(
            'timestamp', NOW(),
            'table', TG_TABLE_NAME,
            'operation', TG_OP
        )
    );
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Create database health check function
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
        'timestamp', NOW(),
        'database_name', current_database(),
        'tables_count', table_count,
        'indexes_count', index_count,
        'database_size_mb', db_size_mb,
        'active_connections', active_connections,
        'extensions', ARRAY['uuid-ossp', 'pg_trgm', 'btree_gin', 'btree_gist', 'pg_stat_statements']
    );
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Create maintenance function
CREATE OR REPLACE FUNCTION perform_maintenance()
RETURNS JSONB AS $$
DECLARE
    result JSONB := '{}';
    cleanup_count INTEGER := 0;
BEGIN
    -- Vacuum and analyze
    VACUUM ANALYZE;
    
    -- Clean up old audit logs (older than 1 year)
    DELETE FROM audit_log 
    WHERE occurred_at < NOW() - INTERVAL '1 year';
    GET DIAGNOSTICS cleanup_count = ROW_COUNT;
    
    -- Clean up old performance metrics (older than 90 days)
    DELETE FROM performance_metrics 
    WHERE measured_at < NOW() - INTERVAL '90 days';
    
    -- Update database metadata
    UPDATE database_metadata SET
        last_migration_at = NOW(),
        updated_at = NOW(),
        database_size_mb = pg_database_size(current_database()) / 1024 / 1024,
        total_tables = (
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        ),
        total_indexes = (
            SELECT COUNT(*) 
            FROM pg_indexes 
            WHERE schemaname = 'public'
        );
    
    result := jsonb_build_object(
        'status', 'completed',
        'timestamp', NOW(),
        'audit_logs_cleaned', cleanup_count,
        'actions_performed', ARRAY[
            'vacuum_analyze',
            'cleanup_audit_logs',
            'cleanup_performance_metrics',
            'update_metadata'
        ]
    );
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Log initialization
INSERT INTO audit_log (
    table_name,
    record_id,
    operation,
    new_values,
    actor_id,
    actor_type,
    context
) VALUES (
    'database_metadata',
    (SELECT id FROM database_metadata LIMIT 1),
    'INITIALIZE',
    jsonb_build_object(
        'schema_version', '1.0.0',
        'modules_initialized', ARRAY['extensions', 'base_schema'],
        'extensions_enabled', ARRAY['uuid-ossp', 'pg_trgm', 'btree_gin', 'btree_gist', 'pg_stat_statements']
    ),
    'system',
    'initialization',
    jsonb_build_object(
        'initialization_type', 'extensions_and_base',
        'database_name', current_database(),
        'timestamp', NOW()
    )
);

-- Comments for documentation
COMMENT ON TABLE database_metadata IS 'Database schema version and configuration metadata';
COMMENT ON TABLE system_configuration IS 'System-wide configuration settings';
COMMENT ON TABLE audit_log IS 'Comprehensive audit trail for all database changes';
COMMENT ON TABLE performance_metrics IS 'System performance monitoring and metrics';

COMMENT ON FUNCTION database_health_check IS 'Comprehensive database health check';
COMMENT ON FUNCTION perform_maintenance IS 'Perform routine database maintenance tasks';
COMMENT ON FUNCTION update_updated_at_column IS 'Trigger function for automatic timestamp updates';
COMMENT ON FUNCTION create_audit_log IS 'Trigger function for automatic audit logging';

-- Final status message
DO $$
BEGIN
    RAISE NOTICE 'Database extensions and base schema initialized successfully!';
    RAISE NOTICE 'Schema version: 1.0.0';
    RAISE NOTICE 'Extensions: uuid-ossp, pg_trgm, btree_gin, btree_gist, pg_stat_statements';
    RAISE NOTICE 'Database: %', current_database();
    RAISE NOTICE 'Timestamp: %', NOW();
END $$;

