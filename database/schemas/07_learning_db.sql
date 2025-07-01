-- =============================================================================
-- LEARNING DATABASE SCHEMA: Pattern Recognition and Improvement Tracking
-- =============================================================================
-- This database handles pattern recognition, improvement tracking, continuous
-- learning, and evolution integration for autonomous system enhancement.
-- =============================================================================

-- Connect to learning_db
\c learning_db;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "btree_gist";
CREATE EXTENSION IF NOT EXISTS "timescaledb" CASCADE; -- For time-series data

-- Set timezone and configuration
SET timezone = 'UTC';
SET default_text_search_config = 'pg_catalog.english';

-- Grant all privileges to learning_user
GRANT ALL PRIVILEGES ON DATABASE learning_db TO learning_user;
GRANT ALL PRIVILEGES ON SCHEMA public TO learning_user;

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
    'evolution_optimizer',
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
    'transformer',
    'lstm',
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
    'positive',
    'negative',
    'neutral',
    'correction',
    'enhancement',
    'bug_report'
);

CREATE TYPE adaptation_type AS ENUM (
    'parameter_tuning',
    'feature_engineering',
    'model_architecture',
    'training_data',
    'preprocessing',
    'postprocessing',
    'ensemble_weights',
    'hyperparameters'
);

CREATE TYPE evolution_stage AS ENUM (
    'initialization',
    'exploration',
    'exploitation',
    'adaptation',
    'convergence',
    'stagnation',
    'reset'
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

-- Users table for learning attribution
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
-- LEARNING MODELS MANAGEMENT
-- =============================================================================

-- Learning models registry
CREATE TABLE learning_models (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Model identification
    name VARCHAR(255) NOT NULL,
    description TEXT,
    model_type learning_model_type NOT NULL,
    
    -- Model configuration
    algorithm learning_algorithm NOT NULL,
    version VARCHAR(50) DEFAULT '1.0.0',
    
    -- Model architecture
    architecture_config JSONB DEFAULT '{}',
    hyperparameters JSONB DEFAULT '{}',
    feature_config JSONB DEFAULT '{}',
    
    -- Model status
    status training_status DEFAULT 'pending',
    is_active BOOLEAN DEFAULT false,
    is_production BOOLEAN DEFAULT false,
    
    -- Performance metrics
    accuracy DECIMAL(5,4),
    precision_score DECIMAL(5,4),
    recall_score DECIMAL(5,4),
    f1_score DECIMAL(5,4),
    
    -- Model metadata
    training_data_size INTEGER,
    validation_data_size INTEGER,
    test_data_size INTEGER,
    
    -- Model artifacts
    model_path TEXT,
    model_size_mb DECIMAL(10,2),
    model_checksum VARCHAR(64),
    
    -- Training information
    training_duration_minutes INTEGER,
    training_epochs INTEGER,
    training_cost_usd DECIMAL(10,4),
    
    -- Deployment information
    deployed_at TIMESTAMP WITH TIME ZONE,
    deployment_config JSONB DEFAULT '{}',
    
    -- Evolution tracking
    parent_model_id UUID REFERENCES learning_models(id),
    evolution_generation INTEGER DEFAULT 1,
    evolution_score DECIMAL(5,4),
    
    -- External references
    external_model_id VARCHAR(255),
    
    -- Metadata
    tags VARCHAR(50)[],
    metadata JSONB DEFAULT '{}',
    
    -- Ownership
    created_by UUID REFERENCES users(id),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT learning_models_name_org_unique UNIQUE (organization_id, name, version),
    CONSTRAINT learning_models_name_not_empty CHECK (length(trim(name)) > 0),
    CONSTRAINT learning_models_scores_valid CHECK (
        accuracy >= 0 AND accuracy <= 1 AND
        precision_score >= 0 AND precision_score <= 1 AND
        recall_score >= 0 AND recall_score <= 1 AND
        f1_score >= 0 AND f1_score <= 1
    ),
    CONSTRAINT learning_models_generation_positive CHECK (evolution_generation > 0)
);

-- =============================================================================
-- TRAINING SESSIONS AND EXPERIMENTS
-- =============================================================================

-- Training sessions for model development
CREATE TABLE training_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    learning_model_id UUID NOT NULL REFERENCES learning_models(id) ON DELETE CASCADE,
    
    -- Session identification
    session_name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Training configuration
    training_config JSONB DEFAULT '{}',
    data_config JSONB DEFAULT '{}',
    
    -- Session status
    status training_status DEFAULT 'pending',
    progress_percentage DECIMAL(5,2) DEFAULT 0,
    
    -- Timing
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_minutes INTEGER,
    
    -- Training data
    training_dataset_id UUID,
    validation_dataset_id UUID,
    test_dataset_id UUID,
    
    -- Training metrics (time-series)
    current_epoch INTEGER DEFAULT 0,
    total_epochs INTEGER,
    current_loss DECIMAL(10,6),
    best_loss DECIMAL(10,6),
    
    -- Performance tracking
    training_metrics JSONB DEFAULT '{}',
    validation_metrics JSONB DEFAULT '{}',
    
    -- Resource usage
    cpu_hours DECIMAL(8,2),
    gpu_hours DECIMAL(8,2),
    memory_peak_gb DECIMAL(8,2),
    
    -- Cost tracking
    training_cost_usd DECIMAL(10,4),
    
    -- Error handling
    error_message TEXT,
    warnings JSONB DEFAULT '[]',
    
    -- Triggered by
    triggered_by UUID REFERENCES users(id),
    trigger_source VARCHAR(100), -- manual, scheduled, evolution, experiment
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT training_sessions_progress_valid CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
    CONSTRAINT training_sessions_epochs_positive CHECK (current_epoch >= 0 AND total_epochs > 0)
);

