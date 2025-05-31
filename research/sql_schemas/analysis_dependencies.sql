-- analysis_dependencies.sql
-- SQL schema for storing Graph-Sitter dependency relationships and analysis

-- Main table for storing dependency relationships
CREATE TABLE dependencies (
    id BIGSERIAL PRIMARY KEY,
    codebase_id VARCHAR(255) NOT NULL,
    source_symbol_id BIGINT NOT NULL REFERENCES symbols(id) ON DELETE CASCADE,
    target_symbol_id BIGINT NOT NULL REFERENCES symbols(id) ON DELETE CASCADE,
    dependency_type VARCHAR(100) NOT NULL, -- 'direct', 'chained', 'indirect', 'aliased', 'inheritance', 'composition'
    usage_type VARCHAR(100) NOT NULL, -- 'call', 'reference', 'import', 'inheritance', 'annotation', 'parameter'
    context_file_path TEXT NOT NULL,
    context_line INTEGER NOT NULL,
    context_column INTEGER,
    source_text TEXT, -- The actual code that creates the dependency
    is_conditional BOOLEAN DEFAULT FALSE, -- Dependency only exists under certain conditions
    confidence_score DECIMAL(3,2) DEFAULT 1.0, -- Confidence in dependency detection (0.0-1.0)
    weight INTEGER DEFAULT 1, -- Weight/strength of the dependency
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(source_symbol_id, target_symbol_id, dependency_type, context_line)
);

