-- =============================================================================
-- ENHANCED TASK DATABASE SCHEMA: GitHub Project Workflow Integration
-- =============================================================================
-- This database handles comprehensive task management with specific support for:
-- - GitHub project selection & pinning workflow
-- - Requirements decomposition into steps
-- - Linear issue creation & tracking
-- - PR validation & dev-branch management
-- - Codegen SDK API integration with enhanced prompting
-- =============================================================================

-- Connect to task_db
\c task_db;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- Set timezone and configuration
SET timezone = 'UTC';
SET default_text_search_config = 'pg_catalog.english';

-- Grant all privileges to task_user
GRANT ALL PRIVILEGES ON DATABASE task_db TO task_user;
GRANT ALL PRIVILEGES ON SCHEMA public TO task_user;

-- Enhanced task-specific enums
CREATE TYPE task_status AS ENUM (
    'draft',
    'pending',
    'assigned',
    'in_progress',
    'blocked',
    'review',
    'completed',
    'failed',
    'cancelled',
    'archived'
);

CREATE TYPE task_type AS ENUM (
    'requirement_analysis',
    'step_decomposition',
    'code_analysis',
    'code_generation',
    'code_review',
    'testing',
    'deployment',
    'documentation',
    'research',
    'bug_fix',
    'feature_development',
    'optimization',
    'maintenance',
    'pr_validation',
    'linear_integration',
    'custom'
);

CREATE TYPE workflow_stage AS ENUM (
    'project_selection',
    'requirements_input',
    'requirements_decomposition',
    'step_planning',
    'linear_issue_creation',
    'task_execution',
    'pr_creation',
    'pr_validation',
    'dev_branch_merge',
    'completion'
);

CREATE TYPE execution_mode AS ENUM (
    'manual',
    'automatic',
    'scheduled',
    'triggered',
    'continuous',
    'codegen_sdk'
);

CREATE TYPE priority_level AS ENUM (
    'low',
    'normal', 
    'high',
    'urgent',
    'critical'
);

-- =============================================================================
-- CORE REFERENCE TABLES WITH INTEGRATIONS
-- =============================================================================

-- Organizations with Codegen SDK integration
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    
    -- Codegen SDK integration
    codegen_org_id VARCHAR(255),
    codegen_api_token_encrypted TEXT,
    
    -- Integration settings
    github_integration_enabled BOOLEAN DEFAULT true,
    linear_integration_enabled BOOLEAN DEFAULT true,
    
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Users with external integrations
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(50) DEFAULT 'member',
    
    -- External integrations
    github_username VARCHAR(255),
    linear_user_id VARCHAR(255),
    
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- GITHUB PROJECT WORKFLOW MANAGEMENT
-- =============================================================================

-- GitHub projects for dashboard integration
CREATE TABLE github_projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- GitHub project details
    github_repo_url TEXT NOT NULL,
    github_repo_name VARCHAR(255) NOT NULL,
    github_owner VARCHAR(255) NOT NULL,
    github_repo_id VARCHAR(255),
    
    -- Dashboard integration
    is_pinned BOOLEAN DEFAULT false,
    pin_order INTEGER,
    dashboard_position JSONB DEFAULT '{}',
    
    -- Project status
    is_active BOOLEAN DEFAULT true,
    last_analyzed_at TIMESTAMP WITH TIME ZONE,
    analysis_status VARCHAR(50) DEFAULT 'pending',
    
    -- Requirements workflow
    requirements_text TEXT,
    requirements_saved_at TIMESTAMP WITH TIME ZONE,
    requirements_version INTEGER DEFAULT 1,
    
    -- Workflow state tracking
    current_stage workflow_stage DEFAULT 'project_selection',
    workflow_started BOOLEAN DEFAULT false,
    workflow_started_at TIMESTAMP WITH TIME ZONE,
    workflow_completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Linear integration
    linear_main_issue_id VARCHAR(255),
    linear_main_issue_url TEXT,
    linear_main_issue_key VARCHAR(100),
    
    -- Development branch management
    dev_branch_name VARCHAR(255),
    dev_branch_created_at TIMESTAMP WITH TIME ZONE,
    dev_branch_status VARCHAR(50) DEFAULT 'pending',
    
    -- Progress tracking
    total_steps INTEGER DEFAULT 0,
    completed_steps INTEGER DEFAULT 0,
    failed_steps INTEGER DEFAULT 0,
    
    -- Metadata
    project_structure JSONB DEFAULT '{}',
    analysis_results JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT github_projects_repo_org_unique UNIQUE (organization_id, github_repo_url),
    CONSTRAINT github_projects_repo_name_not_empty CHECK (length(trim(github_repo_name)) > 0),
    CONSTRAINT github_projects_steps_valid CHECK (
        total_steps >= 0 AND 
        completed_steps >= 0 AND 
        failed_steps >= 0 AND
        completed_steps <= total_steps AND
        failed_steps <= total_steps
    )
);

