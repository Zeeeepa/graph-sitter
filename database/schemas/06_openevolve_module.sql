-- =============================================================================
-- OPENEVOLVE MODULE: Context analysis engine and self-healing architecture
-- =============================================================================
-- This module implements the OpenEvolve integration for full codebase understanding,
-- error reporting, automated debugging, and continuous learning systems.
-- =============================================================================

-- OpenEvolve-specific enums
CREATE TYPE evaluation_status AS ENUM (
    'pending',
    'in_progress',
    'completed',
    'failed',
    'cancelled',
    'timeout'
);

CREATE TYPE error_classification AS ENUM (
    'syntax_error',
    'logic_error',
    'runtime_error',
    'performance_issue',
    'security_vulnerability',
    'dependency_issue',
    'configuration_error',
    'integration_failure',
    'data_inconsistency',
    'resource_exhaustion',
    'unknown'
);

CREATE TYPE learning_pattern_type AS ENUM (
    'successful_implementation',
    'error_resolution',
    'optimization_strategy',
    'testing_approach',
    'deployment_pattern',
    'code_structure',
    'performance_improvement',
    'security_enhancement'
);

-- =============================================================================
-- CORE OPENEVOLVE TABLES
-- =============================================================================

-- Evaluations table - tracks OpenEvolve evaluation runs
CREATE TABLE evaluations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Evaluation metadata
    name VARCHAR(255) NOT NULL,
    description TEXT,
    evaluation_type VARCHAR(100) NOT NULL, -- code_analysis, task_optimization, error_resolution
    
    -- Target information
    target_type VARCHAR(100) NOT NULL, -- repository, task, codebase, function
    target_id UUID NOT NULL,
    target_metadata JSONB DEFAULT '{}',
    
    -- Evaluation configuration
    configuration JSONB DEFAULT '{}',
    parameters JSONB DEFAULT '{}',
    constraints JSONB DEFAULT '{}',
    
    -- Execution details
    status evaluation_status DEFAULT 'pending',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER,
    
    -- Results and metrics
    effectiveness_score DECIMAL(5,2), -- 0-100 score
    improvement_metrics JSONB DEFAULT '{}',
    generated_solutions JSONB DEFAULT '[]',
    selected_solution JSONB DEFAULT '{}',
    
    -- Context and learning
    context_data JSONB DEFAULT '{}',
    learning_insights JSONB DEFAULT '{}',
    
    -- Error handling
    error_message TEXT,
    error_details JSONB DEFAULT '{}',
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT evaluations_name_not_empty CHECK (length(trim(name)) > 0),
    CONSTRAINT evaluations_effectiveness_score_range CHECK (effectiveness_score IS NULL OR (effectiveness_score >= 0 AND effectiveness_score <= 100))
);

-- Context analysis table - stores comprehensive codebase understanding
CREATE TABLE context_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    evaluation_id UUID REFERENCES evaluations(id) ON DELETE CASCADE,
    
    -- Analysis scope
    repository_id UUID REFERENCES repositories(id) ON DELETE CASCADE,
    codebase_id UUID REFERENCES codebases(id) ON DELETE CASCADE,
    file_path TEXT,
    
    -- Analysis metadata
    analysis_type VARCHAR(100) NOT NULL, -- full_codebase, incremental, targeted, function_level
    analysis_depth VARCHAR(50) DEFAULT 'comprehensive', -- surface, detailed, comprehensive, deep
    
    -- Context data
    code_structure JSONB DEFAULT '{}',
    dependencies JSONB DEFAULT '{}',
    patterns JSONB DEFAULT '{}',
    complexity_metrics JSONB DEFAULT '{}',
    
    -- Semantic understanding
    semantic_graph JSONB DEFAULT '{}',
    function_relationships JSONB DEFAULT '{}',
    data_flow JSONB DEFAULT '{}',
    control_flow JSONB DEFAULT '{}',
    
    -- Quality assessment
    quality_indicators JSONB DEFAULT '{}',
    potential_issues JSONB DEFAULT '[]',
    improvement_opportunities JSONB DEFAULT '[]',
    
    -- Performance characteristics
    performance_profile JSONB DEFAULT '{}',
    bottlenecks JSONB DEFAULT '[]',
    optimization_suggestions JSONB DEFAULT '[]',
    
    -- Analysis timing
    analysis_started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    analysis_completed_at TIMESTAMP WITH TIME ZONE,
    analysis_duration_ms INTEGER,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Error classification and tracking
