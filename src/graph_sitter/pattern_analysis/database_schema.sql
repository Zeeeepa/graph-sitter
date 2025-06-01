-- Database schema extensions for pattern analysis engine
-- This file contains the SQL schema for storing pattern analysis data

-- Pattern storage and analysis
CREATE TABLE IF NOT EXISTS detected_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_type VARCHAR(100) NOT NULL,
    pattern_data JSONB NOT NULL,
    significance_score DECIMAL(5,2) NOT NULL CHECK (significance_score >= 0 AND significance_score <= 1),
    detected_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    frequency INTEGER NOT NULL DEFAULT 0,
    impact_score DECIMAL(5,2) NOT NULL CHECK (impact_score >= 0 AND impact_score <= 1),
    confidence DECIMAL(5,2) DEFAULT 0.0 CHECK (confidence >= 0 AND confidence <= 1),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for pattern queries
CREATE INDEX IF NOT EXISTS idx_detected_patterns_type ON detected_patterns(pattern_type);
CREATE INDEX IF NOT EXISTS idx_detected_patterns_detected_at ON detected_patterns(detected_at);
CREATE INDEX IF NOT EXISTS idx_detected_patterns_significance ON detected_patterns(significance_score DESC);
CREATE INDEX IF NOT EXISTS idx_detected_patterns_impact ON detected_patterns(impact_score DESC);

-- ML models storage and metadata
CREATE TABLE IF NOT EXISTS ml_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_name VARCHAR(255) NOT NULL,
    model_type VARCHAR(100) NOT NULL,
    version VARCHAR(50) NOT NULL,
    accuracy DECIMAL(5,2) CHECK (accuracy >= 0 AND accuracy <= 1),
    training_data_size INTEGER NOT NULL DEFAULT 0,
    trained_at TIMESTAMP NOT NULL,
    deployed_at TIMESTAMP,
    model_data BYTEA,
    hyperparameters JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'trained',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(model_name, version)
);

-- Create indexes for model queries
CREATE INDEX IF NOT EXISTS idx_ml_models_name ON ml_models(model_name);
CREATE INDEX IF NOT EXISTS idx_ml_models_type ON ml_models(model_type);
CREATE INDEX IF NOT EXISTS idx_ml_models_status ON ml_models(status);
CREATE INDEX IF NOT EXISTS idx_ml_models_trained_at ON ml_models(trained_at DESC);

-- Predictions storage
CREATE TABLE IF NOT EXISTS predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID REFERENCES ml_models(id) ON DELETE CASCADE,
    prediction_type VARCHAR(100) NOT NULL,
    input_data JSONB NOT NULL,
    prediction_result JSONB NOT NULL,
    confidence_score DECIMAL(5,2) NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),
    actual_outcome JSONB,
    accuracy_score DECIMAL(5,2) CHECK (accuracy_score >= 0 AND accuracy_score <= 1),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for prediction queries
CREATE INDEX IF NOT EXISTS idx_predictions_model_id ON predictions(model_id);
CREATE INDEX IF NOT EXISTS idx_predictions_type ON predictions(prediction_type);
CREATE INDEX IF NOT EXISTS idx_predictions_created_at ON predictions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_confidence ON predictions(confidence_score DESC);

-- Optimization recommendations storage
CREATE TABLE IF NOT EXISTS optimization_recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recommendation_type VARCHAR(100) NOT NULL,
    target_component VARCHAR(100) NOT NULL,
    recommendation_data JSONB NOT NULL,
    expected_impact JSONB NOT NULL,
    priority_score DECIMAL(5,2) NOT NULL CHECK (priority_score >= 0 AND priority_score <= 1),
    status VARCHAR(50) DEFAULT 'pending',
    implemented_at TIMESTAMP,
    effectiveness_score DECIMAL(5,2) CHECK (effectiveness_score >= 0 AND effectiveness_score <= 1),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for recommendation queries
CREATE INDEX IF NOT EXISTS idx_optimization_recommendations_type ON optimization_recommendations(recommendation_type);
CREATE INDEX IF NOT EXISTS idx_optimization_recommendations_component ON optimization_recommendations(target_component);
CREATE INDEX IF NOT EXISTS idx_optimization_recommendations_status ON optimization_recommendations(status);
CREATE INDEX IF NOT EXISTS idx_optimization_recommendations_priority ON optimization_recommendations(priority_score DESC);
CREATE INDEX IF NOT EXISTS idx_optimization_recommendations_created_at ON optimization_recommendations(created_at DESC);