-- Training metrics for detailed tracking (time-series)
CREATE TABLE training_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    training_session_id UUID NOT NULL REFERENCES training_sessions(id) ON DELETE CASCADE,
    
    -- Metric identification
    metric_name VARCHAR(255) NOT NULL,
    metric_type VARCHAR(100), -- loss, accuracy, precision, recall, etc.
    
    -- Metric value
    value DECIMAL(15,6) NOT NULL,
    
    -- Training context
    epoch INTEGER,
    batch INTEGER,
    step INTEGER,
    
    -- Metric metadata
    dataset_type VARCHAR(50), -- training, validation, test
    
    -- Timing
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT training_metrics_epoch_positive CHECK (epoch >= 0),
    CONSTRAINT training_metrics_batch_positive CHECK (batch >= 0),
    CONSTRAINT training_metrics_step_positive CHECK (step >= 0)
);

-- Convert training_metrics to hypertable
SELECT create_hypertable('training_metrics', 'recorded_at', if_not_exists => TRUE);

-- =============================================================================
-- ADAPTATIONS AND EVOLUTION
-- =============================================================================

-- Adaptations for continuous improvement
CREATE TABLE adaptations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    learning_model_id UUID NOT NULL REFERENCES learning_models(id) ON DELETE CASCADE,
    
    -- Adaptation identification
    adaptation_name VARCHAR(255) NOT NULL,
    adaptation_type adaptation_type NOT NULL,
    description TEXT,
    
    -- Adaptation trigger
    trigger_reason TEXT,
    trigger_data JSONB DEFAULT '{}',
    
    -- Adaptation details
    changes_made JSONB DEFAULT '{}',
    parameters_before JSONB DEFAULT '{}',
    parameters_after JSONB DEFAULT '{}',
    
    -- Performance impact
    performance_before JSONB DEFAULT '{}',
    performance_after JSONB DEFAULT '{}',
    improvement_score DECIMAL(5,4),
    
    -- Adaptation status
    status VARCHAR(50) DEFAULT 'pending', -- pending, applied, tested, reverted
    
    -- Timing
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    tested_at TIMESTAMP WITH TIME ZONE,
    
    -- Validation results
    validation_results JSONB DEFAULT '{}',
    is_successful BOOLEAN,
    
    -- Evolution context
    evolution_session_id UUID,
    generation_number INTEGER,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT adaptations_improvement_score_valid CHECK (improvement_score >= -1 AND improvement_score <= 1)
);

-- Evolution sessions for OpenEvolve integration
CREATE TABLE evolution_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Session identification
    session_name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Evolution configuration
    evolution_config JSONB DEFAULT '{}',
    population_size INTEGER DEFAULT 10,
    max_generations INTEGER DEFAULT 100,
    
    -- Evolution status
    current_stage evolution_stage DEFAULT 'initialization',
    current_generation INTEGER DEFAULT 0,
    
    -- Evolution metrics
    best_fitness DECIMAL(10,6),
    average_fitness DECIMAL(10,6),
    diversity_score DECIMAL(5,4),
    
    -- Timing
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_hours DECIMAL(8,2),
    
    -- Results
    best_individual_id UUID,
    convergence_generation INTEGER,
    
    -- Resource usage
    total_evaluations INTEGER DEFAULT 0,
    computational_cost DECIMAL(10,4),
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT evolution_sessions_population_positive CHECK (population_size > 0),
    CONSTRAINT evolution_sessions_generations_positive CHECK (max_generations > 0),
    CONSTRAINT evolution_sessions_current_generation_valid CHECK (current_generation >= 0)
);

