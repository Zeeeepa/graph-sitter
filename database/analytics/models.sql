-- Analytics Module Database Schema
-- Comprehensive codebase analysis and metrics storage system

-- Main codebase analysis results table
CREATE TABLE codebase_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    codebase_id UUID REFERENCES codebases(id) ON DELETE CASCADE,
    analysis_type analysis_type NOT NULL,
    
    -- Analysis metadata
    analyzer_version VARCHAR(20) DEFAULT '1.0',
    analysis_config JSONB DEFAULT '{}',
    
    -- Results and metrics
    results JSONB DEFAULT '{}',
    metrics JSONB DEFAULT '{}',
    summary JSONB DEFAULT '{}',
    
    -- Performance tracking
    analysis_duration_ms INTEGER,
    files_analyzed INTEGER DEFAULT 0,
    
    -- Status and timing
    status VARCHAR(20) DEFAULT 'pending', -- pending, running, completed, failed
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(codebase_id, analysis_type)
);

-- File-level analysis results
CREATE TABLE file_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    codebase_id UUID REFERENCES codebases(id) ON DELETE CASCADE,
    file_path VARCHAR(1000) NOT NULL,
    file_hash VARCHAR(64),
    language language_type,
    
    -- Basic metrics
    lines_of_code INTEGER DEFAULT 0,
    source_lines_of_code INTEGER DEFAULT 0,
    logical_lines_of_code INTEGER DEFAULT 0,
    comment_lines INTEGER DEFAULT 0,
    blank_lines INTEGER DEFAULT 0,
    
    -- Complexity metrics
    cyclomatic_complexity INTEGER DEFAULT 0,
    cognitive_complexity INTEGER DEFAULT 0,
    halstead_volume DECIMAL(10,2),
    maintainability_index INTEGER,
    
    -- Structure counts
    function_count INTEGER DEFAULT 0,
    class_count INTEGER DEFAULT 0,
    import_count INTEGER DEFAULT 0,
    export_count INTEGER DEFAULT 0,
    
    -- Quality indicators
    test_coverage DECIMAL(5,2),
    documentation_coverage DECIMAL(5,2),
    
    -- Detailed analysis results
    functions JSONB DEFAULT '[]',
    classes JSONB DEFAULT '[]',
    imports JSONB DEFAULT '[]',
    exports JSONB DEFAULT '[]',
    issues JSONB DEFAULT '[]',
    
    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(codebase_id, file_path)
);

-- Function-level analysis
CREATE TABLE function_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    file_analysis_id UUID REFERENCES file_analysis(id) ON DELETE CASCADE,
    codebase_id UUID REFERENCES codebases(id) ON DELETE CASCADE,
    
    -- Function identification
    function_name VARCHAR(255) NOT NULL,
    function_signature TEXT,
    start_line INTEGER,
    end_line INTEGER,
    
    -- Complexity metrics
    cyclomatic_complexity INTEGER DEFAULT 0,
    cognitive_complexity INTEGER DEFAULT 0,
    parameter_count INTEGER DEFAULT 0,
    return_count INTEGER DEFAULT 0,
    
    -- Usage analysis
    call_count INTEGER DEFAULT 0,
    is_recursive BOOLEAN DEFAULT FALSE,
    is_async BOOLEAN DEFAULT FALSE,
    is_generator BOOLEAN DEFAULT FALSE,
    
    -- Dependencies
    calls_functions JSONB DEFAULT '[]',
    called_by_functions JSONB DEFAULT '[]',
    dependencies JSONB DEFAULT '[]',
    
    -- Quality metrics
    has_docstring BOOLEAN DEFAULT FALSE,
    has_tests BOOLEAN DEFAULT FALSE,
    test_coverage DECIMAL(5,2),
    
    -- Source code
    source_code TEXT,
    
    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Class-level analysis
