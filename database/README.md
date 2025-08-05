# Comprehensive Database Schema Documentation

This directory contains the complete database schema design for the 5-module system including Projects, Tasks, Analytics, Prompts, and Events modules.

## 📁 Directory Structure

```
database/
├── schemas/           # SQL schema files for each module
├── migrations/        # Version-controlled database migrations
├── scripts/          # Initialization and utility scripts
├── monitoring/       # Health checks and performance queries
└── README.md         # This documentation
```

## 🏗️ Architecture Overview

The database schema is designed with the following principles:

- **Modular Design**: Each module has its own schema file but shares common base elements
- **Scalability**: Optimized indexes and partitioning strategies for high-volume data
- **Flexibility**: JSONB fields for extensible metadata and configuration
- **Performance**: Comprehensive indexing strategy for sub-second queries
- **Data Integrity**: Foreign key constraints and validation functions
- **Monitoring**: Built-in health checks and performance monitoring

## 📊 Database Modules

### 1. Base Schema (`00_base_schema.sql`)
**Foundation for all modules**

- **Organizations**: Top-level tenant isolation
- **Users**: User management with role-based access
- **Common Types**: Shared enums and data types
- **Utility Functions**: Timestamp updates, ID generation

**Key Tables:**
- `organizations` - Multi-tenant organization management
- `users` - User accounts with preferences and metadata

### 2. Projects Module (`01_projects_module.sql`)
**Top-level project organization and repository management**

- **Projects**: Project lifecycle with goals and timelines
- **Repositories**: Git repository management and configuration
- **Branches**: Repository branch tracking
- **Relationships**: Many-to-many project-repository mappings

**Key Tables:**
- `projects` - Project management with status and priorities
- `repositories` - Repository metadata and configuration
- `repository_branches` - Branch tracking with commit information
- `project_repositories` - Project-repository relationships

**Key Features:**
- Project status tracking (planning → active → completed)
- Repository analysis configuration
- Cross-project analytics support
- Team member management

### 3. Tasks Module (`02_tasks_module.sql`)
**Task lifecycle management and workflow orchestration**

- **Task Definitions**: Reusable task templates
- **Tasks**: Individual task executions with metadata
- **Dependencies**: Task dependency management
- **Workflows**: Multi-task orchestration
- **Resource Tracking**: CPU, memory, and execution monitoring

**Key Tables:**
- `task_definitions` - Reusable task templates with resource requirements
- `tasks` - Task instances with execution tracking
- `task_dependencies` - Dependency management for workflow orchestration
- `workflows` - Multi-task workflow coordination
- `task_execution_logs` - Detailed execution logging
- `task_resource_usage` - Resource consumption monitoring

**Key Features:**
- Flexible JSONB metadata for task configuration
- Dependency resolution with circular reference prevention
- Resource usage monitoring and optimization
- Retry logic with exponential backoff
- Workflow orchestration (sequential, parallel, DAG)

### 4. Analytics Module (`03_analytics_module.sql`)
**Codebase analysis and metrics storage**

- **Analysis Runs**: Track analysis executions
- **File Analysis**: File-level metrics and quality data
- **Code Elements**: Function/class/method analysis
- **Metrics**: Flexible metric storage system
- **Issues**: Code issues and violation tracking
- **Trends**: Historical trend analysis

**Key Tables:**
- `analysis_runs` - Analysis execution tracking
- `file_analysis` - File-level analysis results
- `code_element_analysis` - Function/class/method analysis
- `metrics` - Flexible metric storage
- `performance_metrics` - Performance-specific measurements
- `issues` - Code issues and violations
- `metric_trends` - Historical trend tracking

**Key Features:**
- Multi-tool analysis support (SonarQube, ESLint, etc.)
- Hierarchical code element analysis
- Performance and complexity metrics
- Issue severity and resolution tracking
- Trend analysis for quality improvement
- Quality score calculation

### 5. Prompts Module (`04_prompts_module.sql`)
**Dynamic prompt management and effectiveness tracking**

- **Templates**: Reusable prompt templates with variables
- **Executions**: Prompt usage and performance tracking
- **Context Sources**: Dynamic context data management
- **Feedback**: User feedback and effectiveness scoring
- **A/B Testing**: Prompt variation testing

