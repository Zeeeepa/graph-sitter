-- Enhanced Database Schema: Integration and Migration Scripts
-- Part 5: Integration with Existing Schema and Migration Management

-- Schema Version Management
CREATE TABLE schema_migrations (
    version VARCHAR(50) PRIMARY KEY,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    description TEXT,
    migration_type VARCHAR(50) DEFAULT 'enhancement', -- 'enhancement', 'bugfix', 'rollback'
    rollback_script TEXT, -- SQL to rollback this migration
    checksum VARCHAR(64), -- Checksum of migration script
    execution_time_ms INTEGER,
    applied_by VARCHAR(255) DEFAULT current_user
);

-- Integration Tables for Existing 7-Module Schema

-- Git Operation Learning Events Integration
CREATE TABLE git_operation_learning_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    git_operation_id VARCHAR(255) NOT NULL, -- Links to existing git operation tracking
    learning_event_id UUID NOT NULL REFERENCES learning_events(id) ON DELETE CASCADE,
    operation_type VARCHAR(100), -- 'commit', 'merge', 'rebase', 'pull_request', 'branch'
    repository_id VARCHAR(255),
    repository_name VARCHAR(255),
    branch_name VARCHAR(255),
    commit_hash VARCHAR(40),
    author_id VARCHAR(255),
    file_changes_count INTEGER,
    lines_added INTEGER,
    lines_deleted INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CHECK (operation_type IN ('commit', 'merge', 'rebase', 'pull_request', 'branch', 'tag')),
    CHECK (file_changes_count >= 0),
    CHECK (lines_added >= 0),
    CHECK (lines_deleted >= 0)
);

-- Indexes for git_operation_learning_events
CREATE INDEX idx_git_learning_events_operation ON git_operation_learning_events(git_operation_id);
CREATE INDEX idx_git_learning_events_repo ON git_operation_learning_events(repository_id);
CREATE INDEX idx_git_learning_events_learning ON git_operation_learning_events(learning_event_id);
CREATE INDEX idx_git_learning_events_author ON git_operation_learning_events(author_id);

-- User Session Learning Events Integration
CREATE TABLE user_session_learning_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) NOT NULL, -- Links to existing session tracking
    learning_event_id UUID NOT NULL REFERENCES learning_events(id) ON DELETE CASCADE,
    user_id VARCHAR(255) NOT NULL,
    session_start TIMESTAMP WITH TIME ZONE,
    session_end TIMESTAMP WITH TIME ZONE,
    session_duration_ms INTEGER,
    actions_count INTEGER DEFAULT 0,
    platform VARCHAR(100), -- 'web', 'cli', 'api', 'ide_extension'
    user_agent TEXT,
    ip_address INET,
    geographic_location JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CHECK (session_duration_ms >= 0),
    CHECK (actions_count >= 0),
    CHECK (platform IN ('web', 'cli', 'api', 'ide_extension', 'mobile'))
);

-- Indexes for user_session_learning_events
CREATE INDEX idx_user_session_learning_session ON user_session_learning_events(session_id);
CREATE INDEX idx_user_session_learning_user ON user_session_learning_events(user_id);
CREATE INDEX idx_user_session_learning_event ON user_session_learning_events(learning_event_id);
CREATE INDEX idx_user_session_learning_platform ON user_session_learning_events(platform);

-- API Request Learning Events Integration
CREATE TABLE api_request_learning_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id VARCHAR(255) NOT NULL, -- Links to existing API request tracking
    learning_event_id UUID NOT NULL REFERENCES learning_events(id) ON DELETE CASCADE,
    endpoint VARCHAR(255),
    http_method VARCHAR(10),
    status_code INTEGER,
    response_time_ms INTEGER,
    request_size_bytes INTEGER,
    response_size_bytes INTEGER,
    user_id VARCHAR(255),
    api_key_id VARCHAR(255),
    rate_limit_remaining INTEGER,
    error_type VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CHECK (http_method IN ('GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS')),
    CHECK (status_code >= 100 AND status_code < 600),
    CHECK (response_time_ms >= 0),
    CHECK (request_size_bytes >= 0),
    CHECK (response_size_bytes >= 0)
);

