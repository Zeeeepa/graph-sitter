-- =============================================================================
-- ENHANCED PROMPTS DATABASE SCHEMA: Codegen SDK Integration & Prompt Enhancement
-- =============================================================================
-- This database handles template management, conditional prompts, A/B testing,
-- and effectiveness tracking with specific focus on Codegen SDK integration
-- and accurate, factual prompting for workflow orchestration.
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

-- Enhanced prompt-specific enums
CREATE TYPE prompt_type AS ENUM (
    'system',
    'user',
    'assistant',
    'function',
    'template',
    'conditional',
    'codegen_workflow',
    'requirement_decomposition',
    'code_analysis',
    'pr_validation'
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
    'github_project',
    'linear_issue',
    'workflow_state',
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

CREATE TYPE enhancement_type AS ENUM (
    'context_injection',
    'accuracy_boost',
    'format_optimization',
    'workflow_specific',
    'error_reduction',
    'response_quality'
);

-- =============================================================================
-- CORE REFERENCE TABLES
-- =============================================================================

-- Organizations with Codegen SDK integration
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    
    -- Codegen SDK configuration
    codegen_org_id VARCHAR(255),
    codegen_api_token_encrypted TEXT,
    default_model VARCHAR(100) DEFAULT 'claude-3-sonnet',
    
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
-- ENHANCED PROMPT TEMPLATES FOR WORKFLOW INTEGRATION
-- =============================================================================

-- Main prompt templates with workflow-specific enhancements
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
    
    -- Workflow integration
    workflow_stage VARCHAR(100), -- project_selection, requirement_decomposition, etc.
    use_case VARCHAR(100), -- github_analysis, linear_creation, pr_validation
    
    -- Template configuration
    status template_status DEFAULT 'draft',
    version INTEGER DEFAULT 1,
    is_default BOOLEAN DEFAULT false,
    
    -- Template structure
    variables JSONB DEFAULT '[]',
    required_variables JSONB DEFAULT '[]',
    conditions JSONB DEFAULT '{}',
    fallback_template_id UUID REFERENCES prompt_templates(id),
    
    -- Enhancement configuration
    enhancement_rules JSONB DEFAULT '{}',
    context_injection_rules JSONB DEFAULT '{}',
    accuracy_boosters JSONB DEFAULT '[]',
    
    -- Usage and effectiveness
    usage_count INTEGER DEFAULT 0,
    success_rate DECIMAL(5,2) DEFAULT 0,
    average_rating DECIMAL(3,2) DEFAULT 0,
    
    -- Codegen SDK specific
    codegen_model_config JSONB DEFAULT '{}',
    max_tokens INTEGER DEFAULT 4000,
    temperature DECIMAL(3,2) DEFAULT 0.7,
    
    -- Quality metrics
    accuracy_score DECIMAL(5,2),
    factual_accuracy_score DECIMAL(5,2),
    response_quality_score DECIMAL(5,2),
    
    -- Template metadata
    category VARCHAR(100),
    tags VARCHAR(50)[],
    
    -- Validation and constraints
    validation_rules JSONB DEFAULT '{}',
    output_format_rules JSONB DEFAULT '{}',
    
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
    CONSTRAINT prompt_templates_rating_valid CHECK (average_rating >= 0 AND average_rating <= 5),
    CONSTRAINT prompt_templates_scores_valid CHECK (
        accuracy_score >= 0 AND accuracy_score <= 100 AND
        factual_accuracy_score >= 0 AND factual_accuracy_score <= 100 AND
        response_quality_score >= 0 AND response_quality_score <= 100
    )
);

-- =============================================================================
-- PROMPT ENHANCEMENT SYSTEM
-- =============================================================================

