# OpenEvolve Implementation Guide

## Overview

This guide provides step-by-step instructions for implementing the OpenEvolve integration into the Graph-Sitter CI/CD system. Follow this guide to set up continuous learning analytics with minimal performance impact.

## Prerequisites

### System Requirements
- Python 3.9+
- PostgreSQL 13+
- Redis 6+
- Docker (optional, for containerized deployment)
- Minimum 8GB RAM, 4 CPU cores for development
- Minimum 16GB RAM, 8 CPU cores for production

### Dependencies
```bash
# Core dependencies
pip install openevolve>=1.0.0
pip install asyncio-pool>=0.6.0
pip install scikit-learn>=1.3.0
pip install pandas>=2.0.0
pip install numpy>=1.24.0
pip install psycopg2-binary>=2.9.0
pip install redis>=4.5.0
pip install fastapi>=0.100.0
pip install uvicorn>=0.23.0
```

## Installation Steps

### Step 1: Database Setup

#### 1.1 Create Analytics Database
```sql
-- Connect to PostgreSQL as superuser
CREATE DATABASE graph_sitter_analytics;
CREATE USER openevolve_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE graph_sitter_analytics TO openevolve_user;

-- Connect to the analytics database
\c graph_sitter_analytics;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
```

#### 1.2 Run Database Migrations
```bash
# Navigate to the project root
cd /path/to/graph-sitter

# Run the analytics database schema
psql -h localhost -U openevolve_user -d graph_sitter_analytics -f docs/sql/analytics_schema.sql

# Verify tables were created
psql -h localhost -U openevolve_user -d graph_sitter_analytics -c "\dt"
```

### Step 2: Redis Configuration

#### 2.1 Install and Configure Redis
```bash
# Install Redis (Ubuntu/Debian)
sudo apt update
sudo apt install redis-server

# Configure Redis for production
sudo nano /etc/redis/redis.conf

# Key configurations:
# maxmemory 2gb
# maxmemory-policy allkeys-lru
# save 900 1
# save 300 10
# save 60 10000

# Restart Redis
sudo systemctl restart redis-server
sudo systemctl enable redis-server
```

### Step 3: OpenEvolve Extension Implementation

#### 3.1 Create Extension Structure
```bash
# Create the OpenEvolve extension directory
mkdir -p src/contexten/extensions/openevolve
cd src/contexten/extensions/openevolve

# Create required files
touch __init__.py
touch controller.py
touch evaluator_pool.py
touch prompt_sampler.py
touch program_database.py
touch metrics_collector.py
touch pattern_analyzer.py
touch improvement_engine.py
touch config.py
```

#### 3.2 Implement Core Components

Create the main controller:

```python
# src/contexten/extensions/openevolve/__init__.py
from .controller import OpenEvolveController
from .config import OpenEvolveConfig

__all__ = ['OpenEvolveController', 'OpenEvolveConfig']
```

