-- =============================================================================
-- DATABASE HEALTH MONITORING QUERIES
-- =============================================================================
-- This file contains comprehensive health check queries for monitoring
-- database performance, data quality, and system health across all modules.
-- =============================================================================

-- =============================================================================
-- SYSTEM HEALTH CHECKS
-- =============================================================================

-- Overall database health summary
CREATE OR REPLACE VIEW database_health_summary AS
SELECT 
    'database_health' as check_type,
    CASE 
        WHEN active_connections < 80 AND database_size_gb < 100 AND avg_query_time_ms < 1000 THEN 'healthy'
        WHEN active_connections < 150 AND database_size_gb < 200 AND avg_query_time_ms < 2000 THEN 'warning'
        ELSE 'critical'
    END as status,
    jsonb_build_object(
        'active_connections', active_connections,
        'max_connections', max_connections,
        'database_size_gb', database_size_gb,
        'avg_query_time_ms', avg_query_time_ms,
        'slow_queries_count', slow_queries_count,
        'deadlocks_count', deadlocks_count,
        'cache_hit_ratio', cache_hit_ratio
    ) as metrics,
    CURRENT_TIMESTAMP as checked_at
FROM (
    SELECT 
        (SELECT count(*) FROM pg_stat_activity WHERE state = 'active') as active_connections,
        (SELECT setting::int FROM pg_settings WHERE name = 'max_connections') as max_connections,
        ROUND((pg_database_size(current_database()) / 1024.0 / 1024.0 / 1024.0)::numeric, 2) as database_size_gb,
        COALESCE((SELECT ROUND(AVG(mean_exec_time)::numeric, 2) FROM pg_stat_statements WHERE calls > 10), 0) as avg_query_time_ms,
        COALESCE((SELECT count(*) FROM pg_stat_statements WHERE mean_exec_time > 1000), 0) as slow_queries_count,
        COALESCE((SELECT deadlocks FROM pg_stat_database WHERE datname = current_database()), 0) as deadlocks_count,
        ROUND((
            SELECT 
                CASE 
                    WHEN blks_hit + blks_read = 0 THEN 0
                    ELSE (blks_hit::float / (blks_hit + blks_read) * 100)
                END
            FROM pg_stat_database 
            WHERE datname = current_database()
        )::numeric, 2) as cache_hit_ratio
) as health_metrics;

-- Table size and growth monitoring
CREATE OR REPLACE VIEW table_size_monitoring AS
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) as index_size,
    ROUND((pg_total_relation_size(schemaname||'.'||tablename) / 1024.0 / 1024.0)::numeric, 2) as total_size_mb,
    (SELECT reltuples::bigint FROM pg_class WHERE relname = tablename) as estimated_rows
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Index usage and performance
CREATE OR REPLACE VIEW index_performance AS
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
    CASE 
        WHEN idx_scan = 0 THEN 'unused'
        WHEN idx_scan < 100 THEN 'low_usage'
        WHEN idx_scan < 1000 THEN 'medium_usage'
        ELSE 'high_usage'
    END as usage_category
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- =============================================================================
-- DATA QUALITY CHECKS
-- =============================================================================

-- Data integrity checks across all modules
CREATE OR REPLACE VIEW data_integrity_checks AS
SELECT 
    check_name,
    CASE WHEN issue_count = 0 THEN 'pass' ELSE 'fail' END as status,
    issue_count,
    description,
    CURRENT_TIMESTAMP as checked_at
