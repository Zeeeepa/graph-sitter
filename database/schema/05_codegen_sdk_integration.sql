-- =====================================================
-- Codegen SDK Integration Module
-- Agent management and capability tracking
-- =====================================================

-- Agent type enumeration
CREATE TYPE agent_type AS ENUM (
    'code_review', 'bug_fix', 'feature_dev', 'testing', 
    'documentation', 'refactoring', 'security_audit', 'performance_optimization'
);

-- Agent status enumeration
CREATE TYPE agent_status AS ENUM (
    'active', 'inactive', 'maintenance', 'deprecated'
);

-- Task status enumeration for agent tasks
CREATE TYPE agent_task_status AS ENUM (
    'queued', 'running', 'completed', 'failed', 'cancelled', 'timeout'
);

-- Main agents table
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    type agent_type NOT NULL,
    capabilities JSONB NOT NULL DEFAULT '[]',
    configuration JSONB DEFAULT '{}',
    status agent_status DEFAULT 'active',
    version VARCHAR(50),
    model_name VARCHAR(100), -- LLM model being used
    max_concurrent_tasks INTEGER DEFAULT 5,
    timeout_minutes INTEGER DEFAULT 30,
    cost_per_task_cents INTEGER DEFAULT 0,
    created_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    last_used_at TIMESTAMP WITH TIME ZONE,
    total_tasks_completed INTEGER DEFAULT 0,
    average_completion_time_ms INTEGER DEFAULT 0,
    success_rate DECIMAL(5,2) DEFAULT 0.00,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(organization_id, name),
    CONSTRAINT valid_max_concurrent CHECK (max_concurrent_tasks > 0),
    CONSTRAINT valid_timeout CHECK (timeout_minutes > 0),
    CONSTRAINT valid_success_rate CHECK (success_rate >= 0 AND success_rate <= 100)
);

-- Agent tasks table
CREATE TABLE agent_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
    repository_id UUID REFERENCES repositories(id) ON DELETE SET NULL,
    prompt TEXT NOT NULL,
    status agent_task_status NOT NULL DEFAULT 'queued',
    priority INTEGER DEFAULT 3, -- 1-5 scale
    context JSONB DEFAULT '{}',
    input_data JSONB DEFAULT '{}',
    result JSONB,
    output_artifacts JSONB DEFAULT '{}',
    error_details JSONB,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER,
    cost_cents INTEGER, -- Track API costs
    tokens_used INTEGER,
    model_version VARCHAR(50),
    created_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_priority CHECK (priority >= 1 AND priority <= 5),
    CONSTRAINT valid_retry_count CHECK (retry_count >= 0 AND retry_count <= max_retries),
    CONSTRAINT valid_duration CHECK (duration_ms >= 0),
    CONSTRAINT valid_cost CHECK (cost_cents >= 0),
    CONSTRAINT valid_time_range CHECK (completed_at IS NULL OR completed_at >= started_at)
);

-- Agent performance metrics table
CREATE TABLE agent_performance_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,6) NOT NULL,
    metric_unit VARCHAR(50),
    metric_category VARCHAR(50) DEFAULT 'performance', -- 'performance', 'cost', 'quality'
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT valid_metric_category CHECK (metric_category IN ('performance', 'cost', 'quality', 'usage'))
);

-- Agent capabilities table
CREATE TABLE agent_capabilities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    capability_name VARCHAR(100) NOT NULL,
    capability_description TEXT,
    parameters_schema JSONB DEFAULT '{}',
    is_enabled BOOLEAN DEFAULT true,
    confidence_score DECIMAL(3,2), -- 0.00 to 1.00
    usage_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(agent_id, capability_name),
    CONSTRAINT valid_confidence CHECK (confidence_score IS NULL OR (confidence_score >= 0 AND confidence_score <= 1))
);

-- Agent task dependencies table
CREATE TABLE agent_task_dependencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    dependent_task_id UUID NOT NULL REFERENCES agent_tasks(id) ON DELETE CASCADE,
    dependency_task_id UUID NOT NULL REFERENCES agent_tasks(id) ON DELETE CASCADE,
    dependency_type VARCHAR(50) DEFAULT 'blocks',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(dependent_task_id, dependency_task_id),
    CONSTRAINT no_self_dependency CHECK (dependent_task_id != dependency_task_id),
    CONSTRAINT valid_dependency_type CHECK (dependency_type IN ('blocks', 'requires_output', 'sequence'))
);

