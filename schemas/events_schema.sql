-- =====================================================
-- Event System Database Schema
-- Core-7: Event System & Multi-Platform Integration
-- =====================================================

-- Enable UUID extension for PostgreSQL
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- Core Event Tables
-- =====================================================

-- Main events table for all platform events
CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id VARCHAR(255) UNIQUE NOT NULL, -- Platform-specific event ID
    platform VARCHAR(50) NOT NULL, -- 'github', 'linear', 'slack', 'deployment'
    event_type VARCHAR(100) NOT NULL, -- e.g., 'pull_request:opened', 'issue:created'
    source_id VARCHAR(255), -- Repository ID, workspace ID, etc.
    source_name VARCHAR(255), -- Repository name, workspace name, etc.
    actor_id VARCHAR(255), -- User/bot who triggered the event
    actor_name VARCHAR(255), -- User/bot display name
    payload JSONB NOT NULL, -- Full event payload
    metadata JSONB DEFAULT '{}', -- Additional metadata
    processed BOOLEAN DEFAULT FALSE, -- Whether event has been processed
    correlation_id UUID, -- For linking related events
    parent_event_id UUID REFERENCES events(id), -- For event hierarchies
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE
);

-- Event processing status tracking
CREATE TABLE event_processing_status (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    processor_name VARCHAR(100) NOT NULL, -- Name of the processor/handler
    status VARCHAR(50) NOT NULL, -- 'pending', 'processing', 'completed', 'failed', 'retrying'
    attempt_count INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Event correlations for cross-platform event linking
CREATE TABLE event_correlations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    correlation_id UUID NOT NULL,
    primary_event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    related_event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    correlation_type VARCHAR(100) NOT NULL, -- 'pr_to_issue', 'deployment_to_pr', etc.
    confidence_score DECIMAL(3,2) DEFAULT 1.0, -- 0.0 to 1.0
    correlation_data JSONB DEFAULT '{}', -- Additional correlation metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(primary_event_id, related_event_id, correlation_type)
);

-- =====================================================
-- Platform-Specific Event Tables
-- =====================================================

-- GitHub-specific event details
CREATE TABLE github_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    repository_id BIGINT,
    repository_name VARCHAR(255),
    organization VARCHAR(255),
    installation_id BIGINT,
    pull_request_number INTEGER,
    issue_number INTEGER,
    commit_sha VARCHAR(40),
    branch_name VARCHAR(255),
    action VARCHAR(100), -- 'opened', 'closed', 'merged', etc.
    labels JSONB DEFAULT '[]',
    assignees JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Linear-specific event details
CREATE TABLE linear_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    workspace_id VARCHAR(255),
    team_id VARCHAR(255),
    issue_id VARCHAR(255),
    project_id VARCHAR(255),
    cycle_id VARCHAR(255),
    issue_number INTEGER,
    issue_title TEXT,
    state_name VARCHAR(100),
    priority INTEGER,
    labels JSONB DEFAULT '[]',
    assignee_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Slack-specific event details
CREATE TABLE slack_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    workspace_id VARCHAR(255),
    channel_id VARCHAR(255),
    channel_name VARCHAR(255),
    user_id VARCHAR(255),
    thread_ts VARCHAR(255),
    message_ts VARCHAR(255),
    message_text TEXT,
    message_type VARCHAR(100),
    bot_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Deployment-specific event details
CREATE TABLE deployment_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    deployment_id VARCHAR(255),
    environment VARCHAR(100), -- 'production', 'staging', 'development'
    status VARCHAR(100), -- 'pending', 'in_progress', 'success', 'failure'
    repository_name VARCHAR(255),
    commit_sha VARCHAR(40),
    branch_name VARCHAR(255),
    deployment_url TEXT,
    log_url TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- Event Streaming and Real-time Tables
-- =====================================================

