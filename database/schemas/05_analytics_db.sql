-- =============================================================================
-- ANALYTICS DATABASE SCHEMA: OpenEvolve Integration and Step Analysis
-- =============================================================================
-- This database handles OpenEvolve integration, step analysis, real-time
-- analytics, and quality scoring for comprehensive system analytics.
-- =============================================================================

-- Connect to analytics_db
\c analytics_db;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "btree_gist";
CREATE EXTENSION IF NOT EXISTS "timescaledb" CASCADE; -- For time-series data

-- Set timezone and configuration
SET timezone = 'UTC';
SET default_text_search_config = 'pg_catalog.english';

-- Grant all privileges to analytics_user
GRANT ALL PRIVILEGES ON DATABASE analytics_db TO analytics_user;
GRANT ALL PRIVILEGES ON SCHEMA public TO analytics_user;

-- Analytics-specific enums
CREATE TYPE analysis_type AS ENUM (
    'performance',
    'quality',
    'security',
    'complexity',
    'evolution',
    'usage',
    'trend',
    'prediction',
    'anomaly',
    'custom'
);

CREATE TYPE run_status AS ENUM (
    'queued',
    'running',
    'completed',
    'failed',
    'cancelled',
    'timeout'
);

CREATE TYPE metric_type AS ENUM (
    'counter',
    'gauge',
    'histogram',
    'summary',
    'rate',
    'percentage',
    'score',
    'duration'
);

CREATE TYPE aggregation_type AS ENUM (
    'sum',
    'avg',
    'min',
    'max',
    'count',
    'median',
    'percentile',
    'stddev'
);

CREATE TYPE alert_severity AS ENUM (
    'info',
    'warning',
    'error',
    'critical'
);

-- =============================================================================
-- CORE REFERENCE TABLES
-- =============================================================================

-- Organizations table for multi-tenancy
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Users table for analytics tracking
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(50) DEFAULT 'member',
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- ANALYSIS RUNS AND ORCHESTRATION
-- =============================================================================

-- Main analysis runs table
CREATE TABLE analysis_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Run identification
    name VARCHAR(255) NOT NULL,
    description TEXT,
    analysis_type analysis_type NOT NULL,
    
    -- Run configuration
    configuration JSONB DEFAULT '{}',
    parameters JSONB DEFAULT '{}',
    
    -- OpenEvolve integration
    evolve_session_id UUID,
    evolve_step_id UUID,
    evolve_generation INTEGER,
    
    -- Run status and progress
    status run_status DEFAULT 'queued',
    progress_percentage DECIMAL(5,2) DEFAULT 0,
    
    -- Timing and performance
    queued_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    
    -- Resource usage
    cpu_time_seconds DECIMAL(10,3),
    memory_peak_mb INTEGER,
    disk_usage_mb INTEGER,
    
    -- Results summary
    total_metrics INTEGER DEFAULT 0,
    success_metrics INTEGER DEFAULT 0,
    failed_metrics INTEGER DEFAULT 0,
    
    -- Quality scores
    overall_score DECIMAL(5,2),
    quality_score DECIMAL(5,2),
    performance_score DECIMAL(5,2),
    reliability_score DECIMAL(5,2),
    
    -- Error handling
    error_message TEXT,
    error_code VARCHAR(50),
    warnings JSONB DEFAULT '[]',
    
    -- Triggered by
    triggered_by UUID REFERENCES users(id),
    trigger_source VARCHAR(100), -- manual, scheduled, webhook, api, evolve
    
    -- External references
    external_run_id VARCHAR(255),
    
    -- Metadata
    tags VARCHAR(50)[],
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT analysis_runs_name_not_empty CHECK (length(trim(name)) > 0),
    CONSTRAINT analysis_runs_progress_valid CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
    CONSTRAINT analysis_runs_scores_valid CHECK (
        overall_score >= 0 AND overall_score <= 100 AND
        quality_score >= 0 AND quality_score <= 100 AND
        performance_score >= 0 AND performance_score <= 100 AND
        reliability_score >= 0 AND reliability_score <= 100
    )
);

