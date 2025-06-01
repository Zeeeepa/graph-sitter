-- Enhanced Database Schema: Analytics and Performance Optimization
-- Part 4: Time-Series Analytics, Performance Monitoring, and System Optimization

-- Learning Events Table (Time-Series Optimized with Partitioning)
CREATE TABLE learning_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(100) NOT NULL, -- 'model_prediction', 'pattern_detection', 'user_feedback', 'system_optimization'
    event_subtype VARCHAR(100), -- More specific categorization
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    source_system VARCHAR(100), -- 'openevolve', 'pattern_analyzer', 'user_interface', 'api'
    entity_type VARCHAR(100), -- What type of entity this event relates to
    entity_id VARCHAR(255), -- ID of the related entity
    event_data JSONB NOT NULL, -- The actual event payload
    user_id VARCHAR(255), -- User associated with the event (if applicable)
    session_id VARCHAR(255), -- Session ID for grouping related events
    processing_time_ms INTEGER, -- How long it took to process this event
    event_size_bytes INTEGER, -- Size of the event data
    correlation_id VARCHAR(255), -- For tracing related events
    metadata JSONB, -- Additional context
    
    CHECK (processing_time_ms >= 0),
    CHECK (event_size_bytes >= 0),
    CHECK (event_type IN ('model_prediction', 'pattern_detection', 'user_feedback', 'system_optimization', 'error', 'performance_metric'))
) PARTITION BY RANGE (timestamp);

-- Create monthly partitions for learning_events
CREATE TABLE learning_events_y2025m01 PARTITION OF learning_events
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
CREATE TABLE learning_events_y2025m02 PARTITION OF learning_events
    FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');
CREATE TABLE learning_events_y2025m03 PARTITION OF learning_events
    FOR VALUES FROM ('2025-03-01') TO ('2025-04-01');
CREATE TABLE learning_events_y2025m04 PARTITION OF learning_events
    FOR VALUES FROM ('2025-04-01') TO ('2025-05-01');
CREATE TABLE learning_events_y2025m05 PARTITION OF learning_events
    FOR VALUES FROM ('2025-05-01') TO ('2025-06-01');
CREATE TABLE learning_events_y2025m06 PARTITION OF learning_events
    FOR VALUES FROM ('2025-06-01') TO ('2025-07-01');

-- Indexes for learning_events (applied to all partitions)
CREATE INDEX idx_learning_events_type_timestamp ON learning_events(event_type, timestamp);
CREATE INDEX idx_learning_events_entity ON learning_events(entity_type, entity_id);
CREATE INDEX idx_learning_events_user ON learning_events(user_id, timestamp);
CREATE INDEX idx_learning_events_session ON learning_events(session_id);
CREATE INDEX idx_learning_events_source ON learning_events(source_system, timestamp);
CREATE INDEX idx_learning_events_correlation ON learning_events(correlation_id);
CREATE INDEX idx_learning_events_data ON learning_events USING GIN(event_data);

-- System Performance Metrics Table (High-Frequency Time-Series)
CREATE TABLE system_performance_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_name VARCHAR(100) NOT NULL,
    metric_category VARCHAR(100), -- 'database', 'api', 'ml_model', 'user_experience', 'infrastructure'
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    value DECIMAL(15,6) NOT NULL,
    unit VARCHAR(50), -- 'ms', 'mb', 'percentage', 'count', 'bytes_per_second'
    tags JSONB, -- Key-value pairs for filtering and grouping
    source_component VARCHAR(100), -- Which system component generated this metric
    aggregation_level VARCHAR(50) DEFAULT 'raw', -- 'raw', 'minute', 'hour', 'day'
    host_name VARCHAR(255),
    environment VARCHAR(50), -- 'development', 'staging', 'production'
    metadata JSONB,
    
    CHECK (aggregation_level IN ('raw', 'minute', 'hour', 'day', 'week')),
    CHECK (environment IN ('development', 'staging', 'production', 'test'))
) PARTITION BY RANGE (timestamp);

-- Create daily partitions for system_performance_metrics
CREATE TABLE system_performance_metrics_y2025m01d01 PARTITION OF system_performance_metrics
    FOR VALUES FROM ('2025-01-01') TO ('2025-01-02');
CREATE TABLE system_performance_metrics_y2025m01d02 PARTITION OF system_performance_metrics
    FOR VALUES FROM ('2025-01-02') TO ('2025-01-03');