**Key Tables:**
- `prompt_templates` - Reusable prompt templates
- `prompt_executions` - Execution tracking and results
- `context_sources` - Context data source management
- `context_data` - Cached context content
- `prompt_feedback` - User feedback collection
- `prompt_variations` - A/B testing variations

**Key Features:**
- Variable substitution and context injection
- Model parameter configuration
- Effectiveness scoring and optimization
- Context caching with expiration
- A/B testing for prompt optimization
- Cost tracking and optimization

### 6. Events Module (`05_events_module.sql`)
**Integration event tracking and processing**

- **Event Types**: Event schema definitions
- **Events**: Universal event storage
- **Source-Specific**: Linear, Slack, GitHub, deployment events
- **Processing**: Event processing logs and status
- **Subscriptions**: Event routing and notifications

**Key Tables:**
- `event_types` - Event schema and processing configuration
- `events` - Universal event storage
- `linear_events` - Linear-specific event data
- `slack_events` - Slack-specific event data
- `github_events` - GitHub-specific event data
- `deployment_events` - Deployment tracking
- `event_subscriptions` - Event routing configuration

**Key Features:**
- Multi-source event ingestion
- Flexible payload storage with JSONB
- Event processing pipeline with retry logic
- Source-specific event enrichment
- Event routing and subscription management
- Deduplication and idempotency

## 🚀 Getting Started

### Prerequisites

- PostgreSQL 14+ with extensions:
  - `uuid-ossp` - UUID generation
  - `pg_trgm` - Text search optimization
  - `btree_gin` - Advanced indexing
  - `btree_gist` - Advanced indexing

### Installation

1. **Initialize Database:**
   ```bash
   psql -f database/scripts/init_database.sql
   ```

2. **Load Seed Data:**
   ```bash
   psql -f database/scripts/seed_data.sql
   ```

3. **Verify Installation:**
   ```sql
   SELECT * FROM system_health;
   SELECT * FROM data_quality_metrics;
   ```

### Migration Management

Migrations are tracked in the `schema_migrations` table:

```sql
-- Check current schema version
SELECT * FROM schema_migrations ORDER BY applied_at DESC;

-- Apply new migration
\i database/migrations/002_new_feature.sql
```

## 📈 Performance Optimization

### Indexing Strategy

The schema includes comprehensive indexing:

- **Primary Keys**: UUID with B-tree indexes
- **Foreign Keys**: Automatic indexing for relationships
- **Composite Indexes**: Multi-column indexes for common query patterns
- **GIN Indexes**: JSONB and array field optimization
- **Partial Indexes**: Filtered indexes for soft-deleted records
- **Text Search**: Full-text search indexes for content

### Query Optimization

Key optimization features:

- **Materialized Views**: Pre-computed aggregations
- **Partitioning**: Time-based partitioning for large tables
- **Connection Pooling**: Optimized for high-concurrency workloads
- **Query Monitoring**: Built-in slow query detection

### Performance Monitoring

Use the monitoring views:

```sql
-- Overall database health
SELECT * FROM database_health_summary;

-- Slow query analysis
SELECT * FROM slow_query_analysis;

-- Index usage patterns
SELECT * FROM index_usage_analysis;

-- Module-specific performance
SELECT * FROM tasks_performance_analysis;
SELECT * FROM events_performance_analysis;
SELECT * FROM analytics_performance_analysis;
```

## 🔍 Monitoring and Maintenance

### Health Checks

Regular health monitoring:

```sql
-- System health overview
SELECT * FROM system_health;

-- Data integrity checks
SELECT * FROM data_integrity_checks;

-- Critical alerts
SELECT * FROM critical_alerts;

-- Maintenance recommendations
SELECT * FROM maintenance_recommendations;
```

### Automated Maintenance

The schema includes automated maintenance functions:

```sql
-- Clean up old events (respects retention policies)
SELECT cleanup_old_events();

-- Clean up expired context data
SELECT cleanup_expired_context_data();

-- Process pending events
SELECT process_pending_events(100);
```

### Backup and Recovery

**Backup Strategy:**
- Daily full backups
- Continuous WAL archiving
- Point-in-time recovery capability

**Backup Commands:**
```bash
# Full backup
pg_dump -Fc codegen_platform > backup_$(date +%Y%m%d).dump

# Schema-only backup
pg_dump -s codegen_platform > schema_backup.sql

# Data-only backup
pg_dump -a codegen_platform > data_backup.sql
```

## 🔧 Configuration

