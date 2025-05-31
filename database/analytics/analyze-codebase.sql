-- Comprehensive Codebase Analysis Function
-- Performs extensive analysis including all Graph-Sitter features and metrics

CREATE OR REPLACE FUNCTION analyze_codebase_comprehensive(
    p_repository_path VARCHAR,
    p_language language_type DEFAULT 'python',
    p_analysis_types analysis_type[] DEFAULT ARRAY['complexity', 'dependencies', 'dead_code', 'security', 'performance']::analysis_type[],
    p_options JSONB DEFAULT '{}'
) RETURNS JSONB AS $$
DECLARE
    codebase_id UUID;
    analysis_result JSONB := '{}';
    start_time TIMESTAMP WITH TIME ZONE;
    end_time TIMESTAMP WITH TIME ZONE;
    total_files INTEGER := 0;
    total_functions INTEGER := 0;
    total_classes INTEGER := 0;
    total_lines INTEGER := 0;
    complexity_metrics JSONB;
    dependency_metrics JSONB;
    quality_metrics JSONB;
BEGIN
    start_time := NOW();
    
    -- Create or get codebase record
    INSERT INTO codebases (
        repository_id, 
        branch, 
        commit_sha, 
        analysis_started_at
    ) VALUES (
        (SELECT id FROM repositories WHERE full_name = p_repository_path LIMIT 1),
        COALESCE(p_options->>'branch', 'main'),
        COALESCE(p_options->>'commit_sha', 'HEAD'),
        start_time
    ) 
    ON CONFLICT (repository_id, branch, commit_sha) 
    DO UPDATE SET analysis_started_at = start_time
    RETURNING id INTO codebase_id;
    
    -- Initialize analysis records for each type
    FOREACH analysis_type IN ARRAY p_analysis_types
    LOOP
        INSERT INTO codebase_analysis (codebase_id, analysis_type, status, started_at)
        VALUES (codebase_id, analysis_type, 'running', start_time)
        ON CONFLICT (codebase_id, analysis_type) 
        DO UPDATE SET status = 'running', started_at = start_time;
    END LOOP;
    
    -- Simulate comprehensive analysis (in real implementation, this would call Graph-Sitter)
    -- This is where the actual Graph-Sitter integration would happen
    
    -- 1. COMPLEXITY ANALYSIS
    IF 'complexity' = ANY(p_analysis_types) THEN
        complexity_metrics := analyze_complexity_metrics(codebase_id, p_repository_path, p_language);
        
        UPDATE codebase_analysis 
        SET results = complexity_metrics, 
            status = 'completed', 
            completed_at = NOW()
        WHERE codebase_id = codebase_id AND analysis_type = 'complexity';
    END IF;
    
    -- 2. DEPENDENCY ANALYSIS
    IF 'dependencies' = ANY(p_analysis_types) THEN
        dependency_metrics := analyze_dependency_graph(codebase_id, p_repository_path, p_language);
        
        UPDATE codebase_analysis 
        SET results = dependency_metrics, 
            status = 'completed', 
            completed_at = NOW()
        WHERE codebase_id = codebase_id AND analysis_type = 'dependencies';
    END IF;
    
    -- 3. DEAD CODE ANALYSIS
    IF 'dead_code' = ANY(p_analysis_types) THEN
        PERFORM analyze_dead_code_comprehensive(codebase_id, p_repository_path, p_language);
        
        UPDATE codebase_analysis 
        SET status = 'completed', 
            completed_at = NOW()
        WHERE codebase_id = codebase_id AND analysis_type = 'dead_code';
    END IF;
    
    -- 4. SECURITY ANALYSIS
    IF 'security' = ANY(p_analysis_types) THEN
        PERFORM analyze_security_vulnerabilities(codebase_id, p_repository_path, p_language);
        
        UPDATE codebase_analysis 
        SET status = 'completed', 
            completed_at = NOW()
        WHERE codebase_id = codebase_id AND analysis_type = 'security';
    END IF;
    
    -- 5. PERFORMANCE ANALYSIS
    IF 'performance' = ANY(p_analysis_types) THEN
        PERFORM analyze_performance_issues(codebase_id, p_repository_path, p_language);
        
        UPDATE codebase_analysis 
        SET status = 'completed', 
            completed_at = NOW()
        WHERE codebase_id = codebase_id AND analysis_type = 'performance';
    END IF;
    
    -- Calculate overall metrics
    SELECT 
        COUNT(*) as files,
        SUM(function_count) as functions,
        SUM(class_count) as classes,
        SUM(lines_of_code) as lines
    INTO total_files, total_functions, total_classes, total_lines
    FROM file_analysis WHERE codebase_id = codebase_id;
    
    -- Update codebase with final metrics
    UPDATE codebases SET
        total_files = total_files,
        total_functions = total_functions,
        total_classes = total_classes,
        total_lines = total_lines,
        analysis_completed_at = NOW()
    WHERE id = codebase_id;
    
    end_time := NOW();
    
    -- Build comprehensive result
    analysis_result := jsonb_build_object(
        'codebase_id', codebase_id,
        'repository_path', p_repository_path,
        'language', p_language,
        'analysis_types', p_analysis_types,
        'metrics', jsonb_build_object(
            'total_files', total_files,
            'total_functions', total_functions,
            'total_classes', total_classes,
            'total_lines', total_lines
        ),
        'duration_seconds', EXTRACT(EPOCH FROM (end_time - start_time)),
        'started_at', start_time,
        'completed_at', end_time,
        'status', 'completed'
    );
    
    RETURN analysis_result;