-- =============================================================================
-- REQUIREMENT DECOMPOSITION AND STEP PLANNING
-- =============================================================================

-- Requirements decomposition results
CREATE TABLE requirement_decompositions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    github_project_id UUID NOT NULL REFERENCES github_projects(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Decomposition details
    original_requirements TEXT NOT NULL,
    decomposition_prompt TEXT,
    
    -- Codegen SDK execution
    codegen_task_id VARCHAR(255),
    codegen_response JSONB DEFAULT '{}',
    
    -- Decomposition results
    total_steps INTEGER DEFAULT 0,
    steps_data JSONB DEFAULT '[]',
    
    -- Analysis context
    project_structure_analyzed JSONB DEFAULT '{}',
    dependencies_identified JSONB DEFAULT '[]',
    
    -- Status
    status VARCHAR(50) DEFAULT 'pending',
    
    -- Quality metrics
    decomposition_quality_score DECIMAL(5,2),
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT requirement_decompositions_total_steps_positive CHECK (total_steps >= 0),
    CONSTRAINT requirement_decompositions_quality_valid CHECK (
        decomposition_quality_score IS NULL OR 
        (decomposition_quality_score >= 0 AND decomposition_quality_score <= 100)
    )
);

-- Individual decomposed steps
CREATE TABLE decomposed_steps (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    requirement_decomposition_id UUID NOT NULL REFERENCES requirement_decompositions(id) ON DELETE CASCADE,
    github_project_id UUID NOT NULL REFERENCES github_projects(id) ON DELETE CASCADE,
    
    -- Step identification
    step_number INTEGER NOT NULL,
    step_name VARCHAR(255) NOT NULL,
    step_description TEXT,
    
    -- Step requirements
    specific_requirements JSONB DEFAULT '[]',
    success_criteria JSONB DEFAULT '[]',
    acceptance_criteria JSONB DEFAULT '[]',
    
    -- Dependencies
    depends_on_steps INTEGER[],
    blocks_steps INTEGER[],
    
    -- Implementation details
    implementation_approach TEXT,
    technical_requirements JSONB DEFAULT '{}',
    
    -- Estimation
    estimated_effort_hours DECIMAL(5,2),
    complexity_score INTEGER, -- 1-10 scale
    
    -- Status tracking
    status task_status DEFAULT 'draft',
    
    -- Linear integration
    linear_sub_issue_id VARCHAR(255),
    linear_sub_issue_url TEXT,
    linear_sub_issue_key VARCHAR(100),
    
    -- Task association
    associated_task_id UUID,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT decomposed_steps_step_number_positive CHECK (step_number > 0),
    CONSTRAINT decomposed_steps_complexity_valid CHECK (complexity_score >= 1 AND complexity_score <= 10),
    CONSTRAINT decomposed_steps_effort_positive CHECK (estimated_effort_hours >= 0)
);

