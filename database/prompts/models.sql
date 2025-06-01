-- Prompts Module Database Schema
-- Dynamic prompt management, templating, and context-aware generation system

-- Main prompt templates table
CREATE TABLE prompt_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Template identification
    name VARCHAR(255) NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    category VARCHAR(100), -- code_review, bug_fix, feature_implementation, etc.
    type prompt_type NOT NULL,
    
    -- Template content
    template_content TEXT NOT NULL,
    variables JSONB DEFAULT '[]', -- Array of variable definitions
    default_values JSONB DEFAULT '{}', -- Default values for variables
    
    -- Metadata
    version VARCHAR(20) DEFAULT '1.0',
    language language_type,
    framework VARCHAR(100), -- React, Django, FastAPI, etc.
    tags JSONB DEFAULT '[]',
    
    -- Usage and performance
    usage_count INTEGER DEFAULT 0,
    success_rate DECIMAL(5,2) DEFAULT 0.0,
    average_rating DECIMAL(3,2) DEFAULT 0.0,
    
    -- Status and lifecycle
    is_active BOOLEAN DEFAULT TRUE,
    is_public BOOLEAN DEFAULT FALSE,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(organization_id, name, version)
);

-- Prompt template versions (for version control)
CREATE TABLE prompt_template_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_id UUID REFERENCES prompt_templates(id) ON DELETE CASCADE,
    
    version VARCHAR(20) NOT NULL,
    template_content TEXT NOT NULL,
    variables JSONB DEFAULT '[]',
    default_values JSONB DEFAULT '{}',
    
    -- Change tracking
    change_summary VARCHAR(500),
    changed_by UUID REFERENCES users(id) ON DELETE SET NULL,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(template_id, version)
);

-- Generated prompts (instances of templates with actual values)
CREATE TABLE generated_prompts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_id UUID REFERENCES prompt_templates(id) ON DELETE CASCADE,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Generation context
    context JSONB DEFAULT '{}', -- Input variables and values
    generated_content TEXT NOT NULL,
    
    -- Usage tracking
    used_for_task_id UUID, -- References tasks.id but no FK to avoid circular dependency
    codegen_task_id VARCHAR(100),
    
    -- Performance metrics
    execution_time_ms INTEGER,
    success BOOLEAN,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    feedback TEXT,
    
    -- Metadata
    generated_by UUID REFERENCES users(id) ON DELETE SET NULL,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Prompt usage analytics
CREATE TABLE prompt_usage_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_id UUID REFERENCES prompt_templates(id) ON DELETE CASCADE,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Usage metrics
    date DATE NOT NULL,
    usage_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    
    -- Performance metrics
    average_execution_time_ms DECIMAL(10,2),
    average_rating DECIMAL(3,2),
    
    -- Context analysis
    common_variables JSONB DEFAULT '{}',
    common_contexts JSONB DEFAULT '[]',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(template_id, date)
);

-- Context patterns (for intelligent prompt suggestions)
CREATE TABLE context_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Pattern identification
    pattern_name VARCHAR(255) NOT NULL,
    pattern_type VARCHAR(100), -- codebase, task, user_preference
    
    -- Pattern definition
    pattern_conditions JSONB NOT NULL, -- Conditions that trigger this pattern
    recommended_templates JSONB DEFAULT '[]', -- Array of template IDs
    variable_mappings JSONB DEFAULT '{}', -- How to map context to template variables
    
    -- Performance
    match_count INTEGER DEFAULT 0,
    success_rate DECIMAL(5,2) DEFAULT 0.0,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Prompt optimization suggestions
CREATE TABLE prompt_optimization_suggestions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_id UUID REFERENCES prompt_templates(id) ON DELETE CASCADE,
    
    -- Suggestion details
    suggestion_type VARCHAR(100) NOT NULL, -- variable_optimization, content_improvement, performance
    title VARCHAR(500) NOT NULL,
    description TEXT,
    suggested_changes JSONB DEFAULT '{}',
    
    -- Impact analysis
    estimated_improvement DECIMAL(5,2), -- Percentage improvement expected
    confidence DECIMAL(3,2) DEFAULT 0.0, -- Confidence in the suggestion
    
    -- Status
    status VARCHAR(50) DEFAULT 'pending', -- pending, accepted, rejected, implemented
    reviewed_by UUID REFERENCES users(id) ON DELETE SET NULL,
    reviewed_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_prompt_templates_organization_id ON prompt_templates(organization_id);
