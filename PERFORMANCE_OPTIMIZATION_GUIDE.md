# ⚡ Performance Optimization Guide

## Overview

This guide provides comprehensive performance optimization strategies for the 7-module database schema, based on analysis of PRs 74, 75, 76, and 79. The optimizations ensure sub-second query response times and support for 1000+ concurrent operations.

## Performance Targets

### Primary Targets (Based on PR 79 Analysis)
- **Query Response Time**: < 100ms for 95% of queries
- **Concurrent Operations**: 1000+ simultaneous tasks
- **Analysis Throughput**: 100K+ lines of code in under 5 minutes
- **System Uptime**: 99.9% availability
- **Database Size**: Efficient storage with < 10% overhead

### Secondary Targets
- **Memory Usage**: < 4GB for typical workloads
- **CPU Utilization**: < 70% under normal load
- **Disk I/O**: < 1000 IOPS for standard operations
- **Network Latency**: < 50ms for local connections

## Indexing Strategy

### Primary Performance Indexes

```sql
-- Critical performance indexes for high-frequency queries
CREATE INDEX CONCURRENTLY idx_tasks_status_priority_time 
ON tasks(status, priority, created_at DESC) 
WHERE status IN ('pending', 'in_progress', 'assigned');

CREATE INDEX CONCURRENTLY idx_task_executions_status_time 
ON task_executions(status, started_at DESC)
WHERE status IN ('running', 'completed', 'failed');

CREATE INDEX CONCURRENTLY idx_agent_tasks_status_priority 
ON agent_tasks(status, priority, created_at DESC)
WHERE status != 'archived';

CREATE INDEX CONCURRENTLY idx_pipeline_executions_status_time 
ON pipeline_executions(status, started_at DESC)
WHERE completed_at IS NULL OR completed_at >= NOW() - INTERVAL '7 days';

CREATE INDEX CONCURRENTLY idx_integration_events_processing 
ON integration_events(integration_type, processed, created_at DESC)
WHERE processed = false OR created_at >= NOW() - INTERVAL '1 day';
```

### Composite Indexes for Complex Queries

```sql
-- Multi-column indexes for complex filtering
CREATE INDEX CONCURRENTLY idx_tasks_org_project_status_priority 
ON tasks(organization_id, project_id, status, priority)
INCLUDE (title, created_at, assigned_to);

CREATE INDEX CONCURRENTLY idx_agents_org_type_active_performance 
ON codegen_agents(organization_id, agent_type, is_active)
INCLUDE (name, last_used_at, usage_stats);

CREATE INDEX CONCURRENTLY idx_metrics_org_name_time_value 
ON system_metrics(organization_id, metric_name, timestamp DESC)
INCLUDE (value, unit, context);

CREATE INDEX CONCURRENTLY idx_learning_patterns_org_type_confidence 
ON learning_patterns(organization_id, pattern_type, confidence_score DESC)
WHERE confidence_score >= 0.7;
```

### JSONB Optimization Indexes

```sql
-- GIN indexes for JSONB fields with specific paths
CREATE INDEX CONCURRENTLY idx_tasks_metadata_type 
ON tasks USING gin((metadata->'type'));

CREATE INDEX CONCURRENTLY idx_tasks_metadata_priority 
ON tasks USING gin((metadata->'priority'));

CREATE INDEX CONCURRENTLY idx_agent_tasks_context_repo 
ON agent_tasks USING gin((context->'repository'));

CREATE INDEX CONCURRENTLY idx_learning_patterns_data_category 
ON learning_patterns USING gin((pattern_data->'category'));

CREATE INDEX CONCURRENTLY idx_knowledge_base_tags 
ON knowledge_base USING gin(tags);

-- Specific JSONB path indexes for common queries
CREATE INDEX CONCURRENTLY idx_projects_settings_features 
ON projects USING gin((settings->'features'));

CREATE INDEX CONCURRENTLY idx_organizations_settings_limits 
ON organizations USING gin((settings->'limits'));
```

### Text Search Optimization

