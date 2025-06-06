# Graph-sitter Adapters

This directory contains adapters and integrations for the graph-sitter analysis system.

## Analysis Module

**🚀 NEW: Comprehensive Analysis Framework**

The analysis functionality has been completely redesigned and consolidated into a powerful, modular analysis framework located in `analysis/`:

### Key Features
- **Advanced Configuration**: Full integration with graph-sitter advanced settings
- **Tree-sitter Integration**: Advanced syntax tree analysis and query patterns  
- **AI-Powered Analysis**: Automated code analysis and improvement suggestions
- **Interactive Visualization**: Rich HTML reports with D3.js visualizations
- **Comprehensive Metrics**: Quality, complexity, and maintainability analysis
- **Dependency Tracking**: Import relationships and dead code detection
- **Multi-format Output**: JSON, HTML, and text export formats

### Quick Start

```bash
# Basic analysis
python -m graph_sitter.adapters.analysis.cli path/to/code

# Comprehensive analysis with HTML report
python -m graph_sitter.adapters.analysis.cli path/to/code --comprehensive --html report.html

# Tree-sitter analysis with visualization
python -m graph_sitter.adapters.analysis.cli path/to/code --tree-sitter --visualize --output-dir analysis/
```

### Programmatic Usage

```python
from graph_sitter.adapters.analysis import CodebaseAnalyzer, AnalysisConfig

# Create analyzer with comprehensive configuration
config = AnalysisConfig.get_comprehensive_config()
analyzer = CodebaseAnalyzer(config)

# Perform analysis
result = analyzer.analyze("path/to/code", output_dir="analysis_results")

# Export HTML report
analyzer.export_html("path/to/code", "report.html", include_source=True)
```

## Previous Structure (Deprecated)

The following files have been superseded by the new analysis framework:
- ~~`analyze_codebase.py`~~ → Use `analysis/` module
- ~~`analyze_codebase_enhanced.py`~~ → Use `analysis/` module

## Migration Guide

### From analyze_codebase.py

**Old:**
```python
# Direct script execution
python analyze_codebase.py path/to/code --comprehensive --visualize
```

**New:**
```python
# CLI interface
python -m graph_sitter.adapters.analysis.cli path/to/code --comprehensive --visualize

# Or programmatic interface
from graph_sitter.adapters.analysis import CodebaseAnalyzer
analyzer = CodebaseAnalyzer()
result = analyzer.comprehensive_analyze("path/to/code", "output_dir")
```

### Configuration Migration

**Old:**
```python
# Limited configuration options
```

**New:**
```python
from graph_sitter.adapters.analysis import AnalysisConfig

# Comprehensive configuration
config = AnalysisConfig()
config.enable_tree_sitter = True
config.enable_ai_analysis = True
config.enable_visualization = True
config.graph_sitter.debug = True
config.performance.max_worker_threads = 8
```

## Architecture Overview

```
analysis/
├── __init__.py              # Main module exports
├── README.md               # Detailed documentation
├── analyzer.py             # Main analysis interface
├── cli.py                  # Command-line interface
├── orchestrator.py         # Task orchestration
├── config/                 # Configuration management
│   ├── analysis_config.py  # Main analysis configuration
│   ├── graph_sitter_config.py  # Graph-sitter settings
│   └── performance_config.py   # Performance optimization
├── core/                   # Core analysis engine
│   ├── analysis_engine.py  # Main analysis engine
│   └── codebase_analyzer.py    # High-level analyzer
├── tree_sitter/           # Tree-sitter integration
│   ├── query_engine.py     # Query pattern engine
│   ├── syntax_analyzer.py  # Syntax analysis
│   ├── pattern_matcher.py  # Pattern matching
│   └── ast_manipulator.py  # AST manipulation
├── visualization/          # Visualization and reporting
│   ├── html_reporter.py    # HTML report generation
│   ├── d3_visualizer.py    # D3.js visualizations
│   ├── graph_renderer.py   # Graph rendering
│   └── templates/          # HTML templates
├── ai/                     # AI-powered analysis
│   ├── code_analyzer.py    # AI code analysis
│   ├── context_gatherer.py # Context gathering
│   ├── improvement_suggester.py # Improvement suggestions
│   └── training_data_generator.py # Training data
├── metrics/                # Metrics collection
│   ├── quality_metrics.py  # Quality metrics
│   ├── complexity_analyzer.py # Complexity analysis
│   ├── maintainability_scorer.py # Maintainability
│   └── test_analyzer.py    # Test analysis
├── tools/                  # Specialized analysis tools
│   ├── dependency_tracker.py # Dependency analysis
│   ├── dead_code_detector.py # Dead code detection
│   ├── import_analyzer.py  # Import analysis
│   ├── hierarchy_explorer.py # Class hierarchies
│   └── test_organizer.py   # Test organization
└── utils/                  # Utility functions
```

## Features Based on README.md Requirements

All features from the original README.md have been implemented and enhanced:

✅ **Tree-sitter Integration**: Advanced syntax tree analysis with query patterns  
✅ **Visualization**: Interactive HTML reports with D3.js  
✅ **Comprehensive Metrics**: Quality, complexity, and maintainability analysis  
✅ **AI Integration**: Automated analysis and improvement suggestions  
✅ **Multiple Export Formats**: JSON, HTML, and text output  
✅ **Advanced Configuration**: Full graph-sitter settings integration  
✅ **Dependency Analysis**: Import relationships and dependency graphs  
✅ **Dead Code Detection**: Automated detection of unused code  
✅ **Test Analysis**: Test coverage and organization analysis  
✅ **Performance Optimization**: Parallel processing and memory management  

## Advanced Graph-sitter Settings Integration

The new analysis framework fully integrates with graph-sitter advanced settings from https://graph-sitter.com/introduction/advanced-settings:

```python
from graph_sitter.adapters.analysis import AnalysisConfig

config = AnalysisConfig()

# Debug and development
config.graph_sitter.debug = True
config.graph_sitter.verify_graph = True
config.graph_sitter.track_graph = True

# Performance optimization  
config.graph_sitter.sync_enabled = True
config.graph_sitter.method_usages = True
config.graph_sitter.generics = True
config.graph_sitter.exp_lazy_graph = True

# Import resolution
config.graph_sitter.import_resolution_paths = ["src", "lib"]
config.graph_sitter.py_resolve_syspath = True

# TypeScript support
config.graph_sitter.ts_language_engine = True
config.graph_sitter.ts_dependency_manager = True
```

For detailed documentation, see [analysis/README.md](analysis/README.md).

## Legacy Support

The original analysis files are preserved for compatibility but are deprecated:
- `analyze_codebase.py` - Use `analysis/` module instead
- `analyze_codebase_enhanced.py` - Use `analysis/` module instead

## Codemods

The `codemods/` directory contains various code transformation tools and remains unchanged.

