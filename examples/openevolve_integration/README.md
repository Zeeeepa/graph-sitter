# OpenEvolve Integration Example

This example demonstrates how to use the OpenEvolve integration module for continuous learning and system evolution.

## Overview

The OpenEvolve integration provides:

- **Automatic Evaluation Triggering**: Based on system events like task failures, pipeline failures, and performance degradation
- **Evaluation Management**: Submit, monitor, and process evaluations through OpenEvolve API
- **System Improvements**: Receive and apply improvement recommendations
- **Metrics Tracking**: Monitor evaluation success rates, performance improvements, and system health
- **REST API**: Complete API for evaluation management and monitoring

## Prerequisites

1. OpenEvolve API access and API key
2. Database setup with OpenEvolve tables
3. Environment configuration

## Configuration

Create a `.env` file or set environment variables:

```bash
# OpenEvolve Configuration
OPENEVOLVE_API_URL=https://api.openevolve.com
OPENEVOLVE_API_KEY=your_api_key_here
OPENEVOLVE_TIMEOUT=30000
OPENEVOLVE_MAX_RETRIES=3
OPENEVOLVE_EVALUATION_TRIGGERS=task_failure,pipeline_failure,performance_degradation
OPENEVOLVE_BATCH_SIZE=10
OPENEVOLVE_EVALUATION_QUEUE_SIZE=100
OPENEVOLVE_ENABLE_AUTO_EVALUATION=true
OPENEVOLVE_MIN_EVALUATION_INTERVAL=300
```

## Database Setup

Run the migration script to create the required tables:

```sql
-- Run the migration script
\i src/graph_sitter/openevolve/migrations/001_create_openevolve_tables.sql
```

## Basic Usage

### 1. Initialize the Service

```python
from graph_sitter.configs.models.openevolve_config import OpenEvolveConfig
from graph_sitter.openevolve import EvaluationService
from sqlalchemy.orm import Session

# Initialize configuration
config = OpenEvolveConfig()

# Initialize service with database session
async with EvaluationService(config, session) as service:
    # Start background processing
    service.start_processing()
    
    # Your application logic here
    pass
```

### 2. Trigger Evaluations

```python
from graph_sitter.openevolve.models import EvaluationTrigger

# Trigger evaluation on task failure
evaluation_id = await service.trigger_evaluation(
    trigger_event=EvaluationTrigger.TASK_FAILURE,
    context={
        "task_id": "task_123",
        "error_type": "timeout",
        "duration": 300,
        "resource_usage": {"cpu": 0.8, "memory": 0.6}
    },
    priority=3,
    metadata={
        "component": "data_processor",
        "version": "1.2.3"
    }
)

print(f"Evaluation triggered: {evaluation_id}")
```

### 3. Monitor Evaluations

```python
# Get evaluation result
result = await service.get_evaluation_result(evaluation_id)
if result:
    print(f"Status: {result.status}")
    print(f"Results: {result.results}")
    print(f"Metrics: {result.metrics}")

# List recent evaluations
evaluations = await service.list_evaluations(limit=10)
for eval in evaluations:
    print(f"{eval.id}: {eval.status} - {eval.trigger_event}")
```

### 4. Get System Improvements

```python
# Process evaluation results and get improvements
result = await service.process_evaluation_result(evaluation_id)

# Apply improvements (this would be customized for your system)
improvements = await service.get_improvements_for_evaluation(evaluation_id)
for improvement in improvements:
    if improvement.priority <= 3:  # High priority improvements
        success = await service.apply_system_improvement(improvement.id)
        print(f"Applied improvement {improvement.id}: {success}")
```

### 5. Get Evaluation Summary

```python
# Get summary for last 30 days
summary = await service.get_evaluation_summary(days=30)
print(f"Total evaluations: {summary.total_evaluations}")
print(f"Success rate: {summary.success_rate}%")
print(f"Average improvement score: {summary.average_improvement_score}")
```

## REST API Usage

The module provides a complete REST API for evaluation management:

### Create Evaluation

```bash
curl -X POST "http://localhost:8000/api/v1/openevolve/evaluations" \
  -H "Content-Type: application/json" \
  -d '{
    "trigger_event": "task_failure",
    "context": {
      "task_id": "task_123",
      "error_type": "timeout"
    },
    "priority": 3,
    "metadata": {
      "component": "data_processor"
    }
  }'
```

### Get Evaluation

```bash
curl "http://localhost:8000/api/v1/openevolve/evaluations/{evaluation_id}"
```

### List Evaluations

```bash
curl "http://localhost:8000/api/v1/openevolve/evaluations?status=completed&limit=10"
```

### Get Summary

```bash
curl "http://localhost:8000/api/v1/openevolve/summary?days=30"
```

### Health Check

```bash
curl "http://localhost:8000/api/v1/openevolve/health"
```

## Integration with FastAPI

```python
from fastapi import FastAPI
from graph_sitter.openevolve.api import router

app = FastAPI()
app.include_router(router)

# Your application routes here
```