-- Continue creating daily partitions as needed...

-- Indexes for system_performance_metrics
CREATE INDEX idx_performance_metrics_name_timestamp ON system_performance_metrics(metric_name, timestamp);
CREATE INDEX idx_performance_metrics_category ON system_performance_metrics(metric_category, timestamp);
CREATE INDEX idx_performance_metrics_tags ON system_performance_metrics USING GIN(tags);
CREATE INDEX idx_performance_metrics_component ON system_performance_metrics(source_component, timestamp);
CREATE INDEX idx_performance_metrics_environment ON system_performance_metrics(environment, timestamp);

-- Query Performance Tracking Table
CREATE TABLE query_performance_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_hash VARCHAR(64) NOT NULL, -- Hash of the normalized query
    query_text TEXT,
    query_type VARCHAR(100), -- 'SELECT', 'INSERT', 'UPDATE', 'DELETE'
    table_names VARCHAR(255)[], -- Tables involved in the query
    execution_time_ms DECIMAL(10,3) NOT NULL,
    rows_examined BIGINT,
    rows_returned BIGINT,
    index_usage JSONB, -- Which indexes were used
    execution_plan JSONB, -- Query execution plan
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    user_id VARCHAR(255),
    application_name VARCHAR(100),
    database_name VARCHAR(100),
    slow_query BOOLEAN DEFAULT false, -- Flagged as slow query
    
    CHECK (execution_time_ms >= 0),
    CHECK (rows_examined >= 0),
    CHECK (rows_returned >= 0)
) PARTITION BY RANGE (timestamp);

-- Create weekly partitions for query_performance_logs
CREATE TABLE query_performance_logs_y2025w01 PARTITION OF query_performance_logs
    FOR VALUES FROM ('2025-01-01') TO ('2025-01-08');
CREATE TABLE query_performance_logs_y2025w02 PARTITION OF query_performance_logs
    FOR VALUES FROM ('2025-01-08') TO ('2025-01-15');
-- Continue creating weekly partitions...

-- Indexes for query_performance_logs
CREATE INDEX idx_query_performance_hash ON query_performance_logs(query_hash);
CREATE INDEX idx_query_performance_time ON query_performance_logs(execution_time_ms DESC);
CREATE INDEX idx_query_performance_timestamp ON query_performance_logs(timestamp);
CREATE INDEX idx_query_performance_slow ON query_performance_logs(slow_query, timestamp) WHERE slow_query = true;
CREATE INDEX idx_query_performance_tables ON query_performance_logs USING GIN(table_names);

-- Resource Utilization Tracking Table
CREATE TABLE resource_utilization (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resource_type VARCHAR(100) NOT NULL, -- 'cpu', 'memory', 'disk', 'network', 'gpu'
    host_name VARCHAR(255) NOT NULL,
    component_name VARCHAR(100), -- 'database', 'api_server', 'ml_worker', 'web_server'
    utilization_percentage DECIMAL(5,2), -- 0.00 to 100.00
    absolute_value DECIMAL(15,2), -- Absolute value in appropriate units
    unit VARCHAR(50), -- 'bytes', 'cores', 'mbps', 'iops'
    threshold_warning DECIMAL(5,2), -- Warning threshold
    threshold_critical DECIMAL(5,2), -- Critical threshold
    alert_triggered BOOLEAN DEFAULT false,
    metadata JSONB,
    
    CHECK (utilization_percentage >= 0.00 AND utilization_percentage <= 100.00),
    CHECK (absolute_value >= 0),
    CHECK (threshold_warning >= 0 AND threshold_warning <= 100),
    CHECK (threshold_critical >= 0 AND threshold_critical <= 100),
    CHECK (resource_type IN ('cpu', 'memory', 'disk', 'network', 'gpu', 'storage'))
) PARTITION BY RANGE (timestamp);

-- Create hourly partitions for resource_utilization (high frequency)
CREATE TABLE resource_utilization_y2025m01d01h00 PARTITION OF resource_utilization
    FOR VALUES FROM ('2025-01-01 00:00:00') TO ('2025-01-01 01:00:00');
-- Continue creating hourly partitions...