CREATE INDEX idx_prompt_templates_name ON prompt_templates(name);
CREATE INDEX idx_prompt_templates_type ON prompt_templates(type);
CREATE INDEX idx_prompt_templates_category ON prompt_templates(category);
CREATE INDEX idx_prompt_templates_language ON prompt_templates(language);
CREATE INDEX idx_prompt_templates_is_active ON prompt_templates(is_active);
CREATE INDEX idx_prompt_templates_usage_count ON prompt_templates(usage_count);

CREATE INDEX idx_prompt_template_versions_template_id ON prompt_template_versions(template_id);
CREATE INDEX idx_prompt_template_versions_version ON prompt_template_versions(version);

CREATE INDEX idx_generated_prompts_template_id ON generated_prompts(template_id);
CREATE INDEX idx_generated_prompts_organization_id ON generated_prompts(organization_id);
CREATE INDEX idx_generated_prompts_task_id ON generated_prompts(used_for_task_id);
CREATE INDEX idx_generated_prompts_codegen_task_id ON generated_prompts(codegen_task_id);
CREATE INDEX idx_generated_prompts_generated_at ON generated_prompts(generated_at);
CREATE INDEX idx_generated_prompts_success ON generated_prompts(success);

CREATE INDEX idx_prompt_usage_analytics_template_id ON prompt_usage_analytics(template_id);
CREATE INDEX idx_prompt_usage_analytics_date ON prompt_usage_analytics(date);

CREATE INDEX idx_context_patterns_organization_id ON context_patterns(organization_id);
CREATE INDEX idx_context_patterns_type ON context_patterns(pattern_type);
CREATE INDEX idx_context_patterns_is_active ON context_patterns(is_active);

CREATE INDEX idx_prompt_optimization_template_id ON prompt_optimization_suggestions(template_id);
CREATE INDEX idx_prompt_optimization_status ON prompt_optimization_suggestions(status);

-- GIN indexes for JSONB columns
CREATE INDEX idx_prompt_templates_variables ON prompt_templates USING GIN(variables);
CREATE INDEX idx_prompt_templates_default_values ON prompt_templates USING GIN(default_values);
CREATE INDEX idx_prompt_templates_tags ON prompt_templates USING GIN(tags);
CREATE INDEX idx_generated_prompts_context ON generated_prompts USING GIN(context);
CREATE INDEX idx_context_patterns_conditions ON context_patterns USING GIN(pattern_conditions);
CREATE INDEX idx_context_patterns_mappings ON context_patterns USING GIN(variable_mappings);

-- Text search index for prompt content
CREATE INDEX idx_prompt_templates_text_search ON prompt_templates 
    USING GIN(to_tsvector('english', title || ' ' || description || ' ' || template_content));

-- Apply updated_at triggers
CREATE TRIGGER update_prompt_templates_updated_at BEFORE UPDATE ON prompt_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_context_patterns_updated_at BEFORE UPDATE ON context_patterns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Prompt management functions

-- Add a new prompt template
CREATE OR REPLACE FUNCTION add_prompt(
    p_name VARCHAR,
    p_template_content TEXT,
    p_type prompt_type DEFAULT 'code_review',
    p_organization_id UUID DEFAULT NULL,
    p_variables JSONB DEFAULT '[]',
    p_default_values JSONB DEFAULT '{}'
) RETURNS UUID AS $$
DECLARE
    new_template_id UUID;
    org_id UUID;
BEGIN
    -- Get organization ID if not provided
    IF p_organization_id IS NULL THEN
        SELECT id INTO org_id FROM organizations WHERE codegen_org_id = '323' LIMIT 1;
    ELSE
        org_id := p_organization_id;
    END IF;
    
    INSERT INTO prompt_templates (
        organization_id, name, title, template_content, type, variables, default_values
    ) VALUES (
        org_id, p_name, p_name, p_template_content, p_type, p_variables, p_default_values
    ) RETURNING id INTO new_template_id;
    
    -- Create initial version
    INSERT INTO prompt_template_versions (
        template_id, version, template_content, variables, default_values
    ) VALUES (
        new_template_id, '1.0', p_template_content, p_variables, p_default_values
    );
    
    RETURN new_template_id;
END;
$$ LANGUAGE plpgsql;

