-- =============================================================================
-- EVENTS MODULE SCHEMA
-- =============================================================================
-- This module handles Linear issue and comment events, Slack message and
-- interaction events, GitHub PR/commit/workflow events, deployment and system
-- events, and custom event types for extensibility.
-- =============================================================================

-- =============================================================================
-- ENUMS
-- =============================================================================

CREATE TYPE event_source AS ENUM (
    'linear',
    'slack',
    'github',
    'deployment',
    'system',
    'webhook',
    'api',
    'custom'
);

CREATE TYPE event_category AS ENUM (
    'issue',
    'comment',
    'message',
    'pull_request',
    'commit',
    'workflow',
    'deployment',
    'notification',
    'user_action',
    'system_event',
    'integration',
    'custom'
);

CREATE TYPE event_priority AS ENUM (
    'low',
    'normal',
    'high',
    'critical',
    'urgent'
);

CREATE TYPE processing_status AS ENUM (
    'pending',
    'processing',
    'processed',
    'failed',
    'skipped',
    'retrying'
);

-- =============================================================================
-- EVENTS TABLES
-- =============================================================================

-- Event types - define event schemas and processing rules
CREATE TABLE event_types (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Type identification
    name VARCHAR(255) NOT NULL,
    source event_source NOT NULL,
    category event_category NOT NULL,
    
    -- Event schema
    schema_version VARCHAR(20) DEFAULT '1.0.0',
    payload_schema JSONB DEFAULT '{}', -- JSON schema for validation
    
    -- Processing configuration
    is_active BOOLEAN DEFAULT true,
    auto_process BOOLEAN DEFAULT true,
    retention_days INTEGER DEFAULT 90,
    
    -- Routing and handling
    handler_config JSONB DEFAULT '{}',
    routing_rules JSONB DEFAULT '{}',
    
    -- Metadata
    description TEXT,
    tags VARCHAR(50)[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE NULL,
    
    UNIQUE(organization_id, source, name)
);

-- Events - main event storage
CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    event_type_id UUID REFERENCES event_types(id) ON DELETE SET NULL,
    
    -- Event identification
    external_id VARCHAR(255), -- ID from external system
    short_id VARCHAR(20) UNIQUE DEFAULT generate_short_id('EVT-'),
    
    -- Event classification
    source event_source NOT NULL,
    category event_category NOT NULL,
    event_name VARCHAR(255) NOT NULL,
    
    -- Event details
    title VARCHAR(500),
    description TEXT,
    priority event_priority DEFAULT 'normal',
    
    -- Event payload
    payload JSONB NOT NULL DEFAULT '{}',
    raw_payload JSONB DEFAULT '{}', -- Original unprocessed payload
    
    -- Context and relationships
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    repository_id UUID REFERENCES repositories(id) ON DELETE SET NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    
    -- Related entities (flexible references)
    related_entities JSONB DEFAULT '{}', -- {task_id: "uuid", issue_id: "linear-123", etc.}
    
    -- Processing status
    status processing_status DEFAULT 'pending',
    processed_at TIMESTAMP WITH TIME ZONE,
    processing_attempts INTEGER DEFAULT 0,
    last_processing_error TEXT,
    
    -- Timing
    occurred_at TIMESTAMP WITH TIME ZONE NOT NULL,
    received_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Source metadata
    source_metadata JSONB DEFAULT '{}',
    
    -- Deduplication
    deduplication_key VARCHAR(255), -- For preventing duplicate events
    
    -- Metadata
    tags VARCHAR(50)[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Linear events - specific Linear integration events
CREATE TABLE linear_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Linear-specific fields
    linear_id VARCHAR(100) NOT NULL, -- Linear's internal ID
    linear_type VARCHAR(100) NOT NULL, -- Issue, Comment, Project, etc.
    action VARCHAR(100) NOT NULL, -- create, update, delete, etc.
    
    -- Linear entity data
    team_id VARCHAR(100),
    team_key VARCHAR(20),
    issue_number INTEGER,
    issue_identifier VARCHAR(50), -- e.g., "TEAM-123"
    
    -- Actor information
    actor_id VARCHAR(100),
    actor_name VARCHAR(255),
    actor_email VARCHAR(255),
    
    -- Change details
    changes JSONB DEFAULT '{}', -- What fields changed
    previous_values JSONB DEFAULT '{}',
    current_values JSONB DEFAULT '{}',
    
    -- Linear metadata
    linear_created_at TIMESTAMP WITH TIME ZONE,
    linear_updated_at TIMESTAMP WITH TIME ZONE,
    
    UNIQUE(linear_id, action, linear_updated_at)
);

-- Slack events - specific Slack integration events
CREATE TABLE slack_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Slack-specific fields
    slack_event_id VARCHAR(100),
    slack_type VARCHAR(100) NOT NULL, -- message, reaction, app_mention, etc.
    
    -- Channel and workspace
    workspace_id VARCHAR(100),
    workspace_name VARCHAR(255),
    channel_id VARCHAR(100),
    channel_name VARCHAR(255),
    channel_type VARCHAR(50), -- public, private, dm, group
    
    -- Message details
    message_ts VARCHAR(50), -- Slack timestamp
    thread_ts VARCHAR(50), -- Thread timestamp if in thread
    message_text TEXT,
    message_blocks JSONB DEFAULT '{}',
    
    -- User information
    user_id VARCHAR(100),
    user_name VARCHAR(255),
    user_email VARCHAR(255),
    bot_id VARCHAR(100),
    
    -- Interaction details
    reaction_name VARCHAR(100), -- For reaction events
    files JSONB DEFAULT '[]', -- Attached files
    
    -- Slack metadata
    slack_timestamp TIMESTAMP WITH TIME ZONE,
    
    UNIQUE(slack_event_id, slack_type)
);

