# Graph-Sitter CI/CD System

A comprehensive continuous integration and deployment system with intelligent automation, continuous learning, and self-healing capabilities.

## Overview

The Graph-Sitter CI/CD system transforms traditional CI/CD into an intelligent, self-evolving platform that:

- **Learns from historical patterns** to optimize workflows
- **Automatically detects and resolves issues** through self-healing
- **Integrates with Codegen SDK** for AI-powered development tasks
- **Uses OpenEvolve mechanics** for continuous system improvement
- **Provides comprehensive analytics** for performance optimization

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Graph-Sitter CI/CD                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │    Task     │  │  Pipeline   │  │  Codegen    │        │
│  │ Management  │  │   Engine    │  │ Integration │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ OpenEvolve  │  │Self-Healing │  │  Analytics  │        │
│  │Integration  │  │   System    │  │   Engine    │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
├─────────────────────────────────────────────────────────────┤
│                 Database Layer                              │
│  Organizations | Projects | Tasks | Pipelines | Analytics  │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Task Management System

Hierarchical task management with dependency resolution and execution tracking.

**Features:**
- Task creation, assignment, and tracking
- Dependency resolution and execution ordering
- Integration with Codegen SDK for AI-powered task execution
- Performance monitoring and metrics collection

**Example:**
```python
from src.graph_sitter.cicd import TaskManager, Task, TaskType

# Create task manager
task_manager = TaskManager("org_123")

# Create a task
task = Task(
    title="Implement user authentication",
    description="Add OAuth2 authentication to the API",
    task_type=TaskType.FEATURE,
    priority=1,
    estimated_hours=8.0
)

# Execute task
task_id = await task_manager.create_task(task)
execution = await task_manager.execute_task(task_id)
```

### 2. Pipeline Engine

Multi-step pipeline execution with conditional logic and parallel processing.

**Features:**
- Pipeline definition with configurable steps
- Conditional execution and branching
- Integration with task management
- Artifact management and step dependencies

**Example:**
```python
from src.graph_sitter.cicd import PipelineEngine, Pipeline, PipelineStep, StepType

# Create pipeline
pipeline = Pipeline(
    name="Feature Development Pipeline",
    description="Complete feature development workflow",
    pipeline_type="feature_development"
)

# Add steps
pipeline.add_step(PipelineStep(
    name="Code Analysis",
    step_type=StepType.CODEGEN_TASK,
    configuration={"task": {"title": "Analyze code quality"}}
))

# Execute pipeline
pipeline_id = await pipeline_engine.create_pipeline(pipeline)
execution = await pipeline_engine.execute_pipeline(pipeline_id)
```

### 3. Codegen SDK Integration

Seamless integration with Codegen SDK for AI-powered development tasks.

**Features:**
- Agent management and configuration
- Task execution with cost tracking
- Performance analytics and optimization
- Batch task processing

**Example:**
```python
from src.graph_sitter.cicd import CodegenClient, CodegenAgent, AgentType

# Create Codegen client
codegen = CodegenClient("org_123", "codegen_org_id", "token")

# Create agent
agent = CodegenAgent(
    name="Code Analyzer",
    agent_type=AgentType.ANALYZER,
    capabilities=["code_analysis", "security_scan"]
)

# Execute task
agent_id = await codegen.create_agent(agent)
task = await codegen.execute_agent_task(
    agent_id, 
    "Analyze this codebase for security vulnerabilities"
)
```

### 4. OpenEvolve Integration

Continuous learning and system evolution through OpenEvolve mechanics.

**Features:**
- Evaluation submission and tracking
- Pattern discovery and learning
- System improvement recommendations
- Performance optimization

**Example:**
```python
from src.graph_sitter.cicd import OpenEvolveClient, Evaluation, EvaluationType

# Create OpenEvolve client
openevolve = OpenEvolveClient("org_123")

# Submit evaluation
evaluation = Evaluation(
    target_type="pipeline",
    target_id="pipeline_123",
    evaluation_type=EvaluationType.WORKFLOW_OPTIMIZATION
)

evaluation_id = await openevolve.submit_evaluation(evaluation)
results = await openevolve.get_evaluation_result(evaluation_id)
```

### 5. Self-Healing System

