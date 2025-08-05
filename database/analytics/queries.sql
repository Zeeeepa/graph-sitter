-- =====================================================
-- ADVANCED ANALYTICS QUERY LIBRARY
-- Comprehensive SQL queries for codebase analysis
-- =====================================================

-- =====================================================
-- COMPLEXITY ANALYSIS QUERIES
-- =====================================================

-- Query 1: Cyclomatic Complexity Analysis
-- Identifies files with high cyclomatic complexity
SELECT 
    f.file_path,
    f.language,
    cm.cyclomatic_complexity,
    cm.cognitive_complexity,
    cm.lines_of_code,
    cm.maintainability_index,
    CASE 
        WHEN cm.cyclomatic_complexity <= 5 THEN 'Simple'
        WHEN cm.cyclomatic_complexity <= 10 THEN 'Moderate'
        WHEN cm.cyclomatic_complexity <= 20 THEN 'Complex'
        ELSE 'Very Complex'
    END as complexity_category,
    RANK() OVER (PARTITION BY f.language ORDER BY cm.cyclomatic_complexity DESC) as complexity_rank
FROM files f
JOIN code_metrics cm ON f.id = cm.file_id
WHERE cm.cyclomatic_complexity > 0
ORDER BY cm.cyclomatic_complexity DESC;

-- Query 2: Halstead Volume Metrics
-- Analyzes code complexity using Halstead metrics
SELECT 
    f.file_path,
    f.language,
    cm.halstead_vocabulary,
    cm.halstead_length,
    cm.halstead_volume,
    cm.halstead_difficulty,
    cm.halstead_effort,
    cm.halstead_time,
    cm.halstead_bugs,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY cm.halstead_volume) OVER (PARTITION BY f.language) as median_volume,
    CASE 
        WHEN cm.halstead_volume > PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY cm.halstead_volume) OVER (PARTITION BY f.language) 
        THEN 'High Complexity'
        WHEN cm.halstead_volume > PERCENTILE_CONT(0.7) WITHIN GROUP (ORDER BY cm.halstead_volume) OVER (PARTITION BY f.language)
        THEN 'Medium Complexity'
        ELSE 'Low Complexity'
    END as halstead_category
FROM files f
JOIN code_metrics cm ON f.id = cm.file_id
WHERE cm.halstead_volume > 0
ORDER BY cm.halstead_volume DESC;

-- Query 3: Maintainability Index Scoring
-- Calculates and categorizes maintainability scores
WITH maintainability_stats AS (
    SELECT 
        f.language,
        AVG(cm.maintainability_index) as avg_maintainability,
        STDDEV(cm.maintainability_index) as stddev_maintainability,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY cm.maintainability_index) as q1,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY cm.maintainability_index) as q3
    FROM files f
    JOIN code_metrics cm ON f.id = cm.file_id
    GROUP BY f.language
)
SELECT 
    f.file_path,
    f.language,
    cm.maintainability_index,
    ms.avg_maintainability,
    (cm.maintainability_index - ms.avg_maintainability) / NULLIF(ms.stddev_maintainability, 0) as z_score,
    CASE 
        WHEN cm.maintainability_index >= 85 THEN 'Excellent'
        WHEN cm.maintainability_index >= 70 THEN 'Good'
        WHEN cm.maintainability_index >= 50 THEN 'Fair'
        WHEN cm.maintainability_index >= 25 THEN 'Poor'
        ELSE 'Critical'
    END as maintainability_category,
    CASE 
        WHEN cm.maintainability_index < ms.q1 THEN 'Bottom Quartile'
        WHEN cm.maintainability_index > ms.q3 THEN 'Top Quartile'
        ELSE 'Middle Range'
    END as quartile_position
FROM files f
JOIN code_metrics cm ON f.id = cm.file_id
JOIN maintainability_stats ms ON f.language = ms.language
ORDER BY cm.maintainability_index ASC;

-- =====================================================
-- DEPENDENCY ANALYSIS QUERIES
-- =====================================================

