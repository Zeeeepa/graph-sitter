-- Enhanced Database Schema: Common Query Examples
-- Examples of typical queries for continuous learning and analytics

-- ============================================================================
-- MACHINE LEARNING MODEL QUERIES
-- ============================================================================

-- 1. Get all active models with their latest performance metrics
SELECT 
    m.name,
    m.version,
    m.model_type,
    m.status,
    m.performance_metrics->>'accuracy' as accuracy,
    m.performance_metrics->>'f1_score' as f1_score,
    m.created_at,
    COUNT(p.id) as prediction_count,
    AVG(p.accuracy_score) as avg_prediction_accuracy
FROM ml_models m
LEFT JOIN predictions p ON m.id = p.model_id
WHERE m.status = 'active'
GROUP BY m.id, m.name, m.version, m.model_type, m.status, m.performance_metrics, m.created_at
ORDER BY m.created_at DESC;

-- 2. Find models that need retraining (low accuracy)
SELECT 
    m.name,
    m.version,
    m.model_type,
    AVG(p.accuracy_score) as avg_accuracy,
    COUNT(p.id) as prediction_count,
    MAX(p.prediction_timestamp) as last_prediction
FROM ml_models m
JOIN predictions p ON m.id = p.model_id
WHERE m.status = 'active'
AND p.prediction_timestamp > NOW() - INTERVAL '30 days'
GROUP BY m.id, m.name, m.version, m.model_type
HAVING AVG(p.accuracy_score) < 0.80
ORDER BY avg_accuracy ASC;

-- 3. Model training progress tracking
SELECT 
    m.name,
    m.version,
    ts.status,
    ts.progress_percentage,
    ts.current_epoch,
    ts.total_epochs,
    ts.loss_history->-1 as latest_loss,
    EXTRACT(EPOCH FROM (NOW() - ts.training_start))/3600 as training_hours
FROM ml_models m
JOIN model_training_sessions ts ON m.id = ts.model_id
WHERE ts.status IN ('running', 'completed')
ORDER BY ts.training_start DESC;

-- ============================================================================
-- OPENEVOLVE EXPERIMENT QUERIES
-- ============================================================================

-- 4. Active evolution experiments with progress
SELECT 
    e.name,
    e.status,
    e.current_generation,
    e.max_generations,
    e.best_score,
    e.population_size,
    COUNT(i.id) as total_individuals,
    AVG(i.fitness_score) as avg_fitness,
    MAX(i.fitness_score) as max_fitness,
    ROUND((e.current_generation::DECIMAL / e.max_generations * 100), 2) as progress_percentage
FROM evolution_experiments e
LEFT JOIN evolution_generations g ON e.id = g.experiment_id
LEFT JOIN evolution_individuals i ON g.id = i.generation_id
WHERE e.status = 'running'
GROUP BY e.id, e.name, e.status, e.current_generation, e.max_generations, 
         e.best_score, e.population_size
ORDER BY e.started_at DESC;

-- 5. Best performing individuals across all experiments
SELECT 
    e.name as experiment_name,
    g.generation_number,
    i.individual_index,
    i.fitness_score,
    i.evaluation_metrics->>'correctness_score' as correctness,
    i.evaluation_metrics->>'efficiency_score' as efficiency,
    LENGTH(i.phenotype) as code_length,
    i.evaluated_at
FROM evolution_experiments e
JOIN evolution_generations g ON e.id = g.experiment_id
JOIN evolution_individuals i ON g.id = i.generation_id
WHERE i.evaluation_status = 'completed'
AND i.fitness_score IS NOT NULL
ORDER BY i.fitness_score DESC
LIMIT 20;

-- 6. Evolution experiment cost analysis
SELECT 
    e.name,
    e.status,
    COUNT(li.id) as llm_interactions,
    SUM(li.token_count_input) as total_input_tokens,
    SUM(li.token_count_output) as total_output_tokens,
    SUM(li.cost_usd) as total_cost_usd,
    AVG(li.response_time_ms) as avg_response_time_ms
