# 🔍 Comprehensive Codebase Analyzer

A unified tool that executes all codebase analysis functions and generates a complete report with 3D visualization capabilities for dead code detection and overall codebase structure analysis.

## Features

### 📊 **Comprehensive Analysis**
- **Basic Statistics**: Files, classes, functions, imports, lines of code
- **Inheritance Analysis**: Class hierarchies and inheritance chains
- **Recursive Functions**: Detection of recursive function calls
- **Test Coverage**: Test functions, classes, and organization
- **Dead Code Detection**: Unused functions and classes with 3D visualization
- **Import Analysis**: Internal vs external imports, dependency relationships
- **Type Coverage**: Parameter, return type, and attribute type annotations

### 🌐 **3D Visualization**
- Interactive 3D visualization of codebase structure
- Dead code highlighted in red on Z-axis
- File size represented by node size
- Color-coded by dead code count

### 📊 **Multiple Output Formats**
- **JSON Report**: Complete structured data
- **HTML Report**: Interactive web-based report with charts
- **Call Graph**: NetworkX graph in GEXF format
- **3D Visualization Data**: Ready for web rendering

## Installation

```bash
# Install dependencies
pip install graph_sitter networkx plotly

# Make the analyzer executable
chmod +x comprehensive_codebase_analyzer.py
```

## Usage

### Command Line Interface

```bash
# Analyze local repository
python comprehensive_codebase_analyzer.py /path/to/repo

# Analyze remote repository
python comprehensive_codebase_analyzer.py https://github.com/user/repo

# Specify custom output directory
python comprehensive_codebase_analyzer.py /path/to/repo custom_output_dir
```

### Python API

```python
from comprehensive_codebase_analyzer import ComprehensiveCodebaseAnalyzer

# Create analyzer
analyzer = ComprehensiveCodebaseAnalyzer("/path/to/repo")

# Run analysis
results = analyzer.run_comprehensive_analysis()

# Save results
analyzer.save_results("output_directory")

# Access specific analysis results
print(f"Dead functions: {results['dead_code']['total_dead_functions']}")
print(f"Type coverage: {results['type_coverage']['parameter_coverage']['percentage']:.1f}%")
```

### Example Usage

```python
# Analyze current repository
python example_usage.py

# Analyze remote FastAPI repository
python example_usage.py remote
```

## Output Structure

```
analysis_output/
├── comprehensive_analysis_report.json    # Complete JSON report
├── analysis_report.html                  # Interactive HTML report
└── call_graph.gexf                      # Call graph for visualization tools
```

## Analysis Components

### 🔍 **Basic Statistics**
```python
{
    "total_files": 150,
    "total_classes": 45,
    "total_functions": 320,
    "total_imports": 180,
    "lines_of_code": 15000
}
```

### 🗑️ **Dead Code Detection**
```python
{
    "total_dead_functions": 12,
    "total_dead_classes": 3,
    "dead_functions": [
        {
            "name": "unused_function",
            "file": "src/utils.py",
            "line": 45,
            "type": "function"
        }
    ]
}
```

### 🌐 **3D Visualization Data**
```python
{
    "nodes": [
        {
            "id": "file_0",
            "label": "src/main.py",
            "type": "file",
            "size": 150,
            "dead_code_count": 2,
            "x": 0, "y": 0, "z": 2,
            "color": "#FF0000"  # Red for dead code
        }
    ],
    "edges": [...],
    "metadata": {
        "total_nodes": 150,
        "dead_code_nodes": 15
    }
}
```

### 🏷️ **Type Coverage**
```python
{
    "parameter_coverage": {
        "percentage": 75.5,
        "typed": 302,
        "total": 400
    },
    "return_type_coverage": {
        "percentage": 68.2,
        "typed": 218,
        "total": 320
    }
}
```

## Advanced Features

### Call Graph Generation
```python
# Generate call graph for specific function
analyzer = ComprehensiveCodebaseAnalyzer("/path/to/repo")
analyzer.load_codebase()
call_graph = analyzer.create_call_graph("main_function")
```

### Custom Analysis
```python
# Access raw codebase for custom analysis
analyzer = ComprehensiveCodebaseAnalyzer("/path/to/repo")
analyzer.load_codebase()

# Custom dead code analysis
for func in analyzer.codebase.functions:
    if len(func.usages) == 0 and func.name.startswith('_'):
        print(f"Private dead function: {func.name}")
```

## Visualization

The HTML report includes:
- **Interactive 3D scatter plot** showing file structure with dead code on Z-axis
- **Bar charts** for dead code distribution
- **Pie charts** for type coverage
- **Responsive design** for mobile and desktop viewing

## Integration

### CI/CD Pipeline
```yaml
- name: Run Codebase Analysis
  run: |
    python comprehensive_codebase_analyzer.py . ci_analysis
    # Upload analysis results as artifacts
```

### Pre-commit Hook
```bash
#!/bin/bash
python comprehensive_codebase_analyzer.py . pre_commit_analysis
if [ $(jq '.dead_code.total_dead_functions' pre_commit_analysis/comprehensive_analysis_report.json) -gt 10 ]; then
    echo "Too much dead code detected!"
    exit 1
fi
```

## Requirements

- Python 3.8+
- graph_sitter
- networkx
- plotly (for HTML visualizations)

## License

This analyzer is part of the graph-sitter project and follows the same license terms.

