-- =============================================================================
-- ANALYTICS MODULE SCHEMA
-- =============================================================================
-- This module handles codebase analysis results and metrics storage,
-- function/class/file-level analysis data, and performance/complexity metrics.
-- =============================================================================

-- =============================================================================
-- ENUMS
-- =============================================================================

CREATE TYPE analysis_type AS ENUM (
    'static',
    'dynamic',
    'security',
    'performance',
    'quality',
    'complexity',
    'dependency',
    'custom'
);

CREATE TYPE analysis_status AS ENUM (
    'pending',
    'running',
    'completed',
    'failed',
    'cancelled',
    'partial'
);

CREATE TYPE code_element_type AS ENUM (
    'file',
    'class',
    'function',
    'method',
    'variable',
    'constant',
    'interface',
    'enum',
    'module',
    'package'
);

CREATE TYPE metric_type AS ENUM (
    'count',
    'percentage',
    'ratio',
    'score',
    'duration',
    'size',
    'complexity'
);

-- =============================================================================
-- ANALYTICS TABLES
-- =============================================================================

-- Analysis runs - track analysis executions
CREATE TABLE analysis_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    repository_id UUID NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    
    -- Analysis metadata
    name VARCHAR(255) NOT NULL,
    short_id VARCHAR(20) UNIQUE DEFAULT generate_short_id('AR-'),
    analysis_type analysis_type NOT NULL,
    status analysis_status DEFAULT 'pending',
    
    -- Version information
    commit_sha VARCHAR(40) NOT NULL,
    branch_name VARCHAR(255),
    
    -- Configuration
    config JSONB DEFAULT '{}',
    tool_name VARCHAR(100),
    tool_version VARCHAR(50),
    
    -- Timing
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    
    -- Results summary
    total_files_analyzed INTEGER DEFAULT 0,
    total_issues_found INTEGER DEFAULT 0,
    total_metrics_collected INTEGER DEFAULT 0,
    
    -- Error handling
    error_message TEXT,
    error_details JSONB DEFAULT '{}',
    
    -- Ownership
    triggered_by UUID REFERENCES users(id),
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE NULL
);

-- File analysis - file-level analysis results
CREATE TABLE file_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_run_id UUID NOT NULL REFERENCES analysis_runs(id) ON DELETE CASCADE,
    repository_id UUID NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    
    -- File identification
    file_path TEXT NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_extension VARCHAR(20),
    
    -- File metrics
    lines_of_code INTEGER DEFAULT 0,
    lines_of_comments INTEGER DEFAULT 0,
    blank_lines INTEGER DEFAULT 0,
    file_size_bytes INTEGER DEFAULT 0,
    
    -- Complexity metrics
    cyclomatic_complexity INTEGER DEFAULT 0,
    cognitive_complexity INTEGER DEFAULT 0,
    maintainability_index DECIMAL(5,2),
    
    -- Quality metrics
    code_coverage_percentage DECIMAL(5,2),
    test_count INTEGER DEFAULT 0,
    bug_count INTEGER DEFAULT 0,
    vulnerability_count INTEGER DEFAULT 0,
    code_smell_count INTEGER DEFAULT 0,
    
    -- Language-specific metrics
    language VARCHAR(50),
    language_metrics JSONB DEFAULT '{}',
    
    -- Dependencies
    import_count INTEGER DEFAULT 0,
    dependency_count INTEGER DEFAULT 0,
    
    -- Analysis results
    issues JSONB DEFAULT '[]',
    metrics JSONB DEFAULT '{}',
    
    -- Timestamps
    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(analysis_run_id, file_path)
);