-- Update a prompt template
CREATE OR REPLACE FUNCTION update_prompt(
    p_template_id UUID,
    p_template_content TEXT DEFAULT NULL,
    p_variables JSONB DEFAULT NULL,
    p_default_values JSONB DEFAULT NULL,
    p_change_summary VARCHAR DEFAULT NULL,
    p_user_id UUID DEFAULT NULL
) RETURNS BOOLEAN AS $$
DECLARE
    current_version VARCHAR;
    new_version VARCHAR;
BEGIN
    -- Get current version
    SELECT version INTO current_version FROM prompt_templates WHERE id = p_template_id;
    
    IF current_version IS NULL THEN
        RAISE EXCEPTION 'Template not found: %', p_template_id;
    END IF;
    
    -- Generate new version number (simple increment)
    new_version := (current_version::DECIMAL + 0.1)::VARCHAR;
    
    -- Update the main template
    UPDATE prompt_templates SET
        template_content = COALESCE(p_template_content, template_content),
        variables = COALESCE(p_variables, variables),
        default_values = COALESCE(p_default_values, default_values),
        version = new_version
    WHERE id = p_template_id;
    
    -- Create new version record
    INSERT INTO prompt_template_versions (
        template_id, version, template_content, variables, default_values,
        change_summary, changed_by
    ) VALUES (
        p_template_id, new_version, 
        COALESCE(p_template_content, (SELECT template_content FROM prompt_templates WHERE id = p_template_id)),
        COALESCE(p_variables, (SELECT variables FROM prompt_templates WHERE id = p_template_id)),
        COALESCE(p_default_values, (SELECT default_values FROM prompt_templates WHERE id = p_template_id)),
        p_change_summary, p_user_id
    );
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- List prompt titles with filtering
CREATE OR REPLACE FUNCTION list_prompt_titles(
    p_organization_id UUID DEFAULT NULL,
    p_type prompt_type DEFAULT NULL,
    p_category VARCHAR DEFAULT NULL,
    p_is_active BOOLEAN DEFAULT TRUE,
    p_limit INTEGER DEFAULT 50
) RETURNS TABLE(
    template_id UUID,
    name VARCHAR,
    title VARCHAR,
    type prompt_type,
    category VARCHAR,
    usage_count INTEGER,
    success_rate DECIMAL,
    created_at TIMESTAMP WITH TIME ZONE
) AS $$
DECLARE
    org_id UUID;
BEGIN
    -- Get organization ID if not provided
    IF p_organization_id IS NULL THEN
        SELECT id INTO org_id FROM organizations WHERE codegen_org_id = '323' LIMIT 1;
    ELSE
        org_id := p_organization_id;
    END IF;
    
    RETURN QUERY
    SELECT 
        pt.id,
        pt.name,
        pt.title,
        pt.type,
        pt.category,
        pt.usage_count,
        pt.success_rate,
        pt.created_at
    FROM prompt_templates pt
    WHERE pt.organization_id = org_id
    AND (p_type IS NULL OR pt.type = p_type)
    AND (p_category IS NULL OR pt.category = p_category)
    AND (p_is_active IS NULL OR pt.is_active = p_is_active)
    ORDER BY pt.usage_count DESC, pt.created_at DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Expand prompt with full context
CREATE OR REPLACE FUNCTION expand_prompt_full(
    p_template_name VARCHAR,
    p_context JSONB DEFAULT '{}',
    p_organization_id UUID DEFAULT NULL
) RETURNS JSONB AS $$
DECLARE
    template_record RECORD;
    generated_content TEXT;
    variable_record JSONB;
    variable_name TEXT;
    variable_value TEXT;
    org_id UUID;
    generated_prompt_id UUID;