FROM (
    -- Check for orphaned records
    SELECT 
        'orphaned_tasks' as check_name,
        COUNT(*) as issue_count,
        'Tasks without valid project or repository references' as description
    FROM tasks t
    LEFT JOIN projects p ON t.project_id = p.id
    LEFT JOIN repositories r ON t.repository_id = r.id
    WHERE (t.project_id IS NOT NULL AND p.id IS NULL)
       OR (t.repository_id IS NOT NULL AND r.id IS NULL)
    
    UNION ALL
    
    SELECT 
        'orphaned_events' as check_name,
        COUNT(*) as issue_count,
        'Events without valid organization references' as description
    FROM events e
    LEFT JOIN organizations o ON e.organization_id = o.id
    WHERE o.id IS NULL
    
    UNION ALL
    
    SELECT 
        'invalid_task_dependencies' as check_name,
        COUNT(*) as issue_count,
        'Task dependencies with circular references' as description
    FROM task_dependencies td1
    WHERE EXISTS (
        SELECT 1 FROM task_dependencies td2
        WHERE td1.dependent_task_id = td2.prerequisite_task_id
        AND td1.prerequisite_task_id = td2.dependent_task_id
    )
    
    UNION ALL
    
    SELECT 
        'missing_required_fields' as check_name,
        COUNT(*) as issue_count,
        'Records with missing required fields' as description
    FROM (
        SELECT id FROM organizations WHERE name IS NULL OR slug IS NULL
        UNION ALL
        SELECT id FROM users WHERE email IS NULL OR organization_id IS NULL
        UNION ALL
        SELECT id FROM projects WHERE name IS NULL OR organization_id IS NULL
        UNION ALL
        SELECT id FROM repositories WHERE name IS NULL OR organization_id IS NULL
    ) missing_fields
    
    UNION ALL
    
    SELECT 
        'duplicate_slugs' as check_name,
        COUNT(*) - COUNT(DISTINCT slug) as issue_count,
        'Duplicate slugs within organizations' as description
    FROM projects
    WHERE deleted_at IS NULL
) integrity_checks;

-- Data volume and growth trends
CREATE OR REPLACE VIEW data_volume_trends AS
SELECT 
    table_name,
    current_count,
    last_24h_count,
    last_7d_count,
    last_30d_count,
    CASE 
        WHEN last_24h_count > current_count * 0.1 THEN 'high_growth'
        WHEN last_24h_count > current_count * 0.05 THEN 'medium_growth'
        WHEN last_24h_count > 0 THEN 'low_growth'
        ELSE 'no_growth'
    END as growth_rate,
    CURRENT_TIMESTAMP as checked_at
FROM (
    SELECT 
        'organizations' as table_name,
        COUNT(*) as current_count,
        COUNT(CASE WHEN created_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours' THEN 1 END) as last_24h_count,
        COUNT(CASE WHEN created_at >= CURRENT_TIMESTAMP - INTERVAL '7 days' THEN 1 END) as last_7d_count,
        COUNT(CASE WHEN created_at >= CURRENT_TIMESTAMP - INTERVAL '30 days' THEN 1 END) as last_30d_count
    FROM organizations WHERE deleted_at IS NULL
    
    UNION ALL
    
    SELECT 
        'projects' as table_name,
        COUNT(*) as current_count,
        COUNT(CASE WHEN created_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours' THEN 1 END) as last_24h_count,
        COUNT(CASE WHEN created_at >= CURRENT_TIMESTAMP - INTERVAL '7 days' THEN 1 END) as last_7d_count,
        COUNT(CASE WHEN created_at >= CURRENT_TIMESTAMP - INTERVAL '30 days' THEN 1 END) as last_30d_count
    FROM projects WHERE deleted_at IS NULL
    
    UNION ALL
    
    SELECT 
        'tasks' as table_name,
        COUNT(*) as current_count,
        COUNT(CASE WHEN created_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours' THEN 1 END) as last_24h_count,
        COUNT(CASE WHEN created_at >= CURRENT_TIMESTAMP - INTERVAL '7 days' THEN 1 END) as last_7d_count,
        COUNT(CASE WHEN created_at >= CURRENT_TIMESTAMP - INTERVAL '30 days' THEN 1 END) as last_30d_count
    FROM tasks WHERE deleted_at IS NULL
    
    UNION ALL
    
    SELECT 
        'events' as table_name,
        COUNT(*) as current_count,
        COUNT(CASE WHEN created_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours' THEN 1 END) as last_24h_count,
        COUNT(CASE WHEN created_at >= CURRENT_TIMESTAMP - INTERVAL '7 days' THEN 1 END) as last_7d_count,
        COUNT(CASE WHEN created_at >= CURRENT_TIMESTAMP - INTERVAL '30 days' THEN 1 END) as last_30d_count
    FROM events
    
    UNION ALL
    
    SELECT 
        'prompt_executions' as table_name,
        COUNT(*) as current_count,
        COUNT(CASE WHEN created_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours' THEN 1 END) as last_24h_count,
        COUNT(CASE WHEN created_at >= CURRENT_TIMESTAMP - INTERVAL '7 days' THEN 1 END) as last_7d_count,
        COUNT(CASE WHEN created_at >= CURRENT_TIMESTAMP - INTERVAL '30 days' THEN 1 END) as last_30d_count
    FROM prompt_executions
    
    UNION ALL
    
    SELECT 
        'analysis_runs' as table_name,
        COUNT(*) as current_count,
        COUNT(CASE WHEN created_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours' THEN 1 END) as last_24h_count,
        COUNT(CASE WHEN created_at >= CURRENT_TIMESTAMP - INTERVAL '7 days' THEN 1 END) as last_7d_count,
        COUNT(CASE WHEN created_at >= CURRENT_TIMESTAMP - INTERVAL '30 days' THEN 1 END) as last_30d_count
    FROM analysis_runs WHERE deleted_at IS NULL
) volume_data;

-- =============================================================================
-- PERFORMANCE MONITORING
-- =============================================================================

-- Query performance monitoring
CREATE OR REPLACE VIEW query_performance AS
SELECT 
    query,
    calls,
    total_exec_time,
    mean_exec_time,
    stddev_exec_time,
    min_exec_time,
    max_exec_time,
    rows,
    100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent,
    CASE 
        WHEN mean_exec_time > 5000 THEN 'critical'
        WHEN mean_exec_time > 1000 THEN 'warning'
        ELSE 'normal'
    END as performance_status
FROM pg_stat_statements
WHERE calls > 10
ORDER BY mean_exec_time DESC
LIMIT 20;

-- Lock monitoring
CREATE OR REPLACE VIEW lock_monitoring AS
SELECT 
    pg_stat_activity.pid,
    pg_stat_activity.usename,
    pg_stat_activity.query,
    pg_stat_activity.state,
    pg_locks.locktype,
    pg_locks.mode,
    pg_locks.granted,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - pg_stat_activity.query_start)) as duration_seconds
FROM pg_stat_activity
JOIN pg_locks ON pg_stat_activity.pid = pg_locks.pid
WHERE pg_stat_activity.state != 'idle'
AND pg_locks.granted = false
ORDER BY duration_seconds DESC;

-- Connection monitoring
CREATE OR REPLACE VIEW connection_monitoring AS
SELECT 
    state,
    COUNT(*) as connection_count,
    AVG(EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - state_change))) as avg_duration_seconds,
    MAX(EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - state_change))) as max_duration_seconds