-- Table for storing dependency chains and paths
CREATE TABLE dependency_chains (
    id BIGSERIAL PRIMARY KEY,
    codebase_id VARCHAR(255) NOT NULL,
    chain_id VARCHAR(255) NOT NULL, -- Unique identifier for the chain
    source_symbol_id BIGINT NOT NULL REFERENCES symbols(id) ON DELETE CASCADE,
    target_symbol_id BIGINT NOT NULL REFERENCES symbols(id) ON DELETE CASCADE,
    path_length INTEGER NOT NULL,
    path_symbols BIGINT[] NOT NULL, -- Array of symbol IDs in the path
    path_types VARCHAR(100)[] NOT NULL, -- Array of dependency types in the path
    is_circular BOOLEAN DEFAULT FALSE,
    total_weight INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for storing circular dependency analysis
CREATE TABLE circular_dependencies (
    id BIGSERIAL PRIMARY KEY,
    codebase_id VARCHAR(255) NOT NULL,
    cycle_id VARCHAR(255) NOT NULL UNIQUE,
    cycle_symbols BIGINT[] NOT NULL, -- Array of symbol IDs in the cycle
    cycle_length INTEGER NOT NULL,
    cycle_strength DECIMAL(5,2) DEFAULT 0.0, -- Measure of how strong the circular dependency is
    break_suggestions TEXT[], -- Suggested ways to break the cycle
    severity VARCHAR(50) DEFAULT 'medium', -- 'low', 'medium', 'high', 'critical'
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for storing module-level dependencies
CREATE TABLE module_dependencies (
    id BIGSERIAL PRIMARY KEY,
    codebase_id VARCHAR(255) NOT NULL,
    source_module_path TEXT NOT NULL,
    target_module_path TEXT NOT NULL,
    dependency_count INTEGER DEFAULT 1,
    import_statements TEXT[], -- Array of import statements
    dependency_types VARCHAR(100)[] NOT NULL, -- Types of dependencies between modules
    is_external BOOLEAN DEFAULT FALSE, -- Whether target is external dependency
    package_name VARCHAR(200), -- For external dependencies
    package_version VARCHAR(100), -- For external dependencies
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(source_module_path, target_module_path)
);

-- Table for storing dependency metrics and statistics
CREATE TABLE dependency_metrics (
    id BIGSERIAL PRIMARY KEY,
    codebase_id VARCHAR(255) NOT NULL,
    symbol_id BIGINT NOT NULL REFERENCES symbols(id) ON DELETE CASCADE,
    incoming_dependencies INTEGER DEFAULT 0, -- How many symbols depend on this one
    outgoing_dependencies INTEGER DEFAULT 0, -- How many symbols this one depends on
    fan_in INTEGER DEFAULT 0, -- Number of modules that depend on this symbol's module
    fan_out INTEGER DEFAULT 0, -- Number of modules this symbol's module depends on
    coupling_factor DECIMAL(5,2) DEFAULT 0.0, -- Measure of coupling (0.0-1.0)
    cohesion_factor DECIMAL(5,2) DEFAULT 0.0, -- Measure of cohesion (0.0-1.0)
    instability DECIMAL(5,2) DEFAULT 0.0, -- I = fan_out / (fan_in + fan_out)
    abstractness DECIMAL(5,2) DEFAULT 0.0, -- A = abstract_classes / total_classes
    distance_from_main DECIMAL(5,2) DEFAULT 0.0, -- |A + I - 1|
    dependency_depth INTEGER DEFAULT 0, -- Maximum depth in dependency tree
    is_leaf_node BOOLEAN DEFAULT FALSE, -- Has no outgoing dependencies
    is_root_node BOOLEAN DEFAULT FALSE, -- Has no incoming dependencies
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for storing dependency analysis sessions
CREATE TABLE dependency_analysis_sessions (
    id BIGSERIAL PRIMARY KEY,
    codebase_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255) NOT NULL UNIQUE,
    analysis_type VARCHAR(100) NOT NULL, -- 'full', 'incremental', 'targeted'
    total_symbols INTEGER DEFAULT 0,
    total_dependencies INTEGER DEFAULT 0,
    circular_dependencies_found INTEGER DEFAULT 0,
    analysis_duration_ms INTEGER,
    memory_usage_mb INTEGER,
    status VARCHAR(50) NOT NULL DEFAULT 'in_progress', -- 'in_progress', 'completed', 'failed'
    error_message TEXT,
    configuration JSONB, -- Analysis configuration parameters
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Table for storing dependency change tracking
CREATE TABLE dependency_changes (
    id BIGSERIAL PRIMARY KEY,
    codebase_id VARCHAR(255) NOT NULL,
    change_id VARCHAR(255) NOT NULL,
    change_type VARCHAR(100) NOT NULL, -- 'added', 'removed', 'modified'
    dependency_id BIGINT REFERENCES dependencies(id) ON DELETE SET NULL,
    old_values JSONB, -- Previous dependency data
    new_values JSONB, -- New dependency data
    change_reason VARCHAR(200), -- 'code_change', 'refactoring', 'analysis_improvement'
    changed_by VARCHAR(200), -- User or system that made the change
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance optimization
CREATE INDEX idx_dependencies_source ON dependencies(source_symbol_id);
CREATE INDEX idx_dependencies_target ON dependencies(target_symbol_id);
CREATE INDEX idx_dependencies_type ON dependencies(dependency_type);
CREATE INDEX idx_dependencies_usage_type ON dependencies(usage_type);
CREATE INDEX idx_dependencies_codebase ON dependencies(codebase_id);
CREATE INDEX idx_dependencies_context ON dependencies(context_file_path, context_line);
CREATE INDEX idx_dependencies_conditional ON dependencies(is_conditional);
CREATE INDEX idx_dependencies_confidence ON dependencies(confidence_score);

CREATE INDEX idx_dependency_chains_codebase ON dependency_chains(codebase_id);
CREATE INDEX idx_dependency_chains_source ON dependency_chains(source_symbol_id);
CREATE INDEX idx_dependency_chains_target ON dependency_chains(target_symbol_id);
CREATE INDEX idx_dependency_chains_length ON dependency_chains(path_length);
CREATE INDEX idx_dependency_chains_circular ON dependency_chains(is_circular);

CREATE INDEX idx_circular_dependencies_codebase ON circular_dependencies(codebase_id);
CREATE INDEX idx_circular_dependencies_severity ON circular_dependencies(severity);
CREATE INDEX idx_circular_dependencies_length ON circular_dependencies(cycle_length);

CREATE INDEX idx_module_dependencies_source ON module_dependencies(source_module_path);
CREATE INDEX idx_module_dependencies_target ON module_dependencies(target_module_path);
CREATE INDEX idx_module_dependencies_external ON module_dependencies(is_external);
CREATE INDEX idx_module_dependencies_package ON module_dependencies(package_name);

CREATE INDEX idx_dependency_metrics_symbol ON dependency_metrics(symbol_id);
CREATE INDEX idx_dependency_metrics_coupling ON dependency_metrics(coupling_factor);
CREATE INDEX idx_dependency_metrics_instability ON dependency_metrics(instability);
CREATE INDEX idx_dependency_metrics_depth ON dependency_metrics(dependency_depth);

-- Views for common dependency analysis queries
CREATE VIEW v_dependency_summary AS
SELECT 
    codebase_id,
    dependency_type,
    usage_type,
    COUNT(*) as dependency_count,
    AVG(confidence_score) as avg_confidence,
    COUNT(*) FILTER (WHERE is_conditional = TRUE) as conditional_count
FROM dependencies
GROUP BY codebase_id, dependency_type, usage_type;

CREATE VIEW v_high_coupling_symbols AS
SELECT 
    s.id,
    s.name,
    s.qualified_name,
    s.symbol_type,
    dm.incoming_dependencies,
    dm.outgoing_dependencies,
    dm.coupling_factor,
    dm.instability
FROM symbols s
INNER JOIN dependency_metrics dm ON s.id = dm.symbol_id
WHERE dm.coupling_factor > 0.7
ORDER BY dm.coupling_factor DESC;

CREATE VIEW v_dependency_hotspots AS
SELECT 
    s.id,
    s.name,
    s.qualified_name,
    s.file_path,
    COUNT(d.id) as total_dependencies,
    COUNT(d.id) FILTER (WHERE d.dependency_type = 'direct') as direct_dependencies,
    COUNT(d.id) FILTER (WHERE d.dependency_type = 'indirect') as indirect_dependencies,
    AVG(d.confidence_score) as avg_confidence
FROM symbols s
LEFT JOIN dependencies d ON s.id = d.source_symbol_id
GROUP BY s.id, s.name, s.qualified_name, s.file_path
HAVING COUNT(d.id) > 10
ORDER BY COUNT(d.id) DESC;

-- Functions for dependency analysis
CREATE OR REPLACE FUNCTION get_dependency_path(
    p_source_symbol_id BIGINT,
    p_target_symbol_id BIGINT,
    p_max_depth INTEGER DEFAULT 10
)
RETURNS TABLE(
    path_length INTEGER,
    path_symbols BIGINT[],
    path_names TEXT[]
) AS $$
WITH RECURSIVE dependency_path AS (
    -- Base case: direct dependency
    SELECT 
        d.source_symbol_id,
        d.target_symbol_id,
        1 as depth,
        ARRAY[d.source_symbol_id, d.target_symbol_id] as path,
        ARRAY[s1.name, s2.name] as names
    FROM dependencies d
    INNER JOIN symbols s1 ON d.source_symbol_id = s1.id
    INNER JOIN symbols s2 ON d.target_symbol_id = s2.id
    WHERE d.source_symbol_id = p_source_symbol_id
    
    UNION ALL
    
    -- Recursive case: indirect dependency
    SELECT 
        dp.source_symbol_id,
        d.target_symbol_id,
        dp.depth + 1,
        dp.path || d.target_symbol_id,
        dp.names || s.name
    FROM dependency_path dp
    INNER JOIN dependencies d ON dp.target_symbol_id = d.source_symbol_id
    INNER JOIN symbols s ON d.target_symbol_id = s.id
    WHERE dp.depth < p_max_depth
    AND NOT d.target_symbol_id = ANY(dp.path) -- Prevent cycles
)
SELECT 
    dp.depth,
    dp.path,
    dp.names
FROM dependency_path dp
WHERE dp.target_symbol_id = p_target_symbol_id
ORDER BY dp.depth
LIMIT 1;
$$ LANGUAGE sql;

CREATE OR REPLACE FUNCTION calculate_dependency_metrics(p_symbol_id BIGINT)
RETURNS VOID AS $$
DECLARE
    v_incoming INTEGER;
    v_outgoing INTEGER;
    v_coupling DECIMAL(5,2);
    v_depth INTEGER;
BEGIN
    -- Calculate incoming dependencies
    SELECT COUNT(*) INTO v_incoming
    FROM dependencies
    WHERE target_symbol_id = p_symbol_id;
    
    -- Calculate outgoing dependencies
    SELECT COUNT(*) INTO v_outgoing
    FROM dependencies
    WHERE source_symbol_id = p_symbol_id;
    
    -- Calculate coupling factor
    v_coupling := CASE 
        WHEN (v_incoming + v_outgoing) = 0 THEN 0.0
        ELSE v_outgoing::DECIMAL / (v_incoming + v_outgoing)
    END;
    
    -- Calculate dependency depth
    WITH RECURSIVE depth_calc AS (
        SELECT source_symbol_id, 0 as depth
        FROM dependencies
        WHERE source_symbol_id = p_symbol_id
        AND target_symbol_id NOT IN (
            SELECT source_symbol_id FROM dependencies WHERE target_symbol_id = p_symbol_id
        )
        
        UNION ALL
        
        SELECT d.target_symbol_id, dc.depth + 1
        FROM dependencies d
        INNER JOIN depth_calc dc ON d.source_symbol_id = dc.source_symbol_id
        WHERE dc.depth < 20 -- Prevent infinite recursion
    )
    SELECT COALESCE(MAX(depth), 0) INTO v_depth FROM depth_calc;
    
    -- Insert or update metrics
    INSERT INTO dependency_metrics (
        symbol_id, incoming_dependencies, outgoing_dependencies, 
        coupling_factor, dependency_depth, calculated_at
    )
    VALUES (
        p_symbol_id, v_incoming, v_outgoing, 
        v_coupling, v_depth, NOW()
    )
    ON CONFLICT (symbol_id) DO UPDATE SET
        incoming_dependencies = EXCLUDED.incoming_dependencies,
        outgoing_dependencies = EXCLUDED.outgoing_dependencies,
        coupling_factor = EXCLUDED.coupling_factor,
        dependency_depth = EXCLUDED.dependency_depth,
        calculated_at = EXCLUDED.calculated_at;
END;
$$ LANGUAGE plpgsql;

-- Function to detect circular dependencies
CREATE OR REPLACE FUNCTION detect_circular_dependencies(p_codebase_id VARCHAR(255))
RETURNS TABLE(
    cycle_id VARCHAR(255),
    cycle_symbols BIGINT[],
    cycle_length INTEGER
) AS $$
WITH RECURSIVE cycle_detection AS (
    SELECT 
        d.source_symbol_id,
        d.target_symbol_id,
        ARRAY[d.source_symbol_id] as path,
        1 as depth
    FROM dependencies d
    WHERE d.codebase_id = p_codebase_id
    
    UNION ALL
    
    SELECT 
        cd.source_symbol_id,
        d.target_symbol_id,
        cd.path || d.source_symbol_id,
        cd.depth + 1
    FROM cycle_detection cd
    INNER JOIN dependencies d ON cd.target_symbol_id = d.source_symbol_id
    WHERE cd.depth < 50 -- Prevent infinite recursion
    AND NOT d.source_symbol_id = ANY(cd.path)
)
SELECT 
    md5(array_to_string(path || target_symbol_id, ',')) as cycle_id,
    path || target_symbol_id as cycle_symbols,
    depth + 1 as cycle_length
FROM cycle_detection
WHERE target_symbol_id = source_symbol_id;
$$ LANGUAGE sql;

-- Triggers for maintaining dependency metrics
CREATE OR REPLACE FUNCTION update_dependency_metrics_trigger()
RETURNS TRIGGER AS $$
BEGIN
    -- Update metrics for both source and target symbols
    PERFORM calculate_dependency_metrics(NEW.source_symbol_id);
    PERFORM calculate_dependency_metrics(NEW.target_symbol_id);
    
    IF TG_OP = 'UPDATE' THEN
        -- Also update old symbols if they changed
        IF OLD.source_symbol_id != NEW.source_symbol_id THEN
            PERFORM calculate_dependency_metrics(OLD.source_symbol_id);
        END IF;
        IF OLD.target_symbol_id != NEW.target_symbol_id THEN
            PERFORM calculate_dependency_metrics(OLD.target_symbol_id);
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER dependencies_update_metrics
    AFTER INSERT OR UPDATE ON dependencies
    FOR EACH ROW
    EXECUTE FUNCTION update_dependency_metrics_trigger();

-- Comments for documentation
COMMENT ON TABLE dependencies IS 'Stores dependency relationships between symbols';
COMMENT ON TABLE dependency_chains IS 'Stores dependency chains and paths for analysis';
COMMENT ON TABLE circular_dependencies IS 'Stores detected circular dependency cycles';
COMMENT ON TABLE module_dependencies IS 'Stores module-level dependency relationships';
COMMENT ON TABLE dependency_metrics IS 'Stores calculated dependency metrics for symbols';
COMMENT ON TABLE dependency_analysis_sessions IS 'Tracks dependency analysis sessions and performance';
COMMENT ON TABLE dependency_changes IS 'Tracks changes to dependency relationships over time';

COMMENT ON COLUMN dependencies.confidence_score IS 'Confidence in dependency detection accuracy (0.0-1.0)';
COMMENT ON COLUMN dependency_metrics.instability IS 'Martin instability metric: fan_out / (fan_in + fan_out)';
COMMENT ON COLUMN dependency_metrics.distance_from_main IS 'Distance from main sequence in Martin metrics';

