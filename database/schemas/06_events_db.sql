-- =============================================================================
-- EVENTS DATABASE SCHEMA: Multi-Source Event Tracking and Aggregation
-- =============================================================================
-- This database handles multi-source event ingestion from GitHub, Linear,
-- Notion, Slack, and other sources with event aggregations and subscriptions.
-- =============================================================================

-- Connect to events_db
\c events_db;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "btree_gist";
CREATE EXTENSION IF NOT EXISTS "timescaledb" CASCADE; -- For time-series data

-- Set timezone and configuration
SET timezone = 'UTC';
SET default_text_search_config = 'pg_catalog.english';

-- Grant all privileges to events_user
GRANT ALL PRIVILEGES ON DATABASE events_db TO events_user;
GRANT ALL PRIVILEGES ON SCHEMA public TO events_user;

-- Event-specific enums
CREATE TYPE event_source AS ENUM (
    'github',
    'linear',
    'notion',
    'slack',
    'jira',
    'confluence',
    'discord',
    'teams',
    'webhook',
    'api',
    'system',
    'custom'
);

CREATE TYPE event_type AS ENUM (
    'push',
    'pull_request',
    'issue',
    'commit',
    'release',
    'deployment',
    'message',
    'comment',
    'mention',
    'reaction',
    'page_update',
    'task_update',
    'status_change',
    'user_action',
    'system_event',
    'custom'
);

CREATE TYPE event_status AS ENUM (
    'received',
    'processing',
    'processed',
    'failed',
    'ignored',
    'archived'
);

CREATE TYPE subscription_status AS ENUM (
    'active',
    'paused',
    'disabled',
    'error'
);

CREATE TYPE aggregation_period AS ENUM (
    'minute',
    'hour',
    'day',
    'week',
    'month'
);

-- =============================================================================
-- CORE REFERENCE TABLES
-- =============================================================================

-- Organizations table for multi-tenancy
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Users table for event attribution
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    external_ids JSONB DEFAULT '{}', -- Map of external user IDs
    role VARCHAR(50) DEFAULT 'member',
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- EVENT SOURCES AND CONFIGURATION
-- =============================================================================

-- Event sources configuration
CREATE TABLE event_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Source identification
    name VARCHAR(255) NOT NULL,
    source_type event_source NOT NULL,
    description TEXT,
    
    -- Source configuration
    configuration JSONB DEFAULT '{}',
    authentication JSONB DEFAULT '{}', -- Encrypted credentials
    
    -- Source status
    is_active BOOLEAN DEFAULT true,
    last_sync_at TIMESTAMP WITH TIME ZONE,
    next_sync_at TIMESTAMP WITH TIME ZONE,
    
    -- Sync configuration
    sync_interval_minutes INTEGER DEFAULT 60,
    batch_size INTEGER DEFAULT 100,
    
    -- Rate limiting
    rate_limit_per_hour INTEGER DEFAULT 1000,
    current_hour_count INTEGER DEFAULT 0,
    rate_limit_reset_at TIMESTAMP WITH TIME ZONE,
    
    -- Health monitoring
    health_status VARCHAR(50) DEFAULT 'healthy', -- healthy, degraded, unhealthy
    last_error_at TIMESTAMP WITH TIME ZONE,
    error_count INTEGER DEFAULT 0,
    
    -- Statistics
    total_events_received INTEGER DEFAULT 0,
    total_events_processed INTEGER DEFAULT 0,
    total_events_failed INTEGER DEFAULT 0,
    
    -- External references
    external_source_id VARCHAR(255),
    webhook_url TEXT,
    webhook_secret VARCHAR(255),
    
    -- Metadata
    tags VARCHAR(50)[],
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT event_sources_name_org_unique UNIQUE (organization_id, name),
    CONSTRAINT event_sources_name_not_empty CHECK (length(trim(name)) > 0),
    CONSTRAINT event_sources_sync_interval_positive CHECK (sync_interval_minutes > 0),
    CONSTRAINT event_sources_batch_size_positive CHECK (batch_size > 0)
);

-- =============================================================================
-- EVENTS STORAGE AND PROCESSING
-- =============================================================================

