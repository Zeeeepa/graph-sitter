-- =============================================================================
-- PROMPTS DATABASE SCHEMA: Template Management and Conditional Prompts
-- =============================================================================
-- This database handles template management, conditional prompts, A/B testing,
-- and effectiveness tracking for prompt management.
-- =============================================================================

-- Connect to prompts_db
\c prompts_db;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- Set timezone and configuration
SET timezone = 'UTC';
SET default_text_search_config = 'pg_catalog.english';

-- Grant all privileges to prompts_user
GRANT ALL PRIVILEGES ON DATABASE prompts_db TO prompts_user;
GRANT ALL PRIVILEGES ON SCHEMA public TO prompts_user;

-- Prompt-specific enums
CREATE TYPE prompt_type AS ENUM (
    'system',
    'user',
    'assistant',
    'function',
    'template',
    'conditional'
);

CREATE TYPE execution_status AS ENUM (
    'pending',
    'running',
    'completed',
    'failed',
    'cancelled',
    'timeout'
);

CREATE TYPE context_type AS ENUM (
    'code',
    'documentation',
    'conversation',
    'file',
    'database',
    'api',
    'web',
    'custom'
);

CREATE TYPE effectiveness_rating AS ENUM (
    'poor',
    'fair',
    'good',
    'excellent',
    'outstanding'
);

CREATE TYPE template_status AS ENUM (
    'draft',
    'active',
    'deprecated',
    'archived'
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

-- Users table for prompt authoring
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(50) DEFAULT 'member',
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- PROMPT TEMPLATES MANAGEMENT
-- =============================================================================

-- Main prompt templates table
CREATE TABLE prompt_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Template identification
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) NOT NULL,
    description TEXT,
    
    -- Template content
    template_content TEXT NOT NULL,
    prompt_type prompt_type NOT NULL,
    
    -- Template configuration
    status template_status DEFAULT 'draft',
    version INTEGER DEFAULT 1,
    is_default BOOLEAN DEFAULT false,
    
    -- Template structure
    variables JSONB DEFAULT '[]', -- Variable definitions
    conditions JSONB DEFAULT '{}', -- Conditional logic
    fallback_template_id UUID REFERENCES prompt_templates(id),
    
    -- Usage and effectiveness
    usage_count INTEGER DEFAULT 0,
    success_rate DECIMAL(5,2) DEFAULT 0,
    average_rating DECIMAL(3,2) DEFAULT 0,
    
    -- Template metadata
    category VARCHAR(100),
    tags VARCHAR(50)[],
    
    -- Model configuration
    model_config JSONB DEFAULT '{}', -- Model-specific settings
    max_tokens INTEGER,
    temperature DECIMAL(3,2),
    
    -- Validation and constraints
    validation_rules JSONB DEFAULT '{}',
    required_variables JSONB DEFAULT '[]',
    
    -- Authoring and ownership
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    
    -- External references
    external_template_id VARCHAR(255),
    source_url TEXT,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT prompt_templates_name_org_unique UNIQUE (organization_id, name),
    CONSTRAINT prompt_templates_slug_org_unique UNIQUE (organization_id, slug),
    CONSTRAINT prompt_templates_name_not_empty CHECK (length(trim(name)) > 0),
    CONSTRAINT prompt_templates_content_not_empty CHECK (length(trim(template_content)) > 0),
    CONSTRAINT prompt_templates_version_positive CHECK (version > 0),
    CONSTRAINT prompt_templates_success_rate_valid CHECK (success_rate >= 0 AND success_rate <= 100),
    CONSTRAINT prompt_templates_rating_valid CHECK (average_rating >= 0 AND average_rating <= 5)
);

