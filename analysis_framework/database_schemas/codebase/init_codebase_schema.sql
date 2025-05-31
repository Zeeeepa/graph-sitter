-- Codebase Database Schema
-- Manages codebase storage, metadata, and structural information

-- Repository information and metadata
CREATE TABLE IF NOT EXISTS repositories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    full_name VARCHAR(500) NOT NULL UNIQUE, -- org/repo format
    url VARCHAR(1000) NOT NULL,
    clone_url VARCHAR(1000),
    ssh_url VARCHAR(1000),
    description TEXT,
    language VARCHAR(100), -- Primary language
    languages JSONB, -- All detected languages with percentages
    default_branch VARCHAR(255) DEFAULT 'main',
    is_private BOOLEAN DEFAULT false,
    is_fork BOOLEAN DEFAULT false,
    fork_parent VARCHAR(500), -- Parent repository if this is a fork
    size_kb INTEGER, -- Repository size in kilobytes
    stars_count INTEGER DEFAULT 0,
    forks_count INTEGER DEFAULT 0,
    watchers_count INTEGER DEFAULT 0,
    open_issues_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_pushed_at TIMESTAMP WITH TIME ZONE,
    last_analyzed_at TIMESTAMP WITH TIME ZONE,
    analysis_status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'analyzing', 'completed', 'failed'
    owner_type VARCHAR(50), -- 'user', 'organization'
    owner_name VARCHAR(255),
    topics TEXT[], -- Repository topics/tags
    license VARCHAR(100),
    readme_content TEXT,
    configuration JSONB, -- Repository-specific analysis configuration
    metadata JSONB -- Additional repository metadata
);

-- Repository branches tracking
CREATE TABLE IF NOT EXISTS repository_branches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    commit_sha VARCHAR(40) NOT NULL,
    is_default BOOLEAN DEFAULT false,
    is_protected BOOLEAN DEFAULT false,
    last_commit_date TIMESTAMP WITH TIME ZONE,
    last_commit_author VARCHAR(255),
    last_commit_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(repository_id, name)
);

-- File system structure and metadata
CREATE TABLE IF NOT EXISTS files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    branch_name VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL, -- Relative path from repository root
    file_name VARCHAR(255) NOT NULL,
    file_extension VARCHAR(50),
    file_type VARCHAR(100), -- 'source', 'config', 'documentation', 'test', 'asset'
    language VARCHAR(100), -- Programming language
    size_bytes INTEGER,
    line_count INTEGER,
    content_hash VARCHAR(64), -- SHA-256 hash of file content
    encoding VARCHAR(50) DEFAULT 'utf-8',
    is_binary BOOLEAN DEFAULT false,
    is_generated BOOLEAN DEFAULT false, -- Auto-generated files
    is_test BOOLEAN DEFAULT false,
    is_documentation BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_modified_at TIMESTAMP WITH TIME ZONE,
    last_modified_by VARCHAR(255),
    permissions VARCHAR(10), -- Unix-style permissions
    metadata JSONB, -- File-specific metadata
    
    UNIQUE(repository_id, branch_name, file_path)
);

-- Directory structure
CREATE TABLE IF NOT EXISTS directories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    branch_name VARCHAR(255) NOT NULL,
    directory_path TEXT NOT NULL, -- Relative path from repository root
    directory_name VARCHAR(255) NOT NULL,
    parent_directory_id UUID REFERENCES directories(id),
    depth_level INTEGER NOT NULL DEFAULT 0,
    file_count INTEGER DEFAULT 0,
    subdirectory_count INTEGER DEFAULT 0,
    total_size_bytes BIGINT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB,
    
    UNIQUE(repository_id, branch_name, directory_path)
);

