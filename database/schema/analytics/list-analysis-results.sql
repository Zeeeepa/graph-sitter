-- List analysis results with filtering and summary statistics
-- Parameters: codebase_id (optional), analysis_type (optional), status (optional), 
--            limit (optional), offset (optional)

WITH filtered_analyses AS (
    SELECT 
        ar.id,
        ar.codebase_id,
        ar.analysis_type,
        ar.status,
        ar.started_at,
        ar.completed_at,
        ar.duration,
        ar.results,
        ar.error_message,
        c.name as codebase_name,
        c.language as codebase_language,
        -- Extract key metrics from results JSON
        (ar.results->>'files_analyzed')::INTEGER as files_analyzed,
        (ar.results->>'symbols_analyzed')::INTEGER as symbols_analyzed,
        (ar.results->>'metrics_created')::INTEGER as metrics_created,
        (ar.results->>'dependencies_mapped')::INTEGER as dependencies_mapped,
        (ar.results->>'dead_code_items')::INTEGER as dead_code_items,
        (ar.results->>'impact_relationships')::INTEGER as impact_relationships
    FROM analysis_runs ar
    LEFT JOIN codebases c ON ar.codebase_id = c.id
    WHERE ($1::UUID IS NULL OR ar.codebase_id = $1::UUID)
    AND ($2::TEXT IS NULL OR ar.analysis_type = $2::TEXT)
    AND ($3::TEXT IS NULL OR ar.status = $3::TEXT)
),
analysis_summary AS (
    SELECT 
        COUNT(*) as total_analyses,
        COUNT(*) FILTER (WHERE status = 'completed') as completed_analyses,
        COUNT(*) FILTER (WHERE status = 'running') as running_analyses,
        COUNT(*) FILTER (WHERE status = 'failed') as failed_analyses,
        COUNT(DISTINCT codebase_id) as codebases_analyzed,
        COUNT(DISTINCT analysis_type) as analysis_types,
        AVG(EXTRACT(EPOCH FROM duration)) FILTER (WHERE status = 'completed') as avg_duration_seconds,
        SUM(files_analyzed) FILTER (WHERE status = 'completed') as total_files_analyzed,
        SUM(symbols_analyzed) FILTER (WHERE status = 'completed') as total_symbols_analyzed,
        SUM(dead_code_items) FILTER (WHERE status = 'completed') as total_dead_code_items
    FROM filtered_analyses
),
recent_metrics AS (
    SELECT 
        fa.id as analysis_run_id,
        COUNT(cm.id) as total_metrics,
        COUNT(cm.id) FILTER (WHERE cm.threshold_status = 'critical') as critical_metrics,
        COUNT(cm.id) FILTER (WHERE cm.threshold_status = 'warning') as warning_metrics,
        COUNT(cm.id) FILTER (WHERE cm.threshold_status = 'good') as good_metrics,
        AVG(cm.metric_value) FILTER (WHERE cm.metric_type = 'cyclomatic_complexity') as avg_complexity,
        MAX(cm.metric_value) FILTER (WHERE cm.metric_type = 'cyclomatic_complexity') as max_complexity,
        AVG(cm.metric_value) FILTER (WHERE cm.metric_type = 'lines_of_code') as avg_lines_of_code
    FROM filtered_analyses fa
    LEFT JOIN code_metrics cm ON fa.id = cm.analysis_run_id
    GROUP BY fa.id
),
dependency_stats AS (
    SELECT 
        fa.id as analysis_run_id,
        COUNT(da.id) as total_dependencies,
        COUNT(da.id) FILTER (WHERE da.is_circular = TRUE) as circular_dependencies,
        COUNT(DISTINCT da.source_file_id) as files_with_dependencies,
        AVG(da.dependency_strength) as avg_dependency_strength,
        MAX(da.dependency_strength) as max_dependency_strength
    FROM filtered_analyses fa
    LEFT JOIN dependency_analysis da ON fa.id = da.analysis_run_id
    GROUP BY fa.id
),
dead_code_stats AS (
    SELECT 
        fa.id as analysis_run_id,
        COUNT(dca.id) as total_dead_code_items,
        COUNT(dca.id) FILTER (WHERE dca.confidence_score > 0.8) as high_confidence_dead_code,
        COUNT(dca.id) FILTER (WHERE dca.suggested_action = 'remove') as removable_items,
        COUNT(dca.id) FILTER (WHERE dca.dead_code_type = 'unused_function') as unused_functions,
        COUNT(dca.id) FILTER (WHERE dca.dead_code_type = 'unused_class') as unused_classes,
        COUNT(dca.id) FILTER (WHERE dca.dead_code_type = 'unused_variable') as unused_variables
    FROM filtered_analyses fa
    LEFT JOIN dead_code_analysis dca ON fa.id = dca.analysis_run_id
    GROUP BY fa.id
)
SELECT 
    -- Analysis run details
    fa.id,
    fa.codebase_id,
    fa.codebase_name,
    fa.codebase_language,
    fa.analysis_type,
    fa.status,
    fa.started_at,
    fa.completed_at,
    fa.duration,
    fa.error_message,
    
    -- Basic metrics from results JSON
    fa.files_analyzed,
    fa.symbols_analyzed,
    fa.metrics_created,
    fa.dependencies_mapped,
    fa.dead_code_items,
    fa.impact_relationships,
    
    -- Detailed metrics
    rm.total_metrics,
    rm.critical_metrics,
    rm.warning_metrics,
    rm.good_metrics,
    ROUND(rm.avg_complexity, 2) as avg_complexity,
    rm.max_complexity,
    ROUND(rm.avg_lines_of_code, 0) as avg_lines_of_code,
    
    -- Dependency statistics
    ds.total_dependencies,
    ds.circular_dependencies,
    ds.files_with_dependencies,
    ROUND(ds.avg_dependency_strength, 1) as avg_dependency_strength,
    ds.max_dependency_strength,
    
    -- Dead code statistics
    dcs.total_dead_code_items,
    dcs.high_confidence_dead_code,
    dcs.removable_items,
    dcs.unused_functions,
    dcs.unused_classes,
    dcs.unused_variables,
    
    -- Summary statistics (same for all rows)
    asm.total_analyses,
    asm.completed_analyses,
    asm.running_analyses,
    asm.failed_analyses,
    asm.codebases_analyzed,
    asm.analysis_types,
    ROUND(asm.avg_duration_seconds, 1) as avg_duration_seconds,
    asm.total_files_analyzed as summary_total_files,
    asm.total_symbols_analyzed as summary_total_symbols,
    asm.total_dead_code_items as summary_total_dead_code,
    
    -- Status indicators
    CASE fa.status
        WHEN 'completed' THEN '✅ Completed'
        WHEN 'running' THEN '🔄 Running'
        WHEN 'failed' THEN '❌ Failed'
        ELSE '⏳ Pending'
    END as status_label,
    
    -- Quality indicators
    CASE 
        WHEN fa.status != 'completed' THEN NULL
        WHEN rm.critical_metrics > 0 THEN '🔴 Critical Issues'
        WHEN rm.warning_metrics > 0 THEN '🟡 Warnings'
        ELSE '🟢 Good Quality'
    END as quality_label,
    
    -- Dead code indicator
    CASE 
        WHEN fa.status != 'completed' THEN NULL
        WHEN dcs.high_confidence_dead_code > 10 THEN '🗑️ High Dead Code'
        WHEN dcs.high_confidence_dead_code > 0 THEN '📝 Some Dead Code'
        ELSE '✨ Clean Code'
    END as dead_code_label,
    
    -- Dependency health
    CASE 
        WHEN fa.status != 'completed' THEN NULL
        WHEN ds.circular_dependencies > 0 THEN '🔄 Circular Dependencies'
        WHEN ds.max_dependency_strength > 10 THEN '🕸️ High Coupling'
        ELSE '🔗 Healthy Dependencies'
    END as dependency_label
    
FROM filtered_analyses fa
LEFT JOIN recent_metrics rm ON fa.id = rm.analysis_run_id
LEFT JOIN dependency_stats ds ON fa.id = ds.analysis_run_id
LEFT JOIN dead_code_stats dcs ON fa.id = dcs.analysis_run_id
CROSS JOIN analysis_summary asm
ORDER BY fa.started_at DESC
LIMIT COALESCE($4::INTEGER, 50)
OFFSET COALESCE($5::INTEGER, 0);

