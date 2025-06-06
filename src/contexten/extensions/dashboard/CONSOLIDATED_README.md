# Consolidated Strands Agent Dashboard

A comprehensive dashboard system that integrates Strands tools, ControlFlow, Prefect, and Codegen SDK for complete project lifecycle management.

## 🎯 Overview

This consolidated dashboard combines the best elements from multiple implementations to provide:

- **Project Management**: Pin GitHub repositories and manage development workflows
- **Multi-layer Orchestration**: Strands Workflow + ControlFlow + Prefect integration
- **AI-Powered Planning**: Codegen SDK integration for automated plan generation
- **Quality Gates**: Comprehensive validation and quality assessment
- **Real-time Monitoring**: WebSocket-based live updates and system health monitoring
- **Essential Integrations**: Preserved Linear, GitHub, and Slack functionality

## 🏗️ Architecture

### Backend Components

```
src/contexten/extensions/dashboard/
├── consolidated_models.py          # Unified data models
├── consolidated_api.py             # FastAPI endpoints with WebSocket
├── consolidated_dashboard.py       # Main dashboard class
├── services/
│   ├── strands_orchestrator.py    # Multi-layer workflow coordination
│   ├── project_service.py         # GitHub integration & project management
│   ├── codegen_service.py         # Codegen SDK integration
│   ├── quality_service.py         # Quality gates & validation
│   └── monitoring_service.py      # System health & monitoring
└── frontend/
    └── src/components/
        └── ConsolidatedDashboard.tsx  # React UI component
```

### Multi-layer Orchestration

1. **Top Layer**: Prefect flows for high-level workflow management
2. **Middle Layer**: ControlFlow system for task orchestration  
3. **Bottom Layer**: MCP-based agentic flows for granular execution
4. **Integration Layer**: Strands Workflow for unified management

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r consolidated_requirements.txt
```

### 2. Set Environment Variables

```bash
# Required for Codegen SDK
export CODEGEN_ORG_ID="your-org-id"
export CODEGEN_TOKEN="your-token"

# Optional integrations
export GITHUB_ACCESS_TOKEN="your-github-token"
export LINEAR_ACCESS_TOKEN="your-linear-token"
export SLACK_BOT_TOKEN="your-slack-token"

# Optional configuration
export DASHBOARD_HOST="0.0.0.0"
export DASHBOARD_PORT="8000"
export DASHBOARD_DEBUG="false"
```

### 3. Install Strands Tools (when available)

```bash
# Install from source
git clone https://github.com/Zeeeepa/sdk-python.git
cd sdk-python && pip install -e .
```

### 4. Start the Dashboard

```bash
# Option 1: Direct execution
python src/contexten/extensions/dashboard/consolidated_dashboard.py

# Option 2: Using uvicorn
uvicorn src.contexten.extensions.dashboard.consolidated_api:create_dashboard_app --host 0.0.0.0 --port 8000 --reload

