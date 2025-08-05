-- Enhanced Database Schema: Pattern Recognition and Analytics
-- Part 3: Pattern Detection, Predictions, and Recommendations

-- Identified Patterns Table
CREATE TABLE identified_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_type VARCHAR(100) NOT NULL, -- 'code_smell', 'performance_bottleneck', 'usage_pattern', 'security_vulnerability'
    pattern_name VARCHAR(255) NOT NULL,
    pattern_description TEXT,
    detection_algorithm VARCHAR(100), -- Algorithm used to detect this pattern
    confidence_score DECIMAL(3,2), -- 0.00 to 1.00
    pattern_signature JSONB, -- Unique characteristics of the pattern
    pattern_rules JSONB, -- Rules or conditions that define the pattern
    occurrence_frequency INTEGER DEFAULT 1,
    first_detected TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_detected TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    severity_level VARCHAR(50), -- 'low', 'medium', 'high', 'critical'
    impact_metrics JSONB, -- Performance impact, maintainability impact, etc.
    remediation_suggestions JSONB, -- Suggested fixes or improvements
    status VARCHAR(50) DEFAULT 'active', -- 'active', 'resolved', 'ignored', 'false_positive'
    auto_fix_available BOOLEAN DEFAULT false,
    category_tags VARCHAR(255)[], -- Array of category tags
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CHECK (confidence_score >= 0.00 AND confidence_score <= 1.00),
    CHECK (occurrence_frequency >= 0),
    CHECK (severity_level IN ('low', 'medium', 'high', 'critical')),
    CHECK (status IN ('active', 'resolved', 'ignored', 'false_positive', 'investigating')),
    CHECK (pattern_type IN ('code_smell', 'performance_bottleneck', 'usage_pattern', 'security_vulnerability', 'design_pattern', 'anti_pattern'))
);

-- Indexes for identified_patterns
CREATE INDEX idx_patterns_type_status ON identified_patterns(pattern_type, status);
CREATE INDEX idx_patterns_confidence ON identified_patterns(confidence_score DESC);
CREATE INDEX idx_patterns_severity ON identified_patterns(severity_level);
CREATE INDEX idx_patterns_last_detected ON identified_patterns(last_detected);
CREATE INDEX idx_patterns_signature ON identified_patterns USING GIN(pattern_signature);
CREATE INDEX idx_patterns_tags ON identified_patterns USING GIN(category_tags);
CREATE INDEX idx_patterns_frequency ON identified_patterns(occurrence_frequency DESC);

-- Pattern Occurrences Table
CREATE TABLE pattern_occurrences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_id UUID NOT NULL REFERENCES identified_patterns(id) ON DELETE CASCADE,
    source_type VARCHAR(100) NOT NULL, -- 'git_commit', 'code_file', 'user_session', 'api_call'
    source_id VARCHAR(255) NOT NULL, -- ID of the source entity
    location_data JSONB, -- File path, line numbers, function names, etc.
    context_data JSONB, -- Surrounding code or environmental context
    detection_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    detection_model_id UUID REFERENCES ml_models(id),
    confidence_score DECIMAL(3,2),
    severity_override VARCHAR(50), -- Override severity for this specific occurrence
    resolution_status VARCHAR(50) DEFAULT 'open', -- 'open', 'in_progress', 'resolved', 'wont_fix'
    resolution_timestamp TIMESTAMP WITH TIME ZONE,
    resolution_method VARCHAR(100), -- 'manual_fix', 'auto_fix', 'refactoring', 'configuration_change'
    resolution_notes TEXT,
    metadata JSONB, -- Additional context-specific data
    
    CHECK (confidence_score >= 0.00 AND confidence_score <= 1.00),
    CHECK (severity_override IN ('low', 'medium', 'high', 'critical') OR severity_override IS NULL),
    CHECK (resolution_status IN ('open', 'in_progress', 'resolved', 'wont_fix', 'duplicate')),
    CHECK (resolution_timestamp IS NULL OR resolution_timestamp >= detection_timestamp)
);

-- Indexes for pattern_occurrences
CREATE INDEX idx_pattern_occurrences_pattern ON pattern_occurrences(pattern_id);
CREATE INDEX idx_pattern_occurrences_source ON pattern_occurrences(source_type, source_id);
CREATE INDEX idx_pattern_occurrences_timestamp ON pattern_occurrences(detection_timestamp);
CREATE INDEX idx_pattern_occurrences_status ON pattern_occurrences(resolution_status);
CREATE INDEX idx_pattern_occurrences_model ON pattern_occurrences(detection_model_id);

