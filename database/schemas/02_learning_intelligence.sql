-- =============================================================================
-- LEARNING AND INTELLIGENCE MODULE
-- =============================================================================
-- Advanced learning patterns, context analysis, and continuous improvement
-- capabilities for autonomous software development
-- =============================================================================

-- =============================================================================
-- LEARNING-SPECIFIC ENUMS
-- =============================================================================

-- Evaluation status for learning processes
CREATE TYPE evaluation_status AS ENUM (
    'pending',
    'in_progress',
    'completed',
    'failed',
    'cancelled',
    'timeout'
);

-- Error classification for intelligent error handling
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

-- Learning pattern types for continuous improvement
CREATE TYPE learning_pattern_type AS ENUM (
    'successful_implementation',
    'error_resolution',
    'optimization_strategy',
    'testing_approach',
    'deployment_pattern',
    'code_structure',
    'performance_improvement',
    'security_enhancement',
    'refactoring_pattern',
    'integration_pattern'
);

-- =============================================================================
-- EVALUATION AND ANALYSIS TABLES
-- =============================================================================

-- Evaluations - track learning and improvement evaluations
CREATE TABLE evaluations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    codebase_id UUID REFERENCES codebases(id) ON DELETE CASCADE,
    
    -- Evaluation metadata
    name VARCHAR(255) NOT NULL,
    description TEXT,
    evaluation_type VARCHAR(100) NOT NULL, -- 'code_analysis', 'task_optimization', 'error_resolution', 'performance_improvement'
    
    -- Target information
    target_type VARCHAR(100) NOT NULL, -- 'repository', 'task', 'function', 'file', 'system'
    target_id UUID,
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

-- Context analysis - comprehensive codebase understanding
CREATE TABLE context_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    codebase_id UUID NOT NULL REFERENCES codebases(id) ON DELETE CASCADE,
    evaluation_id UUID REFERENCES evaluations(id) ON DELETE CASCADE,
    
    -- Analysis scope
    file_path TEXT,
    function_name VARCHAR(255),
    class_name VARCHAR(255),
    
    -- Analysis metadata
    analysis_type VARCHAR(100) NOT NULL, -- 'full_codebase', 'incremental', 'targeted', 'function_level'
    analysis_depth VARCHAR(50) DEFAULT 'comprehensive', -- 'surface', 'detailed', 'comprehensive', 'deep'
    
    -- Code structure analysis
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
    
    -- Security analysis
    security_vulnerabilities JSONB DEFAULT '[]',
    security_recommendations JSONB DEFAULT '[]',
    
    -- Analysis timing
    analysis_started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    analysis_completed_at TIMESTAMP WITH TIME ZONE,
    analysis_duration_ms INTEGER,
    
    -- Metadata and versioning
    metadata JSONB DEFAULT '{}',
    analysis_version VARCHAR(50) DEFAULT '1.0',
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- ERROR TRACKING AND LEARNING
-- =============================================================================

-- Error reports - intelligent error classification and tracking
CREATE TABLE error_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    codebase_id UUID REFERENCES codebases(id) ON DELETE CASCADE,
    task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
    evaluation_id UUID REFERENCES evaluations(id) ON DELETE SET NULL,
    
    -- Error identification
    error_type error_classification NOT NULL,
    error_code VARCHAR(100),
    error_message TEXT NOT NULL,
    error_context JSONB DEFAULT '{}',
    
    -- Source information
    source_type VARCHAR(100), -- 'task', 'evaluation', 'system', 'integration', 'compilation', 'runtime'
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
    resolution_status VARCHAR(50) DEFAULT 'open', -- 'open', 'investigating', 'resolved', 'closed', 'wont_fix'
    resolution_strategy JSONB DEFAULT '{}',
    resolution_steps TEXT[],
    resolved_at TIMESTAMP WITH TIME ZONE,
    
    -- Learning and prevention
    prevention_measures JSONB DEFAULT '[]',
    learning_notes TEXT,
    similar_errors JSONB DEFAULT '[]', -- References to similar past errors
    
    -- Timing
    occurred_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    reported_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT error_reports_message_not_empty CHECK (length(trim(error_message)) > 0)
);

