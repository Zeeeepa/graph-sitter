# 🚀 Prefect Dashboard Integration for Contexten

## 📋 Overview

This document describes the comprehensive Prefect dashboard integration that makes full Prefect orchestration functionality available through the contexten dashboard. The integration provides a complete web interface for managing autonomous CI/CD workflows, monitoring system health, and controlling all aspects of the Prefect orchestration system.

## ✨ Key Features

### 🎛️ **Complete Dashboard Suite**
- **Main Dashboard** - Overview and quick actions
- **Workflows Management** - Trigger, monitor, and manage workflows
- **System Monitoring** - Real-time health and performance metrics
- **Configuration** - System settings and integration management

### 🤖 **20 Autonomous Workflow Types**
- **Analysis**: component_analysis, failure_analysis, performance_monitoring, code_quality_check
- **Maintenance**: dependency_management, security_audit, test_optimization, dead_code_cleanup
- **Integration**: linear_sync, github_automation, slack_notifications
- **System**: health_check, backup_operations, resource_optimization
- **Advanced**: autonomous_refactoring, intelligent_deployment, predictive_maintenance
- **Recovery**: error_healing, system_recovery, data_recovery

### 📊 **Real-time Monitoring**
- Live system metrics with auto-refresh
- Component health scoring
- Performance tracking and alerting
- Resource usage monitoring (CPU, memory, disk)
- Live log streaming

### 🔧 **Advanced Management**
- Bulk workflow operations
- Configurable alert thresholds
- Integration testing and validation
- Environment variable management
- Advanced performance settings

## 🏗️ Architecture

```
Contexten Dashboard App
├── Main Dashboard (/)
│   ├── System overview
│   ├── Quick actions
│   └── Recent activity
└── Prefect Dashboard (/prefect/)
    ├── Dashboard Home (/prefect/)
    ├── Workflows (/prefect/workflows)
    ├── Monitoring (/prefect/monitoring)
    └── Configuration (/prefect/configuration)
```

### Core Components

1. **PrefectDashboardManager** - Main dashboard controller
2. **OrchestrationConfig** - Configuration management
3. **FastAPI Router** - API endpoints and web routes
4. **HTML Templates** - Modern responsive UI
5. **JavaScript Frontend** - Interactive dashboard features

## 🚀 Installation & Setup

### 1. Dependencies

The Prefect dashboard integration requires the following dependencies:

```bash
# Core orchestration dependencies
pip install prefect>=3.0.0
pip install prefect-github>=0.2.0
pip install prefect-slack>=0.1.0

# System monitoring
pip install psutil>=5.9.0
pip install aiohttp>=3.8.0

# Configuration management
pip install pydantic>=2.0.0
pip install pydantic-settings>=2.0.0
pip install PyYAML>=6.0
```

### 2. Environment Variables

Configure the required environment variables:

```bash
# Required for Codegen SDK integration
export CODEGEN_ORG_ID="your-organization-id"
export CODEGEN_TOKEN="your-api-token"

# Optional integrations
export GITHUB_TOKEN="your-github-token"
export LINEAR_API_KEY="your-linear-api-key"
export SLACK_WEBHOOK_URL="your-slack-webhook"

# Prefect configuration (optional)
export PREFECT_API_URL="http://localhost:4200/api"
export PREFECT_WORKSPACE="your-workspace"

# Dashboard configuration
export DASHBOARD_HOST="0.0.0.0"
export DASHBOARD_PORT="8080"
export DASHBOARD_DEBUG="false"
```

### 3. Start the Dashboard

```bash
# Start the contexten dashboard with Prefect integration
python -m uvicorn src.contexten.dashboard.app:app --host 0.0.0.0 --port 8080 --reload
```

## 🎯 Usage Guide

### Main Dashboard (/)

The main dashboard provides:
- **System Overview** - Health score, active workflows, success rate
- **Quick Actions** - Trigger workflows, check health, analyze components
- **Integration Status** - GitHub, Linear, Slack connectivity
- **Recent Activity** - Timeline of recent workflow executions