-- Predictions Table
CREATE TABLE predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID NOT NULL REFERENCES ml_models(id),
    prediction_type VARCHAR(100) NOT NULL, -- 'performance_degradation', 'bug_likelihood', 'optimization_opportunity'
    target_entity_type VARCHAR(100), -- 'code_file', 'function', 'repository', 'user', 'system'
    target_entity_id VARCHAR(255),
    predicted_value JSONB, -- The actual prediction (could be numeric, categorical, or complex)
    confidence_interval JSONB, -- Statistical confidence bounds
    prediction_horizon INTEGER, -- How far into the future (in days/hours)
    prediction_horizon_unit VARCHAR(20) DEFAULT 'days', -- 'minutes', 'hours', 'days', 'weeks'
    input_features JSONB, -- Features used to make the prediction
    prediction_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    prediction_expires_at TIMESTAMP WITH TIME ZONE,
    actual_outcome JSONB, -- Filled in later when outcome is known
    outcome_timestamp TIMESTAMP WITH TIME ZONE,
    accuracy_score DECIMAL(3,2), -- Calculated when actual outcome is available
    feedback_received JSONB, -- User feedback on prediction quality
    status VARCHAR(50) DEFAULT 'active', -- 'active', 'validated', 'invalidated', 'expired'
    priority_score DECIMAL(3,2), -- 0.00 to 1.00, how important this prediction is
    action_recommended JSONB, -- Recommended actions based on prediction
    
    CHECK (prediction_horizon > 0),
    CHECK (prediction_horizon_unit IN ('minutes', 'hours', 'days', 'weeks', 'months')),
    CHECK (accuracy_score >= 0.00 AND accuracy_score <= 1.00),
    CHECK (priority_score >= 0.00 AND priority_score <= 1.00),
    CHECK (status IN ('active', 'validated', 'invalidated', 'expired', 'monitoring')),
    CHECK (prediction_type IN ('performance_degradation', 'bug_likelihood', 'optimization_opportunity', 'resource_usage', 'user_behavior', 'system_failure'))
);

-- Indexes for predictions
CREATE INDEX idx_predictions_model ON predictions(model_id);
CREATE INDEX idx_predictions_type ON predictions(prediction_type);
CREATE INDEX idx_predictions_target ON predictions(target_entity_type, target_entity_id);
CREATE INDEX idx_predictions_timestamp ON predictions(prediction_timestamp);
CREATE INDEX idx_predictions_status ON predictions(status);
CREATE INDEX idx_predictions_priority ON predictions(priority_score DESC);
CREATE INDEX idx_predictions_expires ON predictions(prediction_expires_at);

-- Recommendations Table
CREATE TABLE recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recommendation_type VARCHAR(100) NOT NULL, -- 'code_optimization', 'refactoring', 'security_fix', 'performance_improvement'
    title VARCHAR(255) NOT NULL,
    description TEXT,
    target_entity_type VARCHAR(100), -- 'code_file', 'function', 'repository', 'configuration'
    target_entity_id VARCHAR(255),
    recommendation_data JSONB, -- Specific recommendation details
    confidence_score DECIMAL(3,2), -- 0.00 to 1.00
    impact_estimate JSONB, -- Estimated impact of implementing recommendation
    effort_estimate JSONB, -- Estimated effort required
    priority_score DECIMAL(3,2), -- 0.00 to 1.00
    source_pattern_id UUID REFERENCES identified_patterns(id),
    source_prediction_id UUID REFERENCES predictions(id),
    generated_by_model_id UUID REFERENCES ml_models(id),
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'accepted', 'rejected', 'implemented', 'expired'
    implementation_status VARCHAR(50), -- 'not_started', 'in_progress', 'completed', 'failed'
    implementation_notes TEXT,
    user_feedback JSONB, -- User feedback on recommendation quality
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    implemented_at TIMESTAMP WITH TIME ZONE,
    created_by VARCHAR(255),
    assigned_to VARCHAR(255),
    
    CHECK (confidence_score >= 0.00 AND confidence_score <= 1.00),
    CHECK (priority_score >= 0.00 AND priority_score <= 1.00),
    CHECK (status IN ('pending', 'accepted', 'rejected', 'implemented', 'expired', 'reviewing')),
    CHECK (implementation_status IN ('not_started', 'in_progress', 'completed', 'failed', 'cancelled')),
    CHECK (recommendation_type IN ('code_optimization', 'refactoring', 'security_fix', 'performance_improvement', 'documentation', 'testing'))
);