-- Main events table (time-series optimized)
CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    event_source_id UUID NOT NULL REFERENCES event_sources(id) ON DELETE CASCADE,
    
    -- Event identification
    external_event_id VARCHAR(255),
    event_type event_type NOT NULL,
    event_subtype VARCHAR(100),
    
    -- Event content
    title VARCHAR(500),
    description TEXT,
    event_data JSONB DEFAULT '{}',
    
    -- Event context
    actor_id UUID REFERENCES users(id),
    actor_external_id VARCHAR(255),
    actor_name VARCHAR(255),
    
    -- Target information
    target_type VARCHAR(100), -- repository, issue, pull_request, page, etc.
    target_id VARCHAR(255),
    target_name VARCHAR(255),
    
    -- Event timing
    occurred_at TIMESTAMP WITH TIME ZONE NOT NULL,
    received_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE,
    
    -- Event status
    status event_status DEFAULT 'received',
    processing_attempts INTEGER DEFAULT 0,
    
    -- Event relationships
    parent_event_id UUID REFERENCES events(id),
    thread_id VARCHAR(255), -- For grouping related events
    
    -- Source-specific data
    source_url TEXT,
    source_metadata JSONB DEFAULT '{}',
    
    -- Event fingerprint for deduplication
    event_fingerprint VARCHAR(64), -- SHA-256 hash
    
    -- Processing metadata
    processing_duration_ms INTEGER,
    error_message TEXT,
    
    -- Metadata
    tags VARCHAR(50)[],
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT events_processing_attempts_positive CHECK (processing_attempts >= 0),
    CONSTRAINT events_occurred_at_not_future CHECK (occurred_at <= NOW() + INTERVAL '1 hour')
);

-- Convert events to hypertable for time-series optimization
SELECT create_hypertable('events', 'occurred_at', if_not_exists => TRUE);

-- Event processing queue for async processing
CREATE TABLE event_processing_queue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    
    -- Queue details
    queue_name VARCHAR(100) NOT NULL,
    priority INTEGER DEFAULT 5, -- 1 (highest) to 10 (lowest)
    
    -- Processing status
    status VARCHAR(50) DEFAULT 'queued', -- queued, processing, completed, failed
    
    -- Timing
    queued_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_processing_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Retry logic
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    next_retry_at TIMESTAMP WITH TIME ZONE,
    
    -- Processing metadata
    processor_id VARCHAR(255),
    error_message TEXT,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT event_processing_queue_priority_valid CHECK (priority >= 1 AND priority <= 10),
    CONSTRAINT event_processing_queue_retry_count_positive CHECK (retry_count >= 0)
);

-- =============================================================================
-- EVENT AGGREGATIONS AND ANALYTICS
-- =============================================================================

-- Event aggregations for analytics and reporting
CREATE TABLE event_aggregations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Aggregation identification
    aggregation_name VARCHAR(255) NOT NULL,
    aggregation_period aggregation_period NOT NULL,
    
    -- Aggregation scope
    event_source event_source,
    event_type event_type,
    event_subtype VARCHAR(100),
    
    -- Time window
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Aggregated metrics
    event_count INTEGER DEFAULT 0,
    unique_actors INTEGER DEFAULT 0,
    unique_targets INTEGER DEFAULT 0,
    
    -- Detailed breakdowns
    actor_breakdown JSONB DEFAULT '{}',
    target_breakdown JSONB DEFAULT '{}',
    hourly_distribution JSONB DEFAULT '{}',
    
    -- Quality metrics
    processing_success_rate DECIMAL(5,2),
    average_processing_time_ms INTEGER,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT event_aggregations_unique UNIQUE (
        organization_id, aggregation_name, aggregation_period, 
        event_source, event_type, period_start
    ),
    CONSTRAINT event_aggregations_period_valid CHECK (period_end > period_start),
    CONSTRAINT event_aggregations_counts_positive CHECK (
        event_count >= 0 AND 
        unique_actors >= 0 AND 
        unique_targets >= 0
    )
);

-- Convert event_aggregations to hypertable
SELECT create_hypertable('event_aggregations', 'period_start', if_not_exists => TRUE);

-- =============================================================================
-- SUBSCRIPTIONS AND NOTIFICATIONS
-- =============================================================================

-- Event subscriptions for real-time notifications
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Subscription identification
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Subscription filters
    event_sources event_source[],
    event_types event_type[],
    event_subtypes VARCHAR(100)[],
    
    -- Advanced filtering
    filter_conditions JSONB DEFAULT '{}',
    actor_filters JSONB DEFAULT '{}',
    target_filters JSONB DEFAULT '{}',
    
    -- Subscription configuration
    status subscription_status DEFAULT 'active',
    delivery_method VARCHAR(50) DEFAULT 'webhook', -- webhook, email, slack, etc.
    delivery_config JSONB DEFAULT '{}',
    
    -- Rate limiting
    max_events_per_hour INTEGER DEFAULT 100,
    current_hour_count INTEGER DEFAULT 0,
    rate_limit_reset_at TIMESTAMP WITH TIME ZONE,
    
    -- Subscription health
    last_delivery_at TIMESTAMP WITH TIME ZONE,
    successful_deliveries INTEGER DEFAULT 0,
    failed_deliveries INTEGER DEFAULT 0,
    
    -- Ownership
    created_by UUID REFERENCES users(id),
    
    -- Metadata
    tags VARCHAR(50)[],
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT subscriptions_name_org_unique UNIQUE (organization_id, name),
    CONSTRAINT subscriptions_name_not_empty CHECK (length(trim(name)) > 0),
    CONSTRAINT subscriptions_max_events_positive CHECK (max_events_per_hour > 0)
);

