-- =====================================================
-- Platform Integrations Module
-- GitHub, Linear, and Slack integration patterns
-- =====================================================

-- Integration status enumeration
CREATE TYPE integration_status AS ENUM (
    'active', 'inactive', 'error', 'pending_auth', 'expired'
);

-- Webhook processing status enumeration
CREATE TYPE webhook_processing_status AS ENUM (
    'pending', 'processing', 'processed', 'failed', 'retrying'
);

-- Main integrations table
CREATE TABLE integrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    platform VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    configuration JSONB NOT NULL,
    credentials_encrypted TEXT, -- Encrypted tokens/secrets
    webhook_secret_hash VARCHAR(255),
    status integration_status DEFAULT 'pending_auth',
    last_sync_at TIMESTAMP WITH TIME ZONE,
    last_error JSONB,
    sync_frequency_minutes INTEGER DEFAULT 60,
    rate_limit_config JSONB DEFAULT '{}',
    created_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(organization_id, platform, name),
    CONSTRAINT valid_platform CHECK (platform IN ('github', 'linear', 'slack', 'jira', 'discord')),
    CONSTRAINT valid_sync_frequency CHECK (sync_frequency_minutes > 0)
);

-- Webhook events table (partitioned by date)
CREATE TABLE webhook_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    integration_id UUID NOT NULL REFERENCES integrations(id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL,
    event_source VARCHAR(50) NOT NULL,
    event_id VARCHAR(255), -- External event ID for deduplication
    payload JSONB NOT NULL,
    headers JSONB DEFAULT '{}',
    signature_verified BOOLEAN DEFAULT false,
    processed_at TIMESTAMP WITH TIME ZONE,
    processing_status webhook_processing_status DEFAULT 'pending',
    processing_attempts INTEGER DEFAULT 0,
    max_processing_attempts INTEGER DEFAULT 3,
    error_details JSONB,
    retry_after TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_processing_attempts CHECK (processing_attempts >= 0 AND processing_attempts <= max_processing_attempts)
) PARTITION BY RANGE (created_at);

-- Create partitions for webhook events (monthly)
CREATE TABLE webhook_events_y2024m01 PARTITION OF webhook_events
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
CREATE TABLE webhook_events_y2024m02 PARTITION OF webhook_events
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
CREATE TABLE webhook_events_y2024m03 PARTITION OF webhook_events
    FOR VALUES FROM ('2024-03-01') TO ('2024-04-01');

-- External entity mappings table
CREATE TABLE external_entity_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    integration_id UUID NOT NULL REFERENCES integrations(id) ON DELETE CASCADE,
    internal_entity_type VARCHAR(100) NOT NULL,
    internal_entity_id UUID NOT NULL,
    external_platform VARCHAR(50) NOT NULL,
    external_entity_type VARCHAR(100) NOT NULL,
    external_entity_id VARCHAR(255) NOT NULL,
    external_entity_url TEXT,
    sync_metadata JSONB DEFAULT '{}',
    last_synced_at TIMESTAMP WITH TIME ZONE,
    sync_status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(organization_id, external_platform, external_entity_type, external_entity_id),
    CONSTRAINT valid_internal_entity_type CHECK (internal_entity_type IN ('task', 'user', 'repository', 'project', 'comment')),
    CONSTRAINT valid_sync_status CHECK (sync_status IN ('active', 'inactive', 'error', 'deleted'))
);

-- Integration sync logs table
CREATE TABLE integration_sync_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    integration_id UUID NOT NULL REFERENCES integrations(id) ON DELETE CASCADE,
    sync_type VARCHAR(50) NOT NULL, -- 'full', 'incremental', 'webhook'
    status VARCHAR(50) NOT NULL DEFAULT 'running',
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER,
    entities_processed INTEGER DEFAULT 0,
    entities_created INTEGER DEFAULT 0,
    entities_updated INTEGER DEFAULT 0,
    entities_deleted INTEGER DEFAULT 0,
    error_details JSONB,
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT valid_sync_type CHECK (sync_type IN ('full', 'incremental', 'webhook', 'manual')),
    CONSTRAINT valid_status CHECK (status IN ('running', 'completed', 'failed', 'cancelled')),
    CONSTRAINT valid_duration CHECK (duration_ms >= 0)
);

