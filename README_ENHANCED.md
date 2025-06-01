<br />

<p align="center">
  <a href="https://graph-sitter.com">
    <img src="https://i.imgur.com/6RF9W0z.jpeg" />
  </a>
</p>

<h2 align="center">
  Scriptable interface to a powerful, multi-lingual language server.
</h2>

<div align="center">

[![PyPI](https://img.shields.io/badge/PyPi-codegen-gray?style=flat-square&color=blue)](https://pypi.org/project/codegen/)
[![Documentation](https://img.shields.io/badge/Docs-graph-sitter.com-purple?style=flat-square)](https://graph-sitter.com)
[![Slack Community](https://img.shields.io/badge/Slack-Join-4A154B?logo=slack&style=flat-square)](https://community.codegen.com)
[![License](https://img.shields.io/badge/Code%20License-Apache%202.0-gray?&color=gray)](https://github.com/codegen-sh/graph-sitter/tree/develop?tab=Apache-2.0-1-ov-file)
[![Follow on X](https://img.shields.io/twitter/follow/codegen?style=social)](https://x.com/codegen)

</div>

<br />

# Graph-Sitter: AI-Powered Code Analysis & Orchestration Platform

[Graph-sitter](https://graph-sitter.com) is a comprehensive Python framework that combines powerful code analysis, AI agent orchestration, and seamless integrations to transform how you work with codebases.

## 🏗️ Architecture Overview

Graph-sitter consists of three core modules working in harmony:

### 1. 🧠 **Codegen SDK** - AI Agent Integration
Direct programmatic access to Codegen's AI Software Engineers via API.

```python
from codegen import Agent

# Initialize the Agent with your organization ID and API token
agent = Agent(
    org_id="11",  # Your organization ID
    token="your_api_token_here",  # Your API authentication token
    base_url="https://codegen-sh-rest-api.modal.run",  # Optional - defaults to this URL
)

# Run an agent with a prompt
task = agent.run(prompt="Which github repos can you currently access?")

# Check the initial status
print(task.status)  # Returns the current status of the task

# Refresh the task to get updated status
task.refresh()

# Once task is complete, you can access the result
if task.status == "completed":
    print(task.result)
```

### 2. 🎯 **Contexten** - Agentic Orchestrator
Advanced chat agents with LangChain integration and multi-platform support (GitHub, Linear, Slack).

```python
from contexten import ContextenAgent

# Initialize contexten agent with integrations
agent = ContextenAgent(
    anthropic_api_key="your_key",
    github_token="your_token",
    linear_api_key="your_key"
)

# Run orchestrated workflows
result = await agent.execute_workflow(
    "Create a Linear issue for the bug found in PR #123 and assign it to the team"
)
```

### 3. 🔍 **Graph-Sitter** - Code Analysis Engine
Powerful code manipulation and analysis using Tree-sitter parsing with graph algorithms.

```python
from graph_sitter import Codebase

# Graph-sitter builds a complete graph connecting
# functions, classes, imports and their relationships
codebase = Codebase("./")

# Work with code without dealing with syntax trees or parsing
for function in codebase.functions:
    # Comprehensive static analysis for references, dependencies, etc.
    if not function.usages:
        # Auto-handles references and imports to maintain correctness
        function.move_to_file("deprecated.py")
```

## 🚀 Quick Start

### Installation

```bash
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

### Environment Setup

Copy `.env.example` to `.env` and configure your integrations:

```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

Key environment variables:
- `CODEGEN_ORG_ID` & `CODEGEN_TOKEN` - For Codegen SDK
- `CONTEXTEN_ANTHROPIC_API_KEY` - For AI agent capabilities  
- `GITHUB_TOKEN` - For GitHub integration
- `LINEAR_API_KEY` - For Linear integration
- `SLACK_BOT_TOKEN` - For Slack integration

## 📚 Core Features

### 🤖 AI-Powered Development
- **Automated Code Generation**: Use AI agents to implement features, fix bugs, and write tests
- **Intelligent Refactoring**: Context-aware code transformations that maintain correctness
- **Multi-Platform Integration**: Seamlessly work across GitHub, Linear, and Slack

### 🔧 Advanced Code Analysis
- **Semantic Understanding**: Deep analysis of code relationships and dependencies
- **Multi-Language Support**: Python, TypeScript, JavaScript, React, and more
- **Graph-Based Operations**: Leverage graph algorithms for complex code transformations

### 🎛️ Orchestration & Automation
- **Workflow Automation**: Chain together complex development tasks
- **Event-Driven Processing**: React to GitHub PRs, Linear issues, and Slack messages
- **Extensible Architecture**: Build custom integrations and workflows

## 🛠️ Development Workflow

### Running Tests

```bash
# Run unit tests (recommended for development)
./scripts/run_tests.sh --unit

# Run integration tests
./scripts/run_tests.sh --integration

# Run all tests
./scripts/run_tests.sh --all

# Run with coverage
./scripts/run_tests.sh --coverage
```

### Building from Source

```bash
# Full development setup
./scripts/fullbuild.sh

# Quick build and test
./scripts/build_and_test.sh --test
```

### CI/CD Pipeline

Our comprehensive CI/CD pipeline includes:
- **Multi-platform testing** (Ubuntu, macOS, ARM)
- **Parallel test execution** for faster feedback
- **Automated releases** to PyPI
- **Code quality checks** (MyPy, pre-commit hooks)

See [CICD_FLOW.md](CICD_FLOW.md) for detailed documentation.

## 🌟 Use Cases

### For Individual Developers
- **Code Analysis**: Understand complex codebases quickly
- **Automated Refactoring**: Safe, large-scale code transformations
- **AI-Assisted Development**: Get help with implementation and debugging

### For Teams
- **Workflow Automation**: Automate issue creation, PR reviews, and deployments
- **Cross-Platform Integration**: Unify GitHub, Linear, and Slack workflows
- **Code Quality Enforcement**: Automated code analysis and improvement suggestions

### For Organizations
- **Enterprise Integration**: Scale AI-powered development across teams
- **Custom Workflows**: Build domain-specific automation and analysis tools
- **Knowledge Management**: Extract insights from large codebases

## 🔧 System Requirements

- **Python**: 3.12 - 3.13 (recommended: Python 3.13+)
- **Operating Systems**:
  - macOS (supported)
  - Linux (x86_64 and aarch64 with glibc 2.34+)
  - Windows (via WSL - see [WSL guide](https://graph-sitter.com/building-with-graph-sitter/codegen-with-wsl))
- **Supported Languages**: Python, TypeScript, JavaScript, React

## 🆘 Troubleshooting

### Common Issues

- **UV Error with `[[ packages ]]`**: Update UV with `uv self update`
- **Missing Cython Extensions**: Run `uv sync --reinstall-package codegen`
- **RecursionError**: Upgrade to Python 3.13 or increase recursion limit with `sys.setrecursionlimit(10000)`

### Getting Help

- 💬 [Join our Slack community](https://community.codegen.com)
- 📖 [Read the documentation](https://graph-sitter.com)
- 🐛 [Report issues on GitHub](https://github.com/codegen-sh/graph-sitter/issues)

## 📖 Documentation & Resources

- **[Getting Started Guide](https://graph-sitter.com/introduction/getting-started)** - Complete tutorial
- **[API Reference](https://graph-sitter.com/api-reference)** - Detailed API documentation
- **[Examples](examples/)** - Real-world usage examples
- **[Contributing Guide](CONTRIBUTING.md)** - How to contribute
- **[CI/CD Documentation](CICD_FLOW.md)** - Development workflow details

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for:
- Development environment setup
- Code style guidelines
- Testing requirements
- Pull request process

## 🏢 Enterprise

For enterprise engagements, custom integrations, or dedicated support:
- 📧 [Contact us](https://codegen.com/contact)
- 🎯 [Request a demo](https://codegen.com/request-demo)

## 🎯 Why Graph-sitter?

Software development is fundamentally programmatic. Graph-sitter provides the tools to express complex code transformations, analysis, and automation as programs themselves.

**Built for the AI Era**: As AI becomes central to development workflows, Graph-sitter provides the programmatic interface that both humans and AI need to manipulate code effectively.

**Enterprise-Tested**: Battle-tested on codebases with millions of lines of code across Python, TypeScript, and React.

**Developer-Focused**: APIs that match how developers think about code changes - "move this function", "rename this variable", "add this parameter" - without wrestling with ASTs or manual import management.

---

<div align="center">

**[Get Started](https://graph-sitter.com/introduction/getting-started)** • **[Documentation](https://graph-sitter.com)** • **[Community](https://community.codegen.com)**

</div>

