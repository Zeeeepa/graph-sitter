-- analysis_call_graphs.sql
-- SQL schema for storing Graph-Sitter function call graph analysis

-- Main table for storing function call relationships
CREATE TABLE function_calls (
    id BIGSERIAL PRIMARY KEY,
    codebase_id VARCHAR(255) NOT NULL,
    caller_symbol_id BIGINT NOT NULL REFERENCES symbols(id) ON DELETE CASCADE,
    callee_symbol_id BIGINT NOT NULL REFERENCES symbols(id) ON DELETE CASCADE,
    call_site_file_path TEXT NOT NULL,
    call_site_line INTEGER NOT NULL,
    call_site_column INTEGER,
    call_type VARCHAR(100) NOT NULL, -- 'direct', 'indirect', 'dynamic', 'recursive', 'virtual', 'interface'
    call_context VARCHAR(200), -- 'conditional', 'loop', 'exception_handler', 'async', 'callback'
    is_recursive BOOLEAN DEFAULT FALSE,
    is_async BOOLEAN DEFAULT FALSE,
    is_conditional BOOLEAN DEFAULT FALSE, -- Call only happens under certain conditions
    call_frequency INTEGER DEFAULT 1, -- How many times this call appears in the code
    execution_probability DECIMAL(3,2) DEFAULT 1.0, -- Estimated probability of execution (0.0-1.0)
    call_depth INTEGER DEFAULT 0, -- Depth in the call stack
    source_text TEXT, -- The actual call expression
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(caller_symbol_id, callee_symbol_id, call_site_line, call_site_column)
);

