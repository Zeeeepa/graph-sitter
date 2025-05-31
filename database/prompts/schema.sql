-- =====================================================
-- PROMPT MANAGEMENT DATABASE SCHEMA
-- AI prompt templates and optimization system
-- =====================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- =====================================================
-- ENUMS AND TYPES
-- =====================================================

-- Prompt category enumeration
CREATE TYPE prompt_category_enum AS ENUM (
    'code_generation',
    'code_review',
    'documentation',
    'testing',
    'refactoring',
    'debugging',
    'analysis',
    'explanation',
    'optimization',
    'security',
    'migration',
    'planning',
    'general'
);

-- Context type enumeration
CREATE TYPE context_type_enum AS ENUM (
    'file_analysis',
    'function_analysis',
    'class_analysis',
    'project_overview',
    'dependency_analysis',
    'error_debugging',
    'performance_optimization',
    'security_review',
    'code_migration',
    'api_documentation',
    'test_generation',
    'refactoring_suggestion'
);

-- Prompt status enumeration
CREATE TYPE prompt_status_enum AS ENUM (
    'draft',
    'active',
    'deprecated',
    'archived',
    'testing'
);

-- Quality rating enumeration
CREATE TYPE quality_rating_enum AS ENUM (
    'excellent',
    'good',
    'fair',
    'poor',
    'failed'
);

-- Model provider enumeration
CREATE TYPE model_provider_enum AS ENUM (
    'openai',
    'anthropic',
    'google',
    'microsoft',
    'meta',
    'cohere',
    'huggingface',
    'local',
    'other'
);

-- =====================================================
-- CORE TABLES
-- =====================================================

-- Prompt templates table
CREATE TABLE prompt_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    display_name VARCHAR(255),
    description TEXT,
    category prompt_category_enum NOT NULL,
    status prompt_status_enum DEFAULT 'draft',
    
    -- Template content
    template_content TEXT NOT NULL,
    system_prompt TEXT,
    user_prompt_template TEXT,
    
    -- Versioning
    version INTEGER DEFAULT 1,
    parent_template_id UUID REFERENCES prompt_templates(id),
    is_latest_version BOOLEAN DEFAULT TRUE,
    
    -- Configuration
    parameters JSONB,
    required_parameters TEXT[],
    optional_parameters TEXT[],
    default_values JSONB,
    
    -- Model configuration
    preferred_model_provider model_provider_enum,
    preferred_model_name VARCHAR(100),
    max_tokens INTEGER DEFAULT 4000,
    temperature DECIMAL(3,2) DEFAULT 0.7,
    top_p DECIMAL(3,2) DEFAULT 1.0,
    
    -- Usage constraints
    max_context_length INTEGER DEFAULT 8000,
    estimated_cost_per_use DECIMAL(8,4),
    rate_limit_per_hour INTEGER,
    
    -- Metadata
    tags TEXT[],
    author_id UUID,
    is_public BOOLEAN DEFAULT FALSE,
    usage_count INTEGER DEFAULT 0,
    success_rate DECIMAL(5,2) DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP,
    
    -- Constraints
    CONSTRAINT valid_temperature CHECK (temperature >= 0 AND temperature <= 2),
    CONSTRAINT valid_top_p CHECK (top_p >= 0 AND top_p <= 1),
    CONSTRAINT valid_success_rate CHECK (success_rate >= 0 AND success_rate <= 100)
);

-- Prompt contexts for context-aware selection
CREATE TABLE prompt_contexts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    context_type context_type_enum NOT NULL,
    context_name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Context data structure
    context_schema JSONB,
    example_context JSONB,
    
    -- Matching rules
    matching_rules JSONB,
    priority_score INTEGER DEFAULT 0,
    
    -- Associated templates
    recommended_template_id UUID REFERENCES prompt_templates(id),
    fallback_template_id UUID REFERENCES prompt_templates(id),
    
    -- Performance metrics
    match_accuracy DECIMAL(5,2) DEFAULT 0,
    usage_frequency INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(context_type, context_name)
);

