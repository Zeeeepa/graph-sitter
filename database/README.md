# Database Schema Documentation

This directory contains comprehensive database schemas for the Graph-Sitter project, designed to support advanced code analysis, task management, and prompt orchestration.

## Architecture Overview

The database system is organized into three main modules:

### 1. Tasks Module (`/tasks/`)
Manages the complete lifecycle of development tasks, from creation to completion.

### 2. Analytics Module (`/analytics/`)
Stores comprehensive codebase analysis data including metrics, dependencies, and code quality indicators.

### 3. Prompts Module (`/prompts/`)
Handles dynamic prompt generation, template management, and context-aware AI interactions.

## Key Features

- **Modular Design**: Each module is self-contained with clear interfaces
- **Scalable Architecture**: Optimized for large codebases and high-volume operations
- **Graph-Sitter Integration**: Native support for all Graph-Sitter analysis features
- **Codegen API Integration**: Seamless integration with Codegen agents
- **Real-time Analytics**: Support for live code analysis and monitoring

## Database Initialization

1. Run the initialization scripts in order:
   ```bash
   # Initialize core tables
   psql -f database/init/00_core_tables.sql
   
   # Initialize tasks module
   psql -f database/tasks/models.sql
   
   # Initialize analytics module
   psql -f database/analytics/models.sql
   
   # Initialize prompts module
   psql -f database/prompts/models.sql
   ```

2. Load sample data (optional):
   ```bash
   psql -f database/init/sample_data.sql
   ```

## Environment Configuration

Set the following environment variables:

```bash
# Database connection
DATABASE_URL=postgresql://user:password@localhost:5432/graph_sitter_db

# Codegen API
CODEGEN_ORG_ID=323
CODEGEN_TOKEN=your_token_here

# Graph-Sitter configuration
GRAPH_SITTER_CACHE_DIR=/tmp/graph_sitter_cache
GRAPH_SITTER_MAX_FILE_SIZE=10485760
```

## Usage Examples

### Task Management
```sql
-- Create a new task
SELECT add_task('Implement user authentication', 'high', '{"framework": "FastAPI"}');

-- Add subtasks
SELECT add_subtask(task_id, 'Create user model', 'medium');
SELECT add_subtask(task_id, 'Implement JWT tokens', 'high');

-- Track progress
SELECT set_task_status(task_id, 'in_progress');
```

### Codebase Analysis
```sql
-- Analyze a codebase
SELECT analyze_codebase('/path/to/repo', 'python');

-- Get complexity metrics
SELECT * FROM get_complexity_metrics(codebase_id);

-- Find dead code
SELECT * FROM find_dead_code(codebase_id);
```

### Prompt Management
```sql
-- Add a new prompt template
SELECT add_prompt('code_review', 'Review this code for security issues: {code}');

-- Generate context-aware prompt
SELECT expand_prompt_full('code_review', '{"code": "def login(user, pass): ..."}');
```

## Performance Considerations

- **Indexing**: All frequently queried columns are properly indexed
- **Partitioning**: Large tables are partitioned by date/codebase for optimal performance
- **Caching**: Query results are cached where appropriate
- **Batch Operations**: Support for bulk operations on large datasets

## Monitoring and Maintenance

- **Health Checks**: Built-in health check queries
- **Performance Metrics**: Comprehensive performance monitoring
- **Cleanup Jobs**: Automated cleanup of old data
- **Backup Strategy**: Regular backups with point-in-time recovery

## Contributing

When adding new features:

1. Follow the existing naming conventions
2. Add appropriate indexes and constraints
3. Include comprehensive documentation
4. Write tests for new functionality
5. Update this README with any new features

## Support

For questions or issues:
- Check the Linear issue: [ZAM-1011](https://linear.app/zambe/issue/ZAM-1011)
- Review the Graph-Sitter documentation
- Consult the Codegen API reference