-- GitHub events - specific GitHub integration events
CREATE TABLE github_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- GitHub-specific fields
    github_id VARCHAR(100),
    github_type VARCHAR(100) NOT NULL, -- push, pull_request, issues, etc.
    action VARCHAR(100), -- opened, closed, synchronize, etc.
    
    -- Repository information
    repo_id VARCHAR(100),
    repo_name VARCHAR(255),
    repo_full_name VARCHAR(500),
    
    -- Pull request details
    pr_number INTEGER,
    pr_title VARCHAR(500),
    pr_state VARCHAR(50),
    pr_merged BOOLEAN,
    
    -- Commit details
    commit_sha VARCHAR(40),
    commit_message TEXT,
    commit_author_name VARCHAR(255),
    commit_author_email VARCHAR(255),
    
    -- Issue details
    issue_number INTEGER,
    issue_title VARCHAR(500),
    issue_state VARCHAR(50),
    
    -- Workflow details
    workflow_id VARCHAR(100),
    workflow_name VARCHAR(255),
    job_id VARCHAR(100),
    job_name VARCHAR(255),
    run_id VARCHAR(100),
    run_status VARCHAR(50),
    run_conclusion VARCHAR(50),
    
    -- Actor information
    actor_login VARCHAR(255),
    actor_name VARCHAR(255),
    actor_email VARCHAR(255),
    
    -- Branch information
    ref VARCHAR(255), -- Branch or tag reference
    base_ref VARCHAR(255),
    head_ref VARCHAR(255),
    
    -- GitHub metadata
    github_created_at TIMESTAMP WITH TIME ZONE,
    github_updated_at TIMESTAMP WITH TIME ZONE
);

-- Deployment events - track deployment activities
CREATE TABLE deployment_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Deployment identification
    deployment_id VARCHAR(100),
    deployment_name VARCHAR(255),
    
    -- Environment and target
    environment VARCHAR(100) NOT NULL, -- production, staging, development, etc.
    target_platform VARCHAR(100), -- kubernetes, docker, aws, etc.
    
    -- Deployment details
    version VARCHAR(100),
    commit_sha VARCHAR(40),
    branch_name VARCHAR(255),
    
    -- Status and timing
    deployment_status VARCHAR(50), -- pending, running, success, failure, cancelled
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    
    -- Actor and automation
    deployed_by VARCHAR(255),
    deployment_tool VARCHAR(100), -- github_actions, jenkins, gitlab_ci, etc.
    automation_triggered BOOLEAN DEFAULT false,
    
    -- Configuration
    config JSONB DEFAULT '{}',
    
    -- Results
    success BOOLEAN,
    error_message TEXT,
    logs_url TEXT,
    
    -- Rollback information
    rollback_deployment_id VARCHAR(100),
    can_rollback BOOLEAN DEFAULT false
);