-- Prompt usage tracking
CREATE TABLE prompt_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID REFERENCES prompt_templates(id) ON DELETE CASCADE,
    context_id UUID REFERENCES prompt_contexts(id),
    
    -- Request details
    session_id UUID,
    user_id UUID,
    request_id VARCHAR(255),
    
    -- Input data
    input_parameters JSONB,
    context_data JSONB,
    generated_prompt TEXT,
    
    -- Model configuration used
    model_provider model_provider_enum,
    model_name VARCHAR(100),
    actual_temperature DECIMAL(3,2),
    actual_max_tokens INTEGER,
    
    -- Response data
    response_content TEXT,
    response_metadata JSONB,
    
    -- Performance metrics
    execution_time_ms INTEGER,
    input_token_count INTEGER,
    output_token_count INTEGER,
    total_cost DECIMAL(10,6),
    
    -- Quality assessment
    quality_rating quality_rating_enum,
    quality_score DECIMAL(3,2),
    user_feedback_score INTEGER CHECK (user_feedback_score >= 1 AND user_feedback_score <= 5),
    
    -- Success indicators
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    error_type VARCHAR(100),
    
    -- Follow-up actions
    required_refinement BOOLEAN DEFAULT FALSE,
    refinement_reason TEXT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Prompt optimization experiments
CREATE TABLE prompt_experiments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Experiment configuration
    base_template_id UUID REFERENCES prompt_templates(id),
    variant_templates UUID[],
    test_contexts JSONB,
    
    -- Experiment parameters
    sample_size INTEGER DEFAULT 100,
    confidence_level DECIMAL(3,2) DEFAULT 0.95,
    significance_threshold DECIMAL(4,3) DEFAULT 0.05,
    
    -- Status and results
    status VARCHAR(50) DEFAULT 'planning',
    current_sample_count INTEGER DEFAULT 0,
    
    -- Performance comparison
    baseline_success_rate DECIMAL(5,2),
    baseline_avg_quality DECIMAL(3,2),
    baseline_avg_cost DECIMAL(8,4),
    
    -- Results
    winning_template_id UUID REFERENCES prompt_templates(id),
    improvement_percentage DECIMAL(5,2),
    statistical_significance DECIMAL(4,3),
    
    -- Metadata
    created_by UUID,
    
    -- Timestamps
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Prompt performance analytics
CREATE TABLE prompt_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID REFERENCES prompt_templates(id) ON DELETE CASCADE,
    
    -- Time period
    analysis_date DATE NOT NULL,
    analysis_period VARCHAR(20) DEFAULT 'daily', -- daily, weekly, monthly
    
    -- Usage statistics
    total_uses INTEGER DEFAULT 0,
    successful_uses INTEGER DEFAULT 0,
    failed_uses INTEGER DEFAULT 0,
    
    -- Performance metrics
    avg_execution_time_ms DECIMAL(10,2),
    avg_input_tokens DECIMAL(8,2),
    avg_output_tokens DECIMAL(8,2),
    total_cost DECIMAL(12,6),
    
    -- Quality metrics
    avg_quality_score DECIMAL(3,2),
    avg_user_feedback DECIMAL(3,2),
    quality_distribution JSONB,
    
    -- Error analysis
    error_rate DECIMAL(5,2),
    common_errors JSONB,
    
    -- Context analysis
    context_distribution JSONB,
    most_common_contexts TEXT[],
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(template_id, analysis_date, analysis_period)
);

-- Prompt feedback and ratings
CREATE TABLE prompt_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usage_id UUID REFERENCES prompt_usage(id) ON DELETE CASCADE,
    template_id UUID REFERENCES prompt_templates(id) ON DELETE CASCADE,
    
    -- Feedback details
    user_id UUID,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    feedback_text TEXT,
    
    -- Specific feedback categories
    clarity_rating INTEGER CHECK (clarity_rating >= 1 AND clarity_rating <= 5),
    accuracy_rating INTEGER CHECK (accuracy_rating >= 1 AND accuracy_rating <= 5),
    usefulness_rating INTEGER CHECK (usefulness_rating >= 1 AND usefulness_rating <= 5),
    
    -- Improvement suggestions
    suggested_improvements TEXT,
    would_recommend BOOLEAN,
    
    -- Metadata
    feedback_type VARCHAR(50) DEFAULT 'user_rating',
    is_verified BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dynamic prompt generation rules