FROM pg_stat_activity
WHERE state IS NOT NULL
GROUP BY state
ORDER BY connection_count DESC;

-- =============================================================================
-- MODULE-SPECIFIC HEALTH CHECKS
-- =============================================================================

-- Tasks module health
CREATE OR REPLACE VIEW tasks_module_health AS
SELECT 
    'tasks_module' as module_name,
    jsonb_build_object(
        'total_tasks', total_tasks,
        'pending_tasks', pending_tasks,
        'running_tasks', running_tasks,
        'failed_tasks', failed_tasks,
        'avg_execution_time_minutes', avg_execution_time_minutes,
        'tasks_last_24h', tasks_last_24h,
        'success_rate_percent', success_rate_percent
    ) as metrics,
    CASE 
        WHEN pending_tasks > 1000 OR failed_tasks > total_tasks * 0.1 THEN 'warning'
        WHEN pending_tasks > 100 OR failed_tasks > total_tasks * 0.05 THEN 'attention'
        ELSE 'healthy'
    END as status,
    CURRENT_TIMESTAMP as checked_at
FROM (
    SELECT 
        COUNT(*) as total_tasks,
        COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_tasks,
        COUNT(CASE WHEN status = 'running' THEN 1 END) as running_tasks,
        COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_tasks,
        COUNT(CASE WHEN created_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours' THEN 1 END) as tasks_last_24h,
        ROUND(AVG(EXTRACT(EPOCH FROM (completed_at - started_at)) / 60.0)::numeric, 2) as avg_execution_time_minutes,
        ROUND((COUNT(CASE WHEN status = 'completed' THEN 1 END)::float / NULLIF(COUNT(*), 0) * 100)::numeric, 2) as success_rate_percent
    FROM tasks
    WHERE deleted_at IS NULL
) task_metrics;

-- Events module health
CREATE OR REPLACE VIEW events_module_health AS
SELECT 
    'events_module' as module_name,
    jsonb_build_object(
        'total_events', total_events,
        'pending_events', pending_events,
        'failed_events', failed_events,
        'events_last_24h', events_last_24h,
        'avg_processing_time_seconds', avg_processing_time_seconds,
        'processing_success_rate', processing_success_rate,
        'events_by_source', events_by_source
    ) as metrics,
    CASE 
        WHEN pending_events > 10000 OR failed_events > total_events * 0.05 THEN 'warning'
        WHEN pending_events > 1000 OR failed_events > total_events * 0.02 THEN 'attention'
        ELSE 'healthy'
    END as status,
    CURRENT_TIMESTAMP as checked_at
FROM (
    SELECT 
        COUNT(*) as total_events,
        COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_events,
        COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_events,
        COUNT(CASE WHEN created_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours' THEN 1 END) as events_last_24h,
        ROUND(AVG(EXTRACT(EPOCH FROM (processed_at - received_at)))::numeric, 2) as avg_processing_time_seconds,
        ROUND((COUNT(CASE WHEN status = 'processed' THEN 1 END)::float / NULLIF(COUNT(*), 0) * 100)::numeric, 2) as processing_success_rate,
        jsonb_object_agg(source, source_count) as events_by_source
    FROM events e
    LEFT JOIN (
        SELECT source, COUNT(*) as source_count
        FROM events
        WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
        GROUP BY source
    ) source_stats ON true
    GROUP BY source_stats.source, source_stats.source_count
) event_metrics;

-- Analytics module health
CREATE OR REPLACE VIEW analytics_module_health AS
SELECT 
    'analytics_module' as module_name,
    jsonb_build_object(
        'total_analysis_runs', total_analysis_runs,
        'completed_runs', completed_runs,
        'failed_runs', failed_runs,
        'runs_last_24h', runs_last_24h,
        'avg_analysis_time_minutes', avg_analysis_time_minutes,
        'total_files_analyzed', total_files_analyzed,
        'total_issues_found', total_issues_found
    ) as metrics,
    CASE 
        WHEN failed_runs > total_analysis_runs * 0.1 THEN 'warning'
        WHEN failed_runs > total_analysis_runs * 0.05 THEN 'attention'
        ELSE 'healthy'
    END as status,
    CURRENT_TIMESTAMP as checked_at
FROM (
    SELECT 
        COUNT(*) as total_analysis_runs,
        COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_runs,
        COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_runs,
        COUNT(CASE WHEN created_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours' THEN 1 END) as runs_last_24h,
        ROUND(AVG(duration_seconds / 60.0)::numeric, 2) as avg_analysis_time_minutes,
        SUM(total_files_analyzed) as total_files_analyzed,
        SUM(total_issues_found) as total_issues_found
    FROM analysis_runs
    WHERE deleted_at IS NULL
) analysis_metrics;

-- =============================================================================
-- ALERTING QUERIES
-- =============================================================================

-- Critical issues that need immediate attention
CREATE OR REPLACE VIEW critical_alerts AS
SELECT 
    alert_type,
    severity,
    message,
    details,
    CURRENT_TIMESTAMP as detected_at
FROM (
    -- High number of failed tasks
    SELECT 
        'high_task_failure_rate' as alert_type,
        'critical' as severity,
        'High task failure rate detected' as message,
        jsonb_build_object('failed_tasks', failed_count, 'total_tasks', total_count, 'failure_rate', failure_rate) as details
    FROM (
        SELECT 
            COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_count,
            COUNT(*) as total_count,
            ROUND((COUNT(CASE WHEN status = 'failed' THEN 1 END)::float / NULLIF(COUNT(*), 0) * 100)::numeric, 2) as failure_rate
        FROM tasks
        WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '1 hour'
        AND deleted_at IS NULL
    ) task_failures
    WHERE failure_rate > 20 AND total_count > 10
    
    UNION ALL
    
    -- Database connection issues
    SELECT 
        'high_connection_usage' as alert_type,
        'warning' as severity,
        'High database connection usage' as message,
        jsonb_build_object('active_connections', active_connections, 'max_connections', max_connections, 'usage_percent', usage_percent) as details
    FROM (
        SELECT 
            (SELECT count(*) FROM pg_stat_activity WHERE state = 'active') as active_connections,
            (SELECT setting::int FROM pg_settings WHERE name = 'max_connections') as max_connections,
            ROUND(((SELECT count(*) FROM pg_stat_activity WHERE state = 'active')::float / (SELECT setting::int FROM pg_settings WHERE name = 'max_connections') * 100)::numeric, 2) as usage_percent
    ) connection_usage
    WHERE usage_percent > 80
    
    UNION ALL
    
    -- Slow query detection
    SELECT 
        'slow_queries_detected' as alert_type,
        'warning' as severity,
        'Slow queries detected' as message,
        jsonb_build_object('slow_query_count', slow_query_count, 'avg_execution_time', avg_execution_time) as details
    FROM (
        SELECT 
            COUNT(*) as slow_query_count,
            ROUND(AVG(mean_exec_time)::numeric, 2) as avg_execution_time
        FROM pg_stat_statements
        WHERE mean_exec_time > 5000
        AND calls > 5
    ) slow_queries
    WHERE slow_query_count > 5
    
    UNION ALL
    
    -- Event processing backlog
    SELECT 
        'event_processing_backlog' as alert_type,
        'warning' as severity,
        'Event processing backlog detected' as message,
        jsonb_build_object('pending_events', pending_count, 'oldest_pending_hours', oldest_pending_hours) as details
    FROM (
        SELECT 
            COUNT(*) as pending_count,
            ROUND(EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - MIN(received_at))) / 3600.0, 2) as oldest_pending_hours
        FROM events
        WHERE status = 'pending'
    ) event_backlog
    WHERE pending_count > 1000 OR oldest_pending_hours > 24
) alerts;

-- =============================================================================
-- MAINTENANCE RECOMMENDATIONS
-- =============================================================================

-- Maintenance recommendations based on current state
CREATE OR REPLACE VIEW maintenance_recommendations AS
SELECT 
    recommendation_type,
    priority,
    description,
    action_required,
    estimated_impact,
    CURRENT_TIMESTAMP as generated_at
FROM (
    -- Unused index recommendations
    SELECT 
        'remove_unused_indexes' as recommendation_type,
        'medium' as priority,
        'Remove unused indexes to improve write performance' as description,
        'DROP INDEX ' || string_agg(indexname, ', DROP INDEX ') as action_required,
        'Improved write performance, reduced storage' as estimated_impact
    FROM pg_stat_user_indexes
    WHERE idx_scan = 0
    AND schemaname = 'public'
    GROUP BY recommendation_type, priority, description, estimated_impact
    HAVING COUNT(*) > 0
    
    UNION ALL
    
    -- Table maintenance recommendations
    SELECT 
        'vacuum_analyze_tables' as recommendation_type,
        'high' as priority,
        'Tables need VACUUM ANALYZE for optimal performance' as description,
        'VACUUM ANALYZE ' || string_agg(schemaname || '.' || tablename, ', ') as action_required,
        'Improved query performance, updated statistics' as estimated_impact
    FROM pg_stat_user_tables
    WHERE (n_dead_tup > n_live_tup * 0.1 OR analyze_count = 0)
    AND schemaname = 'public'
    GROUP BY recommendation_type, priority, description, estimated_impact
    HAVING COUNT(*) > 0
    
    UNION ALL
    
    -- Data cleanup recommendations
    SELECT 
        'cleanup_old_events' as recommendation_type,
        'medium' as priority,
        'Clean up old events to reduce storage usage' as description,
        'Run cleanup_old_events() function' as action_required,
        'Reduced storage usage, improved performance' as estimated_impact
    FROM (
        SELECT COUNT(*) as old_events_count
        FROM events
        WHERE occurred_at < CURRENT_TIMESTAMP - INTERVAL '90 days'
    ) old_events
    WHERE old_events_count > 10000
) recommendations;

COMMENT ON VIEW database_health_summary IS 'Overall database health status and key metrics';
COMMENT ON VIEW table_size_monitoring IS 'Monitor table sizes and growth patterns';
COMMENT ON VIEW data_integrity_checks IS 'Automated data integrity validation across all modules';
COMMENT ON VIEW critical_alerts IS 'Critical issues requiring immediate attention';
COMMENT ON VIEW maintenance_recommendations IS 'Automated maintenance recommendations based on current database state';