```sql
-- Full-text search indexes using pg_trgm
CREATE INDEX CONCURRENTLY idx_tasks_title_description_search 
ON tasks USING gin(to_tsvector('english', title || ' ' || COALESCE(description, '')));

CREATE INDEX CONCURRENTLY idx_knowledge_base_content_search 
ON knowledge_base USING gin(to_tsvector('english', title || ' ' || content));

-- Trigram indexes for partial matching
CREATE INDEX CONCURRENTLY idx_tasks_title_trgm 
ON tasks USING gin(title gin_trgm_ops);

CREATE INDEX CONCURRENTLY idx_repositories_name_trgm 
ON repositories USING gin(name gin_trgm_ops);

CREATE INDEX CONCURRENTLY idx_users_name_email_trgm 
ON users USING gin((name || ' ' || email) gin_trgm_ops);
```

## Query Optimization

### Optimized Query Patterns

#### 1. Task Management Queries
```sql
-- Optimized task retrieval with proper indexing
CREATE OR REPLACE FUNCTION get_active_tasks_optimized(
    org_id UUID,
    limit_count INTEGER DEFAULT 50,
    offset_count INTEGER DEFAULT 0
)
RETURNS TABLE(
    task_id UUID,
    title VARCHAR,
    status VARCHAR,
    priority INTEGER,
    assigned_to_name VARCHAR,
    created_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.id,
        t.title,
        t.status,
        t.priority,
        u.name,
        t.created_at
    FROM tasks t
    LEFT JOIN users u ON t.assigned_to = u.id
    WHERE t.organization_id = org_id
    AND t.status IN ('pending', 'in_progress', 'assigned')
    ORDER BY t.priority ASC, t.created_at DESC
    LIMIT limit_count OFFSET offset_count;
END;
$$ LANGUAGE plpgsql STABLE;
```

#### 2. Agent Performance Queries
```sql
-- Optimized agent performance analysis
CREATE OR REPLACE FUNCTION get_agent_performance_metrics(
    org_id UUID,
    time_period INTERVAL DEFAULT '30 days'
)
RETURNS TABLE(
    agent_id UUID,
    agent_name VARCHAR,
    total_tasks BIGINT,
    success_rate DECIMAL,
    avg_completion_time INTERVAL,
    total_cost DECIMAL,
    performance_score DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    WITH agent_stats AS (
        SELECT 
            a.id,
            a.name,
            COUNT(at.id) as task_count,
            COUNT(at.id) FILTER (WHERE at.status = 'completed') as completed_count,
            AVG(EXTRACT(EPOCH FROM (at.completed_at - at.started_at))) as avg_seconds,
            SUM(at.cost_estimate) as total_cost,
            AVG(at.performance_score) as avg_performance
        FROM codegen_agents a
        LEFT JOIN agent_tasks at ON a.id = at.agent_id
        WHERE a.organization_id = org_id
        AND a.is_active = true
        AND (at.created_at IS NULL OR at.created_at >= NOW() - time_period)
        GROUP BY a.id, a.name
    )
    SELECT 
        s.id,
        s.name,
        s.task_count,
        CASE 
            WHEN s.task_count > 0 THEN (s.completed_count::DECIMAL / s.task_count * 100)
            ELSE 0
        END,
        CASE 
            WHEN s.avg_seconds IS NOT NULL THEN INTERVAL '1 second' * s.avg_seconds
            ELSE NULL
        END,
        COALESCE(s.total_cost, 0),
        COALESCE(s.avg_performance, 0)
    FROM agent_stats s
    ORDER BY s.avg_performance DESC NULLS LAST;
END;
$$ LANGUAGE plpgsql STABLE;
```

