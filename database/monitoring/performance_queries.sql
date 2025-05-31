-- =============================================================================
-- PERFORMANCE OPTIMIZATION QUERIES
-- =============================================================================
-- This file contains queries for performance monitoring, optimization,
-- and troubleshooting across all database modules.
-- =============================================================================

-- =============================================================================
-- QUERY PERFORMANCE ANALYSIS
-- =============================================================================

-- Top slow queries with detailed analysis
CREATE OR REPLACE VIEW slow_query_analysis AS
SELECT 
    query,
    calls,
    total_exec_time,
    mean_exec_time,
    stddev_exec_time,
    min_exec_time,
    max_exec_time,
    rows,
    100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS cache_hit_ratio,
    shared_blks_read,
    shared_blks_written,
    temp_blks_read,
    temp_blks_written,
    CASE 
        WHEN mean_exec_time > 10000 THEN 'critical'
        WHEN mean_exec_time > 5000 THEN 'high'
        WHEN mean_exec_time > 1000 THEN 'medium'
        ELSE 'low'
    END as priority,
    -- Performance recommendations
    CASE 
        WHEN 100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) < 95 THEN 'Consider adding indexes or increasing shared_buffers'
        WHEN temp_blks_read > 0 THEN 'Query uses temporary files - consider increasing work_mem'
        WHEN stddev_exec_time > mean_exec_time THEN 'High execution time variance - investigate query plan stability'
        ELSE 'Query performance is acceptable'
    END as recommendation
FROM pg_stat_statements
WHERE calls > 5
ORDER BY mean_exec_time DESC
LIMIT 50;

-- Index usage effectiveness
CREATE OR REPLACE VIEW index_usage_analysis AS
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
    pg_relation_size(indexrelid) as index_size_bytes,
    -- Calculate index efficiency
    CASE 
        WHEN idx_scan = 0 THEN 'unused'
        WHEN idx_tup_read = 0 THEN 'no_reads'
        WHEN idx_tup_fetch::float / idx_tup_read < 0.1 THEN 'low_selectivity'
        WHEN idx_scan < 100 THEN 'low_usage'
        ELSE 'good_usage'
    END as usage_status,
    -- Cost-benefit analysis
    CASE 
        WHEN idx_scan = 0 AND pg_relation_size(indexrelid) > 1024*1024 THEN 'consider_dropping'
        WHEN idx_scan > 1000 AND idx_tup_fetch::float / idx_tup_read > 0.5 THEN 'high_value'
        WHEN idx_scan > 100 THEN 'moderate_value'
        ELSE 'low_value'
    END as value_assessment,
    -- Maintenance recommendations
    CASE 
        WHEN idx_scan = 0 THEN 'DROP INDEX ' || indexname
        WHEN idx_tup_read > 0 AND idx_tup_fetch::float / idx_tup_read < 0.01 THEN 'Review index selectivity'
        ELSE 'No action needed'
    END as recommendation
FROM pg_stat_user_indexes
ORDER BY pg_relation_size(indexrelid) DESC;

-- Table access patterns and optimization opportunities
CREATE OR REPLACE VIEW table_access_patterns AS
SELECT 
    schemaname,
    relname as tablename,
    seq_scan,
    seq_tup_read,
    idx_scan,
    idx_tup_fetch,
    n_tup_ins,
    n_tup_upd,
    n_tup_del,
    n_live_tup,
    n_dead_tup,
    pg_size_pretty(pg_total_relation_size(relid)) as total_size,
    pg_size_pretty(pg_relation_size(relid)) as table_size,
    -- Calculate ratios for analysis
    CASE 
        WHEN seq_scan + idx_scan = 0 THEN 0
        ELSE ROUND((seq_scan::float / (seq_scan + idx_scan) * 100)::numeric, 2)
    END as seq_scan_ratio,
    CASE 
        WHEN n_live_tup = 0 THEN 0
        ELSE ROUND((n_dead_tup::float / n_live_tup * 100)::numeric, 2)
    END as dead_tuple_ratio,
    -- Performance recommendations
    CASE 
        WHEN seq_scan > idx_scan * 2 AND seq_tup_read > 10000 THEN 'Consider adding indexes for frequent sequential scans'
        WHEN n_dead_tup > n_live_tup * 0.2 THEN 'Table needs VACUUM - high dead tuple ratio'
        WHEN pg_relation_size(relid) > 100*1024*1024 AND idx_scan = 0 THEN 'Large table with no index usage - review query patterns'
        ELSE 'Access pattern is acceptable'
    END as recommendation,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables
