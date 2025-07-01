# Complete CICD System with Codegen SDK

A comprehensive CI/CD system built using the Codegen SDK that provides autonomous development workflows through natural language prompts.

## 🚀 Features

- **Prompt-Driven Architecture**: All actions via natural language prompts using Codegen SDK
- **Project Management**: Create, track, and manage projects with automatic Linear integration
- **GitHub Integration**: Automatic PR reviews, validation, and deployment
- **Linear Orchestration**: Main issues with sub-issues, auto-assignment to @codegen
- **Modal Webhooks**: Unified webhook handling for GitHub and Linear events
- **Real-time Dashboard**: Project monitoring and team collaboration
- **Deployment Validation**: Automatic validation via successful PR deployments

## 📋 Prerequisites

1. **Codegen Account**: Get your org_id and token from [codegen.com/developer](https://codegen.com/developer)
2. **GitHub PAT**: Personal Access Token with repo and webhook permissions
3. **Linear API**: API token and team ID from Linear settings
4. **Modal Account**: For webhook deployment (optional but recommended)

## 🛠️ Installation

1. **Clone and Setup**:
```bash
git clone <repository-url>
cd cicd-system
pip install -r requirements.txt
```

2. **Environment Configuration**:
```bash
cp .env.example .env
# Edit .env with your actual credentials
```

3. **Required Environment Variables**:
```bash
# Codegen (Required)
CODEGEN_ORG_ID=323
CODEGEN_TOKEN=sk-ce027fa7-3c8d-4beb-8c86-ed8ae982ac99

# GitHub (Required)
GITHUB_TOKEN=your_github_pat_token
GITHUB_ORG=your_org
GITHUB_REPO=your_repo

# Linear (Required)
LINEAR_TOKEN=your_linear_token
LINEAR_TEAM_ID=your_team_id

# Webhooks (Optional)
WEBHOOK_BASE_URL=https://your-modal-app.modal.run
```

## 🚀 Quick Start

### 1. Basic Project Creation

```python
from cicd_system import CICDSystem, CICDConfig

# Create system
system = CICDSystem()

# Create a project
project_id = await system.create_project(
    name="AI Code Assistant",
    requirements="""
    Create an AI-powered code assistant that can:
    1. Analyze codebases and provide insights
    2. Generate code based on natural language descriptions
    3. Review pull requests automatically
    4. Suggest optimizations and refactoring
    5. Integrate with GitHub and Linear for workflow automation
    """,
    github_repo="myorg/ai-code-assistant"
)

# Pin to dashboard
dashboard = await system.pin_project_to_dashboard(project_id)
print(f"Dashboard: {dashboard['dashboard_url']}")
```

### 2. Using the Simple API

```python
from cicd_system import quick_project_setup

# One-line project setup
project_id = await quick_project_setup(
    name="My Project",
    requirements="Build a web app with user authentication",
    github_repo="myorg/my-project"
)
```

## 🎯 How It Works

### 1. **Project Creation**
- Creates Linear main issue as project orchestrator
- Generates sub-issues for different functionalities
- Sets up GitHub repository monitoring
- Deploys Modal webhooks for real-time events

### 2. **Linear Orchestration**
```
[MAIN] Project Name - Orchestrator
├── [RESEARCH] Requirements Analysis
├── [IMPL] Core Implementation
├── [TEST] Testing and Validation
├── [DOCS] Documentation
└── [DEPLOY] CI/CD Setup
```

### 3. **Automatic Assignment**
- Monitors Linear issues every 30 seconds
- Auto-assigns unassigned issues to @codegen
- Ensures no tasks are left unattended

### 4. **PR Validation Pipeline**
- Automatic PR reviews on creation
- Code quality and security scans
- Test coverage validation (>80%)
- Deployment validation
- Linear issue updates

## 📊 Dashboard Features

The system provides a comprehensive dashboard with:

- **Real-time Project Status**: Live updates on all projects
- **Linear Issue Tracking**: Visual progress of all issues
- **GitHub PR Pipeline**: CI/CD status and deployment tracking
- **Team Activity**: Notifications and collaboration features
- **Performance Metrics**: Success rates, completion times, analytics

## 🔗 Webhook Integration

### Deploy to Modal

```bash
# Deploy webhooks
modal deploy modal_webhooks.py

# Get webhook URLs
modal app list
```

### Configure GitHub Webhooks

1. Go to your GitHub repository settings
2. Add webhook: `https://your-modal-app.modal.run/github-webhook`
3. Select events: Pull requests, Push, Issues
4. Set content type: `application/json`

### Configure Linear Webhooks

1. Go to Linear team settings
2. Add webhook: `https://your-modal-app.modal.run/linear-webhook`
3. Select events: Issues, Comments, Projects

## 🎮 Usage Examples

### Project Management

```python
# List all projects
projects = system.list_projects()

# Get project status
status = system.get_project_status(project_id)

# Add requirements
await system.add_requirements(
    project_id, 
    "Add mobile app support with React Native"
)

# Validate deployment
result = await system.validate_deployment(project_id, pr_number=42)
```

### Direct Codegen Integration

```python
from codegen import Agent

# Direct Codegen usage (the simple way!)
agent = Agent(org_id="323", token="your-token")

# Create Linear issue
task = agent.run(prompt="Create a Linear issue for implementing user authentication")

# Review PR
task = agent.run(prompt="Review PR #123 and provide detailed feedback")

# Merge PR
task = agent.run(prompt="Merge PR #123 to main branch after validation")
```

## 🔧 Advanced Configuration

### Custom Validation Rules

```python
config = CICDConfig(
    auto_assign_timeout=60,  # 60 seconds instead of 30
    github_org="custom-org",
    linear_team_id="custom-team"
)

system = CICDSystem(config)
```

### Webhook Customization

The Modal webhook handler can be customized for specific workflows:

```python
# In modal_webhooks.py
async def custom_pr_handler(self, payload):
    """Custom PR handling logic"""
    prompt = f"""
    Custom PR review for {payload['repository']['name']}:
    - Check for specific coding standards
    - Validate business logic
    - Ensure security compliance
    """
    
    task = self.codegen_agent.run(prompt=prompt)
    return await self._wait_for_completion(task)
```

## 📈 Monitoring and Analytics

The system tracks:

- **Project Success Rates**: Percentage of successful deployments
- **Issue Resolution Time**: Average time from creation to completion
- **PR Validation Metrics**: Test coverage, security scan results
- **Team Productivity**: Issues completed, PRs merged
- **System Health**: Webhook response times, error rates

## 🛡️ Security

- All credentials stored in environment variables
- GitHub PAT with minimal required permissions
- Linear API token with team-specific access
- Modal secrets for secure deployment
- Webhook signature verification

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

- **Documentation**: [Codegen Docs](https://docs.codegen.com)
- **Issues**: Create GitHub issues for bugs or feature requests
- **Community**: Join the [Codegen Slack](https://community.codegen.com)

## 🎉 Key Benefits

1. **Simplicity**: Everything via natural language prompts
2. **Automation**: Full CI/CD pipeline without manual intervention
3. **Intelligence**: AI-powered code reviews and suggestions
4. **Integration**: Seamless GitHub and Linear workflow
5. **Scalability**: Handle multiple projects simultaneously
6. **Reliability**: Built-in error handling and retry logic

---

**Remember**: This system embraces the Codegen philosophy - **ALL ACTIONS VIA PROMPTS**! 🚀

