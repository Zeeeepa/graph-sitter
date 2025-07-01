-- =============================================================================
-- ANALYTICS MODULE: Codebase analysis and metrics storage
-- =============================================================================
-- This module handles comprehensive code analysis, metrics storage,
-- quality scoring, and trend analysis.
-- =============================================================================

-- Analysis status enumeration
CREATE TYPE analysis_status AS ENUM (
    'pending',
    'running',
    'completed',
    'failed',
    'cancelled'
);

-- Analyzer types
CREATE TYPE analyzer_type AS ENUM (
    'complexity',
    'security',
    'performance',
    'maintainability',
    'dead_code',
    'dependencies',
    'style',
    'documentation',
    'testing',
    'custom'
);

-- Issue severity levels
CREATE TYPE issue_severity AS ENUM (
    'info',
    'minor',
    'major',
    'critical',
    'blocker'
);

-- =============================================================================
-- ANALYSIS RUNS TABLE
-- =============================================================================

CREATE TABLE analysis_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Analysis context
    repository_id UUID REFERENCES repositories(id),
    project_id UUID REFERENCES projects(id),
    branch_name VARCHAR(255),
    commit_sha VARCHAR(40),
    
    -- Analysis configuration
    analysis_type VARCHAR(100) NOT NULL, -- comprehensive, security, performance, etc.
    analyzers_used analyzer_type[] DEFAULT '{}',
    configuration JSONB DEFAULT '{}',
    
    -- Execution details
    status analysis_status DEFAULT 'pending',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    triggered_by UUID REFERENCES users(id),
    
    -- Results summary
    quality_score DECIMAL(5,2), -- 0-100
    total_files_analyzed INTEGER DEFAULT 0,
    total_lines_analyzed BIGINT DEFAULT 0,
    total_issues_found INTEGER DEFAULT 0,
    
    -- Error handling
    error_message TEXT,
    error_details JSONB,
    
    -- Metadata
    tool_versions JSONB DEFAULT '{}',
    environment_info JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT analysis_runs_quality_score_valid CHECK (
        quality_score IS NULL OR (quality_score >= 0 AND quality_score <= 100)
    ),
    CONSTRAINT analysis_runs_files_positive CHECK (total_files_analyzed >= 0),
    CONSTRAINT analysis_runs_lines_positive CHECK (total_lines_analyzed >= 0),
    CONSTRAINT analysis_runs_issues_positive CHECK (total_issues_found >= 0)
);

-- =============================================================================
-- FILE ANALYSIS TABLE
-- =============================================================================

CREATE TABLE file_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_run_id UUID NOT NULL REFERENCES analysis_runs(id) ON DELETE CASCADE,
    
    -- File details
    file_path TEXT NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_extension VARCHAR(20),
    file_size_bytes BIGINT,
    language VARCHAR(50),
    
    -- Analysis metrics
    lines_of_code INTEGER DEFAULT 0,
    comment_lines INTEGER DEFAULT 0,
    blank_lines INTEGER DEFAULT 0,
    complexity_score DECIMAL(8,2),
    maintainability_index DECIMAL(5,2),
    
    -- Quality metrics
    quality_score DECIMAL(5,2),
    issues_count INTEGER DEFAULT 0,
    security_issues_count INTEGER DEFAULT 0,
    performance_issues_count INTEGER DEFAULT 0,
    
    -- Detailed metrics
    metrics JSONB DEFAULT '{}',
    
    -- Analysis results
    issues JSONB DEFAULT '[]',
    suggestions JSONB DEFAULT '[]',
    
    -- Metadata
    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    analyzer_versions JSONB DEFAULT '{}',
    
    CONSTRAINT file_analysis_path_not_empty CHECK (length(trim(file_path)) > 0),
    CONSTRAINT file_analysis_size_positive CHECK (file_size_bytes IS NULL OR file_size_bytes >= 0),
    CONSTRAINT file_analysis_lines_positive CHECK (
        lines_of_code >= 0 AND comment_lines >= 0 AND blank_lines >= 0
    ),
    CONSTRAINT file_analysis_quality_valid CHECK (
        quality_score IS NULL OR (quality_score >= 0 AND quality_score <= 100)
    ),
    CONSTRAINT file_analysis_issues_positive CHECK (
        issues_count >= 0 AND security_issues_count >= 0 AND performance_issues_count >= 0
    )
);