-- Agent feedback table
CREATE TABLE agent_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    agent_task_id UUID NOT NULL REFERENCES agent_tasks(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    rating INTEGER NOT NULL, -- 1-5 scale
    feedback_text TEXT,
    feedback_type VARCHAR(50) DEFAULT 'general',
    is_helpful BOOLEAN,
    improvement_suggestions JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_rating CHECK (rating >= 1 AND rating <= 5),
    CONSTRAINT valid_feedback_type CHECK (feedback_type IN ('general', 'accuracy', 'speed', 'quality', 'usability'))
);

-- Agent learning data table
CREATE TABLE agent_learning_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    learning_type VARCHAR(50) NOT NULL, -- 'success_pattern', 'failure_pattern', 'optimization'
    input_pattern JSONB NOT NULL,
    output_pattern JSONB,
    success_indicators JSONB DEFAULT '{}',
    confidence_score DECIMAL(3,2),
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_learning_type CHECK (learning_type IN ('success_pattern', 'failure_pattern', 'optimization', 'context_adaptation')),
    CONSTRAINT valid_confidence CHECK (confidence_score IS NULL OR (confidence_score >= 0 AND confidence_score <= 1))
);

-- =====================================================
-- Row-Level Security
-- =====================================================

ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_performance_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_capabilities ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_task_dependencies ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_learning_data ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY tenant_isolation_agents ON agents
    USING (organization_id = get_current_tenant());

CREATE POLICY tenant_isolation_agent_tasks ON agent_tasks
    USING (organization_id = get_current_tenant());

CREATE POLICY tenant_isolation_agent_performance_metrics ON agent_performance_metrics
    USING (organization_id = get_current_tenant());

CREATE POLICY tenant_isolation_agent_capabilities ON agent_capabilities
    USING (organization_id = get_current_tenant());

CREATE POLICY tenant_isolation_agent_task_dependencies ON agent_task_dependencies
    USING (organization_id = get_current_tenant());

CREATE POLICY tenant_isolation_agent_feedback ON agent_feedback
    USING (organization_id = get_current_tenant());

CREATE POLICY tenant_isolation_agent_learning_data ON agent_learning_data
    USING (organization_id = get_current_tenant());

-- =====================================================
-- Indexes for Performance
-- =====================================================

-- Agents
CREATE INDEX idx_agents_org_type ON agents(organization_id, type);
CREATE INDEX idx_agents_status ON agents(status);
CREATE INDEX idx_agents_last_used ON agents(last_used_at);
CREATE INDEX idx_agents_success_rate ON agents(success_rate);

-- Agent Tasks
CREATE INDEX idx_agent_tasks_agent_status ON agent_tasks(agent_id, status);
CREATE INDEX idx_agent_tasks_org_status ON agent_tasks(organization_id, status);
CREATE INDEX idx_agent_tasks_priority_created ON agent_tasks(priority, created_at);
CREATE INDEX idx_agent_tasks_repository ON agent_tasks(repository_id);
CREATE INDEX idx_agent_tasks_task ON agent_tasks(task_id);
CREATE INDEX idx_agent_tasks_created_at ON agent_tasks(created_at);

-- Agent Performance Metrics
CREATE INDEX idx_agent_metrics_agent_recorded ON agent_performance_metrics(agent_id, recorded_at);
CREATE INDEX idx_agent_metrics_category ON agent_performance_metrics(metric_category);
CREATE INDEX idx_agent_metrics_name ON agent_performance_metrics(metric_name);

-- Agent Capabilities
CREATE INDEX idx_agent_capabilities_agent ON agent_capabilities(agent_id);
CREATE INDEX idx_agent_capabilities_enabled ON agent_capabilities(agent_id, is_enabled);
CREATE INDEX idx_agent_capabilities_name ON agent_capabilities(capability_name);

-- Agent Feedback
CREATE INDEX idx_agent_feedback_task ON agent_feedback(agent_task_id);
CREATE INDEX idx_agent_feedback_rating ON agent_feedback(rating);
CREATE INDEX idx_agent_feedback_type ON agent_feedback(feedback_type);

-- Agent Learning Data
CREATE INDEX idx_agent_learning_agent_type ON agent_learning_data(agent_id, learning_type);
CREATE INDEX idx_agent_learning_confidence ON agent_learning_data(confidence_score);
CREATE INDEX idx_agent_learning_usage ON agent_learning_data(usage_count);

-- =====================================================
-- Functions for Agent Management
-- =====================================================

-- Function to calculate agent success rate
CREATE OR REPLACE FUNCTION calculate_agent_success_rate(agent_id UUID)
RETURNS DECIMAL(5,2) AS $$
DECLARE
    total_tasks INTEGER;
    successful_tasks INTEGER;
    success_rate DECIMAL(5,2);
