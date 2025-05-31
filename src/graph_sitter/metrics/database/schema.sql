-- Advanced Code Metrics Database Schema
-- This schema stores comprehensive code metrics for historical tracking and analysis

-- Codebase metrics table
CREATE TABLE IF NOT EXISTS codebase_metrics (
    id SERIAL PRIMARY KEY,
    project_name VARCHAR(255) NOT NULL,
    git_commit_hash VARCHAR(40),
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Aggregated metrics
    total_files INTEGER DEFAULT 0,
    total_lines INTEGER DEFAULT 0,
    total_logical_lines INTEGER DEFAULT 0,
    total_source_lines INTEGER DEFAULT 0,
    total_comment_lines INTEGER DEFAULT 0,
    total_blank_lines INTEGER DEFAULT 0,
    
    -- Complexity metrics
    total_cyclomatic_complexity INTEGER DEFAULT 0,
    average_cyclomatic_complexity DECIMAL(10,4) DEFAULT 0.0,
    total_halstead_volume DECIMAL(15,4) DEFAULT 0.0,
    average_maintainability_index DECIMAL(10,4) DEFAULT 0.0,
    
    -- Code structure metrics
    total_classes INTEGER DEFAULT 0,
    total_functions INTEGER DEFAULT 0,
    total_imports INTEGER DEFAULT 0,
    total_global_vars INTEGER DEFAULT 0,
    total_interfaces INTEGER DEFAULT 0,
    
    -- Quality metrics
    dead_code_files INTEGER DEFAULT 0,
    test_files INTEGER DEFAULT 0,
    average_test_coverage DECIMAL(5,2) DEFAULT 0.0,
    
    -- Ratios
    comment_ratio DECIMAL(5,4) DEFAULT 0.0,
    test_file_ratio DECIMAL(5,4) DEFAULT 0.0,
    
    -- Language distribution (JSON)
    language_distribution JSONB,
    
    -- Calculation metadata
    calculation_duration DECIMAL(10,4) DEFAULT 0.0,
    errors_count INTEGER DEFAULT 0,
    warnings_count INTEGER DEFAULT 0,
    
    UNIQUE(project_name, git_commit_hash, calculated_at)
);