-- Rate limiting table
CREATE TABLE integration_rate_limits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    integration_id UUID NOT NULL REFERENCES integrations(id) ON DELETE CASCADE,
    endpoint VARCHAR(255) NOT NULL,
    requests_made INTEGER DEFAULT 0,
    requests_limit INTEGER NOT NULL,
    window_start TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    window_duration_minutes INTEGER DEFAULT 60,
    reset_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(integration_id, endpoint),
    CONSTRAINT valid_requests CHECK (requests_made >= 0 AND requests_limit > 0),
    CONSTRAINT valid_window_duration CHECK (window_duration_minutes > 0)
);

-- Integration notifications table
CREATE TABLE integration_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    integration_id UUID NOT NULL REFERENCES integrations(id) ON DELETE CASCADE,
    notification_type VARCHAR(50) NOT NULL,
    trigger_conditions JSONB NOT NULL,
    target_config JSONB NOT NULL, -- Where to send notification
    is_active BOOLEAN DEFAULT true,
    last_triggered_at TIMESTAMP WITH TIME ZONE,
    trigger_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_notification_type CHECK (notification_type IN ('sync_error', 'rate_limit', 'auth_expired', 'webhook_failed'))
);

-- OAuth tokens table for secure token storage
CREATE TABLE oauth_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    integration_id UUID NOT NULL REFERENCES integrations(id) ON DELETE CASCADE,
    token_type VARCHAR(50) NOT NULL DEFAULT 'bearer',
    access_token_encrypted TEXT NOT NULL,
    refresh_token_encrypted TEXT,
    expires_at TIMESTAMP WITH TIME ZONE,
    scope TEXT,
    token_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(integration_id),
    CONSTRAINT valid_token_type CHECK (token_type IN ('bearer', 'oauth2', 'api_key', 'jwt'))
);

-- =====================================================
-- Row-Level Security
-- =====================================================

ALTER TABLE integrations ENABLE ROW LEVEL SECURITY;
ALTER TABLE webhook_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE external_entity_mappings ENABLE ROW LEVEL SECURITY;
ALTER TABLE integration_sync_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE integration_rate_limits ENABLE ROW LEVEL SECURITY;
ALTER TABLE integration_notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE oauth_tokens ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY tenant_isolation_integrations ON integrations
    USING (organization_id = get_current_tenant());

CREATE POLICY tenant_isolation_webhook_events ON webhook_events
    USING (organization_id = get_current_tenant());

CREATE POLICY tenant_isolation_external_entity_mappings ON external_entity_mappings
    USING (organization_id = get_current_tenant());

CREATE POLICY tenant_isolation_integration_sync_logs ON integration_sync_logs
    USING (organization_id = get_current_tenant());

CREATE POLICY tenant_isolation_integration_rate_limits ON integration_rate_limits
    USING (organization_id = get_current_tenant());

CREATE POLICY tenant_isolation_integration_notifications ON integration_notifications
    USING (organization_id = get_current_tenant());

CREATE POLICY tenant_isolation_oauth_tokens ON oauth_tokens
    USING (organization_id = get_current_tenant());

-- =====================================================
-- Indexes for Performance
-- =====================================================

-- Integrations
CREATE INDEX idx_integrations_org_platform ON integrations(organization_id, platform);
CREATE INDEX idx_integrations_status ON integrations(status);
CREATE INDEX idx_integrations_last_sync ON integrations(last_sync_at);

-- Webhook Events
CREATE INDEX idx_webhook_events_integration_created ON webhook_events(integration_id, created_at);
CREATE INDEX idx_webhook_events_org_status ON webhook_events(organization_id, processing_status);
CREATE INDEX idx_webhook_events_event_type ON webhook_events(event_type);
CREATE INDEX idx_webhook_events_event_id ON webhook_events(integration_id, event_id);
CREATE INDEX idx_webhook_events_retry_after ON webhook_events(retry_after) WHERE retry_after IS NOT NULL;

