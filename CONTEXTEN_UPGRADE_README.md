# Contexten Integration Upgrade

This document describes the comprehensive upgrade of Linear and GitHub integrations in the Contexten framework, along with the new management dashboard.

## Overview

This upgrade implements:

1. **Enhanced Linear Integration** - Comprehensive GraphQL-based Linear integration with advanced features
2. **Enhanced GitHub Integration** - REST API-based GitHub integration with similar capabilities
3. **Management Dashboard** - Web-based interface for managing integrations and Codegen tasks
4. **OAuth Authentication** - Secure authentication for GitHub, Linear, and Slack
5. **Codegen SDK Integration** - Direct integration with Codegen API for task automation

## Architecture

### Enhanced Linear Integration

Located in `src/contexten/extensions/linear/`:

- **`enhanced_agent.py`** - Main agent with comprehensive Linear capabilities
- **`enhanced_client.py`** - GraphQL client with connection pooling, caching, and retry logic
- **`queries.py`** - Complete set of Linear GraphQL queries
- **`mutations.py`** - Complete set of Linear GraphQL mutations
- **`webhook/`** - Webhook processing with validation and event routing
- **`workflow/`** - Workflow automation engine
- **`assignment/`** - Intelligent assignment detection
- **`events/`** - Event management system

### Enhanced GitHub Integration

Located in `src/contexten/extensions/github/`:

- **`enhanced_agent.py`** - Main agent with comprehensive GitHub capabilities
- **`enhanced_client.py`** - REST API client with advanced features
- **`types.py`** - GitHub data type definitions
- **`webhook/`** - Webhook processing for GitHub events
- **`workflow/`** - Workflow automation for GitHub
- **`events/`** - Event management for GitHub

### Management Dashboard

Located in `src/contexten/dashboard/`:

- **`app.py`** - FastAPI-based web application
- **`templates/`** - Jinja2 templates for the web interface
- **`static/`** - CSS and JavaScript assets

## Features

### Linear Integration Features

- **GraphQL API Integration** - Full Linear API access with optimized queries
- **Real-time Webhooks** - Process Linear events in real-time
- **Workflow Automation** - Automated responses to Linear events
- **Assignment Detection** - Intelligent user assignment from text
- **Connection Pooling** - Efficient HTTP connection management
- **Response Caching** - Cached responses for improved performance
- **Retry Logic** - Automatic retries with exponential backoff
- **Rate Limiting** - Respect Linear API rate limits

### GitHub Integration Features

- **REST API Integration** - Complete GitHub API access
- **Repository Management** - Create, update, and manage repositories
- **Issue Management** - Full issue lifecycle management
- **Pull Request Management** - PR creation, updates, and reviews
- **Webhook Processing** - Handle GitHub webhook events
- **Branch Management** - Create and manage branches
- **File Operations** - Read and write repository files

### Dashboard Features

- **OAuth Authentication** - Secure login with GitHub, Linear, and Slack
- **Project Selection** - Browse and select GitHub repositories
- **Requirements Management** - Input and validate project requirements
- **Codegen Integration** - Start/stop Codegen tasks with custom prompts
- **Real-time Status** - Monitor integration and task status
- **Project Pinning** - Pin frequently used projects
- **Responsive Design** - Works on desktop and mobile devices

## Configuration

### Environment Variables

```bash
# Dashboard Configuration
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=8080
DASHBOARD_DEBUG=false
DASHBOARD_SECRET_KEY=your-secret-key
DASHBOARD_BASE_URL=http://localhost:8080

# OAuth Configuration
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
LINEAR_CLIENT_ID=your-linear-client-id
LINEAR_CLIENT_SECRET=your-linear-client-secret
SLACK_CLIENT_ID=your-slack-client-id
SLACK_CLIENT_SECRET=your-slack-client-secret

# Codegen SDK
CODEGEN_ORG_ID=your-org-id
CODEGEN_TOKEN=your-codegen-token
```

### OAuth Setup

1. **GitHub OAuth App**:
   - Go to GitHub Settings > Developer settings > OAuth Apps
   - Create new OAuth App
   - Set Authorization callback URL to `{DASHBOARD_BASE_URL}/auth/github/callback`

2. **Linear OAuth App**:
   - Go to Linear Settings > API > OAuth applications
   - Create new OAuth application
   - Set Redirect URI to `{DASHBOARD_BASE_URL}/auth/linear/callback`

