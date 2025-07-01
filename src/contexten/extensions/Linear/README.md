# Comprehensive Linear Integration for Graph-Sitter

A super comprehensive Linear API integration system that provides real-time webhook processing, intelligent assignment detection, automated workflow management, and seamless integration with the Codegen SDK.

## 🎯 Overview

This enhanced Linear integration transforms the basic GraphQL client into a sophisticated automation system that:

- **Automatically detects** when the bot is assigned to Linear issues
- **Intelligently processes** issue requirements and creates appropriate tasks
- **Integrates seamlessly** with the Codegen SDK for automated code generation
- **Provides real-time progress** updates back to Linear
- **Monitors and manages** the entire task lifecycle
- **Handles failures gracefully** with retry logic and error recovery

## 🏗️ Architecture

### Core Components

1. **Enhanced Linear Client** (`enhanced_client.py`)
   - Advanced GraphQL client with rate limiting, caching, and retry logic
   - Comprehensive error handling and performance monitoring
   - Response caching with TTL for improved performance
   - Request/response statistics and metrics

2. **Webhook Processor** (`webhook_processor.py`)
   - Secure webhook validation with HMAC-SHA256 signatures
   - Event routing and handler management
   - Asynchronous event processing with queuing
   - Event persistence and replay for reliability

3. **Assignment Detector** (`assignment_detector.py`)
   - Intelligent bot assignment detection
   - Auto-assignment based on labels and keywords
   - Rate limiting and cooldown management
   - Assignment history tracking and analytics

4. **Workflow Automation** (`workflow_automation.py`)
   - Task creation from Linear issues
   - Integration with Codegen SDK for execution
   - Real-time progress tracking and reporting
   - Task lifecycle management

5. **Integration Agent** (`integration_agent.py`)
   - Main orchestrator coordinating all components
   - Health monitoring and system status tracking
   - Background task management
   - Comprehensive metrics collection

## 🚀 Features

### Intelligent Automation
- **Smart Assignment Detection**: Automatically detects when the bot is assigned to issues
- **Auto-Assignment**: Assigns bot to issues based on configurable labels and keywords
- **Task Type Detection**: Intelligently determines task type (code generation, bug fix, feature implementation, code review)
- **Progress Tracking**: Real-time progress updates with detailed status information

### Robust Infrastructure
- **Rate Limiting**: Respects Linear API rate limits with intelligent backoff
- **Caching**: Response caching for improved performance and reduced API calls
- **Error Handling**: Comprehensive error handling with retry logic
- **Event Persistence**: Failed events are persisted and retried automatically
- **Health Monitoring**: Continuous health checks and system monitoring

### Codegen SDK Integration
- **Seamless Integration**: Direct integration with Codegen SDK for task execution
- **Task Templates**: Configurable templates for different types of tasks
- **Progress Monitoring**: Real-time monitoring of Codegen task execution
- **Result Posting**: Automatic posting of results back to Linear issues

## 📋 Configuration

### Environment Variables

```bash
# Core Settings
LINEAR_ENABLED=true
LINEAR_API_KEY=your_linear_api_key_here
LINEAR_WEBHOOK_SECRET=your_webhook_secret_here

# Bot Configuration
LINEAR_BOT_USER_ID=your_bot_user_id
LINEAR_BOT_EMAIL=your_bot_email
LINEAR_BOT_NAMES=codegen,openalpha,bot

# API Configuration
LINEAR_API_TIMEOUT=30
LINEAR_API_MAX_RETRIES=3
LINEAR_RATE_LIMIT_REQUESTS=100
LINEAR_RATE_LIMIT_WINDOW=60
LINEAR_CACHE_TTL=300

# Assignment Configuration
LINEAR_AUTO_ASSIGN_LABELS=ai,automation,codegen
LINEAR_AUTO_ASSIGN_KEYWORDS=generate,evolve,optimize,automate
LINEAR_MAX_ASSIGNMENTS_PER_HOUR=10
LINEAR_ASSIGNMENT_COOLDOWN=300

# Workflow Configuration
LINEAR_AUTO_START_TASKS=true
LINEAR_AUTO_UPDATE_STATUS=true
LINEAR_PROGRESS_UPDATE_INTERVAL=60
LINEAR_STATUS_SYNC_INTERVAL=300
LINEAR_TASK_TIMEOUT=3600

# Event Management
LINEAR_EVENT_QUEUE_SIZE=1000
LINEAR_EVENT_BATCH_SIZE=10
LINEAR_EVENT_PROCESSING_INTERVAL=5
LINEAR_EVENT_RETRY_INTERVAL=60
LINEAR_EVENT_PERSISTENCE_ENABLED=true

# Monitoring
LINEAR_MONITORING_ENABLED=true
LINEAR_MONITORING_INTERVAL=60
LINEAR_HEALTH_CHECK_INTERVAL=300
```