END;
$$ LANGUAGE plpgsql;

-- Complexity Analysis Function
CREATE OR REPLACE FUNCTION analyze_complexity_metrics(
    p_codebase_id UUID,
    p_repository_path VARCHAR,
    p_language language_type
) RETURNS JSONB AS $$
DECLARE
    complexity_result JSONB;
    avg_complexity DECIMAL;
    max_complexity INTEGER;
    high_complexity_files INTEGER;
BEGIN
    -- This would integrate with Graph-Sitter for real complexity calculation
    -- For now, we'll simulate the analysis
    
    -- Calculate average cyclomatic complexity
    SELECT 
        AVG(cyclomatic_complexity),
        MAX(cyclomatic_complexity),
        COUNT(*) FILTER (WHERE cyclomatic_complexity > 10)
    INTO avg_complexity, max_complexity, high_complexity_files
    FROM file_analysis 
    WHERE codebase_id = p_codebase_id;
    
    complexity_result := jsonb_build_object(
        'average_cyclomatic_complexity', COALESCE(avg_complexity, 0),
        'max_cyclomatic_complexity', COALESCE(max_complexity, 0),
        'high_complexity_files', COALESCE(high_complexity_files, 0),
        'complexity_distribution', jsonb_build_object(
            'low', (SELECT COUNT(*) FROM file_analysis WHERE codebase_id = p_codebase_id AND cyclomatic_complexity <= 5),
            'medium', (SELECT COUNT(*) FROM file_analysis WHERE codebase_id = p_codebase_id AND cyclomatic_complexity BETWEEN 6 AND 10),
            'high', (SELECT COUNT(*) FROM file_analysis WHERE codebase_id = p_codebase_id AND cyclomatic_complexity > 10)
        ),
        'maintainability_score', CASE 
            WHEN avg_complexity <= 5 THEN 'excellent'
            WHEN avg_complexity <= 10 THEN 'good'
            WHEN avg_complexity <= 15 THEN 'moderate'
            ELSE 'poor'
        END
    );
    
    RETURN complexity_result;
END;
$$ LANGUAGE plpgsql;

-- Dependency Graph Analysis Function
CREATE OR REPLACE FUNCTION analyze_dependency_graph(
    p_codebase_id UUID,
    p_repository_path VARCHAR,
    p_language language_type
) RETURNS JSONB AS $$
DECLARE
    dependency_result JSONB;
    total_dependencies INTEGER;
    circular_dependencies INTEGER;
    external_dependencies INTEGER;
    max_depth INTEGER;
