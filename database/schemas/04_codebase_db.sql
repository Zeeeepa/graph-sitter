-- =============================================================================
-- CODEBASE DATABASE SCHEMA: Analysis Results, Metadata, and Functions
-- =============================================================================
-- This database handles code analysis results, metadata, functions, and
-- relationships. Integrates with existing codebase_analysis.py and adapters.
-- =============================================================================

-- Connect to codebase_db
\c codebase_db;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- Set timezone and configuration
SET timezone = 'UTC';
SET default_text_search_config = 'pg_catalog.english';

-- Grant all privileges to codebase_user
GRANT ALL PRIVILEGES ON DATABASE codebase_db TO codebase_user;
GRANT ALL PRIVILEGES ON SCHEMA public TO codebase_user;

-- Codebase-specific enums
CREATE TYPE symbol_type AS ENUM (
    'function',
    'class',
    'method',
    'variable',
    'constant',
    'interface',
    'enum',
    'type',
    'module',
    'namespace',
    'property',
    'field',
    'parameter',
    'import',
    'export'
);

CREATE TYPE edge_type AS ENUM (
    'calls',
    'imports',
    'inherits',
    'implements',
    'uses',
    'defines',
    'references',
    'contains',
    'depends_on',
    'overrides',
    'extends'
);

CREATE TYPE analysis_status AS ENUM (
    'pending',
    'running',
    'completed',
    'failed',
    'partial',
    'cancelled'
);

CREATE TYPE file_type AS ENUM (
    'source',
    'test',
    'config',
    'documentation',
    'build',
    'data',
    'binary',
    'unknown'
);

CREATE TYPE complexity_level AS ENUM (
    'low',
    'medium',
    'high',
    'very_high',
    'extreme'
);

-- =============================================================================
-- CORE REFERENCE TABLES
-- =============================================================================

-- Organizations table for multi-tenancy
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Users table for analysis tracking
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(50) DEFAULT 'member',
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- CODEBASE MANAGEMENT
-- =============================================================================

-- Main codebases table
CREATE TABLE codebases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Codebase identification
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Repository information
    repository_url TEXT,
    repository_type VARCHAR(50) DEFAULT 'git',
    branch VARCHAR(100) DEFAULT 'main',
    commit_hash VARCHAR(40),
    
    -- Codebase metadata
    language VARCHAR(50),
    languages JSONB DEFAULT '{}', -- Language breakdown
    framework VARCHAR(100),
    
    -- Analysis configuration
    analysis_config JSONB DEFAULT '{}',
    include_patterns JSONB DEFAULT '[]',
    exclude_patterns JSONB DEFAULT '[]',
    
    -- Codebase statistics
    total_files INTEGER DEFAULT 0,
    total_lines INTEGER DEFAULT 0,
    total_functions INTEGER DEFAULT 0,
    total_classes INTEGER DEFAULT 0,
    
    -- Quality metrics
    complexity_score DECIMAL(5,2),
    maintainability_index DECIMAL(5,2),
    technical_debt_ratio DECIMAL(5,2),
    
    -- Analysis status
    last_analyzed_at TIMESTAMP WITH TIME ZONE,
    analysis_status analysis_status DEFAULT 'pending',
    
    -- External references
    external_codebase_id VARCHAR(255),
    
    -- Metadata
    tags VARCHAR(50)[],
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT codebases_name_org_unique UNIQUE (organization_id, name),
    CONSTRAINT codebases_name_not_empty CHECK (length(trim(name)) > 0),
    CONSTRAINT codebases_stats_positive CHECK (
        total_files >= 0 AND 
        total_lines >= 0 AND 
        total_functions >= 0 AND 
        total_classes >= 0
    )
);

-- =============================================================================
-- FILE ANALYSIS
-- =============================================================================

