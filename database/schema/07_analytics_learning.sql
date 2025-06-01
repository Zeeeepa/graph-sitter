-- =====================================================
-- Analytics & Learning Module
-- System metrics and performance analytics
-- =====================================================

-- Metric category enumeration
CREATE TYPE metric_category AS ENUM (
    'performance', 'usage', 'quality', 'cost', 'security', 'user_behavior'
);

-- Learning pattern type enumeration
CREATE TYPE learning_pattern_type AS ENUM (
    'code_quality', 'deployment_success', 'task_estimation', 'user_productivity', 
    'error_prediction', 'optimization_opportunity', 'workflow_efficiency'
);

-- Recommendation status enumeration
CREATE TYPE recommendation_status AS ENUM (
    'pending', 'reviewed', 'accepted', 'rejected', 'implemented', 'expired'
);

-- System metrics table (partitioned by date)
CREATE TABLE system_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    metric_category metric_category NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,6) NOT NULL,
    metric_unit VARCHAR(50),
    dimensions JSONB DEFAULT '{}', -- Additional metric dimensions
    tags JSONB DEFAULT '[]',
    source_entity_type VARCHAR(100), -- 'pipeline', 'task', 'agent', 'user'
    source_entity_id UUID,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT valid_metric_value CHECK (metric_value IS NOT NULL)
) PARTITION BY RANGE (recorded_at);

-- Create partitions for system metrics (monthly)
CREATE TABLE system_metrics_y2024m01 PARTITION OF system_metrics
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
CREATE TABLE system_metrics_y2024m02 PARTITION OF system_metrics
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
CREATE TABLE system_metrics_y2024m03 PARTITION OF system_metrics
    FOR VALUES FROM ('2024-03-01') TO ('2024-04-01');

-- Learning patterns table
CREATE TABLE learning_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    pattern_type learning_pattern_type NOT NULL,
    pattern_name VARCHAR(255) NOT NULL,
    pattern_description TEXT,
    pattern_data JSONB NOT NULL,
    confidence_score DECIMAL(3,2), -- 0.00 to 1.00
    training_data_refs JSONB DEFAULT '{}',
    model_version VARCHAR(50),
    validation_score DECIMAL(3,2),
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(organization_id, pattern_type, pattern_name),
    CONSTRAINT valid_confidence CHECK (confidence_score IS NULL OR (confidence_score >= 0 AND confidence_score <= 1)),
    CONSTRAINT valid_validation CHECK (validation_score IS NULL OR (validation_score >= 0 AND validation_score <= 1))
);

-- Improvement recommendations table
CREATE TABLE improvement_recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    recommendation_type VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    target_entity_type VARCHAR(100) NOT NULL,
    target_entity_id UUID NOT NULL,
    recommendation_data JSONB NOT NULL,
    priority_score DECIMAL(3,2), -- 0.00 to 1.00
    impact_estimate JSONB DEFAULT '{}', -- Expected impact metrics
    implementation_effort VARCHAR(20) DEFAULT 'medium', -- 'low', 'medium', 'high'
    status recommendation_status DEFAULT 'pending',
    reviewed_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    reviewed_at TIMESTAMP WITH TIME ZONE,
    applied_at TIMESTAMP WITH TIME ZONE,
    effectiveness_score DECIMAL(3,2),
    feedback JSONB DEFAULT '{}',
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_priority CHECK (priority_score IS NULL OR (priority_score >= 0 AND priority_score <= 1)),
    CONSTRAINT valid_effectiveness CHECK (effectiveness_score IS NULL OR (effectiveness_score >= 0 AND effectiveness_score <= 1)),
    CONSTRAINT valid_implementation_effort CHECK (implementation_effort IN ('low', 'medium', 'high'))
);

-- Analytics dashboards table
CREATE TABLE analytics_dashboards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    dashboard_config JSONB NOT NULL,
    widget_configs JSONB DEFAULT '[]',
    filters JSONB DEFAULT '{}',
    refresh_interval_minutes INTEGER DEFAULT 15,
    is_public BOOLEAN DEFAULT false,
    created_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    shared_with_users JSONB DEFAULT '[]',
    view_count INTEGER DEFAULT 0,
    last_viewed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(organization_id, name),
    CONSTRAINT valid_refresh_interval CHECK (refresh_interval_minutes > 0)
);

