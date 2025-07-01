-- Analytics Database Schema
-- Manages comprehensive analysis results, metrics, and insights

-- Analysis results storage for different analysis types
CREATE TABLE IF NOT EXISTS analysis_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_type VARCHAR(100) NOT NULL, -- 'complexity', 'quality', 'dependencies', 'security', etc.
    analysis_subtype VARCHAR(100), -- More specific analysis categorization
    repository_id UUID NOT NULL, -- References codebase.repositories.id
    file_id UUID, -- References codebase.files.id (optional, for file-specific analysis)
    symbol_id UUID, -- References codebase.symbols.id (optional, for symbol-specific analysis)
    analysis_version VARCHAR(50) DEFAULT '1.0.0',
    analyzer_name VARCHAR(255) NOT NULL, -- Name of the analyzer that produced results
    analyzer_version VARCHAR(100),
    analysis_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    results JSONB NOT NULL, -- Structured analysis results
    metrics JSONB, -- Extracted metrics in standardized format
    score DECIMAL(10,4), -- Overall score for this analysis
    grade VARCHAR(10), -- Letter grade (A, B, C, D, F) or custom grading
    confidence_level DECIMAL(5,2) DEFAULT 100.0, -- Confidence in analysis results (0-100)
    execution_time_ms INTEGER,
    input_parameters JSONB, -- Parameters used for this analysis
    baseline_comparison JSONB, -- Comparison with baseline/previous results
    trends JSONB, -- Trend analysis data
    recommendations TEXT[], -- Actionable recommendations
    warnings TEXT[], -- Warnings or concerns identified
    errors TEXT[], -- Errors encountered during analysis
    metadata JSONB, -- Additional analysis metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_analysis_type CHECK (analysis_type IN (
        'complexity', 'quality', 'dependencies', 'security', 'performance', 
        'maintainability', 'documentation', 'testing', 'architecture', 'duplication',
        'dead_code', 'unused_imports', 'type_coverage', 'ai_impact', 'ownership'
    )),
    CONSTRAINT valid_confidence CHECK (confidence_level >= 0 AND confidence_level <= 100)
);

-- Code metrics aggregated at different levels
CREATE TABLE IF NOT EXISTS code_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID NOT NULL,
    file_id UUID, -- NULL for repository-level metrics
    symbol_id UUID, -- NULL for file/repository-level metrics
    metric_type VARCHAR(100) NOT NULL, -- 'loc', 'complexity', 'maintainability', etc.
    metric_name VARCHAR(255) NOT NULL, -- Specific metric name
    metric_value DECIMAL(15,4) NOT NULL,
    metric_unit VARCHAR(50), -- Unit of measurement
    measurement_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    measurement_method VARCHAR(100), -- How the metric was calculated
    baseline_value DECIMAL(15,4), -- Previous or baseline value for comparison
    threshold_min DECIMAL(15,4), -- Minimum acceptable value
    threshold_max DECIMAL(15,4), -- Maximum acceptable value
    is_within_threshold BOOLEAN, -- Whether value is within acceptable range
    percentile_rank DECIMAL(5,2), -- Percentile rank compared to similar entities
    trend_direction VARCHAR(20), -- 'improving', 'degrading', 'stable'
    trend_magnitude DECIMAL(10,4), -- Magnitude of trend change
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(repository_id, file_id, symbol_id, metric_type, metric_name, measurement_date),
    CONSTRAINT valid_metric_type CHECK (metric_type IN (
        'loc', 'lloc', 'sloc', 'complexity', 'maintainability', 'halstead',
        'depth_inheritance', 'coupling', 'cohesion', 'duplication', 'coverage',
        'documentation_ratio', 'test_ratio', 'dependency_count', 'vulnerability_count'
    )),
    CONSTRAINT valid_trend_direction CHECK (trend_direction IN ('improving', 'degrading', 'stable', 'unknown'))
);

