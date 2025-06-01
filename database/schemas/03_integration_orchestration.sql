-- =============================================================================
-- INTEGRATION AND ORCHESTRATION MODULE
-- =============================================================================
-- GitHub, Linear, Slack integrations and event orchestration for autonomous
-- development workflows with contexten integration
-- =============================================================================

-- =============================================================================
-- INTEGRATION-SPECIFIC ENUMS
-- =============================================================================

-- Integration types for external services
CREATE TYPE integration_type AS ENUM (
    'github',
    'linear',
    'slack',
    'codegen',
    'webhook',
    'api'
);

-- Event types for integration events
CREATE TYPE event_type AS ENUM (
    'push',
    'pull_request',
    'issue',
    'comment',
    'review',
    'deployment',
    'workflow',
    'notification',
    'sync',
    'webhook'
);

-- Sync status for integration synchronization
CREATE TYPE sync_status AS ENUM (
    'active',
    'inactive',
    'error',
    'syncing',
    'paused'
);

-- =============================================================================
-- INTEGRATION CONFIGURATION TABLES
-- =============================================================================

-- Integrations - centralized integration management
CREATE TABLE integrations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    codebase_id UUID REFERENCES codebases(id) ON DELETE CASCADE,
    
    -- Integration identification
    name VARCHAR(255) NOT NULL,
    integration_type integration_type NOT NULL,
    description TEXT,
    
    -- Configuration and credentials
    configuration JSONB NOT NULL DEFAULT '{}',
    credentials JSONB DEFAULT '{}', -- Encrypted/hashed credentials
    
    -- Connection details
    endpoint_url TEXT,
    api_version VARCHAR(50),
    
    -- Status and health
    status sync_status DEFAULT 'active',
    last_sync_at TIMESTAMP WITH TIME ZONE,
    last_error TEXT,
    error_count INTEGER DEFAULT 0,
    
    -- Settings and preferences
    sync_settings JSONB DEFAULT '{}',
    notification_settings JSONB DEFAULT '{}',
    
    -- Rate limiting and throttling
    rate_limit_per_hour INTEGER DEFAULT 1000,
    current_usage INTEGER DEFAULT 0,
    usage_reset_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP + INTERVAL '1 hour',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT integrations_name_not_empty CHECK (length(trim(name)) > 0),
    CONSTRAINT integrations_unique_per_codebase UNIQUE (codebase_id, integration_type, name)
);

-- GitHub integrations - specific GitHub configuration
CREATE TABLE github_integrations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    integration_id UUID NOT NULL REFERENCES integrations(id) ON DELETE CASCADE,
    codebase_id UUID NOT NULL REFERENCES codebases(id) ON DELETE CASCADE,
    
    -- Repository details
    repository_owner VARCHAR(100) NOT NULL,
    repository_name VARCHAR(100) NOT NULL,
    repository_id BIGINT,
    
    -- GitHub App configuration
    installation_id BIGINT,
    app_id BIGINT,
    
    -- Webhook configuration
    webhook_id BIGINT,
    webhook_secret VARCHAR(255),
    webhook_url TEXT,
    
    -- Access tokens (hashed)
    access_token_hash TEXT,
    refresh_token_hash TEXT,
    token_expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Permissions and scopes
    permissions JSONB DEFAULT '{}',
    scopes TEXT[] DEFAULT '{}',
    
    -- Sync configuration
    sync_pull_requests BOOLEAN DEFAULT true,
    sync_issues BOOLEAN DEFAULT true,
    sync_commits BOOLEAN DEFAULT true,
    sync_releases BOOLEAN DEFAULT true,
    sync_workflows BOOLEAN DEFAULT true,
    
    -- Branch configuration
    default_branch VARCHAR(100) DEFAULT 'main',
    protected_branches TEXT[] DEFAULT '{}',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT github_integrations_repo_unique UNIQUE (repository_owner, repository_name)
);