CREATE TABLE prompt_generation_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    
    -- Rule configuration
    trigger_conditions JSONB,
    context_requirements JSONB,
    
    -- Generation logic
    template_selection_logic JSONB,
    parameter_mapping JSONB,
    content_transformation_rules JSONB,
    
    -- Priority and constraints
    priority INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Performance tracking
    application_count INTEGER DEFAULT 0,
    success_rate DECIMAL(5,2) DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_applied_at TIMESTAMP
);

-- Prompt template relationships
CREATE TABLE prompt_template_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_template_id UUID REFERENCES prompt_templates(id) ON DELETE CASCADE,
    target_template_id UUID REFERENCES prompt_templates(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) NOT NULL, -- extends, includes, follows, alternative
    
    -- Relationship metadata
    description TEXT,
    weight DECIMAL(3,2) DEFAULT 1.0,
    is_bidirectional BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Prevent self-relationships and duplicates
    CONSTRAINT no_self_relationship CHECK (source_template_id != target_template_id),
    CONSTRAINT unique_relationship UNIQUE(source_template_id, target_template_id, relationship_type)
);

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

-- Template indexes
CREATE INDEX idx_prompt_templates_category ON prompt_templates(category);
CREATE INDEX idx_prompt_templates_status ON prompt_templates(status);
CREATE INDEX idx_prompt_templates_version ON prompt_templates(version);
CREATE INDEX idx_prompt_templates_usage_count ON prompt_templates(usage_count);
CREATE INDEX idx_prompt_templates_success_rate ON prompt_templates(success_rate);

-- Context indexes
CREATE INDEX idx_prompt_contexts_type ON prompt_contexts(context_type);
CREATE INDEX idx_prompt_contexts_priority ON prompt_contexts(priority_score);

-- Usage indexes
CREATE INDEX idx_prompt_usage_template ON prompt_usage(template_id);
CREATE INDEX idx_prompt_usage_context ON prompt_usage(context_id);
CREATE INDEX idx_prompt_usage_created ON prompt_usage(created_at);
CREATE INDEX idx_prompt_usage_success ON prompt_usage(success);
CREATE INDEX idx_prompt_usage_quality ON prompt_usage(quality_rating);

-- Analytics indexes
CREATE INDEX idx_prompt_analytics_template ON prompt_analytics(template_id);
CREATE INDEX idx_prompt_analytics_date ON prompt_analytics(analysis_date);
CREATE INDEX idx_prompt_analytics_period ON prompt_analytics(analysis_period);

-- Feedback indexes
CREATE INDEX idx_prompt_feedback_template ON prompt_feedback(template_id);
CREATE INDEX idx_prompt_feedback_rating ON prompt_feedback(rating);
CREATE INDEX idx_prompt_feedback_created ON prompt_feedback(created_at);

-- Full-text search indexes
CREATE INDEX idx_prompt_templates_name_search ON prompt_templates USING gin(to_tsvector('english', name));
CREATE INDEX idx_prompt_templates_description_search ON prompt_templates USING gin(to_tsvector('english', description));
CREATE INDEX idx_prompt_feedback_text_search ON prompt_feedback USING gin(to_tsvector('english', feedback_text));

-- JSONB indexes
CREATE INDEX idx_prompt_templates_parameters ON prompt_templates USING gin(parameters);
CREATE INDEX idx_prompt_contexts_schema ON prompt_contexts USING gin(context_schema);
CREATE INDEX idx_prompt_usage_input_params ON prompt_usage USING gin(input_parameters);
CREATE INDEX idx_prompt_usage_context_data ON prompt_usage USING gin(context_data);

