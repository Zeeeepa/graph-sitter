-- =====================================================
-- CODEBASE ANALYTICS DATABASE SCHEMA
-- Comprehensive code metrics and analysis system
-- =====================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- =====================================================
-- ENUMS AND TYPES
-- =====================================================

-- Programming language enumeration
CREATE TYPE programming_language_enum AS ENUM (
    'python',
    'typescript',
    'javascript',
    'java',
    'csharp',
    'cpp',
    'c',
    'rust',
    'go',
    'ruby',
    'php',
    'swift',
    'kotlin',
    'scala',
    'r',
    'sql',
    'html',
    'css',
    'shell',
    'yaml',
    'json',
    'xml',
    'markdown',
    'other'
);

-- Symbol type enumeration
CREATE TYPE symbol_type_enum AS ENUM (
    'function',
    'method',
    'class',
    'interface',
    'enum',
    'variable',
    'constant',
    'property',
    'parameter',
    'import',
    'export',
    'type_alias',
    'namespace',
    'module',
    'decorator',
    'annotation'
);

-- Visibility enumeration
CREATE TYPE visibility_enum AS ENUM (
    'public',
    'private',
    'protected',
    'internal',
    'package',
    'module'
);

-- Dependency type enumeration
CREATE TYPE dependency_type_enum AS ENUM (
    'import',
    'require',
    'include',
    'extends',
    'implements',
    'calls',
    'references',
    'inherits',
    'uses',
    'depends_on'
);

-- Code quality level enumeration
CREATE TYPE quality_level_enum AS ENUM (
    'excellent',
    'good',
    'fair',
    'poor',
    'critical'
);

-- Analysis type enumeration
CREATE TYPE analysis_type_enum AS ENUM (
    'complexity',
    'maintainability',
    'security',
    'performance',
    'documentation',
    'testing',
    'dependencies',
    'dead_code',
    'duplication',
    'style'
);

-- =====================================================
-- CORE TABLES
-- =====================================================

-- Repositories table
CREATE TABLE repositories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    full_name VARCHAR(500) NOT NULL UNIQUE,
    url VARCHAR(1000),
    default_branch VARCHAR(100) DEFAULT 'main',
    language programming_language_enum,
    description TEXT,
    is_private BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    last_analyzed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Commits table for version tracking
CREATE TABLE commits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID REFERENCES repositories(id) ON DELETE CASCADE,
    sha VARCHAR(40) NOT NULL,
    message TEXT,
    author_name VARCHAR(255),
    author_email VARCHAR(255),
    committer_name VARCHAR(255),
    committer_email VARCHAR(255),
    committed_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(repository_id, sha)
);

-- Files table
CREATE TABLE files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID REFERENCES repositories(id) ON DELETE CASCADE,
    commit_id UUID REFERENCES commits(id) ON DELETE CASCADE,
    file_path VARCHAR(1000) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_extension VARCHAR(50),
    language programming_language_enum,
    file_size_bytes BIGINT,
    content_hash VARCHAR(64),
    is_binary BOOLEAN DEFAULT FALSE,
    is_generated BOOLEAN DEFAULT FALSE,
    is_test_file BOOLEAN DEFAULT FALSE,
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(repository_id, commit_id, file_path)
);

