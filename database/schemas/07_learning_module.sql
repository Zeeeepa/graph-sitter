-- =============================================================================
-- LEARNING MODULE: Pattern Recognition and Continuous Improvement
-- =============================================================================
-- This module implements the 7th database component for continuous learning,
-- pattern recognition, and system improvement tracking. It integrates with
-- OpenEvolve for autonomous system enhancement and adaptation.
-- =============================================================================

-- Learning-specific enums
CREATE TYPE learning_model_type AS ENUM (
    'code_quality_predictor',
    'task_duration_estimator',
    'bug_probability_classifier',
    'performance_optimizer',
    'pattern_recognizer',
    'workflow_optimizer',
    'resource_predictor',
    'quality_scorer',
    'complexity_analyzer',
    'dependency_analyzer',
    'custom'
);

CREATE TYPE learning_algorithm AS ENUM (
    'neural_network',
    'random_forest',
    'gradient_boosting',
    'linear_regression',
    'logistic_regression',
    'svm',
    'clustering',
    'reinforcement_learning',
    'genetic_algorithm',
    'ensemble',
    'custom'
);

CREATE TYPE training_status AS ENUM (
    'pending',
    'preparing_data',
    'training',
    'validating',
    'completed',
    'failed',
    'cancelled',
    'deployed',
    'retired'
);

CREATE TYPE feedback_type AS ENUM (
    'accuracy',
    'performance',
    'user_satisfaction',
    'business_impact',
    'system_improvement',
    'error_correction',
    'feature_importance',
    'model_drift',
    'custom'
);

-- =============================================================================
-- LEARNING MODELS AND VERSIONS
-- =============================================================================

-- Learning models registry
CREATE TABLE learning_models (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Model identification
    name VARCHAR(255) NOT NULL,
    description TEXT,
    model_type learning_model_type NOT NULL,
    algorithm learning_algorithm NOT NULL,
    
    -- Model configuration
    hyperparameters JSONB DEFAULT '{}',
    feature_config JSONB DEFAULT '{}',
    training_config JSONB DEFAULT '{}',
    
    -- Model status and versioning
    current_version INTEGER DEFAULT 1,
    status status_type DEFAULT 'active',
    is_production BOOLEAN DEFAULT false,
    
    -- Performance metrics
    accuracy DECIMAL(5,4),
    precision_score DECIMAL(5,4),
    recall_score DECIMAL(5,4),
    f1_score DECIMAL(5,4),
    
    -- Usage statistics
    prediction_count BIGINT DEFAULT 0,
    last_prediction_at TIMESTAMP WITH TIME ZONE,
    training_count INTEGER DEFAULT 0,
    last_training_at TIMESTAMP WITH TIME ZONE,
    
    -- Integration points
    target_modules VARCHAR(100)[], -- tasks, analytics, prompts, etc.
    integration_config JSONB DEFAULT '{}',
    
    -- Metadata
    tags VARCHAR(50)[],
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT learning_models_name_org_unique UNIQUE (organization_id, name),
    CONSTRAINT learning_models_name_not_empty CHECK (length(trim(name)) > 0),
    CONSTRAINT learning_models_version_positive CHECK (current_version > 0)
);

-- Model versions for tracking evolution
CREATE TABLE model_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID NOT NULL REFERENCES learning_models(id) ON DELETE CASCADE,
    
    -- Version information
    version_number INTEGER NOT NULL,
    version_name VARCHAR(255),
    description TEXT,
    
    -- Model artifacts
    model_data BYTEA, -- Serialized model
    model_path TEXT, -- External storage path
    model_size_bytes BIGINT,
    model_checksum VARCHAR(64),
    
    -- Training information
    training_data_hash VARCHAR(64),
    training_duration_ms BIGINT,
    training_samples_count BIGINT,
    validation_samples_count BIGINT,
    
    -- Performance metrics
    training_accuracy DECIMAL(5,4),
    validation_accuracy DECIMAL(5,4),
    test_accuracy DECIMAL(5,4),
    performance_metrics JSONB DEFAULT '{}',
    
    -- Configuration
    hyperparameters JSONB DEFAULT '{}',
    feature_importance JSONB DEFAULT '{}',
    
    -- Deployment information
    deployed_at TIMESTAMP WITH TIME ZONE,
    retired_at TIMESTAMP WITH TIME ZONE,
    deployment_config JSONB DEFAULT '{}',
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT model_versions_unique UNIQUE (model_id, version_number),
    CONSTRAINT model_versions_version_positive CHECK (version_number > 0)
);