-- External Entity Mappings
CREATE INDEX idx_external_mappings_internal ON external_entity_mappings(internal_entity_type, internal_entity_id);
CREATE INDEX idx_external_mappings_external ON external_entity_mappings(external_platform, external_entity_type, external_entity_id);
CREATE INDEX idx_external_mappings_integration ON external_entity_mappings(integration_id);
CREATE INDEX idx_external_mappings_sync_status ON external_entity_mappings(sync_status);

-- Integration Sync Logs
CREATE INDEX idx_sync_logs_integration_started ON integration_sync_logs(integration_id, started_at);
CREATE INDEX idx_sync_logs_status ON integration_sync_logs(status);
CREATE INDEX idx_sync_logs_sync_type ON integration_sync_logs(sync_type);

-- Rate Limits
CREATE INDEX idx_rate_limits_integration_endpoint ON integration_rate_limits(integration_id, endpoint);
CREATE INDEX idx_rate_limits_reset_at ON integration_rate_limits(reset_at);

-- OAuth Tokens
CREATE INDEX idx_oauth_tokens_integration ON oauth_tokens(integration_id);
CREATE INDEX idx_oauth_tokens_expires_at ON oauth_tokens(expires_at);

-- =====================================================
-- Functions for Integration Management
-- =====================================================

-- Function to check rate limit
CREATE OR REPLACE FUNCTION check_rate_limit(
    integration_id UUID,
    endpoint VARCHAR(255)
) RETURNS BOOLEAN AS $$
DECLARE
    current_requests INTEGER;
    requests_limit INTEGER;
    window_start TIMESTAMP WITH TIME ZONE;
    window_duration INTEGER;
    is_within_limit BOOLEAN;
BEGIN
    -- Get current rate limit info
    SELECT 
        rl.requests_made,
        rl.requests_limit,
        rl.window_start,
        rl.window_duration_minutes
    INTO current_requests, requests_limit, window_start, window_duration
    FROM integration_rate_limits rl
    WHERE rl.integration_id = check_rate_limit.integration_id
    AND rl.endpoint = check_rate_limit.endpoint;
    
    -- If no rate limit record exists, allow the request
    IF NOT FOUND THEN
        RETURN TRUE;
    END IF;
    
    -- Check if we're in a new window
    IF window_start + (window_duration || ' minutes')::INTERVAL < NOW() THEN
        -- Reset the window
        UPDATE integration_rate_limits
        SET requests_made = 0,
            window_start = NOW(),
            reset_at = NOW() + (window_duration || ' minutes')::INTERVAL,
            updated_at = NOW()
        WHERE integration_rate_limits.integration_id = check_rate_limit.integration_id
        AND integration_rate_limits.endpoint = check_rate_limit.endpoint;
        
        RETURN TRUE;
    END IF;
    
    -- Check if within limit
    is_within_limit := current_requests < requests_limit;
    
    -- Increment counter if within limit
    IF is_within_limit THEN
        UPDATE integration_rate_limits
        SET requests_made = requests_made + 1,
            updated_at = NOW()
        WHERE integration_rate_limits.integration_id = check_rate_limit.integration_id
        AND integration_rate_limits.endpoint = check_rate_limit.endpoint;
    END IF;
    
    RETURN is_within_limit;
END;
$$ LANGUAGE plpgsql;