Automated error detection, diagnosis, and recovery.

**Features:**
- Real-time system monitoring
- Automated incident detection and classification
- Recovery procedure execution
- Learning from incidents

**Example:**
```python
from src.graph_sitter.cicd import SelfHealingSystem, IncidentSeverity

# Create self-healing system
healing = SelfHealingSystem("org_123")
await healing.start()

# Detect incident
incident_id = await healing.detect_incident(
    "performance_degradation",
    "Response time exceeded threshold",
    severity=IncidentSeverity.HIGH
)

# System automatically attempts recovery
```

### 6. Analytics Engine

Comprehensive analytics and performance monitoring.

**Features:**
- Performance metrics collection
- Pattern analysis and trend detection
- System health scoring
- Optimization recommendations

**Example:**
```python
from src.graph_sitter.cicd import AnalyticsEngine, MetricsCollector

# Create analytics engine
metrics = MetricsCollector("org_123")
analytics = AnalyticsEngine("org_123", metrics)

# Analyze performance
analysis = await analytics.analyze_performance("pipeline", "pipeline_123")
recommendations = await analytics.get_optimization_recommendations()
```

## Database Schema

The system uses a comprehensive 7-module database schema:

1. **Core System**: Organizations, projects, users
2. **Task Management**: Tasks, executions, dependencies
3. **Pipeline Engine**: Pipelines, steps, executions
4. **Codegen Integration**: Agents, tasks, capabilities
5. **Platform Integrations**: GitHub, Linear, Slack
6. **Analytics**: Metrics, performance data, audit logs
7. **Learning & OpenEvolve**: Patterns, evaluations, improvements

See `database/00_comprehensive_schema.sql` for the complete schema.

## Getting Started

### 1. Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set up database
psql -f database/00_comprehensive_schema.sql
```

### 2. Configuration

```python
# Configure your organization
ORGANIZATION_ID = "your_org_id"
CODEGEN_ORG_ID = "your_codegen_org_id"
CODEGEN_TOKEN = "your_codegen_token"
```

### 3. Basic Usage

```python
import asyncio
from src.graph_sitter.cicd import *

async def main():
    # Initialize components
    task_manager = TaskManager(ORGANIZATION_ID)
    pipeline_engine = PipelineEngine(ORGANIZATION_ID, task_manager)
    codegen_client = CodegenClient(ORGANIZATION_ID, CODEGEN_ORG_ID, CODEGEN_TOKEN)
    
    # Create and execute a simple workflow
    task = Task(title="Sample Task", task_type=TaskType.FEATURE)
    task_id = await task_manager.create_task(task)
    execution = await task_manager.execute_task(task_id)
    
    print(f"Task completed: {execution.status}")

asyncio.run(main())
```

### 4. Complete Example

See `examples/cicd_system_example.py` for a comprehensive demonstration of all features.

## Key Features

### Continuous Learning

The system continuously learns from:
- Task execution patterns
- Pipeline performance data
- Error resolution strategies
- User behavior and preferences

**Benefits:**
- Improved task success rates
- Optimized pipeline execution
- Reduced manual intervention
- Better resource utilization

### Self-Healing

Automated detection and resolution of:
- Performance degradation
- Resource exhaustion
- Integration failures
- Configuration errors

**Capabilities:**
- Real-time monitoring
- Automated incident classification
- Recovery procedure execution
- Learning from incidents

### OpenEvolve Integration

Leverages OpenEvolve mechanics for:
- System evolution and improvement
- Pattern discovery and analysis
- Performance optimization
- Predictive analytics

### Codegen SDK Integration

Seamless integration with Codegen SDK for:
- AI-powered code generation
- Automated code analysis
- Intelligent task execution
- Cost optimization

## Performance Metrics

The system tracks comprehensive metrics:

- **Task Metrics**: Success rate, execution time, resource usage
- **Pipeline Metrics**: Duration, step success, artifact size
- **Agent Metrics**: Performance, cost, token usage
- **System Metrics**: Health score, availability, response time

## Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/graphsitter

# Codegen SDK
CODEGEN_ORG_ID=your_org_id
CODEGEN_TOKEN=your_token

# OpenEvolve
OPENEVOLVE_API_URL=https://api.openevolve.com
OPENEVOLVE_API_KEY=your_api_key

# System
LOG_LEVEL=INFO
METRICS_RETENTION_DAYS=90
```