-- File analysis results
CREATE TABLE file_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    codebase_id UUID NOT NULL REFERENCES codebases(id) ON DELETE CASCADE,
    
    -- File identification
    file_path TEXT NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_extension VARCHAR(20),
    file_type file_type DEFAULT 'source',
    
    -- File content metadata
    file_size_bytes INTEGER,
    line_count INTEGER,
    character_count INTEGER,
    
    -- Language and syntax
    language VARCHAR(50),
    syntax_tree JSONB, -- AST representation
    
    -- Code metrics
    complexity_score DECIMAL(5,2),
    maintainability_index DECIMAL(5,2),
    cyclomatic_complexity INTEGER,
    cognitive_complexity INTEGER,
    
    -- Quality metrics
    code_coverage DECIMAL(5,2),
    test_coverage DECIMAL(5,2),
    documentation_coverage DECIMAL(5,2),
    
    -- Dependencies and imports
    imports JSONB DEFAULT '[]',
    exports JSONB DEFAULT '[]',
    dependencies JSONB DEFAULT '[]',
    
    -- Code structure
    functions_count INTEGER DEFAULT 0,
    classes_count INTEGER DEFAULT 0,
    variables_count INTEGER DEFAULT 0,
    
    -- Analysis results
    issues JSONB DEFAULT '[]', -- Code issues and warnings
    suggestions JSONB DEFAULT '[]', -- Improvement suggestions
    
    -- File hash for change detection
    content_hash VARCHAR(64), -- SHA-256 hash
    
    -- Analysis metadata
    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    analysis_version VARCHAR(50),
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT file_analysis_codebase_path_unique UNIQUE (codebase_id, file_path),
    CONSTRAINT file_analysis_metrics_valid CHECK (
        file_size_bytes >= 0 AND 
        line_count >= 0 AND 
        character_count >= 0 AND
        functions_count >= 0 AND
        classes_count >= 0 AND
        variables_count >= 0
    )
);

-- =============================================================================
-- CODE ELEMENTS (SYMBOLS)
-- =============================================================================

-- Code elements (functions, classes, variables, etc.)
CREATE TABLE code_elements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    codebase_id UUID NOT NULL REFERENCES codebases(id) ON DELETE CASCADE,
    file_analysis_id UUID NOT NULL REFERENCES file_analysis(id) ON DELETE CASCADE,
    
    -- Element identification
    name VARCHAR(255) NOT NULL,
    qualified_name TEXT, -- Full qualified name
    symbol_type symbol_type NOT NULL,
    
    -- Element location
    file_path TEXT NOT NULL,
    start_line INTEGER,
    end_line INTEGER,
    start_column INTEGER,
    end_column INTEGER,
    
    -- Element signature and definition
    signature TEXT,
    definition TEXT,
    documentation TEXT,
    
    -- Element hierarchy
    parent_element_id UUID REFERENCES code_elements(id),
    namespace VARCHAR(255),
    scope VARCHAR(100),
    
    -- Element properties
    visibility VARCHAR(20), -- public, private, protected, internal
    is_static BOOLEAN DEFAULT false,
    is_abstract BOOLEAN DEFAULT false,
    is_async BOOLEAN DEFAULT false,
    is_deprecated BOOLEAN DEFAULT false,
    
    -- Complexity metrics
    complexity_score DECIMAL(5,2),
    cyclomatic_complexity INTEGER,
    cognitive_complexity INTEGER,
    lines_of_code INTEGER,
    
    -- Usage statistics
    reference_count INTEGER DEFAULT 0,
    call_count INTEGER DEFAULT 0,
    
    -- Type information
    return_type VARCHAR(255),
    parameter_types JSONB DEFAULT '[]',
    generic_types JSONB DEFAULT '[]',
    
    -- Analysis metadata
    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT code_elements_name_not_empty CHECK (length(trim(name)) > 0),
    CONSTRAINT code_elements_line_numbers_valid CHECK (
        start_line > 0 AND 
        end_line >= start_line AND
        start_column >= 0 AND
        end_column >= start_column
    ),
    CONSTRAINT code_elements_complexity_positive CHECK (
        complexity_score >= 0 AND
        cyclomatic_complexity >= 0 AND
        cognitive_complexity >= 0 AND
        lines_of_code >= 0
    )
);

-- =============================================================================
-- RELATIONSHIPS AND DEPENDENCIES
-- =============================================================================

-- Relationships between code elements
CREATE TABLE relationships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    codebase_id UUID NOT NULL REFERENCES codebases(id) ON DELETE CASCADE,
    
    -- Relationship endpoints
    source_element_id UUID NOT NULL REFERENCES code_elements(id) ON DELETE CASCADE,
    target_element_id UUID NOT NULL REFERENCES code_elements(id) ON DELETE CASCADE,
    
    -- Relationship details
    edge_type edge_type NOT NULL,
    relationship_strength DECIMAL(5,2) DEFAULT 1.0, -- 0.0 to 100.0
    
    -- Relationship context
    context TEXT, -- Where/how the relationship occurs
    line_number INTEGER, -- Line where relationship is defined
    
    -- Relationship metadata
    is_direct BOOLEAN DEFAULT true,
    is_conditional BOOLEAN DEFAULT false,
    frequency INTEGER DEFAULT 1, -- How often this relationship occurs
    
    -- Analysis metadata
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT relationships_unique UNIQUE (source_element_id, target_element_id, edge_type),
    CONSTRAINT relationships_no_self_reference CHECK (source_element_id != target_element_id),
    CONSTRAINT relationships_strength_valid CHECK (relationship_strength >= 0 AND relationship_strength <= 100)
);

