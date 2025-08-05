-- =============================================================================
-- SEED DATA SCRIPT
-- =============================================================================
-- This script populates the database with comprehensive seed data for
-- development, testing, and demonstration purposes.
-- =============================================================================

-- =============================================================================
-- ORGANIZATIONS AND USERS
-- =============================================================================

-- Create development organization
INSERT INTO organizations (name, slug, description, settings) VALUES 
('Development Org', 'dev-org', 'Development organization for testing', 
 '{"features": ["analytics", "prompts", "events"], "limits": {"projects": 100, "repositories": 500}}'::jsonb)
ON CONFLICT (slug) DO NOTHING;

-- Create test users
INSERT INTO users (organization_id, email, username, full_name, role, preferences) 
SELECT 
    o.id,
    user_data.email,
    user_data.username,
    user_data.full_name,
    user_data.role,
    user_data.preferences::jsonb
FROM organizations o,
(VALUES 
    ('developer@example.com', 'developer', 'John Developer', 'developer', '{"theme": "dark", "notifications": true}'),
    ('analyst@example.com', 'analyst', 'Jane Analyst', 'analyst', '{"theme": "light", "notifications": true}'),
    ('manager@example.com', 'manager', 'Bob Manager', 'manager', '{"theme": "auto", "notifications": false}'),
    ('tester@example.com', 'tester', 'Alice Tester', 'user', '{"theme": "dark", "notifications": true}')
) AS user_data(email, username, full_name, role, preferences)
WHERE o.slug = 'dev-org'
ON CONFLICT (email) DO NOTHING;

-- =============================================================================
-- PROJECTS AND REPOSITORIES
-- =============================================================================

-- Create sample projects
INSERT INTO projects (organization_id, name, slug, description, status, priority, goals, tags, owner_id, start_date, target_end_date)
SELECT 
    o.id,
    project_data.name,
    project_data.slug,
    project_data.description,
    project_data.status::project_status,
    project_data.priority::priority_level,
    project_data.goals::text[],
    project_data.tags::varchar(50)[],
    u.id,
    project_data.start_date::date,
    project_data.target_end_date::date
FROM organizations o, users u,
(VALUES 
    ('AI Code Assistant', 'ai-code-assistant', 'AI-powered code generation and review assistant', 'active', 'high', 
     '{"Improve code quality", "Reduce review time", "Automate testing"}', '{"ai", "automation", "productivity"}',
     '2024-01-01', '2024-06-30'),
    ('Analytics Dashboard', 'analytics-dashboard', 'Real-time analytics and reporting dashboard', 'active', 'medium',
     '{"Provide insights", "Track metrics", "Enable data-driven decisions"}', '{"analytics", "dashboard", "metrics"}',
     '2024-02-01', '2024-08-31'),
    ('Integration Platform', 'integration-platform', 'Multi-platform integration and event processing', 'planning', 'high',
     '{"Connect systems", "Process events", "Enable automation"}', '{"integration", "events", "automation"}',
     '2024-03-01', '2024-09-30')
) AS project_data(name, slug, description, status, priority, goals, tags, start_date, target_end_date)
WHERE o.slug = 'dev-org' AND u.username = 'manager'
ON CONFLICT (organization_id, slug) DO NOTHING;

-- Create sample repositories
INSERT INTO repositories (project_id, organization_id, name, full_name, url, description, language, languages, status, config)
SELECT 
    p.id,
    p.organization_id,
    repo_data.name,
    repo_data.full_name,
    repo_data.url,
    repo_data.description,
    repo_data.language,
    repo_data.languages::jsonb,
    repo_data.status::repository_status,
    repo_data.config::jsonb
FROM projects p,
(VALUES 
    ('ai-assistant-backend', 'dev-org/ai-assistant-backend', 'https://github.com/dev-org/ai-assistant-backend',
     'Backend API for AI code assistant', 'Python', '{"Python": 85, "JavaScript": 10, "Shell": 5}', 'active',
     '{"branch_protection": true, "auto_merge": false, "required_reviews": 2}'),
    ('ai-assistant-frontend', 'dev-org/ai-assistant-frontend', 'https://github.com/dev-org/ai-assistant-frontend',
     'Frontend interface for AI code assistant', 'TypeScript', '{"TypeScript": 70, "CSS": 20, "HTML": 10}', 'active',
     '{"branch_protection": true, "auto_merge": true, "required_reviews": 1}'),
    ('analytics-api', 'dev-org/analytics-api', 'https://github.com/dev-org/analytics-api',
     'Analytics API service', 'Python', '{"Python": 90, "SQL": 8, "Shell": 2}', 'active',
     '{"branch_protection": true, "auto_merge": false, "required_reviews": 2}'),
    ('analytics-ui', 'dev-org/analytics-ui', 'https://github.com/dev-org/analytics-ui',
     'Analytics dashboard UI', 'React', '{"JavaScript": 60, "TypeScript": 30, "CSS": 10}', 'active',
     '{"branch_protection": false, "auto_merge": true, "required_reviews": 1}'),
    ('integration-service', 'dev-org/integration-service', 'https://github.com/dev-org/integration-service',
     'Integration and event processing service', 'Go', '{"Go": 95, "Shell": 3, "Dockerfile": 2}', 'active',
     '{"branch_protection": true, "auto_merge": false, "required_reviews": 2}')
) AS repo_data(name, full_name, url, description, language, languages, status, config)
WHERE p.slug IN ('ai-code-assistant', 'analytics-dashboard', 'integration-platform')
ON CONFLICT (organization_id, full_name) DO NOTHING;

