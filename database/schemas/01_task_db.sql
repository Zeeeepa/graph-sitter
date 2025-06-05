-- =============================================================================
-- TASK DATABASE SCHEMA: Task Context, Execution Tracking, and Dependencies
-- =============================================================================
-- This database handles comprehensive task management including task definitions,
-- execution tracking, dependency management, workflow orchestration, and
-- resource monitoring.
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

-- Task-specific enums
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
    'custom'
);

CREATE TYPE dependency_type AS ENUM (
    'blocks',
    'depends_on',
    'related_to',
    'subtask_of',
    'triggers',
    'conflicts_with'
);

CREATE TYPE workflow_type AS ENUM (
    'sequential',
    'parallel',
    'conditional',
    'dag',
    'pipeline',
    'custom'
);

CREATE TYPE execution_mode AS ENUM (
    'manual',
    'automatic',
    'scheduled',
    'triggered',
    'continuous'
);

CREATE TYPE priority_level AS ENUM (
    'low',
    'normal', 
    'high',
    'urgent',
    'critical'
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

-- Users table for task assignment
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
-- TASK DEFINITIONS AND TEMPLATES
-- =============================================================================

-- Task definitions for reusable task templates
CREATE TABLE task_definitions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Definition identification
    name VARCHAR(255) NOT NULL,
    description TEXT,
    task_type task_type NOT NULL,
    category VARCHAR(100),
    
    -- Task configuration
    default_config JSONB DEFAULT '{}',
    required_inputs JSONB DEFAULT '[]',
    expected_outputs JSONB DEFAULT '[]',
    
    -- Resource requirements
    estimated_duration_minutes INTEGER,
    cpu_requirements DECIMAL(5,2), -- CPU cores
    memory_requirements_mb INTEGER,
    storage_requirements_mb INTEGER,
    
    -- Execution configuration
    execution_mode execution_mode DEFAULT 'manual',
    retry_config JSONB DEFAULT '{}',
    timeout_minutes INTEGER DEFAULT 60,
    
    -- Template and scripting
    script_template TEXT,
    command_template TEXT,
    environment_config JSONB DEFAULT '{}',
    
    -- Validation and constraints
    validation_rules JSONB DEFAULT '{}',
    prerequisites JSONB DEFAULT '[]',
    
    -- Usage and versioning
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT true,
    usage_count INTEGER DEFAULT 0,
    
    -- Metadata
    tags VARCHAR(50)[],
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT task_definitions_name_org_unique UNIQUE (organization_id, name),
    CONSTRAINT task_definitions_name_not_empty CHECK (length(trim(name)) > 0),
    CONSTRAINT task_definitions_version_positive CHECK (version > 0)
);

-- =============================================================================
-- TASKS AND EXECUTION
-- =============================================================================

-- Main tasks table
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    task_definition_id UUID REFERENCES task_definitions(id),
    
    -- Task identification
    name VARCHAR(255) NOT NULL,
    description TEXT,
    task_type task_type NOT NULL,
    
    -- Task hierarchy
    parent_task_id UUID REFERENCES tasks(id),
    root_task_id UUID REFERENCES tasks(id),
    task_level INTEGER DEFAULT 0,
    
    -- Task configuration
    configuration JSONB DEFAULT '{}',
    input_data JSONB DEFAULT '{}',
    output_data JSONB DEFAULT '{}',
    
    -- Status and progress
    status task_status DEFAULT 'draft',
    progress_percentage DECIMAL(5,2) DEFAULT 0,
    priority priority_level DEFAULT 'normal',
    
    -- Assignment and ownership
    assigned_to UUID REFERENCES users(id),
    created_by UUID REFERENCES users(id),
    assigned_at TIMESTAMP WITH TIME ZONE,
    
    -- Timing and scheduling
    scheduled_at TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    due_date TIMESTAMP WITH TIME ZONE,
    
    -- Duration tracking
    estimated_duration_minutes INTEGER,
    actual_duration_minutes INTEGER,
    
    -- Resource tracking
    cpu_usage_percent DECIMAL(5,2),
    memory_usage_mb INTEGER,
    storage_usage_mb INTEGER,
    
    -- Execution details
    execution_mode execution_mode DEFAULT 'manual',
    execution_environment JSONB DEFAULT '{}',
    execution_log TEXT,
    error_message TEXT,
    
    -- Retry and recovery
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    last_retry_at TIMESTAMP WITH TIME ZONE,
    
    -- Quality and validation
    quality_score DECIMAL(5,2),
    validation_results JSONB DEFAULT '{}',
    
    -- External references
    external_task_id VARCHAR(255),
    external_url TEXT,
    
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