CREATE TABLE error_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    evaluation_id UUID REFERENCES evaluations(id) ON DELETE SET NULL,
    
    -- Error identification
    error_type error_classification NOT NULL,
    error_code VARCHAR(100),
    error_message TEXT NOT NULL,
    error_context JSONB DEFAULT '{}',
    
    -- Source information
    source_type VARCHAR(100), -- task, evaluation, system, integration
    source_id UUID,
    source_location TEXT, -- file path, function name, line number
    
    -- Error details
    stack_trace TEXT,
    environment_info JSONB DEFAULT '{}',
    reproduction_steps TEXT[],
    
    -- Classification and analysis
    severity priority_level DEFAULT 'normal',
    impact_assessment JSONB DEFAULT '{}',
    root_cause_analysis JSONB DEFAULT '{}',
    
    -- Resolution tracking
    resolution_status VARCHAR(50) DEFAULT 'open', -- open, investigating, resolved, closed
    resolution_strategy JSONB DEFAULT '{}',
    resolution_steps TEXT[],
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by UUID REFERENCES users(id),
    
    -- Learning and prevention
    prevention_measures JSONB DEFAULT '[]',
    learning_notes TEXT,
    
    -- Timing
    occurred_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    reported_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT error_reports_message_not_empty CHECK (length(trim(error_message)) > 0)
);

-- Learning patterns and insights
CREATE TABLE learning_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Pattern identification
    pattern_type learning_pattern_type NOT NULL,
    pattern_name VARCHAR(255) NOT NULL,
    pattern_description TEXT,
    
    -- Pattern data
    pattern_signature JSONB NOT NULL,
    pattern_context JSONB DEFAULT '{}',
    success_indicators JSONB DEFAULT '{}',
    
    -- Effectiveness metrics
    usage_count INTEGER DEFAULT 0,
    success_rate DECIMAL(5,2) DEFAULT 0.0,
    effectiveness_score DECIMAL(5,2),
    confidence_level DECIMAL(5,2) DEFAULT 0.0,
    
    -- Pattern evolution
    version INTEGER DEFAULT 1,
    parent_pattern_id UUID REFERENCES learning_patterns(id),
    evolution_notes TEXT,
    
    -- Application scope
    applicable_contexts JSONB DEFAULT '[]',
    exclusion_criteria JSONB DEFAULT '[]',
    
    -- Learning metadata
    discovered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_applied_at TIMESTAMP WITH TIME ZONE,
    last_validated_at TIMESTAMP WITH TIME ZONE,
    
    -- Status and lifecycle
    is_active BOOLEAN DEFAULT true,
    is_validated BOOLEAN DEFAULT false,
    validation_notes TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT learning_patterns_name_not_empty CHECK (length(trim(pattern_name)) > 0),
    CONSTRAINT learning_patterns_success_rate_range CHECK (success_rate >= 0 AND success_rate <= 100),
    CONSTRAINT learning_patterns_effectiveness_range CHECK (effectiveness_score IS NULL OR (effectiveness_score >= 0 AND effectiveness_score <= 100))
);

-- Pattern applications - track when and how patterns are applied
CREATE TABLE pattern_applications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    pattern_id UUID NOT NULL REFERENCES learning_patterns(id) ON DELETE CASCADE,
    evaluation_id UUID REFERENCES evaluations(id) ON DELETE SET NULL,
    
    -- Application context
    application_context JSONB DEFAULT '{}',
    target_type VARCHAR(100) NOT NULL,
    target_id UUID NOT NULL,
    
    -- Application details
    applied_configuration JSONB DEFAULT '{}',
    adaptation_notes TEXT,
    
    -- Results and feedback
    application_result VARCHAR(50), -- success, failure, partial_success
    outcome_metrics JSONB DEFAULT '{}',
    feedback_score DECIMAL(5,2),
    
    -- Learning feedback
    lessons_learned TEXT,
    improvement_suggestions JSONB DEFAULT '[]',
    
    -- Timing
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT pattern_applications_feedback_range CHECK (feedback_score IS NULL OR (feedback_score >= 0 AND feedback_score <= 100))
);

