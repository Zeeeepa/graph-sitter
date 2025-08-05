-- Self-Healing Architecture Database Schema Extensions
-- Migration: 001_self_healing_schema.sql
-- Date: June 1, 2025
-- Description: Core tables for error tracking, recovery actions, and system metrics

-- Create custom types
CREATE TYPE error_severity_enum AS ENUM ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO');
CREATE TYPE error_category_enum AS ENUM ('AUTHENTICATION', 'DATABASE', 'API', 'PERFORMANCE', 'INTEGRATION', 'RESOURCE', 'CONFIGURATION', 'NETWORK');
CREATE TYPE risk_level_enum AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL');
CREATE TYPE execution_status_enum AS ENUM ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED');

-- Error Events Table
CREATE TABLE error_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    severity error_severity_enum NOT NULL,
    category error_category_enum NOT NULL,
    message TEXT NOT NULL,
    stack_trace TEXT,
    context JSONB,
    source_component VARCHAR(255),
    user_id UUID,
    session_id VARCHAR(255),
    request_id VARCHAR(255),
    fingerprint VARCHAR(64), -- Hash for deduplication
    occurrence_count INTEGER DEFAULT 1,
    first_occurrence TIMESTAMPTZ DEFAULT NOW(),
    last_occurrence TIMESTAMPTZ DEFAULT NOW(),
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMPTZ,
    resolution_method VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Error Classification Table
CREATE TABLE error_classifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    error_event_id UUID REFERENCES error_events(id) ON DELETE CASCADE,
    classification_type VARCHAR(100) NOT NULL,
    confidence_score DECIMAL(3,2) NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),
    probable_causes JSONB,
    classification_timestamp TIMESTAMPTZ DEFAULT NOW(),
    classifier_version VARCHAR(50),
    ml_model_used VARCHAR(100),
    feature_vector JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- System Metrics Table
CREATE TABLE system_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metric_name VARCHAR(255) NOT NULL,
    metric_value DECIMAL(15,6) NOT NULL,
    metric_unit VARCHAR(50),
    component VARCHAR(255),
    instance_id VARCHAR(255),
    tags JSONB,
    aggregation_period INTERVAL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Performance Baselines Table
CREATE TABLE performance_baselines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    component VARCHAR(255) NOT NULL,
    metric_name VARCHAR(255) NOT NULL,
    baseline_value DECIMAL(15,6) NOT NULL,
    threshold_warning DECIMAL(15,6),
    threshold_critical DECIMAL(15,6),
    calculation_period INTERVAL NOT NULL,
    sample_size INTEGER NOT NULL,
    standard_deviation DECIMAL(15,6),
    last_calculated TIMESTAMPTZ DEFAULT NOW(),
    next_calculation TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(component, metric_name)
);

-- Recovery Actions Table
CREATE TABLE recovery_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    risk_level risk_level_enum NOT NULL,
    success_rate DECIMAL(3,2) CHECK (success_rate >= 0 AND success_rate <= 1),
    average_execution_time INTERVAL,
    max_execution_time INTERVAL,
    prerequisites JSONB,
    configuration JSONB,
    script_path VARCHAR(500),
    timeout_seconds INTEGER DEFAULT 300,
    retry_count INTEGER DEFAULT 0,
    rollback_script_path VARCHAR(500),
    applicable_categories error_category_enum[],
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Recovery Executions Table
CREATE TABLE recovery_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    error_event_id UUID REFERENCES error_events(id) ON DELETE CASCADE,
    recovery_action_id UUID REFERENCES recovery_actions(id),
    execution_status execution_status_enum NOT NULL DEFAULT 'PENDING',
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    execution_time INTERVAL,
    success BOOLEAN,
    error_message TEXT,
    output_log TEXT,
    context JSONB,
    rollback_executed BOOLEAN DEFAULT FALSE,
    rollback_success BOOLEAN,
    rollback_error TEXT,
    retry_attempt INTEGER DEFAULT 0,
    triggered_by VARCHAR(100) DEFAULT 'system', -- 'system', 'manual', 'scheduled'
    approval_required BOOLEAN DEFAULT FALSE,
    approved_by VARCHAR(255),
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Self-Healing Metrics Table
CREATE TABLE self_healing_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date DATE NOT NULL,
    component VARCHAR(255),
    total_errors INTEGER NOT NULL DEFAULT 0,
    automated_recoveries INTEGER NOT NULL DEFAULT 0,
    successful_recoveries INTEGER NOT NULL DEFAULT 0,
    failed_recoveries INTEGER NOT NULL DEFAULT 0,
    escalated_errors INTEGER NOT NULL DEFAULT 0,
    manual_interventions INTEGER NOT NULL DEFAULT 0,
    average_recovery_time INTERVAL,
    median_recovery_time INTERVAL,
    system_availability DECIMAL(7,6) CHECK (system_availability >= 0 AND system_availability <= 1),
    mttr_seconds INTEGER, -- Mean Time To Recovery
    mtbf_seconds INTEGER, -- Mean Time Between Failures
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(date, component)
);