-- Indexes for resource_utilization
CREATE INDEX idx_resource_util_type_host ON resource_utilization(resource_type, host_name, timestamp);
CREATE INDEX idx_resource_util_component ON resource_utilization(component_name, timestamp);
CREATE INDEX idx_resource_util_alerts ON resource_utilization(alert_triggered, timestamp) WHERE alert_triggered = true;
CREATE INDEX idx_resource_util_utilization ON resource_utilization(utilization_percentage DESC);

-- Data Retention Policies Table
CREATE TABLE data_retention_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_name VARCHAR(255) NOT NULL UNIQUE,
    retention_period INTERVAL NOT NULL,
    archive_strategy VARCHAR(100), -- 'delete', 'archive_to_s3', 'compress', 'summarize'
    partition_strategy VARCHAR(100), -- 'monthly', 'weekly', 'daily', 'hourly'
    compression_enabled BOOLEAN DEFAULT false,
    last_cleanup TIMESTAMP WITH TIME ZONE,
    next_cleanup TIMESTAMP WITH TIME ZONE,
    cleanup_status VARCHAR(50) DEFAULT 'scheduled', -- 'scheduled', 'running', 'completed', 'failed'
    records_processed BIGINT DEFAULT 0,
    space_freed_mb DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CHECK (archive_strategy IN ('delete', 'archive_to_s3', 'compress', 'summarize')),
    CHECK (partition_strategy IN ('monthly', 'weekly', 'daily', 'hourly')),
    CHECK (cleanup_status IN ('scheduled', 'running', 'completed', 'failed', 'disabled'))
);

-- Indexes for data_retention_policies
CREATE INDEX idx_retention_policies_next_cleanup ON data_retention_policies(next_cleanup);
CREATE INDEX idx_retention_policies_status ON data_retention_policies(cleanup_status);

-- Capacity Planning Metrics Table
CREATE TABLE capacity_planning_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_date DATE NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    current_usage DECIMAL(15,2) NOT NULL,
    current_capacity DECIMAL(15,2) NOT NULL,
    utilization_percentage DECIMAL(5,2) NOT NULL,
    growth_rate_daily DECIMAL(8,4), -- Daily growth rate as percentage
    growth_rate_weekly DECIMAL(8,4), -- Weekly growth rate as percentage
    growth_rate_monthly DECIMAL(8,4), -- Monthly growth rate as percentage
    projected_capacity_needed_30d DECIMAL(15,2),
    projected_capacity_needed_90d DECIMAL(15,2),
    projected_capacity_needed_365d DECIMAL(15,2),
    capacity_threshold_warning DECIMAL(5,2) DEFAULT 80.00,
    capacity_threshold_critical DECIMAL(5,2) DEFAULT 90.00,
    recommendation JSONB, -- Capacity planning recommendations
    cost_projection JSONB, -- Cost projections for scaling
    
    UNIQUE(metric_date, resource_type),
    CHECK (current_usage >= 0),
    CHECK (current_capacity >= 0),
    CHECK (utilization_percentage >= 0.00 AND utilization_percentage <= 100.00),
    CHECK (capacity_threshold_warning >= 0 AND capacity_threshold_warning <= 100),
    CHECK (capacity_threshold_critical >= 0 AND capacity_threshold_critical <= 100)
);

-- Indexes for capacity_planning_metrics
CREATE INDEX idx_capacity_planning_date ON capacity_planning_metrics(metric_date);
CREATE INDEX idx_capacity_planning_resource ON capacity_planning_metrics(resource_type);
CREATE INDEX idx_capacity_planning_utilization ON capacity_planning_metrics(utilization_percentage DESC);

-- System Health Checks Table
CREATE TABLE system_health_checks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    check_name VARCHAR(255) NOT NULL,
    check_category VARCHAR(100), -- 'database', 'api', 'ml_pipeline', 'infrastructure'
    check_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(50) NOT NULL, -- 'healthy', 'warning', 'critical', 'unknown'
    response_time_ms INTEGER,
    check_details JSONB, -- Detailed check results
    error_message TEXT,
    remediation_suggestions JSONB,
    auto_remediation_attempted BOOLEAN DEFAULT false,
    auto_remediation_successful BOOLEAN,
    next_check_scheduled TIMESTAMP WITH TIME ZONE,
    check_frequency INTERVAL DEFAULT '5 minutes',
    
    CHECK (status IN ('healthy', 'warning', 'critical', 'unknown')),
    CHECK (response_time_ms >= 0)
);