-- Continuous improvement tracking
CREATE TABLE improvement_cycles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Cycle identification
    cycle_name VARCHAR(255) NOT NULL,
    cycle_type VARCHAR(100) NOT NULL, -- process_refinement, pattern_optimization, error_prevention
    
    -- Cycle scope
    scope_type VARCHAR(100), -- global, project, repository, task_type
    scope_id UUID,
    scope_metadata JSONB DEFAULT '{}',
    
    -- Improvement goals
    improvement_goals JSONB DEFAULT '[]',
    success_criteria JSONB DEFAULT '{}',
    target_metrics JSONB DEFAULT '{}',
    
    -- Cycle execution
    status VARCHAR(50) DEFAULT 'planning', -- planning, executing, evaluating, completed
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Results and impact
    baseline_metrics JSONB DEFAULT '{}',
    final_metrics JSONB DEFAULT '{}',
    improvement_achieved JSONB DEFAULT '{}',
    impact_assessment JSONB DEFAULT '{}',
    
    -- Learning outcomes
    insights_gained JSONB DEFAULT '[]',
    new_patterns_discovered INTEGER DEFAULT 0,
    patterns_refined INTEGER DEFAULT 0,
    
    -- Next steps
    follow_up_actions JSONB DEFAULT '[]',
    next_cycle_recommendations TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT improvement_cycles_name_not_empty CHECK (length(trim(cycle_name)) > 0)
);

-- =============================================================================
-- OPENEVOLVE FUNCTIONS
-- =============================================================================

-- Function to calculate context analysis completeness
CREATE OR REPLACE FUNCTION calculate_context_completeness(analysis_id UUID)
RETURNS DECIMAL(5,2) AS $$
DECLARE
    analysis_record RECORD;
    completeness_score DECIMAL(5,2) := 0.0;
    component_count INTEGER := 0;
    completed_components INTEGER := 0;
BEGIN
    SELECT * INTO analysis_record FROM context_analysis WHERE id = analysis_id;
    
    IF NOT FOUND THEN
        RETURN 0.0;
    END IF;
    
    -- Check completeness of different analysis components
    component_count := 8; -- Total components to check
    
    IF jsonb_array_length(COALESCE(analysis_record.code_structure, '{}')) > 0 THEN
        completed_components := completed_components + 1;
    END IF;
    
    IF jsonb_array_length(COALESCE(analysis_record.dependencies, '{}')) > 0 THEN
        completed_components := completed_components + 1;
    END IF;
    
    IF jsonb_array_length(COALESCE(analysis_record.patterns, '{}')) > 0 THEN
        completed_components := completed_components + 1;
    END IF;
    
    IF jsonb_array_length(COALESCE(analysis_record.complexity_metrics, '{}')) > 0 THEN
        completed_components := completed_components + 1;
    END IF;
    
    IF jsonb_array_length(COALESCE(analysis_record.semantic_graph, '{}')) > 0 THEN
        completed_components := completed_components + 1;
    END IF;
    
    IF jsonb_array_length(COALESCE(analysis_record.function_relationships, '{}')) > 0 THEN
        completed_components := completed_components + 1;
    END IF;
    
    IF jsonb_array_length(COALESCE(analysis_record.quality_indicators, '{}')) > 0 THEN
        completed_components := completed_components + 1;
    END IF;
    
    IF jsonb_array_length(COALESCE(analysis_record.performance_profile, '{}')) > 0 THEN
        completed_components := completed_components + 1;
    END IF;
    
    completeness_score := (completed_components::DECIMAL / component_count::DECIMAL) * 100.0;
    
    RETURN completeness_score;
END;
$$ LANGUAGE plpgsql;

-- Function to update learning pattern effectiveness
CREATE OR REPLACE FUNCTION update_pattern_effectiveness(pattern_id UUID, application_result VARCHAR, feedback_score DECIMAL)
RETURNS VOID AS $$
DECLARE
    pattern_record RECORD;
    new_success_rate DECIMAL(5,2);
    new_effectiveness DECIMAL(5,2);
