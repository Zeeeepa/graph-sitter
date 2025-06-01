# OpenEvolve Integration Module

The OpenEvolve Integration Module provides continuous learning and system evolution capabilities for the graph-sitter system. It enables automatic evaluation triggering, system improvement recommendations, and performance optimization through integration with the OpenEvolve API.

## Features

- **Automatic Evaluation Triggering**: Based on system events like task failures, pipeline failures, and performance degradation
- **Evaluation Management**: Submit, monitor, and process evaluations through OpenEvolve API
- **System Improvements**: Receive and apply improvement recommendations
- **Metrics Tracking**: Monitor evaluation success rates, performance improvements, and system health
- **REST API**: Complete API for evaluation management and monitoring
- **Database Integration**: Persistent storage for evaluation results and metrics
- **Async Processing**: Non-blocking evaluation processing with queue management

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Application   │    │  OpenEvolve     │    │   Database      │
│     Events      │    │   Integration   │    │                 │
│                 │    │                 │    │                 │
│ • Task Failure  │───▶│ • Client        │───▶│ • Evaluations   │
│ • Performance   │    │ • Service       │    │ • Improvements  │
│ • Manual        │    │ • API           │    │ • Metrics       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │  OpenEvolve     │
                       │     API         │
                       └─────────────────┘
```

## Components

### 1. Configuration (`openevolve_config.py`)
- Environment-based configuration using BaseConfig pattern
- API credentials, timeouts, and behavior settings
- Validation and configuration checks

### 2. Client (`client.py`)
- HTTP client for OpenEvolve API interactions
- Async/await support with aiohttp
- Retry logic and error handling
- Authentication and request management

### 3. Models (`models.py`)
- Pydantic models for data validation
- Evaluation requests, results, and status tracking
- System improvement recommendations
- Metrics and summary models

### 4. Database (`database.py`)
- SQLAlchemy models for persistent storage
- Evaluation tracking and history
- System improvement storage
- Metrics collection and analysis

### 5. Service (`service.py`)
- Core orchestration logic
- Evaluation queue management
- Background processing
- System improvement application

### 6. API (`api.py`)
- FastAPI REST endpoints
- Complete CRUD operations
- Health checks and monitoring
- Request/response validation

## Quick Start

### 1. Configuration

Set environment variables:

```bash
export OPENEVOLVE_API_KEY="your_api_key_here"
export OPENEVOLVE_API_URL="https://api.openevolve.com"
export OPENEVOLVE_TIMEOUT=30000
export OPENEVOLVE_MAX_RETRIES=3
```

### 2. Database Setup

Run the migration script:

```sql
\i src/graph_sitter/openevolve/migrations/001_create_openevolve_tables.sql
```

### 3. Basic Usage

```python
from graph_sitter.configs.models.openevolve_config import OpenEvolveConfig
from graph_sitter.openevolve import EvaluationService
from graph_sitter.openevolve.models import EvaluationTrigger

# Initialize
config = OpenEvolveConfig()
async with EvaluationService(config, session) as service:
    service.start_processing()
    
    # Trigger evaluation
    eval_id = await service.trigger_evaluation(
        trigger_event=EvaluationTrigger.TASK_FAILURE,
        context={"task_id": "task_123", "error": "timeout"},
        priority=3
    )
    
    # Monitor result
    result = await service.get_evaluation_result(eval_id)
    print(f"Status: {result.status}")
```

### 4. REST API Integration

```python
from fastapi import FastAPI
from graph_sitter.openevolve.api import router

app = FastAPI()
app.include_router(router)
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/openevolve/evaluations` | Create evaluation |
| GET | `/api/v1/openevolve/evaluations/{id}` | Get evaluation |
| GET | `/api/v1/openevolve/evaluations` | List evaluations |
| DELETE | `/api/v1/openevolve/evaluations/{id}` | Cancel evaluation |
| POST | `/api/v1/openevolve/evaluations/{id}/process` | Process result |
| GET | `/api/v1/openevolve/summary` | Get summary |
| GET | `/api/v1/openevolve/improvements/{eval_id}` | Get improvements |
| POST | `/api/v1/openevolve/improvements/{id}/apply` | Apply improvement |
| GET | `/api/v1/openevolve/health` | Health check |

## Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENEVOLVE_API_URL` | `https://api.openevolve.com` | OpenEvolve API base URL |
| `OPENEVOLVE_API_KEY` | None | API key for authentication |
| `OPENEVOLVE_TIMEOUT` | 30000 | Request timeout (ms) |
| `OPENEVOLVE_MAX_RETRIES` | 3 | Maximum retry attempts |
| `OPENEVOLVE_EVALUATION_TRIGGERS` | `task_failure,pipeline_failure,performance_degradation` | Trigger events |
| `OPENEVOLVE_BATCH_SIZE` | 10 | Batch processing size |
| `OPENEVOLVE_EVALUATION_QUEUE_SIZE` | 100 | Maximum queue size |
| `OPENEVOLVE_ENABLE_AUTO_EVALUATION` | true | Enable automatic evaluations |
| `OPENEVOLVE_MIN_EVALUATION_INTERVAL` | 300 | Minimum interval between evaluations (seconds) |

