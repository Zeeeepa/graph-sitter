# 🚀 Database Schema Implementation Guide

## Overview

This guide provides step-by-step instructions for implementing the comprehensive 7-module database schema based on the research analysis of PRs 74, 75, 76, and 79. The implementation follows a phased approach to ensure safe deployment and optimal performance.

## Prerequisites

### System Requirements
- **PostgreSQL 14+** with required extensions
- **Python 3.8+** for automation scripts
- **Git** for version control
- **Minimum 4GB RAM** for database server
- **SSD storage** recommended for optimal performance

### Required PostgreSQL Extensions
```sql
-- Core extensions (required)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";    -- UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";     -- Cryptographic functions
CREATE EXTENSION IF NOT EXISTS "pg_trgm";      -- Text search optimization
CREATE EXTENSION IF NOT EXISTS "btree_gin";    -- Advanced indexing
CREATE EXTENSION IF NOT EXISTS "btree_gist";   -- Advanced indexing
```

### Environment Configuration
```bash
# Database connection
DATABASE_URL=postgresql://user:password@localhost:5432/graph_sitter
CODEGEN_ORG_ID=323
CODEGEN_TOKEN=your_codegen_token

# Optional platform integrations
LINEAR_API_KEY=your_linear_key
GITHUB_TOKEN=your_github_token
SLACK_TOKEN=your_slack_token
```

## Phase 1: Foundation Setup

### Step 1: Database Initialization
```bash
# Create database
createdb graph_sitter

# Set database configuration
psql -d graph_sitter -c "
SET timezone = 'UTC';
SET default_text_search_config = 'pg_catalog.english';
ALTER DATABASE graph_sitter SET timezone = 'UTC';
"
```

### Step 2: Load Comprehensive Schema
```bash
# Load the comprehensive schema
psql -d graph_sitter -f database/comprehensive_schema_v2.sql

# Verify installation
psql -d graph_sitter -c "SELECT get_system_health();"
```

### Step 3: Validate Installation
```sql
-- Check all modules are installed
SELECT 
    'organizations' as module,
    COUNT(*) as record_count
FROM organizations
UNION ALL
SELECT 'users', COUNT(*) FROM users
UNION ALL
SELECT 'projects', COUNT(*) FROM projects
UNION ALL
SELECT 'tasks', COUNT(*) FROM tasks
UNION ALL
SELECT 'pipelines', COUNT(*) FROM pipelines
UNION ALL
SELECT 'codegen_agents', COUNT(*) FROM codegen_agents
UNION ALL
SELECT 'github_integrations', COUNT(*) FROM github_integrations;

-- Verify system health
SELECT get_system_health();
```

## Phase 2: Configuration & Customization

### Step 1: Organization Setup
```sql
-- Update default organization with your details
UPDATE organizations 
SET 
    name = 'Your Organization Name',
    codegen_org_id = 'YOUR_CODEGEN_ORG_ID',
    api_token_hash = crypt('YOUR_CODEGEN_TOKEN', gen_salt('bf')),
    settings = jsonb_build_object(
        'features', ARRAY['codegen_sdk', 'platform_integrations', 'analytics'],
        'limits', jsonb_build_object(
            'max_tasks_per_month', 10000,
            'max_agents', 50,
            'max_projects', 100
        ),
        'notifications', jsonb_build_object(
            'email_enabled', true,
            'slack_enabled', true,
            'webhook_enabled', true
        )
    )
WHERE codegen_org_id = '323';
```

### Step 2: User Management
```sql
-- Add your users
INSERT INTO users (organization_id, email, name, role, permissions) VALUES 
((SELECT id FROM organizations WHERE codegen_org_id = 'YOUR_ORG_ID'),
 'admin@yourcompany.com', 'Admin User', 'admin', 
 '{"can_manage_agents": true, "can_create_projects": true, "can_view_analytics": true}'::jsonb),
((SELECT id FROM organizations WHERE codegen_org_id = 'YOUR_ORG_ID'),
 'developer@yourcompany.com', 'Developer User', 'developer',
 '{"can_create_tasks": true, "can_view_projects": true}'::jsonb);
```

### Step 3: Agent Configuration
```sql
-- Configure your Codegen agents
INSERT INTO codegen_agents (organization_id, name, agent_type, configuration, capabilities) VALUES 
((SELECT id FROM organizations WHERE codegen_org_id = 'YOUR_ORG_ID'),
 'Code Review Agent', 'reviewer', 
 jsonb_build_object(
     'model', 'claude-3-sonnet',
     'temperature', 0.1,
     'max_tokens', 4000,
     'timeout_seconds', 300
 ),
 '["code_review", "security_analysis", "performance_optimization"]'::jsonb),
((SELECT id FROM organizations WHERE codegen_org_id = 'YOUR_ORG_ID'),
 'Task Automation Agent', 'general',
 jsonb_build_object(
     'model', 'claude-3-sonnet',
     'temperature', 0.3,
     'max_tokens', 8000,
     'timeout_seconds', 600
 ),
 '["task_automation", "code_generation", "documentation", "testing"]'::jsonb);
```

