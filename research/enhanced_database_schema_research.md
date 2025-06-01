# Enhanced Database Schema Research for Continuous Learning and Analytics

## Executive Summary

This research document outlines the design of enhanced database schema extensions to support continuous learning, pattern analysis, and OpenEvolve integration for the graph-sitter system. The proposed schema maintains backward compatibility with the existing 7-module structure while adding sophisticated machine learning and analytics capabilities.

## Current System Analysis

### Existing Architecture Overview
Based on codebase analysis, the graph-sitter system currently includes:

1. **Git Operations Module**: Handles repository interactions, pull requests, and code changes
2. **Runner Module**: Manages code execution and transformation operations  
3. **CLI Module**: Command-line interface and API schemas
4. **Extensions Module**: Platform integrations (GitHub, Linear, Slack)
5. **Core Module**: Core functionality and utilities
6. **Python/TypeScript Modules**: Language-specific processing
7. **Shared Module**: Common utilities and types

### Current Data Models
The system uses Pydantic models for data validation and includes:
- Git context models (pull requests, commits, users)
- Runner models (codemods, APIs)
- Integration models (GitHub, Linear, Slack types)
- Configuration schemas

## Enhanced Schema Design

### 1. Learning Data Storage Requirements

#### 1.1 Machine Learning Models Table
```sql
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
    
    UNIQUE(name, version)
);

CREATE INDEX idx_ml_models_type_status ON ml_models(model_type, status);
CREATE INDEX idx_ml_models_created_at ON ml_models(created_at);
CREATE INDEX idx_ml_models_parent ON ml_models(parent_model_id);
```

#### 1.2 Training Datasets Table
```sql
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
    
    UNIQUE(name, version)
);

CREATE INDEX idx_training_datasets_type ON training_datasets(dataset_type);
CREATE INDEX idx_training_datasets_created_at ON training_datasets(created_at);
```

#### 1.3 Model Training Sessions Table
```sql
CREATE TABLE model_training_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID NOT NULL REFERENCES ml_models(id),
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
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_training_sessions_model ON model_training_sessions(model_id);
CREATE INDEX idx_training_sessions_status ON model_training_sessions(status);
CREATE INDEX idx_training_sessions_start ON model_training_sessions(training_start);
```

### 2. OpenEvolve Integration Schema

#### 2.1 Evolution Experiments Table
```sql
CREATE TABLE evolution_experiments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    problem_definition JSONB NOT NULL, -- Problem statement and constraints
    objective_function JSONB NOT NULL, -- Optimization objectives
    population_size INTEGER DEFAULT 50,
    max_generations INTEGER DEFAULT 100,
    current_generation INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'initialized', -- 'initialized', 'running', 'completed', 'failed'
    best_score DECIMAL(10,4),
    convergence_threshold DECIMAL(10,6),
    mutation_rate DECIMAL(3,2) DEFAULT 0.1,
    crossover_rate DECIMAL(3,2) DEFAULT 0.8,
    selection_strategy VARCHAR(100) DEFAULT 'tournament',
    llm_config JSONB, -- LLM settings for code generation
    evaluation_config JSONB, -- How to evaluate generated code
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(255)
);

CREATE INDEX idx_evolution_experiments_status ON evolution_experiments(status);
CREATE INDEX idx_evolution_experiments_created_at ON evolution_experiments(created_at);
```

#### 2.2 Evolution Generations Table
```sql
CREATE TABLE evolution_generations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id UUID NOT NULL REFERENCES evolution_experiments(id),
    generation_number INTEGER NOT NULL,
    population_data JSONB NOT NULL, -- Array of individuals in this generation
    generation_stats JSONB, -- Min, max, avg, std dev of scores
    best_individual_id UUID,
    diversity_metrics JSONB, -- Genetic diversity measurements
    selection_pressure DECIMAL(3,2),
    convergence_metrics JSONB,
    generation_start TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    generation_end TIMESTAMP WITH TIME ZONE,
    
    UNIQUE(experiment_id, generation_number)
);

CREATE INDEX idx_evolution_generations_experiment ON evolution_generations(experiment_id);
CREATE INDEX idx_evolution_generations_number ON evolution_generations(generation_number);
```