-- =============================================================================
-- CODE ELEMENT ANALYSIS TABLE
-- =============================================================================

CREATE TABLE code_element_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    file_analysis_id UUID NOT NULL REFERENCES file_analysis(id) ON DELETE CASCADE,
    
    -- Element identification
    element_type VARCHAR(50) NOT NULL, -- function, class, method, variable, etc.
    element_name VARCHAR(255) NOT NULL,
    element_signature TEXT,
    
    -- Location
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    start_column INTEGER,
    end_column INTEGER,
    
    -- Complexity metrics
    cyclomatic_complexity INTEGER,
    cognitive_complexity INTEGER,
    nesting_depth INTEGER,
    parameter_count INTEGER,
    
    -- Size metrics
    lines_of_code INTEGER DEFAULT 0,
    statements_count INTEGER DEFAULT 0,
    
    -- Quality metrics
    maintainability_index DECIMAL(5,2),
    quality_score DECIMAL(5,2),
    
    -- Issues
    issues_count INTEGER DEFAULT 0,
    issues JSONB DEFAULT '[]',
    
    -- Relationships
    calls_to TEXT[], -- Functions/methods this element calls
    called_by TEXT[], -- Functions/methods that call this element
    dependencies TEXT[], -- External dependencies
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    CONSTRAINT code_element_name_not_empty CHECK (length(trim(element_name)) > 0),
    CONSTRAINT code_element_lines_valid CHECK (end_line >= start_line),
    CONSTRAINT code_element_columns_valid CHECK (
        start_column IS NULL OR end_column IS NULL OR end_column >= start_column
    ),
    CONSTRAINT code_element_complexity_positive CHECK (
        cyclomatic_complexity IS NULL OR cyclomatic_complexity >= 0
    ),
    CONSTRAINT code_element_lines_positive CHECK (lines_of_code >= 0),
    CONSTRAINT code_element_quality_valid CHECK (
        quality_score IS NULL OR (quality_score >= 0 AND quality_score <= 100)
    )
);

-- =============================================================================
-- METRICS TABLE
-- =============================================================================

CREATE TABLE metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_run_id UUID NOT NULL REFERENCES analysis_runs(id) ON DELETE CASCADE,
    
    -- Metric identification
    metric_name VARCHAR(100) NOT NULL,
    metric_category VARCHAR(50) NOT NULL, -- complexity, security, performance, etc.
    metric_type VARCHAR(50) NOT NULL, -- count, percentage, ratio, score, etc.
    
    -- Metric values
    value_numeric DECIMAL(15,6),
    value_text TEXT,
    value_json JSONB,
    
    -- Context
    scope VARCHAR(50) DEFAULT 'global', -- global, file, function, class, etc.
    scope_identifier TEXT, -- file path, function name, etc.
    
    -- Thresholds and evaluation
    threshold_min DECIMAL(15,6),
    threshold_max DECIMAL(15,6),
    is_within_threshold BOOLEAN,
    
    -- Metadata
    unit VARCHAR(20), -- lines, percentage, milliseconds, etc.
    description TEXT,
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    measured_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT metrics_name_not_empty CHECK (length(trim(metric_name)) > 0),
    CONSTRAINT metrics_category_not_empty CHECK (length(trim(metric_category)) > 0),
    CONSTRAINT metrics_has_value CHECK (
        value_numeric IS NOT NULL OR value_text IS NOT NULL OR value_json IS NOT NULL
    )
);

-- =============================================================================
-- PERFORMANCE METRICS TABLE
-- =============================================================================

