-- Enhanced Tasks Module with OpenEvolve Integration
-- Builds upon the foundation from PR 47 with comprehensive task management

-- Task-related enums
CREATE TYPE task_status AS ENUM (
    'pending',
    'assigned',
    'in_progress',
    'blocked',
    'review',
    'testing',
    'completed',
    'failed',
    'cancelled',
    'archived'
);

CREATE TYPE task_priority AS ENUM (
    'low',
    'medium',
    'high',
    'urgent',
    'critical'
);

CREATE TYPE task_type AS ENUM (
    'feature',
    'bug_fix',
    'refactor',
    'documentation',
    'testing',
    'deployment',
    'research',
    'analysis',
    'optimization',
    'security',
    'maintenance'
);

CREATE TYPE execution_status AS ENUM (
    'queued',
    'running',
    'completed',
    'failed',
    'timeout',
    'cancelled',
    'retrying'
);

CREATE TYPE agent_type AS ENUM (
    'codegen',
    'claude',
    'task_manager',
    'openevolve',
    'human',
    'system'
);

-- Enhanced tasks table with comprehensive metadata
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Task identification
    title VARCHAR(500) NOT NULL,
    description TEXT,
    
    -- Task classification
    type task_type NOT NULL DEFAULT 'feature',
    status task_status NOT NULL DEFAULT 'pending',
    priority task_priority NOT NULL DEFAULT 'medium',
    
    -- Project and repository association
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    repository_id UUID REFERENCES repositories(id) ON DELETE SET NULL,
    codebase_id UUID REFERENCES codebases(id) ON DELETE SET NULL,
    
    -- Task hierarchy and dependencies
    parent_task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
    depends_on_task_ids JSONB DEFAULT '[]',
    blocks_task_ids JSONB DEFAULT '[]',
    
    -- Assignment and ownership
    assigned_to VARCHAR(255),
    assigned_agent_type agent_type,
    created_by VARCHAR(255),
    
    -- Task configuration and metadata
    requirements JSONB DEFAULT '{}',
    acceptance_criteria JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    tags JSONB DEFAULT '[]',
    
    -- Estimation and tracking
    estimated_hours DECIMAL(8,2),
    actual_hours DECIMAL(8,2),
    complexity_score INTEGER,
    
    -- Timing
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    assigned_at TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    due_date TIMESTAMP WITH TIME ZONE,
    
    -- External references
    external_id VARCHAR(255), -- Linear issue ID, GitHub issue ID, etc.
    external_url VARCHAR(1000),
    
    -- Constraints
    CONSTRAINT tasks_title_length CHECK (char_length(title) >= 1),
    CONSTRAINT tasks_complexity_range CHECK (complexity_score >= 1 AND complexity_score <= 10),
    CONSTRAINT tasks_hours_positive CHECK (estimated_hours >= 0 AND actual_hours >= 0),
    
    -- Indexes
    INDEX idx_tasks_status (status),
    INDEX idx_tasks_priority (priority),
    INDEX idx_tasks_type (type),
    INDEX idx_tasks_project (project_id),
    INDEX idx_tasks_repository (repository_id),
    INDEX idx_tasks_parent (parent_task_id),
    INDEX idx_tasks_assigned_to (assigned_to),
    INDEX idx_tasks_created_by (created_by),
    INDEX idx_tasks_external_id (external_id),
    INDEX idx_tasks_due_date (due_date),
    INDEX idx_tasks_created_at (created_at),
    
    -- GIN indexes for JSONB fields
    INDEX idx_tasks_requirements_gin USING gin (requirements),
    INDEX idx_tasks_metadata_gin USING gin (metadata),
    INDEX idx_tasks_tags_gin USING gin (tags),
    INDEX idx_tasks_depends_on_gin USING gin (depends_on_task_ids),
    INDEX idx_tasks_blocks_gin USING gin (blocks_task_ids)
);