-- =============================================================================
-- LEARNING PATTERNS AND INTELLIGENCE
-- =============================================================================

-- Learning patterns - capture and reuse successful patterns
CREATE TABLE learning_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Pattern identification
    pattern_type learning_pattern_type NOT NULL,
    pattern_name VARCHAR(255) NOT NULL,
    pattern_description TEXT,
    
    -- Pattern data and signature
    pattern_signature JSONB NOT NULL,
    pattern_context JSONB DEFAULT '{}',
    success_indicators JSONB DEFAULT '{}',
    
    -- Effectiveness metrics
    usage_count INTEGER DEFAULT 0,
    success_rate DECIMAL(5,2) DEFAULT 0.0,
    effectiveness_score DECIMAL(5,2),
    confidence_level DECIMAL(5,2) DEFAULT 0.0,
    
    -- Pattern evolution and versioning
    version INTEGER DEFAULT 1,
    parent_pattern_id UUID REFERENCES learning_patterns(id),
    evolution_notes TEXT,
    
    -- Application scope and constraints
    applicable_contexts JSONB DEFAULT '[]',
    exclusion_criteria JSONB DEFAULT '[]',
    prerequisites JSONB DEFAULT '[]',
    
    -- Learning metadata
    discovered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_applied_at TIMESTAMP WITH TIME ZONE,
    last_validated_at TIMESTAMP WITH TIME ZONE,
    
    -- Status and lifecycle
    is_active BOOLEAN DEFAULT true,
    is_validated BOOLEAN DEFAULT false,
    validation_notes TEXT,
    
    -- Performance tracking
    avg_execution_time_ms INTEGER,
    avg_improvement_score DECIMAL(5,2),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT learning_patterns_name_not_empty CHECK (length(trim(pattern_name)) > 0),
    CONSTRAINT learning_patterns_success_rate_range CHECK (success_rate >= 0 AND success_rate <= 100),
    CONSTRAINT learning_patterns_effectiveness_range CHECK (effectiveness_score IS NULL OR (effectiveness_score >= 0 AND effectiveness_score <= 100))
);

-- Pattern applications - track pattern usage and outcomes
CREATE TABLE pattern_applications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pattern_id UUID NOT NULL REFERENCES learning_patterns(id) ON DELETE CASCADE,
    evaluation_id UUID REFERENCES evaluations(id) ON DELETE SET NULL,
    task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
    
    -- Application context
    application_context JSONB DEFAULT '{}',
    target_type VARCHAR(100) NOT NULL,
    target_id UUID NOT NULL,
    
    -- Application details
    applied_configuration JSONB DEFAULT '{}',
    adaptation_notes TEXT,
    customizations JSONB DEFAULT '{}',
    
    -- Results and feedback
    application_result VARCHAR(50), -- 'success', 'failure', 'partial_success', 'needs_refinement'
    outcome_metrics JSONB DEFAULT '{}',
    feedback_score DECIMAL(5,2),
    
    -- Performance tracking
    execution_time_ms INTEGER,
    improvement_achieved DECIMAL(5,2),
    
    -- Learning feedback
    lessons_learned TEXT,
    improvement_suggestions JSONB DEFAULT '[]',
    issues_encountered JSONB DEFAULT '[]',
    
    -- Timing
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT pattern_applications_feedback_range CHECK (feedback_score IS NULL OR (feedback_score >= 0 AND feedback_score <= 100))
);

-- =============================================================================
-- CONTINUOUS IMPROVEMENT
-- =============================================================================

