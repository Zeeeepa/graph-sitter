-- =============================================================================
-- COMPREHENSIVE DATABASE INITIALIZATION SCRIPT
-- =============================================================================
-- Initializes the complete task management system with all 6 database modules:
-- Base, Projects, Tasks, Analytics, Prompts, Events, and OpenEvolve
-- =============================================================================

-- Set up database configuration
SET timezone = 'UTC';
SET default_text_search_config = 'pg_catalog.english';

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "btree_gist";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create schemas for better organization
CREATE SCHEMA IF NOT EXISTS task_management;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS prompts;
CREATE SCHEMA IF NOT EXISTS events;
CREATE SCHEMA IF NOT EXISTS openevolve;

-- Set search path
SET search_path = public, task_management, analytics, prompts, events, openevolve;

-- =============================================================================
-- DATABASE METADATA AND TRACKING
-- =============================================================================

-- Initialize database metadata
CREATE TABLE IF NOT EXISTS database_metadata (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    schema_version VARCHAR(20) NOT NULL DEFAULT '1.0.0',
    initialized_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_migration_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
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
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
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
        'modules', ARRAY['base', 'projects', 'tasks', 'analytics', 'prompts', 'events', 'openevolve'],
        'features', ARRAY[
            'openevolve_integration', 
            'workflow_management', 
            'real_time_analytics',
            'self_healing_architecture',
            'continuous_learning',
            'intelligent_task_management',
            'end_to_end_automation'
        ],
        'performance_targets', jsonb_build_object(
            'query_response_time_ms', 100,
            'concurrent_users', 1000,
            'data_retention_days', 365,
            'analysis_throughput_loc_per_minute', 100000
        ),
        'integrations', jsonb_build_object(
            'codegen_api', true,
            'autogenlib', true,
            'openevolve', true,
            'linear', true,
            'github', true,
            'slack', true
        )
    )
) ON CONFLICT DO NOTHING;

-- =============================================================================
-- HEALTH CHECK AND MONITORING FUNCTIONS
-- =============================================================================

-- Enhanced database health check function
CREATE OR REPLACE FUNCTION database_health_check()
RETURNS JSONB AS $$
DECLARE
    result JSONB := '{}';
    table_count INTEGER;
    index_count INTEGER;
    db_size_mb BIGINT;
    active_connections INTEGER;
    module_status JSONB;
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
    
    -- Check module status
    module_status := jsonb_build_object(
        'base', EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'organizations'),
        'projects', EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'projects'),
        'tasks', EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'tasks'),
        'analytics', EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'analysis_runs'),
        'prompts', EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'prompt_templates'),
        'events', EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'events'),
        'openevolve', EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'evaluations')
    );
    
    -- Build result
    result := jsonb_build_object(
        'status', 'healthy',
        'timestamp', CURRENT_TIMESTAMP,
        'database_name', current_database(),
        'tables_count', table_count,
        'indexes_count', index_count,
        'database_size_mb', db_size_mb,
        'active_connections', active_connections,
        'modules', module_status,
        'version', (SELECT schema_version FROM database_metadata LIMIT 1)
    );
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Function to get comprehensive system statistics
CREATE OR REPLACE FUNCTION get_system_statistics()
RETURNS JSONB AS $$
DECLARE
    stats JSONB := '{}';
    base_stats JSONB;
    project_stats JSONB;
    task_stats JSONB;
    event_stats JSONB;
    prompt_stats JSONB;
    analytics_stats JSONB;
    openevolve_stats JSONB;