-- Indexes for api_request_learning_events
CREATE INDEX idx_api_learning_request ON api_request_learning_events(request_id);
CREATE INDEX idx_api_learning_event ON api_request_learning_events(learning_event_id);
CREATE INDEX idx_api_learning_endpoint ON api_request_learning_events(endpoint);
CREATE INDEX idx_api_learning_user ON api_request_learning_events(user_id);
CREATE INDEX idx_api_learning_status ON api_request_learning_events(status_code);

-- Code Analysis Learning Events Integration
CREATE TABLE code_analysis_learning_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id VARCHAR(255) NOT NULL, -- Links to existing code analysis tracking
    learning_event_id UUID NOT NULL REFERENCES learning_events(id) ON DELETE CASCADE,
    analysis_type VARCHAR(100), -- 'syntax_check', 'linting', 'complexity_analysis', 'security_scan'
    file_path TEXT,
    language VARCHAR(50),
    lines_of_code INTEGER,
    complexity_score DECIMAL(5,2),
    issues_found INTEGER DEFAULT 0,
    issues_severity JSONB, -- Count by severity level
    analysis_duration_ms INTEGER,
    tool_name VARCHAR(100),
    tool_version VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CHECK (analysis_type IN ('syntax_check', 'linting', 'complexity_analysis', 'security_scan', 'dependency_check')),
    CHECK (lines_of_code >= 0),
    CHECK (complexity_score >= 0),
    CHECK (issues_found >= 0),
    CHECK (analysis_duration_ms >= 0)
);

-- Indexes for code_analysis_learning_events
CREATE INDEX idx_code_analysis_learning_analysis ON code_analysis_learning_events(analysis_id);
CREATE INDEX idx_code_analysis_learning_event ON code_analysis_learning_events(learning_event_id);
CREATE INDEX idx_code_analysis_learning_type ON code_analysis_learning_events(analysis_type);
CREATE INDEX idx_code_analysis_learning_language ON code_analysis_learning_events(language);

-- Legacy System Integration Table
CREATE TABLE legacy_system_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    legacy_table_name VARCHAR(255) NOT NULL,
    legacy_record_id VARCHAR(255) NOT NULL,
    new_table_name VARCHAR(255) NOT NULL,
    new_record_id UUID NOT NULL,
    mapping_type VARCHAR(100), -- 'direct', 'aggregated', 'transformed'
    transformation_rules JSONB, -- Rules used for data transformation
    migration_batch_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(legacy_table_name, legacy_record_id),
    CHECK (mapping_type IN ('direct', 'aggregated', 'transformed', 'split'))
);

-- Indexes for legacy_system_mappings
CREATE INDEX idx_legacy_mappings_legacy ON legacy_system_mappings(legacy_table_name, legacy_record_id);
CREATE INDEX idx_legacy_mappings_new ON legacy_system_mappings(new_table_name, new_record_id);
CREATE INDEX idx_legacy_mappings_batch ON legacy_system_mappings(migration_batch_id);

-- Data Quality Monitoring
CREATE TABLE data_quality_checks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_name VARCHAR(255) NOT NULL,
    column_name VARCHAR(255),
    check_type VARCHAR(100) NOT NULL, -- 'completeness', 'uniqueness', 'validity', 'consistency'
    check_rule JSONB NOT NULL, -- Definition of the quality check
    check_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    records_checked BIGINT,
    records_passed BIGINT,
    records_failed BIGINT,
    quality_score DECIMAL(5,2), -- Percentage of records passing
    threshold_warning DECIMAL(5,2) DEFAULT 95.00,
    threshold_critical DECIMAL(5,2) DEFAULT 90.00,
    status VARCHAR(50), -- 'passed', 'warning', 'failed'
    failure_details JSONB, -- Details about failed records
    
    CHECK (check_type IN ('completeness', 'uniqueness', 'validity', 'consistency', 'accuracy')),
    CHECK (records_checked >= 0),
    CHECK (records_passed >= 0),
    CHECK (records_failed >= 0),
    CHECK (quality_score >= 0.00 AND quality_score <= 100.00),
    CHECK (status IN ('passed', 'warning', 'failed', 'error'))
);

-- Indexes for data_quality_checks
CREATE INDEX idx_data_quality_table ON data_quality_checks(table_name);
CREATE INDEX idx_data_quality_type ON data_quality_checks(check_type);
CREATE INDEX idx_data_quality_timestamp ON data_quality_checks(check_timestamp);
CREATE INDEX idx_data_quality_status ON data_quality_checks(status);