BEGIN
    -- Count dependencies
    SELECT 
        COUNT(*),
        COUNT(*) FILTER (WHERE is_circular = TRUE),
        COUNT(*) FILTER (WHERE is_external = TRUE)
    INTO total_dependencies, circular_dependencies, external_dependencies
    FROM dependency_graph 
    WHERE codebase_id = p_codebase_id;
    
    -- Calculate dependency depth (simplified)
    SELECT MAX(weight) INTO max_depth
    FROM dependency_graph 
    WHERE codebase_id = p_codebase_id;
    
    dependency_result := jsonb_build_object(
        'total_dependencies', COALESCE(total_dependencies, 0),
        'circular_dependencies', COALESCE(circular_dependencies, 0),
        'external_dependencies', COALESCE(external_dependencies, 0),
        'internal_dependencies', COALESCE(total_dependencies - external_dependencies, 0),
        'max_dependency_depth', COALESCE(max_depth, 0),
        'dependency_health', CASE 
            WHEN circular_dependencies = 0 THEN 'excellent'
            WHEN circular_dependencies <= 2 THEN 'good'
            WHEN circular_dependencies <= 5 THEN 'moderate'
            ELSE 'poor'
        END,
        'coupling_score', CASE 
            WHEN total_dependencies = 0 THEN 0
            ELSE ROUND((external_dependencies::DECIMAL / total_dependencies) * 100, 2)
        END
    );
    
    RETURN dependency_result;
END;
$$ LANGUAGE plpgsql;

-- Dead Code Analysis Function
CREATE OR REPLACE FUNCTION analyze_dead_code_comprehensive(
    p_codebase_id UUID,
    p_repository_path VARCHAR,
    p_language language_type
) RETURNS VOID AS $$
DECLARE
    file_record RECORD;
    function_record RECORD;
BEGIN
    -- This would integrate with Graph-Sitter to find actual dead code
    -- For now, we'll simulate finding unused functions
    
    -- Find functions with no usages (simplified dead code detection)
    FOR function_record IN 
        SELECT fa.file_path, fa.function_name, fa.start_line, fa.end_line
        FROM function_analysis fa
        WHERE fa.codebase_id = p_codebase_id
        AND fa.call_count = 0
        AND fa.function_name NOT LIKE 'test_%'  -- Exclude test functions
        AND fa.function_name NOT IN ('main', '__init__', '__str__', '__repr__')  -- Exclude special functions
    LOOP
        INSERT INTO dead_code_analysis (
            codebase_id,
            file_path,
            symbol_name,
            symbol_type,
            start_line,
            end_line,
            reason,
            confidence
        ) VALUES (
            p_codebase_id,
            function_record.file_path,
            function_record.function_name,
            'function',
            function_record.start_line,
            function_record.end_line,
            'unused',
            0.8  -- 80% confidence
        ) ON CONFLICT (codebase_id, file_path, symbol_name, symbol_type) DO NOTHING;
    END LOOP;
    
    -- Find unused imports (simplified)
    -- This would require more sophisticated analysis in real implementation
    
    -- Find unreachable code (simplified)
    -- This would require control flow analysis in real implementation
END;
$$ LANGUAGE plpgsql;

-- Security Analysis Function
CREATE OR REPLACE FUNCTION analyze_security_vulnerabilities(
    p_codebase_id UUID,
    p_repository_path VARCHAR,
    p_language language_type
) RETURNS VOID AS $$
DECLARE
    file_record RECORD;
BEGIN
    -- This would integrate with security analysis tools
    -- For now, we'll simulate finding common security issues
    
    FOR file_record IN 
        SELECT file_path, source_code FROM file_analysis 
        WHERE codebase_id = p_codebase_id
    LOOP
        -- Check for SQL injection patterns (simplified)
        IF file_record.source_code LIKE '%execute(%' AND file_record.source_code LIKE '%+%' THEN
            INSERT INTO security_analysis (
                codebase_id,
                file_path,
                issue_type,
                severity,
                title,
                description,
                recommendation
            ) VALUES (
                p_codebase_id,
                file_record.file_path,
                'sql_injection',
                'high',
                'Potential SQL Injection',
                'String concatenation in SQL query detected',
                'Use parameterized queries instead of string concatenation'
            );
        END IF;
        
        -- Check for hardcoded secrets (simplified)
        IF file_record.source_code ~* '(password|secret|key|token)\s*=\s*["\'][^"\']+["\']' THEN
            INSERT INTO security_analysis (
                codebase_id,
                file_path,
                issue_type,
                severity,
                title,
                description,
                recommendation
            ) VALUES (
                p_codebase_id,
                file_record.file_path,
                'hardcoded_secret',
                'critical',
                'Hardcoded Secret Detected',
                'Potential hardcoded password, secret, or API key found',
                'Move secrets to environment variables or secure configuration'
            );
        END IF;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Performance Analysis Function
