# Contexten Enhanced Dashboard

A comprehensive web interface for managing autonomous CI/CD flows, project tracking, Linear issue management, GitHub PR automation, and full workflow orchestration.

## 🚀 Quick Start

### Prerequisites

1. **Python 3.8+** installed
2. **Environment variables** configured (see below)
3. **Git** for version control

### Installation & Launch

```bash
# 1. Install dependencies
pip install -e .

# 2. Set up environment variables
export CODEGEN_ORG_ID="your-codegen-org-id"
export CODEGEN_TOKEN="your-codegen-api-token"
# ... other optional variables

# 3. Launch the enhanced dashboard
python launch_dashboard.py

# Or with custom settings
python launch_dashboard.py --host 0.0.0.0 --port 8000 --debug
```

The dashboard will be available at: **http://localhost:8000**

## 🎯 Enhanced Features

### 📋 Flow Management
- **Create & Configure Flows**: Use templates or custom configurations
- **Real-time Progress Tracking**: Live updates via WebSocket connections
- **Flow Parameter Management**: Dynamic parameter validation and templates
- **Flow Execution Control**: Start, stop, monitor, and heal flows
- **Flow Templates**: Pre-built templates for common workflows

### 📁 Project Management
- **Project Pinning**: Pin important projects for quick access
- **Requirements Tracking**: Manage project requirements and dependencies
- **Project Health Monitoring**: Real-time health scores and analytics
- **Team Collaboration**: Multi-user project management
- **Project Dashboard**: Comprehensive project overview

### 🔗 Integration Hub
- **Linear Integration**: 
  - Issue state tracking with comprehensive status
  - Automatic flow creation from issues
  - Bidirectional synchronization
  - Sub-issue management
- **GitHub Integration**:
  - PR status monitoring and validation
  - Automated PR creation and management
  - Check status tracking
  - Merge conflict resolution
- **Slack Integration**:
  - Smart notification routing
  - Flow completion alerts
  - Error notifications
  - Team updates

### 🤖 Autonomous Operations
- **Self-Healing Flows**: Automatic error detection and recovery
- **Intelligent Retry Logic**: Smart retry strategies based on error types
- **Predictive Maintenance**: Proactive issue detection and resolution
- **Resource Optimization**: Dynamic resource allocation and scaling
- **Error Pattern Recognition**: Learn from past failures

### 📊 Analytics & Monitoring
- **Real-time Monitoring**: System health, resource usage, flow status
- **Performance Analytics**: Flow execution metrics and trends
- **Predictive Analytics**: Failure prediction and capacity planning
- **Team Productivity Metrics**: Developer productivity tracking
- **Custom Dashboards**: Configurable monitoring dashboards

## 🔌 API Endpoints

### Flow Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/flows` | List all flows with filtering |
| POST | `/api/flows/create` | Create new flow |
| GET | `/api/flows/{id}` | Get flow details |
| POST | `/api/flows/{id}/start` | Start flow execution |
| POST | `/api/flows/{id}/stop` | Stop flow execution |
| GET | `/api/flows/{id}/progress` | Get real-time progress |
| WS | `/ws/flows/{id}` | Real-time flow updates |

### Project Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/projects/pinned` | Get pinned projects |
| POST | `/api/projects/{id}/pin` | Pin a project |
| DELETE | `/api/projects/{id}/pin` | Unpin a project |
| GET | `/api/projects/{id}/dashboard` | Get project dashboard |
| GET | `/api/projects/{id}/requirements` | Get project requirements |
| POST | `/api/projects/{id}/requirements` | Add requirement |
| WS | `/ws/projects/{id}` | Real-time project updates |

### Linear Integration

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/linear/issues/{project}` | Get Linear issues with states |
| GET | `/api/linear/issues/{id}/state` | Get detailed issue state |
| POST | `/api/linear/sync/{project}` | Sync Linear with flows |

### Templates & Configuration

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/flow-templates` | Get available templates |
| GET | `/api/flow-templates/{id}` | Get template details |

## 🛠️ Configuration

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

# Dashboard Configuration
export DASHBOARD_HOST="0.0.0.0"
export DASHBOARD_PORT="8000"
export DASHBOARD_DEBUG="false"
export DASHBOARD_SECRET_KEY="your-secret-key"
```

### Configuration File

Create `config.yaml` for advanced configuration:

```yaml
dashboard:
  host: "0.0.0.0"
  port: 8000
  debug: false

orchestration:
  max_concurrent_workflows: 10
  default_timeout_minutes: 30
  auto_recovery_enabled: true
  monitoring_enabled: true