-- External dependencies (libraries, frameworks, etc.)
CREATE TABLE external_dependencies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    codebase_id UUID NOT NULL REFERENCES codebases(id) ON DELETE CASCADE,
    
    -- Dependency identification
    name VARCHAR(255) NOT NULL,
    version VARCHAR(100),
    package_manager VARCHAR(50), -- npm, pip, maven, etc.
    
    -- Dependency details
    description TEXT,
    license VARCHAR(100),
    homepage_url TEXT,
    repository_url TEXT,
    
    -- Usage tracking
    usage_count INTEGER DEFAULT 0,
    first_used_at TIMESTAMP WITH TIME ZONE,
    last_used_at TIMESTAMP WITH TIME ZONE,
    
    -- Security and quality
    vulnerability_count INTEGER DEFAULT 0,
    security_score DECIMAL(5,2),
    maintenance_score DECIMAL(5,2),
    
    -- Dependency metadata
    is_dev_dependency BOOLEAN DEFAULT false,
    is_optional BOOLEAN DEFAULT false,
    is_deprecated BOOLEAN DEFAULT false,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT external_dependencies_name_codebase_unique UNIQUE (codebase_id, name, version),
    CONSTRAINT external_dependencies_name_not_empty CHECK (length(trim(name)) > 0)
);

-- =============================================================================
-- ANALYSIS RUNS AND HISTORY
-- =============================================================================

-- Analysis runs for tracking analysis history
CREATE TABLE analysis_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    codebase_id UUID NOT NULL REFERENCES codebases(id) ON DELETE CASCADE,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    
    -- Run identification
    run_name VARCHAR(255),
    run_type VARCHAR(100) DEFAULT 'full', -- full, incremental, targeted
    
    -- Run configuration
    analysis_config JSONB DEFAULT '{}',
    include_patterns JSONB DEFAULT '[]',
    exclude_patterns JSONB DEFAULT '[]',
    
    -- Run status and progress
    status analysis_status DEFAULT 'pending',
    progress_percentage DECIMAL(5,2) DEFAULT 0,
    
    -- Timing
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    
    -- Results summary
    files_analyzed INTEGER DEFAULT 0,
    elements_found INTEGER DEFAULT 0,
    relationships_found INTEGER DEFAULT 0,
    issues_found INTEGER DEFAULT 0,
    
    -- Quality metrics
    overall_complexity DECIMAL(5,2),
    overall_maintainability DECIMAL(5,2),
    technical_debt_hours DECIMAL(8,2),
    
    -- Error handling
    error_message TEXT,
    warnings JSONB DEFAULT '[]',
    
    -- Triggered by
    triggered_by UUID REFERENCES users(id),
    trigger_source VARCHAR(100), -- manual, scheduled, webhook, api
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT analysis_runs_progress_valid CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
    CONSTRAINT analysis_runs_counts_positive CHECK (
        files_analyzed >= 0 AND 
        elements_found >= 0 AND 
        relationships_found >= 0 AND 
        issues_found >= 0
    )
);

-- =============================================================================
-- INDEXES FOR OPTIMAL PERFORMANCE
-- =============================================================================

-- Codebases indexes
CREATE INDEX idx_codebases_org_id ON codebases(organization_id);
CREATE INDEX idx_codebases_language ON codebases(language);
CREATE INDEX idx_codebases_analysis_status ON codebases(analysis_status);
CREATE INDEX idx_codebases_last_analyzed ON codebases(last_analyzed_at);

-- File analysis indexes
CREATE INDEX idx_file_analysis_codebase_id ON file_analysis(codebase_id);
CREATE INDEX idx_file_analysis_file_path ON file_analysis(file_path);
CREATE INDEX idx_file_analysis_file_type ON file_analysis(file_type);
CREATE INDEX idx_file_analysis_language ON file_analysis(language);
CREATE INDEX idx_file_analysis_complexity ON file_analysis(complexity_score);

-- Code elements indexes
CREATE INDEX idx_code_elements_codebase_id ON code_elements(codebase_id);
CREATE INDEX idx_code_elements_file_analysis_id ON code_elements(file_analysis_id);
CREATE INDEX idx_code_elements_symbol_type ON code_elements(symbol_type);
CREATE INDEX idx_code_elements_name ON code_elements(name);
CREATE INDEX idx_code_elements_qualified_name ON code_elements(qualified_name);
CREATE INDEX idx_code_elements_parent_id ON code_elements(parent_element_id);
CREATE INDEX idx_code_elements_file_path ON code_elements(file_path);
CREATE INDEX idx_code_elements_complexity ON code_elements(complexity_score);