FROM evolution_experiments e
LEFT JOIN llm_interactions li ON e.id = li.experiment_id
GROUP BY e.id, e.name, e.status
ORDER BY total_cost_usd DESC NULLS LAST;

-- ============================================================================
-- PATTERN RECOGNITION QUERIES
-- ============================================================================

-- 7. Most frequent patterns by severity
SELECT 
    p.pattern_type,
    p.pattern_name,
    p.severity_level,
    p.occurrence_frequency,
    COUNT(po.id) as total_occurrences,
    COUNT(CASE WHEN po.resolution_status = 'resolved' THEN 1 END) as resolved_count,
    ROUND(
        COUNT(CASE WHEN po.resolution_status = 'resolved' THEN 1 END)::DECIMAL / 
        COUNT(po.id) * 100, 2
    ) as resolution_rate_percentage
FROM identified_patterns p
LEFT JOIN pattern_occurrences po ON p.id = po.pattern_id
WHERE p.status = 'active'
GROUP BY p.id, p.pattern_type, p.pattern_name, p.severity_level, p.occurrence_frequency
ORDER BY p.occurrence_frequency DESC, p.severity_level;

-- 8. Pattern trends over time
SELECT 
    DATE_TRUNC('week', po.detection_timestamp) as week,
    p.pattern_type,
    p.severity_level,
    COUNT(po.id) as occurrences,
    COUNT(DISTINCT po.source_id) as affected_entities
FROM pattern_occurrences po
JOIN identified_patterns p ON po.pattern_id = p.id
WHERE po.detection_timestamp > NOW() - INTERVAL '12 weeks'
GROUP BY DATE_TRUNC('week', po.detection_timestamp), p.pattern_type, p.severity_level
ORDER BY week DESC, occurrences DESC;

-- 9. Predictions accuracy analysis
SELECT 
    p.prediction_type,
    COUNT(*) as total_predictions,
    COUNT(CASE WHEN p.status = 'validated' THEN 1 END) as validated_predictions,
    AVG(p.accuracy_score) as avg_accuracy,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY p.accuracy_score) as p95_accuracy,
    AVG(p.confidence_interval->>'upper'::DECIMAL - p.confidence_interval->>'lower'::DECIMAL) as avg_confidence_width
FROM predictions p
WHERE p.prediction_timestamp > NOW() - INTERVAL '30 days'
AND p.accuracy_score IS NOT NULL
GROUP BY p.prediction_type
ORDER BY avg_accuracy DESC;

-- ============================================================================
-- ANALYTICS AND PERFORMANCE QUERIES
-- ============================================================================

-- 10. Learning events volume and processing time trends
SELECT 
    DATE_TRUNC('hour', timestamp) as hour,
    event_type,
    COUNT(*) as event_count,
    AVG(processing_time_ms) as avg_processing_time,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY processing_time_ms) as p95_processing_time,
    SUM(event_size_bytes) as total_size_bytes
FROM learning_events
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', timestamp), event_type
ORDER BY hour DESC, event_count DESC;

-- 11. System performance metrics dashboard
SELECT 
    metric_category,
    metric_name,
    AVG(value) as avg_value,
    MIN(value) as min_value,
    MAX(value) as max_value,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY value) as p95_value,
    unit,
    COUNT(*) as sample_count
FROM system_performance_metrics
WHERE timestamp > NOW() - INTERVAL '1 hour'
GROUP BY metric_category, metric_name, unit
ORDER BY metric_category, metric_name;

-- 12. Resource utilization alerts
SELECT 
    host_name,
    component_name,
    resource_type,
    utilization_percentage,
    threshold_warning,
    threshold_critical,
    timestamp,
    CASE 
        WHEN utilization_percentage > threshold_critical THEN 'CRITICAL'
        WHEN utilization_percentage > threshold_warning THEN 'WARNING'
        ELSE 'OK'
    END as alert_level
