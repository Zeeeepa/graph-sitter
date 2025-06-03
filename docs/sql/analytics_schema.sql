-- OpenEvolve Analytics Database Schema
-- This schema supports the continuous learning analytics system

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Core evaluation results table
CREATE TABLE openevolve_evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    program_id UUID NOT NULL,
    evaluation_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    prompt_context JSONB NOT NULL,
    generated_code TEXT,
    evaluation_metrics JSONB NOT NULL,
    performance_score FLOAT CHECK (performance_score >= 0 AND performance_score <= 1),
    quality_score FLOAT CHECK (quality_score >= 0 AND quality_score <= 1),
    improvement_score FLOAT,
    evaluator_version VARCHAR(50),
    execution_time_ms INTEGER CHECK (execution_time_ms >= 0),
    success BOOLEAN DEFAULT TRUE,
    error_details TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for openevolve_evaluations
CREATE INDEX idx_openevolve_evaluations_program_timestamp ON openevolve_evaluations (program_id, evaluation_timestamp DESC);
CREATE INDEX idx_openevolve_evaluations_performance_score ON openevolve_evaluations (performance_score DESC) WHERE success = TRUE;
CREATE INDEX idx_openevolve_evaluations_improvement_score ON openevolve_evaluations (improvement_score DESC) WHERE improvement_score > 0;
CREATE INDEX idx_openevolve_evaluations_metrics_gin ON openevolve_evaluations USING GIN (evaluation_metrics);
CREATE INDEX idx_openevolve_evaluations_timestamp ON openevolve_evaluations (evaluation_timestamp DESC);

-- System performance metrics with partitioning
CREATE TABLE system_performance_metrics (
    id UUID DEFAULT gen_random_uuid(),
    component VARCHAR(100) NOT NULL,
    operation VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    duration_ms INTEGER NOT NULL CHECK (duration_ms >= 0),
    memory_usage_mb FLOAT CHECK (memory_usage_mb >= 0),
    cpu_usage_percent FLOAT CHECK (cpu_usage_percent >= 0 AND cpu_usage_percent <= 100),
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    context_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
) PARTITION BY RANGE (timestamp);

-- Create monthly partitions for performance metrics
CREATE TABLE system_performance_metrics_y2024m01 PARTITION OF system_performance_metrics
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE system_performance_metrics_y2024m02 PARTITION OF system_performance_metrics
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

CREATE TABLE system_performance_metrics_y2024m03 PARTITION OF system_performance_metrics
    FOR VALUES FROM ('2024-03-01') TO ('2024-04-01');

CREATE TABLE system_performance_metrics_y2024m04 PARTITION OF system_performance_metrics
    FOR VALUES FROM ('2024-04-01') TO ('2024-05-01');

CREATE TABLE system_performance_metrics_y2024m05 PARTITION OF system_performance_metrics
    FOR VALUES FROM ('2024-05-01') TO ('2024-06-01');

CREATE TABLE system_performance_metrics_y2024m06 PARTITION OF system_performance_metrics
    FOR VALUES FROM ('2024-06-01') TO ('2024-07-01');

CREATE TABLE system_performance_metrics_y2024m07 PARTITION OF system_performance_metrics
    FOR VALUES FROM ('2024-07-01') TO ('2024-08-01');

CREATE TABLE system_performance_metrics_y2024m08 PARTITION OF system_performance_metrics
    FOR VALUES FROM ('2024-08-01') TO ('2024-09-01');

CREATE TABLE system_performance_metrics_y2024m09 PARTITION OF system_performance_metrics
    FOR VALUES FROM ('2024-09-01') TO ('2024-10-01');

CREATE TABLE system_performance_metrics_y2024m10 PARTITION OF system_performance_metrics
    FOR VALUES FROM ('2024-10-01') TO ('2024-11-01');

CREATE TABLE system_performance_metrics_y2024m11 PARTITION OF system_performance_metrics
    FOR VALUES FROM ('2024-11-01') TO ('2024-12-01');

CREATE TABLE system_performance_metrics_y2024m12 PARTITION OF system_performance_metrics
    FOR VALUES FROM ('2024-12-01') TO ('2025-01-01');

-- Indexes for system_performance_metrics (applied to all partitions)
CREATE INDEX idx_system_perf_component_operation ON system_performance_metrics (component, operation);
CREATE INDEX idx_system_perf_timestamp_success ON system_performance_metrics (timestamp DESC, success);
CREATE INDEX idx_system_perf_duration_cpu ON system_performance_metrics (duration_ms, cpu_usage_percent);
CREATE INDEX idx_system_perf_context_gin ON system_performance_metrics USING GIN (context_data);