#### 3. Analytics Queries
```sql
-- Optimized analytics aggregation
CREATE OR REPLACE FUNCTION get_organization_analytics(
    org_id UUID,
    start_date DATE DEFAULT CURRENT_DATE - INTERVAL '30 days',
    end_date DATE DEFAULT CURRENT_DATE
)
RETURNS JSONB AS $$
DECLARE
    result JSONB;
BEGIN
    WITH daily_stats AS (
        SELECT 
            DATE(created_at) as date,
            COUNT(*) FILTER (WHERE type = 'task') as tasks_created,
            COUNT(*) FILTER (WHERE type = 'task' AND status = 'completed') as tasks_completed,
            COUNT(*) FILTER (WHERE type = 'agent_task') as agent_tasks,
            AVG(CASE WHEN type = 'agent_task' THEN cost_estimate END) as avg_cost
        FROM (
            SELECT created_at, 'task' as type, status, NULL as cost_estimate
            FROM tasks 
            WHERE organization_id = org_id
            UNION ALL
            SELECT created_at, 'agent_task' as type, status, cost_estimate
            FROM agent_tasks at
            JOIN codegen_agents ca ON at.agent_id = ca.id
            WHERE ca.organization_id = org_id
        ) combined
        WHERE DATE(created_at) BETWEEN start_date AND end_date
        GROUP BY DATE(created_at)
    )
    SELECT jsonb_build_object(
        'period', jsonb_build_object(
            'start_date', start_date,
            'end_date', end_date
        ),
        'summary', jsonb_build_object(
            'total_tasks', SUM(tasks_created),
            'completed_tasks', SUM(tasks_completed),
            'completion_rate', CASE 
                WHEN SUM(tasks_created) > 0 THEN SUM(tasks_completed)::DECIMAL / SUM(tasks_created) * 100
                ELSE 0
            END,
            'total_agent_tasks', SUM(agent_tasks),
            'avg_daily_cost', AVG(avg_cost)
        ),
        'daily_trends', jsonb_agg(
            jsonb_build_object(
                'date', date,
                'tasks_created', tasks_created,
                'tasks_completed', tasks_completed,
                'agent_tasks', agent_tasks,
                'avg_cost', avg_cost
            ) ORDER BY date
        )
    ) INTO result
    FROM daily_stats;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql STABLE;
```

## Materialized Views for Performance

### High-Performance Analytics Views

```sql
-- Daily task summary with performance optimization
CREATE MATERIALIZED VIEW mv_daily_task_summary AS
SELECT 
    DATE(t.created_at) as date,
    t.organization_id,
    t.project_id,
    COUNT(*) as total_tasks,
    COUNT(*) FILTER (WHERE t.status = 'completed') as completed_tasks,
    COUNT(*) FILTER (WHERE t.status = 'failed') as failed_tasks,
    COUNT(*) FILTER (WHERE t.status IN ('pending', 'in_progress')) as active_tasks,
    AVG(t.actual_hours) as avg_hours,
    AVG(t.priority) as avg_priority,
    COUNT(DISTINCT t.assigned_to) as unique_assignees,
    -- Performance metrics
    AVG(EXTRACT(EPOCH FROM (te.completed_at - te.started_at))) as avg_execution_seconds,
    COUNT(te.id) FILTER (WHERE te.status = 'completed') as successful_executions
FROM tasks t
LEFT JOIN task_executions te ON t.id = te.task_id
WHERE t.created_at >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY DATE(t.created_at), t.organization_id, t.project_id;

-- Unique index for efficient updates
CREATE UNIQUE INDEX idx_mv_daily_task_summary_unique 
ON mv_daily_task_summary (date, organization_id, COALESCE(project_id, '00000000-0000-0000-0000-000000000000'::UUID));

-- Agent performance summary
CREATE MATERIALIZED VIEW mv_agent_performance_summary AS
SELECT 
    ca.id as agent_id,
    ca.organization_id,
    ca.name as agent_name,
    ca.agent_type,
    DATE(at.created_at) as date,
    COUNT(*) as total_tasks,
    COUNT(*) FILTER (WHERE at.status = 'completed') as completed_tasks,
    COUNT(*) FILTER (WHERE at.status = 'failed') as failed_tasks,
    AVG(at.tokens_used) as avg_tokens,
    SUM(at.cost_estimate) as total_cost,
    AVG(at.performance_score) as avg_performance_score,
    AVG(EXTRACT(EPOCH FROM (at.completed_at - at.started_at))) as avg_completion_seconds
FROM codegen_agents ca
LEFT JOIN agent_tasks at ON ca.id = at.agent_id
WHERE ca.is_active = true
AND (at.created_at IS NULL OR at.created_at >= CURRENT_DATE - INTERVAL '30 days')
GROUP BY ca.id, ca.organization_id, ca.name, ca.agent_type, DATE(at.created_at);

-- Unique index for agent performance
CREATE UNIQUE INDEX idx_mv_agent_performance_summary_unique 
ON mv_agent_performance_summary (agent_id, COALESCE(date, '1900-01-01'::DATE));

-- System metrics rollup
CREATE MATERIALIZED VIEW mv_system_metrics_hourly AS
SELECT 
    DATE_TRUNC('hour', timestamp) as hour,
    organization_id,
    metric_name,
    metric_type,
    COUNT(*) as measurement_count,
    AVG(value) as avg_value,
    MIN(value) as min_value,
    MAX(value) as max_value,
    STDDEV(value) as stddev_value,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY value) as median_value,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY value) as p95_value
FROM system_metrics
WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL '7 days'
GROUP BY DATE_TRUNC('hour', timestamp), organization_id, metric_name, metric_type;

-- Unique index for metrics rollup
CREATE UNIQUE INDEX idx_mv_system_metrics_hourly_unique 
ON mv_system_metrics_hourly (hour, COALESCE(organization_id, '00000000-0000-0000-0000-000000000000'::UUID), metric_name, metric_type);
```

