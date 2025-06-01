-- Prompts Database Schema
-- Manages prompt templates, AI interactions, and prompt engineering workflows

-- Prompt templates for various analysis and generation tasks
CREATE TABLE IF NOT EXISTS prompt_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    category VARCHAR(100) NOT NULL, -- 'analysis', 'generation', 'review', 'documentation', 'testing'
    subcategory VARCHAR(100), -- More specific categorization
    template_content TEXT NOT NULL, -- The actual prompt template with placeholders
    template_version VARCHAR(50) DEFAULT '1.0.0',
    language VARCHAR(50) DEFAULT 'english', -- Prompt language
    model_type VARCHAR(100), -- 'gpt-4', 'claude-3', 'codegen', 'generic'
    model_parameters JSONB, -- Model-specific parameters (temperature, max_tokens, etc.)
    input_schema JSONB, -- JSON schema for required input variables
    output_schema JSONB, -- Expected output format schema
    example_input JSONB, -- Example input for testing
    example_output TEXT, -- Example expected output
    tags TEXT[], -- Categorization tags
    is_active BOOLEAN DEFAULT true,
    is_system_prompt BOOLEAN DEFAULT false, -- System vs user prompts
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(255),
    usage_count INTEGER DEFAULT 0,
    success_rate DECIMAL(5,2), -- Success rate based on evaluations
    average_rating DECIMAL(3,2), -- User ratings average
    metadata JSONB,
    
    CONSTRAINT valid_category CHECK (category IN (
        'analysis', 'generation', 'review', 'documentation', 'testing', 
        'refactoring', 'debugging', 'optimization', 'security'
    ))
);

-- Prompt template variables and their definitions
CREATE TABLE IF NOT EXISTS prompt_variables (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID NOT NULL REFERENCES prompt_templates(id) ON DELETE CASCADE,
    variable_name VARCHAR(255) NOT NULL,
    variable_type VARCHAR(50) NOT NULL, -- 'string', 'number', 'boolean', 'array', 'object', 'code'
    description TEXT,
    is_required BOOLEAN DEFAULT true,
    default_value TEXT,
    validation_rules JSONB, -- Validation constraints
    example_value TEXT,
    transformation_rules JSONB, -- How to transform input before insertion
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(template_id, variable_name),
    CONSTRAINT valid_variable_type CHECK (variable_type IN (
        'string', 'number', 'boolean', 'array', 'object', 'code', 'file_path', 'url'
    ))
);

-- Prompt execution history and results
CREATE TABLE IF NOT EXISTS prompt_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID NOT NULL REFERENCES prompt_templates(id),
    execution_context VARCHAR(100), -- 'analysis_task', 'code_generation', 'manual_test'
    input_variables JSONB NOT NULL, -- Actual values used for variables
    rendered_prompt TEXT NOT NULL, -- Final prompt after variable substitution
    model_used VARCHAR(100),
    model_parameters JSONB,
    response_content TEXT,
    response_metadata JSONB, -- Token usage, timing, etc.
    execution_status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed'
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER,
    token_usage JSONB, -- Input/output token counts
    cost_estimate DECIMAL(10,4), -- Estimated cost in USD
    quality_score DECIMAL(3,2), -- Automated quality assessment
    user_rating INTEGER, -- 1-5 user rating
    user_feedback TEXT,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    parent_execution_id UUID REFERENCES prompt_executions(id), -- For retry chains
    task_id UUID, -- Reference to tasks.id if part of a task
    codebase_id UUID, -- Reference to repositories.id if codebase-specific
    created_by VARCHAR(255),
    metadata JSONB,
    
    CONSTRAINT valid_execution_status CHECK (execution_status IN (
        'pending', 'running', 'completed', 'failed', 'cancelled'
    )),
    CONSTRAINT valid_user_rating CHECK (user_rating IS NULL OR (user_rating >= 1 AND user_rating <= 5))
);