-- Query 4: Circular Dependency Detection
-- Identifies circular dependencies in the codebase
WITH RECURSIVE dependency_paths AS (
    -- Base case: direct dependencies
    SELECT 
        d.source_file_id,
        d.target_file_id,
        ARRAY[d.source_file_id, d.target_file_id] as path,
        1 as depth,
        d.source_file_id as original_source
    FROM dependencies d
    WHERE d.dependency_type IN ('import', 'require', 'include')
    
    UNION ALL
    
    -- Recursive case: extend paths
    SELECT 
        dp.source_file_id,
        d.target_file_id,
        dp.path || d.target_file_id,
        dp.depth + 1,
        dp.original_source
    FROM dependency_paths dp
    JOIN dependencies d ON dp.target_file_id = d.source_file_id
    WHERE dp.depth < 10  -- Prevent infinite recursion
        AND NOT (d.target_file_id = ANY(dp.path))  -- Prevent cycles in path building
        AND d.dependency_type IN ('import', 'require', 'include')
)
SELECT DISTINCT
    f1.file_path as source_file,
    f2.file_path as target_file,
    dp.depth as cycle_length,
    array_to_string(
        ARRAY(
            SELECT f.file_path 
            FROM unnest(dp.path) as file_id
            JOIN files f ON f.id = file_id::UUID
        ), 
        ' -> '
    ) as dependency_chain
FROM dependency_paths dp
JOIN files f1 ON dp.original_source = f1.id
JOIN files f2 ON dp.target_file_id = f2.id
WHERE dp.target_file_id = dp.original_source  -- Circular dependency found
ORDER BY dp.depth, f1.file_path;

-- Query 5: Dependency Depth Analysis
-- Analyzes the depth of dependency chains
SELECT 
    f.file_path,
    f.language,
    COUNT(d_out.id) as outgoing_dependencies,
    COUNT(d_in.id) as incoming_dependencies,
    AVG(d_out.depth_level) as avg_outgoing_depth,
    MAX(d_out.depth_level) as max_outgoing_depth,
    COUNT(d_out.id) + COUNT(d_in.id) as total_coupling,
    CASE 
        WHEN COUNT(d_out.id) > 20 THEN 'High Efferent Coupling'
        WHEN COUNT(d_in.id) > 20 THEN 'High Afferent Coupling'
        WHEN COUNT(d_out.id) + COUNT(d_in.id) > 30 THEN 'High Total Coupling'
        ELSE 'Normal Coupling'
    END as coupling_assessment
FROM files f
LEFT JOIN dependencies d_out ON f.id = d_out.source_file_id
LEFT JOIN dependencies d_in ON f.id = d_in.target_file_id
GROUP BY f.id, f.file_path, f.language
ORDER BY total_coupling DESC;

-- Query 6: Import Relationship Mapping
-- Maps import relationships and identifies heavily used modules
SELECT 
    target_f.file_path as imported_module,
    target_f.language,
    COUNT(DISTINCT d.source_file_id) as importing_files_count,
    COUNT(d.id) as total_import_statements,
    ARRAY_AGG(DISTINCT source_f.file_path ORDER BY source_f.file_path) as importing_files,
    AVG(cm.maintainability_index) as avg_maintainability_of_importers,
    CASE 
        WHEN COUNT(DISTINCT d.source_file_id) > 50 THEN 'Core Module'
        WHEN COUNT(DISTINCT d.source_file_id) > 20 THEN 'Widely Used'
        WHEN COUNT(DISTINCT d.source_file_id) > 5 THEN 'Moderately Used'
        ELSE 'Rarely Used'
    END as usage_category
FROM dependencies d
JOIN files source_f ON d.source_file_id = source_f.id
JOIN files target_f ON d.target_file_id = target_f.id
LEFT JOIN code_metrics cm ON source_f.id = cm.file_id
WHERE d.dependency_type IN ('import', 'require', 'include')
GROUP BY target_f.id, target_f.file_path, target_f.language
HAVING COUNT(DISTINCT d.source_file_id) > 1
ORDER BY importing_files_count DESC;

-- =====================================================
-- DEAD CODE DETECTION QUERIES
-- =====================================================

-- Query 7: Unused Function Detection
-- Identifies functions that are never called
SELECT 
    s.name as function_name,
    s.symbol_type,
    f.file_path,
    s.complexity_score,
    s.start_line,
    s.end_line,
    s.is_exported,
    s.visibility,
    CASE 
        WHEN s.is_exported AND s.visibility = 'public' THEN 'Potentially Used Externally'
        WHEN s.symbol_type = 'method' AND s.name LIKE 'test_%' THEN 'Test Method'
        WHEN s.name LIKE '__%' THEN 'Magic Method'
        ELSE 'Likely Dead Code'
    END as dead_code_likelihood
FROM symbols s
JOIN files f ON s.file_id = f.id
LEFT JOIN function_calls fc ON s.id = fc.callee_symbol_id
WHERE s.symbol_type IN ('function', 'method')
    AND fc.id IS NULL  -- No calls found
    AND NOT s.is_deprecated
    AND s.name NOT LIKE 'main'
    AND s.name NOT LIKE '__init__'
