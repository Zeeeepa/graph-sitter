-- analysis_metrics.sql
-- SQL schema for storing Graph-Sitter code metrics and statistics

-- Main table for storing code metrics at various levels
CREATE TABLE code_metrics (
    id BIGSERIAL PRIMARY KEY,
    codebase_id VARCHAR(255) NOT NULL,
    metric_scope VARCHAR(100) NOT NULL, -- 'codebase', 'module', 'file', 'class', 'function', 'method'
    scope_identifier TEXT NOT NULL, -- ID, path, or name of the scope
    symbol_id BIGINT REFERENCES symbols(id) ON DELETE CASCADE, -- For symbol-level metrics
    metric_name VARCHAR(200) NOT NULL,
    metric_value DECIMAL(15,6) NOT NULL,
    metric_unit VARCHAR(50), -- 'lines', 'count', 'percentage', 'ratio', 'score'
    metric_category VARCHAR(100) NOT NULL, -- 'complexity', 'size', 'quality', 'maintainability', 'performance'
    calculation_method VARCHAR(200), -- How the metric was calculated
    baseline_value DECIMAL(15,6), -- Baseline or previous value for comparison
    threshold_warning DECIMAL(15,6), -- Warning threshold
    threshold_critical DECIMAL(15,6), -- Critical threshold
    is_derived BOOLEAN DEFAULT FALSE, -- Whether this metric is calculated from other metrics
    source_metrics TEXT[], -- Array of metric names this is derived from
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    valid_until TIMESTAMP WITH TIME ZONE, -- When this metric expires
    metadata JSONB, -- Additional metadata about the metric
    INDEX(codebase_id, metric_scope, metric_name)
);

