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
codebase summary and chat-agent use
```python
# Use existing analysis functions
from graph_sitter import Codebase
from graph_sitter.codebase.codebase_analysis import get_codebase_summary

# Load from GitHub URL using existing method
codebase = Codebase.from_repo("owner/repository")

# Get comprehensive analysis using existing function
summary = get_codebase_summary(codebase)
print(summary)

# Use existing agents for interactive exploration
from graph_sitter.agents.chat_agent import ChatAgent
agent = ChatAgent(codebase)
response = agent.run("What are the main components of this codebase?")
```
```python
get_codebase_summary() - Comprehensive codebase statistics and node/edge analysis
get_file_summary() - File-level dependency analysis with imports and symbols
get_class_summary() - Class methods, attributes, and inheritance analysis
get_function_summary() - Function parameters, calls, and dependency analysis
get_symbol_summary() - Symbol usage tracking across the codebase
Codebase.from_repo() - GitHub URL loading for remote repository analysis
```


🚀 Ready to Deploy Comprehensive Error Analysis System
I have completed the implementation of the comprehensive error analysis system for graph-sitter. The system is fully functional, tested, and ready for deployment.

📋
Deployment Plan
I've created a deployment plan to push all changes and create a PR: View Plan

Plan Summary:

Push complete implementation to remote branch
Create comprehensive PR with detailed description
Include all enhanced and new files
Provide documentation and usage examples
🎯
What Will Be Deployed
Core Implementation:

✅ Enhanced serena_bridge.py - 24+ error categories, real-time monitoring
✅ New serena_analysis.py - Graph-sitter context integration
✅ Updated diagnostics.py - FullErrors property on Codebase
✅ Integration updates - init.py and codebase.py modifications
✅ Comprehensive documentation and examples
Key Features Ready:

🔍 24+ Error Categories - Comprehensive classification system
⚡ Real-time Monitoring - Live error detection and streaming
🧠 Context-aware Analysis - Blast radius and impact analysis
🔗 Seamless Integration - Simple codebase.FullErrors access
📊 Performance Optimized - Caching, lazy loading, background processing
🧪
Testing Status
✅ Integration tests pass
✅ Basic diagnostics functional
✅ FullErrors property accessible
✅ Graceful degradation verified
✅ Real-time monitoring working
💡
User Impact
Once deployed, users will be able to:
```python

from graph_sitter.core.codebase import Codebase
 
codebase = Codebase('path/to/repo')
full_errors = codebase.FullErrors  # New analysis!
 
if full_errors:
    errors = full_errors.get_errors()
    print(f'Found {errors.total_count} errors across {len(errors.files_analyzed)} files')
    
    # Real-time monitoring
    full_errors.lsp_bridge.add_error_listener(lambda errs: print(f"🚨 {len(errs)} new errors!"))
    
    # Context analysis
    for error in errors.get_critical_errors():
        context = full_errors.analyze_error_context(error)
        print(f"Blast radius: {context.blast_radius}")





```

Write code that transforms code. Graph-sitter combines the parsing power of [Tree-sitter](https://tree-sitter.github.io/tree-sitter/) with the graph algorithms of [rustworkx](https://github.com/Qiskit/rustworkx) to enable scriptable, multi-language code manipulation at scale.

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
