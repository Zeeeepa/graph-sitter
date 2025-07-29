# 🚀 Interactive Codebase Visualization Dashboard

A comprehensive, production-ready interactive codebase exploration and visualization system with full CI/CD testing capabilities.

## 🌟 Features

### 🎨 Interactive Visualization
- **File Tree Explorer** - Virtualized, searchable, expandable file tree
- **Monaco Code Editor** - Full IDE features with syntax highlighting
- **Code Graph Visualization** - Interactive network graphs with multiple layouts
- **Real-time Error Detection** - Live error highlighting and indicators
- **Symbol Intelligence** - Go-to-definition, find references, hover information

### 🧪 Comprehensive Testing
- **35 Automated Tests** across 5 test suites
- **Real-time Test Execution** with progress tracking
- **Manual Testing Instructions** with interactive guidance
- **Performance Benchmarks** for large codebases
- **CI/CD Integration Testing** with web-eval-agent

### 🔧 Production Ready
- **Docker Support** for easy deployment
- **WebSocket Integration** for real-time updates
- **GitHub API Integration** with webhook support
- **Codegen Agent Integration** for AI-powered analysis
- **Cloudflare Worker Support** for scalable infrastructure

## 🚀 Quick Start

### Prerequisites

- **Node.js** (v18 or higher)
- **Python** (3.9 or higher)
- **Docker** (for database services)
- **Git** (for repository management)

### Environment Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd web_dashboard
   ```

2. **Configure environment variables:**
   ```bash
   # Copy the provided .env file or create your own
   cp .env.example .env
   
   # Edit .env with your API keys and configuration
   nano .env
   ```

3. **Launch the complete system:**
   ```bash
   ./launch.sh
   ```

4. **Access the application:**
   - **Frontend Dashboard:** http://localhost:5173
   - **Backend API:** http://localhost:8000
   - **API Documentation:** http://localhost:8000/docs

5. **Stop all services:**
   ```bash
   ./stop.sh
   ```

## 🔑 Environment Variables

```bash
# Codegen Agent API
CODEGEN_ORG_ID=your-org-id
CODEGEN_API_TOKEN=sk-your-codegen-api-token

# GitHub Integration
GITHUB_TOKEN=github_pat_your-github-token

# AI/LLM Services
GEMINI_API_KEY=your-gemini-api-key