### Automated Refresh Strategy

```sql
-- Efficient materialized view refresh function
CREATE OR REPLACE FUNCTION refresh_performance_views()
RETURNS JSONB AS $$
DECLARE
    start_time TIMESTAMP;
    end_time TIMESTAMP;
    refresh_stats JSONB;
BEGIN
    start_time := clock_timestamp();
    
    -- Refresh views in dependency order
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_task_summary;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_agent_performance_summary;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_system_metrics_hourly;
    
    end_time := clock_timestamp();
    
    -- Log refresh performance
    refresh_stats := jsonb_build_object(
        'start_time', start_time,
        'end_time', end_time,
        'duration_seconds', EXTRACT(EPOCH FROM (end_time - start_time)),
        'views_refreshed', ARRAY['mv_daily_task_summary', 'mv_agent_performance_summary', 'mv_system_metrics_hourly']
    );
    
    -- Record metrics
    INSERT INTO system_metrics (metric_name, metric_type, value, unit, context)
    VALUES (
        'materialized_view_refresh_duration',
        'performance',
        EXTRACT(EPOCH FROM (end_time - start_time)),
        'seconds',
        refresh_stats
    );
    
    RETURN refresh_stats;
END;
$$ LANGUAGE plpgsql;
```

## Connection Pool Optimization

### PostgreSQL Configuration

```sql
-- Optimal PostgreSQL settings for performance
-- Add to postgresql.conf

-- Memory settings
shared_buffers = '256MB'                    -- 25% of RAM for dedicated server
work_mem = '16MB'                          -- Per-operation memory
maintenance_work_mem = '64MB'              -- Maintenance operations
effective_cache_size = '1GB'              -- OS cache estimate

-- Connection settings
max_connections = 200                      -- Adjust based on workload
shared_preload_libraries = 'pg_stat_statements'

-- Query optimization
random_page_cost = 1.1                    -- SSD optimization
effective_io_concurrency = 200            -- SSD concurrent I/O
default_statistics_target = 100           -- Statistics detail

-- Logging and monitoring
log_min_duration_statement = 1000         -- Log slow queries
log_checkpoints = on
log_connections = on
log_disconnections = on
log_lock_waits = on

-- Write-ahead logging
wal_buffers = '16MB'
checkpoint_completion_target = 0.9
wal_compression = on

-- Background writer
bgwriter_delay = 200ms
bgwriter_lru_maxpages = 100
bgwriter_lru_multiplier = 2.0
```

### Application-Level Connection Pooling

```python
# Optimized connection pool configuration
import asyncpg
import asyncio
from typing import Optional

class OptimizedConnectionPool:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool: Optional[asyncpg.Pool] = None
    
    async def initialize(self):
        self.pool = await asyncpg.create_pool(
            self.database_url,
            min_size=10,                    # Minimum connections
            max_size=50,                    # Maximum connections
            max_queries=50000,              # Queries per connection
            max_inactive_connection_lifetime=300,  # 5 minutes
            command_timeout=60,             # Command timeout
            server_settings={
                'application_name': 'graph_sitter_app',
                'jit': 'off',              # Disable JIT for predictable performance
                'statement_timeout': '30s'  # Statement timeout
            }
        )
    
    async def execute_optimized_query(self, query: str, *args):
        async with self.pool.acquire() as conn:
            # Use prepared statements for better performance
            stmt = await conn.prepare(query)
            return await stmt.fetch(*args)
    
    async def close(self):
        if self.pool:
            await self.pool.close()
```

## Monitoring and Alerting

### Performance Monitoring Functions