-- Table for storing complexity metrics
CREATE TABLE complexity_metrics (
    id BIGSERIAL PRIMARY KEY,
    codebase_id VARCHAR(255) NOT NULL,
    symbol_id BIGINT NOT NULL REFERENCES symbols(id) ON DELETE CASCADE,
    cyclomatic_complexity INTEGER DEFAULT 0,
    cognitive_complexity INTEGER DEFAULT 0,
    npath_complexity BIGINT DEFAULT 0,
    halstead_difficulty DECIMAL(10,4) DEFAULT 0.0,
    halstead_effort DECIMAL(15,6) DEFAULT 0.0,
    halstead_volume DECIMAL(15,6) DEFAULT 0.0,
    maintainability_index DECIMAL(5,2) DEFAULT 0.0,
    nested_depth INTEGER DEFAULT 0,
    parameter_count INTEGER DEFAULT 0,
    return_statement_count INTEGER DEFAULT 0,
    branch_count INTEGER DEFAULT 0,
    loop_count INTEGER DEFAULT 0,
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for storing size and volume metrics
CREATE TABLE size_metrics (
    id BIGSERIAL PRIMARY KEY,
    codebase_id VARCHAR(255) NOT NULL,
    scope_type VARCHAR(100) NOT NULL, -- 'codebase', 'module', 'file', 'class', 'function'
    scope_identifier TEXT NOT NULL,
    symbol_id BIGINT REFERENCES symbols(id) ON DELETE CASCADE,
    lines_of_code INTEGER DEFAULT 0,
    physical_lines INTEGER DEFAULT 0,
    comment_lines INTEGER DEFAULT 0,
    blank_lines INTEGER DEFAULT 0,
    executable_statements INTEGER DEFAULT 0,
    function_count INTEGER DEFAULT 0,
    class_count INTEGER DEFAULT 0,
    method_count INTEGER DEFAULT 0,
    variable_count INTEGER DEFAULT 0,
    import_count INTEGER DEFAULT 0,
    export_count INTEGER DEFAULT 0,
    file_size_bytes BIGINT DEFAULT 0,
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(codebase_id, scope_type, scope_identifier)
);

-- Table for storing quality metrics
CREATE TABLE quality_metrics (
    id BIGSERIAL PRIMARY KEY,
    codebase_id VARCHAR(255) NOT NULL,
    scope_type VARCHAR(100) NOT NULL,
    scope_identifier TEXT NOT NULL,
    symbol_id BIGINT REFERENCES symbols(id) ON DELETE CASCADE,
    test_coverage_percentage DECIMAL(5,2) DEFAULT 0.0,
    documentation_coverage_percentage DECIMAL(5,2) DEFAULT 0.0,
    type_annotation_coverage_percentage DECIMAL(5,2) DEFAULT 0.0,
    code_duplication_percentage DECIMAL(5,2) DEFAULT 0.0,
    technical_debt_ratio DECIMAL(5,2) DEFAULT 0.0,
    bug_density DECIMAL(10,6) DEFAULT 0.0, -- Bugs per KLOC
    vulnerability_count INTEGER DEFAULT 0,
    code_smell_count INTEGER DEFAULT 0,
    warning_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(codebase_id, scope_type, scope_identifier)
);

-- Table for storing maintainability metrics
CREATE TABLE maintainability_metrics (
    id BIGSERIAL PRIMARY KEY,
    codebase_id VARCHAR(255) NOT NULL,
    symbol_id BIGINT NOT NULL REFERENCES symbols(id) ON DELETE CASCADE,
    coupling_factor DECIMAL(5,2) DEFAULT 0.0, -- 0.0 to 1.0
    cohesion_factor DECIMAL(5,2) DEFAULT 0.0, -- 0.0 to 1.0
    instability DECIMAL(5,2) DEFAULT 0.0, -- 0.0 to 1.0
    abstractness DECIMAL(5,2) DEFAULT 0.0, -- 0.0 to 1.0
    distance_from_main_sequence DECIMAL(5,2) DEFAULT 0.0,
    change_frequency DECIMAL(10,6) DEFAULT 0.0, -- Changes per time period
    defect_density DECIMAL(10,6) DEFAULT 0.0, -- Defects per KLOC
    modification_complexity DECIMAL(5,2) DEFAULT 0.0,
    readability_score DECIMAL(5,2) DEFAULT 0.0,
    reusability_score DECIMAL(5,2) DEFAULT 0.0,
    testability_score DECIMAL(5,2) DEFAULT 0.0,
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for storing performance metrics
CREATE TABLE performance_metrics (
    id BIGSERIAL PRIMARY KEY,
    codebase_id VARCHAR(255) NOT NULL,
    symbol_id BIGINT REFERENCES symbols(id) ON DELETE CASCADE,
    scope_identifier TEXT NOT NULL,
    execution_time_ms DECIMAL(15,6) DEFAULT 0.0,
    memory_usage_bytes BIGINT DEFAULT 0,
    cpu_usage_percentage DECIMAL(5,2) DEFAULT 0.0,
    io_operations_count INTEGER DEFAULT 0,
    network_calls_count INTEGER DEFAULT 0,
    database_queries_count INTEGER DEFAULT 0,
    cache_hit_ratio DECIMAL(5,2) DEFAULT 0.0,
    throughput_ops_per_second DECIMAL(15,6) DEFAULT 0.0,
    latency_percentile_95 DECIMAL(15,6) DEFAULT 0.0,
    error_rate_percentage DECIMAL(5,2) DEFAULT 0.0,
    profiling_session_id VARCHAR(255),
    measured_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for storing metric trends and historical data
CREATE TABLE metric_trends (
    id BIGSERIAL PRIMARY KEY,
    codebase_id VARCHAR(255) NOT NULL,
    metric_name VARCHAR(200) NOT NULL,
    scope_type VARCHAR(100) NOT NULL,
    scope_identifier TEXT NOT NULL,
    measurement_date DATE NOT NULL,
    metric_value DECIMAL(15,6) NOT NULL,
    previous_value DECIMAL(15,6),
    change_amount DECIMAL(15,6),
    change_percentage DECIMAL(5,2),
    trend_direction VARCHAR(20), -- 'increasing', 'decreasing', 'stable'
    is_anomaly BOOLEAN DEFAULT FALSE,
    anomaly_score DECIMAL(5,2), -- Statistical anomaly score
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(codebase_id, metric_name, scope_type, scope_identifier, measurement_date)
);

-- Table for storing metric thresholds and rules
CREATE TABLE metric_thresholds (
    id BIGSERIAL PRIMARY KEY,
    metric_name VARCHAR(200) NOT NULL,
    scope_type VARCHAR(100) NOT NULL,
    language VARCHAR(50),
    warning_threshold DECIMAL(15,6),
    critical_threshold DECIMAL(15,6),
    optimal_range_min DECIMAL(15,6),
    optimal_range_max DECIMAL(15,6),
    threshold_type VARCHAR(50) NOT NULL, -- 'upper_bound', 'lower_bound', 'range'
    description TEXT,
    rationale TEXT,
    created_by VARCHAR(200),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for storing metric violations and alerts
CREATE TABLE metric_violations (
    id BIGSERIAL PRIMARY KEY,
    codebase_id VARCHAR(255) NOT NULL,
    metric_id BIGINT REFERENCES code_metrics(id) ON DELETE CASCADE,
    threshold_id BIGINT REFERENCES metric_thresholds(id) ON DELETE CASCADE,
    violation_type VARCHAR(50) NOT NULL, -- 'warning', 'critical', 'out_of_range'
    current_value DECIMAL(15,6) NOT NULL,
    threshold_value DECIMAL(15,6) NOT NULL,
    severity VARCHAR(50) NOT NULL, -- 'low', 'medium', 'high', 'critical'
    is_resolved BOOLEAN DEFAULT FALSE,
    resolution_notes TEXT,
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by VARCHAR(200)
);

-- Table for storing aggregated metrics summaries
CREATE TABLE metric_summaries (
    id BIGSERIAL PRIMARY KEY,
    codebase_id VARCHAR(255) NOT NULL,
    summary_type VARCHAR(100) NOT NULL, -- 'daily', 'weekly', 'monthly', 'release'
    summary_date DATE NOT NULL,
    total_files INTEGER DEFAULT 0,
    total_functions INTEGER DEFAULT 0,
    total_classes INTEGER DEFAULT 0,
    total_lines_of_code INTEGER DEFAULT 0,
    average_complexity DECIMAL(5,2) DEFAULT 0.0,
    max_complexity INTEGER DEFAULT 0,
    high_complexity_functions INTEGER DEFAULT 0,
    test_coverage_percentage DECIMAL(5,2) DEFAULT 0.0,
    documentation_coverage_percentage DECIMAL(5,2) DEFAULT 0.0,
    technical_debt_hours DECIMAL(10,2) DEFAULT 0.0,
    code_smell_count INTEGER DEFAULT 0,
    vulnerability_count INTEGER DEFAULT 0,
    duplication_percentage DECIMAL(5,2) DEFAULT 0.0,
    maintainability_score DECIMAL(5,2) DEFAULT 0.0,
    quality_gate_status VARCHAR(50) DEFAULT 'unknown', -- 'passed', 'failed', 'warning'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(codebase_id, summary_type, summary_date)
);

-- Indexes for performance optimization
CREATE INDEX idx_code_metrics_codebase_scope ON code_metrics(codebase_id, metric_scope);
CREATE INDEX idx_code_metrics_name ON code_metrics(metric_name);
CREATE INDEX idx_code_metrics_category ON code_metrics(metric_category);
CREATE INDEX idx_code_metrics_symbol ON code_metrics(symbol_id);
CREATE INDEX idx_code_metrics_calculated_at ON code_metrics(calculated_at);

CREATE INDEX idx_complexity_metrics_codebase ON complexity_metrics(codebase_id);
CREATE INDEX idx_complexity_metrics_symbol ON complexity_metrics(symbol_id);
CREATE INDEX idx_complexity_metrics_cyclomatic ON complexity_metrics(cyclomatic_complexity);
CREATE INDEX idx_complexity_metrics_cognitive ON complexity_metrics(cognitive_complexity);

CREATE INDEX idx_size_metrics_codebase_scope ON size_metrics(codebase_id, scope_type);
CREATE INDEX idx_size_metrics_symbol ON size_metrics(symbol_id);
CREATE INDEX idx_size_metrics_loc ON size_metrics(lines_of_code);

CREATE INDEX idx_quality_metrics_codebase_scope ON quality_metrics(codebase_id, scope_type);
CREATE INDEX idx_quality_metrics_symbol ON quality_metrics(symbol_id);
CREATE INDEX idx_quality_metrics_coverage ON quality_metrics(test_coverage_percentage);

CREATE INDEX idx_maintainability_metrics_symbol ON maintainability_metrics(symbol_id);
CREATE INDEX idx_maintainability_metrics_coupling ON maintainability_metrics(coupling_factor);
CREATE INDEX idx_maintainability_metrics_instability ON maintainability_metrics(instability);

CREATE INDEX idx_performance_metrics_symbol ON performance_metrics(symbol_id);
CREATE INDEX idx_performance_metrics_session ON performance_metrics(profiling_session_id);
CREATE INDEX idx_performance_metrics_measured_at ON performance_metrics(measured_at);

CREATE INDEX idx_metric_trends_codebase_metric ON metric_trends(codebase_id, metric_name);
CREATE INDEX idx_metric_trends_date ON metric_trends(measurement_date);
CREATE INDEX idx_metric_trends_direction ON metric_trends(trend_direction);
CREATE INDEX idx_metric_trends_anomaly ON metric_trends(is_anomaly) WHERE is_anomaly = TRUE;

CREATE INDEX idx_metric_violations_codebase ON metric_violations(codebase_id);
CREATE INDEX idx_metric_violations_severity ON metric_violations(severity);
CREATE INDEX idx_metric_violations_resolved ON metric_violations(is_resolved);

-- Views for common metric queries
CREATE VIEW v_codebase_health_summary AS
SELECT 
    cm.codebase_id,
    AVG(CASE WHEN cm.metric_name = 'cyclomatic_complexity' THEN cm.metric_value END) as avg_complexity,
    MAX(CASE WHEN cm.metric_name = 'cyclomatic_complexity' THEN cm.metric_value END) as max_complexity,
    AVG(CASE WHEN cm.metric_name = 'test_coverage' THEN cm.metric_value END) as avg_test_coverage,
    AVG(CASE WHEN cm.metric_name = 'maintainability_index' THEN cm.metric_value END) as avg_maintainability,
    COUNT(mv.id) FILTER (WHERE mv.severity = 'critical') as critical_violations,
    COUNT(mv.id) FILTER (WHERE mv.severity = 'high') as high_violations
FROM code_metrics cm
LEFT JOIN metric_violations mv ON cm.codebase_id = mv.codebase_id AND mv.is_resolved = FALSE
GROUP BY cm.codebase_id;

CREATE VIEW v_high_complexity_functions AS
SELECT 
    s.id,
    s.name,
    s.qualified_name,
    s.file_path,
    cm.cyclomatic_complexity,
    cm.cognitive_complexity,
    cm.maintainability_index
FROM symbols s
INNER JOIN complexity_metrics cm ON s.id = cm.symbol_id
WHERE s.symbol_type IN ('function', 'method')
AND cm.cyclomatic_complexity > 10
ORDER BY cm.cyclomatic_complexity DESC;

CREATE VIEW v_metric_trend_analysis AS
SELECT 
    mt.codebase_id,
    mt.metric_name,
    mt.scope_type,
    COUNT(*) as measurement_count,
    AVG(mt.metric_value) as avg_value,
    STDDEV(mt.metric_value) as value_stddev,
    MIN(mt.metric_value) as min_value,
    MAX(mt.metric_value) as max_value,
    COUNT(*) FILTER (WHERE mt.trend_direction = 'increasing') as increasing_count,
    COUNT(*) FILTER (WHERE mt.trend_direction = 'decreasing') as decreasing_count,
    COUNT(*) FILTER (WHERE mt.is_anomaly = TRUE) as anomaly_count
FROM metric_trends mt
WHERE mt.measurement_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY mt.codebase_id, mt.metric_name, mt.scope_type;

-- Functions for metric calculations
CREATE OR REPLACE FUNCTION calculate_maintainability_index(
    p_cyclomatic_complexity INTEGER,
    p_lines_of_code INTEGER,
    p_halstead_volume DECIMAL(15,6),
    p_comment_percentage DECIMAL(5,2)
)
RETURNS DECIMAL(5,2) AS $$
DECLARE
    v_mi DECIMAL(5,2);
BEGIN
    -- Microsoft's Maintainability Index formula
    v_mi := 171 - 5.2 * LN(p_halstead_volume) - 0.23 * p_cyclomatic_complexity - 16.2 * LN(p_lines_of_code) + 50 * SIN(SQRT(2.4 * p_comment_percentage));
    
    -- Normalize to 0-100 scale
    v_mi := GREATEST(0, LEAST(100, v_mi));
    
    RETURN v_mi;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION calculate_technical_debt_hours(
    p_codebase_id VARCHAR(255)
)
RETURNS DECIMAL(10,2) AS $$
DECLARE
    v_debt_hours DECIMAL(10,2) := 0.0;
    v_complexity_debt DECIMAL(10,2);
    v_duplication_debt DECIMAL(10,2);
    v_coverage_debt DECIMAL(10,2);
BEGIN
    -- Calculate debt from high complexity
    SELECT COALESCE(SUM(
        CASE 
            WHEN cm.cyclomatic_complexity > 20 THEN (cm.cyclomatic_complexity - 20) * 0.5
            WHEN cm.cyclomatic_complexity > 10 THEN (cm.cyclomatic_complexity - 10) * 0.25
            ELSE 0
        END
    ), 0) INTO v_complexity_debt
    FROM complexity_metrics cm
    WHERE cm.codebase_id = p_codebase_id;
    
    -- Calculate debt from code duplication
    SELECT COALESCE(SUM(
        CASE 
            WHEN qm.code_duplication_percentage > 10 THEN 
                (qm.code_duplication_percentage - 10) * sm.lines_of_code * 0.001
            ELSE 0
        END
    ), 0) INTO v_duplication_debt
    FROM quality_metrics qm
    INNER JOIN size_metrics sm ON qm.codebase_id = sm.codebase_id 
        AND qm.scope_identifier = sm.scope_identifier
    WHERE qm.codebase_id = p_codebase_id;
    
    -- Calculate debt from low test coverage
    SELECT COALESCE(SUM(
        CASE 
            WHEN qm.test_coverage_percentage < 80 THEN 
                (80 - qm.test_coverage_percentage) * sm.lines_of_code * 0.002
            ELSE 0
        END
    ), 0) INTO v_coverage_debt
    FROM quality_metrics qm
    INNER JOIN size_metrics sm ON qm.codebase_id = sm.codebase_id 
        AND qm.scope_identifier = sm.scope_identifier
    WHERE qm.codebase_id = p_codebase_id;
    
    v_debt_hours := v_complexity_debt + v_duplication_debt + v_coverage_debt;
    
    RETURN v_debt_hours;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION detect_metric_anomalies(
    p_codebase_id VARCHAR(255),
    p_metric_name VARCHAR(200),
    p_lookback_days INTEGER DEFAULT 30
)
RETURNS TABLE(
    measurement_date DATE,
    metric_value DECIMAL(15,6),
    anomaly_score DECIMAL(5,2),
    is_anomaly BOOLEAN
) AS $$
DECLARE
    v_mean DECIMAL(15,6);
    v_stddev DECIMAL(15,6);
    v_threshold DECIMAL(5,2) := 2.0; -- Z-score threshold
BEGIN
    -- Calculate mean and standard deviation
    SELECT AVG(mt.metric_value), STDDEV(mt.metric_value)
    INTO v_mean, v_stddev
    FROM metric_trends mt
    WHERE mt.codebase_id = p_codebase_id
    AND mt.metric_name = p_metric_name
    AND mt.measurement_date >= CURRENT_DATE - INTERVAL '1 day' * p_lookback_days;
    
    -- Return anomaly analysis
    RETURN QUERY
    SELECT 
        mt.measurement_date,
        mt.metric_value,
        CASE 
            WHEN v_stddev > 0 THEN ABS(mt.metric_value - v_mean) / v_stddev
            ELSE 0.0
        END::DECIMAL(5,2) as anomaly_score,
        CASE 
            WHEN v_stddev > 0 AND ABS(mt.metric_value - v_mean) / v_stddev > v_threshold THEN TRUE
            ELSE FALSE
        END as is_anomaly
    FROM metric_trends mt
    WHERE mt.codebase_id = p_codebase_id
    AND mt.metric_name = p_metric_name
    AND mt.measurement_date >= CURRENT_DATE - INTERVAL '1 day' * p_lookback_days
    ORDER BY mt.measurement_date;
END;
$$ LANGUAGE plpgsql;

-- Triggers for maintaining metric data
CREATE OR REPLACE FUNCTION update_metric_trends_trigger()
RETURNS TRIGGER AS $$
BEGIN
    -- Insert or update trend data
    INSERT INTO metric_trends (
        codebase_id, metric_name, scope_type, scope_identifier,
        measurement_date, metric_value
    )
    VALUES (
        NEW.codebase_id, NEW.metric_name, NEW.metric_scope, NEW.scope_identifier,
        CURRENT_DATE, NEW.metric_value
    )
    ON CONFLICT (codebase_id, metric_name, scope_type, scope_identifier, measurement_date)
    DO UPDATE SET
        metric_value = EXCLUDED.metric_value,
        previous_value = metric_trends.metric_value,
        change_amount = EXCLUDED.metric_value - metric_trends.metric_value,
        change_percentage = CASE 
            WHEN metric_trends.metric_value != 0 THEN 
                ((EXCLUDED.metric_value - metric_trends.metric_value) / metric_trends.metric_value) * 100
            ELSE 0
        END,
        trend_direction = CASE 
            WHEN EXCLUDED.metric_value > metric_trends.metric_value THEN 'increasing'
            WHEN EXCLUDED.metric_value < metric_trends.metric_value THEN 'decreasing'
            ELSE 'stable'
        END;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER code_metrics_update_trends
    AFTER INSERT OR UPDATE ON code_metrics
    FOR EACH ROW
    EXECUTE FUNCTION update_metric_trends_trigger();

-- Comments for documentation
COMMENT ON TABLE code_metrics IS 'Stores various code metrics at different scopes (codebase, file, function, etc.)';
COMMENT ON TABLE complexity_metrics IS 'Stores complexity metrics for functions and methods';
COMMENT ON TABLE size_metrics IS 'Stores size and volume metrics for different code scopes';
COMMENT ON TABLE quality_metrics IS 'Stores quality-related metrics like test coverage and technical debt';
COMMENT ON TABLE maintainability_metrics IS 'Stores maintainability metrics for symbols';
COMMENT ON TABLE performance_metrics IS 'Stores performance metrics from profiling and monitoring';
COMMENT ON TABLE metric_trends IS 'Stores historical trends and changes in metrics over time';
COMMENT ON TABLE metric_thresholds IS 'Stores threshold values and rules for metric violations';
COMMENT ON TABLE metric_violations IS 'Stores detected violations of metric thresholds';
COMMENT ON TABLE metric_summaries IS 'Stores aggregated metric summaries for reporting';

COMMENT ON COLUMN code_metrics.is_derived IS 'Whether this metric is calculated from other metrics';
COMMENT ON COLUMN metric_trends.anomaly_score IS 'Statistical anomaly score based on historical data';
COMMENT ON COLUMN maintainability_metrics.distance_from_main_sequence IS 'Distance from the main sequence in Martin metrics';