-- =============================================================================
-- TRAINING AND LEARNING SESSIONS
-- =============================================================================

-- Training sessions for model development
CREATE TABLE training_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID NOT NULL REFERENCES learning_models(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Session identification
    session_name VARCHAR(255),
    description TEXT,
    session_type VARCHAR(100) DEFAULT 'full_training', -- full_training, incremental, fine_tuning
    
    -- Training configuration
    algorithm learning_algorithm NOT NULL,
    hyperparameters JSONB DEFAULT '{}',
    training_config JSONB DEFAULT '{}',
    
    -- Data information
    training_data_source VARCHAR(255),
    training_samples_count BIGINT,
    validation_samples_count BIGINT,
    test_samples_count BIGINT,
    feature_count INTEGER,
    
    -- Training progress and status
    status training_status DEFAULT 'pending',
    progress_percentage DECIMAL(5,2) DEFAULT 0,
    current_epoch INTEGER DEFAULT 0,
    total_epochs INTEGER,
    
    -- Performance tracking
    best_accuracy DECIMAL(5,4),
    current_accuracy DECIMAL(5,4),
    loss_value DECIMAL(10,6),
    validation_loss DECIMAL(10,6),
    
    -- Resource usage
    cpu_usage_percent DECIMAL(5,2),
    memory_usage_mb BIGINT,
    gpu_usage_percent DECIMAL(5,2),
    
    -- Timing information
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    estimated_completion_at TIMESTAMP WITH TIME ZONE,
    duration_ms BIGINT,
    
    -- Results and artifacts
    final_metrics JSONB DEFAULT '{}',
    training_log TEXT,
    error_message TEXT,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Training metrics for detailed tracking
CREATE TABLE training_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    training_session_id UUID NOT NULL REFERENCES training_sessions(id) ON DELETE CASCADE,
    
    -- Metric identification
    metric_name VARCHAR(255) NOT NULL,
    metric_type VARCHAR(100) NOT NULL, -- accuracy, loss, precision, recall, custom
    
    -- Metric values
    value DECIMAL(15,6) NOT NULL,
    epoch INTEGER,
    batch INTEGER,
    step BIGINT,
    
    -- Context
    dataset_split VARCHAR(50), -- train, validation, test
    
    -- Timing
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Metadata
    metadata JSONB DEFAULT '{}'
);

-- =============================================================================
-- PREDICTIONS AND INFERENCE
-- =============================================================================

-- Model predictions and inference results
CREATE TABLE model_predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID NOT NULL REFERENCES learning_models(id) ON DELETE CASCADE,
    model_version_id UUID REFERENCES model_versions(id),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Prediction context
    prediction_type VARCHAR(100), -- real_time, batch, scheduled
    request_id VARCHAR(255),
    
    -- Input data
    input_features JSONB NOT NULL,
    input_hash VARCHAR(64),
    
    -- Prediction results
    prediction_value JSONB NOT NULL,
    confidence_score DECIMAL(5,4),
    probability_distribution JSONB DEFAULT '{}',
    
    -- Model information
    model_version INTEGER,
    inference_time_ms INTEGER,
    
    -- Context and associations
    related_task_id UUID,
    related_project_id UUID,
    related_analysis_id UUID,
    
    -- Feedback and validation
    actual_value JSONB,
    feedback_score DECIMAL(5,4),
    is_correct BOOLEAN,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    predicted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    feedback_received_at TIMESTAMP WITH TIME ZONE
);

-- =============================================================================
-- FEEDBACK AND CONTINUOUS LEARNING
-- =============================================================================