ORDER BY s.complexity_score DESC, f.file_path;

-- Query 8: Unreachable Code Analysis
-- Identifies code segments that may be unreachable
SELECT 
    dc.id,
    f.file_path,
    dc.dead_code_type,
    dc.start_line,
    dc.end_line,
    dc.confidence_score,
    dc.reason,
    dc.potential_savings_loc,
    dc.removal_risk_level,
    s.name as associated_symbol,
    CASE 
        WHEN dc.confidence_score >= 0.9 THEN 'High Confidence'
        WHEN dc.confidence_score >= 0.7 THEN 'Medium Confidence'
        ELSE 'Low Confidence'
    END as confidence_level
FROM dead_code dc
JOIN files f ON dc.file_id = f.id
LEFT JOIN symbols s ON dc.symbol_id = s.id
WHERE NOT dc.is_false_positive
ORDER BY dc.confidence_score DESC, dc.potential_savings_loc DESC;

-- Query 9: Variable Usage Analysis
-- Analyzes variable usage patterns
SELECT 
    s.name as variable_name,
    s.symbol_type,
    f.file_path,
    s.start_line,
    COUNT(d.id) as reference_count,
    ARRAY_AGG(DISTINCT ref_f.file_path) as referenced_in_files,
    CASE 
        WHEN COUNT(d.id) = 0 THEN 'Unused Variable'
        WHEN COUNT(d.id) = 1 THEN 'Single Use'
        WHEN COUNT(d.id) <= 5 THEN 'Limited Use'
        ELSE 'Frequently Used'
    END as usage_pattern
FROM symbols s
JOIN files f ON s.file_id = f.id
LEFT JOIN dependencies d ON s.id = d.source_symbol_id
LEFT JOIN files ref_f ON d.target_file_id = ref_f.id
WHERE s.symbol_type IN ('variable', 'constant', 'property')
GROUP BY s.id, s.name, s.symbol_type, f.file_path, s.start_line
ORDER BY reference_count ASC, f.file_path;

-- =====================================================
-- FUNCTION CALL FLOW ANALYSIS
-- =====================================================

-- Query 10: Function Call Hierarchy
-- Builds function call hierarchies and identifies call patterns
WITH RECURSIVE call_hierarchy AS (
    -- Base case: entry points (functions not called by others)
    SELECT 
        s.id as function_id,
        s.name as function_name,
        f.file_path,
        0 as call_depth,
        ARRAY[s.name] as call_path,
        s.complexity_score
    FROM symbols s
    JOIN files f ON s.file_id = f.id
    LEFT JOIN function_calls fc_in ON s.id = fc_in.callee_symbol_id
    WHERE s.symbol_type IN ('function', 'method')
        AND fc_in.id IS NULL  -- Not called by any other function
        AND s.name NOT LIKE 'test_%'  -- Exclude test functions
    
    UNION ALL
    
    -- Recursive case: follow call chains
    SELECT 
        callee.id as function_id,
        callee.name as function_name,
        callee_f.file_path,
        ch.call_depth + 1,
        ch.call_path || callee.name,
        callee.complexity_score
    FROM call_hierarchy ch
    JOIN function_calls fc ON ch.function_id = fc.caller_symbol_id
    JOIN symbols callee ON fc.callee_symbol_id = callee.id
    JOIN files callee_f ON callee.file_id = callee_f.id
    WHERE ch.call_depth < 10  -- Prevent infinite recursion
        AND NOT (callee.name = ANY(ch.call_path))  -- Prevent cycles
)
SELECT 
    function_name,
    file_path,
    call_depth,
    array_to_string(call_path, ' -> ') as call_chain,
    complexity_score,
    COUNT(*) OVER (PARTITION BY function_id) as total_call_paths
FROM call_hierarchy
ORDER BY call_depth, complexity_score DESC;

-- Query 11: Call Graph Centrality Analysis
-- Identifies central functions in the call graph
SELECT 
    s.name as function_name,
    f.file_path,
    s.symbol_type,
    COUNT(DISTINCT fc_in.caller_symbol_id) as incoming_calls,
    COUNT(DISTINCT fc_out.callee_symbol_id) as outgoing_calls,
    COUNT(DISTINCT fc_in.caller_symbol_id) + COUNT(DISTINCT fc_out.callee_symbol_id) as total_connections,
    s.complexity_score,
    CASE 
        WHEN COUNT(DISTINCT fc_in.caller_symbol_id) > 10 THEN 'Hub Function'
        WHEN COUNT(DISTINCT fc_out.callee_symbol_id) > 10 THEN 'Utility Function'
        WHEN COUNT(DISTINCT fc_in.caller_symbol_id) + COUNT(DISTINCT fc_out.callee_symbol_id) > 15 THEN 'Central Function'
        ELSE 'Peripheral Function'
    END as centrality_category
