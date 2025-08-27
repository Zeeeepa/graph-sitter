# PyStaticCheck - Comprehensive Python Static Code Checker

PyStaticCheck is a unified tool that combines multiple Python static analysis tools into a single interface. It leverages UV for package management and provides a consistent output format across all tools.

## Features

- **Unified Interface**: Run multiple static analysis tools with a single command
- **UV Integration**: Fast package management for tool installation
- **Parallel Execution**: Run tools in parallel for faster analysis
- **Comprehensive Analysis**: Combines the strengths of multiple tools
- **Configurable**: Customize which tools to run and their settings
- **Multiple Output Formats**: Text, JSON, and HTML reports
- **Pre-commit Integration**: Use as a pre-commit hook

## Tools Integrated

PyStaticCheck integrates the following tools:

1. **ruff**: Fast Python linter (includes pyflakes, pycodestyle, mccabe, isort functionality)
2. **mypy**: Static type checker
3. **pylint**: Comprehensive linter
4. **bandit**: Security-focused linter
5. **pyright**: Microsoft's static type checker
6. **vulture**: Dead code detector
7. **dodgy**: Suspicious code pattern detector
8. **pydocstyle**: Docstring style checker
9. **pyroma**: Packaging best practices checker
10. **codespell**: Spell checker for code
11. **biome**: Fast formatter and linter (requires Node.js)
12. **graph_sitter**: Code structure analysis (if available)

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/pystaticcheck.git
cd pystaticcheck

# Install UV if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install the required tools
python pystaticcheck.py --install
```

## Usage

```bash
# Basic usage (runs all tools on the current directory)
python pystaticcheck.py

# Run on a specific directory or file
python pystaticcheck.py path/to/code

# Run only specific tools
python pystaticcheck.py --only ruff,mypy,bandit

# Run tools in parallel
python pystaticcheck.py --parallel

# Apply automatic fixes where possible
python pystaticcheck.py --fix

# Generate a JSON report
python pystaticcheck.py --format json

# Generate an HTML report
python pystaticcheck.py --format html

# Show only a summary of issues
python pystaticcheck.py --summary

# Show verbose output
python pystaticcheck.py --verbose

# Use a custom configuration file
python pystaticcheck.py --config custom_pystaticcheck.toml
```

## Configuration

PyStaticCheck can be configured using a TOML file. By default, it looks for `pystaticcheck.toml` in the current directory.

```toml
# Example configuration (pystaticcheck.toml)
[general]
exclude = ["**/__pycache__/**", "**/venv/**"]

[tools]
# Enable/disable specific tools
ruff = true
mypy = true
pylint = true
# ... other tools

# Tool-specific settings
[tools.ruff]
inherit_project_config = true
line_length = 100
```

See the included `pystaticcheck.toml` for a complete example configuration.

## Pre-commit Integration

Add the following to your `.pre-commit-config.yaml` file:

```yaml
repos:
  - repo: local
    hooks:
      - id: pystaticcheck
        name: PyStaticCheck - Comprehensive Python Static Code Checker
        entry: python pystaticcheck.py
        language: python
        types: [python]
        args: ["--summary", "--only", "ruff,mypy,bandit"]
        pass_filenames: false
```

## Recommended Workflow

For the best experience with PyStaticCheck, we recommend the following workflow:

1. **Initial Setup**:
   - Install all tools with `python pystaticcheck.py --install`
   - Create a custom configuration in `pystaticcheck.toml`

2. **Daily Development**:
   - Run `python pystaticcheck.py --only ruff,mypy --fix` frequently during development
   - This catches common issues and applies automatic fixes

3. **Pre-commit**:
   - Configure pre-commit to run a subset of tools (e.g., ruff, mypy, bandit)
   - This ensures basic quality checks before committing

4. **CI Pipeline**:
   - Run the full suite of tools in your CI pipeline
   - Generate HTML or JSON reports for easier analysis

5. **Code Reviews**:
   - Use the comprehensive reports to guide code reviews
   - Focus on issues that automated tools can't fix

## License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.