-- Prompt chains for complex multi-step workflows
CREATE TABLE IF NOT EXISTS prompt_chains (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    chain_type VARCHAR(100) NOT NULL, -- 'sequential', 'conditional', 'parallel', 'loop'
    configuration JSONB, -- Chain-specific configuration
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(255),
    usage_count INTEGER DEFAULT 0,
    success_rate DECIMAL(5,2),
    metadata JSONB,
    
    CONSTRAINT valid_chain_type CHECK (chain_type IN (
        'sequential', 'conditional', 'parallel', 'loop', 'decision_tree'
    ))
);

-- Steps within prompt chains
CREATE TABLE IF NOT EXISTS prompt_chain_steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chain_id UUID NOT NULL REFERENCES prompt_chains(id) ON DELETE CASCADE,
    step_order INTEGER NOT NULL,
    step_name VARCHAR(255) NOT NULL,
    template_id UUID NOT NULL REFERENCES prompt_templates(id),
    condition_expression TEXT, -- Conditional logic for step execution
    input_mapping JSONB, -- How to map previous outputs to this step's inputs
    output_mapping JSONB, -- How to map this step's output for next steps
    retry_policy JSONB, -- Step-specific retry configuration
    timeout_seconds INTEGER DEFAULT 300,
    is_optional BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(chain_id, step_order),
    UNIQUE(chain_id, step_name)
);

-- Prompt chain execution history
CREATE TABLE IF NOT EXISTS prompt_chain_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chain_id UUID NOT NULL REFERENCES prompt_chains(id),
    execution_status VARCHAR(50) DEFAULT 'pending',
    input_data JSONB,
    output_data JSONB,
    current_step_order INTEGER,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER,
    total_cost DECIMAL(10,4),
    error_message TEXT,
    task_id UUID, -- Reference to tasks.id
    created_by VARCHAR(255),
    metadata JSONB,
    
    CONSTRAINT valid_chain_execution_status CHECK (execution_status IN (
        'pending', 'running', 'completed', 'failed', 'cancelled', 'paused'
    ))
);

-- Individual step executions within chain executions
CREATE TABLE IF NOT EXISTS prompt_chain_step_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chain_execution_id UUID NOT NULL REFERENCES prompt_chain_executions(id) ON DELETE CASCADE,
    step_id UUID NOT NULL REFERENCES prompt_chain_steps(id),
    prompt_execution_id UUID REFERENCES prompt_executions(id),
    step_order INTEGER NOT NULL,
    execution_status VARCHAR(50) DEFAULT 'pending',
    input_data JSONB,
    output_data JSONB,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER,
    retry_count INTEGER DEFAULT 0,
    error_message TEXT,
    
    CONSTRAINT valid_step_execution_status CHECK (execution_status IN (
        'pending', 'running', 'completed', 'failed', 'skipped', 'cancelled'
    ))
);

-- Prompt evaluation and testing
CREATE TABLE IF NOT EXISTS prompt_evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID NOT NULL REFERENCES prompt_templates(id),
    evaluation_type VARCHAR(100) NOT NULL, -- 'accuracy', 'relevance', 'completeness', 'safety'
    test_case_name VARCHAR(255),
    test_input JSONB,
    expected_output TEXT,
    actual_output TEXT,
    evaluation_score DECIMAL(5,2), -- 0-100 score
    evaluation_criteria JSONB, -- Specific criteria used for evaluation
    evaluator_type VARCHAR(50), -- 'human', 'automated', 'llm'
    evaluator_id VARCHAR(255), -- User ID or system identifier
    evaluation_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    feedback TEXT,
    is_baseline BOOLEAN DEFAULT false, -- Baseline evaluation for comparison
    metadata JSONB,
    
    CONSTRAINT valid_evaluation_type CHECK (evaluation_type IN (
        'accuracy', 'relevance', 'completeness', 'safety', 'efficiency', 
        'creativity', 'coherence', 'factuality'
    )),
    CONSTRAINT valid_evaluator_type CHECK (evaluator_type IN ('human', 'automated', 'llm', 'hybrid'))
);

