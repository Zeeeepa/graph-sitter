# Prefect Autonomous CI/CD Setup Guide

This guide explains how to set up and configure the Prefect-based autonomous CI/CD system for the graph-sitter project.

## Overview

The autonomous CI/CD system uses Prefect to orchestrate:
- **Codegen SDK** integration for automated task execution
- **Linear** issue monitoring and management
- **GitHub** event processing and PR automation
- **System monitoring** and health checks

## Prerequisites

1. **Prefect Cloud Account** or local Prefect server
2. **Codegen SDK credentials** (API token and org ID)
3. **Linear API access** (API key)
4. **GitHub API access** (personal access token)

## Installation

1. Install Prefect and dependencies:
```bash
pip install prefect
pip install codegen  # Codegen SDK
pip install psutil   # For system monitoring
```

2. Configure Prefect:
```bash
# For Prefect Cloud
prefect cloud login

# Or for local server
prefect server start
```

## Environment Setup

### Required Environment Variables

Create a `.env` file or set these environment variables:

```bash
# Codegen SDK
CODEGEN_API_TOKEN=your_codegen_api_token
CODEGEN_ORG_ID=your_codegen_org_id

# Linear API
LINEAR_API_KEY=your_linear_api_key

# GitHub API
GITHUB_TOKEN=your_github_token

# Prefect (if using cloud)
PREFECT_API_KEY=your_prefect_api_key
```

### Prefect Secrets (Recommended)

For production, use Prefect secrets instead of environment variables:

```bash
# Create secrets in Prefect
prefect block register --module prefect.blocks.system

# Set secrets
prefect secret set codegen-api-token "your_token_here"
prefect secret set codegen-org-id "your_org_id_here"
prefect secret set linear-api-key "your_linear_key_here"
prefect secret set github-token "your_github_token_here"
```

## Deployment

### 1. Deploy the Flows

Run the deployment script:

```bash
python prefect_deployment.py
```

This creates three deployments:
- **autonomous-cicd-main**: Main orchestration flow (runs every 15 minutes)
- **component-analysis**: On-demand component analysis
- **system-health-monitoring**: Health checks (runs every 5 minutes)

### 2. Start the Agent

Start a Prefect agent to execute the flows:

```bash
prefect agent start --pool default-agent-pool
```

### 3. Monitor Flows

Access the Prefect UI to monitor flow runs:
- **Prefect Cloud**: https://app.prefect.cloud
- **Local server**: http://localhost:4200

## Flow Descriptions

### Autonomous CI/CD Flow (`autonomous_cicd_flow`)

**Purpose**: Main orchestration flow that coordinates the entire system.

**Schedule**: Every 15 minutes

**Tasks**:
1. Initialize Codegen SDK agent
2. Monitor GitHub events (PRs, issues)
3. Monitor Linear issues for component analysis requests
4. Process component analysis requests
5. Execute automated tasks via Codegen SDK
6. Handle error recovery and notifications

### Component Analysis Flow (`component_analysis_flow`)

**Purpose**: Detailed analysis of individual project components.

**Trigger**: On-demand (triggered by Linear issues or manual execution)

**Tasks**:
1. Get component files for analysis
2. Perform code quality analysis
3. Perform architectural analysis
4. Analyze integration points
5. Execute analyses via Codegen SDK
6. Report results

### System Health Flow (`system_health_flow`)

**Purpose**: Monitor system health and send alerts.

**Schedule**: Every 5 minutes

**Tasks**:
1. Check Codegen SDK connectivity
2. Check Linear API health
3. Check GitHub API health
4. Monitor system resources (CPU, memory, disk)
5. Check Prefect flow status
6. Send alerts for any issues

## Manual Execution

### Run Component Analysis

To manually trigger component analysis for a specific component:

```python
from src.contexten.prefect_flows.component_analysis import component_analysis_flow

# Analyze the contexten/agents component
result = component_analysis_flow(
    component="contexten/agents",
    linear_issue_id="ZAM-1084"  # Optional Linear issue ID
)
```

### Run Health Check

To manually run a health check:

```python
from src.contexten.prefect_flows.monitoring import system_health_flow

result = system_health_flow()
```

## Integration with Linear Issues

The system automatically processes Linear issues tagged for component analysis:

1. **Main Issue**: ZAM-1083 - Tracks overall progress
2. **Sub-Issues**: ZAM-1084 through ZAM-1093 - Individual component analyses

When a Linear issue is updated or assigned, the autonomous CI/CD flow will:
1. Detect the change
2. Generate appropriate analysis prompts
3. Execute the analysis via Codegen SDK
4. Update the Linear issue with results

## Monitoring and Alerts

### Health Monitoring

The system continuously monitors:
- **Codegen SDK**: API connectivity and response times
- **Linear API**: Service availability
- **GitHub API**: Rate limits and connectivity
- **System Resources**: CPU, memory, and disk usage
- **Prefect Flows**: Flow run status and errors

### Alert Thresholds

Default alert thresholds:
- CPU usage > 80%
- Memory usage > 80%
- Disk usage > 90%
- API response time > 30 seconds
- Flow failure rate > 10%

### Alert Channels

Configure alert channels in the monitoring flow:
- Slack notifications
- Email alerts
- Linear issue creation
- GitHub issue creation

## Troubleshooting

### Common Issues

1. **Codegen SDK Connection Errors**
   - Verify API token and org ID
   - Check network connectivity
   - Ensure sufficient API quota

2. **Prefect Flow Failures**
   - Check agent status: `prefect agent ls`
   - Review flow run logs in Prefect UI
   - Verify environment variables/secrets

3. **Linear API Issues**
   - Verify API key permissions
   - Check rate limiting
   - Ensure proper team/project access

4. **GitHub API Issues**
   - Verify token permissions
   - Check rate limiting
   - Ensure repository access

### Debugging

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

View flow run details:

```bash
prefect flow-run ls --limit 10
prefect flow-run logs <flow-run-id>
```

## Security Considerations

1. **Use Prefect Secrets** for sensitive credentials
2. **Rotate API tokens** regularly
3. **Limit API permissions** to minimum required
4. **Monitor API usage** for unusual activity
5. **Use HTTPS** for all API communications

## Scaling

For high-volume environments:

1. **Multiple Agents**: Deploy multiple Prefect agents
2. **Work Pools**: Use different work pools for different flow types
3. **Concurrency Limits**: Set appropriate concurrency limits
4. **Resource Monitoring**: Monitor and scale infrastructure as needed

## Next Steps

1. **Implement GitHub Webhooks**: Replace polling with real-time webhooks
2. **Add Slack Integration**: Direct notifications to Slack channels
3. **Enhanced Analytics**: Add metrics and dashboards
4. **Auto-scaling**: Implement dynamic resource scaling
5. **Advanced Alerting**: Implement sophisticated alerting rules