## Phase 3: Integration Setup

### Step 1: GitHub Integration
```sql
-- Add GitHub integration for your projects
INSERT INTO github_integrations (
    project_id, 
    repository_owner, 
    repository_name, 
    access_token_hash,
    permissions
) VALUES (
    (SELECT id FROM projects WHERE name = 'Your Project'),
    'your-github-org',
    'your-repo-name',
    crypt('YOUR_GITHUB_TOKEN', gen_salt('bf')),
    jsonb_build_object(
        'read', true,
        'write', true,
        'admin', false,
        'webhooks', true
    )
);
```

### Step 2: Linear Integration
```sql
-- Add Linear integration
INSERT INTO linear_integrations (
    project_id,
    team_id,
    api_key_hash,
    sync_settings
) VALUES (
    (SELECT id FROM projects WHERE name = 'Your Project'),
    'YOUR_LINEAR_TEAM_ID',
    crypt('YOUR_LINEAR_API_KEY', gen_salt('bf')),
    jsonb_build_object(
        'sync_issues', true,
        'sync_comments', true,
        'auto_create_tasks', true,
        'sync_interval_minutes', 15
    )
);
```

### Step 3: Slack Integration
```sql
-- Add Slack integration
INSERT INTO slack_integrations (
    project_id,
    workspace_id,
    channel_id,
    bot_token_hash,
    notification_settings
) VALUES (
    (SELECT id FROM projects WHERE name = 'Your Project'),
    'YOUR_SLACK_WORKSPACE_ID',
    'YOUR_SLACK_CHANNEL_ID',
    crypt('YOUR_SLACK_BOT_TOKEN', gen_salt('bf')),
    jsonb_build_object(
        'notify_task_completion', true,
        'notify_errors', true,
        'daily_summary', true,
        'mention_users', true
    )
);
```

## Phase 4: Performance Optimization

### Step 1: Index Optimization
```sql
-- Verify all indexes are created
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes 
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

-- Check index usage
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats 
WHERE schemaname = 'public'
ORDER BY tablename, attname;
```

### Step 2: Query Performance Tuning
```sql
-- Enable query monitoring
ALTER SYSTEM SET log_min_duration_statement = 1000;
ALTER SYSTEM SET log_statement = 'all';
SELECT pg_reload_conf();

-- Create performance monitoring view
CREATE VIEW slow_queries AS
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    rows,
    100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
FROM pg_stat_statements
ORDER BY total_time DESC;
```

### Step 3: Materialized View Refresh
```sql
-- Set up automated refresh for materialized views
CREATE OR REPLACE FUNCTION refresh_all_materialized_views()
RETURNS VOID AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY daily_task_summary;
    REFRESH MATERIALIZED VIEW CONCURRENTLY agent_performance_summary;
    
    -- Log the refresh
    INSERT INTO system_metrics (metric_name, metric_type, value, unit)
    VALUES ('materialized_views_refreshed', 'maintenance', 1, 'count');
END;
$$ LANGUAGE plpgsql;

-- Schedule refresh (call from external scheduler)
-- Example: */15 * * * * psql -d graph_sitter -c "SELECT refresh_all_materialized_views();"
```

## Phase 5: Monitoring & Maintenance

### Step 1: Health Monitoring Setup
```sql
-- Create monitoring dashboard data
CREATE VIEW system_dashboard AS
SELECT 
    jsonb_build_object(
        'timestamp', NOW(),
        'system_health', get_system_health(),
        'active_tasks', (
            SELECT COUNT(*) FROM tasks 
            WHERE status IN ('pending', 'in_progress')
        ),
        'agent_utilization', (
            SELECT jsonb_object_agg(name, usage_stats)
            FROM codegen_agents 
            WHERE is_active = true
        ),
        'recent_errors', (
            SELECT jsonb_agg(jsonb_build_object(
                'task_id', id,
                'error', error_message,
                'timestamp', created_at
            ))
            FROM task_executions 
            WHERE status = 'failed' 
            AND created_at >= NOW() - INTERVAL '1 hour'
            LIMIT 10
        )
    ) as dashboard_data;
```

### Step 2: Automated Maintenance
```sql
-- Create maintenance schedule function
CREATE OR REPLACE FUNCTION daily_maintenance()
RETURNS JSONB AS $$
DECLARE
    cleanup_result JSONB;
    health_result JSONB;
BEGIN
    -- Perform data cleanup
    SELECT cleanup_old_data(90) INTO cleanup_result;
    
    -- Refresh materialized views
    PERFORM refresh_all_materialized_views();
    
    -- Update statistics
    ANALYZE;
    
    -- Check system health
    SELECT get_system_health() INTO health_result;
    
    -- Log maintenance completion
    INSERT INTO system_metrics (metric_name, metric_type, value, unit, context)
    VALUES (
        'daily_maintenance_completed', 
        'maintenance', 
        1, 
        'count',
        jsonb_build_object(
            'cleanup_result', cleanup_result,
            'health_status', health_result
        )
    );
    
    RETURN jsonb_build_object(
        'status', 'completed',
        'timestamp', NOW(),
        'cleanup', cleanup_result,
        'health', health_result
    );
END;
$$ LANGUAGE plpgsql;
```

