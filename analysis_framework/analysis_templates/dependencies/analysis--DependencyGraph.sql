-- Dependency Graph Analysis Template
-- Analyzes import relationships, circular dependencies, and dependency health

WITH import_relationships AS (
    SELECT 
        i.id as import_id,
        i.file_id as source_file_id,
        sf.file_path as source_file_path,
        sf.language as source_language,
        i.resolved_file_id as target_file_id,
        tf.file_path as target_file_path,
        tf.language as target_language,
        i.import_type,
        i.import_path,
        i.import_name,
        i.is_external,
        i.is_relative,
        i.package_name,
        r.id as repository_id,
        r.name as repository_name
    FROM imports i
    JOIN files sf ON i.file_id = sf.id
    LEFT JOIN files tf ON i.resolved_file_id = tf.id
    JOIN repositories r ON sf.repository_id = r.id
    WHERE r.id = $1 -- Repository ID parameter
),
internal_dependencies AS (
    SELECT *
    FROM import_relationships
    WHERE is_external = false AND target_file_id IS NOT NULL
),
external_dependencies AS (
    SELECT 
        repository_id,
        package_name,
        COUNT(*) as usage_count,
        COUNT(DISTINCT source_file_id) as files_using,
        ARRAY_AGG(DISTINCT source_file_path) as using_files
    FROM import_relationships
    WHERE is_external = true AND package_name IS NOT NULL
    GROUP BY repository_id, package_name
),
file_dependency_stats AS (
    SELECT 
        source_file_id,
        source_file_path,
        source_language,
        COUNT(*) as outgoing_dependencies,
        COUNT(CASE WHEN is_external = false THEN 1 END) as internal_dependencies,
        COUNT(CASE WHEN is_external = true THEN 1 END) as external_dependencies,
        COUNT(DISTINCT package_name) FILTER (WHERE is_external = true) as unique_external_packages
    FROM import_relationships
    GROUP BY source_file_id, source_file_path, source_language
    
    UNION ALL
    
    SELECT 
        target_file_id as source_file_id,
        target_file_path as source_file_path,
        target_language as source_language,
        0 as outgoing_dependencies,
        0 as internal_dependencies,
        0 as external_dependencies,
        0 as unique_external_packages
    FROM internal_dependencies
    WHERE target_file_id NOT IN (SELECT source_file_id FROM import_relationships)
),
file_incoming_deps AS (
    SELECT 
        target_file_id as file_id,
        COUNT(*) as incoming_dependencies,
        COUNT(DISTINCT source_file_id) as dependent_files
    FROM internal_dependencies
    GROUP BY target_file_id
),
dependency_graph AS (
    SELECT 
        fds.source_file_id as file_id,
        fds.source_file_path as file_path,
        fds.source_language as language,
        COALESCE(fds.outgoing_dependencies, 0) as outgoing_deps,
        COALESCE(fds.internal_dependencies, 0) as internal_deps,
        COALESCE(fds.external_dependencies, 0) as external_deps,
        COALESCE(fds.unique_external_packages, 0) as external_packages,
        COALESCE(fid.incoming_dependencies, 0) as incoming_deps,
        COALESCE(fid.dependent_files, 0) as dependent_files,
        
        -- Calculate coupling metrics
        COALESCE(fds.outgoing_dependencies, 0) + COALESCE(fid.incoming_dependencies, 0) as total_coupling,
        
        -- Identify potential issues
        CASE 
            WHEN COALESCE(fds.outgoing_dependencies, 0) > 20 THEN 'high_fan_out'
            WHEN COALESCE(fid.incoming_dependencies, 0) > 15 THEN 'high_fan_in'
            WHEN COALESCE(fds.outgoing_dependencies, 0) = 0 AND COALESCE(fid.incoming_dependencies, 0) = 0 THEN 'isolated'
            ELSE 'normal'
        END as coupling_category
        
    FROM file_dependency_stats fds
    LEFT JOIN file_incoming_deps fid ON fds.source_file_id = fid.file_id
),
-- Detect circular dependencies using recursive CTE
circular_dependency_detection AS (
    WITH RECURSIVE dependency_paths AS (
        -- Base case: direct dependencies
        SELECT 
            source_file_id,
            target_file_id,
            ARRAY[source_file_id, target_file_id] as path,
            1 as depth
        FROM internal_dependencies
        
        UNION ALL
        
        -- Recursive case: extend paths
        SELECT 
            dp.source_file_id,
            id.target_file_id,
            dp.path || id.target_file_id,
            dp.depth + 1
        FROM dependency_paths dp
        JOIN internal_dependencies id ON dp.target_file_id = id.source_file_id
        WHERE dp.depth < 10 -- Prevent infinite recursion
        AND NOT (id.target_file_id = ANY(dp.path)) -- Prevent cycles in path building
    ),
    circular_deps AS (
        SELECT DISTINCT
            source_file_id,
            target_file_id,
            path,
            depth
        FROM dependency_paths
        WHERE target_file_id = source_file_id -- Found a cycle
        AND depth > 1
    )
    SELECT 
        repository_id,
        jsonb_agg(
            jsonb_build_object(
                'cycle_files', (
                    SELECT jsonb_agg(f.file_path)
                    FROM files f
                    WHERE f.id = ANY(cd.path)
                ),
                'cycle_length', cd.depth,
                'cycle_complexity', cd.depth * 2 -- Simple complexity metric
            )
        ) as circular_dependencies
    FROM circular_deps cd
    JOIN files f ON cd.source_file_id = f.id
    WHERE f.repository_id = $1
    GROUP BY repository_id
),
dependency_metrics AS (
    SELECT 
        $1 as repository_id,
        COUNT(DISTINCT file_id) as total_files,
        AVG(outgoing_deps) as avg_outgoing_deps,
        AVG(incoming_deps) as avg_incoming_deps,
        AVG(total_coupling) as avg_total_coupling,
        MAX(outgoing_deps) as max_outgoing_deps,
        MAX(incoming_deps) as max_incoming_deps,
        COUNT(CASE WHEN coupling_category = 'high_fan_out' THEN 1 END) as high_fan_out_files,
        COUNT(CASE WHEN coupling_category = 'high_fan_in' THEN 1 END) as high_fan_in_files,
        COUNT(CASE WHEN coupling_category = 'isolated' THEN 1 END) as isolated_files,
        STDDEV(total_coupling) as coupling_stddev
    FROM dependency_graph
),
language_dependency_stats AS (
    SELECT 
        language,
        COUNT(*) as file_count,
        AVG(outgoing_deps) as avg_outgoing_deps,
        AVG(incoming_deps) as avg_incoming_deps,
        COUNT(CASE WHEN coupling_category != 'normal' THEN 1 END) as problematic_files
    FROM dependency_graph
    GROUP BY language
),
dependency_hotspots AS (
    SELECT 
        file_path,
        language,
        outgoing_deps,
        incoming_deps,
        total_coupling,
        coupling_category,
        ROW_NUMBER() OVER (ORDER BY total_coupling DESC) as coupling_rank
    FROM dependency_graph
    WHERE coupling_category != 'normal'
),
recommendations AS (
    SELECT 
        $1 as repository_id,
        ARRAY_AGG(
            CASE 
                WHEN coupling_category = 'high_fan_out' THEN 
                    'File "' || file_path || '" has high outgoing dependencies (' || outgoing_deps || '). Consider breaking into smaller modules.'
                WHEN coupling_category = 'high_fan_in' THEN 
                    'File "' || file_path || '" has high incoming dependencies (' || incoming_deps || '). Consider if this indicates a god class/module.'
                WHEN coupling_category = 'isolated' THEN 
                    'File "' || file_path || '" appears isolated. Verify if it\'s actually used or can be removed.'
            END
        ) FILTER (WHERE coupling_category != 'normal') as improvement_suggestions
    FROM dependency_hotspots
    WHERE coupling_rank <= 15 -- Top 15 issues
)