```python
# src/contexten/extensions/openevolve/controller.py
import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from contexten.extensions.base import BaseExtension
from graph_sitter.codebase.codebase_analysis import get_codebase_summary
from .config import OpenEvolveConfig
from .metrics_collector import MetricsCollector
from .pattern_analyzer import PatternAnalyzer
from .improvement_engine import ImprovementEngine
from .program_database import ProgramDatabase

logger = logging.getLogger(__name__)

class OpenEvolveController(BaseExtension):
    """
    Main controller for OpenEvolve integration.
    Orchestrates continuous learning and optimization.
    """
    
    def __init__(self, config: OpenEvolveConfig):
        super().__init__()
        self.config = config
        self.metrics_collector = MetricsCollector(config.performance)
        self.pattern_analyzer = PatternAnalyzer()
        self.improvement_engine = ImprovementEngine(config)
        self.program_database = ProgramDatabase(config.database)
        self.is_running = False
        self._background_tasks = set()
    
    async def initialize(self):
        """Initialize the OpenEvolve controller."""
        logger.info("Initializing OpenEvolve controller...")
        
        # Initialize database connections
        await self.program_database.initialize()
        
        # Start background tasks
        await self._start_background_tasks()
        
        logger.info("OpenEvolve controller initialized successfully")
    
    async def shutdown(self):
        """Shutdown the OpenEvolve controller."""
        logger.info("Shutting down OpenEvolve controller...")
        
        self.is_running = False
        
        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self._background_tasks, return_exceptions=True)
        
        # Close database connections
        await self.program_database.close()
        
        logger.info("OpenEvolve controller shutdown complete")
    
    async def start_evolution_cycle(self, codebase_context: Any) -> Dict[str, Any]:
        """Start a new evolution cycle based on current codebase state."""
        if not self.config.enabled:
            return {"status": "disabled", "message": "OpenEvolve is disabled"}
        
        if self.is_running:
            return {"status": "already_running", "message": "Evolution cycle already in progress"}
        
        cycle_id = f"cycle_{datetime.now().isoformat()}"
        logger.info(f"Starting evolution cycle: {cycle_id}")
        
        try:
            self.is_running = True
            
            # Collect current system metrics
            current_metrics = await self.metrics_collector.collect_system_snapshot()
            
            # Analyze patterns from historical data
            patterns = await self.pattern_analyzer.analyze_recent_patterns()
            
            # Generate improvement suggestions
            improvements = await self.improvement_engine.generate_improvements(
                codebase_context, current_metrics, patterns
            )
            
            # Store results
            cycle_result = {
                "cycle_id": cycle_id,
                "timestamp": datetime.now().isoformat(),
                "metrics": current_metrics,
                "patterns_found": len(patterns),
                "improvements_suggested": len(improvements),
                "status": "completed"
            }
            
            await self.program_database.store_evolution_cycle(cycle_result)
            
            logger.info(f"Evolution cycle {cycle_id} completed successfully")
            return cycle_result
            
        except Exception as e:
            logger.error(f"Evolution cycle {cycle_id} failed: {str(e)}")
            return {
                "cycle_id": cycle_id,
                "status": "failed",
                "error": str(e)
            }
        finally:
            self.is_running = False
    
    async def get_optimization_suggestions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get current optimization suggestions."""
        return await self.program_database.get_top_suggestions(limit)
    
    async def get_performance_metrics(
        self, 
        component: Optional[str] = None,
        hours: int = 24
    ) -> Dict[str, Any]:
        """Get performance metrics for the specified timeframe."""
        return await self.program_database.get_performance_summary(component, hours)
    
    async def _start_background_tasks(self):
        """Start background tasks for continuous operation."""
        # Metrics collection task
        metrics_task = asyncio.create_task(self._metrics_collection_loop())
        self._background_tasks.add(metrics_task)
        
        # Pattern analysis task
        analysis_task = asyncio.create_task(self._pattern_analysis_loop())
        self._background_tasks.add(analysis_task)
        
        # Database maintenance task
        maintenance_task = asyncio.create_task(self._database_maintenance_loop())
        self._background_tasks.add(maintenance_task)
    
    async def _metrics_collection_loop(self):
        """Background loop for metrics collection."""
        while self.is_running:
            try:
                await self.metrics_collector.flush_metrics_to_database()
                await asyncio.sleep(self.config.performance.flush_interval_seconds)
            except Exception as e:
                logger.error(f"Metrics collection error: {str(e)}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def _pattern_analysis_loop(self):
        """Background loop for pattern analysis."""
        while self.is_running:
            try:
                # Run pattern analysis every hour
                await self.pattern_analyzer.analyze_and_store_patterns()
                await asyncio.sleep(3600)  # 1 hour
            except Exception as e:
                logger.error(f"Pattern analysis error: {str(e)}")
                await asyncio.sleep(1800)  # Wait 30 minutes before retrying
    
    async def _database_maintenance_loop(self):
        """Background loop for database maintenance."""
        while self.is_running:
            try:
                # Run maintenance every 6 hours
                await self.program_database.run_maintenance()
                await asyncio.sleep(21600)  # 6 hours
            except Exception as e:
                logger.error(f"Database maintenance error: {str(e)}")
                await asyncio.sleep(3600)  # Wait 1 hour before retrying
```