-- Linear integrations - specific Linear configuration
CREATE TABLE linear_integrations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    integration_id UUID NOT NULL REFERENCES integrations(id) ON DELETE CASCADE,
    codebase_id UUID NOT NULL REFERENCES codebases(id) ON DELETE CASCADE,
    
    -- Linear workspace details
    workspace_id VARCHAR(100) NOT NULL,
    workspace_name VARCHAR(255),
    
    -- Team configuration
    team_id VARCHAR(100) NOT NULL,
    team_name VARCHAR(255),
    
    -- API configuration
    api_key_hash TEXT NOT NULL,
    
    -- Webhook configuration
    webhook_id VARCHAR(100),
    webhook_secret VARCHAR(255),
    webhook_url TEXT,
    
    -- Sync configuration
    sync_issues BOOLEAN DEFAULT true,
    sync_projects BOOLEAN DEFAULT true,
    sync_comments BOOLEAN DEFAULT true,
    sync_labels BOOLEAN DEFAULT true,
    sync_milestones BOOLEAN DEFAULT true,
    
    -- Project mapping
    project_mappings JSONB DEFAULT '{}', -- Map Linear projects to local tasks
    
    -- Status mapping
    status_mappings JSONB DEFAULT '{}', -- Map Linear statuses to local statuses
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT linear_integrations_team_unique UNIQUE (workspace_id, team_id)
);

-- Slack integrations - specific Slack configuration
CREATE TABLE slack_integrations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    integration_id UUID NOT NULL REFERENCES integrations(id) ON DELETE CASCADE,
    codebase_id UUID NOT NULL REFERENCES codebases(id) ON DELETE CASCADE,
    
    -- Slack workspace details
    workspace_id VARCHAR(100) NOT NULL,
    workspace_name VARCHAR(255),
    
    -- Channel configuration
    channel_id VARCHAR(100),
    channel_name VARCHAR(255),
    
    -- Bot configuration
    bot_user_id VARCHAR(100),
    bot_token_hash TEXT,
    
    -- App configuration
    app_id VARCHAR(100),
    client_id VARCHAR(100),
    client_secret_hash TEXT,
    
    -- Webhook configuration
    webhook_url_hash TEXT,
    signing_secret_hash TEXT,
    
    -- Notification settings
    notify_on_tasks BOOLEAN DEFAULT true,
    notify_on_errors BOOLEAN DEFAULT true,
    notify_on_completions BOOLEAN DEFAULT true,
    notify_on_deployments BOOLEAN DEFAULT false,
    
    -- Message formatting
    message_format VARCHAR(50) DEFAULT 'rich', -- 'simple', 'rich', 'minimal'
    include_links BOOLEAN DEFAULT true,
    include_previews BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT slack_integrations_workspace_unique UNIQUE (workspace_id, channel_id)
);

-- =============================================================================
-- EVENT PROCESSING AND ORCHESTRATION
-- =============================================================================

-- Integration events - centralized event processing
CREATE TABLE integration_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    integration_id UUID NOT NULL REFERENCES integrations(id) ON DELETE CASCADE,
    
    -- Event identification
    event_type event_type NOT NULL,
    event_source VARCHAR(100) NOT NULL, -- 'github', 'linear', 'slack', 'webhook', 'system'
    external_event_id VARCHAR(255),
    
    -- Event data
    event_data JSONB NOT NULL,
    raw_payload JSONB DEFAULT '{}',
    headers JSONB DEFAULT '{}',
    
    -- Processing status
    processed BOOLEAN DEFAULT false,
    processing_started_at TIMESTAMP WITH TIME ZONE,
    processed_at TIMESTAMP WITH TIME ZONE,
    processing_duration_ms INTEGER,
    
    -- Results and actions
    actions_triggered JSONB DEFAULT '[]',
    tasks_created JSONB DEFAULT '[]',
    notifications_sent JSONB DEFAULT '[]',
    
    -- Error handling
    error_message TEXT,
    error_details JSONB DEFAULT '{}',
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    
    -- Priority and scheduling
    priority priority_level DEFAULT 'normal',
    scheduled_for TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT integration_events_external_id_unique UNIQUE (integration_id, external_event_id)
);

