-- =============================================================================
-- PROMPTS MODULE SCHEMA
-- =============================================================================
-- This module handles dynamic prompt generation and template management,
-- context-aware prompt expansion, and prompt effectiveness tracking.
-- =============================================================================

-- =============================================================================
-- ENUMS
-- =============================================================================

CREATE TYPE prompt_type AS ENUM (
    'system',
    'user',
    'assistant',
    'function',
    'template',
    'context'
);

CREATE TYPE prompt_category AS ENUM (
    'code_generation',
    'code_review',
    'debugging',
    'refactoring',
    'testing',
    'documentation',
    'analysis',
    'explanation',
    'custom'
);

CREATE TYPE template_status AS ENUM (
    'draft',
    'active',
    'deprecated',
    'archived'
);

CREATE TYPE execution_status AS ENUM (
    'pending',
    'running',
    'completed',
    'failed',
    'cancelled'
);

-- =============================================================================
-- PROMPTS TABLES
-- =============================================================================

-- Prompt templates - reusable prompt structures
CREATE TABLE prompt_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Template identification
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) NOT NULL,
    version VARCHAR(20) DEFAULT '1.0.0',
    description TEXT,
    
    -- Template configuration
    prompt_type prompt_type NOT NULL,
    category prompt_category NOT NULL,
    status template_status DEFAULT 'draft',
    
    -- Template content
    template_content TEXT NOT NULL,
    system_prompt TEXT,
    
    -- Variables and parameters
    variables JSONB DEFAULT '{}', -- Variable definitions with types and defaults
    required_variables TEXT[] DEFAULT '{}',
    optional_variables TEXT[] DEFAULT '{}',
    
    -- Context requirements
    context_requirements JSONB DEFAULT '{}',
    max_context_length INTEGER DEFAULT 4000,
    
    -- Model configuration
    model_name VARCHAR(100),
    model_parameters JSONB DEFAULT '{}', -- temperature, max_tokens, etc.
    
    -- Usage tracking
    usage_count INTEGER DEFAULT 0,
    success_rate DECIMAL(5,2) DEFAULT 0,
    avg_execution_time_ms INTEGER DEFAULT 0,
    
    -- Ownership and permissions
    created_by UUID REFERENCES users(id),
    is_public BOOLEAN DEFAULT false,
    allowed_users UUID[] DEFAULT '{}',
    allowed_roles VARCHAR(50)[] DEFAULT '{}',
    
    -- Metadata
    tags VARCHAR(50)[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE NULL,
    
    UNIQUE(organization_id, slug, version)
);

-- Prompt executions - track prompt usage and results
CREATE TABLE prompt_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    template_id UUID REFERENCES prompt_templates(id) ON DELETE SET NULL,
    
    -- Execution identification
    short_id VARCHAR(20) UNIQUE DEFAULT generate_short_id('PE-'),
    
    -- Context
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    repository_id UUID REFERENCES repositories(id) ON DELETE SET NULL,
    task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
    
    -- Execution details
    status execution_status DEFAULT 'pending',
    prompt_type prompt_type NOT NULL,
    category prompt_category NOT NULL,
    
    -- Input data
    input_variables JSONB DEFAULT '{}',
    context_data JSONB DEFAULT '{}',
    raw_prompt TEXT NOT NULL,
    system_prompt TEXT,
    
    -- Model configuration
    model_name VARCHAR(100) NOT NULL,
    model_parameters JSONB DEFAULT '{}',
    
    -- Execution results
    response_text TEXT,
    response_data JSONB DEFAULT '{}',
    
    -- Performance metrics
    execution_time_ms INTEGER,
    token_count_input INTEGER,
    token_count_output INTEGER,
    cost_usd DECIMAL(10,6),
    
    -- Quality metrics
    user_rating INTEGER CHECK (user_rating >= 1 AND user_rating <= 5),
    effectiveness_score DECIMAL(5,2),
    
    -- Error handling
    error_message TEXT,
    error_details JSONB DEFAULT '{}',
    
    -- Ownership
    executed_by UUID REFERENCES users(id),
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Context sources - manage context data for prompts
CREATE TABLE context_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Source identification
    name VARCHAR(255) NOT NULL,
    source_type VARCHAR(100) NOT NULL, -- file, database, api, repository, etc.
    
    -- Source configuration
    config JSONB DEFAULT '{}',
    connection_string TEXT,
    
    -- Content processing
    content_processor VARCHAR(100), -- text, code, json, xml, etc.
    max_content_length INTEGER DEFAULT 10000,
    
    -- Caching
    cache_duration_minutes INTEGER DEFAULT 60,
    last_cached_at TIMESTAMP WITH TIME ZONE,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE NULL,
    
    UNIQUE(organization_id, name)
);