-- Prompt enhancement rules for improving accuracy and effectiveness
CREATE TABLE prompt_enhancements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Enhancement identification
    name VARCHAR(255) NOT NULL,
    enhancement_type enhancement_type NOT NULL,
    description TEXT,
    
    -- Enhancement configuration
    enhancement_rules JSONB DEFAULT '{}',
    trigger_conditions JSONB DEFAULT '{}',
    application_order INTEGER DEFAULT 1,
    
    -- Context-specific enhancements
    workflow_stage_specific VARCHAR(100),
    prompt_type_specific prompt_type,
    
    -- Enhancement content
    context_injection_template TEXT,
    accuracy_instructions TEXT,
    format_requirements TEXT,
    
    -- Effectiveness tracking
    usage_count INTEGER DEFAULT 0,
    success_rate DECIMAL(5,2) DEFAULT 0,
    improvement_score DECIMAL(5,2) DEFAULT 0,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT prompt_enhancements_name_org_unique UNIQUE (organization_id, name),
    CONSTRAINT prompt_enhancements_success_rate_valid CHECK (success_rate >= 0 AND success_rate <= 100),
    CONSTRAINT prompt_enhancements_improvement_valid CHECK (improvement_score >= -100 AND improvement_score <= 100)
);

-- =============================================================================
-- CODEGEN SDK EXECUTION TRACKING
-- =============================================================================

-- Enhanced executions for Codegen SDK integration
CREATE TABLE executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    template_id UUID REFERENCES prompt_templates(id),
    
    -- Execution identification
    execution_name VARCHAR(255),
    session_id UUID,
    
    -- Workflow context
    workflow_stage VARCHAR(100),
    github_project_id UUID,
    task_id UUID,
    
    -- Execution details
    status execution_status DEFAULT 'pending',
    prompt_type prompt_type NOT NULL,
    
    -- Prompt content and enhancement
    original_prompt TEXT NOT NULL,
    enhanced_prompt TEXT,
    enhancements_applied JSONB DEFAULT '[]',
    variables_used JSONB DEFAULT '{}',
    
    -- Codegen SDK specific
    codegen_org_id VARCHAR(255),
    codegen_task_id VARCHAR(255),
    codegen_model_used VARCHAR(100),
    codegen_config JSONB DEFAULT '{}',
    
    -- Timing and performance
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER,
    
    -- Token usage
    input_tokens INTEGER,
    output_tokens INTEGER,
    total_tokens INTEGER,
    
    -- Response and results
    response_content TEXT,
    response_metadata JSONB DEFAULT '{}',
    parsed_response JSONB DEFAULT '{}',
    
    -- Quality and effectiveness
    effectiveness_rating effectiveness_rating,
    quality_score DECIMAL(5,2),
    accuracy_score DECIMAL(5,2),
    factual_accuracy_verified BOOLEAN DEFAULT false,
    user_feedback TEXT,
    
    -- Error handling
    error_message TEXT,
    error_code VARCHAR(50),
    retry_count INTEGER DEFAULT 0,
    
    -- Cost tracking
    cost_usd DECIMAL(10,6),
    
    -- Context and environment
    execution_context JSONB DEFAULT '{}',
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
    CONSTRAINT executions_scores_valid CHECK (
        quality_score >= 0 AND quality_score <= 100 AND
        accuracy_score >= 0 AND accuracy_score <= 100
    ),
    CONSTRAINT executions_cost_positive CHECK (cost_usd >= 0)
);

-- =============================================================================
-- WORKFLOW-SPECIFIC CONTEXT SOURCES
-- =============================================================================

-- Enhanced context sources for workflow integration
CREATE TABLE context_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Source identification
    name VARCHAR(255) NOT NULL,
    description TEXT,
    context_type context_type NOT NULL,
    
    -- Workflow integration
    workflow_stage VARCHAR(100),
    applicable_prompt_types prompt_type[],
    
    -- Source configuration
    source_config JSONB DEFAULT '{}',
    access_config JSONB DEFAULT '{}',
    
    -- Content and metadata
    content TEXT,
    content_hash VARCHAR(64),
    content_size_bytes INTEGER,
    
    -- GitHub project context
    github_repo_url TEXT,
    github_branch VARCHAR(255),
    file_patterns JSONB DEFAULT '[]',
    
    -- Dynamic content
    is_dynamic BOOLEAN DEFAULT false,
    refresh_interval_minutes INTEGER,
    
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