-- Main analysis result
SELECT 
    'dependencies' as analysis_type,
    'dependency_graph' as analysis_subtype,
    dm.repository_id,
    'dependency_graph_analyzer' as analyzer_name,
    '2.0.0' as analyzer_version,
    NOW() as analysis_date,
    
    -- Results JSON
    jsonb_build_object(
        'summary', jsonb_build_object(
            'total_files', dm.total_files,
            'avg_outgoing_dependencies', ROUND(dm.avg_outgoing_deps, 2),
            'avg_incoming_dependencies', ROUND(dm.avg_incoming_deps, 2),
            'avg_total_coupling', ROUND(dm.avg_total_coupling, 2),
            'max_outgoing_dependencies', dm.max_outgoing_deps,
            'max_incoming_dependencies', dm.max_incoming_deps,
            'coupling_distribution', jsonb_build_object(
                'high_fan_out_files', dm.high_fan_out_files,
                'high_fan_in_files', dm.high_fan_in_files,
                'isolated_files', dm.isolated_files,
                'normal_files', dm.total_files - dm.high_fan_out_files - dm.high_fan_in_files - dm.isolated_files
            )
        ),
        'external_dependencies', (
            SELECT jsonb_agg(
                jsonb_build_object(
                    'package_name', package_name,
                    'usage_count', usage_count,
                    'files_using', files_using,
                    'popularity_score', LEAST(100, usage_count * 10) -- Simple popularity metric
                )
            )
            FROM external_dependencies
            WHERE repository_id = dm.repository_id
            ORDER BY usage_count DESC
            LIMIT 20
        ),
        'dependency_hotspots', (
            SELECT jsonb_agg(
                jsonb_build_object(
                    'file_path', file_path,
                    'language', language,
                    'outgoing_dependencies', outgoing_deps,
                    'incoming_dependencies', incoming_deps,
                    'total_coupling', total_coupling,
                    'issue_type', coupling_category
                )
            )
            FROM dependency_hotspots
            WHERE coupling_rank <= 15
        ),
        'circular_dependencies', COALESCE(
            (SELECT circular_dependencies FROM circular_dependency_detection WHERE repository_id = dm.repository_id),
            '[]'::jsonb
        ),
        'language_breakdown', (
            SELECT jsonb_object_agg(
                language,
                jsonb_build_object(
                    'file_count', file_count,
                    'avg_outgoing_deps', ROUND(avg_outgoing_deps, 2),
                    'avg_incoming_deps', ROUND(avg_incoming_deps, 2),
                    'problematic_files', problematic_files
                )
            )
            FROM language_dependency_stats
        ),
        'dependency_graph_data', (
            SELECT jsonb_build_object(
                'nodes', jsonb_agg(
                    jsonb_build_object(
                        'id', file_id,
                        'label', file_path,
                        'language', language,
                        'outgoing_deps', outgoing_deps,
                        'incoming_deps', incoming_deps,
                        'coupling_category', coupling_category
                    )
                ),
                'edges', (
                    SELECT jsonb_agg(
                        jsonb_build_object(
                            'source', source_file_id,
                            'target', target_file_id,
                            'type', import_type
                        )
                    )
                    FROM internal_dependencies
                    LIMIT 1000 -- Limit for performance
                )
            )
            FROM dependency_graph
        )
    ) as results,
    
    -- Metrics JSON
    jsonb_build_object(
        'avg_outgoing_dependencies', ROUND(dm.avg_outgoing_deps, 2),
        'avg_incoming_dependencies', ROUND(dm.avg_incoming_deps, 2),
        'avg_total_coupling', ROUND(dm.avg_total_coupling, 2),
        'coupling_variance', ROUND(dm.coupling_stddev, 2),
        'problematic_files_ratio', ROUND(((dm.high_fan_out_files + dm.high_fan_in_files)::decimal / dm.total_files) * 100, 2),
        'isolated_files_ratio', ROUND((dm.isolated_files::decimal / dm.total_files) * 100, 2),
        'external_dependency_count', (SELECT COUNT(*) FROM external_dependencies WHERE repository_id = dm.repository_id)
    ) as metrics,
    
    -- Overall score (0-100, lower coupling is better)
    GREATEST(0, LEAST(100, 
        100 - (
            (dm.avg_total_coupling - 5) * 5 + -- Penalty for high average coupling
            ((dm.high_fan_out_files + dm.high_fan_in_files)::decimal / dm.total_files) * 40 + -- Penalty for problematic files
            CASE WHEN EXISTS(SELECT 1 FROM circular_dependency_detection WHERE repository_id = dm.repository_id) THEN 20 ELSE 0 END -- Penalty for circular dependencies
        )
    )) as score,
    
    -- Grade based on coupling and issues
    CASE 
        WHEN dm.avg_total_coupling <= 8 AND dm.high_fan_out_files + dm.high_fan_in_files <= dm.total_files * 0.1 THEN 'A'
        WHEN dm.avg_total_coupling <= 12 AND dm.high_fan_out_files + dm.high_fan_in_files <= dm.total_files * 0.2 THEN 'B'
        WHEN dm.avg_total_coupling <= 18 AND dm.high_fan_out_files + dm.high_fan_in_files <= dm.total_files * 0.3 THEN 'C'
        WHEN dm.avg_total_coupling <= 25 THEN 'D'
        ELSE 'F'
    END as grade,
    
    85.0 as confidence_level, -- Good confidence for dependency analysis
    
    -- Recommendations
    COALESCE(r.improvement_suggestions, ARRAY[]::text[]) as recommendations,
    
    -- Warnings
    ARRAY[
        CASE WHEN EXISTS(SELECT 1 FROM circular_dependency_detection WHERE repository_id = dm.repository_id) THEN 
            'Circular dependencies detected. This can lead to compilation issues and tight coupling.'
        END,
        CASE WHEN dm.avg_total_coupling > 15 THEN 
            'Average coupling (' || ROUND(dm.avg_total_coupling, 1) || ') is high. Consider architectural refactoring.'
        END,
        CASE WHEN dm.high_fan_out_files > dm.total_files * 0.2 THEN 
            'More than 20% of files have high fan-out. This may indicate architectural issues.'
        END,
        CASE WHEN dm.isolated_files > dm.total_files * 0.1 THEN 
            'Found ' || dm.isolated_files || ' isolated files. Review if they are actually needed.'
        END
    ]::text[] as warnings,
    
    -- Metadata
    jsonb_build_object(
        'analysis_parameters', jsonb_build_object(
            'coupling_thresholds', jsonb_build_object(
                'high_fan_out', 20,
                'high_fan_in', 15,
                'normal_coupling_range', '5-12'
            ),
            'metrics_calculated', ARRAY[
                'fan_in', 'fan_out', 'total_coupling', 'circular_dependencies',
                'external_dependencies', 'dependency_depth'
            ]
        ),
        'methodology', 'Dependency analysis examines import relationships to identify coupling issues, circular dependencies, and architectural problems.',
        'tools_used', ARRAY['graph_sitter_dependency_analyzer'],
        'standards_reference', ARRAY['Martin Metrics', 'Object-Oriented Metrics', 'Architectural Patterns']
    ) as metadata

FROM dependency_metrics dm
LEFT JOIN recommendations r ON dm.repository_id = r.repository_id
WHERE dm.repository_id = $1;