-- Event streams for real-time processing
CREATE TABLE event_streams (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stream_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    filter_criteria JSONB DEFAULT '{}', -- JSON filter for events
    is_active BOOLEAN DEFAULT TRUE,
    subscriber_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Stream subscriptions for real-time event delivery
CREATE TABLE stream_subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stream_id UUID NOT NULL REFERENCES event_streams(id) ON DELETE CASCADE,
    subscriber_id VARCHAR(255) NOT NULL, -- Client/service identifier
    subscriber_type VARCHAR(50) NOT NULL, -- 'websocket', 'webhook', 'internal'
    endpoint_url TEXT, -- For webhook subscriptions
    is_active BOOLEAN DEFAULT TRUE,
    last_delivered_event_id UUID REFERENCES events(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(stream_id, subscriber_id)
);

-- Event delivery tracking
CREATE TABLE event_deliveries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    subscription_id UUID NOT NULL REFERENCES stream_subscriptions(id) ON DELETE CASCADE,
    delivery_status VARCHAR(50) NOT NULL, -- 'pending', 'delivered', 'failed', 'retrying'
    attempt_count INTEGER DEFAULT 0,
    response_code INTEGER,
    response_body TEXT,
    error_message TEXT,
    delivered_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- Event Analytics and Metrics
-- =====================================================

-- Event metrics aggregation
CREATE TABLE event_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_date DATE NOT NULL,
    platform VARCHAR(50) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    source_name VARCHAR(255),
    event_count INTEGER DEFAULT 0,
    processing_time_avg DECIMAL(10,3), -- Average processing time in seconds
    processing_time_max DECIMAL(10,3), -- Max processing time in seconds
    error_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(metric_date, platform, event_type, source_name)
);

-- Event processing performance tracking
CREATE TABLE event_performance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    processor_name VARCHAR(100) NOT NULL,
    processing_duration DECIMAL(10,3) NOT NULL, -- Duration in seconds
    memory_usage_mb INTEGER,
    cpu_usage_percent DECIMAL(5,2),
    queue_wait_time DECIMAL(10,3), -- Time spent waiting in queue
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- Indexes for Performance
-- =====================================================

-- Primary event indexes
CREATE INDEX idx_events_platform_type ON events(platform, event_type);
CREATE INDEX idx_events_created_at ON events(created_at);
CREATE INDEX idx_events_processed ON events(processed);
CREATE INDEX idx_events_correlation_id ON events(correlation_id);
CREATE INDEX idx_events_source_id ON events(source_id);
CREATE INDEX idx_events_actor_id ON events(actor_id);

-- Event processing indexes
CREATE INDEX idx_event_processing_status_event_id ON event_processing_status(event_id);
CREATE INDEX idx_event_processing_status_processor ON event_processing_status(processor_name, status);
CREATE INDEX idx_event_processing_created_at ON event_processing_status(created_at);

-- Correlation indexes
CREATE INDEX idx_event_correlations_correlation_id ON event_correlations(correlation_id);
CREATE INDEX idx_event_correlations_primary_event ON event_correlations(primary_event_id);
CREATE INDEX idx_event_correlations_related_event ON event_correlations(related_event_id);
CREATE INDEX idx_event_correlations_type ON event_correlations(correlation_type);

-- Platform-specific indexes
CREATE INDEX idx_github_events_repo ON github_events(repository_name);
CREATE INDEX idx_github_events_pr ON github_events(pull_request_number);
CREATE INDEX idx_github_events_commit ON github_events(commit_sha);

CREATE INDEX idx_linear_events_issue ON linear_events(issue_id);
CREATE INDEX idx_linear_events_team ON linear_events(team_id);
CREATE INDEX idx_linear_events_project ON linear_events(project_id);

CREATE INDEX idx_slack_events_channel ON slack_events(channel_id);
CREATE INDEX idx_slack_events_user ON slack_events(user_id);
CREATE INDEX idx_slack_events_thread ON slack_events(thread_ts);