-- Context data - cached context content
CREATE TABLE context_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    context_source_id UUID NOT NULL REFERENCES context_sources(id) ON DELETE CASCADE,
    
    -- Content identification
    content_key VARCHAR(500) NOT NULL, -- file path, query hash, etc.
    content_hash VARCHAR(64), -- SHA-256 hash of content
    
    -- Content data
    content_text TEXT,
    content_data JSONB DEFAULT '{}',
    content_size_bytes INTEGER,
    
    -- Processing metadata
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Usage tracking
    access_count INTEGER DEFAULT 0,
    last_accessed_at TIMESTAMP WITH TIME ZONE,
    
    UNIQUE(context_source_id, content_key)
);

-- Prompt context mappings - link prompts to context sources
CREATE TABLE prompt_context_mappings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_id UUID NOT NULL REFERENCES prompt_templates(id) ON DELETE CASCADE,
    context_source_id UUID NOT NULL REFERENCES context_sources(id) ON DELETE CASCADE,
    
    -- Mapping configuration
    is_required BOOLEAN DEFAULT false,
    priority INTEGER DEFAULT 1, -- Order of context inclusion
    
    -- Context processing
    context_processor VARCHAR(100), -- How to process this context
    max_length INTEGER, -- Max length for this specific context
    
    -- Filtering
    filter_expression TEXT, -- JSON logic expression for filtering
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(template_id, context_source_id)
);

-- Prompt feedback - collect user feedback on prompt effectiveness
CREATE TABLE prompt_feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    execution_id UUID NOT NULL REFERENCES prompt_executions(id) ON DELETE CASCADE,
    
    -- Feedback details
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    feedback_text TEXT,
    
    -- Feedback categories
    accuracy_rating INTEGER CHECK (accuracy_rating >= 1 AND accuracy_rating <= 5),
    relevance_rating INTEGER CHECK (relevance_rating >= 1 AND relevance_rating <= 5),
    completeness_rating INTEGER CHECK (completeness_rating >= 1 AND completeness_rating <= 5),
    clarity_rating INTEGER CHECK (clarity_rating >= 1 AND clarity_rating <= 5),
    
    -- Improvement suggestions
    suggested_improvements TEXT,
    
    -- Feedback metadata
    feedback_type VARCHAR(50) DEFAULT 'manual', -- manual, automated, implicit
    
    -- Ownership
    provided_by UUID REFERENCES users(id),
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Prompt variations - A/B testing for prompts
CREATE TABLE prompt_variations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    base_template_id UUID NOT NULL REFERENCES prompt_templates(id) ON DELETE CASCADE,
    
    -- Variation details
    variation_name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Variation content
    template_content TEXT NOT NULL,
    system_prompt TEXT,
    model_parameters JSONB DEFAULT '{}',
    
    -- A/B testing
    traffic_percentage DECIMAL(5,2) DEFAULT 0, -- Percentage of traffic to route to this variation
    is_active BOOLEAN DEFAULT false,
    
    -- Performance tracking
    execution_count INTEGER DEFAULT 0,
    success_rate DECIMAL(5,2) DEFAULT 0,
    avg_rating DECIMAL(3,2) DEFAULT 0,
    avg_execution_time_ms INTEGER DEFAULT 0,
    
    -- Statistical significance
    confidence_level DECIMAL(5,2),
    p_value DECIMAL(10,8),
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE NULL,
    
    UNIQUE(base_template_id, variation_name)
);

-- =============================================================================
-- INDEXES
-- =============================================================================

-- Prompt templates indexes
CREATE INDEX idx_prompt_templates_organization_id ON prompt_templates(organization_id);
CREATE INDEX idx_prompt_templates_slug ON prompt_templates(slug);
CREATE INDEX idx_prompt_templates_prompt_type ON prompt_templates(prompt_type);
CREATE INDEX idx_prompt_templates_category ON prompt_templates(category);
CREATE INDEX idx_prompt_templates_status ON prompt_templates(status);
CREATE INDEX idx_prompt_templates_created_by ON prompt_templates(created_by);
CREATE INDEX idx_prompt_templates_is_public ON prompt_templates(is_public);
CREATE INDEX idx_prompt_templates_usage_count ON prompt_templates(usage_count);
CREATE INDEX idx_prompt_templates_success_rate ON prompt_templates(success_rate);
CREATE INDEX idx_prompt_templates_created_at ON prompt_templates(created_at);
CREATE INDEX idx_prompt_templates_deleted_at ON prompt_templates(deleted_at) WHERE deleted_at IS NULL;

