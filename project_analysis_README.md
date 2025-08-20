# Comprehensive Codebase Analysis Tool

A powerful tool for analyzing codebases using graph-sitter, with an interactive web UI for visualizing tree structure, entrypoints, dead code, and issues.

## Features

- **Tree Structure Visualization**: View your codebase's directory structure with embedded issue counts and entrypoints
- **Entry Point Detection**: Identify main functions, classes, and other entry points in your codebase
- **Dead Code Analysis**: Find unused functions, classes, and imports
- **Issue Detection**: Identify code issues like unused parameters, high complexity, and import cycles
- **Interactive Web UI**: Explore analysis results through a user-friendly web interface
- **Command-line Reports**: Generate text reports for integration with other tools

## Installation

1. Make sure you have graph-sitter installed:
   ```
   pip install graph-sitter
   ```

2. Install additional dependencies:
   ```
   pip install flask networkx plotly
   ```

## Usage

### Web UI

Launch the web UI with:

```bash
python project_analysis_full_scope.py --web
```

Then open your browser to http://localhost:5000

You can also analyze a repository directly and view the results in the web UI:

```bash
python project_analysis_full_scope.py --repo username/repo --web
```

### Command-line

Analyze a repository and print the report to stdout:

```bash
python project_analysis_full_scope.py --repo username/repo
```

Save the report to a file:

```bash
python project_analysis_full_scope.py --repo username/repo --output report.txt
```

### Options

- `--repo`, `-r`: Repository path (local) or name (GitHub)
- `--output`, `-o`: Output file for report (default: stdout)
- `--web`, `-w`: Launch web UI
- `--port`, `-p`: Port for web UI (default: 5000)
- `--host`: Host for web UI (default: 0.0.0.0)
- `--language`, `-l`: Programming language (default: auto-detect)

## Examples

Analyze a GitHub repository:

```bash
python project_analysis_full_scope.py --repo fastapi/fastapi
```

Analyze a local repository:

```bash
python project_analysis_full_scope.py --repo /path/to/local/repo
```

Launch web UI with analysis of a repository:

```bash
python project_analysis_full_scope.py --repo django/django --web --port 8080
```

## Output

The tool generates a comprehensive report with:

1. Tree structure with embedded issue counts and entrypoints
2. List of entrypoints with details
3. Dead code items categorized by type
4. Issues categorized by severity

## Web UI Features

The web UI provides an interactive way to explore the analysis results:

- **Tree View**: Navigate the codebase structure with embedded issue counts and entrypoints
- **Entry Points Tab**: View all entry points with details about their functions and inheritance
- **Dead Code Tab**: Explore all dead code items categorized by type
- **Issues Tab**: Browse all issues sorted by severity with detailed context

## Built With

- [graph-sitter](https://graph-sitter.com/) - For codebase analysis
- [Flask](https://flask.palletsprojects.com/) - For the web UI
- [NetworkX](https://networkx.org/) - For graph analysis
- [Plotly](https://plotly.com/) - For visualizations

## License

This project is licensed under the MIT License - see the LICENSE file for details.