-- Code symbols (functions, classes, variables, etc.)
CREATE TABLE IF NOT EXISTS symbols (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id UUID NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    symbol_type VARCHAR(100) NOT NULL, -- 'function', 'class', 'variable', 'interface', 'enum', 'constant'
    name VARCHAR(500) NOT NULL,
    qualified_name TEXT, -- Fully qualified name including namespace/module
    signature TEXT, -- Function signature or variable declaration
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    start_column INTEGER,
    end_column INTEGER,
    visibility VARCHAR(50), -- 'public', 'private', 'protected', 'internal'
    is_static BOOLEAN DEFAULT false,
    is_abstract BOOLEAN DEFAULT false,
    is_async BOOLEAN DEFAULT false,
    is_generator BOOLEAN DEFAULT false,
    is_exported BOOLEAN DEFAULT false,
    is_deprecated BOOLEAN DEFAULT false,
    parent_symbol_id UUID REFERENCES symbols(id), -- For nested symbols
    return_type VARCHAR(255),
    parameters JSONB, -- Function parameters with types
    decorators TEXT[], -- Decorators/annotations
    docstring TEXT,
    complexity_score INTEGER, -- Cyclomatic complexity
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB,
    
    CONSTRAINT valid_symbol_type CHECK (symbol_type IN (
        'function', 'method', 'class', 'interface', 'variable', 'constant', 
        'enum', 'type_alias', 'namespace', 'module', 'property', 'field'
    )),
    CONSTRAINT valid_visibility CHECK (visibility IN ('public', 'private', 'protected', 'internal', 'package'))
);

-- Symbol relationships (inheritance, composition, usage, etc.)
CREATE TABLE IF NOT EXISTS symbol_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_symbol_id UUID NOT NULL REFERENCES symbols(id) ON DELETE CASCADE,
    target_symbol_id UUID NOT NULL REFERENCES symbols(id) ON DELETE CASCADE,
    relationship_type VARCHAR(100) NOT NULL,
    relationship_context TEXT, -- Additional context about the relationship
    line_number INTEGER, -- Line where relationship occurs
    confidence_score DECIMAL(3,2) DEFAULT 1.0, -- Confidence in relationship detection
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB,
    
    UNIQUE(source_symbol_id, target_symbol_id, relationship_type),
    CONSTRAINT valid_relationship_type CHECK (relationship_type IN (
        'inherits', 'implements', 'uses', 'calls', 'imports', 'exports',
        'contains', 'overrides', 'references', 'instantiates', 'extends'
    )),
    CONSTRAINT no_self_relationship CHECK (source_symbol_id != target_symbol_id)
);

-- Import and dependency tracking
CREATE TABLE IF NOT EXISTS imports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id UUID NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    import_type VARCHAR(50) NOT NULL, -- 'module', 'package', 'file', 'library'
    import_path TEXT NOT NULL, -- The imported module/file path
    import_name VARCHAR(500), -- Specific imported symbol name
    alias_name VARCHAR(500), -- Import alias if any
    is_relative BOOLEAN DEFAULT false,
    is_wildcard BOOLEAN DEFAULT false, -- import * style imports
    line_number INTEGER,
    resolved_file_id UUID REFERENCES files(id), -- If import resolves to a file in the codebase
    is_external BOOLEAN DEFAULT true, -- External library vs internal module
    package_name VARCHAR(255), -- Package/library name for external imports
    package_version VARCHAR(100), -- Version if available
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB
);

-- External dependencies and packages
CREATE TABLE IF NOT EXISTS dependencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    package_name VARCHAR(255) NOT NULL,
    package_version VARCHAR(100),
    version_constraint VARCHAR(200), -- Version range/constraint
    dependency_type VARCHAR(50) NOT NULL, -- 'runtime', 'development', 'peer', 'optional'
    package_manager VARCHAR(50), -- 'npm', 'pip', 'cargo', 'maven', 'gradle'
    source_file VARCHAR(500), -- File where dependency is declared (package.json, requirements.txt, etc.)
    is_direct BOOLEAN DEFAULT true, -- Direct vs transitive dependency
    is_dev_dependency BOOLEAN DEFAULT false,
    license VARCHAR(100),
    description TEXT,
    homepage_url VARCHAR(1000),
    repository_url VARCHAR(1000),
    vulnerability_count INTEGER DEFAULT 0,
    last_updated TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB,
    
    UNIQUE(repository_id, package_name, dependency_type),
    CONSTRAINT valid_dependency_type CHECK (dependency_type IN (
        'runtime', 'development', 'peer', 'optional', 'build', 'test'
    ))
);