-- Feedback collection for model improvement
CREATE TABLE learning_feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID NOT NULL REFERENCES learning_models(id) ON DELETE CASCADE,
    prediction_id UUID REFERENCES model_predictions(id),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Feedback source
    feedback_source VARCHAR(100), -- user, system, automated, external
    source_user_id UUID REFERENCES users(id),
    source_system VARCHAR(255),
    
    -- Feedback content
    feedback_type feedback_type NOT NULL,
    feedback_value JSONB NOT NULL,
    feedback_score DECIMAL(5,4),
    
    -- Context
    context JSONB DEFAULT '{}',
    related_entities JSONB DEFAULT '{}',
    
    -- Feedback details
    is_positive BOOLEAN,
    confidence DECIMAL(5,4),
    explanation TEXT,
    
    -- Processing status
    processed BOOLEAN DEFAULT false,
    processed_at TIMESTAMP WITH TIME ZONE,
    impact_score DECIMAL(5,4),
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Pattern recognition and insights
CREATE TABLE learning_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Pattern identification
    pattern_name VARCHAR(255) NOT NULL,
    pattern_type VARCHAR(100) NOT NULL, -- code_pattern, workflow_pattern, performance_pattern
    description TEXT,
    
    -- Pattern data
    pattern_definition JSONB NOT NULL,
    pattern_examples JSONB DEFAULT '[]',
    pattern_metrics JSONB DEFAULT '{}',
    
    -- Discovery information
    discovered_by VARCHAR(100), -- algorithm, user, system
    discovery_method VARCHAR(255),
    confidence_score DECIMAL(5,4),
    
    -- Pattern statistics
    occurrence_count INTEGER DEFAULT 0,
    success_rate DECIMAL(5,4),
    impact_score DECIMAL(5,4),
    
    -- Validation
    validated BOOLEAN DEFAULT false,
    validated_by UUID REFERENCES users(id),
    validated_at TIMESTAMP WITH TIME ZONE,
    
    -- Usage tracking
    applied_count INTEGER DEFAULT 0,
    last_applied_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    tags VARCHAR(50)[],
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- SYSTEM ADAPTATIONS AND IMPROVEMENTS
-- =============================================================================