-- Task execution tracking with detailed monitoring
CREATE TABLE task_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    
    -- Execution metadata
    execution_number INTEGER NOT NULL DEFAULT 1,
    status execution_status NOT NULL DEFAULT 'queued',
    
    -- Agent and environment
    agent_type agent_type NOT NULL,
    agent_id VARCHAR(255),
    environment VARCHAR(100) DEFAULT 'production',
    
    -- Execution configuration
    execution_config JSONB DEFAULT '{}',
    input_data JSONB DEFAULT '{}',
    
    -- Results and outputs
    output_data JSONB DEFAULT '{}',
    result_summary TEXT,
    error_message TEXT,
    logs TEXT,
    
    -- Resource usage
    cpu_time_ms INTEGER,
    memory_usage_mb INTEGER,
    disk_usage_mb INTEGER,
    network_requests INTEGER,
    
    -- Timing
    queued_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER,
    
    -- Quality metrics
    success_rate DECIMAL(5,2),
    quality_score DECIMAL(5,2),
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}',
    
    UNIQUE(task_id, execution_number),
    INDEX idx_task_executions_task (task_id),
    INDEX idx_task_executions_status (status),
    INDEX idx_task_executions_agent (agent_type, agent_id),
    INDEX idx_task_executions_started_at (started_at),
    INDEX idx_task_executions_duration (duration_ms)
);

-- OpenEvolve integration tables
CREATE TABLE openevolve_evaluations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    execution_id UUID REFERENCES task_executions(id) ON DELETE CASCADE,
    
    -- OpenEvolve program identification
    program_id VARCHAR(255) NOT NULL,
    evaluation_type VARCHAR(50) NOT NULL,
    
    -- Evaluation configuration
    evaluation_config JSONB DEFAULT '{}',
    evaluation_criteria JSONB DEFAULT '{}',
    
    -- Evaluation results
    scores JSONB DEFAULT '{}',
    metrics JSONB DEFAULT '{}',
    recommendations JSONB DEFAULT '[]',
    
    -- Evolution tracking
    generation INTEGER DEFAULT 0,
    parent_program_id VARCHAR(255),
    iteration_found INTEGER DEFAULT 0,
    
    -- Performance data
    evaluation_duration_ms INTEGER,
    complexity_score DECIMAL(10,4),
    diversity_score DECIMAL(10,4),
    quality_score DECIMAL(10,4),
    
    -- Status and timing
    status VARCHAR(50) DEFAULT 'pending',
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}',
    
    INDEX idx_openevolve_task_id (task_id),
    INDEX idx_openevolve_execution_id (execution_id),
    INDEX idx_openevolve_program_id (program_id),
    INDEX idx_openevolve_generation (generation),
    INDEX idx_openevolve_status (status)
);

-- Program evolution tracking for OpenEvolve integration
CREATE TABLE program_evolution (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    evaluation_id UUID REFERENCES openevolve_evaluations(id) ON DELETE CASCADE,
    
    -- Program identification
    program_id VARCHAR(255) NOT NULL,
    
    -- Program data
    code TEXT NOT NULL,
    language VARCHAR(50) DEFAULT 'python',
    
    -- Evolution metadata
    parent_id VARCHAR(255),
    generation INTEGER DEFAULT 0,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    iteration_found INTEGER DEFAULT 0,
    
    -- Performance metrics
    metrics JSONB DEFAULT '{}',
    complexity DECIMAL(10,4) DEFAULT 0.0,
    diversity DECIMAL(10,4) DEFAULT 0.0,
    fitness_score DECIMAL(10,4) DEFAULT 0.0,
    
    -- Code analysis results
    ast_analysis JSONB DEFAULT '{}',
    static_analysis JSONB DEFAULT '{}',
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}',
    
    UNIQUE(task_id, program_id),
    INDEX idx_program_evolution_task (task_id),
    INDEX idx_program_evolution_evaluation (evaluation_id),
    INDEX idx_program_evolution_parent (parent_id),
    INDEX idx_program_evolution_generation (generation),
    INDEX idx_program_evolution_fitness (fitness_score)
);

-- Task dependencies with detailed relationship tracking
CREATE TABLE task_dependencies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Dependency relationship
    source_task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    target_task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    
    -- Dependency metadata
    dependency_type VARCHAR(100) NOT NULL DEFAULT 'blocks', -- blocks, requires, related
    description TEXT,
    
    -- Dependency strength
    is_hard_dependency BOOLEAN DEFAULT true,
    weight DECIMAL(3,2) DEFAULT 1.0,
    
    -- Status tracking
    is_satisfied BOOLEAN DEFAULT false,
    satisfied_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(source_task_id, target_task_id, dependency_type),
    INDEX idx_task_deps_source (source_task_id),
    INDEX idx_task_deps_target (target_task_id),
    INDEX idx_task_deps_type (dependency_type),
    INDEX idx_task_deps_satisfied (is_satisfied),
    
    -- Prevent self-dependencies
    CONSTRAINT no_self_dependency CHECK (source_task_id != target_task_id)
);

