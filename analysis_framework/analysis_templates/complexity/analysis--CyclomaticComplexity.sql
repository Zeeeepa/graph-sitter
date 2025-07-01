-- Cyclomatic Complexity Analysis Template
-- Analyzes control flow complexity in functions and methods

WITH function_complexity AS (
    SELECT 
        s.id as symbol_id,
        s.file_id,
        s.name as function_name,
        s.qualified_name,
        s.start_line,
        s.end_line,
        s.complexity_score,
        f.file_path,
        f.language,
        r.id as repository_id,
        r.name as repository_name,
        -- Calculate complexity grade
        CASE 
            WHEN s.complexity_score <= 5 THEN 'A'
            WHEN s.complexity_score <= 10 THEN 'B'
            WHEN s.complexity_score <= 15 THEN 'C'
            WHEN s.complexity_score <= 25 THEN 'D'
            ELSE 'F'
        END as complexity_grade,
        -- Risk assessment
        CASE 
            WHEN s.complexity_score <= 5 THEN 'Low'
            WHEN s.complexity_score <= 10 THEN 'Medium'
            WHEN s.complexity_score <= 15 THEN 'High'
            ELSE 'Critical'
        END as risk_level
    FROM symbols s
    JOIN files f ON s.file_id = f.id
    JOIN repositories r ON f.repository_id = r.id
    WHERE s.symbol_type IN ('function', 'method')
    AND s.complexity_score IS NOT NULL
    AND r.id = $1 -- Repository ID parameter
),
complexity_stats AS (
    SELECT 
        repository_id,
        COUNT(*) as total_functions,
        AVG(complexity_score) as avg_complexity,
        STDDEV(complexity_score) as complexity_stddev,
        MIN(complexity_score) as min_complexity,
        MAX(complexity_score) as max_complexity,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY complexity_score) as median_complexity,
        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY complexity_score) as p95_complexity,
        COUNT(CASE WHEN complexity_score > 15 THEN 1 END) as high_complexity_functions,
        COUNT(CASE WHEN complexity_score > 25 THEN 1 END) as critical_complexity_functions
    FROM function_complexity
    GROUP BY repository_id
),
file_complexity_summary AS (
    SELECT 
        file_id,
        file_path,
        language,
        COUNT(*) as function_count,
        AVG(complexity_score) as avg_file_complexity,
        MAX(complexity_score) as max_file_complexity,
        SUM(CASE WHEN complexity_score > 15 THEN 1 ELSE 0 END) as problematic_functions
    FROM function_complexity
    GROUP BY file_id, file_path, language
),
complexity_hotspots AS (
    SELECT 
        fc.*,
        ROW_NUMBER() OVER (ORDER BY complexity_score DESC) as complexity_rank
    FROM function_complexity fc
    WHERE complexity_score > 10
),
recommendations AS (
    SELECT 
        repository_id,
        ARRAY_AGG(
            CASE 
                WHEN risk_level = 'Critical' THEN 
                    'Function "' || function_name || '" in ' || file_path || ' has critical complexity (' || complexity_score || '). Consider breaking into smaller functions.'
                WHEN risk_level = 'High' THEN 
                    'Function "' || function_name || '" in ' || file_path || ' has high complexity (' || complexity_score || '). Review for refactoring opportunities.'
            END
        ) FILTER (WHERE risk_level IN ('Critical', 'High')) as improvement_suggestions
    FROM function_complexity
    GROUP BY repository_id
)