-- System adaptations based on learning
CREATE TABLE system_adaptations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Adaptation identification
    adaptation_name VARCHAR(255) NOT NULL,
    adaptation_type VARCHAR(100) NOT NULL, -- workflow, configuration, algorithm, process
    description TEXT,
    
    -- Source information
    triggered_by VARCHAR(100), -- learning_model, pattern, feedback, analysis
    source_model_id UUID REFERENCES learning_models(id),
    source_pattern_id UUID REFERENCES learning_patterns(id),
    
    -- Adaptation details
    target_component VARCHAR(255), -- tasks, analytics, prompts, etc.
    adaptation_config JSONB NOT NULL,
    previous_config JSONB,
    
    -- Impact and metrics
    expected_improvement DECIMAL(5,4),
    actual_improvement DECIMAL(5,4),
    impact_metrics JSONB DEFAULT '{}',
    
    -- Implementation status
    status VARCHAR(50) DEFAULT 'proposed', -- proposed, approved, implementing, deployed, rolled_back
    implemented_at TIMESTAMP WITH TIME ZONE,
    rollback_at TIMESTAMP WITH TIME ZONE,
    
    -- Approval workflow
    approved_by UUID REFERENCES users(id),
    approved_at TIMESTAMP WITH TIME ZONE,
    approval_notes TEXT,
    
    -- Monitoring
    monitoring_period_days INTEGER DEFAULT 30,
    monitoring_metrics JSONB DEFAULT '{}',
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Learning insights and recommendations
CREATE TABLE learning_insights (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Insight identification
    insight_title VARCHAR(255) NOT NULL,
    insight_type VARCHAR(100) NOT NULL, -- performance, quality, efficiency, cost
    category VARCHAR(100), -- code_quality, workflow, resource_usage
    
    -- Insight content
    description TEXT NOT NULL,
    detailed_analysis JSONB DEFAULT '{}',
    supporting_data JSONB DEFAULT '{}',
    
    -- Confidence and impact
    confidence_score DECIMAL(5,4) NOT NULL,
    impact_score DECIMAL(5,4),
    priority priority_level DEFAULT 'normal',
    
    -- Recommendations
    recommendations JSONB DEFAULT '[]',
    action_items JSONB DEFAULT '[]',
    
    -- Source information
    generated_by VARCHAR(100), -- model, algorithm, analysis
    source_models UUID[],
    source_data_period TSTZRANGE,
    
    -- Status and tracking
    status VARCHAR(50) DEFAULT 'new', -- new, reviewed, accepted, implemented, dismissed
    reviewed_by UUID REFERENCES users(id),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    review_notes TEXT,
    
    -- Implementation tracking
    implemented BOOLEAN DEFAULT false,
    implementation_notes TEXT,
    
    -- Metadata
    tags VARCHAR(50)[],
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- OPENEVOLVE INTEGRATION
-- =============================================================================

-- OpenEvolve evaluation sessions
CREATE TABLE openevolve_evaluations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Evaluation identification
    evaluation_name VARCHAR(255) NOT NULL,
    evaluation_type VARCHAR(100) NOT NULL, -- code_generation, optimization, analysis
    description TEXT,
    
    -- Target information
    target_component VARCHAR(255), -- specific component being evaluated
    target_config JSONB DEFAULT '{}',
    
    -- Evaluation parameters
    population_size INTEGER DEFAULT 50,
    generations INTEGER DEFAULT 100,
    mutation_rate DECIMAL(5,4) DEFAULT 0.1,
    crossover_rate DECIMAL(5,4) DEFAULT 0.8,
    
    -- Fitness function
    fitness_function VARCHAR(255),
    fitness_config JSONB DEFAULT '{}',
    
    -- Progress tracking
    current_generation INTEGER DEFAULT 0,
    best_fitness DECIMAL(10,6),
    average_fitness DECIMAL(10,6),
    convergence_threshold DECIMAL(10,6),
    
    -- Status and timing
    status training_status DEFAULT 'pending',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    estimated_completion_at TIMESTAMP WITH TIME ZONE,
    
    -- Results
    best_solution JSONB,
    final_metrics JSONB DEFAULT '{}',
    evolution_history JSONB DEFAULT '[]',
    
    -- Resource usage
    cpu_time_ms BIGINT,
    memory_usage_mb BIGINT,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- OpenEvolve generation tracking
CREATE TABLE openevolve_generations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    evaluation_id UUID NOT NULL REFERENCES openevolve_evaluations(id) ON DELETE CASCADE,
    
    -- Generation information
    generation_number INTEGER NOT NULL,
    population_size INTEGER NOT NULL,
    
    -- Fitness statistics
    best_fitness DECIMAL(10,6),
    worst_fitness DECIMAL(10,6),
    average_fitness DECIMAL(10,6),
    fitness_variance DECIMAL(10,6),
    
    -- Population diversity
    diversity_score DECIMAL(5,4),
    convergence_score DECIMAL(5,4),
    
    -- Best individual
    best_individual JSONB,
    best_individual_metrics JSONB DEFAULT '{}',
    
    -- Generation timing
    generation_start_at TIMESTAMP WITH TIME ZONE,
    generation_end_at TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT openevolve_generations_unique UNIQUE (evaluation_id, generation_number)
);

-- =============================================================================
-- TRIGGERS AND FUNCTIONS
-- =============================================================================

-- Update timestamps
CREATE TRIGGER update_learning_models_updated_at 
    BEFORE UPDATE ON learning_models 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_training_sessions_updated_at 
    BEFORE UPDATE ON training_sessions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_learning_patterns_updated_at 
    BEFORE UPDATE ON learning_patterns 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_system_adaptations_updated_at 
    BEFORE UPDATE ON system_adaptations 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_learning_insights_updated_at 
    BEFORE UPDATE ON learning_insights 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_openevolve_evaluations_updated_at 
    BEFORE UPDATE ON openevolve_evaluations 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to update model statistics
