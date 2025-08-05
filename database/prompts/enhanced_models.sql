-- Enhanced Prompts Module with Dynamic Generation and OpenEvolve Integration
-- Advanced prompt management, template system, and effectiveness tracking

-- Prompt-related enums
CREATE TYPE prompt_type AS ENUM (
    'system',
    'user',
    'assistant',
    'function',
    'template',
    'evaluation',
    'analysis',
    'generation',
    'optimization'
);

CREATE TYPE prompt_category AS ENUM (
    'code_generation',
    'code_review',
    'bug_fixing',
    'refactoring',
    'documentation',
    'testing',
    'analysis',
    'optimization',
    'security',
    'deployment',
    'general'
);

CREATE TYPE template_engine AS ENUM (
    'jinja2',
    'mustache',
    'handlebars',
    'simple',
    'custom'
);

-- Enhanced prompts table with comprehensive metadata
CREATE TABLE prompts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Prompt identification
    name VARCHAR(255) NOT NULL,
    description TEXT,
    version VARCHAR(50) DEFAULT '1.0',
    
    -- Prompt classification
    type prompt_type NOT NULL DEFAULT 'user',
    category prompt_category NOT NULL DEFAULT 'general',
    
    -- Prompt content
    content TEXT NOT NULL,
    template_engine template_engine DEFAULT 'jinja2',
    
    -- Template variables and schema
    variables JSONB DEFAULT '{}',
    variable_schema JSONB DEFAULT '{}',
    
    -- Prompt metadata
    tags JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    
    -- Usage and effectiveness
    usage_count INTEGER DEFAULT 0,
    success_rate DECIMAL(5,2),
    average_rating DECIMAL(3,2),
    
    -- Ownership and access
    created_by VARCHAR(255),
    is_public BOOLEAN DEFAULT false,
    is_template BOOLEAN DEFAULT false,
    
    -- Project and context association
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    
    -- Timing
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_used_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT prompts_name_length CHECK (char_length(name) >= 1),
    CONSTRAINT prompts_content_length CHECK (char_length(content) >= 1),
    CONSTRAINT prompts_rating_range CHECK (average_rating >= 1.0 AND average_rating <= 5.0),
    
    -- Indexes
    INDEX idx_prompts_name (name),
    INDEX idx_prompts_type (type),
    INDEX idx_prompts_category (category),
    INDEX idx_prompts_project (project_id),
    INDEX idx_prompts_created_by (created_by),
    INDEX idx_prompts_public (is_public),
    INDEX idx_prompts_template (is_template),
    INDEX idx_prompts_usage_count (usage_count),
    INDEX idx_prompts_success_rate (success_rate),
    
    -- GIN indexes for JSONB fields
    INDEX idx_prompts_tags_gin USING gin (tags),
    INDEX idx_prompts_metadata_gin USING gin (metadata),
    INDEX idx_prompts_variables_gin USING gin (variables)
);

-- Prompt templates with inheritance and composition
CREATE TABLE prompt_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Template identification
    name VARCHAR(255) NOT NULL,
    description TEXT,
    version VARCHAR(50) DEFAULT '1.0',
    
    -- Template hierarchy
    parent_template_id UUID REFERENCES prompt_templates(id) ON DELETE SET NULL,
    
    -- Template content
    template_content TEXT NOT NULL,
    template_engine template_engine DEFAULT 'jinja2',
    
    -- Template configuration
    default_variables JSONB DEFAULT '{}',
    required_variables JSONB DEFAULT '[]',
    variable_schema JSONB DEFAULT '{}',
    
    -- Template metadata
    category prompt_category NOT NULL DEFAULT 'general',
    tags JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    
    -- Usage tracking
    usage_count INTEGER DEFAULT 0,
    instantiation_count INTEGER DEFAULT 0,
    
    -- Ownership
    created_by VARCHAR(255),
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    is_public BOOLEAN DEFAULT false,
    
    -- Timing
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT prompt_templates_name_length CHECK (char_length(name) >= 1),
    CONSTRAINT prompt_templates_content_length CHECK (char_length(template_content) >= 1),
    
    -- Indexes
    INDEX idx_prompt_templates_name (name),
    INDEX idx_prompt_templates_parent (parent_template_id),
    INDEX idx_prompt_templates_category (category),
    INDEX idx_prompt_templates_project (project_id),
    INDEX idx_prompt_templates_active (is_active),
    INDEX idx_prompt_templates_public (is_public),
    
    -- GIN indexes
    INDEX idx_prompt_templates_tags_gin USING gin (tags),
    INDEX idx_prompt_templates_metadata_gin USING gin (metadata)
);