-- =============================================================================
-- FEEDBACK AND LEARNING DATA
-- =============================================================================

-- User feedback for model improvement
CREATE TABLE user_feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    learning_model_id UUID REFERENCES learning_models(id),
    
    -- Feedback identification
    feedback_type feedback_type NOT NULL,
    
    -- Feedback content
    feedback_text TEXT,
    rating INTEGER, -- 1-5 scale
    
    -- Context information
    context_type VARCHAR(100), -- prediction, recommendation, analysis, etc.
    context_data JSONB DEFAULT '{}',
    
    -- Model prediction details
    predicted_value JSONB,
    actual_value JSONB,
    confidence_score DECIMAL(5,4),
    
    -- Feedback metadata
    is_processed BOOLEAN DEFAULT false,
    processing_notes TEXT,
    
    -- User information
    provided_by UUID REFERENCES users(id),
    user_session_id UUID,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT user_feedback_rating_valid CHECK (rating >= 1 AND rating <= 5),
    CONSTRAINT user_feedback_confidence_valid CHECK (confidence_score >= 0 AND confidence_score <= 1)
);

-- Pattern recognition results
CREATE TABLE pattern_recognition (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    learning_model_id UUID REFERENCES learning_models(id),
    
    -- Pattern identification
    pattern_name VARCHAR(255) NOT NULL,
    pattern_type VARCHAR(100),
    description TEXT,
    
    -- Pattern details
    pattern_data JSONB DEFAULT '{}',
    pattern_signature VARCHAR(64), -- Hash of pattern characteristics
    
    -- Pattern statistics
    occurrences_count INTEGER DEFAULT 1,
    confidence_score DECIMAL(5,4),
    significance_score DECIMAL(5,4),
    
    -- Pattern context
    context_type VARCHAR(100),
    context_data JSONB DEFAULT '{}',
    
    -- Discovery information
    discovered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    discovery_method VARCHAR(100),
    
    -- Pattern validation
    is_validated BOOLEAN DEFAULT false,
    validation_score DECIMAL(5,4),
    
    -- Pattern relationships
    related_patterns JSONB DEFAULT '[]',
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT pattern_recognition_occurrences_positive CHECK (occurrences_count > 0),
    CONSTRAINT pattern_recognition_scores_valid CHECK (
        confidence_score >= 0 AND confidence_score <= 1 AND
        significance_score >= 0 AND significance_score <= 1
    )
);

-- =============================================================================
-- INDEXES FOR OPTIMAL PERFORMANCE
-- =============================================================================

-- Learning models indexes
CREATE INDEX idx_learning_models_org_id ON learning_models(organization_id);
CREATE INDEX idx_learning_models_type ON learning_models(model_type);
CREATE INDEX idx_learning_models_algorithm ON learning_models(algorithm);
CREATE INDEX idx_learning_models_status ON learning_models(status);
CREATE INDEX idx_learning_models_active ON learning_models(is_active);
CREATE INDEX idx_learning_models_production ON learning_models(is_production);
CREATE INDEX idx_learning_models_parent_id ON learning_models(parent_model_id);
CREATE INDEX idx_learning_models_generation ON learning_models(evolution_generation);

-- Training sessions indexes
CREATE INDEX idx_training_sessions_model_id ON training_sessions(learning_model_id);
CREATE INDEX idx_training_sessions_status ON training_sessions(status);
CREATE INDEX idx_training_sessions_started_at ON training_sessions(started_at);
CREATE INDEX idx_training_sessions_triggered_by ON training_sessions(triggered_by);

-- Training metrics indexes (time-series optimized)
CREATE INDEX idx_training_metrics_session_id ON training_metrics(training_session_id, recorded_at DESC);
CREATE INDEX idx_training_metrics_name ON training_metrics(metric_name, recorded_at DESC);
CREATE INDEX idx_training_metrics_epoch ON training_metrics(epoch, recorded_at DESC);

-- Adaptations indexes
CREATE INDEX idx_adaptations_model_id ON adaptations(learning_model_id);
CREATE INDEX idx_adaptations_type ON adaptations(adaptation_type);
CREATE INDEX idx_adaptations_applied_at ON adaptations(applied_at);
CREATE INDEX idx_adaptations_evolution_session ON adaptations(evolution_session_id);