CREATE OR REPLACE FUNCTION update_model_statistics()
RETURNS TRIGGER AS $$
BEGIN
    -- Update prediction count and last prediction time
    UPDATE learning_models 
    SET 
        prediction_count = prediction_count + 1,
        last_prediction_at = NEW.predicted_at
    WHERE id = NEW.model_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update model statistics on new predictions
CREATE TRIGGER update_model_stats_on_prediction
    AFTER INSERT ON model_predictions
    FOR EACH ROW EXECUTE FUNCTION update_model_statistics();

-- Function to process learning feedback
CREATE OR REPLACE FUNCTION process_learning_feedback()
RETURNS TRIGGER AS $$
DECLARE
    feedback_count INTEGER;
    avg_score DECIMAL(5,4);
BEGIN
    -- Mark as processed
    NEW.processed := true;
    NEW.processed_at := NOW();
    
    -- Calculate impact score based on feedback type and value
    NEW.impact_score := CASE 
        WHEN NEW.feedback_type = 'accuracy' THEN NEW.feedback_score * 1.0
        WHEN NEW.feedback_type = 'user_satisfaction' THEN NEW.feedback_score * 0.8
        WHEN NEW.feedback_type = 'business_impact' THEN NEW.feedback_score * 1.2
        ELSE NEW.feedback_score * 0.5
    END;
    
    -- Update model performance metrics
    SELECT COUNT(*), AVG(feedback_score) 
    INTO feedback_count, avg_score
    FROM learning_feedback 
    WHERE model_id = NEW.model_id AND processed = true;
    
    -- Update model accuracy based on feedback
    UPDATE learning_models 
    SET accuracy = LEAST(1.0, GREATEST(0.0, avg_score))
    WHERE id = NEW.model_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to process feedback automatically
CREATE TRIGGER process_feedback_on_insert
    BEFORE INSERT ON learning_feedback
    FOR EACH ROW EXECUTE FUNCTION process_learning_feedback();

-- =============================================================================
-- INDEXES FOR OPTIMAL PERFORMANCE
-- =============================================================================

-- Learning models indexes
CREATE INDEX idx_learning_models_org_id ON learning_models(organization_id);
CREATE INDEX idx_learning_models_type ON learning_models(model_type);
CREATE INDEX idx_learning_models_status ON learning_models(status) WHERE deleted_at IS NULL;
CREATE INDEX idx_learning_models_production ON learning_models(is_production) WHERE is_production = true;
CREATE INDEX idx_learning_models_last_training ON learning_models(last_training_at);

-- Model versions indexes
CREATE INDEX idx_model_versions_model_id ON model_versions(model_id);
CREATE INDEX idx_model_versions_version ON model_versions(version_number);
CREATE INDEX idx_model_versions_deployed ON model_versions(deployed_at) WHERE deployed_at IS NOT NULL;

-- Training sessions indexes
CREATE INDEX idx_training_sessions_model_id ON training_sessions(model_id);
CREATE INDEX idx_training_sessions_org_id ON training_sessions(organization_id);
CREATE INDEX idx_training_sessions_status ON training_sessions(status);
CREATE INDEX idx_training_sessions_started ON training_sessions(started_at);

-- Training metrics indexes
CREATE INDEX idx_training_metrics_session_id ON training_metrics(training_session_id);
CREATE INDEX idx_training_metrics_name_type ON training_metrics(metric_name, metric_type);
CREATE INDEX idx_training_metrics_recorded_at ON training_metrics(recorded_at);

-- Model predictions indexes
CREATE INDEX idx_model_predictions_model_id ON model_predictions(model_id);
CREATE INDEX idx_model_predictions_org_id ON model_predictions(organization_id);
CREATE INDEX idx_model_predictions_predicted_at ON model_predictions(predicted_at);
CREATE INDEX idx_model_predictions_confidence ON model_predictions(confidence_score);
CREATE INDEX idx_model_predictions_feedback ON model_predictions(is_correct) WHERE is_correct IS NOT NULL;