## Event-Driven Integration

```python
import asyncio
from graph_sitter.openevolve.models import EvaluationTrigger

class SystemMonitor:
    def __init__(self, evaluation_service):
        self.evaluation_service = evaluation_service
    
    async def on_task_failure(self, task_id: str, error: Exception):
        """Handle task failure events."""
        await self.evaluation_service.trigger_evaluation(
            trigger_event=EvaluationTrigger.TASK_FAILURE,
            context={
                "task_id": task_id,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    async def on_performance_degradation(self, metrics: dict):
        """Handle performance degradation events."""
        await self.evaluation_service.trigger_evaluation(
            trigger_event=EvaluationTrigger.PERFORMANCE_DEGRADATION,
            context={
                "metrics": metrics,
                "threshold_exceeded": True,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
```

## Custom Improvement Application

```python
class CustomImprovementApplicator:
    async def apply_improvement(self, improvement):
        """Apply system improvement based on type."""
        if improvement.improvement_type == "cache_optimization":
            return await self._optimize_cache(improvement)
        elif improvement.improvement_type == "query_optimization":
            return await self._optimize_queries(improvement)
        elif improvement.improvement_type == "resource_scaling":
            return await self._scale_resources(improvement)
        else:
            return False
    
    async def _optimize_cache(self, improvement):
        # Implement cache optimization logic
        pass
    
    async def _optimize_queries(self, improvement):
        # Implement query optimization logic
        pass
    
    async def _scale_resources(self, improvement):
        # Implement resource scaling logic
        pass
```

## Monitoring and Alerting

```python
import logging

class EvaluationMonitor:
    def __init__(self, evaluation_service):
        self.evaluation_service = evaluation_service
        self.logger = logging.getLogger(__name__)
    
    async def monitor_evaluations(self):
        """Monitor evaluation health and send alerts."""
        summary = await self.evaluation_service.get_evaluation_summary(days=1)
        
        # Check success rate
        if summary.success_rate < 80:
            self.logger.warning(f"Low evaluation success rate: {summary.success_rate}%")
            await self._send_alert("Low evaluation success rate")
        
        # Check for recent failures
        failed_evaluations = await self.evaluation_service.list_evaluations(
            status=EvaluationStatus.FAILED,
            limit=10
        )
        
        if len(failed_evaluations) > 5:
            self.logger.error(f"High number of failed evaluations: {len(failed_evaluations)}")
            await self._send_alert("High evaluation failure rate")
    
    async def _send_alert(self, message: str):
        # Implement alerting logic (email, Slack, etc.)
        pass
```

## Testing

```python
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
async def evaluation_service():
    config = OpenEvolveConfig(api_key="test_key")
    session = MagicMock()
    
    async with EvaluationService(config, session) as service:
        yield service

@pytest.mark.asyncio
async def test_trigger_evaluation(evaluation_service):
    # Mock the client
    evaluation_service._client = AsyncMock()
    evaluation_service._client.submit_evaluation.return_value = "eval_123"
    
    # Trigger evaluation
    eval_id = await evaluation_service.trigger_evaluation(
        trigger_event=EvaluationTrigger.TASK_FAILURE,
        context={"task_id": "test_task"}
    )
    
    assert eval_id is not None
    evaluation_service._client.submit_evaluation.assert_called_once()
```

## Performance Considerations

1. **Queue Management**: Monitor queue size and adjust `evaluation_queue_size` based on load
2. **Rate Limiting**: Configure `min_evaluation_interval` to prevent API overload
3. **Batch Processing**: Use `batch_size` to optimize database operations
4. **Database Indexing**: Ensure proper indexes are created for query performance
5. **Connection Pooling**: Use connection pooling for database sessions
6. **Async Processing**: All operations are async for better performance

## Security Considerations

1. **API Key Management**: Store API keys securely using environment variables
2. **Database Security**: Use proper database authentication and encryption
3. **Input Validation**: All inputs are validated using Pydantic models
4. **Error Handling**: Sensitive information is not exposed in error messages
5. **Rate Limiting**: Implement rate limiting to prevent abuse

## Troubleshooting

### Common Issues

1. **API Key Not Set**: Ensure `OPENEVOLVE_API_KEY` is configured
2. **Database Connection**: Verify database connection and table creation
3. **Queue Full**: Increase `evaluation_queue_size` or process evaluations faster
4. **Rate Limiting**: Adjust `min_evaluation_interval` if hitting rate limits
5. **Timeout Issues**: Increase `timeout` value for long-running evaluations

### Logging

Enable debug logging to troubleshoot issues:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("graph_sitter.openevolve")
logger.setLevel(logging.DEBUG)
```

### Health Checks

Use the health check endpoint to monitor system status:

```python
# Check if OpenEvolve API is accessible
health = await service.health_check()
print(f"OpenEvolve API healthy: {health.openevolve_api_healthy}")
```