### Step 3: Backup Strategy
```bash
#!/bin/bash
# backup_database.sh

# Configuration
DB_NAME="graph_sitter"
BACKUP_DIR="/backups/graph_sitter"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Full backup
pg_dump -Fc $DB_NAME > $BACKUP_DIR/full_backup_$DATE.dump

# Schema-only backup
pg_dump -s $DB_NAME > $BACKUP_DIR/schema_backup_$DATE.sql

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "*.dump" -mtime +30 -delete
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete

echo "Backup completed: $DATE"
```

## Phase 6: Application Integration

### Step 1: Connection Pool Configuration
```python
# database_config.py
import os
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

DATABASE_URL = os.getenv('DATABASE_URL')

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False
)
```

### Step 2: Basic API Integration
```python
# graph_sitter_client.py
import asyncio
import asyncpg
from typing import Dict, List, Optional

class GraphSitterClient:
    def __init__(self, database_url: str, codegen_org_id: str):
        self.database_url = database_url
        self.codegen_org_id = codegen_org_id
        self.pool = None
    
    async def initialize(self):
        self.pool = await asyncpg.create_pool(self.database_url)
    
    async def get_system_health(self) -> Dict:
        async with self.pool.acquire() as conn:
            result = await conn.fetchval("SELECT get_system_health()")
            return result
    
    async def create_task(self, title: str, description: str, task_type: str) -> str:
        async with self.pool.acquire() as conn:
            task_id = await conn.fetchval("""
                INSERT INTO tasks (organization_id, title, description, type)
                VALUES ((SELECT id FROM organizations WHERE codegen_org_id = $1), $2, $3, $4)
                RETURNING id
            """, self.codegen_org_id, title, description, task_type)
            return str(task_id)
    
    async def get_active_agents(self) -> List[Dict]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, name, agent_type, capabilities, usage_stats
                FROM codegen_agents
                WHERE organization_id = (SELECT id FROM organizations WHERE codegen_org_id = $1)
                AND is_active = true
            """, self.codegen_org_id)
            return [dict(row) for row in rows]
```

## Troubleshooting

### Common Issues

#### 1. Extension Installation Errors
```sql
-- Check available extensions
SELECT name, installed_version, default_version 
FROM pg_available_extensions 
WHERE name IN ('uuid-ossp', 'pgcrypto', 'pg_trgm', 'btree_gin');

-- Install missing extensions
CREATE EXTENSION IF NOT EXISTS "extension_name";
```

#### 2. Performance Issues
```sql
-- Check slow queries
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 10;

-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan ASC;
```

#### 3. Connection Issues
```sql
-- Check active connections
SELECT count(*), state
FROM pg_stat_activity
GROUP BY state;

-- Check connection limits
SHOW max_connections;
```

### Recovery Procedures

#### Database Corruption
```bash
# Check database integrity
pg_dump --schema-only graph_sitter > /dev/null

# Restore from backup if needed
pg_restore -d graph_sitter /backups/latest_backup.dump
```

#### Performance Degradation
```sql
-- Rebuild indexes
REINDEX DATABASE graph_sitter;

-- Update statistics
ANALYZE;

-- Vacuum full (during maintenance window)
VACUUM FULL;
```

## Security Considerations

### 1. Token Management
- Store all API tokens using `pgcrypto` encryption
- Rotate tokens regularly
- Use environment variables for sensitive configuration

### 2. Access Control
```sql
-- Create role-based access
CREATE ROLE graph_sitter_readonly;
CREATE ROLE graph_sitter_readwrite;
CREATE ROLE graph_sitter_admin;

-- Grant appropriate permissions
GRANT SELECT ON ALL TABLES IN SCHEMA public TO graph_sitter_readonly;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO graph_sitter_readwrite;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO graph_sitter_admin;
```

### 3. Network Security
- Use SSL connections for all database access
- Implement IP whitelisting
- Regular security audits

## Maintenance Schedule

### Daily
- Run `daily_maintenance()` function
- Check system health
- Monitor error logs

### Weekly
- Refresh materialized views
- Review performance metrics
- Update statistics

### Monthly
- Full database backup
- Security audit
- Performance optimization review

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review system health metrics
3. Examine recent error logs
4. Consult the comprehensive schema documentation

---

This implementation guide provides a complete roadmap for deploying the comprehensive 7-module database schema. Follow the phases sequentially for optimal results and minimal risk.