-- Learning feedback indexes
CREATE INDEX idx_learning_feedback_model_id ON learning_feedback(model_id);
CREATE INDEX idx_learning_feedback_prediction_id ON learning_feedback(prediction_id);
CREATE INDEX idx_learning_feedback_type ON learning_feedback(feedback_type);
CREATE INDEX idx_learning_feedback_processed ON learning_feedback(processed, created_at);

-- Learning patterns indexes
CREATE INDEX idx_learning_patterns_org_id ON learning_patterns(organization_id);
CREATE INDEX idx_learning_patterns_type ON learning_patterns(pattern_type);
CREATE INDEX idx_learning_patterns_validated ON learning_patterns(validated);
CREATE INDEX idx_learning_patterns_confidence ON learning_patterns(confidence_score);

-- System adaptations indexes
CREATE INDEX idx_system_adaptations_org_id ON system_adaptations(organization_id);
CREATE INDEX idx_system_adaptations_type ON system_adaptations(adaptation_type);
CREATE INDEX idx_system_adaptations_status ON system_adaptations(status);
CREATE INDEX idx_system_adaptations_component ON system_adaptations(target_component);

-- Learning insights indexes
CREATE INDEX idx_learning_insights_org_id ON learning_insights(organization_id);
CREATE INDEX idx_learning_insights_type ON learning_insights(insight_type);
CREATE INDEX idx_learning_insights_status ON learning_insights(status);
CREATE INDEX idx_learning_insights_priority ON learning_insights(priority);
CREATE INDEX idx_learning_insights_confidence ON learning_insights(confidence_score);

-- OpenEvolve indexes
CREATE INDEX idx_openevolve_evaluations_org_id ON openevolve_evaluations(organization_id);
CREATE INDEX idx_openevolve_evaluations_status ON openevolve_evaluations(status);
CREATE INDEX idx_openevolve_evaluations_type ON openevolve_evaluations(evaluation_type);

CREATE INDEX idx_openevolve_generations_eval_id ON openevolve_generations(evaluation_id);
CREATE INDEX idx_openevolve_generations_number ON openevolve_generations(generation_number);

-- GIN indexes for JSONB fields
CREATE INDEX idx_learning_models_hyperparams_gin USING gin (hyperparameters);
CREATE INDEX idx_model_predictions_features_gin USING gin (input_features);
CREATE INDEX idx_learning_feedback_value_gin USING gin (feedback_value);
CREATE INDEX idx_learning_patterns_definition_gin USING gin (pattern_definition);
CREATE INDEX idx_system_adaptations_config_gin USING gin (adaptation_config);

-- =============================================================================
-- VIEWS FOR ANALYTICS AND REPORTING
-- =============================================================================

-- Model performance overview
CREATE VIEW model_performance_overview AS
SELECT 
    lm.id,
    lm.name,
    lm.model_type,
    lm.status,
    lm.accuracy,
    lm.prediction_count,
    lm.last_prediction_at,
    lm.training_count,
    lm.last_training_at,
    COUNT(mp.id) as total_predictions,
    COUNT(mp.id) FILTER (WHERE mp.is_correct = true) as correct_predictions,
    COUNT(lf.id) as feedback_count,
    AVG(lf.feedback_score) as avg_feedback_score
FROM learning_models lm
LEFT JOIN model_predictions mp ON lm.id = mp.model_id
LEFT JOIN learning_feedback lf ON lm.id = lf.model_id
WHERE lm.deleted_at IS NULL
GROUP BY lm.id, lm.name, lm.model_type, lm.status, lm.accuracy, 
         lm.prediction_count, lm.last_prediction_at, lm.training_count, lm.last_training_at;

-- Learning insights summary
CREATE VIEW learning_insights_summary AS
SELECT 
    insight_type,
    category,
    COUNT(*) as total_insights,
    COUNT(*) FILTER (WHERE status = 'new') as new_insights,
    COUNT(*) FILTER (WHERE status = 'implemented') as implemented_insights,
    AVG(confidence_score) as avg_confidence,
    AVG(impact_score) as avg_impact
