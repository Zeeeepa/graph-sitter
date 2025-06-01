"""
Database schema for self-healing architecture.
"""

import os
from typing import Optional


def get_database_url() -> Optional[str]:
    """Get database URL from environment or configuration."""
    return os.getenv("SELF_HEALING_DATABASE_URL", os.getenv("DATABASE_URL"))


# SQL schema for self-healing tables
SCHEMA_SQL = """
-- Error tracking and recovery
CREATE TABLE IF NOT EXISTS error_incidents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    error_type VARCHAR(100) NOT NULL,
    severity VARCHAR(50) NOT NULL,
    message TEXT,
    context JSONB,
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    diagnosis JSONB,
    recovery_actions JSONB,
    effectiveness_score DECIMAL(3,2),
    source_component VARCHAR(255),
    stack_trace TEXT,
    metrics JSONB,
    tags TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS recovery_procedures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    error_pattern VARCHAR(255) NOT NULL,
    procedure_steps JSONB NOT NULL,
    success_rate DECIMAL(3,2) DEFAULT 0.0,
    execution_count INTEGER DEFAULT 0,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    description TEXT,
    parameters_schema JSONB,
    conditions JSONB,
    enabled BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS system_health_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_name VARCHAR(100) NOT NULL,
    current_value DECIMAL(15,6) NOT NULL,
    threshold_warning DECIMAL(15,6),
    threshold_critical DECIMAL(15,6),
    status VARCHAR(50) NOT NULL,
    measured_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    component VARCHAR(255),
    tags JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Diagnosis results table
CREATE TABLE IF NOT EXISTS diagnosis_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    error_event_id UUID NOT NULL,
    root_cause TEXT NOT NULL,
    confidence VARCHAR(50) NOT NULL,
    recommended_actions JSONB,
    analysis_data JSONB,
    correlated_events UUID[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    FOREIGN KEY (error_event_id) REFERENCES error_incidents(id) ON DELETE CASCADE
);

-- Recovery actions execution log
CREATE TABLE IF NOT EXISTS recovery_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    error_event_id UUID NOT NULL,
    diagnosis_id UUID,
    action_type VARCHAR(100) NOT NULL,
    description TEXT,
    parameters JSONB,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    result JSONB,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    FOREIGN KEY (error_event_id) REFERENCES error_incidents(id) ON DELETE CASCADE,
    FOREIGN KEY (diagnosis_id) REFERENCES diagnosis_results(id) ON DELETE SET NULL
);

-- Learning patterns and effectiveness tracking
CREATE TABLE IF NOT EXISTS learning_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_type VARCHAR(100) NOT NULL,
    pattern_data JSONB NOT NULL,
    effectiveness_score DECIMAL(3,2),
    usage_count INTEGER DEFAULT 0,
    last_used TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_error_incidents_detected_at ON error_incidents(detected_at);
CREATE INDEX IF NOT EXISTS idx_error_incidents_error_type ON error_incidents(error_type);
CREATE INDEX IF NOT EXISTS idx_error_incidents_severity ON error_incidents(severity);
CREATE INDEX IF NOT EXISTS idx_error_incidents_source_component ON error_incidents(source_component);

CREATE INDEX IF NOT EXISTS idx_recovery_procedures_error_pattern ON recovery_procedures(error_pattern);
CREATE INDEX IF NOT EXISTS idx_recovery_procedures_success_rate ON recovery_procedures(success_rate);

CREATE INDEX IF NOT EXISTS idx_system_health_metrics_metric_name ON system_health_metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_system_health_metrics_measured_at ON system_health_metrics(measured_at);
CREATE INDEX IF NOT EXISTS idx_system_health_metrics_status ON system_health_metrics(status);

CREATE INDEX IF NOT EXISTS idx_diagnosis_results_error_event_id ON diagnosis_results(error_event_id);
CREATE INDEX IF NOT EXISTS idx_diagnosis_results_confidence ON diagnosis_results(confidence);

CREATE INDEX IF NOT EXISTS idx_recovery_actions_error_event_id ON recovery_actions(error_event_id);
CREATE INDEX IF NOT EXISTS idx_recovery_actions_status ON recovery_actions(status);
CREATE INDEX IF NOT EXISTS idx_recovery_actions_action_type ON recovery_actions(action_type);

CREATE INDEX IF NOT EXISTS idx_learning_patterns_pattern_type ON learning_patterns(pattern_type);
CREATE INDEX IF NOT EXISTS idx_learning_patterns_effectiveness_score ON learning_patterns(effectiveness_score);

-- Update triggers for updated_at columns
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_error_incidents_updated_at BEFORE UPDATE ON error_incidents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_learning_patterns_updated_at BEFORE UPDATE ON learning_patterns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
"""


async def create_tables(database_url: Optional[str] = None) -> bool:
    """
    Create database tables for self-healing architecture.
    
    Args:
        database_url: Database connection URL. If None, will try to get from environment.
        
    Returns:
        True if tables were created successfully, False otherwise.
    """
    if database_url is None:
        database_url = get_database_url()
    
    if not database_url:
        print("Warning: No database URL provided. Self-healing database features will be disabled.")
        return False
    
    try:
        # Try to import asyncpg for PostgreSQL support
        import asyncpg
        
        conn = await asyncpg.connect(database_url)
        try:
            await conn.execute(SCHEMA_SQL)
            print("Self-healing database tables created successfully.")
            return True
        finally:
            await conn.close()
            
    except ImportError:
        print("Warning: asyncpg not available. Install with 'pip install asyncpg' for PostgreSQL support.")
        return False
    except Exception as e:
        print(f"Error creating self-healing database tables: {e}")
        return False


def get_schema_sql() -> str:
    """Get the SQL schema for self-healing tables."""
    return SCHEMA_SQL

