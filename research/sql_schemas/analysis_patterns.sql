-- analysis_patterns.sql
-- SQL schema for storing Graph-Sitter pattern matching results and templates

-- Main table for storing pattern definitions and templates
CREATE TABLE pattern_templates (
    id BIGSERIAL PRIMARY KEY,
    template_name VARCHAR(200) NOT NULL UNIQUE,
    template_category VARCHAR(100) NOT NULL, -- 'code_smell', 'design_pattern', 'anti_pattern', 'security', 'performance'
    language VARCHAR(50) NOT NULL,
    pattern_type VARCHAR(100) NOT NULL, -- 'ast_pattern', 'semantic_pattern', 'structural_pattern', 'behavioral_pattern'
    pattern_definition JSONB NOT NULL, -- The pattern definition in JSON format
    pattern_query TEXT, -- SQL-like or custom query for pattern matching
    ast_pattern TEXT, -- Tree-sitter query pattern
    description TEXT NOT NULL,
    severity VARCHAR(50) DEFAULT 'medium', -- 'low', 'medium', 'high', 'critical'
    confidence_threshold DECIMAL(3,2) DEFAULT 0.8, -- Minimum confidence for matches
    tags VARCHAR(100)[], -- Array of tags for categorization
    examples JSONB, -- Example code snippets that match this pattern
    false_positive_filters JSONB, -- Filters to reduce false positives
    created_by VARCHAR(200),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for storing pattern match results
CREATE TABLE pattern_matches (
    id BIGSERIAL PRIMARY KEY,
    codebase_id VARCHAR(255) NOT NULL,
    template_id BIGINT NOT NULL REFERENCES pattern_templates(id) ON DELETE CASCADE,
    match_id VARCHAR(255) NOT NULL, -- Unique identifier for this match
    file_path TEXT NOT NULL,
    start_line INTEGER NOT NULL,
    start_column INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    end_column INTEGER NOT NULL,
    matched_code TEXT NOT NULL, -- The actual code that matched
    confidence_score DECIMAL(3,2) NOT NULL, -- Confidence in the match (0.0-1.0)
    match_context JSONB, -- Additional context about the match
    symbol_ids BIGINT[], -- Array of symbol IDs involved in the match
    is_confirmed BOOLEAN DEFAULT NULL, -- User confirmation of the match
    is_false_positive BOOLEAN DEFAULT FALSE,
    suppressed BOOLEAN DEFAULT FALSE, -- Whether this match has been suppressed
    suppression_reason TEXT,
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    reviewed_by VARCHAR(200)
);

-- Table for storing pattern match metadata and extracted data
CREATE TABLE pattern_match_data (
    id BIGSERIAL PRIMARY KEY,
    match_id BIGINT NOT NULL REFERENCES pattern_matches(id) ON DELETE CASCADE,
    data_key VARCHAR(200) NOT NULL,
    data_value TEXT,
    data_type VARCHAR(50) NOT NULL, -- 'string', 'number', 'boolean', 'json', 'symbol_reference'
    extraction_method VARCHAR(100), -- How this data was extracted
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for storing pattern analysis sessions
CREATE TABLE pattern_analysis_sessions (
    id BIGSERIAL PRIMARY KEY,
    codebase_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255) NOT NULL UNIQUE,
    templates_used BIGINT[], -- Array of template IDs used in this session
    total_files_scanned INTEGER DEFAULT 0,
    total_matches_found INTEGER DEFAULT 0,
    high_confidence_matches INTEGER DEFAULT 0,
    false_positives_detected INTEGER DEFAULT 0,
    analysis_duration_ms INTEGER,
    memory_usage_mb INTEGER,
    status VARCHAR(50) NOT NULL DEFAULT 'in_progress', -- 'in_progress', 'completed', 'failed'
    error_message TEXT,
    configuration JSONB, -- Analysis configuration parameters
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Table for storing custom pattern rules and transformations
CREATE TABLE pattern_rules (
    id BIGSERIAL PRIMARY KEY,
    rule_name VARCHAR(200) NOT NULL,
    template_id BIGINT NOT NULL REFERENCES pattern_templates(id) ON DELETE CASCADE,
    rule_type VARCHAR(100) NOT NULL, -- 'validation', 'transformation', 'suggestion', 'warning'
    rule_condition JSONB NOT NULL, -- Conditions for when this rule applies
    rule_action JSONB NOT NULL, -- Action to take when rule matches
    priority INTEGER DEFAULT 100, -- Rule priority (lower = higher priority)
    is_active BOOLEAN DEFAULT TRUE,
    created_by VARCHAR(200),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for storing pattern evolution and changes over time
CREATE TABLE pattern_evolution (
    id BIGSERIAL PRIMARY KEY,
    codebase_id VARCHAR(255) NOT NULL,
    template_id BIGINT NOT NULL REFERENCES pattern_templates(id) ON DELETE CASCADE,
    analysis_date DATE NOT NULL,
    match_count INTEGER DEFAULT 0,
    new_matches INTEGER DEFAULT 0,
    resolved_matches INTEGER DEFAULT 0,
    false_positive_rate DECIMAL(5,2) DEFAULT 0.0,
    average_confidence DECIMAL(3,2) DEFAULT 0.0,
    trend_direction VARCHAR(20), -- 'increasing', 'decreasing', 'stable'
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(codebase_id, template_id, analysis_date)
);

-- Table for storing pattern relationships and dependencies
CREATE TABLE pattern_relationships (
    id BIGSERIAL PRIMARY KEY,
    source_template_id BIGINT NOT NULL REFERENCES pattern_templates(id) ON DELETE CASCADE,
    target_template_id BIGINT NOT NULL REFERENCES pattern_templates(id) ON DELETE CASCADE,
    relationship_type VARCHAR(100) NOT NULL, -- 'implies', 'conflicts', 'requires', 'suggests', 'excludes'
    relationship_strength DECIMAL(3,2) DEFAULT 1.0, -- Strength of the relationship (0.0-1.0)
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(source_template_id, target_template_id, relationship_type)
);

-- Table for storing pattern suppression rules
CREATE TABLE pattern_suppressions (
    id BIGSERIAL PRIMARY KEY,
    codebase_id VARCHAR(255) NOT NULL,
    template_id BIGINT REFERENCES pattern_templates(id) ON DELETE CASCADE,
    suppression_scope VARCHAR(100) NOT NULL, -- 'global', 'file', 'function', 'line', 'symbol'
    scope_identifier TEXT, -- File path, function name, symbol ID, etc.
    suppression_reason TEXT NOT NULL,
    suppressed_by VARCHAR(200) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE, -- Optional expiration
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance optimization
CREATE INDEX idx_pattern_templates_category ON pattern_templates(template_category);
CREATE INDEX idx_pattern_templates_language ON pattern_templates(language);
CREATE INDEX idx_pattern_templates_type ON pattern_templates(pattern_type);
CREATE INDEX idx_pattern_templates_severity ON pattern_templates(severity);
CREATE INDEX idx_pattern_templates_tags ON pattern_templates USING GIN(tags);

CREATE INDEX idx_pattern_matches_codebase ON pattern_matches(codebase_id);
CREATE INDEX idx_pattern_matches_template ON pattern_matches(template_id);
CREATE INDEX idx_pattern_matches_file ON pattern_matches(file_path);
CREATE INDEX idx_pattern_matches_confidence ON pattern_matches(confidence_score);
CREATE INDEX idx_pattern_matches_confirmed ON pattern_matches(is_confirmed);
CREATE INDEX idx_pattern_matches_false_positive ON pattern_matches(is_false_positive);
CREATE INDEX idx_pattern_matches_suppressed ON pattern_matches(suppressed);
CREATE INDEX idx_pattern_matches_position ON pattern_matches(start_line, start_column);

CREATE INDEX idx_pattern_match_data_match ON pattern_match_data(match_id);
CREATE INDEX idx_pattern_match_data_key ON pattern_match_data(data_key);
CREATE INDEX idx_pattern_match_data_type ON pattern_match_data(data_type);

CREATE INDEX idx_pattern_analysis_sessions_codebase ON pattern_analysis_sessions(codebase_id);
CREATE INDEX idx_pattern_analysis_sessions_status ON pattern_analysis_sessions(status);

CREATE INDEX idx_pattern_rules_template ON pattern_rules(template_id);
CREATE INDEX idx_pattern_rules_type ON pattern_rules(rule_type);
CREATE INDEX idx_pattern_rules_active ON pattern_rules(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_pattern_rules_priority ON pattern_rules(priority);

CREATE INDEX idx_pattern_evolution_codebase_template ON pattern_evolution(codebase_id, template_id);
CREATE INDEX idx_pattern_evolution_date ON pattern_evolution(analysis_date);
CREATE INDEX idx_pattern_evolution_trend ON pattern_evolution(trend_direction);

CREATE INDEX idx_pattern_relationships_source ON pattern_relationships(source_template_id);
CREATE INDEX idx_pattern_relationships_target ON pattern_relationships(target_template_id);
CREATE INDEX idx_pattern_relationships_type ON pattern_relationships(relationship_type);

CREATE INDEX idx_pattern_suppressions_codebase ON pattern_suppressions(codebase_id);
CREATE INDEX idx_pattern_suppressions_template ON pattern_suppressions(template_id);
CREATE INDEX idx_pattern_suppressions_scope ON pattern_suppressions(suppression_scope);
CREATE INDEX idx_pattern_suppressions_active ON pattern_suppressions(is_active) WHERE is_active = TRUE;

-- Views for common pattern analysis queries
CREATE VIEW v_pattern_summary AS
SELECT 
    pt.template_category,
    pt.language,
    pt.severity,
    COUNT(pt.id) as template_count,
    COUNT(pm.id) as total_matches,
    COUNT(pm.id) FILTER (WHERE pm.confidence_score >= 0.8) as high_confidence_matches,
    COUNT(pm.id) FILTER (WHERE pm.is_false_positive = TRUE) as false_positives,
    AVG(pm.confidence_score) as avg_confidence
FROM pattern_templates pt
LEFT JOIN pattern_matches pm ON pt.id = pm.template_id
GROUP BY pt.template_category, pt.language, pt.severity;

CREATE VIEW v_high_impact_patterns AS
SELECT 
    pt.id,
    pt.template_name,
    pt.template_category,
    pt.severity,
    COUNT(pm.id) as match_count,
    COUNT(pm.id) FILTER (WHERE pm.confidence_score >= 0.9) as high_confidence_count,
    AVG(pm.confidence_score) as avg_confidence,
    COUNT(pm.id) FILTER (WHERE pm.is_false_positive = TRUE) as false_positive_count
FROM pattern_templates pt
LEFT JOIN pattern_matches pm ON pt.id = pm.template_id
GROUP BY pt.id, pt.template_name, pt.template_category, pt.severity
HAVING COUNT(pm.id) > 5
ORDER BY COUNT(pm.id) DESC;

CREATE VIEW v_pattern_hotspots AS
SELECT 
    pm.file_path,
    COUNT(pm.id) as total_matches,
    COUNT(DISTINCT pm.template_id) as unique_patterns,
    COUNT(pm.id) FILTER (WHERE pt.severity = 'critical') as critical_matches,
    COUNT(pm.id) FILTER (WHERE pt.severity = 'high') as high_matches,
    AVG(pm.confidence_score) as avg_confidence
FROM pattern_matches pm
INNER JOIN pattern_templates pt ON pm.template_id = pt.id
WHERE pm.is_false_positive = FALSE AND pm.suppressed = FALSE
GROUP BY pm.file_path
HAVING COUNT(pm.id) > 3
ORDER BY COUNT(pm.id) DESC;

-- Functions for pattern analysis
CREATE OR REPLACE FUNCTION get_pattern_matches_for_symbol(
    p_symbol_id BIGINT,
    p_min_confidence DECIMAL(3,2) DEFAULT 0.5
)
RETURNS TABLE(
    match_id BIGINT,
    template_name VARCHAR(200),
    severity VARCHAR(50),
    confidence_score DECIMAL(3,2),
    matched_code TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        pm.id,
        pt.template_name,
        pt.severity,
        pm.confidence_score,
        pm.matched_code
    FROM pattern_matches pm
    INNER JOIN pattern_templates pt ON pm.template_id = pt.id
    WHERE p_symbol_id = ANY(pm.symbol_ids)
    AND pm.confidence_score >= p_min_confidence
    AND pm.is_false_positive = FALSE
    AND pm.suppressed = FALSE
    ORDER BY pm.confidence_score DESC;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION calculate_pattern_statistics(
    p_codebase_id VARCHAR(255),
    p_template_id BIGINT DEFAULT NULL
)
RETURNS TABLE(
    template_id BIGINT,
    template_name VARCHAR(200),
    total_matches INTEGER,
    confirmed_matches INTEGER,
    false_positives INTEGER,
    avg_confidence DECIMAL(3,2),
    false_positive_rate DECIMAL(5,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        pt.id,
        pt.template_name,
        COUNT(pm.id)::INTEGER as total_matches,
        COUNT(pm.id) FILTER (WHERE pm.is_confirmed = TRUE)::INTEGER as confirmed_matches,
        COUNT(pm.id) FILTER (WHERE pm.is_false_positive = TRUE)::INTEGER as false_positives,
        COALESCE(AVG(pm.confidence_score), 0.0)::DECIMAL(3,2) as avg_confidence,
        CASE 
            WHEN COUNT(pm.id) > 0 THEN 
                (COUNT(pm.id) FILTER (WHERE pm.is_false_positive = TRUE)::DECIMAL / COUNT(pm.id) * 100)
            ELSE 0.0
        END::DECIMAL(5,2) as false_positive_rate
    FROM pattern_templates pt
    LEFT JOIN pattern_matches pm ON pt.id = pm.template_id AND pm.codebase_id = p_codebase_id
    WHERE (p_template_id IS NULL OR pt.id = p_template_id)
    GROUP BY pt.id, pt.template_name
    ORDER BY total_matches DESC;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION apply_pattern_suppressions(p_codebase_id VARCHAR(255))
RETURNS INTEGER AS $$
DECLARE
    v_suppressed_count INTEGER := 0;
    v_suppression RECORD;
BEGIN
    -- Apply active suppressions
    FOR v_suppression IN 
        SELECT * FROM pattern_suppressions 
        WHERE codebase_id = p_codebase_id 
        AND is_active = TRUE 
        AND (expires_at IS NULL OR expires_at > NOW())
    LOOP
        UPDATE pattern_matches 
        SET suppressed = TRUE, suppression_reason = v_suppression.suppression_reason
        WHERE codebase_id = p_codebase_id
        AND (v_suppression.template_id IS NULL OR template_id = v_suppression.template_id)
        AND CASE v_suppression.suppression_scope
            WHEN 'global' THEN TRUE
            WHEN 'file' THEN file_path = v_suppression.scope_identifier
            WHEN 'function' THEN v_suppression.scope_identifier = ANY(
                SELECT s.qualified_name FROM symbols s WHERE s.id = ANY(symbol_ids)
            )
            WHEN 'symbol' THEN v_suppression.scope_identifier::BIGINT = ANY(symbol_ids)
            ELSE FALSE
        END
        AND suppressed = FALSE;
        
        GET DIAGNOSTICS v_suppressed_count = ROW_COUNT;
    END LOOP;
    
    RETURN v_suppressed_count;
END;
$$ LANGUAGE plpgsql;

-- Function to detect pattern relationships
CREATE OR REPLACE FUNCTION detect_pattern_relationships(p_codebase_id VARCHAR(255))
RETURNS TABLE(
    source_template VARCHAR(200),
    target_template VARCHAR(200),
    relationship_type VARCHAR(100),
    co_occurrence_count INTEGER,
    relationship_strength DECIMAL(3,2)
) AS $$
BEGIN
    RETURN QUERY
    WITH pattern_co_occurrences AS (
        SELECT 
            pm1.template_id as source_id,
            pm2.template_id as target_id,
            COUNT(*) as co_count
        FROM pattern_matches pm1
        INNER JOIN pattern_matches pm2 ON pm1.file_path = pm2.file_path
        WHERE pm1.codebase_id = p_codebase_id
        AND pm2.codebase_id = p_codebase_id
        AND pm1.template_id != pm2.template_id
        AND pm1.is_false_positive = FALSE
        AND pm2.is_false_positive = FALSE
        AND pm1.suppressed = FALSE
        AND pm2.suppressed = FALSE
        GROUP BY pm1.template_id, pm2.template_id
        HAVING COUNT(*) > 1
    )
    SELECT 
        pt1.template_name,
        pt2.template_name,
        CASE 
            WHEN pco.co_count > 10 THEN 'strong_correlation'
            WHEN pco.co_count > 5 THEN 'correlation'
            ELSE 'weak_correlation'
        END as relationship_type,
        pco.co_count::INTEGER,
        LEAST(pco.co_count::DECIMAL / 100.0, 1.0) as relationship_strength
    FROM pattern_co_occurrences pco
    INNER JOIN pattern_templates pt1 ON pco.source_id = pt1.id
    INNER JOIN pattern_templates pt2 ON pco.target_id = pt2.id
    ORDER BY pco.co_count DESC;
END;
$$ LANGUAGE plpgsql;

-- Triggers for maintaining pattern data
CREATE OR REPLACE FUNCTION update_pattern_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER pattern_templates_update_timestamp
    BEFORE UPDATE ON pattern_templates
    FOR EACH ROW
    EXECUTE FUNCTION update_pattern_timestamp();

CREATE TRIGGER pattern_rules_update_timestamp
    BEFORE UPDATE ON pattern_rules
    FOR EACH ROW
    EXECUTE FUNCTION update_pattern_timestamp();

-- Function to clean up expired suppressions
CREATE OR REPLACE FUNCTION cleanup_expired_suppressions()
RETURNS INTEGER AS $$
DECLARE
    v_cleaned_count INTEGER;
BEGIN
    UPDATE pattern_suppressions 
    SET is_active = FALSE 
    WHERE expires_at IS NOT NULL 
    AND expires_at <= NOW() 
    AND is_active = TRUE;
    
    GET DIAGNOSTICS v_cleaned_count = ROW_COUNT;
    
    RETURN v_cleaned_count;
END;
$$ LANGUAGE plpgsql;

-- Comments for documentation
COMMENT ON TABLE pattern_templates IS 'Stores pattern definitions and templates for code analysis';
COMMENT ON TABLE pattern_matches IS 'Stores results of pattern matching analysis';
COMMENT ON TABLE pattern_match_data IS 'Stores extracted data and metadata from pattern matches';
COMMENT ON TABLE pattern_analysis_sessions IS 'Tracks pattern analysis sessions and performance metrics';
COMMENT ON TABLE pattern_rules IS 'Stores custom rules and transformations for patterns';
COMMENT ON TABLE pattern_evolution IS 'Tracks how pattern occurrences change over time';
COMMENT ON TABLE pattern_relationships IS 'Stores relationships and dependencies between patterns';
COMMENT ON TABLE pattern_suppressions IS 'Stores suppression rules for pattern matches';

COMMENT ON COLUMN pattern_templates.confidence_threshold IS 'Minimum confidence score required for a match to be reported';
COMMENT ON COLUMN pattern_matches.confidence_score IS 'Confidence in the pattern match accuracy (0.0-1.0)';
COMMENT ON COLUMN pattern_evolution.false_positive_rate IS 'Percentage of matches that were false positives';
COMMENT ON COLUMN pattern_relationships.relationship_strength IS 'Strength of the relationship between patterns (0.0-1.0)';