### Prefect Dashboard (/prefect/)

#### Dashboard Home (/prefect/)
- System health overview with real-time metrics
- Quick workflow triggers for common operations
- Workflow categories with descriptions
- Recent workflow execution history

#### Workflows Management (/prefect/workflows)
- **Workflow Types Grid** - All 20 workflow types with descriptions
- **Active Workflows Table** - Real-time status of running workflows
- **Filtering & Search** - Filter by category, status, or search terms
- **Bulk Operations** - Cancel multiple workflows, export data
- **Workflow Details** - View logs, parameters, and execution details

#### System Monitoring (/prefect/monitoring)
- **Real-time Metrics** - CPU, memory, disk usage with live charts
- **Component Health** - Individual integration health scores
- **Alert Configuration** - Configurable thresholds for notifications
- **Live Logs** - Real-time system log streaming
- **Performance Charts** - Historical performance data

#### Configuration (/prefect/configuration)
- **System Settings** - Concurrent workflows, retry attempts, intervals
- **Integration Status** - Test and validate all integrations
- **Alert Thresholds** - Configure monitoring alerts
- **Workflow Defaults** - Default priority, timeout, caching settings
- **Environment Variables** - Secure display of configuration
- **Advanced Settings** - Logging, performance, and feature toggles

## 🔄 Workflow Management

### Triggering Workflows

#### Via Web Interface
1. Navigate to `/prefect/workflows`
2. Click "Run" on any workflow type
3. Configure parameters and priority
4. Submit to start execution

#### Via API
```bash
curl -X POST http://localhost:8080/prefect/api/workflows/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_type": "component_analysis",
    "priority": 5,
    "parameters": {
      "component": "contexten/agents",
      "linear_issue_id": "ZAM-1084"
    }
  }'
```

#### Via Quick Actions
```python
# Trigger component analysis from main dashboard
POST /prefect/api/components/analyze
{
  "component": "contexten/agents",
  "linear_issue_id": "ZAM-1084"
}
```

### Monitoring Workflows

#### Real-time Status
- View active workflows in the workflows table
- Monitor progress with visual indicators
- Check execution logs and parameters

#### Historical Data
```bash
# Get workflow history
curl http://localhost:8080/prefect/api/workflows/history?limit=50&workflow_type=component_analysis
```

### Bulk Operations

#### Cancel Multiple Workflows
```bash
curl -X POST http://localhost:8080/prefect/api/workflows/bulk/cancel \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_ids": ["workflow-1", "workflow-2", "workflow-3"]
  }'
```

#### Trigger Multiple Workflows
```bash
curl -X POST http://localhost:8080/prefect/api/workflows/bulk/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "workflows": [
      {
        "workflow_type": "health_check",
        "priority": 5,
        "parameters": {}
      },
      {
        "workflow_type": "security_audit",
        "priority": 8,
        "parameters": {}
      }
    ]
  }'
```

## 📊 API Reference

### System Status
- `GET /prefect/api/status` - Get system overview
- `GET /prefect/api/health` - Get detailed health status
- `GET /prefect/api/metrics` - Get system metrics

### Workflow Management
- `GET /prefect/api/workflows` - List active workflows
- `POST /prefect/api/workflows/trigger` - Trigger workflow
- `GET /prefect/api/workflows/{id}/status` - Get workflow status
- `POST /prefect/api/workflows/{id}/cancel` - Cancel workflow
- `GET /prefect/api/workflows/history` - Get workflow history

### Component Analysis
- `GET /prefect/api/components` - Get available components
- `POST /prefect/api/components/analyze` - Trigger component analysis

### Configuration
- `GET /prefect/api/configuration` - Get configuration
- `POST /prefect/api/configuration` - Update configuration

### Real-time Data
- `GET /prefect/api/live/metrics` - Get live metrics
- `GET /prefect/api/live/logs` - Get live logs