-- Code metrics table
CREATE TABLE code_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id UUID REFERENCES files(id) ON DELETE CASCADE,
    repository_id UUID REFERENCES repositories(id) ON DELETE CASCADE,
    commit_id UUID REFERENCES commits(id) ON DELETE CASCADE,
    
    -- Basic metrics
    lines_of_code INTEGER DEFAULT 0,
    source_lines_of_code INTEGER DEFAULT 0,
    logical_lines_of_code INTEGER DEFAULT 0,
    comment_lines INTEGER DEFAULT 0,
    blank_lines INTEGER DEFAULT 0,
    
    -- Complexity metrics
    cyclomatic_complexity INTEGER DEFAULT 0,
    cognitive_complexity INTEGER DEFAULT 0,
    npath_complexity BIGINT DEFAULT 0,
    
    -- Halstead metrics
    halstead_vocabulary INTEGER DEFAULT 0,
    halstead_length INTEGER DEFAULT 0,
    halstead_volume DECIMAL(12,2) DEFAULT 0,
    halstead_difficulty DECIMAL(8,2) DEFAULT 0,
    halstead_effort DECIMAL(15,2) DEFAULT 0,
    halstead_time DECIMAL(10,2) DEFAULT 0,
    halstead_bugs DECIMAL(8,4) DEFAULT 0,
    
    -- Maintainability metrics
    maintainability_index DECIMAL(5,2) DEFAULT 0,
    technical_debt_ratio DECIMAL(5,4) DEFAULT 0,
    code_duplication_ratio DECIMAL(5,4) DEFAULT 0,
    
    -- Object-oriented metrics
    depth_of_inheritance INTEGER DEFAULT 0,
    coupling_between_objects INTEGER DEFAULT 0,
    lack_of_cohesion INTEGER DEFAULT 0,
    number_of_children INTEGER DEFAULT 0,
    
    -- Function/method metrics
    function_count INTEGER DEFAULT 0,
    class_count INTEGER DEFAULT 0,
    method_count INTEGER DEFAULT 0,
    parameter_count INTEGER DEFAULT 0,
    
    -- Quality indicators
    test_coverage_percentage DECIMAL(5,2) DEFAULT 0,
    documentation_coverage_percentage DECIMAL(5,2) DEFAULT 0,
    
    -- Timestamps
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Symbols table for functions, classes, variables, etc.
CREATE TABLE symbols (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id UUID REFERENCES files(id) ON DELETE CASCADE,
    repository_id UUID REFERENCES repositories(id) ON DELETE CASCADE,
    commit_id UUID REFERENCES commits(id) ON DELETE CASCADE,
    
    -- Symbol identification
    name VARCHAR(500) NOT NULL,
    qualified_name VARCHAR(1000),
    symbol_type symbol_type_enum NOT NULL,
    visibility visibility_enum DEFAULT 'public',
    
    -- Location information
    start_line INTEGER,
    end_line INTEGER,
    start_column INTEGER,
    end_column INTEGER,
    
    -- Symbol characteristics
    is_abstract BOOLEAN DEFAULT FALSE,
    is_static BOOLEAN DEFAULT FALSE,
    is_async BOOLEAN DEFAULT FALSE,
    is_generator BOOLEAN DEFAULT FALSE,
    is_deprecated BOOLEAN DEFAULT FALSE,
    is_exported BOOLEAN DEFAULT FALSE,
    
    -- Metrics
    complexity_score INTEGER DEFAULT 0,
    parameter_count INTEGER DEFAULT 0,
    return_type VARCHAR(200),
    
    -- Documentation
    docstring TEXT,
    documentation_quality_score DECIMAL(3,2) DEFAULT 0,
    
    -- Metadata
    annotations JSONB,
    decorators TEXT[],
    modifiers TEXT[],
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes for performance
    CONSTRAINT unique_symbol_location UNIQUE(file_id, name, start_line, symbol_type)
);

-- Dependencies table for tracking relationships
CREATE TABLE dependencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID REFERENCES repositories(id) ON DELETE CASCADE,
    commit_id UUID REFERENCES commits(id) ON DELETE CASCADE,
    
    -- Source and target
    source_file_id UUID REFERENCES files(id) ON DELETE CASCADE,
    target_file_id UUID REFERENCES files(id) ON DELETE CASCADE,
    source_symbol_id UUID REFERENCES symbols(id) ON DELETE CASCADE,
    target_symbol_id UUID REFERENCES symbols(id) ON DELETE CASCADE,
    
    -- Dependency details
    dependency_type dependency_type_enum NOT NULL,
    import_statement TEXT,
    line_number INTEGER,
    
    -- Relationship characteristics
    is_circular BOOLEAN DEFAULT FALSE,
    is_external BOOLEAN DEFAULT FALSE,
    is_transitive BOOLEAN DEFAULT FALSE,
    depth_level INTEGER DEFAULT 1,
    weight DECIMAL(5,2) DEFAULT 1.0,
    
    -- Metadata
    metadata JSONB,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Prevent duplicate dependencies
    UNIQUE(source_file_id, target_file_id, dependency_type, line_number)
);