-- Subscription deliveries for tracking notifications
CREATE TABLE subscription_deliveries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    subscription_id UUID NOT NULL REFERENCES subscriptions(id) ON DELETE CASCADE,
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    
    -- Delivery details
    delivery_method VARCHAR(50) NOT NULL,
    delivery_status VARCHAR(50) DEFAULT 'pending', -- pending, sent, failed, retrying
    
    -- Delivery timing
    scheduled_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    delivered_at TIMESTAMP WITH TIME ZONE,
    
    -- Delivery content
    payload JSONB DEFAULT '{}',
    response_data JSONB DEFAULT '{}',
    
    -- Error handling
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    next_retry_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT subscription_deliveries_retry_count_positive CHECK (retry_count >= 0)
);

-- =============================================================================
-- EVENT PATTERNS AND ANOMALIES
-- =============================================================================

-- Event patterns for detecting recurring behaviors
CREATE TABLE event_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Pattern identification
    pattern_name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Pattern definition
    pattern_config JSONB DEFAULT '{}',
    detection_rules JSONB DEFAULT '{}',
    
    -- Pattern statistics
    occurrences_count INTEGER DEFAULT 0,
    last_occurrence_at TIMESTAMP WITH TIME ZONE,
    average_interval_hours DECIMAL(8,2),
    
    -- Pattern status
    is_active BOOLEAN DEFAULT true,
    confidence_score DECIMAL(5,2) DEFAULT 0,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT event_patterns_name_org_unique UNIQUE (organization_id, pattern_name),
    CONSTRAINT event_patterns_confidence_valid CHECK (confidence_score >= 0 AND confidence_score <= 100)
);

-- Event anomalies for detecting unusual patterns
CREATE TABLE event_anomalies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Anomaly identification
    anomaly_type VARCHAR(100) NOT NULL,
    severity VARCHAR(50) DEFAULT 'medium', -- low, medium, high, critical
    
    -- Anomaly details
    description TEXT,
    anomaly_data JSONB DEFAULT '{}',
    
    -- Detection information
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    detection_method VARCHAR(100),
    confidence_score DECIMAL(5,2),
    
    -- Related events
    related_events JSONB DEFAULT '[]',
    event_count INTEGER DEFAULT 0,
    
    -- Resolution
    is_resolved BOOLEAN DEFAULT false,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_notes TEXT,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT event_anomalies_confidence_valid CHECK (confidence_score >= 0 AND confidence_score <= 100),
    CONSTRAINT event_anomalies_event_count_positive CHECK (event_count >= 0)
);

-- =============================================================================
-- INDEXES FOR OPTIMAL PERFORMANCE
-- =============================================================================

-- Event sources indexes
CREATE INDEX idx_event_sources_org_id ON event_sources(organization_id);
CREATE INDEX idx_event_sources_type ON event_sources(source_type);
CREATE INDEX idx_event_sources_active ON event_sources(is_active);
CREATE INDEX idx_event_sources_last_sync ON event_sources(last_sync_at);

-- Events indexes (time-series optimized)
CREATE INDEX idx_events_org_id ON events(organization_id, occurred_at DESC);
CREATE INDEX idx_events_source_id ON events(event_source_id, occurred_at DESC);
CREATE INDEX idx_events_type ON events(event_type, occurred_at DESC);
CREATE INDEX idx_events_actor_id ON events(actor_id, occurred_at DESC);
CREATE INDEX idx_events_target ON events(target_type, target_id, occurred_at DESC);
CREATE INDEX idx_events_status ON events(status);
CREATE INDEX idx_events_fingerprint ON events(event_fingerprint);
CREATE INDEX idx_events_thread_id ON events(thread_id, occurred_at DESC);

-- Event processing queue indexes
CREATE INDEX idx_event_processing_queue_status ON event_processing_queue(status, priority);
CREATE INDEX idx_event_processing_queue_next_retry ON event_processing_queue(next_retry_at);

-- Event aggregations indexes
CREATE INDEX idx_event_aggregations_org_period ON event_aggregations(organization_id, period_start DESC);
CREATE INDEX idx_event_aggregations_source_type ON event_aggregations(event_source, event_type, period_start DESC);

-- Subscriptions indexes
CREATE INDEX idx_subscriptions_org_id ON subscriptions(organization_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);
CREATE INDEX idx_subscriptions_created_by ON subscriptions(created_by);