-- Healing Audit Trail Table
CREATE TABLE healing_audit_trail (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    error_event_id UUID REFERENCES error_events(id) ON DELETE CASCADE,
    action_type VARCHAR(100) NOT NULL,
    action_details JSONB NOT NULL,
    actor VARCHAR(255), -- 'system' or user identifier
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    result VARCHAR(100),
    impact_assessment JSONB,
    before_state JSONB,
    after_state JSONB,
    correlation_id UUID, -- For tracking related actions
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Pattern Learning Table
CREATE TABLE error_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_signature VARCHAR(500) NOT NULL,
    pattern_description TEXT,
    pattern_type VARCHAR(100), -- 'frequency', 'sequence', 'correlation'
    occurrence_count INTEGER NOT NULL DEFAULT 1,
    first_seen TIMESTAMPTZ NOT NULL,
    last_seen TIMESTAMPTZ NOT NULL,
    associated_recovery_actions JSONB,
    success_rate DECIMAL(3,2) CHECK (success_rate >= 0 AND success_rate <= 1),
    confidence_score DECIMAL(3,2) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    pattern_features JSONB,
    ml_cluster_id INTEGER,
    severity_distribution JSONB,
    time_patterns JSONB, -- hourly, daily, weekly patterns
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(pattern_signature)
);

-- Health Check Definitions Table
CREATE TABLE health_check_definitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    component VARCHAR(255) NOT NULL,
    check_type VARCHAR(100) NOT NULL, -- 'http', 'tcp', 'database', 'custom'
    configuration JSONB NOT NULL,
    interval_seconds INTEGER NOT NULL DEFAULT 60,
    timeout_seconds INTEGER NOT NULL DEFAULT 30,
    retry_count INTEGER DEFAULT 3,
    enabled BOOLEAN DEFAULT TRUE,
    critical BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Health Check Results Table