-- Analysis steps for detailed tracking
CREATE TABLE analysis_steps (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_run_id UUID NOT NULL REFERENCES analysis_runs(id) ON DELETE CASCADE,
    
    -- Step identification
    step_name VARCHAR(255) NOT NULL,
    step_order INTEGER NOT NULL,
    description TEXT,
    
    -- Step configuration
    step_config JSONB DEFAULT '{}',
    
    -- Step status
    status run_status DEFAULT 'queued',
    
    -- Timing
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    
    -- Results
    output_data JSONB DEFAULT '{}',
    metrics_generated INTEGER DEFAULT 0,
    
    -- Error handling
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT analysis_steps_run_step_unique UNIQUE (analysis_run_id, step_order),
    CONSTRAINT analysis_steps_step_order_positive CHECK (step_order > 0)
);

-- =============================================================================
-- METRICS AND MEASUREMENTS
-- =============================================================================

-- Core metrics table (time-series optimized)
CREATE TABLE metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    analysis_run_id UUID REFERENCES analysis_runs(id) ON DELETE CASCADE,
    
    -- Metric identification
    metric_name VARCHAR(255) NOT NULL,
    metric_type metric_type NOT NULL,
    category VARCHAR(100),
    
    -- Metric value
    value_numeric DECIMAL(15,6),
    value_text TEXT,
    value_json JSONB,
    
    -- Metric context
    entity_type VARCHAR(100), -- codebase, file, function, class, etc.
    entity_id UUID,
    entity_name VARCHAR(255),
    
    -- Dimensions for grouping
    dimensions JSONB DEFAULT '{}',
    
    -- Quality and confidence
    confidence_score DECIMAL(5,2) DEFAULT 100,
    quality_flags JSONB DEFAULT '[]',
    
    -- Temporal information
    measured_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    valid_from TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    valid_until TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT metrics_name_not_empty CHECK (length(trim(metric_name)) > 0),
    CONSTRAINT metrics_confidence_valid CHECK (confidence_score >= 0 AND confidence_score <= 100),
    CONSTRAINT metrics_has_value CHECK (
        value_numeric IS NOT NULL OR 
        value_text IS NOT NULL OR 
        value_json IS NOT NULL
    )
);

-- Convert metrics to hypertable for time-series optimization
SELECT create_hypertable('metrics', 'measured_at', if_not_exists => TRUE);

-- Performance data for detailed performance tracking
CREATE TABLE performance_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    analysis_run_id UUID REFERENCES analysis_runs(id) ON DELETE CASCADE,
    
    -- Performance context
    operation_name VARCHAR(255) NOT NULL,
    operation_type VARCHAR(100),
    
    -- Performance metrics
    duration_ms INTEGER NOT NULL,
    cpu_usage_percent DECIMAL(5,2),
    memory_usage_mb INTEGER,
    disk_io_mb INTEGER,
    network_io_mb INTEGER,
    
    -- Throughput metrics
    operations_per_second DECIMAL(10,3),
    items_processed INTEGER,
    
    -- Quality metrics
    success_rate DECIMAL(5,2),
    error_rate DECIMAL(5,2),
    
    -- Resource efficiency
    cpu_efficiency DECIMAL(5,2),
    memory_efficiency DECIMAL(5,2),
    
    -- Context information
    environment VARCHAR(100),
    version VARCHAR(50),
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    measured_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT performance_data_operation_not_empty CHECK (length(trim(operation_name)) > 0),
    CONSTRAINT performance_data_duration_positive CHECK (duration_ms >= 0),
    CONSTRAINT performance_data_rates_valid CHECK (
        success_rate >= 0 AND success_rate <= 100 AND
        error_rate >= 0 AND error_rate <= 100
    )
);

-- Convert performance_data to hypertable
SELECT create_hypertable('performance_data', 'measured_at', if_not_exists => TRUE);

-- =============================================================================
-- AGGREGATIONS AND SUMMARIES
-- =============================================================================

-- Metric aggregations for pre-computed summaries
CREATE TABLE metric_aggregations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Aggregation identification
    metric_name VARCHAR(255) NOT NULL,
    aggregation_type aggregation_type NOT NULL,
    
    -- Aggregation scope
    time_window_minutes INTEGER NOT NULL,
    entity_type VARCHAR(100),
    entity_filter JSONB DEFAULT '{}',
    
    -- Aggregated values
    aggregated_value DECIMAL(15,6),
    sample_count INTEGER,
    
    -- Time range
    window_start TIMESTAMP WITH TIME ZONE NOT NULL,
    window_end TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Quality indicators
    confidence_score DECIMAL(5,2) DEFAULT 100,
    completeness_percentage DECIMAL(5,2) DEFAULT 100,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT metric_aggregations_unique UNIQUE (
        metric_name, aggregation_type, time_window_minutes, 
        entity_type, window_start
    ),
    CONSTRAINT metric_aggregations_window_valid CHECK (window_end > window_start),
    CONSTRAINT metric_aggregations_sample_count_positive CHECK (sample_count >= 0)
);