-- Migration Scripts and Functions

-- Function to migrate existing data to enhanced schema
CREATE OR REPLACE FUNCTION migrate_existing_data(batch_size INTEGER DEFAULT 1000)
RETURNS TABLE(
    table_name TEXT,
    records_migrated BIGINT,
    migration_time_ms BIGINT
) AS $$
DECLARE
    start_time TIMESTAMP;
    end_time TIMESTAMP;
    migrated_count BIGINT;
BEGIN
    -- Example migration for existing analytics data
    start_time := clock_timestamp();
    
    -- Migrate existing system metrics (if they exist)
    INSERT INTO system_performance_metrics (
        metric_name, metric_category, timestamp, value, unit, 
        source_component, aggregation_level, metadata
    )
    SELECT 
        'legacy_metric' as metric_name,
        'system' as metric_category,
        NOW() as timestamp,
        0.0 as value,
        'count' as unit,
        'migration' as source_component,
        'raw' as aggregation_level,
        '{"migrated": true}'::JSONB as metadata
    WHERE NOT EXISTS (
        SELECT 1 FROM system_performance_metrics 
        WHERE source_component = 'migration'
    );
    
    GET DIAGNOSTICS migrated_count = ROW_COUNT;
    end_time := clock_timestamp();
    
    RETURN QUERY SELECT 
        'system_performance_metrics'::TEXT,
        migrated_count,
        EXTRACT(EPOCH FROM (end_time - start_time) * 1000)::BIGINT;
END;
$$ LANGUAGE plpgsql;

-- Function to validate schema integrity
CREATE OR REPLACE FUNCTION validate_schema_integrity()
RETURNS TABLE(
    check_name TEXT,
    status TEXT,
    details TEXT
) AS $$
BEGIN
    -- Check foreign key constraints
    RETURN QUERY
    SELECT 
        'foreign_key_constraints'::TEXT as check_name,
        CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END as status,
        CASE WHEN COUNT(*) = 0 THEN 'All foreign keys valid' 
             ELSE COUNT(*)::TEXT || ' foreign key violations found' END as details
    FROM information_schema.table_constraints tc
    WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_schema = current_schema();
    
    -- Check for orphaned records
    RETURN QUERY
    SELECT 
        'orphaned_learning_events'::TEXT as check_name,
        CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'WARN' END as status,
        COUNT(*)::TEXT || ' learning events without valid references' as details
    FROM learning_events le
    LEFT JOIN git_operation_learning_events gole ON le.id = gole.learning_event_id
    LEFT JOIN user_session_learning_events usle ON le.id = usle.learning_event_id
    LEFT JOIN api_request_learning_events arle ON le.id = arle.learning_event_id
    WHERE gole.id IS NULL AND usle.id IS NULL AND arle.id IS NULL
    AND le.timestamp > NOW() - INTERVAL '1 day';
    
    -- Check data quality thresholds
    RETURN QUERY
    SELECT 
        'data_quality_thresholds'::TEXT as check_name,
        CASE WHEN AVG(quality_score) >= 95.0 THEN 'PASS' 
             WHEN AVG(quality_score) >= 90.0 THEN 'WARN' 
             ELSE 'FAIL' END as status,
        'Average quality score: ' || ROUND(AVG(quality_score), 2)::TEXT || '%' as details
    FROM data_quality_checks
    WHERE check_timestamp > NOW() - INTERVAL '1 day';
END;
$$ LANGUAGE plpgsql;

-- Function to rollback schema changes
CREATE OR REPLACE FUNCTION rollback_schema_version(target_version VARCHAR(50))
RETURNS BOOLEAN AS $$
DECLARE
    migration_record RECORD;
    rollback_successful BOOLEAN := true;
BEGIN
    -- Get all migrations after target version in reverse order
    FOR migration_record IN 
        SELECT version, rollback_script 
        FROM schema_migrations 
        WHERE version > target_version 
        ORDER BY applied_at DESC
    LOOP
        BEGIN
            -- Execute rollback script
            IF migration_record.rollback_script IS NOT NULL THEN
                EXECUTE migration_record.rollback_script;
            END IF;
            
            -- Remove migration record
            DELETE FROM schema_migrations WHERE version = migration_record.version;
            
        EXCEPTION WHEN OTHERS THEN
            rollback_successful := false;
            RAISE NOTICE 'Failed to rollback version %: %', migration_record.version, SQLERRM;
        END;
    END LOOP;
    
    RETURN rollback_successful;
