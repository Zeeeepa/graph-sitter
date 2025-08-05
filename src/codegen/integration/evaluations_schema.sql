-- OpenEvolve Integration & Evaluation System Database Schema
-- Research-3: evaluations_schema.sql

-- Core evaluation tracking tables
CREATE TABLE IF NOT EXISTS evaluation_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'active',
    metadata JSONB DEFAULT '{}'
);

-- Component effectiveness tracking
CREATE TABLE IF NOT EXISTS component_evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES evaluation_sessions(id) ON DELETE CASCADE,
    component_type VARCHAR(100) NOT NULL, -- 'evaluator', 'database', 'controller'
    component_name VARCHAR(255) NOT NULL,
    evaluation_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    effectiveness_score DECIMAL(5,4), -- 0.0000 to 1.0000
    performance_metrics JSONB DEFAULT '{}',
    execution_time_ms INTEGER,
    memory_usage_mb DECIMAL(10,2),
    success_rate DECIMAL(5,4),
    error_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}'
);

-- Step-by-step evaluation tracking
CREATE TABLE IF NOT EXISTS evaluation_steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    component_evaluation_id UUID REFERENCES component_evaluations(id) ON DELETE CASCADE,
    step_number INTEGER NOT NULL,
    step_name VARCHAR(255) NOT NULL,
    step_description TEXT,
    start_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    end_time TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER,
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed'
    input_data JSONB DEFAULT '{}',
    output_data JSONB DEFAULT '{}',
    error_message TEXT,
    effectiveness_contribution DECIMAL(5,4)
);

-- Outcome vs effectiveness correlation tracking
CREATE TABLE IF NOT EXISTS outcome_correlations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES evaluation_sessions(id) ON DELETE CASCADE,
    component_type VARCHAR(100) NOT NULL,
    expected_outcome JSONB NOT NULL,
    actual_outcome JSONB NOT NULL,
    correlation_score DECIMAL(5,4), -- -1.0000 to 1.0000
    effectiveness_impact DECIMAL(5,4),
    analysis_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    analysis_method VARCHAR(100),
    confidence_level DECIMAL(5,4),
    metadata JSONB DEFAULT '{}'
);

-- Performance optimization analysis
CREATE TABLE IF NOT EXISTS performance_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES evaluation_sessions(id) ON DELETE CASCADE,
    component_type VARCHAR(100) NOT NULL,
    analysis_type VARCHAR(100) NOT NULL, -- 'bottleneck', 'optimization', 'regression'
    baseline_metrics JSONB NOT NULL,
    current_metrics JSONB NOT NULL,
    improvement_percentage DECIMAL(7,4),
    optimization_suggestions JSONB DEFAULT '[]',
    priority_level INTEGER DEFAULT 3, -- 1=high, 2=medium, 3=low
    analysis_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    analyst_agent VARCHAR(255),
    metadata JSONB DEFAULT '{}'
);

-- OpenEvolve agent execution tracking
CREATE TABLE IF NOT EXISTS agent_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES evaluation_sessions(id) ON DELETE CASCADE,
    agent_type VARCHAR(100) NOT NULL, -- 'evaluator_agent', 'database_agent', 'selection_controller'
    agent_instance_id VARCHAR(255),
    execution_start TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    execution_end TIMESTAMP WITH TIME ZONE,
    execution_status VARCHAR(50) DEFAULT 'running',
    input_parameters JSONB DEFAULT '{}',
    output_results JSONB DEFAULT '{}',
    resource_usage JSONB DEFAULT '{}',
    error_details TEXT,
    parent_execution_id UUID REFERENCES agent_executions(id)
);

-- Evaluation metrics aggregation
CREATE TABLE IF NOT EXISTS evaluation_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES evaluation_sessions(id) ON DELETE CASCADE,
    metric_name VARCHAR(255) NOT NULL,
    metric_category VARCHAR(100) NOT NULL, -- 'effectiveness', 'performance', 'reliability'
    metric_value DECIMAL(15,6),
    metric_unit VARCHAR(50),
    aggregation_period VARCHAR(50), -- 'real-time', 'hourly', 'daily', 'session'
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    component_filter VARCHAR(100),
    metadata JSONB DEFAULT '{}'
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_component_evaluations_session_id ON component_evaluations(session_id);
CREATE INDEX IF NOT EXISTS idx_component_evaluations_component_type ON component_evaluations(component_type);
CREATE INDEX IF NOT EXISTS idx_component_evaluations_timestamp ON component_evaluations(evaluation_timestamp);
CREATE INDEX IF NOT EXISTS idx_evaluation_steps_component_evaluation_id ON evaluation_steps(component_evaluation_id);
CREATE INDEX IF NOT EXISTS idx_outcome_correlations_session_id ON outcome_correlations(session_id);
CREATE INDEX IF NOT EXISTS idx_performance_analyses_session_id ON performance_analyses(session_id);
CREATE INDEX IF NOT EXISTS idx_agent_executions_session_id ON agent_executions(session_id);
CREATE INDEX IF NOT EXISTS idx_evaluation_metrics_session_id ON evaluation_metrics(session_id);
CREATE INDEX IF NOT EXISTS idx_evaluation_metrics_category ON evaluation_metrics(metric_category);

-- Views for common queries
CREATE OR REPLACE VIEW component_effectiveness_summary AS
SELECT 
    ce.session_id,
    ce.component_type,
    ce.component_name,
    AVG(ce.effectiveness_score) as avg_effectiveness,
    AVG(ce.execution_time_ms) as avg_execution_time,
    AVG(ce.memory_usage_mb) as avg_memory_usage,
    AVG(ce.success_rate) as avg_success_rate,
    COUNT(*) as evaluation_count,
    MAX(ce.evaluation_timestamp) as last_evaluation
FROM component_evaluations ce
GROUP BY ce.session_id, ce.component_type, ce.component_name;

CREATE OR REPLACE VIEW session_performance_overview AS
SELECT 
    es.id as session_id,
    es.session_name,
    es.status,
    COUNT(DISTINCT ce.id) as total_evaluations,
    AVG(ce.effectiveness_score) as overall_effectiveness,
    COUNT(DISTINCT pa.id) as performance_analyses_count,
    COUNT(DISTINCT oc.id) as outcome_correlations_count
FROM evaluation_sessions es
LEFT JOIN component_evaluations ce ON es.id = ce.session_id
LEFT JOIN performance_analyses pa ON es.id = pa.session_id
LEFT JOIN outcome_correlations oc ON es.id = oc.session_id
GROUP BY es.id, es.session_name, es.status;