BEGIN
    -- Base statistics
    SELECT jsonb_build_object(
        'total_organizations', COUNT(*),
        'active_organizations', COUNT(*) FILTER (WHERE status = 'active'),
        'total_users', (SELECT COUNT(*) FROM users WHERE deleted_at IS NULL),
        'active_users', (SELECT COUNT(*) FROM users WHERE status = 'active' AND deleted_at IS NULL)
    ) INTO base_stats
    FROM organizations WHERE deleted_at IS NULL;
    
    -- Project statistics (if projects table exists)
    IF EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'projects') THEN
        EXECUTE 'SELECT jsonb_build_object(
            ''total_projects'', COUNT(*),
            ''active_projects'', COUNT(*) FILTER (WHERE status = ''active''),
            ''total_repositories'', (SELECT COUNT(*) FROM repositories WHERE deleted_at IS NULL)
        ) FROM projects WHERE deleted_at IS NULL' INTO project_stats;
    ELSE
        project_stats := '{"status": "not_initialized"}';
    END IF;
    
    -- Task statistics (if tasks table exists)
    IF EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'tasks') THEN
        EXECUTE 'SELECT jsonb_build_object(
            ''total_tasks'', COUNT(*),
            ''active_tasks'', COUNT(*) FILTER (WHERE status IN (''pending'', ''in_progress'', ''assigned'')),
            ''completed_tasks'', COUNT(*) FILTER (WHERE status = ''completed''),
            ''failed_tasks'', COUNT(*) FILTER (WHERE status = ''failed'')
        ) FROM tasks' INTO task_stats;
    ELSE
        task_stats := '{"status": "not_initialized"}';
    END IF;
    
    -- Event statistics (if events table exists)
    IF EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'events') THEN
        EXECUTE 'SELECT jsonb_build_object(
            ''total_events'', COUNT(*),
            ''events_today'', COUNT(*) FILTER (WHERE occurred_at >= CURRENT_DATE),
            ''events_this_week'', COUNT(*) FILTER (WHERE occurred_at >= CURRENT_DATE - INTERVAL ''7 days'')
        ) FROM events' INTO event_stats;
    ELSE
        event_stats := '{"status": "not_initialized"}';
    END IF;
    
    -- Prompt statistics (if prompts table exists)
    IF EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'prompt_templates') THEN
        EXECUTE 'SELECT jsonb_build_object(
            ''total_prompts'', COUNT(*),
            ''active_prompts'', COUNT(*) FILTER (WHERE is_active = true),
            ''total_executions'', COALESCE(SUM(usage_count), 0)
        ) FROM prompt_templates' INTO prompt_stats;
    ELSE
        prompt_stats := '{"status": "not_initialized"}';
    END IF;
    
    -- Analytics statistics (if analysis_runs table exists)
    IF EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'analysis_runs') THEN
        EXECUTE 'SELECT jsonb_build_object(
            ''total_analysis_runs'', COUNT(*),
            ''completed_analyses'', COUNT(*) FILTER (WHERE status = ''completed''),
            ''average_quality_score'', AVG(quality_score)
        ) FROM analysis_runs' INTO analytics_stats;
    ELSE
        analytics_stats := '{"status": "not_initialized"}';
    END IF;
    
    -- OpenEvolve statistics (if evaluations table exists)
    IF EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'evaluations') THEN
        EXECUTE 'SELECT jsonb_build_object(
            ''total_evaluations'', COUNT(*),
            ''successful_evaluations'', COUNT(*) FILTER (WHERE status = ''completed''),
            ''average_effectiveness_score'', AVG(effectiveness_score)
        ) FROM evaluations' INTO openevolve_stats;
    ELSE
        openevolve_stats := '{"status": "not_initialized"}';
    END IF;
    
    -- Combine all statistics
    stats := jsonb_build_object(
        'generated_at', CURRENT_TIMESTAMP,
        'base', base_stats,
        'projects', project_stats,
        'tasks', task_stats,
        'events', event_stats,
        'prompts', prompt_stats,
        'analytics', analytics_stats,
        'openevolve', openevolve_stats
    );
    
    RETURN stats;
END;
$$ LANGUAGE plpgsql;

-- Function for comprehensive database maintenance
CREATE OR REPLACE FUNCTION perform_maintenance()
RETURNS JSONB AS $$
DECLARE
    result JSONB := '{}';
    cleanup_results JSONB := '{}';
    maintenance_actions TEXT[] := '{}';