FROM symbols s
JOIN files f ON s.file_id = f.id
LEFT JOIN function_calls fc_in ON s.id = fc_in.callee_symbol_id
LEFT JOIN function_calls fc_out ON s.id = fc_out.caller_symbol_id
WHERE s.symbol_type IN ('function', 'method')
GROUP BY s.id, s.name, f.file_path, s.symbol_type, s.complexity_score
ORDER BY total_connections DESC;

-- Query 12: Recursive Function Detection
-- Identifies recursive functions and analyzes recursion patterns
SELECT 
    s.name as function_name,
    f.file_path,
    fc.call_count,
    fc.line_number,
    s.complexity_score,
    CASE 
        WHEN fc.call_count > 1 THEN 'Multiple Recursive Calls'
        ELSE 'Single Recursive Call'
    END as recursion_type,
    CASE 
        WHEN s.complexity_score > 20 THEN 'High Risk Recursion'
        WHEN s.complexity_score > 10 THEN 'Medium Risk Recursion'
        ELSE 'Low Risk Recursion'
    END as risk_assessment
FROM function_calls fc
JOIN symbols s ON fc.caller_symbol_id = s.id AND fc.callee_symbol_id = s.id
JOIN files f ON s.file_id = f.id
WHERE fc.is_recursive = TRUE
ORDER BY s.complexity_score DESC, fc.call_count DESC;

-- =====================================================
-- CODE QUALITY METRICS
-- =====================================================

-- Query 13: Lines of Code Analysis
-- Comprehensive LOC analysis with quality correlations
SELECT 
    f.language,
    COUNT(f.id) as file_count,
    SUM(cm.lines_of_code) as total_loc,
    SUM(cm.source_lines_of_code) as total_sloc,
    SUM(cm.logical_lines_of_code) as total_lloc,
    SUM(cm.comment_lines) as total_comment_lines,
    SUM(cm.blank_lines) as total_blank_lines,
    AVG(cm.lines_of_code) as avg_loc_per_file,
    AVG(cm.maintainability_index) as avg_maintainability,
    AVG(cm.cyclomatic_complexity) as avg_complexity,
    SUM(cm.comment_lines) * 100.0 / NULLIF(SUM(cm.source_lines_of_code), 0) as comment_ratio,
    CASE 
        WHEN SUM(cm.comment_lines) * 100.0 / NULLIF(SUM(cm.source_lines_of_code), 0) >= 20 THEN 'Well Documented'
        WHEN SUM(cm.comment_lines) * 100.0 / NULLIF(SUM(cm.source_lines_of_code), 0) >= 10 THEN 'Adequately Documented'
        ELSE 'Under Documented'
    END as documentation_level
FROM files f
JOIN code_metrics cm ON f.id = cm.file_id
WHERE f.language IS NOT NULL
GROUP BY f.language
ORDER BY total_loc DESC;

-- Query 14: Depth of Inheritance Analysis
-- Analyzes class inheritance hierarchies
SELECT 
    s.name as class_name,
    f.file_path,
    cm.depth_of_inheritance,
    cm.number_of_children,
    cm.coupling_between_objects,
    cm.lack_of_cohesion,
    CASE 
        WHEN cm.depth_of_inheritance > 6 THEN 'Deep Inheritance'
        WHEN cm.depth_of_inheritance > 3 THEN 'Moderate Inheritance'
        ELSE 'Shallow Inheritance'
    END as inheritance_category,
    CASE 
        WHEN cm.coupling_between_objects > 20 THEN 'High Coupling'
        WHEN cm.coupling_between_objects > 10 THEN 'Medium Coupling'
        ELSE 'Low Coupling'
    END as coupling_level
FROM symbols s
JOIN files f ON s.file_id = f.id
JOIN code_metrics cm ON f.id = cm.file_id
WHERE s.symbol_type = 'class'
    AND cm.depth_of_inheritance > 0
ORDER BY cm.depth_of_inheritance DESC, cm.coupling_between_objects DESC;