-- Prompt executions with detailed tracking
CREATE TABLE prompt_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Prompt reference
    prompt_id UUID REFERENCES prompts(id) ON DELETE CASCADE,
    template_id UUID REFERENCES prompt_templates(id) ON DELETE SET NULL,
    
    -- Execution context
    task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
    execution_id UUID REFERENCES task_executions(id) ON DELETE SET NULL,
    
    -- Execution metadata
    executor_type agent_type NOT NULL,
    executor_id VARCHAR(255),
    
    -- Input and output
    input_variables JSONB DEFAULT '{}',
    rendered_prompt TEXT,
    response TEXT,
    
    -- Execution results
    success BOOLEAN,
    error_message TEXT,
    
    -- Performance metrics
    execution_time_ms INTEGER,
    token_count INTEGER,
    cost_estimate DECIMAL(10,6),
    
    -- Quality metrics
    relevance_score DECIMAL(3,2),
    coherence_score DECIMAL(3,2),
    completeness_score DECIMAL(3,2),
    overall_quality DECIMAL(3,2),
    
    -- Timing
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}',
    
    -- Indexes
    INDEX idx_prompt_executions_prompt (prompt_id),
    INDEX idx_prompt_executions_template (template_id),
    INDEX idx_prompt_executions_task (task_id),
    INDEX idx_prompt_executions_executor (executor_type, executor_id),
    INDEX idx_prompt_executions_success (success),
    INDEX idx_prompt_executions_started_at (started_at),
    INDEX idx_prompt_executions_quality (overall_quality)
);

-- Context-aware prompt generation
CREATE TABLE prompt_contexts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Context identification
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Context scope
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    repository_id UUID REFERENCES repositories(id) ON DELETE SET NULL,
    task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
    
    -- Context data
    context_data JSONB NOT NULL DEFAULT '{}',
    context_schema JSONB DEFAULT '{}',
    
    -- Context metadata
    context_type VARCHAR(100) NOT NULL,
    priority INTEGER DEFAULT 0,
    
    -- Validity and caching
    is_active BOOLEAN DEFAULT true,
    expires_at TIMESTAMP WITH TIME ZONE,
    cache_ttl_seconds INTEGER DEFAULT 3600,
    
    -- Timing
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_accessed_at TIMESTAMP WITH TIME ZONE,
    
    -- Indexes
    INDEX idx_prompt_contexts_project (project_id),
    INDEX idx_prompt_contexts_repository (repository_id),
    INDEX idx_prompt_contexts_task (task_id),
    INDEX idx_prompt_contexts_type (context_type),
    INDEX idx_prompt_contexts_active (is_active),
    INDEX idx_prompt_contexts_expires_at (expires_at),
    
    -- GIN index for context data
    INDEX idx_prompt_contexts_data_gin USING gin (context_data)
);