-- Quality assessments and scores
CREATE TABLE IF NOT EXISTS quality_assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID NOT NULL,
    file_id UUID,
    symbol_id UUID,
    assessment_type VARCHAR(100) NOT NULL, -- 'overall', 'maintainability', 'readability', etc.
    quality_score DECIMAL(5,2) NOT NULL, -- 0-100 quality score
    quality_grade VARCHAR(10), -- A, B, C, D, F
    assessment_criteria JSONB, -- Criteria used for assessment
    contributing_factors JSONB, -- Factors that influenced the score
    improvement_suggestions TEXT[],
    assessment_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    assessor_type VARCHAR(50) DEFAULT 'automated', -- 'automated', 'human', 'hybrid'
    assessor_id VARCHAR(255),
    confidence_score DECIMAL(5,2) DEFAULT 100.0,
    metadata JSONB,
    
    CONSTRAINT valid_assessment_type CHECK (assessment_type IN (
        'overall', 'maintainability', 'readability', 'testability', 'performance',
        'security', 'documentation', 'architecture', 'design_patterns'
    )),
    CONSTRAINT valid_quality_score CHECK (quality_score >= 0 AND quality_score <= 100),
    CONSTRAINT valid_assessor_type CHECK (assessor_type IN ('automated', 'human', 'hybrid'))
);

-- Dependency analysis results
CREATE TABLE IF NOT EXISTS dependency_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID NOT NULL,
    analysis_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    dependency_graph JSONB, -- Graph representation of dependencies
    circular_dependencies JSONB, -- Detected circular dependencies
    unused_dependencies TEXT[], -- Dependencies that appear unused
    outdated_dependencies JSONB, -- Dependencies with available updates
    vulnerable_dependencies JSONB, -- Dependencies with known vulnerabilities
    license_conflicts JSONB, -- License compatibility issues
    dependency_depth_stats JSONB, -- Statistics about dependency depth
    package_manager_stats JSONB, -- Statistics by package manager
    recommendations TEXT[],
    risk_assessment JSONB, -- Overall dependency risk assessment
    metadata JSONB
);

-- Security analysis results
CREATE TABLE IF NOT EXISTS security_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID NOT NULL,
    file_id UUID,
    symbol_id UUID,
    analysis_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    vulnerability_type VARCHAR(100), -- 'sql_injection', 'xss', 'hardcoded_secrets', etc.
    severity_level VARCHAR(20) NOT NULL, -- 'critical', 'high', 'medium', 'low', 'info'
    cwe_id VARCHAR(20), -- Common Weakness Enumeration ID
    cvss_score DECIMAL(3,1), -- CVSS score if applicable
    description TEXT NOT NULL,
    affected_code TEXT, -- Code snippet showing the issue
    line_number INTEGER,
    remediation_advice TEXT,
    false_positive_likelihood DECIMAL(5,2), -- Likelihood this is a false positive
    exploit_complexity VARCHAR(20), -- 'low', 'medium', 'high'
    impact_assessment TEXT,
    references TEXT[], -- External references for more information
    status VARCHAR(50) DEFAULT 'open', -- 'open', 'fixed', 'accepted_risk', 'false_positive'
    assigned_to VARCHAR(255),
    metadata JSONB,
    
    CONSTRAINT valid_severity CHECK (severity_level IN ('critical', 'high', 'medium', 'low', 'info')),
    CONSTRAINT valid_complexity CHECK (exploit_complexity IN ('low', 'medium', 'high')),
    CONSTRAINT valid_status CHECK (status IN ('open', 'fixed', 'accepted_risk', 'false_positive', 'investigating'))
);

-- Performance analysis results
CREATE TABLE IF NOT EXISTS performance_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID NOT NULL,
    file_id UUID,
    symbol_id UUID,
    analysis_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    performance_metric VARCHAR(100) NOT NULL, -- 'time_complexity', 'space_complexity', 'runtime'
    metric_value VARCHAR(100), -- O(n), O(log n), actual timing, etc.
    measurement_context TEXT, -- Context of the measurement
    bottleneck_identified BOOLEAN DEFAULT false,
    optimization_suggestions TEXT[],
    benchmark_results JSONB, -- Actual benchmark data if available
    profiling_data JSONB, -- Profiling information
    resource_usage JSONB, -- CPU, memory, I/O usage
    scalability_assessment TEXT,
    metadata JSONB
);

