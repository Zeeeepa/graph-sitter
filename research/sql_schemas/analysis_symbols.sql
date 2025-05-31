-- analysis_symbols.sql
-- SQL schema for storing Graph-Sitter symbol resolution and metadata

-- Main table for storing symbol definitions
CREATE TABLE symbols (
    id BIGSERIAL PRIMARY KEY,
    codebase_id VARCHAR(255) NOT NULL,
    name VARCHAR(500) NOT NULL,
    qualified_name TEXT NOT NULL, -- Full qualified name including module path
    symbol_type VARCHAR(100) NOT NULL, -- 'function', 'class', 'variable', 'import', 'export', 'parameter', 'attribute'
    file_path TEXT NOT NULL,
    start_line INTEGER NOT NULL,
    start_column INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    end_column INTEGER NOT NULL,
    language VARCHAR(50) NOT NULL,
    scope VARCHAR(200), -- 'global', 'class:ClassName', 'function:FunctionName', etc.
    visibility VARCHAR(50) DEFAULT 'public', -- 'public', 'private', 'protected', 'internal'
    is_exported BOOLEAN DEFAULT FALSE,
    is_imported BOOLEAN DEFAULT FALSE,
    is_abstract BOOLEAN DEFAULT FALSE,
    is_static BOOLEAN DEFAULT FALSE,
    is_async BOOLEAN DEFAULT FALSE,
    source_text TEXT,
    docstring TEXT,
    signature_text TEXT, -- Function/method signature
    return_type VARCHAR(200),
    complexity_score INTEGER DEFAULT 0,
    line_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for storing symbol parameters (for functions/methods)
CREATE TABLE symbol_parameters (
    id BIGSERIAL PRIMARY KEY,
    symbol_id BIGINT NOT NULL REFERENCES symbols(id) ON DELETE CASCADE,
    parameter_name VARCHAR(200) NOT NULL,
    parameter_type VARCHAR(200),
    default_value TEXT,
    is_optional BOOLEAN DEFAULT FALSE,
    is_variadic BOOLEAN DEFAULT FALSE,
    position INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for storing symbol attributes and metadata
CREATE TABLE symbol_attributes (
    id BIGSERIAL PRIMARY KEY,
    symbol_id BIGINT NOT NULL REFERENCES symbols(id) ON DELETE CASCADE,
    attribute_name VARCHAR(200) NOT NULL,
    attribute_value TEXT,
    attribute_type VARCHAR(50) NOT NULL, -- 'string', 'number', 'boolean', 'json', 'type'
    is_inherited BOOLEAN DEFAULT FALSE,
    source_symbol_id BIGINT REFERENCES symbols(id), -- For inherited attributes
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for storing symbol decorators/annotations
CREATE TABLE symbol_decorators (
    id BIGSERIAL PRIMARY KEY,
    symbol_id BIGINT NOT NULL REFERENCES symbols(id) ON DELETE CASCADE,
    decorator_name VARCHAR(200) NOT NULL,
    decorator_arguments TEXT, -- JSON array of arguments
    position INTEGER NOT NULL, -- Order of decorators
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for storing symbol type information
CREATE TABLE symbol_types (
    id BIGSERIAL PRIMARY KEY,
    symbol_id BIGINT NOT NULL REFERENCES symbols(id) ON DELETE CASCADE,
    type_name VARCHAR(200) NOT NULL,
    type_category VARCHAR(100) NOT NULL, -- 'primitive', 'class', 'interface', 'union', 'generic', 'function'
    type_parameters TEXT, -- JSON array for generic types
    is_nullable BOOLEAN DEFAULT FALSE,
    is_optional BOOLEAN DEFAULT FALSE,
    is_array BOOLEAN DEFAULT FALSE,
    array_dimensions INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for storing symbol inheritance relationships
CREATE TABLE symbol_inheritance (
    id BIGSERIAL PRIMARY KEY,
    child_symbol_id BIGINT NOT NULL REFERENCES symbols(id) ON DELETE CASCADE,
    parent_symbol_id BIGINT NOT NULL REFERENCES symbols(id) ON DELETE CASCADE,
    inheritance_type VARCHAR(50) NOT NULL, -- 'extends', 'implements', 'mixin'
    position INTEGER, -- Order for multiple inheritance
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(child_symbol_id, parent_symbol_id, inheritance_type)
);

-- Table for storing symbol scopes and namespaces
CREATE TABLE symbol_scopes (
    id BIGSERIAL PRIMARY KEY,
    codebase_id VARCHAR(255) NOT NULL,
    scope_name VARCHAR(500) NOT NULL,
    scope_type VARCHAR(100) NOT NULL, -- 'global', 'module', 'class', 'function', 'block'
    parent_scope_id BIGINT REFERENCES symbol_scopes(id),
    file_path TEXT NOT NULL,
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for storing symbol scope memberships
CREATE TABLE symbol_scope_memberships (
    id BIGSERIAL PRIMARY KEY,
    symbol_id BIGINT NOT NULL REFERENCES symbols(id) ON DELETE CASCADE,
    scope_id BIGINT NOT NULL REFERENCES symbol_scopes(id) ON DELETE CASCADE,
    is_defined_in_scope BOOLEAN DEFAULT TRUE, -- FALSE for imported symbols
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(symbol_id, scope_id)
);

-- Table for storing symbol resolution cache
CREATE TABLE symbol_resolution_cache (
    id BIGSERIAL PRIMARY KEY,
    codebase_id VARCHAR(255) NOT NULL,
    symbol_reference TEXT NOT NULL, -- The reference as it appears in code
    resolved_symbol_id BIGINT REFERENCES symbols(id) ON DELETE CASCADE,
    context_file_path TEXT NOT NULL,
    context_line INTEGER NOT NULL,
    resolution_confidence DECIMAL(3,2) DEFAULT 1.0, -- 0.0 to 1.0
    resolution_method VARCHAR(100), -- 'exact_match', 'fuzzy_match', 'inference'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    INDEX(codebase_id, symbol_reference, context_file_path)
);

-- Indexes for performance optimization
CREATE INDEX idx_symbols_codebase_name ON symbols(codebase_id, name);
CREATE INDEX idx_symbols_qualified_name ON symbols(qualified_name);
CREATE INDEX idx_symbols_type ON symbols(symbol_type);
CREATE INDEX idx_symbols_file_path ON symbols(file_path);
CREATE INDEX idx_symbols_scope ON symbols(scope);
CREATE INDEX idx_symbols_visibility ON symbols(visibility);
CREATE INDEX idx_symbols_exported ON symbols(is_exported) WHERE is_exported = TRUE;
CREATE INDEX idx_symbols_imported ON symbols(is_imported) WHERE is_imported = TRUE;
CREATE INDEX idx_symbols_complexity ON symbols(complexity_score);

CREATE INDEX idx_symbol_parameters_symbol_id ON symbol_parameters(symbol_id);
CREATE INDEX idx_symbol_parameters_position ON symbol_parameters(symbol_id, position);

CREATE INDEX idx_symbol_attributes_symbol_id ON symbol_attributes(symbol_id);
CREATE INDEX idx_symbol_attributes_name ON symbol_attributes(attribute_name);
CREATE INDEX idx_symbol_attributes_inherited ON symbol_attributes(is_inherited);

CREATE INDEX idx_symbol_decorators_symbol_id ON symbol_decorators(symbol_id);
CREATE INDEX idx_symbol_decorators_name ON symbol_decorators(decorator_name);

CREATE INDEX idx_symbol_types_symbol_id ON symbol_types(symbol_id);
CREATE INDEX idx_symbol_types_category ON symbol_types(type_category);

CREATE INDEX idx_symbol_inheritance_child ON symbol_inheritance(child_symbol_id);
CREATE INDEX idx_symbol_inheritance_parent ON symbol_inheritance(parent_symbol_id);
CREATE INDEX idx_symbol_inheritance_type ON symbol_inheritance(inheritance_type);

CREATE INDEX idx_symbol_scopes_codebase ON symbol_scopes(codebase_id);
CREATE INDEX idx_symbol_scopes_type ON symbol_scopes(scope_type);
CREATE INDEX idx_symbol_scopes_parent ON symbol_scopes(parent_scope_id);

CREATE INDEX idx_symbol_scope_memberships_symbol ON symbol_scope_memberships(symbol_id);
CREATE INDEX idx_symbol_scope_memberships_scope ON symbol_scope_memberships(scope_id);

-- Views for common queries
CREATE VIEW v_symbol_summary AS
SELECT 
    codebase_id,
    symbol_type,
    language,
    COUNT(*) as symbol_count,
    COUNT(*) FILTER (WHERE is_exported = TRUE) as exported_count,
    COUNT(*) FILTER (WHERE is_imported = TRUE) as imported_count,
    AVG(complexity_score) as avg_complexity,
    MAX(complexity_score) as max_complexity
FROM symbols
GROUP BY codebase_id, symbol_type, language;

CREATE VIEW v_function_signatures AS
SELECT 
    s.id,
    s.name,
    s.qualified_name,
    s.signature_text,
    s.return_type,
    s.complexity_score,
    s.is_async,
    COALESCE(
        JSON_AGG(
            JSON_BUILD_OBJECT(
                'name', sp.parameter_name,
                'type', sp.parameter_type,
                'default_value', sp.default_value,
                'is_optional', sp.is_optional,
                'position', sp.position
            ) ORDER BY sp.position
        ) FILTER (WHERE sp.id IS NOT NULL),
        '[]'::json
    ) as parameters
FROM symbols s
LEFT JOIN symbol_parameters sp ON s.id = sp.symbol_id
WHERE s.symbol_type IN ('function', 'method')
GROUP BY s.id, s.name, s.qualified_name, s.signature_text, s.return_type, s.complexity_score, s.is_async;

CREATE VIEW v_class_hierarchy AS
WITH RECURSIVE hierarchy AS (
    -- Base case: classes with no parents
    SELECT 
        s.id,
        s.name,
        s.qualified_name,
        0 as depth,
        ARRAY[s.id] as path
    FROM symbols s
    WHERE s.symbol_type = 'class'
    AND NOT EXISTS (
        SELECT 1 FROM symbol_inheritance si 
        WHERE si.child_symbol_id = s.id
    )
    
    UNION ALL
    
    -- Recursive case: classes with parents
    SELECT 
        s.id,
        s.name,
        s.qualified_name,
        h.depth + 1,
        h.path || s.id
    FROM symbols s
    INNER JOIN symbol_inheritance si ON s.id = si.child_symbol_id
    INNER JOIN hierarchy h ON si.parent_symbol_id = h.id
    WHERE NOT s.id = ANY(h.path) -- Prevent cycles
)
SELECT * FROM hierarchy;

-- Functions for common operations
CREATE OR REPLACE FUNCTION get_symbol_by_reference(
    p_codebase_id VARCHAR(255),
    p_reference TEXT,
    p_context_file TEXT,
    p_context_line INTEGER
)
RETURNS TABLE(
    symbol_id BIGINT,
    name VARCHAR(500),
    qualified_name TEXT,
    symbol_type VARCHAR(100),
    confidence DECIMAL(3,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.id,
        s.name,
        s.qualified_name,
        s.symbol_type,
        COALESCE(src.resolution_confidence, 1.0) as confidence
    FROM symbols s
    LEFT JOIN symbol_resolution_cache src ON s.id = src.resolved_symbol_id
        AND src.codebase_id = p_codebase_id
        AND src.symbol_reference = p_reference
        AND src.context_file_path = p_context_file
    WHERE s.codebase_id = p_codebase_id
    AND (
        s.name = p_reference
        OR s.qualified_name = p_reference
        OR src.symbol_reference = p_reference
    )
    ORDER BY confidence DESC, s.name;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_symbol_children(p_symbol_id BIGINT)
RETURNS TABLE(
    id BIGINT,
    name VARCHAR(500),
    symbol_type VARCHAR(100),
    visibility VARCHAR(50)
) AS $$
BEGIN
    RETURN QUERY
    SELECT s.id, s.name, s.symbol_type, s.visibility
    FROM symbols s
    WHERE s.scope LIKE '%:' || (SELECT name FROM symbols WHERE id = p_symbol_id) || '%'
    OR EXISTS (
        SELECT 1 FROM symbol_scope_memberships ssm
        INNER JOIN symbol_scopes ss ON ssm.scope_id = ss.id
        WHERE ssm.symbol_id = s.id
        AND ss.scope_name = (SELECT name FROM symbols WHERE id = p_symbol_id)
    );
END;
$$ LANGUAGE plpgsql;

-- Triggers for maintaining data consistency
CREATE OR REPLACE FUNCTION update_symbol_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER symbols_update_timestamp
    BEFORE UPDATE ON symbols
    FOR EACH ROW
    EXECUTE FUNCTION update_symbol_timestamp();

-- Function to update qualified names when symbols are moved
CREATE OR REPLACE FUNCTION update_qualified_names()
RETURNS TRIGGER AS $$
BEGIN
    -- Update qualified names for symbols in the affected scope
    UPDATE symbols 
    SET qualified_name = NEW.scope || '.' || name
    WHERE scope = NEW.scope
    AND id != NEW.id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER symbols_update_qualified_names
    AFTER UPDATE OF scope ON symbols
    FOR EACH ROW
    EXECUTE FUNCTION update_qualified_names();

-- Comments for documentation
COMMENT ON TABLE symbols IS 'Stores all symbol definitions found in the codebase';
COMMENT ON TABLE symbol_parameters IS 'Stores parameters for function and method symbols';
COMMENT ON TABLE symbol_attributes IS 'Stores attributes and metadata for symbols';
COMMENT ON TABLE symbol_decorators IS 'Stores decorators/annotations applied to symbols';
COMMENT ON TABLE symbol_types IS 'Stores type information for symbols';
COMMENT ON TABLE symbol_inheritance IS 'Stores inheritance relationships between symbols';
COMMENT ON TABLE symbol_scopes IS 'Stores scope definitions and hierarchies';
COMMENT ON TABLE symbol_scope_memberships IS 'Maps symbols to their containing scopes';
COMMENT ON TABLE symbol_resolution_cache IS 'Caches symbol resolution results for performance';

COMMENT ON COLUMN symbols.qualified_name IS 'Full qualified name including module/namespace path';
COMMENT ON COLUMN symbols.complexity_score IS 'Cyclomatic complexity or similar metric';
COMMENT ON COLUMN symbol_resolution_cache.resolution_confidence IS 'Confidence level of symbol resolution (0.0-1.0)';

