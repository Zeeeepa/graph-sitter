# Graph-Sitter Database Architecture

This directory contains the database schemas and initialization scripts for the graph-sitter system's 7 specialized databases.

## Overview

The graph-sitter system uses a **multi-database architecture** with 7 specialized databases, each optimized for specific domains:

| Database | Purpose | Key Features |
|----------|---------|--------------|
| **Task DB** | Task management and workflow orchestration | Task definitions, dependencies, workflows, resource monitoring |
| **Projects DB** | Project management and repository tracking | Projects, repositories, team management, cross-project analytics |
| **Prompts DB** | Template management and conditional prompts | Prompt templates, A/B testing, effectiveness tracking |
| **Codebase DB** | Code analysis results and metadata | Code elements, relationships, analysis runs, integration with adapters |
| **Analytics DB** | OpenEvolve integration and step analysis | Real-time analytics, performance data, quality scoring |
| **Events DB** | Multi-source event tracking | GitHub, Linear, Notion, Slack event ingestion and aggregation |
| **Learning DB** | Pattern recognition and improvement tracking | Learning models, training sessions, adaptations, evolution |

## Quick Start

### Prerequisites

- PostgreSQL 12+ installed and running
- TimescaleDB extension (optional, for time-series optimization)
- Sufficient permissions to create databases and users

### Setup All Databases

Run the setup script to initialize all databases:

```bash
cd database
./setup_all_databases.sh
```

### Environment Variables

You can customize the setup using environment variables:

```bash
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_ADMIN_USER=postgres
export POSTGRES_ADMIN_PASSWORD=your_password

./setup_all_databases.sh
```

## Database Details

### 1. Task DB (`task_db`)

**Purpose**: Comprehensive task management with workflow orchestration and resource monitoring.

**Key Tables**:
- `task_definitions` - Reusable task templates
- `tasks` - Main tasks with hierarchy support
- `dependencies` - Task dependency management
- `workflows` - Workflow definitions and orchestration

**User**: `task_user` / `task_secure_2024!`

**Features**:
- Hierarchical task structure
- Circular dependency detection
- Resource usage tracking
- Workflow execution monitoring

### 2. Projects DB (`projects_db`)

**Purpose**: Project management, repository tracking, and team management.

**Key Tables**:
- `projects` - Project definitions and tracking
- `repositories` - Repository metadata and statistics
- `project_repositories` - Many-to-many project-repository relationships
- `project_teams` - Team member management

**User**: `projects_user` / `projects_secure_2024!`

**Features**:
- Cross-project analytics
- Repository integration (GitHub, GitLab, etc.)
- Team collaboration tracking
- Project milestone management

### 3. Prompts DB (`prompts_db`)

**Purpose**: Template management, conditional prompts, and A/B testing.

**Key Tables**:
- `prompt_templates` - Template definitions with versioning
- `executions` - Prompt execution tracking
- `context_sources` - Context data for prompt enrichment
- `ab_experiments` - A/B testing experiments

**User**: `prompts_user` / `prompts_secure_2024!`

**Features**:
- Template versioning and management
- A/B testing framework
- Effectiveness tracking
- Context-aware prompting

### 4. Codebase DB (`codebase_db`)

**Purpose**: Code analysis results, metadata, and relationships. Integrates with existing `codebase_analysis.py`.

**Key Tables**:
- `codebases` - Codebase metadata and statistics
- `file_analysis` - File-level analysis results
- `code_elements` - Functions, classes, variables, etc.
- `relationships` - Code element relationships and dependencies

**User**: `codebase_user` / `codebase_secure_2024!`

**Features**:
- Integration with existing adapters
- Symbol tracking and relationship mapping
- Complexity analysis
- Dependency management

### 5. Analytics DB (`analytics_db`)

**Purpose**: OpenEvolve integration, step analysis, and real-time analytics.

**Key Tables**:
- `analysis_runs` - Analysis execution tracking
- `metrics` - Time-series metrics data (TimescaleDB optimized)
- `performance_data` - Detailed performance tracking
- `dashboards` - Real-time dashboard configurations

**User**: `analytics_user` / `analytics_secure_2024!`

**Features**:
- OpenEvolve integration
- Time-series optimization with TimescaleDB
- Real-time analytics and alerting
- Performance trend analysis

### 6. Events DB (`events_db`)

**Purpose**: Multi-source event ingestion and aggregation.