-- GIN indexes for prompt templates
CREATE INDEX idx_prompt_templates_tags ON prompt_templates USING GIN(tags);
CREATE INDEX idx_prompt_templates_variables ON prompt_templates USING GIN(variables);
CREATE INDEX idx_prompt_templates_context_requirements ON prompt_templates USING GIN(context_requirements);
CREATE INDEX idx_prompt_templates_metadata ON prompt_templates USING GIN(metadata);
CREATE INDEX idx_prompt_templates_allowed_users ON prompt_templates USING GIN(allowed_users);
CREATE INDEX idx_prompt_templates_allowed_roles ON prompt_templates USING GIN(allowed_roles);

-- Text search index for template content
CREATE INDEX idx_prompt_templates_content_search ON prompt_templates USING GIN(to_tsvector('english', template_content || ' ' || COALESCE(description, '')));

-- Prompt executions indexes
CREATE INDEX idx_prompt_executions_organization_id ON prompt_executions(organization_id);
CREATE INDEX idx_prompt_executions_template_id ON prompt_executions(template_id);
CREATE INDEX idx_prompt_executions_short_id ON prompt_executions(short_id);
CREATE INDEX idx_prompt_executions_project_id ON prompt_executions(project_id);
CREATE INDEX idx_prompt_executions_repository_id ON prompt_executions(repository_id);
CREATE INDEX idx_prompt_executions_task_id ON prompt_executions(task_id);
CREATE INDEX idx_prompt_executions_status ON prompt_executions(status);
CREATE INDEX idx_prompt_executions_prompt_type ON prompt_executions(prompt_type);
CREATE INDEX idx_prompt_executions_category ON prompt_executions(category);
CREATE INDEX idx_prompt_executions_model_name ON prompt_executions(model_name);
CREATE INDEX idx_prompt_executions_executed_by ON prompt_executions(executed_by);
CREATE INDEX idx_prompt_executions_user_rating ON prompt_executions(user_rating);
CREATE INDEX idx_prompt_executions_effectiveness_score ON prompt_executions(effectiveness_score);
CREATE INDEX idx_prompt_executions_started_at ON prompt_executions(started_at);
CREATE INDEX idx_prompt_executions_completed_at ON prompt_executions(completed_at);
CREATE INDEX idx_prompt_executions_created_at ON prompt_executions(created_at);

-- Composite indexes for common queries
CREATE INDEX idx_prompt_executions_template_status ON prompt_executions(template_id, status);
CREATE INDEX idx_prompt_executions_category_rating ON prompt_executions(category, user_rating);

-- GIN indexes for prompt executions
CREATE INDEX idx_prompt_executions_input_variables ON prompt_executions USING GIN(input_variables);
CREATE INDEX idx_prompt_executions_context_data ON prompt_executions USING GIN(context_data);
CREATE INDEX idx_prompt_executions_response_data ON prompt_executions USING GIN(response_data);
CREATE INDEX idx_prompt_executions_metadata ON prompt_executions USING GIN(metadata);

-- Context sources indexes
CREATE INDEX idx_context_sources_organization_id ON context_sources(organization_id);
CREATE INDEX idx_context_sources_name ON context_sources(name);
CREATE INDEX idx_context_sources_source_type ON context_sources(source_type);
CREATE INDEX idx_context_sources_is_active ON context_sources(is_active);
CREATE INDEX idx_context_sources_last_cached_at ON context_sources(last_cached_at);
CREATE INDEX idx_context_sources_created_at ON context_sources(created_at);
CREATE INDEX idx_context_sources_deleted_at ON context_sources(deleted_at) WHERE deleted_at IS NULL;

-- GIN indexes for context sources
CREATE INDEX idx_context_sources_config ON context_sources USING GIN(config);
CREATE INDEX idx_context_sources_metadata ON context_sources USING GIN(metadata);

-- Context data indexes
CREATE INDEX idx_context_data_context_source_id ON context_data(context_source_id);
CREATE INDEX idx_context_data_content_key ON context_data(content_key);
CREATE INDEX idx_context_data_content_hash ON context_data(content_hash);
CREATE INDEX idx_context_data_processed_at ON context_data(processed_at);
CREATE INDEX idx_context_data_expires_at ON context_data(expires_at);
CREATE INDEX idx_context_data_access_count ON context_data(access_count);
CREATE INDEX idx_context_data_last_accessed_at ON context_data(last_accessed_at);

-- GIN index for context data content
CREATE INDEX idx_context_data_content_data ON context_data USING GIN(content_data);