-- Composite indexes for common queries
CREATE INDEX idx_prompt_usage_template_success ON prompt_usage(template_id, success);
CREATE INDEX idx_prompt_templates_category_status ON prompt_templates(category, status);

-- =====================================================
-- TRIGGERS AND FUNCTIONS
-- =====================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at trigger
CREATE TRIGGER update_prompt_templates_updated_at BEFORE UPDATE ON prompt_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_prompt_contexts_updated_at BEFORE UPDATE ON prompt_contexts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_prompt_generation_rules_updated_at BEFORE UPDATE ON prompt_generation_rules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to update template usage statistics
CREATE OR REPLACE FUNCTION update_template_usage_stats()
RETURNS TRIGGER AS $$
BEGIN
    -- Update usage count and last used timestamp
    UPDATE prompt_templates 
    SET 
        usage_count = usage_count + 1,
        last_used_at = CURRENT_TIMESTAMP
    WHERE id = NEW.template_id;
    
    -- Update success rate if the usage is completed
    IF NEW.completed_at IS NOT NULL THEN
        UPDATE prompt_templates 
        SET success_rate = (
            SELECT 
                (COUNT(CASE WHEN success THEN 1 END) * 100.0 / COUNT(*))
            FROM prompt_usage 
            WHERE template_id = NEW.template_id 
                AND completed_at IS NOT NULL
        )
        WHERE id = NEW.template_id;
    END IF;
    
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_template_usage_stats_trigger
    AFTER INSERT OR UPDATE ON prompt_usage
    FOR EACH ROW EXECUTE FUNCTION update_template_usage_stats();

-- Function to automatically version templates
CREATE OR REPLACE FUNCTION version_template_on_update()
RETURNS TRIGGER AS $$
BEGIN
    -- If template content is being changed, create a new version
    IF OLD.template_content IS DISTINCT FROM NEW.template_content OR
       OLD.system_prompt IS DISTINCT FROM NEW.system_prompt THEN
        
        -- Mark old version as not latest
        UPDATE prompt_templates 
        SET is_latest_version = FALSE 
        WHERE id = OLD.id;
        
        -- Create new version
        INSERT INTO prompt_templates (
            name, display_name, description, category, status,
            template_content, system_prompt, user_prompt_template,
            version, parent_template_id, is_latest_version,
            parameters, required_parameters, optional_parameters, default_values,
            preferred_model_provider, preferred_model_name, max_tokens, temperature, top_p,
            max_context_length, estimated_cost_per_use, rate_limit_per_hour,
            tags, author_id, is_public
        ) VALUES (
            NEW.name, NEW.display_name, NEW.description, NEW.category, NEW.status,
            NEW.template_content, NEW.system_prompt, NEW.user_prompt_template,
            OLD.version + 1, OLD.id, TRUE,
            NEW.parameters, NEW.required_parameters, NEW.optional_parameters, NEW.default_values,
            NEW.preferred_model_provider, NEW.preferred_model_name, NEW.max_tokens, NEW.temperature, NEW.top_p,
            NEW.max_context_length, NEW.estimated_cost_per_use, NEW.rate_limit_per_hour,
            NEW.tags, NEW.author_id, NEW.is_public
        );
        
        -- Prevent the original update
        RETURN NULL;
    END IF;
    
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER version_template_on_update_trigger
    BEFORE UPDATE ON prompt_templates
    FOR EACH ROW EXECUTE FUNCTION version_template_on_update();

-- =====================================================
-- VIEWS FOR COMMON QUERIES
-- =====================================================

-- Template performance summary
CREATE VIEW template_performance_summary AS
SELECT 
    pt.id,
    pt.name,
    pt.category,
    pt.version,
    pt.usage_count,
    pt.success_rate,
    AVG(pu.quality_score) as avg_quality_score,
    AVG(pu.execution_time_ms) as avg_execution_time,
    AVG(pu.total_cost) as avg_cost_per_use,
    COUNT(pf.id) as feedback_count,
    AVG(pf.rating) as avg_user_rating,
    pt.last_used_at