## Database Schema

### openevolve_evaluations
- `id` (UUID): Primary key
- `evaluation_id` (VARCHAR): OpenEvolve API ID
- `status` (VARCHAR): Current status
- `trigger_event` (VARCHAR): Triggering event
- `priority` (INTEGER): Priority level
- `context` (JSONB): Context data
- `metadata` (JSONB): Additional metadata
- `results` (JSONB): Evaluation results
- `metrics` (JSONB): Performance metrics
- Timestamps: created_at, submitted_at, started_at, completed_at, updated_at

### system_improvements
- `id` (UUID): Primary key
- `evaluation_id` (UUID): Foreign key to evaluation
- `improvement_type` (VARCHAR): Type of improvement
- `description` (TEXT): Detailed description
- `priority` (INTEGER): Priority level
- `estimated_impact` (FLOAT): Impact score
- `implementation_complexity` (VARCHAR): Complexity level
- `applied` (BOOLEAN): Application status
- `results` (JSONB): Application results
- Timestamps: created_at, updated_at, applied_at

### evaluation_metrics
- `id` (UUID): Primary key
- `evaluation_id` (UUID): Foreign key to evaluation
- `accuracy` (FLOAT): Accuracy score
- `performance_score` (FLOAT): Performance score
- `improvement_score` (FLOAT): Improvement score
- `execution_time` (FLOAT): Execution time
- `resource_usage` (JSONB): Resource usage data
- `custom_metrics` (JSONB): Custom metrics
- `recorded_at` (TIMESTAMP): Recording timestamp

## Event Types

### EvaluationTrigger
- `TASK_FAILURE`: Task execution failures
- `PIPELINE_FAILURE`: Pipeline or workflow failures
- `PERFORMANCE_DEGRADATION`: Performance threshold violations
- `MANUAL`: Manually triggered evaluations
- `SCHEDULED`: Scheduled evaluations

### EvaluationStatus
- `PENDING`: Queued for processing
- `SUBMITTED`: Submitted to OpenEvolve
- `RUNNING`: Currently being evaluated
- `COMPLETED`: Successfully completed
- `FAILED`: Failed with error
- `CANCELLED`: Cancelled by user

## Error Handling

The module provides comprehensive error handling:

- **OpenEvolveAPIError**: API communication errors
- **Configuration validation**: Missing or invalid configuration
- **Rate limiting**: Prevents API overload
- **Queue management**: Handles queue overflow
- **Retry logic**: Automatic retry with exponential backoff
- **Timeout handling**: Request and evaluation timeouts

## Performance Considerations

- **Async Processing**: All operations are non-blocking
- **Queue Management**: Configurable queue size and processing
- **Database Indexing**: Optimized queries with proper indexes
- **Connection Pooling**: Efficient database connection usage
- **Rate Limiting**: Prevents API overload
- **Batch Processing**: Efficient bulk operations

## Security

- **API Key Management**: Secure credential storage
- **Input Validation**: Pydantic model validation
- **SQL Injection Prevention**: SQLAlchemy ORM protection
- **Error Message Sanitization**: No sensitive data exposure
- **Authentication**: Bearer token authentication

## Monitoring and Observability

- **Health Checks**: API and database health monitoring
- **Metrics Collection**: Success rates, execution times, improvement scores
- **Logging**: Comprehensive logging with configurable levels
- **Evaluation Summary**: Aggregated statistics and trends
- **Error Tracking**: Failed evaluation analysis

## Testing

The module includes comprehensive unit tests:

- **Client Tests**: API interaction testing with mocks
- **Service Tests**: Business logic and orchestration testing
- **Model Tests**: Data validation and serialization testing
- **Integration Tests**: End-to-end workflow testing
- **Error Scenario Tests**: Error handling and edge cases

Run tests:

```bash
pytest tests/unit/openevolve/ -v
```

## Examples

See the `examples/openevolve_integration/` directory for:

- Basic usage examples
- Event-driven integration patterns
- REST API usage
- Custom improvement application
- Monitoring and alerting setup

## Contributing

1. Follow the existing code style and patterns
2. Add comprehensive tests for new features
3. Update documentation for API changes
4. Ensure all tests pass before submitting
5. Follow the project's contribution guidelines

## License

This module is part of the graph-sitter project and follows the same license terms.