### Step 4: Configuration Setup

#### 4.1 Create Configuration File
```yaml
# config/openevolve.yaml
openevolve:
  enabled: true
  debug_mode: false
  log_level: "INFO"
  
  llm:
    primary_model: "gpt-4"
    secondary_model: "gpt-3.5-turbo"
    temperature: 0.7
    max_tokens: 2000
    api_key: "${OPENAI_API_KEY}"
  
  database:
    host: "localhost"
    port: 5432
    database: "graph_sitter_analytics"
    username: "openevolve_user"
    password: "${OPENEVOLVE_DB_PASSWORD}"
    pool_size: 10
    max_overflow: 20
  
  performance:
    max_overhead_percent: 5.0
    sampling_rate: 0.1
    batch_size: 1000
    flush_interval_seconds: 60
    max_memory_usage_mb: 1024
  
  evaluation:
    population_size: 500
    num_islands: 5
    max_iterations: 1000
    evaluation_timeout_seconds: 300
    checkpoint_interval: 10
    max_concurrent_evaluations: 20
```

#### 4.2 Environment Variables
```bash
# .env file
OPENAI_API_KEY=your_openai_api_key_here
OPENEVOLVE_DB_PASSWORD=secure_database_password
OPENEVOLVE_REDIS_URL=redis://localhost:6379/0
OPENEVOLVE_LOG_LEVEL=INFO
OPENEVOLVE_ENABLED=true
```

### Step 5: Integration with Contexten

#### 5.1 Register Extension
```python
# src/contexten/extensions/__init__.py
from .openevolve import OpenEvolveController

# Add to extension registry
AVAILABLE_EXTENSIONS = {
    'github': 'contexten.extensions.github',
    'linear': 'contexten.extensions.linear',
    'slack': 'contexten.extensions.slack',
    'openevolve': 'contexten.extensions.openevolve',  # Add this line
}
```

#### 5.2 Update Contexten Configuration
```python
# src/contexten/config.py
from contexten.extensions.openevolve.config import OpenEvolveConfig

class ContextenConfig:
    def __init__(self):
        # ... existing configuration ...
        self.openevolve = OpenEvolveConfig.from_env()
```

### Step 6: Event Integration

#### 6.1 Create Event Handlers
```python
# src/contexten/extensions/openevolve/event_handlers.py
import asyncio
from contexten.extensions.events import EventHandler, Event
from .controller import OpenEvolveController

class OpenEvolveEventHandler(EventHandler):
    def __init__(self, controller: OpenEvolveController):
        self.controller = controller
    
    async def handle_codebase_analysis_complete(self, event: Event):
        """Trigger optimization analysis when codebase analysis completes."""
        codebase_context = event.data.get('codebase_context')
        if codebase_context:
            # Run in background to avoid blocking
            asyncio.create_task(
                self.controller.start_evolution_cycle(codebase_context)
            )
    
    async def handle_ci_pipeline_complete(self, event: Event):
        """Collect metrics when CI pipeline completes."""
        pipeline_metrics = event.data.get('pipeline_metrics')
        if pipeline_metrics:
            await self.controller.metrics_collector.collect_pipeline_metrics(
                pipeline_metrics
            )
    
    async def handle_task_complete(self, event: Event):
        """Collect task completion metrics."""
        task_data = event.data.get('task_data')
        if task_data:
            await self.controller.metrics_collector.collect_task_metrics(
                task_data
            )
```

### Step 7: Testing Setup