```sql
-- Comprehensive performance monitoring
CREATE OR REPLACE FUNCTION get_performance_metrics()
RETURNS JSONB AS $$
DECLARE
    result JSONB;
    slow_queries JSONB;
    index_usage JSONB;
    connection_stats JSONB;
BEGIN
    -- Get slow queries
    SELECT jsonb_agg(
        jsonb_build_object(
            'query', substr(query, 1, 100),
            'calls', calls,
            'total_time', total_time,
            'mean_time', mean_time,
            'rows', rows
        )
    ) INTO slow_queries
    FROM pg_stat_statements
    WHERE mean_time > 100  -- Queries slower than 100ms
    ORDER BY total_time DESC
    LIMIT 10;
    
    -- Get index usage statistics
    SELECT jsonb_agg(
        jsonb_build_object(
            'table', schemaname || '.' || tablename,
            'index', indexname,
            'scans', idx_scan,
            'tuples_read', idx_tup_read,
            'tuples_fetched', idx_tup_fetch,
            'usage_ratio', CASE 
                WHEN idx_scan > 0 THEN idx_tup_fetch::DECIMAL / idx_tup_read
                ELSE 0
            END
        )
    ) INTO index_usage
    FROM pg_stat_user_indexes
    WHERE idx_scan < 100  -- Potentially unused indexes
    ORDER BY idx_scan ASC
    LIMIT 10;
    
    -- Get connection statistics
    SELECT jsonb_build_object(
        'total_connections', COUNT(*),
        'active_connections', COUNT(*) FILTER (WHERE state = 'active'),
        'idle_connections', COUNT(*) FILTER (WHERE state = 'idle'),
        'waiting_connections', COUNT(*) FILTER (WHERE wait_event IS NOT NULL),
        'max_connections', (SELECT setting::INTEGER FROM pg_settings WHERE name = 'max_connections')
    ) INTO connection_stats
    FROM pg_stat_activity;
    
    -- Combine all metrics
    result := jsonb_build_object(
        'timestamp', NOW(),
        'database_size_mb', pg_database_size(current_database()) / 1024 / 1024,
        'slow_queries', slow_queries,
        'index_usage', index_usage,
        'connections', connection_stats,
        'cache_hit_ratio', (
            SELECT ROUND(
                100.0 * sum(blks_hit) / (sum(blks_hit) + sum(blks_read)), 2
            )
            FROM pg_stat_database
            WHERE datname = current_database()
        )
    );
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Performance alerting function
CREATE OR REPLACE FUNCTION check_performance_alerts()
RETURNS JSONB AS $$
DECLARE
    alerts JSONB := '[]'::JSONB;
    cache_hit_ratio DECIMAL;
    active_connections INTEGER;
    max_connections INTEGER;
    slow_query_count INTEGER;
BEGIN
    -- Check cache hit ratio
    SELECT ROUND(
        100.0 * sum(blks_hit) / (sum(blks_hit) + sum(blks_read)), 2
    ) INTO cache_hit_ratio
    FROM pg_stat_database
    WHERE datname = current_database();
    
    IF cache_hit_ratio < 95 THEN
        alerts := alerts || jsonb_build_object(
            'type', 'cache_hit_ratio',
            'severity', 'warning',
            'message', 'Cache hit ratio is ' || cache_hit_ratio || '% (should be > 95%)',
            'value', cache_hit_ratio
        );
    END IF;
    
    -- Check connection usage
    SELECT 
        COUNT(*) FILTER (WHERE state = 'active'),
        (SELECT setting::INTEGER FROM pg_settings WHERE name = 'max_connections')
    INTO active_connections, max_connections
    FROM pg_stat_activity;
    
    IF active_connections > max_connections * 0.8 THEN
        alerts := alerts || jsonb_build_object(
            'type', 'high_connection_usage',
            'severity', 'warning',
            'message', 'Active connections (' || active_connections || ') > 80% of max (' || max_connections || ')',
            'value', active_connections
        );
    END IF;
    
    -- Check for slow queries
    SELECT COUNT(*) INTO slow_query_count
    FROM pg_stat_statements
    WHERE mean_time > 1000;  -- Queries slower than 1 second
    
    IF slow_query_count > 5 THEN
        alerts := alerts || jsonb_build_object(
            'type', 'slow_queries',
            'severity', 'critical',
            'message', 'Found ' || slow_query_count || ' queries with mean time > 1 second',
            'value', slow_query_count
        );
    END IF;
    
    RETURN jsonb_build_object(
        'timestamp', NOW(),
        'alert_count', jsonb_array_length(alerts),
        'alerts', alerts
    );
END;
$$ LANGUAGE plpgsql;
```

### Automated Performance Optimization