-- Indexes for system_health_checks
CREATE INDEX idx_health_checks_name_timestamp ON system_health_checks(check_name, check_timestamp);
CREATE INDEX idx_health_checks_status ON system_health_checks(status, check_timestamp);
CREATE INDEX idx_health_checks_category ON system_health_checks(check_category);
CREATE INDEX idx_health_checks_next_scheduled ON system_health_checks(next_check_scheduled);

-- Performance Baselines Table
CREATE TABLE performance_baselines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    baseline_name VARCHAR(255) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    baseline_value DECIMAL(15,6) NOT NULL,
    baseline_unit VARCHAR(50),
    measurement_period INTERVAL, -- Period over which baseline was calculated
    confidence_interval_lower DECIMAL(15,6),
    confidence_interval_upper DECIMAL(15,6),
    sample_size INTEGER,
    baseline_date DATE NOT NULL,
    environment VARCHAR(50),
    conditions JSONB, -- Conditions under which baseline was established
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(baseline_name, metric_name, baseline_date),
    CHECK (sample_size > 0),
    CHECK (environment IN ('development', 'staging', 'production'))
);

-- Indexes for performance_baselines
CREATE INDEX idx_baselines_name_metric ON performance_baselines(baseline_name, metric_name);
CREATE INDEX idx_baselines_date ON performance_baselines(baseline_date);
CREATE INDEX idx_baselines_environment ON performance_baselines(environment);

-- Materialized Views for Analytics

-- Daily Learning Events Summary
CREATE MATERIALIZED VIEW daily_learning_metrics AS
SELECT 
    DATE(timestamp) as date,
    event_type,
    source_system,
    COUNT(*) as event_count,
    AVG(processing_time_ms) as avg_processing_time,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY processing_time_ms) as p95_processing_time,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY processing_time_ms) as p99_processing_time,
    SUM(event_size_bytes) as total_event_size_bytes,
    COUNT(DISTINCT user_id) as unique_users,
    COUNT(DISTINCT session_id) as unique_sessions
FROM learning_events
WHERE timestamp >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY DATE(timestamp), event_type, source_system;

CREATE UNIQUE INDEX idx_daily_learning_metrics ON daily_learning_metrics(date, event_type, source_system);

-- Hourly Performance Metrics Summary
CREATE MATERIALIZED VIEW hourly_performance_summary AS
SELECT 
    DATE_TRUNC('hour', timestamp) as hour,
    metric_category,
    metric_name,
    AVG(value) as avg_value,
    MIN(value) as min_value,
    MAX(value) as max_value,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY value) as p95_value,
    COUNT(*) as sample_count,
    STDDEV(value) as std_deviation
FROM system_performance_metrics
WHERE timestamp >= NOW() - INTERVAL '7 days'
GROUP BY DATE_TRUNC('hour', timestamp), metric_category, metric_name;

CREATE UNIQUE INDEX idx_hourly_performance_summary ON hourly_performance_summary(hour, metric_category, metric_name);

-- Query Performance Summary
CREATE MATERIALIZED VIEW query_performance_summary AS
SELECT 
    query_hash,
    query_type,
    table_names,
    COUNT(*) as execution_count,
    AVG(execution_time_ms) as avg_execution_time,
    MIN(execution_time_ms) as min_execution_time,
    MAX(execution_time_ms) as max_execution_time,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY execution_time_ms) as p95_execution_time,
    AVG(rows_examined) as avg_rows_examined,
    AVG(rows_returned) as avg_rows_returned,
    COUNT(*) FILTER (WHERE slow_query = true) as slow_query_count,
    MAX(timestamp) as last_execution
FROM query_performance_logs
WHERE timestamp >= NOW() - INTERVAL '7 days'
GROUP BY query_hash, query_type, table_names;

CREATE UNIQUE INDEX idx_query_performance_summary ON query_performance_summary(query_hash);

-- Functions for Maintenance and Optimization

-- Function to create monthly partition for learning_events
CREATE OR REPLACE FUNCTION create_monthly_partition(table_name TEXT, start_date DATE)
RETURNS VOID AS $$
DECLARE
    partition_name TEXT;
    end_date DATE;
