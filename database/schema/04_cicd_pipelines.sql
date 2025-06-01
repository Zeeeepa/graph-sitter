-- =====================================================
-- CI/CD Pipelines Module
-- Pipeline definition and execution tracking
-- =====================================================

-- Pipeline status enumeration
CREATE TYPE pipeline_status AS ENUM (
    'active', 'inactive', 'archived', 'draft'
);

-- Execution status enumeration
CREATE TYPE execution_status AS ENUM (
    'queued', 'running', 'completed', 'failed', 'cancelled', 'timeout'
);

-- Step status enumeration
CREATE TYPE step_status AS ENUM (
    'pending', 'running', 'completed', 'failed', 'skipped', 'cancelled'
);

-- Main pipelines table
CREATE TABLE pipelines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    repository_id UUID NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    definition JSONB NOT NULL, -- Pipeline configuration (YAML/JSON)
    trigger_config JSONB DEFAULT '{}',
    environment_variables JSONB DEFAULT '{}',
    status pipeline_status DEFAULT 'active',
    version INTEGER DEFAULT 1,
    created_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    last_execution_at TIMESTAMP WITH TIME ZONE,
    success_rate DECIMAL(5,2) DEFAULT 0.00, -- Percentage
    average_duration_ms INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(organization_id, repository_id, name),
    CONSTRAINT valid_success_rate CHECK (success_rate >= 0 AND success_rate <= 100)
);

-- Pipeline executions table (partitioned by date)
CREATE TABLE pipeline_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    pipeline_id UUID NOT NULL REFERENCES pipelines(id) ON DELETE CASCADE,
    trigger_event JSONB NOT NULL,
    trigger_type VARCHAR(50) NOT NULL, -- 'push', 'pull_request', 'schedule', 'manual'
    branch_name VARCHAR(255),
    commit_sha VARCHAR(40),
    commit_message TEXT,
    status execution_status NOT NULL DEFAULT 'queued',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER,
    metadata JSONB DEFAULT '{}',
    environment JSONB DEFAULT '{}',
    artifacts JSONB DEFAULT '{}',
    error_details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_duration CHECK (duration_ms >= 0),
    CONSTRAINT valid_time_range CHECK (completed_at IS NULL OR completed_at >= started_at)
) PARTITION BY RANGE (created_at);

-- Create partitions for pipeline executions (monthly)
CREATE TABLE pipeline_executions_y2024m01 PARTITION OF pipeline_executions
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
CREATE TABLE pipeline_executions_y2024m02 PARTITION OF pipeline_executions
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
CREATE TABLE pipeline_executions_y2024m03 PARTITION OF pipeline_executions
    FOR VALUES FROM ('2024-03-01') TO ('2024-04-01');
-- Add more partitions as needed

-- Pipeline steps table
CREATE TABLE pipeline_steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    execution_id UUID NOT NULL REFERENCES pipeline_executions(id) ON DELETE CASCADE,
    step_name VARCHAR(255) NOT NULL,
    step_type VARCHAR(100) NOT NULL, -- 'build', 'test', 'deploy', 'custom'
    step_order INTEGER NOT NULL,
    depends_on JSONB DEFAULT '[]', -- Array of step names this step depends on
    configuration JSONB DEFAULT '{}',
    status step_status NOT NULL DEFAULT 'pending',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER,
    logs TEXT,
    artifacts JSONB DEFAULT '{}',
    metrics JSONB DEFAULT '{}',
    error_details JSONB,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_step_duration CHECK (duration_ms >= 0),
    CONSTRAINT valid_retry_count CHECK (retry_count >= 0 AND retry_count <= max_retries),
    CONSTRAINT valid_step_time_range CHECK (completed_at IS NULL OR completed_at >= started_at)
);

-- Pipeline triggers table
CREATE TABLE pipeline_triggers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    pipeline_id UUID NOT NULL REFERENCES pipelines(id) ON DELETE CASCADE,
    trigger_type VARCHAR(50) NOT NULL,
    trigger_config JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    last_triggered_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_trigger_type CHECK (trigger_type IN ('push', 'pull_request', 'schedule', 'webhook', 'manual'))
);

-- Pipeline environments table
CREATE TABLE pipeline_environments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    pipeline_id UUID NOT NULL REFERENCES pipelines(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    variables JSONB DEFAULT '{}',
    secrets JSONB DEFAULT '{}', -- Encrypted secrets
    deployment_config JSONB DEFAULT '{}',
    is_production BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(pipeline_id, name)
);