-- Git commit information
CREATE TABLE IF NOT EXISTS commits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
    commit_sha VARCHAR(40) NOT NULL UNIQUE,
    author_name VARCHAR(255),
    author_email VARCHAR(255),
    committer_name VARCHAR(255),
    committer_email VARCHAR(255),
    commit_date TIMESTAMP WITH TIME ZONE NOT NULL,
    message TEXT,
    parent_commits TEXT[], -- Array of parent commit SHAs
    branch_name VARCHAR(255),
    is_merge BOOLEAN DEFAULT false,
    files_changed INTEGER DEFAULT 0,
    insertions INTEGER DEFAULT 0,
    deletions INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB
);

-- File changes in commits
CREATE TABLE IF NOT EXISTS file_changes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    commit_id UUID NOT NULL REFERENCES commits(id) ON DELETE CASCADE,
    file_id UUID REFERENCES files(id), -- May be null for deleted files
    file_path TEXT NOT NULL,
    change_type VARCHAR(50) NOT NULL, -- 'added', 'modified', 'deleted', 'renamed', 'copied'
    old_file_path TEXT, -- For renamed/moved files
    lines_added INTEGER DEFAULT 0,
    lines_deleted INTEGER DEFAULT 0,
    is_binary BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_change_type CHECK (change_type IN ('added', 'modified', 'deleted', 'renamed', 'copied'))
);

-- Code ownership and attribution
CREATE TABLE IF NOT EXISTS code_ownership (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id UUID NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    symbol_id UUID REFERENCES symbols(id), -- Optional: ownership at symbol level
    owner_type VARCHAR(50) NOT NULL, -- 'author', 'team', 'ai_bot'
    owner_identifier VARCHAR(255) NOT NULL, -- Email, username, or team name
    ownership_percentage DECIMAL(5,2) DEFAULT 100.0, -- Percentage of ownership
    last_contribution_date TIMESTAMP WITH TIME ZONE,
    contribution_count INTEGER DEFAULT 1,
    lines_contributed INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_owner_type CHECK (owner_type IN ('author', 'team', 'ai_bot', 'organization')),
    CONSTRAINT valid_percentage CHECK (ownership_percentage >= 0 AND ownership_percentage <= 100)
);

-- Indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_repositories_full_name ON repositories(full_name);
CREATE INDEX IF NOT EXISTS idx_repositories_language ON repositories(language);
CREATE INDEX IF NOT EXISTS idx_repositories_analysis_status ON repositories(analysis_status);
CREATE INDEX IF NOT EXISTS idx_repositories_last_analyzed ON repositories(last_analyzed_at);

CREATE INDEX IF NOT EXISTS idx_files_repository_branch ON files(repository_id, branch_name);
CREATE INDEX IF NOT EXISTS idx_files_file_path ON files(file_path);
CREATE INDEX IF NOT EXISTS idx_files_language ON files(language);
CREATE INDEX IF NOT EXISTS idx_files_file_type ON files(file_type);
CREATE INDEX IF NOT EXISTS idx_files_content_hash ON files(content_hash);

CREATE INDEX IF NOT EXISTS idx_directories_repository_branch ON directories(repository_id, branch_name);
CREATE INDEX IF NOT EXISTS idx_directories_parent ON directories(parent_directory_id);
CREATE INDEX IF NOT EXISTS idx_directories_depth ON directories(depth_level);

CREATE INDEX IF NOT EXISTS idx_symbols_file_id ON symbols(file_id);
CREATE INDEX IF NOT EXISTS idx_symbols_type ON symbols(symbol_type);
CREATE INDEX IF NOT EXISTS idx_symbols_name ON symbols(name);
CREATE INDEX IF NOT EXISTS idx_symbols_qualified_name ON symbols(qualified_name);
CREATE INDEX IF NOT EXISTS idx_symbols_parent ON symbols(parent_symbol_id);
CREATE INDEX IF NOT EXISTS idx_symbols_visibility ON symbols(visibility);

CREATE INDEX IF NOT EXISTS idx_symbol_relationships_source ON symbol_relationships(source_symbol_id);
CREATE INDEX IF NOT EXISTS idx_symbol_relationships_target ON symbol_relationships(target_symbol_id);
CREATE INDEX IF NOT EXISTS idx_symbol_relationships_type ON symbol_relationships(relationship_type);

CREATE INDEX IF NOT EXISTS idx_imports_file_id ON imports(file_id);
CREATE INDEX IF NOT EXISTS idx_imports_path ON imports(import_path);
CREATE INDEX IF NOT EXISTS idx_imports_external ON imports(is_external);
CREATE INDEX IF NOT EXISTS idx_imports_resolved ON imports(resolved_file_id);