-- Improvement cycles - systematic continuous improvement tracking
CREATE TABLE improvement_cycles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    codebase_id UUID REFERENCES codebases(id) ON DELETE CASCADE,
    
    -- Cycle identification
    cycle_name VARCHAR(255) NOT NULL,
    cycle_type VARCHAR(100) NOT NULL, -- 'process_refinement', 'pattern_optimization', 'error_prevention', 'performance_improvement'
    
    -- Cycle scope
    scope_type VARCHAR(100), -- 'global', 'codebase', 'task_type', 'pattern_type'
    scope_id UUID,
    scope_metadata JSONB DEFAULT '{}',
    
    -- Improvement goals and metrics
    improvement_goals JSONB DEFAULT '[]',
    success_criteria JSONB DEFAULT '{}',
    target_metrics JSONB DEFAULT '{}',
    
    -- Cycle execution
    status VARCHAR(50) DEFAULT 'planning', -- 'planning', 'executing', 'evaluating', 'completed', 'cancelled'
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
    errors_prevented INTEGER DEFAULT 0,
    
    -- Next steps and recommendations
    follow_up_actions JSONB DEFAULT '[]',
    next_cycle_recommendations TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT improvement_cycles_name_not_empty CHECK (length(trim(cycle_name)) > 0)
);

-- Knowledge base - accumulated learning and insights
CREATE TABLE knowledge_base (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Content identification
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    content_type VARCHAR(50) DEFAULT 'markdown', -- 'markdown', 'code', 'json', 'yaml'
    
    -- Categorization and tagging
    category VARCHAR(100),
    tags JSONB DEFAULT '[]',
    keywords JSONB DEFAULT '[]',
    
    -- Source and provenance
    source VARCHAR(100), -- 'manual', 'auto_generated', 'learned', 'pattern_derived', 'error_analysis'
    source_id UUID,
    confidence_score DECIMAL(3,2),
    
    -- Usage and validation
    usage_count INTEGER DEFAULT 0,
    validation_count INTEGER DEFAULT 0,
    accuracy_score DECIMAL(3,2),
    
    -- Relationships
    related_patterns JSONB DEFAULT '[]',
    related_errors JSONB DEFAULT '[]',
    related_evaluations JSONB DEFAULT '[]',
    
    -- Lifecycle
    last_accessed_at TIMESTAMP WITH TIME ZONE,
    last_validated_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT knowledge_base_title_not_empty CHECK (length(trim(title)) > 0),
    CONSTRAINT knowledge_base_content_not_empty CHECK (length(trim(content)) > 0)
);

-- =============================================================================
-- ADVANCED FUNCTIONS
-- =============================================================================

-- Calculate context analysis completeness score
CREATE OR REPLACE FUNCTION calculate_context_completeness(analysis_id UUID)
RETURNS DECIMAL(5,2) AS $$
DECLARE
    analysis_record RECORD;
    completeness_score DECIMAL(5,2) := 0.0;
    component_count INTEGER := 10; -- Total components to check
    completed_components INTEGER := 0;
