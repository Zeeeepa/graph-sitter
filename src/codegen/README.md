# Codegen SDK

The Codegen SDK enables developers to programmatically interact with [Codegen](https://codegen.com/) SWE agents via API.

## Features

- **Agent Management**: Create and manage AI software engineering agents
- **Task Execution**: Run tasks with prompts and get results
- **Repository Integration**: Work with specific repositories and branches
- **Real-time Monitoring**: Track task progress and status
- **Webhook Support**: Receive notifications for task events
- **CLI Interface**: Command-line tool for easy interaction
- **Error Handling**: Comprehensive error handling and retry logic

## Installation

Install the SDK using pip or uv:

```bash
pip install codegen
# or
uv pip install codegen
```

## Quick Start

### Basic Usage

```python
from codegen import Agent

# Initialize the Agent with your organization ID and API token
agent = Agent(org_id="your-org-id", token="your-api-token")

# Run an agent with a prompt
task = agent.run(prompt="Leave a review on PR #123")

# Check the initial status
print(task.status)

# Refresh the task to get updated status (tasks can take time)
task.refresh()

if task.status == "completed":
    print(task.result)  # Result often contains code, summaries, or links
```

### Advanced Usage

```python
from codegen import Agent

agent = Agent(org_id="your-org-id", token="your-api-token")

# Run a task with additional context
task = agent.run(
    prompt="Fix the authentication bug in the login component",
    context={
        "issue_number": 456,
        "priority": "high",
        "affected_files": ["src/auth/login.py", "tests/test_auth.py"]
    },
    repository="myorg/myrepo",
    branch="develop",
    priority="high"
)

# Wait for completion with timeout
try:
    task.wait_for_completion(timeout=600, poll_interval=10)
    print(f"Task completed: {task.result}")
    
    # Get artifacts (e.g., created PRs, modified files)
    artifacts = task.get_artifacts()
    for artifact in artifacts:
        print(f"Artifact: {artifact}")
        
except TaskError as e:
    print(f"Task failed: {e}")
```

## Configuration

### Environment Variables

Set these environment variables for automatic configuration:

```bash
export CODEGEN_ORG_ID="your-org-id"
export CODEGEN_TOKEN="your-api-token"
export CODEGEN_BASE_URL="https://api.codegen.com"  # Optional
```

### Configuration File

Create a `.env` file or JSON configuration:

```bash
# .env file
CODEGEN_ORG_ID=your-org-id
CODEGEN_TOKEN=your-api-token
CODEGEN_BASE_URL=https://api.codegen.com
```

```python
from codegen import Config, Agent

# Load from file
config = Config.from_file(".env")
agent = Agent(org_id=config.org_id, token=config.token)
```

## API Reference

### Agent Class

The main class for interacting with Codegen agents.

#### Constructor

```python
Agent(org_id: str, token: str, base_url: str = "https://api.codegen.com")
```

#### Methods

- `run(prompt, context=None, repository=None, branch=None, priority="normal")` - Run a new task
- `get_task(task_id)` - Get a task by ID
- `list_tasks(status=None, limit=50, offset=0)` - List tasks
- `get_usage(start_date=None, end_date=None)` - Get usage statistics
- `get_repositories()` - Get available repositories
- `create_webhook(url, events)` - Create a webhook

### Task Class

Represents a task executed by a Codegen agent.

#### Properties

- `status` - Current task status
- `result` - Task result (if completed)
- `error` - Error message (if failed)
- `progress` - Progress information
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp
- `prompt` - Original prompt
- `metadata` - Additional metadata
- `logs` - Execution logs

#### Methods

- `refresh()` - Refresh task data from API
- `wait_for_completion(timeout=300, poll_interval=5)` - Wait for completion
- `cancel()` - Cancel the task
- `get_artifacts()` - Get task artifacts

## Command Line Interface

The SDK includes a CLI tool for easy interaction:

```bash
# Run a simple task
codegen run "Review PR #123"

# Run with specific repository and context
codegen run "Fix authentication bug" --repo myorg/myrepo --branch develop

# List recent tasks
codegen list --status completed --limit 10

# Get task details
codegen get task-id-123

# Check usage statistics
codegen usage --start-date 2024-01-01
```

## Error Handling

The SDK provides comprehensive error handling:

```python
from codegen import Agent, CodegenError, TaskError, AuthenticationError

try:
    agent = Agent(org_id="org-id", token="token")
    task = agent.run(prompt="Review code")
    task.wait_for_completion()
    
except AuthenticationError:
    print("Invalid credentials")
except TaskError as e:
    print(f"Task failed: {e}")
except CodegenError as e:
    print(f"General error: {e}")
```

## Examples

### Batch Processing

```python
from codegen import Agent

agent = Agent(org_id="your-org-id", token="your-api-token")

# Run multiple tasks
prompts = [
    "Review PR #123 for security issues",
    "Update documentation for new API",
    "Fix linting errors in codebase"
]

tasks = []
for prompt in prompts:
    task = agent.run(prompt=prompt)
    tasks.append(task)

# Wait for all to complete
for task in tasks:
    task.wait_for_completion()
    print(f"Task {task.task_id}: {task.status}")
```

### Webhook Integration

```python
from codegen import Agent

agent = Agent(org_id="your-org-id", token="your-api-token")

# Set up webhook for task events
webhook = agent.create_webhook(
    url="https://your-app.com/webhooks/codegen",
    events=["task.completed", "task.failed"]
)

# Your webhook endpoint will receive POST requests when tasks complete
```

## What can I do with the Codegen SDK?

The Codegen SDK is your gateway to programmatically interacting with your AI Software Engineer. You can use it to:

- **Automate development tasks**: Assign tasks like implementing features, fixing bugs, writing tests, or improving documentation to the agent
- **Integrate AI into your workflows**: Trigger agent tasks from your CI/CD pipelines, scripts, or other development tools
- **Provide context and guidance**: Supply the agent with specific instructions, relevant code snippets, or background information to ensure it performs tasks according to your requirements

Essentially, the SDK allows you to leverage Codegen's AI capabilities wherever you can run Python code.

## Getting Your API Token

1. Go to [developer settings](https://codegen.sh/token) to generate an API token
2. Set your organization ID and token as environment variables or pass them directly to the Agent constructor

## Support

- Documentation: [https://docs.codegen.com](https://docs.codegen.com)
- API Reference: [https://docs.codegen.com/introduction/api](https://docs.codegen.com/introduction/api)
- GitHub: [https://github.com/codegen-sh/codegen-sdk](https://github.com/codegen-sh/codegen-sdk)

## License

This project is licensed under the MIT License.