-- Data quality metrics table
CREATE TABLE data_quality_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    table_name VARCHAR(100) NOT NULL,
    column_name VARCHAR(100),
    quality_dimension VARCHAR(50) NOT NULL, -- 'completeness', 'accuracy', 'consistency', 'timeliness'
    quality_score DECIMAL(5,2) NOT NULL, -- 0.00 to 100.00
    total_records INTEGER NOT NULL,
    valid_records INTEGER NOT NULL,
    invalid_records INTEGER NOT NULL,
    quality_rules JSONB DEFAULT '{}',
    validation_details JSONB DEFAULT '{}',
    measured_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_quality_score CHECK (quality_score >= 0 AND quality_score <= 100),
    CONSTRAINT valid_record_counts CHECK (total_records = valid_records + invalid_records),
    CONSTRAINT valid_quality_dimension CHECK (quality_dimension IN ('completeness', 'accuracy', 'consistency', 'timeliness', 'validity'))
);

-- Predictive models table
CREATE TABLE predictive_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    model_name VARCHAR(255) NOT NULL,
    model_type VARCHAR(100) NOT NULL, -- 'classification', 'regression', 'clustering', 'anomaly_detection'
    target_variable VARCHAR(100) NOT NULL,
    features JSONB NOT NULL,
    model_config JSONB DEFAULT '{}',
    training_data_query TEXT,
    model_artifacts JSONB DEFAULT '{}', -- Serialized model or reference
    performance_metrics JSONB DEFAULT '{}',
    validation_metrics JSONB DEFAULT '{}',
    feature_importance JSONB DEFAULT '{}',
    model_version VARCHAR(50) DEFAULT '1.0',
    is_active BOOLEAN DEFAULT true,
    last_trained_at TIMESTAMP WITH TIME ZONE,
    last_prediction_at TIMESTAMP WITH TIME ZONE,
    prediction_count INTEGER DEFAULT 0,
    created_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(organization_id, model_name, model_version),
    CONSTRAINT valid_model_type CHECK (model_type IN ('classification', 'regression', 'clustering', 'anomaly_detection', 'time_series'))
);

-- Model predictions table
CREATE TABLE model_predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    model_id UUID NOT NULL REFERENCES predictive_models(id) ON DELETE CASCADE,
    input_features JSONB NOT NULL,
    prediction_value JSONB NOT NULL,
    confidence_score DECIMAL(3,2),
    prediction_metadata JSONB DEFAULT '{}',
    actual_value JSONB, -- For validation when available
    prediction_error DECIMAL(10,4), -- Difference between predicted and actual
    target_entity_type VARCHAR(100),
    target_entity_id UUID,
    predicted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    validated_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT valid_confidence CHECK (confidence_score IS NULL OR (confidence_score >= 0 AND confidence_score <= 1))
);

-- Anomaly detection table
CREATE TABLE anomaly_detections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    anomaly_type VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    entity_id UUID NOT NULL,
    anomaly_score DECIMAL(5,4) NOT NULL, -- 0.0000 to 1.0000
    threshold_value DECIMAL(5,4) NOT NULL,
    anomaly_details JSONB NOT NULL,
    context_data JSONB DEFAULT '{}',
    is_confirmed BOOLEAN,
    confirmed_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    confirmed_at TIMESTAMP WITH TIME ZONE,
    resolution_notes TEXT,
    resolved_at TIMESTAMP WITH TIME ZONE,
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_anomaly_score CHECK (anomaly_score >= 0 AND anomaly_score <= 1),
    CONSTRAINT valid_threshold CHECK (threshold_value >= 0 AND threshold_value <= 1)
);

-- =====================================================
-- Row-Level Security
-- =====================================================

ALTER TABLE system_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE learning_patterns ENABLE ROW LEVEL SECURITY;
ALTER TABLE improvement_recommendations ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics_dashboards ENABLE ROW LEVEL SECURITY;
ALTER TABLE data_quality_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE predictive_models ENABLE ROW LEVEL SECURITY;
ALTER TABLE model_predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE anomaly_detections ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY tenant_isolation_system_metrics ON system_metrics
    USING (organization_id = get_current_tenant());

CREATE POLICY tenant_isolation_learning_patterns ON learning_patterns
    USING (organization_id = get_current_tenant());

CREATE POLICY tenant_isolation_improvement_recommendations ON improvement_recommendations
    USING (organization_id = get_current_tenant());

CREATE POLICY tenant_isolation_analytics_dashboards ON analytics_dashboards
    USING (organization_id = get_current_tenant());

CREATE POLICY tenant_isolation_data_quality_metrics ON data_quality_metrics
    USING (organization_id = get_current_tenant());

CREATE POLICY tenant_isolation_predictive_models ON predictive_models
    USING (organization_id = get_current_tenant());

CREATE POLICY tenant_isolation_model_predictions ON model_predictions
    USING (organization_id = get_current_tenant());

