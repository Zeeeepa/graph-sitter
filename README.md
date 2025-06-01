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

[Graph-sitter](https://graph-sitter.com) is a comprehensive Python framework for intelligent codebase manipulation, analysis, and autonomous development. It combines the parsing power of [Tree-sitter](https://tree-sitter.github.io/tree-sitter/) with advanced AI capabilities to enable scriptable, multi-language code transformation at scale.

## 🚀 Key Features

### 🔍 **Graph-Sitter Core** - Advanced Code Analysis
```python
from graph_sitter import Codebase

# Build a complete graph connecting functions, classes, imports and their relationships
codebase = Codebase("./")

# Work with code without dealing with syntax trees or parsing
for function in codebase.functions:
    # Comprehensive static analysis for references, dependencies, etc.
    if not function.usages:
        # Auto-handles references and imports to maintain correctness
        function.move_to_file("deprecated.py")
```

### 🤖 **Codegen SDK** - AI-Powered Development
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

### 🎯 **Contexten** - Agentic Orchestrator
Advanced AI agent orchestration with platform integrations:
- **GitHub Integration**: Automated PR reviews, issue management, workflow automation
- **Linear Integration**: Task management, issue tracking, project coordination
- **Slack Integration**: Real-time notifications, chat-based interactions
- **OpenAlpha_Evolve**: Autonomous development capabilities with self-healing architecture

## 📦 Installation and Setup

### Prerequisites
- Python 3.12 - 3.13 (recommended: Python 3.13+)
- macOS, Linux, or Windows (via WSL)
- Git for version control

### Quick Installation

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

### Environment Configuration

Copy `.env.example` to `.env` and configure your settings:

```bash
cp .env.example .env
```

Key configuration sections:
- **Codegen API**: Organization ID and API token
- **Platform Integrations**: GitHub, Linear, Slack tokens
- **Contexten Settings**: AI model configuration, feature flags
- **Performance**: Concurrency limits, cache settings

## 🏗️ Architecture Overview

Graph-sitter consists of three main modules:

### 1. **Graph-Sitter Core** 📊
Advanced code analysis and manipulation engine:
- **Static Analysis**: AST-based parsing with dependency mapping
- **Code Transformation**: Safe refactoring with automatic import updates
- **Multi-language Support**: Python, TypeScript, JavaScript, React
- **Performance Optimized**: Handles codebases with millions of lines

### 2. **Codegen SDK** 🔧
Programmatic interface to AI development agents:
- **Task Automation**: Feature implementation, bug fixes, documentation
- **Workflow Integration**: CI/CD pipeline integration
- **Context-Aware**: Leverages codebase understanding for better results
- **Scalable**: Handles complex, multi-step development tasks

### 3. **Contexten** 🤖
Agentic orchestrator with platform integrations:
- **Multi-Platform**: GitHub, Linear, Slack integrations
- **Autonomous Development**: Self-healing capabilities with OpenAlpha_Evolve
- **Real-time Monitoring**: Progress tracking and error recovery
- **Extensible**: Plugin architecture for custom integrations

## 🚀 Quick Start Examples

### Basic Code Analysis
```python
from graph_sitter import Codebase

# Initialize codebase
codebase = Codebase("./")

# Print overall stats
print(f"📚 Total Classes: {len(codebase.classes)}")
print(f"⚡ Total Functions: {len(codebase.functions)}")
print(f"🔄 Total Imports: {len(codebase.imports)}")

# Find recursive functions
recursive = [f for f in codebase.functions
            if any(call.name == f.name for call in f.function_calls)]
print(f"🔄 Recursive functions: {[f.name for f in recursive]}")
```

### Automated Development with Contexten
```python
from contexten.extensions.contexten_app import ContextenOrchestrator, ContextenConfig

# Configure autonomous features
config = ContextenConfig(
    codegen_org_id="your_org_id",
    codegen_token="your_token",
    linear_enabled=True,
    github_enabled=True,
    slack_enabled=True
)

# Initialize orchestrator
orchestrator = ContextenOrchestrator(config)

# Run autonomous development task
result = await orchestrator.execute_task({
    "type": "feature_implementation",
    "description": "Add user authentication system",
    "requirements": ["JWT tokens", "password hashing", "session management"]
})
```

### OpenAlpha_Evolve Integration
```python
from contexten.extensions.open_evolve.main import TaskManagerAgent
from contexten.extensions.open_evolve.core.interfaces import TaskDefinition

# Define evolutionary task
task = TaskDefinition(
    id="fibonacci_optimization",
    description="Optimize fibonacci calculation for performance",
    function_name_to_evolve="fibonacci",
    input_output_examples=[
        {"input": [0], "output": 0},
        {"input": [1], "output": 1},
        {"input": [10], "output": 55}
    ]
)

# Run autonomous evolution
manager = TaskManagerAgent(task_definition=task)
optimized_programs = await manager.execute()
```

## 🔄 CI/CD Integration

Graph-sitter includes a comprehensive CI/CD pipeline:

### GitHub Actions Workflow
```yaml
# Triggered on: push to develop, PRs to develop, manual dispatch
name: Tests

jobs:
  unit-tests:
    # Parallel execution across 8 groups for speed
    strategy:
      matrix:
        group: [1, 2, 3, 4, 5, 6, 7, 8]
    
  integration-tests:
    # Full integration testing with real codebases
    
  codemod-tests:
    # Large-scale codebase transformation testing
    
  parse-tests:
    # Multi-language parsing validation
```

### Pipeline Stages
1. **Access Control**: Verify contributor permissions
2. **Unit Testing**: Fast, parallel test execution
3. **Integration Testing**: Real-world scenario validation
4. **Codemod Testing**: Large codebase transformation tests
5. **Parse Testing**: Multi-language parsing verification
6. **Coverage Reporting**: Comprehensive test coverage analysis

### Performance Optimizations
- **Parallel Execution**: Tests run across 8 parallel groups
- **Intelligent Caching**: OSS repository caching for faster tests
- **Conditional Execution**: Resource-intensive tests only when needed
- **Timeout Management**: Prevents hanging tests with 15-minute limits

## 🛠️ Advanced Usage

### Safe Code Transformations
```python
# Move all Enum classes to a dedicated file
for cls in codebase.classes:
    if cls.is_subclass_of('Enum'):
        # Graph-sitter automatically:
        # - Updates all imports that reference this class
        # - Maintains the class's dependencies
        # - Preserves comments and decorators
        cls.move_to_file('enums.py')

# Rename a function and all its usages
old_function = codebase.get_function('process_data')
old_function.rename('process_resource')  # Updates all references automatically

# Change a function's signature
handler = codebase.get_function('event_handler')
handler.get_parameter('e').rename('event')  # Automatically updates all call-sites
handler.add_parameter('timeout: int = 30')  # Handles formatting and edge cases
handler.add_return_type('Response | None')
```

### Dead Code Detection and Cleanup
```python
# Find and remove dead code
for func in codebase.functions:
    if len(func.usages) == 0:
        print(f'🗑️ Dead code: {func.name}')
        func.remove()

# Analyze import relationships
file = codebase.get_file('api/endpoints.py')
print("Files that import endpoints.py:")
for import_stmt in file.inbound_imports:
    print(f"  {import_stmt.file.path}")
```

### Advanced Configuration
```python
from graph_sitter import Codebase
from codegen.configs import CodebaseConfig

# Initialize with custom configuration
codebase = Codebase(
    "path/to/repo",
    config=CodebaseConfig(
        verify_graph=True,
        method_usages=False,
        sync_enabled=True,
        generics=False,
        import_resolution_overrides={
          "old_module": "new_module"
        },
        ts_language_engine=True,
        v8_ts_engine=True
    )
)
```

## 🔧 Platform Integrations

### GitHub Integration
- **Automated PR Reviews**: Intelligent code review with suggestions
- **Issue Management**: Automatic issue creation and tracking
- **Workflow Automation**: Custom GitHub Actions integration
- **Branch Management**: Automated branch creation and merging

### Linear Integration
- **Task Synchronization**: Bidirectional sync with Linear issues
- **Project Management**: Automated project tracking and updates
- **Team Coordination**: Real-time status updates and notifications
- **Milestone Tracking**: Progress monitoring and reporting

### Slack Integration
- **Real-time Notifications**: Development progress updates
- **Chat-based Commands**: Interactive development assistance
- **Team Collaboration**: Shared development insights
- **Alert Management**: Error notifications and status updates

## 🧪 Testing and Quality Assurance

### Test Categories
- **Unit Tests**: Fast, isolated component testing
- **Integration Tests**: End-to-end workflow validation
- **Codemod Tests**: Large-scale transformation verification
- **Parse Tests**: Multi-language parsing accuracy

### Quality Metrics
- **Code Coverage**: Comprehensive test coverage reporting
- **Performance Benchmarks**: Execution time and memory usage
- **Static Analysis**: Code quality and security scanning
- **Dependency Auditing**: Security vulnerability detection

## 🚨 Troubleshooting

### Common Issues

**UV Error related to `[[ packages ]]`**
```bash
# Update to latest UV version
uv self update
```

**Module import errors**
```bash
# Reinstall compiled extensions
uv sync --reinstall-package codegen
```

**RecursionError during parsing**
```bash
# Increase recursion limit (Python 3.13 recommended)
python -c "import sys; sys.setrecursionlimit(10000)"
```

**CI/CD Pipeline Failures**
- Check GitHub Actions logs for detailed error information
- Verify all required secrets are configured
- Ensure branch protection rules are properly set

### Debug Commands
```bash
# Validate autonomous setup
python -c "
import asyncio
from contexten.extensions.open_evolve.main import TaskManagerAgent
from contexten.extensions.open_evolve.core.interfaces import TaskDefinition

async def validate():
    task = TaskDefinition(id='test', description='test')
    manager = TaskManagerAgent(task)
    print('Validation complete')

asyncio.run(validate())
"

# Check codebase health
gs health-check

# Analyze performance metrics
gs analyze --performance
```

## 📚 Documentation and Resources

- **[Complete Documentation](https://graph-sitter.com)** - Comprehensive guides and API reference
- **[Getting Started Tutorial](https://graph-sitter.com/introduction/getting-started)** - Step-by-step introduction
- **[API Reference](https://graph-sitter.com/api-reference)** - Detailed API documentation
- **[Examples Repository](./examples/)** - Real-world usage examples
- **[Contributing Guide](CONTRIBUTING.md)** - Development and contribution guidelines

### Community and Support
- **[Slack Community](https://community.codegen.com)** - Get help and share insights
- **[GitHub Issues](https://github.com/codegen-sh/graph-sitter/issues)** - Bug reports and feature requests
- **[Contact Us](https://codegen.com/contact)** - Enterprise support and consulting

## 🌟 Why Graph-sitter?

### Intelligent Automation
Software development is fundamentally programmatic. Graph-sitter enables you to express complex code transformations as programs themselves, with AI-powered assistance for enhanced productivity.

### Battle-tested Reliability
Built from real-world refactors performed on enterprise codebases with millions of lines of code. Handles Python, TypeScript, and React applications with proven reliability.

### AI-Native Architecture
Designed for the age of AI developers. Provides expressive yet precise tools that both humans and AI can use to manipulate code through programmatic interfaces.

### Key Benefits
- **Natural Mental Model**: Write transforms that read like your thought process
- **Automatic Correctness**: No manual import management or AST wrestling
- **Enterprise Scale**: Handle complex codebases with confidence
- **AI Integration**: Built-in support for AI-powered development workflows

## 🏢 Enterprise

For enterprise engagements, custom integrations, and professional support:
- **[Contact Sales](https://codegen.com/contact)** - Discuss enterprise needs
- **[Request Demo](https://codegen.com/request-demo)** - See Graph-sitter in action
- **[Enterprise Documentation](https://graph-sitter.com/enterprise)** - Enterprise-specific features

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for:
- Development environment setup
- Code style guidelines
- Testing requirements
- Pull request process

### Development Setup
```bash
# Clone the repository
git clone https://github.com/codegen-sh/graph-sitter.git
cd graph-sitter

# Install dependencies
uv sync

# Install pre-commit hooks
./install-hooks.sh

# Run tests
uv run pytest
```

## 📄 License

Graph-sitter is licensed under the [Apache 2.0 License](LICENSE). See the license file for details.

---

<div align="center">

**Built with ❤️ by the [Codegen](https://codegen.com) team**

[Website](https://codegen.com) • [Documentation](https://graph-sitter.com) • [Community](https://community.codegen.com) • [Twitter](https://x.com/codegen)

</div>