-- Pipeline artifacts table
CREATE TABLE pipeline_artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    execution_id UUID NOT NULL REFERENCES pipeline_executions(id) ON DELETE CASCADE,
    step_id UUID REFERENCES pipeline_steps(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100) NOT NULL, -- 'build', 'test_report', 'coverage', 'docker_image'
    file_path TEXT,
    file_size INTEGER,
    checksum VARCHAR(64),
    metadata JSONB DEFAULT '{}',
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_file_size CHECK (file_size >= 0)
);

-- Pipeline notifications table
CREATE TABLE pipeline_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    pipeline_id UUID NOT NULL REFERENCES pipelines(id) ON DELETE CASCADE,
    notification_type VARCHAR(50) NOT NULL, -- 'email', 'slack', 'webhook'
    trigger_events JSONB NOT NULL DEFAULT '[]', -- ['success', 'failure', 'start']
    configuration JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_notification_type CHECK (notification_type IN ('email', 'slack', 'webhook', 'linear'))
);

-- =====================================================
-- Row-Level Security
-- =====================================================

ALTER TABLE pipelines ENABLE ROW LEVEL SECURITY;
ALTER TABLE pipeline_executions ENABLE ROW LEVEL SECURITY;
ALTER TABLE pipeline_steps ENABLE ROW LEVEL SECURITY;
ALTER TABLE pipeline_triggers ENABLE ROW LEVEL SECURITY;
ALTER TABLE pipeline_environments ENABLE ROW LEVEL SECURITY;
ALTER TABLE pipeline_artifacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE pipeline_notifications ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY tenant_isolation_pipelines ON pipelines
    USING (organization_id = get_current_tenant());

CREATE POLICY tenant_isolation_pipeline_executions ON pipeline_executions
    USING (organization_id = get_current_tenant());

CREATE POLICY tenant_isolation_pipeline_steps ON pipeline_steps
    USING (organization_id = get_current_tenant());

CREATE POLICY tenant_isolation_pipeline_triggers ON pipeline_triggers
    USING (organization_id = get_current_tenant());

CREATE POLICY tenant_isolation_pipeline_environments ON pipeline_environments
    USING (organization_id = get_current_tenant());

CREATE POLICY tenant_isolation_pipeline_artifacts ON pipeline_artifacts
    USING (organization_id = get_current_tenant());

CREATE POLICY tenant_isolation_pipeline_notifications ON pipeline_notifications
    USING (organization_id = get_current_tenant());

-- =====================================================
-- Indexes for Performance
-- =====================================================

-- Pipelines
CREATE INDEX idx_pipelines_org_repo ON pipelines(organization_id, repository_id);
CREATE INDEX idx_pipelines_status ON pipelines(status);
CREATE INDEX idx_pipelines_last_execution ON pipelines(last_execution_at);

-- Pipeline Executions
CREATE INDEX idx_pipeline_executions_pipeline_created ON pipeline_executions(pipeline_id, created_at);
CREATE INDEX idx_pipeline_executions_org_status ON pipeline_executions(organization_id, status);
CREATE INDEX idx_pipeline_executions_trigger_type ON pipeline_executions(trigger_type);
CREATE INDEX idx_pipeline_executions_branch ON pipeline_executions(branch_name);
CREATE INDEX idx_pipeline_executions_commit ON pipeline_executions(commit_sha);

-- Pipeline Steps
CREATE INDEX idx_pipeline_steps_execution_order ON pipeline_steps(execution_id, step_order);
CREATE INDEX idx_pipeline_steps_status ON pipeline_steps(status);
CREATE INDEX idx_pipeline_steps_type ON pipeline_steps(step_type);
CREATE INDEX idx_pipeline_steps_duration ON pipeline_steps(duration_ms);

-- Pipeline Triggers
CREATE INDEX idx_pipeline_triggers_pipeline_active ON pipeline_triggers(pipeline_id, is_active);
CREATE INDEX idx_pipeline_triggers_type ON pipeline_triggers(trigger_type);

-- Pipeline Artifacts
CREATE INDEX idx_pipeline_artifacts_execution ON pipeline_artifacts(execution_id);
CREATE INDEX idx_pipeline_artifacts_type ON pipeline_artifacts(type);
CREATE INDEX idx_pipeline_artifacts_expires ON pipeline_artifacts(expires_at);