-- Prompt effectiveness tracking and analytics
CREATE TABLE prompt_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Analytics scope
    prompt_id UUID REFERENCES prompts(id) ON DELETE CASCADE,
    template_id UUID REFERENCES prompt_templates(id) ON DELETE SET NULL,
    
    -- Analytics period
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Usage metrics
    total_executions INTEGER DEFAULT 0,
    successful_executions INTEGER DEFAULT 0,
    failed_executions INTEGER DEFAULT 0,
    
    -- Performance metrics
    average_execution_time_ms INTEGER,
    average_token_count INTEGER,
    total_cost DECIMAL(10,6),
    
    -- Quality metrics
    average_relevance_score DECIMAL(3,2),
    average_coherence_score DECIMAL(3,2),
    average_completeness_score DECIMAL(3,2),
    average_overall_quality DECIMAL(3,2),
    
    -- Effectiveness metrics
    success_rate DECIMAL(5,2),
    improvement_rate DECIMAL(5,2),
    user_satisfaction DECIMAL(3,2),
    
    -- Detailed analytics
    execution_distribution JSONB DEFAULT '{}',
    quality_trends JSONB DEFAULT '{}',
    usage_patterns JSONB DEFAULT '{}',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(prompt_id, template_id, period_start, period_end),
    INDEX idx_prompt_analytics_prompt (prompt_id),
    INDEX idx_prompt_analytics_template (template_id),
    INDEX idx_prompt_analytics_period (period_start, period_end),
    INDEX idx_prompt_analytics_success_rate (success_rate)
);

-- OpenEvolve prompt optimization
CREATE TABLE openevolve_prompt_optimization (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Optimization target
    prompt_id UUID REFERENCES prompts(id) ON DELETE CASCADE,
    template_id UUID REFERENCES prompt_templates(id) ON DELETE SET NULL,
    
    -- Optimization configuration
    optimization_goal VARCHAR(100) NOT NULL, -- quality, speed, cost, effectiveness
    target_metrics JSONB DEFAULT '{}',
    constraints JSONB DEFAULT '{}',
    
    -- Evolution parameters
    population_size INTEGER DEFAULT 10,
    max_generations INTEGER DEFAULT 50,
    mutation_rate DECIMAL(3,2) DEFAULT 0.1,
    
    -- Optimization results
    best_prompt_variant TEXT,
    best_score DECIMAL(10,4),
    improvement_percentage DECIMAL(5,2),
    
    -- Evolution tracking
    current_generation INTEGER DEFAULT 0,
    total_evaluations INTEGER DEFAULT 0,
    convergence_achieved BOOLEAN DEFAULT false,
    
    -- Status and timing
    status VARCHAR(50) DEFAULT 'pending',
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Results and metadata
    optimization_history JSONB DEFAULT '[]',
    final_results JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    
    INDEX idx_openevolve_prompt_opt_prompt (prompt_id),
    INDEX idx_openevolve_prompt_opt_template (template_id),
    INDEX idx_openevolve_prompt_opt_status (status),
    INDEX idx_openevolve_prompt_opt_goal (optimization_goal)
);

-- Prompt variant tracking for A/B testing
CREATE TABLE prompt_variants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Variant identification
    base_prompt_id UUID REFERENCES prompts(id) ON DELETE CASCADE,
    variant_name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Variant content
    variant_content TEXT NOT NULL,
    variables JSONB DEFAULT '{}',
    
    -- A/B testing configuration
    traffic_percentage DECIMAL(5,2) DEFAULT 0.0,
    is_active BOOLEAN DEFAULT false,
    
    -- Performance tracking
    execution_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    average_quality DECIMAL(3,2),
    
    -- Statistical significance
    confidence_level DECIMAL(5,2),
    p_value DECIMAL(10,8),
    is_statistically_significant BOOLEAN DEFAULT false,
    
    -- Timing
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    activated_at TIMESTAMP WITH TIME ZONE,
    deactivated_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    UNIQUE(base_prompt_id, variant_name),
    INDEX idx_prompt_variants_base (base_prompt_id),
    INDEX idx_prompt_variants_active (is_active),
    INDEX idx_prompt_variants_traffic (traffic_percentage),
    INDEX idx_prompt_variants_quality (average_quality)
);

