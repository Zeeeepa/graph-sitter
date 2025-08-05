# Self-Healing Architecture

A comprehensive self-healing system that provides automated error detection, diagnosis, and recovery capabilities for the graph-sitter platform.

## Overview

The self-healing architecture enables the system to automatically detect, diagnose, and recover from various types of errors and performance issues without human intervention. It includes continuous learning capabilities to improve recovery effectiveness over time.

## Features

### 🔍 Error Detection System
- **Real-time monitoring** of system health metrics (CPU, memory, network, disk)
- **Anomaly detection** algorithms for performance degradation
- **Pattern recognition** for recurring issues
- **Threshold-based alerting** with configurable escalation

### 🧠 Automated Diagnosis Engine
- **Root cause analysis** algorithms
- **Event correlation** to identify related issues
- **Decision trees** for automated problem resolution
- **Integration** with existing analytics and logging

### 🔧 Recovery and Remediation System
- **Automated recovery procedures** for common failures
- **Rollback mechanisms** for failed deployments
- **Self-optimization triggers** and procedures
- **Escalation to human intervention** when needed

### 📊 Monitoring and Feedback Loop
- **Effectiveness tracking** for recovery actions
- **Learning mechanisms** for improving procedures
- **Health monitoring** and system status reporting
- **Continuous improvement** through pattern analysis

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Self-Healing Orchestrator                │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │ Error Detection │  │ Diagnosis Engine│  │ Recovery     │ │
│  │                 │  │                 │  │ System       │ │
│  │ • CPU Monitor   │  │ • Root Cause    │  │ • Actions    │ │
│  │ • Memory Monitor│  │   Analysis      │  │ • Rollbacks  │ │
│  │ • Network Mon.  │  │ • Event         │  │ • Escalation │ │
│  │ • Anomaly Det.  │  │   Correlation   │  │ • Procedures │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                Health Monitor                           │ │
│  │ • System Status  • Effectiveness Tracking              │ │
│  │ • Performance    • Learning Engine                     │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### Basic Usage

```python
import asyncio
from graph_sitter.self_healing import SelfHealingConfig
from graph_sitter.self_healing.orchestrator import SelfHealingOrchestrator

async def main():
    # Create configuration
    config = SelfHealingConfig(
        enabled=True,
        log_level="INFO"
    )
    
    # Initialize orchestrator
    orchestrator = SelfHealingOrchestrator(config)
    
    try:
        # Start the self-healing system
        await orchestrator.start()
        
        # System will now automatically detect and recover from errors
        # Monitor status
        status = orchestrator.get_system_status()
        print(f"System status: {status}")
        
        # Keep running
        await asyncio.sleep(3600)  # Run for 1 hour
        
    finally:
        await orchestrator.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

### Configuration

Create a `config.yaml` file:

```yaml
self_healing:
  enabled: true
  
  error_detection:
    monitoring_interval: 30
    threshold_cpu: 80.0
    threshold_memory: 85.0
    threshold_error_rate: 5.0
    pattern_recognition_enabled: true
    anomaly_detection_enabled: true
  
  recovery:
    max_retry_attempts: 3
    escalation_timeout: 300
    rollback_enabled: true
    auto_scaling_enabled: true
  
  learning:
    effectiveness_tracking: true
    pattern_recognition: true
    continuous_improvement: true
```

Load configuration:

```python
import yaml
from graph_sitter.self_healing.models.config import SelfHealingConfig

with open('config.yaml', 'r') as f:
    config_dict = yaml.safe_load(f)

config = SelfHealingConfig.from_dict(config_dict['self_healing'])
```

## Components

### Error Detection Service

Monitors system health and detects various types of errors:

```python
from graph_sitter.self_healing.error_detection import ErrorDetectionService
from graph_sitter.self_healing.models.config import ErrorDetectionConfig

config = ErrorDetectionConfig(
    monitoring_interval=30,
    threshold_cpu=80.0,
    threshold_memory=85.0
)