CREATE TABLE performance_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_run_id UUID NOT NULL REFERENCES analysis_runs(id) ON DELETE CASCADE,
    
    -- Performance measurement
    metric_name VARCHAR(100) NOT NULL,
    measurement_type VARCHAR(50) NOT NULL, -- execution_time, memory_usage, throughput, etc.
    
    -- Values
    value DECIMAL(15,6) NOT NULL,
    unit VARCHAR(20) NOT NULL, -- ms, mb, ops/sec, etc.
    
    -- Context
    test_case VARCHAR(255),
    environment VARCHAR(100),
    conditions JSONB DEFAULT '{}',
    
    -- Benchmarking
    baseline_value DECIMAL(15,6),
    improvement_percent DECIMAL(8,2),
    is_regression BOOLEAN DEFAULT false,
    
    -- Metadata
    measurement_tool VARCHAR(100),
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    measured_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT perf_metrics_name_not_empty CHECK (length(trim(metric_name)) > 0),
    CONSTRAINT perf_metrics_unit_not_empty CHECK (length(trim(unit)) > 0),
    CONSTRAINT perf_metrics_baseline_positive CHECK (
        baseline_value IS NULL OR baseline_value >= 0
    )
);

-- =============================================================================
-- ISSUES TABLE
-- =============================================================================

CREATE TABLE issues (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_run_id UUID NOT NULL REFERENCES analysis_runs(id) ON DELETE CASCADE,
    file_analysis_id UUID REFERENCES file_analysis(id),
    
    -- Issue identification
    issue_type VARCHAR(100) NOT NULL,
    issue_category VARCHAR(50) NOT NULL, -- security, performance, style, etc.
    severity issue_severity NOT NULL,
    
    -- Issue details
    title VARCHAR(500) NOT NULL,
    description TEXT,
    message TEXT NOT NULL,
    
    -- Location
    file_path TEXT,
    start_line INTEGER,
    end_line INTEGER,
    start_column INTEGER,
    end_column INTEGER,
    
    -- Rule information
    rule_id VARCHAR(100),
    rule_name VARCHAR(255),
    rule_description TEXT,
    
    -- Resolution
    is_resolved BOOLEAN DEFAULT false,
    resolution_type VARCHAR(50), -- fixed, suppressed, false_positive, wont_fix
    resolution_comment TEXT,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by UUID REFERENCES users(id),
    
    -- Suggestions
    suggested_fix TEXT,
    fix_effort VARCHAR(20), -- trivial, easy, medium, hard
    
    -- Metadata
    analyzer_name VARCHAR(100),
    confidence_score DECIMAL(5,2), -- 0-100
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT issues_title_not_empty CHECK (length(trim(title)) > 0),
    CONSTRAINT issues_message_not_empty CHECK (length(trim(message)) > 0),
    CONSTRAINT issues_lines_valid CHECK (
        start_line IS NULL OR end_line IS NULL OR end_line >= start_line
    ),
    CONSTRAINT issues_confidence_valid CHECK (
        confidence_score IS NULL OR (confidence_score >= 0 AND confidence_score <= 100)
    )
);

-- =============================================================================
-- METRIC TRENDS TABLE
-- =============================================================================

CREATE TABLE metric_trends (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    repository_id UUID REFERENCES repositories(id),
    project_id UUID REFERENCES projects(id),
    
    -- Trend identification
    metric_name VARCHAR(100) NOT NULL,
    metric_category VARCHAR(50) NOT NULL,
    
    -- Trend data
    time_period VARCHAR(20) NOT NULL, -- daily, weekly, monthly
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Values
    current_value DECIMAL(15,6),
    previous_value DECIMAL(15,6),
    change_value DECIMAL(15,6),
    change_percent DECIMAL(8,2),
    
    -- Trend analysis
    trend_direction VARCHAR(20), -- improving, degrading, stable
    is_significant_change BOOLEAN DEFAULT false,
    
    -- Statistics
    min_value DECIMAL(15,6),
    max_value DECIMAL(15,6),
    avg_value DECIMAL(15,6),
    std_deviation DECIMAL(15,6),
    
    -- Metadata
    data_points_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT metric_trends_name_not_empty CHECK (length(trim(metric_name)) > 0),
    CONSTRAINT metric_trends_period_valid CHECK (period_end > period_start),
    CONSTRAINT metric_trends_data_points_positive CHECK (data_points_count >= 0)
);

-- =============================================================================
-- TRIGGERS
-- =============================================================================

-- Update timestamps
CREATE TRIGGER update_analysis_runs_updated_at 
    BEFORE UPDATE ON analysis_runs 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- INDEXES
-- =============================================================================

