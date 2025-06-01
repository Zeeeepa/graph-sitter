-- OpenEvolve Integration Database Schema
-- Migration: 001_create_openevolve_tables.sql
-- Description: Create tables for OpenEvolve evaluation tracking and system improvements

-- Create extension for UUID generation if not exists
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create openevolve_evaluations table
CREATE TABLE IF NOT EXISTS openevolve_evaluations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    evaluation_id VARCHAR(255) UNIQUE NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    trigger_event VARCHAR(100) NOT NULL,
    priority INTEGER NOT NULL DEFAULT 5,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    submitted_at TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Data columns
    context JSONB NOT NULL DEFAULT '{}',
    metadata JSONB NOT NULL DEFAULT '{}',
    results JSONB,
    metrics JSONB,
    error_message TEXT,
    
    -- Configuration
    timeout INTEGER,
    retry_count INTEGER NOT NULL DEFAULT 0,
    max_retries INTEGER NOT NULL DEFAULT 3
);

-- Create system_improvements table
CREATE TABLE IF NOT EXISTS system_improvements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    evaluation_id UUID NOT NULL REFERENCES openevolve_evaluations(id) ON DELETE CASCADE,
    
    -- Improvement details
    improvement_type VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    priority INTEGER NOT NULL DEFAULT 5,
    estimated_impact FLOAT,
    implementation_complexity VARCHAR(50),
    
    -- Application status
    applied BOOLEAN NOT NULL DEFAULT FALSE,
    applied_at TIMESTAMP WITH TIME ZONE,
    results JSONB,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create evaluation_metrics table for detailed metrics
CREATE TABLE IF NOT EXISTS evaluation_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    evaluation_id UUID NOT NULL REFERENCES openevolve_evaluations(id) ON DELETE CASCADE,
    
    -- Metrics
    accuracy FLOAT,
    performance_score FLOAT,
    improvement_score FLOAT,
    execution_time FLOAT,
    resource_usage JSONB,
    custom_metrics JSONB,
    
    -- Timestamp
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Ensure one metrics record per evaluation
    CONSTRAINT uq_evaluation_metrics_evaluation_id UNIQUE (evaluation_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_openevolve_evaluations_evaluation_id ON openevolve_evaluations(evaluation_id);
CREATE INDEX IF NOT EXISTS idx_openevolve_evaluations_status ON openevolve_evaluations(status);
CREATE INDEX IF NOT EXISTS idx_openevolve_evaluations_trigger_event ON openevolve_evaluations(trigger_event);
CREATE INDEX IF NOT EXISTS idx_openevolve_evaluations_status_created ON openevolve_evaluations(status, created_at);
CREATE INDEX IF NOT EXISTS idx_openevolve_evaluations_trigger_created ON openevolve_evaluations(trigger_event, created_at);
CREATE INDEX IF NOT EXISTS idx_openevolve_evaluations_completed_at ON openevolve_evaluations(completed_at);

CREATE INDEX IF NOT EXISTS idx_system_improvements_evaluation_id ON system_improvements(evaluation_id);
CREATE INDEX IF NOT EXISTS idx_system_improvements_improvement_type ON system_improvements(improvement_type);
CREATE INDEX IF NOT EXISTS idx_system_improvements_applied ON system_improvements(applied);
CREATE INDEX IF NOT EXISTS idx_system_improvements_type_priority ON system_improvements(improvement_type, priority);
CREATE INDEX IF NOT EXISTS idx_system_improvements_applied_created ON system_improvements(applied, created_at);

CREATE INDEX IF NOT EXISTS idx_evaluation_metrics_evaluation_id ON evaluation_metrics(evaluation_id);
CREATE INDEX IF NOT EXISTS idx_evaluation_metrics_recorded_at ON evaluation_metrics(recorded_at);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers to automatically update updated_at
CREATE TRIGGER update_openevolve_evaluations_updated_at 
    BEFORE UPDATE ON openevolve_evaluations 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_system_improvements_updated_at 
    BEFORE UPDATE ON system_improvements 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert initial data or configuration if needed
-- (This section can be used for default configurations)

-- Add comments for documentation
COMMENT ON TABLE openevolve_evaluations IS 'Stores OpenEvolve evaluation requests and results';
COMMENT ON TABLE system_improvements IS 'Stores system improvement recommendations from evaluations';
COMMENT ON TABLE evaluation_metrics IS 'Stores detailed metrics for completed evaluations';

COMMENT ON COLUMN openevolve_evaluations.evaluation_id IS 'OpenEvolve API evaluation identifier';
COMMENT ON COLUMN openevolve_evaluations.status IS 'Current status: pending, submitted, running, completed, failed, cancelled';
COMMENT ON COLUMN openevolve_evaluations.trigger_event IS 'Event that triggered the evaluation';
COMMENT ON COLUMN openevolve_evaluations.priority IS 'Evaluation priority (1=highest, 10=lowest)';
COMMENT ON COLUMN openevolve_evaluations.context IS 'Context data for the evaluation';
COMMENT ON COLUMN openevolve_evaluations.metadata IS 'Additional metadata';
COMMENT ON COLUMN openevolve_evaluations.results IS 'Evaluation results from OpenEvolve';
COMMENT ON COLUMN openevolve_evaluations.metrics IS 'Evaluation metrics';

COMMENT ON COLUMN system_improvements.improvement_type IS 'Type of improvement (e.g., performance, reliability, security)';
COMMENT ON COLUMN system_improvements.description IS 'Detailed description of the improvement';
COMMENT ON COLUMN system_improvements.estimated_impact IS 'Estimated impact score (0.0 to 1.0)';
COMMENT ON COLUMN system_improvements.implementation_complexity IS 'Complexity level (low, medium, high)';
COMMENT ON COLUMN system_improvements.applied IS 'Whether the improvement has been applied';
COMMENT ON COLUMN system_improvements.results IS 'Results after applying the improvement';