# Cloudflare Infrastructure
CLOUDFLARE_API_KEY=your-cloudflare-api-key
CLOUDFLARE_ACCOUNT_ID=your-cloudflare-account-id
CLOUDFLARE_WORKER_URL=https://your-worker.your-domain.workers.dev
```

## 🧪 Testing Guide

### Automated Testing

1. **Launch the Test Dashboard:**
   ```bash
   ./launch.sh
   ```

2. **Open the Test Interface:**
   - Navigate to http://localhost:5173
   - Click "Run All Tests" button
   - Watch real-time progress and results

3. **Test Suites:**
   - **File Tree Component** (7 tests)
   - **Code Editor Component** (7 tests)
   - **Code Graph Visualization** (7 tests)
   - **Dashboard Integration** (7 tests)
   - **Interactivity & Performance** (7 tests)

### Manual Testing

#### 📁 File Tree Testing
- Click folders to expand/collapse directories
- Select files to view content in editor
- Use search box to filter files
- Observe error indicators (red borders)
- Check file icons and size display

#### 💻 Code Editor Testing
- View syntax highlighting for TypeScript code
- Hover over symbols to see documentation
- Right-click for context menu (Go to Definition, Find References)
- Try search functionality (Ctrl/Cmd+F)
- Check error decorations (red underlines)

#### 🕸️ Graph Visualization Testing
- Toggle "Graph View" button in top bar
- Drag nodes around the canvas
- Use layout controls (hierarchical, force, circular, grid)
- Try search functionality to highlight nodes
- Toggle physics simulation on/off
- Use zoom and fit-to-screen controls

#### 🎛️ Dashboard Integration Testing
- Resize panels by dragging borders
- Toggle sidebar visibility
- Switch between activity bar tabs
- Check responsive design at different sizes
- Test theme switching

### Performance Testing
- Navigate large file trees smoothly
- Open multiple files quickly
- Interact with graph containing many nodes
- Check memory usage in browser dev tools

## 🏗️ Architecture

### Backend (FastAPI + Python)
```
backend/
├── main.py                 # FastAPI application entry point
├── api/                    # API route handlers
├── models/                 # Database models
├── services/               # Business logic services
├── integrations/           # External API integrations
├── websocket/              # WebSocket handlers
└── requirements.txt        # Python dependencies
```

### Frontend (React + TypeScript)
```
frontend/
├── src/
│   ├── components/         # React components
│   │   ├── Dashboard/      # Main dashboard interface
│   │   ├── FileTree/       # Interactive file tree
│   │   ├── CodeEditor/     # Monaco editor integration
│   │   ├── CodeGraph/      # Vis.js graph visualization
│   │   └── TestDashboard/  # Comprehensive test suite
│   ├── store/              # Zustand state management
│   ├── types/              # TypeScript type definitions
│   ├── utils/              # Utility functions
│   ├── hooks/              # Custom React hooks
│   └── demo/               # Mock data for testing
├── package.json            # Node.js dependencies
└── vite.config.ts          # Vite configuration
```

## 🔌 API Integration

### Codegen Agent Integration
```typescript
// Example: Create a new agent run
const response = await fetch('/api/v1/agent/runs', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${CODEGEN_API_TOKEN}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    project_id: 'project-123',
    task: 'Analyze codebase and suggest improvements',
    target_files: ['src/components/Dashboard.tsx']
  })
});
```

### GitHub Integration
```typescript
// Example: Create webhook for repository
const webhook = await fetch('/api/v1/github/webhooks', {
  method: 'POST',
  headers: {
    'Authorization': `token ${GITHUB_TOKEN}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    name: 'web',
    active: true,
    events: ['push', 'pull_request'],
    config: {
      url: CLOUDFLARE_WORKER_URL,
      content_type: 'json'
    }
  })
});
```

### Web-Eval-Agent Testing
```python
# Example: Run full CI/CD cycle test
import asyncio
from web_eval_agent import WebEvalAgent

async def test_cicd_cycle():
    agent = WebEvalAgent(
        codegen_token=CODEGEN_API_TOKEN,
        github_token=GITHUB_TOKEN,
        gemini_key=GEMINI_API_KEY
    )
    
    # Test project creation
    project = await agent.create_project({
        'name': 'Test Project',
        'github_repo': 'test-org/test-repo'
    })
    
    # Test code analysis
    analysis = await agent.analyze_codebase(project.id)
    
    # Test PR creation and validation
    pr = await agent.create_pr(project.id, {
        'title': 'Automated improvements',
        'changes': analysis.suggestions
    })
    
    return {
        'project': project,
        'analysis': analysis,
        'pr': pr
    }

# Run the test
result = asyncio.run(test_cicd_cycle())
```

## 🚀 Deployment

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up -d

# Or build individual services
docker build -t web-dashboard-backend ./backend
docker build -t web-dashboard-frontend ./frontend

docker run -d -p 8000:8000 web-dashboard-backend
docker run -d -p 3000:3000 web-dashboard-frontend
```

### Cloudflare Workers
```bash
# Deploy webhook gateway
wrangler deploy --name webhook-gateway

# Configure environment variables
wrangler secret put CODEGEN_API_TOKEN
wrangler secret put GITHUB_TOKEN
wrangler secret put GEMINI_API_KEY
```

## 📊 Monitoring & Observability

### Health Checks
- **Backend Health:** http://localhost:8000/health
- **Database Health:** http://localhost:8000/health/db
- **WebSocket Health:** ws://localhost:8000/ws/health

### Metrics
- **API Response Times:** Available in `/metrics` endpoint
- **WebSocket Connections:** Real-time connection count
- **Test Results:** Comprehensive test reporting
- **Error Tracking:** Centralized error logging

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch:** `git checkout -b feature/amazing-feature`
3. **Make your changes** and add tests
4. **Run the test suite:** `./launch.sh` and verify all tests pass
5. **Commit your changes:** `git commit -m 'Add amazing feature'`
6. **Push to the branch:** `git push origin feature/amazing-feature`
7. **Open a Pull Request**

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation:** Check the `/docs` endpoint when running
- **Issues:** Create an issue on GitHub
- **Discussions:** Use GitHub Discussions for questions
- **Email:** Contact the development team

## 🎯 Roadmap

- [ ] **Real-time Collaboration** - Multi-user editing and sharing
- [ ] **Advanced Analytics** - Code quality metrics and trends
- [ ] **Plugin System** - Extensible architecture for custom tools
- [ ] **Mobile Support** - Responsive design for mobile devices
- [ ] **Enterprise Features** - SSO, RBAC, and audit logging

---

**Built with ❤️ for developers who love beautiful, functional code exploration tools.**
