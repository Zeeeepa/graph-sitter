# CircleCI Extension for Contexten

A comprehensive CircleCI integration that provides intelligent build monitoring, automatic failure analysis, and AI-powered fix generation.

## 🎯 Features

### Core Capabilities
- **Real-time Build Monitoring** - Monitor CircleCI builds via webhooks
- **Intelligent Failure Analysis** - Parse logs and identify root causes
- **Automatic Fix Generation** - Generate fixes using Codegen SDK + graph-sitter
- **GitHub Integration** - Create PRs with fixes automatically
- **Workflow Orchestration** - End-to-end automation from failure to fix

### Advanced Features
- **Wake-up on Failures** - Automatically trigger when CI checks fail
- **Log Analysis** - Deep parsing of build logs and error messages
- **Pattern Recognition** - Learn from common failures and solutions
- **Multi-project Support** - Handle multiple CircleCI projects
- **Security** - Secure webhook validation and credential management

## 🚀 Quick Start

### Installation

```python
from contexten.extensions.circleci import CircleCIIntegrationAgent, CircleCIIntegrationConfig

# Configure the integration
config = CircleCIIntegrationConfig(
    api_token="your-circleci-token",
    webhook_secret="your-webhook-secret",
    github_token="your-github-token",
    codegen_api_token="your-codegen-token"
)

# Initialize the agent
agent = CircleCIIntegrationAgent(config)

# Start monitoring
await agent.start()
```

### Webhook Setup

1. **Configure CircleCI Webhook**:
   ```bash
   # Add webhook URL to your CircleCI project
   https://your-domain.com/webhooks/circleci
   ```

2. **Set Environment Variables**:
   ```bash
   export CIRCLECI_API_TOKEN="your-token"
   export CIRCLECI_WEBHOOK_SECRET="your-secret"
   export GITHUB_TOKEN="your-github-token"
   export CODEGEN_API_TOKEN="your-codegen-token"
   ```

## 📖 Usage Examples

### Basic Monitoring

```python
import asyncio
from contexten.extensions.circleci import CircleCIIntegrationAgent

async def monitor_builds():
    agent = CircleCIIntegrationAgent.from_env()
    
    # Start monitoring
    await agent.start()
    
    # Get current status
    status = await agent.get_integration_status()
    print(f"Monitoring {status.projects_monitored} projects")
    
    # Keep running
    await agent.run_forever()

asyncio.run(monitor_builds())
```

### Webhook Processing

```python
from contexten.extensions.circleci import WebhookProcessor

async def handle_webhook(request):
    processor = WebhookProcessor(config)
    
    # Process incoming webhook
    result = await processor.process_webhook(
        headers=request.headers,
        body=request.body
    )
    
    if result.success:
        print(f"Processed {result.event_type} event")
    else:
        print(f"Failed to process webhook: {result.error}")
```

### Failure Analysis

```python
from contexten.extensions.circleci import FailureAnalyzer

async def analyze_failure():
    analyzer = FailureAnalyzer(config)
    
    # Analyze a failed build
    analysis = await analyzer.analyze_build_failure(
        project_slug="gh/owner/repo",
        build_number=123
    )
    
    print(f"Root cause: {analysis.root_cause}")
    print(f"Suggested fixes: {analysis.suggested_fixes}")
```

### Auto-Fix Generation

```python
from contexten.extensions.circleci import AutoFixGenerator

async def generate_fix():
    generator = AutoFixGenerator(config)
    
    # Generate fix for a failure
    fix = await generator.generate_fix(
        failure_analysis=analysis,
        repository="owner/repo",
        branch="main"
    )
    
    if fix.success:
        print(f"Generated fix: {fix.description}")
        print(f"PR created: {fix.pr_url}")
```

## 🔧 Configuration

### Basic Configuration

```python
from contexten.extensions.circleci import CircleCIIntegrationConfig

config = CircleCIIntegrationConfig(
    # Required
    api_token="your-circleci-token",
    webhook_secret="your-webhook-secret",
    
    # Optional
    github_token="your-github-token",
    codegen_api_token="your-codegen-token",
    
    # Automation settings
    auto_fix_enabled=True,
    auto_create_prs=True,
    max_fix_attempts=3,
    
    # Monitoring settings
    monitor_all_projects=True,
    failure_notification_enabled=True,
)
```