-- Template versions for version control
CREATE TABLE template_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_id UUID NOT NULL REFERENCES prompt_templates(id) ON DELETE CASCADE,
    
    -- Version details
    version_number INTEGER NOT NULL,
    version_name VARCHAR(255),
    description TEXT,
    
    -- Version content
    template_content TEXT NOT NULL,
    variables JSONB DEFAULT '[]',
    conditions JSONB DEFAULT '{}',
    model_config JSONB DEFAULT '{}',
    
    -- Version status
    is_current BOOLEAN DEFAULT false,
    is_published BOOLEAN DEFAULT false,
    
    -- Change tracking
    changes_summary TEXT,
    changed_by UUID REFERENCES users(id),
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT template_versions_unique UNIQUE (template_id, version_number),
    CONSTRAINT template_versions_version_positive CHECK (version_number > 0)
);

-- =============================================================================
-- PROMPT EXECUTIONS AND TRACKING
-- =============================================================================

-- Prompt executions for tracking usage and effectiveness
CREATE TABLE executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    template_id UUID REFERENCES prompt_templates(id),
    
    -- Execution identification
    execution_name VARCHAR(255),
    session_id UUID,
    
    -- Execution details
    status execution_status DEFAULT 'pending',
    prompt_type prompt_type NOT NULL,
    
    -- Prompt content
    rendered_prompt TEXT NOT NULL,
    variables_used JSONB DEFAULT '{}',
    
    -- Execution context
    context_data JSONB DEFAULT '{}',
    model_used VARCHAR(100),
    model_config JSONB DEFAULT '{}',
    
    -- Timing and performance
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER,
    
    -- Input/Output tracking
    input_tokens INTEGER,
    output_tokens INTEGER,
    total_tokens INTEGER,
    
    -- Response and results
    response_content TEXT,
    response_metadata JSONB DEFAULT '{}',
    
    -- Quality and effectiveness
    effectiveness_rating effectiveness_rating,
    quality_score DECIMAL(5,2),
    user_feedback TEXT,
    
    -- Error handling
    error_message TEXT,
    error_code VARCHAR(50),
    retry_count INTEGER DEFAULT 0,
    
    -- Cost tracking
    cost_usd DECIMAL(10,6),
    
    -- User and session tracking
    user_id UUID REFERENCES users(id),
    user_agent TEXT,
    ip_address INET,
    
    -- External references
    external_execution_id VARCHAR(255),
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT executions_duration_positive CHECK (duration_ms >= 0),
    CONSTRAINT executions_tokens_positive CHECK (
        input_tokens >= 0 AND 
        output_tokens >= 0 AND 
        total_tokens >= 0
    ),
    CONSTRAINT executions_quality_score_valid CHECK (quality_score >= 0 AND quality_score <= 100),
    CONSTRAINT executions_cost_positive CHECK (cost_usd >= 0)
);

-- =============================================================================
-- CONTEXT SOURCES AND DATA
-- =============================================================================

-- Context sources for prompt enrichment
CREATE TABLE context_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Source identification
    name VARCHAR(255) NOT NULL,
    description TEXT,
    context_type context_type NOT NULL,
    
    -- Source configuration
    source_config JSONB DEFAULT '{}',
    access_config JSONB DEFAULT '{}',
    
    -- Content and metadata
    content TEXT,
    content_hash VARCHAR(64), -- SHA-256 hash for change detection
    content_size_bytes INTEGER,
    
    -- Source status
    is_active BOOLEAN DEFAULT true,
    last_updated_at TIMESTAMP WITH TIME ZONE,
    last_accessed_at TIMESTAMP WITH TIME ZONE,
    
    -- Usage tracking
    usage_count INTEGER DEFAULT 0,
    
    -- External references
    external_source_id VARCHAR(255),
    source_url TEXT,
    
    -- Metadata
    tags VARCHAR(50)[],
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT context_sources_name_org_unique UNIQUE (organization_id, name),
    CONSTRAINT context_sources_name_not_empty CHECK (length(trim(name)) > 0),
    CONSTRAINT context_sources_size_positive CHECK (content_size_bytes >= 0)
);

