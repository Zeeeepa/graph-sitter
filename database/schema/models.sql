-- Core Database Schema for Graph-Sitter
-- Comprehensive database schema covering tasks, codebase, prompts, and analytics

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable full-text search
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Core Tables

-- Organizations/Projects
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    avatar_url TEXT,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Organization memberships
CREATE TABLE organization_memberships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL DEFAULT 'member',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(organization_id, user_id)
);

-- Codebases
CREATE TABLE codebases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    repository_url TEXT,
    repository_path TEXT,
    language VARCHAR(50),
    branch VARCHAR(255) DEFAULT 'main',
    last_analyzed_at TIMESTAMP WITH TIME ZONE,
    analysis_status VARCHAR(50) DEFAULT 'pending',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(organization_id, name)
);

-- Files in codebases
CREATE TABLE codebase_files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    codebase_id UUID NOT NULL REFERENCES codebases(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_extension VARCHAR(50),
    file_size BIGINT,
    content_hash VARCHAR(64),
    last_modified TIMESTAMP WITH TIME ZONE,
    is_deleted BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(codebase_id, file_path)
);

-- Code symbols (classes, functions, variables, etc.)
CREATE TABLE code_symbols (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    file_id UUID NOT NULL REFERENCES codebase_files(id) ON DELETE CASCADE,
    symbol_type VARCHAR(50) NOT NULL, -- 'class', 'function', 'variable', 'interface', 'type_alias'
    name VARCHAR(255) NOT NULL,
    qualified_name TEXT,
    start_line INTEGER,
    end_line INTEGER,
    start_column INTEGER,
    end_column INTEGER,
    visibility VARCHAR(20), -- 'public', 'private', 'protected'
    is_exported BOOLEAN DEFAULT FALSE,
    signature TEXT,
    docstring TEXT,
    complexity_score INTEGER,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Symbol dependencies (imports, calls, inheritance, etc.)
CREATE TABLE symbol_dependencies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_symbol_id UUID NOT NULL REFERENCES code_symbols(id) ON DELETE CASCADE,
    target_symbol_id UUID REFERENCES code_symbols(id) ON DELETE CASCADE,
    target_external_name TEXT, -- For external dependencies
    dependency_type VARCHAR(50) NOT NULL, -- 'import', 'call', 'inheritance', 'composition', 'reference'
    line_number INTEGER,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tasks
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    codebase_id UUID REFERENCES codebases(id) ON DELETE SET NULL,
    parent_task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    task_type VARCHAR(50) NOT NULL, -- 'analysis', 'refactor', 'feature', 'bug_fix', 'documentation'
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- 'pending', 'in_progress', 'completed', 'failed', 'cancelled'
    priority INTEGER DEFAULT 0,
    complexity_score INTEGER,
    estimated_duration INTERVAL,
    actual_duration INTERVAL,
    assigned_to UUID REFERENCES users(id) ON DELETE SET NULL,
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    dependencies JSONB DEFAULT '[]', -- Array of task IDs this task depends on
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Task files (files affected by a task)
CREATE TABLE task_files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    file_id UUID NOT NULL REFERENCES codebase_files(id) ON DELETE CASCADE,
    operation_type VARCHAR(50) NOT NULL, -- 'create', 'modify', 'delete', 'move'
    changes_summary TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(task_id, file_id)
);

-- Prompts
CREATE TABLE prompts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    content TEXT NOT NULL,
    prompt_type VARCHAR(50) NOT NULL, -- 'system', 'user', 'template', 'codemod'
    category VARCHAR(100),
    tags TEXT[],
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    usage_count INTEGER DEFAULT 0,
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Prompt versions for tracking changes
CREATE TABLE prompt_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prompt_id UUID NOT NULL REFERENCES prompts(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    content TEXT NOT NULL,
    changes_summary TEXT,
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(prompt_id, version)
);

-- Analytics tables
CREATE TABLE analysis_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    codebase_id UUID NOT NULL REFERENCES codebases(id) ON DELETE CASCADE,
    analysis_type VARCHAR(100) NOT NULL, -- 'full', 'incremental', 'dependency', 'metrics', 'dead_code'
    status VARCHAR(50) NOT NULL DEFAULT 'running', -- 'running', 'completed', 'failed'
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    duration INTERVAL,
    results JSONB DEFAULT '{}',
    error_message TEXT,
    metadata JSONB DEFAULT '{}'
);