#### 2.3 Evolution Individuals Table
```sql
CREATE TABLE evolution_individuals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    generation_id UUID NOT NULL REFERENCES evolution_generations(id),
    experiment_id UUID NOT NULL REFERENCES evolution_experiments(id),
    individual_index INTEGER NOT NULL, -- Position in generation
    genotype JSONB NOT NULL, -- Code representation
    phenotype TEXT, -- Actual executable code
    fitness_score DECIMAL(10,4),
    evaluation_metrics JSONB, -- Detailed performance metrics
    parent_ids UUID[], -- Array of parent individual IDs
    mutation_applied JSONB, -- What mutations were applied
    crossover_applied JSONB, -- Crossover operations applied
    evaluation_time_ms INTEGER,
    evaluation_status VARCHAR(50), -- 'pending', 'evaluating', 'completed', 'failed'
    error_log TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(generation_id, individual_index)
);

CREATE INDEX idx_evolution_individuals_generation ON evolution_individuals(generation_id);
CREATE INDEX idx_evolution_individuals_fitness ON evolution_individuals(fitness_score DESC);
CREATE INDEX idx_evolution_individuals_status ON evolution_individuals(evaluation_status);
```

### 3. Pattern Recognition Data Structures

#### 3.1 Identified Patterns Table
```sql
CREATE TABLE identified_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_type VARCHAR(100) NOT NULL, -- 'code_smell', 'performance_bottleneck', 'usage_pattern'
    pattern_name VARCHAR(255) NOT NULL,
    pattern_description TEXT,
    detection_algorithm VARCHAR(100), -- Algorithm used to detect this pattern
    confidence_score DECIMAL(3,2), -- 0.00 to 1.00
    pattern_signature JSONB, -- Unique characteristics of the pattern
    occurrence_frequency INTEGER DEFAULT 1,
    first_detected TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_detected TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    severity_level VARCHAR(50), -- 'low', 'medium', 'high', 'critical'
    impact_metrics JSONB, -- Performance impact, maintainability impact, etc.
    remediation_suggestions JSONB, -- Suggested fixes or improvements
    status VARCHAR(50) DEFAULT 'active', -- 'active', 'resolved', 'ignored', 'false_positive'
    
    UNIQUE(pattern_type, pattern_name, pattern_signature)
);

CREATE INDEX idx_patterns_type_status ON identified_patterns(pattern_type, status);
CREATE INDEX idx_patterns_confidence ON identified_patterns(confidence_score DESC);
CREATE INDEX idx_patterns_severity ON identified_patterns(severity_level);
CREATE INDEX idx_patterns_last_detected ON identified_patterns(last_detected);
```

#### 3.2 Pattern Occurrences Table
```sql
CREATE TABLE pattern_occurrences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_id UUID NOT NULL REFERENCES identified_patterns(id),
    source_type VARCHAR(100) NOT NULL, -- 'git_commit', 'code_file', 'user_session'
    source_id VARCHAR(255) NOT NULL, -- ID of the source entity
    location_data JSONB, -- File path, line numbers, function names, etc.
    context_data JSONB, -- Surrounding code or environmental context
    detection_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    detection_model_id UUID REFERENCES ml_models(id),
    confidence_score DECIMAL(3,2),
    metadata JSONB -- Additional context-specific data
);

CREATE INDEX idx_pattern_occurrences_pattern ON pattern_occurrences(pattern_id);
CREATE INDEX idx_pattern_occurrences_source ON pattern_occurrences(source_type, source_id);
CREATE INDEX idx_pattern_occurrences_timestamp ON pattern_occurrences(detection_timestamp);
```

#### 3.3 Predictions Table
```sql
CREATE TABLE predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID NOT NULL REFERENCES ml_models(id),
    prediction_type VARCHAR(100) NOT NULL, -- 'performance_degradation', 'bug_likelihood', 'optimization_opportunity'
    target_entity_type VARCHAR(100), -- 'code_file', 'function', 'repository', 'user'
    target_entity_id VARCHAR(255),
    predicted_value JSONB, -- The actual prediction (could be numeric, categorical, or complex)
    confidence_interval JSONB, -- Statistical confidence bounds
    prediction_horizon INTEGER, -- How far into the future (in days/hours)
    input_features JSONB, -- Features used to make the prediction
    prediction_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    actual_outcome JSONB, -- Filled in later when outcome is known
    accuracy_score DECIMAL(3,2), -- Calculated when actual outcome is available
    feedback_received JSONB, -- User feedback on prediction quality
    status VARCHAR(50) DEFAULT 'active' -- 'active', 'validated', 'invalidated', 'expired'
);

CREATE INDEX idx_predictions_model ON predictions(model_id);
CREATE INDEX idx_predictions_type ON predictions(prediction_type);
CREATE INDEX idx_predictions_target ON predictions(target_entity_type, target_entity_id);
CREATE INDEX idx_predictions_timestamp ON predictions(prediction_timestamp);
CREATE INDEX idx_predictions_status ON predictions(status);
```