-- =====================================================
-- Functions for Pipeline Management
-- =====================================================

-- Function to calculate pipeline success rate
CREATE OR REPLACE FUNCTION calculate_pipeline_success_rate(pipeline_id UUID)
RETURNS DECIMAL(5,2) AS $$
DECLARE
    total_executions INTEGER;
    successful_executions INTEGER;
    success_rate DECIMAL(5,2);
BEGIN
    -- Count total and successful executions in last 30 days
    SELECT 
        COUNT(*),
        COUNT(*) FILTER (WHERE status = 'completed')
    INTO total_executions, successful_executions
    FROM pipeline_executions
    WHERE pipeline_executions.pipeline_id = calculate_pipeline_success_rate.pipeline_id
    AND created_at > NOW() - INTERVAL '30 days'
    AND organization_id = get_current_tenant();
    
    IF total_executions = 0 THEN
        RETURN 0.00;
    END IF;
    
    success_rate := (successful_executions::DECIMAL / total_executions) * 100;
    
    -- Update pipeline record
    UPDATE pipelines 
    SET success_rate = calculate_pipeline_success_rate.success_rate,
        updated_at = NOW()
    WHERE id = calculate_pipeline_success_rate.pipeline_id;
    
    RETURN success_rate;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate average pipeline duration
CREATE OR REPLACE FUNCTION calculate_average_duration(pipeline_id UUID)
RETURNS INTEGER AS $$
DECLARE
    avg_duration INTEGER;
BEGIN
    SELECT COALESCE(AVG(duration_ms)::INTEGER, 0)
    INTO avg_duration
    FROM pipeline_executions
    WHERE pipeline_executions.pipeline_id = calculate_average_duration.pipeline_id
    AND status = 'completed'
    AND created_at > NOW() - INTERVAL '30 days'
    AND organization_id = get_current_tenant();
    
    -- Update pipeline record
    UPDATE pipelines 
    SET average_duration_ms = avg_duration,
        updated_at = NOW()
    WHERE id = calculate_average_duration.pipeline_id;
    
    RETURN avg_duration;
END;
$$ LANGUAGE plpgsql;

-- Function to get pipeline execution statistics
CREATE OR REPLACE FUNCTION get_pipeline_execution_stats(pipeline_id UUID)
RETURNS JSONB AS $$
DECLARE
    stats JSONB;
BEGIN
    SELECT jsonb_build_object(
        'total_executions', COUNT(*),
        'successful_executions', COUNT(*) FILTER (WHERE status = 'completed'),
        'failed_executions', COUNT(*) FILTER (WHERE status = 'failed'),
        'average_duration_ms', COALESCE(AVG(duration_ms), 0),
        'last_execution_at', MAX(created_at),
        'success_rate_30d', (
            COUNT(*) FILTER (WHERE status = 'completed' AND created_at > NOW() - INTERVAL '30 days')::DECIMAL /
            NULLIF(COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '30 days'), 0) * 100
        )
    ) INTO stats
    FROM pipeline_executions
    WHERE pipeline_executions.pipeline_id = get_pipeline_execution_stats.pipeline_id
    AND organization_id = get_current_tenant();
    
    RETURN stats;
END;
$$ LANGUAGE plpgsql;

-- Function to check if pipeline can be triggered
CREATE OR REPLACE FUNCTION can_trigger_pipeline(
    pipeline_id UUID,
    trigger_type VARCHAR(50)
) RETURNS BOOLEAN AS $$
DECLARE
    pipeline_active BOOLEAN;
    trigger_active BOOLEAN;
    concurrent_executions INTEGER;
BEGIN
    -- Check if pipeline is active
    SELECT status = 'active' INTO pipeline_active
    FROM pipelines
    WHERE id = pipeline_id AND organization_id = get_current_tenant();
    
    IF NOT pipeline_active THEN
        RETURN FALSE;
    END IF;
    
    -- Check if trigger is active
    SELECT EXISTS(
        SELECT 1 FROM pipeline_triggers
        WHERE pipeline_triggers.pipeline_id = can_trigger_pipeline.pipeline_id
        AND pipeline_triggers.trigger_type = can_trigger_pipeline.trigger_type
        AND is_active = true
    ) INTO trigger_active;
    
    IF NOT trigger_active THEN
        RETURN FALSE;
    END IF;
    
    -- Check concurrent execution limit (max 3 concurrent executions per pipeline)
    SELECT COUNT(*) INTO concurrent_executions
    FROM pipeline_executions
    WHERE pipeline_executions.pipeline_id = can_trigger_pipeline.pipeline_id
    AND status IN ('queued', 'running')
    AND organization_id = get_current_tenant();
    
    RETURN concurrent_executions < 3;