-- Event processing logs - track event processing
CREATE TABLE event_processing_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    
    -- Processing details
    processor_name VARCHAR(255) NOT NULL,
    processing_step VARCHAR(100),
    
    -- Status and timing
    status processing_status NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER,
    
    -- Results
    success BOOLEAN,
    error_message TEXT,
    error_details JSONB DEFAULT '{}',
    
    -- Processing metadata
    processor_version VARCHAR(50),
    processing_context JSONB DEFAULT '{}',
    
    -- Retry information
    retry_attempt INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3
);

-- Event subscriptions - manage event routing and notifications
CREATE TABLE event_subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Subscription identification
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Event filtering
    event_sources event_source[] DEFAULT '{}',
    event_categories event_category[] DEFAULT '{}',
    event_names VARCHAR(255)[] DEFAULT '{}',
    
    -- Advanced filtering
    filter_expression JSONB DEFAULT '{}', -- JSON logic expression
    
    -- Delivery configuration
    delivery_method VARCHAR(100) NOT NULL, -- webhook, email, slack, linear, etc.
    delivery_config JSONB NOT NULL DEFAULT '{}',
    
    -- Subscription settings
    is_active BOOLEAN DEFAULT true,
    batch_size INTEGER DEFAULT 1,
    batch_timeout_seconds INTEGER DEFAULT 60,
    
    -- Retry configuration
    max_retries INTEGER DEFAULT 3,
    retry_delay_seconds INTEGER DEFAULT 60,
    
    -- Ownership
    created_by UUID REFERENCES users(id),
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE NULL,
    
    UNIQUE(organization_id, name)
);

-- =============================================================================
-- INDEXES
-- =============================================================================

-- Event types indexes
CREATE INDEX idx_event_types_organization_id ON event_types(organization_id);
CREATE INDEX idx_event_types_source ON event_types(source);
CREATE INDEX idx_event_types_category ON event_types(category);
CREATE INDEX idx_event_types_name ON event_types(name);
CREATE INDEX idx_event_types_is_active ON event_types(is_active);
CREATE INDEX idx_event_types_created_at ON event_types(created_at);
CREATE INDEX idx_event_types_deleted_at ON event_types(deleted_at) WHERE deleted_at IS NULL;

-- GIN indexes for event types
CREATE INDEX idx_event_types_tags ON event_types USING GIN(tags);
CREATE INDEX idx_event_types_payload_schema ON event_types USING GIN(payload_schema);
CREATE INDEX idx_event_types_handler_config ON event_types USING GIN(handler_config);
CREATE INDEX idx_event_types_metadata ON event_types USING GIN(metadata);

-- Events indexes
CREATE INDEX idx_events_organization_id ON events(organization_id);
CREATE INDEX idx_events_event_type_id ON events(event_type_id);
CREATE INDEX idx_events_external_id ON events(external_id);
CREATE INDEX idx_events_short_id ON events(short_id);
CREATE INDEX idx_events_source ON events(source);
CREATE INDEX idx_events_category ON events(category);
CREATE INDEX idx_events_event_name ON events(event_name);
CREATE INDEX idx_events_priority ON events(priority);
CREATE INDEX idx_events_project_id ON events(project_id);
CREATE INDEX idx_events_repository_id ON events(repository_id);
CREATE INDEX idx_events_user_id ON events(user_id);
CREATE INDEX idx_events_status ON events(status);
CREATE INDEX idx_events_occurred_at ON events(occurred_at);
CREATE INDEX idx_events_received_at ON events(received_at);
CREATE INDEX idx_events_processed_at ON events(processed_at);
CREATE INDEX idx_events_deduplication_key ON events(deduplication_key);
CREATE INDEX idx_events_created_at ON events(created_at);

-- Composite indexes for common queries
CREATE INDEX idx_events_source_category ON events(source, category);
CREATE INDEX idx_events_status_priority ON events(status, priority);
CREATE INDEX idx_events_org_occurred_at ON events(organization_id, occurred_at);
CREATE INDEX idx_events_repo_occurred_at ON events(repository_id, occurred_at);

-- GIN indexes for events
CREATE INDEX idx_events_payload ON events USING GIN(payload);
CREATE INDEX idx_events_related_entities ON events USING GIN(related_entities);
CREATE INDEX idx_events_source_metadata ON events USING GIN(source_metadata);
CREATE INDEX idx_events_tags ON events USING GIN(tags);
CREATE INDEX idx_events_metadata ON events USING GIN(metadata);

-- Text search index for events
CREATE INDEX idx_events_text_search ON events USING GIN(to_tsvector('english', COALESCE(title, '') || ' ' || COALESCE(description, '')));