-- Analysis runs indexes
CREATE INDEX idx_analysis_runs_org_id ON analysis_runs(organization_id);
CREATE INDEX idx_analysis_runs_repository_id ON analysis_runs(repository_id);
CREATE INDEX idx_analysis_runs_project_id ON analysis_runs(project_id);
CREATE INDEX idx_analysis_runs_status ON analysis_runs(status);
CREATE INDEX idx_analysis_runs_type ON analysis_runs(analysis_type);
CREATE INDEX idx_analysis_runs_triggered_by ON analysis_runs(triggered_by);
CREATE INDEX idx_analysis_runs_created_at ON analysis_runs(created_at);
CREATE INDEX idx_analysis_runs_quality_score ON analysis_runs(quality_score);

-- File analysis indexes
CREATE INDEX idx_file_analysis_run_id ON file_analysis(analysis_run_id);
CREATE INDEX idx_file_analysis_path ON file_analysis(file_path);
CREATE INDEX idx_file_analysis_language ON file_analysis(language);
CREATE INDEX idx_file_analysis_quality_score ON file_analysis(quality_score);

-- Code element analysis indexes
CREATE INDEX idx_code_element_file_id ON code_element_analysis(file_analysis_id);
CREATE INDEX idx_code_element_type ON code_element_analysis(element_type);
CREATE INDEX idx_code_element_name ON code_element_analysis(element_name);
CREATE INDEX idx_code_element_complexity ON code_element_analysis(cyclomatic_complexity);

-- Metrics indexes
CREATE INDEX idx_metrics_run_id ON metrics(analysis_run_id);
CREATE INDEX idx_metrics_name ON metrics(metric_name);
CREATE INDEX idx_metrics_category ON metrics(metric_category);
CREATE INDEX idx_metrics_scope ON metrics(scope, scope_identifier);
CREATE INDEX idx_metrics_measured_at ON metrics(measured_at);

-- Performance metrics indexes
CREATE INDEX idx_perf_metrics_run_id ON performance_metrics(analysis_run_id);
CREATE INDEX idx_perf_metrics_name ON performance_metrics(metric_name);
CREATE INDEX idx_perf_metrics_type ON performance_metrics(measurement_type);
CREATE INDEX idx_perf_metrics_measured_at ON performance_metrics(measured_at);

-- Issues indexes
CREATE INDEX idx_issues_run_id ON issues(analysis_run_id);
CREATE INDEX idx_issues_file_id ON issues(file_analysis_id);
CREATE INDEX idx_issues_type ON issues(issue_type);
CREATE INDEX idx_issues_category ON issues(issue_category);
CREATE INDEX idx_issues_severity ON issues(severity);
CREATE INDEX idx_issues_resolved ON issues(is_resolved);
CREATE INDEX idx_issues_file_path ON issues(file_path);

-- Metric trends indexes
CREATE INDEX idx_metric_trends_org_id ON metric_trends(organization_id);
CREATE INDEX idx_metric_trends_repository_id ON metric_trends(repository_id);
CREATE INDEX idx_metric_trends_project_id ON metric_trends(project_id);
CREATE INDEX idx_metric_trends_name ON metric_trends(metric_name);
CREATE INDEX idx_metric_trends_period ON metric_trends(time_period, period_start, period_end);

-- =============================================================================
-- VIEWS
-- =============================================================================

-- Repository quality overview
CREATE VIEW repository_quality_overview AS
SELECT 
    r.id as repository_id,
    r.name as repository_name,
    r.organization_id,
    COUNT(ar.id) as total_analyses,
    AVG(ar.quality_score) as avg_quality_score,
    MAX(ar.quality_score) as best_quality_score,
    MIN(ar.quality_score) as worst_quality_score,
    SUM(ar.total_issues_found) as total_issues,
    MAX(ar.created_at) as last_analysis_date,
    COUNT(CASE WHEN ar.status = 'completed' THEN 1 END) as successful_analyses,
    COUNT(CASE WHEN ar.status = 'failed' THEN 1 END) as failed_analyses
FROM repositories r
LEFT JOIN analysis_runs ar ON r.id = ar.repository_id
WHERE r.deleted_at IS NULL
GROUP BY r.id, r.name, r.organization_id;

