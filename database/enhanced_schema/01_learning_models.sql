-- Enhanced Database Schema: Learning Models and Training Data
-- Part 1: Machine Learning Infrastructure

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_cron";

-- Machine Learning Models Table
CREATE TABLE ml_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    model_type VARCHAR(100) NOT NULL, -- 'pattern_recognition', 'optimization', 'prediction'
    framework VARCHAR(50), -- 'tensorflow', 'pytorch', 'scikit-learn'
    model_data JSONB, -- Serialized model or reference to storage
    hyperparameters JSONB,
    training_config JSONB,
    performance_metrics JSONB,
    status VARCHAR(50) DEFAULT 'training', -- 'training', 'active', 'deprecated', 'archived'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(255),
    parent_model_id UUID REFERENCES ml_models(id),
    
    UNIQUE(name, version),
    CHECK (status IN ('training', 'active', 'deprecated', 'archived')),
    CHECK (model_type IN ('pattern_recognition', 'optimization', 'prediction', 'classification', 'regression'))
);

-- Indexes for ml_models
CREATE INDEX idx_ml_models_type_status ON ml_models(model_type, status);
CREATE INDEX idx_ml_models_created_at ON ml_models(created_at);
CREATE INDEX idx_ml_models_parent ON ml_models(parent_model_id);
CREATE INDEX idx_ml_models_name_version ON ml_models(name, version);
CREATE INDEX idx_ml_models_hyperparameters ON ml_models USING GIN(hyperparameters);

-- Training Datasets Table
CREATE TABLE training_datasets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    dataset_type VARCHAR(100) NOT NULL, -- 'code_patterns', 'performance_metrics', 'user_behavior'
    source_type VARCHAR(100), -- 'git_history', 'user_interactions', 'system_metrics'
    data_schema JSONB, -- Schema definition for the dataset
    storage_location TEXT, -- Path or URL to actual data
    size_bytes BIGINT,
    record_count BIGINT,
    quality_score DECIMAL(3,2), -- 0.00 to 1.00
    preprocessing_config JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(name, version),
    CHECK (quality_score >= 0.00 AND quality_score <= 1.00),
    CHECK (size_bytes >= 0),
    CHECK (record_count >= 0)
);

-- Indexes for training_datasets
CREATE INDEX idx_training_datasets_type ON training_datasets(dataset_type);
CREATE INDEX idx_training_datasets_created_at ON training_datasets(created_at);
CREATE INDEX idx_training_datasets_source_type ON training_datasets(source_type);
CREATE INDEX idx_training_datasets_quality ON training_datasets(quality_score DESC);

-- Model Training Sessions Table
CREATE TABLE model_training_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID NOT NULL REFERENCES ml_models(id) ON DELETE CASCADE,
    dataset_id UUID NOT NULL REFERENCES training_datasets(id),
    training_start TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    training_end TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'running', -- 'running', 'completed', 'failed', 'cancelled'
    progress_percentage DECIMAL(5,2) DEFAULT 0.00,
    current_epoch INTEGER DEFAULT 0,
    total_epochs INTEGER,
    loss_history JSONB, -- Array of loss values per epoch
    validation_metrics JSONB,
    resource_usage JSONB, -- CPU, memory, GPU usage stats
    error_log TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CHECK (status IN ('running', 'completed', 'failed', 'cancelled')),
    CHECK (progress_percentage >= 0.00 AND progress_percentage <= 100.00),
    CHECK (current_epoch >= 0),
    CHECK (total_epochs > 0),
    CHECK (training_end IS NULL OR training_end >= training_start)
);

-- Indexes for model_training_sessions
CREATE INDEX idx_training_sessions_model ON model_training_sessions(model_id);
CREATE INDEX idx_training_sessions_status ON model_training_sessions(status);
CREATE INDEX idx_training_sessions_start ON model_training_sessions(training_start);
CREATE INDEX idx_training_sessions_dataset ON model_training_sessions(dataset_id);

-- Model Evaluation Results Table
CREATE TABLE model_evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID NOT NULL REFERENCES ml_models(id) ON DELETE CASCADE,
    evaluation_dataset_id UUID REFERENCES training_datasets(id),
    evaluation_type VARCHAR(100) NOT NULL, -- 'validation', 'test', 'production'
    metrics JSONB NOT NULL, -- Accuracy, precision, recall, F1, etc.
    confusion_matrix JSONB,
    feature_importance JSONB,
    evaluation_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    evaluation_duration_ms INTEGER,
    evaluator_version VARCHAR(50),
    notes TEXT,
    
    CHECK (evaluation_type IN ('validation', 'test', 'production', 'cross_validation')),
    CHECK (evaluation_duration_ms >= 0)
);