-- Prompt optimization experiments
CREATE TABLE IF NOT EXISTS prompt_experiments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_name VARCHAR(255) NOT NULL,
    description TEXT,
    base_template_id UUID NOT NULL REFERENCES prompt_templates(id),
    experiment_type VARCHAR(100) NOT NULL, -- 'a_b_test', 'parameter_tuning', 'template_variation'
    hypothesis TEXT,
    test_configurations JSONB, -- Different configurations to test
    sample_size INTEGER,
    success_criteria JSONB, -- What constitutes success
    status VARCHAR(50) DEFAULT 'planned', -- 'planned', 'running', 'completed', 'cancelled'
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    results JSONB, -- Experiment results and analysis
    conclusions TEXT,
    created_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB,
    
    CONSTRAINT valid_experiment_type CHECK (experiment_type IN (
        'a_b_test', 'parameter_tuning', 'template_variation', 'model_comparison'
    )),
    CONSTRAINT valid_experiment_status CHECK (status IN (
        'planned', 'running', 'completed', 'cancelled', 'paused'
    ))
);

-- Prompt libraries and collections
CREATE TABLE IF NOT EXISTS prompt_libraries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    library_type VARCHAR(100) NOT NULL, -- 'public', 'private', 'team', 'organization'
    owner_id VARCHAR(255),
    is_public BOOLEAN DEFAULT false,
    tags TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB,
    
    CONSTRAINT valid_library_type CHECK (library_type IN (
        'public', 'private', 'team', 'organization', 'system'
    ))
);

-- Association between templates and libraries
CREATE TABLE IF NOT EXISTS prompt_library_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    library_id UUID NOT NULL REFERENCES prompt_libraries(id) ON DELETE CASCADE,
    template_id UUID NOT NULL REFERENCES prompt_templates(id) ON DELETE CASCADE,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    added_by VARCHAR(255),
    
    UNIQUE(library_id, template_id)
);

-- Indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_prompt_templates_category ON prompt_templates(category);
CREATE INDEX IF NOT EXISTS idx_prompt_templates_active ON prompt_templates(is_active);
CREATE INDEX IF NOT EXISTS idx_prompt_templates_model_type ON prompt_templates(model_type);
CREATE INDEX IF NOT EXISTS idx_prompt_templates_usage_count ON prompt_templates(usage_count);
CREATE INDEX IF NOT EXISTS idx_prompt_templates_success_rate ON prompt_templates(success_rate);

CREATE INDEX IF NOT EXISTS idx_prompt_variables_template ON prompt_variables(template_id);
CREATE INDEX IF NOT EXISTS idx_prompt_variables_required ON prompt_variables(is_required);

CREATE INDEX IF NOT EXISTS idx_prompt_executions_template ON prompt_executions(template_id);
CREATE INDEX IF NOT EXISTS idx_prompt_executions_status ON prompt_executions(execution_status);
CREATE INDEX IF NOT EXISTS idx_prompt_executions_started_at ON prompt_executions(started_at);
CREATE INDEX IF NOT EXISTS idx_prompt_executions_task_id ON prompt_executions(task_id);
CREATE INDEX IF NOT EXISTS idx_prompt_executions_codebase_id ON prompt_executions(codebase_id);
CREATE INDEX IF NOT EXISTS idx_prompt_executions_created_by ON prompt_executions(created_by);

CREATE INDEX IF NOT EXISTS idx_prompt_chains_active ON prompt_chains(is_active);
CREATE INDEX IF NOT EXISTS idx_prompt_chains_type ON prompt_chains(chain_type);

CREATE INDEX IF NOT EXISTS idx_prompt_chain_steps_chain ON prompt_chain_steps(chain_id);
CREATE INDEX IF NOT EXISTS idx_prompt_chain_steps_order ON prompt_chain_steps(step_order);
CREATE INDEX IF NOT EXISTS idx_prompt_chain_steps_template ON prompt_chain_steps(template_id);

CREATE INDEX IF NOT EXISTS idx_prompt_chain_executions_chain ON prompt_chain_executions(chain_id);
CREATE INDEX IF NOT EXISTS idx_prompt_chain_executions_status ON prompt_chain_executions(execution_status);
CREATE INDEX IF NOT EXISTS idx_prompt_chain_executions_task ON prompt_chain_executions(task_id);