3. **Slack OAuth App**:
   - Go to Slack API > Your Apps
   - Create new Slack app
   - Set Redirect URL to `{DASHBOARD_BASE_URL}/auth/slack/callback`

## Usage

### Starting the Dashboard

```python
from src.contexten.dashboard.app import app
import uvicorn

uvicorn.run(app, host="0.0.0.0", port=8080)
```

### Using the Linear Agent

```python
from src.contexten.extensions.linear.enhanced_agent import EnhancedLinearAgent, LinearAgentConfig

# Configure the agent
config = LinearAgentConfig(
    api_key="your-linear-api-key",
    webhook_secret="your-webhook-secret",
    auto_assignment=True,
    workflow_automation=True
)

# Create and start the agent
agent = EnhancedLinearAgent(config)
await agent.start()

# Create an issue
issue = await agent.create_issue(
    title="New Feature Request",
    description="Implement user authentication",
    team_id="team-id",
    priority=2
)

# Process webhooks
await agent.process_webhook(webhook_payload, signature)

# Stop the agent
await agent.stop()
```

### Using the GitHub Agent

```python
from src.contexten.extensions.github.enhanced_agent import EnhancedGitHubAgent, GitHubAgentConfig

# Configure the agent
config = GitHubAgentConfig(
    token="your-github-token",
    webhook_secret="your-webhook-secret",
    workflow_automation=True
)

# Create and start the agent
agent = EnhancedGitHubAgent(config)
await agent.start()

# Get repositories
repos = await agent.get_repositories()

# Create an issue
issue = await agent.create_issue(
    owner="username",
    repo="repository",
    title="Bug Report",
    body="Description of the bug"
)

# Stop the agent
await agent.stop()
```

## API Endpoints

### Authentication
- `GET /auth/{provider}` - Initiate OAuth login
- `GET /auth/{provider}/callback` - OAuth callback
- `POST /auth/logout` - Logout user

### Projects
- `GET /api/projects` - Get user's GitHub projects
- `POST /api/projects/{project_id}/select` - Select a project
- `POST /api/projects/{project_id}/pin` - Pin a project
- `DELETE /api/projects/{project_id}/pin` - Unpin a project

### Requirements
- `POST /api/requirements` - Submit project requirements

### Codegen
- `POST /api/codegen/start` - Start Codegen task
- `GET /api/codegen/status` - Get task status
- `POST /api/codegen/stop` - Stop Codegen task

### Integrations
- `GET /api/integrations/status` - Get integration status

## Dependencies

### Python Packages
- `fastapi` - Web framework
- `aiohttp` - HTTP client
- `authlib` - OAuth implementation
- `jinja2` - Template engine
- `python-multipart` - Form data parsing
- `codegen` - Codegen SDK

### Frontend Dependencies
- Bootstrap 5.1.3 - UI framework
- Font Awesome 6.0.0 - Icons
- Vanilla JavaScript - No additional frameworks

## Security Considerations

1. **OAuth Security** - Secure token storage and validation
2. **Webhook Validation** - HMAC signature verification
3. **Session Management** - Secure session handling
4. **Rate Limiting** - Respect API rate limits
5. **Input Validation** - Validate all user inputs
6. **HTTPS** - Use HTTPS in production

## Monitoring and Logging

- **Health Checks** - Built-in health check endpoints
- **Structured Logging** - Comprehensive logging throughout
- **Error Handling** - Graceful error handling and recovery
- **Metrics** - Performance and usage metrics

## Future Enhancements

1. **Database Integration** - Persistent storage for projects and tasks
2. **Advanced Workflows** - More sophisticated automation rules
3. **Team Management** - Multi-user support and team features
4. **Analytics Dashboard** - Usage analytics and insights
5. **Plugin System** - Extensible plugin architecture
6. **Mobile App** - Native mobile applications

## Troubleshooting

### Common Issues

1. **OAuth Errors** - Check client IDs and secrets
2. **Webhook Failures** - Verify webhook secrets and URLs
3. **API Rate Limits** - Implement proper rate limiting
4. **Connection Issues** - Check network connectivity and API status

### Debug Mode

Enable debug mode by setting `DASHBOARD_DEBUG=true` to get:
- Detailed error messages
- API documentation at `/docs`
- Enhanced logging

## Contributing

1. Follow the existing code structure
2. Add comprehensive tests
3. Update documentation
4. Follow security best practices
5. Test OAuth flows thoroughly

## License

This implementation follows the same license as the parent Contexten project.