CREATE TABLE health_check_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    health_check_id UUID REFERENCES health_check_definitions(id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status VARCHAR(50) NOT NULL, -- 'healthy', 'unhealthy', 'unknown'
    response_time_ms INTEGER,
    error_message TEXT,
    details JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_error_events_timestamp ON error_events(timestamp);
CREATE INDEX idx_error_events_severity ON error_events(severity);
CREATE INDEX idx_error_events_category ON error_events(category);
CREATE INDEX idx_error_events_component ON error_events(source_component);
CREATE INDEX idx_error_events_fingerprint ON error_events(fingerprint);
CREATE INDEX idx_error_events_resolved ON error_events(resolved);

CREATE INDEX idx_error_classifications_error_event ON error_classifications(error_event_id);
CREATE INDEX idx_error_classifications_confidence ON error_classifications(confidence_score);

CREATE INDEX idx_system_metrics_timestamp ON system_metrics(timestamp);
CREATE INDEX idx_system_metrics_component ON system_metrics(component);
CREATE INDEX idx_system_metrics_name ON system_metrics(metric_name);
CREATE INDEX idx_system_metrics_component_name ON system_metrics(component, metric_name);

CREATE INDEX idx_performance_baselines_component ON performance_baselines(component);
CREATE INDEX idx_performance_baselines_metric ON performance_baselines(metric_name);

CREATE INDEX idx_recovery_actions_risk_level ON recovery_actions(risk_level);
CREATE INDEX idx_recovery_actions_enabled ON recovery_actions(enabled);
CREATE INDEX idx_recovery_actions_categories ON recovery_actions USING GIN(applicable_categories);

CREATE INDEX idx_recovery_executions_error_event ON recovery_executions(error_event_id);
CREATE INDEX idx_recovery_executions_action ON recovery_executions(recovery_action_id);
CREATE INDEX idx_recovery_executions_status ON recovery_executions(execution_status);
CREATE INDEX idx_recovery_executions_started_at ON recovery_executions(started_at);

CREATE INDEX idx_self_healing_metrics_date ON self_healing_metrics(date);
CREATE INDEX idx_self_healing_metrics_component ON self_healing_metrics(component);

CREATE INDEX idx_healing_audit_trail_error_event ON healing_audit_trail(error_event_id);
CREATE INDEX idx_healing_audit_trail_timestamp ON healing_audit_trail(timestamp);
CREATE INDEX idx_healing_audit_trail_action_type ON healing_audit_trail(action_type);

CREATE INDEX idx_error_patterns_signature ON error_patterns(pattern_signature);
CREATE INDEX idx_error_patterns_last_seen ON error_patterns(last_seen);
CREATE INDEX idx_error_patterns_confidence ON error_patterns(confidence_score);

CREATE INDEX idx_health_check_definitions_component ON health_check_definitions(component);
CREATE INDEX idx_health_check_definitions_enabled ON health_check_definitions(enabled);

CREATE INDEX idx_health_check_results_check_id ON health_check_results(health_check_id);
CREATE INDEX idx_health_check_results_timestamp ON health_check_results(timestamp);
CREATE INDEX idx_health_check_results_status ON health_check_results(status);

-- Create partial indexes for better performance on common queries
CREATE INDEX idx_error_events_unresolved ON error_events(timestamp) WHERE resolved = FALSE;
CREATE INDEX idx_recovery_executions_active ON recovery_executions(started_at) WHERE execution_status IN ('PENDING', 'RUNNING');
CREATE INDEX idx_health_check_results_unhealthy ON health_check_results(timestamp) WHERE status = 'unhealthy';

-- Create composite indexes for common query patterns
CREATE INDEX idx_error_events_component_severity_time ON error_events(source_component, severity, timestamp);
CREATE INDEX idx_system_metrics_component_time ON system_metrics(component, timestamp);
CREATE INDEX idx_recovery_executions_status_time ON recovery_executions(execution_status, started_at);

-- Add comments for documentation
COMMENT ON TABLE error_events IS 'Central table for tracking all system errors and exceptions';
COMMENT ON TABLE error_classifications IS 'ML-based classifications and root cause analysis for errors';
COMMENT ON TABLE system_metrics IS 'Real-time system performance and health metrics';
COMMENT ON TABLE performance_baselines IS 'Baseline performance metrics for anomaly detection';
COMMENT ON TABLE recovery_actions IS 'Catalog of available automated recovery procedures';
COMMENT ON TABLE recovery_executions IS 'Log of all recovery action executions and their results';
COMMENT ON TABLE self_healing_metrics IS 'Daily aggregated metrics for self-healing system effectiveness';
COMMENT ON TABLE healing_audit_trail IS 'Complete audit trail of all healing system actions';
COMMENT ON TABLE error_patterns IS 'Learned patterns from historical error data for predictive analysis';
COMMENT ON TABLE health_check_definitions IS 'Configuration for automated health checks';
COMMENT ON TABLE health_check_results IS 'Results from automated health check executions';

-- Create functions for common operations
CREATE OR REPLACE FUNCTION update_error_occurrence(
    p_fingerprint VARCHAR(64),
    p_severity error_severity_enum,
    p_category error_category_enum,
    p_message TEXT,
    p_stack_trace TEXT DEFAULT NULL,
    p_context JSONB DEFAULT NULL,
    p_source_component VARCHAR(255) DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    v_error_id UUID;
BEGIN
    -- Try to update existing error
    UPDATE error_events 
    SET 
        occurrence_count = occurrence_count + 1,
        last_occurrence = NOW(),
        updated_at = NOW()
    WHERE fingerprint = p_fingerprint
    RETURNING id INTO v_error_id;
    
    -- If no existing error, create new one
    IF v_error_id IS NULL THEN
        INSERT INTO error_events (
            fingerprint, severity, category, message, stack_trace, 
            context, source_component, occurrence_count, first_occurrence, last_occurrence
        ) VALUES (
            p_fingerprint, p_severity, p_category, p_message, p_stack_trace,
            p_context, p_source_component, 1, NOW(), NOW()
        ) RETURNING id INTO v_error_id;
    END IF;
    
    RETURN v_error_id;
END;
$$ LANGUAGE plpgsql;

-- Create function to calculate system availability
CREATE OR REPLACE FUNCTION calculate_system_availability(
    p_component VARCHAR(255),
    p_start_date DATE,
    p_end_date DATE
) RETURNS DECIMAL(7,6) AS $$
DECLARE
    v_total_time INTERVAL;
    v_downtime INTERVAL;
    v_availability DECIMAL(7,6);
BEGIN
    v_total_time := (p_end_date - p_start_date) * INTERVAL '1 day';
    
    -- Calculate downtime based on critical errors
    SELECT COALESCE(SUM(
        CASE 
            WHEN resolved_at IS NOT NULL THEN resolved_at - timestamp
            ELSE INTERVAL '0'
        END
    ), INTERVAL '0')
    INTO v_downtime
    FROM error_events
    WHERE source_component = p_component
    AND severity = 'CRITICAL'
    AND timestamp::date BETWEEN p_start_date AND p_end_date;
    
    v_availability := 1 - (EXTRACT(EPOCH FROM v_downtime) / EXTRACT(EPOCH FROM v_total_time));
    
    RETURN GREATEST(0, LEAST(1, v_availability));
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply the trigger to relevant tables
CREATE TRIGGER update_error_events_updated_at
    BEFORE UPDATE ON error_events
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_performance_baselines_updated_at
    BEFORE UPDATE ON performance_baselines
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_recovery_actions_updated_at
    BEFORE UPDATE ON recovery_actions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_self_healing_metrics_updated_at
    BEFORE UPDATE ON self_healing_metrics
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_error_patterns_updated_at
    BEFORE UPDATE ON error_patterns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_health_check_definitions_updated_at
    BEFORE UPDATE ON health_check_definitions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