-- Linear events indexes
CREATE INDEX idx_linear_events_event_id ON linear_events(event_id);
CREATE INDEX idx_linear_events_organization_id ON linear_events(organization_id);
CREATE INDEX idx_linear_events_linear_id ON linear_events(linear_id);
CREATE INDEX idx_linear_events_linear_type ON linear_events(linear_type);
CREATE INDEX idx_linear_events_action ON linear_events(action);
CREATE INDEX idx_linear_events_team_id ON linear_events(team_id);
CREATE INDEX idx_linear_events_issue_identifier ON linear_events(issue_identifier);
CREATE INDEX idx_linear_events_actor_id ON linear_events(actor_id);
CREATE INDEX idx_linear_events_linear_created_at ON linear_events(linear_created_at);

-- GIN indexes for Linear events
CREATE INDEX idx_linear_events_changes ON linear_events USING GIN(changes);
CREATE INDEX idx_linear_events_current_values ON linear_events USING GIN(current_values);

-- Slack events indexes
CREATE INDEX idx_slack_events_event_id ON slack_events(event_id);
CREATE INDEX idx_slack_events_organization_id ON slack_events(organization_id);
CREATE INDEX idx_slack_events_slack_event_id ON slack_events(slack_event_id);
CREATE INDEX idx_slack_events_slack_type ON slack_events(slack_type);
CREATE INDEX idx_slack_events_workspace_id ON slack_events(workspace_id);
CREATE INDEX idx_slack_events_channel_id ON slack_events(channel_id);
CREATE INDEX idx_slack_events_user_id ON slack_events(user_id);
CREATE INDEX idx_slack_events_message_ts ON slack_events(message_ts);
CREATE INDEX idx_slack_events_thread_ts ON slack_events(thread_ts);
CREATE INDEX idx_slack_events_slack_timestamp ON slack_events(slack_timestamp);

-- Text search for Slack messages
CREATE INDEX idx_slack_events_message_search ON slack_events USING GIN(to_tsvector('english', COALESCE(message_text, '')));

-- GitHub events indexes
CREATE INDEX idx_github_events_event_id ON github_events(event_id);
CREATE INDEX idx_github_events_organization_id ON github_events(organization_id);
CREATE INDEX idx_github_events_github_id ON github_events(github_id);
CREATE INDEX idx_github_events_github_type ON github_events(github_type);
CREATE INDEX idx_github_events_action ON github_events(action);
CREATE INDEX idx_github_events_repo_id ON github_events(repo_id);
CREATE INDEX idx_github_events_repo_full_name ON github_events(repo_full_name);
CREATE INDEX idx_github_events_pr_number ON github_events(pr_number);
CREATE INDEX idx_github_events_commit_sha ON github_events(commit_sha);
CREATE INDEX idx_github_events_issue_number ON github_events(issue_number);
CREATE INDEX idx_github_events_workflow_id ON github_events(workflow_id);
CREATE INDEX idx_github_events_run_id ON github_events(run_id);
CREATE INDEX idx_github_events_actor_login ON github_events(actor_login);
CREATE INDEX idx_github_events_ref ON github_events(ref);
CREATE INDEX idx_github_events_github_created_at ON github_events(github_created_at);

-- Deployment events indexes
CREATE INDEX idx_deployment_events_event_id ON deployment_events(event_id);
CREATE INDEX idx_deployment_events_organization_id ON deployment_events(organization_id);
CREATE INDEX idx_deployment_events_deployment_id ON deployment_events(deployment_id);
CREATE INDEX idx_deployment_events_environment ON deployment_events(environment);
CREATE INDEX idx_deployment_events_deployment_status ON deployment_events(deployment_status);
CREATE INDEX idx_deployment_events_commit_sha ON deployment_events(commit_sha);
CREATE INDEX idx_deployment_events_deployed_by ON deployment_events(deployed_by);
CREATE INDEX idx_deployment_events_started_at ON deployment_events(started_at);
CREATE INDEX idx_deployment_events_completed_at ON deployment_events(completed_at);

-- Event processing logs indexes
CREATE INDEX idx_event_processing_logs_event_id ON event_processing_logs(event_id);
CREATE INDEX idx_event_processing_logs_processor_name ON event_processing_logs(processor_name);
CREATE INDEX idx_event_processing_logs_status ON event_processing_logs(status);
CREATE INDEX idx_event_processing_logs_started_at ON event_processing_logs(started_at);
CREATE INDEX idx_event_processing_logs_success ON event_processing_logs(success);