-- Main analysis result
SELECT 
    'complexity' as analysis_type,
    'cyclomatic_complexity' as analysis_subtype,
    cs.repository_id,
    'cyclomatic_complexity_analyzer' as analyzer_name,
    '2.0.0' as analyzer_version,
    NOW() as analysis_date,
    
    -- Results JSON
    jsonb_build_object(
        'summary', jsonb_build_object(
            'total_functions', cs.total_functions,
            'average_complexity', ROUND(cs.avg_complexity, 2),
            'median_complexity', ROUND(cs.median_complexity, 2),
            'max_complexity', cs.max_complexity,
            'standard_deviation', ROUND(cs.complexity_stddev, 2),
            'high_complexity_functions', cs.high_complexity_functions,
            'critical_complexity_functions', cs.critical_complexity_functions,
            'complexity_distribution', jsonb_build_object(
                'grade_A', (SELECT COUNT(*) FROM function_complexity WHERE complexity_grade = 'A' AND repository_id = cs.repository_id),
                'grade_B', (SELECT COUNT(*) FROM function_complexity WHERE complexity_grade = 'B' AND repository_id = cs.repository_id),
                'grade_C', (SELECT COUNT(*) FROM function_complexity WHERE complexity_grade = 'C' AND repository_id = cs.repository_id),
                'grade_D', (SELECT COUNT(*) FROM function_complexity WHERE complexity_grade = 'D' AND repository_id = cs.repository_id),
                'grade_F', (SELECT COUNT(*) FROM function_complexity WHERE complexity_grade = 'F' AND repository_id = cs.repository_id)
            )
        ),
        'hotspots', (
            SELECT jsonb_agg(
                jsonb_build_object(
                    'function_name', function_name,
                    'file_path', file_path,
                    'complexity_score', complexity_score,
                    'risk_level', risk_level,
                    'line_range', jsonb_build_object('start', start_line, 'end', end_line)
                )
            )
            FROM complexity_hotspots 
            WHERE repository_id = cs.repository_id 
            AND complexity_rank <= 20
        ),
        'file_analysis', (
            SELECT jsonb_agg(
                jsonb_build_object(
                    'file_path', file_path,
                    'language', language,
                    'function_count', function_count,
                    'avg_complexity', ROUND(avg_file_complexity, 2),
                    'max_complexity', max_file_complexity,
                    'problematic_functions', problematic_functions
                )
            )
            FROM file_complexity_summary fcs
            WHERE fcs.file_id IN (
                SELECT DISTINCT file_id FROM function_complexity WHERE repository_id = cs.repository_id
            )
        ),
        'language_breakdown', (
            SELECT jsonb_object_agg(
                language,
                jsonb_build_object(
                    'function_count', COUNT(*),
                    'avg_complexity', ROUND(AVG(complexity_score), 2),
                    'max_complexity', MAX(complexity_score)
                )
            )
            FROM function_complexity
            WHERE repository_id = cs.repository_id
            GROUP BY language
        )
    ) as results,
    
    -- Metrics JSON
    jsonb_build_object(
        'average_complexity', ROUND(cs.avg_complexity, 2),
        'median_complexity', ROUND(cs.median_complexity, 2),
        'max_complexity', cs.max_complexity,
        'p95_complexity', ROUND(cs.p95_complexity, 2),
        'high_complexity_ratio', ROUND((cs.high_complexity_functions::decimal / cs.total_functions) * 100, 2),
        'critical_complexity_ratio', ROUND((cs.critical_complexity_functions::decimal / cs.total_functions) * 100, 2)
    ) as metrics,
    
    -- Overall score (0-100, higher is better)
    GREATEST(0, LEAST(100, 
        100 - (
            (cs.avg_complexity - 1) * 10 + -- Penalty for high average complexity
            (cs.high_complexity_functions::decimal / cs.total_functions) * 50 + -- Penalty for high complexity functions
            (cs.critical_complexity_functions::decimal / cs.total_functions) * 100 -- Heavy penalty for critical complexity
        )
    )) as score,
    
    -- Grade based on score
    CASE 
        WHEN (100 - ((cs.avg_complexity - 1) * 10 + (cs.high_complexity_functions::decimal / cs.total_functions) * 50 + (cs.critical_complexity_functions::decimal / cs.total_functions) * 100)) >= 90 THEN 'A'
        WHEN (100 - ((cs.avg_complexity - 1) * 10 + (cs.high_complexity_functions::decimal / cs.total_functions) * 50 + (cs.critical_complexity_functions::decimal / cs.total_functions) * 100)) >= 80 THEN 'B'
        WHEN (100 - ((cs.avg_complexity - 1) * 10 + (cs.high_complexity_functions::decimal / cs.total_functions) * 50 + (cs.critical_complexity_functions::decimal / cs.total_functions) * 100)) >= 70 THEN 'C'
        WHEN (100 - ((cs.avg_complexity - 1) * 10 + (cs.high_complexity_functions::decimal / cs.total_functions) * 50 + (cs.critical_complexity_functions::decimal / cs.total_functions) * 100)) >= 60 THEN 'D'
        ELSE 'F'
    END as grade,
    
    95.0 as confidence_level, -- High confidence for cyclomatic complexity
    
    -- Recommendations
    COALESCE(r.improvement_suggestions, ARRAY[]::text[]) as recommendations,
    
    -- Warnings
    ARRAY[
        CASE WHEN cs.critical_complexity_functions > 0 THEN 
            'Found ' || cs.critical_complexity_functions || ' functions with critical complexity (>25). Immediate refactoring recommended.'
        END,
        CASE WHEN cs.avg_complexity > 10 THEN 
            'Average complexity (' || ROUND(cs.avg_complexity, 1) || ') exceeds recommended threshold of 10.'
        END,
        CASE WHEN (cs.high_complexity_functions::decimal / cs.total_functions) > 0.2 THEN 
            'More than 20% of functions have high complexity. Consider architectural review.'
        END
    ]::text[] as warnings,
    
    -- Metadata
    jsonb_build_object(
        'analysis_parameters', jsonb_build_object(
            'complexity_thresholds', jsonb_build_object(
                'low', 5,
                'medium', 10,
                'high', 15,
                'critical', 25
            ),
            'grading_scale', jsonb_build_object(
                'A', '1-5',
                'B', '6-10', 
                'C', '11-15',
                'D', '16-25',
                'F', '>25'
            )
        ),
        'methodology', 'Cyclomatic complexity measures the number of linearly independent paths through a program. Lower values indicate simpler, more maintainable code.',
        'tools_used', ARRAY['graph_sitter_complexity_analyzer'],
        'standards_reference', ARRAY['ISO/IEC 25010', 'IEEE 1061']
    ) as metadata

FROM complexity_stats cs
LEFT JOIN recommendations r ON cs.repository_id = r.repository_id
WHERE cs.repository_id = $1;

