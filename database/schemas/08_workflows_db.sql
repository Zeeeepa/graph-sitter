-- =============================================================================
-- WORKFLOWS DATABASE SCHEMA: Complete Workflow Orchestration
-- =============================================================================
-- This database handles the complete GitHub project workflow orchestration:
-- Project selection → Requirements input → Decomposition → Linear issues → 
-- Task execution → PR validation → Dev branch management → Completion
-- =============================================================================

-- Connect to workflows_db
\c workflows_db;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- Set timezone and configuration
SET timezone = 'UTC';
SET default_text_search_config = 'pg_catalog.english';

-- Grant all privileges to workflows_user
GRANT ALL PRIVILEGES ON DATABASE workflows_db TO workflows_user;
GRANT ALL PRIVILEGES ON SCHEMA public TO workflows_user;

-- Workflow-specific enums
CREATE TYPE workflow_status AS ENUM (
    'draft',
    'active',
    'paused',
    'completed',
    'failed',
    'cancelled'
);

CREATE TYPE workflow_stage AS ENUM (
    'project_selection',
    'requirements_input',
    'requirements_saved',
    'requirements_decomposition',
    'step_planning',
    'linear_main_issue_creation',
    'linear_sub_issues_creation',
    'task_execution',
    'pr_creation',
    'pr_validation',
    'dev_branch_merge',
    'completion',
    'error'
);

CREATE TYPE integration_type AS ENUM (
    'github',
    'linear',
    'codegen_sdk',
    'slack',
    'notion'
);

CREATE TYPE validation_status AS ENUM (
    'pending',
    'in_progress',
    'passed',
    'failed',
    'skipped'
);

-- =============================================================================
-- CORE REFERENCE TABLES
-- =============================================================================

-- Organizations with all integrations
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    
    -- Integration configurations
    codegen_org_id VARCHAR(255),
    codegen_api_token_encrypted TEXT,
    github_integration_config JSONB DEFAULT '{}',
    linear_integration_config JSONB DEFAULT '{}',
    
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Users with workflow permissions
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(50) DEFAULT 'member',
    
    -- External integrations
    github_username VARCHAR(255),
    linear_user_id VARCHAR(255),
    
    -- Workflow permissions
    can_create_workflows BOOLEAN DEFAULT true,
    can_manage_workflows BOOLEAN DEFAULT false,
    
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- WORKFLOW DEFINITIONS AND TEMPLATES
-- =============================================================================

-- Workflow templates for reusable workflow patterns
CREATE TABLE workflow_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Template identification
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Template configuration
    stages JSONB DEFAULT '[]', -- Ordered array of workflow stages
    stage_configurations JSONB DEFAULT '{}', -- Configuration for each stage
    
    -- Integration requirements
    required_integrations integration_type[],
    
    -- Template settings
    is_default BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    
    -- Usage tracking
    usage_count INTEGER DEFAULT 0,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT workflow_templates_name_org_unique UNIQUE (organization_id, name)
);

-- =============================================================================
-- WORKFLOW EXECUTIONS
-- =============================================================================

-- Main workflow executions table
CREATE TABLE workflow_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    workflow_template_id UUID REFERENCES workflow_templates(id),
    
    -- Workflow identification
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- GitHub project context
    github_repo_url TEXT NOT NULL,
    github_repo_name VARCHAR(255) NOT NULL,
    github_owner VARCHAR(255) NOT NULL,
    github_branch VARCHAR(255) DEFAULT 'main',
    
    -- Workflow status
    status workflow_status DEFAULT 'draft',
    current_stage workflow_stage DEFAULT 'project_selection',
    
    -- Requirements
    requirements_text TEXT,
    requirements_saved_at TIMESTAMP WITH TIME ZONE,
    
    -- Progress tracking
    total_stages INTEGER DEFAULT 10,
    completed_stages INTEGER DEFAULT 0,
    failed_stages INTEGER DEFAULT 0,
    
    -- Timing
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_minutes INTEGER,
    
    -- Integration tracking
    codegen_session_id VARCHAR(255),
    linear_main_issue_id VARCHAR(255),
    linear_main_issue_url TEXT,
    
    -- Development branch
    dev_branch_name VARCHAR(255),
    dev_branch_created_at TIMESTAMP WITH TIME ZONE,
    
    -- Results
    total_tasks_created INTEGER DEFAULT 0,
    total_prs_created INTEGER DEFAULT 0,
    final_pr_number INTEGER,
    final_pr_url TEXT,
    
    -- Error handling
    error_message TEXT,
    error_stage workflow_stage,
    retry_count INTEGER DEFAULT 0,
    
    -- User context
    created_by UUID REFERENCES users(id),
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT workflow_executions_stages_valid CHECK (
        total_stages >= 0 AND 
        completed_stages >= 0 AND 
        failed_stages >= 0 AND
        completed_stages <= total_stages AND
        failed_stages <= total_stages
    ),
    CONSTRAINT workflow_executions_tasks_positive CHECK (
        total_tasks_created >= 0 AND total_prs_created >= 0
    )
);

