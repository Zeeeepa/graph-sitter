# Enhanced Event System & Multi-Platform Integration

## Overview

The Enhanced Event System provides comprehensive event processing, real-time streaming, and multi-platform integration for Linear, Slack, GitHub, and deployment events. This system is designed to handle high-volume event processing with correlation, analytics, and real-time delivery capabilities.

## Architecture

### Core Components

1. **Event Processing Engine** (`engine.py`)
   - Multi-threaded event processing with priority queues
   - Event correlation across platforms
   - Retry mechanisms and error handling
   - Performance metrics and monitoring

2. **Database Storage Layer** (`storage.py`)
   - PostgreSQL-based event persistence
   - Platform-specific event details storage
   - Event correlation tracking
   - Analytics and metrics aggregation

3. **Real-time Streaming System** (`streaming.py`)
   - WebSocket and Server-Sent Events support
   - Event filtering and subscription management
   - Webhook delivery for external integrations
   - Internal callback system

4. **Enhanced CodegenApp** (`codegen_app.py`)
   - Backward-compatible with existing event handlers
   - Integrated event submission and processing
   - Management APIs for metrics and monitoring

## Database Schema

The system uses a comprehensive PostgreSQL schema with the following key tables:

- `events` - Main events table with unified schema
- `event_processing_status` - Processing status tracking
- `event_correlations` - Cross-platform event linking
- Platform-specific tables: `github_events`, `linear_events`, `slack_events`, `deployment_events`
- Streaming tables: `event_streams`, `stream_subscriptions`, `event_deliveries`
- Analytics tables: `event_metrics`, `event_performance`

### Schema Setup

```sql
-- Run the schema creation script
psql -d your_database -f schemas/events_schema.sql
```

## Configuration

### Basic Configuration

```python
from codegen.extensions.events.codegen_app import CodegenApp

# Event processing configuration
event_config = {
    'max_workers': 4,           # Number of worker threads
    'queue_maxsize': 1000,      # Maximum queue size
    'enable_correlation': True,  # Enable event correlation
    'enable_streaming': True     # Enable real-time streaming
}

# Database configuration (optional)
database_config = {
    'host': 'localhost',
    'port': 5432,
    'database': 'events',
    'user': 'postgres',
    'password': 'your_password',
    'min_connections': 1,
    'max_connections': 10
}

# Create enhanced app
app = CodegenApp(
    name="My Event System",
    event_config=event_config,
    database_config=database_config
)
```

### Environment Variables

```bash
# Database configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=events
DB_USER=postgres
DB_PASSWORD=your_password

# Platform tokens
GITHUB_TOKEN=your_github_token
SLACK_BOT_TOKEN=your_slack_token
LINEAR_API_KEY=your_linear_key
```

## Usage Examples

### 1. Event Handlers (Backward Compatible)

```python
# GitHub event handler
@app.github.event("pull_request:opened")
def handle_pr_opened(event):
    print(f"New PR: {event['pull_request']['title']}")
    return {"message": "PR processed"}

# Linear event handler
@app.linear.event("Issue")
def handle_linear_issue(event):
    print(f"Issue: {event['data']['title']}")
    return {"message": "Issue processed"}

# Slack event handler
@app.slack.event("app_mention")
async def handle_mention(event):
    print(f"Mentioned: {event.text}")
    return {"message": "Mention processed"}
```

### 2. Custom Event Submission

```python
# Submit deployment event
app.submit_deployment_event(
    deployment_id="deploy-123",
    environment="production",
    status="success",
    repository_name="org/repo",
    commit_sha="abc123",
    branch_name="main"
)

# Submit custom event
app.submit_custom_event(
    platform="internal",
    event_type="custom_action",
    payload={"data": "value"},
    priority=EventPriority.HIGH
)
```

### 3. Event Streaming Subscriptions

```python
# Subscribe to all events
def event_logger(event):
    print(f"Event: {event.platform}.{event.event_type}")

subscription_id = app.subscribe_to_events(
    "all_events",
    event_logger,
    "my_logger"
)

# Subscribe with filters
github_filter = {
    "platforms": ["github"],
    "event_types": ["pull_request:*"]
}

pr_subscription = app.subscribe_to_events(
    "github_events",
    handle_pr_events,
    "pr_handler",
    github_filter
)
```

### 4. WebSocket Streaming

```python
from fastapi import WebSocket
from codegen.extensions.events.streaming import websocket_endpoint

@app.app.websocket("/ws/events/{stream_name}")
async def websocket_events(websocket: WebSocket, stream_name: str):
    await websocket_endpoint(websocket, app.streaming_manager, stream_name)
```

### 5. Server-Sent Events

```python
from fastapi import Request
from codegen.extensions.events.streaming import sse_endpoint

@app.app.get("/events/stream/{stream_name}")
async def stream_events(stream_name: str, request: Request):
    filter_params = dict(request.query_params)
    return await sse_endpoint(app.streaming_manager, stream_name, filter_params)
```

## Event Correlation

The system automatically correlates related events across platforms:

### Built-in Correlation Rules

