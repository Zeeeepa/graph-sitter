# Graph-sitter Adapters

This directory contains adapters and integrations for the graph-sitter analysis system.

## Analysis Module Consolidation

**Note**: The analysis functionality has been consolidated into a single comprehensive tool:

- **Main Analysis Tool**: `analyze_codebase.py` (in project root)
- **Features**: All analysis capabilities including tree-sitter integration, visualization, and comprehensive reporting

### Previous Structure (Removed)
- `analysis/analysis.py` - Redundant analysis module (removed for clarity)

### Current Structure
- All analysis functionality is now in the main `analyze_codebase.py` file
- This provides a single source of truth for all analysis capabilities
- Includes tree-sitter query patterns, visualization, and comprehensive reporting

## Usage

```bash
# Basic analysis
python analyze_codebase.py path/to/code

# With tree-sitter features
python analyze_codebase.py . --tree-sitter --visualize

# Export HTML visualization
python analyze_codebase.py . --export-html analysis.html

# Comprehensive analysis with all features
python analyze_codebase.py . --comprehensive --tree-sitter --export-html report.html
```

## Features

- **Tree-sitter Integration**: Advanced syntax tree analysis
- **Query Patterns**: Pattern-based code search and analysis
- **Visualization**: Interactive HTML reports with D3.js
- **Comprehensive Metrics**: Quality, complexity, and maintainability analysis
- **Multiple Export Formats**: JSON, HTML, and text output

All functionality is based on: https://graph-sitter.com/tutorials/at-a-glance