-- =============================================================================
-- ENHANCED TASKS WITH WORKFLOW INTEGRATION
-- =============================================================================

-- Main tasks table with comprehensive workflow support
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    github_project_id UUID REFERENCES github_projects(id),
    decomposed_step_id UUID REFERENCES decomposed_steps(id),
    
    -- Task identification
    name VARCHAR(255) NOT NULL,
    description TEXT,
    task_type task_type NOT NULL,
    
    -- Requirements context
    original_requirement TEXT,
    step_requirements JSONB DEFAULT '[]',
    success_criteria JSONB DEFAULT '[]',
    
    -- Task hierarchy
    parent_task_id UUID REFERENCES tasks(id),
    root_task_id UUID REFERENCES tasks(id),
    task_level INTEGER DEFAULT 0,
    
    -- Status and progress
    status task_status DEFAULT 'draft',
    progress_percentage DECIMAL(5,2) DEFAULT 0,
    priority priority_level DEFAULT 'normal',
    
    -- Assignment and ownership
    assigned_to UUID REFERENCES users(id),
    created_by UUID REFERENCES users(id),
    assigned_at TIMESTAMP WITH TIME ZONE,
    
    -- Timing
    scheduled_at TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    due_date TIMESTAMP WITH TIME ZONE,
    estimated_duration_minutes INTEGER,
    actual_duration_minutes INTEGER,
    
    -- Codegen SDK integration
    codegen_task_id VARCHAR(255),
    codegen_prompt_used TEXT,
    codegen_response JSONB DEFAULT '{}',
    prompt_enhancement_applied BOOLEAN DEFAULT false,
    
    -- Linear integration
    linear_sub_issue_id VARCHAR(255),
    linear_sub_issue_url TEXT,
    linear_sub_issue_status VARCHAR(50),
    
    -- PR tracking and validation
    github_pr_number INTEGER,
    github_pr_url TEXT,
    pr_validation_status VARCHAR(50),
    pr_validation_results JSONB DEFAULT '{}',
    code_changes_validated BOOLEAN DEFAULT false,
    
    -- Execution details
    execution_mode execution_mode DEFAULT 'manual',
    execution_log TEXT,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    
    -- Quality metrics
    quality_score DECIMAL(5,2),
    validation_results JSONB DEFAULT '{}',
    
    -- Configuration
    configuration JSONB DEFAULT '{}',
    input_data JSONB DEFAULT '{}',
    output_data JSONB DEFAULT '{}',
    
    -- Metadata
    tags VARCHAR(50)[],
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT tasks_name_not_empty CHECK (length(trim(name)) > 0),
    CONSTRAINT tasks_progress_valid CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
    CONSTRAINT tasks_retry_count_valid CHECK (retry_count >= 0),
    CONSTRAINT tasks_level_valid CHECK (task_level >= 0)
);

-- =============================================================================
-- WORKFLOW ORCHESTRATION
-- =============================================================================

-- Workflow executions for tracking complete project workflows
CREATE TABLE workflow_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    github_project_id UUID NOT NULL REFERENCES github_projects(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Workflow identification
    workflow_name VARCHAR(255) DEFAULT 'GitHub Project Workflow',
    current_stage workflow_stage DEFAULT 'project_selection',
    
    -- Workflow status
    status VARCHAR(50) DEFAULT 'running',
    
    -- Stage tracking
    stages_completed workflow_stage[],
    current_stage_started_at TIMESTAMP WITH TIME ZONE,
    
    -- Progress tracking
    total_tasks INTEGER DEFAULT 0,
    completed_tasks INTEGER DEFAULT 0,
    failed_tasks INTEGER DEFAULT 0,
    
    -- Timing
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_minutes INTEGER,
    
    -- Results
    workflow_results JSONB DEFAULT '{}',
    final_dev_branch VARCHAR(255),
    main_pr_number INTEGER,
    
    -- Error handling
    error_message TEXT,
    last_error_stage workflow_stage,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT workflow_executions_tasks_valid CHECK (
        total_tasks >= 0 AND 
        completed_tasks >= 0 AND 
        failed_tasks >= 0 AND
        completed_tasks <= total_tasks AND
        failed_tasks <= total_tasks
    )
);