-- Code duplication analysis
CREATE TABLE IF NOT EXISTS duplication_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID NOT NULL,
    analysis_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    duplicate_group_id UUID NOT NULL, -- Groups related duplicates
    file_id UUID NOT NULL,
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    duplicate_content TEXT,
    content_hash VARCHAR(64), -- Hash of the duplicated content
    similarity_score DECIMAL(5,2), -- 0-100 similarity score
    duplicate_type VARCHAR(50), -- 'exact', 'structural', 'semantic'
    lines_duplicated INTEGER,
    tokens_duplicated INTEGER,
    refactoring_suggestion TEXT,
    estimated_effort_hours DECIMAL(5,2), -- Estimated effort to refactor
    priority_score DECIMAL(5,2), -- Priority for addressing this duplication
    metadata JSONB,
    
    CONSTRAINT valid_duplicate_type CHECK (duplicate_type IN ('exact', 'structural', 'semantic', 'near_exact'))
);

-- Dead code analysis
CREATE TABLE IF NOT EXISTS dead_code_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID NOT NULL,
    file_id UUID NOT NULL,
    symbol_id UUID,
    analysis_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    dead_code_type VARCHAR(100) NOT NULL, -- 'unused_function', 'unused_variable', 'unreachable_code'
    confidence_level DECIMAL(5,2) NOT NULL, -- Confidence that this is actually dead code
    usage_analysis JSONB, -- Analysis of how/where this code might be used
    removal_impact JSONB, -- Potential impact of removing this code
    removal_recommendation VARCHAR(50), -- 'safe_to_remove', 'investigate', 'keep'
    last_modified_date TIMESTAMP WITH TIME ZONE,
    last_modified_by VARCHAR(255),
    estimated_savings JSONB, -- Estimated benefits of removal (LOC, complexity, etc.)
    metadata JSONB,
    
    CONSTRAINT valid_dead_code_type CHECK (dead_code_type IN (
        'unused_function', 'unused_variable', 'unused_import', 'unreachable_code',
        'unused_class', 'unused_method', 'unused_constant', 'dead_branch'
    )),
    CONSTRAINT valid_removal_recommendation CHECK (removal_recommendation IN (
        'safe_to_remove', 'investigate', 'keep', 'refactor'
    ))
);

-- AI impact analysis results
CREATE TABLE IF NOT EXISTS ai_impact_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID NOT NULL,
    analysis_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ai_contribution_percentage DECIMAL(5,2), -- Percentage of code attributed to AI
    ai_authors TEXT[], -- List of AI authors/bots identified
    human_authors TEXT[], -- List of human authors
    ai_touched_files INTEGER, -- Number of files with AI contributions
    ai_touched_symbols INTEGER, -- Number of symbols with AI contributions
    collaboration_patterns JSONB, -- Patterns of AI-human collaboration
    quality_comparison JSONB, -- Quality comparison between AI and human code
    timeline_analysis JSONB, -- Timeline of AI contributions
    high_impact_ai_symbols JSONB, -- AI-created symbols with high usage
    risk_assessment JSONB, -- Risks associated with AI contributions
    recommendations TEXT[],
    metadata JSONB
);

-- Architecture analysis results
CREATE TABLE IF NOT EXISTS architecture_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID NOT NULL,
    analysis_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    architecture_patterns JSONB, -- Detected architectural patterns
    layer_analysis JSONB, -- Analysis of architectural layers
    module_coupling JSONB, -- Coupling between modules/components
    module_cohesion JSONB, -- Cohesion within modules
    dependency_violations JSONB, -- Violations of dependency rules
    design_principles_adherence JSONB, -- Adherence to SOLID, DRY, etc.
    anti_patterns JSONB, -- Detected anti-patterns
    architecture_debt JSONB, -- Technical debt related to architecture
    refactoring_opportunities JSONB, -- Opportunities for architectural improvement
    scalability_assessment TEXT,
    maintainability_assessment TEXT,
    metadata JSONB
);