-- Learned patterns storage
CREATE TABLE learned_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_type VARCHAR(50) NOT NULL,
    pattern_name VARCHAR(200) NOT NULL,
    description TEXT,
    pattern_data JSONB NOT NULL,
    confidence_score FLOAT CHECK (confidence_score >= 0 AND confidence_score <= 1),
    improvement_potential FLOAT,
    frequency INTEGER DEFAULT 1 CHECK (frequency > 0),
    first_discovered TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_validated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    validation_count INTEGER DEFAULT 0 CHECK (validation_count >= 0),
    success_rate FLOAT DEFAULT 0 CHECK (success_rate >= 0 AND success_rate <= 1),
    impact_metrics JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for learned_patterns
CREATE INDEX idx_learned_patterns_type_confidence ON learned_patterns (pattern_type, confidence_score DESC);
CREATE INDEX idx_learned_patterns_last_validated ON learned_patterns (last_validated DESC);
CREATE INDEX idx_learned_patterns_active_confidence ON learned_patterns (is_active, confidence_score DESC) WHERE is_active = TRUE;
CREATE INDEX idx_learned_patterns_data_gin ON learned_patterns USING GIN (pattern_data);
CREATE UNIQUE INDEX idx_learned_patterns_name_type ON learned_patterns (pattern_name, pattern_type);

-- Program evolution tracking
CREATE TABLE program_evolution_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_program_id UUID,
    child_program_id UUID NOT NULL,
    evolution_type VARCHAR(50) NOT NULL,
    generation INTEGER NOT NULL CHECK (generation >= 0),
    evolution_strategy VARCHAR(100),
    improvement_metrics JSONB,
    evolution_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    validation_status VARCHAR(20) DEFAULT 'pending' CHECK (validation_status IN ('pending', 'validated', 'failed', 'rejected')),
    deployment_status VARCHAR(20) DEFAULT 'not_deployed' CHECK (deployment_status IN ('not_deployed', 'deployed', 'rolled_back', 'failed')),
    rollback_reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for program_evolution_history
CREATE INDEX idx_program_evolution_generation_time ON program_evolution_history (generation, evolution_timestamp DESC);
CREATE INDEX idx_program_evolution_parent_child ON program_evolution_history (parent_program_id, child_program_id);
CREATE INDEX idx_program_evolution_validation_deployment ON program_evolution_history (validation_status, deployment_status);
CREATE INDEX idx_program_evolution_type_generation ON program_evolution_history (evolution_type, generation);

-- Optimization suggestions
CREATE TABLE optimization_suggestions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    suggestion_type VARCHAR(50) NOT NULL,
    target_component VARCHAR(100) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    implementation_details JSONB,
    expected_improvement JSONB,
    confidence_score FLOAT CHECK (confidence_score >= 0 AND confidence_score <= 1),
    priority_score FLOAT CHECK (priority_score >= 0 AND priority_score <= 1),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'implemented', 'rejected', 'expired')),
    implemented_at TIMESTAMP WITH TIME ZONE,
    validation_results JSONB,
    created_by VARCHAR(100),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for optimization_suggestions
CREATE INDEX idx_optimization_suggestions_target_priority ON optimization_suggestions (target_component, priority_score DESC);
CREATE INDEX idx_optimization_suggestions_status_created ON optimization_suggestions (status, created_at DESC);
CREATE INDEX idx_optimization_suggestions_confidence_priority ON optimization_suggestions (confidence_score DESC, priority_score DESC);
CREATE INDEX idx_optimization_suggestions_type_status ON optimization_suggestions (suggestion_type, status);

-- Evolution cycles tracking
CREATE TABLE evolution_cycles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cycle_id VARCHAR(100) UNIQUE NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    end_time TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'running' CHECK (status IN ('running', 'completed', 'failed', 'cancelled')),
    codebase_context JSONB,
    metrics_collected JSONB,
    patterns_found INTEGER DEFAULT 0,
    improvements_suggested INTEGER DEFAULT 0,
    evaluations_completed INTEGER DEFAULT 0,
    performance_impact_percent FLOAT,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for evolution_cycles