### System Configuration

```python
# Task management
TASK_TIMEOUT_SECONDS = 3600
MAX_CONCURRENT_TASKS = 10

# Pipeline execution
PIPELINE_TIMEOUT_SECONDS = 7200
MAX_PIPELINE_STEPS = 50

# Self-healing
MONITORING_INTERVAL_SECONDS = 30
AUTO_RECOVERY_ENABLED = True

# Analytics
METRICS_COLLECTION_INTERVAL = 60
PATTERN_DETECTION_ENABLED = True
```

## API Reference

### Task Management

- `TaskManager.create_task(task)` - Create a new task
- `TaskManager.execute_task(task_id)` - Execute a task
- `TaskManager.get_task_metrics(task_id)` - Get task performance metrics

### Pipeline Engine

- `PipelineEngine.create_pipeline(pipeline)` - Create a pipeline
- `PipelineEngine.execute_pipeline(pipeline_id)` - Execute a pipeline
- `PipelineEngine.get_execution_metrics(execution_id)` - Get execution metrics

### Codegen Integration

- `CodegenClient.create_agent(agent)` - Create a Codegen agent
- `CodegenClient.execute_agent_task(agent_id, prompt)` - Execute agent task
- `CodegenClient.get_agent_performance(agent_id)` - Get agent metrics

### OpenEvolve Integration

- `OpenEvolveClient.submit_evaluation(evaluation)` - Submit evaluation
- `OpenEvolveClient.discover_patterns(data_source)` - Discover patterns
- `OpenEvolveClient.apply_pattern(pattern_id, context)` - Apply pattern

### Self-Healing

- `SelfHealingSystem.detect_incident(type, message)` - Detect incident
- `SelfHealingSystem.get_system_health()` - Get system health
- `SelfHealingSystem.get_incident_metrics()` - Get incident metrics

### Analytics

- `AnalyticsEngine.analyze_performance(target_type, target_id)` - Analyze performance
- `AnalyticsEngine.detect_patterns(period_days)` - Detect patterns
- `AnalyticsEngine.get_optimization_recommendations()` - Get recommendations

## Best Practices

### Task Design

1. **Keep tasks focused** - Single responsibility principle
2. **Define clear dependencies** - Explicit task relationships
3. **Set realistic estimates** - Accurate time and resource estimates
4. **Use appropriate priorities** - Critical path optimization

### Pipeline Design

1. **Modular steps** - Reusable and composable pipeline steps
2. **Error handling** - Robust error handling and recovery
3. **Conditional logic** - Smart branching based on context
4. **Artifact management** - Proper artifact storage and retrieval

### Agent Configuration

1. **Capability matching** - Match agent capabilities to task requirements
2. **Cost optimization** - Monitor and optimize agent costs
3. **Performance tuning** - Regular performance analysis and optimization
4. **Batch processing** - Use batch operations for efficiency

### Monitoring and Analytics

1. **Comprehensive metrics** - Track all relevant system metrics
2. **Regular analysis** - Periodic performance and quality analysis
3. **Pattern recognition** - Leverage pattern detection for optimization
4. **Proactive monitoring** - Set up alerts and automated responses

## Troubleshooting

### Common Issues

1. **Task execution failures**
   - Check task dependencies
   - Verify agent capabilities
   - Review error logs

2. **Pipeline execution issues**
   - Validate step configurations
   - Check conditional logic
   - Review timeout settings

3. **Performance degradation**
   - Monitor system metrics
   - Check resource utilization
   - Review optimization recommendations

4. **Integration failures**
   - Verify API credentials
   - Check network connectivity
   - Review integration logs

### Debugging

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check system health:
```python
health = await self_healing_system.get_system_health()
print(f"System health: {health['overall_health_score']}")
```

Review metrics:
```python
metrics = await analytics_engine.get_system_health_score()
print(f"Performance score: {metrics['overall_score']}")
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review the examples
- Contact the development team

---

**Graph-Sitter CI/CD System** - Intelligent, self-evolving continuous integration and deployment.