FROM resource_utilization
WHERE timestamp > NOW() - INTERVAL '1 hour'
AND (utilization_percentage > threshold_warning OR alert_triggered = true)
ORDER BY utilization_percentage DESC;

-- ============================================================================
-- A/B TESTING QUERIES
-- ============================================================================

-- 13. A/B test results analysis
SELECT 
    e.experiment_name,
    a.variant,
    COUNT(DISTINCT a.user_id) as unique_users,
    COUNT(m.id) as total_events,
    AVG(m.metric_value) as avg_metric_value,
    STDDEV(m.metric_value) as stddev_metric_value,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY m.metric_value) as median_metric_value
FROM ab_testing_experiments e
JOIN ab_testing_assignments a ON e.id = a.experiment_id
LEFT JOIN ab_testing_metrics m ON a.id = m.assignment_id
WHERE e.status = 'running'
GROUP BY e.id, e.experiment_name, a.variant
ORDER BY e.experiment_name, a.variant;

-- 14. Statistical significance calculation for A/B tests
WITH variant_stats AS (
    SELECT 
        e.experiment_name,
        a.variant,
        COUNT(DISTINCT a.user_id) as sample_size,
        AVG(m.metric_value) as mean_value,
        STDDEV(m.metric_value) as std_dev
    FROM ab_testing_experiments e
    JOIN ab_testing_assignments a ON e.id = a.experiment_id
    JOIN ab_testing_metrics m ON a.id = m.assignment_id
    WHERE e.status IN ('running', 'completed')
    AND m.metric_name = 'conversion_rate'
    GROUP BY e.experiment_name, a.variant
),
control_treatment AS (
    SELECT 
        experiment_name,
        MAX(CASE WHEN variant = 'control' THEN mean_value END) as control_mean,
        MAX(CASE WHEN variant = 'control' THEN std_dev END) as control_std,
        MAX(CASE WHEN variant = 'control' THEN sample_size END) as control_n,
        MAX(CASE WHEN variant = 'treatment' THEN mean_value END) as treatment_mean,
        MAX(CASE WHEN variant = 'treatment' THEN std_dev END) as treatment_std,
        MAX(CASE WHEN variant = 'treatment' THEN sample_size END) as treatment_n
    FROM variant_stats
    GROUP BY experiment_name
)
SELECT 
    experiment_name,
    control_mean,
    treatment_mean,
    (treatment_mean - control_mean) as effect_size,
    ROUND(((treatment_mean - control_mean) / control_mean * 100), 2) as lift_percentage,
    control_n,
    treatment_n,
    -- Simplified t-test calculation (for demonstration)
    CASE 
        WHEN control_n > 30 AND treatment_n > 30 THEN 'Sufficient sample size'
        ELSE 'Insufficient sample size'
    END as sample_size_status
FROM control_treatment
WHERE control_mean IS NOT NULL AND treatment_mean IS NOT NULL;

-- ============================================================================
-- INTEGRATION QUERIES
-- ============================================================================

-- 15. Git operations with learning insights
SELECT 
    gole.repository_name,
    gole.operation_type,
    gole.author_id,
    COUNT(gole.id) as operation_count,
    AVG(gole.lines_added + gole.lines_deleted) as avg_code_changes,
    COUNT(DISTINCT le.event_type) as learning_event_types,
    STRING_AGG(DISTINCT le.event_type, ', ') as event_types_list
FROM git_operation_learning_events gole
JOIN learning_events le ON gole.learning_event_id = le.id
WHERE gole.created_at > NOW() - INTERVAL '7 days'
GROUP BY gole.repository_name, gole.operation_type, gole.author_id
ORDER BY operation_count DESC;

-- 16. User behavior analysis across platforms
SELECT 
    usle.user_id,
    usle.platform,
    COUNT(DISTINCT usle.session_id) as session_count,
    SUM(usle.session_duration_ms) / 1000 / 60 as total_minutes,
    AVG(usle.session_duration_ms) / 1000 / 60 as avg_session_minutes,
    SUM(usle.actions_count) as total_actions,
    COUNT(DISTINCT le.event_type) as unique_event_types