-- Task comments and communication
CREATE TABLE task_comments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    
    -- Comment metadata
    author_id VARCHAR(255) NOT NULL,
    author_name VARCHAR(255),
    author_type agent_type DEFAULT 'human',
    
    -- Comment content
    content TEXT NOT NULL,
    content_type VARCHAR(50) DEFAULT 'text', -- text, markdown, code
    
    -- Comment classification
    comment_type VARCHAR(100) DEFAULT 'general', -- general, status_update, question, solution, feedback
    
    -- Threading
    parent_comment_id UUID REFERENCES task_comments(id) ON DELETE SET NULL,
    thread_id UUID,
    
    -- Status and visibility
    is_internal BOOLEAN DEFAULT false,
    is_resolved BOOLEAN DEFAULT false,
    
    -- Timing
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}',
    
    INDEX idx_task_comments_task (task_id),
    INDEX idx_task_comments_author (author_id),
    INDEX idx_task_comments_parent (parent_comment_id),
    INDEX idx_task_comments_thread (thread_id),
    INDEX idx_task_comments_created_at (created_at)
);

-- Task attachments and artifacts
CREATE TABLE task_attachments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    execution_id UUID REFERENCES task_executions(id) ON DELETE SET NULL,
    
    -- Attachment metadata
    filename VARCHAR(500) NOT NULL,
    file_type VARCHAR(100),
    file_size_bytes BIGINT,
    mime_type VARCHAR(200),
    
    -- Storage information
    storage_path VARCHAR(1000),
    storage_url VARCHAR(1000),
    checksum VARCHAR(64),
    
    -- Attachment classification
    attachment_type VARCHAR(100) DEFAULT 'general', -- code, documentation, test, artifact, log
    description TEXT,
    
    -- Upload metadata
    uploaded_by VARCHAR(255),
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}',
    
    INDEX idx_task_attachments_task (task_id),
    INDEX idx_task_attachments_execution (execution_id),
    INDEX idx_task_attachments_type (attachment_type),
    INDEX idx_task_attachments_uploaded_at (uploaded_at)
);

-- Task metrics and analytics
CREATE TABLE task_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    
    -- Metrics period
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Performance metrics
    total_executions INTEGER DEFAULT 0,
    successful_executions INTEGER DEFAULT 0,
    failed_executions INTEGER DEFAULT 0,
    average_duration_ms INTEGER,
    
    -- Quality metrics
    average_quality_score DECIMAL(5,2),
    code_coverage DECIMAL(5,2),
    test_pass_rate DECIMAL(5,2),
    
    -- Evolution metrics (OpenEvolve)
    total_generations INTEGER DEFAULT 0,
    best_fitness_score DECIMAL(10,4),
    convergence_rate DECIMAL(5,2),
    
    -- Resource usage
    total_cpu_time_ms BIGINT DEFAULT 0,
    peak_memory_usage_mb INTEGER DEFAULT 0,
    total_network_requests INTEGER DEFAULT 0,
    
    -- Detailed metrics
    detailed_metrics JSONB DEFAULT '{}',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(task_id, period_start, period_end),
    INDEX idx_task_metrics_task (task_id),
    INDEX idx_task_metrics_period (period_start, period_end)
);

-- Workflow definitions for complex task orchestration
CREATE TABLE workflows (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Workflow identification
    name VARCHAR(255) NOT NULL,
    description TEXT,
    version VARCHAR(50) DEFAULT '1.0',
    
    -- Workflow definition
    definition JSONB NOT NULL,
    triggers JSONB DEFAULT '[]',
    
    -- Workflow metadata
    is_active BOOLEAN DEFAULT true,
    is_template BOOLEAN DEFAULT false,
    
    -- Ownership
    created_by VARCHAR(255),
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    
    -- Timing
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}',
    
    INDEX idx_workflows_name (name),
    INDEX idx_workflows_project (project_id),
    INDEX idx_workflows_active (is_active),
    INDEX idx_workflows_template (is_template)
);

-- Workflow executions
CREATE TABLE workflow_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id UUID REFERENCES workflows(id) ON DELETE CASCADE,
    
    -- Execution metadata
    status execution_status NOT NULL DEFAULT 'queued',
    trigger_event JSONB DEFAULT '{}',
    
    -- Execution context
    context JSONB DEFAULT '{}',
    variables JSONB DEFAULT '{}',
    
    -- Results
    results JSONB DEFAULT '{}',
    error_message TEXT,
    
    -- Timing
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER,
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}',
    
    INDEX idx_workflow_executions_workflow (workflow_id),
    INDEX idx_workflow_executions_status (status),
    INDEX idx_workflow_executions_started_at (started_at)
);

