# Linear & GitHub Dashboard

A comprehensive dashboard for managing GitHub projects with advanced project management capabilities, requirements management, webhook integration, and AI-powered chat interface.

## 🚀 Features

### 📊 Project Management
- **Display 150+ GitHub projects** from your organization or personal repositories
- **Tab-based interface** with pin/unpin functionality for easy organization
- **Real-time PR/Branch status indicators** to track development progress
- **Quick diff view** between main branch and PR/branch on hover
- **Advanced filtering and sorting** by language, status, stars, and more

### 📋 Requirements Management
- **Requirements button** for each project to manage specifications
- **Dialog interface** for inputting and editing project requirements
- **Automatic saving** as `REQUIREMENTS.md` in project root
- **Version control integration** for requirements tracking and history
- **AI-powered requirements generation** based on code analysis

### 🔗 Webhook Integration
- **GitHub webhook support** for PR/Branch/Comment events
- **Linear webhook integration** for issue management
- **Real-time notifications** and updates across platforms
- **Event history tracking** with detailed delivery logs
- **Configurable webhook endpoints** with signature verification

### ⚙️ Settings and Configuration
- **Settings dialog** with API key management (GitHub, Linear, Anthropic)
- **Configuration management** for various integrations
- **User preferences** and customization options
- **Feature toggles** for enabling/disabling functionality

### 💬 AI Chat Interface
- **Conversational interface** powered by Anthropic Claude
- **Code analysis integration** for intelligent project insights
- **Requirements generation** using AI and codebase analysis
- **Codegen API integration** for advanced prompt processing
- **Context-aware responses** based on project information

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- GitHub account with API access
- Linear account (optional)
- Anthropic API key (optional, for AI features)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd graph-sitter/src/graph_sitter/dashboard
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   # Required for GitHub integration
   export GITHUB_ACCESS_TOKEN="your_github_token"
   
   # Optional for Linear integration
   export LINEAR_ACCESS_TOKEN="your_linear_token"
   
   # Optional for AI chat features
   export ANTHROPIC_API_KEY="your_anthropic_key"
   
   # Optional for advanced features
   export CODEGEN_API_KEY="your_codegen_key"
   ```

4. **Start the dashboard**
   ```bash
   python run_dashboard.py
   ```

5. **Access the dashboard**
   - Dashboard UI: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

## 🔧 Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_ACCESS_TOKEN` | Yes | GitHub personal access token |
| `LINEAR_ACCESS_TOKEN` | No | Linear API access token |
| `ANTHROPIC_API_KEY` | No | Anthropic API key for AI features |
| `CODEGEN_API_KEY` | No | Codegen API key for advanced features |
| `DASHBOARD_HOST` | No | Server host (default: 0.0.0.0) |
| `DASHBOARD_PORT` | No | Server port (default: 8000) |
| `DASHBOARD_DEBUG` | No | Enable debug mode (default: false) |
| `GITHUB_ORGANIZATION` | No | GitHub organization to filter repositories |
| `LINEAR_TEAM_ID` | No | Default Linear team ID |
| `WEBHOOK_SECRET` | No | Webhook secret for signature verification |

### Configuration via API

You can also configure the dashboard through the settings API:

```bash
# Get current configuration
curl http://localhost:8000/api/config

# Update settings
curl -X PUT http://localhost:8000/api/settings \
  -H "Content-Type: application/json" \
  -d '{"github_organization": "your-org"}'
```

## 📡 API Reference

### Projects API
- `GET /api/projects/` - List all projects with filtering and pagination
- `GET /api/projects/{project_id}` - Get specific project details
- `PATCH /api/projects/{project_id}` - Update project properties
- `GET /api/projects/{project_id}/branches` - Get project branches
- `GET /api/projects/{project_id}/pull-requests` - Get project PRs
- `GET /api/projects/{project_id}/diff` - Get diff between branches

### Requirements API
- `GET /api/requirements/{project_id}` - Get project requirements
- `POST /api/requirements/{project_id}` - Create project requirements
- `PUT /api/requirements/{project_id}` - Update project requirements
- `GET /api/requirements/{project_id}/history` - Get requirements history
- `POST /api/requirements/{project_id}/generate` - AI-generate requirements

