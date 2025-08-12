# Comprehensive Codebase Analysis System

A powerful analysis system built on top of the graph-sitter framework that provides detailed codebase insights, error detection, and interactive visualization capabilities.

## 🚀 Features

### Core Analysis Capabilities
- **Comprehensive Code Analysis**: Deep analysis of functions, classes, files, and symbols
- **Error Detection & Classification**: Three-tier severity system (Critical ⚠️, Major 👉, Minor 🔍)
- **Entry Point Detection**: Automatically identifies main functions and high-import files
- **Complexity Metrics**: Halstead complexity analysis and function complexity scoring
- **Dead Code Analysis**: Identifies unused functions and potential cleanup opportunities
- **Dependency Analysis**: Maps relationships between code components

### Visualization & Reporting
- **Directory Tree Visualization**: Interactive tree view with issue counts per directory/file
- **Issue Heatmaps**: Visual representation of problem areas in the codebase
- **Interactive Dashboards**: Web-based dashboards with charts and metrics
- **API Endpoints**: RESTful API for programmatic access to analysis data

### Advanced Features
- **Lazy Graph Parsing**: Efficient analysis of large codebases
- **Multi-language Support**: Built-in support for Python and TypeScript
- **Extensible Architecture**: Easy to add new analysis methods and visualizations
- **Real-time Analysis**: Fast incremental analysis capabilities

## 📁 File Structure

```
├── analysis.py          # Core analysis engine
├── api.py              # REST API server with interactive dashboard
├── visualize.py        # Visualization data generation
├── demo.py             # Comprehensive demo script
└── README_analysis.md  # This documentation
```

## 🔧 Installation & Setup

### Prerequisites
- Python 3.8+
- graph-sitter framework (already installed in this repository)
- Optional: Flask for API server functionality

### Basic Usage

```python
from analysis import load_codebase, analyze_codebase

# Load a codebase
codebase = load_codebase("/path/to/repository")

# Perform comprehensive analysis
results = analyze_codebase(codebase)

# Access results
print(f"Total issues found: {results.summary['total_issues']}")
print(f"Critical issues: {results.summary['critical_issues']}")
```

## 🎯 Quick Start

### 1. Run the Demo
```bash
python demo.py
```

This will analyze the current graph-sitter codebase and display:
- Summary statistics
- Most important functions
- Issues by severity
- Directory tree with issue counts
- Detailed issue listings
- Halstead complexity metrics

### 2. Start the API Server
```bash
python api.py
```

Then visit:
- `http://localhost:5000/` - API documentation
- `http://localhost:5000/analyze/codegen-sh/graph-sitter` - JSON analysis results
- `http://localhost:5000/dashboard/codegen-sh/graph-sitter` - Interactive dashboard

### 3. Programmatic Usage
```python
from analysis import load_codebase, analyze_codebase
from visualize import generate_visualization_data

# Analyze any repository
codebase = load_codebase("/path/to/repo")
results = analyze_codebase(codebase)

# Generate visualization data
viz_data = generate_visualization_data(results)

# Access specific analysis results
for severity, issues in results.issues_by_severity.items():
    print(f"{severity.upper()}: {len(issues)} issues")
    for issue in issues[:3]:  # Show first 3
        print(f"  - {issue}")
```

## 📊 Analysis Output Format

### Summary Statistics
```python
{
    'total_files': 150,
    'total_functions': 800,
    'total_classes': 120,
    'total_issues': 104,
    'critical_issues': 30,
    'major_issues': 39,
    'minor_issues': 35,
    'entry_points': 8
}
```

### Issue Classification
- **Critical ⚠️**: Security vulnerabilities, memory leaks, null pointer dereferences
- **Major 👉**: High complexity functions, classes with too many methods, performance issues
- **Minor 🔍**: Unused functions, style issues, minor code smells

### Directory Tree Format
```
codegen-sh/graph-sitter/
├── 📁 src/ [Total: 20 issues]
│   ├── 📁 graph_sitter/ [Total: 20 issues]
│   │   ├── 📁 core/ [🟩 Entrypoint: 1][⚠️ Critical: 1]
│   │   │   └── 🐍 codebase.py [🟩 Entrypoint: Class: 'Codebase']
│   │   ├── 📁 python/ [⚠️ Critical: 1] [👉 Major: 4] [🔍 Minor: 5]
│   │   │   ├── 🐍 file.py [👉 Major: 4] [🔍 Minor: 3]
│   │   │   └── 🐍 function.py [⚠️ Critical: 1] [🔍 Minor: 2]
```

## 🔍 Analysis Methods

### Function Analysis
- Parameter count validation (flags >7 parameters)
- Return statement analysis
- Function call complexity
- Usage pattern analysis
- Dead code detection