-- Indexes for recommendations
CREATE INDEX idx_recommendations_type ON recommendations(recommendation_type);
CREATE INDEX idx_recommendations_target ON recommendations(target_entity_type, target_entity_id);
CREATE INDEX idx_recommendations_status ON recommendations(status);
CREATE INDEX idx_recommendations_priority ON recommendations(priority_score DESC);
CREATE INDEX idx_recommendations_pattern ON recommendations(source_pattern_id);
CREATE INDEX idx_recommendations_prediction ON recommendations(source_prediction_id);
CREATE INDEX idx_recommendations_assigned ON recommendations(assigned_to);
CREATE INDEX idx_recommendations_created_at ON recommendations(created_at);

-- A/B Testing Experiments Table
CREATE TABLE ab_testing_experiments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    hypothesis TEXT,
    feature_flag VARCHAR(255), -- Feature flag controlling the experiment
    control_variant JSONB, -- Configuration for control group
    treatment_variants JSONB, -- Array of treatment configurations
    target_metrics JSONB, -- What metrics we're trying to optimize
    traffic_allocation JSONB, -- How traffic is split between variants
    start_date TIMESTAMP WITH TIME ZONE,
    end_date TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'draft', -- 'draft', 'running', 'completed', 'cancelled', 'paused'
    statistical_power DECIMAL(3,2) DEFAULT 0.80,
    significance_level DECIMAL(3,2) DEFAULT 0.05,
    minimum_sample_size INTEGER,
    current_sample_size INTEGER DEFAULT 0,
    results JSONB, -- Statistical results when experiment completes
    winner_variant VARCHAR(100), -- Which variant won (if any)
    confidence_interval JSONB, -- Confidence intervals for results
    p_value DECIMAL(10,8), -- Statistical significance
    effect_size DECIMAL(6,4), -- Practical significance
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(255),
    
    CHECK (status IN ('draft', 'running', 'completed', 'cancelled', 'paused')),
    CHECK (statistical_power >= 0.50 AND statistical_power <= 0.99),
    CHECK (significance_level >= 0.01 AND significance_level <= 0.10),
    CHECK (minimum_sample_size > 0),
    CHECK (current_sample_size >= 0),
    CHECK (end_date IS NULL OR end_date > start_date),
    CHECK (p_value >= 0.0 AND p_value <= 1.0)
);

-- Indexes for ab_testing_experiments
CREATE INDEX idx_ab_experiments_status ON ab_testing_experiments(status);
CREATE INDEX idx_ab_experiments_dates ON ab_testing_experiments(start_date, end_date);
CREATE INDEX idx_ab_experiments_feature_flag ON ab_testing_experiments(feature_flag);
CREATE INDEX idx_ab_experiments_created_by ON ab_testing_experiments(created_by);

-- A/B Testing Assignments Table
CREATE TABLE ab_testing_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id UUID NOT NULL REFERENCES ab_testing_experiments(id) ON DELETE CASCADE,
    user_id VARCHAR(255) NOT NULL,
    variant VARCHAR(100) NOT NULL,
    assignment_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    session_id VARCHAR(255),
    user_agent TEXT,
    ip_address INET,
    geographic_location JSONB, -- Country, region, city
    device_info JSONB, -- Device type, OS, browser
    metadata JSONB,
    
    UNIQUE(experiment_id, user_id)
);

-- Indexes for ab_testing_assignments
CREATE INDEX idx_ab_assignments_experiment ON ab_testing_assignments(experiment_id);
CREATE INDEX idx_ab_assignments_user ON ab_testing_assignments(user_id);
CREATE INDEX idx_ab_assignments_variant ON ab_testing_assignments(experiment_id, variant);
CREATE INDEX idx_ab_assignments_timestamp ON ab_testing_assignments(assignment_timestamp);

-- A/B Testing Metrics Table
CREATE TABLE ab_testing_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id UUID NOT NULL REFERENCES ab_testing_experiments(id) ON DELETE CASCADE,
    assignment_id UUID NOT NULL REFERENCES ab_testing_assignments(id) ON DELETE CASCADE,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,6) NOT NULL,
    metric_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    session_id VARCHAR(255),
    additional_context JSONB,
    
    UNIQUE(assignment_id, metric_name, metric_timestamp)
);

-- Indexes for ab_testing_metrics
CREATE INDEX idx_ab_metrics_experiment ON ab_testing_metrics(experiment_id);
CREATE INDEX idx_ab_metrics_assignment ON ab_testing_metrics(assignment_id);
CREATE INDEX idx_ab_metrics_name ON ab_testing_metrics(metric_name);
CREATE INDEX idx_ab_metrics_timestamp ON ab_testing_metrics(metric_timestamp);

