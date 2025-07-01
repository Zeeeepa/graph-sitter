# Unified Webhooks - GitHub & Linear Integration

This directory contains a unified Modal deployment that handles both GitHub and Linear webhook events using the CodegenApp framework. The system automatically detects webhook sources and routes events to appropriate handlers.

## 🚀 What This Does

The unified webhook system provides:

- **Automatic Webhook Detection**: Intelligently routes GitHub and Linear webhooks to appropriate handlers
- **Event Processing**: Handles pull requests, issues, pushes (GitHub) and issues, comments, projects (Linear)
- **Codebase Context**: Maintains awareness of repository structure and changes
- **Scalable Architecture**: Built on Modal for serverless deployment with auto-scaling
- **Development Support**: Local development mode for testing

## 📋 Features

### GitHub Events Handled
- **Pull Requests**: `opened`, `synchronize`, `closed`, etc.
- **Issues**: `opened`, `closed`, `labeled`, etc.
- **Push Events**: Commits to any branch
- **Repository Events**: Various repository-level changes

### Linear Events Handled
- **Issues**: Create, update, delete, status changes
- **Comments**: New comments on issues
- **Projects**: Project creation and updates

### Key Capabilities
- ✅ Unified endpoint for both GitHub and Linear
- ✅ Separate endpoints for specific webhook types
- ✅ Health check endpoint
- ✅ Local development support
- ✅ Automatic codebase context management
- ✅ Event logging and monitoring

## 🛠️ Prerequisites

1. **Modal Account**: Sign up at [modal.com](https://modal.com)
2. **Environment Variables**: Configure required secrets
3. **Webhook URLs**: Access to GitHub/Linear webhook configuration

## 📦 Installation & Setup

### 1. Install Dependencies

```bash
# Install Modal CLI
pip install modal

# Install project dependencies
pip install codegen>=0.22.2 fastapi uvicorn pydantic openai slack_sdk
```

### 2. Configure Environment Variables

Create a `.env` file with the following variables:

```bash
# GitHub Configuration
GITHUB_TOKEN=your_github_token
GITHUB_ORG=your-organization
GITHUB_REPO=your-repository

# Linear Configuration  
LINEAR_API_KEY=your_linear_api_key
LINEAR_WEBHOOK_SECRET=your_linear_webhook_secret

# Codegen Configuration
CODEGEN_API_KEY=your_codegen_api_key
CODEGEN_ORG_ID=your_codegen_org_id

# Optional: OpenAI for enhanced processing
OPENAI_API_KEY=your_openai_api_key

# Optional: Slack integration
SLACK_BOT_TOKEN=your_slack_bot_token
SLACK_SIGNING_SECRET=your_slack_signing_secret
```

### 3. Modal Authentication

```bash
# Authenticate with Modal
modal token new

# Verify authentication
modal token current
```

## 🚀 Deployment

### Quick Deploy

```bash
# Deploy to Modal
modal deploy examples/examples/unified_webhooks/webhooks.py
```

### Deploy with Custom Name

```bash
# Deploy with specific app name
modal deploy examples/examples/unified_webhooks/webhooks.py --name my-webhooks
```

### Deploy for Development

```bash
# Deploy in development mode (with hot reloading)
modal serve examples/examples/unified_webhooks/webhooks.py
```

## 🔗 Webhook Configuration

After deployment, Modal will provide webhook URLs. Configure these in your services:

### GitHub Webhook Setup

1. Go to your repository settings → Webhooks
2. Add webhook with URL: `https://your-app.modal.run/unified-webhook`
3. Select events: Pull requests, Issues, Pushes
4. Content type: `application/json`

### Linear Webhook Setup

1. Go to Linear Settings → API → Webhooks
2. Add webhook with URL: `https://your-app.modal.run/unified-webhook`
3. Select events: Issues, Comments, Projects
4. Save webhook configuration

### Alternative: Separate Endpoints

For more control, use dedicated endpoints:

- GitHub only: `https://your-app.modal.run/github-only-webhook`
- Linear only: `https://your-app.modal.run/linear-only-webhook`

## 🧪 Local Development

### Run Locally

```bash
# Start local development server
python examples/examples/unified_webhooks/webhooks.py
```

This starts a FastAPI server on `http://localhost:8000` with:
- Webhook endpoint: `http://localhost:8000/webhook`
- Health check: `http://localhost:8000/health`

### Test Webhooks Locally

Use tools like ngrok to expose your local server:

```bash
# Install ngrok
npm install -g ngrok

# Expose local server
ngrok http 8000

# Use the ngrok URL in webhook configurations
```

## 📊 Monitoring & Logs

### View Logs

```bash
# View real-time logs
modal logs your-app-name

# View logs for specific function
modal logs your-app-name::UnifiedEventRouter.unified_webhook
```

### Health Check

```bash
# Check deployment health
curl https://your-app.modal.run/health-check
```

## 🔧 Customization

### Adding New Event Handlers

Edit the `setup_handlers` method in `UnifiedEventsApp`:

```python
@cg.github.event("release")
async def handle_release_event(data: dict, request: Request):
    """Handle GitHub Release events."""
    action = data.get("action", "unknown")
    release_name = data.get("release", {}).get("name", "No name")
    
    print(f"🎉 GitHub Release Event: {action} - {release_name}")
    
    # Your custom logic here
    
    return {"status": "processed", "event_type": "release", "action": action}
```

### Environment-Specific Configuration

```python
import os

# Different configurations per environment
if os.environ.get("ENVIRONMENT") == "production":
    # Production settings
    container_idle_timeout = 600
    keep_warm = 2
else:
    # Development settings  
    container_idle_timeout = 300
    keep_warm = 1
```

## 🐛 Troubleshooting

### Common Issues

1. **Webhook Not Receiving Events**
   - Check webhook URL configuration
   - Verify environment variables
   - Check Modal app logs

2. **Authentication Errors**
   - Verify GitHub/Linear tokens
   - Check token permissions
   - Ensure secrets are properly configured

3. **Deployment Failures**
   - Check Modal authentication
   - Verify dependencies in requirements
   - Review error logs

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📚 Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐
│   GitHub        │    │   Linear        │
│   Webhooks      │    │   Webhooks      │
└─────────┬───────┘    └─────────┬───────┘
          │                      │
          └──────────┬───────────┘
                     │
          ┌─────────────────────┐
          │  Unified Webhook    │
          │  Endpoint (Modal)   │
          └─────────┬───────────┘
                    │
          ┌─────────────────────┐
          │  Event Detection    │
          │  & Routing          │
          └─────────┬───────────┘
                    │
    ┌───────────────┼───────────────┐
    │               │               │
┌───▼────┐    ┌────▼────┐    ┌────▼────┐
│GitHub  │    │ Linear  │    │ Custom  │
│Handler │    │ Handler │    │ Handler │
└────────┘    └─────────┘    └─────────┘
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally
5. Submit a pull request

## 📄 License

This project follows the same license as the parent repository.

## 🆘 Support

- Check the [Modal documentation](https://modal.com/docs)
- Review [CodegenApp examples](../../../)
- Open an issue for bugs or feature requests

---

**Happy webhook handling! 🎉**