-- Link projects and repositories
INSERT INTO project_repositories (project_id, repository_id, role, importance)
SELECT p.id, r.id, 'primary', 'high'::priority_level
FROM projects p
JOIN repositories r ON p.id = r.project_id
ON CONFLICT (project_id, repository_id) DO NOTHING;

-- =============================================================================
-- TASK DEFINITIONS AND TASKS
-- =============================================================================

-- Create task definitions
INSERT INTO task_definitions (organization_id, name, slug, description, task_type, default_timeout_seconds, max_retries, cpu_limit, memory_limit_mb, environment, input_schema, output_schema, tags)
SELECT 
    o.id,
    task_def.name,
    task_def.slug,
    task_def.description,
    task_def.task_type::task_type,
    task_def.timeout_seconds,
    task_def.max_retries,
    task_def.cpu_limit,
    task_def.memory_limit_mb,
    task_def.environment::execution_environment,
    task_def.input_schema::jsonb,
    task_def.output_schema::jsonb,
    task_def.tags::varchar(50)[]
FROM organizations o,
(VALUES 
    ('Static Code Analysis', 'static-analysis', 'Perform static code analysis using various tools', 'analysis', 1800, 3, 2.0, 4096, 'docker',
     '{"repository_url": "string", "branch": "string", "tools": "array"}',
     '{"issues": "array", "metrics": "object", "summary": "object"}',
     '{"analysis", "quality", "static"}'),
    ('Unit Test Generation', 'unit-test-gen', 'Generate unit tests for code functions', 'testing', 900, 2, 1.0, 2048, 'docker',
     '{"source_code": "string", "language": "string", "framework": "string"}',
     '{"test_code": "string", "coverage": "number", "test_count": "number"}',
     '{"testing", "generation", "automation"}'),
    ('Code Review', 'code-review', 'Automated code review and feedback', 'analysis', 600, 2, 1.0, 2048, 'local',
     '{"diff": "string", "context": "object", "rules": "array"}',
     '{"feedback": "array", "score": "number", "suggestions": "array"}',
     '{"review", "quality", "feedback"}'),
    ('Documentation Generation', 'doc-generation', 'Generate documentation from code', 'generation', 1200, 2, 1.5, 3072, 'docker',
     '{"source_files": "array", "format": "string", "template": "string"}',
     '{"documentation": "string", "files_generated": "array"}',
     '{"documentation", "generation", "automation"}')
) AS task_def(name, slug, description, task_type, timeout_seconds, max_retries, cpu_limit, memory_limit_mb, environment, input_schema, output_schema, tags)
WHERE o.slug = 'dev-org'
ON CONFLICT (organization_id, slug, version) DO NOTHING;

-- Create sample tasks
INSERT INTO tasks (organization_id, project_id, repository_id, task_definition_id, name, task_type, status, priority, arguments, created_by, assigned_to, scheduled_at, tags)
SELECT 
    o.id,
    p.id,
    r.id,
    td.id,
    task_data.name,
    task_data.task_type::task_type,
    task_data.status::task_status,
    task_data.priority::priority_level,
    task_data.arguments::jsonb,
    u1.id,
    u2.id,
    task_data.scheduled_at::timestamp with time zone,
    task_data.tags::varchar(50)[]