CREATE INDEX idx_evolution_cycles_status_start ON evolution_cycles (status, start_time DESC);
CREATE INDEX idx_evolution_cycles_cycle_id ON evolution_cycles (cycle_id);
CREATE INDEX idx_evolution_cycles_performance_impact ON evolution_cycles (performance_impact_percent) WHERE performance_impact_percent IS NOT NULL;

-- System health metrics
CREATE TABLE system_health_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    component VARCHAR(100) NOT NULL,
    health_status VARCHAR(20) NOT NULL CHECK (health_status IN ('healthy', 'degraded', 'unhealthy')),
    metrics JSONB NOT NULL,
    alerts JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for system_health_metrics
CREATE INDEX idx_system_health_timestamp ON system_health_metrics (timestamp DESC);
CREATE INDEX idx_system_health_component_status ON system_health_metrics (component, health_status);
CREATE INDEX idx_system_health_status_timestamp ON system_health_metrics (health_status, timestamp DESC);

-- Views for common queries
CREATE VIEW performance_summary AS
SELECT 
    component,
    operation,
    DATE_TRUNC('hour', timestamp) as hour,
    COUNT(*) as operation_count,
    AVG(duration_ms) as avg_duration_ms,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY duration_ms) as median_duration_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_ms) as p95_duration_ms,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY duration_ms) as p99_duration_ms,
    AVG(memory_usage_mb) as avg_memory_mb,
    MAX(memory_usage_mb) as max_memory_mb,
    AVG(cpu_usage_percent) as avg_cpu_percent,
    MAX(cpu_usage_percent) as max_cpu_percent,
    SUM(CASE WHEN success THEN 1 ELSE 0 END)::FLOAT / COUNT(*) as success_rate
FROM system_performance_metrics
WHERE timestamp >= NOW() - INTERVAL '7 days'
GROUP BY component, operation, DATE_TRUNC('hour', timestamp)
ORDER BY hour DESC, component, operation;

CREATE VIEW top_optimization_opportunities AS
SELECT 
    suggestion_type,
    target_component,
    title,
    description,
    expected_improvement,
    confidence_score,
    priority_score,
    created_at
FROM optimization_suggestions
WHERE status = 'pending'
    AND confidence_score > 0.7
    AND created_at >= NOW() - INTERVAL '30 days'
ORDER BY priority_score DESC, confidence_score DESC
LIMIT 20;

CREATE VIEW recent_evolution_cycles AS
SELECT 
    cycle_id,
    start_time,
    end_time,
    status,
    patterns_found,
    improvements_suggested,
    evaluations_completed,
    performance_impact_percent,
    EXTRACT(EPOCH FROM (COALESCE(end_time, NOW()) - start_time)) as duration_seconds
FROM evolution_cycles
WHERE start_time >= NOW() - INTERVAL '30 days'
ORDER BY start_time DESC;

CREATE VIEW pattern_effectiveness AS
SELECT 
    p.pattern_type,
    p.pattern_name,
    p.confidence_score,
    p.success_rate,
    p.validation_count,
    p.frequency,
    COUNT(s.id) as suggestions_generated,
    COUNT(CASE WHEN s.status = 'implemented' THEN 1 END) as suggestions_implemented
FROM learned_patterns p
LEFT JOIN optimization_suggestions s ON s.description LIKE '%' || p.pattern_name || '%'
WHERE p.is_active = TRUE
GROUP BY p.id, p.pattern_type, p.pattern_name, p.confidence_score, p.success_rate, p.validation_count, p.frequency
ORDER BY p.confidence_score DESC, p.success_rate DESC;

-- Functions for maintenance and utilities
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for automatic updated_at timestamps
CREATE TRIGGER update_openevolve_evaluations_updated_at BEFORE UPDATE ON openevolve_evaluations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_learned_patterns_updated_at BEFORE UPDATE ON learned_patterns FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_program_evolution_updated_at BEFORE UPDATE ON program_evolution_history FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_optimization_suggestions_updated_at BEFORE UPDATE ON optimization_suggestions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_evolution_cycles_updated_at BEFORE UPDATE ON evolution_cycles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to create new monthly partitions
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
    EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I (component, operation)', 
                   'idx_' || partition_name || '_component_operation', partition_name);
    EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I (timestamp DESC, success)', 
                   'idx_' || partition_name || '_timestamp_success', partition_name);
END;
$$ LANGUAGE plpgsql;