BEGIN
    -- Count total and successful tasks in last 30 days
    SELECT 
        COUNT(*),
        COUNT(*) FILTER (WHERE status = 'completed')
    INTO total_tasks, successful_tasks
    FROM agent_tasks
    WHERE agent_tasks.agent_id = calculate_agent_success_rate.agent_id
    AND created_at > NOW() - INTERVAL '30 days'
    AND organization_id = get_current_tenant();
    
    IF total_tasks = 0 THEN
        RETURN 0.00;
    END IF;
    
    success_rate := (successful_tasks::DECIMAL / total_tasks) * 100;
    
    -- Update agent record
    UPDATE agents 
    SET success_rate = calculate_agent_success_rate.success_rate,
        total_tasks_completed = (
            SELECT COUNT(*) FROM agent_tasks 
            WHERE agent_tasks.agent_id = calculate_agent_success_rate.agent_id 
            AND status = 'completed'
        ),
        updated_at = NOW()
    WHERE id = calculate_agent_success_rate.agent_id;
    
    RETURN success_rate;
END;
$$ LANGUAGE plpgsql;

-- Function to get agent statistics
CREATE OR REPLACE FUNCTION get_agent_stats(agent_id UUID)
RETURNS JSONB AS $$
DECLARE
    stats JSONB;
BEGIN
    SELECT jsonb_build_object(
        'total_tasks', COUNT(*),
        'completed_tasks', COUNT(*) FILTER (WHERE status = 'completed'),
        'failed_tasks', COUNT(*) FILTER (WHERE status = 'failed'),
        'average_duration_ms', COALESCE(AVG(duration_ms) FILTER (WHERE status = 'completed'), 0),
        'total_cost_cents', COALESCE(SUM(cost_cents), 0),
        'average_cost_cents', COALESCE(AVG(cost_cents), 0),
        'total_tokens_used', COALESCE(SUM(tokens_used), 0),
        'success_rate_30d', (
            COUNT(*) FILTER (WHERE status = 'completed' AND created_at > NOW() - INTERVAL '30 days')::DECIMAL /
            NULLIF(COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '30 days'), 0) * 100
        ),
        'average_rating', (
            SELECT COALESCE(AVG(rating), 0) 
            FROM agent_feedback af 
            JOIN agent_tasks at ON af.agent_task_id = at.id 
            WHERE at.agent_id = get_agent_stats.agent_id
        )
    ) INTO stats
    FROM agent_tasks
    WHERE agent_tasks.agent_id = get_agent_stats.agent_id
    AND organization_id = get_current_tenant();
    
    RETURN stats;
END;
$$ LANGUAGE plpgsql;

-- Function to find best agent for task
CREATE OR REPLACE FUNCTION find_best_agent_for_task(
    task_type VARCHAR(100),
    required_capabilities JSONB DEFAULT '[]'
) RETURNS UUID AS $$
DECLARE
    best_agent_id UUID;
    capability_name TEXT;
BEGIN
    -- Find agent with highest success rate that has required capabilities
    SELECT a.id INTO best_agent_id
    FROM agents a
    WHERE a.organization_id = get_current_tenant()
    AND a.status = 'active'
    AND a.type::TEXT = task_type
    AND (
        jsonb_array_length(required_capabilities) = 0 OR
        EXISTS (
            SELECT 1 FROM jsonb_array_elements_text(required_capabilities) AS req_cap
            WHERE EXISTS (
                SELECT 1 FROM agent_capabilities ac
                WHERE ac.agent_id = a.id 
                AND ac.capability_name = req_cap 
                AND ac.is_enabled = true
            )
        )
    )
    AND (
        SELECT COUNT(*) FROM agent_tasks at 
        WHERE at.agent_id = a.id 
        AND at.status IN ('queued', 'running')
    ) < a.max_concurrent_tasks
    ORDER BY a.success_rate DESC, a.average_completion_time_ms ASC
    LIMIT 1;
    
    RETURN best_agent_id;
END;
$$ LANGUAGE plpgsql;