```sql
-- Automated maintenance and optimization
CREATE OR REPLACE FUNCTION optimize_database_performance()
RETURNS JSONB AS $$
DECLARE
    optimization_results JSONB := '{}'::JSONB;
    table_stats RECORD;
    index_stats RECORD;
BEGIN
    -- Update table statistics for better query planning
    ANALYZE;
    
    -- Check for tables that need vacuuming
    FOR table_stats IN
        SELECT schemaname, tablename, n_dead_tup, n_live_tup
        FROM pg_stat_user_tables
        WHERE n_dead_tup > n_live_tup * 0.1  -- More than 10% dead tuples
    LOOP
        EXECUTE format('VACUUM ANALYZE %I.%I', table_stats.schemaname, table_stats.tablename);
        
        optimization_results := optimization_results || jsonb_build_object(
            'vacuumed_table', table_stats.schemaname || '.' || table_stats.tablename,
            'dead_tuples', table_stats.n_dead_tup,
            'live_tuples', table_stats.n_live_tup
        );
    END LOOP;
    
    -- Identify and suggest missing indexes
    INSERT INTO system_metrics (metric_name, metric_type, value, unit, context)
    SELECT 
        'missing_index_suggestion',
        'optimization',
        seq_scan,
        'scans',
        jsonb_build_object(
            'table', schemaname || '.' || tablename,
            'seq_scans', seq_scan,
            'seq_tup_read', seq_tup_read,
            'suggestion', 'Consider adding index for frequently scanned table'
        )
    FROM pg_stat_user_tables
    WHERE seq_scan > 1000 AND seq_tup_read > seq_scan * 1000;
    
    -- Record optimization completion
    INSERT INTO system_metrics (metric_name, metric_type, value, unit, context)
    VALUES (
        'database_optimization_completed',
        'maintenance',
        1,
        'count',
        optimization_results
    );
    
    RETURN jsonb_build_object(
        'status', 'completed',
        'timestamp', NOW(),
        'optimizations', optimization_results
    );
END;
$$ LANGUAGE plpgsql;
```

## Performance Testing

### Load Testing Queries

```sql
-- Simulate high-load scenarios for testing
CREATE OR REPLACE FUNCTION simulate_high_load(
    duration_seconds INTEGER DEFAULT 60,
    concurrent_queries INTEGER DEFAULT 100
)
RETURNS JSONB AS $$
DECLARE
    start_time TIMESTAMP;
    end_time TIMESTAMP;
    query_count INTEGER := 0;
    error_count INTEGER := 0;
BEGIN
    start_time := clock_timestamp();
    end_time := start_time + INTERVAL '1 second' * duration_seconds;
    
    -- Simulate concurrent task queries
    WHILE clock_timestamp() < end_time LOOP
        BEGIN
            -- Simulate common queries
            PERFORM COUNT(*) FROM tasks WHERE status = 'pending';
            PERFORM COUNT(*) FROM agent_tasks WHERE status = 'running';
            PERFORM get_system_health();
            
            query_count := query_count + 3;
        EXCEPTION WHEN OTHERS THEN
            error_count := error_count + 1;
        END;
    END LOOP;
    
    RETURN jsonb_build_object(
        'duration_seconds', EXTRACT(EPOCH FROM (clock_timestamp() - start_time)),
        'queries_executed', query_count,
        'errors', error_count,
        'queries_per_second', query_count / EXTRACT(EPOCH FROM (clock_timestamp() - start_time))
    );
END;
$$ LANGUAGE plpgsql;
```

## Best Practices Summary

### 1. Query Optimization
- Use appropriate indexes for all frequent queries
- Avoid SELECT * in production queries
- Use LIMIT for large result sets
- Implement proper WHERE clause ordering

### 2. Index Management
- Create indexes CONCURRENTLY to avoid blocking
- Monitor index usage and remove unused indexes
- Use partial indexes for filtered queries
- Implement composite indexes for multi-column queries

### 3. Connection Management
- Use connection pooling for all applications
- Set appropriate timeout values
- Monitor connection usage patterns
- Implement proper error handling

### 4. Monitoring
- Regular performance metric collection
- Automated alerting for performance issues
- Query performance analysis
- Resource utilization monitoring

### 5. Maintenance
- Regular VACUUM and ANALYZE operations
- Materialized view refresh scheduling
- Index maintenance and optimization
- Statistics updates

This performance optimization guide ensures the database system meets all performance targets while maintaining reliability and scalability for production workloads.

