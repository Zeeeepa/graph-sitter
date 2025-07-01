# Graph-sitter Analysis Module

This module provides comprehensive codebase analysis capabilities following patterns identified from [graph-sitter.com](http://graph-sitter.com) documentation.

## Overview

The analysis module extends the existing graph_sitter functionality with advanced analysis capabilities including:

- **Advanced Code Metrics** - Cyclomatic complexity, maintainability index, technical debt analysis
- **Call Graph Analysis** - Function call relationships, path finding, visualization
- **Dead Code Detection** - Unused functions, classes, imports with confidence scoring
- **Dependency Analysis** - Import resolution, circular dependency detection, hop-through-imports
- **Database Storage** - Persistent storage of analysis results with efficient querying

## Quick Start

```python
from graph_sitter import Codebase
from graph_sitter.analysis import EnhancedCodebaseAnalysis

# Initialize codebase and analysis
codebase = Codebase("./my_project")
analysis = EnhancedCodebaseAnalysis(codebase, db_path="analysis.db")

# Run comprehensive analysis
results = analysis.run_full_analysis(store_in_db=True)

# Get codebase health score
health = analysis.get_codebase_health_score()
print(f"Health Score: {health['overall_health_score']}/100")

# Query specific analysis data
dead_code = analysis.query_analysis_data('dead_code')
complex_functions = analysis.query_analysis_data('complex_functions', min_complexity=10)

# Generate report
report = analysis.generate_analysis_report('markdown')
```

## Module Components

### 1. Enhanced Analysis (`enhanced_analysis.py`)
Main interface for comprehensive codebase analysis.

**Key Features:**
- Full codebase analysis with database storage
- Function context analysis
- Health score calculation
- Analysis data querying
- Report generation

### 2. Code Metrics (`metrics.py`)
Advanced code quality metrics and analysis.

**Key Features:**
- Cyclomatic complexity calculation
- Maintainability index computation
- Function, class, and file-level metrics
- Technical debt analysis
- Documentation coverage analysis

### 3. Call Graph Analysis (`call_graph.py`)
Function call relationship analysis and visualization.

**Key Features:**
- Call graph construction and traversal
- Path finding between functions
- Recursive function detection
- Call chain analysis
- Graph visualization

### 4. Dead Code Detection (`dead_code.py`)
Comprehensive dead code identification and analysis.

**Key Features:**
- Unused function and class detection
- Unused import identification
- Confidence-based scoring
- Safe removal recommendations
- Impact analysis

### 5. Dependency Analysis (`dependency_analyzer.py`)
Import and dependency relationship analysis.

**Key Features:**
- Dependency graph construction
- Circular dependency detection
- Import resolution and hop-through-imports
- Dependency impact analysis
- Import pattern analysis

### 6. Database Storage (`database.py`)
Persistent storage layer for analysis results.

**Key Features:**
- Comprehensive database schema
- Efficient storage and retrieval
- Performance-optimized queries
- Analysis result persistence

## Usage Examples

### Basic Analysis

```python
from graph_sitter import Codebase
from graph_sitter.analysis import CodeMetrics, CallGraphAnalyzer

codebase = Codebase(".")

# Analyze code metrics
metrics = CodeMetrics(codebase)
summary = metrics.get_codebase_summary()
print(f"Total functions: {summary['total_functions']}")
print(f"Dead functions: {summary['dead_functions_count']}")

# Analyze call graph
call_analyzer = CallGraphAnalyzer(codebase)
call_metrics = call_analyzer.get_call_graph_metrics()
print(f"Most called function: {call_metrics.most_called_function}")
```

### Function Analysis

```python
# Analyze specific function
function = codebase.get_function("my_function")
func_metrics = metrics.analyze_function(function)

print(f"Complexity: {func_metrics.cyclomatic_complexity}")
print(f"Maintainability: {func_metrics.maintainability_index}")
print(f"Is recursive: {func_metrics.is_recursive}")
```

### Dead Code Detection

```python
from graph_sitter.analysis import DeadCodeDetector

detector = DeadCodeDetector(codebase)
report = detector.analyze(confidence_threshold=0.7)

print(f"Dead functions: {len(report.dead_functions)}")
print(f"Potential LOC savings: {report.total_potential_loc_savings}")

# Get removal plan
removal_plan = detector.get_removal_plan(report)
for file_path, items in removal_plan.items():
    print(f"{file_path}: {len(items)} items to remove")
```

### Dependency Analysis

```python
from graph_sitter.analysis import DependencyAnalyzer

dep_analyzer = DependencyAnalyzer(codebase)

# Find circular dependencies
circular_deps = dep_analyzer.find_circular_dependencies()
for dep in circular_deps:
    print(f"Circular dependency: {dep.cycle_description}")

# Hop through imports
import_path = dep_analyzer.hop_through_imports("my_symbol", max_hops=5)
print(f"Import path: {' -> '.join(import_path)}")
```

### Database Queries

```python
# Store analysis in database
analysis = EnhancedCodebaseAnalysis(codebase, "analysis.db")
results = analysis.run_full_analysis(store_in_db=True)

# Query stored data
dead_code = analysis.query_analysis_data('dead_code')
complex_funcs = analysis.query_analysis_data('complex_functions', min_complexity=15)
recursive_funcs = analysis.query_analysis_data('recursive_functions')

print(f"Found {len(dead_code)} dead code items")
print(f"Found {len(complex_funcs)} complex functions")
print(f"Found {len(recursive_funcs)} recursive functions")
```

## Database Schema

The analysis module uses a comprehensive SQLite database schema to store analysis results:

### Core Tables
- **codebases** - Codebase-level information and metrics
- **files** - File-level analysis results
- **functions** - Function-level metrics and analysis
- **classes** - Class-level analysis results
- **function_calls** - Function call relationships
- **dependencies** - Symbol dependency relationships
- **imports** - Import analysis results

### Query Examples

```python
from graph_sitter.analysis import AnalysisDatabase

db = AnalysisDatabase("analysis.db")

# Get codebase metrics
metrics = db.get_codebase_metrics(codebase_id=1)

# Find dead code candidates
dead_code = db.get_dead_code_candidates(codebase_id=1)

# Get complex functions
complex_funcs = db.get_complex_functions(codebase_id=1, min_complexity=10)

# Get call graph data
call_data = db.get_call_graph_data(codebase_id=1)
```

## Integration with Existing Code

The analysis module is designed to integrate seamlessly with the existing graph_sitter codebase:

### Extending Existing Analysis

```python
# Enhance existing codebase analysis
from graph_sitter.codebase.codebase_analysis import get_codebase_summary
from graph_sitter.analysis import EnhancedCodebaseAnalysis

# Basic summary (existing)
basic_summary = get_codebase_summary(codebase)

# Enhanced analysis (new)
enhanced_analysis = EnhancedCodebaseAnalysis(codebase)
enhanced_results = enhanced_analysis.run_full_analysis()

# Combined insights
print("Basic summary:", basic_summary)
print("Enhanced insights:", enhanced_results['analysis_insights'])
```

### Backward Compatibility

The module maintains full backward compatibility with existing analysis functions while providing enhanced capabilities:

```python
# Existing analysis still works
from graph_sitter.codebase.codebase_analysis import (
    get_codebase_summary, get_function_summary, get_class_summary
)

# New enhanced analysis provides additional capabilities
from graph_sitter.analysis import EnhancedCodebaseAnalysis
```

## Performance Considerations

### Database Optimization
- Proper indexing on frequently queried columns
- Efficient storage of JSON metadata
- Optimized queries for large codebases

### Memory Management
- Lazy loading of analysis results
- Caching of frequently accessed data
- Efficient graph algorithms for large call graphs

### Scalability
- Incremental analysis capabilities
- Parallel processing for independent analysis tasks
- Configurable analysis depth and scope

## Configuration Options

```python
# Configure analysis behavior
analysis = EnhancedCodebaseAnalysis(
    codebase, 
    db_path="custom_analysis.db"
)

# Configure dead code detection
dead_code_report = detector.analyze(
    include_tests=False,           # Exclude test files
    confidence_threshold=0.8       # Higher confidence threshold
)

# Configure call graph analysis
call_graph = analyzer.build_call_graph()
visualization = analyzer.visualize_call_graph(
    output_file="call_graph.png",
    include_external=False,        # Exclude external calls
    max_nodes=50                   # Limit visualization size
)
```

## Error Handling

The module includes comprehensive error handling:

```python
try:
    analysis = EnhancedCodebaseAnalysis(codebase, "analysis.db")
    results = analysis.run_full_analysis()
except Exception as e:
    print(f"Analysis failed: {e}")
finally:
    analysis.close()  # Ensure database connection is closed
```

## Contributing

When extending the analysis module:

1. **Follow existing patterns** - Use the established class structure and naming conventions
2. **Add comprehensive tests** - Include unit tests for new analysis capabilities
3. **Update documentation** - Add new functions to the catalog and examples
4. **Maintain compatibility** - Ensure new features don't break existing functionality
5. **Consider performance** - Optimize for large codebases and frequent analysis

## See Also

- [Graph-sitter.com Function Catalog](../../docs/graph_sitter_com_function_catalog.md) - Complete catalog of implemented functions
- [Comprehensive Analysis Example](../../examples/comprehensive_analysis_example.py) - Full usage example
- [Database Schema Documentation](database.py) - Detailed database schema information