### Webhooks API
- `POST /api/webhooks/{project_id}/configure` - Configure webhook
- `GET /api/webhooks/{project_id}/config` - Get webhook configuration
- `POST /api/webhooks/github` - GitHub webhook endpoint
- `POST /api/webhooks/linear` - Linear webhook endpoint
- `GET /api/webhooks/events` - List webhook events

### Chat API
- `POST /api/chat/sessions` - Create chat session
- `POST /api/chat/sessions/{session_id}/messages` - Send message
- `GET /api/chat/sessions/{session_id}/history` - Get chat history
- `POST /api/chat/analysis/{project_id}` - Get code analysis
- `POST /api/chat/quick-chat` - Quick chat without session

### Settings API
- `GET /api/settings/` - Get current settings
- `PUT /api/settings/` - Update settings
- `POST /api/settings/validate` - Validate API keys
- `GET /api/settings/api-keys/status` - Get API key status

## 🔌 Integration Points

### GitHub Integration
- **Repository access** via GitHub API
- **Webhook events** for real-time updates
- **Branch and PR monitoring** with status checks
- **Requirements file management** with version control

### Linear Integration
- **Issue management** and tracking
- **Webhook events** for issue updates
- **Team and project synchronization**
- **Comment and status updates**

### Anthropic Claude Integration
- **AI-powered chat interface** for project assistance
- **Code analysis** and recommendations
- **Requirements generation** based on codebase
- **Intelligent project insights**

### Codegen API Integration
- **Advanced prompt processing** for requirements
- **Code generation** and analysis capabilities
- **Integration with existing Codegen workflows**

## 🏗️ Architecture

```
src/graph_sitter/dashboard/
├── api/                    # FastAPI application and routes
│   ├── main.py            # Main application factory
│   └── routes/            # API route modules
├── models/                # Pydantic data models
├── services/              # Business logic and external integrations
├── utils/                 # Utilities (cache, logging, config)
├── frontend/              # Simple web interface
├── requirements.txt       # Python dependencies
├── run_dashboard.py       # Startup script
└── README.md             # This file
```

### Key Components

- **FastAPI Application**: Modern, fast web framework with automatic API documentation
- **Service Layer**: Modular services for GitHub, Linear, webhooks, requirements, and chat
- **Data Models**: Pydantic models for type safety and validation
- **Caching**: In-memory caching for improved performance
- **Configuration**: Environment-based configuration with validation
- **Logging**: Structured logging for debugging and monitoring

## 🚀 Deployment

### Development
```bash
python run_dashboard.py --debug --reload
```

### Production
```bash
# Using uvicorn directly
uvicorn graph_sitter.dashboard.api.main:app --host 0.0.0.0 --port 8000

# Using gunicorn (recommended for production)
gunicorn graph_sitter.dashboard.api.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Docker
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "run_dashboard.py"]
```

## 🔒 Security

- **API Key Management**: Secure storage and validation of API keys
- **Webhook Verification**: HMAC signature verification for webhooks
- **CORS Configuration**: Configurable CORS settings for web security
- **Input Validation**: Pydantic models for request/response validation
- **Rate Limiting**: Built-in rate limiting for API endpoints

## 🧪 Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/

# Run with coverage
pytest --cov=graph_sitter.dashboard tests/
```

## 📊 Monitoring

- **Health Check Endpoint**: `/health` for service monitoring
- **Metrics Endpoint**: `/api/stats/overview` for dashboard metrics
- **Logging**: Structured logging with configurable levels
- **Error Tracking**: Comprehensive error handling and reporting

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is part of the graph-sitter repository and follows the same license terms.

## 🆘 Support

- **Documentation**: Check the API docs at `/docs`
- **Health Check**: Monitor service status at `/health`
- **Configuration**: Review settings at `/api/config`
- **Issues**: Report bugs and feature requests via GitHub issues

## 🎯 Roadmap

- [ ] **Database Integration**: Persistent storage for projects and requirements
- [ ] **Advanced Analytics**: Project metrics and insights dashboard
- [ ] **Team Collaboration**: Multi-user support with permissions
- [ ] **Mobile Interface**: Responsive design improvements
- [ ] **Plugin System**: Extensible architecture for custom integrations
- [ ] **Notification System**: Email and Slack notifications
- [ ] **Advanced AI Features**: Code review assistance and automated suggestions