-- Pattern Evolution Tracking Table
CREATE TABLE pattern_evolution (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_id UUID NOT NULL REFERENCES identified_patterns(id) ON DELETE CASCADE,
    evolution_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    change_type VARCHAR(100) NOT NULL, -- 'frequency_increase', 'frequency_decrease', 'severity_change', 'new_variant'
    previous_state JSONB, -- Previous pattern state
    new_state JSONB, -- New pattern state
    change_magnitude DECIMAL(5,2), -- How significant the change is
    contributing_factors JSONB, -- What caused the change
    impact_assessment JSONB, -- Assessment of the change impact
    automated_response JSONB, -- Any automated responses triggered
    
    CHECK (change_type IN ('frequency_increase', 'frequency_decrease', 'severity_change', 'new_variant', 'pattern_merge', 'pattern_split')),
    CHECK (change_magnitude >= 0.0)
);

-- Indexes for pattern_evolution
CREATE INDEX idx_pattern_evolution_pattern ON pattern_evolution(pattern_id);
CREATE INDEX idx_pattern_evolution_timestamp ON pattern_evolution(evolution_timestamp);
CREATE INDEX idx_pattern_evolution_type ON pattern_evolution(change_type);
CREATE INDEX idx_pattern_evolution_magnitude ON pattern_evolution(change_magnitude DESC);

-- Materialized View for Pattern Analytics
CREATE MATERIALIZED VIEW pattern_analytics_summary AS
SELECT 
    p.pattern_type,
    p.severity_level,
    COUNT(p.id) as pattern_count,
    COUNT(po.id) as total_occurrences,
    AVG(p.confidence_score) as avg_confidence,
    COUNT(CASE WHEN po.resolution_status = 'resolved' THEN 1 END) as resolved_count,
    COUNT(CASE WHEN po.resolution_status = 'open' THEN 1 END) as open_count,
    AVG(EXTRACT(EPOCH FROM (po.resolution_timestamp - po.detection_timestamp))/3600) as avg_resolution_time_hours,
    MAX(p.last_detected) as most_recent_detection
FROM identified_patterns p
LEFT JOIN pattern_occurrences po ON p.id = po.pattern_id
GROUP BY p.pattern_type, p.severity_level;

CREATE UNIQUE INDEX idx_pattern_analytics_summary ON pattern_analytics_summary(pattern_type, severity_level);

-- Trigger to update updated_at timestamps
CREATE TRIGGER update_patterns_updated_at BEFORE UPDATE ON identified_patterns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_recommendations_updated_at BEFORE UPDATE ON recommendations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ab_experiments_updated_at BEFORE UPDATE ON ab_testing_experiments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to calculate recommendation priority
CREATE OR REPLACE FUNCTION calculate_recommendation_priority(
    confidence DECIMAL(3,2),
    impact_score DECIMAL(3,2),
    effort_score DECIMAL(3,2)
) RETURNS DECIMAL(3,2) AS $$
BEGIN
    -- Priority = (Confidence * Impact) / Effort
    -- Normalized to 0.00-1.00 scale
    RETURN LEAST(1.00, (confidence * impact_score) / GREATEST(0.01, effort_score));
END;
$$ LANGUAGE plpgsql;

-- Function to auto-expire old predictions
CREATE OR REPLACE FUNCTION expire_old_predictions()
RETURNS INTEGER AS $$
DECLARE
    expired_count INTEGER;
BEGIN
    UPDATE predictions 
    SET status = 'expired'
    WHERE status = 'active' 
    AND prediction_expires_at < NOW()
    AND prediction_expires_at IS NOT NULL;
    
    GET DIAGNOSTICS expired_count = ROW_COUNT;
    RETURN expired_count;
END;
$$ LANGUAGE plpgsql;

-- Schedule prediction expiration job (runs daily)
SELECT cron.schedule('expire-predictions', '0 1 * * *', 'SELECT expire_old_predictions();');

-- Comments for documentation
COMMENT ON TABLE identified_patterns IS 'Catalog of detected patterns in code, usage, and system behavior';
COMMENT ON TABLE pattern_occurrences IS 'Specific instances where patterns were detected';
COMMENT ON TABLE predictions IS 'ML model predictions about future system behavior';
COMMENT ON TABLE recommendations IS 'Actionable recommendations based on patterns and predictions';
COMMENT ON TABLE ab_testing_experiments IS 'A/B testing experiments for feature validation';
COMMENT ON TABLE ab_testing_assignments IS 'User assignments to A/B test variants';
COMMENT ON TABLE ab_testing_metrics IS 'Metrics collected during A/B testing';
COMMENT ON TABLE pattern_evolution IS 'Tracking how patterns change over time';

