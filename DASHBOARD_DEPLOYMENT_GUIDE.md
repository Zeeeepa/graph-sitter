# Contexten Dashboard Deployment Guide

## 🚀 Quick Start

### Prerequisites

1. **Python 3.8+** installed
2. **Git** for version control
3. **Environment variables** configured (see below)

### Installation

```bash
# 1. Install graph-sitter package
pip install -e .

# 2. Set up environment variables (see Environment Setup section)
export CODEGEN_ORG_ID="your-org-id"
export CODEGEN_TOKEN="your-api-token"
# ... other variables

# 3. Launch the dashboard
python src/contexten/dashboard.py
```

The dashboard will be available at: **http://localhost:8000**

---

## 🔧 Environment Setup

### Required Environment Variables

```bash
# Codegen SDK (Required)
export CODEGEN_ORG_ID="your-codegen-organization-id"
export CODEGEN_TOKEN="your-codegen-api-token"
```

### Optional Environment Variables

```bash
# GitHub Integration
export GITHUB_TOKEN="your-github-personal-access-token"

# Linear Integration
export LINEAR_API_KEY="your-linear-api-key"

# Slack Integration
export SLACK_WEBHOOK_URL="your-slack-webhook-url"

# Prefect Integration
export PREFECT_API_URL="your-prefect-api-url"
export PREFECT_WORKSPACE="your-prefect-workspace"
```

### Environment File Setup

Create a `.env` file in the project root:

```bash
# .env file
CODEGEN_ORG_ID=your-org-id
CODEGEN_TOKEN=your-token
GITHUB_TOKEN=your-github-token
LINEAR_API_KEY=your-linear-key
SLACK_WEBHOOK_URL=your-slack-webhook
PREFECT_API_URL=your-prefect-url
PREFECT_WORKSPACE=your-workspace
```

---

## 🎯 Dashboard Features

### 1. **Flow Management**
- ✅ Create and configure autonomous flows
- ✅ Real-time progress tracking
- ✅ Flow parameter configuration
- ✅ Template-based flow creation
- ✅ WebSocket-based live updates

### 2. **Project Management**
- ✅ Pin projects for easy access
- ✅ Requirements tracking and management
- ✅ Project health monitoring
- ✅ Team collaboration features
- ✅ Integration with GitHub and Linear

### 3. **System Monitoring**
- ✅ Real-time system health status
- ✅ Performance metrics dashboard
- ✅ Error tracking and alerting
- ✅ Resource utilization monitoring

### 4. **Agent Orchestration**
- ✅ Multi-agent coordination
- ✅ Task execution and monitoring
- ✅ Agent performance tracking
- ✅ Intelligent task routing

---

## 📊 API Endpoints

### Flow Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/flows` | List all flows |
| POST | `/api/flows/create` | Create new flow |
| GET | `/api/flows/{id}` | Get flow details |
| POST | `/api/flows/{id}/start` | Start flow execution |
| POST | `/api/flows/{id}/stop` | Stop flow execution |
| WS | `/ws/flows/{id}` | Real-time flow updates |

### Project Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/projects/pinned` | List pinned projects |
| POST | `/api/projects/pin` | Pin a project |
| DELETE | `/api/projects/{id}/pin` | Unpin a project |
| GET | `/api/projects/{id}` | Get project details |
| GET | `/api/projects/{id}/dashboard` | Get project dashboard |
| PUT | `/api/projects/{id}` | Update project |

### Requirements Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/projects/{id}/requirements` | List requirements |
| POST | `/api/projects/{id}/requirements` | Add requirement |
| GET | `/api/projects/{id}/requirements/stats` | Get requirement stats |

### System Monitoring

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/system/health` | System health status |
| GET | `/api/system/metrics` | Performance metrics |
| GET | `/api/dashboard/stats` | Dashboard statistics |

### Flow Templates

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/flow-templates` | List templates |
| GET | `/api/flow-templates/{id}` | Get template details |

---

## 🔄 Flow Types and Templates

### Available Flow Templates

#### 1. **Feature Development**
- **Purpose**: Complete feature development workflow
- **Duration**: ~120 minutes
- **Parameters**:
  - `feature_name`: Name of the feature
  - `requirements`: Detailed requirements
  - `priority`: Priority level (low/normal/high/critical)
  - `target_branch`: Target branch for development
  - `create_tests`: Whether to create automated tests
  - `reviewers`: List of code reviewers

#### 2. **Bug Fix**
- **Purpose**: Automated bug investigation and fix
- **Duration**: ~60 minutes
- **Parameters**:
  - `bug_description`: Description of the bug
  - `reproduction_steps`: Steps to reproduce
  - `severity`: Bug severity level
  - `affected_components`: List of affected components
  - `hotfix`: Whether this is a hotfix

#### 3. **Code Review**
- **Purpose**: Comprehensive automated code review
- **Duration**: ~30 minutes
- **Parameters**:
  - `pr_url`: GitHub Pull Request URL
  - `review_depth`: Analysis depth (basic/standard/comprehensive)
  - `check_security`: Include security analysis
  - `check_performance`: Include performance analysis
  - `auto_approve`: Auto-approve if all checks pass

---