CREATE TABLE class_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    file_analysis_id UUID REFERENCES file_analysis(id) ON DELETE CASCADE,
    codebase_id UUID REFERENCES codebases(id) ON DELETE CASCADE,
    
    -- Class identification
    class_name VARCHAR(255) NOT NULL,
    start_line INTEGER,
    end_line INTEGER,
    
    -- Inheritance analysis
    superclasses JSONB DEFAULT '[]',
    subclasses JSONB DEFAULT '[]',
    depth_of_inheritance INTEGER DEFAULT 0,
    
    -- Structure metrics
    method_count INTEGER DEFAULT 0,
    property_count INTEGER DEFAULT 0,
    private_method_count INTEGER DEFAULT 0,
    public_method_count INTEGER DEFAULT 0,
    
    -- Complexity
    weighted_methods_per_class INTEGER DEFAULT 0,
    coupling_between_objects INTEGER DEFAULT 0,
    
    -- Methods and properties
    methods JSONB DEFAULT '[]',
    properties JSONB DEFAULT '[]',
    
    -- Quality indicators
    has_docstring BOOLEAN DEFAULT FALSE,
    has_tests BOOLEAN DEFAULT FALSE,
    
    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Dependency graph storage
CREATE TABLE dependency_graph (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    codebase_id UUID REFERENCES codebases(id) ON DELETE CASCADE,
    
    -- Dependency relationship
    source_file VARCHAR(1000) NOT NULL,
    target_file VARCHAR(1000) NOT NULL,
    dependency_type VARCHAR(50) NOT NULL, -- import, inheritance, composition, usage
    
    -- Dependency details
    symbol_name VARCHAR(255),
    import_statement TEXT,
    line_number INTEGER,
    
    -- Metadata
    is_external BOOLEAN DEFAULT FALSE,
    is_circular BOOLEAN DEFAULT FALSE,
    weight INTEGER DEFAULT 1, -- Strength of dependency
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(codebase_id, source_file, target_file, dependency_type, symbol_name)
);

-- Dead code detection results
CREATE TABLE dead_code_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    codebase_id UUID REFERENCES codebases(id) ON DELETE CASCADE,
    
    -- Dead code item
    file_path VARCHAR(1000) NOT NULL,
    symbol_name VARCHAR(255) NOT NULL,
    symbol_type VARCHAR(50) NOT NULL, -- function, class, variable, import
    start_line INTEGER,
    end_line INTEGER,
    
    -- Analysis details
    reason VARCHAR(100), -- unused, unreachable, deprecated
    confidence DECIMAL(3,2) DEFAULT 1.0, -- 0.0 to 1.0
    
    -- Context
    last_used_at TIMESTAMP WITH TIME ZONE,
    potential_usage JSONB DEFAULT '[]',
    
    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Security analysis results
CREATE TABLE security_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    codebase_id UUID REFERENCES codebases(id) ON DELETE CASCADE,
    
    -- Issue identification
    file_path VARCHAR(1000) NOT NULL,
    line_number INTEGER,
    issue_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL, -- low, medium, high, critical
    
    -- Issue details
    title VARCHAR(500) NOT NULL,
    description TEXT,
    recommendation TEXT,
    
    -- Code context
    code_snippet TEXT,
    
    -- Classification
    cwe_id VARCHAR(20), -- Common Weakness Enumeration ID
    owasp_category VARCHAR(100),
    
    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Performance analysis results
CREATE TABLE performance_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    codebase_id UUID REFERENCES codebases(id) ON DELETE CASCADE,
    
    -- Performance issue
    file_path VARCHAR(1000) NOT NULL,
    function_name VARCHAR(255),
    line_number INTEGER,
    issue_type VARCHAR(100) NOT NULL,
    
    -- Performance metrics
    estimated_impact VARCHAR(20), -- low, medium, high
    complexity_class VARCHAR(20), -- O(1), O(n), O(n²), etc.
    
    -- Details
    description TEXT,
    recommendation TEXT,
    code_snippet TEXT,
    
    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- API documentation analysis
