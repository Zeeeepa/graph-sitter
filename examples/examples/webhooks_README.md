# Modern Modal Webhook Deployments

This directory contains updated Modal webhook deployments using the latest CodegenApp patterns and best practices.

## 🚀 What's New

### Key Improvements
- **Latest CodegenApp Architecture**: Uses the new `CodebaseEventsApp` and `EventRouterMixin` base classes
- **Memory Snapshots**: Automatic codebase snapshotting for better performance
- **Unified Webhook Support**: Single endpoint can handle both GitHub and Linear webhooks
- **Better Error Handling**: Comprehensive error handling and logging
- **Environment Configuration**: Flexible configuration via environment variables
- **Health Checks**: Built-in health check endpoints

### Updated Dependencies
- `codegen>=0.22.2` (latest version)
- `fastapi[standard]` (modern FastAPI with all features)
- `pydantic>=2.0.0` (latest Pydantic v2)
- Python 3.12 (latest stable version)

## 📁 Available Deployments

### 1. Linear Webhooks (`linear_webhooks/webhooks.py`)
Dedicated Linear webhook handler with support for:
- Issue events (create, update, delete)
- Comment events
- Project events
- Automatic codebase context management

### 2. GitHub Webhooks (`github_webhooks/webhooks.py`)
Dedicated GitHub webhook handler with support for:
- Pull request events
- Issue events
- Push events
- Pull request review events
- Automatic repository detection from payload

### 3. Unified Webhooks (`unified_webhooks/webhooks.py`)
**Recommended**: Single deployment handling both GitHub and Linear webhooks:
- Automatic webhook source detection
- Unified event handling
- Separate endpoints for specific webhook types
- Health check endpoints

## 🛠️ Setup Instructions

### 1. Environment Variables
Create a `.env` file with the following variables:

```bash
# Required for all deployments
GITHUB_ACCESS_TOKEN=your_github_token
LINEAR_ACCESS_TOKEN=your_linear_api_key
CODEGEN_ORG_ID=your_codegen_org_id
CODEGEN_TOKEN=your_codegen_token

# Optional: For Linear webhooks when repository info isn't in payload
GITHUB_ORG=your-github-org
GITHUB_REPO=your-repo-name
GITHUB_REPO_FULL_NAME=your-org/your-repo
```

### 2. Deploy to Modal

```bash
# Deploy the unified webhook (recommended)
modal deploy examples/examples/unified_webhooks/webhooks.py

# Or deploy specific webhook handlers
modal deploy examples/examples/linear_webhooks/webhooks.py
modal deploy examples/examples/github_webhooks/webhooks.py
```

### 3. Configure Webhooks

#### GitHub Webhook Configuration
1. Go to your repository settings → Webhooks
2. Add webhook with URL: `https://your-app.modal.run/unified-webhook`
3. Select events: Pull requests, Issues, Pushes, Pull request reviews
4. Content type: `application/json`

#### Linear Webhook Configuration
1. Go to Linear Settings → API → Webhooks
2. Add webhook with URL: `https://your-app.modal.run/unified-webhook`
3. Select events: Issues, Comments, Projects

## 🔧 Customization

### Adding Custom Event Handlers

```python
# In your setup_handlers method
@cg.github.event("pull_request")
async def handle_pull_request_event(data: dict, request: Request):
    action = data.get("action")
    pr_number = data.get("pull_request", {}).get("number")
    
    if action == "opened":
        # Your custom logic for new PRs
        pass
    elif action == "closed":
        # Your custom logic for closed PRs
        pass
    
    return {"status": "processed"}

@cg.linear.event("Issue")
async def handle_linear_issue_event(data: dict):
    action = data.get("action")
    issue_data = data.get("data", {})
    
    if action == "create":
        # Your custom logic for new Linear issues
        pass
    
    return {"status": "processed"}
```

### Environment-Specific Configuration

```python
import os

# Different configurations for different environments
if os.environ.get("ENVIRONMENT") == "production":
    keep_warm = 5
    container_idle_timeout = 600
else:
    keep_warm = 1
    container_idle_timeout = 300
```

## 🧪 Local Development

### Running Locally

```bash
# Install dependencies
pip install codegen>=0.22.2 fastapi[standard] uvicorn

# Run locally
python examples/examples/unified_webhooks/webhooks.py
```

### Testing Webhooks Locally

Use tools like ngrok to expose your local server:

```bash
# Install ngrok
npm install -g ngrok

# Expose local server
ngrok http 8000

# Use the ngrok URL in your webhook configurations
```

## 📊 Monitoring and Debugging

### Health Checks
- Unified webhook: `GET https://your-app.modal.run/health-check`
- Returns: `{"status": "healthy", "service": "unified-webhooks"}`

### Logs
View logs in Modal dashboard or via CLI:

```bash
modal logs your-app-name
```

### Common Issues

1. **Repository not found**: Ensure `GITHUB_ACCESS_TOKEN` has access to the repository
2. **Linear webhook not detected**: Check that `x-linear-signature` header is present
3. **Memory snapshot issues**: Increase `container_idle_timeout` for large repositories

## 🔄 Migration from Old Deployments

### From Old Linear Webhook
1. Update imports: `from codegen.extensions.events.app import CodegenApp`
2. Replace `@app.cls` with `CodebaseEventsApp` inheritance
3. Move event handlers to `setup_handlers` method
4. Update Modal app initialization

### From Old GitHub Webhook
1. Replace function-based approach with class-based `CodebaseEventsApp`
2. Add automatic repository detection
3. Update event handler signatures to include `Request` parameter

## 🚀 Advanced Features

### Memory Snapshots
Automatic codebase snapshotting improves performance by caching parsed repositories:

```python
@app.cls(
    enable_memory_snapshot=True,  # Enable snapshots
    container_idle_timeout=300,   # Keep containers warm
)
```

### Multi-Repository Support
Handle multiple repositories in a single deployment:

```python
def setup_handlers(self, cg: CodegenApp):
    # Repository-specific logic
    repo_name = f"{self.repo_org}/{self.repo_name}"
    
    if repo_name == "org/frontend-repo":
        # Frontend-specific handlers
        pass
    elif repo_name == "org/backend-repo":
        # Backend-specific handlers
        pass
```

## 📚 Additional Resources

- [Modal Documentation](https://modal.com/docs)
- [CodegenApp API Reference](https://docs.codegen.com)
- [GitHub Webhooks Documentation](https://docs.github.com/en/developers/webhooks-and-events/webhooks)
- [Linear Webhooks Documentation](https://developers.linear.app/docs/graphql/webhooks)

