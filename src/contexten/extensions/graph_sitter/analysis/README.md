# 🚀 Comprehensive Analysis System

**Unified codebase analysis system with graph-sitter integration**

## ⚡ Quick Start

### Python API
```python
from graph_sitter.adapters.analysis import analyze_codebase

# Basic analysis
result = analyze_codebase("/path/to/code")
print(f"Found {result.total_functions} functions")

# Comprehensive analysis
from graph_sitter.adapters.analysis import AnalysisPresets
config = AnalysisPresets.comprehensive()
result = analyze_codebase("/path/to/code", config)

# Save results
result.save_to_file("analysis_results.json")
```

### Command Line
```bash
# Basic analysis
python -m graph_sitter.adapters.analysis.cli /path/to/code

# Comprehensive analysis
python -m graph_sitter.adapters.analysis.cli /path/to/code --comprehensive

# Quick analysis
python -m graph_sitter.adapters.analysis.cli /path/to/code --quick

# Save results
python -m graph_sitter.adapters.analysis.cli /path/to/code --output results.json
```

## 🎯 Features

- **🔧 Enhanced Graph-Sitter Integration** - Advanced codebase analysis
- **🔄 Import Loop Detection** - Find circular dependencies
- **💀 Dead Code Detection** - Identify unused functions and classes
- **📊 Advanced Metrics** - Complexity, maintainability, quality scores
- **🤖 Training Data Generation** - ML model training data
- **⚡ Performance Optimized** - Fast analysis with configurable depth
- **🎛️ Flexible Configuration** - Customizable analysis options

## 📁 Architecture

```
analysis/
├── core/
│   └── engine.py              # Main analysis engine
├── enhanced/
│   └── graph_sitter_integration.py  # Enhanced metrics & analysis
├── modules/                   # Legacy analysis modules (8 modules)
├── cli.py                     # Command-line interface
└── __init__.py               # Unified exports
```

## 🔧 Configuration

```python
from graph_sitter.adapters.analysis import AnalysisConfig

config = AnalysisConfig(
    detect_import_loops=True,      # Find circular imports
    detect_dead_code=True,         # Find unused code
    generate_training_data=False,  # Generate ML training data
    analyze_graph_structure=True,  # Graph analysis
    use_advanced_config=True,      # Use advanced CodebaseConfig
    ignore_external_modules=True,  # Skip external dependencies
    include_source_locations=True  # Include file locations
)
```

## 📊 Analysis Results

```python
result = analyze_codebase("/path/to/code")

# Basic metrics
print(f"Files: {result.total_files}")
print(f"Functions: {result.total_functions}")
print(f"Classes: {result.total_classes}")

# Advanced analysis
print(f"Import loops: {len(result.import_loops)}")
print(f"Dead code items: {len(result.dead_code)}")
print(f"Analysis time: {result.analysis_time:.2f}s")

# Graph metrics
print(f"Graph metrics: {result.graph_metrics}")
```

## 🎛️ Presets

```python
from graph_sitter.adapters.analysis import AnalysisPresets

# Full analysis with all features
config = AnalysisPresets.comprehensive()

# Focus on code quality
config = AnalysisPresets.quality_focused()

# Fast analysis
config = AnalysisPresets.performance()

# Generate ML training data
config = AnalysisPresets.ml_training()
```

## 🚀 Examples

### Find Import Loops
```python
result = analyze_codebase("/path/to/code")
for loop in result.import_loops:
    print(f"Loop: {' -> '.join(loop.files)} ({loop.severity})")
```

### Detect Dead Code
```python
result = analyze_codebase("/path/to/code")
for dead_item in result.dead_code:
    print(f"Dead {dead_item.type}: {dead_item.name} in {dead_item.file_path}")
```

### Enhanced Function Analysis
```python
from graph_sitter.adapters.analysis import analyze_function_enhanced

# Analyze specific function
function = codebase.get_function("my_function")
metrics = analyze_function_enhanced(function)
print(f"Complexity: {metrics.cyclomatic_complexity}")
print(f"Maintainability: {metrics.maintainability_index}")
```

## 🔗 Integration

This system consolidates functionality from:
- `graph_sitter_enhancements.py` - Enhanced analysis functions
- `enhanced_analyzer.py` - Advanced analyzer with CodebaseConfig
- `analyze_codebase_enhanced.py` - Comprehensive analysis tool
- All 8 existing analysis modules

## ⚡ Performance

- **Advanced CodebaseConfig** - Optimized graph-sitter settings
- **Configurable Analysis Depth** - Control analysis scope
- **Lazy Loading** - Load only what's needed
- **Caching** - Reuse computed results
- **Parallel Processing** - Multi-threaded analysis (where applicable)

## 🎯 Use Cases

- **Code Quality Assessment** - Measure maintainability and complexity
- **Refactoring Planning** - Identify problematic code areas
- **Dependency Analysis** - Understand code relationships
- **ML Model Training** - Generate training data for AI models
- **CI/CD Integration** - Automated code quality checks
- **Architecture Review** - Analyze system structure