CREATE POLICY tenant_isolation_anomaly_detections ON anomaly_detections
    USING (organization_id = get_current_tenant());

-- =====================================================
-- Indexes for Performance
-- =====================================================

-- System Metrics
CREATE INDEX idx_system_metrics_org_category_recorded ON system_metrics(organization_id, metric_category, recorded_at);
CREATE INDEX idx_system_metrics_name_recorded ON system_metrics(metric_name, recorded_at);
CREATE INDEX idx_system_metrics_source_entity ON system_metrics(source_entity_type, source_entity_id);
CREATE INDEX idx_system_metrics_dimensions ON system_metrics USING GIN (dimensions);

-- Learning Patterns
CREATE INDEX idx_learning_patterns_org_type ON learning_patterns(organization_id, pattern_type);
CREATE INDEX idx_learning_patterns_confidence ON learning_patterns(confidence_score);
CREATE INDEX idx_learning_patterns_active ON learning_patterns(is_active);
CREATE INDEX idx_learning_patterns_usage ON learning_patterns(usage_count);

-- Improvement Recommendations
CREATE INDEX idx_recommendations_org_status ON improvement_recommendations(organization_id, status);
CREATE INDEX idx_recommendations_target ON improvement_recommendations(target_entity_type, target_entity_id);
CREATE INDEX idx_recommendations_priority ON improvement_recommendations(priority_score);
CREATE INDEX idx_recommendations_type ON improvement_recommendations(recommendation_type);
CREATE INDEX idx_recommendations_expires ON improvement_recommendations(expires_at);

-- Analytics Dashboards
CREATE INDEX idx_dashboards_org_public ON analytics_dashboards(organization_id, is_public);
CREATE INDEX idx_dashboards_created_by ON analytics_dashboards(created_by_user_id);
CREATE INDEX idx_dashboards_last_viewed ON analytics_dashboards(last_viewed_at);

-- Data Quality Metrics
CREATE INDEX idx_data_quality_table_measured ON data_quality_metrics(table_name, measured_at);
CREATE INDEX idx_data_quality_dimension_score ON data_quality_metrics(quality_dimension, quality_score);

-- Predictive Models
CREATE INDEX idx_models_org_active ON predictive_models(organization_id, is_active);
CREATE INDEX idx_models_type ON predictive_models(model_type);
CREATE INDEX idx_models_last_trained ON predictive_models(last_trained_at);

-- Model Predictions
CREATE INDEX idx_predictions_model_predicted ON model_predictions(model_id, predicted_at);
CREATE INDEX idx_predictions_target_entity ON model_predictions(target_entity_type, target_entity_id);
CREATE INDEX idx_predictions_confidence ON model_predictions(confidence_score);

-- Anomaly Detections
CREATE INDEX idx_anomalies_org_detected ON anomaly_detections(organization_id, detected_at);
CREATE INDEX idx_anomalies_entity ON anomaly_detections(entity_type, entity_id);
CREATE INDEX idx_anomalies_score ON anomaly_detections(anomaly_score);
CREATE INDEX idx_anomalies_confirmed ON anomaly_detections(is_confirmed);

-- =====================================================
-- Functions for Analytics and Learning
-- =====================================================

