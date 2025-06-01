-- =============================================================================
-- AUTONOMOUS DEVELOPMENT DATABASE DEPLOYMENT SCRIPT
-- =============================================================================
-- Complete deployment script for the autonomous development database schemas
-- Deploy in the correct order with proper error handling and validation
-- =============================================================================

-- Set deployment parameters
\set ON_ERROR_STOP on
\set ECHO all

-- Display deployment information
\echo '============================================================================='
\echo 'AUTONOMOUS DEVELOPMENT DATABASE DEPLOYMENT'
\echo '============================================================================='
\echo 'Deploying simplified, single-user focused database schemas for intelligent'
\echo 'autonomous software development with comprehensive learning capabilities'
\echo '============================================================================='

-- Check PostgreSQL version
SELECT version();

-- Check required extensions availability
\echo 'Checking required extensions...'
SELECT 
    name,
    installed_version,
    CASE WHEN installed_version IS NOT NULL THEN '✅ Available' ELSE '❌ Missing' END as status
FROM pg_available_extensions 
WHERE name IN ('uuid-ossp', 'pg_trgm', 'btree_gin', 'btree_gist', 'pg_stat_statements')
ORDER BY name;

-- Create deployment log table
CREATE TABLE IF NOT EXISTS deployment_log (
    id SERIAL PRIMARY KEY,
    deployment_step VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL, -- 'started', 'completed', 'failed'
    start_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP WITH TIME ZONE,
    duration INTERVAL,
    error_message TEXT,
    details JSONB DEFAULT '{}'
);

-- Function to log deployment steps
CREATE OR REPLACE FUNCTION log_deployment_step(
    step_name VARCHAR(255),
    step_status VARCHAR(50),
    error_msg TEXT DEFAULT NULL,
    step_details JSONB DEFAULT '{}'
)
RETURNS VOID AS $$
DECLARE
    step_id INTEGER;
BEGIN
    IF step_status = 'started' THEN
        INSERT INTO deployment_log (deployment_step, status, details)
        VALUES (step_name, step_status, step_details);
    ELSE
        UPDATE deployment_log 
        SET status = step_status,
            end_time = CURRENT_TIMESTAMP,
            duration = CURRENT_TIMESTAMP - start_time,
            error_message = error_msg,
            details = details || step_details
        WHERE deployment_step = step_name 
        AND status = 'started'
        AND start_time = (
            SELECT MAX(start_time) FROM deployment_log 
            WHERE deployment_step = step_name AND status = 'started'
        );
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Start deployment
SELECT log_deployment_step('deployment_start', 'started', NULL, 
    jsonb_build_object('database', current_database(), 'user', current_user, 'timestamp', CURRENT_TIMESTAMP));

\echo ''
\echo '============================================================================='
\echo 'STEP 1: DEPLOYING AUTONOMOUS CORE SCHEMA'
\echo '============================================================================='

SELECT log_deployment_step('autonomous_core_schema', 'started');

-- Deploy core schema
\i database/schemas/01_autonomous_core.sql

-- Validate core schema deployment
DO $$
DECLARE
    missing_tables TEXT[] := '{}';
    table_name TEXT;
    expected_tables TEXT[] := ARRAY[
        'system_configuration', 'codebases', 'tasks', 'task_executions',
        'codegen_agents', 'agent_tasks', 'audit_log', 'performance_metrics'
    ];
BEGIN
    FOREACH table_name IN ARRAY expected_tables
    LOOP
        IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = table_name) THEN
            missing_tables := array_append(missing_tables, table_name);
        END IF;
    END LOOP;
    
    IF array_length(missing_tables, 1) > 0 THEN
        RAISE EXCEPTION 'Core schema deployment failed. Missing tables: %', array_to_string(missing_tables, ', ');
    END IF;
    
    RAISE NOTICE '✅ Core schema deployed successfully. All % tables created.', array_length(expected_tables, 1);
END $$;

SELECT log_deployment_step('autonomous_core_schema', 'completed');

\echo ''
\echo '============================================================================='
\echo 'STEP 2: DEPLOYING LEARNING INTELLIGENCE SCHEMA'
\echo '============================================================================='

SELECT log_deployment_step('learning_intelligence_schema', 'started');

-- Deploy learning intelligence schema
\i database/schemas/02_learning_intelligence.sql

-- Validate learning intelligence schema deployment
DO $$
DECLARE
    missing_tables TEXT[] := '{}';
    table_name TEXT;
    expected_tables TEXT[] := ARRAY[
        'evaluations', 'context_analysis', 'error_reports', 'learning_patterns',
        'pattern_applications', 'improvement_cycles', 'knowledge_base'
    ];
BEGIN
    FOREACH table_name IN ARRAY expected_tables
    LOOP
        IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = table_name) THEN
            missing_tables := array_append(missing_tables, table_name);
        END IF;
    END LOOP;
    
    IF array_length(missing_tables, 1) > 0 THEN
        RAISE EXCEPTION 'Learning intelligence schema deployment failed. Missing tables: %', array_to_string(missing_tables, ', ');
    END IF;
    
    RAISE NOTICE '✅ Learning intelligence schema deployed successfully. All % tables created.', array_length(expected_tables, 1);
