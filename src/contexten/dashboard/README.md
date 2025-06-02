# Contexten Enhanced Dashboard

A comprehensive dashboard for managing flows, projects, requirements, Linear issues, GitHub repositories, Prefect workflows, and graph-sitter code analysis.

## 🚀 Features

### Core Dashboard Features
- **Project Management**: GitHub repository integration with project pinning and selection
- **Flow Management**: Create, monitor, and control autonomous flows
- **Real-time Monitoring**: Live updates of system status and activity
- **Analytics**: Comprehensive analytics and insights
- **AI Assistant**: Built-in chat interface for assistance

### Enhanced Integrations

#### 🔗 Linear Integration
- Issue synchronization and management
- Automatic issue creation from flows
- Project and milestone tracking
- Team collaboration features

#### 🐙 GitHub Integration
- Repository management and analysis
- Pull request comprehensive analysis
- Automated code review with AI
- Issue and PR creation from flows

#### ⚡ Prefect Integration
- Workflow orchestration and scheduling
- Flow deployment management
- Real-time flow monitoring
- Performance analytics

#### 🌳 Graph-Sitter Analysis
- Comprehensive code analysis
- Dead code detection and cleanup
- Code quality metrics
- Security vulnerability scanning
- Complexity analysis
- Dependency analysis

## 🏗️ Architecture

### Backend Components
- **FastAPI Application**: Main dashboard server
- **Enhanced Routes**: Comprehensive API endpoints for all integrations
- **Graph-Sitter Integration**: Code analysis engine
- **Orchestrator Integration**: Multi-service coordination
- **Advanced Analytics**: AI-powered insights and recommendations

### Frontend Components
- **Responsive Dashboard**: Bootstrap-based UI
- **Real-time Updates**: WebSocket connections for live data
- **Interactive Charts**: Chart.js visualizations
- **Chat Interface**: AI assistant integration

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Node.js (for frontend dependencies)
- Git
- Access to GitHub, Linear, and Prefect (optional)

### Installation

1. **Install the package**:
   ```bash
   pip install -e .
   ```

2. **Set up environment variables**:
   ```bash
   # Create .env file
   DASHBOARD_HOST=0.0.0.0
   DASHBOARD_PORT=8080
   DASHBOARD_DEBUG=false
   DASHBOARD_SECRET_KEY=your-secret-key
   
   # Integration tokens (optional)
   GITHUB_TOKEN=your-github-token
   LINEAR_API_KEY=your-linear-api-key
   PREFECT_API_KEY=your-prefect-api-key
   SLACK_WEBHOOK_URL=your-slack-webhook
   ```

3. **Launch the dashboard**:
   ```bash
   python -m contexten.dashboard
   ```

   Or using the main entry point:
   ```bash
   python -m contexten
   ```

### Alternative Launch Methods

#### Using the dashboard module directly:
```bash
cd src/contexten
python dashboard.py --host 0.0.0.0 --port 8080
```

#### Using uvicorn directly:
```bash
uvicorn contexten.dashboard.app:app --host 0.0.0.0 --port 8080 --reload
```

## 📊 Dashboard Sections

### 1. Overview
- System status and health indicators
- Key metrics and statistics
- Recent activity feed
- Quick action buttons

### 2. Projects
- GitHub repository management
- Project pinning and selection
- Project analysis and insights
- Integration status

### 3. Flows
- Active flow monitoring
- Flow creation and management
- Progress tracking
- Flow templates

### 4. Linear Integration
- Issue management and tracking
- Project synchronization
- Team collaboration
- Automated workflows

### 5. Analytics
- Performance metrics
- Code quality analysis
- AI-powered insights
- Trend analysis

### 6. Agents
- Active agent monitoring
- Agent configuration
- Performance tracking
- Resource usage

### 7. Workflows
- Automated workflow management
- Trigger configuration
- Multi-integration workflows
- Workflow templates

## 🔧 API Endpoints

### Core Endpoints
- `GET /` - Dashboard home page
- `GET /api/dashboard/overview` - Dashboard overview data
- `GET /api/projects` - List projects
- `POST /api/flows/create` - Create new flow
- `GET /api/flows/active` - Get active flows

### Enhanced Analysis Endpoints
- `POST /api/analysis/project` - Comprehensive project analysis
- `POST /api/analysis/dead-code` - Dead code detection
- `POST /api/analysis/code-quality` - Code quality analysis
- `GET /api/integrations/status` - Integration status

### V2 Enhanced Endpoints
- `GET /api/v2/projects/comprehensive` - Comprehensive project data
- `POST /api/v2/flows/autonomous` - Create autonomous flow
- `POST /api/v2/linear/sync/comprehensive` - Linear synchronization
- `POST /api/v2/github/prs/{pr_id}/comprehensive-analysis` - PR analysis
- `GET /api/v2/analytics/comprehensive` - Comprehensive analytics
- `GET /api/v2/monitoring/real-time` - Real-time monitoring

## 🔌 Integration Configuration

### GitHub Integration
```python
# Set environment variable
GITHUB_TOKEN=your_github_personal_access_token

# Or configure in dashboard settings
```

### Linear Integration
```python
# Set environment variable
LINEAR_API_KEY=your_linear_api_key

# Configure team and project IDs in dashboard
```

### Prefect Integration
```python
# Set environment variables
PREFECT_API_KEY=your_prefect_api_key
PREFECT_API_URL=https://api.prefect.cloud/api/accounts/[ACCOUNT-ID]/workspaces/[WORKSPACE-ID]
```

### Graph-Sitter Setup
The graph-sitter integration requires language parsers. Install them using:

```bash
# Install tree-sitter and language parsers
pip install tree-sitter
pip install tree-sitter-python
pip install tree-sitter-javascript
# ... other language parsers as needed
```

## 🤖 AI Features

### Comprehensive Analysis
- **Code Quality**: Automated code quality assessment
- **Security Scanning**: Vulnerability detection
- **Performance Analysis**: Performance bottleneck identification
- **Dead Code Detection**: Unused code identification

### AI Assistant
- Natural language queries about projects
- Code analysis explanations
- Workflow recommendations
- Integration guidance

### Automated Workflows
- **Feature Development**: End-to-end feature development flows
- **Bug Fix**: Automated bug detection and fixing
- **Code Review**: AI-powered code review
- **Deployment**: Automated deployment workflows

## 📈 Analytics and Monitoring

### Real-time Metrics
- System health and performance
- Active flows and their progress
- Integration status
- Resource utilization

### Historical Analytics
- Flow success rates
- Code quality trends
- Performance metrics
- Team productivity

### AI Insights
- Project health assessment
- Risk identification
- Optimization recommendations
- Predictive analytics

## 🛠️ Development

### Project Structure
```
src/contexten/dashboard/
├── app.py                      # Main FastAPI application
├── enhanced_routes.py          # Enhanced API endpoints
├── graph_sitter_integration.py # Code analysis engine
├── orchestrator_integration.py # Multi-service coordination
├── advanced_analytics.py       # Analytics engine
├── prefect_dashboard.py        # Prefect integration
├── templates/                  # HTML templates
│   ├── dashboard.html         # Main dashboard template
│   └── prefect_dashboard.html # Prefect dashboard template
├── static/                     # Static assets
│   ├── css/
│   │   └── dashboard.css      # Dashboard styles
│   └── js/
│       └── dashboard.js       # Dashboard JavaScript
└── README.md                   # This file
```

### Adding New Integrations

1. **Create integration module**:
   ```python
   # src/contexten/extensions/your_service/enhanced_client.py
   class YourServiceClient:
       async def connect(self):
           # Implementation
           pass
   ```

2. **Add to enhanced routes**:
   ```python
   # In enhanced_routes.py
   @enhanced_router.post("/your-service/action")
   async def your_service_action():
       # Implementation
       pass
   ```

3. **Update dashboard UI**:
   ```javascript
   // In dashboard.js
   async function yourServiceFunction() {
       // Implementation
   }
   ```

### Testing

Run the dashboard in development mode:
```bash
python -m contexten.dashboard --debug
```

Access the dashboard at: http://localhost:8080

## 🔒 Security

### Authentication
- OAuth integration with GitHub
- Session management
- Secure token storage

### API Security
- Rate limiting
- Input validation
- CORS configuration
- HTTPS enforcement (in production)

### Data Protection
- Encrypted sensitive data
- Secure environment variable handling
- Audit logging

## 📝 Configuration

### Environment Variables
```bash
# Dashboard Configuration
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=8080
DASHBOARD_DEBUG=false
DASHBOARD_SECRET_KEY=your-secret-key
DASHBOARD_BASE_URL=http://localhost:8080

# Integration Tokens
GITHUB_TOKEN=your-github-token
LINEAR_API_KEY=your-linear-api-key
PREFECT_API_KEY=your-prefect-api-key
SLACK_WEBHOOK_URL=your-slack-webhook

# Database (optional)
DATABASE_URL=postgresql://user:pass@localhost/dbname

# Redis (optional, for caching)
REDIS_URL=redis://localhost:6379
```

### Dashboard Settings
Configure additional settings through the dashboard UI:
- Integration preferences
- Notification settings
- Analysis parameters
- Workflow templates

## 🚨 Troubleshooting

### Common Issues

1. **Dashboard won't start**:
   - Check Python version (3.8+ required)
   - Verify all dependencies are installed
   - Check environment variables

2. **Integrations not working**:
   - Verify API tokens are correct
   - Check network connectivity
   - Review integration status in dashboard

3. **Graph-sitter analysis fails**:
   - Ensure language parsers are installed
   - Check project path permissions
   - Verify supported file types

4. **Performance issues**:
   - Check system resources
   - Review analysis cache settings
   - Consider reducing analysis scope

### Debug Mode
Enable debug mode for detailed logging:
```bash
DASHBOARD_DEBUG=true python -m contexten.dashboard
```

### Logs
Check logs for detailed error information:
```bash
tail -f logs/dashboard.log
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Development Setup
```bash
# Clone repository
git clone https://github.com/your-org/contexten.git
cd contexten

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run dashboard
python -m contexten.dashboard --debug
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Documentation**: [Link to docs]
- **Issues**: [GitHub Issues]
- **Discussions**: [GitHub Discussions]
- **Email**: support@contexten.ai

## 🗺️ Roadmap

### Upcoming Features
- [ ] Advanced AI code generation
- [ ] Multi-repository analysis
- [ ] Custom workflow builder
- [ ] Advanced security scanning
- [ ] Performance optimization suggestions
- [ ] Team collaboration features
- [ ] Mobile dashboard app
- [ ] API rate limiting and quotas
- [ ] Advanced caching mechanisms
- [ ] Real-time collaboration

### Integration Roadmap
- [ ] Jira integration
- [ ] Slack bot integration
- [ ] Jenkins/CI integration
- [ ] Docker/Kubernetes integration
- [ ] AWS/Cloud integration
- [ ] Database integration
- [ ] Monitoring tools integration

---

**Happy coding with Contexten Dashboard! 🚀**