**Key Tables**:
- `event_sources` - Source configurations (GitHub, Linear, etc.)
- `events` - Time-series event data (TimescaleDB optimized)
- `event_aggregations` - Pre-computed event summaries
- `subscriptions` - Real-time event subscriptions

**User**: `events_user` / `events_secure_2024!`

**Features**:
- Multi-source event ingestion (GitHub, Linear, Notion, Slack)
- Real-time event processing
- Event pattern detection
- Subscription-based notifications

### 7. Learning DB (`learning_db`)

**Purpose**: Pattern recognition, continuous learning, and evolution integration.

**Key Tables**:
- `learning_models` - ML model registry and metadata
- `training_sessions` - Training execution tracking
- `adaptations` - Continuous improvement tracking
- `evolution_sessions` - OpenEvolve integration

**User**: `learning_user` / `learning_secure_2024!`

**Features**:
- ML model lifecycle management
- Training metrics tracking (TimescaleDB optimized)
- Continuous adaptation and improvement
- Evolution integration

## Special Users

### Analytics Read-Only User
- **User**: `analytics_readonly` / `analytics_readonly_2024!`
- **Purpose**: Cross-database analytics and reporting
- **Access**: Read-only access to all databases

### Admin User
- **User**: `graph_sitter_admin` / `admin_secure_2024!`
- **Purpose**: Database administration and maintenance
- **Access**: Superuser privileges

## File Structure

```
database/
├── README.md                    # This documentation
├── init_databases.sql          # Database and user creation
├── setup_all_databases.sh      # Complete setup script
└── schemas/
    ├── 01_task_db.sql          # Task database schema
    ├── 02_projects_db.sql      # Projects database schema
    ├── 03_prompts_db.sql       # Prompts database schema
    ├── 04_codebase_db.sql      # Codebase database schema
    ├── 05_analytics_db.sql     # Analytics database schema
    ├── 06_events_db.sql        # Events database schema
    └── 07_learning_db.sql      # Learning database schema
```

## Integration Points

### Existing Codebase Integration

The **Codebase DB** is designed to integrate seamlessly with existing components:

- `src/graph_sitter/adapters/codebase_db_adapter.py` - Database adapter
- `src/graph_sitter/adapters/database.py` - General database utilities
- `src/graph_sitter/codebase/codebase_analysis.py` - Analysis functions

### Cross-Database Analytics

The `analytics_readonly` user enables cross-database queries for:
- Comprehensive system analytics
- Cross-domain insights
- Performance correlation analysis
- System-wide reporting

## Time-Series Optimization

Several databases use **TimescaleDB** for time-series optimization:

- **Analytics DB**: `metrics` and `performance_data` tables
- **Events DB**: `events` and `event_aggregations` tables  
- **Learning DB**: `training_metrics` table

If TimescaleDB is not available, the system will function normally without time-series optimization.

## Security Considerations

- Each database has a dedicated user with minimal required privileges
- Passwords follow a secure pattern (change in production)
- Cross-database access is limited to the analytics read-only user
- All connections should use SSL in production environments

## Maintenance

### Backup Strategy

```bash
# Backup all databases
for db in task_db projects_db prompts_db codebase_db analytics_db events_db learning_db; do
    pg_dump -h localhost -U postgres $db > backup_${db}_$(date +%Y%m%d).sql
done
```

### Monitoring

Key metrics to monitor:
- Database sizes and growth rates
- Query performance and slow queries
- Connection counts and user activity
- Time-series data retention (for TimescaleDB tables)

### Updates

When updating schemas:
1. Test changes on a development environment
2. Create database backups before applying changes
3. Use migration scripts for data preservation
4. Update adapter code if schema changes affect integration points

## Troubleshooting

### Common Issues

1. **TimescaleDB not available**: System will work without time-series optimization
2. **Permission errors**: Ensure PostgreSQL user has sufficient privileges
3. **Connection failures**: Check PostgreSQL service status and network connectivity
4. **Schema conflicts**: Drop and recreate databases if needed (development only)

### Logs and Debugging

- PostgreSQL logs: Check for connection and query errors
- Application logs: Monitor adapter integration points
- Performance: Use `pg_stat_statements` for query analysis

## Contributing

When adding new features:
1. Follow the established naming conventions
2. Add appropriate indexes for performance
3. Include JSONB fields for extensibility
4. Update this documentation
5. Test with the existing adapter integration

---

For questions or issues, please refer to the main graph-sitter documentation or create an issue in the repository.