-- Model performance metrics tracking
CREATE TABLE IF NOT EXISTS model_performance_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID REFERENCES ml_models(id) ON DELETE CASCADE,
    accuracy DECIMAL(5,2) NOT NULL CHECK (accuracy >= 0 AND accuracy <= 1),
    precision_score DECIMAL(5,2) CHECK (precision_score >= 0 AND precision_score <= 1),
    recall DECIMAL(5,2) CHECK (recall >= 0 AND recall <= 1),
    f1_score DECIMAL(5,2) CHECK (f1_score >= 0 AND f1_score <= 1),
    auc_roc DECIMAL(5,2) CHECK (auc_roc >= 0 AND auc_roc <= 1),
    mean_squared_error DECIMAL(10,6),
    mean_absolute_error DECIMAL(10,6),
    evaluation_data_size INTEGER DEFAULT 0,
    evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance metrics
CREATE INDEX IF NOT EXISTS idx_model_performance_model_id ON model_performance_metrics(model_id);
CREATE INDEX IF NOT EXISTS idx_model_performance_evaluated_at ON model_performance_metrics(evaluated_at DESC);

-- Feature importance tracking
CREATE TABLE IF NOT EXISTS feature_importance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID REFERENCES ml_models(id) ON DELETE CASCADE,
    feature_name VARCHAR(255) NOT NULL,
    importance_score DECIMAL(8,6) NOT NULL,
    feature_type VARCHAR(100),
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for feature importance
CREATE INDEX IF NOT EXISTS idx_feature_importance_model_id ON feature_importance(model_id);
CREATE INDEX IF NOT EXISTS idx_feature_importance_score ON feature_importance(importance_score DESC);

-- Data pipeline execution logs
CREATE TABLE IF NOT EXISTS data_pipeline_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_name VARCHAR(255) NOT NULL,
    execution_id VARCHAR(255) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    status VARCHAR(50) NOT NULL DEFAULT 'running',
    records_processed INTEGER DEFAULT 0,
    records_output INTEGER DEFAULT 0,
    error_message TEXT,
    execution_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for pipeline logs
CREATE INDEX IF NOT EXISTS idx_data_pipeline_logs_name ON data_pipeline_logs(pipeline_name);
CREATE INDEX IF NOT EXISTS idx_data_pipeline_logs_execution_id ON data_pipeline_logs(execution_id);
CREATE INDEX IF NOT EXISTS idx_data_pipeline_logs_start_time ON data_pipeline_logs(start_time DESC);
CREATE INDEX IF NOT EXISTS idx_data_pipeline_logs_status ON data_pipeline_logs(status);

-- Pattern analysis configuration
CREATE TABLE IF NOT EXISTS pattern_analysis_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_name VARCHAR(255) NOT NULL UNIQUE,
    config_data JSONB NOT NULL,
    is_active BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for config queries
CREATE INDEX IF NOT EXISTS idx_pattern_analysis_config_name ON pattern_analysis_config(config_name);
CREATE INDEX IF NOT EXISTS idx_pattern_analysis_config_active ON pattern_analysis_config(is_active);

-- Early warning alerts
CREATE TABLE IF NOT EXISTS early_warning_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_type VARCHAR(100) NOT NULL,
    severity VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    alert_data JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    acknowledged_at TIMESTAMP,
    acknowledged_by VARCHAR(255),
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for alerts
CREATE INDEX IF NOT EXISTS idx_early_warning_alerts_type ON early_warning_alerts(alert_type);
CREATE INDEX IF NOT EXISTS idx_early_warning_alerts_severity ON early_warning_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_early_warning_alerts_status ON early_warning_alerts(status);
CREATE INDEX IF NOT EXISTS idx_early_warning_alerts_created_at ON early_warning_alerts(created_at DESC);