health_checks:
  interval_minutes: 15
  performance_monitoring_interval_minutes: 60
  dependency_check_interval_hours: 24

alerts:
  cpu_usage_percent: 80
  memory_usage_percent: 80
  disk_usage_percent: 90
```

## 📊 Issue State Tracking

The enhanced dashboard provides comprehensive issue state tracking across all integrations:

### Issue States

- **`no_response`**: Issue has not been responded to
- **`bot_responded`**: Bot has responded but no human interaction
- **`human_responded`**: Human has responded to the issue
- **`automated`**: Issue is being handled by automation
- **`in_progress`**: Issue has active flows or PRs
- **`pr_open`**: Pull request is open for the issue
- **`pr_merged`**: Pull request has been merged
- **`flow_failed`**: Associated flow has failed
- **`completed`**: Issue is marked as done

### State Tracking Features

- **Real-time Updates**: Live state changes via WebSocket
- **Multi-platform Sync**: Synchronization between Linear and GitHub
- **Automation Detection**: Identify automated vs manual handling
- **Progress Tracking**: Monitor issue resolution progress
- **Escalation Management**: Automatic escalation for stalled issues

## 🔄 Flow Types & Templates

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

#### 4. **Issue Resolution**
- **Purpose**: Automated Linear issue resolution
- **Duration**: ~90 minutes
- **Parameters**:
  - `issue_id`: Linear issue ID
  - `resolution_strategy`: Resolution approach
  - `create_pr`: Whether to create a PR
  - `notify_assignee`: Notify issue assignee

## 🚀 Advanced Usage

### Custom Flow Templates

Create custom flow templates programmatically:

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
await flow_manager.template_manager.create_template(custom_template)
```

### WebSocket Integration

Connect to real-time updates:

```javascript
// Flow updates
const flowWs = new WebSocket('ws://localhost:8000/ws/flows/flow-id');
flowWs.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Flow update:', data);
};

// Project updates
const projectWs = new WebSocket('ws://localhost:8000/ws/projects/project-id');
projectWs.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Project update:', data);
};
```

### API Integration

Use the REST API programmatically:

```python
import requests

# Create a new flow
response = requests.post('http://localhost:8000/api/flows/create', json={
    'name': 'Feature Development',
    'project': 'my-project',
    'type': 'feature_development',
    'requirements': 'Implement user authentication',
    'priority': 'high',
    'notifications': True
})

flow_data = response.json()
print(f"Created flow: {flow_data['flow_id']}")

# Start the flow
start_response = requests.post(f'http://localhost:8000/api/flows/{flow_data["flow_id"]}/start')
print(f"Flow started: {start_response.json()}")
```

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
- Verify template parameters are correct
- Check agent availability and configuration
- Review system logs for detailed error messages

#### 3. **Integration Issues**
- Verify API tokens and credentials are valid
- Check network connectivity to external services
- Review integration logs in the dashboard

#### 4. **WebSocket Connection Issues**
- Ensure firewall allows WebSocket connections
- Check browser console for connection errors
- Verify WebSocket endpoint URLs are correct

### Debug Mode

Enable debug mode for detailed logging:

```bash
python launch_dashboard.py --debug
```

### Log Files

Check log files for detailed information:
- Dashboard logs: Console output
- Flow execution logs: Available via API
- System monitoring logs: Real-time via WebSocket

## 📈 Monitoring & Metrics

### Health Monitoring

The dashboard continuously monitors:

- **System Health**: CPU, memory, disk usage
- **Flow Health**: Execution status, error rates, completion times
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
- Security incidents

## 🎉 Success Metrics

### Operational Metrics
- Flow completion rate: >95%
- Average flow execution time: <30 minutes
- Error recovery success rate: >90%
- System uptime: >99.9%

### User Experience Metrics
- Dashboard response time: <2 seconds
- User task completion rate: >90%
- User satisfaction score: >4.5/5
- Feature adoption rate: >80%

### Business Metrics
- Developer productivity increase: >25%
- Bug resolution time reduction: >40%
- Deployment frequency increase: >50%
- Mean time to recovery reduction: >60%

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

## 🎊 Ready to Go!

Your Contexten Enhanced Dashboard is now ready for comprehensive autonomous CI/CD flow management!

**Next Steps:**
1. Pin your first project
2. Create your first flow
3. Monitor system health
4. Explore advanced features

**Dashboard URL:** http://localhost:8000

Enjoy building with autonomous intelligence! 🤖✨

