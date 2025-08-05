-- =============================================================================
-- DATABASE INITIALIZATION SCRIPT
-- =============================================================================
-- This script initializes a new database with the complete schema and
-- essential seed data for all 5 modules.
-- =============================================================================

-- Create database (run this separately if needed)
-- CREATE DATABASE codegen_platform;

-- Connect to the database
\c codegen_platform;

-- =============================================================================
-- SCHEMA MIGRATIONS TABLE
-- =============================================================================

-- Create schema migrations table first
CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(20) PRIMARY KEY,
    description TEXT,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    rollback_sql TEXT,
    checksum VARCHAR(64)
);

-- =============================================================================
-- APPLY INITIAL MIGRATION
-- =============================================================================

-- Execute the initial migration
\i database/migrations/001_initial_schema.sql

-- =============================================================================
-- SEED DATA
-- =============================================================================

-- Create system user for automated operations
INSERT INTO users (id, organization_id, email, username, full_name, role) 
SELECT 
    uuid_generate_v4(),
    o.id,
    'system@codegen.platform',
    'system',
    'System User',
    'system'
FROM organizations o 
WHERE o.slug = 'default'
ON CONFLICT (email) DO NOTHING;

-- Create admin user
INSERT INTO users (id, organization_id, email, username, full_name, role) 
SELECT 
    uuid_generate_v4(),
    o.id,
    'admin@codegen.platform',
    'admin',
    'Administrator',
    'admin'
FROM organizations o 
WHERE o.slug = 'default'
ON CONFLICT (email) DO NOTHING;

-- Create sample project
INSERT INTO projects (organization_id, name, slug, description, status, priority, owner_id)
SELECT 
    o.id,
    'Sample Project',
    'sample-project',
    'A sample project for demonstration purposes',
    'active'::project_status,
    'medium'::priority_level,
    u.id
FROM organizations o, users u
WHERE o.slug = 'default' 
AND u.username = 'admin'
ON CONFLICT (organization_id, slug) DO NOTHING;

-- Create sample repository
INSERT INTO repositories (project_id, organization_id, name, full_name, url, description, language, status)
SELECT 
    p.id,
    p.organization_id,
    'sample-repo',
    'codegen/sample-repo',
    'https://github.com/codegen/sample-repo',
    'Sample repository for testing',
    'Python',
    'active'::repository_status
FROM projects p
WHERE p.slug = 'sample-project'
ON CONFLICT (organization_id, full_name) DO NOTHING;

-- Link project and repository
INSERT INTO project_repositories (project_id, repository_id, role, importance)
SELECT 
    p.id,
    r.id,
    'primary',
    'high'::priority_level
FROM projects p, repositories r
WHERE p.slug = 'sample-project'
AND r.name = 'sample-repo'
ON CONFLICT (project_id, repository_id) DO NOTHING;

-- Create sample task definition
INSERT INTO task_definitions (organization_id, name, slug, description, task_type, default_timeout_seconds)
SELECT 
    o.id,
    'Code Analysis',
    'code-analysis',
    'Analyze code quality and complexity',
    'analysis'::task_type,
    1800
FROM organizations o
WHERE o.slug = 'default'
ON CONFLICT (organization_id, slug, version) DO NOTHING;

-- Create sample context source
INSERT INTO context_sources (organization_id, name, source_type, config, description)
SELECT 
    o.id,
    'Repository Files',
    'repository',
    '{"include_patterns": ["*.py", "*.js", "*.ts"], "exclude_patterns": ["*.pyc", "node_modules/*"]}'::jsonb,
    'Source code files from repositories'
FROM organizations o
WHERE o.slug = 'default'
ON CONFLICT (organization_id, name) DO NOTHING;

-- =============================================================================
-- PERFORMANCE OPTIMIZATION
-- =============================================================================

-- Update table statistics
ANALYZE;

-- Create additional performance indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_composite_performance 
ON events(organization_id, status, occurred_at DESC) 
WHERE status IN ('pending', 'processing');

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tasks_execution_performance 
ON tasks(status, priority, scheduled_at) 
WHERE status IN ('pending', 'queued', 'running');

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_prompt_executions_recent 
ON prompt_executions(template_id, started_at DESC) 
WHERE started_at >= CURRENT_DATE - INTERVAL '30 days';

-- =============================================================================
-- MONITORING SETUP
-- =============================================================================

-- Create monitoring views
CREATE OR REPLACE VIEW system_health AS
SELECT 
    'database' as component,
    'healthy' as status,
    jsonb_build_object(
        'total_tables', (SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'),
        'total_indexes', (SELECT count(*) FROM pg_indexes WHERE schemaname = 'public'),
        'database_size', pg_size_pretty(pg_database_size(current_database())),
        'active_connections', (SELECT count(*) FROM pg_stat_activity WHERE state = 'active')
    ) as details,
    CURRENT_TIMESTAMP as checked_at;

-- Create data quality monitoring view
CREATE OR REPLACE VIEW data_quality_metrics AS
SELECT 
    'organizations' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN deleted_at IS NULL THEN 1 END) as active_records,
    COUNT(CASE WHEN created_at >= CURRENT_DATE - INTERVAL '24 hours' THEN 1 END) as records_last_24h
FROM organizations
UNION ALL
SELECT 
    'projects' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN deleted_at IS NULL THEN 1 END) as active_records,
    COUNT(CASE WHEN created_at >= CURRENT_DATE - INTERVAL '24 hours' THEN 1 END) as records_last_24h
FROM projects
UNION ALL
SELECT 
    'repositories' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN deleted_at IS NULL THEN 1 END) as active_records,
    COUNT(CASE WHEN created_at >= CURRENT_DATE - INTERVAL '24 hours' THEN 1 END) as records_last_24h
FROM repositories
UNION ALL
SELECT 
    'tasks' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN deleted_at IS NULL THEN 1 END) as active_records,
    COUNT(CASE WHEN created_at >= CURRENT_DATE - INTERVAL '24 hours' THEN 1 END) as records_last_24h
FROM tasks
UNION ALL
SELECT 
    'events' as table_name,
    COUNT(*) as total_records,
    COUNT(*) as active_records, -- Events don't have soft delete
    COUNT(CASE WHEN created_at >= CURRENT_DATE - INTERVAL '24 hours' THEN 1 END) as records_last_24h
FROM events;

-- =============================================================================
-- COMPLETION LOG
-- =============================================================================

INSERT INTO schema_migrations (version, description, applied_at) VALUES 
('init_complete', 'Database initialization completed successfully', CURRENT_TIMESTAMP);

-- Display initialization summary
SELECT 
    'Database initialization completed successfully!' as message,
    CURRENT_TIMESTAMP as completed_at,
    (SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public') as tables_created,
    (SELECT count(*) FROM pg_indexes WHERE schemaname = 'public') as indexes_created,
    pg_size_pretty(pg_database_size(current_database())) as database_size;

-- Display seed data summary
SELECT 
    'Seed data summary:' as summary,
    (SELECT count(*) FROM organizations) as organizations,
    (SELECT count(*) FROM users) as users,
    (SELECT count(*) FROM projects) as projects,
    (SELECT count(*) FROM repositories) as repositories,
    (SELECT count(*) FROM task_definitions) as task_definitions,
    (SELECT count(*) FROM prompt_templates) as prompt_templates,
    (SELECT count(*) FROM event_types) as event_types;

COMMENT ON VIEW system_health IS 'System health monitoring view';
COMMENT ON VIEW data_quality_metrics IS 'Data quality and volume metrics across all tables';