-- Query 15: Parameter Validation Analysis
-- Analyzes function parameters and identifies potential issues
SELECT 
    s.name as function_name,
    f.file_path,
    s.parameter_count,
    s.complexity_score,
    s.return_type,
    CASE 
        WHEN s.parameter_count > 7 THEN 'Too Many Parameters'
        WHEN s.parameter_count > 4 THEN 'Many Parameters'
        WHEN s.parameter_count = 0 AND s.symbol_type = 'function' THEN 'No Parameters'
        ELSE 'Normal Parameter Count'
    END as parameter_assessment,
    CASE 
        WHEN s.parameter_count > 5 AND s.complexity_score > 15 THEN 'High Risk Function'
        WHEN s.parameter_count > 7 OR s.complexity_score > 20 THEN 'Medium Risk Function'
        ELSE 'Low Risk Function'
    END as risk_level
FROM symbols s
JOIN files f ON s.file_id = f.id
WHERE s.symbol_type IN ('function', 'method')
    AND s.parameter_count IS NOT NULL
ORDER BY s.parameter_count DESC, s.complexity_score DESC;

-- =====================================================
-- IMPACT RADIUS ANALYSIS
-- =====================================================

-- Query 16: Change Impact Analysis
-- Analyzes the potential impact of changes to specific files or functions
WITH impact_calculation AS (
    SELECT 
        f.id as file_id,
        f.file_path,
        COUNT(DISTINCT d_in.source_file_id) as direct_dependents,
        COUNT(DISTINCT fc_in.caller_symbol_id) as function_callers,
        COUNT(DISTINCT s.id) as symbols_in_file,
        AVG(s.complexity_score) as avg_symbol_complexity
    FROM files f
    LEFT JOIN dependencies d_in ON f.id = d_in.target_file_id
    LEFT JOIN symbols s ON f.id = s.file_id
    LEFT JOIN function_calls fc_in ON s.id = fc_in.callee_symbol_id
    GROUP BY f.id, f.file_path
)
SELECT 
    ic.file_path,
    ic.direct_dependents,
    ic.function_callers,
    ic.symbols_in_file,
    ic.avg_symbol_complexity,
    ic.direct_dependents + ic.function_callers as total_impact_points,
    CASE 
        WHEN ic.direct_dependents + ic.function_callers > 50 THEN 'Critical Impact'
        WHEN ic.direct_dependents + ic.function_callers > 20 THEN 'High Impact'
        WHEN ic.direct_dependents + ic.function_callers > 5 THEN 'Medium Impact'
        ELSE 'Low Impact'
    END as impact_level,
    CASE 
        WHEN ic.avg_symbol_complexity > 15 AND ic.direct_dependents > 10 THEN 'High Risk Change'
        WHEN ic.avg_symbol_complexity > 10 OR ic.direct_dependents > 5 THEN 'Medium Risk Change'
        ELSE 'Low Risk Change'
    END as change_risk
FROM impact_calculation ic
ORDER BY total_impact_points DESC;

-- =====================================================
-- PERFORMANCE OPTIMIZATION QUERIES
-- =====================================================

-- Query 17: Code Hotspot Analysis
-- Identifies code hotspots based on complexity and usage
SELECT 
    f.file_path,
    s.name as symbol_name,
    s.symbol_type,
    s.complexity_score,
    COUNT(fc.id) as call_frequency,
    s.complexity_score * COUNT(fc.id) as hotspot_score,
    cm.lines_of_code,
    cm.maintainability_index,
    CASE 
        WHEN s.complexity_score * COUNT(fc.id) > 200 THEN 'Critical Hotspot'
        WHEN s.complexity_score * COUNT(fc.id) > 100 THEN 'Major Hotspot'
        WHEN s.complexity_score * COUNT(fc.id) > 50 THEN 'Minor Hotspot'
        ELSE 'Normal'
    END as hotspot_category
FROM symbols s
JOIN files f ON s.file_id = f.id
JOIN code_metrics cm ON f.id = cm.file_id
LEFT JOIN function_calls fc ON s.id = fc.callee_symbol_id
WHERE s.symbol_type IN ('function', 'method')
GROUP BY s.id, f.file_path, s.name, s.symbol_type, s.complexity_score, cm.lines_of_code, cm.maintainability_index
HAVING COUNT(fc.id) > 0
ORDER BY hotspot_score DESC;