-- Function calls table
CREATE TABLE function_calls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID REFERENCES repositories(id) ON DELETE CASCADE,
    commit_id UUID REFERENCES commits(id) ON DELETE CASCADE,
    
    -- Call relationship
    caller_symbol_id UUID REFERENCES symbols(id) ON DELETE CASCADE,
    callee_symbol_id UUID REFERENCES symbols(id) ON DELETE CASCADE,
    caller_file_id UUID REFERENCES files(id) ON DELETE CASCADE,
    callee_file_id UUID REFERENCES files(id) ON DELETE CASCADE,
    
    -- Call details
    call_type VARCHAR(50), -- direct, indirect, recursive, etc.
    line_number INTEGER,
    column_number INTEGER,
    call_count INTEGER DEFAULT 1,
    
    -- Call characteristics
    is_recursive BOOLEAN DEFAULT FALSE,
    is_async BOOLEAN DEFAULT FALSE,
    is_conditional BOOLEAN DEFAULT FALSE,
    
    -- Performance data
    estimated_frequency DECIMAL(10,2) DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(caller_symbol_id, callee_symbol_id, line_number)
);

-- Dead code detection table
CREATE TABLE dead_code (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID REFERENCES repositories(id) ON DELETE CASCADE,
    commit_id UUID REFERENCES commits(id) ON DELETE CASCADE,
    file_id UUID REFERENCES files(id) ON DELETE CASCADE,
    symbol_id UUID REFERENCES symbols(id) ON DELETE CASCADE,
    
    -- Dead code details
    dead_code_type VARCHAR(100), -- unused_function, unreachable_code, unused_variable, etc.
    confidence_score DECIMAL(3,2) DEFAULT 0,
    reason TEXT,
    
    -- Location
    start_line INTEGER,
    end_line INTEGER,
    
    -- Impact analysis
    potential_savings_loc INTEGER DEFAULT 0,
    removal_risk_level quality_level_enum DEFAULT 'good',
    
    -- Status
    is_confirmed BOOLEAN DEFAULT FALSE,
    is_false_positive BOOLEAN DEFAULT FALSE,
    reviewed_by VARCHAR(255),
    reviewed_at TIMESTAMP,
    
    -- Timestamps
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Code duplication table
CREATE TABLE code_duplications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID REFERENCES repositories(id) ON DELETE CASCADE,
    commit_id UUID REFERENCES commits(id) ON DELETE CASCADE,
    
    -- Duplication group
    duplication_group_id UUID NOT NULL,
    
    -- Location
    file_id UUID REFERENCES files(id) ON DELETE CASCADE,
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    
    -- Duplication metrics
    duplicate_lines INTEGER NOT NULL,
    similarity_percentage DECIMAL(5,2) NOT NULL,
    
    -- Content
    content_hash VARCHAR(64),
    normalized_content_hash VARCHAR(64),
    
    -- Timestamps
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- API documentation table
CREATE TABLE api_documentation (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID REFERENCES repositories(id) ON DELETE CASCADE,
    commit_id UUID REFERENCES commits(id) ON DELETE CASCADE,
    symbol_id UUID REFERENCES symbols(id) ON DELETE CASCADE,
    
    -- Documentation content
    title VARCHAR(500),
    description TEXT,
    parameters JSONB,
    return_value JSONB,
    examples TEXT[],
    see_also TEXT[],
    
    -- Documentation quality
    completeness_score DECIMAL(3,2) DEFAULT 0,
    clarity_score DECIMAL(3,2) DEFAULT 0,
    accuracy_score DECIMAL(3,2) DEFAULT 0,
    
    -- Generation metadata
    is_auto_generated BOOLEAN DEFAULT FALSE,
    generation_method VARCHAR(100),
    
    -- Timestamps
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Impact analysis table
CREATE TABLE impact_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID REFERENCES repositories(id) ON DELETE CASCADE,
    
    -- Change details
    change_type VARCHAR(100), -- modification, addition, deletion
    affected_symbol_id UUID REFERENCES symbols(id),
    affected_file_id UUID REFERENCES files(id),
    
    -- Impact scope
    impact_radius INTEGER DEFAULT 0, -- number of affected components
    affected_files_count INTEGER DEFAULT 0,
    affected_symbols_count INTEGER DEFAULT 0,
    affected_tests_count INTEGER DEFAULT 0,
    
    -- Risk assessment
    risk_level quality_level_enum DEFAULT 'good',
    breaking_change_probability DECIMAL(3,2) DEFAULT 0,
    
    -- Affected components
    affected_files JSONB,
    affected_symbols JSONB,
    affected_dependencies JSONB,
    
    -- Recommendations
    recommendations TEXT[],
    required_tests TEXT[],
    
    -- Timestamps
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Analysis runs table for tracking analysis sessions
CREATE TABLE analysis_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID REFERENCES repositories(id) ON DELETE CASCADE,
    commit_id UUID REFERENCES commits(id) ON DELETE CASCADE,
    
    -- Run details
    analysis_type analysis_type_enum NOT NULL,
    status VARCHAR(50) DEFAULT 'running',
    
    -- Configuration
    configuration JSONB,
    
    -- Results summary
    files_analyzed INTEGER DEFAULT 0,
    symbols_found INTEGER DEFAULT 0,
    issues_found INTEGER DEFAULT 0,
    
    -- Performance metrics
    execution_time_ms BIGINT,
    memory_usage_mb INTEGER,
    
    -- Error handling
    error_message TEXT,
    warnings TEXT[],
    
    -- Timestamps
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

-- Repository indexes
CREATE INDEX idx_repositories_name ON repositories(name);
CREATE INDEX idx_repositories_language ON repositories(language);
CREATE INDEX idx_repositories_active ON repositories(is_active);

-- Commit indexes
CREATE INDEX idx_commits_repository ON commits(repository_id);
CREATE INDEX idx_commits_sha ON commits(sha);
CREATE INDEX idx_commits_date ON commits(committed_at);

-- File indexes
CREATE INDEX idx_files_repository ON files(repository_id);
CREATE INDEX idx_files_commit ON files(commit_id);
CREATE INDEX idx_files_path ON files(file_path);
CREATE INDEX idx_files_language ON files(language);
CREATE INDEX idx_files_extension ON files(file_extension);

-- Code metrics indexes
CREATE INDEX idx_code_metrics_file ON code_metrics(file_id);
CREATE INDEX idx_code_metrics_repository ON code_metrics(repository_id);
CREATE INDEX idx_code_metrics_complexity ON code_metrics(cyclomatic_complexity);
CREATE INDEX idx_code_metrics_maintainability ON code_metrics(maintainability_index);

-- Symbol indexes
CREATE INDEX idx_symbols_file ON symbols(file_id);
CREATE INDEX idx_symbols_repository ON symbols(repository_id);
CREATE INDEX idx_symbols_name ON symbols(name);
CREATE INDEX idx_symbols_type ON symbols(symbol_type);
CREATE INDEX idx_symbols_visibility ON symbols(visibility);

-- Dependency indexes
CREATE INDEX idx_dependencies_source_file ON dependencies(source_file_id);
CREATE INDEX idx_dependencies_target_file ON dependencies(target_file_id);
CREATE INDEX idx_dependencies_source_symbol ON dependencies(source_symbol_id);
CREATE INDEX idx_dependencies_target_symbol ON dependencies(target_symbol_id);
CREATE INDEX idx_dependencies_type ON dependencies(dependency_type);
CREATE INDEX idx_dependencies_circular ON dependencies(is_circular);

-- Function call indexes
CREATE INDEX idx_function_calls_caller ON function_calls(caller_symbol_id);
CREATE INDEX idx_function_calls_callee ON function_calls(callee_symbol_id);
CREATE INDEX idx_function_calls_repository ON function_calls(repository_id);

-- Dead code indexes
CREATE INDEX idx_dead_code_repository ON dead_code(repository_id);
CREATE INDEX idx_dead_code_file ON dead_code(file_id);
CREATE INDEX idx_dead_code_type ON dead_code(dead_code_type);
CREATE INDEX idx_dead_code_confidence ON dead_code(confidence_score);

-- Full-text search indexes
CREATE INDEX idx_symbols_name_search ON symbols USING gin(to_tsvector('english', name));
CREATE INDEX idx_symbols_docstring_search ON symbols USING gin(to_tsvector('english', docstring));
CREATE INDEX idx_files_path_search ON files USING gin(to_tsvector('english', file_path));

-- JSONB indexes
CREATE INDEX idx_symbols_annotations ON symbols USING gin(annotations);
CREATE INDEX idx_dependencies_metadata ON dependencies USING gin(metadata);
CREATE INDEX idx_analysis_runs_config ON analysis_runs USING gin(configuration);

-- Composite indexes for common queries
CREATE INDEX idx_symbols_file_type ON symbols(file_id, symbol_type);
CREATE INDEX idx_code_metrics_repo_commit ON code_metrics(repository_id, commit_id);
CREATE INDEX idx_dependencies_repo_type ON dependencies(repository_id, dependency_type);

-- =====================================================
-- TRIGGERS AND FUNCTIONS
-- =====================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at trigger
CREATE TRIGGER update_repositories_updated_at BEFORE UPDATE ON repositories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to calculate maintainability index
CREATE OR REPLACE FUNCTION calculate_maintainability_index(
    halstead_volume DECIMAL,
    cyclomatic_complexity INTEGER,
    lines_of_code INTEGER
)
RETURNS DECIMAL AS $$
BEGIN
    -- Microsoft's maintainability index formula
    RETURN GREATEST(0, 
        171 - 5.2 * LN(GREATEST(1, halstead_volume)) 
        - 0.23 * cyclomatic_complexity 
        - 16.2 * LN(GREATEST(1, lines_of_code))
    );
END;
$$ LANGUAGE plpgsql;

-- Function to detect circular dependencies
CREATE OR REPLACE FUNCTION detect_circular_dependencies(repo_id UUID)
RETURNS TABLE (
    dependency_chain TEXT[],
    chain_length INTEGER
) AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE dependency_chain AS (
        -- Base case: start with all dependencies
        SELECT 
            ARRAY[source_file_id::TEXT, target_file_id::TEXT] as chain,
            source_file_id,
            target_file_id,
            1 as depth
        FROM dependencies 
        WHERE repository_id = repo_id
        
        UNION ALL
        
        -- Recursive case: extend chains
        SELECT 
            dc.chain || d.target_file_id::TEXT,
            dc.source_file_id,
            d.target_file_id,
            dc.depth + 1
        FROM dependency_chain dc
        JOIN dependencies d ON dc.target_file_id = d.source_file_id
        WHERE d.repository_id = repo_id
            AND dc.depth < 20  -- Prevent infinite recursion
            AND NOT (d.target_file_id = ANY(dc.chain::UUID[]))  -- Prevent cycles in chain building
    )
    SELECT 
        dc.chain,
        dc.depth
    FROM dependency_chain dc
    WHERE dc.target_file_id = dc.source_file_id  -- Found a cycle
    ORDER BY dc.depth;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate code quality score
CREATE OR REPLACE FUNCTION calculate_quality_score(
    maintainability_index DECIMAL,
    test_coverage DECIMAL,
    documentation_coverage DECIMAL,
    duplication_ratio DECIMAL,
    complexity INTEGER
)
RETURNS DECIMAL AS $$
DECLARE
    quality_score DECIMAL := 0;
BEGIN
    -- Weighted quality score calculation
    quality_score := (
        maintainability_index * 0.3 +
        test_coverage * 0.25 +
        documentation_coverage * 0.2 +
        (100 - duplication_ratio * 100) * 0.15 +
        GREATEST(0, 100 - complexity * 2) * 0.1
    );
    
    RETURN LEAST(100, GREATEST(0, quality_score));
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- VIEWS FOR COMMON QUERIES
-- =====================================================

-- Repository summary view
CREATE VIEW repository_summary AS
SELECT 
    r.id,
    r.name,
    r.language,
    COUNT(DISTINCT f.id) as total_files,
    COUNT(DISTINCT s.id) as total_symbols,
    SUM(cm.lines_of_code) as total_loc,
    AVG(cm.maintainability_index) as avg_maintainability,
    AVG(cm.cyclomatic_complexity) as avg_complexity,
    COUNT(DISTINCT CASE WHEN dc.id IS NOT NULL THEN dc.id END) as dead_code_issues,
    r.last_analyzed_at
FROM repositories r
LEFT JOIN files f ON r.id = f.repository_id
LEFT JOIN symbols s ON f.id = s.file_id
LEFT JOIN code_metrics cm ON f.id = cm.file_id
LEFT JOIN dead_code dc ON f.id = dc.file_id
GROUP BY r.id, r.name, r.language, r.last_analyzed_at;

-- File quality dashboard
CREATE VIEW file_quality_dashboard AS
SELECT 
    f.id,
    f.file_path,
    f.language,
    cm.lines_of_code,
    cm.cyclomatic_complexity,
    cm.maintainability_index,
    cm.test_coverage_percentage,
    cm.documentation_coverage_percentage,
    cm.code_duplication_ratio,
    calculate_quality_score(
        cm.maintainability_index,
        cm.test_coverage_percentage,
        cm.documentation_coverage_percentage,
        cm.code_duplication_ratio,
        cm.cyclomatic_complexity
    ) as quality_score,
    CASE 
        WHEN cm.maintainability_index >= 80 THEN 'excellent'
        WHEN cm.maintainability_index >= 60 THEN 'good'
        WHEN cm.maintainability_index >= 40 THEN 'fair'
        WHEN cm.maintainability_index >= 20 THEN 'poor'
        ELSE 'critical'
    END as quality_level
FROM files f
JOIN code_metrics cm ON f.id = cm.file_id;

-- Symbol complexity view
CREATE VIEW symbol_complexity_analysis AS
SELECT 
    s.id,
    s.name,
    s.symbol_type,
    s.complexity_score,
    s.parameter_count,
    f.file_path,
    f.language,
    COUNT(fc.id) as call_count,
    COUNT(DISTINCT fc.caller_symbol_id) as unique_callers,
    s.is_deprecated,
    CASE 
        WHEN s.complexity_score <= 5 THEN 'simple'
        WHEN s.complexity_score <= 10 THEN 'moderate'
        WHEN s.complexity_score <= 20 THEN 'complex'
        ELSE 'very_complex'
    END as complexity_level
FROM symbols s
JOIN files f ON s.file_id = f.id
LEFT JOIN function_calls fc ON s.id = fc.callee_symbol_id
GROUP BY s.id, s.name, s.symbol_type, s.complexity_score, s.parameter_count, 
         f.file_path, f.language, s.is_deprecated;

-- Dependency analysis view
CREATE VIEW dependency_analysis AS
SELECT 
    r.name as repository_name,
    COUNT(d.id) as total_dependencies,
    COUNT(CASE WHEN d.is_circular THEN 1 END) as circular_dependencies,
    COUNT(CASE WHEN d.is_external THEN 1 END) as external_dependencies,
    AVG(d.depth_level) as avg_dependency_depth,
    COUNT(DISTINCT d.source_file_id) as files_with_dependencies,
    COUNT(DISTINCT d.target_file_id) as files_being_depended_on
FROM repositories r
LEFT JOIN dependencies d ON r.id = d.repository_id
GROUP BY r.id, r.name;

-- =====================================================
-- ANALYTICAL FUNCTIONS
-- =====================================================

-- Function to get top complex files
CREATE OR REPLACE FUNCTION get_top_complex_files(
    repo_id UUID,
    limit_count INTEGER DEFAULT 10
)
RETURNS TABLE (
    file_path VARCHAR,
    complexity_score INTEGER,
    maintainability_index DECIMAL,
    lines_of_code INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        f.file_path,
        cm.cyclomatic_complexity as complexity_score,
        cm.maintainability_index,
        cm.lines_of_code
    FROM files f
    JOIN code_metrics cm ON f.id = cm.file_id
    WHERE f.repository_id = repo_id
    ORDER BY cm.cyclomatic_complexity DESC
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

-- Function to analyze code hotspots
CREATE OR REPLACE FUNCTION analyze_code_hotspots(repo_id UUID)
RETURNS TABLE (
    file_path VARCHAR,
    symbol_name VARCHAR,
    change_frequency INTEGER,
    complexity_score INTEGER,
    hotspot_score DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        f.file_path,
        s.name as symbol_name,
        COUNT(DISTINCT c.id) as change_frequency,
        s.complexity_score,
        (COUNT(DISTINCT c.id) * s.complexity_score)::DECIMAL as hotspot_score
    FROM files f
    JOIN symbols s ON f.id = s.file_id
    JOIN commits c ON f.commit_id = c.id
    WHERE f.repository_id = repo_id
    GROUP BY f.file_path, s.name, s.complexity_score
    HAVING COUNT(DISTINCT c.id) > 1
    ORDER BY hotspot_score DESC;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- SAMPLE DATA FOR TESTING
-- =====================================================

-- Insert sample repository
INSERT INTO repositories (name, full_name, language, description) VALUES
('graph-sitter-core', 'example/graph-sitter-core', 'python', 'Core graph-sitter parsing engine'),
('analytics-dashboard', 'example/analytics-dashboard', 'typescript', 'Code analytics visualization'),
('api-gateway', 'example/api-gateway', 'java', 'Microservices API gateway');

-- =====================================================
-- PERFORMANCE MONITORING
-- =====================================================

-- Function to get repository health metrics
CREATE OR REPLACE FUNCTION get_repository_health(repo_id UUID)
RETURNS TABLE (
    metric_name VARCHAR,
    metric_value DECIMAL,
    status VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        'Average Maintainability'::VARCHAR,
        AVG(cm.maintainability_index),
        CASE 
            WHEN AVG(cm.maintainability_index) >= 70 THEN 'healthy'
            WHEN AVG(cm.maintainability_index) >= 50 THEN 'warning'
            ELSE 'critical'
        END::VARCHAR
    FROM code_metrics cm
    JOIN files f ON cm.file_id = f.id
    WHERE f.repository_id = repo_id
    
    UNION ALL
    
    SELECT 
        'Test Coverage'::VARCHAR,
        AVG(cm.test_coverage_percentage),
        CASE 
            WHEN AVG(cm.test_coverage_percentage) >= 80 THEN 'healthy'
            WHEN AVG(cm.test_coverage_percentage) >= 60 THEN 'warning'
            ELSE 'critical'
        END::VARCHAR
    FROM code_metrics cm
    JOIN files f ON cm.file_id = f.id
    WHERE f.repository_id = repo_id
    
    UNION ALL
    
    SELECT 
        'Dead Code Ratio'::VARCHAR,
        (COUNT(dc.id)::DECIMAL / NULLIF(COUNT(s.id), 0) * 100),
        CASE 
            WHEN (COUNT(dc.id)::DECIMAL / NULLIF(COUNT(s.id), 0) * 100) <= 5 THEN 'healthy'
            WHEN (COUNT(dc.id)::DECIMAL / NULLIF(COUNT(s.id), 0) * 100) <= 15 THEN 'warning'
            ELSE 'critical'
        END::VARCHAR
    FROM symbols s
    LEFT JOIN dead_code dc ON s.id = dc.symbol_id
    JOIN files f ON s.file_id = f.id
    WHERE f.repository_id = repo_id;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- COMMENTS AND DOCUMENTATION
-- =====================================================

COMMENT ON TABLE repositories IS 'Central repository information and metadata';
COMMENT ON TABLE code_metrics IS 'Comprehensive code quality and complexity metrics';
COMMENT ON TABLE symbols IS 'All code symbols (functions, classes, variables) with detailed metadata';
COMMENT ON TABLE dependencies IS 'File and symbol-level dependency relationships';
COMMENT ON TABLE function_calls IS 'Function call relationships for call graph analysis';
COMMENT ON TABLE dead_code IS 'Detected unused or unreachable code segments';
COMMENT ON TABLE impact_analysis IS 'Change impact analysis and risk assessment';

COMMENT ON COLUMN code_metrics.maintainability_index IS 'Microsoft maintainability index (0-100)';
COMMENT ON COLUMN code_metrics.technical_debt_ratio IS 'Ratio of technical debt to total development cost';
COMMENT ON COLUMN symbols.complexity_score IS 'Cyclomatic complexity score for the symbol';
COMMENT ON COLUMN dependencies.is_circular IS 'Indicates if this dependency creates a circular reference';

-- =====================================================
-- GRANTS AND PERMISSIONS
-- =====================================================

-- Create roles for different access levels
-- CREATE ROLE analytics_admin;
-- CREATE ROLE analytics_analyst;
-- CREATE ROLE analytics_viewer;

-- Grant appropriate permissions
-- GRANT ALL ON ALL TABLES IN SCHEMA public TO analytics_admin;
-- GRANT SELECT, INSERT, UPDATE ON code_metrics, symbols, dependencies TO analytics_analyst;
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO analytics_viewer;