ORDER BY pg_total_relation_size(relid) DESC;

-- =============================================================================
-- MODULE-SPECIFIC PERFORMANCE QUERIES
-- =============================================================================

-- Tasks module performance analysis
CREATE OR REPLACE VIEW tasks_performance_analysis AS
SELECT 
    'tasks_performance' as analysis_type,
    jsonb_build_object(
        'avg_task_duration_minutes', avg_duration_minutes,
        'median_task_duration_minutes', median_duration_minutes,
        'p95_task_duration_minutes', p95_duration_minutes,
        'tasks_per_hour_last_24h', tasks_per_hour,
        'completion_rate_percent', completion_rate,
        'retry_rate_percent', retry_rate,
        'bottleneck_analysis', bottleneck_analysis
    ) as metrics,
    CURRENT_TIMESTAMP as analyzed_at
FROM (
    SELECT 
        ROUND(AVG(EXTRACT(EPOCH FROM (completed_at - started_at)) / 60.0)::numeric, 2) as avg_duration_minutes,
        ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (completed_at - started_at)) / 60.0)::numeric, 2) as median_duration_minutes,
        ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (completed_at - started_at)) / 60.0)::numeric, 2) as p95_duration_minutes,
        ROUND((COUNT(CASE WHEN created_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours' THEN 1 END)::float / 24)::numeric, 2) as tasks_per_hour,
        ROUND((COUNT(CASE WHEN status = 'completed' THEN 1 END)::float / NULLIF(COUNT(*), 0) * 100)::numeric, 2) as completion_rate,
        ROUND((COUNT(CASE WHEN retry_count > 0 THEN 1 END)::float / NULLIF(COUNT(*), 0) * 100)::numeric, 2) as retry_rate,
        jsonb_build_object(
            'most_common_task_type', (
                SELECT task_type 
                FROM tasks 
                WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '7 days'
                GROUP BY task_type 
                ORDER BY COUNT(*) DESC 
                LIMIT 1
            ),
            'slowest_task_type', (
                SELECT task_type
                FROM tasks
                WHERE completed_at IS NOT NULL AND started_at IS NOT NULL
                GROUP BY task_type
                ORDER BY AVG(EXTRACT(EPOCH FROM (completed_at - started_at))) DESC
                LIMIT 1
            ),
            'highest_failure_rate_type', (
                SELECT task_type
                FROM tasks
                WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '7 days'
                GROUP BY task_type
                HAVING COUNT(*) > 10
                ORDER BY (COUNT(CASE WHEN status = 'failed' THEN 1 END)::float / COUNT(*)) DESC
                LIMIT 1
            )
        ) as bottleneck_analysis
    FROM tasks
    WHERE deleted_at IS NULL
    AND created_at >= CURRENT_TIMESTAMP - INTERVAL '30 days'
) task_metrics;

-- Events module performance analysis
CREATE OR REPLACE VIEW events_performance_analysis AS
SELECT 
    'events_performance' as analysis_type,
    jsonb_build_object(
        'avg_processing_time_seconds', avg_processing_time,
        'median_processing_time_seconds', median_processing_time,
        'p95_processing_time_seconds', p95_processing_time,
        'events_per_hour_last_24h', events_per_hour,
        'processing_success_rate', processing_success_rate,
        'backlog_size', backlog_size,
        'source_performance', source_performance
    ) as metrics,
    CURRENT_TIMESTAMP as analyzed_at
FROM (
    SELECT 
        ROUND(AVG(EXTRACT(EPOCH FROM (processed_at - received_at)))::numeric, 2) as avg_processing_time,
        ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (processed_at - received_at)))::numeric, 2) as median_processing_time,
        ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (processed_at - received_at)))::numeric, 2) as p95_processing_time,
        ROUND((COUNT(CASE WHEN received_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours' THEN 1 END)::float / 24)::numeric, 2) as events_per_hour,
        ROUND((COUNT(CASE WHEN status = 'processed' THEN 1 END)::float / NULLIF(COUNT(*), 0) * 100)::numeric, 2) as processing_success_rate,
        (SELECT COUNT(*) FROM events WHERE status = 'pending') as backlog_size,
        (
            SELECT jsonb_object_agg(source, metrics)
            FROM (
                SELECT 
                    source,
                    jsonb_build_object(
                        'avg_processing_time', ROUND(AVG(EXTRACT(EPOCH FROM (processed_at - received_at)))::numeric, 2),
                        'success_rate', ROUND((COUNT(CASE WHEN status = 'processed' THEN 1 END)::float / COUNT(*) * 100)::numeric, 2),
                        'volume_last_24h', COUNT(CASE WHEN received_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours' THEN 1 END)
                    ) as metrics
                FROM events
                WHERE received_at >= CURRENT_TIMESTAMP - INTERVAL '7 days'
                GROUP BY source
            ) source_stats
        ) as source_performance
    FROM events
    WHERE received_at >= CURRENT_TIMESTAMP - INTERVAL '30 days'
) event_metrics;

-- Analytics module performance analysis
CREATE OR REPLACE VIEW analytics_performance_analysis AS
SELECT 
    'analytics_performance' as analysis_type,
    jsonb_build_object(
        'avg_analysis_duration_minutes', avg_analysis_duration,
        'median_analysis_duration_minutes', median_analysis_duration,
        'p95_analysis_duration_minutes', p95_analysis_duration,
        'analyses_per_day', analyses_per_day,
        'success_rate_percent', success_rate,
        'avg_files_per_analysis', avg_files_per_analysis,
        'avg_issues_per_analysis', avg_issues_per_analysis,
        'tool_performance', tool_performance
    ) as metrics,
    CURRENT_TIMESTAMP as analyzed_at
FROM (
    SELECT 
        ROUND(AVG(duration_seconds / 60.0)::numeric, 2) as avg_analysis_duration,
        ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY duration_seconds / 60.0)::numeric, 2) as median_analysis_duration,
        ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_seconds / 60.0)::numeric, 2) as p95_analysis_duration,
        ROUND((COUNT(CASE WHEN created_at >= CURRENT_TIMESTAMP - INTERVAL '7 days' THEN 1 END)::float / 7)::numeric, 2) as analyses_per_day,
        ROUND((COUNT(CASE WHEN status = 'completed' THEN 1 END)::float / NULLIF(COUNT(*), 0) * 100)::numeric, 2) as success_rate,
        ROUND(AVG(total_files_analyzed)::numeric, 2) as avg_files_per_analysis,
        ROUND(AVG(total_issues_found)::numeric, 2) as avg_issues_per_analysis,
        (
            SELECT jsonb_object_agg(tool_name, tool_metrics)
            FROM (
                SELECT 
                    tool_name,
                    jsonb_build_object(
                        'avg_duration_minutes', ROUND(AVG(duration_seconds / 60.0)::numeric, 2),
                        'success_rate', ROUND((COUNT(CASE WHEN status = 'completed' THEN 1 END)::float / COUNT(*) * 100)::numeric, 2),
                        'avg_files_analyzed', ROUND(AVG(total_files_analyzed)::numeric, 2),
                        'usage_count', COUNT(*)
                    ) as tool_metrics
                FROM analysis_runs
                WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '30 days'
                AND tool_name IS NOT NULL
                GROUP BY tool_name
            ) tool_stats
        ) as tool_performance
    FROM analysis_runs
    WHERE deleted_at IS NULL
    AND created_at >= CURRENT_TIMESTAMP - INTERVAL '30 days'
) analysis_metrics;