-- Code element analysis - function/class/method level analysis
CREATE TABLE code_element_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_run_id UUID NOT NULL REFERENCES analysis_runs(id) ON DELETE CASCADE,
    file_analysis_id UUID NOT NULL REFERENCES file_analysis(id) ON DELETE CASCADE,
    
    -- Element identification
    element_type code_element_type NOT NULL,
    element_name VARCHAR(255) NOT NULL,
    qualified_name TEXT, -- Full qualified name including namespace
    
    -- Location information
    start_line INTEGER,
    end_line INTEGER,
    start_column INTEGER,
    end_column INTEGER,
    
    -- Element metrics
    lines_of_code INTEGER DEFAULT 0,
    cyclomatic_complexity INTEGER DEFAULT 0,
    cognitive_complexity INTEGER DEFAULT 0,
    parameter_count INTEGER DEFAULT 0,
    return_statement_count INTEGER DEFAULT 0,
    
    -- Quality metrics
    test_coverage_percentage DECIMAL(5,2),
    bug_count INTEGER DEFAULT 0,
    vulnerability_count INTEGER DEFAULT 0,
    code_smell_count INTEGER DEFAULT 0,
    
    -- Relationships
    parent_element_id UUID REFERENCES code_element_analysis(id),
    calls_count INTEGER DEFAULT 0,
    called_by_count INTEGER DEFAULT 0,
    
    -- Analysis results
    issues JSONB DEFAULT '[]',
    metrics JSONB DEFAULT '{}',
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(analysis_run_id, file_analysis_id, element_type, qualified_name)
);

-- Metrics - flexible metric storage
CREATE TABLE metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    analysis_run_id UUID REFERENCES analysis_runs(id) ON DELETE CASCADE,
    repository_id UUID REFERENCES repositories(id) ON DELETE CASCADE,
    file_analysis_id UUID REFERENCES file_analysis(id) ON DELETE CASCADE,
    code_element_id UUID REFERENCES code_element_analysis(id) ON DELETE CASCADE,
    
    -- Metric identification
    metric_name VARCHAR(255) NOT NULL,
    metric_type metric_type NOT NULL,
    category VARCHAR(100), -- performance, quality, complexity, etc.
    
    -- Metric values
    value_numeric DECIMAL(15,6),
    value_text TEXT,
    value_json JSONB,
    
    -- Context
    scope VARCHAR(50), -- global, repository, file, function, etc.
    tags VARCHAR(50)[],
    
    -- Timing
    measured_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Metadata
    metadata JSONB DEFAULT '{}'
);

-- Performance metrics - specific performance analysis
CREATE TABLE performance_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_run_id UUID NOT NULL REFERENCES analysis_runs(id) ON DELETE CASCADE,
    repository_id UUID NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    file_analysis_id UUID REFERENCES file_analysis(id) ON DELETE CASCADE,
    code_element_id UUID REFERENCES code_element_analysis(id) ON DELETE CASCADE,
    
    -- Performance measurements
    execution_time_ms DECIMAL(10,3),
    memory_usage_mb DECIMAL(10,3),
    cpu_usage_percent DECIMAL(5,2),
    
    -- Throughput metrics
    requests_per_second DECIMAL(10,2),
    operations_per_second DECIMAL(10,2),
    
    -- Latency metrics
    p50_latency_ms DECIMAL(10,3),
    p95_latency_ms DECIMAL(10,3),
    p99_latency_ms DECIMAL(10,3),
    max_latency_ms DECIMAL(10,3),
    
    -- Resource metrics
    database_queries_count INTEGER DEFAULT 0,
    api_calls_count INTEGER DEFAULT 0,
    file_io_operations INTEGER DEFAULT 0,
    
    -- Test context
    test_scenario VARCHAR(255),
    load_level VARCHAR(50), -- light, medium, heavy
    
    -- Additional metrics
    custom_metrics JSONB DEFAULT '{}',
    
    -- Timestamps
    measured_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Issues - track code issues and violations