-- Function to clean up old data
CREATE OR REPLACE FUNCTION cleanup_old_data(retention_days INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER := 0;
    temp_count INTEGER;
BEGIN
    -- Clean up old performance metrics
    DELETE FROM system_performance_metrics 
    WHERE timestamp < NOW() - (retention_days || ' days')::INTERVAL;
    GET DIAGNOSTICS temp_count = ROW_COUNT;
    deleted_count := deleted_count + temp_count;
    
    -- Clean up old evaluation results (longer retention)
    DELETE FROM openevolve_evaluations 
    WHERE evaluation_timestamp < NOW() - ((retention_days * 2) || ' days')::INTERVAL;
    GET DIAGNOSTICS temp_count = ROW_COUNT;
    deleted_count := deleted_count + temp_count;
    
    -- Clean up old health metrics
    DELETE FROM system_health_metrics 
    WHERE timestamp < NOW() - (retention_days || ' days')::INTERVAL;
    GET DIAGNOSTICS temp_count = ROW_COUNT;
    deleted_count := deleted_count + temp_count;
    
    -- Clean up expired suggestions
    UPDATE optimization_suggestions 
    SET status = 'expired' 
    WHERE status = 'pending' 
    AND created_at < NOW() - '30 days'::INTERVAL;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to get system performance summary
CREATE OR REPLACE FUNCTION get_performance_summary(hours_back INTEGER DEFAULT 24)
RETURNS TABLE (
    component TEXT,
    operation TEXT,
    avg_duration_ms NUMERIC,
    p95_duration_ms NUMERIC,
    success_rate NUMERIC,
    total_operations BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        spm.component::TEXT,
        spm.operation::TEXT,
        ROUND(AVG(spm.duration_ms)::NUMERIC, 2) as avg_duration_ms,
        ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY spm.duration_ms)::NUMERIC, 2) as p95_duration_ms,
        ROUND((SUM(CASE WHEN spm.success THEN 1 ELSE 0 END)::FLOAT / COUNT(*))::NUMERIC, 4) as success_rate,
        COUNT(*) as total_operations
    FROM system_performance_metrics spm
    WHERE spm.timestamp >= NOW() - (hours_back || ' hours')::INTERVAL
    GROUP BY spm.component, spm.operation
    ORDER BY total_operations DESC;
END;
$$ LANGUAGE plpgsql;

-- Initial data for testing (optional)
INSERT INTO learned_patterns (pattern_type, pattern_name, description, pattern_data, confidence_score, improvement_potential) VALUES
('performance', 'slow_codebase_analysis', 'Codebase analysis operations taking longer than expected', '{"avg_duration_threshold": 5000, "components": ["graph_sitter.codebase"]}', 0.85, 0.3),
('reliability', 'high_failure_rate_imports', 'Import resolution failing frequently', '{"failure_rate_threshold": 0.1, "components": ["import_resolution"]}', 0.92, 0.4),
('optimization', 'memory_usage_spike', 'Memory usage spikes during large file processing', '{"memory_threshold_mb": 1024, "file_size_threshold": 10000}', 0.78, 0.25);

-- Create initial optimization suggestions
INSERT INTO optimization_suggestions (suggestion_type, target_component, title, description, expected_improvement, confidence_score, priority_score) VALUES
('performance', 'graph_sitter.codebase', 'Optimize codebase analysis caching', 'Implement intelligent caching for frequently analyzed code patterns', '{"performance_improvement": 0.3, "memory_reduction": 0.15}', 0.85, 0.9),
('reliability', 'import_resolution', 'Improve import resolution error handling', 'Add retry logic and better error recovery for import resolution', '{"reliability_improvement": 0.4, "error_reduction": 0.6}', 0.92, 0.8),
('scalability', 'evaluation_pool', 'Implement dynamic evaluation scaling', 'Auto-scale evaluation pool based on workload', '{"throughput_improvement": 0.5, "resource_efficiency": 0.3}', 0.75, 0.7);

-- Grant permissions (adjust as needed for your setup)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO openevolve_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO openevolve_user;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO openevolve_user;

-- Create a maintenance schedule (example using pg_cron if available)
-- SELECT cron.schedule('cleanup-old-data', '0 2 * * *', 'SELECT cleanup_old_data(90);');
-- SELECT cron.schedule('create-next-partition', '0 0 1 * *', 'SELECT create_monthly_partition(''system_performance_metrics'', DATE_TRUNC(''month'', NOW() + INTERVAL ''1 month''));');

COMMIT;