#### 7.1 Unit Tests
```python
# tests/unit/extensions/openevolve/test_controller.py
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

from contexten.extensions.openevolve import OpenEvolveController, OpenEvolveConfig

@pytest.fixture
def config():
    return OpenEvolveConfig(
        enabled=True,
        debug_mode=True
    )

@pytest.fixture
async def controller(config):
    controller = OpenEvolveController(config)
    await controller.initialize()
    yield controller
    await controller.shutdown()

@pytest.mark.asyncio
async def test_evolution_cycle(controller):
    """Test basic evolution cycle functionality."""
    codebase_context = {"files": 10, "functions": 50}
    
    result = await controller.start_evolution_cycle(codebase_context)
    
    assert result["status"] == "completed"
    assert "cycle_id" in result
    assert "improvements_suggested" in result

@pytest.mark.asyncio
async def test_metrics_collection(controller):
    """Test metrics collection functionality."""
    metrics = await controller.get_performance_metrics()
    
    assert isinstance(metrics, dict)
    assert "timestamp" in metrics

@pytest.mark.asyncio
async def test_optimization_suggestions(controller):
    """Test optimization suggestions retrieval."""
    suggestions = await controller.get_optimization_suggestions()
    
    assert isinstance(suggestions, list)
```

#### 7.2 Integration Tests
```python
# tests/integration/openevolve/test_full_integration.py
import pytest
import asyncio
from contexten.app import ContextenApp
from contexten.extensions.openevolve import OpenEvolveController

@pytest.mark.asyncio
async def test_full_integration():
    """Test full integration with Contexten app."""
    app = ContextenApp()
    await app.initialize()
    
    # Verify OpenEvolve extension is loaded
    assert 'openevolve' in app.extensions
    
    openevolve = app.extensions['openevolve']
    assert isinstance(openevolve, OpenEvolveController)
    
    # Test basic functionality
    suggestions = await openevolve.get_optimization_suggestions()
    assert isinstance(suggestions, list)
    
    await app.shutdown()
```

### Step 8: Monitoring Setup

#### 8.1 Prometheus Metrics
```python
# src/contexten/extensions/openevolve/monitoring.py
from prometheus_client import Counter, Histogram, Gauge
import time

# Metrics definitions
evolution_cycles_total = Counter(
    'openevolve_evolution_cycles_total',
    'Total number of evolution cycles',
    ['status']
)

evolution_cycle_duration = Histogram(
    'openevolve_evolution_cycle_duration_seconds',
    'Duration of evolution cycles'
)

active_evaluations = Gauge(
    'openevolve_active_evaluations',
    'Number of active evaluations'
)

performance_overhead = Gauge(
    'openevolve_performance_overhead_percent',
    'Current performance overhead percentage'
)

class MetricsExporter:
    def __init__(self, controller: OpenEvolveController):
        self.controller = controller
    
    async def update_metrics(self):
        """Update Prometheus metrics."""
        # Update performance overhead
        current_overhead = await self.controller.get_current_overhead()
        performance_overhead.set(current_overhead)
        
        # Update active evaluations
        active_count = await self.controller.get_active_evaluation_count()
        active_evaluations.set(active_count)
```

#### 8.2 Health Checks
```python
# src/contexten/extensions/openevolve/health.py
from typing import Dict, Any
import asyncio

class HealthChecker:
    def __init__(self, controller: OpenEvolveController):
        self.controller = controller
    
    async def check_health(self) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        health_status = {
            "status": "healthy",
            "checks": {}
        }
        
        # Database connectivity
        try:
            await self.controller.program_database.ping()
            health_status["checks"]["database"] = "healthy"
        except Exception as e:
            health_status["checks"]["database"] = f"unhealthy: {str(e)}"
            health_status["status"] = "unhealthy"
        
        # Redis connectivity
        try:
            await self.controller.metrics_collector.ping_redis()
            health_status["checks"]["redis"] = "healthy"
        except Exception as e:
            health_status["checks"]["redis"] = f"unhealthy: {str(e)}"
            health_status["status"] = "unhealthy"
        
        # Performance overhead check
        current_overhead = await self.controller.get_current_overhead()
        if current_overhead > self.controller.config.performance.max_overhead_percent:
            health_status["checks"]["performance"] = f"degraded: {current_overhead}% overhead"
            health_status["status"] = "degraded"
        else:
            health_status["checks"]["performance"] = "healthy"
        
        return health_status
```

### Step 9: Deployment