-- File metrics table
CREATE TABLE IF NOT EXISTS file_metrics (
    id SERIAL PRIMARY KEY,
    codebase_metrics_id INTEGER REFERENCES codebase_metrics(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    language VARCHAR(50),
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Core metrics
    cyclomatic_complexity INTEGER DEFAULT 0,
    maintainability_index DECIMAL(10,4) DEFAULT 0.0,
    
    -- Lines of code metrics
    total_lines INTEGER DEFAULT 0,
    logical_lines INTEGER DEFAULT 0,
    source_lines INTEGER DEFAULT 0,
    comment_lines INTEGER DEFAULT 0,
    blank_lines INTEGER DEFAULT 0,
    
    -- File structure metrics
    class_count INTEGER DEFAULT 0,
    function_count INTEGER DEFAULT 0,
    import_count INTEGER DEFAULT 0,
    global_var_count INTEGER DEFAULT 0,
    interface_count INTEGER DEFAULT 0,
    
    -- Quality metrics
    has_dead_code BOOLEAN DEFAULT FALSE,
    test_coverage DECIMAL(5,2) DEFAULT 0.0,
    is_test_file BOOLEAN DEFAULT FALSE,
    
    -- Ratios
    comment_ratio DECIMAL(5,4) DEFAULT 0.0,
    
    UNIQUE(codebase_metrics_id, file_path)
);

-- Halstead metrics table (separate for normalization)
CREATE TABLE IF NOT EXISTS halstead_metrics (
    id SERIAL PRIMARY KEY,
    
    -- Halstead components
    n1 INTEGER DEFAULT 0,  -- distinct operators
    n2 INTEGER DEFAULT 0,  -- distinct operands
    N1 INTEGER DEFAULT 0,  -- total operators
    N2 INTEGER DEFAULT 0,  -- total operands
    
    -- Calculated values
    vocabulary INTEGER GENERATED ALWAYS AS (n1 + n2) STORED,
    length INTEGER GENERATED ALWAYS AS (N1 + N2) STORED,
    volume DECIMAL(15,4) DEFAULT 0.0,
    difficulty DECIMAL(15,4) DEFAULT 0.0,
    effort DECIMAL(15,4) DEFAULT 0.0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Class metrics table
CREATE TABLE IF NOT EXISTS class_metrics (
    id SERIAL PRIMARY KEY,
    file_metrics_id INTEGER REFERENCES file_metrics(id) ON DELETE CASCADE,
    halstead_metrics_id INTEGER REFERENCES halstead_metrics(id) ON DELETE SET NULL,
    class_name VARCHAR(255) NOT NULL,
    start_line INTEGER,
    end_line INTEGER,
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Core metrics
    cyclomatic_complexity INTEGER DEFAULT 0,
    maintainability_index DECIMAL(10,4) DEFAULT 0.0,
    
    -- Lines of code metrics
    total_lines INTEGER DEFAULT 0,
    logical_lines INTEGER DEFAULT 0,
    source_lines INTEGER DEFAULT 0,
    comment_lines INTEGER DEFAULT 0,
    blank_lines INTEGER DEFAULT 0,
    
    -- Class-specific metrics
    method_count INTEGER DEFAULT 0,
    attribute_count INTEGER DEFAULT 0,
    depth_of_inheritance INTEGER DEFAULT 0,
    number_of_children INTEGER DEFAULT 0,
    
    -- Quality metrics
    has_dead_methods BOOLEAN DEFAULT FALSE,
    
    -- Ratios
    comment_ratio DECIMAL(5,4) DEFAULT 0.0,
    
    UNIQUE(file_metrics_id, class_name)
);

-- Function metrics table
CREATE TABLE IF NOT EXISTS function_metrics (
    id SERIAL PRIMARY KEY,
    file_metrics_id INTEGER REFERENCES file_metrics(id) ON DELETE CASCADE,
    class_metrics_id INTEGER REFERENCES class_metrics(id) ON DELETE CASCADE,
    halstead_metrics_id INTEGER REFERENCES halstead_metrics(id) ON DELETE SET NULL,
    function_name VARCHAR(255) NOT NULL,
    start_line INTEGER,
    end_line INTEGER,
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Core metrics
    cyclomatic_complexity INTEGER DEFAULT 0,
    maintainability_index DECIMAL(10,4) DEFAULT 0.0,
    
    -- Lines of code metrics
    total_lines INTEGER DEFAULT 0,
    logical_lines INTEGER DEFAULT 0,
    source_lines INTEGER DEFAULT 0,
    comment_lines INTEGER DEFAULT 0,
    blank_lines INTEGER DEFAULT 0,
    
    -- Function-specific metrics
    parameter_count INTEGER DEFAULT 0,
    return_statement_count INTEGER DEFAULT 0,
    function_call_count INTEGER DEFAULT 0,
    nesting_depth INTEGER DEFAULT 0,
    
    -- Quality metrics
    is_recursive BOOLEAN DEFAULT FALSE,
    is_dead_code BOOLEAN DEFAULT FALSE,
    has_unused_parameters BOOLEAN DEFAULT FALSE,
    
    -- Context metrics
    call_site_count INTEGER DEFAULT 0,
    dependency_count INTEGER DEFAULT 0,
    
    -- Ratios
    comment_ratio DECIMAL(5,4) DEFAULT 0.0,
    complexity_per_line DECIMAL(10,4) DEFAULT 0.0,
    
    UNIQUE(file_metrics_id, function_name, start_line)
);

-- Metrics trends table for historical analysis
CREATE TABLE IF NOT EXISTS metrics_trends (
    id SERIAL PRIMARY KEY,
    project_name VARCHAR(255) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,4),
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    git_commit_hash VARCHAR(40),
    
    -- Trend analysis
    previous_value DECIMAL(15,4),
    change_amount DECIMAL(15,4),
    change_percentage DECIMAL(10,4),
    trend_direction VARCHAR(20), -- 'increasing', 'decreasing', 'stable'
    
    INDEX(project_name, metric_name, calculated_at)
);

-- Quality thresholds table for configurable quality gates
CREATE TABLE IF NOT EXISTS quality_thresholds (
    id SERIAL PRIMARY KEY,
    project_name VARCHAR(255),
    metric_name VARCHAR(100) NOT NULL,
    
    -- Threshold values
    excellent_min DECIMAL(15,4),
    good_min DECIMAL(15,4),
    acceptable_min DECIMAL(15,4),
    poor_max DECIMAL(15,4),
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(project_name, metric_name)
);

-- Metrics calculation jobs table for tracking background processing
CREATE TABLE IF NOT EXISTS metrics_calculation_jobs (
    id SERIAL PRIMARY KEY,
    project_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed'
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Job configuration
    calculators_enabled TEXT[], -- Array of calculator names
    git_commit_hash VARCHAR(40),
    
    -- Results
    codebase_metrics_id INTEGER REFERENCES codebase_metrics(id) ON DELETE SET NULL,
    files_processed INTEGER DEFAULT 0,
    errors_count INTEGER DEFAULT 0,
    warnings_count INTEGER DEFAULT 0,
    
    -- Error details
    error_message TEXT,
    error_details JSONB,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_codebase_metrics_project_time ON codebase_metrics(project_name, calculated_at DESC);
CREATE INDEX IF NOT EXISTS idx_file_metrics_codebase ON file_metrics(codebase_metrics_id);
CREATE INDEX IF NOT EXISTS idx_file_metrics_language ON file_metrics(language);
CREATE INDEX IF NOT EXISTS idx_class_metrics_file ON class_metrics(file_metrics_id);
CREATE INDEX IF NOT EXISTS idx_function_metrics_file ON function_metrics(file_metrics_id);
CREATE INDEX IF NOT EXISTS idx_function_metrics_class ON function_metrics(class_metrics_id);
CREATE INDEX IF NOT EXISTS idx_metrics_trends_project_metric ON metrics_trends(project_name, metric_name);
CREATE INDEX IF NOT EXISTS idx_quality_thresholds_project ON quality_thresholds(project_name);
CREATE INDEX IF NOT EXISTS idx_calculation_jobs_status ON metrics_calculation_jobs(status, created_at);

-- Views for common queries

-- Latest metrics per project
CREATE OR REPLACE VIEW latest_codebase_metrics AS
SELECT DISTINCT ON (project_name) *
FROM codebase_metrics
ORDER BY project_name, calculated_at DESC;

-- File metrics with latest codebase context
CREATE OR REPLACE VIEW latest_file_metrics AS
SELECT fm.*, cm.project_name, cm.git_commit_hash
FROM file_metrics fm
JOIN latest_codebase_metrics cm ON fm.codebase_metrics_id = cm.id;

-- Function complexity summary
CREATE OR REPLACE VIEW function_complexity_summary AS
SELECT 
    fm.function_name,
    fm.cyclomatic_complexity,
    fm.maintainability_index,
    fm.total_lines,
    fm.comment_ratio,
    file_m.file_path,
    file_m.language,
    cb.project_name
FROM function_metrics fm
JOIN file_metrics file_m ON fm.file_metrics_id = file_m.id
JOIN codebase_metrics cb ON file_m.codebase_metrics_id = cb.id;

-- Class inheritance analysis
CREATE OR REPLACE VIEW class_inheritance_analysis AS
SELECT 
    cm.class_name,
    cm.depth_of_inheritance,
    cm.number_of_children,
    cm.method_count,
    cm.cyclomatic_complexity,
    fm.file_path,
    cb.project_name
FROM class_metrics cm
JOIN file_metrics fm ON cm.file_metrics_id = fm.id
JOIN codebase_metrics cb ON fm.codebase_metrics_id = cb.id;

-- Quality metrics dashboard
CREATE OR REPLACE VIEW quality_dashboard AS
SELECT 
    project_name,
    calculated_at,
    average_cyclomatic_complexity,
    average_maintainability_index,
    comment_ratio,
    test_file_ratio,
    average_test_coverage,
    dead_code_files,
    total_files,
    CASE 
        WHEN average_maintainability_index >= 85 THEN 'Excellent'
        WHEN average_maintainability_index >= 65 THEN 'Good'
        WHEN average_maintainability_index >= 45 THEN 'Acceptable'
        ELSE 'Poor'
    END as maintainability_rating,
    CASE 
        WHEN average_cyclomatic_complexity <= 5 THEN 'Low'
        WHEN average_cyclomatic_complexity <= 10 THEN 'Moderate'
        WHEN average_cyclomatic_complexity <= 20 THEN 'High'
        ELSE 'Very High'
    END as complexity_rating
FROM latest_codebase_metrics;

-- Triggers for automatic trend calculation
CREATE OR REPLACE FUNCTION update_metrics_trends()
RETURNS TRIGGER AS $$
BEGIN
    -- Insert trend data for key metrics
    INSERT INTO metrics_trends (
        project_name, 
        metric_name, 
        metric_value, 
        calculated_at, 
        git_commit_hash,
        previous_value,
        change_amount,
        change_percentage,
        trend_direction
    )
    SELECT 
        NEW.project_name,
        'average_cyclomatic_complexity',
        NEW.average_cyclomatic_complexity,
        NEW.calculated_at,
        NEW.git_commit_hash,
        prev.average_cyclomatic_complexity,
        NEW.average_cyclomatic_complexity - COALESCE(prev.average_cyclomatic_complexity, 0),
        CASE 
            WHEN COALESCE(prev.average_cyclomatic_complexity, 0) > 0 
            THEN ((NEW.average_cyclomatic_complexity - prev.average_cyclomatic_complexity) / prev.average_cyclomatic_complexity) * 100
            ELSE 0
        END,
        CASE 
            WHEN NEW.average_cyclomatic_complexity > COALESCE(prev.average_cyclomatic_complexity, 0) THEN 'increasing'
            WHEN NEW.average_cyclomatic_complexity < COALESCE(prev.average_cyclomatic_complexity, 0) THEN 'decreasing'
            ELSE 'stable'
        END
    FROM (
        SELECT average_cyclomatic_complexity
        FROM codebase_metrics 
        WHERE project_name = NEW.project_name 
        AND calculated_at < NEW.calculated_at
        ORDER BY calculated_at DESC 
        LIMIT 1
    ) prev;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_metrics_trends
    AFTER INSERT ON codebase_metrics
    FOR EACH ROW
    EXECUTE FUNCTION update_metrics_trends();

