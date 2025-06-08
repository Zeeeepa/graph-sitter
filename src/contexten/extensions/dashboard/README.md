# Contexten Dashboard

A comprehensive single-user dashboard that integrates all 11 Contexten extensions into a unified, intelligent system for project management and development automation.

## 🚀 Features

### **Core Workflow**
1. **📌 Project Discovery** - Browse and pin GitHub repositories
2. **🔍 Code Analysis** - Graph-sitter deep analysis for errors, missing features, and quality metrics
3. **🤖 AI Planning** - Codegen SDK generates actionable plans from requirements
4. **⚡ Workflow Execution** - ControlFlow + Prefect orchestration with Linear task tracking
5. **🏗️ Sandboxed Deployment** - GrainChain isolated environments with automated testing
6. **📊 Real-time Monitoring** - Live progress tracking and notifications via Slack

### **Integrated Extensions**
- **Modal** - Serverless infrastructure and scaling
- **Contexten App** - Main orchestrator and plugin host
- **Prefect** - Workflow orchestration and state management
- **ControlFlow** - Agent orchestration and decision making
- **Codegen** - AI-powered planning and code generation
- **GitHub** - Repository management and automation
- **Linear** - Task management and issue tracking
- **Slack** - Intelligent notifications and updates
- **CircleCI** - CI/CD pipeline monitoring
- **GrainChain** - Sandboxed deployments and quality gates
- **Graph-sitter** - Comprehensive code analysis and insights

## 🛠️ Setup

### **1. Environment Variables**

Required:
```bash
export GITHUB_TOKEN="your_github_personal_access_token"
export CODEGEN_ORG_ID="your_codegen_organization_id"
export CODEGEN_TOKEN="your_codegen_api_token"
```

Optional:
```bash
export LINEAR_API_KEY="your_linear_api_key"
export SLACK_WEBHOOK="your_slack_webhook_url"
export CIRCLECI_TOKEN="your_circleci_api_token"
export DATABASE_URL="sqlite:///dashboard.db"  # Default: SQLite
```

### **2. Installation**

```bash
# Install dependencies
pip install fastapi uvicorn websockets jinja2

# Install Contexten extensions (if not already installed)
pip install -e src/contexten/extensions/github
pip install -e src/contexten/extensions/linear
pip install -e src/contexten/extensions/codegen
# ... etc for other extensions
```

### **3. Run Dashboard**

```bash
# From the dashboard directory
cd src/contexten/extensions/dashboard
python run_dashboard.py
```

Or using uvicorn directly:
```bash
uvicorn dashboard:create_dashboard().app --host 0.0.0.0 --port 8000
```

### **4. Access Dashboard**

- **Dashboard**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **WebSocket**: ws://localhost:8000/ws

## 📋 Usage

### **Basic Workflow**

1. **Setup Credentials**
   - Configure environment variables
   - Check setup status in Settings

2. **Pin a Project**
   - Click "Select Project To Pin"
   - Choose from your GitHub repositories
   - Project automatically gets analyzed

3. **Create Requirements**
   - Open pinned project
   - Go to Requirements tab
   - Enter your project requirements
   - Click "Generate Plan"

4. **Execute Workflow**
   - Review generated plan in Plan tab
   - Click "Start Flow" to begin execution
   - Monitor progress in real-time

5. **Monitor Results**
   - View code analysis in Analysis tab
   - Check deployment status in Deployment tab
   - Get notifications via Slack

### **API Endpoints**

#### Projects
- `GET /api/projects` - List all projects
- `GET /api/projects/pinned` - List pinned projects
- `POST /api/projects/pin` - Pin a repository
- `POST /api/projects/{id}/unpin` - Unpin a project

#### Planning & Execution
- `POST /api/projects/{id}/plan` - Generate plan from requirements
- `POST /api/projects/{id}/workflow/start` - Start workflow execution
- `POST /api/projects/{id}/workflow/stop` - Stop workflow execution

#### Analysis & Deployment
- `POST /api/projects/{id}/analyze` - Analyze project code
- `POST /api/projects/{id}/deploy` - Deploy to sandbox
- `GET /api/projects/{id}/quality` - Get quality summary

#### System
- `GET /api/status` - System status and statistics
- `GET /api/events` - Recent events
- `GET /api/settings` - Configuration and setup status

## 🏗️ Architecture