-- Event handlers - define how events should be processed
CREATE TABLE event_handlers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    integration_id UUID REFERENCES integrations(id) ON DELETE CASCADE,
    
    -- Handler identification
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Event matching criteria
    event_type event_type NOT NULL,
    event_source VARCHAR(100) NOT NULL,
    filter_conditions JSONB DEFAULT '{}', -- JSON conditions for event filtering
    
    -- Handler configuration
    handler_type VARCHAR(100) NOT NULL, -- 'task_creation', 'notification', 'webhook', 'codegen_trigger'
    handler_config JSONB NOT NULL DEFAULT '{}',
    
    -- Execution settings
    is_active BOOLEAN DEFAULT true,
    execution_order INTEGER DEFAULT 100,
    timeout_seconds INTEGER DEFAULT 300,
    
    -- Rate limiting
    rate_limit_per_minute INTEGER DEFAULT 60,
    
    -- Success and error handling
    on_success_actions JSONB DEFAULT '[]',
    on_error_actions JSONB DEFAULT '[]',
    
    -- Statistics
    execution_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    last_executed_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT event_handlers_name_not_empty CHECK (length(trim(name)) > 0)
);

-- Event handler executions - track handler execution results
CREATE TABLE event_handler_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id UUID NOT NULL REFERENCES integration_events(id) ON DELETE CASCADE,
    handler_id UUID NOT NULL REFERENCES event_handlers(id) ON DELETE CASCADE,
    
    -- Execution details
    status status_type NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER,
    
    -- Results
    result JSONB DEFAULT '{}',
    actions_performed JSONB DEFAULT '[]',
    
    -- Error handling
    error_message TEXT,
    error_details JSONB DEFAULT '{}',
    
    -- Context
    execution_context JSONB DEFAULT '{}',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- WORKFLOW ORCHESTRATION
-- =============================================================================

-- Workflows - define autonomous development workflows
CREATE TABLE workflows (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    codebase_id UUID REFERENCES codebases(id) ON DELETE CASCADE,
    
    -- Workflow identification
    name VARCHAR(255) NOT NULL,
    description TEXT,
    workflow_type VARCHAR(100) NOT NULL, -- 'ci_cd', 'code_review', 'deployment', 'analysis', 'maintenance'
    
    -- Trigger configuration
    trigger_events JSONB DEFAULT '[]', -- Events that trigger this workflow
    trigger_conditions JSONB DEFAULT '{}', -- Conditions for triggering
    
    -- Workflow definition
    steps JSONB NOT NULL DEFAULT '[]', -- Ordered list of workflow steps
    parallel_execution BOOLEAN DEFAULT false,
    
    -- Configuration
    configuration JSONB DEFAULT '{}',
    environment_variables JSONB DEFAULT '{}',
    
    -- Status and lifecycle
    is_active BOOLEAN DEFAULT true,
    version INTEGER DEFAULT 1,
    
    -- Execution settings
    timeout_minutes INTEGER DEFAULT 60,
    max_concurrent_executions INTEGER DEFAULT 1,
    retry_on_failure BOOLEAN DEFAULT true,
    max_retries INTEGER DEFAULT 3,
    
    -- Statistics
    execution_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    last_executed_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT workflows_name_not_empty CHECK (length(trim(name)) > 0)
);

-- Workflow executions - track workflow execution instances
CREATE TABLE workflow_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    triggered_by_event_id UUID REFERENCES integration_events(id) ON DELETE SET NULL,
    
    -- Execution metadata
    execution_number INTEGER NOT NULL,
    status status_type DEFAULT 'pending',
    
    -- Trigger information
    trigger_source VARCHAR(100),
    trigger_data JSONB DEFAULT '{}',
    
    -- Execution details
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER,
    
    -- Results and artifacts
    result JSONB DEFAULT '{}',
    artifacts JSONB DEFAULT '{}',
    logs TEXT,
    
    -- Error handling
    error_message TEXT,
    error_details JSONB DEFAULT '{}',
    failed_step_index INTEGER,
    
    -- Context
    execution_context JSONB DEFAULT '{}',
    environment_snapshot JSONB DEFAULT '{}',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Workflow step executions - track individual step executions
CREATE TABLE workflow_step_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_execution_id UUID NOT NULL REFERENCES workflow_executions(id) ON DELETE CASCADE,
    
    -- Step identification
    step_index INTEGER NOT NULL,
    step_name VARCHAR(255) NOT NULL,
    step_type VARCHAR(100) NOT NULL, -- 'task', 'codegen', 'webhook', 'condition', 'parallel'
    
    -- Execution details
    status status_type DEFAULT 'pending',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER,
    
    -- Step configuration and context
    step_config JSONB DEFAULT '{}',
    input_data JSONB DEFAULT '{}',
    output_data JSONB DEFAULT '{}',
    
    -- Results
    result JSONB DEFAULT '{}',
    logs TEXT,
    
    -- Error handling
    error_message TEXT,
    error_details JSONB DEFAULT '{}',
    retry_count INTEGER DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- NOTIFICATION AND COMMUNICATION
