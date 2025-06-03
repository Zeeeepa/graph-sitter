# Graph-Sitter Adapters: Comprehensive Codebase Analysis

This directory contains a comprehensive suite of adapters for analyzing codebases with full comprehension, interactive reporting, and advanced insights.

## 🎯 Overview

The adapters provide:
- **Function context analysis** with dependency tracking and issue detection
- **Interactive visualizations** with dependency graphs, call graphs, and complexity heatmaps
- **Training data generation** for ML applications and code embeddings
- **Comprehensive analysis** integrating all components for complete codebase understanding
- **Database storage** for historical analysis and querying

## 📁 Components

### Core Analysis Adapters

| Adapter | Purpose | Key Features |
|---------|---------|--------------|
| `enhanced_analysis.py` | Comprehensive analysis coordinator | Integrates all analysis types, generates reports |
| `metrics.py` | Code quality metrics | Complexity, maintainability, documentation coverage |
| `dependency_analyzer.py` | Import and dependency analysis | Circular dependencies, import patterns |
| `dead_code.py` | Unused code detection | Cleanup plans, impact assessment |
| `call_graph.py` | Function call relationships | Call patterns, graph analysis |
| `database.py` | Analysis result storage | Schema management, querying |
| `codebase_db_adapter.py` | Database operations | Cross-database compatibility |

### Enhanced Components (New)

| Component | Purpose | Key Features |
|-----------|---------|--------------|
| `function_context.py` | Function context analysis | Dependency tracking, issue detection, training data |
| `codebase_visualization.py` | Interactive visualizations | HTML reports, graphs, heatmaps |
| `unified_analyzer.py` | Unified analysis orchestrator | Integrates all components, comprehensive reporting |

## 🚀 Quick Start

### 1. Basic Function Context Analysis

```python
from graph_sitter.core.codebase import Codebase
from graph_sitter.adapters.function_context import get_function_context, get_enhanced_function_context

# Load codebase
codebase = Codebase.from_directory("path/to/your/project")

# Analyze a specific function
function = codebase.get_function("your_function_name")

# Get basic context (dependencies, usages, metrics)
context = get_function_context(function)
print(f"Dependencies: {len(context['dependencies'])}")
print(f"Usages: {len(context['usages'])}")
print(f"Complexity: {context['metrics']['complexity_estimate']}")

# Get enhanced context with issue detection
enhanced_context = get_enhanced_function_context(function)
print(f"Risk Level: {enhanced_context.risk_level}")
print(f"Issues: {len(enhanced_context.issues)}")
print(f"Recommendations: {enhanced_context.recommendations}")
```

### 2. Generate Training Data for ML

```python
from graph_sitter.adapters.function_context import analyze_codebase_functions

# Generate comprehensive training data
summary = analyze_codebase_functions(codebase, "training_data.json")
print(f"Generated {summary['training_examples']} training examples")
```

### 3. Create Interactive Visualizations

```python
from graph_sitter.adapters.codebase_visualization import create_comprehensive_visualization

# Create interactive HTML report with visualizations
report = create_comprehensive_visualization(codebase, "analysis_output")
print(f"Interactive report saved to: analysis_output/interactive_report.html")
```

### 4. Run Comprehensive Analysis

```python
from graph_sitter.adapters.unified_analyzer import analyze_codebase_comprehensive

# Run complete analysis with all components
results = analyze_codebase_comprehensive(codebase, "my_project", "output_dir")

print(f"Health Score: {results.health_score:.2f}")
print(f"Risk Level: {results.risk_assessment['level']}")
print(f"Functions Analyzed: {len(results.function_contexts)}")
print(f"Issues Found: {sum(len(fc.issues) for fc in results.function_contexts)}")

# Export summary report
analyzer = UnifiedCodebaseAnalyzer(codebase)
analyzer.analysis_results = results
summary_file = analyzer.export_summary_report("summary.md")
```

## 🔍 Function Context Analysis

The function context system provides comprehensive understanding of each function:

### Basic Context Structure

```python
{
    "implementation": {
        "source": "def process_data(input: str) -> dict: ...",
        "filepath": "src/data_processor.py",
        "name": "process_data",
        "parameters": ["input"],
        "return_type": "dict"
    },
    "dependencies": [
        {
            "source": "def validate_input(data: str) -> bool: ...",
            "filepath": "src/validators.py",
            "name": "validate_input"
        }
    ],
    "usages": [
        {
            "source": "result = process_data(user_input)",
            "filepath": "src/api.py"
        }
    ],
    "metrics": {
        "line_count": 15,
        "complexity_estimate": 3,
        "dependency_count": 2,
        "usage_count": 5
    }
}
```

### Enhanced Context with Issues