### 4. Analytics and Performance Optimization

#### 4.1 Learning Events Table (Time-Series Optimized)
```sql
CREATE TABLE learning_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(100) NOT NULL, -- 'model_prediction', 'pattern_detection', 'user_feedback', 'system_optimization'
    event_subtype VARCHAR(100), -- More specific categorization
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    source_system VARCHAR(100), -- 'openevolve', 'pattern_analyzer', 'user_interface'
    entity_type VARCHAR(100), -- What type of entity this event relates to
    entity_id VARCHAR(255), -- ID of the related entity
    event_data JSONB NOT NULL, -- The actual event payload
    user_id VARCHAR(255), -- User associated with the event (if applicable)
    session_id VARCHAR(255), -- Session ID for grouping related events
    processing_time_ms INTEGER, -- How long it took to process this event
    metadata JSONB -- Additional context
) PARTITION BY RANGE (timestamp);

-- Create monthly partitions for better performance
CREATE TABLE learning_events_y2025m01 PARTITION OF learning_events
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');
CREATE TABLE learning_events_y2025m02 PARTITION OF learning_events
    FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');
-- Continue creating partitions as needed...

CREATE INDEX idx_learning_events_type_timestamp ON learning_events(event_type, timestamp);
CREATE INDEX idx_learning_events_entity ON learning_events(entity_type, entity_id);
CREATE INDEX idx_learning_events_user ON learning_events(user_id, timestamp);
CREATE INDEX idx_learning_events_session ON learning_events(session_id);
```

#### 4.2 System Performance Metrics Table
```sql
CREATE TABLE system_performance_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_name VARCHAR(100) NOT NULL,
    metric_category VARCHAR(100), -- 'database', 'api', 'ml_model', 'user_experience'
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    value DECIMAL(15,6) NOT NULL,
    unit VARCHAR(50), -- 'ms', 'mb', 'percentage', 'count'
    tags JSONB, -- Key-value pairs for filtering and grouping
    source_component VARCHAR(100), -- Which system component generated this metric
    aggregation_level VARCHAR(50) DEFAULT 'raw', -- 'raw', 'minute', 'hour', 'day'
    metadata JSONB
) PARTITION BY RANGE (timestamp);

-- Create daily partitions for high-frequency metrics
CREATE TABLE system_performance_metrics_y2025m01d01 PARTITION OF system_performance_metrics
    FOR VALUES FROM ('2025-01-01') TO ('2025-01-02');
-- Continue creating partitions...

CREATE INDEX idx_performance_metrics_name_timestamp ON system_performance_metrics(metric_name, timestamp);
CREATE INDEX idx_performance_metrics_category ON system_performance_metrics(metric_category, timestamp);
CREATE INDEX idx_performance_metrics_tags ON system_performance_metrics USING GIN(tags);
```

#### 4.3 A/B Testing Experiments Table
```sql
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
    status VARCHAR(50) DEFAULT 'draft', -- 'draft', 'running', 'completed', 'cancelled'
    statistical_power DECIMAL(3,2) DEFAULT 0.80,
    significance_level DECIMAL(3,2) DEFAULT 0.05,
    minimum_sample_size INTEGER,
    current_sample_size INTEGER DEFAULT 0,
    results JSONB, -- Statistical results when experiment completes
    winner_variant VARCHAR(100), -- Which variant won (if any)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(255)
);

CREATE INDEX idx_ab_experiments_status ON ab_testing_experiments(status);
CREATE INDEX idx_ab_experiments_dates ON ab_testing_experiments(start_date, end_date);
```

#### 4.4 A/B Testing Assignments Table
```sql
CREATE TABLE ab_testing_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id UUID NOT NULL REFERENCES ab_testing_experiments(id),
    user_id VARCHAR(255) NOT NULL,
    variant VARCHAR(100) NOT NULL,
    assignment_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    session_id VARCHAR(255),
    user_agent TEXT,
    metadata JSONB,
    
    UNIQUE(experiment_id, user_id)
);

CREATE INDEX idx_ab_assignments_experiment ON ab_testing_assignments(experiment_id);
CREATE INDEX idx_ab_assignments_user ON ab_testing_assignments(user_id);
CREATE INDEX idx_ab_assignments_variant ON ab_testing_assignments(experiment_id, variant);
```

## Integration with Existing Schema

### Foreign Key Relationships

The enhanced schema integrates with the existing 7-module structure through these key relationships:

1. **User Integration**: All tables reference users through `user_id` fields that connect to the existing user management system
2. **Repository Integration**: Git-related events and patterns link to existing repository and commit tracking
3. **Session Integration**: User sessions and interactions connect to existing session management
4. **Configuration Integration**: Model and experiment configurations extend existing configuration schemas