-- Indexes for model_evaluations
CREATE INDEX idx_model_evaluations_model ON model_evaluations(model_id);
CREATE INDEX idx_model_evaluations_type ON model_evaluations(evaluation_type);
CREATE INDEX idx_model_evaluations_timestamp ON model_evaluations(evaluation_timestamp);

-- Model Deployment History Table
CREATE TABLE model_deployments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID NOT NULL REFERENCES ml_models(id),
    deployment_environment VARCHAR(100) NOT NULL, -- 'development', 'staging', 'production'
    deployment_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deployment_status VARCHAR(50) DEFAULT 'deploying', -- 'deploying', 'active', 'inactive', 'failed'
    deployment_config JSONB,
    health_check_url TEXT,
    performance_baseline JSONB,
    rollback_model_id UUID REFERENCES ml_models(id),
    deployed_by VARCHAR(255),
    notes TEXT,
    
    CHECK (deployment_status IN ('deploying', 'active', 'inactive', 'failed')),
    CHECK (deployment_environment IN ('development', 'staging', 'production'))
);

-- Indexes for model_deployments
CREATE INDEX idx_model_deployments_model ON model_deployments(model_id);
CREATE INDEX idx_model_deployments_environment ON model_deployments(deployment_environment);
CREATE INDEX idx_model_deployments_status ON model_deployments(deployment_status);
CREATE INDEX idx_model_deployments_timestamp ON model_deployments(deployment_timestamp);

-- Feature Store Table
CREATE TABLE feature_store (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    feature_name VARCHAR(255) NOT NULL,
    feature_version VARCHAR(50) NOT NULL,
    feature_type VARCHAR(100) NOT NULL, -- 'numerical', 'categorical', 'text', 'embedding'
    description TEXT,
    computation_logic TEXT, -- SQL or code to compute the feature
    data_source VARCHAR(255), -- Source table or system
    update_frequency VARCHAR(100), -- 'real_time', 'hourly', 'daily', 'weekly'
    last_updated TIMESTAMP WITH TIME ZONE,
    feature_statistics JSONB, -- Min, max, mean, std, etc.
    quality_metrics JSONB, -- Completeness, uniqueness, etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(255),
    
    UNIQUE(feature_name, feature_version),
    CHECK (feature_type IN ('numerical', 'categorical', 'text', 'embedding', 'boolean')),
    CHECK (update_frequency IN ('real_time', 'hourly', 'daily', 'weekly', 'monthly'))
);

-- Indexes for feature_store
CREATE INDEX idx_feature_store_name_version ON feature_store(feature_name, feature_version);
CREATE INDEX idx_feature_store_type ON feature_store(feature_type);
CREATE INDEX idx_feature_store_update_frequency ON feature_store(update_frequency);
CREATE INDEX idx_feature_store_last_updated ON feature_store(last_updated);

-- Model Feature Dependencies Table
CREATE TABLE model_feature_dependencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID NOT NULL REFERENCES ml_models(id) ON DELETE CASCADE,
    feature_id UUID NOT NULL REFERENCES feature_store(id),
    importance_score DECIMAL(5,4), -- 0.0000 to 1.0000
    is_required BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(model_id, feature_id),
    CHECK (importance_score >= 0.0000 AND importance_score <= 1.0000)
);

-- Indexes for model_feature_dependencies
CREATE INDEX idx_model_features_model ON model_feature_dependencies(model_id);
CREATE INDEX idx_model_features_feature ON model_feature_dependencies(feature_id);
CREATE INDEX idx_model_features_importance ON model_feature_dependencies(importance_score DESC);

-- Trigger to update updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_ml_models_updated_at BEFORE UPDATE ON ml_models
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_training_datasets_updated_at BEFORE UPDATE ON training_datasets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_training_sessions_updated_at BEFORE UPDATE ON model_training_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Comments for documentation
COMMENT ON TABLE ml_models IS 'Storage for machine learning models with versioning and metadata';
COMMENT ON TABLE training_datasets IS 'Catalog of training datasets with quality metrics';
COMMENT ON TABLE model_training_sessions IS 'Tracking of model training processes and progress';
COMMENT ON TABLE model_evaluations IS 'Results of model evaluations across different datasets';
COMMENT ON TABLE model_deployments IS 'History of model deployments across environments';
COMMENT ON TABLE feature_store IS 'Central repository for feature definitions and metadata';
COMMENT ON TABLE model_feature_dependencies IS 'Mapping between models and their required features';

