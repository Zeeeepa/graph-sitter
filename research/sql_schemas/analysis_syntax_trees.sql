-- analysis_syntax_trees.sql
-- SQL schema for storing Graph-Sitter syntax tree analysis results

-- Main table for storing syntax tree nodes
CREATE TABLE syntax_tree_nodes (
    id BIGSERIAL PRIMARY KEY,
    codebase_id VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    node_type VARCHAR(100) NOT NULL,
    parent_id BIGINT REFERENCES syntax_tree_nodes(id),
    start_line INTEGER NOT NULL,
    start_column INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    end_column INTEGER NOT NULL,
    source_text TEXT,
    language VARCHAR(50) NOT NULL,
    depth INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for storing node attributes and metadata
CREATE TABLE syntax_tree_node_attributes (
    id BIGSERIAL PRIMARY KEY,
    node_id BIGINT NOT NULL REFERENCES syntax_tree_nodes(id) ON DELETE CASCADE,
    attribute_name VARCHAR(100) NOT NULL,
    attribute_value TEXT,
    attribute_type VARCHAR(50) NOT NULL, -- 'string', 'number', 'boolean', 'json'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for storing syntax tree relationships
CREATE TABLE syntax_tree_relationships (
    id BIGSERIAL PRIMARY KEY,
    source_node_id BIGINT NOT NULL REFERENCES syntax_tree_nodes(id) ON DELETE CASCADE,
    target_node_id BIGINT NOT NULL REFERENCES syntax_tree_nodes(id) ON DELETE CASCADE,
    relationship_type VARCHAR(100) NOT NULL, -- 'parent', 'sibling', 'reference', 'definition'
    relationship_metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for storing parse errors and warnings
CREATE TABLE syntax_tree_parse_errors (
    id BIGSERIAL PRIMARY KEY,
    codebase_id VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    error_type VARCHAR(100) NOT NULL, -- 'syntax_error', 'warning', 'incomplete_parse'
    error_message TEXT NOT NULL,
    line_number INTEGER,
    column_number INTEGER,
    severity VARCHAR(20) NOT NULL DEFAULT 'error', -- 'error', 'warning', 'info'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table for storing syntax tree analysis sessions
CREATE TABLE syntax_tree_analysis_sessions (
    id BIGSERIAL PRIMARY KEY,
    codebase_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255) NOT NULL UNIQUE,
    language VARCHAR(50) NOT NULL,
    total_files INTEGER NOT NULL DEFAULT 0,
    total_nodes INTEGER NOT NULL DEFAULT 0,
    parse_duration_ms INTEGER,
    analysis_duration_ms INTEGER,
    memory_usage_mb INTEGER,
    status VARCHAR(50) NOT NULL DEFAULT 'in_progress', -- 'in_progress', 'completed', 'failed'
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for performance optimization
CREATE INDEX idx_syntax_tree_nodes_codebase_file ON syntax_tree_nodes(codebase_id, file_path);
CREATE INDEX idx_syntax_tree_nodes_type ON syntax_tree_nodes(node_type);
CREATE INDEX idx_syntax_tree_nodes_parent ON syntax_tree_nodes(parent_id);
CREATE INDEX idx_syntax_tree_nodes_position ON syntax_tree_nodes(start_line, start_column);
CREATE INDEX idx_syntax_tree_nodes_language ON syntax_tree_nodes(language);

CREATE INDEX idx_node_attributes_node_id ON syntax_tree_node_attributes(node_id);
CREATE INDEX idx_node_attributes_name ON syntax_tree_node_attributes(attribute_name);

CREATE INDEX idx_relationships_source ON syntax_tree_relationships(source_node_id);
CREATE INDEX idx_relationships_target ON syntax_tree_relationships(target_node_id);
CREATE INDEX idx_relationships_type ON syntax_tree_relationships(relationship_type);

CREATE INDEX idx_parse_errors_codebase_file ON syntax_tree_parse_errors(codebase_id, file_path);
CREATE INDEX idx_parse_errors_severity ON syntax_tree_parse_errors(severity);

CREATE INDEX idx_analysis_sessions_codebase ON syntax_tree_analysis_sessions(codebase_id);
CREATE INDEX idx_analysis_sessions_status ON syntax_tree_analysis_sessions(status);

-- Views for common queries
CREATE VIEW v_syntax_tree_summary AS
SELECT 
    codebase_id,
    language,
    COUNT(*) as total_nodes,
    COUNT(DISTINCT file_path) as total_files,
    COUNT(DISTINCT node_type) as unique_node_types,
    AVG(depth) as average_depth,
    MAX(depth) as max_depth
FROM syntax_tree_nodes
GROUP BY codebase_id, language;

CREATE VIEW v_parse_error_summary AS
SELECT 
    codebase_id,
    COUNT(*) as total_errors,
    COUNT(*) FILTER (WHERE severity = 'error') as error_count,
    COUNT(*) FILTER (WHERE severity = 'warning') as warning_count,
    COUNT(DISTINCT file_path) as files_with_errors
FROM syntax_tree_parse_errors
GROUP BY codebase_id;

-- Functions for common operations
CREATE OR REPLACE FUNCTION get_node_children(node_id BIGINT)
RETURNS TABLE(
    id BIGINT,
    node_type VARCHAR(100),
    source_text TEXT,
    start_line INTEGER,
    start_column INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT n.id, n.node_type, n.source_text, n.start_line, n.start_column
    FROM syntax_tree_nodes n
    WHERE n.parent_id = node_id
    ORDER BY n.start_line, n.start_column;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_node_ancestors(node_id BIGINT)
RETURNS TABLE(
    id BIGINT,
    node_type VARCHAR(100),
    depth INTEGER
) AS $$
WITH RECURSIVE ancestors AS (
    SELECT id, node_type, depth, parent_id
    FROM syntax_tree_nodes
    WHERE id = node_id
    
    UNION ALL
    
    SELECT n.id, n.node_type, n.depth, n.parent_id
    FROM syntax_tree_nodes n
    INNER JOIN ancestors a ON n.id = a.parent_id
)
SELECT id, node_type, depth
FROM ancestors
WHERE id != node_id
ORDER BY depth;
$$ LANGUAGE sql;

-- Triggers for maintaining data consistency
CREATE OR REPLACE FUNCTION update_syntax_tree_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER syntax_tree_nodes_update_timestamp
    BEFORE UPDATE ON syntax_tree_nodes
    FOR EACH ROW
    EXECUTE FUNCTION update_syntax_tree_timestamp();

-- Comments for documentation
COMMENT ON TABLE syntax_tree_nodes IS 'Stores individual nodes from syntax trees generated by Tree-sitter parsing';
COMMENT ON TABLE syntax_tree_node_attributes IS 'Stores additional attributes and metadata for syntax tree nodes';
COMMENT ON TABLE syntax_tree_relationships IS 'Stores relationships between syntax tree nodes beyond parent-child';
COMMENT ON TABLE syntax_tree_parse_errors IS 'Stores parsing errors and warnings encountered during analysis';
COMMENT ON TABLE syntax_tree_analysis_sessions IS 'Tracks analysis sessions and their performance metrics';

COMMENT ON COLUMN syntax_tree_nodes.codebase_id IS 'Identifier for the codebase being analyzed';
COMMENT ON COLUMN syntax_tree_nodes.depth IS 'Depth of the node in the syntax tree (0 = root)';
COMMENT ON COLUMN syntax_tree_node_attributes.attribute_type IS 'Data type of the attribute value for proper deserialization';
COMMENT ON COLUMN syntax_tree_relationships.relationship_metadata IS 'Additional metadata about the relationship in JSON format';