-- =============================================================================
-- PROMPT ENHANCEMENT AND TRACKING
-- =============================================================================

-- Prompt enhancement rules and tracking
CREATE TABLE prompt_enhancements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Enhancement identification
    enhancement_name VARCHAR(255) NOT NULL,
    enhancement_type VARCHAR(100), -- context_injection, accuracy_boost, format_optimization
    
    -- Enhancement rules
    enhancement_rules JSONB DEFAULT '{}',
    trigger_conditions JSONB DEFAULT '{}',
    
    -- Effectiveness tracking
    usage_count INTEGER DEFAULT 0,
    success_rate DECIMAL(5,2) DEFAULT 0,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT prompt_enhancements_name_org_unique UNIQUE (organization_id, enhancement_name),
    CONSTRAINT prompt_enhancements_success_rate_valid CHECK (success_rate >= 0 AND success_rate <= 100)
);

-- =============================================================================
-- INDEXES FOR OPTIMAL PERFORMANCE
-- =============================================================================

-- GitHub projects indexes
CREATE INDEX idx_github_projects_org_id ON github_projects(organization_id);
CREATE INDEX idx_github_projects_pinned ON github_projects(is_pinned, pin_order);
CREATE INDEX idx_github_projects_active ON github_projects(is_active);
CREATE INDEX idx_github_projects_stage ON github_projects(current_stage);
CREATE INDEX idx_github_projects_repo_name ON github_projects(github_repo_name);

-- Requirement decompositions indexes
CREATE INDEX idx_requirement_decompositions_project_id ON requirement_decompositions(github_project_id);
CREATE INDEX idx_requirement_decompositions_status ON requirement_decompositions(status);
CREATE INDEX idx_requirement_decompositions_created_at ON requirement_decompositions(created_at);

-- Decomposed steps indexes
CREATE INDEX idx_decomposed_steps_decomposition_id ON decomposed_steps(requirement_decomposition_id);
CREATE INDEX idx_decomposed_steps_project_id ON decomposed_steps(github_project_id);
CREATE INDEX idx_decomposed_steps_step_number ON decomposed_steps(step_number);
CREATE INDEX idx_decomposed_steps_status ON decomposed_steps(status);
CREATE INDEX idx_decomposed_steps_linear_issue ON decomposed_steps(linear_sub_issue_id);