service = ErrorDetectionService(config)

# Add error handler
def on_error(error_event):
    print(f"Error detected: {error_event.message}")

service.add_error_handler(on_error)

await service.start()
```

### Diagnosis Engine

Performs root cause analysis and generates recommendations:

```python
from graph_sitter.self_healing.diagnosis import DiagnosisEngine
from graph_sitter.self_healing.models.events import ErrorEvent
from graph_sitter.self_healing.models.enums import ErrorType, ErrorSeverity

engine = DiagnosisEngine()

error_event = ErrorEvent(
    error_type=ErrorType.MEMORY_LEAK,
    severity=ErrorSeverity.HIGH,
    message="Memory usage exceeded threshold"
)

diagnosis = await engine.analyze_error("error-123", error_event)
print(f"Root cause: {diagnosis.root_cause}")
print(f"Recommendations: {diagnosis.recommended_actions}")
```

### Recovery System

Executes automated recovery actions:

```python
from graph_sitter.self_healing.recovery import RecoverySystem
from graph_sitter.self_healing.models.config import RecoveryConfig
from graph_sitter.self_healing.models.events import RecoveryAction

config = RecoveryConfig(
    max_retry_attempts=3,
    rollback_enabled=True
)

system = RecoverySystem(config)

action = RecoveryAction(
    action_type="restart_service",
    description="Restart affected service",
    parameters={"service_name": "web_server"}
)

result = await system.execute_recovery_action(action)
print(f"Recovery result: {result.status}")
```

### Health Monitor

Tracks system health and recovery effectiveness:

```python
from graph_sitter.self_healing.monitoring import HealthMonitor

monitor = HealthMonitor(update_interval=30)

# Add status handler
def on_status_change(new_status):
    print(f"Health status: {new_status}")

monitor.add_status_handler(on_status_change)

await monitor.start()

# Get system status
status = monitor.get_system_status()
print(f"System health: {status}")
```

## Database Schema

The self-healing system uses the following database tables:

### Error Incidents
```sql
CREATE TABLE error_incidents (
    id UUID PRIMARY KEY,
    error_type VARCHAR(100),
    severity VARCHAR(50),
    detected_at TIMESTAMP,
    resolved_at TIMESTAMP,
    diagnosis JSONB,
    recovery_actions JSONB,
    effectiveness_score DECIMAL(3,2)
);
```

### Recovery Procedures
```sql
CREATE TABLE recovery_procedures (
    id UUID PRIMARY KEY,
    error_pattern VARCHAR(255),
    procedure_steps JSONB,
    success_rate DECIMAL(3,2),
    last_updated TIMESTAMP
);
```

### System Health Metrics
```sql
CREATE TABLE system_health_metrics (
    id UUID PRIMARY KEY,
    metric_name VARCHAR(100),
    current_value DECIMAL(15,6),
    threshold_warning DECIMAL(15,6),
    threshold_critical DECIMAL(15,6),
    status VARCHAR(50),
    measured_at TIMESTAMP
);
```

## Error Types

The system can detect and handle various error types:

- **MEMORY_LEAK**: Memory usage issues and leaks
- **CPU_SPIKE**: High CPU usage and performance issues
- **NETWORK_TIMEOUT**: Network connectivity and timeout issues
- **DATABASE_CONNECTION**: Database connectivity problems
- **API_FAILURE**: API and service failures
- **DEPLOYMENT_FAILURE**: Deployment and rollback issues
- **CONFIGURATION_ERROR**: Configuration and environment issues
- **DEPENDENCY_FAILURE**: Dependency and module issues

## Recovery Actions

Available recovery actions include:

- **restart_service**: Restart affected services
- **scale_resources**: Scale CPU/memory resources
- **rollback_deployment**: Rollback failed deployments
- **increase_resources**: Increase resource allocations
- **adjust_timeout**: Adjust timeout values
- **enable_monitoring**: Enable additional monitoring
- **health_check**: Perform health checks

## Monitoring and Metrics

The system tracks various metrics:

### Performance Metrics
- **Mean Time to Detection (MTTD)**: Average time to detect errors
- **Mean Time to Recovery (MTTR)**: Average time to recover from errors
- **Recovery Success Rate**: Percentage of successful recoveries
- **Error Rate**: Number of errors per hour
- **System Uptime**: Overall system availability

### Effectiveness Metrics
- **Action Effectiveness**: Success rate by action type
- **Error Type Effectiveness**: Recovery success by error type
- **Severity Effectiveness**: Recovery success by severity level
- **Learning Insights**: Patterns and improvement opportunities

## Configuration Options

### Error Detection
- `monitoring_interval`: How often to check system health (seconds)
- `threshold_cpu`: CPU usage threshold (percentage)
- `threshold_memory`: Memory usage threshold (percentage)
- `threshold_error_rate`: Error rate threshold (percentage)
- `pattern_recognition_enabled`: Enable pattern recognition
- `anomaly_detection_enabled`: Enable anomaly detection

### Recovery
- `max_retry_attempts`: Maximum retry attempts for recovery actions
- `escalation_timeout`: Timeout before escalating to humans (seconds)
- `rollback_enabled`: Enable automatic rollbacks
- `auto_scaling_enabled`: Enable automatic resource scaling
- `recovery_timeout`: Maximum time for recovery actions (seconds)

### Learning
- `effectiveness_tracking`: Track recovery effectiveness
- `pattern_recognition`: Learn from error patterns
- `continuous_improvement`: Enable continuous learning
- `learning_rate`: Rate of learning adaptation
- `confidence_threshold`: Minimum confidence for automated actions

## Testing

Run the test suite:

```bash
# Run all self-healing tests
pytest tests/self_healing/