### Data Flow Integration Points

```sql
-- Example integration table linking to existing git operations
CREATE TABLE git_operation_learning_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    git_operation_id VARCHAR(255) NOT NULL, -- Links to existing git operation tracking
    learning_event_id UUID NOT NULL REFERENCES learning_events(id),
    operation_type VARCHAR(100), -- 'commit', 'merge', 'rebase', 'pull_request'
    repository_id VARCHAR(255),
    branch_name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_git_learning_events_operation ON git_operation_learning_events(git_operation_id);
CREATE INDEX idx_git_learning_events_repo ON git_operation_learning_events(repository_id);
```

## Performance Optimization Strategies

### 1. Indexing Strategy

#### Time-Series Optimized Indexes
```sql
-- Composite indexes for common query patterns
CREATE INDEX idx_learning_events_type_time_entity ON learning_events(event_type, timestamp, entity_type);
CREATE INDEX idx_performance_metrics_component_time ON system_performance_metrics(source_component, timestamp);

-- Partial indexes for active records
CREATE INDEX idx_active_experiments ON evolution_experiments(id) WHERE status = 'running';
CREATE INDEX idx_active_predictions ON predictions(id) WHERE status = 'active';

-- GIN indexes for JSONB queries
CREATE INDEX idx_ml_models_hyperparameters ON ml_models USING GIN(hyperparameters);
CREATE INDEX idx_pattern_signatures ON identified_patterns USING GIN(pattern_signature);
CREATE INDEX idx_event_data ON learning_events USING GIN(event_data);
```

#### Partitioning Strategy
```sql
-- Time-based partitioning for high-volume tables
-- learning_events: Monthly partitions
-- system_performance_metrics: Daily partitions
-- pattern_occurrences: Weekly partitions

-- Example partition maintenance function
CREATE OR REPLACE FUNCTION create_monthly_partition(table_name TEXT, start_date DATE)
RETURNS VOID AS $$
DECLARE
    partition_name TEXT;
    end_date DATE;
BEGIN
    partition_name := table_name || '_y' || EXTRACT(YEAR FROM start_date) || 'm' || LPAD(EXTRACT(MONTH FROM start_date)::TEXT, 2, '0');
    end_date := start_date + INTERVAL '1 month';
    
    EXECUTE format('CREATE TABLE %I PARTITION OF %I FOR VALUES FROM (%L) TO (%L)',
                   partition_name, table_name, start_date, end_date);
    
    EXECUTE format('CREATE INDEX idx_%s_timestamp ON %I(timestamp)', partition_name, partition_name);
END;
$$ LANGUAGE plpgsql;
```

### 2. Query Optimization

#### Materialized Views for Common Analytics
```sql
-- Daily aggregated metrics
CREATE MATERIALIZED VIEW daily_learning_metrics AS
SELECT 
    DATE(timestamp) as date,
    event_type,
    source_system,
    COUNT(*) as event_count,
    AVG(processing_time_ms) as avg_processing_time,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY processing_time_ms) as p95_processing_time
FROM learning_events
WHERE timestamp >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY DATE(timestamp), event_type, source_system;

CREATE UNIQUE INDEX idx_daily_learning_metrics ON daily_learning_metrics(date, event_type, source_system);

-- Model performance summary
CREATE MATERIALIZED VIEW model_performance_summary AS
SELECT 
    m.id,
    m.name,
    m.version,
    m.model_type,
    COUNT(p.id) as prediction_count,
    AVG(p.accuracy_score) as avg_accuracy,
    COUNT(CASE WHEN p.status = 'validated' THEN 1 END) as validated_predictions,
    MAX(p.prediction_timestamp) as last_prediction
FROM ml_models m
LEFT JOIN predictions p ON m.id = p.model_id
WHERE m.status = 'active'
GROUP BY m.id, m.name, m.version, m.model_type;

CREATE UNIQUE INDEX idx_model_performance_summary ON model_performance_summary(id);
```

### 3. Data Retention and Archival

```sql
-- Data retention policies
CREATE TABLE data_retention_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_name VARCHAR(255) NOT NULL,
    retention_period INTERVAL NOT NULL,
    archive_strategy VARCHAR(100), -- 'delete', 'archive_to_s3', 'compress'
    last_cleanup TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Example retention policy function
CREATE OR REPLACE FUNCTION cleanup_old_learning_events()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Archive events older than 2 years to cold storage
    WITH archived_events AS (
        DELETE FROM learning_events 
        WHERE timestamp < NOW() - INTERVAL '2 years'
        RETURNING *
    )
    SELECT COUNT(*) INTO deleted_count FROM archived_events;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Schedule cleanup job
SELECT cron.schedule('cleanup-learning-events', '0 2 * * 0', 'SELECT cleanup_old_learning_events();');
```

