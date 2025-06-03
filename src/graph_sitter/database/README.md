# Graph-Sitter Database Module

Comprehensive database integration for the graph-sitter codebase analysis system, providing SQLAlchemy models, connection management, and integration adapters for a 7-module database schema.

## Overview

This module implements a complete database layer that seamlessly integrates with existing graph-sitter functionality while providing enhanced persistence, analytics, and workflow management capabilities.

### 7-Module Architecture

1. **Organizations & Users** - Multi-tenant foundation with role-based access
2. **Projects & Repositories** - Project management and repository tracking  
3. **Tasks & Workflows** - Task lifecycle and workflow orchestration
4. **Analytics & Codebase Analysis** - Analysis results and metrics storage
5. **Prompts & Templates** - Dynamic prompt management for AI workflows
6. **Events & Integrations** - Event tracking for Linear, GitHub, Slack
7. **Learning & OpenEvolve** - Continuous learning and system improvement

## Quick Start

### Installation

```bash
# Install required dependencies
pip install sqlalchemy psycopg2-binary alembic

# Set up environment variables
export DATABASE_URL="postgresql://user:password@localhost:5432/graph_sitter"
export ENVIRONMENT="development"
```

### Basic Usage

```python
from graph_sitter.database import (
    get_database_session, Organization, User, Repository, 
    analyze_codebase_with_storage
)
from graph_sitter.core.codebase import Codebase

# Get database session
with get_database_session() as session:
    # Create organization
    org = Organization(name="My Company", slug="my-company")
    session.add(org)
    session.commit()
    
    # Create user
    user = User(email="user@example.com", name="John Doe")
    session.add(user)
    
    # Add user to organization
    org.add_user(session, user, role="admin")
    session.commit()

# Analyze codebase with database storage
codebase = Codebase.from_directory("/path/to/code")
analysis_run = analyze_codebase_with_storage(
    codebase=codebase,
    repository_id=str(repository.id),
    organization_id=str(org.id),
    commit_sha="abc123",
    branch_name="main"
)

print(f"Analysis completed with quality score: {analysis_run.quality_score}")
```

## Configuration

### Environment Variables

```bash
# Database connection
DATABASE_URL=postgresql://user:password@localhost:5432/graph_sitter

# Connection pooling
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_TIMEOUT=30

# Performance monitoring
DB_ENABLE_QUERY_MONITORING=true
DB_SLOW_QUERY_THRESHOLD_MS=1000

# Environment
ENVIRONMENT=development  # development, test, production
```

### Programmatic Configuration

```python
from graph_sitter.database.config import DatabaseConfig, set_database_config

# Custom configuration
config = DatabaseConfig(
    url="postgresql://localhost:5432/my_db",
    pool_size=50,
    enable_query_monitoring=True,
    slow_query_threshold_ms=500
)

set_database_config(config)
```

## Database Schema

### Organizations & Users Module

Multi-tenant architecture with row-level security:

```python
from graph_sitter.database import Organization, User, OrganizationMembership

# Create organization
org = Organization(name="Acme Corp", slug="acme-corp")

# Create user with external platform integration
user = User(
    email="developer@acme.com",
    name="Jane Developer",
    external_ids={
        "github": "jane-dev",
        "linear": "user-123",
        "slack": "U123456"
    }
)

# Add user to organization with role
membership = org.add_user(session, user, role="admin")
```

### Projects & Repositories Module

Project organization and repository tracking:

```python
from graph_sitter.database import Project, Repository

# Create project
project = Project(
    organization_id=str(org.id),
    name="Web Platform",
    slug="web-platform",
    description="Main web platform project"
)

# Create repository
repository = Repository(
    organization_id=str(org.id),
    project_id=str(project.id),
    full_name="acme-corp/web-platform",
    name="web-platform",
    owner="acme-corp",
    language="python"
)
```

### Analytics & Codebase Analysis Module

Integration with existing codebase analysis:

```python
from graph_sitter.database.adapters import CodebaseAnalysisAdapter
from graph_sitter.core.codebase import Codebase

# Analyze codebase and store results
adapter = CodebaseAnalysisAdapter()
codebase = Codebase.from_directory("/path/to/code")

analysis_run = adapter.analyze_and_store_codebase(
    codebase=codebase,
    repository_id=str(repository.id),
    organization_id=str(org.id),
    commit_sha="abc123def",
    branch_name="main",
    project_id=str(project.id)
)

# Get analysis results
print(f"Quality Score: {analysis_run.quality_score}")
print(f"Total Issues: {analysis_run.total_issues}")
print(f"Complexity Score: {analysis_run.complexity_score}")

# Get file-level analysis
for file_analysis in analysis_run.file_analyses:
    print(f"File: {file_analysis.file_path}")
    print(f"  Lines of Code: {file_analysis.lines_of_code}")
    print(f"  Complexity: {file_analysis.cyclomatic_complexity}")
    print(f"  Issues: {file_analysis.issue_count}")
```