-- =============================================================================
-- WORKFLOW STAGE EXECUTIONS
-- =============================================================================

-- Individual stage executions within workflows
CREATE TABLE workflow_stage_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_execution_id UUID NOT NULL REFERENCES workflow_executions(id) ON DELETE CASCADE,
    
    -- Stage identification
    stage workflow_stage NOT NULL,
    stage_order INTEGER NOT NULL,
    stage_name VARCHAR(255),
    
    -- Stage status
    status workflow_status DEFAULT 'draft',
    
    -- Timing
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_minutes INTEGER,
    
    -- Stage configuration
    stage_config JSONB DEFAULT '{}',
    
    -- Input/Output
    input_data JSONB DEFAULT '{}',
    output_data JSONB DEFAULT '{}',
    
    -- Integration executions
    codegen_executions JSONB DEFAULT '[]', -- Array of Codegen task IDs
    github_operations JSONB DEFAULT '[]',
    linear_operations JSONB DEFAULT '[]',
    
    -- Results
    success_criteria_met BOOLEAN DEFAULT false,
    validation_results JSONB DEFAULT '{}',
    
    -- Error handling
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT workflow_stage_executions_order_positive CHECK (stage_order > 0),
    CONSTRAINT workflow_stage_executions_retry_positive CHECK (retry_count >= 0)
);

-- =============================================================================
-- INTEGRATION OPERATIONS TRACKING
-- =============================================================================

-- Codegen SDK operations within workflows
CREATE TABLE codegen_operations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_execution_id UUID NOT NULL REFERENCES workflow_executions(id) ON DELETE CASCADE,
    workflow_stage_execution_id UUID REFERENCES workflow_stage_executions(id),
    
    -- Operation details
    operation_type VARCHAR(100) NOT NULL, -- analyze_project, decompose_requirements, validate_pr
    codegen_task_id VARCHAR(255),
    
    -- Prompt and execution
    prompt_template_used VARCHAR(255),
    enhanced_prompt TEXT,
    
    -- Status and timing
    status VARCHAR(50) DEFAULT 'pending',
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER,
    
    -- Results
    response_data JSONB DEFAULT '{}',
    parsed_results JSONB DEFAULT '{}',
    
    -- Quality metrics
    quality_score DECIMAL(5,2),
    accuracy_verified BOOLEAN DEFAULT false,
    
    -- Error handling
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Linear operations within workflows
CREATE TABLE linear_operations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_execution_id UUID NOT NULL REFERENCES workflow_executions(id) ON DELETE CASCADE,
    workflow_stage_execution_id UUID REFERENCES workflow_stage_executions(id),
    
    -- Operation details
    operation_type VARCHAR(100) NOT NULL, -- create_main_issue, create_sub_issue, update_issue
    linear_issue_id VARCHAR(255),
    linear_issue_url TEXT,
    linear_issue_key VARCHAR(100),
    
    -- Issue details
    issue_title VARCHAR(500),
    issue_description TEXT,
    issue_type VARCHAR(50), -- main_issue, sub_issue
    
    -- Relationships
    parent_issue_id VARCHAR(255),
    related_step_number INTEGER,
    
    -- Status and timing
    status VARCHAR(50) DEFAULT 'pending',
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Results
    operation_results JSONB DEFAULT '{}',
    
    -- Error handling
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- GitHub operations within workflows
CREATE TABLE github_operations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_execution_id UUID NOT NULL REFERENCES workflow_executions(id) ON DELETE CASCADE,
    workflow_stage_execution_id UUID REFERENCES workflow_stage_executions(id),
    
    -- Operation details
    operation_type VARCHAR(100) NOT NULL, -- create_branch, create_pr, validate_pr, merge_pr
    
    -- GitHub references
    branch_name VARCHAR(255),
    pr_number INTEGER,
    pr_url TEXT,
    commit_sha VARCHAR(40),
    
    -- Operation details
    operation_data JSONB DEFAULT '{}',
    
    -- Status and timing
    status VARCHAR(50) DEFAULT 'pending',
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Results
    operation_results JSONB DEFAULT '{}',
    
    -- Error handling
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- WORKFLOW VALIDATION AND QUALITY CONTROL
-- =============================================================================