-- =============================================================================
-- RESOURCE UTILIZATION MONITORING
-- =============================================================================

-- Database resource utilization
CREATE OR REPLACE VIEW database_resource_utilization AS
SELECT 
    'database_resources' as resource_type,
    jsonb_build_object(
        'cpu_usage_percent', cpu_usage_percent,
        'memory_usage_percent', memory_usage_percent,
        'disk_usage_percent', disk_usage_percent,
        'connection_usage_percent', connection_usage_percent,
        'cache_hit_ratio', cache_hit_ratio,
        'active_queries', active_queries,
        'waiting_queries', waiting_queries,
        'temp_files_usage_mb', temp_files_usage_mb
    ) as metrics,
    CASE 
        WHEN cpu_usage_percent > 90 OR memory_usage_percent > 90 OR disk_usage_percent > 90 THEN 'critical'
        WHEN cpu_usage_percent > 80 OR memory_usage_percent > 80 OR disk_usage_percent > 80 THEN 'warning'
        ELSE 'normal'
    END as status,
    CURRENT_TIMESTAMP as measured_at
FROM (
    SELECT 
        -- CPU usage (approximated from query activity)
        ROUND((
            SELECT COUNT(*) * 10.0 -- Rough approximation
            FROM pg_stat_activity 
            WHERE state = 'active'
        )::numeric, 2) as cpu_usage_percent,
        
        -- Memory usage (shared buffers hit ratio as proxy)
        ROUND((
            SELECT 
                CASE 
                    WHEN blks_hit + blks_read = 0 THEN 0
                    ELSE (blks_hit::float / (blks_hit + blks_read) * 100)
                END
            FROM pg_stat_database 
            WHERE datname = current_database()
        )::numeric, 2) as memory_usage_percent,
        
        -- Disk usage
        ROUND((pg_database_size(current_database())::float / (1024*1024*1024*100) * 100)::numeric, 2) as disk_usage_percent,
        
        -- Connection usage
        ROUND((
            (SELECT count(*) FROM pg_stat_activity)::float / 
            (SELECT setting::int FROM pg_settings WHERE name = 'max_connections') * 100
        )::numeric, 2) as connection_usage_percent,
        
        -- Cache hit ratio
        ROUND((
            SELECT 
                CASE 
                    WHEN blks_hit + blks_read = 0 THEN 0
                    ELSE (blks_hit::float / (blks_hit + blks_read) * 100)
                END
            FROM pg_stat_database 
            WHERE datname = current_database()
        )::numeric, 2) as cache_hit_ratio,
        
        -- Active queries
        (SELECT count(*) FROM pg_stat_activity WHERE state = 'active') as active_queries,
        
        -- Waiting queries
        (SELECT count(*) FROM pg_stat_activity WHERE wait_event IS NOT NULL) as waiting_queries,
        
        -- Temporary files usage
        ROUND((
            SELECT COALESCE(SUM(temp_bytes), 0) / (1024*1024)
            FROM pg_stat_database
        )::numeric, 2) as temp_files_usage_mb
) resource_data;

