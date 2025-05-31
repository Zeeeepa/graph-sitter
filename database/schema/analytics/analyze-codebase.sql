-- Comprehensive codebase analysis including dependency graphs, metrics, and dead code detection
-- Parameters: codebase_id, analysis_type (optional, default 'full')

WITH analysis_start AS (
    INSERT INTO analysis_runs (
        codebase_id,
        analysis_type,
        status,
        started_at
    ) VALUES (
        $1::UUID,
        COALESCE($2::TEXT, 'full'),
        'running',
        NOW()
    )
    RETURNING id, codebase_id, analysis_type, started_at
),
codebase_overview AS (
    SELECT 
        c.id,
        c.name,
        c.language,
        COUNT(cf.id) as total_files,
        COUNT(cf.id) FILTER (WHERE cf.is_deleted = FALSE) as active_files,
        COUNT(DISTINCT cf.file_extension) as file_types,
        SUM(cf.file_size) as total_size_bytes,
        COUNT(cs.id) as total_symbols,
        COUNT(cs.id) FILTER (WHERE cs.symbol_type = 'function') as function_count,
        COUNT(cs.id) FILTER (WHERE cs.symbol_type = 'class') as class_count,
        COUNT(cs.id) FILTER (WHERE cs.symbol_type = 'variable') as variable_count
    FROM codebases c
    LEFT JOIN codebase_files cf ON c.id = cf.codebase_id
    LEFT JOIN code_symbols cs ON cf.id = cs.file_id
    WHERE c.id = $1::UUID
    GROUP BY c.id, c.name, c.language
),
file_metrics AS (
    INSERT INTO code_metrics (
        analysis_run_id,
        file_id,
        metric_type,
        metric_value,
        threshold_status
    )
    SELECT 
        ast.id,
        cf.id,
        'lines_of_code',
        COALESCE(
            ARRAY_LENGTH(STRING_TO_ARRAY(cf.metadata->>'content', E'\n'), 1),
            0
        ),
        CASE 
            WHEN COALESCE(ARRAY_LENGTH(STRING_TO_ARRAY(cf.metadata->>'content', E'\n'), 1), 0) > 1000 THEN 'critical'
            WHEN COALESCE(ARRAY_LENGTH(STRING_TO_ARRAY(cf.metadata->>'content', E'\n'), 1), 0) > 500 THEN 'warning'
            ELSE 'good'
        END
    FROM analysis_start ast
    JOIN codebase_files cf ON ast.codebase_id = cf.codebase_id
    WHERE cf.is_deleted = FALSE
    RETURNING analysis_run_id, COUNT(*) as metrics_created
),
symbol_complexity AS (
    INSERT INTO code_metrics (
        analysis_run_id,
        symbol_id,
        metric_type,
        metric_value,
        threshold_status
    )
    SELECT 
        ast.id,
        cs.id,
        'cyclomatic_complexity',
        COALESCE(cs.complexity_score, 1),
        CASE 
            WHEN COALESCE(cs.complexity_score, 1) > 10 THEN 'critical'
            WHEN COALESCE(cs.complexity_score, 1) > 5 THEN 'warning'
            ELSE 'good'
        END
    FROM analysis_start ast
    JOIN codebase_files cf ON ast.codebase_id = cf.codebase_id
    JOIN code_symbols cs ON cf.id = cs.file_id
    WHERE cf.is_deleted = FALSE
    AND cs.symbol_type IN ('function', 'method')
    RETURNING analysis_run_id, COUNT(*) as complexity_metrics_created
),
dependency_analysis AS (
    INSERT INTO dependency_analysis (
        analysis_run_id,
        source_file_id,
        target_file_id,
        target_external_name,
        dependency_strength,
        is_circular
    )
    SELECT 
        ast.id,
        sf.id as source_file_id,
        tf.id as target_file_id,
        sd.target_external_name,
        COUNT(*) as dependency_strength,
        -- Simple circular dependency detection (would need more sophisticated algorithm)
        EXISTS(
            SELECT 1 FROM symbol_dependencies sd2
            JOIN code_symbols cs2_source ON sd2.source_symbol_id = cs2_source.id
            JOIN code_symbols cs2_target ON sd2.target_symbol_id = cs2_target.id
            JOIN codebase_files cf2_source ON cs2_source.file_id = cf2_source.id
            JOIN codebase_files cf2_target ON cs2_target.file_id = cf2_target.id
            WHERE cf2_source.id = tf.id AND cf2_target.id = sf.id
        ) as is_circular
    FROM analysis_start ast
    JOIN codebase_files sf ON ast.codebase_id = sf.codebase_id  -- source files
    JOIN code_symbols cs_source ON sf.id = cs_source.file_id
    JOIN symbol_dependencies sd ON cs_source.id = sd.source_symbol_id
    LEFT JOIN code_symbols cs_target ON sd.target_symbol_id = cs_target.id
    LEFT JOIN codebase_files tf ON cs_target.file_id = tf.id  -- target files
    WHERE sf.is_deleted = FALSE
    AND (tf.is_deleted = FALSE OR tf.id IS NULL)
    GROUP BY ast.id, sf.id, tf.id, sd.target_external_name
    RETURNING analysis_run_id, COUNT(*) as dependencies_analyzed
),
dead_code_detection AS (
    INSERT INTO dead_code_analysis (
        analysis_run_id,
        symbol_id,
        dead_code_type,
        confidence_score,
        reason,
        suggested_action
    )
    SELECT 
        ast.id,
        cs.id,
        CASE 
            WHEN cs.symbol_type = 'function' THEN 'unused_function'
            WHEN cs.symbol_type = 'class' THEN 'unused_class'
            WHEN cs.symbol_type = 'variable' THEN 'unused_variable'
            ELSE 'unused_symbol'
        END,
        CASE 
            WHEN cs.is_exported = FALSE AND NOT EXISTS(
                SELECT 1 FROM symbol_dependencies sd WHERE sd.target_symbol_id = cs.id
            ) THEN 0.9
            WHEN cs.visibility = 'private' AND NOT EXISTS(
                SELECT 1 FROM symbol_dependencies sd WHERE sd.target_symbol_id = cs.id
            ) THEN 0.7
            ELSE 0.3
        END,
        CASE 
            WHEN cs.is_exported = FALSE AND NOT EXISTS(
                SELECT 1 FROM symbol_dependencies sd WHERE sd.target_symbol_id = cs.id
            ) THEN 'Not exported and no internal references found'
            WHEN cs.visibility = 'private' AND NOT EXISTS(
                SELECT 1 FROM symbol_dependencies sd WHERE sd.target_symbol_id = cs.id
            ) THEN 'Private symbol with no references'
            ELSE 'Low usage detected'
        END,
        CASE 
            WHEN cs.is_exported = FALSE AND NOT EXISTS(
                SELECT 1 FROM symbol_dependencies sd WHERE sd.target_symbol_id = cs.id
            ) THEN 'remove'
            ELSE 'review'
        END
    FROM analysis_start ast
    JOIN codebase_files cf ON ast.codebase_id = cf.codebase_id
    JOIN code_symbols cs ON cf.id = cs.file_id
    WHERE cf.is_deleted = FALSE
    AND cs.symbol_type IN ('function', 'class', 'variable')
    RETURNING analysis_run_id, COUNT(*) as dead_code_items_found
),
impact_analysis AS (
    INSERT INTO impact_analysis (
        analysis_run_id,
        changed_symbol_id,
        impacted_symbol_id,
        impact_type,
        impact_severity,
        impact_radius,
        estimated_effort
    )
    WITH RECURSIVE impact_chain AS (
        -- Direct impacts
        SELECT 
            cs.id as changed_symbol_id,
            cs_target.id as impacted_symbol_id,
            'direct' as impact_type,
            1 as radius
        FROM code_symbols cs
        JOIN symbol_dependencies sd ON cs.id = sd.target_symbol_id
        JOIN code_symbols cs_target ON sd.source_symbol_id = cs_target.id
        JOIN codebase_files cf ON cs.file_id = cf.codebase_id
        WHERE cf.codebase_id = $1::UUID
        
        UNION ALL
        
        -- Indirect impacts (up to 3 levels)
        SELECT 
            ic.changed_symbol_id,
            cs_next.id as impacted_symbol_id,
            'indirect' as impact_type,
            ic.radius + 1
        FROM impact_chain ic
        JOIN symbol_dependencies sd ON ic.impacted_symbol_id = sd.target_symbol_id
        JOIN code_symbols cs_next ON sd.source_symbol_id = cs_next.id
        WHERE ic.radius < 3
    )
    SELECT 
        ast.id,
        ic.changed_symbol_id,
        ic.impacted_symbol_id,
        ic.impact_type,
        CASE 
            WHEN ic.radius = 1 THEN 'high'
            WHEN ic.radius = 2 THEN 'medium'
            ELSE 'low'
        END,
        ic.radius,
        CASE 
            WHEN ic.radius = 1 THEN 2
            WHEN ic.radius = 2 THEN 1
            ELSE 1
        END
    FROM analysis_start ast
    CROSS JOIN impact_chain ic
    RETURNING analysis_run_id, COUNT(*) as impact_relationships_mapped
),
analysis_completion AS (
    UPDATE analysis_runs 
    SET 
        status = 'completed',
        completed_at = NOW(),
        duration = NOW() - started_at,
        results = JSON_BUILD_OBJECT(
            'files_analyzed', (SELECT active_files FROM codebase_overview),
            'symbols_analyzed', (SELECT total_symbols FROM codebase_overview),
            'metrics_created', COALESCE((SELECT SUM(metrics_created) FROM file_metrics), 0),
            'dependencies_mapped', COALESCE((SELECT SUM(dependencies_analyzed) FROM dependency_analysis), 0),
            'dead_code_items', COALESCE((SELECT SUM(dead_code_items_found) FROM dead_code_detection), 0),
            'impact_relationships', COALESCE((SELECT SUM(impact_relationships_mapped) FROM impact_analysis), 0)
        )
    WHERE id = (SELECT id FROM analysis_start)
    RETURNING id, status, completed_at, duration, results
)
SELECT 
    ast.id as analysis_run_id,
    ast.analysis_type,
    ast.started_at,
    ac.completed_at,
    ac.duration,
    ac.status,
    co.name as codebase_name,
    co.language,
    co.total_files,
    co.active_files,
    co.file_types,
    co.total_size_bytes,
    co.total_symbols,
    co.function_count,
    co.class_count,
    co.variable_count,
    ac.results,
    'Analysis completed successfully' as result_message
FROM analysis_start ast
LEFT JOIN analysis_completion ac ON ast.id = ac.id
CROSS JOIN codebase_overview co;