CREATE INDEX IF NOT EXISTS idx_dependencies_repository ON dependencies(repository_id);
CREATE INDEX IF NOT EXISTS idx_dependencies_package ON dependencies(package_name);
CREATE INDEX IF NOT EXISTS idx_dependencies_type ON dependencies(dependency_type);
CREATE INDEX IF NOT EXISTS idx_dependencies_manager ON dependencies(package_manager);

CREATE INDEX IF NOT EXISTS idx_commits_repository ON commits(repository_id);
CREATE INDEX IF NOT EXISTS idx_commits_sha ON commits(commit_sha);
CREATE INDEX IF NOT EXISTS idx_commits_date ON commits(commit_date);
CREATE INDEX IF NOT EXISTS idx_commits_author ON commits(author_email);
CREATE INDEX IF NOT EXISTS idx_commits_branch ON commits(branch_name);

CREATE INDEX IF NOT EXISTS idx_file_changes_commit ON file_changes(commit_id);
CREATE INDEX IF NOT EXISTS idx_file_changes_file ON file_changes(file_id);
CREATE INDEX IF NOT EXISTS idx_file_changes_type ON file_changes(change_type);

CREATE INDEX IF NOT EXISTS idx_code_ownership_file ON code_ownership(file_id);
CREATE INDEX IF NOT EXISTS idx_code_ownership_symbol ON code_ownership(symbol_id);
CREATE INDEX IF NOT EXISTS idx_code_ownership_owner ON code_ownership(owner_identifier);

-- Triggers for automatic timestamp updates
CREATE TRIGGER update_repositories_updated_at BEFORE UPDATE ON repositories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_repository_branches_updated_at BEFORE UPDATE ON repository_branches
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_files_updated_at BEFORE UPDATE ON files
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_directories_updated_at BEFORE UPDATE ON directories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_symbols_updated_at BEFORE UPDATE ON symbols
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_code_ownership_updated_at BEFORE UPDATE ON code_ownership
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Views for common queries
CREATE OR REPLACE VIEW repository_summary AS
SELECT 
    r.id,
    r.name,
    r.full_name,
    r.language,
    r.description,
    r.analysis_status,
    r.last_analyzed_at,
    COUNT(DISTINCT f.id) as file_count,
    COUNT(DISTINCT s.id) as symbol_count,
    COUNT(DISTINCT d.id) as dependency_count,
    SUM(f.size_bytes) as total_size_bytes,
    SUM(f.line_count) as total_lines
FROM repositories r
LEFT JOIN files f ON r.id = f.repository_id
LEFT JOIN symbols s ON f.id = s.file_id
LEFT JOIN dependencies d ON r.id = d.repository_id
GROUP BY r.id, r.name, r.full_name, r.language, r.description, r.analysis_status, r.last_analyzed_at;

CREATE OR REPLACE VIEW file_symbol_summary AS
SELECT 
    f.id as file_id,
    f.file_path,
    f.language,
    f.line_count,
    COUNT(s.id) as symbol_count,
    COUNT(CASE WHEN s.symbol_type = 'function' THEN 1 END) as function_count,
    COUNT(CASE WHEN s.symbol_type = 'class' THEN 1 END) as class_count,
    AVG(s.complexity_score) as avg_complexity
FROM files f
LEFT JOIN symbols s ON f.id = s.file_id
GROUP BY f.id, f.file_path, f.language, f.line_count;

CREATE OR REPLACE VIEW dependency_summary AS
SELECT 
    repository_id,
    package_manager,
    dependency_type,
    COUNT(*) as dependency_count,
    COUNT(CASE WHEN vulnerability_count > 0 THEN 1 END) as vulnerable_dependencies
FROM dependencies
GROUP BY repository_id, package_manager, dependency_type;

-- Sample data for testing
INSERT INTO repositories (name, full_name, url, description, language, default_branch) VALUES
('graph-sitter', 'codegen-sh/graph-sitter', 'https://github.com/codegen-sh/graph-sitter', 
 'Code analysis and manipulation framework', 'python', 'develop'),
('example-repo', 'example-org/example-repo', 'https://github.com/example-org/example-repo',
 'Example repository for testing', 'typescript', 'main');