-- Workflow validation checkpoints
CREATE TABLE workflow_validations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_execution_id UUID NOT NULL REFERENCES workflow_executions(id) ON DELETE CASCADE,
    workflow_stage_execution_id UUID REFERENCES workflow_stage_executions(id),
    
    -- Validation details
    validation_type VARCHAR(100) NOT NULL, -- requirements_complete, steps_valid, pr_quality
    validation_name VARCHAR(255),
    
    -- Validation criteria
    validation_criteria JSONB DEFAULT '{}',
    
    -- Status
    status validation_status DEFAULT 'pending',
    
    -- Results
    validation_passed BOOLEAN,
    validation_score DECIMAL(5,2),
    validation_details JSONB DEFAULT '{}',
    
    -- Issues found
    issues_found JSONB DEFAULT '[]',
    recommendations JSONB DEFAULT '[]',
    
    -- Timing
    validated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT workflow_validations_score_valid CHECK (
        validation_score IS NULL OR 
        (validation_score >= 0 AND validation_score <= 100)
    )
);

-- =============================================================================
-- WORKFLOW ANALYTICS AND MONITORING
-- =============================================================================

-- Workflow performance metrics
CREATE TABLE workflow_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_execution_id UUID NOT NULL REFERENCES workflow_executions(id) ON DELETE CASCADE,
    
    -- Metric identification
    metric_name VARCHAR(255) NOT NULL,
    metric_category VARCHAR(100), -- performance, quality, cost, user_satisfaction
    
    -- Metric value
    metric_value DECIMAL(15,6),
    metric_unit VARCHAR(50),
    
    -- Context
    stage workflow_stage,
    measurement_context JSONB DEFAULT '{}',
    
    -- Timing
    measured_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- INDEXES FOR OPTIMAL PERFORMANCE
-- =============================================================================

-- Workflow templates indexes
CREATE INDEX idx_workflow_templates_org_id ON workflow_templates(organization_id);
CREATE INDEX idx_workflow_templates_active ON workflow_templates(is_active);
CREATE INDEX idx_workflow_templates_default ON workflow_templates(is_default);

-- Workflow executions indexes
CREATE INDEX idx_workflow_executions_org_id ON workflow_executions(organization_id);
CREATE INDEX idx_workflow_executions_status ON workflow_executions(status);
CREATE INDEX idx_workflow_executions_stage ON workflow_executions(current_stage);
CREATE INDEX idx_workflow_executions_repo ON workflow_executions(github_repo_name);
CREATE INDEX idx_workflow_executions_created_by ON workflow_executions(created_by);
CREATE INDEX idx_workflow_executions_started_at ON workflow_executions(started_at);

-- Stage executions indexes
CREATE INDEX idx_workflow_stage_executions_workflow_id ON workflow_stage_executions(workflow_execution_id);
CREATE INDEX idx_workflow_stage_executions_stage ON workflow_stage_executions(stage);
CREATE INDEX idx_workflow_stage_executions_status ON workflow_stage_executions(status);
CREATE INDEX idx_workflow_stage_executions_order ON workflow_stage_executions(stage_order);

-- Operations indexes
CREATE INDEX idx_codegen_operations_workflow_id ON codegen_operations(workflow_execution_id);
CREATE INDEX idx_codegen_operations_type ON codegen_operations(operation_type);
CREATE INDEX idx_codegen_operations_task_id ON codegen_operations(codegen_task_id);

CREATE INDEX idx_linear_operations_workflow_id ON linear_operations(workflow_execution_id);
CREATE INDEX idx_linear_operations_type ON linear_operations(operation_type);
CREATE INDEX idx_linear_operations_issue_id ON linear_operations(linear_issue_id);

CREATE INDEX idx_github_operations_workflow_id ON github_operations(workflow_execution_id);
CREATE INDEX idx_github_operations_type ON github_operations(operation_type);
CREATE INDEX idx_github_operations_pr_number ON github_operations(pr_number);

-- Validations and metrics indexes
CREATE INDEX idx_workflow_validations_workflow_id ON workflow_validations(workflow_execution_id);
CREATE INDEX idx_workflow_validations_type ON workflow_validations(validation_type);
CREATE INDEX idx_workflow_validations_status ON workflow_validations(status);

CREATE INDEX idx_workflow_metrics_workflow_id ON workflow_metrics(workflow_execution_id);
CREATE INDEX idx_workflow_metrics_name ON workflow_metrics(metric_name);
CREATE INDEX idx_workflow_metrics_category ON workflow_metrics(metric_category);
CREATE INDEX idx_workflow_metrics_measured_at ON workflow_metrics(measured_at);

