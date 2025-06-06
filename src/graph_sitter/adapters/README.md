# Comprehensive Analysis System

A unified, powerful codebase analysis system that consolidates all analysis capabilities.

## Quick Start

```bash
# Basic analysis
python comprehensive_analysis_system.py /path/to/code

# Comprehensive analysis with HTML report
python comprehensive_analysis_system.py /path/to/code --comprehensive --export-html report.html

# Quality-focused analysis
python comprehensive_analysis_system.py /path/to/code --preset quality

# AST-only analysis (no graph-sitter)
python comprehensive_analysis_system.py /path/to/code --no-graph-sitter
```

## Python API

```python
from comprehensive_analysis_system import analyze_codebase, AnalysisPresets

# Basic analysis
result = analyze_codebase("/path/to/code")
result.print_summary()

# Comprehensive analysis
config = AnalysisPresets.comprehensive()
result = analyze_codebase("/path/to/code", config)

# Export results
result.save_to_file("analysis.json", "json")
result.save_to_file("report.html", "html")
```

## Features

- ✅ Core quality metrics (maintainability, complexity, Halstead)
- ✅ Advanced pattern detection and code smell analysis
- ✅ Import loop detection and circular dependency analysis
- ✅ Dead code detection using usage analysis
- ✅ Graph-sitter integration (when available)
- ✅ Training data generation for ML models
- ✅ Multiple output formats (JSON, HTML, text)
- ✅ Comprehensive CLI interface

## Consolidated From

This system consolidates functionality from:
- `analyze_codebase_enhanced.py`
- `enhanced_analyzer.py`
- `graph_sitter_enhancements.py`

Based on successful methodologies from PRs #211-216.