## 🏗️ Architecture Overview

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Contexten Dashboard                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Flow        │  │ Project     │  │ System      │         │
│  │ Manager     │  │ Manager     │  │ Monitor     │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Autonomous  │  │ Agent       │  │ Prefect     │         │
│  │ Orchestrator│  │ Coordinator │  │ Integration │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ GitHub      │  │ Linear      │  │ Slack       │         │
│  │ Integration │  │ Integration │  │ Integration │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **User Input** → Dashboard UI
2. **Flow Creation** → Template Validation → Parameter Processing
3. **Execution** → Agent Orchestration → Real-time Updates
4. **Monitoring** → Health Checks → Metrics Collection
5. **Integration** → GitHub/Linear/Slack → Notifications

---

## 🛠️ Configuration Options

### Command Line Arguments

```bash
python src/contexten/dashboard.py --help

Options:
  --host TEXT        Host to bind to (default: 0.0.0.0)
  --port INTEGER     Port to bind to (default: 8000)
  --config TEXT      Path to configuration file
  --debug            Enable debug mode
```

### Configuration File

Create `config.yaml`:

```yaml
# Dashboard Configuration
dashboard:
  host: "0.0.0.0"
  port: 8000
  debug: false

# Orchestration Settings
orchestration:
  max_concurrent_workflows: 5
  default_timeout_minutes: 30
  auto_recovery_enabled: true
  monitoring_enabled: true

# Health Check Settings
health_checks:
  interval_minutes: 15
  performance_monitoring_interval_minutes: 60
  dependency_check_interval_hours: 24

# Alert Thresholds
alerts:
  cpu_usage_percent: 80
  memory_usage_percent: 80
  disk_usage_percent: 90
```

---

## 📈 Monitoring and Metrics

### Health Monitoring

The dashboard continuously monitors:

- **System Health**: CPU, memory, disk usage
- **Flow Health**: Execution status, error rates
- **Integration Health**: API connectivity, response times
- **Agent Health**: Availability, performance metrics

### Performance Metrics

- **Flow Metrics**: Completion rate, execution time, error rate
- **Project Metrics**: Code quality, test coverage, deployment frequency
- **System Metrics**: Resource utilization, response times
- **User Metrics**: Dashboard usage, feature adoption

### Alerting

Automatic alerts for:
- System resource thresholds exceeded
- Flow execution failures
- Integration connectivity issues
- Performance degradation

---

## 🔧 Troubleshooting

### Common Issues

#### 1. **Dashboard Won't Start**
```bash
# Check environment variables
python -c "import os; print('CODEGEN_ORG_ID:', os.getenv('CODEGEN_ORG_ID'))"

# Check dependencies
pip install -e .

# Check port availability
netstat -an | grep :8000
```

#### 2. **Flow Creation Fails**
- Verify template parameters
- Check agent availability
- Review system logs

#### 3. **Integration Issues**
- Verify API tokens and credentials
- Check network connectivity
- Review integration logs

#### 4. **Performance Issues**
- Monitor system resources
- Check database connections
- Review concurrent flow limits

### Debug Mode

Enable debug mode for detailed logging:

```bash
python src/contexten/dashboard.py --debug
```

### Log Files

Check log files for detailed information:
- `contexten_dashboard.log`: Main dashboard logs
- `flow_execution.log`: Flow execution logs
- `system_monitor.log`: System monitoring logs

---

## 🚀 Advanced Usage

### Custom Flow Templates

Create custom flow templates:

```python
from src.contexten.dashboard.flow_manager import FlowTemplate, FlowParameter

custom_template = FlowTemplate(
    id="custom_workflow",
    name="Custom Workflow",
    description="Your custom workflow description",
    category="Custom",
    workflow_type="custom",
    estimated_duration=90,
    parameters=[
        FlowParameter(
            name="custom_param",
            type="string",
            description="Custom parameter description",
            required=True
        )
    ]
)

# Add to template manager
flow_manager.template_manager.create_template(custom_template)
```

### WebSocket Integration

Connect to real-time flow updates:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/flows/flow-id');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Flow update:', data);
};
```

### API Integration

Use the REST API programmatically:

```python
import requests

# Create a new flow
response = requests.post('http://localhost:8000/api/flows/create', json={
    'template_id': 'feature_development',
    'parameters': {
        'feature_name': 'New Feature',
        'requirements': 'Detailed requirements...',
        'priority': 'high'
    },
    'project_id': 'project-123'
})

flow_data = response.json()
print(f"Created flow: {flow_data['flow_id']}")
```

---

## 📚 Additional Resources

### Documentation
- [Flow Management Guide](./docs/flow-management.md)
- [Project Management Guide](./docs/project-management.md)
- [API Reference](./docs/api-reference.md)
- [Integration Guide](./docs/integrations.md)

### Support
- GitHub Issues: [Report bugs and feature requests](https://github.com/Zeeeepa/graph-sitter/issues)
- Documentation: [Full documentation](./docs/)
- Examples: [Usage examples](./examples/)

---

## 🎉 Success!

Your Contexten Dashboard is now ready for autonomous CI/CD flow management!

**Next Steps:**
1. Pin your first project
2. Create your first flow
3. Monitor system health
4. Explore advanced features

**Dashboard URL:** http://localhost:8000

Enjoy building with autonomous intelligence! 🤖✨

