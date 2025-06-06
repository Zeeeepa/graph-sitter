# Graph-sitter Analysis Module

A comprehensive codebase analysis system that provides advanced static analysis, visualization, and AI-powered insights for software projects.

## Features

### 🔍 Core Analysis
- **Comprehensive Codebase Analysis**: Deep analysis of code structure, dependencies, and relationships
- **File-level Metrics**: Lines of code, complexity, function/class counts
- **Symbol Analysis**: Detailed analysis of functions, classes, variables, and their usage patterns
- **Dependency Tracking**: Import relationships and dependency graphs

### 🌳 Tree-sitter Integration
- **Advanced Syntax Analysis**: Leverages tree-sitter for precise syntax tree analysis
- **Query Patterns**: Pattern-based code search and analysis
- **Language Support**: Multi-language support with extensible language configurations
- **AST Manipulation**: Advanced abstract syntax tree operations

### 🤖 AI-Powered Analysis
- **Code Quality Assessment**: AI-driven code quality evaluation
- **Improvement Suggestions**: Automated suggestions for code improvements
- **Context-aware Analysis**: Intelligent analysis using function and class context
- **Training Data Generation**: Generate training data for machine learning models

### 📊 Visualization & Reporting
- **Interactive HTML Reports**: Rich, interactive reports with D3.js visualizations
- **Dependency Graphs**: Visual representation of code dependencies
- **Metrics Dashboards**: Comprehensive metrics visualization
- **Multiple Export Formats**: JSON, HTML, and text output formats

### 🔧 Advanced Configuration
- **Graph-sitter Settings**: Full integration with graph-sitter advanced settings
- **Performance Optimization**: Configurable performance and memory settings
- **Feature Toggles**: Enable/disable specific analysis features
- **Custom Configurations**: Predefined configurations for different use cases

## Installation

The analysis module is part of the graph-sitter package. Ensure you have the required dependencies:

```bash
# Core dependencies
pip install graph-sitter

# Optional dependencies for enhanced features
pip install jinja2  # For HTML reporting
pip install tree-sitter  # For tree-sitter integration
```

## Quick Start

### Basic Analysis

```python
from graph_sitter.adapters.analysis import CodebaseAnalyzer

# Create analyzer with default configuration
analyzer = CodebaseAnalyzer()

# Analyze a codebase
result = analyzer.analyze("path/to/your/codebase")

# Print summary
print(f"Files: {result.codebase_summary['nodes']['files']}")
print(f"Functions: {result.codebase_summary['nodes']['functions']}")
print(f"Classes: {result.codebase_summary['nodes']['classes']}")
```

### Comprehensive Analysis

```python
from graph_sitter.adapters.analysis import CodebaseAnalyzer, AnalysisConfig

# Use comprehensive configuration
config = AnalysisConfig.get_comprehensive_config()
analyzer = CodebaseAnalyzer(config)

# Perform comprehensive analysis with all features
result = analyzer.comprehensive_analyze(
    "path/to/your/codebase",
    "analysis_output"
)
```

### Command Line Interface

```bash
# Basic analysis
python -m graph_sitter.adapters.analysis.cli path/to/code

# Quick analysis with JSON output
python -m graph_sitter.adapters.analysis.cli path/to/code --quick --output results.json

# Comprehensive analysis with HTML report
python -m graph_sitter.adapters.analysis.cli path/to/code --comprehensive --html report.html

# Tree-sitter analysis with visualization
python -m graph_sitter.adapters.analysis.cli path/to/code --tree-sitter --visualize --output-dir analysis/
```

## Configuration

### Analysis Configuration

```python
from graph_sitter.adapters.analysis import AnalysisConfig

# Create custom configuration
config = AnalysisConfig()

# Enable specific features
config.enable_tree_sitter = True
config.enable_ai_analysis = True
config.enable_visualization = True
config.enable_dead_code_detection = True

# Configure output formats
config.output_formats = {'json', 'html'}
config.export_visualizations = True

# Performance settings
config.performance.max_files_per_batch = 100
config.performance.enable_parallel_processing = True
```

### Graph-sitter Configuration

```python
from graph_sitter.adapters.analysis import AnalysisConfig

config = AnalysisConfig()

# Enable debug mode
config.graph_sitter.debug = True
config.graph_sitter.verify_graph = True

# Performance optimization
config.graph_sitter.sync_enabled = True
config.graph_sitter.method_usages = True
config.graph_sitter.generics = True

# Import resolution
config.graph_sitter.import_resolution_paths = ["src", "lib"]
config.graph_sitter.py_resolve_syspath = True
```

## Usage Examples

### Dependency Analysis