### Configuration Loading

```python
from contexten.extensions.Linear import get_linear_config, LinearIntegrationAgent

# Load configuration from environment
config = get_linear_config()

# Create and initialize agent
agent = LinearIntegrationAgent(config)
```

## 🔧 Usage

### Basic Setup

```python
from contexten.extensions.Linear import create_linear_integration_agent

# Create and initialize the comprehensive integration
agent = await create_linear_integration_agent()

# The agent is now running and monitoring for assignments
```

### Integration with ContextenApp

The enhanced Linear integration is automatically integrated with the existing `ContextenApp` through the enhanced `Linear` event handler:

```python
from contexten.extensions.events.contexten_app import ContextenApp

# Create app - Linear integration is automatically initialized
app = ContextenApp(name="my-app")

# Initialize the Linear agent
await app.linear.initialize_agent()

# Get integration status
status = await app.linear.get_integration_status()
print(f"Integration status: {status}")

# Get comprehensive metrics
metrics = await app.linear.get_metrics()
print(f"Active tasks: {metrics['status']['active_tasks']}")
```

### Manual Task Creation

```python
from contexten.extensions.Linear.types import LinearIssue

# Create issue object
issue = LinearIssue(
    id="issue_id",
    title="Implement fibonacci function",
    description="Create a function that calculates fibonacci numbers efficiently",
    assignee_id="bot_user_id"
)

# Create task from issue
task = await agent.workflow_automation.create_task_from_issue(issue)

# Start task execution
if task:
    success = await agent.workflow_automation.start_task(task.id)
    print(f"Task started: {success}")
```

### Webhook Handling

```python
from fastapi import Request

@app.post("/linear/webhook")
async def handle_linear_webhook(request: Request):
    payload = await request.body()
    signature = request.headers.get("Linear-Signature", "")
    
    success = await agent.handle_webhook(payload, signature)
    return {"success": success}
```

## 📊 Monitoring and Metrics

### Integration Status

```python
# Get comprehensive status
status = await agent.get_integration_status()

print(f"Initialized: {status.initialized}")
print(f"Monitoring Active: {status.monitoring_active}")
print(f"Active Tasks: {status.active_tasks}")
print(f"Processed Events: {status.processed_events}")
print(f"Failed Events: {status.failed_events}")
```

### Component Metrics

```python
# Get detailed metrics
metrics = await agent.get_metrics()

# Client statistics
client_stats = metrics.client_stats
print(f"API Requests: {client_stats.requests_made}")
print(f"Cache Hit Rate: {client_stats.cache_hits / (client_stats.cache_hits + client_stats.cache_misses):.2%}")

# Webhook statistics
webhook_stats = metrics.webhook_stats
print(f"Events Processed: {webhook_stats.requests_successful}")
print(f"Events Failed: {webhook_stats.requests_failed}")

# Assignment statistics
assignment_stats = metrics.assignment_stats
print(f"Assignments Detected: {assignment_stats.requests_made}")
print(f"Assignments Processed: {assignment_stats.requests_successful}")

# Workflow statistics
workflow_stats = metrics.workflow_stats
print(f"Tasks Created: {workflow_stats.requests_made}")
print(f"Tasks Completed: {workflow_stats.requests_successful}")
```

### Active Tasks

```python
# Get information about active tasks
active_tasks = agent.workflow_automation.get_active_tasks()

for issue_id, task_info in active_tasks.items():
    print(f"Issue {issue_id}:")
    print(f"  Status: {task_info['status']}")
    print(f"  Progress: {task_info['progress']:.1f}%")
    print(f"  Current Step: {task_info['current_step']}")
```

## 🔄 Workflow Examples

### Issue Assignment Workflow

1. **Issue Created/Updated**: Linear webhook triggered
2. **Assignment Detection**: Bot assignment detected by `AssignmentDetector`
3. **Task Creation**: `WorkflowAutomation` creates task from issue
4. **Task Execution**: Integration with Codegen SDK begins
5. **Progress Updates**: Real-time progress comments posted to Linear
6. **Completion**: Final results posted to Linear issue

### Auto-assignment Workflow

1. **Issue Created**: New issue with specific labels/keywords
2. **Auto-assignment Check**: `AssignmentDetector` evaluates labels and keywords
3. **Bot Assignment**: Bot automatically assigned to issue via Linear API
4. **Workflow Trigger**: Standard assignment workflow begins

### Task Types and Templates

The system automatically detects task types based on issue content:

