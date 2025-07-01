<br />

<p align="center">
  <a href="https://graph-sitter.com">
    <img src="https://i.imgur.com/6RF9W0z.jpeg" />
  </a>
</p>

<h2 align="center">
  Scriptable interface to a powerful, multi-lingual language server with autonomous CI/CD capabilities.
</h2>

<div align="center">

[![PyPI](https://img.shields.io/badge/PyPi-codegen-gray?style=flat-square&color=blue)](https://pypi.org/project/codegen/)
[![Documentation](https://img.shields.io/badge/Docs-graph-sitter.com-purple?style=flat-square)](https://graph-sitter.com)
[![Slack Community](https://img.shields.io/badge/Slack-Join-4A154B?logo=slack&style=flat-square)](https://community.codegen.com)
[![License](https://img.shields.io/badge/Code%20License-Apache%202.0-gray?&color=gray)](https://github.com/codegen-sh/graph-sitter/tree/develop?tab=Apache-2.0-1-ov-file)
[![Follow on X](https://img.shields.io/twitter/follow/codegen?style=social)](https://x.com/codegen)

</div>

<br />

[Graph-sitter](https://graph-sitter.com) is a python library for manipulating codebases with **autonomous CI/CD capabilities** powered by the Codegen SDK.

## 🚀 Autonomous CI/CD Features

Graph-sitter now includes a fully autonomous CI/CD system that integrates with the Codegen SDK for intelligent automation:

```python
from contexten.autonomous_cicd import setup_autonomous_cicd

# Setup autonomous CI/CD with Codegen SDK
cicd = await setup_autonomous_cicd(
    codegen_org_id="your-org-id",
    codegen_token="your-token",
    repo_path="./",
    enable_all_features=True
)

# The system automatically:
# - Analyzes code quality on every push
# - Runs intelligent tests based on changes
# - Deploys to staging environments
# - Creates PR reviews with AI insights
# - Tracks issues and manages workflows
```

### Key Autonomous Features

- **🔍 Intelligent Code Analysis**: AI-powered code quality assessment using Codegen SDK
- **🧪 Adaptive Testing**: Smart test selection based on code changes
- **🚀 Automated Deployment**: Intelligent deployment to staging/production
- **📊 Real-time Monitoring**: Health checks and performance metrics
- **🔗 Platform Integration**: GitHub, Linear, and Slack webhooks
- **🛡️ Security Scanning**: Automated vulnerability detection
- **📈 Analytics Dashboard**: Comprehensive CI/CD metrics and insights

## Core Capabilities

```python
from graph_sitter import Codebase
from codegen.agents.agent import Agent

# Initialize Codegen agent
agent = Agent(
    org_id="11",  # Your organization ID
    token="your_api_token_here",  # Your API authentication token
    base_url="https://codegen-sh-rest-api.modal.run",  # Optional - defaults to this URL
)

# Run an agent with a prompt
task = agent.run(prompt="Which github repos can you currently access?")

# Check the initial status
print(task.status)  # Returns the current status of the task (e.g., "queued", "in_progress", etc.)

# Graph-sitter builds a complete graph connecting
# functions, classes, imports and their relationships
codebase = Codebase("./")

# Work with code without dealing with syntax trees or parsing
for function in codebase.functions:
    # Comprehensive static analysis for references, dependencies, etc.
    if not function.usages:
        # Auto-handles references and imports to maintain correctness
        function.move_to_file("deprecated.py")

# Refresh the task to get updated status
task.refresh()

# Check the updated status
print(task.status)

# Once task is complete, you can access the result
if task.status == "completed":
    print(task.result)
```

## Quick Start with Autonomous CI/CD

### 1. Installation

```bash
# Install graph-sitter with CI/CD capabilities
uv pip install graph-sitter

# Or install global CLI
uv tool install graph-sitter --python 3.13
```

### 2. Setup Environment

```bash
# Set up your Codegen credentials
export CODEGEN_ORG_ID="your-org-id"
export CODEGEN_TOKEN="your-token"

# Optional: GitHub and Linear integration
export GITHUB_TOKEN="your-github-token"
export LINEAR_API_KEY="your-linear-key"
```

### 3. Initialize Autonomous CI/CD

```bash
# Initialize CI/CD configuration
python -m contexten.autonomous_cicd.cli init

# Start the autonomous CI/CD system
python -m contexten.autonomous_cicd.cli start
```

### 4. Web Dashboard

```bash
# Start the web API and dashboard
python -m contexten.autonomous_cicd.web_api

# Access dashboard at http://localhost:8000
```

## Autonomous CI/CD Architecture

The system consists of three main components:

### 1. **Intelligent Agents**
- **Code Analysis Agent**: Uses Codegen SDK for deep code understanding
- **Testing Agent**: Adaptive test execution based on changes
- **Deployment Agent**: Smart deployment with rollback capabilities

### 2. **Event Triggers**
- **GitHub Webhooks**: Automatic pipeline triggers on push/PR
- **Linear Integration**: Issue-driven CI/CD workflows
- **Scheduled Tasks**: Periodic health checks and maintenance

### 3. **Platform Integration**
- **Contexten Orchestrator**: Seamless integration with existing workflows
- **Graph-Sitter Analysis**: Enhanced code understanding and manipulation
- **Codegen SDK**: AI-powered automation and decision making

## Example: Autonomous Pipeline

```python
# Example: Run autonomous analysis pipeline
from contexten.autonomous_cicd import AutonomousCICD, CICDConfig

config = CICDConfig.from_env()
cicd = AutonomousCICD(config)

await cicd.initialize()

# Trigger intelligent analysis
result = await cicd.execute_pipeline(
    trigger_event={
        "branch": "feature/new-api",
        "changes": ["src/api/endpoints.py", "tests/test_api.py"],
        "trigger_type": "github_push"
    },
    pipeline_type="full"  # analysis + testing + deployment
)

print(f"Pipeline {result.pipeline_id} completed: {result.status}")
print(f"Quality score: {result.stages['analysis'].quality_score}")
print(f"Test coverage: {result.stages['testing'].coverage}%")
```

## Installation and Usage

We support

- Running Graph-sitter in Python 3.12 - 3.13 (recommended: Python 3.13+)
- macOS and Linux
  - macOS is supported
  - Linux is supported on x86_64 and aarch64 with glibc 2.34+
  - Windows is supported via WSL. See [here](https://graph-sitter.com/building-with-graph-sitter/codegen-with-wsl) for more details.
- Python, Typescript, Javascript and React codebases

```
# Install inside existing project
uv pip install graph-sitter

# Install global CLI
uv tool install graph-sitter --python 3.13

# Create a codemod for a given repo
cd path/to/repo
gs init
gs create test-function

# Run the codemod
gs run test-function

# Create an isolated venv with codegen => open jupyter
gs notebook
```

## Usage

See [Getting Started](https://graph-sitter.com/introduction/getting-started) for a full tutorial.

```
from graph_sitter import Codebase
```

## Troubleshooting

Having issues? Here are some common problems and their solutions:

- **I'm hitting an UV error related to `[[ packages ]]`**: This means you're likely using an outdated version of UV. Try updating to the latest version with: `uv self update`.
- **I'm hitting an error about `No module named 'codegen.sdk.extensions.utils'`**: The compiled cython extensions are out of sync. Update them with `uv sync --reinstall-package codegen`.
- **I'm hitting a `RecursionError: maximum recursion depth exceeded` error while parsing my codebase**: If you are using python 3.12, try upgrading to 3.13. If you are already on 3.13, try upping the recursion limit with `sys.setrecursionlimit(10000)`.

If you run into additional issues not listed here, please [join our slack community](https://community.codegen.com) and we'll help you out!

## Resources

- [Docs](https://graph-sitter.com)
- [Getting Started](https://graph-sitter.com/introduction/getting-started)
- [Contributing](CONTRIBUTING.md)
- [Contact Us](https://codegen.com/contact)

## Why Graph-sitter?

Software development is fundamentally programmatic. Refactoring a codebase, enforcing patterns, or analyzing control flow - these are all operations that can (and should) be expressed as programs themselves.

We built Graph-sitter backwards from real-world refactors performed on enterprise codebases. Instead of starting with theoretical abstractions, we focused on creating APIs that match how developers actually think about code changes:

- **Natural mental model**: Write transforms that read like your thought process - "move this function", "rename this variable", "add this parameter". No more wrestling with ASTs or manual import management.

- **Battle-tested on complex codebases**: Handle Python, TypeScript, and React codebases with millions of lines of code.

- **Built for advanced intelligences**: As AI developers become more sophisticated, they need expressive yet precise tools to manipulate code. Graph-sitter provides a programmatic interface that both humans and AI can use to express complex transformations through code itself.

## Contributing

Please see our [Contributing Guide](CONTRIBUTING.md) for instructions on how to set up the development environment and submit contributions.

## Enterprise

For more information on enterprise engagements, please [contact us](https://codegen.com/contact) or [request a demo](https://codegen.com/request-demo).