# Run specific test files
pytest tests/self_healing/test_error_detection.py
pytest tests/self_healing/test_orchestrator.py

# Run with coverage
pytest tests/self_healing/ --cov=src/graph_sitter/self_healing
```

## Examples

See the `examples/` directory for complete usage examples:

- `basic_usage.py`: Basic setup and usage
- `custom_monitors.py`: Custom monitoring implementation
- `recovery_procedures.py`: Custom recovery procedures
- `integration_example.py`: Integration with existing systems

## Integration

### With Existing Monitoring

```python
# Integrate with existing monitoring systems
from graph_sitter.self_healing.error_detection.monitors import BaseMonitor

class CustomMonitor(BaseMonitor):
    async def get_current_value(self) -> float:
        # Integrate with your monitoring system
        return await your_monitoring_system.get_metric()
    
    def get_metric_name(self) -> str:
        return "custom_metric"

# Add to error detection service
service.monitors["custom"] = CustomMonitor()
```

### With CI/CD Systems

```python
# Custom rollback integration
from graph_sitter.self_healing.recovery.actions import RollbackManager

class CustomRollbackManager(RollbackManager):
    async def rollback_deployment(self, deployment_id: str):
        # Integrate with your CI/CD system
        return await your_cicd_system.rollback(deployment_id)
```

## Troubleshooting

### Common Issues

1. **High False Positive Rate**
   - Adjust thresholds in configuration
   - Enable anomaly detection for better accuracy
   - Review error classification patterns

2. **Low Recovery Success Rate**
   - Review recovery procedures
   - Check resource availability
   - Verify escalation procedures

3. **Performance Impact**
   - Increase monitoring intervals
   - Optimize monitor implementations
   - Use async operations

### Debugging

Enable debug logging:

```python
import logging
logging.getLogger('graph_sitter.self_healing').setLevel(logging.DEBUG)
```

Check system status:

```python
status = orchestrator.get_system_status()
print(f"Active incidents: {status['active_incidents']}")
print(f"Recovery stats: {status['recovery_stats']}")
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

