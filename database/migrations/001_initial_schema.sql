-- =============================================================================
-- MIGRATION 001: INITIAL SCHEMA
-- =============================================================================
-- This migration creates the complete database schema for all 5 modules:
-- - Base schema with organizations and users
-- - Projects module for repository and project management
-- - Tasks module for task lifecycle and workflow management
-- - Analytics module for codebase analysis and metrics
-- - Prompts module for dynamic prompt management
-- - Events module for integration event tracking
-- =============================================================================

-- Migration metadata
INSERT INTO schema_migrations (version, description, applied_at) VALUES 
('001', 'Initial comprehensive schema for all 5 modules', CURRENT_TIMESTAMP);

-- =============================================================================
-- EXECUTE SCHEMA FILES IN ORDER
-- =============================================================================

-- Base schema with common elements
\i database/schemas/00_base_schema.sql

-- Projects module - must come first as other modules reference it
\i database/schemas/01_projects_module.sql

-- Tasks module - references projects
\i database/schemas/02_tasks_module.sql

-- Analytics module - references projects and repositories
\i database/schemas/03_analytics_module.sql

-- Prompts module - references projects, repositories, and tasks
\i database/schemas/04_prompts_module.sql

-- Events module - references all other modules
\i database/schemas/05_events_module.sql

-- =============================================================================
-- POST-MIGRATION SETUP
-- =============================================================================

-- Create schema migrations table if it doesn't exist
CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(20) PRIMARY KEY,
    description TEXT,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    rollback_sql TEXT
);

-- Insert initial data
INSERT INTO organizations (name, slug, description) VALUES 
('Default Organization', 'default', 'Default organization for initial setup')
ON CONFLICT (slug) DO NOTHING;

-- Create default event types
INSERT INTO event_types (organization_id, name, source, category, description) 
SELECT 
    o.id,
    event_data.name,
    event_data.source::event_source,
    event_data.category::event_category,
    event_data.description
FROM organizations o,
(VALUES 
    ('linear_issue_created', 'linear', 'issue', 'Linear issue creation events'),
    ('linear_issue_updated', 'linear', 'issue', 'Linear issue update events'),
    ('linear_comment_created', 'linear', 'comment', 'Linear comment creation events'),
    ('slack_message', 'slack', 'message', 'Slack message events'),
    ('slack_app_mention', 'slack', 'message', 'Slack app mention events'),
    ('github_push', 'github', 'commit', 'GitHub push events'),
    ('github_pull_request', 'github', 'pull_request', 'GitHub pull request events'),
    ('github_workflow_run', 'github', 'workflow', 'GitHub workflow run events'),
    ('deployment_started', 'deployment', 'deployment', 'Deployment start events'),
    ('deployment_completed', 'deployment', 'deployment', 'Deployment completion events'),
    ('system_startup', 'system', 'system_event', 'System startup events'),
    ('system_shutdown', 'system', 'system_event', 'System shutdown events')
) AS event_data(name, source, category, description)
WHERE o.slug = 'default'
ON CONFLICT (organization_id, source, name) DO NOTHING;

-- Create default prompt templates
INSERT INTO prompt_templates (organization_id, name, slug, prompt_type, category, template_content, description, created_by)
SELECT 
    o.id,
    template_data.name,
    template_data.slug,
    template_data.prompt_type::prompt_type,
    template_data.category::prompt_category,
    template_data.content,
    template_data.description,
    u.id
FROM organizations o,
     users u,
(VALUES 
    ('Code Review', 'code-review', 'system', 'code_review', 
     'Please review the following code changes:\n\n{code_diff}\n\nProvide feedback on:\n1. Code quality\n2. Potential bugs\n3. Performance considerations\n4. Best practices',
     'Standard code review prompt template'),
    ('Bug Analysis', 'bug-analysis', 'system', 'debugging',
     'Analyze the following error and code context:\n\nError: {error_message}\nCode: {code_context}\n\nProvide:\n1. Root cause analysis\n2. Suggested fixes\n3. Prevention strategies',
     'Bug analysis and debugging prompt template'),
    ('Code Generation', 'code-generation', 'system', 'code_generation',
     'Generate {language} code for the following requirements:\n\n{requirements}\n\nEnsure the code:\n1. Follows best practices\n2. Includes error handling\n3. Is well-documented',
     'Code generation prompt template'),
    ('Test Generation', 'test-generation', 'system', 'testing',
     'Generate comprehensive tests for the following code:\n\n{code}\n\nInclude:\n1. Unit tests\n2. Edge cases\n3. Error scenarios',
     'Test generation prompt template')
) AS template_data(name, slug, prompt_type, category, content, description)
WHERE o.slug = 'default'
AND u.email = 'system@example.com'
ON CONFLICT (organization_id, slug, version) DO NOTHING;

-- Create indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_events_occurred_at_desc ON events(occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_tasks_status_priority_created ON tasks(status, priority, created_at);
CREATE INDEX IF NOT EXISTS idx_analysis_runs_repo_completed ON analysis_runs(repository_id, completed_at DESC);
CREATE INDEX IF NOT EXISTS idx_prompt_executions_template_completed ON prompt_executions(template_id, completed_at DESC);

-- Update statistics
ANALYZE;

-- Log completion
INSERT INTO schema_migrations (version, description, applied_at) VALUES 
('001_complete', 'Initial schema migration completed successfully', CURRENT_TIMESTAMP);

COMMENT ON TABLE schema_migrations IS 'Track database schema migrations and versions';

