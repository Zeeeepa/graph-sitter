-- Comprehensive Database Initialization Script
-- Initializes the complete task management system with all 5 database categories

-- Set up database configuration
SET timezone = 'UTC';
SET default_text_search_config = 'pg_catalog.english';

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "btree_gist";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create schema for better organization
CREATE SCHEMA IF NOT EXISTS task_management;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS prompts;
CREATE SCHEMA IF NOT EXISTS events;
CREATE SCHEMA IF NOT EXISTS openevolve;

-- Set search path
SET search_path = public, task_management, analytics, prompts, events, openevolve;

-- Create base enums used across modules
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

-- Initialize database metadata
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
        'modules', ARRAY['tasks', 'analytics', 'prompts', 'events', 'projects'],
        'features', ARRAY['openevolve_integration', 'workflow_management', 'real_time_analytics'],
        'performance_targets', jsonb_build_object(
            'query_response_time_ms', 100,
            'concurrent_users', 1000,
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
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_system_config_key (config_key),
    INDEX idx_system_config_category (category)
);

-- Insert default system configuration
INSERT INTO system_configuration (config_key, config_value, description, category) VALUES
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
('events.processing_interval_seconds', '60', 'Interval for event processing', 'events');

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
    occurred_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes
    INDEX idx_audit_log_table (table_name),
    INDEX idx_audit_log_record (record_id),
    INDEX idx_audit_log_operation (operation),
    INDEX idx_audit_log_actor (actor_id),
    INDEX idx_audit_log_occurred_at (occurred_at)
);

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
    measured_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes
    INDEX idx_performance_metrics_name (metric_name),
    INDEX idx_performance_metrics_type (metric_type),
    INDEX idx_performance_metrics_measured_at (measured_at),
    
    -- GIN index for context
    INDEX idx_performance_metrics_context_gin USING gin (context)
);

-- Create health check functions
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
    SELECT pg_size_pretty(pg_database_size(current_database()))::TEXT INTO db_size_mb;
    
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
        'database_size', db_size_mb,
        'active_connections', active_connections,
        'modules', jsonb_build_object(
            'tasks', EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'tasks'),
            'analytics', EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'codebase_analysis'),
            'prompts', EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'prompts'),
            'events', EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'events'),
            'projects', EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'projects')
        )
    );
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Create function to get system statistics
CREATE OR REPLACE FUNCTION get_system_statistics()
RETURNS JSONB AS $$
DECLARE
    stats JSONB := '{}';
    task_stats JSONB;
    event_stats JSONB;
    prompt_stats JSONB;
    project_stats JSONB;
BEGIN
    -- Task statistics
    SELECT jsonb_build_object(
        'total_tasks', COUNT(*),
        'active_tasks', COUNT(*) FILTER (WHERE status IN ('pending', 'in_progress', 'assigned')),
        'completed_tasks', COUNT(*) FILTER (WHERE status = 'completed'),
        'failed_tasks', COUNT(*) FILTER (WHERE status = 'failed')
    ) INTO task_stats
    FROM tasks;
    
    -- Event statistics
    SELECT jsonb_build_object(
        'total_events', COUNT(*),
        'events_today', COUNT(*) FILTER (WHERE occurred_at >= CURRENT_DATE),
        'events_this_week', COUNT(*) FILTER (WHERE occurred_at >= CURRENT_DATE - INTERVAL '7 days')
    ) INTO event_stats
    FROM events;
    
    -- Prompt statistics
    SELECT jsonb_build_object(
        'total_prompts', COUNT(*),
        'active_prompts', COUNT(*) FILTER (WHERE usage_count > 0),
        'total_executions', COALESCE(SUM(usage_count), 0)
    ) INTO prompt_stats
    FROM prompts;
    
    -- Project statistics
    SELECT jsonb_build_object(
        'total_projects', COUNT(*),
        'active_projects', COUNT(*) FILTER (WHERE status = 'active'),
        'total_repositories', (SELECT COUNT(*) FROM repositories)
    ) INTO project_stats
    FROM projects;
    
    -- Combine all statistics
    stats := jsonb_build_object(
        'generated_at', NOW(),
        'tasks', task_stats,
        'events', event_stats,
        'prompts', prompt_stats,
        'projects', project_stats
    );
    
    RETURN stats;
END;
$$ LANGUAGE plpgsql;

-- Create function for database maintenance
CREATE OR REPLACE FUNCTION perform_maintenance()
RETURNS JSONB AS $$
DECLARE
    result JSONB := '{}';
    vacuum_result TEXT;
    analyze_result TEXT;
    reindex_count INTEGER := 0;
