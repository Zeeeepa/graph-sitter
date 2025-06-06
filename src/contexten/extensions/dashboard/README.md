# Contexten Dashboard Extension

A comprehensive dashboard UI system for managing projects, workflows, and automated development processes through GitHub, Linear, Slack, and Codegen SDK integrations.

## Features

### 🏗️ Project Management
- **Project Pinning**: Pin GitHub repositories to your dashboard for easy access
- **Real-time Status**: Live updates on project health, PRs, and issues
- **Multi-service Integration**: Seamless integration with GitHub, Linear, Slack, and Codegen

### 🤖 AI-Powered Workflow Orchestration
- **Requirements-based Planning**: Generate automated plans using Codegen SDK
- **Multi-layered Execution**: 
  - **Top Layer**: Prefect flows for high-level workflow management
  - **Middle Layer**: ControlFlow system for task orchestration
  - **Bottom Layer**: MCP-based agentic flows for granular execution

### ⚡ Real-time Updates
- **WebSocket Integration**: Live dashboard updates for all workflow activities
- **Event Broadcasting**: Real-time notifications for PR status, workflow progress, and quality gates
- **Multi-topic Subscriptions**: Subscribe to specific project or workflow events

### ✅ Quality Gates & Validation
- **Automated Code Analysis**: Integration with graph-sitter for code quality assessment
- **PR Validation**: Automated quality checks and issue detection
- **Validation Cycles**: Continuous validation until requirements are met

## Architecture

### Backend Components

```
src/contexten/extensions/dashboard/
├── __init__.py                 # Extension exports
├── dashboard.py               # Main dashboard extension class
├── models.py                  # Data models and schemas
├── database.py               # PostgreSQL integration
├── api.py                    # FastAPI routes and endpoints
├── websocket.py              # Real-time WebSocket manager
├── github_integration.py     # GitHub API integration
├── codegen_integration.py    # Codegen SDK integration
└── workflows/                # Multi-layered orchestration
    ├── __init__.py
    ├── orchestrator.py       # Main workflow coordinator
    ├── prefect_integration.py # Top-layer Prefect flows
    ├── controlflow_integration.py # Middle-layer task orchestration
    └── mcp_integration.py    # Bottom-layer agentic flows
```

### Frontend Components

```
frontend/
├── package.json              # React dependencies
├── src/
│   ├── App.tsx              # Main application component
│   ├── components/          # React components
│   │   ├── TopBar.tsx       # Navigation and actions
│   │   ├── Dashboard.tsx    # Main dashboard view
│   │   ├── ProjectCard.tsx  # Project display cards
│   │   ├── ProjectView.tsx  # Individual project view
│   │   ├── SettingsDialog.tsx # Settings configuration
│   │   └── ProjectSelectionDialog.tsx # GitHub repo selection
│   ├── store/               # State management
│   │   └── dashboardStore.ts # Zustand store
│   ├── services/            # API integration
│   │   └── api.ts          # Dashboard API client
│   ├── hooks/               # Custom React hooks
│   │   └── useWebSocket.ts  # WebSocket integration
│   └── types/               # TypeScript definitions
│       └── index.ts        # Type definitions
└── public/
    └── index.html          # HTML template
```

## Installation & Setup

### Prerequisites
- Python 3.8+
- Node.js 16+
- PostgreSQL 12+
- Redis (optional, for caching)

### Backend Setup

1. **Install Dependencies**:
```bash
# Core dependencies
pip install fastapi uvicorn sqlalchemy asyncpg

# Optional workflow dependencies
pip install prefect controlflow

# Optional MCP dependencies (if available)
pip install mcp-client
```

2. **Database Setup**:
```bash
# Create PostgreSQL database
createdb contexten_dashboard

# Set environment variable
export POSTGRESQL_URL="postgresql://user:password@localhost:5432/contexten_dashboard"
```

3. **Environment Configuration**:
```bash
# GitHub integration
export GITHUB_ACCESS_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"

# Linear integration
export LINEAR_ACCESS_TOKEN="lin_api_xxxxxxxxxxxxxxxxxxxx"

# Slack integration
export SLACK_BOT_TOKEN="xoxb-xxxxxxxxxxxxxxxxxxxx"

# Codegen SDK
export CODEGEN_ORG_ID="org_xxxxxxxxxxxxxxxxxxxx"
export CODEGEN_TOKEN="cg_xxxxxxxxxxxxxxxxxxxx"
```

### Frontend Setup

1. **Install Dependencies**:
```bash
cd src/contexten/extensions/dashboard/frontend
npm install
```