BEGIN
    -- Get organization ID if not provided
    IF p_organization_id IS NULL THEN
        SELECT id INTO org_id FROM organizations WHERE codegen_org_id = '323' LIMIT 1;
    ELSE
        org_id := p_organization_id;
    END IF;
    
    -- Get template
    SELECT * INTO template_record 
    FROM prompt_templates 
    WHERE organization_id = org_id 
    AND name = p_template_name 
    AND is_active = TRUE;
    
    IF template_record IS NULL THEN
        RAISE EXCEPTION 'Template not found: %', p_template_name;
    END IF;
    
    -- Start with template content
    generated_content := template_record.template_content;
    
    -- Replace variables with values from context or defaults
    FOR variable_record IN SELECT * FROM jsonb_array_elements(template_record.variables)
    LOOP
        variable_name := variable_record->>'name';
        
        -- Get value from context or default
        IF p_context ? variable_name THEN
            variable_value := p_context->>variable_name;
        ELSIF template_record.default_values ? variable_name THEN
            variable_value := template_record.default_values->>variable_name;
        ELSE
            variable_value := '{' || variable_name || '}'; -- Keep placeholder if no value
        END IF;
        
        -- Replace in content
        generated_content := REPLACE(generated_content, '{' || variable_name || '}', variable_value);
    END LOOP;
    
    -- Store generated prompt
    INSERT INTO generated_prompts (
        template_id, organization_id, context, generated_content
    ) VALUES (
        template_record.id, org_id, p_context, generated_content
    ) RETURNING id INTO generated_prompt_id;
    
    -- Update usage count
    UPDATE prompt_templates 
    SET usage_count = usage_count + 1 
    WHERE id = template_record.id;
    
    RETURN jsonb_build_object(
        'template_id', template_record.id,
        'generated_prompt_id', generated_prompt_id,
        'generated_content', generated_content,
        'variables_used', p_context,
        'template_name', p_template_name
    );
END;
$$ LANGUAGE plpgsql;

-- Find best prompt template for given context
CREATE OR REPLACE FUNCTION find_best_prompt_template(
    p_context JSONB,
    p_type prompt_type DEFAULT NULL,
    p_organization_id UUID DEFAULT NULL
) RETURNS TABLE(
    template_id UUID,
    template_name VARCHAR,
    match_score DECIMAL,
    success_rate DECIMAL
) AS $$
DECLARE
    org_id UUID;
BEGIN
    -- Get organization ID if not provided
    IF p_organization_id IS NULL THEN
        SELECT id INTO org_id FROM organizations WHERE codegen_org_id = '323' LIMIT 1;
    ELSE
        org_id := p_organization_id;
    END IF;
    
    RETURN QUERY
    WITH template_scores AS (
        SELECT 
            pt.id,
            pt.name,
            pt.success_rate,
            -- Simple scoring based on usage and success rate
            (pt.usage_count * 0.3 + pt.success_rate * 0.7) as match_score
        FROM prompt_templates pt
        WHERE pt.organization_id = org_id
        AND pt.is_active = TRUE
        AND (p_type IS NULL OR pt.type = p_type)
    )
    SELECT 
        ts.id,
        ts.name,
        ts.match_score,
        ts.success_rate
    FROM template_scores ts
    ORDER BY ts.match_score DESC
    LIMIT 5;
END;
$$ LANGUAGE plpgsql;

-- Record prompt usage feedback
CREATE OR REPLACE FUNCTION record_prompt_feedback(
    p_generated_prompt_id UUID,
    p_success BOOLEAN,
    p_rating INTEGER DEFAULT NULL,
    p_feedback TEXT DEFAULT NULL,
    p_execution_time_ms INTEGER DEFAULT NULL
) RETURNS BOOLEAN AS $$
DECLARE
    template_id UUID;
BEGIN
    -- Update generated prompt record
    UPDATE generated_prompts SET
        success = p_success,
        rating = p_rating,
        feedback = p_feedback,
        execution_time_ms = p_execution_time_ms
    WHERE id = p_generated_prompt_id
    RETURNING template_id INTO template_id;
    
    IF template_id IS NULL THEN
        RAISE EXCEPTION 'Generated prompt not found: %', p_generated_prompt_id;
    END IF;
    
    -- Update template success rate
    UPDATE prompt_templates SET
        success_rate = (
            SELECT 
                (COUNT(*) FILTER (WHERE success = TRUE) * 100.0) / COUNT(*)
            FROM generated_prompts 
            WHERE template_id = prompt_templates.id
        ),
        average_rating = (
            SELECT AVG(rating)
            FROM generated_prompts 
            WHERE template_id = prompt_templates.id 
            AND rating IS NOT NULL
        )
    WHERE id = template_id;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Generate usage analytics
CREATE OR REPLACE FUNCTION update_prompt_analytics(p_date DATE DEFAULT CURRENT_DATE)
RETURNS INTEGER AS $$
DECLARE
    updated_count INTEGER := 0;
    template_record RECORD;