FROM user_session_learning_events usle
JOIN learning_events le ON usle.learning_event_id = le.id
WHERE usle.created_at > NOW() - INTERVAL '30 days'
GROUP BY usle.user_id, usle.platform
ORDER BY total_minutes DESC;

-- ============================================================================
-- DATA QUALITY AND MONITORING QUERIES
-- ============================================================================

-- 17. Data quality summary
SELECT 
    table_name,
    check_type,
    COUNT(*) as total_checks,
    COUNT(CASE WHEN status = 'passed' THEN 1 END) as passed_checks,
    AVG(quality_score) as avg_quality_score,
    MIN(quality_score) as min_quality_score,
    MAX(check_timestamp) as last_check
FROM data_quality_checks
WHERE check_timestamp > NOW() - INTERVAL '7 days'
GROUP BY table_name, check_type
ORDER BY avg_quality_score ASC;

-- 18. System health overview
SELECT 
    check_category,
    COUNT(*) as total_checks,
    COUNT(CASE WHEN status = 'healthy' THEN 1 END) as healthy_checks,
    COUNT(CASE WHEN status = 'warning' THEN 1 END) as warning_checks,
    COUNT(CASE WHEN status = 'critical' THEN 1 END) as critical_checks,
    AVG(response_time_ms) as avg_response_time,
    MAX(check_timestamp) as last_check
FROM system_health_checks
WHERE check_timestamp > NOW() - INTERVAL '1 hour'
GROUP BY check_category
ORDER BY critical_checks DESC, warning_checks DESC;

-- ============================================================================
-- ADVANCED ANALYTICS QUERIES
-- ============================================================================

-- 19. Model performance correlation with data quality
SELECT 
    m.model_type,
    m.name,
    AVG(p.accuracy_score) as avg_model_accuracy,
    AVG(dqc.quality_score) as avg_data_quality,
    CORR(p.accuracy_score, dqc.quality_score) as correlation_coefficient,
    COUNT(*) as sample_size
FROM ml_models m
JOIN predictions p ON m.id = p.model_id
JOIN training_datasets td ON m.id = td.id  -- Simplified join for example
JOIN data_quality_checks dqc ON td.name = dqc.table_name
WHERE p.prediction_timestamp > NOW() - INTERVAL '30 days'
AND dqc.check_timestamp > NOW() - INTERVAL '30 days'
GROUP BY m.model_type, m.name
HAVING COUNT(*) > 10
ORDER BY correlation_coefficient DESC NULLS LAST;

-- 20. Predictive maintenance alerts
WITH performance_trends AS (
    SELECT 
        metric_name,
        DATE_TRUNC('hour', timestamp) as hour,
        AVG(value) as avg_value,
        LAG(AVG(value)) OVER (PARTITION BY metric_name ORDER BY DATE_TRUNC('hour', timestamp)) as prev_hour_value
    FROM system_performance_metrics
    WHERE timestamp > NOW() - INTERVAL '24 hours'
    AND metric_category = 'database'
    GROUP BY metric_name, DATE_TRUNC('hour', timestamp)
)
SELECT 
    metric_name,
    hour,
    avg_value,
    prev_hour_value,
    ROUND(((avg_value - prev_hour_value) / prev_hour_value * 100), 2) as change_percentage,
    CASE 
        WHEN ABS((avg_value - prev_hour_value) / prev_hour_value) > 0.5 THEN 'ALERT'
        WHEN ABS((avg_value - prev_hour_value) / prev_hour_value) > 0.2 THEN 'WARNING'
        ELSE 'NORMAL'
    END as status
FROM performance_trends
WHERE prev_hour_value IS NOT NULL
AND ABS((avg_value - prev_hour_value) / prev_hour_value) > 0.1
ORDER BY ABS((avg_value - prev_hour_value) / prev_hour_value) DESC;