-- Event subscriptions indexes
CREATE INDEX idx_event_subscriptions_organization_id ON event_subscriptions(organization_id);
CREATE INDEX idx_event_subscriptions_name ON event_subscriptions(name);
CREATE INDEX idx_event_subscriptions_is_active ON event_subscriptions(is_active);
CREATE INDEX idx_event_subscriptions_delivery_method ON event_subscriptions(delivery_method);
CREATE INDEX idx_event_subscriptions_created_by ON event_subscriptions(created_by);
CREATE INDEX idx_event_subscriptions_created_at ON event_subscriptions(created_at);
CREATE INDEX idx_event_subscriptions_deleted_at ON event_subscriptions(deleted_at) WHERE deleted_at IS NULL;

-- GIN indexes for event subscriptions
CREATE INDEX idx_event_subscriptions_event_sources ON event_subscriptions USING GIN(event_sources);
CREATE INDEX idx_event_subscriptions_event_categories ON event_subscriptions USING GIN(event_categories);
CREATE INDEX idx_event_subscriptions_event_names ON event_subscriptions USING GIN(event_names);
CREATE INDEX idx_event_subscriptions_filter_expression ON event_subscriptions USING GIN(filter_expression);
CREATE INDEX idx_event_subscriptions_delivery_config ON event_subscriptions USING GIN(delivery_config);

-- =============================================================================
-- TRIGGERS
-- =============================================================================

CREATE TRIGGER trigger_event_types_updated_at
    BEFORE UPDATE ON event_types
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_events_updated_at
    BEFORE UPDATE ON events
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_event_subscriptions_updated_at
    BEFORE UPDATE ON event_subscriptions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- VIEWS
-- =============================================================================

-- Event summary view
CREATE VIEW event_summary AS
SELECT 
    DATE_TRUNC('day', e.occurred_at) as event_date,
    e.source,
    e.category,
    e.priority,
    COUNT(*) as event_count,
    COUNT(CASE WHEN e.status = 'processed' THEN 1 END) as processed_count,
    COUNT(CASE WHEN e.status = 'failed' THEN 1 END) as failed_count,
    COUNT(CASE WHEN e.status = 'pending' THEN 1 END) as pending_count,
    AVG(EXTRACT(EPOCH FROM (e.processed_at - e.received_at))) as avg_processing_time_seconds
FROM events e
WHERE e.occurred_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE_TRUNC('day', e.occurred_at), e.source, e.category, e.priority
ORDER BY event_date DESC;

-- Repository activity view
CREATE VIEW repository_activity AS
SELECT 
    r.id as repository_id,
    r.name as repository_name,
    r.full_name as repository_full_name,
    COUNT(e.id) as total_events,
    COUNT(CASE WHEN e.source = 'github' THEN 1 END) as github_events,
    COUNT(CASE WHEN e.source = 'linear' THEN 1 END) as linear_events,
    COUNT(CASE WHEN e.source = 'deployment' THEN 1 END) as deployment_events,
    MAX(e.occurred_at) as last_activity_at,
    COUNT(DISTINCT DATE_TRUNC('day', e.occurred_at)) as active_days_last_30
FROM repositories r
LEFT JOIN events e ON r.id = e.repository_id 
    AND e.occurred_at >= CURRENT_DATE - INTERVAL '30 days'
WHERE r.deleted_at IS NULL
GROUP BY r.id, r.name, r.full_name;

-- Processing performance view
CREATE VIEW processing_performance AS
SELECT 
    epl.processor_name,
    epl.processing_step,
    COUNT(*) as total_attempts,
    COUNT(CASE WHEN epl.success THEN 1 END) as successful_attempts,
    COUNT(CASE WHEN NOT epl.success THEN 1 END) as failed_attempts,
    AVG(epl.duration_ms) as avg_duration_ms,
    MAX(epl.duration_ms) as max_duration_ms,
    AVG(epl.retry_attempt) as avg_retry_attempts
FROM event_processing_logs epl
WHERE epl.started_at >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY epl.processor_name, epl.processing_step
ORDER BY total_attempts DESC;

-- =============================================================================
-- FUNCTIONS
-- =============================================================================

