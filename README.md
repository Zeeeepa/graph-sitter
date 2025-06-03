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

[Graph-sitter](https://graph-sitter.com) is a python library for manipulating codebases.

```python
from graph_sitter import Codebase
from codegen.agents.agent import Agent
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

Write code that transforms code. Graph-sitter combines the parsing power of [Tree-sitter](https://tree-sitter.github.io/tree-sitter/) with the graph algorithms of [rustworkx](https://github.com/Qiskit/rustworkx) to enable scriptable, multi-language code manipulation at scale.

## Installation

Install both `graph_sitter` and `contexten` packages from the project root:

```bash
pip install -e .
```

This will install both packages with all their dependencies and CLI tools:
- `gs` - Graph Sitter CLI for code analysis
- `contexten` - Contexten agent CLI
- `contexten-dashboard` - Contexten dashboard interface

## Separate Package Installation

This project contains two main packages that can be installed separately:

### 🔧 Graph Sitter (Code Analysis SDK)
Core code analysis and manipulation toolkit built on Tree-sitter.

```bash
cd graph_sitter_package
pip install -e .
```

**CLI Usage:**
```bash
gs --help
```

**Python Usage:**
```python
from graph_sitter import Codebase
codebase = Codebase.from_path("/path/to/your/project")
```

### 🤖 Contexten (Agentic Orchestrator)
Intelligent agent orchestration framework with chat capabilities and integrations.

```bash
cd contexten_package
pip install -e .
```

**CLI Usage:**
```bash
contexten --help
contexten-dashboard  # Launch interactive dashboard
```

**Python Usage:**
```python
from contexten import FlowManager
flow_manager = FlowManager()
```

### ��� Install Both Packages
To install both packages at once:

```bash
./install_packages.sh
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

---

## 🚀 Enhanced Agent Integration

Graph-Sitter now includes enhanced **ChatAgent** and **CodeAgent** with seamless [Codegen SDK](https://codegen.com) integration:

### Key Features
- **Automatic SDK Detection**: Agents automatically detect and use Codegen SDK when credentials are available
- **Intelligent Fallback**: Falls back to local LangChain agents when SDK is unavailable
- **Unified Interface**: Same API works for both local and remote agents
- **Enhanced Context**: Codegen SDK agents receive enhanced prompts with codebase context

### Quick Setup

1. **Install Codegen SDK** (optional but recommended):
   ```bash
   pip install codegen
   ```

2. **Configure Environment Variables**:
   ```bash
   export CODEGEN_ORG_ID="your_organization_id_here"
   export CODEGEN_TOKEN="your_api_token_here"
   ```

3. **Use Enhanced Agents**:
   ```python
   from graph_sitter import Codebase
   from contexten.agents.chat_agent import ChatAgent
   from contexten.agents.code_agent import CodeAgent

   codebase = Codebase("path/to/your/project")
   
   # Auto-detects Codegen SDK configuration
   chat_agent = ChatAgent(codebase)
   code_agent = CodeAgent(codebase)
   
   # Chat with your codebase
   response = chat_agent.run("Explain the main components of this project")
   
   # Request code changes
   result = code_agent.run("Add input validation to the login function")
   ```

### Configuration Options

```python
# Force Codegen SDK usage
agent = ChatAgent(codebase, use_codegen_sdk=True)

# Force local-only mode
agent = ChatAgent(codebase, use_codegen_sdk=False)

# Check configuration status
from contexten.agents.codegen_config import print_codegen_status
print_codegen_status()
```

See the [examples/codegen_sdk_integration_demo.py](examples/codegen_sdk_integration_demo.py) for complete usage examples.