### **Component Structure**
```
Dashboard (Main Orchestrator)
├── SettingsManager (Configuration)
├── ProjectManager (GitHub Integration)
├── PlanningEngine (Codegen SDK)
├── WorkflowEngine (ControlFlow + Prefect)
├── QualityManager (Graph-sitter + GrainChain)
└── EventCoordinator (Slack + WebSocket)
```

### **Data Flow**
```
GitHub Repos → Project Discovery → Code Analysis (Graph-sitter)
     ↓
Requirements Input → AI Planning (Codegen) → Task Breakdown
     ↓
Workflow Execution (ControlFlow) → Linear Tasks → Progress Tracking
     ↓
Sandbox Deployment (GrainChain) → Testing → Quality Validation
     ↓
Real-time Updates (WebSocket) → Slack Notifications
```

### **Event System**
- **Event Bus** - Simple pub/sub for component communication
- **WebSocket** - Real-time dashboard updates
- **Slack Integration** - Automated notifications
- **Event History** - Debugging and monitoring

## 🔧 Configuration

### **Extension Settings**
Each extension can be configured in `dashboard_config.json`:

```json
{
  "extensions": {
    "github": {
      "enabled": true,
      "config": {
        "auto_sync": true,
        "webhook_enabled": false
      }
    },
    "codegen": {
      "enabled": true,
      "config": {
        "model": "claude-3-sonnet",
        "max_tokens": 4000
      }
    },
    "grainchain": {
      "enabled": true,
      "config": {
        "sandbox_type": "development",
        "auto_snapshot": true,
        "cleanup_after": 24
      }
    }
  }
}
```

### **Notification Settings**
Configure which events trigger Slack notifications:
- Workflow started/completed/failed
- Task completed/failed
- Analysis completed
- Deployment completed
- Project pinned/unpinned

## 🧪 Development

### **Adding New Features**
1. Extend relevant manager class
2. Add API endpoints in `dashboard.py`
3. Update frontend if needed
4. Add event handling for real-time updates

### **Testing**
```bash
# Test individual components
python -m pytest tests/

# Test API endpoints
curl http://localhost:8000/api/status

# Test WebSocket connection
wscat -c ws://localhost:8000/ws
```

### **Debugging**
- Check logs in console output
- Use `/api/events` to see recent activity
- Monitor WebSocket messages in browser dev tools
- Check `/api/status` for system health

## 🎯 Key Benefits

### **For Single Users**
- **No Authentication Complexity** - Direct access without login systems
- **Simple Configuration** - Environment variables and JSON config
- **Real-time Feedback** - Live progress and notifications
- **Complete Integration** - All 11 extensions working together

### **For Development Teams**
- **Automated Workflows** - From requirements to deployment
- **Quality Assurance** - Automated code analysis and testing
- **Project Visibility** - Centralized project management
- **Intelligent Planning** - AI-powered task breakdown

### **For DevOps**
- **Sandboxed Testing** - Safe deployment environments
- **CI/CD Integration** - CircleCI monitoring and automation
- **Infrastructure Scaling** - Modal serverless compute
- **Deployment Snapshots** - Easy rollback and recovery

## 🚨 Troubleshooting

### **Common Issues**

1. **"System not ready" warning**
   - Check environment variables are set
   - Verify API tokens are valid
   - Check network connectivity

2. **Repository discovery fails**
   - Verify GITHUB_TOKEN has repo access
   - Check GitHub API rate limits
   - Ensure token has correct permissions

3. **Plan generation fails**
   - Verify CODEGEN_ORG_ID and CODEGEN_TOKEN
   - Check Codegen API status
   - Try with simpler requirements

4. **Workflow execution issues**
   - Check Linear API key if using Linear integration
   - Verify project has a valid plan
   - Check extension configurations

5. **WebSocket connection issues**
   - Check firewall settings
   - Verify port 8000 is accessible
   - Try refreshing the browser

### **Getting Help**
- Check the console logs for detailed error messages
- Use `/api/status` to verify system health
- Test individual components using API endpoints
- Check extension-specific documentation

## 📚 Related Documentation

- [Graph-sitter Analysis](../graph_sitter/README.md)
- [GrainChain Deployment](../grainchain/README.md)
- [Codegen Integration](../codegen/README.md)
- [ControlFlow Orchestration](../controlflow/README.md)
- [Prefect Workflows](../prefect/README.md)