-- Evolution sessions indexes
CREATE INDEX idx_evolution_sessions_org_id ON evolution_sessions(organization_id);
CREATE INDEX idx_evolution_sessions_stage ON evolution_sessions(current_stage);
CREATE INDEX idx_evolution_sessions_started_at ON evolution_sessions(started_at);

-- Feedback indexes
CREATE INDEX idx_user_feedback_model_id ON user_feedback(learning_model_id);
CREATE INDEX idx_user_feedback_type ON user_feedback(feedback_type);
CREATE INDEX idx_user_feedback_provided_by ON user_feedback(provided_by);
CREATE INDEX idx_user_feedback_processed ON user_feedback(is_processed);

-- Pattern recognition indexes
CREATE INDEX idx_pattern_recognition_org_id ON pattern_recognition(organization_id);
CREATE INDEX idx_pattern_recognition_model_id ON pattern_recognition(learning_model_id);
CREATE INDEX idx_pattern_recognition_type ON pattern_recognition(pattern_type);
CREATE INDEX idx_pattern_recognition_signature ON pattern_recognition(pattern_signature);
CREATE INDEX idx_pattern_recognition_discovered_at ON pattern_recognition(discovered_at);

-- GIN indexes for JSONB fields
CREATE INDEX idx_learning_models_config_gin USING gin (architecture_config);
CREATE INDEX idx_learning_models_hyperparams_gin USING gin (hyperparameters);
CREATE INDEX idx_training_sessions_metrics_gin USING gin (training_metrics);
CREATE INDEX idx_adaptations_changes_gin USING gin (changes_made);
CREATE INDEX idx_pattern_recognition_data_gin USING gin (pattern_data);

-- =============================================================================
-- VIEWS FOR ANALYTICS AND MONITORING
-- =============================================================================

-- Model performance overview
CREATE VIEW model_performance_overview AS
SELECT 
    lm.*,
    o.name as organization_name,
    u.name as created_by_name,
    COUNT(ts.id) as training_sessions_count,
    COUNT(a.id) as adaptations_count,
    AVG(uf.rating) as average_user_rating,
    COUNT(uf.id) as feedback_count
FROM learning_models lm
JOIN organizations o ON lm.organization_id = o.id
LEFT JOIN users u ON lm.created_by = u.id
LEFT JOIN training_sessions ts ON lm.id = ts.learning_model_id
LEFT JOIN adaptations a ON lm.id = a.learning_model_id
LEFT JOIN user_feedback uf ON lm.id = uf.learning_model_id
WHERE lm.deleted_at IS NULL
GROUP BY lm.id, o.name, u.name;

-- Active training sessions
CREATE VIEW active_training_sessions AS
SELECT 
    ts.*,
    lm.name as model_name,
    lm.model_type,
    u.name as triggered_by_name
FROM training_sessions ts
JOIN learning_models lm ON ts.learning_model_id = lm.id
LEFT JOIN users u ON ts.triggered_by = u.id
WHERE ts.status IN ('pending', 'preparing_data', 'training', 'validating')
ORDER BY ts.started_at DESC;

-- Evolution progress view
CREATE VIEW evolution_progress AS
SELECT 
    es.*,
    COUNT(a.id) as adaptations_count,
    AVG(a.improvement_score) as avg_improvement_score,
    MAX(a.applied_at) as last_adaptation_at
FROM evolution_sessions es
LEFT JOIN adaptations a ON es.id = a.evolution_session_id
GROUP BY es.id
ORDER BY es.started_at DESC;

-- Grant permissions to learning_user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO learning_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO learning_user;
GRANT USAGE ON SCHEMA public TO learning_user;

-- Insert default organization
INSERT INTO organizations (name, slug, description) VALUES 
('Default Organization', 'default', 'Default organization for learning and evolution');

-- Insert default admin user
INSERT INTO users (organization_id, name, email, role) VALUES 
((SELECT id FROM organizations WHERE slug = 'default'), 'Learning Admin', 'admin@learning.local', 'admin');

-- Final status message
DO $$
BEGIN
    RAISE NOTICE '🧠 Learning Database initialized successfully!';
    RAISE NOTICE 'Features: Pattern recognition, Continuous learning, Evolution integration, Model management';
    RAISE NOTICE 'Capabilities: Training tracking, Adaptation management, User feedback, Performance optimization';
    RAISE NOTICE 'Time-series optimization: Enabled with TimescaleDB for training metrics';
    RAISE NOTICE 'Timestamp: %', NOW();
END $$;