BEGIN
    SELECT * INTO analysis_record FROM context_analysis WHERE id = analysis_id;
    
    IF NOT FOUND THEN
        RETURN 0.0;
    END IF;
    
    -- Check completeness of different analysis components
    IF jsonb_typeof(analysis_record.code_structure) = 'object' AND jsonb_object_keys(analysis_record.code_structure) IS NOT NULL THEN
        completed_components := completed_components + 1;
    END IF;
    
    IF jsonb_typeof(analysis_record.dependencies) = 'object' AND jsonb_object_keys(analysis_record.dependencies) IS NOT NULL THEN
        completed_components := completed_components + 1;
    END IF;
    
    IF jsonb_typeof(analysis_record.patterns) = 'object' AND jsonb_object_keys(analysis_record.patterns) IS NOT NULL THEN
        completed_components := completed_components + 1;
    END IF;
    
    IF jsonb_typeof(analysis_record.complexity_metrics) = 'object' AND jsonb_object_keys(analysis_record.complexity_metrics) IS NOT NULL THEN
        completed_components := completed_components + 1;
    END IF;
    
    IF jsonb_typeof(analysis_record.semantic_graph) = 'object' AND jsonb_object_keys(analysis_record.semantic_graph) IS NOT NULL THEN
        completed_components := completed_components + 1;
    END IF;
    
    IF jsonb_typeof(analysis_record.function_relationships) = 'object' AND jsonb_object_keys(analysis_record.function_relationships) IS NOT NULL THEN
        completed_components := completed_components + 1;
    END IF;
    
    IF jsonb_typeof(analysis_record.quality_indicators) = 'object' AND jsonb_object_keys(analysis_record.quality_indicators) IS NOT NULL THEN
        completed_components := completed_components + 1;
    END IF;
    
    IF jsonb_typeof(analysis_record.performance_profile) = 'object' AND jsonb_object_keys(analysis_record.performance_profile) IS NOT NULL THEN
        completed_components := completed_components + 1;
    END IF;
    
    IF jsonb_array_length(COALESCE(analysis_record.security_vulnerabilities, '[]')) > 0 THEN
        completed_components := completed_components + 1;
    END IF;
    
    IF jsonb_array_length(COALESCE(analysis_record.optimization_suggestions, '[]')) > 0 THEN
        completed_components := completed_components + 1;
    END IF;
    
    completeness_score := (completed_components::DECIMAL / component_count::DECIMAL) * 100.0;
    
    RETURN completeness_score;
END;
$$ LANGUAGE plpgsql;

-- Update learning pattern effectiveness based on application results
CREATE OR REPLACE FUNCTION update_pattern_effectiveness(
    pattern_id UUID, 
    application_result VARCHAR, 
    feedback_score DECIMAL,
    execution_time_ms INTEGER DEFAULT NULL
)
RETURNS VOID AS $$
DECLARE
    pattern_record RECORD;
    new_success_rate DECIMAL(5,2);
    new_effectiveness DECIMAL(5,2);
    new_avg_time INTEGER;
BEGIN
    SELECT * INTO pattern_record FROM learning_patterns WHERE id = pattern_id;
    
    IF NOT FOUND THEN
        RETURN;
    END IF;
    
    -- Update usage count and last applied timestamp
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
    
    -- Update average execution time
    IF execution_time_ms IS NOT NULL THEN
        SELECT 
            COALESCE(
                (COALESCE(avg_execution_time_ms, 0) * usage_count + execution_time_ms) / (usage_count + 1),
                execution_time_ms
            )
        INTO new_avg_time
        FROM learning_patterns 
        WHERE id = pattern_id;
    END IF;
    
    -- Update the pattern with new metrics
    UPDATE learning_patterns 
    SET success_rate = new_success_rate,
        effectiveness_score = COALESCE(new_effectiveness, effectiveness_score),
        avg_execution_time_ms = COALESCE(new_avg_time, avg_execution_time_ms),
        updated_at = CURRENT_TIMESTAMP
    WHERE id = pattern_id;
END;
$$ LANGUAGE plpgsql;

-- Get learning system health and statistics
CREATE OR REPLACE FUNCTION get_learning_system_health()
RETURNS JSONB AS $$
DECLARE
    result JSONB;
    evaluation_stats JSONB;
    error_stats JSONB;
    learning_stats JSONB;
    knowledge_stats JSONB;