## Migration Strategy

### Phase 1: Core Infrastructure (Weeks 1-2)
1. Create base tables for ML models and training data
2. Implement basic learning events tracking
3. Set up partitioning for time-series tables
4. Create initial indexes and constraints

### Phase 2: OpenEvolve Integration (Weeks 3-4)
1. Implement evolution experiment tracking
2. Create generation and individual management
3. Add evaluation and scoring systems
4. Integrate with existing git operations

### Phase 3: Pattern Recognition (Weeks 5-6)
1. Deploy pattern detection tables
2. Implement prediction tracking
3. Create recommendation systems
4. Add A/B testing infrastructure

### Phase 4: Analytics and Optimization (Weeks 7-8)
1. Create materialized views for analytics
2. Implement data retention policies
3. Optimize query performance
4. Add monitoring and alerting

### Migration Scripts

```sql
-- Migration script template
BEGIN;

-- Create new schema version tracking
CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(50) PRIMARY KEY,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    description TEXT
);

-- Check if migration already applied
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM schema_migrations WHERE version = '2025.01.001') THEN
        -- Apply migration changes here
        
        -- Record migration
        INSERT INTO schema_migrations (version, description) 
        VALUES ('2025.01.001', 'Enhanced database schema for continuous learning');
    END IF;
END $$;

COMMIT;
```

## Scalability Analysis

### Storage Requirements Projection

| Component | Daily Volume | Monthly Growth | Annual Storage |
|-----------|--------------|----------------|----------------|
| Learning Events | 1M events | 30M events | 12GB |
| Performance Metrics | 10M metrics | 300M metrics | 120GB |
| Pattern Occurrences | 100K patterns | 3M patterns | 1.2GB |
| Evolution Data | 1K experiments | 30K experiments | 500MB |
| **Total** | | | **~134GB/year** |

### Query Performance Benchmarks

Target performance metrics:
- Learning event insertion: <10ms p95
- Pattern detection queries: <100ms p95
- Analytics aggregations: <5s p95
- Model training data retrieval: <1s p95

### Horizontal Scaling Strategy

1. **Read Replicas**: Deploy read replicas for analytics workloads
2. **Sharding**: Partition learning events by user_id or timestamp
3. **Caching**: Implement Redis caching for frequently accessed patterns
4. **Archive Storage**: Move old data to S3/cold storage after 1 year

## Security and Compliance

### Data Privacy
- Implement field-level encryption for sensitive model data
- Add audit logging for all data access
- Support GDPR right-to-be-forgotten through cascading deletes

### Access Control
```sql
-- Row-level security for multi-tenant access
ALTER TABLE ml_models ENABLE ROW LEVEL SECURITY;

CREATE POLICY ml_models_tenant_isolation ON ml_models
    FOR ALL TO application_role
    USING (created_by = current_setting('app.current_user_id'));
```

## Monitoring and Observability

### Key Metrics to Track
1. **Data Quality**: Completeness, accuracy, consistency of learning data
2. **Performance**: Query response times, throughput, resource utilization
3. **Model Health**: Prediction accuracy, drift detection, training success rates
4. **System Health**: Partition sizes, index usage, replication lag

### Alerting Thresholds
- Learning event processing lag > 5 minutes
- Model accuracy drops below 80% of baseline
- Partition size exceeds 10GB
- Query response time p95 > 2x baseline

## Conclusion

This enhanced database schema provides a robust foundation for continuous learning and analytics while maintaining compatibility with the existing 7-module structure. The design emphasizes:

1. **Scalability**: Partitioned tables and optimized indexes support millions of events
2. **Flexibility**: JSONB fields allow schema evolution without migrations
3. **Performance**: Time-series optimizations and materialized views ensure fast queries
4. **Integration**: Clear foreign key relationships with existing systems
5. **Maintainability**: Automated retention policies and monitoring

The phased migration approach minimizes risk while delivering value incrementally. The schema is designed to grow with the system's needs while providing immediate benefits for pattern recognition, model management, and analytics.

## Next Steps

1. **Validation**: Review schema with stakeholders and validate against use cases
2. **Prototyping**: Implement core tables in development environment
3. **Performance Testing**: Validate query performance with realistic data volumes
4. **Integration Testing**: Ensure compatibility with existing 7-module schema
5. **Documentation**: Create detailed API documentation and usage examples

