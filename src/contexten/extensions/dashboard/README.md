# 🚀 Contexten Dashboard System

A comprehensive AI-powered dashboard for managing development workflows with GitHub, Linear, and Codegen SDK integration.

## 🎯 Overview

The Contexten Dashboard provides a complete project management interface that enables:
- **Project Pinning**: Select and monitor GitHub projects
- **Requirements Management**: Input detailed project specifications
- **Automated Planning**: AI-generated execution plans via Codegen SDK
- **Workflow Orchestration**: Automated task execution and monitoring
- **Real-time Analytics**: Live progress tracking and metrics

## 🏗️ Architecture

```
Dashboard System
├── Frontend (React + Material-UI + TypeScript)
│   ├── Project Management Interface
│   ├── Real-time Monitoring
│   └── Settings Configuration
├── Backend (Python + FastAPI)
│   ├── API Endpoints
│   ├── Workflow Orchestration
│   └── Database Integration
└── Integrations
    ├── GitHub API
    ├── Linear API
    ├── Codegen SDK
    └── PostgreSQL
```

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm
- Python 3.9+
- PostgreSQL (optional, for persistence)

### 1. Frontend Setup
```bash
# Navigate to frontend directory
cd src/contexten/extensions/dashboard/frontend

# Install dependencies
npm install

# Start development server
npm start
```

The frontend will be available at `http://localhost:3000`

### 2. Backend Setup
```bash
# Navigate to dashboard directory
cd src/contexten/extensions/dashboard

# Install Python dependencies
pip install -r requirements.txt

# Start backend server
python launch_dashboard.py
```

The backend API will be available at `http://localhost:8000`

### 3. Environment Configuration

Create a `.env` file in the dashboard directory:
```env
# GitHub Integration
GITHUB_TOKEN=your_github_token

# Linear Integration
LINEAR_TOKEN=your_linear_token

# Codegen SDK
CODEGEN_ORG_ID=your_org_id
CODEGEN_TOKEN=your_codegen_token

# Database (optional)
POSTGRESQL_URL=postgresql://user:password@localhost:5432/dashboard

# Slack Integration (optional)
SLACK_TOKEN=your_slack_token
```

## 🎨 UI Components

### ProjectDialog
Multi-tab interface for project management:
- **Requirements Tab**: Input project specifications
- **Plan Tab**: View AI-generated execution plans
- **Progress Tab**: Monitor task completion

### Dashboard Features
- **TopBar**: Project selection and settings access
- **ProjectCard**: Visual project representation with status
- **RealTimeMetrics**: Live analytics and performance metrics
- **WorkflowMonitor**: Real-time workflow execution tracking

## 🔧 Development

### Frontend Development
```bash
cd frontend

# Development server with hot reload
npm start

# Type checking
npm run type-check

# Build for production
npm run build

# Run tests
npm test
```

### Backend Development
```bash
# Run with auto-reload
uvicorn api.enhanced_endpoints:app --reload --host 0.0.0.0 --port 8000

# Run tests
python -m pytest tests/

# Type checking
mypy src/
```

## 📊 Workflow Process

### 1. Project Selection
- Click "Select Project To Pin"
- Choose from available GitHub repositories
- Project appears on dashboard with status indicators

### 2. Requirements Input
- Open project dialog
- Navigate to Requirements tab
- Input detailed project specifications
- Click "Generate Plan"

### 3. Plan Generation
- System sends requirements to Codegen SDK
- AI generates comprehensive execution plan
- Plan appears in Plan tab with task breakdown

### 4. Flow Execution
- Click "Start Flow" to begin execution
- System creates Linear issues for each task
- Real-time monitoring shows progress
- Quality gates ensure code quality

### 5. Progress Monitoring
- Dashboard shows live project status
- Real-time metrics display performance
- Workflow monitor tracks task execution
- Notifications for important events

## 🔗 API Integration

### GitHub API
- Repository discovery and access
- Pull request management
- Branch operations
- Issue tracking

### Linear API
- Task creation and assignment
- Issue management
- Project organization
- Progress tracking

### Codegen SDK
- Automated plan generation
- Task execution
- Code analysis
- Quality validation

## 🛠️ Configuration

### Frontend Configuration
Located in `frontend/src/config/`:
- API endpoints
- Theme settings
- Feature flags
- Environment variables

### Backend Configuration
Located in `backend/config/`:
- Database connections
- API integrations
- Workflow settings
- Security configurations

## 🔒 Security

- Environment variables for sensitive data
- API token validation
- CORS configuration
- Input sanitization
- Rate limiting

## 📈 Monitoring

### Real-time Metrics
- Project completion rates
- Task execution times
- Error rates and debugging
- Performance analytics

### Logging
- Structured logging with levels
- Request/response tracking
- Error monitoring
- Performance profiling

## 🚀 Production Deployment

### Frontend Deployment
```bash
# Build production bundle
npm run build

# Serve with nginx or similar
# Configure reverse proxy to backend
```

### Backend Deployment
```bash
# Production server
gunicorn api.enhanced_endpoints:app -w 4 -k uvicorn.workers.UvicornWorker

# Or with Docker
docker build -t dashboard-backend .
docker run -p 8000:8000 dashboard-backend
```

### Environment Setup
- Configure production environment variables
- Set up PostgreSQL database
- Configure reverse proxy
- Set up SSL certificates

## 🧪 Testing

### Frontend Tests
```bash
cd frontend
npm test                    # Run all tests
npm run test:coverage      # Coverage report
npm run test:e2e          # End-to-end tests
```

### Backend Tests
```bash
python -m pytest tests/           # Run all tests
python -m pytest --cov=src       # Coverage report
python -m pytest tests/integration/  # Integration tests
```

## 🔄 Advanced Features

### Prefect Integration
- Advanced workflow orchestration
- Complex task dependencies
- Retry mechanisms
- Monitoring and alerting

### ControlFlow Integration
- Granular agentic flows
- Decision trees
- Conditional execution
- Dynamic task generation

### MCP Integration
- Model Context Protocol support
- Enhanced AI capabilities
- Context-aware processing
- Advanced reasoning

## 📚 Documentation

- [API Documentation](./docs/api.md)
- [Component Guide](./docs/components.md)
- [Deployment Guide](./docs/deployment.md)
- [Troubleshooting](./docs/troubleshooting.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- GitHub Issues: Report bugs and feature requests
- Documentation: Comprehensive guides and API docs
- Community: Join our Discord for discussions

---

**🎉 Ready to revolutionize your development workflow with AI-powered project management!**