### Advanced Configuration

```python
config = CircleCIIntegrationConfig(
    # API settings
    api_token="your-token",
    api_base_url="https://circleci.com/api/v2",
    request_timeout=30,
    max_retries=3,
    
    # Webhook settings
    webhook_secret="your-secret",
    webhook_signature_header="circleci-signature",
    webhook_event_types=["workflow-completed", "job-completed"],
    
    # Failure analysis
    failure_analysis_enabled=True,
    log_analysis_depth="deep",
    pattern_learning_enabled=True,
    
    # Auto-fix settings
    auto_fix_enabled=True,
    fix_confidence_threshold=0.8,
    auto_create_prs=True,
    pr_auto_merge=False,
    
    # Integration settings
    github_integration_enabled=True,
    codegen_integration_enabled=True,
    slack_notifications_enabled=False,
)
```

## 🏗️ Architecture

### Component Overview

```
CircleCIIntegrationAgent
├── WebhookProcessor      # Handles incoming webhooks
├── FailureAnalyzer      # Analyzes build failures
├── AutoFixGenerator     # Generates code fixes
├── WorkflowAutomation   # Orchestrates workflows
└── CircleCIClient       # API communication
```

### Data Flow

1. **Webhook Reception** → CircleCI sends build status
2. **Event Processing** → Validate and route events
3. **Failure Detection** → Identify failed builds
4. **Log Analysis** → Parse logs for root causes
5. **Fix Generation** → Create targeted fixes
6. **PR Creation** → Deploy fixes via GitHub
7. **Status Monitoring** → Track fix success

## 🧪 Testing

### Unit Tests

```bash
# Run unit tests
pytest tests/unit/extensions/circleci/

# Run with coverage
pytest --cov=src/contexten/extensions/circleci tests/unit/extensions/circleci/
```

### Integration Tests

```bash
# Run integration tests
pytest tests/integration/circleci/

# Run end-to-end tests
pytest tests/integration/circleci/test_e2e_workflow.py
```

### Manual Testing

```python
# Test webhook processing
python -m contexten.extensions.circleci.test_webhook

# Test failure analysis
python -m contexten.extensions.circleci.test_analysis

# Test fix generation
python -m contexten.extensions.circleci.test_fixes
```

## 📊 Monitoring & Metrics

### Built-in Metrics

```python
# Get integration metrics
metrics = await agent.get_metrics()

print(f"Builds monitored: {metrics.builds_monitored}")
print(f"Failures detected: {metrics.failures_detected}")
print(f"Fixes generated: {metrics.fixes_generated}")
print(f"PRs created: {metrics.prs_created}")
print(f"Success rate: {metrics.fix_success_rate}%")
```

### Health Checks

```python
# Check integration health
health = await agent.health_check()

if health.healthy:
    print("✅ CircleCI integration is healthy")
else:
    print(f"❌ Issues detected: {health.issues}")
```

## 🔒 Security

### Webhook Security
- HMAC signature validation
- Request timestamp verification
- IP allowlist support
- Rate limiting

### Credential Management
- Environment variable support
- Secure credential storage
- Token rotation support
- Audit logging

## 🚨 Troubleshooting

### Common Issues

1. **Webhook Not Received**
   - Check CircleCI webhook configuration
   - Verify webhook URL is accessible
   - Check webhook secret matches

2. **API Authentication Failed**
   - Verify CircleCI API token is valid
   - Check token permissions
   - Ensure token hasn't expired

3. **Fix Generation Failed**
   - Check Codegen SDK configuration
   - Verify repository access
   - Review failure analysis logs

### Debug Mode

```python
# Enable debug logging
import logging
logging.getLogger('contexten.extensions.circleci').setLevel(logging.DEBUG)

# Run with debug mode
config.debug_mode = True
agent = CircleCIIntegrationAgent(config)
```

## 📚 API Reference

See the [API Documentation](./docs/api.md) for detailed information about all classes and methods.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This extension is part of the Contexten framework and follows the same licensing terms.

## 🆘 Support

- **Documentation**: [Full docs](./docs/)
- **Issues**: [GitHub Issues](https://github.com/your-org/contexten/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/contexten/discussions)