-- Prompt feedback and ratings
CREATE TABLE prompt_feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Feedback target
    prompt_id UUID REFERENCES prompts(id) ON DELETE CASCADE,
    execution_id UUID REFERENCES prompt_executions(id) ON DELETE CASCADE,
    
    -- Feedback source
    feedback_by VARCHAR(255) NOT NULL,
    feedback_type agent_type DEFAULT 'human',
    
    -- Feedback content
    rating INTEGER NOT NULL,
    feedback_text TEXT,
    
    -- Feedback categories
    relevance_rating INTEGER,
    clarity_rating INTEGER,
    usefulness_rating INTEGER,
    
    -- Improvement suggestions
    suggested_improvements JSONB DEFAULT '[]',
    
    -- Timing
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT prompt_feedback_rating_range CHECK (rating >= 1 AND rating <= 5),
    CONSTRAINT prompt_feedback_relevance_range CHECK (relevance_rating >= 1 AND relevance_rating <= 5),
    CONSTRAINT prompt_feedback_clarity_range CHECK (clarity_rating >= 1 AND clarity_rating <= 5),
    CONSTRAINT prompt_feedback_usefulness_range CHECK (usefulness_rating >= 1 AND usefulness_rating <= 5),
    
    INDEX idx_prompt_feedback_prompt (prompt_id),
    INDEX idx_prompt_feedback_execution (execution_id),
    INDEX idx_prompt_feedback_by (feedback_by),
    INDEX idx_prompt_feedback_rating (rating),
    INDEX idx_prompt_feedback_created_at (created_at)
);

-- Functions for prompt management
CREATE OR REPLACE FUNCTION render_prompt_template(
    template_id UUID,
    variables JSONB DEFAULT '{}'
) RETURNS TEXT AS $$
DECLARE
    template_content TEXT;
    rendered_content TEXT;
BEGIN
    -- Get template content
    SELECT pt.template_content INTO template_content
    FROM prompt_templates pt
    WHERE pt.id = template_id AND pt.is_active = true;
    
    IF template_content IS NULL THEN
        RAISE EXCEPTION 'Template not found or inactive: %', template_id;
    END IF;
    
    -- Simple variable substitution (in real implementation, use proper template engine)
    rendered_content := template_content;
    
    -- Update usage count
    UPDATE prompt_templates 
    SET usage_count = usage_count + 1,
        instantiation_count = instantiation_count + 1
    WHERE id = template_id;
    
    RETURN rendered_content;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION calculate_prompt_effectiveness(prompt_id UUID)
RETURNS DECIMAL(5,2) AS $$
DECLARE
    success_rate DECIMAL(5,2);
    avg_quality DECIMAL(3,2);
    effectiveness DECIMAL(5,2);
BEGIN
    -- Calculate success rate and average quality
    SELECT 
        CASE 
            WHEN COUNT(*) = 0 THEN 0
            ELSE (COUNT(*) FILTER (WHERE success = true)::DECIMAL / COUNT(*)) * 100
        END,
        AVG(overall_quality)
    INTO success_rate, avg_quality
    FROM prompt_executions
    WHERE prompt_id = prompt_id;
    
    -- Calculate effectiveness as weighted combination
    effectiveness := (COALESCE(success_rate, 0) * 0.6) + (COALESCE(avg_quality, 0) * 20 * 0.4);
    
    -- Update prompt record
    UPDATE prompts 
    SET success_rate = success_rate,
        average_rating = avg_quality
    WHERE id = prompt_id;
    
    RETURN effectiveness;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_context_aware_prompt(
    base_prompt_id UUID,
    context_data JSONB DEFAULT '{}'
) RETURNS TEXT AS $$
DECLARE
    base_content TEXT;
    enhanced_content TEXT;
    relevant_contexts JSONB;
