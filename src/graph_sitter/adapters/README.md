# Graph-Sitter Adapters

This directory contains comprehensive adapters for analyzing codebases using tree-sitter, organized into specialized modules:

## 📁 Directory Structure

```
adapters/
├── analysis/           # Analysis-related functionality
│   ├── enhanced_analysis.py    # Enhanced code analysis
│   ├── metrics.py             # Metrics calculation
│   ├── dependency_analyzer.py # Dependency analysis
│   ├── call_graph.py         # Call graph generation
│   ├── dead_code.py          # Dead code detection
│   ├── function_context.py   # Function context analysis
│   └── codemods/             # Code modification tools
├── visualizations/     # Visualization functionality
│   ├── react_visualizations.py    # React-based visualizations
│   └── codebase_visualization.py  # HTML report generation
├── unified_analyzer.py # Main orchestrator
├── database.py        # Database storage
└── codebase_db_adapter.py # Enhanced database adapter
```

## 🔍 Analysis Module

The `analysis/` module contains all code analysis functionality:

### Enhanced Analysis
```python
from graph_sitter.adapters.analysis.enhanced_analysis import analyze_codebase_enhanced

# ... rest of examples ...
```