-- Function to record system metric
CREATE OR REPLACE FUNCTION record_system_metric(
    category metric_category,
    name VARCHAR(100),
    value DECIMAL(15,6),
    unit VARCHAR(50) DEFAULT NULL,
    dimensions JSONB DEFAULT '{}',
    source_type VARCHAR(100) DEFAULT NULL,
    source_id UUID DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    metric_id UUID;
BEGIN
    INSERT INTO system_metrics (
        organization_id,
        metric_category,
        metric_name,
        metric_value,
        metric_unit,
        dimensions,
        source_entity_type,
        source_entity_id
    ) VALUES (
        get_current_tenant(),
        category,
        name,
        value,
        unit,
        dimensions,
        source_type,
        source_id
    ) RETURNING id INTO metric_id;
    
    RETURN metric_id;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate metric aggregations
CREATE OR REPLACE FUNCTION calculate_metric_aggregation(
    metric_name VARCHAR(100),
    aggregation_type VARCHAR(20), -- 'avg', 'sum', 'min', 'max', 'count'
    time_range INTERVAL DEFAULT INTERVAL '24 hours'
) RETURNS DECIMAL(15,6) AS $$
DECLARE
    result DECIMAL(15,6);
BEGIN
    CASE aggregation_type
        WHEN 'avg' THEN
            SELECT COALESCE(AVG(metric_value), 0) INTO result
            FROM system_metrics
            WHERE metric_name = calculate_metric_aggregation.metric_name
            AND recorded_at > NOW() - time_range
            AND organization_id = get_current_tenant();
        WHEN 'sum' THEN
            SELECT COALESCE(SUM(metric_value), 0) INTO result
            FROM system_metrics
            WHERE metric_name = calculate_metric_aggregation.metric_name
            AND recorded_at > NOW() - time_range
            AND organization_id = get_current_tenant();
        WHEN 'min' THEN
            SELECT COALESCE(MIN(metric_value), 0) INTO result
            FROM system_metrics
            WHERE metric_name = calculate_metric_aggregation.metric_name
            AND recorded_at > NOW() - time_range
            AND organization_id = get_current_tenant();
        WHEN 'max' THEN
            SELECT COALESCE(MAX(metric_value), 0) INTO result
            FROM system_metrics
            WHERE metric_name = calculate_metric_aggregation.metric_name
            AND recorded_at > NOW() - time_range
            AND organization_id = get_current_tenant();
        WHEN 'count' THEN
            SELECT COUNT(*) INTO result
            FROM system_metrics
            WHERE metric_name = calculate_metric_aggregation.metric_name
            AND recorded_at > NOW() - time_range
            AND organization_id = get_current_tenant();
        ELSE
            result := 0;
    END CASE;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Function to detect anomalies
CREATE OR REPLACE FUNCTION detect_anomalies(
    entity_type VARCHAR(100),
    entity_id UUID,
    metric_name VARCHAR(100),
    threshold DECIMAL(5,4) DEFAULT 0.95
) RETURNS BOOLEAN AS $$
DECLARE
    recent_values DECIMAL(15,6)[];
    current_value DECIMAL(15,6);
    mean_value DECIMAL(15,6);
    std_dev DECIMAL(15,6);
    z_score DECIMAL(10,4);
    anomaly_score DECIMAL(5,4);
    is_anomaly BOOLEAN := FALSE;
BEGIN
    -- Get recent metric values for baseline
    SELECT array_agg(metric_value ORDER BY recorded_at)
    INTO recent_values
    FROM system_metrics
    WHERE metric_name = detect_anomalies.metric_name
    AND source_entity_type = detect_anomalies.entity_type
    AND source_entity_id = detect_anomalies.entity_id
    AND recorded_at > NOW() - INTERVAL '7 days'
    AND organization_id = get_current_tenant();
    
    -- Get current value
    SELECT metric_value INTO current_value
    FROM system_metrics
    WHERE metric_name = detect_anomalies.metric_name
    AND source_entity_type = detect_anomalies.entity_type
    AND source_entity_id = detect_anomalies.entity_id
    AND organization_id = get_current_tenant()
    ORDER BY recorded_at DESC
    LIMIT 1;
    
    -- Calculate statistics if we have enough data
    IF array_length(recent_values, 1) >= 10 THEN
        SELECT AVG(val), STDDEV(val)
        INTO mean_value, std_dev
        FROM unnest(recent_values) AS val;
        
        -- Calculate z-score
        IF std_dev > 0 THEN
            z_score := ABS(current_value - mean_value) / std_dev;
            anomaly_score := LEAST(z_score / 3.0, 1.0); -- Normalize to 0-1 scale
            
            IF anomaly_score >= threshold THEN
                is_anomaly := TRUE;
                
                -- Record the anomaly
                INSERT INTO anomaly_detections (
                    organization_id,
                    anomaly_type,
                    entity_type,
                    entity_id,
                    anomaly_score,
                    threshold_value,
                    anomaly_details,
                    context_data
                ) VALUES (
                    get_current_tenant(),
                    'statistical_outlier',
                    detect_anomalies.entity_type,
                    detect_anomalies.entity_id,
                    anomaly_score,
                    threshold,
                    jsonb_build_object(
                        'metric_name', metric_name,
                        'current_value', current_value,
                        'mean_value', mean_value,
                        'std_dev', std_dev,
                        'z_score', z_score
                    ),
                    jsonb_build_object(
                        'baseline_samples', array_length(recent_values, 1)
                    )
                );
            END IF;
        END IF;
    END IF;
    
    RETURN is_anomaly;
END;
$$ LANGUAGE plpgsql;

-- Function to generate improvement recommendations
CREATE OR REPLACE FUNCTION generate_improvement_recommendation(
    rec_type VARCHAR(100),
    title VARCHAR(255),
    description TEXT,
    target_type VARCHAR(100),
    target_id UUID,
    rec_data JSONB,
    priority DECIMAL(3,2) DEFAULT 0.5
) RETURNS UUID AS $$
DECLARE
    recommendation_id UUID;
BEGIN
    INSERT INTO improvement_recommendations (
        organization_id,
        recommendation_type,
        title,
        description,
        target_entity_type,
        target_entity_id,
        recommendation_data,
        priority_score,
        expires_at
    ) VALUES (
        get_current_tenant(),
        rec_type,
        title,
        description,
        target_type,
        target_id,
        rec_data,
        priority,
        NOW() + INTERVAL '30 days' -- Default expiration
    ) RETURNING id INTO recommendation_id;
    
    RETURN recommendation_id;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate data quality score
CREATE OR REPLACE FUNCTION calculate_data_quality_score(
    table_name VARCHAR(100),
    column_name VARCHAR(100) DEFAULT NULL
) RETURNS DECIMAL(5,2) AS $$
DECLARE
    overall_score DECIMAL(5,2);
BEGIN
    SELECT AVG(quality_score) INTO overall_score
    FROM data_quality_metrics
    WHERE data_quality_metrics.table_name = calculate_data_quality_score.table_name
    AND (column_name IS NULL OR data_quality_metrics.column_name = calculate_data_quality_score.column_name)
    AND measured_at > NOW() - INTERVAL '24 hours'
    AND organization_id = get_current_tenant();
    
    RETURN COALESCE(overall_score, 0.00);
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- Triggers
-- =====================================================

-- Update timestamp triggers
CREATE TRIGGER update_learning_patterns_updated_at 
    BEFORE UPDATE ON learning_patterns 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_improvement_recommendations_updated_at 
    BEFORE UPDATE ON improvement_recommendations 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_analytics_dashboards_updated_at 
    BEFORE UPDATE ON analytics_dashboards 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_predictive_models_updated_at 
    BEFORE UPDATE ON predictive_models 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger to auto-detect anomalies on metric insertion
CREATE OR REPLACE FUNCTION auto_detect_anomalies()
RETURNS TRIGGER AS $$
BEGIN
    -- Only check for anomalies on performance and quality metrics
    IF NEW.metric_category IN ('performance', 'quality') AND 
       NEW.source_entity_type IS NOT NULL AND 
       NEW.source_entity_id IS NOT NULL THEN
        
        PERFORM detect_anomalies(
            NEW.source_entity_type,
            NEW.source_entity_id,
            NEW.metric_name,
            0.95
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER auto_detect_anomalies_trigger
    AFTER INSERT ON system_metrics
    FOR EACH ROW EXECUTE FUNCTION auto_detect_anomalies();

-- =====================================================
-- Views for Common Queries
-- =====================================================

-- Metrics summary view
CREATE VIEW metrics_summary AS
SELECT 
    metric_category,
    metric_name,
    COUNT(*) as measurement_count,
    AVG(metric_value) as avg_value,
    MIN(metric_value) as min_value,
    MAX(metric_value) as max_value,
    STDDEV(metric_value) as std_dev,
    MAX(recorded_at) as last_recorded_at
FROM system_metrics
WHERE recorded_at > NOW() - INTERVAL '24 hours'
GROUP BY metric_category, metric_name;

-- Active recommendations view
CREATE VIEW active_recommendations AS
SELECT 
    ir.id,
    ir.organization_id,
    ir.recommendation_type,
    ir.title,
    ir.target_entity_type,
    ir.target_entity_id,
    ir.priority_score,
    ir.status,
    ir.created_at,
    ir.expires_at,
    CASE 
        WHEN ir.expires_at < NOW() THEN 'expired'
        WHEN ir.priority_score >= 0.8 THEN 'high'
        WHEN ir.priority_score >= 0.5 THEN 'medium'
        ELSE 'low'
    END as priority_level
FROM improvement_recommendations ir
WHERE ir.status IN ('pending', 'reviewed')
AND (ir.expires_at IS NULL OR ir.expires_at > NOW());

-- Recent anomalies view
CREATE VIEW recent_anomalies AS
SELECT 
    ad.id,
    ad.organization_id,
    ad.anomaly_type,
    ad.entity_type,
    ad.entity_id,
    ad.anomaly_score,
    ad.is_confirmed,
    ad.detected_at,
    ad.resolved_at,
    CASE 
        WHEN ad.anomaly_score >= 0.9 THEN 'critical'
        WHEN ad.anomaly_score >= 0.7 THEN 'high'
        WHEN ad.anomaly_score >= 0.5 THEN 'medium'
        ELSE 'low'
    END as severity_level
FROM anomaly_detections ad
WHERE ad.detected_at > NOW() - INTERVAL '7 days'
ORDER BY ad.anomaly_score DESC, ad.detected_at DESC;