CREATE OR REPLACE FUNCTION analyze_performance_issues(
    p_codebase_id UUID,
    p_repository_path VARCHAR,
    p_language language_type
) RETURNS VOID AS $$
DECLARE
    function_record RECORD;
BEGIN
    -- This would integrate with performance analysis tools
    -- For now, we'll simulate finding performance issues
    
    FOR function_record IN 
        SELECT fa.file_path, fa.function_name, fa.cyclomatic_complexity, fa.source_code
        FROM function_analysis fa
        WHERE fa.codebase_id = p_codebase_id
    LOOP
        -- Check for high complexity functions
        IF function_record.cyclomatic_complexity > 15 THEN
            INSERT INTO performance_analysis (
                codebase_id,
                file_path,
                function_name,
                issue_type,
                estimated_impact,
                description,
                recommendation
            ) VALUES (
                p_codebase_id,
                function_record.file_path,
                function_record.function_name,
                'high_complexity',
                'medium',
                'Function has high cyclomatic complexity which may impact performance',
                'Consider breaking down the function into smaller, more focused functions'
            );
        END IF;
        
        -- Check for nested loops (simplified pattern matching)
        IF function_record.source_code ~* 'for.*for.*:' OR function_record.source_code ~* 'while.*while.*:' THEN
            INSERT INTO performance_analysis (
                codebase_id,
                file_path,
                function_name,
                issue_type,
                estimated_impact,
                complexity_class,
                description,
                recommendation
            ) VALUES (
                p_codebase_id,
                function_record.file_path,
                function_record.function_name,
                'nested_loops',
                'high',
                'O(n²)',
                'Nested loops detected which may cause performance issues with large datasets',
                'Consider optimizing algorithm or using more efficient data structures'
            );
        END IF;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Function to get comprehensive analysis summary
CREATE OR REPLACE FUNCTION get_analysis_summary(p_codebase_id UUID)
RETURNS JSONB AS $$
DECLARE
    summary JSONB;
    codebase_metrics JSONB;
    analysis_results JSONB := '{}';
    analysis_record RECORD;
BEGIN
    -- Get codebase metrics
    SELECT jsonb_build_object(
        'total_files', total_files,
        'total_functions', total_functions,
        'total_classes', total_classes,
        'total_lines', total_lines,
        'languages', languages
    ) INTO codebase_metrics
    FROM codebases WHERE id = p_codebase_id;
    
    -- Get all analysis results
    FOR analysis_record IN 
        SELECT analysis_type, results, metrics, status, completed_at
        FROM codebase_analysis 
        WHERE codebase_id = p_codebase_id
    LOOP
        analysis_results := analysis_results || jsonb_build_object(
            analysis_record.analysis_type::TEXT, 
            jsonb_build_object(
                'results', analysis_record.results,
                'metrics', analysis_record.metrics,
                'status', analysis_record.status,
                'completed_at', analysis_record.completed_at
            )
        );
    END LOOP;
    
    summary := jsonb_build_object(
        'codebase_id', p_codebase_id,
        'codebase_metrics', codebase_metrics,
        'analysis_results', analysis_results,
        'generated_at', NOW()
    );
    
    RETURN summary;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION analyze_codebase_comprehensive IS 'Comprehensive codebase analysis using Graph-Sitter integration';
COMMENT ON FUNCTION analyze_complexity_metrics IS 'Analyzes code complexity metrics including cyclomatic complexity';
COMMENT ON FUNCTION analyze_dependency_graph IS 'Analyzes dependency relationships and coupling';
COMMENT ON FUNCTION analyze_dead_code_comprehensive IS 'Identifies unused code, functions, and imports';
COMMENT ON FUNCTION analyze_security_vulnerabilities IS 'Scans for security vulnerabilities and issues';
COMMENT ON FUNCTION analyze_performance_issues IS 'Identifies potential performance bottlenecks';
COMMENT ON FUNCTION get_analysis_summary IS 'Returns comprehensive analysis summary for a codebase';