-- Subscription deliveries indexes
CREATE INDEX idx_subscription_deliveries_subscription_id ON subscription_deliveries(subscription_id);
CREATE INDEX idx_subscription_deliveries_event_id ON subscription_deliveries(event_id);
CREATE INDEX idx_subscription_deliveries_status ON subscription_deliveries(delivery_status);
CREATE INDEX idx_subscription_deliveries_next_retry ON subscription_deliveries(next_retry_at);

-- Patterns and anomalies indexes
CREATE INDEX idx_event_patterns_org_id ON event_patterns(organization_id);
CREATE INDEX idx_event_patterns_active ON event_patterns(is_active);

CREATE INDEX idx_event_anomalies_org_id ON event_anomalies(organization_id);
CREATE INDEX idx_event_anomalies_detected_at ON event_anomalies(detected_at);
CREATE INDEX idx_event_anomalies_severity ON event_anomalies(severity);
CREATE INDEX idx_event_anomalies_resolved ON event_anomalies(is_resolved);

-- GIN indexes for JSONB fields
CREATE INDEX idx_events_data_gin USING gin (event_data);
CREATE INDEX idx_events_metadata_gin USING gin (metadata);
CREATE INDEX idx_event_aggregations_breakdowns_gin USING gin (actor_breakdown);
CREATE INDEX idx_subscriptions_filters_gin USING gin (filter_conditions);

-- Full-text search indexes
CREATE INDEX idx_events_title_trgm USING gin (title gin_trgm_ops);
CREATE INDEX idx_events_description_trgm USING gin (description gin_trgm_ops);

-- =============================================================================
-- VIEWS FOR ANALYTICS AND MONITORING
-- =============================================================================

-- Recent events view
CREATE VIEW recent_events AS
SELECT 
    e.*,
    es.name as source_name,
    es.source_type,
    u.name as actor_name
FROM events e
JOIN event_sources es ON e.event_source_id = es.id
LEFT JOIN users u ON e.actor_id = u.id
WHERE e.occurred_at >= NOW() - INTERVAL '24 hours'
ORDER BY e.occurred_at DESC;

-- Event source health view
CREATE VIEW event_source_health AS
SELECT 
    es.*,
    o.name as organization_name,
    CASE 
        WHEN es.last_sync_at < NOW() - INTERVAL '2 hours' THEN 'stale'
        WHEN es.error_count > 10 THEN 'unhealthy'
        WHEN es.error_count > 0 THEN 'degraded'
        ELSE 'healthy'
    END as computed_health_status,
    COUNT(e.id) as events_last_hour
FROM event_sources es
JOIN organizations o ON es.organization_id = o.id
LEFT JOIN events e ON es.id = e.event_source_id 
    AND e.occurred_at >= NOW() - INTERVAL '1 hour'
GROUP BY es.id, o.name;

-- Subscription performance view
CREATE VIEW subscription_performance AS
SELECT 
    s.*,
    COUNT(sd.id) as total_deliveries,
    COUNT(CASE WHEN sd.delivery_status = 'sent' THEN 1 END) as successful_deliveries,
    COUNT(CASE WHEN sd.delivery_status = 'failed' THEN 1 END) as failed_deliveries,
    ROUND(
        CASE 
            WHEN COUNT(sd.id) > 0 
            THEN (COUNT(CASE WHEN sd.delivery_status = 'sent' THEN 1 END)::DECIMAL / COUNT(sd.id)) * 100 
            ELSE 0 
        END, 2
    ) as success_rate_percentage
FROM subscriptions s
LEFT JOIN subscription_deliveries sd ON s.id = sd.subscription_id
    AND sd.created_at >= NOW() - INTERVAL '24 hours'
GROUP BY s.id;

-- Grant permissions to events_user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO events_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO events_user;
GRANT USAGE ON SCHEMA public TO events_user;

-- Insert default organization
INSERT INTO organizations (name, slug, description) VALUES 
('Default Organization', 'default', 'Default organization for event tracking');

-- Insert default admin user
INSERT INTO users (organization_id, name, email, role) VALUES 
((SELECT id FROM organizations WHERE slug = 'default'), 'Events Admin', 'admin@events.local', 'admin');

-- Final status message
DO $$
BEGIN
    RAISE NOTICE '📡 Events Database initialized successfully!';
    RAISE NOTICE 'Features: Multi-source ingestion, Real-time subscriptions, Event aggregations, Anomaly detection';
    RAISE NOTICE 'Sources: GitHub, Linear, Notion, Slack, and custom webhooks';
    RAISE NOTICE 'Time-series optimization: Enabled with TimescaleDB';
    RAISE NOTICE 'Timestamp: %', NOW();
END $$;