-- =============================================================================

-- Notifications - centralized notification management
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Notification identification
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    notification_type VARCHAR(100) NOT NULL, -- 'info', 'success', 'warning', 'error', 'task_update'
    
    -- Source information
    source_type VARCHAR(100), -- 'task', 'workflow', 'integration', 'system'
    source_id UUID,
    
    -- Target configuration
    target_integrations JSONB DEFAULT '[]', -- Which integrations to send to
    target_channels JSONB DEFAULT '[]', -- Specific channels/recipients
    
    -- Content and formatting
    content JSONB DEFAULT '{}', -- Rich content for different platforms
    attachments JSONB DEFAULT '[]',
    
    -- Delivery tracking
    delivery_status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'sent', 'delivered', 'failed'
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    
    -- Priority and scheduling
    priority priority_level DEFAULT 'normal',
    scheduled_for TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Error handling
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT notifications_title_not_empty CHECK (length(trim(title)) > 0),
    CONSTRAINT notifications_message_not_empty CHECK (length(trim(message)) > 0)
);

-- Notification deliveries - track delivery to specific integrations
CREATE TABLE notification_deliveries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    notification_id UUID NOT NULL REFERENCES notifications(id) ON DELETE CASCADE,
    integration_id UUID NOT NULL REFERENCES integrations(id) ON DELETE CASCADE,
    
    -- Delivery details
    delivery_method VARCHAR(100) NOT NULL, -- 'slack_message', 'github_comment', 'linear_comment', 'webhook'
    target_identifier VARCHAR(255), -- Channel ID, issue number, etc.
    
    -- Status tracking
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'sent', 'delivered', 'failed'
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    
    -- Platform-specific details
    external_message_id VARCHAR(255),
    platform_response JSONB DEFAULT '{}',
    
    -- Error handling
    error_message TEXT,
    error_details JSONB DEFAULT '{}',
    retry_count INTEGER DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- INTEGRATION FUNCTIONS
-- =============================================================================

-- Process integration event and trigger appropriate handlers
CREATE OR REPLACE FUNCTION process_integration_event(event_id UUID)
RETURNS JSONB AS $$
DECLARE
    event_record RECORD;
    handler_record RECORD;
    execution_id UUID;
    result JSONB := '{}';
    handlers_executed INTEGER := 0;
    handlers_succeeded INTEGER := 0;
BEGIN
    -- Get the event details
    SELECT * INTO event_record FROM integration_events WHERE id = event_id;
    
    IF NOT FOUND THEN
        RETURN jsonb_build_object('error', 'Event not found');
    END IF;
    
    -- Mark event as being processed
    UPDATE integration_events 
    SET processing_started_at = CURRENT_TIMESTAMP 
    WHERE id = event_id;
    
    -- Find matching event handlers
    FOR handler_record IN 
        SELECT * FROM event_handlers 
        WHERE integration_id = event_record.integration_id
        AND event_type = event_record.event_type
        AND event_source = event_record.event_source
        AND is_active = true
        ORDER BY execution_order ASC
    LOOP
        handlers_executed := handlers_executed + 1;
        
        -- Create execution record
        INSERT INTO event_handler_executions (
            event_id, handler_id, status, execution_context
        ) VALUES (
            event_id, handler_record.id, 'active', 
            jsonb_build_object('handler_name', handler_record.name)
        ) RETURNING id INTO execution_id;
        
        -- Update handler statistics
        UPDATE event_handlers 
        SET execution_count = execution_count + 1,
            last_executed_at = CURRENT_TIMESTAMP
        WHERE id = handler_record.id;
        
        -- Mark execution as completed (simplified - actual processing would be async)
        UPDATE event_handler_executions 
        SET status = 'completed',
            completed_at = CURRENT_TIMESTAMP,
            duration_ms = 100,
            result = jsonb_build_object('status', 'success')
        WHERE id = execution_id;
        
        -- Update success count
        UPDATE event_handlers 
        SET success_count = success_count + 1
        WHERE id = handler_record.id;
        
        handlers_succeeded := handlers_succeeded + 1;
    END LOOP;
    
    -- Mark event as processed
    UPDATE integration_events 
    SET processed = true,
        processed_at = CURRENT_TIMESTAMP,
        processing_duration_ms = EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - processing_started_at)) * 1000,
        actions_triggered = jsonb_build_array(
            jsonb_build_object(
                'handlers_executed', handlers_executed,
                'handlers_succeeded', handlers_succeeded
            )
        )
    WHERE id = event_id;
    
    result := jsonb_build_object(
        'event_id', event_id,
        'handlers_executed', handlers_executed,
        'handlers_succeeded', handlers_succeeded,
        'status', 'completed'
    );
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Get integration health status
CREATE OR REPLACE FUNCTION get_integration_health()
RETURNS JSONB AS $$
DECLARE
    result JSONB;
    integration_stats JSONB;
    event_stats JSONB;
    workflow_stats JSONB;
    notification_stats JSONB;
