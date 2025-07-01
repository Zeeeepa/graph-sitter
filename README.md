# AI-Powered CI/CD Automation Platform

A comprehensive platform that integrates Codegen SDK, GitHub, Graph-sitter, and Modal for automated development workflows with intelligent code analysis and deployment validation.

## Features

- 🔐 **GitHub Integration**: OAuth authentication and repository management
- 🤖 **Codegen SDK Integration**: AI agent execution with real-time status monitoring
- 📊 **Real-time Dashboard**: Live agent status updates and workflow monitoring
- 🔍 **Code Analysis**: Graph-sitter integration for dead code detection and quality checks
- 🚀 **Automated Deployments**: Modal integration for infrastructure provisioning
- 🔄 **Workflow Orchestration**: Intelligent CI/CD cycles with validation loops
- ✨ **Prompt Enhancement**: Advanced prompt engineering for better agent performance

## Architecture

```
Frontend (React)
├── Project Dashboard
├── Agent Status Monitor
├── Workflow Visualizer
└── Real-time Updates (WebSocket)

Backend (FastAPI)
├── API Endpoints
├── WebSocket Handlers
├── Service Integration Layer
│   ├── GitHub Service
│   ├── Codegen Service
│   ├── Graph-sitter Analyzer
│   └── Modal Deployer
└── Workflow Orchestration Engine

Database (PostgreSQL)
├── Projects
├── Workflows
├── Agent Tasks
└── Analysis Results
```

## Quick Start

1. **Setup Environment**
   ```bash
   docker-compose up -d
   ```

2. **Configure Credentials**
   - Add GitHub token
   - Configure Codegen API credentials
   - Setup Modal authentication

3. **Access Dashboard**
   - Navigate to `http://localhost:3000`
   - Authenticate with GitHub
   - Select and pin projects

## Workflow

1. **Project Setup**: Add GitHub token → Select repositories → Pin to dashboard
2. **Requirements**: Input project requirements and goals
3. **Plan Generation**: AI creates execution plan using Codegen SDK
4. **Automated Execution**: Workflow engine orchestrates:
   - Code analysis with Graph-sitter
   - PR creation and validation
   - Deployment with Modal
   - Continuous validation cycles
5. **Monitoring**: Real-time dashboard shows agent status and progress

## Development

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend
cd frontend
npm install
npm start
```

## License

MIT License