-- Text search index for context content
CREATE INDEX idx_context_data_content_search ON context_data USING GIN(to_tsvector('english', COALESCE(content_text, '')));

-- Prompt context mappings indexes
CREATE INDEX idx_prompt_context_mappings_template_id ON prompt_context_mappings(template_id);
CREATE INDEX idx_prompt_context_mappings_context_source_id ON prompt_context_mappings(context_source_id);
CREATE INDEX idx_prompt_context_mappings_is_required ON prompt_context_mappings(is_required);
CREATE INDEX idx_prompt_context_mappings_priority ON prompt_context_mappings(priority);

-- Prompt feedback indexes
CREATE INDEX idx_prompt_feedback_execution_id ON prompt_feedback(execution_id);
CREATE INDEX idx_prompt_feedback_rating ON prompt_feedback(rating);
CREATE INDEX idx_prompt_feedback_accuracy_rating ON prompt_feedback(accuracy_rating);
CREATE INDEX idx_prompt_feedback_relevance_rating ON prompt_feedback(relevance_rating);
CREATE INDEX idx_prompt_feedback_provided_by ON prompt_feedback(provided_by);
CREATE INDEX idx_prompt_feedback_feedback_type ON prompt_feedback(feedback_type);
CREATE INDEX idx_prompt_feedback_created_at ON prompt_feedback(created_at);

-- Prompt variations indexes
CREATE INDEX idx_prompt_variations_base_template_id ON prompt_variations(base_template_id);
CREATE INDEX idx_prompt_variations_variation_name ON prompt_variations(variation_name);
CREATE INDEX idx_prompt_variations_is_active ON prompt_variations(is_active);
CREATE INDEX idx_prompt_variations_traffic_percentage ON prompt_variations(traffic_percentage);
CREATE INDEX idx_prompt_variations_success_rate ON prompt_variations(success_rate);
CREATE INDEX idx_prompt_variations_avg_rating ON prompt_variations(avg_rating);
CREATE INDEX idx_prompt_variations_created_at ON prompt_variations(created_at);
CREATE INDEX idx_prompt_variations_deleted_at ON prompt_variations(deleted_at) WHERE deleted_at IS NULL;

-- =============================================================================
-- TRIGGERS
-- =============================================================================

CREATE TRIGGER trigger_prompt_templates_updated_at
    BEFORE UPDATE ON prompt_templates
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_prompt_executions_updated_at
    BEFORE UPDATE ON prompt_executions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_context_sources_updated_at
    BEFORE UPDATE ON context_sources
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_prompt_variations_updated_at
    BEFORE UPDATE ON prompt_variations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- VIEWS
-- =============================================================================

-- Template performance view
CREATE VIEW template_performance AS
SELECT 
    pt.*,
    COUNT(pe.id) as total_executions,
    COUNT(CASE WHEN pe.status = 'completed' THEN 1 END) as successful_executions,
    COUNT(CASE WHEN pe.status = 'failed' THEN 1 END) as failed_executions,
    AVG(pe.execution_time_ms) as avg_execution_time_ms,
    AVG(pe.token_count_input) as avg_input_tokens,
    AVG(pe.token_count_output) as avg_output_tokens,
    AVG(pe.cost_usd) as avg_cost_usd,
    AVG(pe.user_rating) as avg_user_rating,
    AVG(pe.effectiveness_score) as avg_effectiveness_score,
    MAX(pe.completed_at) as last_execution_at
FROM prompt_templates pt
LEFT JOIN prompt_executions pe ON pt.id = pe.template_id
WHERE pt.deleted_at IS NULL
GROUP BY pt.id;

-- Context source usage view
CREATE VIEW context_source_usage AS
SELECT 
    cs.*,
    COUNT(cd.id) as cached_items_count,
    SUM(cd.content_size_bytes) as total_content_size_bytes,
    SUM(cd.access_count) as total_access_count,
    MAX(cd.last_accessed_at) as last_accessed_at,
    COUNT(pcm.id) as template_mappings_count
FROM context_sources cs
LEFT JOIN context_data cd ON cs.id = cd.context_source_id
LEFT JOIN prompt_context_mappings pcm ON cs.id = pcm.context_source_id
WHERE cs.deleted_at IS NULL
GROUP BY cs.id;

-- Execution analytics view
CREATE VIEW execution_analytics AS
SELECT 
    DATE_TRUNC('day', pe.started_at) as execution_date,
    pe.category,
    pe.model_name,
    COUNT(*) as execution_count,
    COUNT(CASE WHEN pe.status = 'completed' THEN 1 END) as successful_count,
    AVG(pe.execution_time_ms) as avg_execution_time_ms,
    SUM(pe.token_count_input) as total_input_tokens,
    SUM(pe.token_count_output) as total_output_tokens,
    SUM(pe.cost_usd) as total_cost_usd,
    AVG(pe.user_rating) as avg_user_rating