### Database Settings

Recommended PostgreSQL configuration:

```sql
-- Memory settings
shared_buffers = '256MB'
work_mem = '16MB'
maintenance_work_mem = '64MB'

-- Connection settings
max_connections = 200
shared_preload_libraries = 'pg_stat_statements'

-- Logging
log_min_duration_statement = 1000
log_checkpoints = on
log_connections = on
log_disconnections = on
```

### Application Settings

Environment variables for application configuration:

```bash
# Database connection
DATABASE_URL=postgresql://user:password@localhost:5432/codegen_platform

# Connection pooling
DATABASE_POOL_SIZE=20
DATABASE_POOL_TIMEOUT=30

# Monitoring
ENABLE_QUERY_MONITORING=true
SLOW_QUERY_THRESHOLD_MS=1000
```

## 📚 API Integration

### Common Query Patterns

**Project Management:**
```sql
-- Get project with repositories
SELECT p.*, array_agg(r.name) as repositories
FROM projects p
LEFT JOIN project_repositories pr ON p.id = pr.project_id
LEFT JOIN repositories r ON pr.repository_id = r.id
WHERE p.organization_id = $1 AND p.deleted_at IS NULL
GROUP BY p.id;
```

**Task Execution:**
```sql
-- Get ready-to-run tasks
SELECT t.*
FROM tasks t
WHERE t.status = 'pending'
AND t.scheduled_at <= CURRENT_TIMESTAMP
AND are_task_dependencies_satisfied(t.id) = true
ORDER BY t.priority DESC, t.scheduled_at ASC;
```

**Analytics Queries:**
```sql
-- Repository quality overview
SELECT * FROM repository_quality_overview
WHERE repository_id = $1;

-- Calculate quality score
SELECT calculate_quality_score($1) as quality_score;
```

**Event Processing:**
```sql
-- Process events by subscription
SELECT e.* FROM events e
JOIN event_subscriptions es ON check_subscription_match(e.id, es.id)
WHERE e.status = 'pending' AND es.is_active = true;
```

## 🛠️ Troubleshooting

### Common Issues

**Slow Queries:**
```sql
-- Identify slow queries
SELECT * FROM slow_query_analysis WHERE priority = 'critical';

-- Check missing indexes
SELECT * FROM performance_optimization_recommendations 
WHERE category = 'indexing';
```

**High Resource Usage:**
```sql
-- Check resource utilization
SELECT * FROM database_resource_utilization;

-- Identify resource-intensive tasks
SELECT * FROM task_resource_usage 
WHERE measured_at >= CURRENT_TIMESTAMP - INTERVAL '1 hour'
ORDER BY cpu_usage_percent DESC;
```

**Data Quality Issues:**
```sql
-- Run integrity checks
SELECT * FROM data_integrity_checks WHERE status = 'fail';

-- Check for orphaned records
SELECT check_name, issue_count FROM data_integrity_checks;
```

### Performance Tuning

**Index Optimization:**
```sql
-- Find unused indexes
SELECT * FROM index_usage_analysis WHERE usage_status = 'unused';

-- Identify missing indexes
SELECT * FROM table_access_patterns 
WHERE recommendation LIKE '%Consider adding indexes%';
```

**Query Optimization:**
```sql
-- Analyze query performance
EXPLAIN (ANALYZE, BUFFERS) SELECT ...;

-- Update table statistics
ANALYZE;
```

## 📞 Support

For issues and questions:

1. Check the monitoring views for system health
2. Review the troubleshooting section
3. Examine the performance optimization recommendations
4. Consult the schema documentation for specific modules

## 🔄 Schema Evolution

The schema is designed for evolution:

- **Backward Compatibility**: New columns are nullable or have defaults
- **Migration Scripts**: All changes are tracked in migrations
- **Versioning**: Schema versions are tracked in `schema_migrations`
- **Rollback Support**: Each migration includes rollback instructions

## 📋 Best Practices

1. **Always use transactions** for schema changes
2. **Test migrations** on a copy of production data
3. **Monitor performance** after schema changes
4. **Use JSONB sparingly** - prefer structured columns when possible
5. **Regular maintenance** - vacuum, analyze, and reindex as needed
6. **Backup before migrations** - always have a recovery plan

---

This comprehensive database schema provides a solid foundation for the 5-module system with optimal performance, scalability, and maintainability.