-- =============================================================================
-- WORKFLOW-SPECIFIC PROMPT COLLECTIONS
-- =============================================================================

-- Prompt collections for complete workflow orchestration
CREATE TABLE prompt_collections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Collection identification
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Workflow integration
    workflow_type VARCHAR(100) NOT NULL, -- github_project_workflow, requirement_decomposition
    
    -- Collection configuration
    execution_order JSONB DEFAULT '[]', -- Array of template IDs in order
    conditional_logic JSONB DEFAULT '{}',
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    version INTEGER DEFAULT 1,
    
    -- Usage tracking
    usage_count INTEGER DEFAULT 0,
    success_rate DECIMAL(5,2) DEFAULT 0,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT prompt_collections_name_org_unique UNIQUE (organization_id, name),
    CONSTRAINT prompt_collections_success_rate_valid CHECK (success_rate >= 0 AND success_rate <= 100)
);

-- Collection templates mapping
CREATE TABLE collection_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    collection_id UUID NOT NULL REFERENCES prompt_collections(id) ON DELETE CASCADE,
    template_id UUID NOT NULL REFERENCES prompt_templates(id) ON DELETE CASCADE,
    
    -- Execution details
    execution_order INTEGER NOT NULL,
    is_conditional BOOLEAN DEFAULT false,
    conditions JSONB DEFAULT '{}',
    
    -- Configuration overrides
    config_overrides JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT collection_templates_unique UNIQUE (collection_id, template_id),
    CONSTRAINT collection_templates_order_positive CHECK (execution_order > 0)
);

-- =============================================================================
-- INDEXES FOR OPTIMAL PERFORMANCE
-- =============================================================================

-- Prompt templates indexes
CREATE INDEX idx_prompt_templates_org_id ON prompt_templates(organization_id);
CREATE INDEX idx_prompt_templates_status ON prompt_templates(status);
CREATE INDEX idx_prompt_templates_type ON prompt_templates(prompt_type);
CREATE INDEX idx_prompt_templates_workflow_stage ON prompt_templates(workflow_stage);
CREATE INDEX idx_prompt_templates_use_case ON prompt_templates(use_case);
CREATE INDEX idx_prompt_templates_usage_count ON prompt_templates(usage_count DESC);
CREATE INDEX idx_prompt_templates_success_rate ON prompt_templates(success_rate DESC);

-- Prompt enhancements indexes
CREATE INDEX idx_prompt_enhancements_org_id ON prompt_enhancements(organization_id);
CREATE INDEX idx_prompt_enhancements_type ON prompt_enhancements(enhancement_type);
CREATE INDEX idx_prompt_enhancements_active ON prompt_enhancements(is_active);
CREATE INDEX idx_prompt_enhancements_workflow_stage ON prompt_enhancements(workflow_stage_specific);

-- Executions indexes
CREATE INDEX idx_executions_org_id ON executions(organization_id);
CREATE INDEX idx_executions_template_id ON executions(template_id);
CREATE INDEX idx_executions_status ON executions(status);
CREATE INDEX idx_executions_workflow_stage ON executions(workflow_stage);
CREATE INDEX idx_executions_github_project_id ON executions(github_project_id);
CREATE INDEX idx_executions_codegen_task_id ON executions(codegen_task_id);
CREATE INDEX idx_executions_started_at ON executions(started_at);
CREATE INDEX idx_executions_effectiveness ON executions(effectiveness_rating);

-- Context sources indexes
CREATE INDEX idx_context_sources_org_id ON context_sources(organization_id);
CREATE INDEX idx_context_sources_type ON context_sources(context_type);
CREATE INDEX idx_context_sources_workflow_stage ON context_sources(workflow_stage);
CREATE INDEX idx_context_sources_active ON context_sources(is_active);