#### 9.1 Docker Configuration
```dockerfile
# Dockerfile.openevolve
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY config/ ./config/

# Set environment variables
ENV PYTHONPATH=/app/src
ENV OPENEVOLVE_CONFIG_PATH=/app/config/openevolve.yaml

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import asyncio; from src.contexten.extensions.openevolve.health import HealthChecker; print('healthy')"

# Run the application
CMD ["python", "-m", "contexten.app"]
```

#### 9.2 Docker Compose
```yaml
# docker-compose.openevolve.yml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: graph_sitter_analytics
      POSTGRES_USER: openevolve_user
      POSTGRES_PASSWORD: ${OPENEVOLVE_DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./docs/sql/analytics_schema.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
  
  redis:
    image: redis:7-alpine
    command: redis-server --maxmemory 2gb --maxmemory-policy allkeys-lru
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
  
  openevolve:
    build:
      context: .
      dockerfile: Dockerfile.openevolve
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - OPENEVOLVE_DB_PASSWORD=${OPENEVOLVE_DB_PASSWORD}
      - OPENEVOLVE_REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    ports:
      - "8000:8000"
    volumes:
      - ./logs:/app/logs

volumes:
  postgres_data:
  redis_data:
```

### Step 10: Production Deployment

#### 10.1 Deployment Script
```bash
#!/bin/bash
# deploy-openevolve.sh

set -e

echo "Deploying OpenEvolve integration..."

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "Docker is required but not installed. Aborting." >&2; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "Docker Compose is required but not installed. Aborting." >&2; exit 1; }

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | xargs)
else
    echo "Error: .env file not found"
    exit 1
fi

# Validate required environment variables
required_vars=("OPENAI_API_KEY" "OPENEVOLVE_DB_PASSWORD")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "Error: $var is not set"
        exit 1
    fi
done

# Build and deploy
echo "Building OpenEvolve containers..."
docker-compose -f docker-compose.openevolve.yml build

echo "Starting services..."
docker-compose -f docker-compose.openevolve.yml up -d

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 30

# Run health check
echo "Running health check..."
docker-compose -f docker-compose.openevolve.yml exec openevolve python -c "
import asyncio
from src.contexten.extensions.openevolve.health import HealthChecker
from src.contexten.extensions.openevolve import OpenEvolveController, OpenEvolveConfig

async def main():
    config = OpenEvolveConfig.from_env()
    controller = OpenEvolveController(config)
    await controller.initialize()
    
    health_checker = HealthChecker(controller)
    health = await health_checker.check_health()
    
    print(f'Health status: {health[\"status\"]}')
    for check, status in health['checks'].items():
        print(f'  {check}: {status}')
    
    await controller.shutdown()

asyncio.run(main())
"

echo "OpenEvolve deployment completed successfully!"
echo "Access the API at: http://localhost:8000"
echo "View logs with: docker-compose -f docker-compose.openevolve.yml logs -f"
```

### Step 11: Monitoring and Maintenance

#### 11.1 Log Configuration
```yaml
# config/logging.yaml
version: 1
disable_existing_loggers: false

formatters:
  standard:
    format: '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
  detailed:
    format: '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s'

handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: standard
    stream: ext://sys.stdout
  
  file:
    class: logging.handlers.RotatingFileHandler
    level: DEBUG
    formatter: detailed
    filename: logs/openevolve.log
    maxBytes: 10485760  # 10MB
    backupCount: 5
  
  error_file:
    class: logging.handlers.RotatingFileHandler
    level: ERROR
    formatter: detailed
    filename: logs/openevolve_errors.log
    maxBytes: 10485760  # 10MB
    backupCount: 5

loggers:
  contexten.extensions.openevolve:
    level: DEBUG
    handlers: [console, file, error_file]
    propagate: false

root:
  level: INFO
  handlers: [console, file]
```