-- Issue summary by severity
CREATE VIEW issue_summary_by_severity AS
SELECT 
    ar.repository_id,
    ar.analysis_type,
    i.severity,
    COUNT(*) as issue_count,
    COUNT(CASE WHEN i.is_resolved THEN 1 END) as resolved_count,
    ROUND(
        (COUNT(CASE WHEN i.is_resolved THEN 1 END)::DECIMAL / COUNT(*)) * 100, 
        2
    ) as resolution_rate
FROM issues i
JOIN analysis_runs ar ON i.analysis_run_id = ar.id
GROUP BY ar.repository_id, ar.analysis_type, i.severity;

-- Quality trends view
CREATE VIEW quality_trends AS
SELECT 
    mt.repository_id,
    mt.metric_name,
    mt.time_period,
    mt.period_start,
    mt.period_end,
    mt.current_value,
    mt.previous_value,
    mt.change_percent,
    mt.trend_direction,
    CASE 
        WHEN mt.change_percent > 5 THEN 'significant_improvement'
        WHEN mt.change_percent < -5 THEN 'significant_degradation'
        ELSE 'stable'
    END as trend_significance
FROM metric_trends mt
WHERE mt.metric_category = 'quality';

-- =============================================================================
-- FUNCTIONS
-- =============================================================================

-- Function to calculate quality score
CREATE OR REPLACE FUNCTION calculate_quality_score(analysis_run_uuid UUID)
RETURNS DECIMAL(5,2) AS $$
DECLARE
    complexity_score DECIMAL(5,2);
    security_score DECIMAL(5,2);
    maintainability_score DECIMAL(5,2);
    final_score DECIMAL(5,2);
BEGIN
    -- Get complexity score (inverse of average complexity)
    SELECT 
        CASE 
            WHEN AVG(complexity_score) > 0 
            THEN GREATEST(0, 100 - (AVG(complexity_score) * 10))
            ELSE 100 
        END
    INTO complexity_score
    FROM file_analysis 
    WHERE analysis_run_id = analysis_run_uuid;
    
    -- Get security score (based on security issues)
    SELECT 
        CASE 
            WHEN COUNT(*) = 0 THEN 100
            ELSE GREATEST(0, 100 - (COUNT(*) * 5))
        END
    INTO security_score
    FROM issues i
    JOIN analysis_runs ar ON i.analysis_run_id = ar.id
    WHERE ar.id = analysis_run_uuid AND i.issue_category = 'security';
    
    -- Get maintainability score
    SELECT COALESCE(AVG(maintainability_index), 70)
    INTO maintainability_score
    FROM file_analysis 
    WHERE analysis_run_id = analysis_run_uuid;
    
    -- Calculate weighted final score
    final_score := (
        COALESCE(complexity_score, 70) * 0.3 +
        COALESCE(security_score, 70) * 0.4 +
        COALESCE(maintainability_score, 70) * 0.3
    );
    
    RETURN ROUND(final_score, 2);
END;
$$ LANGUAGE plpgsql;

-- Function to get analysis statistics
CREATE OR REPLACE FUNCTION get_analysis_statistics(repo_uuid UUID DEFAULT NULL)
RETURNS JSONB AS $$
DECLARE
    result JSONB;
    total_runs INTEGER;
    avg_quality DECIMAL;
    total_issues INTEGER;
    avg_files INTEGER;
BEGIN
    SELECT 
        COUNT(*),
        AVG(quality_score),
        SUM(total_issues_found),
        AVG(total_files_analyzed)
    INTO total_runs, avg_quality, total_issues, avg_files
    FROM analysis_runs
    WHERE (repo_uuid IS NULL OR repository_id = repo_uuid)
      AND status = 'completed';
    
    result := jsonb_build_object(
        'total_analysis_runs', COALESCE(total_runs, 0),
        'average_quality_score', COALESCE(avg_quality, 0),
        'total_issues_found', COALESCE(total_issues, 0),
        'average_files_analyzed', COALESCE(avg_files, 0),
        'calculated_at', CURRENT_TIMESTAMP
    );
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Record this migration
INSERT INTO schema_migrations (version, description) VALUES 
('03_analytics_module', 'Analytics module with comprehensive code analysis and metrics storage');