-- Table for storing call site details and arguments
CREATE TABLE call_sites (
    id BIGSERIAL PRIMARY KEY,
    function_call_id BIGINT NOT NULL REFERENCES function_calls(id) ON DELETE CASCADE,
    call_site_id VARCHAR(255) NOT NULL, -- Unique identifier for the call site
    argument_count INTEGER DEFAULT 0,
    arguments JSONB, -- Array of argument expressions
    argument_types VARCHAR(200)[], -- Array of argument types
    return_value_used BOOLEAN DEFAULT TRUE,
    call_chain_position INTEGER DEFAULT 0, -- Position in a chain of calls (e.g., obj.method1().method2())
    is_method_chain BOOLEAN DEFAULT FALSE,
    is_constructor_call BOOLEAN DEFAULT FALSE,
    is_static_call BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for storing call graph paths and chains
CREATE TABLE call_paths (
    id BIGSERIAL PRIMARY KEY,
    codebase_id VARCHAR(255) NOT NULL,
    path_id VARCHAR(255) NOT NULL, -- Unique identifier for the path
    start_symbol_id BIGINT NOT NULL REFERENCES symbols(id) ON DELETE CASCADE,
    end_symbol_id BIGINT NOT NULL REFERENCES symbols(id) ON DELETE CASCADE,
    path_length INTEGER NOT NULL,
    path_symbols BIGINT[] NOT NULL, -- Array of symbol IDs in the call path
    path_call_types VARCHAR(100)[] NOT NULL, -- Array of call types in the path
    is_circular BOOLEAN DEFAULT FALSE,
    total_depth INTEGER DEFAULT 0,
    execution_probability DECIMAL(3,2) DEFAULT 1.0, -- Combined probability for the entire path
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for storing recursive call analysis
CREATE TABLE recursive_calls (
    id BIGSERIAL PRIMARY KEY,
    codebase_id VARCHAR(255) NOT NULL,
    function_symbol_id BIGINT NOT NULL REFERENCES symbols(id) ON DELETE CASCADE,
    recursion_type VARCHAR(100) NOT NULL, -- 'direct', 'indirect', 'mutual'
    recursion_depth INTEGER, -- Maximum detected recursion depth
    base_case_detected BOOLEAN DEFAULT FALSE,
    termination_condition TEXT, -- Description of termination condition
    recursion_pattern VARCHAR(200), -- 'tail_recursive', 'head_recursive', 'tree_recursive'
    performance_impact VARCHAR(50) DEFAULT 'unknown', -- 'low', 'medium', 'high', 'critical'
    optimization_suggestions TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for storing call graph metrics
CREATE TABLE call_graph_metrics (
    id BIGSERIAL PRIMARY KEY,
    codebase_id VARCHAR(255) NOT NULL,
    symbol_id BIGINT NOT NULL REFERENCES symbols(id) ON DELETE CASCADE,
    incoming_calls INTEGER DEFAULT 0, -- Number of functions that call this one
    outgoing_calls INTEGER DEFAULT 0, -- Number of functions this one calls
    call_depth INTEGER DEFAULT 0, -- Maximum depth when called from entry points
    fan_in INTEGER DEFAULT 0, -- Number of different callers
    fan_out INTEGER DEFAULT 0, -- Number of different callees
    cyclomatic_complexity INTEGER DEFAULT 0,
    call_complexity INTEGER DEFAULT 0, -- Complexity based on call patterns
    is_entry_point BOOLEAN DEFAULT FALSE, -- Function is an entry point (main, handler, etc.)
    is_leaf_function BOOLEAN DEFAULT FALSE, -- Function makes no calls
    is_hot_path BOOLEAN DEFAULT FALSE, -- Function is on a frequently executed path
    call_frequency_score DECIMAL(5,2) DEFAULT 0.0, -- Estimated call frequency
    performance_criticality VARCHAR(50) DEFAULT 'normal', -- 'low', 'normal', 'high', 'critical'
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for storing call graph analysis sessions
CREATE TABLE call_graph_analysis_sessions (
    id BIGSERIAL PRIMARY KEY,
    codebase_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255) NOT NULL UNIQUE,
    analysis_type VARCHAR(100) NOT NULL, -- 'static', 'dynamic', 'hybrid'
    total_functions INTEGER DEFAULT 0,
    total_calls INTEGER DEFAULT 0,
    recursive_functions_found INTEGER DEFAULT 0,
    max_call_depth INTEGER DEFAULT 0,
    circular_calls_found INTEGER DEFAULT 0,
    analysis_duration_ms INTEGER,
    memory_usage_mb INTEGER,
    status VARCHAR(50) NOT NULL DEFAULT 'in_progress', -- 'in_progress', 'completed', 'failed'
    error_message TEXT,
    configuration JSONB, -- Analysis configuration parameters
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Table for storing dynamic call information (if available)
CREATE TABLE dynamic_call_data (
    id BIGSERIAL PRIMARY KEY,
    codebase_id VARCHAR(255) NOT NULL,
    function_call_id BIGINT NOT NULL REFERENCES function_calls(id) ON DELETE CASCADE,
    execution_count INTEGER DEFAULT 0,
    total_execution_time_ms INTEGER DEFAULT 0,
    average_execution_time_ms DECIMAL(10,3) DEFAULT 0.0,
    memory_usage_bytes BIGINT DEFAULT 0,
    cpu_usage_percent DECIMAL(5,2) DEFAULT 0.0,
    last_executed_at TIMESTAMP WITH TIME ZONE,
    profiling_session_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for storing call graph visualizations and layouts
CREATE TABLE call_graph_layouts (
    id BIGSERIAL PRIMARY KEY,
    codebase_id VARCHAR(255) NOT NULL,
    layout_name VARCHAR(200) NOT NULL,
    layout_type VARCHAR(100) NOT NULL, -- 'hierarchical', 'force_directed', 'circular', 'tree'
    filter_criteria JSONB, -- Criteria used to filter the graph
    node_positions JSONB, -- Positions of nodes in the visualization
    edge_styles JSONB, -- Styling information for edges
    layout_metadata JSONB, -- Additional layout information
    created_by VARCHAR(200),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(codebase_id, layout_name)
);

-- Indexes for performance optimization
CREATE INDEX idx_function_calls_caller ON function_calls(caller_symbol_id);
CREATE INDEX idx_function_calls_callee ON function_calls(callee_symbol_id);
CREATE INDEX idx_function_calls_codebase ON function_calls(codebase_id);
CREATE INDEX idx_function_calls_type ON function_calls(call_type);
CREATE INDEX idx_function_calls_recursive ON function_calls(is_recursive) WHERE is_recursive = TRUE;
CREATE INDEX idx_function_calls_async ON function_calls(is_async) WHERE is_async = TRUE;
CREATE INDEX idx_function_calls_conditional ON function_calls(is_conditional) WHERE is_conditional = TRUE;
CREATE INDEX idx_function_calls_site ON function_calls(call_site_file_path, call_site_line);

CREATE INDEX idx_call_sites_function_call ON call_sites(function_call_id);
CREATE INDEX idx_call_sites_argument_count ON call_sites(argument_count);
CREATE INDEX idx_call_sites_method_chain ON call_sites(is_method_chain) WHERE is_method_chain = TRUE;

CREATE INDEX idx_call_paths_codebase ON call_paths(codebase_id);
CREATE INDEX idx_call_paths_start ON call_paths(start_symbol_id);
CREATE INDEX idx_call_paths_end ON call_paths(end_symbol_id);
CREATE INDEX idx_call_paths_length ON call_paths(path_length);
CREATE INDEX idx_call_paths_circular ON call_paths(is_circular) WHERE is_circular = TRUE;

CREATE INDEX idx_recursive_calls_codebase ON recursive_calls(codebase_id);
CREATE INDEX idx_recursive_calls_function ON recursive_calls(function_symbol_id);
CREATE INDEX idx_recursive_calls_type ON recursive_calls(recursion_type);

CREATE INDEX idx_call_graph_metrics_symbol ON call_graph_metrics(symbol_id);
CREATE INDEX idx_call_graph_metrics_entry_point ON call_graph_metrics(is_entry_point) WHERE is_entry_point = TRUE;
CREATE INDEX idx_call_graph_metrics_leaf ON call_graph_metrics(is_leaf_function) WHERE is_leaf_function = TRUE;
CREATE INDEX idx_call_graph_metrics_hot_path ON call_graph_metrics(is_hot_path) WHERE is_hot_path = TRUE;
CREATE INDEX idx_call_graph_metrics_complexity ON call_graph_metrics(call_complexity);

CREATE INDEX idx_dynamic_call_data_function_call ON dynamic_call_data(function_call_id);
CREATE INDEX idx_dynamic_call_data_execution_count ON dynamic_call_data(execution_count);
CREATE INDEX idx_dynamic_call_data_session ON dynamic_call_data(profiling_session_id);

-- Views for common call graph analysis queries
CREATE VIEW v_call_graph_summary AS
SELECT 
    codebase_id,
    call_type,
    COUNT(*) as call_count,
    COUNT(DISTINCT caller_symbol_id) as unique_callers,
    COUNT(DISTINCT callee_symbol_id) as unique_callees,
    COUNT(*) FILTER (WHERE is_recursive = TRUE) as recursive_calls,
    COUNT(*) FILTER (WHERE is_async = TRUE) as async_calls,
    AVG(execution_probability) as avg_execution_probability
FROM function_calls
GROUP BY codebase_id, call_type;

CREATE VIEW v_function_call_metrics AS
SELECT 
    s.id,
    s.name,
    s.qualified_name,
    s.symbol_type,
    cgm.incoming_calls,
    cgm.outgoing_calls,
    cgm.fan_in,
    cgm.fan_out,
    cgm.call_depth,
    cgm.cyclomatic_complexity,
    cgm.call_complexity,
    cgm.is_entry_point,
    cgm.is_leaf_function,
    cgm.is_hot_path,
    cgm.performance_criticality
FROM symbols s
INNER JOIN call_graph_metrics cgm ON s.id = cgm.symbol_id
WHERE s.symbol_type IN ('function', 'method');

CREATE VIEW v_recursive_function_analysis AS
SELECT 
    s.id,
    s.name,
    s.qualified_name,
    rc.recursion_type,
    rc.recursion_depth,
    rc.base_case_detected,
    rc.recursion_pattern,
    rc.performance_impact,
    array_length(rc.optimization_suggestions, 1) as suggestion_count
FROM symbols s
INNER JOIN recursive_calls rc ON s.id = rc.function_symbol_id;

CREATE VIEW v_hot_call_paths AS
SELECT 
    cp.path_id,
    s1.name as start_function,
    s2.name as end_function,
    cp.path_length,
    cp.execution_probability,
    cp.total_depth
FROM call_paths cp
INNER JOIN symbols s1 ON cp.start_symbol_id = s1.id
INNER JOIN symbols s2 ON cp.end_symbol_id = s2.id
WHERE cp.execution_probability > 0.7
ORDER BY cp.execution_probability DESC, cp.path_length;

-- Functions for call graph analysis
CREATE OR REPLACE FUNCTION get_call_chain(
    p_start_symbol_id BIGINT,
    p_max_depth INTEGER DEFAULT 10
)
RETURNS TABLE(
    depth INTEGER,
    symbol_id BIGINT,
    symbol_name VARCHAR(500),
    call_type VARCHAR(100)
) AS $$
WITH RECURSIVE call_chain AS (
    -- Base case: starting function
    SELECT 
        0 as depth,
        p_start_symbol_id as symbol_id,
        s.name as symbol_name,
        'start'::VARCHAR(100) as call_type
    FROM symbols s
    WHERE s.id = p_start_symbol_id
    
    UNION ALL
    
    -- Recursive case: called functions
    SELECT 
        cc.depth + 1,
        fc.callee_symbol_id,
        s.name,
        fc.call_type
    FROM call_chain cc
    INNER JOIN function_calls fc ON cc.symbol_id = fc.caller_symbol_id
    INNER JOIN symbols s ON fc.callee_symbol_id = s.id
    WHERE cc.depth < p_max_depth
)
SELECT * FROM call_chain ORDER BY depth;
$$ LANGUAGE sql;

CREATE OR REPLACE FUNCTION calculate_call_graph_metrics(p_symbol_id BIGINT)
RETURNS VOID AS $$
DECLARE
    v_incoming INTEGER;
    v_outgoing INTEGER;
    v_fan_in INTEGER;
    v_fan_out INTEGER;
    v_is_entry BOOLEAN;
    v_is_leaf BOOLEAN;
BEGIN
    -- Calculate incoming calls
    SELECT COUNT(*) INTO v_incoming
    FROM function_calls
    WHERE callee_symbol_id = p_symbol_id;
    
    -- Calculate outgoing calls
    SELECT COUNT(*) INTO v_outgoing
    FROM function_calls
    WHERE caller_symbol_id = p_symbol_id;
    
    -- Calculate fan-in (unique callers)
    SELECT COUNT(DISTINCT caller_symbol_id) INTO v_fan_in
    FROM function_calls
    WHERE callee_symbol_id = p_symbol_id;
    
    -- Calculate fan-out (unique callees)
    SELECT COUNT(DISTINCT callee_symbol_id) INTO v_fan_out
    FROM function_calls
    WHERE caller_symbol_id = p_symbol_id;
    
    -- Determine if entry point (no incoming calls or special function names)
    v_is_entry := (v_incoming = 0) OR EXISTS (
        SELECT 1 FROM symbols s 
        WHERE s.id = p_symbol_id 
        AND s.name IN ('main', '__main__', 'init', 'setup', 'start')
    );
    
    -- Determine if leaf function (no outgoing calls)
    v_is_leaf := (v_outgoing = 0);
    
    -- Insert or update metrics
    INSERT INTO call_graph_metrics (
        symbol_id, incoming_calls, outgoing_calls, fan_in, fan_out,
        is_entry_point, is_leaf_function, calculated_at
    )
    VALUES (
        p_symbol_id, v_incoming, v_outgoing, v_fan_in, v_fan_out,
        v_is_entry, v_is_leaf, NOW()
    )
    ON CONFLICT (symbol_id) DO UPDATE SET
        incoming_calls = EXCLUDED.incoming_calls,
        outgoing_calls = EXCLUDED.outgoing_calls,
        fan_in = EXCLUDED.fan_in,
        fan_out = EXCLUDED.fan_out,
        is_entry_point = EXCLUDED.is_entry_point,
        is_leaf_function = EXCLUDED.is_leaf_function,
        calculated_at = EXCLUDED.calculated_at;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION detect_recursive_calls(p_codebase_id VARCHAR(255))
RETURNS TABLE(
    function_id BIGINT,
    recursion_type VARCHAR(100),
    recursion_depth INTEGER
) AS $$
WITH RECURSIVE recursion_detection AS (
    -- Direct recursion
    SELECT 
        fc.caller_symbol_id as function_id,
        'direct'::VARCHAR(100) as recursion_type,
        1 as depth,
        ARRAY[fc.caller_symbol_id] as path
    FROM function_calls fc
    WHERE fc.codebase_id = p_codebase_id
    AND fc.caller_symbol_id = fc.callee_symbol_id
    
    UNION ALL
    
    -- Indirect recursion
    SELECT 
        rd.function_id,
        'indirect'::VARCHAR(100),
        rd.depth + 1,
        rd.path || fc.callee_symbol_id
    FROM recursion_detection rd
    INNER JOIN function_calls fc ON rd.path[array_length(rd.path, 1)] = fc.caller_symbol_id
    WHERE rd.depth < 20 -- Prevent infinite recursion
    AND fc.callee_symbol_id = rd.function_id
    AND NOT fc.callee_symbol_id = ANY(rd.path[1:array_length(rd.path, 1)-1])
)
SELECT DISTINCT function_id, recursion_type, MAX(depth) as recursion_depth
FROM recursion_detection
GROUP BY function_id, recursion_type;
$$ LANGUAGE sql;

-- Triggers for maintaining call graph metrics
CREATE OR REPLACE FUNCTION update_call_graph_metrics_trigger()
RETURNS TRIGGER AS $$
BEGIN
    -- Update metrics for both caller and callee
    PERFORM calculate_call_graph_metrics(NEW.caller_symbol_id);
    PERFORM calculate_call_graph_metrics(NEW.callee_symbol_id);
    
    IF TG_OP = 'UPDATE' THEN
        -- Also update old symbols if they changed
        IF OLD.caller_symbol_id != NEW.caller_symbol_id THEN
            PERFORM calculate_call_graph_metrics(OLD.caller_symbol_id);
        END IF;
        IF OLD.callee_symbol_id != NEW.callee_symbol_id THEN
            PERFORM calculate_call_graph_metrics(OLD.callee_symbol_id);
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER function_calls_update_metrics
    AFTER INSERT OR UPDATE ON function_calls
    FOR EACH ROW
    EXECUTE FUNCTION update_call_graph_metrics_trigger();

-- Comments for documentation
COMMENT ON TABLE function_calls IS 'Stores function call relationships and call sites';
COMMENT ON TABLE call_sites IS 'Stores detailed information about individual call sites';
COMMENT ON TABLE call_paths IS 'Stores call paths and chains for analysis';
COMMENT ON TABLE recursive_calls IS 'Stores analysis of recursive function calls';
COMMENT ON TABLE call_graph_metrics IS 'Stores calculated metrics for call graph analysis';
COMMENT ON TABLE call_graph_analysis_sessions IS 'Tracks call graph analysis sessions and performance';
COMMENT ON TABLE dynamic_call_data IS 'Stores dynamic execution data for function calls';
COMMENT ON TABLE call_graph_layouts IS 'Stores visualization layouts for call graphs';

COMMENT ON COLUMN function_calls.execution_probability IS 'Estimated probability that this call will be executed (0.0-1.0)';
COMMENT ON COLUMN call_graph_metrics.call_frequency_score IS 'Estimated frequency of function calls based on static analysis';
COMMENT ON COLUMN recursive_calls.performance_impact IS 'Estimated performance impact of the recursive pattern';