-- Function to queue agent task
CREATE OR REPLACE FUNCTION queue_agent_task(
    agent_id UUID,
    prompt TEXT,
    context JSONB DEFAULT '{}',
    priority INTEGER DEFAULT 3,
    task_id UUID DEFAULT NULL,
    repository_id UUID DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    new_task_id UUID;
    agent_available BOOLEAN;
BEGIN
    -- Check if agent is available
    SELECT (
        SELECT COUNT(*) FROM agent_tasks 
        WHERE agent_tasks.agent_id = queue_agent_task.agent_id 
        AND status IN ('queued', 'running')
    ) < (
        SELECT max_concurrent_tasks FROM agents 
        WHERE id = queue_agent_task.agent_id
    ) INTO agent_available;
    
    IF NOT agent_available THEN
        RAISE EXCEPTION 'Agent is at maximum concurrent task limit';
    END IF;
    
    -- Create new agent task
    INSERT INTO agent_tasks (
        organization_id,
        agent_id,
        task_id,
        repository_id,
        prompt,
        priority,
        context,
        created_by_user_id
    ) VALUES (
        get_current_tenant(),
        queue_agent_task.agent_id,
        queue_agent_task.task_id,
        queue_agent_task.repository_id,
        queue_agent_task.prompt,
        queue_agent_task.priority,
        queue_agent_task.context,
        current_setting('app.current_user_id', true)::UUID
    ) RETURNING id INTO new_task_id;
    
    RETURN new_task_id;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- Triggers
-- =====================================================

-- Update timestamp triggers
CREATE TRIGGER update_agents_updated_at 
    BEFORE UPDATE ON agents 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agent_capabilities_updated_at 
    BEFORE UPDATE ON agent_capabilities 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agent_learning_data_updated_at 
    BEFORE UPDATE ON agent_learning_data 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger to update agent statistics
CREATE OR REPLACE FUNCTION update_agent_stats()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'UPDATE' AND OLD.status IS DISTINCT FROM NEW.status THEN
        IF NEW.status IN ('completed', 'failed') THEN
            -- Calculate task duration
            IF NEW.started_at IS NOT NULL AND NEW.completed_at IS NOT NULL THEN
                NEW.duration_ms := EXTRACT(EPOCH FROM (NEW.completed_at - NEW.started_at)) * 1000;
            END IF;
            
            -- Update agent success rate and last used time
            PERFORM calculate_agent_success_rate(NEW.agent_id);
            
            UPDATE agents 
            SET last_used_at = NEW.completed_at,
                average_completion_time_ms = (
                    SELECT COALESCE(AVG(duration_ms)::INTEGER, 0)
                    FROM agent_tasks 
                    WHERE agent_id = NEW.agent_id 
                    AND status = 'completed'
                    AND duration_ms IS NOT NULL
                ),
                updated_at = NOW()
            WHERE id = NEW.agent_id;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_agent_stats_trigger
    AFTER UPDATE ON agent_tasks
    FOR EACH ROW EXECUTE FUNCTION update_agent_stats();

-- Trigger to update capability usage
CREATE OR REPLACE FUNCTION update_capability_usage()
RETURNS TRIGGER AS $$
DECLARE
    capability_names JSONB;
    capability_name TEXT;
BEGIN
    IF TG_OP = 'UPDATE' AND OLD.status != 'completed' AND NEW.status = 'completed' THEN
        -- Extract used capabilities from result
        capability_names := NEW.result->'capabilities_used';
        
        IF capability_names IS NOT NULL THEN
            FOR capability_name IN SELECT jsonb_array_elements_text(capability_names)
            LOOP
                UPDATE agent_capabilities 
                SET usage_count = usage_count + 1,
                    success_count = success_count + 1,
                    updated_at = NOW()
                WHERE agent_id = NEW.agent_id 
                AND capability_name = update_capability_usage.capability_name;
            END LOOP;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_capability_usage_trigger
    AFTER UPDATE ON agent_tasks
    FOR EACH ROW EXECUTE FUNCTION update_capability_usage();

-- Audit triggers
CREATE TRIGGER audit_agents 
    AFTER INSERT OR UPDATE OR DELETE ON agents
    FOR EACH ROW EXECUTE FUNCTION create_audit_log();

-- =====================================================
-- Views for Common Queries
-- =====================================================

-- Agent summary view
CREATE VIEW agent_summary AS
SELECT 
    a.id,
    a.organization_id,
    a.name,
    a.type,
    a.status,
    a.success_rate,
    a.total_tasks_completed,
    a.average_completion_time_ms,
    COUNT(DISTINCT at.id) as active_tasks,
    COUNT(DISTINCT ac.id) as capability_count,
    COALESCE(AVG(af.rating), 0) as average_rating,
    a.last_used_at,
    a.created_at,
    a.updated_at
FROM agents a
LEFT JOIN agent_tasks at ON a.id = at.agent_id AND at.status IN ('queued', 'running')
LEFT JOIN agent_capabilities ac ON a.id = ac.agent_id AND ac.is_enabled = true
LEFT JOIN agent_tasks at2 ON a.id = at2.agent_id
LEFT JOIN agent_feedback af ON at2.id = af.agent_task_id
GROUP BY a.id;