END;
$$ LANGUAGE plpgsql;

-- Function to backup critical data before migration
CREATE OR REPLACE FUNCTION backup_critical_data()
RETURNS TEXT AS $$
DECLARE
    backup_id TEXT;
    backup_path TEXT;
BEGIN
    backup_id := 'backup_' || TO_CHAR(NOW(), 'YYYY_MM_DD_HH24_MI_SS');
    backup_path := '/tmp/' || backup_id;
    
    -- Create backup tables with timestamp suffix
    EXECUTE format('CREATE TABLE ml_models_%s AS SELECT * FROM ml_models', backup_id);
    EXECUTE format('CREATE TABLE evolution_experiments_%s AS SELECT * FROM evolution_experiments', backup_id);
    EXECUTE format('CREATE TABLE identified_patterns_%s AS SELECT * FROM identified_patterns', backup_id);
    
    RETURN backup_path;
END;
$$ LANGUAGE plpgsql;

-- Data Quality Check Functions

-- Function to check data completeness
CREATE OR REPLACE FUNCTION check_data_completeness(
    target_table TEXT,
    target_column TEXT,
    threshold_percentage DECIMAL DEFAULT 95.0
)
RETURNS JSONB AS $$
DECLARE
    total_records BIGINT;
    complete_records BIGINT;
    completeness_percentage DECIMAL;
    result JSONB;
BEGIN
    -- Count total records
    EXECUTE format('SELECT COUNT(*) FROM %I', target_table) INTO total_records;
    
    -- Count complete records (non-null)
    EXECUTE format('SELECT COUNT(*) FROM %I WHERE %I IS NOT NULL', 
                   target_table, target_column) INTO complete_records;
    
    -- Calculate completeness percentage
    IF total_records > 0 THEN
        completeness_percentage := (complete_records::DECIMAL / total_records::DECIMAL) * 100;
    ELSE
        completeness_percentage := 0;
    END IF;
    
    -- Build result
    result := jsonb_build_object(
        'table_name', target_table,
        'column_name', target_column,
        'total_records', total_records,
        'complete_records', complete_records,
        'completeness_percentage', completeness_percentage,
        'threshold', threshold_percentage,
        'status', CASE WHEN completeness_percentage >= threshold_percentage THEN 'PASS' ELSE 'FAIL' END
    );
    
    -- Insert into data quality checks
    INSERT INTO data_quality_checks (
        table_name, column_name, check_type, check_rule,
        records_checked, records_passed, records_failed,
        quality_score, status
    ) VALUES (
        target_table, target_column, 'completeness',
        jsonb_build_object('threshold', threshold_percentage),
        total_records, complete_records, total_records - complete_records,
        completeness_percentage,
        CASE WHEN completeness_percentage >= threshold_percentage THEN 'passed' ELSE 'failed' END
    );
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Scheduled maintenance jobs
SELECT cron.schedule('validate-schema-integrity', '0 3 * * *', 'SELECT validate_schema_integrity();');
SELECT cron.schedule('data-quality-checks', '0 4 * * *', 
    'SELECT check_data_completeness(''ml_models'', ''name''); 
     SELECT check_data_completeness(''learning_events'', ''event_type'');');

-- Insert initial migration record
INSERT INTO schema_migrations (version, description, migration_type, checksum) 
VALUES ('2025.01.001', 'Enhanced database schema for continuous learning and analytics', 'enhancement', 
        md5('enhanced_schema_v1'));

-- Comments for documentation
COMMENT ON TABLE schema_migrations IS 'Tracking of database schema versions and migrations';
COMMENT ON TABLE git_operation_learning_events IS 'Integration between git operations and learning events';
COMMENT ON TABLE user_session_learning_events IS 'Integration between user sessions and learning events';
COMMENT ON TABLE api_request_learning_events IS 'Integration between API requests and learning events';
COMMENT ON TABLE code_analysis_learning_events IS 'Integration between code analysis and learning events';
COMMENT ON TABLE legacy_system_mappings IS 'Mapping between legacy and new system records';
COMMENT ON TABLE data_quality_checks IS 'Automated data quality monitoring and validation';