### Class Analysis
- Method count validation (flags >20 methods)
- Inheritance depth analysis
- Attribute complexity
- Design pattern recognition

### File Analysis
- Line count validation (flags >1000 lines)
- Import complexity analysis
- Module dependency mapping
- Entry point detection

### Complexity Metrics
- **Halstead Metrics**: Vocabulary, length, volume, difficulty, effort
- **Cyclomatic Complexity**: Control flow complexity analysis
- **Dependency Complexity**: Inter-module dependency analysis

## 🌐 API Endpoints

### Core Endpoints
- `GET /` - API documentation
- `GET /health` - Health check
- `GET /analyze/<username>/<repo>` - Complete analysis results
- `GET /visualize/<username>/<repo>` - Visualization data
- `GET /dashboard/<username>/<repo>` - Interactive web dashboard

### Example API Response
```json
{
  "repository": "codegen-sh/graph-sitter",
  "analysis_results": {
    "summary": {
      "total_files": 150,
      "total_functions": 800,
      "total_issues": 104
    },
    "most_important_functions": {
      "most_calls": {
        "name": "parse_file",
        "call_count": 45
      }
    },
    "issues_by_severity": {
      "critical": ["⚠️- src/core/parser.py / Function - 'parse' [Memory leak detected]"]
    }
  }
}
```

## 🎨 Visualization Features

### Interactive Dashboard
- Real-time metrics display
- Issue severity distribution charts
- Function complexity scatter plots
- Dependency network graphs
- Halstead metrics visualization

### Data Export
- JSON export for external tools
- CSV export for spreadsheet analysis
- Interactive HTML reports
- PNG/SVG chart exports

## ⚙️ Configuration

### Analysis Configuration
```python
from graph_sitter.configs.models.codebase import CodebaseConfig

config = CodebaseConfig(
    exp_lazy_graph=True,        # Enable lazy loading
    method_usages=True,         # Track method usage
    import_resolution_paths=[   # Custom import paths
        "src/",
        "lib/"
    ]
)

codebase = load_codebase("/path/to/repo", config=config)
```

### Custom Issue Detection
```python
def custom_issue_detector(func):
    """Custom function to detect specific issues"""
    issues = []
    
    # Example: Flag functions with specific naming patterns
    if func.name.startswith('temp_'):
        issues.append(Issue(
            severity=IssueSeverity.MINOR,
            message="Temporary function detected",
            filepath=func.filepath,
            function_name=func.name
        ))
    
    return issues
```

## 🚀 Performance

### Optimization Features
- **Lazy Loading**: Only analyzes code as needed
- **Incremental Analysis**: Updates only changed components
- **Caching**: Intelligent caching of analysis results
- **Parallel Processing**: Multi-threaded analysis for large codebases

### Benchmarks
- **Small Projects** (<1K files): ~5-10 seconds
- **Medium Projects** (1K-10K files): ~30-60 seconds  
- **Large Projects** (>10K files): ~2-5 minutes

## 🔧 Extending the System

### Adding New Analysis Methods
```python
def analyze_custom_patterns(codebase):
    """Add custom analysis logic"""
    issues = []
    
    for func in codebase.functions:
        # Your custom analysis logic here
        if custom_condition(func):
            issues.append(create_issue(func))
    
    return issues
```

### Custom Visualizations
```python
def generate_custom_visualization(analysis_results):
    """Generate custom visualization data"""
    return {
        "custom_chart": {
            "type": "bar",
            "data": extract_custom_data(analysis_results)
        }
    }
```

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**: Ensure graph-sitter is properly installed
2. **Memory Issues**: Use lazy loading for large codebases
3. **Performance**: Enable caching and incremental analysis
4. **API Errors**: Check Flask installation for API functionality

### Debug Mode
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Run analysis with error handling
try:
    results = analyze_codebase(codebase)
except Exception as e:
    print(f"Analysis failed: {e}")
    traceback.print_exc()
```

## 📈 Future Enhancements

### Planned Features
- **Machine Learning Integration**: AI-powered issue detection
- **IDE Plugins**: VS Code and IntelliJ integration
- **CI/CD Integration**: GitHub Actions and Jenkins plugins
- **Multi-language Expansion**: Java, C++, Go support
- **Real-time Monitoring**: Live codebase health monitoring

### Contributing
The analysis system is designed to be extensible. Key areas for contribution:
- New analysis methods
- Additional visualizations
- Performance optimizations
- Language support
- Integration plugins

## 📄 License

This analysis system is part of the graph-sitter project and follows the same licensing terms.

---

**Built with ❤️ using the graph-sitter framework**