BEGIN
    SELECT * INTO pattern_record FROM learning_patterns WHERE id = pattern_id;
    
    IF NOT FOUND THEN
        RETURN;
    END IF;
    
    -- Update usage count
    UPDATE learning_patterns 
    SET usage_count = usage_count + 1,
        last_applied_at = CURRENT_TIMESTAMP
    WHERE id = pattern_id;
    
    -- Calculate new success rate
    IF application_result = 'success' THEN
        SELECT 
            ((usage_count * success_rate / 100.0) + 1) / (usage_count + 1) * 100.0
        INTO new_success_rate
        FROM learning_patterns 
        WHERE id = pattern_id;
    ELSE
        SELECT 
            (usage_count * success_rate / 100.0) / (usage_count + 1) * 100.0
        INTO new_success_rate
        FROM learning_patterns 
        WHERE id = pattern_id;
    END IF;
    
    -- Calculate new effectiveness score (weighted average with feedback)
    IF feedback_score IS NOT NULL THEN
        SELECT 
            COALESCE(
                (COALESCE(effectiveness_score, 0) * 0.7) + (feedback_score * 0.3),
                feedback_score
            )
        INTO new_effectiveness
        FROM learning_patterns 
        WHERE id = pattern_id;
    END IF;
    
    -- Update the pattern
    UPDATE learning_patterns 
    SET success_rate = new_success_rate,
        effectiveness_score = COALESCE(new_effectiveness, effectiveness_score),
        updated_at = CURRENT_TIMESTAMP
    WHERE id = pattern_id;
END;
$$ LANGUAGE plpgsql;

-- Function to get OpenEvolve system health
CREATE OR REPLACE FUNCTION openevolve_health_check()
RETURNS JSONB AS $$
DECLARE
    result JSONB;
    evaluation_stats JSONB;
    error_stats JSONB;
    learning_stats JSONB;