CREATE TABLE api_documentation (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    codebase_id UUID REFERENCES codebases(id) ON DELETE CASCADE,
    
    -- API endpoint/function
    file_path VARCHAR(1000) NOT NULL,
    symbol_name VARCHAR(255) NOT NULL,
    symbol_type VARCHAR(50) NOT NULL, -- function, class, method
    
    -- Documentation
    docstring TEXT,
    parameters JSONB DEFAULT '[]',
    return_type VARCHAR(255),
    return_description TEXT,
    examples JSONB DEFAULT '[]',
    
    -- Quality metrics
    documentation_score DECIMAL(3,2), -- 0.0 to 1.0
    has_examples BOOLEAN DEFAULT FALSE,
    has_type_hints BOOLEAN DEFAULT FALSE,
    
    -- Generated documentation
    generated_docs TEXT,
    
    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Test coverage analysis
CREATE TABLE test_coverage_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    codebase_id UUID REFERENCES codebases(id) ON DELETE CASCADE,
    
    -- Coverage target
    file_path VARCHAR(1000) NOT NULL,
    function_name VARCHAR(255),
    line_number INTEGER,
    
    -- Coverage metrics
    is_covered BOOLEAN DEFAULT FALSE,
    hit_count INTEGER DEFAULT 0,
    branch_coverage DECIMAL(5,2),
    
    -- Test information
    test_files JSONB DEFAULT '[]',
    test_functions JSONB DEFAULT '[]',
    
    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_codebase_analysis_codebase_id ON codebase_analysis(codebase_id);
CREATE INDEX idx_codebase_analysis_type ON codebase_analysis(analysis_type);
CREATE INDEX idx_codebase_analysis_status ON codebase_analysis(status);

CREATE INDEX idx_file_analysis_codebase_id ON file_analysis(codebase_id);
CREATE INDEX idx_file_analysis_file_path ON file_analysis(file_path);
CREATE INDEX idx_file_analysis_language ON file_analysis(language);
CREATE INDEX idx_file_analysis_complexity ON file_analysis(cyclomatic_complexity);

CREATE INDEX idx_function_analysis_codebase_id ON function_analysis(codebase_id);
CREATE INDEX idx_function_analysis_file_id ON function_analysis(file_analysis_id);
CREATE INDEX idx_function_analysis_name ON function_analysis(function_name);
CREATE INDEX idx_function_analysis_complexity ON function_analysis(cyclomatic_complexity);

CREATE INDEX idx_class_analysis_codebase_id ON class_analysis(codebase_id);
CREATE INDEX idx_class_analysis_file_id ON class_analysis(file_analysis_id);
CREATE INDEX idx_class_analysis_name ON class_analysis(class_name);

CREATE INDEX idx_dependency_graph_codebase_id ON dependency_graph(codebase_id);
CREATE INDEX idx_dependency_graph_source ON dependency_graph(source_file);
CREATE INDEX idx_dependency_graph_target ON dependency_graph(target_file);
CREATE INDEX idx_dependency_graph_type ON dependency_graph(dependency_type);

CREATE INDEX idx_dead_code_codebase_id ON dead_code_analysis(codebase_id);
CREATE INDEX idx_dead_code_file_path ON dead_code_analysis(file_path);
CREATE INDEX idx_dead_code_symbol_type ON dead_code_analysis(symbol_type);

CREATE INDEX idx_security_analysis_codebase_id ON security_analysis(codebase_id);
CREATE INDEX idx_security_analysis_severity ON security_analysis(severity);
CREATE INDEX idx_security_analysis_type ON security_analysis(issue_type);

CREATE INDEX idx_performance_analysis_codebase_id ON performance_analysis(codebase_id);
CREATE INDEX idx_performance_analysis_impact ON performance_analysis(estimated_impact);

CREATE INDEX idx_api_documentation_codebase_id ON api_documentation(codebase_id);
CREATE INDEX idx_api_documentation_symbol ON api_documentation(symbol_name);

CREATE INDEX idx_test_coverage_codebase_id ON test_coverage_analysis(codebase_id);
CREATE INDEX idx_test_coverage_file_path ON test_coverage_analysis(file_path);

-- GIN indexes for JSONB columns
CREATE INDEX idx_codebase_analysis_results ON codebase_analysis USING GIN(results);
CREATE INDEX idx_codebase_analysis_metrics ON codebase_analysis USING GIN(metrics);
CREATE INDEX idx_file_analysis_functions ON file_analysis USING GIN(functions);
CREATE INDEX idx_file_analysis_classes ON file_analysis USING GIN(classes);
CREATE INDEX idx_function_analysis_calls ON function_analysis USING GIN(calls_functions);
CREATE INDEX idx_function_analysis_dependencies ON function_analysis USING GIN(dependencies);

-- Analysis functions

-- Main codebase analysis function
CREATE OR REPLACE FUNCTION analyze_codebase(
    p_codebase_id UUID,
    p_analysis_types analysis_type[] DEFAULT ARRAY['complexity', 'dependencies', 'dead_code']::analysis_type[]
) RETURNS JSONB AS $$
DECLARE
    analysis_result JSONB := '{}';
    analysis_type analysis_type;
    start_time TIMESTAMP WITH TIME ZONE;
    end_time TIMESTAMP WITH TIME ZONE;
BEGIN
    start_time := NOW();
    
    -- Loop through each analysis type
    FOREACH analysis_type IN ARRAY p_analysis_types
    LOOP
        -- Insert analysis record
        INSERT INTO codebase_analysis (codebase_id, analysis_type, status)
        VALUES (p_codebase_id, analysis_type, 'running')
        ON CONFLICT (codebase_id, analysis_type) 
        DO UPDATE SET status = 'running', started_at = NOW();
        
        -- Perform specific analysis based on type
        CASE analysis_type
            WHEN 'complexity' THEN
                PERFORM analyze_complexity(p_codebase_id);
            WHEN 'dependencies' THEN
                PERFORM analyze_dependencies(p_codebase_id);
            WHEN 'dead_code' THEN
                PERFORM analyze_dead_code(p_codebase_id);
            WHEN 'security' THEN
                PERFORM analyze_security(p_codebase_id);
            WHEN 'performance' THEN
                PERFORM analyze_performance(p_codebase_id);
            ELSE
                -- Generic analysis
                NULL;
        END CASE;
        
        -- Mark analysis as completed
        UPDATE codebase_analysis 
        SET status = 'completed', completed_at = NOW()
        WHERE codebase_id = p_codebase_id AND analysis_type = analysis_type;
    END LOOP;
    
    end_time := NOW();
    
    analysis_result := jsonb_build_object(
        'codebase_id', p_codebase_id,
        'analysis_types', p_analysis_types,
        'duration_ms', EXTRACT(EPOCH FROM (end_time - start_time)) * 1000,
        'completed_at', end_time
    );
    
    RETURN analysis_result;
END;
$$ LANGUAGE plpgsql;

-- Complexity analysis function
CREATE OR REPLACE FUNCTION analyze_complexity(p_codebase_id UUID)
RETURNS VOID AS $$
DECLARE
    file_record RECORD;
    complexity_metrics JSONB;
BEGIN
    -- This would integrate with Graph-Sitter analysis
    -- For now, we'll create a placeholder implementation
    
    FOR file_record IN 
        SELECT * FROM file_analysis WHERE codebase_id = p_codebase_id
    LOOP
        -- Calculate complexity metrics (placeholder)
        complexity_metrics := jsonb_build_object(
            'cyclomatic_complexity', file_record.cyclomatic_complexity,
            'cognitive_complexity', file_record.cognitive_complexity,
            'maintainability_index', file_record.maintainability_index
        );
        
        -- Update analysis results
        UPDATE codebase_analysis 
        SET results = results || jsonb_build_object(file_record.file_path, complexity_metrics)
        WHERE codebase_id = p_codebase_id AND analysis_type = 'complexity';
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Dependencies analysis function
CREATE OR REPLACE FUNCTION analyze_dependencies(p_codebase_id UUID)
RETURNS VOID AS $$
DECLARE
    dependency_count INTEGER;
    circular_deps INTEGER;
    results JSONB;
BEGIN
    -- Count total dependencies
    SELECT COUNT(*) INTO dependency_count
    FROM dependency_graph WHERE codebase_id = p_codebase_id;
    
    -- Count circular dependencies
    SELECT COUNT(*) INTO circular_deps
    FROM dependency_graph WHERE codebase_id = p_codebase_id AND is_circular = TRUE;
    
    results := jsonb_build_object(
        'total_dependencies', dependency_count,
        'circular_dependencies', circular_deps,
        'dependency_ratio', CASE WHEN dependency_count > 0 THEN circular_deps::DECIMAL / dependency_count ELSE 0 END
    );
    
    UPDATE codebase_analysis 
    SET results = results, metrics = results
    WHERE codebase_id = p_codebase_id AND analysis_type = 'dependencies';
END;
$$ LANGUAGE plpgsql;

-- Dead code analysis function
CREATE OR REPLACE FUNCTION analyze_dead_code(p_codebase_id UUID)
RETURNS VOID AS $$
DECLARE
    dead_code_count INTEGER;
    total_symbols INTEGER;
    results JSONB;
BEGIN
    -- Count dead code items
    SELECT COUNT(*) INTO dead_code_count
    FROM dead_code_analysis WHERE codebase_id = p_codebase_id;
    
    -- Count total symbols (approximate)
    SELECT SUM(function_count + class_count) INTO total_symbols
    FROM file_analysis WHERE codebase_id = p_codebase_id;
    
    results := jsonb_build_object(
        'dead_code_items', dead_code_count,
        'total_symbols', COALESCE(total_symbols, 0),
        'dead_code_ratio', CASE WHEN total_symbols > 0 THEN dead_code_count::DECIMAL / total_symbols ELSE 0 END
    );
    
    UPDATE codebase_analysis 
    SET results = results, metrics = results
    WHERE codebase_id = p_codebase_id AND analysis_type = 'dead_code';
END;
$$ LANGUAGE plpgsql;

-- Security analysis function
CREATE OR REPLACE FUNCTION analyze_security(p_codebase_id UUID)
RETURNS VOID AS $$
DECLARE
    security_issues INTEGER;
    critical_issues INTEGER;
    results JSONB;
BEGIN
    -- Count security issues by severity
    SELECT 
        COUNT(*) as total,
        COUNT(*) FILTER (WHERE severity = 'critical') as critical
    INTO security_issues, critical_issues
    FROM security_analysis WHERE codebase_id = p_codebase_id;
    
    results := jsonb_build_object(
        'total_issues', security_issues,
        'critical_issues', critical_issues,
        'security_score', CASE WHEN security_issues = 0 THEN 100 ELSE GREATEST(0, 100 - (critical_issues * 20 + security_issues * 5)) END
    );
    
    UPDATE codebase_analysis 
    SET results = results, metrics = results
    WHERE codebase_id = p_codebase_id AND analysis_type = 'security';
END;
$$ LANGUAGE plpgsql;

-- Performance analysis function
CREATE OR REPLACE FUNCTION analyze_performance(p_codebase_id UUID)
RETURNS VOID AS $$
DECLARE
    perf_issues INTEGER;
    high_impact_issues INTEGER;
    results JSONB;
BEGIN
    -- Count performance issues
    SELECT 
        COUNT(*) as total,
        COUNT(*) FILTER (WHERE estimated_impact = 'high') as high_impact
    INTO perf_issues, high_impact_issues
    FROM performance_analysis WHERE codebase_id = p_codebase_id;
    
    results := jsonb_build_object(
        'performance_issues', perf_issues,
        'high_impact_issues', high_impact_issues,
        'performance_score', CASE WHEN perf_issues = 0 THEN 100 ELSE GREATEST(0, 100 - (high_impact_issues * 15 + perf_issues * 3)) END
    );
    
    UPDATE codebase_analysis 
    SET results = results, metrics = results
    WHERE codebase_id = p_codebase_id AND analysis_type = 'performance';
END;
$$ LANGUAGE plpgsql;

-- Get comprehensive analysis results
CREATE OR REPLACE FUNCTION list_analysis_results(
    p_codebase_id UUID,
    p_analysis_type analysis_type DEFAULT NULL
) RETURNS TABLE(
    analysis_type analysis_type,
    status VARCHAR,
    results JSONB,
    metrics JSONB,
    completed_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ca.analysis_type,
        ca.status,
        ca.results,
        ca.metrics,
        ca.completed_at
    FROM codebase_analysis ca
    WHERE ca.codebase_id = p_codebase_id
    AND (p_analysis_type IS NULL OR ca.analysis_type = p_analysis_type)
    ORDER BY ca.completed_at DESC;
END;
$$ LANGUAGE plpgsql;

-- Find unused functions (dead code detection)
CREATE OR REPLACE FUNCTION find_unused_functions(p_codebase_id UUID)
RETURNS TABLE(
    file_path VARCHAR,
    function_name VARCHAR,
    line_number INTEGER,
    confidence DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        dca.file_path,
        dca.symbol_name,
        dca.start_line,
        dca.confidence
    FROM dead_code_analysis dca
    WHERE dca.codebase_id = p_codebase_id
    AND dca.symbol_type = 'function'
    AND dca.reason = 'unused'
    ORDER BY dca.confidence DESC, dca.file_path;
END;
$$ LANGUAGE plpgsql;

-- Get function call hierarchy
CREATE OR REPLACE FUNCTION get_function_call_hierarchy(
    p_codebase_id UUID,
    p_function_name VARCHAR
) RETURNS TABLE(
    caller_file VARCHAR,
    caller_function VARCHAR,
    callee_file VARCHAR,
    callee_function VARCHAR,
    call_depth INTEGER
) AS $$
WITH RECURSIVE call_tree AS (
    -- Base case: direct calls to the target function
    SELECT 
        fa.file_path as caller_file,
        fa.function_name as caller_function,
        p_function_name as callee_function,
        '' as callee_file,
        1 as call_depth
    FROM function_analysis fa
    WHERE fa.codebase_id = p_codebase_id
    AND fa.calls_functions @> jsonb_build_array(p_function_name)
    
    UNION ALL
    
    -- Recursive case: functions that call the callers
    SELECT 
        fa.file_path,
        fa.function_name,
        ct.caller_function,
        ct.caller_file,
        ct.call_depth + 1
    FROM function_analysis fa
    JOIN call_tree ct ON fa.calls_functions @> jsonb_build_array(ct.caller_function)
    WHERE fa.codebase_id = p_codebase_id
    AND ct.call_depth < 10 -- Prevent infinite recursion
)
SELECT * FROM call_tree ORDER BY call_depth, caller_file, caller_function;
$$ LANGUAGE sql;

-- Sync active tracking changes for codebase
CREATE OR REPLACE FUNCTION sync_active_track_changes_codebase(
    p_codebase_id UUID,
    p_changes JSONB
) RETURNS JSONB AS $$
DECLARE
    result JSONB;
    change_record JSONB;
BEGIN
    result := '{"synced_changes": []}';
    
    -- Process each change in the changes array
    FOR change_record IN SELECT * FROM jsonb_array_elements(p_changes)
    LOOP
        -- Update file analysis if file was modified
        IF change_record->>'type' = 'file_modified' THEN
            UPDATE file_analysis 
            SET analyzed_at = NOW(),
                file_hash = change_record->>'new_hash'
            WHERE codebase_id = p_codebase_id 
            AND file_path = change_record->>'file_path';
        END IF;
        
        -- Add to result
        result := jsonb_set(
            result, 
            '{synced_changes}', 
            (result->'synced_changes') || jsonb_build_array(change_record)
        );
    END LOOP;
    
    -- Update codebase last analyzed timestamp
    UPDATE codebases SET updated_at = NOW() WHERE id = p_codebase_id;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

COMMENT ON TABLE codebase_analysis IS 'Main table storing comprehensive codebase analysis results';
COMMENT ON TABLE file_analysis IS 'Detailed analysis results for individual files';
COMMENT ON TABLE function_analysis IS 'Function-level analysis including complexity and usage metrics';
COMMENT ON TABLE class_analysis IS 'Class-level analysis including inheritance and structure metrics';
COMMENT ON TABLE dependency_graph IS 'Complete dependency relationships between files and symbols';
COMMENT ON TABLE dead_code_analysis IS 'Detection and analysis of unused code elements';
COMMENT ON TABLE security_analysis IS 'Security vulnerability detection and analysis';
COMMENT ON TABLE performance_analysis IS 'Performance issue detection and optimization suggestions';
COMMENT ON TABLE api_documentation IS 'API documentation analysis and generation';
COMMENT ON TABLE test_coverage_analysis IS 'Test coverage analysis and reporting';