- **Bug Fix**: Issues with labels like "bug", "fix", "error" or keywords like "broken", "issue"
- **Feature Implementation**: Issues with labels like "feature", "enhancement" or keywords like "implement", "add"
- **Code Review**: Issues with labels like "review", "audit" or keywords like "review", "analyze"
- **Code Generation**: Default type for other issues

Each task type has a customized prompt template optimized for that specific type of work.

## 🔒 Security

### Webhook Security
- **Signature Validation**: HMAC-SHA256 signature verification
- **Timestamp Validation**: Replay attack prevention
- **Payload Sanitization**: Input validation and sanitization
- **Size Limits**: Configurable payload size restrictions

### API Security
- **Authentication**: Bearer token authentication with Linear API
- **Rate Limiting**: Compliance with Linear API rate limits
- **Error Handling**: Secure error message handling without information leakage
- **Input Validation**: Comprehensive input validation throughout

## ��� Error Handling and Recovery

### Retry Mechanisms
- **Webhook Processing**: Automatic retry for failed webhook events with exponential backoff
- **API Requests**: Intelligent retry logic for API failures
- **Event Processing**: Queue-based retry for event processing failures
- **Task Execution**: Graceful handling of task execution failures

### Monitoring and Alerting
- **Health Checks**: Continuous system health monitoring
- **Stuck Task Detection**: Automatic detection and cancellation of stuck tasks
- **Failed Event Tracking**: Comprehensive tracking of failed events
- **Performance Monitoring**: Real-time performance metrics and alerting

## 🔧 Development and Testing

### Running Tests

```bash
# Run comprehensive integration tests
python -m pytest src/contexten/extensions/Linear/tests/ -v

# Run specific component tests
python -m pytest src/contexten/extensions/Linear/tests/test_enhanced_client.py -v
python -m pytest src/contexten/extensions/Linear/tests/test_webhook_processor.py -v
python -m pytest src/contexten/extensions/Linear/tests/test_assignment_detector.py -v
python -m pytest src/contexten/extensions/Linear/tests/test_workflow_automation.py -v
```

### Configuration Template

Generate a complete configuration template:

```python
from contexten.extensions.Linear import create_config_template

template = create_config_template()
print(template)
```

### Debugging

Enable debug logging for detailed information:

```python
import logging
logging.getLogger("contexten.extensions.Linear").setLevel(logging.DEBUG)
```

## 🤝 Backward Compatibility

The enhanced integration maintains full backward compatibility with the existing Linear integration:

- **Existing handlers** continue to work unchanged
- **Legacy LinearClient** remains available
- **Existing event processing** is preserved
- **API compatibility** is maintained

The comprehensive features are additive and can be enabled/disabled via configuration.

## 📈 Performance Optimizations

### Caching Strategy
- **Response Caching**: Intelligent caching of API responses with TTL
- **Cache Invalidation**: Smart cache invalidation based on events
- **Memory Management**: Automatic cleanup of expired cache entries

### Rate Limiting
- **Adaptive Rate Limiting**: Dynamic adjustment based on API responses
- **Request Queuing**: Intelligent request queuing to avoid rate limits
- **Backoff Strategies**: Exponential backoff for rate limit recovery

### Async Processing
- **Event Queuing**: Asynchronous event processing with configurable queue sizes
- **Batch Processing**: Batch processing for improved throughput
- **Background Tasks**: Non-blocking background task execution

## 🔮 Future Enhancements

Planned enhancements for future versions:

- **Machine Learning**: ML-based task type detection and priority assignment
- **Advanced Analytics**: Comprehensive analytics dashboard
- **Multi-tenant Support**: Support for multiple Linear organizations
- **Custom Integrations**: Plugin system for custom integrations
- **Advanced Workflows**: Support for complex multi-step workflows

## 📝 License

This comprehensive Linear integration is part of the graph-sitter project and follows the same licensing terms.

## 🆘 Support

For issues, questions, or contributions:

1. **Check Configuration**: Ensure all environment variables are properly set
2. **Review Logs**: Check the application logs for detailed error information
3. **Test Connectivity**: Verify Linear API connectivity and webhook configuration
4. **Monitor Metrics**: Use the built-in metrics to identify issues
5. **Create Issues**: Report bugs with detailed reproduction steps

---

**Note**: This integration requires valid Linear API credentials and proper webhook configuration. The comprehensive features are designed to work alongside the existing basic integration, providing a smooth upgrade path.

## 🔥 Backward Incompatibilities

### Changes to Event Handling

- **Event Handler Changes**: The event handling mechanism has been updated to use the `ContextenApp` event handler instead of the `Linear` event handler. This change ensures better integration with the existing `ContextenApp` framework.

---

**Note**: This integration requires valid Linear API credentials and proper webhook configuration. The comprehensive features are designed to work alongside the existing basic integration, providing a smooth upgrade path.