-- Context usage tracking
CREATE TABLE execution_contexts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    execution_id UUID NOT NULL REFERENCES executions(id) ON DELETE CASCADE,
    context_source_id UUID NOT NULL REFERENCES context_sources(id) ON DELETE CASCADE,
    
    -- Context usage details
    context_portion TEXT, -- Specific portion used
    relevance_score DECIMAL(5,2), -- How relevant was this context
    
    -- Usage metadata
    usage_metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT execution_contexts_unique UNIQUE (execution_id, context_source_id),
    CONSTRAINT execution_contexts_relevance_valid CHECK (relevance_score >= 0 AND relevance_score <= 100)
);

-- =============================================================================
-- A/B TESTING AND EXPERIMENTS
-- =============================================================================

-- A/B testing experiments
CREATE TABLE ab_experiments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Experiment identification
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Experiment configuration
    hypothesis TEXT,
    success_metrics JSONB DEFAULT '[]',
    
    -- Experiment status
    status VARCHAR(50) DEFAULT 'draft', -- draft, running, paused, completed
    
    -- Experiment timeline
    start_date TIMESTAMP WITH TIME ZONE,
    end_date TIMESTAMP WITH TIME ZONE,
    duration_days INTEGER,
    
    -- Traffic allocation
    traffic_percentage DECIMAL(5,2) DEFAULT 50, -- Percentage of traffic to include
    
    -- Statistical configuration
    confidence_level DECIMAL(5,2) DEFAULT 95,
    minimum_sample_size INTEGER DEFAULT 100,
    
    -- Results tracking
    statistical_significance BOOLEAN DEFAULT false,
    winner_variant_id UUID,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT ab_experiments_name_org_unique UNIQUE (organization_id, name),
    CONSTRAINT ab_experiments_traffic_valid CHECK (traffic_percentage >= 0 AND traffic_percentage <= 100),
    CONSTRAINT ab_experiments_confidence_valid CHECK (confidence_level >= 0 AND confidence_level <= 100)
);

-- Experiment variants
CREATE TABLE experiment_variants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    experiment_id UUID NOT NULL REFERENCES ab_experiments(id) ON DELETE CASCADE,
    template_id UUID NOT NULL REFERENCES prompt_templates(id) ON DELETE CASCADE,
    
    -- Variant details
    variant_name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Traffic allocation
    traffic_weight DECIMAL(5,2) DEFAULT 50, -- Weight for traffic distribution
    
    -- Performance metrics
    execution_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    average_quality_score DECIMAL(5,2) DEFAULT 0,
    average_duration_ms INTEGER DEFAULT 0,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT experiment_variants_name_exp_unique UNIQUE (experiment_id, variant_name),
    CONSTRAINT experiment_variants_weight_valid CHECK (traffic_weight >= 0 AND traffic_weight <= 100)
);

-- =============================================================================
-- INDEXES FOR OPTIMAL PERFORMANCE
-- =============================================================================

-- Prompt templates indexes
CREATE INDEX idx_prompt_templates_org_id ON prompt_templates(organization_id);
CREATE INDEX idx_prompt_templates_status ON prompt_templates(status);
CREATE INDEX idx_prompt_templates_type ON prompt_templates(prompt_type);
CREATE INDEX idx_prompt_templates_category ON prompt_templates(category);
CREATE INDEX idx_prompt_templates_created_by ON prompt_templates(created_by);
CREATE INDEX idx_prompt_templates_usage_count ON prompt_templates(usage_count DESC);
CREATE INDEX idx_prompt_templates_success_rate ON prompt_templates(success_rate DESC);

-- Template versions indexes
CREATE INDEX idx_template_versions_template_id ON template_versions(template_id);
CREATE INDEX idx_template_versions_version_number ON template_versions(version_number);
CREATE INDEX idx_template_versions_is_current ON template_versions(is_current);

-- Executions indexes
CREATE INDEX idx_executions_org_id ON executions(organization_id);
CREATE INDEX idx_executions_template_id ON executions(template_id);
CREATE INDEX idx_executions_status ON executions(status);
CREATE INDEX idx_executions_user_id ON executions(user_id);
CREATE INDEX idx_executions_session_id ON executions(session_id);
CREATE INDEX idx_executions_started_at ON executions(started_at);
CREATE INDEX idx_executions_completed_at ON executions(completed_at);
CREATE INDEX idx_executions_effectiveness ON executions(effectiveness_rating);