FROM organizations o, projects p, repositories r, task_definitions td, users u1, users u2,
(VALUES 
    ('Analyze AI Assistant Backend', 'analysis', 'completed', 'high', 
     '{"repository_url": "https://github.com/dev-org/ai-assistant-backend", "branch": "main", "tools": ["pylint", "bandit", "mypy"]}',
     'static-analysis', 'developer', 'analyst', '2024-01-15 10:00:00+00', '{"urgent", "backend"}'),
    ('Generate Tests for Analytics API', 'testing', 'running', 'medium',
     '{"source_code": "analytics/api.py", "language": "python", "framework": "pytest"}',
     'unit-test-gen', 'developer', 'tester', '2024-01-16 14:00:00+00', '{"testing", "api"}'),
    ('Review Integration Service PR', 'analysis', 'pending', 'high',
     '{"diff": "integration/handlers.go", "context": {"pr_number": 42}, "rules": ["security", "performance"]}',
     'code-review', 'manager', 'developer', '2024-01-17 09:00:00+00', '{"review", "integration"}')
) AS task_data(name, task_type, status, priority, arguments, task_def_slug, created_by_username, assigned_to_username, scheduled_at, tags)
WHERE o.slug = 'dev-org' 
AND p.slug = 'ai-code-assistant'
AND r.name = 'ai-assistant-backend'
AND td.slug = task_data.task_def_slug
AND u1.username = task_data.created_by_username
AND u2.username = task_data.assigned_to_username
ON CONFLICT DO NOTHING;

-- =============================================================================
-- ANALYTICS DATA
-- =============================================================================

-- Create analysis runs
INSERT INTO analysis_runs (organization_id, repository_id, name, analysis_type, status, commit_sha, branch_name, tool_name, tool_version, started_at, completed_at, total_files_analyzed, total_issues_found, triggered_by)
SELECT 
    o.id,
    r.id,
    analysis_data.name,
    analysis_data.analysis_type::analysis_type,
    analysis_data.status::analysis_status,
    analysis_data.commit_sha,
    analysis_data.branch_name,
    analysis_data.tool_name,
    analysis_data.tool_version,
    analysis_data.started_at::timestamp with time zone,
    analysis_data.completed_at::timestamp with time zone,
    analysis_data.files_analyzed,
    analysis_data.issues_found,
    u.id
FROM organizations o, repositories r, users u,
(VALUES 
    ('Static Analysis - Main Branch', 'static', 'completed', 'abc123def456', 'main', 'SonarQube', '9.7.1',
     '2024-01-15 10:00:00+00', '2024-01-15 10:15:00+00', 45, 12, 'analyst'),
    ('Security Scan - Feature Branch', 'security', 'completed', 'def456ghi789', 'feature/auth-improvements', 'Bandit', '1.7.4',
     '2024-01-16 14:30:00+00', '2024-01-16 14:35:00+00', 23, 3, 'developer'),
    ('Performance Analysis - Main', 'performance', 'running', 'ghi789jkl012', 'main', 'PyProfiler', '2.1.0',
     '2024-01-17 09:00:00+00', NULL, 0, 0, 'analyst')
) AS analysis_data(name, analysis_type, status, commit_sha, branch_name, tool_name, tool_version, started_at, completed_at, files_analyzed, issues_found, triggered_by_username)
WHERE o.slug = 'dev-org' 
AND r.name = 'ai-assistant-backend'
AND u.username = analysis_data.triggered_by_username
ON CONFLICT DO NOTHING;

-- =============================================================================
-- PROMPT TEMPLATES AND EXECUTIONS
-- =============================================================================

-- Create additional prompt templates
INSERT INTO prompt_templates (organization_id, name, slug, prompt_type, category, template_content, system_prompt, variables, model_name, model_parameters, created_by, tags)
SELECT 
    o.id,
    template_data.name,
    template_data.slug,
    template_data.prompt_type::prompt_type,
    template_data.category::prompt_category,
    template_data.template_content,
    template_data.system_prompt,
    template_data.variables::jsonb,
    template_data.model_name,
    template_data.model_parameters::jsonb,
    u.id,
    template_data.tags::varchar(50)[]