```python
enhanced_context = get_enhanced_function_context(function)

# Access issue detection
for issue in enhanced_context.issues:
    print(f"{issue['severity']}: {issue['message']}")
    print(f"Recommendation: {issue['recommendation']}")

# Access risk assessment
print(f"Risk Level: {enhanced_context.risk_level}")
print(f"Impact Score: {enhanced_context.impact_score}")
```

## 📊 Interactive Visualizations

The visualization system creates comprehensive HTML reports with:

### Dependency Graphs
- Function dependency relationships
- File-based clustering
- Risk level color coding
- Interactive exploration

### Call Graphs
- Function call relationships
- Call pattern analysis
- Complexity visualization

### Complexity Heatmaps
- Function complexity distribution
- File-based grouping
- Risk assessment integration

### Issue Dashboards
- Issue type distribution
- Severity analysis
- Function-specific issues

## 🤖 Training Data Generation

Generate structured training data for ML applications:

### Masked Function Prediction
```python
from graph_sitter.adapters.function_context import create_training_example

# Create training example for function prediction
training_example = create_training_example(function_context)
# Returns: {"context": {...}, "target": {...}}
```

### Code Embeddings
- Function dependency vectors
- Usage pattern embeddings
- Complexity feature vectors

### Usage Pattern Learning
- Common dependency patterns
- Function usage contexts
- Code structure relationships

## 🗄️ Database Integration

Store and query analysis results:

```python
from graph_sitter.adapters.database import AnalysisDatabase
from graph_sitter.adapters.codebase_db_adapter import CodebaseDbAdapter

# Initialize database
db = AnalysisDatabase("analysis.db")
adapter = CodebaseDbAdapter(db)

# Store analysis results
adapter.store_analysis_result(analysis_report)

# Query historical data
historical = adapter.get_historical_analysis("codebase_id", days_back=30)
```

## 🎛️ Configuration

### Analysis Profiles

Create custom analysis configurations:

```python
from graph_sitter.adapters.unified_analyzer import UnifiedCodebaseAnalyzer

analyzer = UnifiedCodebaseAnalyzer(codebase)

# Run with specific options
results = analyzer.run_comprehensive_analysis(
    save_to_db=True,
    generate_training_data=True,
    create_visualizations=True
)
```

### Output Customization

Control output formats and locations:

```python
# Custom output directory
results = analyze_codebase_comprehensive(
    codebase, 
    codebase_id="my_project",
    output_dir="custom_analysis_output"
)

# Export specific formats
analyzer.export_summary_report("custom_summary.md")
```

## 🔧 Advanced Usage

### Issue Detection Customization

Extend issue detection for specific patterns:

```python
from graph_sitter.adapters.function_context import analyze_function_issues

# Custom issue analysis
def custom_issue_detector(function, context):
    issues = analyze_function_issues(function, context)
    
    # Add custom checks
    if "password" in function.name.lower() and not context["implementation"].get("docstring"):
        issues.append({
            "type": "security_documentation",
            "severity": "warning",
            "message": "Security-related function lacks documentation",
            "recommendation": "Add comprehensive docstring for security functions"
        })
    
    return issues
```

### Visualization Customization

Create custom visualizations:

```python
from graph_sitter.adapters.codebase_visualization import CodebaseVisualizer

visualizer = CodebaseVisualizer(codebase, "custom_output")

# Access visualization data
dependency_graph = visualizer._create_dependency_visualization()
call_graph = visualizer._create_call_graph_visualization()

# Custom processing
for node in dependency_graph.nodes:
    if node["risk_level"] == "high":
        print(f"High-risk function: {node['label']}")
```

## 📈 Performance Considerations

### Large Codebases

For large codebases, consider:

```python
# Limit function analysis for performance
analyzer = UnifiedCodebaseAnalyzer(codebase)

# Process in batches
functions = list(codebase.functions)
batch_size = 100

for i in range(0, len(functions), batch_size):
    batch = functions[i:i+batch_size]
    # Process batch...
```

### Incremental Analysis

Use database storage for incremental updates:

```python
# Check for existing analysis
existing = adapter.get_historical_analysis("codebase_id", days_back=1)

if not existing:
    # Run full analysis
    results = analyzer.run_comprehensive_analysis()
else:
    # Run incremental analysis
    # (Implementation depends on specific needs)
```

## 🧪 Testing

Run the comprehensive example:

```bash
cd examples
python comprehensive_codebase_analysis.py
```

This will demonstrate all features and generate example outputs.

## 📚 Examples

See `examples/comprehensive_codebase_analysis.py` for a complete demonstration of all features.

## 🤝 Contributing

When adding new analysis capabilities:

1. Follow the existing adapter patterns
2. Add comprehensive docstrings
3. Include error handling
4. Add to the unified analyzer
5. Update visualization components
6. Add examples and tests

## 📄 License

Same as the main graph-sitter project.