### Bulk Operations
- `POST /prefect/api/workflows/bulk/trigger` - Trigger multiple workflows
- `POST /prefect/api/workflows/bulk/cancel` - Cancel multiple workflows

## 🎨 User Interface Features

### Modern Design
- **Responsive Layout** - Works on desktop, tablet, and mobile
- **Tailwind CSS** - Modern, clean design system
- **Font Awesome Icons** - Comprehensive icon set
- **Real-time Updates** - Auto-refreshing data and charts

### Interactive Elements
- **Live Charts** - Real-time performance metrics with Chart.js
- **Progress Indicators** - Visual workflow progress tracking
- **Modal Dialogs** - Workflow configuration and bulk operations
- **Toast Notifications** - Success/error feedback
- **Search & Filtering** - Find workflows and data quickly

### Accessibility
- **Keyboard Navigation** - Full keyboard support
- **Screen Reader Support** - ARIA labels and semantic HTML
- **High Contrast** - Clear visual hierarchy
- **Responsive Text** - Scalable font sizes

## 🔧 Configuration Options

### System Configuration
```yaml
# orchestration_config.yaml
max_concurrent_workflows: 5
health_check_interval_minutes: 15
workflow_retry_attempts: 3
auto_recovery_enabled: true
monitoring_enabled: true

alert_thresholds:
  cpu_usage_percent: 80
  memory_usage_percent: 80
  disk_usage_percent: 90
  error_rate_percent: 10
```

### Dashboard Configuration
```bash
# Dashboard settings
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=8080
DASHBOARD_DEBUG=false
DASHBOARD_SECRET_KEY=your-secret-key

# Auto-refresh intervals
DASHBOARD_REFRESH_INTERVAL=30  # seconds
DASHBOARD_LOG_REFRESH_INTERVAL=5  # seconds
```

### Workflow Defaults
- **Default Priority**: Normal (5)
- **Default Timeout**: 30 minutes
- **Workflow Caching**: Enabled
- **Structured Logging**: Enabled

## 🔍 Monitoring & Alerting

### System Health Metrics
- **Overall Health Score** - Composite health percentage
- **Component Health** - Individual integration status
- **Resource Usage** - CPU, memory, disk utilization
- **API Connectivity** - Response times and availability

### Alert Thresholds
Configurable alerts for:
- High CPU usage (default: 80%)
- High memory usage (default: 80%)
- High disk usage (default: 90%)
- High error rate (default: 10%)
- API connectivity issues
- Workflow failure patterns

### Real-time Monitoring
- **Live Metrics Dashboard** - Auto-updating charts and gauges
- **Component Status Grid** - Visual health indicators
- **Alert Timeline** - Recent alerts and notifications
- **Log Streaming** - Real-time system logs

## 🛡️ Security Features

### Environment Variable Security
- Sensitive values are masked in the UI
- Secure storage and transmission
- No plaintext exposure in logs

### Access Control
- Session-based authentication
- Role-based permissions (future enhancement)
- API rate limiting
- Secure communication channels

### Audit Logging
- All workflow operations logged
- Configuration changes tracked
- User actions recorded
- System events monitored

## 🚀 Advanced Features

### Predictive Maintenance
- Pattern recognition for failure prediction
- Proactive issue identification
- Automated preventive actions
- Performance trend analysis

### Autonomous Error Healing
- Automatic failure detection
- Root cause analysis
- Recovery strategy selection
- Self-healing capabilities

### Intelligent Deployment
- Smart deployment strategies
- Automated rollback capabilities
- Performance validation
- Risk assessment

## 🔄 Integration Points

### Codegen SDK Integration
```python
from contexten.orchestration import PrefectOrchestrator, OrchestrationConfig

# Initialize with Codegen SDK
config = OrchestrationConfig(
    codegen_org_id="your-org-id",
    codegen_token="your-token"
)

orchestrator = PrefectOrchestrator(config)
await orchestrator.initialize()

# Trigger AI-powered analysis
run_id = await orchestrator.trigger_component_analysis(
    component="contexten/agents",
    linear_issue_id="ZAM-1084"
)
```