BEGIN
    -- Vacuum and analyze
    VACUUM ANALYZE;
    
    -- Update statistics
    ANALYZE;
    
    -- Clean up old audit logs (older than 1 year)
    DELETE FROM audit_log 
    WHERE occurred_at < NOW() - INTERVAL '1 year';
    
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
        'actions_performed', ARRAY[
            'vacuum_analyze',
            'update_statistics', 
            'cleanup_audit_logs',
            'cleanup_performance_metrics',
            'update_metadata'
        ]
    );
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Create indexes for better performance
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_log_composite 
ON audit_log (table_name, occurred_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_performance_metrics_composite 
ON performance_metrics (metric_name, measured_at DESC);

-- Create materialized views for analytics
CREATE MATERIALIZED VIEW daily_task_summary AS
SELECT 
    DATE(created_at) as date,
    COUNT(*) as total_tasks,
    COUNT(*) FILTER (WHERE status = 'completed') as completed_tasks,
    COUNT(*) FILTER (WHERE status = 'failed') as failed_tasks,
    AVG(actual_hours) as avg_hours,
    AVG(complexity_score) as avg_complexity
FROM tasks
WHERE created_at >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;

CREATE MATERIALIZED VIEW daily_event_summary AS
SELECT 
    DATE(occurred_at) as date,
    source,
    type,
    COUNT(*) as event_count
FROM events
WHERE occurred_at >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY DATE(occurred_at), source, type
ORDER BY date DESC, event_count DESC;

-- Create unique indexes on materialized views
CREATE UNIQUE INDEX idx_daily_task_summary_date 
ON daily_task_summary (date);

CREATE UNIQUE INDEX idx_daily_event_summary_composite 
ON daily_event_summary (date, source, type);

-- Create function to refresh materialized views
CREATE OR REPLACE FUNCTION refresh_analytics_views()
RETURNS VOID AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY daily_task_summary;
    REFRESH MATERIALIZED VIEW CONCURRENTLY daily_event_summary;
END;
$$ LANGUAGE plpgsql;

-- Create scheduled job function (to be called by external scheduler)
CREATE OR REPLACE FUNCTION scheduled_maintenance()
RETURNS JSONB AS $$
DECLARE
    maintenance_result JSONB;
BEGIN
    -- Perform maintenance
    SELECT perform_maintenance() INTO maintenance_result;
    
    -- Refresh analytics views
    PERFORM refresh_analytics_views();
    
    -- Log performance metrics
    INSERT INTO performance_metrics (metric_name, metric_type, value, unit, context)
    VALUES 
        ('database_size_mb', 'system', pg_database_size(current_database()) / 1024 / 1024, 'MB', '{}'),
        ('active_connections', 'system', (SELECT COUNT(*) FROM pg_stat_activity WHERE state = 'active'), 'count', '{}'),
        ('total_tables', 'system', (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'), 'count', '{}');
    
    RETURN jsonb_build_object(
        'maintenance', maintenance_result,
        'analytics_refreshed', true,
        'metrics_logged', true,
        'timestamp', NOW()
    );
END;
$$ LANGUAGE plpgsql;

-- Create notification functions for real-time updates
CREATE OR REPLACE FUNCTION notify_task_change()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM pg_notify(
        'task_changes',
        jsonb_build_object(
            'operation', TG_OP,
            'task_id', COALESCE(NEW.id, OLD.id),
            'status', CASE WHEN NEW IS NOT NULL THEN NEW.status ELSE NULL END,
            'timestamp', NOW()
        )::TEXT
    );
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Create triggers for real-time notifications
CREATE TRIGGER task_change_notification
    AFTER INSERT OR UPDATE OR DELETE ON tasks
    FOR EACH ROW EXECUTE FUNCTION notify_task_change();

-- Create role-based access control
CREATE ROLE task_manager_readonly;
CREATE ROLE task_manager_readwrite;
CREATE ROLE task_manager_admin;

-- Grant permissions
GRANT SELECT ON ALL TABLES IN SCHEMA public TO task_manager_readonly;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO task_manager_readwrite;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO task_manager_admin;

-- Grant sequence permissions
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO task_manager_readwrite;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO task_manager_admin;

-- Create final initialization log
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
        'modules_initialized', ARRAY['tasks', 'analytics', 'prompts', 'events', 'projects'],
        'features_enabled', ARRAY['openevolve_integration', 'workflow_management', 'real_time_analytics']
    ),
    'system',
    'initialization',
    jsonb_build_object(
        'initialization_type', 'comprehensive',
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
COMMENT ON FUNCTION get_system_statistics IS 'Get current system statistics across all modules';
COMMENT ON FUNCTION perform_maintenance IS 'Perform routine database maintenance tasks';
COMMENT ON FUNCTION refresh_analytics_views IS 'Refresh materialized views for analytics';
COMMENT ON FUNCTION scheduled_maintenance IS 'Scheduled maintenance job function';

-- Final status message
DO $$
BEGIN
    RAISE NOTICE 'Comprehensive Task Management System database initialized successfully!';
    RAISE NOTICE 'Schema version: 1.0.0';
    RAISE NOTICE 'Modules: Tasks, Analytics, Prompts, Events, Projects';
    RAISE NOTICE 'Features: OpenEvolve Integration, Workflow Management, Real-time Analytics';
    RAISE NOTICE 'Database: %', current_database();
    RAISE NOTICE 'Timestamp: %', NOW();
END $$;