FROM prompt_templates pt
LEFT JOIN prompt_usage pu ON pt.id = pu.template_id
LEFT JOIN prompt_feedback pf ON pt.id = pf.template_id
GROUP BY pt.id, pt.name, pt.category, pt.version, pt.usage_count, pt.success_rate, pt.last_used_at;

-- Context effectiveness analysis
CREATE VIEW context_effectiveness_analysis AS
SELECT 
    pc.id,
    pc.context_type,
    pc.context_name,
    pc.match_accuracy,
    COUNT(pu.id) as usage_count,
    AVG(pu.quality_score) as avg_quality,
    AVG(pu.execution_time_ms) as avg_execution_time,
    COUNT(CASE WHEN pu.success THEN 1 END) * 100.0 / COUNT(pu.id) as success_rate
FROM prompt_contexts pc
LEFT JOIN prompt_usage pu ON pc.id = pu.context_id
GROUP BY pc.id, pc.context_type, pc.context_name, pc.match_accuracy;

-- Daily usage analytics
CREATE VIEW daily_usage_analytics AS
SELECT 
    DATE(pu.created_at) as usage_date,
    COUNT(*) as total_uses,
    COUNT(CASE WHEN pu.success THEN 1 END) as successful_uses,
    AVG(pu.quality_score) as avg_quality,
    SUM(pu.total_cost) as total_cost,
    COUNT(DISTINCT pu.template_id) as unique_templates_used,
    COUNT(DISTINCT pu.user_id) as unique_users
FROM prompt_usage pu
GROUP BY DATE(pu.created_at)
ORDER BY usage_date DESC;

-- Template recommendation view
CREATE VIEW template_recommendations AS
SELECT 
    pt.id,
    pt.name,
    pt.category,
    pt.success_rate,
    AVG(pf.rating) as avg_rating,
    pt.usage_count,
    CASE 
        WHEN pt.success_rate >= 90 AND AVG(pf.rating) >= 4.0 THEN 'highly_recommended'
        WHEN pt.success_rate >= 80 AND AVG(pf.rating) >= 3.5 THEN 'recommended'
        WHEN pt.success_rate >= 70 AND AVG(pf.rating) >= 3.0 THEN 'acceptable'
        ELSE 'needs_improvement'
    END as recommendation_level
FROM prompt_templates pt
LEFT JOIN prompt_feedback pf ON pt.id = pf.template_id
WHERE pt.status = 'active' AND pt.is_latest_version = TRUE
GROUP BY pt.id, pt.name, pt.category, pt.success_rate, pt.usage_count
HAVING pt.usage_count >= 10; -- Only recommend templates with sufficient usage

-- =====================================================
-- ANALYTICAL FUNCTIONS
-- =====================================================