```python
analyzer = CodebaseAnalyzer()

# Analyze dependencies only
dependencies = analyzer.analyze_dependencies("path/to/code")

# Print dependency relationships
for file, deps in dependencies.items():
    print(f"{file} depends on:")
    for dep in deps:
        print(f"  - {dep}")
```

### Dead Code Detection

```python
analyzer = CodebaseAnalyzer()

# Detect dead code
dead_code = analyzer.detect_dead_code("path/to/code")

# Print dead code items
for item in dead_code:
    print(f"Unused {item['type']}: {item['name']} in {item['location']}")
```

### Test Analysis

```python
analyzer = CodebaseAnalyzer()

# Analyze test coverage and organization
test_analysis = analyzer.analyze_tests("path/to/code")

print(f"Test functions: {len(test_analysis['test_functions'])}")
print(f"Test classes: {len(test_analysis['test_classes'])}")
print(f"Coverage estimate: {test_analysis['coverage_estimate']:.2%}")
```

### HTML Report Generation

```python
analyzer = CodebaseAnalyzer()

# Generate comprehensive HTML report
success = analyzer.export_html(
    "path/to/code",
    "analysis_report.html",
    title="My Project Analysis",
    include_source=True
)

if success:
    print("HTML report generated successfully!")
```

### Tree-sitter Integration

```python
from graph_sitter.adapters.analysis.tree_sitter import QueryEngine

# Setup query engine
query_engine = QueryEngine()
query_engine.setup_language("python")

# Parse file and run queries
tree = query_engine.parse_file("example.py", "python")
functions = query_engine.find_functions(tree, "python")

for func in functions:
    print(f"Function: {func.text} at line {func.start_line}")
```

## Advanced Features

### Custom Analysis Pipeline

```python
from graph_sitter.adapters.analysis import AnalysisOrchestrator

# Create orchestrator
orchestrator = AnalysisOrchestrator()

# Add custom analysis tasks
orchestrator.add_task(
    "custom_analysis",
    my_custom_analysis_function,
    args=(codebase,),
    dependencies=["load_codebase"]
)

# Execute pipeline
results = orchestrator.execute_analysis_pipeline("path/to/code")
```

### AI-Powered Analysis

```python
from graph_sitter.adapters.analysis.ai import CodeAnalyzer

# Enable AI analysis
config = AnalysisConfig()
config.enable_ai_analysis = True
config.ai_max_requests = 200

analyzer = CodebaseAnalyzer(config)
result = analyzer.analyze("path/to/code")

# AI-generated insights will be included in the results
for issue in result.issues:
    if issue.get('source') == 'ai':
        print(f"AI Suggestion: {issue['message']}")
```

## Output Formats

### JSON Output

```json
{
  "timestamp": "2024-01-01 12:00:00",
  "execution_time": 45.2,
  "codebase_summary": {
    "nodes": {
      "files": 150,
      "functions": 1200,
      "classes": 300
    }
  },
  "metrics": {
    "code_quality_score": 85.5,
    "maintainability_index": 78.2
  },
  "issues": [
    {
      "type": "high_complexity",
      "target": "process_data",
      "message": "Function has high complexity",
      "severity": "warning"
    }
  ]
}
```

### HTML Report

The HTML report includes:
- Interactive overview dashboard
- Detailed metrics with charts
- Dependency graph visualization
- Issue tracking and categorization
- File, function, and class analysis tables
- Responsive design with tabbed interface

## Performance Considerations

### Memory Management

```python
config = AnalysisConfig()
config.performance.max_memory_usage_mb = 2048
config.performance.enable_memory_monitoring = True
```

### Parallel Processing

```python
config = AnalysisConfig()
config.performance.enable_parallel_processing = True
config.performance.max_worker_threads = 8
```

### File Filtering

```python
config = AnalysisConfig()
config.include_patterns = ['*.py', '*.js']
config.exclude_patterns = ['node_modules/*', '__pycache__/*']
config.max_file_size_kb = 1024
```

## Troubleshooting

### Common Issues

1. **Memory Issues**: Reduce `max_files_per_batch` or `max_memory_usage_mb`
2. **Slow Performance**: Enable parallel processing and adjust worker threads
3. **Missing Dependencies**: Install optional dependencies for full functionality
4. **Graph-sitter Errors**: Check graph-sitter configuration and language support

### Debug Mode

```python
config = AnalysisConfig.get_debug_config()
analyzer = CodebaseAnalyzer(config)
```

### Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

The analysis module is designed to be extensible. You can:

1. Add new analysis engines
2. Create custom visualization components
3. Implement additional AI analysis features
4. Extend tree-sitter language support

## License

This module is part of the graph-sitter project and follows the same licensing terms.

