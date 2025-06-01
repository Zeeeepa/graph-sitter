-- Maintainability Index Analysis Template
-- Calculates maintainability index based on Halstead metrics, cyclomatic complexity, and lines of code

WITH function_metrics AS (
    SELECT 
        s.id as symbol_id,
        s.file_id,
        s.name as function_name,
        s.qualified_name,
        s.complexity_score,
        s.start_line,
        s.end_line,
        (s.end_line - s.start_line + 1) as function_loc,
        f.file_path,
        f.language,
        f.line_count as file_loc,
        r.id as repository_id,
        r.name as repository_name,
        
        -- Extract Halstead metrics from metadata if available
        COALESCE((s.metadata->>'halstead_volume')::decimal, 0) as halstead_volume,
        COALESCE((s.metadata->>'halstead_difficulty')::decimal, 0) as halstead_difficulty,
        COALESCE((s.metadata->>'halstead_effort')::decimal, 0) as halstead_effort,
        
        -- Calculate maintainability index using Microsoft's formula
        -- MI = 171 - 5.2 * ln(HV) - 0.23 * CC - 16.2 * ln(LOC)
        -- Where HV = Halstead Volume, CC = Cyclomatic Complexity, LOC = Lines of Code
        CASE 
            WHEN s.complexity_score > 0 AND (s.end_line - s.start_line + 1) > 0 THEN
                GREATEST(0, LEAST(100,
                    171 - 
                    5.2 * LN(GREATEST(1, COALESCE((s.metadata->>'halstead_volume')::decimal, (s.end_line - s.start_line + 1) * 2))) - 
                    0.23 * s.complexity_score - 
                    16.2 * LN(s.end_line - s.start_line + 1)
                ))
            ELSE NULL
        END as maintainability_index
        
    FROM symbols s
    JOIN files f ON s.file_id = f.id
    JOIN repositories r ON f.repository_id = r.id
    WHERE s.symbol_type IN ('function', 'method')
    AND s.complexity_score IS NOT NULL
    AND r.id = $1 -- Repository ID parameter
),
file_maintainability AS (
    SELECT 
        file_id,
        file_path,
        language,
        file_loc,
        COUNT(*) as function_count,
        AVG(maintainability_index) as avg_maintainability,
        MIN(maintainability_index) as min_maintainability,
        MAX(maintainability_index) as max_maintainability,
        STDDEV(maintainability_index) as maintainability_stddev,
        COUNT(CASE WHEN maintainability_index < 20 THEN 1 END) as low_maintainability_functions,
        COUNT(CASE WHEN maintainability_index BETWEEN 20 AND 40 THEN 1 END) as moderate_maintainability_functions,
        COUNT(CASE WHEN maintainability_index > 40 THEN 1 END) as high_maintainability_functions
    FROM function_metrics
    WHERE maintainability_index IS NOT NULL
    GROUP BY file_id, file_path, language, file_loc
),
repository_maintainability AS (
    SELECT 
        repository_id,
        COUNT(*) as total_functions,
        AVG(maintainability_index) as avg_maintainability,
        STDDEV(maintainability_index) as maintainability_stddev,
        MIN(maintainability_index) as min_maintainability,
        MAX(maintainability_index) as max_maintainability,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY maintainability_index) as q1_maintainability,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY maintainability_index) as median_maintainability,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY maintainability_index) as q3_maintainability,
        COUNT(CASE WHEN maintainability_index < 20 THEN 1 END) as low_maintainability_count,
        COUNT(CASE WHEN maintainability_index BETWEEN 20 AND 40 THEN 1 END) as moderate_maintainability_count,
        COUNT(CASE WHEN maintainability_index > 40 THEN 1 END) as high_maintainability_count
    FROM function_metrics
    WHERE maintainability_index IS NOT NULL
    GROUP BY repository_id
),
maintainability_issues AS (
    SELECT 
        fm.*,
        CASE 
            WHEN maintainability_index < 10 THEN 'Critical'
            WHEN maintainability_index < 20 THEN 'Poor'
            WHEN maintainability_index < 40 THEN 'Moderate'
            WHEN maintainability_index < 60 THEN 'Good'
            ELSE 'Excellent'
        END as maintainability_rating,
        ROW_NUMBER() OVER (ORDER BY maintainability_index ASC) as issue_rank
    FROM function_metrics fm
    WHERE maintainability_index < 40 -- Focus on functions needing attention
),
language_maintainability AS (
    SELECT 
        repository_id,
        language,
        COUNT(*) as function_count,
        AVG(maintainability_index) as avg_maintainability,
        COUNT(CASE WHEN maintainability_index < 20 THEN 1 END) as problematic_functions
    FROM function_metrics
    WHERE maintainability_index IS NOT NULL
    GROUP BY repository_id, language
),
recommendations AS (
    SELECT 
        repository_id,
        ARRAY_AGG(
            CASE 
                WHEN maintainability_rating = 'Critical' THEN 
                    'Function "' || function_name || '" in ' || file_path || ' has critical maintainability (MI: ' || ROUND(maintainability_index, 1) || '). Immediate refactoring required.'
                WHEN maintainability_rating = 'Poor' THEN 
                    'Function "' || function_name || '" in ' || file_path || ' has poor maintainability (MI: ' || ROUND(maintainability_index, 1) || '). Consider simplification.'
            END
        ) FILTER (WHERE maintainability_rating IN ('Critical', 'Poor')) as improvement_suggestions
    FROM maintainability_issues
    WHERE issue_rank <= 20 -- Top 20 issues
    GROUP BY repository_id
)