### Linear Integration
- Automatic issue creation for component analysis
- Sub-issue generation for granular tasks
- Status synchronization based on workflow progress
- Result documentation with findings and recommendations

### GitHub Integration
- PR lifecycle automation
- Code review automation
- Branch management
- Deployment validation

### Slack Integration
- Real-time workflow notifications
- System health alerts
- Error condition reporting
- Manual intervention requests

## 📈 Performance Optimization

### Concurrent Execution
- Configurable parallel workflow limit (default: 5)
- Resource-aware scheduling
- Load balancing across workers
- Queue management

### Caching Strategy
- Workflow result caching
- Configuration caching
- API response caching
- Static asset optimization

### Database Optimization
- Connection pooling
- Query optimization
- Index management
- Data retention policies

## 🧪 Testing & Validation

### Health Check Endpoints
```bash
# Test system health
curl http://localhost:8080/prefect/api/health

# Test specific integration
curl http://localhost:8080/prefect/api/health?component=codegen

# Validate configuration
curl http://localhost:8080/prefect/api/configuration
```

### Workflow Testing
```bash
# Test workflow trigger
curl -X POST http://localhost:8080/prefect/api/workflows/trigger \
  -H "Content-Type: application/json" \
  -d '{"workflow_type": "health_check", "parameters": {}}'

# Monitor execution
curl http://localhost:8080/prefect/api/workflows/{run_id}/status
```

### Integration Testing
- Component connectivity tests
- API endpoint validation
- Workflow execution tests
- Error handling verification

## 🔧 Troubleshooting

### Common Issues

#### Dashboard Not Loading
```bash
# Check if the service is running
curl http://localhost:8080/prefect/api/health

# Check logs
tail -f orchestrator.log

# Verify environment variables
echo $CODEGEN_ORG_ID
echo $CODEGEN_TOKEN
```

#### Workflow Failures
```bash
# Check workflow status
curl http://localhost:8080/prefect/api/workflows/{run_id}/status

# View workflow logs
curl http://localhost:8080/prefect/api/workflows/{run_id}/logs

# Check system health
curl http://localhost:8080/prefect/api/health
```

#### Integration Issues
```bash
# Test Codegen SDK connection
python -c "from codegen import Agent; Agent(org_id='$CODEGEN_ORG_ID', token='$CODEGEN_TOKEN')"

# Test Linear API
curl -H "Authorization: Bearer $LINEAR_API_KEY" https://api.linear.app/graphql

# Test GitHub API
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
```

### Debug Mode
```bash
# Enable debug mode
export DASHBOARD_DEBUG=true

# Start with verbose logging
export LOG_LEVEL=DEBUG
python -m uvicorn src.contexten.dashboard.app:app --host 0.0.0.0 --port 8080 --reload --log-level debug
```

## 🚀 Future Enhancements

### Planned Features
- **Multi-Repository Support** - Cross-project orchestration
- **Advanced Analytics** - Predictive maintenance and optimization
- **Custom Workflow Builder** - Visual workflow designer
- **Enhanced AI Integration** - More sophisticated analysis capabilities
- **Real-time Collaboration** - Multi-user workflow management

### Extensibility
- Plugin architecture for custom workflows
- API for external integrations
- Webhook support for real-time events
- Custom notification channels

## 📄 License

This Prefect dashboard integration follows the same license as the parent graph-sitter project.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add comprehensive tests
5. Update documentation
6. Submit a pull request

## 📞 Support

For issues and questions:
- Create GitHub issues for bugs
- Use Linear for feature requests
- Join Slack for discussions
- Check documentation for guidance

---

**🎉 The Prefect Dashboard Integration transforms the contexten dashboard into a comprehensive autonomous CI/CD management platform, providing full visibility and control over all orchestration operations through an intuitive web interface.**