### Tasks & Workflows Module

Task management and workflow orchestration:

```python
from graph_sitter.database import TaskDefinition, Task, Workflow

# Create reusable task definition
task_def = TaskDefinition(
    organization_id=str(org.id),
    name="Code Analysis",
    task_type="analysis",
    description="Analyze repository code quality",
    estimated_duration_minutes=30
)

# Create task instance
task = task_def.create_task_instance(
    session,
    title="Analyze main branch",
    repository_id=str(repository.id),
    assignee_id=str(user.id)
)

# Create workflow
workflow = Workflow(
    organization_id=str(org.id),
    name="CI/CD Pipeline",
    workflow_type="sequential",
    project_id=str(project.id)
)

# Start task execution
task.start_task()
# ... perform work ...
task.complete_task({"analysis_completed": True})
```

### Events & Integrations Module

Event tracking for external integrations:

```python
from graph_sitter.database import Event, LinearEvent, GitHubEvent

# Create GitHub event
github_event = Event(
    organization_id=str(org.id),
    source="github",
    type="pr_opened",
    title="New pull request opened",
    repository_id=str(repository.id),
    actor_name="jane-dev",
    external_id="123",
    event_data={
        "pr_number": 123,
        "title": "Add new feature",
        "author": "jane-dev"
    }
)

# Create Linear event
linear_event = Event(
    organization_id=str(org.id),
    source="linear",
    type="issue_created",
    title="New issue created",
    project_id=str(project.id),
    external_id="ISS-456"
)
```

## Performance Features

### Connection Pooling

Optimized connection pooling with monitoring:

```python
from graph_sitter.database import get_database_connection

# Get connection with health check
connection = get_database_connection()
health = connection.health_check()

print(f"Database Status: {health['status']}")
print(f"Active Connections: {health['active_connections']}")
print(f"Pool Status: {health['pool_status']}")
```

### Query Monitoring

Automatic slow query detection and logging:

```python
from graph_sitter.database import get_database_statistics

# Get query performance statistics
stats = get_database_statistics()
print(f"Total Queries: {stats['total_queries']}")
print(f"Slow Queries: {stats['slow_queries']} ({stats['slow_query_percentage']}%)")
print(f"Average Query Time: {stats['avg_query_time_ms']}ms")
```

### Caching and Optimization

Built-in caching and query optimization:

```python
# Materialized views for analytics
from graph_sitter.database.performance import refresh_analytics_views

# Refresh analytics views for better performance
refresh_analytics_views()

# Get repository quality trends efficiently
from graph_sitter.database.adapters import get_repository_quality_trend

trend = get_repository_quality_trend(str(repository.id), days=30)
for point in trend:
    print(f"Date: {point['date']}, Quality: {point['quality_score']}")
```

## Integration with Existing Code

### Backward Compatibility

The database module maintains full backward compatibility with existing graph-sitter functionality:

```python
# Existing code continues to work
from graph_sitter.codebase.codebase_analysis import get_codebase_summary
from graph_sitter.core.codebase import Codebase

codebase = Codebase.from_directory("/path/to/code")
summary = get_codebase_summary(codebase)  # Still works as before

# Enhanced with database storage
from graph_sitter.database.adapters import analyze_codebase_with_storage

# Same codebase, now with database persistence
analysis_run = analyze_codebase_with_storage(
    codebase=codebase,
    repository_id=repository_id,
    organization_id=organization_id,
    commit_sha=commit_sha
)
```

### Migration from Existing Systems

```python
# Migrate existing analysis results
from graph_sitter.database.adapters import CodebaseAnalysisAdapter

adapter = CodebaseAnalysisAdapter()

# Analyze existing codebases and store in database
for repo_path in existing_repositories:
    codebase = Codebase.from_directory(repo_path)
    analysis_run = adapter.analyze_and_store_codebase(
        codebase=codebase,
        repository_id=get_repository_id(repo_path),
        organization_id=organization_id,
        commit_sha=get_current_commit(repo_path)
    )
    print(f"Migrated {repo_path}: Quality Score {analysis_run.quality_score}")
```

## Testing

### Unit Tests