CREATE INDEX IF NOT EXISTS idx_prompt_evaluations_template ON prompt_evaluations(template_id);
CREATE INDEX IF NOT EXISTS idx_prompt_evaluations_type ON prompt_evaluations(evaluation_type);
CREATE INDEX IF NOT EXISTS idx_prompt_evaluations_score ON prompt_evaluations(evaluation_score);

CREATE INDEX IF NOT EXISTS idx_prompt_experiments_base_template ON prompt_experiments(base_template_id);
CREATE INDEX IF NOT EXISTS idx_prompt_experiments_status ON prompt_experiments(status);
CREATE INDEX IF NOT EXISTS idx_prompt_experiments_type ON prompt_experiments(experiment_type);

-- Triggers for automatic timestamp updates
CREATE TRIGGER update_prompt_templates_updated_at BEFORE UPDATE ON prompt_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_prompt_chains_updated_at BEFORE UPDATE ON prompt_chains
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_prompt_libraries_updated_at BEFORE UPDATE ON prompt_libraries
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Views for common queries
CREATE OR REPLACE VIEW prompt_template_stats AS
SELECT 
    pt.id,
    pt.name,
    pt.category,
    pt.subcategory,
    pt.is_active,
    pt.usage_count,
    pt.success_rate,
    pt.average_rating,
    COUNT(pe.id) as execution_count,
    AVG(pe.duration_ms) as avg_duration_ms,
    AVG(pe.quality_score) as avg_quality_score,
    COUNT(CASE WHEN pe.execution_status = 'completed' THEN 1 END) as successful_executions,
    COUNT(CASE WHEN pe.execution_status = 'failed' THEN 1 END) as failed_executions
FROM prompt_templates pt
LEFT JOIN prompt_executions pe ON pt.id = pe.template_id
GROUP BY pt.id, pt.name, pt.category, pt.subcategory, pt.is_active, 
         pt.usage_count, pt.success_rate, pt.average_rating;

CREATE OR REPLACE VIEW recent_prompt_executions AS
SELECT 
    pe.id,
    pt.name as template_name,
    pt.category,
    pe.execution_status,
    pe.started_at,
    pe.duration_ms,
    pe.quality_score,
    pe.user_rating,
    pe.created_by
FROM prompt_executions pe
JOIN prompt_templates pt ON pe.template_id = pt.id
WHERE pe.started_at >= NOW() - INTERVAL '7 days'
ORDER BY pe.started_at DESC;

-- Sample data for testing
INSERT INTO prompt_templates (name, description, category, template_content, input_schema, model_type) VALUES
('code_analysis_summary', 'Generate a comprehensive analysis summary for a codebase', 'analysis',
 'Analyze the following codebase and provide a summary including:\n1. Overall structure\n2. Key components\n3. Code quality metrics\n4. Potential issues\n\nCodebase: {{codebase_info}}\nFiles: {{file_list}}\nMetrics: {{metrics}}',
 '{"type": "object", "properties": {"codebase_info": {"type": "string"}, "file_list": {"type": "array"}, "metrics": {"type": "object"}}}',
 'gpt-4'),
('function_documentation', 'Generate documentation for a function', 'documentation',
 'Generate comprehensive documentation for the following function:\n\n```{{language}}\n{{function_code}}\n```\n\nInclude:\n- Purpose and functionality\n- Parameters and return values\n- Usage examples\n- Edge cases and considerations',
 '{"type": "object", "properties": {"language": {"type": "string"}, "function_code": {"type": "string"}}}',
 'claude-3'),
('code_review', 'Perform automated code review', 'review',
 'Review the following code changes and provide feedback on:\n1. Code quality\n2. Best practices\n3. Potential bugs\n4. Performance considerations\n5. Security issues\n\nChanges:\n{{code_diff}}\n\nContext:\n{{file_context}}',
 '{"type": "object", "properties": {"code_diff": {"type": "string"}, "file_context": {"type": "string"}}}',
 'gpt-4');

INSERT INTO prompt_libraries (name, description, library_type, is_public) VALUES
('codebase_analysis', 'Standard prompts for codebase analysis tasks', 'system', true),
('code_generation', 'Prompts for automated code generation', 'system', true),
('documentation', 'Documentation generation prompts', 'public', true);