END;
$$ LANGUAGE plpgsql;

-- Function to cleanup expired artifacts
CREATE OR REPLACE FUNCTION cleanup_expired_artifacts()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM pipeline_artifacts
    WHERE expires_at IS NOT NULL 
    AND expires_at < NOW();
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- Triggers
-- =====================================================

-- Update timestamp triggers
CREATE TRIGGER update_pipelines_updated_at 
    BEFORE UPDATE ON pipelines 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_pipeline_triggers_updated_at 
    BEFORE UPDATE ON pipeline_triggers 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_pipeline_environments_updated_at 
    BEFORE UPDATE ON pipeline_environments 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_pipeline_notifications_updated_at 
    BEFORE UPDATE ON pipeline_notifications 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger to update pipeline statistics
CREATE OR REPLACE FUNCTION update_pipeline_stats()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'UPDATE' AND OLD.status IS DISTINCT FROM NEW.status THEN
        IF NEW.status IN ('completed', 'failed') THEN
            -- Update success rate and average duration
            PERFORM calculate_pipeline_success_rate(NEW.pipeline_id);
            PERFORM calculate_average_duration(NEW.pipeline_id);
            
            -- Update last execution time
            UPDATE pipelines 
            SET last_execution_at = NEW.completed_at,
                updated_at = NOW()
            WHERE id = NEW.pipeline_id;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_pipeline_stats_trigger
    AFTER UPDATE ON pipeline_executions
    FOR EACH ROW EXECUTE FUNCTION update_pipeline_stats();

-- Trigger to calculate execution duration
CREATE OR REPLACE FUNCTION calculate_execution_duration()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'UPDATE' AND OLD.completed_at IS NULL AND NEW.completed_at IS NOT NULL THEN
        NEW.duration_ms := EXTRACT(EPOCH FROM (NEW.completed_at - NEW.started_at)) * 1000;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER calculate_execution_duration_trigger
    BEFORE UPDATE ON pipeline_executions
    FOR EACH ROW EXECUTE FUNCTION calculate_execution_duration();

CREATE TRIGGER calculate_step_duration_trigger
    BEFORE UPDATE ON pipeline_steps
    FOR EACH ROW EXECUTE FUNCTION calculate_execution_duration();

-- Audit triggers
CREATE TRIGGER audit_pipelines 
    AFTER INSERT OR UPDATE OR DELETE ON pipelines
    FOR EACH ROW EXECUTE FUNCTION create_audit_log();

-- =====================================================
-- Views for Common Queries
-- =====================================================

-- Pipeline summary view
CREATE VIEW pipeline_summary AS
SELECT 
    p.id,
    p.organization_id,
    p.name,
    p.status,
    r.name as repository_name,
    r.full_name as repository_full_name,
    p.success_rate,
    p.average_duration_ms,
    p.last_execution_at,
    COUNT(DISTINCT pe.id) as total_executions,
    COUNT(DISTINCT pe.id) FILTER (WHERE pe.status = 'completed') as successful_executions,
    COUNT(DISTINCT pe.id) FILTER (WHERE pe.status = 'failed') as failed_executions,
    COUNT(DISTINCT pt.id) as trigger_count,
    p.created_at,
    p.updated_at
FROM pipelines p
LEFT JOIN repositories r ON p.repository_id = r.id
LEFT JOIN pipeline_executions pe ON p.id = pe.pipeline_id
LEFT JOIN pipeline_triggers pt ON p.id = pt.pipeline_id AND pt.is_active = true
GROUP BY p.id, r.id;

-- Recent pipeline executions view
CREATE VIEW recent_pipeline_executions AS
SELECT 
    pe.id,
    pe.organization_id,
    p.name as pipeline_name,
    r.name as repository_name,
    pe.status,
    pe.trigger_type,
    pe.branch_name,
    pe.commit_sha,
    pe.duration_ms,
    pe.started_at,
    pe.completed_at,
    pe.created_at
FROM pipeline_executions pe
JOIN pipelines p ON pe.pipeline_id = p.id
JOIN repositories r ON p.repository_id = r.id
WHERE pe.created_at > NOW() - INTERVAL '7 days'
ORDER BY pe.created_at DESC;