-- Prompt collections indexes
CREATE INDEX idx_prompt_collections_org_id ON prompt_collections(organization_id);
CREATE INDEX idx_prompt_collections_workflow_type ON prompt_collections(workflow_type);
CREATE INDEX idx_prompt_collections_active ON prompt_collections(is_active);

-- Collection templates indexes
CREATE INDEX idx_collection_templates_collection_id ON collection_templates(collection_id);
CREATE INDEX idx_collection_templates_template_id ON collection_templates(template_id);
CREATE INDEX idx_collection_templates_order ON collection_templates(execution_order);

-- GIN indexes for JSONB fields
CREATE INDEX idx_prompt_templates_variables_gin USING gin (variables);
CREATE INDEX idx_prompt_templates_enhancement_rules_gin USING gin (enhancement_rules);
CREATE INDEX idx_executions_variables_gin USING gin (variables_used);
CREATE INDEX idx_executions_response_gin USING gin (parsed_response);
CREATE INDEX idx_context_sources_config_gin USING gin (source_config);

-- =============================================================================
-- VIEWS FOR WORKFLOW ANALYTICS
-- =============================================================================

-- Workflow prompt effectiveness
CREATE VIEW workflow_prompt_effectiveness AS
SELECT 
    pt.workflow_stage,
    pt.use_case,
    COUNT(e.id) as total_executions,
    COUNT(CASE WHEN e.status = 'completed' THEN 1 END) as successful_executions,
    AVG(e.quality_score) as avg_quality_score,
    AVG(e.accuracy_score) as avg_accuracy_score,
    AVG(e.duration_ms) as avg_duration_ms,
    SUM(e.cost_usd) as total_cost_usd
FROM prompt_templates pt
LEFT JOIN executions e ON pt.id = e.template_id
WHERE pt.deleted_at IS NULL
GROUP BY pt.workflow_stage, pt.use_case;

-- Recent workflow executions
CREATE VIEW recent_workflow_executions AS
SELECT 
    e.*,
    pt.name as template_name,
    pt.workflow_stage,
    pt.use_case,
    u.name as user_name
FROM executions e
LEFT JOIN prompt_templates pt ON e.template_id = pt.id
LEFT JOIN users u ON e.user_id = u.id
WHERE e.created_at >= NOW() - INTERVAL '24 hours'
ORDER BY e.created_at DESC;

-- Enhancement effectiveness tracking
CREATE VIEW enhancement_effectiveness AS
SELECT 
    pe.name,
    pe.enhancement_type,
    pe.usage_count,
    pe.success_rate,
    pe.improvement_score,
    COUNT(e.id) as executions_with_enhancement,
    AVG(e.quality_score) as avg_quality_with_enhancement
FROM prompt_enhancements pe
LEFT JOIN executions e ON pe.id = ANY(
    SELECT jsonb_array_elements_text(e.enhancements_applied)::UUID
)
WHERE pe.is_active = true
GROUP BY pe.id, pe.name, pe.enhancement_type, pe.usage_count, pe.success_rate, pe.improvement_score;

-- Grant permissions to prompts_user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO prompts_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO prompts_user;
GRANT USAGE ON SCHEMA public TO prompts_user;

-- Insert default organization
INSERT INTO organizations (name, slug, description) VALUES 
('Default Organization', 'default', 'Default organization for enhanced prompt management');

-- Insert default admin user
INSERT INTO users (organization_id, name, email, role) VALUES 
((SELECT id FROM organizations WHERE slug = 'default'), 'Prompts Admin', 'admin@prompts.local', 'admin');