2. **Development Server**:
```bash
npm start
```

3. **Production Build**:
```bash
npm run build
```

## Usage

### Starting the Dashboard

1. **Initialize the Dashboard Extension**:
```python
from contexten.extensions.contexten_app import ContextenApp
from contexten.extensions.dashboard import setup_dashboard

# Create Contexten app
app = ContextenApp("my-app")

# Dashboard is automatically setup during app initialization
# Access via app.dashboard
```

2. **Run the Application**:
```bash
uvicorn contexten.extensions.contexten_app.contexten_app:app --reload
```

3. **Access the Dashboard**:
- Open browser to `http://localhost:8000/dashboard`
- The dashboard UI will be served with the React frontend

### Dashboard Features

#### Project Management
1. **Pin Projects**: Click "Select Project To Pin" to browse GitHub repositories
2. **Project Cards**: View project status, health metrics, and recent activity
3. **Flow Control**: Toggle workflow automation on/off per project

#### Workflow Creation
1. **Requirements Input**: Describe what you want to build
2. **AI Plan Generation**: Codegen SDK generates detailed implementation plan
3. **Multi-layer Execution**: Automatic orchestration through Prefect → ControlFlow → MCP
4. **Real-time Monitoring**: Live progress updates and quality gate results

#### Settings Configuration
1. **Environment Variables**: Configure API keys for all integrations
2. **Project Settings**: Enable/disable features per project
3. **Notification Preferences**: Customize alert settings

## API Endpoints

### Project Management
- `GET /dashboard/projects` - Get pinned projects
- `POST /dashboard/projects` - Create new project
- `POST /dashboard/projects/pin` - Pin project to dashboard
- `GET /dashboard/projects/github` - Get GitHub repositories

### Workflow Management
- `GET /dashboard/projects/{id}/plans` - Get workflow plans
- `POST /dashboard/projects/{id}/plans` - Create workflow plan
- `POST /dashboard/projects/{id}/plans/{plan_id}/start` - Start workflow

### Settings
- `PUT /dashboard/projects/{id}/settings` - Update project settings
- `PUT /dashboard/settings/environment` - Update environment variables

### Real-time Updates
- `WebSocket /dashboard/ws/{user_id}` - Real-time event stream

## WebSocket Events

### Subscription Topics
- `project_updates` - Project status changes
- `workflow_updates` - Workflow execution progress
- `github_events` - GitHub webhook events
- `linear_events` - Linear webhook events
- `quality_gate_updates` - Code quality results

### Event Types
- `project_update` - Project status changed
- `workflow_update` - Workflow progress update
- `github_event` - GitHub webhook received
- `pr_update` - Pull request status changed
- `quality_gate_update` - Quality gate result

## Development

### Adding New Features

1. **Backend**: Add new API endpoints in `api.py`
2. **Frontend**: Create React components in `components/`
3. **Database**: Update models in `models.py` and database schema
4. **WebSocket**: Add new event types in `websocket.py`

### Testing

```bash
# Backend tests
pytest tests/contexten/extensions/dashboard/

# Frontend tests
cd frontend && npm test
```

### Building for Production

```bash
# Build frontend
cd frontend && npm run build

# The built files will be served by the FastAPI backend
```

## Integration with Contexten

The dashboard integrates seamlessly with the existing Contexten architecture:

1. **Extension Pattern**: Follows Contexten's extension system
2. **Event Integration**: Hooks into GitHub, Linear, and Slack webhooks
3. **Shared Services**: Uses existing authentication and configuration
4. **Database Integration**: Extends Contexten's database schema

## Troubleshooting

### Common Issues

1. **WebSocket Connection Failed**:
   - Check if the backend server is running
   - Verify WebSocket endpoint is accessible
   - Check browser console for connection errors

2. **GitHub Integration Not Working**:
   - Verify `GITHUB_ACCESS_TOKEN` is set correctly
   - Check token permissions (repo, user, admin:org)
   - Ensure GitHub app is installed on repositories

3. **Database Connection Issues**:
   - Verify PostgreSQL is running
   - Check `POSTGRESQL_URL` environment variable
   - Ensure database exists and is accessible

4. **Frontend Build Errors**:
   - Clear node_modules and reinstall: `rm -rf node_modules && npm install`
   - Check Node.js version compatibility
   - Verify all dependencies are installed

### Logs and Debugging

- Backend logs: Check FastAPI server output
- Frontend logs: Open browser developer console
- Database logs: Check PostgreSQL logs
- WebSocket logs: Monitor network tab in browser dev tools

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This dashboard extension is part of the Contexten project and follows the same licensing terms.