-- Function to process event queue
CREATE OR REPLACE FUNCTION process_pending_events(batch_size INTEGER DEFAULT 100)
RETURNS INTEGER AS $$
DECLARE
    processed_count INTEGER := 0;
    event_record RECORD;
BEGIN
    FOR event_record IN
        SELECT id, source, category, event_name, payload
        FROM events
        WHERE status = 'pending'
        ORDER BY priority DESC, occurred_at ASC
        LIMIT batch_size
        FOR UPDATE SKIP LOCKED
    LOOP
        -- Update status to processing
        UPDATE events
        SET status = 'processing', processing_attempts = processing_attempts + 1
        WHERE id = event_record.id;
        
        -- Here you would call specific processors based on event type
        -- For now, just mark as processed
        UPDATE events
        SET status = 'processed', processed_at = CURRENT_TIMESTAMP
        WHERE id = event_record.id;
        
        processed_count := processed_count + 1;
    END LOOP;
    
    RETURN processed_count;
END;
$$ LANGUAGE plpgsql;

-- Function to clean up old events
CREATE OR REPLACE FUNCTION cleanup_old_events()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER := 0;
    event_type_record RECORD;
BEGIN
    FOR event_type_record IN
        SELECT id, retention_days
        FROM event_types
        WHERE retention_days > 0
    LOOP
        DELETE FROM events
        WHERE event_type_id = event_type_record.id
        AND occurred_at < CURRENT_DATE - INTERVAL '1 day' * event_type_record.retention_days;
        
        GET DIAGNOSTICS deleted_count = deleted_count + ROW_COUNT;
    END LOOP;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to check event subscription matches
CREATE OR REPLACE FUNCTION check_subscription_match(
    p_event_id UUID,
    p_subscription_id UUID
)
RETURNS BOOLEAN AS $$
DECLARE
    event_record RECORD;
    subscription_record RECORD;
    matches BOOLEAN := false;
BEGIN
    -- Get event details
    SELECT source, category, event_name, payload
    INTO event_record
    FROM events
    WHERE id = p_event_id;
    
    -- Get subscription details
    SELECT event_sources, event_categories, event_names, filter_expression
    INTO subscription_record
    FROM event_subscriptions
    WHERE id = p_subscription_id AND is_active = true;
    
    IF NOT FOUND THEN
        RETURN false;
    END IF;
    
    -- Check source match
    IF array_length(subscription_record.event_sources, 1) > 0 THEN
        IF NOT (event_record.source = ANY(subscription_record.event_sources)) THEN
            RETURN false;
        END IF;
    END IF;
    
    -- Check category match
    IF array_length(subscription_record.event_categories, 1) > 0 THEN
        IF NOT (event_record.category = ANY(subscription_record.event_categories)) THEN
            RETURN false;
        END IF;
    END IF;
    
    -- Check event name match
    IF array_length(subscription_record.event_names, 1) > 0 THEN
        IF NOT (event_record.event_name = ANY(subscription_record.event_names)) THEN
            RETURN false;
        END IF;
    END IF;
    
    -- TODO: Implement JSON logic expression evaluation for filter_expression
    -- For now, if we get here, it's a match
    RETURN true;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON TABLE event_types IS 'Define event schemas and processing rules for different event sources';
COMMENT ON TABLE events IS 'Main event storage with flexible payload and relationship tracking';
COMMENT ON TABLE linear_events IS 'Linear-specific event data with issue and comment tracking';
COMMENT ON TABLE slack_events IS 'Slack-specific event data with message and interaction tracking';
COMMENT ON TABLE github_events IS 'GitHub-specific event data with PR, commit, and workflow tracking';
COMMENT ON TABLE deployment_events IS 'Deployment activity tracking with environment and status information';
COMMENT ON TABLE event_processing_logs IS 'Track event processing attempts and performance';
COMMENT ON TABLE event_subscriptions IS 'Manage event routing and notification delivery';

COMMENT ON VIEW event_summary IS 'Daily event statistics by source, category, and processing status';
COMMENT ON VIEW repository_activity IS 'Repository activity summary across all event sources';
COMMENT ON VIEW processing_performance IS 'Event processor performance metrics and success rates';

COMMENT ON FUNCTION process_pending_events(INTEGER) IS 'Process pending events in batches with locking';
COMMENT ON FUNCTION cleanup_old_events() IS 'Remove old events based on retention policies';
COMMENT ON FUNCTION check_subscription_match(UUID, UUID) IS 'Check if an event matches a subscription filter';