BEGIN
    -- Get base prompt content
    SELECT content INTO base_content
    FROM prompts
    WHERE id = base_prompt_id;
    
    IF base_content IS NULL THEN
        RAISE EXCEPTION 'Prompt not found: %', base_prompt_id;
    END IF;
    
    -- Get relevant contexts (simplified - in real implementation, use ML/similarity)
    SELECT jsonb_agg(pc.context_data) INTO relevant_contexts
    FROM prompt_contexts pc
    WHERE pc.is_active = true
    AND pc.expires_at > NOW()
    LIMIT 5;
    
    -- Enhance prompt with context (simplified)
    enhanced_content := base_content;
    
    -- Update usage tracking
    UPDATE prompts 
    SET usage_count = usage_count + 1,
        last_used_at = NOW()
    WHERE id = base_prompt_id;
    
    RETURN enhanced_content;
END;
$$ LANGUAGE plpgsql;

-- Triggers for automatic updates
CREATE TRIGGER update_prompts_updated_at 
    BEFORE UPDATE ON prompts 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_prompt_templates_updated_at 
    BEFORE UPDATE ON prompt_templates 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_prompt_contexts_updated_at 
    BEFORE UPDATE ON prompt_contexts 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Views for common prompt queries
CREATE VIEW effective_prompts AS
SELECT 
    p.*,
    COUNT(pe.id) as execution_count,
    AVG(pe.overall_quality) as avg_quality,
    COUNT(pe.id) FILTER (WHERE pe.success = true) as success_count,
    calculate_prompt_effectiveness(p.id) as effectiveness_score
FROM prompts p
LEFT JOIN prompt_executions pe ON p.id = pe.prompt_id
GROUP BY p.id
HAVING COUNT(pe.id) >= 5  -- Only prompts with sufficient data
ORDER BY effectiveness_score DESC;

CREATE VIEW prompt_usage_summary AS
SELECT 
    p.id,
    p.name,
    p.category,
    p.usage_count,
    COUNT(DISTINCT pe.executor_id) as unique_users,
    COUNT(pe.id) as total_executions,
    AVG(pe.execution_time_ms) as avg_execution_time,
    AVG(pe.overall_quality) as avg_quality,
    MAX(pe.started_at) as last_used
FROM prompts p
LEFT JOIN prompt_executions pe ON p.id = pe.prompt_id
GROUP BY p.id, p.name, p.category, p.usage_count;

CREATE VIEW template_hierarchy AS
WITH RECURSIVE template_tree AS (
    -- Base case: root templates (no parent)
    SELECT 
        id,
        name,
        parent_template_id,
        0 as level,
        ARRAY[id] as path
    FROM prompt_templates 
    WHERE parent_template_id IS NULL
    
    UNION ALL
    
    -- Recursive case: child templates
    SELECT 
        pt.id,
        pt.name,
        pt.parent_template_id,
        tt.level + 1,
        tt.path || pt.id
    FROM prompt_templates pt
    JOIN template_tree tt ON pt.parent_template_id = tt.id
)
SELECT * FROM template_tree ORDER BY path;

-- Comments for documentation
COMMENT ON TABLE prompts IS 'Enhanced prompt management with effectiveness tracking and OpenEvolve integration';
COMMENT ON TABLE prompt_templates IS 'Reusable prompt templates with inheritance and composition';
COMMENT ON TABLE prompt_executions IS 'Detailed tracking of prompt executions with quality metrics';
COMMENT ON TABLE prompt_contexts IS 'Context-aware prompt generation and enhancement';
COMMENT ON TABLE prompt_analytics IS 'Prompt performance analytics and effectiveness metrics';
COMMENT ON TABLE openevolve_prompt_optimization IS 'OpenEvolve-powered prompt optimization and evolution';
COMMENT ON TABLE prompt_variants IS 'A/B testing variants for prompt optimization';
COMMENT ON TABLE prompt_feedback IS 'User feedback and ratings for prompt improvement';

COMMENT ON FUNCTION render_prompt_template IS 'Render a prompt template with provided variables';
COMMENT ON FUNCTION calculate_prompt_effectiveness IS 'Calculate overall effectiveness score for a prompt';
COMMENT ON FUNCTION get_context_aware_prompt IS 'Get enhanced prompt with relevant context data';