FROM prompt_executions pe
WHERE pe.started_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE_TRUNC('day', pe.started_at), pe.category, pe.model_name
ORDER BY execution_date DESC;

-- =============================================================================
-- FUNCTIONS
-- =============================================================================

-- Function to calculate template effectiveness score
CREATE OR REPLACE FUNCTION calculate_template_effectiveness(template_uuid UUID)
RETURNS DECIMAL(5,2) AS $$
DECLARE
    effectiveness_score DECIMAL(5,2) := 0;
    success_rate DECIMAL(5,2) := 0;
    avg_rating DECIMAL(5,2) := 0;
    avg_execution_time DECIMAL(10,2) := 0;
    execution_count INTEGER := 0;
BEGIN
    -- Get basic metrics
    SELECT 
        COUNT(*),
        COUNT(CASE WHEN status = 'completed' THEN 1 END)::DECIMAL / NULLIF(COUNT(*), 0) * 100,
        AVG(user_rating),
        AVG(execution_time_ms)
    INTO execution_count, success_rate, avg_rating, avg_execution_time
    FROM prompt_executions
    WHERE template_id = template_uuid
    AND started_at >= CURRENT_DATE - INTERVAL '30 days';
    
    -- Calculate effectiveness score (0-100)
    IF execution_count > 0 THEN
        -- Success rate component (0-40 points)
        effectiveness_score := effectiveness_score + (success_rate * 0.4);
        
        -- User rating component (0-40 points)
        IF avg_rating IS NOT NULL THEN
            effectiveness_score := effectiveness_score + ((avg_rating / 5.0) * 40);
        END IF;
        
        -- Performance component (0-20 points, faster is better)
        IF avg_execution_time IS NOT NULL THEN
            -- Assume 5000ms is baseline (10 points), faster gets more points
            effectiveness_score := effectiveness_score + GREATEST(0, LEAST(20, 20 - (avg_execution_time / 250)));
        END IF;
    END IF;
    
    RETURN LEAST(100, GREATEST(0, effectiveness_score));
END;
$$ LANGUAGE plpgsql;

-- Function to update template statistics
CREATE OR REPLACE FUNCTION update_template_statistics()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'completed' AND OLD.status != 'completed' THEN
        UPDATE prompt_templates
        SET 
            usage_count = usage_count + 1,
            success_rate = calculate_template_effectiveness(NEW.template_id),
            avg_execution_time_ms = (
                SELECT AVG(execution_time_ms)::INTEGER
                FROM prompt_executions
                WHERE template_id = NEW.template_id
                AND status = 'completed'
                AND started_at >= CURRENT_DATE - INTERVAL '30 days'
            )
        WHERE id = NEW.template_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update template statistics
CREATE TRIGGER trigger_update_template_statistics
    AFTER UPDATE ON prompt_executions
    FOR EACH ROW
    EXECUTE FUNCTION update_template_statistics();

-- Function to clean up expired context data
CREATE OR REPLACE FUNCTION cleanup_expired_context_data()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM context_data
    WHERE expires_at < CURRENT_TIMESTAMP;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON TABLE prompt_templates IS 'Reusable prompt templates with variables and context requirements';
COMMENT ON TABLE prompt_executions IS 'Track prompt usage, performance, and effectiveness';
COMMENT ON TABLE context_sources IS 'Manage context data sources for prompt enhancement';
COMMENT ON TABLE context_data IS 'Cached context content with expiration and usage tracking';
COMMENT ON TABLE prompt_context_mappings IS 'Link prompt templates to context sources';
COMMENT ON TABLE prompt_feedback IS 'Collect user feedback on prompt effectiveness';
COMMENT ON TABLE prompt_variations IS 'A/B testing variations of prompt templates';

COMMENT ON VIEW template_performance IS 'Template usage statistics and performance metrics';
COMMENT ON VIEW context_source_usage IS 'Context source utilization and access patterns';
COMMENT ON VIEW execution_analytics IS 'Daily execution analytics for monitoring and optimization';

COMMENT ON FUNCTION calculate_template_effectiveness(UUID) IS 'Calculate effectiveness score based on success rate, ratings, and performance';
COMMENT ON FUNCTION update_template_statistics() IS 'Automatically update template statistics when executions complete';
COMMENT ON FUNCTION cleanup_expired_context_data() IS 'Remove expired context data to manage storage';