FROM organizations o, users u,
(VALUES 
    ('API Documentation Generator', 'api-doc-generator', 'system', 'documentation',
     'Generate comprehensive API documentation for the following endpoints:\n\n{endpoints}\n\nInclude:\n1. Request/response schemas\n2. Example usage\n3. Error codes\n4. Authentication requirements',
     'You are an expert technical writer specializing in API documentation.',
     '{"endpoints": {"type": "array", "description": "List of API endpoints to document"}}',
     'gpt-4', '{"temperature": 0.3, "max_tokens": 2000}',
     'developer', '{"documentation", "api", "automation"}'),
    ('Refactoring Suggestions', 'refactoring-suggestions', 'system', 'refactoring',
     'Analyze the following code and provide refactoring suggestions:\n\n{code}\n\nFocus on:\n1. Code structure improvements\n2. Performance optimizations\n3. Maintainability enhancements\n4. Design pattern applications',
     'You are a senior software engineer with expertise in code refactoring and design patterns.',
     '{"code": {"type": "string", "description": "Code to analyze for refactoring"}}',
     'gpt-4', '{"temperature": 0.2, "max_tokens": 1500}',
     'developer', '{"refactoring", "optimization", "patterns"}'),
    ('Error Explanation', 'error-explanation', 'system', 'debugging',
     'Explain the following error in simple terms and provide solutions:\n\nError: {error_message}\nStack trace: {stack_trace}\nContext: {context}',
     'You are a helpful debugging assistant that explains errors clearly and provides actionable solutions.',
     '{"error_message": {"type": "string"}, "stack_trace": {"type": "string"}, "context": {"type": "object"}}',
     'gpt-3.5-turbo', '{"temperature": 0.1, "max_tokens": 1000}',
     'developer', '{"debugging", "errors", "help"}'
) AS template_data(name, slug, prompt_type, category, template_content, system_prompt, variables, model_name, model_parameters, created_by_username, tags)
WHERE o.slug = 'dev-org' AND u.username = template_data.created_by_username
ON CONFLICT (organization_id, slug, version) DO NOTHING;

-- =============================================================================
-- EVENTS DATA
-- =============================================================================

-- Create sample events
INSERT INTO events (organization_id, source, category, event_name, title, description, priority, payload, project_id, repository_id, user_id, occurred_at, status, tags)
SELECT 
    o.id,
    event_data.source::event_source,
    event_data.category::event_category,
    event_data.event_name,
    event_data.title,
    event_data.description,
    event_data.priority::event_priority,
    event_data.payload::jsonb,
    p.id,
    r.id,
    u.id,
    event_data.occurred_at::timestamp with time zone,
    event_data.status::processing_status,
    event_data.tags::varchar(50)[]
FROM organizations o, projects p, repositories r, users u,
(VALUES 
    ('github', 'pull_request', 'pull_request_opened', 'Pull Request #42 Opened', 'New pull request for authentication improvements',
     'normal', '{"pr_number": 42, "title": "Add OAuth2 authentication", "author": "developer", "files_changed": 8}',
     'ai-code-assistant', 'ai-assistant-backend', 'developer', '2024-01-15 09:30:00+00', 'processed', '{"github", "pr", "auth"}'),
    ('linear', 'issue', 'issue_created', 'Issue PROJ-123 Created', 'New issue: Implement rate limiting',
     'high', '{"issue_id": "PROJ-123", "title": "Implement rate limiting", "assignee": "developer", "priority": "high"}',
     'ai-code-assistant', 'ai-assistant-backend', 'manager', '2024-01-16 11:00:00+00', 'processed', '{"linear", "issue", "feature"}'),
    ('slack', 'message', 'app_mention', 'Bot Mentioned in #dev-team', 'User asked for code review assistance',
     'normal', '{"channel": "#dev-team", "user": "developer", "message": "@bot please review my latest changes", "timestamp": "1705401600"}',
     'ai-code-assistant', NULL, 'developer', '2024-01-16 12:00:00+00', 'processed', '{"slack", "mention", "review"}'),
    ('deployment', 'deployment', 'deployment_completed', 'Production Deployment Successful', 'Version 1.2.3 deployed to production',
     'high', '{"version": "1.2.3", "environment": "production", "duration": 180, "success": true}',
     'ai-code-assistant', 'ai-assistant-backend', 'manager', '2024-01-17 08:00:00+00', 'processed', '{"deployment", "production", "success"}'
) AS event_data(source, category, event_name, title, description, priority, payload, project_slug, repo_name, user_username, occurred_at, status, tags)
WHERE o.slug = 'dev-org'
AND p.slug = event_data.project_slug
AND (r.name = event_data.repo_name OR event_data.repo_name IS NULL)
AND u.username = event_data.user_username
ON CONFLICT DO NOTHING;

-- =============================================================================
-- PERFORMANCE OPTIMIZATION
-- =============================================================================

-- Update statistics for all tables
ANALYZE;

-- Create additional indexes for seed data queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_seed_data_performance_1 
ON tasks(project_id, status, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_seed_data_performance_2 
ON events(project_id, occurred_at DESC) 
WHERE status = 'processed';

-- =============================================================================
-- COMPLETION SUMMARY
-- =============================================================================

-- Log seed data completion
INSERT INTO schema_migrations (version, description, applied_at) VALUES 
('seed_data_complete', 'Comprehensive seed data loaded successfully', CURRENT_TIMESTAMP);

-- Display seed data summary
SELECT 
    'Seed data loading completed!' as message,
    jsonb_build_object(
        'organizations', (SELECT count(*) FROM organizations),
        'users', (SELECT count(*) FROM users),
        'projects', (SELECT count(*) FROM projects),
        'repositories', (SELECT count(*) FROM repositories),
        'task_definitions', (SELECT count(*) FROM task_definitions),
        'tasks', (SELECT count(*) FROM tasks),
        'analysis_runs', (SELECT count(*) FROM analysis_runs),
        'prompt_templates', (SELECT count(*) FROM prompt_templates),
        'events', (SELECT count(*) FROM events)
    ) as summary,
    CURRENT_TIMESTAMP as completed_at;