-- Relationships indexes
CREATE INDEX idx_relationships_codebase_id ON relationships(codebase_id);
CREATE INDEX idx_relationships_source_id ON relationships(source_element_id);
CREATE INDEX idx_relationships_target_id ON relationships(target_element_id);
CREATE INDEX idx_relationships_edge_type ON relationships(edge_type);
CREATE INDEX idx_relationships_strength ON relationships(relationship_strength);

-- External dependencies indexes
CREATE INDEX idx_external_dependencies_codebase_id ON external_dependencies(codebase_id);
CREATE INDEX idx_external_dependencies_name ON external_dependencies(name);
CREATE INDEX idx_external_dependencies_package_manager ON external_dependencies(package_manager);

-- Analysis runs indexes
CREATE INDEX idx_analysis_runs_codebase_id ON analysis_runs(codebase_id);
CREATE INDEX idx_analysis_runs_org_id ON analysis_runs(organization_id);
CREATE INDEX idx_analysis_runs_status ON analysis_runs(status);
CREATE INDEX idx_analysis_runs_started_at ON analysis_runs(started_at);
CREATE INDEX idx_analysis_runs_triggered_by ON analysis_runs(triggered_by);

-- GIN indexes for JSONB fields
CREATE INDEX idx_codebases_languages_gin USING gin (languages);
CREATE INDEX idx_file_analysis_syntax_tree_gin USING gin (syntax_tree);
CREATE INDEX idx_file_analysis_imports_gin USING gin (imports);
CREATE INDEX idx_code_elements_metadata_gin USING gin (metadata);

-- Full-text search indexes
CREATE INDEX idx_code_elements_name_trgm USING gin (name gin_trgm_ops);
CREATE INDEX idx_code_elements_qualified_name_trgm USING gin (qualified_name gin_trgm_ops);

-- =============================================================================
-- VIEWS FOR COMMON QUERIES
-- =============================================================================

-- Codebase overview
CREATE VIEW codebase_overview AS
SELECT 
    c.*,
    o.name as organization_name,
    COUNT(DISTINCT fa.id) as analyzed_files,
    COUNT(DISTINCT ce.id) as total_elements,
    COUNT(DISTINCT r.id) as total_relationships,
    AVG(fa.complexity_score) as avg_file_complexity,
    MAX(ar.completed_at) as last_analysis_completed
FROM codebases c
JOIN organizations o ON c.organization_id = o.id
LEFT JOIN file_analysis fa ON c.id = fa.codebase_id
LEFT JOIN code_elements ce ON c.id = ce.codebase_id
LEFT JOIN relationships r ON c.id = r.codebase_id
LEFT JOIN analysis_runs ar ON c.id = ar.codebase_id AND ar.status = 'completed'
WHERE c.deleted_at IS NULL
GROUP BY c.id, o.name;

-- Code complexity analysis
CREATE VIEW code_complexity_analysis AS
SELECT 
    ce.codebase_id,
    ce.symbol_type,
    COUNT(*) as element_count,
    AVG(ce.complexity_score) as avg_complexity,
    MAX(ce.complexity_score) as max_complexity,
    COUNT(CASE WHEN ce.complexity_score > 10 THEN 1 END) as high_complexity_count
FROM code_elements ce
GROUP BY ce.codebase_id, ce.symbol_type;

-- Dependency analysis
CREATE VIEW dependency_analysis AS
SELECT 
    c.id as codebase_id,
    c.name as codebase_name,
    COUNT(ed.id) as total_dependencies,
    COUNT(CASE WHEN ed.is_dev_dependency = false THEN 1 END) as production_dependencies,
    COUNT(CASE WHEN ed.vulnerability_count > 0 THEN 1 END) as vulnerable_dependencies,
    AVG(ed.security_score) as avg_security_score
FROM codebases c
LEFT JOIN external_dependencies ed ON c.id = ed.codebase_id
WHERE c.deleted_at IS NULL
GROUP BY c.id, c.name;

-- Grant permissions to codebase_user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO codebase_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO codebase_user;
GRANT USAGE ON SCHEMA public TO codebase_user;

-- Insert default organization
INSERT INTO organizations (name, slug, description) VALUES 
('Default Organization', 'default', 'Default organization for codebase analysis');

-- Insert default admin user
INSERT INTO users (organization_id, name, email, role) VALUES 
((SELECT id FROM organizations WHERE slug = 'default'), 'Codebase Admin', 'admin@codebase.local', 'admin');

-- Final status message
DO $$
BEGIN
    RAISE NOTICE '🔍 Codebase Database initialized successfully!';
    RAISE NOTICE 'Features: Code analysis, Symbol tracking, Relationship mapping, Dependency management';
    RAISE NOTICE 'Integration: Compatible with existing codebase_analysis.py and adapters';
    RAISE NOTICE 'Timestamp: %', NOW();
END $$;