-- =============================================================================
-- OPTIMIZATION RECOMMENDATIONS
-- =============================================================================

-- Automated performance optimization recommendations
CREATE OR REPLACE VIEW performance_optimization_recommendations AS
SELECT 
    recommendation_id,
    category,
    priority,
    title,
    description,
    sql_command,
    estimated_impact,
    risk_level,
    CURRENT_TIMESTAMP as generated_at
FROM (
    -- Missing index recommendations
    SELECT 
        'missing_indexes_' || ROW_NUMBER() OVER() as recommendation_id,
        'indexing' as category,
        'high' as priority,
        'Add indexes for frequently scanned tables' as title,
        'Table ' || schemaname || '.' || relname || ' has high sequential scan ratio (' || 
        ROUND((seq_scan::float / NULLIF(seq_scan + idx_scan, 0) * 100)::numeric, 2) || '%)' as description,
        'ANALYZE ' || schemaname || '.' || relname || '; -- Review query patterns and add appropriate indexes' as sql_command,
        'Significant query performance improvement' as estimated_impact,
        'low' as risk_level
    FROM pg_stat_user_tables
    WHERE seq_scan > idx_scan * 2 
    AND seq_tup_read > 10000
    AND schemaname = 'public'
    
    UNION ALL
    
    -- Unused index recommendations
    SELECT 
        'unused_indexes_' || ROW_NUMBER() OVER() as recommendation_id,
        'indexing' as category,
        'medium' as priority,
        'Remove unused indexes' as title,
        'Index ' || indexname || ' on table ' || tablename || ' is unused and consuming ' || 
        pg_size_pretty(pg_relation_size(indexrelid)) as description,
        'DROP INDEX CONCURRENTLY ' || indexname || ';' as sql_command,
        'Improved write performance, reduced storage' as estimated_impact,
        'low' as risk_level
    FROM pg_stat_user_indexes
    WHERE idx_scan = 0
    AND pg_relation_size(indexrelid) > 1024*1024 -- Only suggest for indexes > 1MB
    AND schemaname = 'public'
    
    UNION ALL
    
    -- Table maintenance recommendations
    SELECT 
        'table_maintenance_' || ROW_NUMBER() OVER() as recommendation_id,
        'maintenance' as category,
        'high' as priority,
        'Vacuum and analyze tables with high dead tuple ratio' as title,
        'Table ' || schemaname || '.' || relname || ' has ' || 
        ROUND((n_dead_tup::float / NULLIF(n_live_tup, 0) * 100)::numeric, 2) || '% dead tuples' as description,
        'VACUUM ANALYZE ' || schemaname || '.' || relname || ';' as sql_command,
        'Improved query performance, reclaimed storage' as estimated_impact,
        'low' as risk_level
    FROM pg_stat_user_tables
    WHERE n_dead_tup > n_live_tup * 0.2
    AND n_live_tup > 1000
    AND schemaname = 'public'
    
    UNION ALL
    
    -- Configuration recommendations
    SELECT 
        'config_optimization_' || ROW_NUMBER() OVER() as recommendation_id,
        'configuration' as category,
        'medium' as priority,
        'Optimize PostgreSQL configuration' as title,
        'Consider increasing ' || setting_name || ' from ' || current_value || ' to improve performance' as description,
        'ALTER SYSTEM SET ' || setting_name || ' = ''' || recommended_value || '''; SELECT pg_reload_conf();' as sql_command,
        estimated_impact,
        'medium' as risk_level
    FROM (
        SELECT 
            'shared_buffers' as setting_name,
            current_setting('shared_buffers') as current_value,
            '256MB' as recommended_value,
            'Better cache performance' as estimated_impact
        WHERE pg_size_bytes(current_setting('shared_buffers')) < 256*1024*1024
        
        UNION ALL
        
        SELECT 
            'work_mem' as setting_name,
            current_setting('work_mem') as current_value,
            '16MB' as recommended_value,
            'Reduced temporary file usage' as estimated_impact
        WHERE pg_size_bytes(current_setting('work_mem')) < 16*1024*1024
    ) config_recommendations
) all_recommendations
ORDER BY 
    CASE priority 
        WHEN 'high' THEN 1 
        WHEN 'medium' THEN 2 
        WHEN 'low' THEN 3 
    END,
    category;

COMMENT ON VIEW slow_query_analysis IS 'Detailed analysis of slow queries with performance recommendations';
COMMENT ON VIEW index_usage_analysis IS 'Index usage patterns and optimization opportunities';
COMMENT ON VIEW table_access_patterns IS 'Table access patterns and maintenance recommendations';
COMMENT ON VIEW tasks_performance_analysis IS 'Performance metrics and bottleneck analysis for tasks module';
COMMENT ON VIEW events_performance_analysis IS 'Performance metrics and processing analysis for events module';
COMMENT ON VIEW analytics_performance_analysis IS 'Performance metrics and tool analysis for analytics module';
COMMENT ON VIEW database_resource_utilization IS 'Real-time database resource utilization monitoring';
COMMENT ON VIEW performance_optimization_recommendations IS 'Automated performance optimization recommendations';