-- Context sources indexes
CREATE INDEX idx_context_sources_org_id ON context_sources(organization_id);
CREATE INDEX idx_context_sources_type ON context_sources(context_type);
CREATE INDEX idx_context_sources_is_active ON context_sources(is_active);
CREATE INDEX idx_context_sources_last_updated ON context_sources(last_updated_at);

-- Execution contexts indexes
CREATE INDEX idx_execution_contexts_execution_id ON execution_contexts(execution_id);
CREATE INDEX idx_execution_contexts_context_source_id ON execution_contexts(context_source_id);
CREATE INDEX idx_execution_contexts_relevance ON execution_contexts(relevance_score DESC);

-- A/B testing indexes
CREATE INDEX idx_ab_experiments_org_id ON ab_experiments(organization_id);
CREATE INDEX idx_ab_experiments_status ON ab_experiments(status);
CREATE INDEX idx_ab_experiments_start_date ON ab_experiments(start_date);
CREATE INDEX idx_ab_experiments_end_date ON ab_experiments(end_date);

CREATE INDEX idx_experiment_variants_experiment_id ON experiment_variants(experiment_id);
CREATE INDEX idx_experiment_variants_template_id ON experiment_variants(template_id);

-- GIN indexes for JSONB fields
CREATE INDEX idx_prompt_templates_variables_gin USING gin (variables);
CREATE INDEX idx_prompt_templates_metadata_gin USING gin (metadata);
CREATE INDEX idx_executions_variables_gin USING gin (variables_used);
CREATE INDEX idx_executions_context_gin USING gin (context_data);

-- =============================================================================
-- VIEWS FOR ANALYTICS AND REPORTING
-- =============================================================================

-- Template effectiveness view
CREATE VIEW template_effectiveness AS
SELECT 
    pt.id,
    pt.name,
    pt.category,
    pt.usage_count,
    pt.success_rate,
    pt.average_rating,
    COUNT(e.id) as total_executions,
    COUNT(CASE WHEN e.status = 'completed' THEN 1 END) as successful_executions,
    AVG(e.duration_ms) as avg_duration_ms,
    AVG(e.quality_score) as avg_quality_score,
    SUM(e.cost_usd) as total_cost_usd
FROM prompt_templates pt
LEFT JOIN executions e ON pt.id = e.template_id
WHERE pt.deleted_at IS NULL
GROUP BY pt.id, pt.name, pt.category, pt.usage_count, pt.success_rate, pt.average_rating;

-- Recent executions view
CREATE VIEW recent_executions AS
SELECT 
    e.*,
    pt.name as template_name,
    pt.category as template_category,
    u.name as user_name
FROM executions e
LEFT JOIN prompt_templates pt ON e.template_id = pt.id
LEFT JOIN users u ON e.user_id = u.id
WHERE e.created_at >= NOW() - INTERVAL '7 days'
ORDER BY e.created_at DESC;

-- Grant permissions to prompts_user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO prompts_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO prompts_user;
GRANT USAGE ON SCHEMA public TO prompts_user;

-- Insert default organization
INSERT INTO organizations (name, slug, description) VALUES 
('Default Organization', 'default', 'Default organization for prompt management');

-- Insert default admin user
INSERT INTO users (organization_id, name, email, role) VALUES 
((SELECT id FROM organizations WHERE slug = 'default'), 'Prompts Admin', 'admin@prompts.local', 'admin');

-- Final status message
DO $$
BEGIN
    RAISE NOTICE '💬 Prompts Database initialized successfully!';
    RAISE NOTICE 'Features: Template management, A/B testing, Effectiveness tracking, Context sources';
    RAISE NOTICE 'Timestamp: %', NOW();
END $$;