-- Function to get optimal template for context
CREATE OR REPLACE FUNCTION get_optimal_template(
    context_type_param context_type_enum,
    context_data_param JSONB DEFAULT '{}'::JSONB
)
RETURNS TABLE (
    template_id UUID,
    template_name VARCHAR,
    confidence_score DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        pt.id as template_id,
        pt.name as template_name,
        (pt.success_rate * 0.4 + 
         COALESCE(AVG(pf.rating) * 20, 0) * 0.3 + 
         pc.match_accuracy * 0.3) as confidence_score
    FROM prompt_templates pt
    LEFT JOIN prompt_contexts pc ON pt.id = pc.recommended_template_id
    LEFT JOIN prompt_feedback pf ON pt.id = pf.template_id
    WHERE pt.status = 'active' 
        AND pt.is_latest_version = TRUE
        AND (pc.context_type = context_type_param OR pc.context_type IS NULL)
    GROUP BY pt.id, pt.name, pt.success_rate, pc.match_accuracy
    ORDER BY confidence_score DESC
    LIMIT 5;
END;
$$ LANGUAGE plpgsql;

-- Function to analyze prompt performance trends
CREATE OR REPLACE FUNCTION analyze_prompt_trends(
    template_id_param UUID,
    days_back INTEGER DEFAULT 30
)
RETURNS TABLE (
    date DATE,
    usage_count INTEGER,
    success_rate DECIMAL,
    avg_quality DECIMAL,
    avg_cost DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        DATE(pu.created_at) as date,
        COUNT(*)::INTEGER as usage_count,
        (COUNT(CASE WHEN pu.success THEN 1 END) * 100.0 / COUNT(*))::DECIMAL as success_rate,
        AVG(pu.quality_score)::DECIMAL as avg_quality,
        AVG(pu.total_cost)::DECIMAL as avg_cost
    FROM prompt_usage pu
    WHERE pu.template_id = template_id_param
        AND pu.created_at >= CURRENT_DATE - INTERVAL '1 day' * days_back
    GROUP BY DATE(pu.created_at)
    ORDER BY date;
END;
$$ LANGUAGE plpgsql;

-- Function to identify underperforming templates
CREATE OR REPLACE FUNCTION identify_underperforming_templates()
RETURNS TABLE (
    template_id UUID,
    template_name VARCHAR,
    success_rate DECIMAL,
    avg_rating DECIMAL,
    usage_count INTEGER,
    issues TEXT[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        pt.id as template_id,
        pt.name as template_name,
        pt.success_rate,
        AVG(pf.rating) as avg_rating,
        pt.usage_count,
        ARRAY_REMOVE(ARRAY[
            CASE WHEN pt.success_rate < 70 THEN 'low_success_rate' END,
            CASE WHEN AVG(pf.rating) < 3.0 THEN 'poor_user_rating' END,
            CASE WHEN pt.usage_count > 50 AND pt.success_rate < 80 THEN 'high_usage_low_success' END,
            CASE WHEN AVG(pu.execution_time_ms) > 10000 THEN 'slow_execution' END
        ], NULL) as issues
    FROM prompt_templates pt
    LEFT JOIN prompt_feedback pf ON pt.id = pf.template_id
    LEFT JOIN prompt_usage pu ON pt.id = pu.template_id
    WHERE pt.status = 'active' AND pt.usage_count >= 10
    GROUP BY pt.id, pt.name, pt.success_rate, pt.usage_count
    HAVING pt.success_rate < 80 OR AVG(pf.rating) < 3.5 OR AVG(pu.execution_time_ms) > 8000
    ORDER BY pt.success_rate ASC, AVG(pf.rating) ASC;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- SAMPLE DATA FOR TESTING
-- =====================================================

-- Insert sample prompt templates
INSERT INTO prompt_templates (name, display_name, description, category, template_content, system_prompt) VALUES
('code_review_python', 'Python Code Review', 'Comprehensive Python code review template', 'code_review', 
 'Review the following Python code for:\n1. Code quality\n2. Best practices\n3. Potential bugs\n4. Performance issues\n\nCode:\n{code}\n\nFile: {file_path}',
 'You are an expert Python developer with 10+ years of experience. Provide thorough, constructive code reviews.'),

('function_documentation', 'Function Documentation Generator', 'Generate comprehensive function documentation', 'documentation',
 'Generate detailed documentation for this function:\n\n{function_code}\n\nInclude:\n- Purpose and description\n- Parameters with types\n- Return value\n- Usage examples\n- Edge cases',
 'You are a technical writer specializing in API documentation. Create clear, comprehensive documentation.'),

('bug_analysis', 'Bug Analysis and Fix', 'Analyze bugs and suggest fixes', 'debugging',
 'Analyze this bug report and code:\n\nError: {error_message}\nCode: {code}\nStack trace: {stack_trace}\n\nProvide:\n1. Root cause analysis\n2. Suggested fix\n3. Prevention strategies',
 'You are a senior software engineer expert in debugging and problem-solving.');

-- Insert sample contexts
INSERT INTO prompt_contexts (context_type, context_name, description, context_schema) VALUES
('function_analysis', 'Python Function Review', 'Context for reviewing Python functions', 
 '{"function_name": "string", "function_code": "string", "file_path": "string", "complexity_score": "number"}'),

('file_analysis', 'Full File Review', 'Context for reviewing entire files',
 '{"file_path": "string", "file_content": "string", "language": "string", "metrics": "object"}'),

('error_debugging', 'Error Analysis', 'Context for debugging errors',
 '{"error_message": "string", "stack_trace": "string", "code_snippet": "string", "environment": "object"}');

-- =====================================================
-- PERFORMANCE MONITORING
-- =====================================================

-- Function to generate daily analytics
CREATE OR REPLACE FUNCTION generate_daily_analytics(analysis_date DATE DEFAULT CURRENT_DATE)
RETURNS VOID AS $$
BEGIN
    INSERT INTO prompt_analytics (
        template_id, analysis_date, analysis_period,
        total_uses, successful_uses, failed_uses,
        avg_execution_time_ms, avg_input_tokens, avg_output_tokens, total_cost,
        avg_quality_score, avg_user_feedback, error_rate
    )
    SELECT 
        pu.template_id,
        analysis_date,
        'daily',
        COUNT(*),
        COUNT(CASE WHEN pu.success THEN 1 END),
        COUNT(CASE WHEN NOT pu.success THEN 1 END),
        AVG(pu.execution_time_ms),
        AVG(pu.input_token_count),
        AVG(pu.output_token_count),
        SUM(pu.total_cost),
        AVG(pu.quality_score),
        AVG(pf.rating),
        COUNT(CASE WHEN NOT pu.success THEN 1 END) * 100.0 / COUNT(*)
    FROM prompt_usage pu
    LEFT JOIN prompt_feedback pf ON pu.id = pf.usage_id
    WHERE DATE(pu.created_at) = analysis_date
    GROUP BY pu.template_id
    ON CONFLICT (template_id, analysis_date, analysis_period) 
    DO UPDATE SET
        total_uses = EXCLUDED.total_uses,
        successful_uses = EXCLUDED.successful_uses,
        failed_uses = EXCLUDED.failed_uses,
        avg_execution_time_ms = EXCLUDED.avg_execution_time_ms,
        avg_input_tokens = EXCLUDED.avg_input_tokens,
        avg_output_tokens = EXCLUDED.avg_output_tokens,
        total_cost = EXCLUDED.total_cost,
        avg_quality_score = EXCLUDED.avg_quality_score,
        avg_user_feedback = EXCLUDED.avg_user_feedback,
        error_rate = EXCLUDED.error_rate;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- COMMENTS AND DOCUMENTATION
-- =====================================================

COMMENT ON TABLE prompt_templates IS 'Core prompt templates with versioning and performance tracking';
COMMENT ON TABLE prompt_contexts IS 'Context definitions for intelligent prompt selection';
COMMENT ON TABLE prompt_usage IS 'Detailed tracking of every prompt execution';
COMMENT ON TABLE prompt_experiments IS 'A/B testing framework for prompt optimization';
COMMENT ON TABLE prompt_analytics IS 'Aggregated performance analytics for templates';
COMMENT ON TABLE prompt_feedback IS 'User feedback and ratings for continuous improvement';

COMMENT ON COLUMN prompt_templates.success_rate IS 'Calculated success rate based on usage history (0-100%)';
COMMENT ON COLUMN prompt_usage.quality_score IS 'Automated quality assessment score (0-1)';
COMMENT ON COLUMN prompt_experiments.statistical_significance IS 'P-value for experiment results';
COMMENT ON COLUMN prompt_contexts.match_accuracy IS 'Accuracy of context matching algorithm (0-100%)';

-- =====================================================
-- GRANTS AND PERMISSIONS
-- =====================================================

-- Create roles for different access levels
-- CREATE ROLE prompt_admin;
-- CREATE ROLE prompt_manager;
-- CREATE ROLE prompt_user;
-- CREATE ROLE prompt_viewer;

-- Grant appropriate permissions
-- GRANT ALL ON ALL TABLES IN SCHEMA public TO prompt_admin;
-- GRANT SELECT, INSERT, UPDATE ON prompt_templates, prompt_usage, prompt_feedback TO prompt_user;
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO prompt_viewer;