BEGIN
    partition_name := table_name || '_y' || EXTRACT(YEAR FROM start_date) || 'm' || LPAD(EXTRACT(MONTH FROM start_date)::TEXT, 2, '0');
    end_date := start_date + INTERVAL '1 month';
    
    EXECUTE format('CREATE TABLE IF NOT EXISTS %I PARTITION OF %I FOR VALUES FROM (%L) TO (%L)',
                   partition_name, table_name, start_date, end_date);
    
    -- Create indexes on the new partition
    EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%s_timestamp ON %I(timestamp)', partition_name, partition_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%s_type_timestamp ON %I(event_type, timestamp)', partition_name, partition_name);
END;
$$ LANGUAGE plpgsql;

-- Function to cleanup old learning events
CREATE OR REPLACE FUNCTION cleanup_old_learning_events()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
    retention_days INTEGER := 730; -- 2 years
BEGIN
    -- Archive events older than retention period
    WITH archived_events AS (
        DELETE FROM learning_events 
        WHERE timestamp < NOW() - (retention_days || ' days')::INTERVAL
        RETURNING *
    )
    SELECT COUNT(*) INTO deleted_count FROM archived_events;
    
    -- Update retention policy record
    UPDATE data_retention_policies 
    SET last_cleanup = NOW(),
        records_processed = deleted_count
    WHERE table_name = 'learning_events';
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to refresh materialized views
CREATE OR REPLACE FUNCTION refresh_analytics_views()
RETURNS VOID AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY daily_learning_metrics;
    REFRESH MATERIALIZED VIEW CONCURRENTLY hourly_performance_summary;
    REFRESH MATERIALIZED VIEW CONCURRENTLY query_performance_summary;
END;
$$ LANGUAGE plpgsql;

-- Function to detect performance anomalies
CREATE OR REPLACE FUNCTION detect_performance_anomalies()
RETURNS TABLE(
    metric_name TEXT,
    current_value DECIMAL,
    baseline_value DECIMAL,
    deviation_percentage DECIMAL,
    severity VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        m.metric_name::TEXT,
        m.value as current_value,
        b.baseline_value,
        ((m.value - b.baseline_value) / b.baseline_value * 100) as deviation_percentage,
        CASE 
            WHEN ABS((m.value - b.baseline_value) / b.baseline_value) > 0.5 THEN 'critical'
            WHEN ABS((m.value - b.baseline_value) / b.baseline_value) > 0.3 THEN 'warning'
            ELSE 'normal'
        END::VARCHAR as severity
    FROM system_performance_metrics m
    JOIN performance_baselines b ON m.metric_name = b.metric_name
    WHERE m.timestamp >= NOW() - INTERVAL '1 hour'
    AND ABS((m.value - b.baseline_value) / b.baseline_value) > 0.2
    ORDER BY ABS((m.value - b.baseline_value) / b.baseline_value) DESC;
END;
$$ LANGUAGE plpgsql;

-- Scheduled Jobs using pg_cron

-- Cleanup old learning events (weekly)
SELECT cron.schedule('cleanup-learning-events', '0 2 * * 0', 'SELECT cleanup_old_learning_events();');

-- Refresh materialized views (every 15 minutes)
SELECT cron.schedule('refresh-analytics-views', '*/15 * * * *', 'SELECT refresh_analytics_views();');

-- Create next month's partitions (monthly on 1st)
SELECT cron.schedule('create-monthly-partitions', '0 0 1 * *', 
    'SELECT create_monthly_partition(''learning_events'', DATE_TRUNC(''month'', NOW() + INTERVAL ''1 month''));');

-- Update updated_at triggers
CREATE TRIGGER update_retention_policies_updated_at BEFORE UPDATE ON data_retention_policies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Comments for documentation
COMMENT ON TABLE learning_events IS 'Time-series log of all learning and analytics events';
COMMENT ON TABLE system_performance_metrics IS 'High-frequency system performance measurements';
COMMENT ON TABLE query_performance_logs IS 'Database query performance tracking and optimization';
COMMENT ON TABLE resource_utilization IS 'System resource usage monitoring and alerting';
COMMENT ON TABLE data_retention_policies IS 'Automated data lifecycle management policies';
COMMENT ON TABLE capacity_planning_metrics IS 'Capacity planning and growth projection data';
COMMENT ON TABLE system_health_checks IS 'Automated system health monitoring and checks';
COMMENT ON TABLE performance_baselines IS 'Performance baselines for anomaly detection';