BEGIN
    FOR template_record IN 
        SELECT DISTINCT template_id FROM generated_prompts 
        WHERE DATE(generated_at) = p_date
    LOOP
        INSERT INTO prompt_usage_analytics (
            template_id, 
            organization_id,
            date,
            usage_count,
            success_count,
            failure_count,
            average_execution_time_ms,
            average_rating
        )
        SELECT 
            gp.template_id,
            pt.organization_id,
            p_date,
            COUNT(*),
            COUNT(*) FILTER (WHERE gp.success = TRUE),
            COUNT(*) FILTER (WHERE gp.success = FALSE),
            AVG(gp.execution_time_ms),
            AVG(gp.rating)
        FROM generated_prompts gp
        JOIN prompt_templates pt ON gp.template_id = pt.id
        WHERE gp.template_id = template_record.template_id
        AND DATE(gp.generated_at) = p_date
        GROUP BY gp.template_id, pt.organization_id
        ON CONFLICT (template_id, date) DO UPDATE SET
            usage_count = EXCLUDED.usage_count,
            success_count = EXCLUDED.success_count,
            failure_count = EXCLUDED.failure_count,
            average_execution_time_ms = EXCLUDED.average_execution_time_ms,
            average_rating = EXCLUDED.average_rating;
        
        updated_count := updated_count + 1;
    END LOOP;
    
    RETURN updated_count;
END;
$$ LANGUAGE plpgsql;

-- Insert default prompt templates
INSERT INTO prompt_templates (
    organization_id, name, title, type, category, template_content, variables, default_values
) VALUES 
(
    (SELECT id FROM organizations WHERE codegen_org_id = '323' LIMIT 1),
    'code_review_security',
    'Security-focused Code Review',
    'code_review',
    'security',
    'Please review the following code for security vulnerabilities and best practices:

Code to review:
```{language}
{code}
```

Focus areas:
- Input validation and sanitization
- Authentication and authorization
- Data encryption and secure storage
- SQL injection and XSS prevention
- Error handling and information disclosure

Please provide:
1. Identified security issues (if any)
2. Risk assessment for each issue
3. Specific recommendations for fixes
4. Best practices suggestions',
    '[{"name": "code", "type": "string", "required": true}, {"name": "language", "type": "string", "required": false}]',
    '{"language": "python"}'
),
(
    (SELECT id FROM organizations WHERE codegen_org_id = '323' LIMIT 1),
    'bug_fix_analysis',
    'Bug Analysis and Fix Suggestion',
    'bug_fix',
    'debugging',
    'Analyze the following bug report and provide a fix:

Bug Description: {bug_description}

Error Message: {error_message}

Code Context:
```{language}
{code_context}
```

Please provide:
1. Root cause analysis
2. Step-by-step fix implementation
3. Prevention strategies
4. Test cases to verify the fix',
    '[{"name": "bug_description", "type": "string", "required": true}, {"name": "error_message", "type": "string", "required": false}, {"name": "code_context", "type": "string", "required": true}, {"name": "language", "type": "string", "required": false}]',
    '{"language": "python", "error_message": "Not provided"}'
),
(
    (SELECT id FROM organizations WHERE codegen_org_id = '323' LIMIT 1),
    'feature_implementation',
    'Feature Implementation Guide',
    'feature_implementation',
    'development',
    'Implement the following feature:

Feature Requirements: {requirements}

Technical Specifications:
{technical_specs}

Existing Codebase Context:
```{language}
{existing_code}
```

Please provide:
1. Implementation plan and architecture
2. Code implementation with best practices
3. Testing strategy and test cases
4. Documentation updates needed
5. Potential impact on existing functionality',
    '[{"name": "requirements", "type": "string", "required": true}, {"name": "technical_specs", "type": "string", "required": false}, {"name": "existing_code", "type": "string", "required": false}, {"name": "language", "type": "string", "required": false}]',
    '{"language": "python", "technical_specs": "To be determined", "existing_code": "No existing code provided"}'
)
ON CONFLICT (organization_id, name, version) DO NOTHING;

COMMENT ON TABLE prompt_templates IS 'Template definitions for dynamic prompt generation';
COMMENT ON TABLE prompt_template_versions IS 'Version control for prompt templates';
COMMENT ON TABLE generated_prompts IS 'Instances of generated prompts with actual values';
COMMENT ON TABLE prompt_usage_analytics IS 'Analytics and metrics for prompt template usage';
COMMENT ON TABLE context_patterns IS 'Patterns for intelligent prompt template suggestions';
COMMENT ON TABLE prompt_optimization_suggestions IS 'AI-generated suggestions for prompt optimization';