BEGIN
    -- Integration statistics
    SELECT jsonb_build_object(
        'total_integrations', COUNT(*),
        'active_integrations', COUNT(*) FILTER (WHERE status = 'active'),
        'error_integrations', COUNT(*) FILTER (WHERE status = 'error'),
        'github_integrations', COUNT(*) FILTER (WHERE integration_type = 'github'),
        'linear_integrations', COUNT(*) FILTER (WHERE integration_type = 'linear'),
        'slack_integrations', COUNT(*) FILTER (WHERE integration_type = 'slack')
    ) INTO integration_stats
    FROM integrations;
    
    -- Event processing statistics
    SELECT jsonb_build_object(
        'total_events', COUNT(*),
        'processed_events', COUNT(*) FILTER (WHERE processed = true),
        'pending_events', COUNT(*) FILTER (WHERE processed = false),
        'events_last_24h', COUNT(*) FILTER (WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours'),
        'avg_processing_time_ms', ROUND(AVG(processing_duration_ms), 2) FILTER (WHERE processed = true)
    ) INTO event_stats
    FROM integration_events;
    
    -- Workflow statistics
    SELECT jsonb_build_object(
        'total_workflows', COUNT(*),
        'active_workflows', COUNT(*) FILTER (WHERE is_active = true),
        'executions_last_24h', (
            SELECT COUNT(*) FROM workflow_executions 
            WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
        ),
        'avg_success_rate', ROUND(AVG(
            CASE WHEN execution_count > 0 
            THEN (success_count::DECIMAL / execution_count::DECIMAL) * 100 
            ELSE 0 END
        ), 2)
    ) INTO workflow_stats
    FROM workflows;
    
    -- Notification statistics
    SELECT jsonb_build_object(
        'total_notifications', COUNT(*),
        'delivered_notifications', COUNT(*) FILTER (WHERE delivery_status = 'delivered'),
        'failed_notifications', COUNT(*) FILTER (WHERE delivery_status = 'failed'),
        'notifications_last_24h', COUNT(*) FILTER (WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours')
    ) INTO notification_stats
    FROM notifications;
    
    result := jsonb_build_object(
        'status', 'operational',
        'timestamp', CURRENT_TIMESTAMP,
        'integrations', integration_stats,
        'events', event_stats,
        'workflows', workflow_stats,
        'notifications', notification_stats
    );
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- TRIGGERS
-- =============================================================================

-- Update timestamps
CREATE TRIGGER update_integrations_updated_at 
    BEFORE UPDATE ON integrations 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_github_integrations_updated_at 
    BEFORE UPDATE ON github_integrations 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_linear_integrations_updated_at 
    BEFORE UPDATE ON linear_integrations 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_slack_integrations_updated_at 
    BEFORE UPDATE ON slack_integrations 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_event_handlers_updated_at 
    BEFORE UPDATE ON event_handlers 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_workflows_updated_at 
    BEFORE UPDATE ON workflows 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- INDEXES FOR INTEGRATION PERFORMANCE
-- =============================================================================

-- Integration indexes
CREATE INDEX idx_integrations_codebase ON integrations(codebase_id);
CREATE INDEX idx_integrations_type ON integrations(integration_type);
CREATE INDEX idx_integrations_status ON integrations(status);
CREATE INDEX idx_integrations_last_sync ON integrations(last_sync_at);

-- GitHub integration indexes
CREATE INDEX idx_github_integrations_integration ON github_integrations(integration_id);
CREATE INDEX idx_github_integrations_codebase ON github_integrations(codebase_id);
CREATE INDEX idx_github_integrations_repo ON github_integrations(repository_owner, repository_name);

-- Linear integration indexes
CREATE INDEX idx_linear_integrations_integration ON linear_integrations(integration_id);
CREATE INDEX idx_linear_integrations_codebase ON linear_integrations(codebase_id);
CREATE INDEX idx_linear_integrations_team ON linear_integrations(workspace_id, team_id);

-- Slack integration indexes
CREATE INDEX idx_slack_integrations_integration ON slack_integrations(integration_id);
CREATE INDEX idx_slack_integrations_codebase ON slack_integrations(codebase_id);
CREATE INDEX idx_slack_integrations_workspace ON slack_integrations(workspace_id, channel_id);

-- Event indexes
CREATE INDEX idx_integration_events_integration ON integration_events(integration_id);
CREATE INDEX idx_integration_events_type ON integration_events(event_type);
CREATE INDEX idx_integration_events_source ON integration_events(event_source);
CREATE INDEX idx_integration_events_processed ON integration_events(processed);
CREATE INDEX idx_integration_events_created_at ON integration_events(created_at);
CREATE INDEX idx_integration_events_priority ON integration_events(priority);

-- Event handler indexes
CREATE INDEX idx_event_handlers_integration ON event_handlers(integration_id);
CREATE INDEX idx_event_handlers_type_source ON event_handlers(event_type, event_source);
CREATE INDEX idx_event_handlers_active ON event_handlers(is_active);
CREATE INDEX idx_event_handlers_order ON event_handlers(execution_order);

-- Workflow indexes
CREATE INDEX idx_workflows_codebase ON workflows(codebase_id);
CREATE INDEX idx_workflows_type ON workflows(workflow_type);
CREATE INDEX idx_workflows_active ON workflows(is_active);
CREATE INDEX idx_workflow_executions_workflow ON workflow_executions(workflow_id);
CREATE INDEX idx_workflow_executions_status ON workflow_executions(status);
CREATE INDEX idx_workflow_executions_created_at ON workflow_executions(created_at);

-- Notification indexes
CREATE INDEX idx_notifications_type ON notifications(notification_type);
CREATE INDEX idx_notifications_source ON notifications(source_type, source_id);
CREATE INDEX idx_notifications_status ON notifications(delivery_status);
CREATE INDEX idx_notifications_priority ON notifications(priority);
CREATE INDEX idx_notifications_scheduled ON notifications(scheduled_for);
CREATE INDEX idx_notification_deliveries_notification ON notification_deliveries(notification_id);
CREATE INDEX idx_notification_deliveries_integration ON notification_deliveries(integration_id);

-- JSONB indexes for complex queries
CREATE INDEX idx_integrations_configuration_gin USING gin (configuration);
CREATE INDEX idx_integration_events_data_gin USING gin (event_data);
CREATE INDEX idx_event_handlers_config_gin USING gin (handler_config);
CREATE INDEX idx_workflows_steps_gin USING gin (steps);
CREATE INDEX idx_notifications_content_gin USING gin (content);

-- =============================================================================
-- COMMENTS FOR DOCUMENTATION
-- =============================================================================

COMMENT ON TABLE integrations IS 'Centralized integration management for external services';
COMMENT ON TABLE github_integrations IS 'GitHub-specific integration configuration and state';
COMMENT ON TABLE linear_integrations IS 'Linear-specific integration configuration and state';
COMMENT ON TABLE slack_integrations IS 'Slack-specific integration configuration and state';
COMMENT ON TABLE integration_events IS 'Centralized event processing and orchestration';
COMMENT ON TABLE event_handlers IS 'Configurable event processing handlers';
COMMENT ON TABLE workflows IS 'Autonomous development workflow definitions';
COMMENT ON TABLE workflow_executions IS 'Workflow execution tracking and results';
COMMENT ON TABLE notifications IS 'Centralized notification management and delivery';

COMMENT ON FUNCTION process_integration_event IS 'Process integration event and trigger appropriate handlers';
COMMENT ON FUNCTION get_integration_health IS 'Get comprehensive integration system health overview';