CREATE INDEX idx_deployment_events_repo ON deployment_events(repository_name);
CREATE INDEX idx_deployment_events_env ON deployment_events(environment);
CREATE INDEX idx_deployment_events_status ON deployment_events(status);

-- Streaming indexes
CREATE INDEX idx_stream_subscriptions_stream ON stream_subscriptions(stream_id);
CREATE INDEX idx_stream_subscriptions_subscriber ON stream_subscriptions(subscriber_id);
CREATE INDEX idx_event_deliveries_event ON event_deliveries(event_id);
CREATE INDEX idx_event_deliveries_subscription ON event_deliveries(subscription_id);
CREATE INDEX idx_event_deliveries_status ON event_deliveries(delivery_status);

-- Analytics indexes
CREATE INDEX idx_event_metrics_date_platform ON event_metrics(metric_date, platform);
CREATE INDEX idx_event_metrics_platform_type ON event_metrics(platform, event_type);
CREATE INDEX idx_event_performance_processor ON event_performance(processor_name);
CREATE INDEX idx_event_performance_duration ON event_performance(processing_duration);

-- =====================================================
-- Triggers for Automatic Updates
-- =====================================================

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update triggers
CREATE TRIGGER update_events_updated_at BEFORE UPDATE ON events
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_event_processing_status_updated_at BEFORE UPDATE ON event_processing_status
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_event_streams_updated_at BEFORE UPDATE ON event_streams
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_stream_subscriptions_updated_at BEFORE UPDATE ON stream_subscriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_event_deliveries_updated_at BEFORE UPDATE ON event_deliveries
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_event_metrics_updated_at BEFORE UPDATE ON event_metrics
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- Views for Common Queries
-- =====================================================

-- Recent events with platform details
CREATE VIEW recent_events AS
SELECT 
    e.id,
    e.event_id,
    e.platform,
    e.event_type,
    e.source_name,
    e.actor_name,
    e.created_at,
    e.processed,
    CASE 
        WHEN e.platform = 'github' THEN gh.repository_name
        WHEN e.platform = 'linear' THEN le.issue_title
        WHEN e.platform = 'slack' THEN se.channel_name
        WHEN e.platform = 'deployment' THEN de.environment
    END as context_info
FROM events e
LEFT JOIN github_events gh ON e.id = gh.event_id
LEFT JOIN linear_events le ON e.id = le.event_id
LEFT JOIN slack_events se ON e.id = se.event_id
LEFT JOIN deployment_events de ON e.id = de.event_id
ORDER BY e.created_at DESC;

-- Event processing summary
CREATE VIEW event_processing_summary AS
SELECT 
    e.platform,
    e.event_type,
    COUNT(*) as total_events,
    COUNT(CASE WHEN e.processed THEN 1 END) as processed_events,
    COUNT(CASE WHEN eps.status = 'failed' THEN 1 END) as failed_events,
    AVG(ep.processing_duration) as avg_processing_time
FROM events e
LEFT JOIN event_processing_status eps ON e.id = eps.event_id
LEFT JOIN event_performance ep ON e.id = ep.event_id
GROUP BY e.platform, e.event_type;

-- Correlated events view
CREATE VIEW correlated_events AS
SELECT 
    ec.correlation_id,
    ec.correlation_type,
    pe.platform as primary_platform,
    pe.event_type as primary_event_type,
    pe.source_name as primary_source,
    re.platform as related_platform,
    re.event_type as related_event_type,
    re.source_name as related_source,
    ec.confidence_score,
    ec.created_at
FROM event_correlations ec
JOIN events pe ON ec.primary_event_id = pe.id
JOIN events re ON ec.related_event_id = re.id
ORDER BY ec.created_at DESC;

-- =====================================================
-- Functions for Event Management
-- =====================================================

-- Function to create event correlation
CREATE OR REPLACE FUNCTION create_event_correlation(
    p_primary_event_id UUID,
    p_related_event_id UUID,
    p_correlation_type VARCHAR(100),
    p_confidence_score DECIMAL(3,2) DEFAULT 1.0,
    p_correlation_data JSONB DEFAULT '{}'
) RETURNS UUID AS $$
DECLARE
    correlation_uuid UUID;