-- Trend analysis for tracking changes over time
CREATE TABLE IF NOT EXISTS trend_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID NOT NULL,
    metric_type VARCHAR(100) NOT NULL,
    metric_name VARCHAR(255) NOT NULL,
    time_period VARCHAR(50) NOT NULL, -- 'daily', 'weekly', 'monthly', 'quarterly'
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    data_points JSONB NOT NULL, -- Array of {date, value} objects
    trend_direction VARCHAR(20), -- 'improving', 'degrading', 'stable'
    trend_strength DECIMAL(5,2), -- Strength of the trend (0-100)
    seasonal_patterns JSONB, -- Detected seasonal patterns
    anomalies JSONB, -- Detected anomalies in the trend
    forecast JSONB, -- Forecasted future values
    statistical_summary JSONB, -- Mean, median, std dev, etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(repository_id, metric_type, metric_name, time_period, start_date, end_date)
);

-- Benchmarking and comparison data
CREATE TABLE IF NOT EXISTS benchmark_comparisons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID NOT NULL,
    comparison_type VARCHAR(100) NOT NULL, -- 'industry', 'similar_projects', 'historical'
    benchmark_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    comparison_metrics JSONB NOT NULL, -- Metrics being compared
    benchmark_data JSONB NOT NULL, -- Benchmark/comparison data
    percentile_rankings JSONB, -- Where this repo ranks in percentiles
    peer_group_definition JSONB, -- How the peer group was defined
    insights TEXT[],
    recommendations TEXT[],
    metadata JSONB,
    
    CONSTRAINT valid_comparison_type CHECK (comparison_type IN (
        'industry', 'similar_projects', 'historical', 'team', 'organization'
    ))
);

-- Indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_analysis_results_repository ON analysis_results(repository_id);
CREATE INDEX IF NOT EXISTS idx_analysis_results_type ON analysis_results(analysis_type);
CREATE INDEX IF NOT EXISTS idx_analysis_results_date ON analysis_results(analysis_date);
CREATE INDEX IF NOT EXISTS idx_analysis_results_file ON analysis_results(file_id);
CREATE INDEX IF NOT EXISTS idx_analysis_results_symbol ON analysis_results(symbol_id);
CREATE INDEX IF NOT EXISTS idx_analysis_results_score ON analysis_results(score);

CREATE INDEX IF NOT EXISTS idx_code_metrics_repository ON code_metrics(repository_id);
CREATE INDEX IF NOT EXISTS idx_code_metrics_type ON code_metrics(metric_type);
CREATE INDEX IF NOT EXISTS idx_code_metrics_name ON code_metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_code_metrics_date ON code_metrics(measurement_date);
CREATE INDEX IF NOT EXISTS idx_code_metrics_file ON code_metrics(file_id);
CREATE INDEX IF NOT EXISTS idx_code_metrics_symbol ON code_metrics(symbol_id);
CREATE INDEX IF NOT EXISTS idx_code_metrics_value ON code_metrics(metric_value);

CREATE INDEX IF NOT EXISTS idx_quality_assessments_repository ON quality_assessments(repository_id);
CREATE INDEX IF NOT EXISTS idx_quality_assessments_type ON quality_assessments(assessment_type);
CREATE INDEX IF NOT EXISTS idx_quality_assessments_score ON quality_assessments(quality_score);
CREATE INDEX IF NOT EXISTS idx_quality_assessments_date ON quality_assessments(assessment_date);

CREATE INDEX IF NOT EXISTS idx_security_analysis_repository ON security_analysis(repository_id);
CREATE INDEX IF NOT EXISTS idx_security_analysis_severity ON security_analysis(severity_level);
CREATE INDEX IF NOT EXISTS idx_security_analysis_type ON security_analysis(vulnerability_type);
CREATE INDEX IF NOT EXISTS idx_security_analysis_status ON security_analysis(status);
CREATE INDEX IF NOT EXISTS idx_security_analysis_date ON security_analysis(analysis_date);

CREATE INDEX IF NOT EXISTS idx_duplication_analysis_repository ON duplication_analysis(repository_id);
CREATE INDEX IF NOT EXISTS idx_duplication_analysis_group ON duplication_analysis(duplicate_group_id);
CREATE INDEX IF NOT EXISTS idx_duplication_analysis_hash ON duplication_analysis(content_hash);
CREATE INDEX IF NOT EXISTS idx_duplication_analysis_score ON duplication_analysis(similarity_score);