-- Insert default workflow prompt templates
INSERT INTO prompt_templates (
    organization_id, name, slug, description, template_content, prompt_type, 
    workflow_stage, use_case, category, created_by
) VALUES 
(
    (SELECT id FROM organizations WHERE slug = 'default'),
    'GitHub Project Analysis',
    'github-project-analysis',
    'Analyzes GitHub project structure and provides comprehensive overview',
    'Analyze the GitHub project at {github_repo_url}. Provide a detailed analysis including:\n1. Project structure and architecture\n2. Main technologies and frameworks used\n3. Code quality assessment\n4. Potential areas for improvement\n5. Dependencies and their status\n\nProject URL: {github_repo_url}\nBranch: {branch}\n\nProvide your analysis in structured JSON format.',
    'codegen_workflow',
    'project_selection',
    'github_analysis',
    'workflow',
    (SELECT id FROM users WHERE email = 'admin@prompts.local')
),
(
    (SELECT id FROM organizations WHERE slug = 'default'),
    'Requirements Decomposition',
    'requirements-decomposition',
    'Decomposes user requirements into actionable steps with dependencies',
    'Given the following user requirements for the project, decompose them into specific, actionable steps:\n\nRequirements: {requirements_text}\nProject Context: {project_structure}\n\nFor each step, provide:\n1. Step number and name\n2. Detailed description\n3. Specific requirements\n4. Success criteria\n5. Dependencies on other steps\n6. Estimated effort (hours)\n7. Complexity score (1-10)\n\nReturn the decomposition as a structured JSON array.',
    'codegen_workflow',
    'requirements_decomposition',
    'requirement_decomposition',
    'workflow',
    (SELECT id FROM users WHERE email = 'admin@prompts.local')
),
(
    (SELECT id FROM organizations WHERE slug = 'default'),
    'PR Validation',
    'pr-validation',
    'Validates pull request changes for code quality and requirements compliance',
    'Validate the following pull request changes:\n\nPR Number: {pr_number}\nPR URL: {pr_url}\nChanges: {code_changes}\nOriginal Requirements: {requirements}\nStep Requirements: {step_requirements}\n\nValidate:\n1. Code quality and best practices\n2. Compliance with requirements\n3. Potential issues or bugs\n4. Test coverage\n5. Documentation updates needed\n\nProvide validation results in JSON format with pass/fail status and detailed feedback.',
    'codegen_workflow',
    'pr_validation',
    'pr_validation',
    'workflow',
    (SELECT id FROM users WHERE email = 'admin@prompts.local')
);

-- Insert default prompt enhancements
INSERT INTO prompt_enhancements (
    organization_id, name, enhancement_type, description, enhancement_rules, 
    context_injection_template, accuracy_instructions
) VALUES 
(
    (SELECT id FROM organizations WHERE slug = 'default'),
    'Context Accuracy Booster',
    'accuracy_boost',
    'Enhances prompt accuracy by injecting relevant context and validation instructions',
    '{"apply_to": ["codegen_workflow"], "conditions": {"workflow_stage": ["project_selection", "requirements_decomposition"]}}',
    'IMPORTANT CONTEXT:\n- This is part of an automated workflow\n- Accuracy and factual information are critical\n- Response will be used for automated processing\n\nAdditional Context: {context}',
    'Please ensure your response is:\n1. Factually accurate and verifiable\n2. Structured and machine-readable\n3. Complete and comprehensive\n4. Free of assumptions or speculation'
),
(
    (SELECT id FROM organizations WHERE slug = 'default'),
    'JSON Format Enforcer',
    'format_optimization',
    'Ensures responses are properly formatted JSON for automated processing',
    '{"apply_to": ["codegen_workflow"], "output_format": "json"}',
    '',
    'CRITICAL: Your response MUST be valid JSON format. Do not include any text outside the JSON structure. Validate JSON syntax before responding.'
);

-- Final status message
DO $$
BEGIN
    RAISE NOTICE '💬 Enhanced Prompts Database initialized successfully!';
    RAISE NOTICE 'Features: Codegen SDK integration, Workflow-specific templates, Prompt enhancement system';
    RAISE NOTICE 'Workflow support: GitHub project analysis, Requirements decomposition, PR validation';
    RAISE NOTICE 'Enhancement types: Context injection, Accuracy boosting, Format optimization';
    RAISE NOTICE 'Default templates: GitHub analysis, Requirements decomposition, PR validation';
    RAISE NOTICE 'Timestamp: %', NOW();
END $$;

