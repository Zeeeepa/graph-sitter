# Graph-Sitter Database Schema

This directory contains the comprehensive database schema for the graph-sitter project, covering tasks, codebase analysis, prompts, and analytics.

## Directory Structure

```
database/
├── schema/
│   ├── models.sql              # Core database schema
│   ├── tasks/                  # Task management SQL files
│   ├── codebase/              # Codebase management SQL files
│   ├── prompts/               # Prompt management SQL files
│   └── analytics/             # Analytics and analysis SQL files
├── migrations/                # Database migration scripts
└── README.md                  # This file
```

## Schema Overview

### Core Tables

- **organizations**: Organization/project management
- **users**: User management and authentication
- **codebases**: Repository and codebase tracking
- **codebase_files**: File management within codebases
- **code_symbols**: Code elements (classes, functions, variables)
- **symbol_dependencies**: Code dependency relationships
- **tasks**: Task management system
- **prompts**: Prompt templates and versioning
- **analysis_runs**: Analysis execution tracking

### Analytics Tables

- **code_metrics**: Code quality metrics
- **dead_code_analysis**: Dead code detection results
- **dependency_analysis**: Dependency graph analysis
- **impact_analysis**: Change impact analysis

## SQL File Categories

### Tasks Module (`/tasks/`)

Complete task management system with 15 SQL files:

- `add-task.sql` - Create new tasks
- `add-subtask.sql` - Create subtasks
- `analyze-task-complexity.sql` - Calculate task complexity
- `clear-subtasks.sql` - Remove all subtasks
- `expand-all-tasks.sql` - Hierarchical task view
- `expand-task.sql` - Detailed single task view
- `find-next-task.sql` - Task prioritization
- `generate-task-files.sql` - Link tasks to files
- `is-task-dependent.sql` - Dependency checking
- `list-tasks.sql` - Task listing with filters
- `move-task.sql` - Task hierarchy management
- `parse-prd.sql` - Extract tasks from PRDs
- `remove-task.sql` - Task deletion
- `set-task-status.sql` - Status management
- `update-*.sql` - Various update operations

### Codebase Module (`/codebase/`)

Codebase management with 3 core files:

- `add-codebase.sql` - Register new codebases
- `update-codebase.sql` - Update codebase information
- `remove-codebase.sql` - Remove codebases with cleanup

### Prompts Module (`/prompts/`)

Prompt management with versioning:

- `add-prompt.sql` - Create new prompts
- `update-prompt.sql` - Update prompts with versioning
- `list-prompt-titles.sql` - List and search prompts
- `expand-prompt-full.sql` - Full prompt details

### Analytics Module (`/analytics/`)

Comprehensive code analysis:

- `analyze-codebase.sql` - Full codebase analysis
- `list-analysis-results.sql` - Analysis results with statistics
- `sync-active-track-changes-codebase.sql` - Incremental change tracking

## Key Features

### 1. Comprehensive Task Management
- Hierarchical task structure with subtasks
- Dependency tracking and validation
- Complexity analysis and estimation
- PRD parsing for automatic task creation
- Priority-based task recommendation

### 2. Advanced Code Analysis
- **Dependency Graph Analysis**: Maps code dependencies and detects circular references
- **Code Metrics**: Cyclomatic complexity, lines of code, maintainability index
- **Dead Code Detection**: Identifies unused functions, classes, and variables
- **Impact Analysis**: Calculates change impact radius
- **Incremental Analysis**: Tracks changes for efficient re-analysis

### 3. Intelligent Prompt Management
- Version control for prompt templates
- Category and tag-based organization
- Usage tracking and analytics
- Full-text search capabilities

### 4. Performance Optimization
- Comprehensive indexing strategy
- Full-text search with trigram indexes
- Efficient pagination support
- Optimized queries for large datasets

## Usage Examples

### Task Management
```sql
-- Create a new task
\i database/schema/tasks/add-task.sql
-- Parameters: organization_id, codebase_id, title, description, task_type, priority, assigned_to, created_by

-- Find next task to work on
\i database/schema/tasks/find-next-task.sql
-- Parameters: organization_id, assigned_to, codebase_id

-- Analyze task complexity
\i database/schema/tasks/analyze-task-complexity.sql
-- Parameters: task_id
```

### Codebase Analysis
```sql
-- Run comprehensive analysis
\i database/schema/analytics/analyze-codebase.sql
-- Parameters: codebase_id, analysis_type

-- List analysis results
\i database/schema/analytics/list-analysis-results.sql
-- Parameters: codebase_id, analysis_type, status, limit, offset
```

### Prompt Management
```sql
-- Add new prompt
\i database/schema/prompts/add-prompt.sql
-- Parameters: organization_id, title, description, content, prompt_type, category, tags, created_by

-- Search prompts
\i database/schema/prompts/list-prompt-titles.sql
-- Parameters: organization_id, prompt_type, category, is_active, search_term, limit, offset
```

## Migration System

The database includes a migration system for schema evolution:

1. **schema_migrations.sql**: Migration tracking table and functions
2. **001_initial_schema.sql**: Initial schema creation
3. Future migrations can be added as needed

### Running Migrations
```sql
-- Initialize migration system
\i database/migrations/schema_migrations.sql

-- Run initial migration
\i database/migrations/001_initial_schema.sql
```

## Integration with Graph-Sitter

This schema is designed to integrate seamlessly with the existing graph-sitter functionality:

- **Code Symbol Extraction**: Populates `code_symbols` table from AST analysis
- **Dependency Mapping**: Uses graph-sitter to identify symbol relationships
- **File Change Tracking**: Monitors file modifications for incremental analysis
- **Metrics Calculation**: Leverages AST data for complexity metrics

## Performance Considerations

- **Indexing**: Comprehensive indexes on frequently queried columns
- **Partitioning**: Consider partitioning large tables by organization or date
- **Archival**: Implement archival strategy for old analysis runs
- **Caching**: Use materialized views for expensive aggregate queries

## Security Features

- **UUID Primary Keys**: Prevents enumeration attacks
- **Organization Isolation**: All data scoped to organizations
- **Audit Trails**: Automatic timestamp tracking
- **Soft Deletes**: Preserves data integrity with `is_deleted` flags

## Future Enhancements

- **Real-time Analysis**: WebSocket integration for live updates
- **Machine Learning**: Integration with ML models for better predictions
- **API Documentation**: Automatic API doc generation from schema
- **Performance Monitoring**: Query performance tracking and optimization
- **Data Visualization**: Built-in dashboard queries for analytics

This schema provides a solid foundation for the graph-sitter project's data management needs while maintaining flexibility for future expansion and optimization.