-- =============================================================================
-- REAL-TIME ANALYTICS AND ALERTS
-- =============================================================================

-- Real-time dashboards configuration
CREATE TABLE dashboards (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Dashboard identification
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Dashboard configuration
    layout_config JSONB DEFAULT '{}',
    widget_configs JSONB DEFAULT '[]',
    
    -- Access control
    is_public BOOLEAN DEFAULT false,
    allowed_users JSONB DEFAULT '[]',
    
    -- Refresh settings
    auto_refresh_seconds INTEGER DEFAULT 300,
    
    -- Metadata
    tags VARCHAR(50)[],
    metadata JSONB DEFAULT '{}',
    
    -- Ownership
    created_by UUID REFERENCES users(id),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT dashboards_name_org_unique UNIQUE (organization_id, name),
    CONSTRAINT dashboards_name_not_empty CHECK (length(trim(name)) > 0)
);

-- Alert rules for monitoring
CREATE TABLE alert_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Alert identification
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Alert condition
    metric_name VARCHAR(255) NOT NULL,
    condition_operator VARCHAR(20) NOT NULL, -- >, <, >=, <=, =, !=
    threshold_value DECIMAL(15,6) NOT NULL,
    
    -- Alert configuration
    severity alert_severity DEFAULT 'warning',
    evaluation_window_minutes INTEGER DEFAULT 5,
    
    -- Alert state
    is_active BOOLEAN DEFAULT true,
    last_triggered_at TIMESTAMP WITH TIME ZONE,
    trigger_count INTEGER DEFAULT 0,
    
    -- Notification settings
    notification_config JSONB DEFAULT '{}',
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Ownership
    created_by UUID REFERENCES users(id),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT alert_rules_name_org_unique UNIQUE (organization_id, name),
    CONSTRAINT alert_rules_name_not_empty CHECK (length(trim(name)) > 0),
    CONSTRAINT alert_rules_window_positive CHECK (evaluation_window_minutes > 0)
);

