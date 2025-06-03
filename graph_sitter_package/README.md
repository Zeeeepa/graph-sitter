# Graph Sitter

A powerful code analysis and manipulation toolkit built on top of Tree-sitter.

## Installation

```bash
cd graph_sitter_package
pip install -e .
```

## Usage

```python
from graph_sitter import Codebase

# Load and analyze a codebase
codebase = Codebase.from_path("/path/to/your/project")

# Perform code analysis and manipulation
for file in codebase.files:
    print(f"File: {file.path}")
    for symbol in file.symbols:
        print(f"  Symbol: {symbol.name}")
```

## CLI Usage

After installation, you can use the `gs` command:

```bash
gs --help
```

## Features

- Code analysis and manipulation
- Tree-sitter based parsing
- Multi-language support
- Semantic code understanding
- Refactoring capabilities
- Code generation tools

