# RenderGit: Interactive Dark Mode Codebase Explorer

RenderGit is a powerful tool that flattens a GitHub repository into an interactive HTML page with dark mode support and graph-sitter visualizations for exploring code relationships.

## Features

- **Dark Mode Support**: Toggle between light and dark themes with a single click
- **Interactive Graph Visualizations**: Explore code dependencies and relationships visually
- **Multiple View Options**: Switch between human-readable, graph visualization, and LLM-friendly views
- **Syntax Highlighting**: Beautiful syntax highlighting for all supported file types
- **Responsive Design**: Works well on different screen sizes
- **Search Functionality**: Search for files, functions, and code patterns
- **Zoom and Pan**: Navigate large codebases with ease
- **Code Relationship Analysis**: Visualize dependencies, function calls, and imports

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/rendergit.git

# Install dependencies
pip install pygments markdown networkx
```

## Usage

```bash
# Basic usage
./rendergit.py https://github.com/username/repo

# Specify output file
./rendergit.py https://github.com/username/repo -o output.html

# Set maximum file size to render (in bytes)
./rendergit.py https://github.com/username/repo --max-bytes 100000

# Don't open the HTML file in browser after generation
./rendergit.py https://github.com/username/repo --no-open
```

## Views

### Human View
The default view showing the directory tree, table of contents, and file contents with syntax highlighting.

### Graph View
Interactive visualization of code relationships:
- **Dependency Graph**: Shows dependencies between files based on imports
- **Call Graph**: Shows function call relationships

### LLM View
CXML format text for LLM consumption, making it easy to analyze the codebase with AI tools.

## Requirements

- Python 3.6+
- pygments
- markdown
- networkx
- d3.js (included via CDN)

## License

MIT

## Acknowledgements

This tool is inspired by graph-sitter's visualization capabilities and builds upon them to create a comprehensive codebase exploration experience.