END $$;

SELECT log_deployment_step('learning_intelligence_schema', 'completed');

\echo ''
\echo '============================================================================='
\echo 'STEP 3: DEPLOYING INTEGRATION ORCHESTRATION SCHEMA'
\echo '============================================================================='

SELECT log_deployment_step('integration_orchestration_schema', 'started');

-- Deploy integration orchestration schema
\i database/schemas/03_integration_orchestration.sql

-- Validate integration orchestration schema deployment
DO $$
DECLARE
    missing_tables TEXT[] := '{}';
    table_name TEXT;
    expected_tables TEXT[] := ARRAY[
        'integrations', 'github_integrations', 'linear_integrations', 'slack_integrations',
        'integration_events', 'event_handlers', 'workflows', 'workflow_executions',
        'notifications', 'notification_deliveries'
    ];
BEGIN
    FOREACH table_name IN ARRAY expected_tables
    LOOP
        IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = table_name) THEN
            missing_tables := array_append(missing_tables, table_name);
        END IF;
    END LOOP;
    
    IF array_length(missing_tables, 1) > 0 THEN
        RAISE EXCEPTION 'Integration orchestration schema deployment failed. Missing tables: %', array_to_string(missing_tables, ', ');
    END IF;
    
    RAISE NOTICE '✅ Integration orchestration schema deployed successfully. All % tables created.', array_length(expected_tables, 1);
END $$;

SELECT log_deployment_step('integration_orchestration_schema', 'completed');

\echo ''
\echo '============================================================================='
\echo 'STEP 4: DEPLOYMENT VALIDATION AND HEALTH CHECKS'
\echo '============================================================================='

SELECT log_deployment_step('deployment_validation', 'started');

-- Count total tables created
\echo 'Database schema summary:'
SELECT 
    schemaname,
    COUNT(*) as table_count
FROM pg_tables 
WHERE schemaname = 'public'
GROUP BY schemaname;

-- Count total indexes created
\echo 'Index summary:'
SELECT 
    schemaname,
    COUNT(*) as index_count
FROM pg_indexes 
WHERE schemaname = 'public'
GROUP BY schemaname;

-- Count total functions created
\echo 'Function summary:'
SELECT 
    n.nspname as schema_name,
    COUNT(*) as function_count
FROM pg_proc p
JOIN pg_namespace n ON p.pronamespace = n.oid
WHERE n.nspname = 'public'
AND p.prokind = 'f'
GROUP BY n.nspname;

-- Test core system health function
\echo 'Testing system health function:'
SELECT get_system_health();

-- Test learning system health function
\echo 'Testing learning system health function:'
SELECT get_learning_system_health();

-- Test integration system health function
\echo 'Testing integration system health function:'
SELECT get_integration_health();

-- Verify configuration data
\echo 'Verifying system configuration:'
SELECT 
    category,
    COUNT(*) as config_count
FROM system_configuration 
GROUP BY category
ORDER BY category;

-- Verify default agents
\echo 'Verifying default agents:'
SELECT 
    name,
    agent_type,
    is_active
FROM codegen_agents
ORDER BY name;

SELECT log_deployment_step('deployment_validation', 'completed');

\echo ''
\echo '============================================================================='
\echo 'DEPLOYMENT COMPLETED SUCCESSFULLY'
\echo '============================================================================='

-- Final deployment summary
SELECT log_deployment_step('deployment_complete', 'completed', NULL,
    jsonb_build_object(
        'total_tables', (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'),
        'total_indexes', (SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public'),
        'total_functions', (SELECT COUNT(*) FROM pg_proc p JOIN pg_namespace n ON p.pronamespace = n.oid WHERE n.nspname = 'public' AND p.prokind = 'f'),
        'deployment_duration', (SELECT MAX(duration) FROM deployment_log WHERE deployment_step = 'deployment_start')
    ));

-- Display deployment summary
\echo 'Deployment Summary:'
SELECT 
    deployment_step,
    status,
    duration,
    CASE 
        WHEN status = 'completed' THEN '✅'
        WHEN status = 'failed' THEN '❌'
        ELSE '⏳'
    END as status_icon
FROM deployment_log 
WHERE deployment_step != 'deployment_start'
ORDER BY start_time;

\echo ''
\echo '🎉 AUTONOMOUS DEVELOPMENT DATABASE DEPLOYMENT COMPLETE!'
\echo ''
\echo 'Next Steps:'
\echo '1. Configure Codegen SDK credentials in system_configuration'
\echo '2. Set up GitHub, Linear, and Slack integrations'
\echo '3. Create your first codebase entry'
\echo '4. Start autonomous development!'
\echo ''
\echo 'Health Check Commands:'
\echo '  SELECT get_system_health();'
\echo '  SELECT get_learning_system_health();'
\echo '  SELECT get_integration_health();'
\echo ''
\echo '============================================================================='