-- Task dependencies for complex workflow management
CREATE TABLE dependencies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Dependency relationship
    source_task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    target_task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    
    -- Dependency details
    dependency_type dependency_type NOT NULL,
    description TEXT,
    
    -- Dependency configuration
    is_hard_dependency BOOLEAN DEFAULT true,
    delay_minutes INTEGER DEFAULT 0,
    condition_config JSONB DEFAULT '{}',
    
    -- Status tracking
    is_satisfied BOOLEAN DEFAULT false,
    satisfied_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT dependencies_unique UNIQUE (source_task_id, target_task_id, dependency_type),
    CONSTRAINT dependencies_no_self_reference CHECK (source_task_id != target_task_id)
);

-- =============================================================================
-- WORKFLOWS AND ORCHESTRATION
-- =============================================================================

-- Workflows for task orchestration
CREATE TABLE workflows (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Workflow identification
    name VARCHAR(255) NOT NULL,
    description TEXT,
    workflow_type workflow_type NOT NULL,
    
    -- Workflow configuration
    configuration JSONB DEFAULT '{}',
    execution_plan JSONB DEFAULT '{}',
    
    -- Workflow status
    status VARCHAR(20) DEFAULT 'active',
    is_template BOOLEAN DEFAULT false,
    
    -- Execution tracking
    execution_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    
    -- Timing configuration
    schedule_config JSONB DEFAULT '{}',
    timeout_minutes INTEGER DEFAULT 240,
    
    -- Triggers and conditions
    trigger_config JSONB DEFAULT '{}',
    conditions JSONB DEFAULT '{}',
    
    -- Metadata
    tags VARCHAR(50)[],
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT workflows_name_org_unique UNIQUE (organization_id, name),
    CONSTRAINT workflows_name_not_empty CHECK (length(trim(name)) > 0)
);

-- =============================================================================
-- INDEXES FOR OPTIMAL PERFORMANCE
-- =============================================================================

-- Task definitions indexes
CREATE INDEX idx_task_definitions_org_id ON task_definitions(organization_id);
CREATE INDEX idx_task_definitions_type ON task_definitions(task_type);
CREATE INDEX idx_task_definitions_active ON task_definitions(is_active) WHERE deleted_at IS NULL;

-- Tasks indexes
CREATE INDEX idx_tasks_org_id ON tasks(organization_id);
CREATE INDEX idx_tasks_definition_id ON tasks(task_definition_id);
CREATE INDEX idx_tasks_parent_id ON tasks(parent_task_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_priority ON tasks(priority);
CREATE INDEX idx_tasks_assigned_to ON tasks(assigned_to);
CREATE INDEX idx_tasks_created_by ON tasks(created_by);

-- Dependencies indexes
CREATE INDEX idx_dependencies_source ON dependencies(source_task_id);
CREATE INDEX idx_dependencies_target ON dependencies(target_task_id);
CREATE INDEX idx_dependencies_type ON dependencies(dependency_type);

-- Workflows indexes
CREATE INDEX idx_workflows_org_id ON workflows(organization_id);
CREATE INDEX idx_workflows_type ON workflows(workflow_type);
CREATE INDEX idx_workflows_status ON workflows(status) WHERE deleted_at IS NULL;

-- GIN indexes for JSONB fields
CREATE INDEX idx_task_definitions_config_gin USING gin (default_config);
CREATE INDEX idx_tasks_configuration_gin USING gin (configuration);
CREATE INDEX idx_tasks_metadata_gin USING gin (metadata);

-- Grant permissions to task_user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO task_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO task_user;
GRANT USAGE ON SCHEMA public TO task_user;

-- Insert default organization
INSERT INTO organizations (name, slug, description) VALUES 
('Default Organization', 'default', 'Default organization for task management');

-- Insert default admin user
INSERT INTO users (organization_id, name, email, role) VALUES 
((SELECT id FROM organizations WHERE slug = 'default'), 'Task Admin', 'admin@task.local', 'admin');

-- Final status message
DO $$
BEGIN
    RAISE NOTICE '📋 Task Database initialized successfully!';
    RAISE NOTICE 'Features: Task definitions, Dependencies, Workflows, Resource tracking';
    RAISE NOTICE 'Timestamp: %', NOW();
END $$;