-- GIN indexes for JSONB fields
CREATE INDEX idx_workflow_executions_metadata_gin USING gin (metadata);
CREATE INDEX idx_workflow_stage_executions_config_gin USING gin (stage_config);
CREATE INDEX idx_codegen_operations_response_gin USING gin (response_data);

-- =============================================================================
-- VIEWS FOR WORKFLOW MONITORING
-- =============================================================================

-- Active workflows dashboard
CREATE VIEW active_workflows_dashboard AS
SELECT 
    we.*,
    o.name as organization_name,
    u.name as created_by_name,
    COUNT(wse.id) as total_stages,
    COUNT(CASE WHEN wse.status = 'completed' THEN 1 END) as completed_stages,
    COUNT(co.id) as codegen_operations_count,
    COUNT(lo.id) as linear_operations_count,
    COUNT(go.id) as github_operations_count
FROM workflow_executions we
JOIN organizations o ON we.organization_id = o.id
LEFT JOIN users u ON we.created_by = u.id
LEFT JOIN workflow_stage_executions wse ON we.id = wse.workflow_execution_id
LEFT JOIN codegen_operations co ON we.id = co.workflow_execution_id
LEFT JOIN linear_operations lo ON we.id = lo.workflow_execution_id
LEFT JOIN github_operations go ON we.id = go.workflow_execution_id
WHERE we.status IN ('active', 'paused')
GROUP BY we.id, o.name, u.name;

-- Workflow performance summary
CREATE VIEW workflow_performance_summary AS
SELECT 
    we.id,
    we.name,
    we.status,
    we.current_stage,
    we.duration_minutes,
    we.total_tasks_created,
    we.total_prs_created,
    COUNT(wv.id) as total_validations,
    COUNT(CASE WHEN wv.validation_passed = true THEN 1 END) as passed_validations,
    AVG(wv.validation_score) as avg_validation_score,
    COUNT(wm.id) as metrics_collected
FROM workflow_executions we
LEFT JOIN workflow_validations wv ON we.id = wv.workflow_execution_id
LEFT JOIN workflow_metrics wm ON we.id = wm.workflow_execution_id
GROUP BY we.id, we.name, we.status, we.current_stage, we.duration_minutes, 
         we.total_tasks_created, we.total_prs_created;

-- Grant permissions to workflows_user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO workflows_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO workflows_user;
GRANT USAGE ON SCHEMA public TO workflows_user;

-- Insert default organization
INSERT INTO organizations (name, slug, description) VALUES 
('Default Organization', 'default', 'Default organization for workflow orchestration');

-- Insert default admin user
INSERT INTO users (organization_id, name, email, role, can_manage_workflows) VALUES 
((SELECT id FROM organizations WHERE slug = 'default'), 'Workflow Admin', 'admin@workflows.local', 'admin', true);

-- Insert default workflow template
INSERT INTO workflow_templates (
    organization_id, name, description, stages, stage_configurations, 
    required_integrations, is_default
) VALUES (
    (SELECT id FROM organizations WHERE slug = 'default'),
    'GitHub Project Complete Workflow',
    'Complete workflow for GitHub project from selection to completion',
    '["project_selection", "requirements_input", "requirements_decomposition", "linear_main_issue_creation", "linear_sub_issues_creation", "task_execution", "pr_validation", "completion"]',
    '{
        "project_selection": {"timeout_minutes": 30, "validation_required": true},
        "requirements_input": {"timeout_minutes": 60, "validation_required": true},
        "requirements_decomposition": {"timeout_minutes": 45, "codegen_required": true},
        "linear_main_issue_creation": {"timeout_minutes": 15, "linear_required": true},
        "linear_sub_issues_creation": {"timeout_minutes": 30, "linear_required": true},
        "task_execution": {"timeout_minutes": 480, "codegen_required": true},
        "pr_validation": {"timeout_minutes": 60, "validation_required": true},
        "completion": {"timeout_minutes": 15, "cleanup_required": true}
    }',
    ARRAY['github', 'linear', 'codegen_sdk'],
    true
);

-- Final status message
DO $$
BEGIN
    RAISE NOTICE '🔄 Workflows Database initialized successfully!';
    RAISE NOTICE 'Features: Complete workflow orchestration, Multi-integration support, Stage tracking';
    RAISE NOTICE 'Integrations: GitHub, Linear, Codegen SDK, validation systems';
    RAISE NOTICE 'Workflow stages: Project selection → Requirements → Decomposition → Linear issues → Execution → Validation → Completion';
    RAISE NOTICE 'Default template: GitHub Project Complete Workflow';
    RAISE NOTICE 'Timestamp: %', NOW();
END $$;