-- Code metrics
CREATE TABLE code_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_run_id UUID NOT NULL REFERENCES analysis_runs(id) ON DELETE CASCADE,
    file_id UUID REFERENCES codebase_files(id) ON DELETE CASCADE,
    symbol_id UUID REFERENCES code_symbols(id) ON DELETE CASCADE,
    metric_type VARCHAR(100) NOT NULL, -- 'cyclomatic_complexity', 'lines_of_code', 'maintainability_index', 'cognitive_complexity'
    metric_value NUMERIC NOT NULL,
    threshold_status VARCHAR(20), -- 'good', 'warning', 'critical'
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Dead code detection
CREATE TABLE dead_code_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_run_id UUID NOT NULL REFERENCES analysis_runs(id) ON DELETE CASCADE,
    symbol_id UUID NOT NULL REFERENCES code_symbols(id) ON DELETE CASCADE,
    dead_code_type VARCHAR(50) NOT NULL, -- 'unused_function', 'unused_class', 'unused_variable', 'unreachable_code'
    confidence_score NUMERIC(3,2), -- 0.00 to 1.00
    reason TEXT,
    suggested_action VARCHAR(100), -- 'remove', 'review', 'keep'
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Dependency graph analysis
CREATE TABLE dependency_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_run_id UUID NOT NULL REFERENCES analysis_runs(id) ON DELETE CASCADE,
    source_file_id UUID NOT NULL REFERENCES codebase_files(id) ON DELETE CASCADE,
    target_file_id UUID REFERENCES codebase_files(id) ON DELETE CASCADE,
    target_external_name TEXT, -- For external dependencies
    dependency_strength INTEGER DEFAULT 1, -- Number of dependencies between files
    is_circular BOOLEAN DEFAULT FALSE,
    path_length INTEGER, -- Shortest path in dependency graph
    metadata JSONB DEFAULT '{}'
);

-- Impact analysis
CREATE TABLE impact_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_run_id UUID NOT NULL REFERENCES analysis_runs(id) ON DELETE CASCADE,
    changed_symbol_id UUID NOT NULL REFERENCES code_symbols(id) ON DELETE CASCADE,
    impacted_symbol_id UUID NOT NULL REFERENCES code_symbols(id) ON DELETE CASCADE,
    impact_type VARCHAR(50) NOT NULL, -- 'direct', 'indirect', 'transitive'
    impact_severity VARCHAR(20) NOT NULL, -- 'low', 'medium', 'high', 'critical'
    impact_radius INTEGER, -- Number of hops in dependency chain
    estimated_effort INTEGER, -- Estimated effort to handle the impact
    metadata JSONB DEFAULT '{}'
);

-- Indexes for performance
CREATE INDEX idx_codebase_files_codebase_id ON codebase_files(codebase_id);
CREATE INDEX idx_codebase_files_path ON codebase_files(file_path);
CREATE INDEX idx_codebase_files_extension ON codebase_files(file_extension);
CREATE INDEX idx_code_symbols_file_id ON code_symbols(file_id);
CREATE INDEX idx_code_symbols_type ON code_symbols(symbol_type);
CREATE INDEX idx_code_symbols_name ON code_symbols(name);
CREATE INDEX idx_symbol_dependencies_source ON symbol_dependencies(source_symbol_id);
CREATE INDEX idx_symbol_dependencies_target ON symbol_dependencies(target_symbol_id);
CREATE INDEX idx_symbol_dependencies_type ON symbol_dependencies(dependency_type);
CREATE INDEX idx_tasks_organization_id ON tasks(organization_id);
CREATE INDEX idx_tasks_codebase_id ON tasks(codebase_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_parent_id ON tasks(parent_task_id);
CREATE INDEX idx_prompts_organization_id ON prompts(organization_id);
CREATE INDEX idx_prompts_type ON prompts(prompt_type);
CREATE INDEX idx_prompts_category ON prompts(category);
CREATE INDEX idx_analysis_runs_codebase_id ON analysis_runs(codebase_id);
CREATE INDEX idx_code_metrics_analysis_run_id ON code_metrics(analysis_run_id);
CREATE INDEX idx_code_metrics_type ON code_metrics(metric_type);
CREATE INDEX idx_dead_code_analysis_run_id ON dead_code_analysis(analysis_run_id);
CREATE INDEX idx_dependency_analysis_run_id ON dependency_analysis(analysis_run_id);
CREATE INDEX idx_impact_analysis_run_id ON impact_analysis(analysis_run_id);

-- Full-text search indexes
CREATE INDEX idx_code_symbols_name_trgm ON code_symbols USING gin (name gin_trgm_ops);
CREATE INDEX idx_prompts_title_trgm ON prompts USING gin (title gin_trgm_ops);
CREATE INDEX idx_prompts_content_trgm ON prompts USING gin (content gin_trgm_ops);
CREATE INDEX idx_tasks_title_trgm ON tasks USING gin (title gin_trgm_ops);

-- Updated at triggers
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_organizations_updated_at BEFORE UPDATE ON organizations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_codebases_updated_at BEFORE UPDATE ON codebases FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_codebase_files_updated_at BEFORE UPDATE ON codebase_files FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_code_symbols_updated_at BEFORE UPDATE ON code_symbols FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_prompts_updated_at BEFORE UPDATE ON prompts FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