BEGIN
    -- Vacuum and analyze
    VACUUM ANALYZE;
    maintenance_actions := array_append(maintenance_actions, 'vacuum_analyze');
    
    -- Update statistics
    ANALYZE;
    maintenance_actions := array_append(maintenance_actions, 'update_statistics');
    
    -- Clean up old audit logs (older than 1 year)
    IF EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'audit_log') THEN
        EXECUTE 'DELETE FROM audit_log WHERE occurred_at < CURRENT_TIMESTAMP - INTERVAL ''1 year''';
        maintenance_actions := array_append(maintenance_actions, 'cleanup_audit_logs');
    END IF;
    
    -- Clean up old performance metrics (older than 90 days)
    IF EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'performance_metrics') THEN
        EXECUTE 'DELETE FROM performance_metrics WHERE measured_at < CURRENT_TIMESTAMP - INTERVAL ''90 days''';
        maintenance_actions := array_append(maintenance_actions, 'cleanup_performance_metrics');
    END IF;
    
    -- Clean up old events (based on retention policy)
    IF EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'events') THEN
        EXECUTE 'DELETE FROM events WHERE occurred_at < CURRENT_TIMESTAMP - INTERVAL ''1 year'' AND status = ''processed''';
        maintenance_actions := array_append(maintenance_actions, 'cleanup_old_events');
    END IF;
    
    -- Update database metadata
    UPDATE database_metadata SET
        last_migration_at = CURRENT_TIMESTAMP,
        updated_at = CURRENT_TIMESTAMP,
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
    maintenance_actions := array_append(maintenance_actions, 'update_metadata');
    
    result := jsonb_build_object(
        'status', 'completed',
        'timestamp', CURRENT_TIMESTAMP,
        'actions_performed', maintenance_actions,
        'database_size_mb', (SELECT database_size_mb FROM database_metadata LIMIT 1),
        'total_tables', (SELECT total_tables FROM database_metadata LIMIT 1),
        'total_indexes', (SELECT total_indexes FROM database_metadata LIMIT 1)
    );
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- MATERIALIZED VIEWS FOR ANALYTICS
-- =============================================================================

-- Create materialized views for performance (will be populated after module initialization)
CREATE MATERIALIZED VIEW IF NOT EXISTS daily_system_summary AS
SELECT 
    CURRENT_DATE as date,
    0 as total_tasks,
    0 as completed_tasks,
    0 as failed_tasks,
    0 as total_events,
    0 as total_analyses,
    0.0 as avg_quality_score
WHERE false; -- Empty initially

-- Create unique index for concurrent refresh
CREATE UNIQUE INDEX IF NOT EXISTS idx_daily_system_summary_date 
ON daily_system_summary (date);

-- Function to refresh all materialized views
CREATE OR REPLACE FUNCTION refresh_analytics_views()
RETURNS VOID AS $$
BEGIN
    -- Only refresh if tables exist
    IF EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'tasks') THEN
        REFRESH MATERIALIZED VIEW CONCURRENTLY daily_system_summary;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- NOTIFICATION SYSTEM
-- =============================================================================

-- Create notification functions for real-time updates
CREATE OR REPLACE FUNCTION notify_system_change()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM pg_notify(
        'system_changes',
        jsonb_build_object(
            'operation', TG_OP,
            'table', TG_TABLE_NAME,
            'record_id', COALESCE(NEW.id, OLD.id),
            'timestamp', CURRENT_TIMESTAMP
        )::TEXT
    );
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- ROLE-BASED ACCESS CONTROL
-- =============================================================================

-- Create roles for different access levels
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'system_readonly') THEN
        CREATE ROLE system_readonly;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'system_readwrite') THEN
        CREATE ROLE system_readwrite;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'system_admin') THEN
        CREATE ROLE system_admin;
    END IF;
END $$;

-- Grant permissions (will be extended as modules are added)
GRANT SELECT ON ALL TABLES IN SCHEMA public TO system_readonly;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO system_readwrite;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO system_admin;