1. **GitHub PR to Linear Issue**: Links PRs to Linear issues based on issue IDs in PR titles/descriptions
2. **Slack Mention to GitHub PR**: Links Slack messages to PRs based on GitHub URLs

### Custom Correlation Rules

```python
def custom_correlation_rule(event):
    """Custom correlation logic."""
    if event.platform == "github" and "deploy" in event.event_type:
        # Correlate deployment events with PRs
        pr_number = event.payload.get("pull_request", {}).get("number")
        if pr_number:
            return f"deployment_pr_{pr_number}"
    return None

app.event_engine.add_correlation_rule(custom_correlation_rule)
```

## Monitoring and Analytics

### Event Metrics

```python
# Get processing metrics
metrics = app.get_event_metrics()
print(f"Events processed: {metrics['processing']['events_processed']}")
print(f"Queue status: {metrics['queue']}")
print(f"Stream stats: {metrics['streaming']}")

# Get recent events
recent_events = app.get_recent_events(limit=50)
for event in recent_events:
    print(f"{event['platform']}.{event['event_type']} - {event['created_at']}")
```

### Database Analytics

```sql
-- Event processing summary
SELECT * FROM event_processing_summary;

-- Recent events with details
SELECT * FROM recent_events LIMIT 10;

-- Correlated events
SELECT * FROM correlated_events WHERE correlation_type = 'pr_to_issue';

-- Event metrics by platform
SELECT 
    platform,
    COUNT(*) as total_events,
    AVG(EXTRACT(EPOCH FROM (processed_at - created_at))) as avg_processing_time
FROM events 
WHERE processed_at IS NOT NULL
GROUP BY platform;
```

## Performance Considerations

### Scaling Guidelines

1. **Worker Threads**: Start with 4 workers, scale based on CPU cores and event volume
2. **Queue Size**: Set based on expected burst capacity (default: 1000)
3. **Database Connections**: Scale connection pool based on worker count
4. **Event Retention**: Regularly cleanup old events to manage database size

### Optimization Tips

1. **Indexing**: The schema includes optimized indexes for common queries
2. **Partitioning**: Consider table partitioning for high-volume deployments
3. **Caching**: Use Redis for frequently accessed event data
4. **Monitoring**: Set up alerts for queue depth and processing times

## Error Handling

### Retry Mechanisms

- Automatic retry for failed event processing
- Configurable retry counts and delays
- Dead letter queue for permanently failed events

### Error Monitoring

```python
# Monitor processing errors
metrics = app.get_event_metrics()
error_rate = metrics['processing']['events_failed'] / metrics['processing']['events_processed']
if error_rate > 0.05:  # 5% error rate threshold
    print("High error rate detected!")
```

## Security Considerations

1. **Database Access**: Use dedicated database user with minimal privileges
2. **Webhook Validation**: Validate webhook signatures from external platforms
3. **Event Filtering**: Sanitize event payloads before processing
4. **Access Control**: Implement authentication for streaming endpoints

## Migration from Basic Event System

The enhanced system is backward compatible with existing event handlers:

1. **No Code Changes Required**: Existing `@app.platform.event()` decorators continue to work
2. **Enhanced Features**: Automatic event storage, correlation, and streaming
3. **Gradual Migration**: Add database configuration when ready for persistence
4. **Monitoring**: Immediate access to metrics and analytics

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Check connection string and credentials
   - Ensure PostgreSQL is running and accessible
   - Verify database schema is created

2. **High Memory Usage**
   - Reduce queue size or increase worker count
   - Check for event processing bottlenecks
   - Monitor correlation cache size

3. **Slow Event Processing**
   - Increase worker thread count
   - Optimize event handler logic
   - Check database query performance

### Debug Mode

```python
import logging
logging.getLogger('codegen.extensions.events').setLevel(logging.DEBUG)
```

## API Reference

### CodegenApp Methods

- `submit_deployment_event()` - Submit deployment events
- `submit_custom_event()` - Submit custom events
- `get_event_metrics()` - Get processing metrics
- `get_recent_events()` - Get recent events from storage
- `subscribe_to_events()` - Subscribe to event streams
- `unsubscribe_from_events()` - Unsubscribe from streams
- `cleanup()` - Cleanup resources on shutdown

### Event Processing Engine

- `submit_event()` - Submit event for processing
- `register_processor()` - Register custom processor
- `add_correlation_rule()` - Add correlation rule
- `get_metrics()` - Get processing metrics
- `start()` / `stop()` - Control processing

### Streaming Manager

- `create_stream()` - Create custom stream
- `subscribe_websocket()` - WebSocket subscription
- `subscribe_sse()` - Server-Sent Events subscription
- `subscribe_webhook()` - Webhook subscription
- `broadcast_event()` - Broadcast to streams

## Contributing

When contributing to the event system:

1. **Database Changes**: Update schema and migration scripts
2. **New Platforms**: Add platform-specific storage tables
3. **Correlation Rules**: Add tests for new correlation logic
4. **Performance**: Benchmark changes with realistic event volumes
5. **Documentation**: Update this guide with new features

## License

This event system is part of the graph-sitter project and follows the same license terms.