BEGIN
    -- Evaluation statistics
    SELECT jsonb_build_object(
        'total_evaluations', COUNT(*),
        'active_evaluations', COUNT(*) FILTER (WHERE status IN ('pending', 'in_progress')),
        'completed_evaluations', COUNT(*) FILTER (WHERE status = 'completed'),
        'failed_evaluations', COUNT(*) FILTER (WHERE status = 'failed'),
        'average_effectiveness', ROUND(AVG(effectiveness_score), 2),
        'evaluations_last_24h', COUNT(*) FILTER (WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours')
    ) INTO evaluation_stats
    FROM evaluations;
    
    -- Error statistics
    SELECT jsonb_build_object(
        'total_errors', COUNT(*),
        'open_errors', COUNT(*) FILTER (WHERE resolution_status = 'open'),
        'resolved_errors', COUNT(*) FILTER (WHERE resolution_status = 'resolved'),
        'critical_errors', COUNT(*) FILTER (WHERE severity = 'critical'),
        'errors_last_24h', COUNT(*) FILTER (WHERE occurred_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours'),
        'avg_resolution_time_hours', ROUND(AVG(EXTRACT(EPOCH FROM (resolved_at - occurred_at)) / 3600), 2) FILTER (WHERE resolved_at IS NOT NULL)
    ) INTO error_stats
    FROM error_reports;
    
    -- Learning pattern statistics
    SELECT jsonb_build_object(
        'total_patterns', COUNT(*),
        'active_patterns', COUNT(*) FILTER (WHERE is_active = true),
        'validated_patterns', COUNT(*) FILTER (WHERE is_validated = true),
        'average_effectiveness', ROUND(AVG(effectiveness_score), 2),
        'average_success_rate', ROUND(AVG(success_rate), 2),
        'patterns_applied_last_24h', (
            SELECT COUNT(*) FROM pattern_applications 
            WHERE applied_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
        )
    ) INTO learning_stats
    FROM learning_patterns;
    
    -- Knowledge base statistics
    SELECT jsonb_build_object(
        'total_articles', COUNT(*),
        'active_articles', COUNT(*) FILTER (WHERE is_active = true),
        'average_confidence', ROUND(AVG(confidence_score), 2),
        'total_usage', SUM(usage_count),
        'articles_accessed_last_24h', COUNT(*) FILTER (WHERE last_accessed_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours')
    ) INTO knowledge_stats
    FROM knowledge_base;
    
    result := jsonb_build_object(
        'status', 'operational',
        'timestamp', CURRENT_TIMESTAMP,
        'evaluations', evaluation_stats,
        'errors', error_stats,
        'learning_patterns', learning_stats,
        'knowledge_base', knowledge_stats,
        'system_version', '1.0.0'
    );
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- TRIGGERS
-- =============================================================================

-- Update timestamps for learning tables
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

CREATE TRIGGER update_knowledge_base_updated_at 
    BEFORE UPDATE ON knowledge_base 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- INDEXES FOR LEARNING PERFORMANCE
-- =============================================================================

-- Evaluation indexes
CREATE INDEX idx_evaluations_codebase ON evaluations(codebase_id);
CREATE INDEX idx_evaluations_status ON evaluations(status);
CREATE INDEX idx_evaluations_type ON evaluations(evaluation_type);
CREATE INDEX idx_evaluations_target ON evaluations(target_type, target_id);
CREATE INDEX idx_evaluations_created_at ON evaluations(created_at);
CREATE INDEX idx_evaluations_effectiveness ON evaluations(effectiveness_score) WHERE effectiveness_score IS NOT NULL;

-- Context analysis indexes
CREATE INDEX idx_context_analysis_codebase ON context_analysis(codebase_id);
CREATE INDEX idx_context_analysis_evaluation ON context_analysis(evaluation_id);
CREATE INDEX idx_context_analysis_type ON context_analysis(analysis_type);
CREATE INDEX idx_context_analysis_file_path ON context_analysis(file_path);
CREATE INDEX idx_context_analysis_completed_at ON context_analysis(analysis_completed_at);

-- Error report indexes
CREATE INDEX idx_error_reports_codebase ON error_reports(codebase_id);
CREATE INDEX idx_error_reports_task ON error_reports(task_id);
CREATE INDEX idx_error_reports_type ON error_reports(error_type);
CREATE INDEX idx_error_reports_severity ON error_reports(severity);
CREATE INDEX idx_error_reports_status ON error_reports(resolution_status);
CREATE INDEX idx_error_reports_occurred_at ON error_reports(occurred_at);

-- Learning pattern indexes
CREATE INDEX idx_learning_patterns_type ON learning_patterns(pattern_type);
CREATE INDEX idx_learning_patterns_active ON learning_patterns(is_active);
CREATE INDEX idx_learning_patterns_validated ON learning_patterns(is_validated);
CREATE INDEX idx_learning_patterns_effectiveness ON learning_patterns(effectiveness_score) WHERE effectiveness_score IS NOT NULL;
CREATE INDEX idx_learning_patterns_success_rate ON learning_patterns(success_rate);
CREATE INDEX idx_learning_patterns_last_applied ON learning_patterns(last_applied_at);

-- Pattern application indexes
CREATE INDEX idx_pattern_applications_pattern ON pattern_applications(pattern_id);
CREATE INDEX idx_pattern_applications_evaluation ON pattern_applications(evaluation_id);
CREATE INDEX idx_pattern_applications_task ON pattern_applications(task_id);
CREATE INDEX idx_pattern_applications_result ON pattern_applications(application_result);
CREATE INDEX idx_pattern_applications_applied_at ON pattern_applications(applied_at);

-- Improvement cycle indexes
CREATE INDEX idx_improvement_cycles_codebase ON improvement_cycles(codebase_id);
CREATE INDEX idx_improvement_cycles_type ON improvement_cycles(cycle_type);
CREATE INDEX idx_improvement_cycles_status ON improvement_cycles(status);
CREATE INDEX idx_improvement_cycles_created_at ON improvement_cycles(created_at);

-- Knowledge base indexes
CREATE INDEX idx_knowledge_base_category ON knowledge_base(category);
CREATE INDEX idx_knowledge_base_source ON knowledge_base(source);
CREATE INDEX idx_knowledge_base_active ON knowledge_base(is_active);
CREATE INDEX idx_knowledge_base_confidence ON knowledge_base(confidence_score) WHERE confidence_score IS NOT NULL;
CREATE INDEX idx_knowledge_base_usage ON knowledge_base(usage_count);

-- JSONB indexes for complex queries
CREATE INDEX idx_evaluations_context_gin USING gin (context_data);
CREATE INDEX idx_context_analysis_structure_gin USING gin (code_structure);
CREATE INDEX idx_context_analysis_dependencies_gin USING gin (dependencies);
CREATE INDEX idx_error_reports_context_gin USING gin (error_context);
CREATE INDEX idx_learning_patterns_signature_gin USING gin (pattern_signature);
CREATE INDEX idx_pattern_applications_context_gin USING gin (application_context);
CREATE INDEX idx_knowledge_base_tags_gin USING gin (tags);

-- Full-text search indexes
CREATE INDEX idx_evaluations_name_search ON evaluations USING gin(to_tsvector('english', name));
CREATE INDEX idx_error_reports_message_search ON error_reports USING gin(to_tsvector('english', error_message));
CREATE INDEX idx_learning_patterns_name_search ON learning_patterns USING gin(to_tsvector('english', pattern_name));
CREATE INDEX idx_knowledge_base_content_search ON knowledge_base USING gin(to_tsvector('english', content));

-- =============================================================================
-- COMMENTS FOR DOCUMENTATION
-- =============================================================================

COMMENT ON TABLE evaluations IS 'Learning and improvement evaluation tracking';
COMMENT ON TABLE context_analysis IS 'Comprehensive codebase context and semantic analysis';
COMMENT ON TABLE error_reports IS 'Intelligent error classification and learning system';
COMMENT ON TABLE learning_patterns IS 'Captured patterns for continuous improvement';
COMMENT ON TABLE pattern_applications IS 'Pattern usage tracking and effectiveness measurement';
COMMENT ON TABLE improvement_cycles IS 'Systematic continuous improvement cycle management';
COMMENT ON TABLE knowledge_base IS 'Accumulated learning and insights repository';

COMMENT ON FUNCTION calculate_context_completeness IS 'Calculate completeness score for context analysis';
COMMENT ON FUNCTION update_pattern_effectiveness IS 'Update learning pattern effectiveness metrics';
COMMENT ON FUNCTION get_learning_system_health IS 'Get comprehensive learning system health overview';