-- Alert instances for tracking fired alerts
CREATE TABLE alert_instances (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    alert_rule_id UUID NOT NULL REFERENCES alert_rules(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Alert instance details
    triggered_value DECIMAL(15,6),
    threshold_value DECIMAL(15,6),
    
    -- Alert timing
    triggered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    duration_minutes INTEGER,
    
    -- Alert context
    entity_type VARCHAR(100),
    entity_id UUID,
    context_data JSONB DEFAULT '{}',
    
    -- Notification tracking
    notifications_sent INTEGER DEFAULT 0,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- INDEXES FOR OPTIMAL PERFORMANCE
-- =============================================================================

-- Analysis runs indexes
CREATE INDEX idx_analysis_runs_org_id ON analysis_runs(organization_id);
CREATE INDEX idx_analysis_runs_type ON analysis_runs(analysis_type);
CREATE INDEX idx_analysis_runs_status ON analysis_runs(status);
CREATE INDEX idx_analysis_runs_started_at ON analysis_runs(started_at);
CREATE INDEX idx_analysis_runs_evolve_session ON analysis_runs(evolve_session_id);
CREATE INDEX idx_analysis_runs_triggered_by ON analysis_runs(triggered_by);

-- Analysis steps indexes
CREATE INDEX idx_analysis_steps_run_id ON analysis_steps(analysis_run_id);
CREATE INDEX idx_analysis_steps_status ON analysis_steps(status);
CREATE INDEX idx_analysis_steps_order ON analysis_steps(step_order);

-- Metrics indexes (time-series optimized)
CREATE INDEX idx_metrics_org_id ON metrics(organization_id, measured_at DESC);
CREATE INDEX idx_metrics_run_id ON metrics(analysis_run_id, measured_at DESC);
CREATE INDEX idx_metrics_name ON metrics(metric_name, measured_at DESC);
CREATE INDEX idx_metrics_type ON metrics(metric_type, measured_at DESC);
CREATE INDEX idx_metrics_entity ON metrics(entity_type, entity_id, measured_at DESC);

-- Performance data indexes
CREATE INDEX idx_performance_data_org_id ON performance_data(organization_id, measured_at DESC);
CREATE INDEX idx_performance_data_operation ON performance_data(operation_name, measured_at DESC);
CREATE INDEX idx_performance_data_duration ON performance_data(duration_ms DESC);

-- Aggregations indexes
CREATE INDEX idx_metric_aggregations_metric ON metric_aggregations(metric_name, window_start DESC);
CREATE INDEX idx_metric_aggregations_window ON metric_aggregations(window_start, window_end);

-- Dashboards and alerts indexes
CREATE INDEX idx_dashboards_org_id ON dashboards(organization_id);
CREATE INDEX idx_dashboards_created_by ON dashboards(created_by);

CREATE INDEX idx_alert_rules_org_id ON alert_rules(organization_id);
CREATE INDEX idx_alert_rules_metric ON alert_rules(metric_name);
CREATE INDEX idx_alert_rules_active ON alert_rules(is_active);

CREATE INDEX idx_alert_instances_rule_id ON alert_instances(alert_rule_id);
CREATE INDEX idx_alert_instances_triggered_at ON alert_instances(triggered_at);

-- GIN indexes for JSONB fields
CREATE INDEX idx_analysis_runs_config_gin USING gin (configuration);
CREATE INDEX idx_metrics_dimensions_gin USING gin (dimensions);
CREATE INDEX idx_metrics_metadata_gin USING gin (metadata);

-- =============================================================================
-- VIEWS FOR ANALYTICS AND REPORTING
-- =============================================================================

-- Analysis run summary
CREATE VIEW analysis_run_summary AS
SELECT 
    ar.*,
    o.name as organization_name,
    u.name as triggered_by_name,
    COUNT(as_steps.id) as total_steps,
    COUNT(CASE WHEN as_steps.status = 'completed' THEN 1 END) as completed_steps,
    COUNT(m.id) as metrics_generated
FROM analysis_runs ar
JOIN organizations o ON ar.organization_id = o.id
LEFT JOIN users u ON ar.triggered_by = u.id
LEFT JOIN analysis_steps as_steps ON ar.id = as_steps.analysis_run_id
LEFT JOIN metrics m ON ar.id = m.analysis_run_id
GROUP BY ar.id, o.name, u.name;

-- Real-time metrics view
CREATE VIEW real_time_metrics AS
SELECT 
    m.*,
    o.name as organization_name,
    ar.name as analysis_run_name
FROM metrics m
JOIN organizations o ON m.organization_id = o.id
LEFT JOIN analysis_runs ar ON m.analysis_run_id = ar.id
WHERE m.measured_at >= NOW() - INTERVAL '1 hour'
ORDER BY m.measured_at DESC;

-- Performance trends view
CREATE VIEW performance_trends AS
SELECT 
    operation_name,
    DATE_TRUNC('hour', measured_at) as hour,
    AVG(duration_ms) as avg_duration_ms,
    MIN(duration_ms) as min_duration_ms,
    MAX(duration_ms) as max_duration_ms,
    AVG(cpu_usage_percent) as avg_cpu_usage,
    AVG(memory_usage_mb) as avg_memory_usage,
    COUNT(*) as operation_count
FROM performance_data
WHERE measured_at >= NOW() - INTERVAL '24 hours'
GROUP BY operation_name, DATE_TRUNC('hour', measured_at)
ORDER BY hour DESC;

-- Grant permissions to analytics_user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO analytics_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO analytics_user;
GRANT USAGE ON SCHEMA public TO analytics_user;

-- Insert default organization
INSERT INTO organizations (name, slug, description) VALUES 
('Default Organization', 'default', 'Default organization for analytics');

-- Insert default admin user
INSERT INTO users (organization_id, name, email, role) VALUES 
((SELECT id FROM organizations WHERE slug = 'default'), 'Analytics Admin', 'admin@analytics.local', 'admin');

-- Final status message
DO $$
BEGIN
    RAISE NOTICE '📊 Analytics Database initialized successfully!';
    RAISE NOTICE 'Features: OpenEvolve integration, Real-time analytics, Performance tracking, Quality scoring';
    RAISE NOTICE 'Time-series optimization: Enabled with TimescaleDB';
    RAISE NOTICE 'Timestamp: %', NOW();
END $$;

