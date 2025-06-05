# Graph-sitter Analysis Module

Comprehensive codebase analysis with interactive dashboard visualizations.

## Overview

The Analysis module extends graph-sitter with powerful analysis capabilities that provide:

- **Comprehensive Issue Detection**: Identifies code quality issues, security vulnerabilities, performance bottlenecks, and architectural problems
- **Interactive HTML Dashboards**: Beautiful, responsive dashboards with filtering and drill-down capabilities  
- **Flexible Visualizations**: Multiple visualization types including dependency graphs, blast radius analysis, complexity heatmaps, and more
- **Health Scoring**: Overall codebase health metrics with actionable recommendations
- **Simple API**: Easy-to-use API that integrates seamlessly with existing workflows

## Quick Start

### Basic Usage

```python
from graph_sitter import Codebase

# Analyze any repository with one line
analysis = Codebase.AnalysisFromPath('fastapi/fastapi')
report = analysis.run_comprehensive_analysis()

# Open interactive dashboard
dashboard_url = analysis.open_dashboard()

# Get health score and issues
health_score = analysis.get_health_score()
issues = analysis.get_issues_summary()
```

### Chained API

```python
from graph_sitter import Codebase

# Chain from existing codebase
codebase = Codebase.from_repo('fastapi/fastapi')
analysis = codebase.Analysis()
report = analysis.run_comprehensive_analysis()
```

### Local Repository Analysis

```python
from graph_sitter import Codebase

# Analyze local repository
analysis = Codebase.AnalysisFromPath('/path/to/repo')
report = analysis.run_comprehensive_analysis()
analysis.open_dashboard()
```

## Features

### 🔍 Issue Detection

Automatically detects:
- **Code Quality**: High complexity functions, long methods, god classes
- **Dead Code**: Unused functions, classes, and imports
- **Dependencies**: Circular dependencies, high coupling
- **Security**: Potential security vulnerabilities and unsafe patterns
- **Performance**: Performance bottlenecks and inefficient code
- **Documentation**: Missing docstrings and documentation issues
- **Architecture**: Architectural violations and design issues

### 📊 Interactive Dashboard

The HTML dashboard provides:
- **Issue Overview**: Categorized by severity and type with filtering
- **Metrics Summary**: Key codebase metrics and health indicators
- **Interactive Charts**: Visual representations of issues and metrics
- **Drill-down Capabilities**: Click through to specific files and functions
- **Responsive Design**: Works on desktop and mobile devices

### 🎨 Visualizations

Multiple visualization types:
- **Dependency Analysis**: Module and package dependencies
- **Call Graph**: Function call relationships
- **Blast Radius**: Impact analysis for specific components
- **Complexity Heatmap**: Visual complexity distribution
- **Class Relationships**: Inheritance and composition diagrams
- **File Structure**: Interactive file tree visualization

### 📈 Health Scoring

Comprehensive health scoring based on:
- Code quality metrics
- Issue severity and frequency
- Test coverage (when available)
- Documentation completeness
- Architectural adherence

## API Reference

### AnalysisOrchestrator

Main orchestrator for comprehensive analysis.

```python
class AnalysisOrchestrator:
    def run_comprehensive_analysis(self, include_visualizations=True, generate_dashboard=True) -> AnalysisReport
    def get_issues_summary(self) -> Dict[str, Any]
    def open_dashboard(self) -> str
    def get_visualization(self, viz_type: str, target: Optional[str] = None) -> Dict[str, Any]
    def export_results(self, output_path: str, format: str = 'json') -> str
    def get_health_score(self) -> float
    def get_recommendations(self) -> List[str]
```

### Visualization Types

Available visualization types:
- `dependency`: Dependency analysis
- `call_graph`: Call graph visualization  
- `blast_radius`: Blast radius analysis (requires target)
- `complexity_heatmap`: Complexity heatmap
- `class_relationships`: Class relationship diagram
- `file_structure`: File structure tree
- `import_graph`: Import dependency graph
- `function_flow`: Function flow diagram (requires target)

### Configuration

Optional configuration parameters:

```python
config = {
    'codebase_id': 'my-project',
    'output_dir': '/path/to/output',
    'analysis_scope': ['src/', 'lib/'],
    'exclude_patterns': ['test/', '*.min.js'],
    'complexity_threshold': 10,
    'enable_security_scan': True
}

analysis = Codebase.AnalysisFromPath('repo', config)
```

## Integration

### Contexten Integration

Perfect for contexten workflows:

```python
from graph_sitter import Codebase

# Simple one-liner for any repository
analysis = Codebase.AnalysisFromPath('owner/repo')
report = analysis.run_comprehensive_analysis()

# Get structured data for further processing
results = {
    'health_score': analysis.get_health_score(),
    'issues': analysis.get_issues_summary(),
    'dashboard_url': analysis.open_dashboard(),
    'recommendations': analysis.get_recommendations()
}
```

### Export Options

Export analysis results in multiple formats:

```python
# Export to JSON
analysis.export_results('report.json', format='json')

# Export to HTML
analysis.export_results('report.html', format='html')

# Export specific visualizations
analysis.visualization_interface.export_visualization(
    'dependency', format='json', output_path='deps.json'
)
```

## Examples

See the `examples/` directory for comprehensive examples:

- `analysis_comprehensive_example.py`: Full feature demonstration
- `contexten_integration_example.py`: Contexten integration patterns

## Architecture

The Analysis module consists of:

- **AnalysisOrchestrator**: Central coordinator for all analysis operations
- **IssueDetector**: Comprehensive issue detection and categorization
- **HTMLDashboardGenerator**: Interactive dashboard generation
- **VisualizationInterface**: Flexible visualization system
- **CodebaseExtension**: Seamless integration with existing Codebase API

## Requirements

- Python 3.8+
- graph-sitter core modules
- Web browser for dashboard viewing

## License

Same as graph-sitter main project.