-- Grant sequence permissions
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO system_readwrite;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO system_admin;

-- =============================================================================
-- SCHEDULED MAINTENANCE FUNCTION
-- =============================================================================

-- Create scheduled job function (to be called by external scheduler)
CREATE OR REPLACE FUNCTION scheduled_maintenance()
RETURNS JSONB AS $$
DECLARE
    maintenance_result JSONB;
    health_check_result JSONB;
BEGIN
    -- Perform maintenance
    SELECT perform_maintenance() INTO maintenance_result;
    
    -- Refresh analytics views
    PERFORM refresh_analytics_views();
    
    -- Run health check
    SELECT database_health_check() INTO health_check_result;
    
    -- Log performance metrics
    INSERT INTO performance_metrics (metric_name, metric_type, value, unit, context)
    VALUES 
        ('database_size_mb', 'system', pg_database_size(current_database()) / 1024 / 1024, 'MB', '{}'),
        ('active_connections', 'system', (SELECT COUNT(*) FROM pg_stat_activity WHERE state = 'active'), 'count', '{}'),
        ('total_tables', 'system', (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'), 'count', '{}');
    
    RETURN jsonb_build_object(
        'maintenance', maintenance_result,
        'health_check', health_check_result,
        'analytics_refreshed', true,
        'metrics_logged', true,
        'timestamp', CURRENT_TIMESTAMP
    );
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- INITIALIZATION LOG
-- =============================================================================

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
        'modules_initialized', ARRAY['base'],
        'features_enabled', ARRAY[
            'comprehensive_database_init',
            'health_monitoring',
            'performance_tracking',
            'automated_maintenance'
        ]
    ),
    NULL,
    'system',
    jsonb_build_object(
        'initialization_type', 'comprehensive',
        'database_name', current_database(),
        'timestamp', CURRENT_TIMESTAMP,
        'script_version', '1.0.0'
    )
);

-- =============================================================================
-- COMMENTS FOR DOCUMENTATION
-- =============================================================================

COMMENT ON TABLE database_metadata IS 'Database schema version and configuration metadata';
COMMENT ON FUNCTION database_health_check IS 'Comprehensive database health check with module status';
COMMENT ON FUNCTION get_system_statistics IS 'Get current system statistics across all modules';
COMMENT ON FUNCTION perform_maintenance IS 'Perform routine database maintenance tasks';
COMMENT ON FUNCTION refresh_analytics_views IS 'Refresh materialized views for analytics';
COMMENT ON FUNCTION scheduled_maintenance IS 'Scheduled maintenance job function';
COMMENT ON FUNCTION notify_system_change IS 'Notification function for real-time system updates';

-- =============================================================================
-- FINAL STATUS MESSAGE
-- =============================================================================

DO $$
BEGIN
    RAISE NOTICE '=============================================================================';
    RAISE NOTICE 'COMPREHENSIVE TASK MANAGEMENT SYSTEM DATABASE INITIALIZED SUCCESSFULLY!';
    RAISE NOTICE '=============================================================================';
    RAISE NOTICE 'Schema version: 1.0.0';
    RAISE NOTICE 'Base module: INITIALIZED';
    RAISE NOTICE 'Ready for module installation: Projects, Tasks, Analytics, Prompts, Events, OpenEvolve';
    RAISE NOTICE 'Features: Health Monitoring, Performance Tracking, Automated Maintenance';
    RAISE NOTICE 'Database: %', current_database();
    RAISE NOTICE 'Timestamp: %', CURRENT_TIMESTAMP;
    RAISE NOTICE '=============================================================================';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '1. Load base schema: psql -f database/schemas/00_base_schema.sql';
    RAISE NOTICE '2. Load module schemas: psql -f database/schemas/01_projects_module.sql (etc.)';
    RAISE NOTICE '3. Verify installation: SELECT * FROM database_health_check();';
    RAISE NOTICE '=============================================================================';
END $$;