BEGIN
    -- Generate or reuse correlation ID
    SELECT correlation_id INTO correlation_uuid 
    FROM events 
    WHERE id = p_primary_event_id;
    
    IF correlation_uuid IS NULL THEN
        correlation_uuid := uuid_generate_v4();
        UPDATE events SET correlation_id = correlation_uuid WHERE id = p_primary_event_id;
    END IF;
    
    -- Update related event with same correlation ID
    UPDATE events SET correlation_id = correlation_uuid WHERE id = p_related_event_id;
    
    -- Insert correlation record
    INSERT INTO event_correlations (
        correlation_id, primary_event_id, related_event_id, 
        correlation_type, confidence_score, correlation_data
    ) VALUES (
        correlation_uuid, p_primary_event_id, p_related_event_id,
        p_correlation_type, p_confidence_score, p_correlation_data
    );
    
    RETURN correlation_uuid;
END;
$$ LANGUAGE plpgsql;

-- Function to mark event as processed
CREATE OR REPLACE FUNCTION mark_event_processed(
    p_event_id UUID,
    p_processor_name VARCHAR(100)
) RETURNS VOID AS $$
BEGIN
    UPDATE events SET 
        processed = TRUE,
        processed_at = NOW()
    WHERE id = p_event_id;
    
    UPDATE event_processing_status SET
        status = 'completed',
        completed_at = NOW()
    WHERE event_id = p_event_id AND processor_name = p_processor_name;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- Initial Data Setup
-- =====================================================

-- Create default event streams
INSERT INTO event_streams (stream_name, description, filter_criteria) VALUES
('all_events', 'Stream for all events across all platforms', '{}'),
('github_events', 'Stream for GitHub events only', '{"platform": "github"}'),
('linear_events', 'Stream for Linear events only', '{"platform": "linear"}'),
('slack_events', 'Stream for Slack events only', '{"platform": "slack"}'),
('deployment_events', 'Stream for deployment events only', '{"platform": "deployment"}'),
('pr_events', 'Stream for pull request related events', '{"event_type": "pull_request:*"}'),
('issue_events', 'Stream for issue related events', '{"event_type": "*issue*"}');

-- =====================================================
-- Comments and Documentation
-- =====================================================

COMMENT ON TABLE events IS 'Main events table storing all platform events with unified schema';
COMMENT ON TABLE event_processing_status IS 'Tracks processing status of events by different processors';
COMMENT ON TABLE event_correlations IS 'Links related events across platforms for workflow tracking';
COMMENT ON TABLE github_events IS 'GitHub-specific event details and metadata';
COMMENT ON TABLE linear_events IS 'Linear-specific event details and metadata';
COMMENT ON TABLE slack_events IS 'Slack-specific event details and metadata';
COMMENT ON TABLE deployment_events IS 'Deployment-specific event details and metadata';
COMMENT ON TABLE event_streams IS 'Defines real-time event streams with filtering criteria';
COMMENT ON TABLE stream_subscriptions IS 'Manages subscriptions to event streams';
COMMENT ON TABLE event_deliveries IS 'Tracks delivery of events to subscribers';
COMMENT ON TABLE event_metrics IS 'Aggregated metrics for event processing analytics';
COMMENT ON TABLE event_performance IS 'Performance tracking for event processing';

COMMENT ON COLUMN events.correlation_id IS 'UUID linking related events across platforms';
COMMENT ON COLUMN events.payload IS 'Full JSON payload from the original platform event';
COMMENT ON COLUMN events.metadata IS 'Additional metadata for processing and analytics';
COMMENT ON COLUMN event_correlations.confidence_score IS 'Confidence level (0.0-1.0) for the correlation';
COMMENT ON COLUMN event_streams.filter_criteria IS 'JSON criteria for filtering events in the stream';