CREATE TABLE issues (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_run_id UUID NOT NULL REFERENCES analysis_runs(id) ON DELETE CASCADE,
    repository_id UUID NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    file_analysis_id UUID REFERENCES file_analysis(id) ON DELETE CASCADE,
    code_element_id UUID REFERENCES code_element_analysis(id) ON DELETE CASCADE,
    
    -- Issue identification
    issue_type VARCHAR(100) NOT NULL, -- bug, vulnerability, code_smell, etc.
    rule_id VARCHAR(100),
    rule_name VARCHAR(255),
    
    -- Severity and priority
    severity severity_level NOT NULL,
    priority priority_level DEFAULT 'medium',
    
    -- Location
    file_path TEXT,
    start_line INTEGER,
    end_line INTEGER,
    start_column INTEGER,
    end_column INTEGER,
    
    -- Issue details
    title VARCHAR(500) NOT NULL,
    description TEXT,
    message TEXT,
    
    -- Resolution
    status status_type DEFAULT 'active',
    resolution VARCHAR(100), -- fixed, false_positive, wont_fix, etc.
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by UUID REFERENCES users(id),
    
    -- Effort estimation
    effort_minutes INTEGER,
    
    -- Additional data
    tags VARCHAR(50)[],
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Trend analysis - track metrics over time
CREATE TABLE metric_trends (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    repository_id UUID NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    
    -- Trend identification
    metric_name VARCHAR(255) NOT NULL,
    scope VARCHAR(50), -- repository, file, function, etc.
    scope_identifier TEXT, -- file path, function name, etc.
    
    -- Trend data
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Values
    start_value DECIMAL(15,6),
    end_value DECIMAL(15,6),
    min_value DECIMAL(15,6),
    max_value DECIMAL(15,6),
    avg_value DECIMAL(15,6),
    
    -- Trend analysis
    trend_direction VARCHAR(20), -- increasing, decreasing, stable
    change_percentage DECIMAL(8,4),
    
    -- Data points
    data_points JSONB DEFAULT '[]',
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- INDEXES
-- =============================================================================

-- Analysis runs indexes
CREATE INDEX idx_analysis_runs_organization_id ON analysis_runs(organization_id);
CREATE INDEX idx_analysis_runs_project_id ON analysis_runs(project_id);
CREATE INDEX idx_analysis_runs_repository_id ON analysis_runs(repository_id);
CREATE INDEX idx_analysis_runs_short_id ON analysis_runs(short_id);
CREATE INDEX idx_analysis_runs_analysis_type ON analysis_runs(analysis_type);
CREATE INDEX idx_analysis_runs_status ON analysis_runs(status);
CREATE INDEX idx_analysis_runs_commit_sha ON analysis_runs(commit_sha);
CREATE INDEX idx_analysis_runs_branch_name ON analysis_runs(branch_name);
CREATE INDEX idx_analysis_runs_tool_name ON analysis_runs(tool_name);
CREATE INDEX idx_analysis_runs_started_at ON analysis_runs(started_at);
CREATE INDEX idx_analysis_runs_completed_at ON analysis_runs(completed_at);
CREATE INDEX idx_analysis_runs_created_at ON analysis_runs(created_at);
CREATE INDEX idx_analysis_runs_deleted_at ON analysis_runs(deleted_at) WHERE deleted_at IS NULL;

-- Composite indexes for common queries
CREATE INDEX idx_analysis_runs_repo_type_status ON analysis_runs(repository_id, analysis_type, status);
CREATE INDEX idx_analysis_runs_repo_commit ON analysis_runs(repository_id, commit_sha);

-- File analysis indexes
CREATE INDEX idx_file_analysis_analysis_run_id ON file_analysis(analysis_run_id);
CREATE INDEX idx_file_analysis_repository_id ON file_analysis(repository_id);
CREATE INDEX idx_file_analysis_file_path ON file_analysis(file_path);
CREATE INDEX idx_file_analysis_file_name ON file_analysis(file_name);
CREATE INDEX idx_file_analysis_file_extension ON file_analysis(file_extension);
CREATE INDEX idx_file_analysis_language ON file_analysis(language);
CREATE INDEX idx_file_analysis_lines_of_code ON file_analysis(lines_of_code);
CREATE INDEX idx_file_analysis_cyclomatic_complexity ON file_analysis(cyclomatic_complexity);
CREATE INDEX idx_file_analysis_maintainability_index ON file_analysis(maintainability_index);
CREATE INDEX idx_file_analysis_analyzed_at ON file_analysis(analyzed_at);

-- GIN indexes for JSONB fields
CREATE INDEX idx_file_analysis_issues ON file_analysis USING GIN(issues);
CREATE INDEX idx_file_analysis_metrics ON file_analysis USING GIN(metrics);
CREATE INDEX idx_file_analysis_language_metrics ON file_analysis USING GIN(language_metrics);

-- Code element analysis indexes
CREATE INDEX idx_code_element_analysis_analysis_run_id ON code_element_analysis(analysis_run_id);
CREATE INDEX idx_code_element_analysis_file_analysis_id ON code_element_analysis(file_analysis_id);
CREATE INDEX idx_code_element_analysis_element_type ON code_element_analysis(element_type);
CREATE INDEX idx_code_element_analysis_element_name ON code_element_analysis(element_name);
CREATE INDEX idx_code_element_analysis_qualified_name ON code_element_analysis(qualified_name);
CREATE INDEX idx_code_element_analysis_parent_element_id ON code_element_analysis(parent_element_id);
CREATE INDEX idx_code_element_analysis_cyclomatic_complexity ON code_element_analysis(cyclomatic_complexity);
CREATE INDEX idx_code_element_analysis_analyzed_at ON code_element_analysis(analyzed_at);

-- GIN indexes for code element JSONB fields
CREATE INDEX idx_code_element_analysis_issues ON code_element_analysis USING GIN(issues);
CREATE INDEX idx_code_element_analysis_metrics ON code_element_analysis USING GIN(metrics);
CREATE INDEX idx_code_element_analysis_metadata ON code_element_analysis USING GIN(metadata);

-- Metrics indexes
CREATE INDEX idx_metrics_organization_id ON metrics(organization_id);
CREATE INDEX idx_metrics_analysis_run_id ON metrics(analysis_run_id);
CREATE INDEX idx_metrics_repository_id ON metrics(repository_id);
CREATE INDEX idx_metrics_file_analysis_id ON metrics(file_analysis_id);
CREATE INDEX idx_metrics_code_element_id ON metrics(code_element_id);
CREATE INDEX idx_metrics_metric_name ON metrics(metric_name);
CREATE INDEX idx_metrics_metric_type ON metrics(metric_type);
CREATE INDEX idx_metrics_category ON metrics(category);
CREATE INDEX idx_metrics_scope ON metrics(scope);
CREATE INDEX idx_metrics_measured_at ON metrics(measured_at);

-- Composite indexes for metrics
CREATE INDEX idx_metrics_name_scope ON metrics(metric_name, scope);
CREATE INDEX idx_metrics_repo_name_measured ON metrics(repository_id, metric_name, measured_at);

-- GIN indexes for metrics
CREATE INDEX idx_metrics_tags ON metrics USING GIN(tags);
CREATE INDEX idx_metrics_value_json ON metrics USING GIN(value_json);
CREATE INDEX idx_metrics_metadata ON metrics USING GIN(metadata);

-- Performance metrics indexes
CREATE INDEX idx_performance_metrics_analysis_run_id ON performance_metrics(analysis_run_id);
CREATE INDEX idx_performance_metrics_repository_id ON performance_metrics(repository_id);
CREATE INDEX idx_performance_metrics_file_analysis_id ON performance_metrics(file_analysis_id);
CREATE INDEX idx_performance_metrics_code_element_id ON performance_metrics(code_element_id);
CREATE INDEX idx_performance_metrics_execution_time_ms ON performance_metrics(execution_time_ms);
CREATE INDEX idx_performance_metrics_memory_usage_mb ON performance_metrics(memory_usage_mb);
CREATE INDEX idx_performance_metrics_test_scenario ON performance_metrics(test_scenario);
CREATE INDEX idx_performance_metrics_measured_at ON performance_metrics(measured_at);

-- Issues indexes
CREATE INDEX idx_issues_analysis_run_id ON issues(analysis_run_id);
CREATE INDEX idx_issues_repository_id ON issues(repository_id);
CREATE INDEX idx_issues_file_analysis_id ON issues(file_analysis_id);
CREATE INDEX idx_issues_code_element_id ON issues(code_element_id);
CREATE INDEX idx_issues_issue_type ON issues(issue_type);
CREATE INDEX idx_issues_rule_id ON issues(rule_id);
CREATE INDEX idx_issues_severity ON issues(severity);
CREATE INDEX idx_issues_priority ON issues(priority);
CREATE INDEX idx_issues_status ON issues(status);
CREATE INDEX idx_issues_file_path ON issues(file_path);
CREATE INDEX idx_issues_detected_at ON issues(detected_at);
CREATE INDEX idx_issues_resolved_at ON issues(resolved_at);

-- Composite indexes for issues
CREATE INDEX idx_issues_repo_status_severity ON issues(repository_id, status, severity);
CREATE INDEX idx_issues_type_status ON issues(issue_type, status);

-- GIN indexes for issues
CREATE INDEX idx_issues_tags ON issues USING GIN(tags);
CREATE INDEX idx_issues_metadata ON issues USING GIN(metadata);

-- Metric trends indexes
CREATE INDEX idx_metric_trends_organization_id ON metric_trends(organization_id);
CREATE INDEX idx_metric_trends_repository_id ON metric_trends(repository_id);
CREATE INDEX idx_metric_trends_metric_name ON metric_trends(metric_name);
CREATE INDEX idx_metric_trends_scope ON metric_trends(scope);
CREATE INDEX idx_metric_trends_scope_identifier ON metric_trends(scope_identifier);
CREATE INDEX idx_metric_trends_period_start ON metric_trends(period_start);
CREATE INDEX idx_metric_trends_period_end ON metric_trends(period_end);
CREATE INDEX idx_metric_trends_calculated_at ON metric_trends(calculated_at);

-- Composite indexes for trends
CREATE INDEX idx_metric_trends_repo_metric_period ON metric_trends(repository_id, metric_name, period_start);

-- =============================================================================
-- TRIGGERS
-- =============================================================================

CREATE TRIGGER trigger_analysis_runs_updated_at
    BEFORE UPDATE ON analysis_runs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_issues_updated_at
    BEFORE UPDATE ON issues
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- VIEWS
-- =============================================================================

-- Analysis summary view
CREATE VIEW analysis_summary AS
SELECT 
    ar.*,
    r.name as repository_name,
    r.full_name as repository_full_name,
    COUNT(fa.id) as files_analyzed,
    COUNT(cea.id) as code_elements_analyzed,
    COUNT(i.id) as total_issues,
    COUNT(CASE WHEN i.severity = 'critical' THEN 1 END) as critical_issues,
    COUNT(CASE WHEN i.severity = 'error' THEN 1 END) as error_issues,
    COUNT(CASE WHEN i.severity = 'warning' THEN 1 END) as warning_issues,
    AVG(fa.cyclomatic_complexity) as avg_file_complexity,
    AVG(fa.maintainability_index) as avg_maintainability_index
FROM analysis_runs ar
LEFT JOIN repositories r ON ar.repository_id = r.id
LEFT JOIN file_analysis fa ON ar.id = fa.analysis_run_id
LEFT JOIN code_element_analysis cea ON ar.id = cea.analysis_run_id
LEFT JOIN issues i ON ar.id = i.analysis_run_id AND i.status = 'active'
WHERE ar.deleted_at IS NULL
GROUP BY ar.id, r.name, r.full_name;

-- Repository quality overview
CREATE VIEW repository_quality_overview AS
SELECT 
    r.id as repository_id,
    r.name as repository_name,
    r.full_name as repository_full_name,
    COUNT(DISTINCT ar.id) as total_analysis_runs,
    MAX(ar.completed_at) as last_analysis_at,
    COUNT(DISTINCT fa.id) as total_files_analyzed,
    AVG(fa.lines_of_code) as avg_lines_of_code,
    AVG(fa.cyclomatic_complexity) as avg_cyclomatic_complexity,
    AVG(fa.maintainability_index) as avg_maintainability_index,
    COUNT(i.id) as total_active_issues,
    COUNT(CASE WHEN i.severity = 'critical' THEN 1 END) as critical_issues,
    COUNT(CASE WHEN i.issue_type = 'bug' THEN 1 END) as bug_count,
    COUNT(CASE WHEN i.issue_type = 'vulnerability' THEN 1 END) as vulnerability_count,
    COUNT(CASE WHEN i.issue_type = 'code_smell' THEN 1 END) as code_smell_count
FROM repositories r
LEFT JOIN analysis_runs ar ON r.id = ar.repository_id AND ar.deleted_at IS NULL AND ar.status = 'completed'
LEFT JOIN file_analysis fa ON ar.id = fa.analysis_run_id
LEFT JOIN issues i ON ar.id = i.analysis_run_id AND i.status = 'active'
WHERE r.deleted_at IS NULL
GROUP BY r.id, r.name, r.full_name;

-- =============================================================================
-- FUNCTIONS
-- =============================================================================

-- Function to calculate quality score
CREATE OR REPLACE FUNCTION calculate_quality_score(
    p_repository_id UUID,
    p_analysis_run_id UUID DEFAULT NULL
)
RETURNS DECIMAL(5,2) AS $$
DECLARE
    quality_score DECIMAL(5,2) := 0;
    maintainability_score DECIMAL(5,2) := 0;
    complexity_score DECIMAL(5,2) := 0;
    issue_score DECIMAL(5,2) := 0;
    coverage_score DECIMAL(5,2) := 0;
BEGIN
    -- Calculate maintainability score (0-25 points)
    SELECT COALESCE(AVG(maintainability_index), 0) * 0.25
    INTO maintainability_score
    FROM file_analysis fa
    JOIN analysis_runs ar ON fa.analysis_run_id = ar.id
    WHERE ar.repository_id = p_repository_id
    AND (p_analysis_run_id IS NULL OR ar.id = p_analysis_run_id)
    AND ar.status = 'completed';
    
    -- Calculate complexity score (0-25 points, inverse of complexity)
    SELECT GREATEST(0, 25 - COALESCE(AVG(cyclomatic_complexity), 0))
    INTO complexity_score
    FROM file_analysis fa
    JOIN analysis_runs ar ON fa.analysis_run_id = ar.id
    WHERE ar.repository_id = p_repository_id
    AND (p_analysis_run_id IS NULL OR ar.id = p_analysis_run_id)
    AND ar.status = 'completed';
    
    -- Calculate issue score (0-25 points, penalize for issues)
    SELECT GREATEST(0, 25 - (
        COUNT(CASE WHEN severity = 'critical' THEN 1 END) * 5 +
        COUNT(CASE WHEN severity = 'error' THEN 1 END) * 3 +
        COUNT(CASE WHEN severity = 'warning' THEN 1 END) * 1
    ))
    INTO issue_score
    FROM issues i
    JOIN analysis_runs ar ON i.analysis_run_id = ar.id
    WHERE ar.repository_id = p_repository_id
    AND (p_analysis_run_id IS NULL OR ar.id = p_analysis_run_id)
    AND i.status = 'active'
    AND ar.status = 'completed';
    
    -- Calculate coverage score (0-25 points)
    SELECT COALESCE(AVG(code_coverage_percentage), 0) * 0.25
    INTO coverage_score
    FROM file_analysis fa
    JOIN analysis_runs ar ON fa.analysis_run_id = ar.id
    WHERE ar.repository_id = p_repository_id
    AND (p_analysis_run_id IS NULL OR ar.id = p_analysis_run_id)
    AND ar.status = 'completed';
    
    quality_score := maintainability_score + complexity_score + issue_score + coverage_score;
    
    RETURN LEAST(100, GREATEST(0, quality_score));
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON TABLE analysis_runs IS 'Track analysis executions with configuration and results summary';
COMMENT ON TABLE file_analysis IS 'File-level analysis results with metrics and quality data';
COMMENT ON TABLE code_element_analysis IS 'Function/class/method level analysis with detailed metrics';
COMMENT ON TABLE metrics IS 'Flexible metric storage for various analysis types';
COMMENT ON TABLE performance_metrics IS 'Specific performance analysis results';
COMMENT ON TABLE issues IS 'Code issues and violations with severity and resolution tracking';
COMMENT ON TABLE metric_trends IS 'Track metric changes over time for trend analysis';

COMMENT ON VIEW analysis_summary IS 'Analysis run overview with file, element, and issue counts';
COMMENT ON VIEW repository_quality_overview IS 'Repository quality metrics and issue summary';

COMMENT ON FUNCTION calculate_quality_score(UUID, UUID) IS 'Calculate overall quality score based on maintainability, complexity, issues, and coverage';