# Option 3: Programmatic
from src.contexten.extensions.dashboard.consolidated_dashboard import create_consolidated_dashboard
dashboard = create_consolidated_dashboard()
dashboard.run()
```

### 5. Access the Dashboard

- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **WebSocket**: ws://localhost:8000/ws
- **Health Check**: http://localhost:8000/health

## 📋 Key Features

### Project Management
- **Pin GitHub Projects**: Select and pin repositories to your dashboard
- **Requirements Input**: Add project requirements and generate automated plans
- **Progress Tracking**: Real-time progress monitoring with visual indicators
- **Quality Metrics**: Code quality, test coverage, complexity, and security scores

### Workflow Orchestration
- **Multi-layer Execution**: Coordinated execution across Strands, ControlFlow, and Prefect
- **Automated Planning**: AI-generated development plans using Codegen SDK
- **Task Management**: Granular task tracking with dependencies and status updates
- **Flow Control**: Start, pause, resume, and stop workflows with real-time feedback

### Quality Gates
- **Automated Validation**: Comprehensive quality checks with configurable thresholds
- **Adaptive Thresholds**: Self-adjusting quality gates based on historical performance
- **PR Validation**: Automated pull request quality assessment
- **Custom Gates**: Create custom quality metrics and validation rules

### System Monitoring
- **Real-time Health**: Live system resource monitoring (CPU, memory, disk)
- **Service Status**: Health checks for all integrated services
- **Alert Management**: Configurable alerts with notification system
- **Performance Metrics**: Workflow execution statistics and performance tracking

### Essential Integrations (Preserved)
- **Linear**: Enhanced issue management with automated task creation
- **GitHub**: Intelligent PR management and repository analytics
- **Slack**: Rich messaging and notification workflows

## 🔧 API Endpoints

### Health & Monitoring
- `GET /health` - Basic health check
- `GET /api/health` - Comprehensive system health
- `GET /api/status` - Service status overview

### Projects
- `GET /api/projects` - List all projects
- `POST /api/projects` - Create new project
- `GET /api/projects/{id}` - Get project details
- `PUT /api/projects/{id}` - Update project
- `DELETE /api/projects/{id}` - Delete project
- `GET /api/github/repositories` - List GitHub repositories

### Workflows
- `POST /api/workflows/start` - Start multi-layer workflow
- `GET /api/workflows/{id}` - Get workflow status
- `POST /api/workflows/{id}/pause` - Pause workflow
- `POST /api/workflows/{id}/resume` - Resume workflow
- `POST /api/workflows/{id}/stop` - Stop workflow

### Codegen Integration
- `POST /api/codegen/plans` - Generate development plan
- `POST /api/codegen/tasks` - Create Codegen task
- `GET /api/codegen/tasks` - List all tasks
- `GET /api/codegen/tasks/{id}` - Get task status

### Quality Gates
- `GET /api/quality-gates/{project_id}` - Get quality gates
- `POST /api/quality-gates/{project_id}/validate` - Validate quality gates

### Settings
- `GET /api/settings` - Get user settings
- `PUT /api/settings` - Update user settings

### WebSocket
- `WS /ws` - Real-time updates and notifications

## 🎨 Frontend Usage

The React UI provides a comprehensive dashboard interface:

### Main Dashboard
- **System Health Panel**: Real-time system metrics and service status
- **Project Cards**: Visual project overview with progress and quality metrics
- **Action Buttons**: Quick access to plan generation and workflow execution

### Project Management
- **Add Project Dialog**: Simple GitHub repository URL input with requirements
- **Requirements Dialog**: Detailed requirements input for plan generation
- **Settings Dialog**: Configuration management for API keys and preferences

### Real-time Updates
- **WebSocket Integration**: Live updates for all workflow and system changes
- **Notification System**: Toast notifications for important events
- **Progress Tracking**: Real-time progress bars and status indicators

## 🔄 Workflow Example

1. **Pin Project**: Add a GitHub repository to your dashboard
2. **Add Requirements**: Describe what you want to build or improve
3. **Generate Plan**: Use Codegen SDK to create a detailed development plan
4. **Start Flow**: Execute the plan through multi-layer orchestration
5. **Monitor Progress**: Watch real-time updates as tasks are completed
6. **Quality Validation**: Automated quality gates ensure code quality
7. **Review Results**: Examine completed work and generated artifacts

## 🛠️ Development Mode

The system includes comprehensive mock implementations for development:

- **Mock Strands Tools**: Fallback implementations when actual tools aren't available
- **Mock Codegen Agent**: Simulated code generation for testing
- **Mock GitHub Client**: Repository simulation for offline development
- **Mock Orchestration**: Workflow simulation for UI development

## 📊 Quality Gates

Default quality gates include:

- **Test Coverage**: ≥80% (adaptive)
- **Code Complexity**: ≤7.0 (adaptive)
- **Security Score**: ≥85% (fixed)
- **Performance Score**: ≥75% (adaptive)
- **Dependency Health**: ≥90% (adaptive)
- **Recent Failures**: ≤3 (fixed)
- **Documentation Coverage**: ≥70% (adaptive)
- **Code Duplication**: ≤5% (adaptive)

## 🔐 Security

- **Token Management**: Secure storage and handling of API keys
- **Environment Variables**: Sensitive data stored in environment variables
- **CORS Configuration**: Proper cross-origin resource sharing setup
- **Input Validation**: Comprehensive input validation and sanitization

## 📈 Monitoring & Alerts

- **System Resources**: CPU, memory, and disk usage monitoring
- **Service Health**: Continuous health checks for all integrations
- **Workflow Status**: Real-time workflow and task status tracking
- **Error Tracking**: Comprehensive error logging and alerting
- **Performance Metrics**: Response time and throughput monitoring

## 🧪 Testing

```bash
# Run backend tests
pytest src/contexten/extensions/dashboard/

# Run with coverage
pytest --cov=src/contexten/extensions/dashboard/

# Run specific test categories
pytest -m "unit"
pytest -m "integration"
```

## 🚀 Deployment

### Docker Deployment
```bash
# Build image
docker build -t strands-dashboard .

# Run container
docker run -p 8000:8000 \
  -e CODEGEN_ORG_ID="your-org-id" \
  -e CODEGEN_TOKEN="your-token" \
  strands-dashboard
```

### Production Configuration
- Use proper environment variable management
- Configure reverse proxy (nginx/Apache)
- Set up SSL/TLS certificates
- Configure monitoring and logging
- Set up backup and disaster recovery

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This consolidated dashboard is part of the graph-sitter project and follows the same licensing terms.

## 🆘 Troubleshooting

### Common Issues

1. **WebSocket Connection Failed**:
   - Check if the backend server is running
   - Verify WebSocket endpoint is accessible
   - Check browser console for connection errors

2. **Codegen Integration Not Working**:
   - Verify `CODEGEN_ORG_ID` and `CODEGEN_TOKEN` are set correctly
   - Check Codegen SDK installation
   - Review API endpoint accessibility

3. **GitHub Integration Issues**:
   - Verify `GITHUB_ACCESS_TOKEN` is set correctly
   - Check token permissions (repo, user, admin:org)
   - Ensure GitHub app is installed on repositories

4. **Quality Gates Failing**:
   - Review quality gate thresholds
   - Check project analysis results
   - Verify graph-sitter integration

### Logs and Debugging

- **Backend logs**: Check FastAPI server output
- **Frontend logs**: Open browser developer console
- **WebSocket logs**: Monitor network tab in browser dev tools
- **System health**: Use `/api/health` endpoint for diagnostics

## 🔗 Related Projects

- [Strands Tools](https://github.com/Zeeeepa/sdk-python)
- [ControlFlow](https://github.com/PrefectHQ/ControlFlow)
- [Prefect](https://github.com/PrefectHQ/prefect)
- [Graph-sitter](https://github.com/Zeeeepa/graph-sitter)

---

**Ready to transform your development workflow with AI-powered automation!** 🚀