FROM learning_insights
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY insight_type, category;

-- System adaptation tracking
CREATE VIEW adaptation_effectiveness AS
SELECT 
    adaptation_type,
    target_component,
    COUNT(*) as total_adaptations,
    COUNT(*) FILTER (WHERE status = 'deployed') as deployed_adaptations,
    AVG(expected_improvement) as avg_expected_improvement,
    AVG(actual_improvement) as avg_actual_improvement,
    AVG(actual_improvement - expected_improvement) as improvement_variance
FROM system_adaptations
WHERE created_at >= NOW() - INTERVAL '90 days'
GROUP BY adaptation_type, target_component;

-- =============================================================================
-- INITIAL DATA AND CONFIGURATION
-- =============================================================================

-- Insert default learning models for common use cases
INSERT INTO learning_models (
    organization_id, 
    name, 
    description, 
    model_type, 
    algorithm,
    hyperparameters,
    target_modules
) VALUES 
(
    (SELECT id FROM organizations WHERE slug = 'default' LIMIT 1),
    'Code Quality Predictor',
    'Predicts code quality scores based on complexity metrics and patterns',
    'code_quality_predictor',
    'random_forest',
    '{"n_estimators": 100, "max_depth": 10, "min_samples_split": 5}',
    ARRAY['analytics', 'codebase']
),
(
    (SELECT id FROM organizations WHERE slug = 'default' LIMIT 1),
    'Task Duration Estimator',
    'Estimates task completion time based on historical data and complexity',
    'task_duration_estimator',
    'gradient_boosting',
    '{"n_estimators": 200, "learning_rate": 0.1, "max_depth": 6}',
    ARRAY['tasks', 'projects']
),
(
    (SELECT id FROM organizations WHERE slug = 'default' LIMIT 1),
    'Pattern Recognizer',
    'Identifies common patterns in code and workflows for optimization',
    'pattern_recognizer',
    'clustering',
    '{"n_clusters": 10, "algorithm": "k-means", "max_iter": 300}',
    ARRAY['analytics', 'learning']
);

-- Record this migration
INSERT INTO schema_migrations (version, description, module) VALUES 
('07_learning_module', 'Learning DB module for continuous improvement and pattern recognition', 'learning');

-- =============================================================================
-- COMMENTS FOR DOCUMENTATION
-- =============================================================================

COMMENT ON TABLE learning_models IS 'Registry of machine learning models for continuous system improvement';
COMMENT ON TABLE model_versions IS 'Version tracking for model evolution and deployment';
COMMENT ON TABLE training_sessions IS 'Training session tracking with progress and performance metrics';
COMMENT ON TABLE training_metrics IS 'Detailed metrics collected during model training';
COMMENT ON TABLE model_predictions IS 'Model inference results and prediction tracking';
COMMENT ON TABLE learning_feedback IS 'Feedback collection for model improvement and validation';
COMMENT ON TABLE learning_patterns IS 'Discovered patterns for system optimization';
COMMENT ON TABLE system_adaptations IS 'System adaptations based on learning insights';
COMMENT ON TABLE learning_insights IS 'Generated insights and recommendations for improvement';
COMMENT ON TABLE openevolve_evaluations IS 'OpenEvolve evolutionary algorithm evaluation sessions';
COMMENT ON TABLE openevolve_generations IS 'Generation tracking for evolutionary algorithms';

-- Final status message
DO $$
BEGIN
    RAISE NOTICE '🧠 Learning Module initialized successfully!';
    RAISE NOTICE 'Features: Model management, Training tracking, Pattern recognition, OpenEvolve integration';
    RAISE NOTICE 'Default models: Code Quality Predictor, Task Duration Estimator, Pattern Recognizer';
    RAISE NOTICE 'Integration points: Analytics, Tasks, Projects, Codebase modules';
    RAISE NOTICE 'Timestamp: %', NOW();
END $$;