CREATE INDEX IF NOT EXISTS idx_dead_code_analysis_repository ON dead_code_analysis(repository_id);
CREATE INDEX IF NOT EXISTS idx_dead_code_analysis_type ON dead_code_analysis(dead_code_type);
CREATE INDEX IF NOT EXISTS idx_dead_code_analysis_confidence ON dead_code_analysis(confidence_level);
CREATE INDEX IF NOT EXISTS idx_dead_code_analysis_recommendation ON dead_code_analysis(removal_recommendation);

CREATE INDEX IF NOT EXISTS idx_trend_analysis_repository ON trend_analysis(repository_id);
CREATE INDEX IF NOT EXISTS idx_trend_analysis_metric ON trend_analysis(metric_type, metric_name);
CREATE INDEX IF NOT EXISTS idx_trend_analysis_period ON trend_analysis(time_period);
CREATE INDEX IF NOT EXISTS idx_trend_analysis_dates ON trend_analysis(start_date, end_date);

-- Triggers for automatic timestamp updates
CREATE TRIGGER update_analysis_results_updated_at BEFORE UPDATE ON analysis_results
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Views for common analytics queries
CREATE OR REPLACE VIEW repository_health_summary AS
SELECT 
    r.repository_id,
    AVG(CASE WHEN r.analysis_type = 'quality' THEN r.score END) as avg_quality_score,
    AVG(CASE WHEN r.analysis_type = 'complexity' THEN r.score END) as avg_complexity_score,
    AVG(CASE WHEN r.analysis_type = 'maintainability' THEN r.score END) as avg_maintainability_score,
    COUNT(CASE WHEN sa.severity_level IN ('critical', 'high') THEN 1 END) as high_severity_issues,
    COUNT(CASE WHEN dca.removal_recommendation = 'safe_to_remove' THEN 1 END) as removable_dead_code_items,
    MAX(r.analysis_date) as last_analysis_date
FROM analysis_results r
LEFT JOIN security_analysis sa ON r.repository_id = sa.repository_id
LEFT JOIN dead_code_analysis dca ON r.repository_id = dca.repository_id
GROUP BY r.repository_id;

CREATE OR REPLACE VIEW metric_trends_summary AS
SELECT 
    repository_id,
    metric_type,
    metric_name,
    COUNT(*) as measurement_count,
    MIN(measurement_date) as first_measurement,
    MAX(measurement_date) as last_measurement,
    AVG(metric_value) as avg_value,
    STDDEV(metric_value) as value_stddev,
    COUNT(CASE WHEN trend_direction = 'improving' THEN 1 END) as improving_count,
    COUNT(CASE WHEN trend_direction = 'degrading' THEN 1 END) as degrading_count
FROM code_metrics
GROUP BY repository_id, metric_type, metric_name;

CREATE OR REPLACE VIEW security_risk_summary AS
SELECT 
    repository_id,
    COUNT(*) as total_vulnerabilities,
    COUNT(CASE WHEN severity_level = 'critical' THEN 1 END) as critical_count,
    COUNT(CASE WHEN severity_level = 'high' THEN 1 END) as high_count,
    COUNT(CASE WHEN severity_level = 'medium' THEN 1 END) as medium_count,
    COUNT(CASE WHEN severity_level = 'low' THEN 1 END) as low_count,
    COUNT(CASE WHEN status = 'open' THEN 1 END) as open_issues,
    AVG(cvss_score) as avg_cvss_score,
    MAX(analysis_date) as last_security_scan
FROM security_analysis
GROUP BY repository_id;

-- Sample data for testing
INSERT INTO analysis_results (analysis_type, repository_id, analyzer_name, results, score) VALUES
('complexity', (SELECT id FROM repositories WHERE name = 'graph-sitter' LIMIT 1), 'cyclomatic_complexity_analyzer', 
 '{"average_complexity": 3.2, "max_complexity": 15, "functions_analyzed": 245}', 85.5),
('quality', (SELECT id FROM repositories WHERE name = 'graph-sitter' LIMIT 1), 'code_quality_analyzer',
 '{"maintainability_index": 78, "documentation_coverage": 65, "test_coverage": 82}', 75.0),
('dependencies', (SELECT id FROM repositories WHERE name = 'graph-sitter' LIMIT 1), 'dependency_analyzer',
 '{"total_dependencies": 42, "outdated_dependencies": 5, "vulnerable_dependencies": 2}', 88.0);

