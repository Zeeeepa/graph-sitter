# Comprehensive Database Schema Documentation

This directory contains the complete database schema design for the comprehensive graph-sitter enhancement system including Projects, Tasks, Analytics, Prompts, and Events modules with OpenEvolve integration.

## 🏗️ Architecture Overview

The database schema is designed with the following principles:

- **Modular Design**: Each module has its own schema file but shares common base elements
- **Scalability**: Optimized indexes and partitioning strategies for high-volume data
- **Flexibility**: JSONB fields for extensible metadata and configuration
- **Performance**: Comprehensive indexing strategy for sub-second queries
- **Data Integrity**: Foreign key constraints and validation functions
- **Monitoring**: Built-in health checks and performance monitoring
- **OpenEvolve Integration**: Context analysis engine for full codebase understanding
- **Self-Healing Architecture**: Error reporting and automated debugging systems

## 📊 Database Modules

### 1. Base Schema (`schemas/00_base_schema.sql`)
**Foundation for all modules**

- **Organizations**: Top-level tenant isolation
- **Users**: User management with role-based access
- **Common Types**: Shared enums and data types
- **Utility Functions**: Timestamp updates, ID generation

### 2. Projects Module (`schemas/01_projects_module.sql`)
**Top-level project organization and repository management**

- **Projects**: Project lifecycle with goals and timelines
- **Repositories**: Git repository management and configuration
- **Branches**: Repository branch tracking
- **Relationships**: Many-to-many project-repository mappings

### 3. Tasks Module (`schemas/02_tasks_module.sql`)
**Task lifecycle management and workflow orchestration**

- **Task Definitions**: Reusable task templates
- **Tasks**: Individual task executions with metadata
- **Dependencies**: Task dependency management
- **Workflows**: Multi-task orchestration
- **Resource Tracking**: CPU, memory, and execution monitoring

### 4. Analytics Module (`schemas/03_analytics_module.sql`)
**Codebase analysis and metrics storage**

- **Analysis Runs**: Track analysis executions
- **File Analysis**: File-level metrics and quality data
- **Code Elements**: Function/class/method analysis
- **Metrics**: Flexible metric storage system
- **Issues**: Code issues and violation tracking
- **Trends**: Historical trend analysis

### 5. Prompts Module (`schemas/04_prompts_module.sql`)
**Dynamic prompt management and effectiveness tracking**

- **Templates**: Reusable prompt templates with variables
- **Executions**: Prompt usage and performance tracking
- **Context Sources**: Dynamic context data management
- **Feedback**: User feedback and effectiveness scoring
- **A/B Testing**: Prompt variation testing

### 6. Events Module (`schemas/05_events_module.sql`)
**Integration event tracking and processing**

- **Event Types**: Event schema definitions
- **Events**: Universal event storage
- **Source-Specific**: Linear, Slack, GitHub, deployment events
- **Processing**: Event processing logs and status
- **Subscriptions**: Event routing and notifications

### 7. OpenEvolve Module (`schemas/06_openevolve_module.sql`)
**Context analysis engine and self-healing architecture**

- **Evaluations**: OpenEvolve evaluation tracking
- **Context Analysis**: Full codebase understanding
- **Error Classification**: Intelligent categorization of failure types
- **Root Cause Analysis**: Deep investigation of underlying issues
- **Learning Systems**: Pattern recognition and process refinement

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
   psql -f database/init/00_comprehensive_init.sql
   ```

2. **Load Schema Modules:**
   ```bash
   psql -f database/schemas/00_base_schema.sql
   psql -f database/schemas/01_projects_module.sql
   psql -f database/schemas/02_tasks_module.sql
   psql -f database/schemas/03_analytics_module.sql
   psql -f database/schemas/04_prompts_module.sql
   psql -f database/schemas/05_events_module.sql
   psql -f database/schemas/06_openevolve_module.sql
   ```

3. **Verify Installation:**
   ```sql
   SELECT * FROM system_health();
   SELECT * FROM data_quality_metrics();
   ```

## 🔧 Integration Points

### Contexten Extensions Integration
- **Linear Integration**: Enhanced implementation from `contexten/extensions/linear`
- **GitHub Integration**: Enhanced implementation from `contexten/extensions/git`
- **Slack Integration**: Event tracking and notification system

### Autogenlib Integration
- **Codegen API**: Effective implementation with org_id and token
- **Task Automation**: Automated task creation and execution
- **Code Generation**: On-demand missing code generation

### OpenEvolve Integration
- **Context Analysis**: Full codebase understanding engine
- **Error Reporting**: Automated debugging and retry mechanisms
- **Continuous Learning**: Pattern recognition and improvement

## 📈 Performance Optimization

### Indexing Strategy
- **Primary Keys**: UUID with B-tree indexes
- **Foreign Keys**: Automatic indexing for relationships
- **Composite Indexes**: Multi-column indexes for common query patterns
- **GIN Indexes**: JSONB and array field optimization
- **Partial Indexes**: Filtered indexes for soft-deleted records

### Monitoring
```sql
-- Overall database health
SELECT * FROM database_health_summary();

-- Performance analysis
SELECT * FROM performance_optimization_recommendations();

-- Module-specific metrics
SELECT * FROM tasks_performance_analysis();
SELECT * FROM events_performance_analysis();
SELECT * FROM analytics_performance_analysis();
```

## 🔄 Maintenance

### Automated Maintenance
```sql
-- Clean up old data
SELECT cleanup_old_events();
SELECT cleanup_expired_context_data();

-- Process pending events
SELECT process_pending_events(100);

-- Refresh analytics views
SELECT refresh_analytics_views();
```

### Health Monitoring
```sql
-- System health overview
SELECT * FROM system_health();

-- Data integrity checks
SELECT * FROM data_integrity_checks();

-- Critical alerts
SELECT * FROM critical_alerts();
```

## 📚 Documentation

- **Schema Files**: Individual module documentation in `schemas/`
- **Migration Scripts**: Version-controlled migrations in `migrations/`
- **Monitoring Queries**: Performance and health checks in `monitoring/`
- **Examples**: Working demonstrations in `examples/`

---

This comprehensive database schema provides the foundation for a fully autonomous, intelligent software development system that combines AI precision with systematic validation, creating a self-managing development ecosystem that continuously improves while delivering high-quality, production-ready code implementations.