-- Query 18: Repository Health Dashboard
-- Comprehensive repository health metrics
SELECT 
    r.name as repository_name,
    r.language as primary_language,
    COUNT(DISTINCT f.id) as total_files,
    COUNT(DISTINCT s.id) as total_symbols,
    SUM(cm.lines_of_code) as total_loc,
    AVG(cm.maintainability_index) as avg_maintainability,
    AVG(cm.cyclomatic_complexity) as avg_complexity,
    AVG(cm.test_coverage_percentage) as avg_test_coverage,
    COUNT(CASE WHEN dc.id IS NOT NULL THEN 1 END) as dead_code_issues,
    COUNT(CASE WHEN d.is_circular THEN 1 END) as circular_dependencies,
    CASE 
        WHEN AVG(cm.maintainability_index) >= 80 AND AVG(cm.test_coverage_percentage) >= 80 THEN 'Excellent'
        WHEN AVG(cm.maintainability_index) >= 60 AND AVG(cm.test_coverage_percentage) >= 60 THEN 'Good'
        WHEN AVG(cm.maintainability_index) >= 40 AND AVG(cm.test_coverage_percentage) >= 40 THEN 'Fair'
        ELSE 'Needs Improvement'
    END as overall_health
FROM repositories r
LEFT JOIN files f ON r.id = f.repository_id
LEFT JOIN symbols s ON f.id = s.file_id
LEFT JOIN code_metrics cm ON f.id = cm.file_id
LEFT JOIN dead_code dc ON f.id = dc.file_id
LEFT JOIN dependencies d ON f.id = d.source_file_id
GROUP BY r.id, r.name, r.language
ORDER BY avg_maintainability DESC;

-- =====================================================
-- TREND ANALYSIS QUERIES
-- =====================================================

-- Query 19: Code Quality Trends Over Time
-- Analyzes how code quality metrics change over time
SELECT 
    DATE_TRUNC('week', c.committed_at) as week,
    r.name as repository_name,
    AVG(cm.maintainability_index) as avg_maintainability,
    AVG(cm.cyclomatic_complexity) as avg_complexity,
    AVG(cm.test_coverage_percentage) as avg_test_coverage,
    SUM(cm.lines_of_code) as total_loc,
    COUNT(DISTINCT f.id) as files_analyzed,
    LAG(AVG(cm.maintainability_index)) OVER (PARTITION BY r.id ORDER BY DATE_TRUNC('week', c.committed_at)) as prev_maintainability,
    AVG(cm.maintainability_index) - LAG(AVG(cm.maintainability_index)) OVER (PARTITION BY r.id ORDER BY DATE_TRUNC('week', c.committed_at)) as maintainability_change
FROM commits c
JOIN repositories r ON c.repository_id = r.id
JOIN files f ON c.id = f.commit_id
JOIN code_metrics cm ON f.id = cm.file_id
WHERE c.committed_at >= CURRENT_DATE - INTERVAL '3 months'
GROUP BY DATE_TRUNC('week', c.committed_at), r.id, r.name
ORDER BY week DESC, repository_name;

-- Query 20: Technical Debt Accumulation
-- Tracks technical debt accumulation over time
SELECT 
    r.name as repository_name,
    SUM(cm.lines_of_code) as total_loc,
    AVG(cm.technical_debt_ratio) as avg_debt_ratio,
    SUM(cm.lines_of_code * cm.technical_debt_ratio) as estimated_debt_loc,
    COUNT(CASE WHEN cm.maintainability_index < 50 THEN 1 END) as problematic_files,
    COUNT(CASE WHEN cm.cyclomatic_complexity > 20 THEN 1 END) as complex_files,
    COUNT(CASE WHEN dc.id IS NOT NULL THEN 1 END) as dead_code_instances,
    (SUM(cm.lines_of_code * cm.technical_debt_ratio) / NULLIF(SUM(cm.lines_of_code), 0)) * 100 as debt_percentage,
    CASE 
        WHEN (SUM(cm.lines_of_code * cm.technical_debt_ratio) / NULLIF(SUM(cm.lines_of_code), 0)) * 100 > 30 THEN 'High Debt'
        WHEN (SUM(cm.lines_of_code * cm.technical_debt_ratio) / NULLIF(SUM(cm.lines_of_code), 0)) * 100 > 15 THEN 'Medium Debt'
        ELSE 'Low Debt'
    END as debt_level
FROM repositories r
JOIN files f ON r.id = f.repository_id
JOIN code_metrics cm ON f.id = cm.file_id
LEFT JOIN dead_code dc ON f.id = dc.file_id
GROUP BY r.id, r.name
ORDER BY debt_percentage DESC;