-- Functions for task management
CREATE OR REPLACE FUNCTION calculate_task_complexity(task_id UUID)
RETURNS INTEGER AS $$
DECLARE
    complexity INTEGER := 1;
    subtask_count INTEGER;
    dependency_count INTEGER;
BEGIN
    -- Count subtasks
    SELECT COUNT(*) INTO subtask_count
    FROM tasks WHERE parent_task_id = task_id;
    
    -- Count dependencies
    SELECT COUNT(*) INTO dependency_count
    FROM task_dependencies WHERE source_task_id = task_id;
    
    -- Calculate complexity based on subtasks and dependencies
    complexity := 1 + (subtask_count * 2) + dependency_count;
    
    -- Cap at 10
    IF complexity > 10 THEN
        complexity := 10;
    END IF;
    
    RETURN complexity;
END;
$$ LANGUAGE plpgsql;

-- Function to check if task dependencies are satisfied
CREATE OR REPLACE FUNCTION check_task_dependencies_satisfied(task_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    unsatisfied_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO unsatisfied_count
    FROM task_dependencies td
    JOIN tasks t ON td.target_task_id = t.id
    WHERE td.source_task_id = task_id
    AND td.is_hard_dependency = true
    AND (t.status NOT IN ('completed') OR td.is_satisfied = false);
    
    RETURN unsatisfied_count = 0;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update task complexity automatically
CREATE OR REPLACE FUNCTION update_task_complexity()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
        NEW.complexity_score := calculate_task_complexity(NEW.id);
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_task_complexity
    BEFORE INSERT OR UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION update_task_complexity();

-- Trigger to update task timestamps
CREATE TRIGGER update_tasks_updated_at 
    BEFORE UPDATE ON tasks 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_task_dependencies_updated_at 
    BEFORE UPDATE ON task_dependencies 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_task_comments_updated_at 
    BEFORE UPDATE ON task_comments 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_workflows_updated_at 
    BEFORE UPDATE ON workflows 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Views for common task queries
CREATE VIEW active_tasks AS
SELECT 
    t.*,
    COUNT(DISTINCT te.id) as execution_count,
    MAX(te.completed_at) as last_execution,
    COUNT(DISTINCT tc.id) as comment_count,
    check_task_dependencies_satisfied(t.id) as dependencies_satisfied
FROM tasks t
LEFT JOIN task_executions te ON t.id = te.task_id
LEFT JOIN task_comments tc ON t.id = tc.task_id
WHERE t.status IN ('pending', 'assigned', 'in_progress', 'blocked', 'review', 'testing')
GROUP BY t.id;

CREATE VIEW task_hierarchy AS
WITH RECURSIVE task_tree AS (
    -- Base case: root tasks (no parent)
    SELECT 
        id,
        title,
        parent_task_id,
        status,
        priority,
        0 as level,
        ARRAY[id] as path
    FROM tasks 
    WHERE parent_task_id IS NULL
    
    UNION ALL
    
    -- Recursive case: child tasks
    SELECT 
        t.id,
        t.title,
        t.parent_task_id,
        t.status,
        t.priority,
        tt.level + 1,
        tt.path || t.id
    FROM tasks t
    JOIN task_tree tt ON t.parent_task_id = tt.id
)
SELECT * FROM task_tree ORDER BY path;

-- Comments for documentation
COMMENT ON TABLE tasks IS 'Enhanced task management with comprehensive metadata and OpenEvolve integration';
COMMENT ON TABLE task_executions IS 'Detailed tracking of task execution attempts with resource monitoring';
COMMENT ON TABLE openevolve_evaluations IS 'OpenEvolve evaluation results and step-by-step analysis';
COMMENT ON TABLE program_evolution IS 'Program evolution tracking for OpenEvolve integration';
COMMENT ON TABLE task_dependencies IS 'Task dependency relationships with satisfaction tracking';
COMMENT ON TABLE task_comments IS 'Task communication and collaboration';
COMMENT ON TABLE task_attachments IS 'Task-related files and artifacts';
COMMENT ON TABLE task_metrics IS 'Task performance and quality metrics over time';
COMMENT ON TABLE workflows IS 'Workflow definitions for complex task orchestration';
COMMENT ON TABLE workflow_executions IS 'Workflow execution tracking and results';