#### 11.2 Maintenance Scripts
```bash
#!/bin/bash
# maintenance/cleanup.sh

# Clean up old metrics data (older than 90 days)
psql -h localhost -U openevolve_user -d graph_sitter_analytics -c "
DELETE FROM system_performance_metrics 
WHERE timestamp < NOW() - INTERVAL '90 days';
"

# Clean up old evaluation results (older than 180 days)
psql -h localhost -U openevolve_user -d graph_sitter_analytics -c "
DELETE FROM openevolve_evaluations 
WHERE evaluation_timestamp < NOW() - INTERVAL '180 days';
"

# Vacuum and analyze tables
psql -h localhost -U openevolve_user -d graph_sitter_analytics -c "
VACUUM ANALYZE system_performance_metrics;
VACUUM ANALYZE openevolve_evaluations;
VACUUM ANALYZE learned_patterns;
"

echo "Database cleanup completed"
```

## Troubleshooting

### Common Issues

#### 1. High Performance Overhead
```bash
# Check current overhead
curl http://localhost:8000/api/v1/performance-metrics

# Reduce sampling rate
export OPENEVOLVE_SAMPLING_RATE=0.05

# Restart service
docker-compose -f docker-compose.openevolve.yml restart openevolve
```

#### 2. Database Connection Issues
```bash
# Check database connectivity
docker-compose -f docker-compose.openevolve.yml exec postgres pg_isready

# Check database logs
docker-compose -f docker-compose.openevolve.yml logs postgres

# Reset database connection pool
curl -X POST http://localhost:8000/api/v1/admin/reset-db-pool
```

#### 3. Memory Issues
```bash
# Check memory usage
docker stats

# Increase memory limits in docker-compose.yml
# Add under openevolve service:
# deploy:
#   resources:
#     limits:
#       memory: 2G
```

### Performance Tuning

#### 1. Database Optimization
```sql
-- Create additional indexes for common queries
CREATE INDEX CONCURRENTLY idx_perf_metrics_component_time 
ON system_performance_metrics (component, timestamp DESC);

-- Optimize PostgreSQL configuration
-- Add to postgresql.conf:
-- shared_buffers = 256MB
-- effective_cache_size = 1GB
-- work_mem = 4MB
-- maintenance_work_mem = 64MB
```

#### 2. Redis Optimization
```bash
# Optimize Redis configuration
# Add to redis.conf:
# maxmemory-samples 10
# hash-max-ziplist-entries 512
# hash-max-ziplist-value 64
```

## Validation and Testing

### Performance Validation
```python
# scripts/validate_performance.py
import asyncio
import time
import statistics
from contexten.extensions.openevolve import OpenEvolveController, OpenEvolveConfig

async def measure_overhead():
    """Measure the performance overhead of OpenEvolve integration."""
    config = OpenEvolveConfig.from_env()
    controller = OpenEvolveController(config)
    
    # Baseline measurement (without OpenEvolve)
    baseline_times = []
    for _ in range(100):
        start = time.perf_counter()
        # Simulate typical operation
        await asyncio.sleep(0.01)
        end = time.perf_counter()
        baseline_times.append(end - start)
    
    # Initialize OpenEvolve
    await controller.initialize()
    
    # Measurement with OpenEvolve
    openevolve_times = []
    for _ in range(100):
        start = time.perf_counter()
        # Simulate typical operation with metrics collection
        await controller.metrics_collector.collect_operation_metrics("test", "operation")
        await asyncio.sleep(0.01)
        end = time.perf_counter()
        openevolve_times.append(end - start)
    
    await controller.shutdown()
    
    # Calculate overhead
    baseline_avg = statistics.mean(baseline_times)
    openevolve_avg = statistics.mean(openevolve_times)
    overhead_percent = ((openevolve_avg - baseline_avg) / baseline_avg) * 100
    
    print(f"Baseline average: {baseline_avg:.6f}s")
    print(f"OpenEvolve average: {openevolve_avg:.6f}s")
    print(f"Performance overhead: {overhead_percent:.2f}%")
    
    assert overhead_percent < 5.0, f"Performance overhead {overhead_percent:.2f}% exceeds 5% limit"

if __name__ == "__main__":
    asyncio.run(measure_overhead())
```

This implementation guide provides a comprehensive roadmap for integrating OpenEvolve into the Graph-Sitter system. Follow these steps carefully, and refer to the troubleshooting section if you encounter any issues during deployment.