-- Function to create external entity mapping
CREATE OR REPLACE FUNCTION create_entity_mapping(
    integration_id UUID,
    internal_type VARCHAR(100),
    internal_id UUID,
    external_platform VARCHAR(50),
    external_type VARCHAR(100),
    external_id VARCHAR(255),
    external_url TEXT DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    mapping_id UUID;
    org_id UUID;
BEGIN
    -- Get organization ID from integration
    SELECT organization_id INTO org_id
    FROM integrations
    WHERE id = integration_id;
    
    -- Insert or update mapping
    INSERT INTO external_entity_mappings (
        organization_id,
        integration_id,
        internal_entity_type,
        internal_entity_id,
        external_platform,
        external_entity_type,
        external_entity_id,
        external_entity_url,
        last_synced_at
    ) VALUES (
        org_id,
        create_entity_mapping.integration_id,
        create_entity_mapping.internal_type,
        create_entity_mapping.internal_id,
        create_entity_mapping.external_platform,
        create_entity_mapping.external_type,
        create_entity_mapping.external_id,
        create_entity_mapping.external_url,
        NOW()
    )
    ON CONFLICT (organization_id, external_platform, external_entity_type, external_entity_id)
    DO UPDATE SET
        internal_entity_id = create_entity_mapping.internal_id,
        external_entity_url = create_entity_mapping.external_url,
        last_synced_at = NOW(),
        sync_status = 'active',
        updated_at = NOW()
    RETURNING id INTO mapping_id;
    
    RETURN mapping_id;
END;
$$ LANGUAGE plpgsql;

-- Function to process webhook event
CREATE OR REPLACE FUNCTION process_webhook_event(event_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    event_record webhook_events%ROWTYPE;
    processing_result BOOLEAN := FALSE;
BEGIN
    -- Get event details
    SELECT * INTO event_record
    FROM webhook_events
    WHERE id = event_id
    AND organization_id = get_current_tenant();
    
    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;
    
    -- Update processing status
    UPDATE webhook_events
    SET processing_status = 'processing',
        processing_attempts = processing_attempts + 1
    WHERE id = event_id;
    
    BEGIN
        -- Process based on event type and source
        CASE event_record.event_source
            WHEN 'github' THEN
                processing_result := process_github_webhook(event_record);
            WHEN 'linear' THEN
                processing_result := process_linear_webhook(event_record);
            WHEN 'slack' THEN
                processing_result := process_slack_webhook(event_record);
            ELSE
                processing_result := FALSE;
        END CASE;
        
        -- Update status based on result
        IF processing_result THEN
            UPDATE webhook_events
            SET processing_status = 'processed',
                processed_at = NOW(),
                error_details = NULL
            WHERE id = event_id;
        ELSE
            UPDATE webhook_events
            SET processing_status = 'failed',
                error_details = jsonb_build_object('error', 'Processing failed')
            WHERE id = event_id;
        END IF;
        
    EXCEPTION WHEN OTHERS THEN
        -- Handle processing errors
        UPDATE webhook_events
        SET processing_status = CASE 
            WHEN processing_attempts >= max_processing_attempts THEN 'failed'
            ELSE 'retrying'
        END,
        error_details = jsonb_build_object(
            'error', SQLERRM,
            'sqlstate', SQLSTATE
        ),
        retry_after = CASE 
            WHEN processing_attempts < max_processing_attempts THEN 
                NOW() + (processing_attempts * INTERVAL '5 minutes')
            ELSE NULL
        END
        WHERE id = event_id;
        
        processing_result := FALSE;
    END;
    
    RETURN processing_result;
END;
$$ LANGUAGE plpgsql;

-- Placeholder functions for webhook processing (to be implemented)
CREATE OR REPLACE FUNCTION process_github_webhook(event webhook_events)
RETURNS BOOLEAN AS $$
BEGIN
    -- Implementation for GitHub webhook processing
    -- This would integrate with the contexten orchestrator
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION process_linear_webhook(event webhook_events)
RETURNS BOOLEAN AS $$
BEGIN
    -- Implementation for Linear webhook processing
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION process_slack_webhook(event webhook_events)
RETURNS BOOLEAN AS $$
BEGIN
    -- Implementation for Slack webhook processing
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Function to get integration statistics
CREATE OR REPLACE FUNCTION get_integration_stats(integration_id UUID)
RETURNS JSONB AS $$
DECLARE
    stats JSONB;
BEGIN
    SELECT jsonb_build_object(
        'total_webhooks_24h', COUNT(DISTINCT we.id) FILTER (WHERE we.created_at > NOW() - INTERVAL '24 hours'),
        'processed_webhooks_24h', COUNT(DISTINCT we.id) FILTER (WHERE we.processing_status = 'processed' AND we.created_at > NOW() - INTERVAL '24 hours'),
        'failed_webhooks_24h', COUNT(DISTINCT we.id) FILTER (WHERE we.processing_status = 'failed' AND we.created_at > NOW() - INTERVAL '24 hours'),
        'total_entity_mappings', COUNT(DISTINCT eem.id),
        'active_entity_mappings', COUNT(DISTINCT eem.id) FILTER (WHERE eem.sync_status = 'active'),
        'last_sync_at', MAX(isl.completed_at),
        'sync_success_rate', (
            COUNT(DISTINCT isl.id) FILTER (WHERE isl.status = 'completed' AND isl.started_at > NOW() - INTERVAL '7 days')::DECIMAL /
            NULLIF(COUNT(DISTINCT isl.id) FILTER (WHERE isl.started_at > NOW() - INTERVAL '7 days'), 0) * 100
        )
    ) INTO stats
    FROM integrations i
    LEFT JOIN webhook_events we ON i.id = we.integration_id
    LEFT JOIN external_entity_mappings eem ON i.id = eem.integration_id
    LEFT JOIN integration_sync_logs isl ON i.id = isl.integration_id
    WHERE i.id = get_integration_stats.integration_id
    AND i.organization_id = get_current_tenant();
    
    RETURN stats;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- Triggers
-- =====================================================

-- Update timestamp triggers
CREATE TRIGGER update_integrations_updated_at 
    BEFORE UPDATE ON integrations 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_external_entity_mappings_updated_at 
    BEFORE UPDATE ON external_entity_mappings 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_integration_rate_limits_updated_at 
    BEFORE UPDATE ON integration_rate_limits 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_integration_notifications_updated_at 
    BEFORE UPDATE ON integration_notifications 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_oauth_tokens_updated_at 
    BEFORE UPDATE ON oauth_tokens 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger to auto-process webhook events
CREATE OR REPLACE FUNCTION auto_process_webhook()
RETURNS TRIGGER AS $$
BEGIN
    -- Schedule processing for high-priority events
    IF NEW.event_type IN ('push', 'pull_request', 'issue_comment') THEN
        -- This would typically queue a background job
        -- For now, we'll just mark it for immediate processing
        NEW.processing_status := 'pending';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER auto_process_webhook_trigger
    BEFORE INSERT ON webhook_events
    FOR EACH ROW EXECUTE FUNCTION auto_process_webhook();

-- Audit triggers
CREATE TRIGGER audit_integrations 
    AFTER INSERT OR UPDATE OR DELETE ON integrations
    FOR EACH ROW EXECUTE FUNCTION create_audit_log();

-- =====================================================
-- Views for Common Queries
-- =====================================================

-- Integration summary view
CREATE VIEW integration_summary AS
SELECT 
    i.id,
    i.organization_id,
    i.platform,
    i.name,
    i.status,
    i.last_sync_at,
    COUNT(DISTINCT we.id) as total_webhooks,
    COUNT(DISTINCT we.id) FILTER (WHERE we.processing_status = 'processed') as processed_webhooks,
    COUNT(DISTINCT we.id) FILTER (WHERE we.processing_status = 'failed') as failed_webhooks,
    COUNT(DISTINCT eem.id) as entity_mappings,
    i.created_at,
    i.updated_at
FROM integrations i
LEFT JOIN webhook_events we ON i.id = we.integration_id AND we.created_at > NOW() - INTERVAL '24 hours'
LEFT JOIN external_entity_mappings eem ON i.id = eem.integration_id AND eem.sync_status = 'active'
GROUP BY i.id;

-- Recent webhook events view
CREATE VIEW recent_webhook_events AS
SELECT 
    we.id,
    we.organization_id,
    i.platform,
    i.name as integration_name,
    we.event_type,
    we.processing_status,
    we.processing_attempts,
    we.created_at,
    we.processed_at
FROM webhook_events we
JOIN integrations i ON we.integration_id = i.id
WHERE we.created_at > NOW() - INTERVAL '24 hours'
ORDER BY we.created_at DESC;