```bash
# Run database unit tests
pytest tests/unit/database/

# Run specific test file
pytest tests/unit/database/test_database_config.py -v

# Run with coverage
pytest tests/unit/database/ --cov=src.graph_sitter.database
```

### Integration Tests

```bash
# Run integration tests (requires test database)
pytest tests/integration/database/

# Set up test database
export TEST_DATABASE_URL="postgresql://test:test@localhost:5432/graph_sitter_test"
pytest tests/integration/database/test_analysis_integration.py
```

### Test Database Setup

```python
from graph_sitter.database.config import get_test_config, set_database_config
from graph_sitter.database import Base, get_database_connection

# Configure for testing
config = get_test_config()
set_database_config(config)

# Create test tables
connection = get_database_connection()
Base.metadata.create_all(connection.engine)
```

## Monitoring and Maintenance

### Health Checks

```python
from graph_sitter.database import database_health_check

health = database_health_check()
if health['status'] == 'healthy':
    print("Database is healthy")
    print(f"Response time: {health['response_time_ms']}ms")
else:
    print(f"Database issue: {health.get('error')}")
```

### Performance Monitoring

```python
from graph_sitter.database.performance import get_performance_metrics

metrics = get_performance_metrics()
print(f"Query performance: {metrics['query_performance']}")
print(f"Index usage: {metrics['index_usage']}")
```

### Maintenance Tasks

```python
from graph_sitter.database.performance import perform_maintenance

# Run maintenance tasks
result = perform_maintenance()
print(f"Maintenance completed: {result['actions_performed']}")
```

## Advanced Usage

### Custom Models

```python
from graph_sitter.database.base import DatabaseModel, TimestampMixin

class CustomModel(DatabaseModel, TimestampMixin):
    __tablename__ = 'custom_table'
    
    name = Column(String(255), nullable=False)
    data = Column(JSON, default=dict)
    
    def custom_method(self):
        return f"Custom: {self.name}"
```

### Raw SQL Queries

```python
from graph_sitter.database import get_database_session
from sqlalchemy import text

with get_database_session() as session:
    result = session.execute(text("""
        SELECT r.name, COUNT(ar.id) as analysis_count
        FROM repositories r
        LEFT JOIN analysis_runs ar ON r.id = ar.repository_id
        GROUP BY r.id, r.name
        ORDER BY analysis_count DESC
    """))
    
    for row in result:
        print(f"Repository: {row.name}, Analyses: {row.analysis_count}")
```

### Bulk Operations

```python
from graph_sitter.database.base import bulk_create

# Bulk create multiple records efficiently
data_list = [
    {"name": f"Repo {i}", "full_name": f"org/repo-{i}"}
    for i in range(100)
]

repositories = bulk_create(session, Repository, data_list)
print(f"Created {len(repositories)} repositories")
```

## Troubleshooting

### Common Issues

1. **Connection Pool Exhaustion**
   ```python
   # Increase pool size
   config = DatabaseConfig(pool_size=50, max_overflow=100)
   ```

2. **Slow Queries**
   ```python
   # Enable query monitoring
   config = DatabaseConfig(
       enable_slow_query_logging=True,
       slow_query_threshold_ms=500
   )
   ```

3. **Memory Usage**
   ```python
   # Optimize session management
   with database_session_scope() as session:
       # Use session for multiple operations
       # Session automatically closed
   ```

### Performance Optimization

1. **Use Indexes Effectively**
   - All foreign keys are automatically indexed
   - JSONB fields use GIN indexes for fast queries
   - Composite indexes for common query patterns

2. **Batch Operations**
   ```python
   # Use bulk operations for large datasets
   session.bulk_insert_mappings(Repository, data_list)
   ```

3. **Query Optimization**
   ```python
   # Use eager loading for relationships
   repositories = session.query(Repository).options(
       joinedload(Repository.project),
       joinedload(Repository.organization)
   ).all()
   ```

## API Reference

See the individual model files for detailed API documentation:

- [`organizations.py`](models/organizations.py) - Organizations and Users
- [`projects.py`](models/projects.py) - Projects and Repositories  
- [`tasks.py`](models/tasks.py) - Tasks and Workflows
- [`analytics.py`](models/analytics.py) - Analytics and Analysis
- [`prompts.py`](models/prompts.py) - Prompts and Templates
- [`events.py`](models/events.py) - Events and Integrations
- [`learning.py`](models/learning.py) - Learning and OpenEvolve

## Contributing

1. Follow the existing model patterns
2. Add comprehensive tests for new functionality
3. Update documentation for API changes
4. Ensure backward compatibility
5. Add appropriate indexes for new queries

## License

This module is part of the graph-sitter project and follows the same license terms.