BEGIN
    -- Evaluation statistics
    SELECT jsonb_build_object(
        'total_evaluations', COUNT(*),
        'active_evaluations', COUNT(*) FILTER (WHERE status IN ('pending', 'in_progress')),
        'completed_evaluations', COUNT(*) FILTER (WHERE status = 'completed'),
        'failed_evaluations', COUNT(*) FILTER (WHERE status = 'failed'),
        'average_effectiveness', AVG(effectiveness_score),
        'evaluations_last_24h', COUNT(*) FILTER (WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours')
    ) INTO evaluation_stats
    FROM evaluations;
    
    -- Error statistics
    SELECT jsonb_build_object(
        'total_errors', COUNT(*),
        'open_errors', COUNT(*) FILTER (WHERE resolution_status = 'open'),
        'resolved_errors', COUNT(*) FILTER (WHERE resolution_status = 'resolved'),
        'critical_errors', COUNT(*) FILTER (WHERE severity = 'critical'),
        'errors_last_24h', COUNT(*) FILTER (WHERE occurred_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours')
    ) INTO error_stats
    FROM error_reports;
    
    -- Learning statistics
    SELECT jsonb_build_object(
        'total_patterns', COUNT(*),
        'active_patterns', COUNT(*) FILTER (WHERE is_active = true),
        'validated_patterns', COUNT(*) FILTER (WHERE is_validated = true),
        'average_effectiveness', AVG(effectiveness_score),
        'patterns_applied_last_24h', (
            SELECT COUNT(*) FROM pattern_applications 
            WHERE applied_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
        )
    ) INTO learning_stats
    FROM learning_patterns;
    
    result := jsonb_build_object(
        'status', 'operational',
        'timestamp', CURRENT_TIMESTAMP,
        'evaluations', evaluation_stats,
        'errors', error_stats,
        'learning', learning_stats,
        'system_version', '1.0.0'
    );
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- TRIGGERS
-- =============================================================================

-- Update timestamps
CREATE TRIGGER update_evaluations_updated_at 
    BEFORE UPDATE ON evaluations 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_context_analysis_updated_at 
    BEFORE UPDATE ON context_analysis 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_error_reports_updated_at 
    BEFORE UPDATE ON error_reports 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_learning_patterns_updated_at 
    BEFORE UPDATE ON learning_patterns 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_improvement_cycles_updated_at 
    BEFORE UPDATE ON improvement_cycles 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Notification triggers
CREATE TRIGGER evaluation_change_notification
    AFTER INSERT OR UPDATE OR DELETE ON evaluations
    FOR EACH ROW EXECUTE FUNCTION notify_system_change();

CREATE TRIGGER error_report_notification
    AFTER INSERT OR UPDATE ON error_reports
    FOR EACH ROW EXECUTE FUNCTION notify_system_change();

-- =============================================================================
-- INDEXES
-- =============================================================================

-- Evaluations indexes
CREATE INDEX idx_evaluations_organization ON evaluations(organization_id);
CREATE INDEX idx_evaluations_status ON evaluations(status);
CREATE INDEX idx_evaluations_type ON evaluations(evaluation_type);
CREATE INDEX idx_evaluations_target ON evaluations(target_type, target_id);
CREATE INDEX idx_evaluations_created_at ON evaluations(created_at);
CREATE INDEX idx_evaluations_effectiveness ON evaluations(effectiveness_score) WHERE effectiveness_score IS NOT NULL;

-- Context analysis indexes
CREATE INDEX idx_context_analysis_organization ON context_analysis(organization_id);
CREATE INDEX idx_context_analysis_evaluation ON context_analysis(evaluation_id);
CREATE INDEX idx_context_analysis_repository ON context_analysis(repository_id);
CREATE INDEX idx_context_analysis_codebase ON context_analysis(codebase_id);
CREATE INDEX idx_context_analysis_type ON context_analysis(analysis_type);
CREATE INDEX idx_context_analysis_completed ON context_analysis(analysis_completed_at);

-- Error reports indexes
CREATE INDEX idx_error_reports_organization ON error_reports(organization_id);
CREATE INDEX idx_error_reports_evaluation ON error_reports(evaluation_id);
CREATE INDEX idx_error_reports_type ON error_reports(error_type);
CREATE INDEX idx_error_reports_severity ON error_reports(severity);
CREATE INDEX idx_error_reports_status ON error_reports(resolution_status);
CREATE INDEX idx_error_reports_occurred_at ON error_reports(occurred_at);
CREATE INDEX idx_error_reports_source ON error_reports(source_type, source_id);

-- Learning patterns indexes
CREATE INDEX idx_learning_patterns_organization ON learning_patterns(organization_id);
CREATE INDEX idx_learning_patterns_type ON learning_patterns(pattern_type);
CREATE INDEX idx_learning_patterns_active ON learning_patterns(is_active) WHERE is_active = true;
CREATE INDEX idx_learning_patterns_validated ON learning_patterns(is_validated) WHERE is_validated = true;
CREATE INDEX idx_learning_patterns_effectiveness ON learning_patterns(effectiveness_score) WHERE effectiveness_score IS NOT NULL;
CREATE INDEX idx_learning_patterns_success_rate ON learning_patterns(success_rate);

-- Pattern applications indexes
CREATE INDEX idx_pattern_applications_organization ON pattern_applications(organization_id);
CREATE INDEX idx_pattern_applications_pattern ON pattern_applications(pattern_id);
CREATE INDEX idx_pattern_applications_evaluation ON pattern_applications(evaluation_id);
CREATE INDEX idx_pattern_applications_target ON pattern_applications(target_type, target_id);
CREATE INDEX idx_pattern_applications_result ON pattern_applications(application_result);
CREATE INDEX idx_pattern_applications_applied_at ON pattern_applications(applied_at);

-- Improvement cycles indexes
CREATE INDEX idx_improvement_cycles_organization ON improvement_cycles(organization_id);
CREATE INDEX idx_improvement_cycles_type ON improvement_cycles(cycle_type);
CREATE INDEX idx_improvement_cycles_status ON improvement_cycles(status);
CREATE INDEX idx_improvement_cycles_scope ON improvement_cycles(scope_type, scope_id);

-- GIN indexes for JSONB fields
CREATE INDEX idx_evaluations_configuration_gin USING gin (configuration);
CREATE INDEX idx_evaluations_results_gin USING gin (improvement_metrics);
CREATE INDEX idx_context_analysis_structure_gin USING gin (code_structure);
CREATE INDEX idx_context_analysis_dependencies_gin USING gin (dependencies);
CREATE INDEX idx_error_reports_context_gin USING gin (error_context);
CREATE INDEX idx_learning_patterns_signature_gin USING gin (pattern_signature);

-- =============================================================================
-- VIEWS
-- =============================================================================

-- Active evaluations view
CREATE VIEW active_evaluations AS
SELECT 
    e.*,
    o.name as organization_name,
    CASE 
        WHEN e.status = 'in_progress' AND e.started_at < CURRENT_TIMESTAMP - INTERVAL '1 hour'
        THEN 'potentially_stuck'
        ELSE 'normal'
    END as health_status
FROM evaluations e
JOIN organizations o ON e.organization_id = o.id
WHERE e.status IN ('pending', 'in_progress');

-- Error summary view
CREATE VIEW error_summary AS
SELECT 
    er.error_type,
    er.severity,
    COUNT(*) as error_count,
    COUNT(*) FILTER (WHERE er.resolution_status = 'open') as open_count,
    COUNT(*) FILTER (WHERE er.resolution_status = 'resolved') as resolved_count,
    AVG(EXTRACT(EPOCH FROM (er.resolved_at - er.occurred_at))/3600) as avg_resolution_hours
FROM error_reports er
WHERE er.occurred_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY er.error_type, er.severity
ORDER BY error_count DESC;

-- Learning effectiveness view
CREATE VIEW learning_effectiveness AS
SELECT 
    lp.pattern_type,
    COUNT(*) as pattern_count,
    AVG(lp.effectiveness_score) as avg_effectiveness,
    AVG(lp.success_rate) as avg_success_rate,
    SUM(lp.usage_count) as total_applications,
    COUNT(*) FILTER (WHERE lp.is_validated = true) as validated_count
FROM learning_patterns lp
WHERE lp.is_active = true
GROUP BY lp.pattern_type
ORDER BY avg_effectiveness DESC;

-- =============================================================================
-- INITIAL DATA
-- =============================================================================

-- Insert default learning patterns
INSERT INTO learning_patterns (
    organization_id, 
    pattern_type, 
    pattern_name, 
    pattern_description, 
    pattern_signature,
    applicable_contexts
) VALUES 
(
    (SELECT id FROM organizations WHERE slug = 'default' LIMIT 1),
    'error_resolution',
    'Retry with Exponential Backoff',
    'Standard retry pattern for transient failures',
    jsonb_build_object(
        'strategy', 'exponential_backoff',
        'max_retries', 3,
        'base_delay_ms', 1000,
        'max_delay_ms', 30000
    ),
    jsonb_build_array('network_errors', 'timeout_errors', 'rate_limit_errors')
),
(
    (SELECT id FROM organizations WHERE slug = 'default' LIMIT 1),
    'successful_implementation',
    'Modular Code Structure',
    'Organize code into small, focused modules with clear interfaces',
    jsonb_build_object(
        'principles', jsonb_build_array('single_responsibility', 'clear_interfaces', 'minimal_dependencies'),
        'metrics', jsonb_build_object('max_function_lines', 50, 'max_class_methods', 20)
    ),
    jsonb_build_array('new_features', 'refactoring', 'code_organization')
);

-- =============================================================================
-- SCHEMA MIGRATION TRACKING
-- =============================================================================

-- Record this migration
INSERT INTO schema_migrations (version, description) VALUES 
('06_openevolve_module', 'OpenEvolve integration module with context analysis and self-healing architecture');

-- =============================================================================
-- COMMENTS FOR DOCUMENTATION
-- =============================================================================

COMMENT ON TABLE evaluations IS 'OpenEvolve evaluation runs for code analysis and optimization';
COMMENT ON TABLE context_analysis IS 'Comprehensive codebase understanding and semantic analysis';
COMMENT ON TABLE error_reports IS 'Error classification, tracking, and resolution management';
COMMENT ON TABLE learning_patterns IS 'Learned patterns for successful implementations and error prevention';
COMMENT ON TABLE pattern_applications IS 'Tracking of when and how learning patterns are applied';
COMMENT ON TABLE improvement_cycles IS 'Continuous improvement cycles and their outcomes';

COMMENT ON FUNCTION calculate_context_completeness IS 'Calculate completeness score for context analysis';
COMMENT ON FUNCTION update_pattern_effectiveness IS 'Update learning pattern effectiveness based on application results';
COMMENT ON FUNCTION openevolve_health_check IS 'Health check for OpenEvolve system components';