-- Enhanced tasks indexes
CREATE INDEX idx_tasks_org_id ON tasks(organization_id);
CREATE INDEX idx_tasks_project_id ON tasks(github_project_id);
CREATE INDEX idx_tasks_step_id ON tasks(decomposed_step_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_type ON tasks(task_type);
CREATE INDEX idx_tasks_assigned_to ON tasks(assigned_to);
CREATE INDEX idx_tasks_codegen_task_id ON tasks(codegen_task_id);
CREATE INDEX idx_tasks_linear_issue ON tasks(linear_sub_issue_id);
CREATE INDEX idx_tasks_pr_number ON tasks(github_pr_number);

-- Workflow executions indexes
CREATE INDEX idx_workflow_executions_project_id ON workflow_executions(github_project_id);
CREATE INDEX idx_workflow_executions_stage ON workflow_executions(current_stage);
CREATE INDEX idx_workflow_executions_status ON workflow_executions(status);
CREATE INDEX idx_workflow_executions_started_at ON workflow_executions(started_at);

-- Prompt enhancements indexes
CREATE INDEX idx_prompt_enhancements_org_id ON prompt_enhancements(organization_id);
CREATE INDEX idx_prompt_enhancements_type ON prompt_enhancements(enhancement_type);
CREATE INDEX idx_prompt_enhancements_active ON prompt_enhancements(is_active);

-- GIN indexes for JSONB fields
CREATE INDEX idx_github_projects_metadata_gin USING gin (metadata);
CREATE INDEX idx_requirement_decompositions_steps_gin USING gin (steps_data);
CREATE INDEX idx_decomposed_steps_requirements_gin USING gin (specific_requirements);
CREATE INDEX idx_tasks_configuration_gin USING gin (configuration);
CREATE INDEX idx_tasks_codegen_response_gin USING gin (codegen_response);

-- =============================================================================
-- VIEWS FOR WORKFLOW MONITORING
-- =============================================================================

-- Dashboard project overview
CREATE VIEW dashboard_projects AS
SELECT 
    gp.*,
    o.name as organization_name,
    COUNT(ds.id) as total_decomposed_steps,
    COUNT(CASE WHEN ds.status = 'completed' THEN 1 END) as completed_steps,
    COUNT(t.id) as total_tasks,
    COUNT(CASE WHEN t.status = 'completed' THEN 1 END) as completed_tasks,
    we.current_stage as workflow_stage,
    we.status as workflow_status
FROM github_projects gp
JOIN organizations o ON gp.organization_id = o.id
LEFT JOIN decomposed_steps ds ON gp.id = ds.github_project_id
LEFT JOIN tasks t ON gp.id = t.github_project_id
LEFT JOIN workflow_executions we ON gp.id = we.github_project_id AND we.status = 'running'
GROUP BY gp.id, o.name, we.current_stage, we.status
ORDER BY gp.is_pinned DESC, gp.pin_order ASC, gp.updated_at DESC;

-- Active workflow tracking
CREATE VIEW active_workflows AS
SELECT 
    we.*,
    gp.github_repo_name,
    gp.requirements_text,
    COUNT(t.id) as associated_tasks,
    COUNT(CASE WHEN t.status = 'completed' THEN 1 END) as completed_tasks
FROM workflow_executions we
JOIN github_projects gp ON we.github_project_id = gp.id
LEFT JOIN tasks t ON gp.id = t.github_project_id
WHERE we.status IN ('running', 'paused')
GROUP BY we.id, gp.github_repo_name, gp.requirements_text;

-- Step execution progress
CREATE VIEW step_execution_progress AS
SELECT 
    ds.*,
    gp.github_repo_name,
    t.status as task_status,
    t.codegen_task_id,
    t.github_pr_number,
    t.pr_validation_status
FROM decomposed_steps ds
JOIN github_projects gp ON ds.github_project_id = gp.id
LEFT JOIN tasks t ON ds.id = t.decomposed_step_id
ORDER BY ds.step_number;

-- Grant permissions to task_user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO task_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO task_user;
GRANT USAGE ON SCHEMA public TO task_user;

-- Insert default organization
INSERT INTO organizations (name, slug, description) VALUES 
('Default Organization', 'default', 'Default organization for GitHub project workflow management');

-- Insert default admin user
INSERT INTO users (organization_id, name, email, role) VALUES 
((SELECT id FROM organizations WHERE slug = 'default'), 'Workflow Admin', 'admin@workflow.local', 'admin');

-- Final status message
DO $$
BEGIN
    RAISE NOTICE '🚀 Enhanced Task Database initialized successfully!';
    RAISE NOTICE 'Features: GitHub project workflow, Requirements decomposition, Linear integration, PR validation';
    RAISE NOTICE 'Workflow stages: Project selection → Requirements → Decomposition → Linear issues → Task execution → PR validation';
    RAISE NOTICE 'Codegen SDK integration: Enhanced prompting, API token management, response tracking';
    RAISE NOTICE 'Timestamp: %', NOW();
END $$;