-- Pattern relationships (for tracking pattern correlations)
CREATE TABLE IF NOT EXISTS pattern_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_id_1 UUID REFERENCES detected_patterns(id) ON DELETE CASCADE,
    pattern_id_2 UUID REFERENCES detected_patterns(id) ON DELETE CASCADE,
    relationship_type VARCHAR(100) NOT NULL,
    correlation_strength DECIMAL(5,2) CHECK (correlation_strength >= -1 AND correlation_strength <= 1),
    relationship_data JSONB DEFAULT '{}',
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(pattern_id_1, pattern_id_2, relationship_type)
);

-- Create indexes for pattern relationships
CREATE INDEX IF NOT EXISTS idx_pattern_relationships_pattern1 ON pattern_relationships(pattern_id_1);
CREATE INDEX IF NOT EXISTS idx_pattern_relationships_pattern2 ON pattern_relationships(pattern_id_2);
CREATE INDEX IF NOT EXISTS idx_pattern_relationships_type ON pattern_relationships(relationship_type);
CREATE INDEX IF NOT EXISTS idx_pattern_relationships_strength ON pattern_relationships(correlation_strength DESC);

-- Update triggers for timestamp management
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update triggers to relevant tables
CREATE TRIGGER update_detected_patterns_updated_at 
    BEFORE UPDATE ON detected_patterns 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ml_models_updated_at 
    BEFORE UPDATE ON ml_models 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_predictions_updated_at 
    BEFORE UPDATE ON predictions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_optimization_recommendations_updated_at 
    BEFORE UPDATE ON optimization_recommendations 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_pattern_analysis_config_updated_at 
    BEFORE UPDATE ON pattern_analysis_config 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Views for common queries

-- Active patterns view
CREATE OR REPLACE VIEW active_patterns AS
SELECT 
    p.*,
    CASE 
        WHEN p.significance_score >= 0.8 THEN 'high'
        WHEN p.significance_score >= 0.5 THEN 'medium'
        ELSE 'low'
    END as significance_level,
    CASE 
        WHEN p.impact_score >= 0.8 THEN 'high'
        WHEN p.impact_score >= 0.5 THEN 'medium'
        ELSE 'low'
    END as impact_level
FROM detected_patterns p
WHERE p.detected_at >= CURRENT_TIMESTAMP - INTERVAL '30 days'
ORDER BY p.significance_score DESC, p.impact_score DESC;

-- Model performance summary view
CREATE OR REPLACE VIEW model_performance_summary AS
SELECT 
    m.id,
    m.model_name,
    m.model_type,
    m.version,
    m.status,
    m.accuracy as training_accuracy,
    COALESCE(latest_perf.accuracy, 0) as latest_accuracy,
    COALESCE(avg_perf.avg_accuracy, 0) as avg_accuracy,
    m.trained_at,
    m.deployed_at,
    latest_perf.evaluated_at as last_evaluated
FROM ml_models m
LEFT JOIN LATERAL (
    SELECT accuracy, evaluated_at
    FROM model_performance_metrics mpm
    WHERE mpm.model_id = m.id
    ORDER BY evaluated_at DESC
    LIMIT 1
) latest_perf ON true
LEFT JOIN (
    SELECT 
        model_id,
        AVG(accuracy) as avg_accuracy
    FROM model_performance_metrics
    WHERE evaluated_at >= CURRENT_TIMESTAMP - INTERVAL '30 days'
    GROUP BY model_id
) avg_perf ON avg_perf.model_id = m.id;

-- Recommendation effectiveness view
CREATE OR REPLACE VIEW recommendation_effectiveness AS
SELECT 
    recommendation_type,
    target_component,
    COUNT(*) as total_recommendations,
    COUNT(CASE WHEN status = 'implemented' THEN 1 END) as implemented_count,
    COUNT(CASE WHEN status = 'implemented' THEN 1 END)::DECIMAL / COUNT(*) as implementation_rate,
    AVG(CASE WHEN effectiveness_score IS NOT NULL THEN effectiveness_score END) as avg_effectiveness,
    AVG(priority_score) as avg_priority
FROM optimization_recommendations
WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '90 days'
GROUP BY recommendation_type, target_component
ORDER BY implementation_rate DESC, avg_effectiveness DESC;

-- Grant permissions (adjust as needed for your security model)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO pattern_analysis_user;
-- GRANT SELECT ON ALL VIEWS IN SCHEMA public TO pattern_analysis_readonly;