-- Main analysis result
SELECT 
    'quality' as analysis_type,
    'maintainability_index' as analysis_subtype,
    rm.repository_id,
    'maintainability_index_analyzer' as analyzer_name,
    '2.0.0' as analyzer_version,
    NOW() as analysis_date,
    
    -- Results JSON
    jsonb_build_object(
        'summary', jsonb_build_object(
            'total_functions', rm.total_functions,
            'average_maintainability', ROUND(rm.avg_maintainability, 2),
            'median_maintainability', ROUND(rm.median_maintainability, 2),
            'min_maintainability', ROUND(rm.min_maintainability, 2),
            'max_maintainability', ROUND(rm.max_maintainability, 2),
            'standard_deviation', ROUND(rm.maintainability_stddev, 2),
            'quartiles', jsonb_build_object(
                'q1', ROUND(rm.q1_maintainability, 2),
                'q2', ROUND(rm.median_maintainability, 2),
                'q3', ROUND(rm.q3_maintainability, 2)
            ),
            'distribution', jsonb_build_object(
                'excellent', (SELECT COUNT(*) FROM function_metrics WHERE maintainability_index >= 60 AND repository_id = rm.repository_id),
                'good', (SELECT COUNT(*) FROM function_metrics WHERE maintainability_index >= 40 AND maintainability_index < 60 AND repository_id = rm.repository_id),
                'moderate', rm.moderate_maintainability_count,
                'poor', (SELECT COUNT(*) FROM function_metrics WHERE maintainability_index >= 10 AND maintainability_index < 20 AND repository_id = rm.repository_id),
                'critical', (SELECT COUNT(*) FROM function_metrics WHERE maintainability_index < 10 AND repository_id = rm.repository_id)
            )
        ),
        'problematic_functions', (
            SELECT jsonb_agg(
                jsonb_build_object(
                    'function_name', function_name,
                    'file_path', file_path,
                    'maintainability_index', ROUND(maintainability_index, 2),
                    'maintainability_rating', maintainability_rating,
                    'complexity_score', complexity_score,
                    'function_loc', function_loc,
                    'halstead_volume', ROUND(halstead_volume, 2)
                )
            )
            FROM maintainability_issues 
            WHERE repository_id = rm.repository_id 
            AND issue_rank <= 20
        ),
        'file_analysis', (
            SELECT jsonb_agg(
                jsonb_build_object(
                    'file_path', file_path,
                    'language', language,
                    'function_count', function_count,
                    'avg_maintainability', ROUND(avg_maintainability, 2),
                    'min_maintainability', ROUND(min_maintainability, 2),
                    'problematic_functions', low_maintainability_functions
                )
            )
            FROM file_maintainability fm
            WHERE fm.file_id IN (
                SELECT DISTINCT file_id FROM function_metrics WHERE repository_id = rm.repository_id
            )
            ORDER BY avg_maintainability ASC
        ),
        'language_breakdown', (
            SELECT jsonb_object_agg(
                language,
                jsonb_build_object(
                    'function_count', function_count,
                    'avg_maintainability', ROUND(avg_maintainability, 2),
                    'problematic_functions', problematic_functions,
                    'problematic_ratio', ROUND((problematic_functions::decimal / function_count) * 100, 2)
                )
            )
            FROM language_maintainability
            WHERE repository_id = rm.repository_id
        )
    ) as results,
    
    -- Metrics JSON
    jsonb_build_object(
        'average_maintainability', ROUND(rm.avg_maintainability, 2),
        'median_maintainability', ROUND(rm.median_maintainability, 2),
        'low_maintainability_ratio', ROUND((rm.low_maintainability_count::decimal / rm.total_functions) * 100, 2),
        'high_maintainability_ratio', ROUND((rm.high_maintainability_count::decimal / rm.total_functions) * 100, 2),
        'maintainability_variance', ROUND(rm.maintainability_stddev, 2)
    ) as metrics,
    
    -- Overall score (0-100, based on average maintainability with penalties)
    GREATEST(0, LEAST(100, 
        rm.avg_maintainability - 
        (rm.low_maintainability_count::decimal / rm.total_functions) * 30 -- Penalty for low maintainability functions
    )) as score,
    
    -- Grade based on average maintainability
    CASE 
        WHEN rm.avg_maintainability >= 60 THEN 'A'
        WHEN rm.avg_maintainability >= 40 THEN 'B'
        WHEN rm.avg_maintainability >= 20 THEN 'C'
        WHEN rm.avg_maintainability >= 10 THEN 'D'
        ELSE 'F'
    END as grade,
    
    90.0 as confidence_level, -- High confidence for maintainability index
    
    -- Recommendations
    COALESCE(r.improvement_suggestions, ARRAY[]::text[]) as recommendations,
    
    -- Warnings
    ARRAY[
        CASE WHEN rm.low_maintainability_count > 0 THEN 
            'Found ' || rm.low_maintainability_count || ' functions with low maintainability (MI < 20). Refactoring recommended.'
        END,
        CASE WHEN rm.avg_maintainability < 30 THEN 
            'Average maintainability (' || ROUND(rm.avg_maintainability, 1) || ') is below recommended threshold of 30.'
        END,
        CASE WHEN (rm.low_maintainability_count::decimal / rm.total_functions) > 0.25 THEN 
            'More than 25% of functions have low maintainability. Consider systematic refactoring.'
        END
    ]::text[] as warnings,
    
    -- Metadata
    jsonb_build_object(
        'analysis_parameters', jsonb_build_object(
            'maintainability_thresholds', jsonb_build_object(
                'excellent', '60+',
                'good', '40-59',
                'moderate', '20-39',
                'poor', '10-19',
                'critical', '<10'
            ),
            'formula', 'MI = 171 - 5.2 * ln(HV) - 0.23 * CC - 16.2 * ln(LOC)',
            'components', jsonb_build_object(
                'HV', 'Halstead Volume',
                'CC', 'Cyclomatic Complexity', 
                'LOC', 'Lines of Code'
            )
        ),
        'methodology', 'Maintainability Index combines Halstead metrics, cyclomatic complexity, and lines of code to assess how maintainable code is. Higher values indicate more maintainable code.',
        'tools_used', ARRAY['graph_sitter_maintainability_analyzer'],
        'standards_reference', ARRAY['IEEE 1061', 'ISO/IEC 25010', 'Microsoft Maintainability Index']
    ) as metadata

FROM repository_maintainability rm
LEFT JOIN recommendations r ON rm.repository_id = r.repository_id
WHERE rm.repository_id = $1;

