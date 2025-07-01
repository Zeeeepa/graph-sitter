# Comprehensive Analysis System

This document describes the comprehensive codebase analysis system that implements all graph-sitter.com capabilities in a unified, powerful analysis framework.

## 🎯 Overview

The comprehensive analysis system provides:

- **Complete Graph-sitter.com Integration**: All documented capabilities from the official documentation
- **Advanced Metrics**: Cyclomatic complexity, maintainability index, cohesion, coupling
- **Call Graph Analysis**: Function relationships, call patterns, recursive detection
- **Dependency Analysis**: Import resolution, circular dependency detection, optimization
- **Dead Code Detection**: Unused functions, classes, imports with safe removal planning
- **AI-Powered Insights**: Natural language queries and intelligent recommendations
- **Database Integration**: Persistent storage and historical analysis tracking
- **Health Scoring**: Comprehensive codebase health assessment

## 🏗️ Architecture

### Core Modules

```
graph_sitter.analysis/
├── metrics.py              # Code quality metrics
├── call_graph.py          # Call graph analysis
├── dependency_analyzer.py # Dependency and import analysis
├── dead_code.py           # Dead code detection
├── enhanced_analysis.py   # Unified analysis engine
├── database.py            # Database integration
└── __init__.py            # Module exports
```

### Integration Flow

```
Codebase → Enhanced Analyzer → Individual Analyzers → Database → Reports
    ↓              ↓                    ↓               ↓         ↓
Static Code → Unified Engine → Specialized Analysis → Storage → Insights
```

## 📊 Metrics Analysis

### Function Metrics

The `MetricsCalculator` provides comprehensive function-level analysis:

```python
from graph_sitter.analysis import analyze_function_metrics

# Analyze a function
function = codebase.get_function("process_data")
metrics = analyze_function_metrics(function)

print(f"Complexity: {metrics.cyclomatic_complexity}")
print(f"Maintainability: {metrics.maintainability_index}")
print(f"Documentation: {metrics.documentation_coverage}")
print(f"Impact Score: {metrics.impact_score}")
```

#### Available Metrics

- **Cyclomatic Complexity**: Decision point counting
- **Maintainability Index**: 0-100 scale maintainability score
- **Documentation Coverage**: Docstring and type annotation coverage
- **Test Coverage Estimate**: Heuristic-based test coverage estimation
- **Impact Score**: Usage-based importance scoring

### Class Metrics

```python
from graph_sitter.analysis import analyze_class_metrics

# Analyze a class
class_def = codebase.get_class("DataProcessor")
metrics = analyze_class_metrics(class_def)

print(f"Cohesion: {metrics.cohesion_score}")
print(f"Coupling: {metrics.coupling_score}")
print(f"Methods: {metrics.method_count}")
print(f"Inheritance Depth: {metrics.inheritance_depth}")
```

#### Class Analysis Features

- **LCOM Cohesion**: Lack of Cohesion of Methods calculation
- **Coupling Analysis**: External dependency measurement
- **Inheritance Analysis**: Depth and relationship tracking
- **Method Categorization**: Public, private, magic method classification

### Codebase Summary

```python
from graph_sitter.analysis import get_codebase_summary

# Get overall metrics
summary = get_codebase_summary(codebase)

print(f"Health Score: {summary.health_score}")
print(f"Technical Debt: {summary.technical_debt_score}")
print(f"Dead Code: {summary.dead_code_percentage}")
```

## 🔄 Call Graph Analysis

### Basic Call Graph

```python
from graph_sitter.analysis import build_call_graph

# Build call graph
call_graph = build_call_graph(codebase)

# Find patterns
most_called = call_graph.find_most_called_function()
recursive_funcs = call_graph.find_recursive_functions()
unused_funcs = call_graph.find_unused_functions()

print(f"Most called: {most_called.name}")
print(f"Recursive functions: {len(recursive_funcs)}")
print(f"Unused functions: {len(unused_funcs)}")
```

### Call Path Analysis

```python
# Find paths between functions
paths = call_graph.find_call_paths("main", "process_data")

for path in paths:
    print(f"Path: {' → '.join([f.name for f in path.path])}")
    print(f"Depth: {path.max_depth}")
```

### Call Patterns

```python
# Analyze call patterns
patterns = call_graph.analyze_call_patterns()

print(f"Average calls per function: {patterns['average_calls_per_function']}")
print(f"Max call depth: {patterns['max_call_depth']}")
print(f"Hub functions: {patterns['hub_functions']}")
```

### Method Chaining

```python
# Analyze method chaining
chains = call_graph.analyze_call_chains()

print(f"Total chains: {chains['total_chains']}")
print(f"Average length: {chains['average_chain_length']}")

longest = chains['longest_chain']
print(f"Longest chain: {longest['chain_length']} calls")
```

## 🔗 Dependency Analysis

### Import Analysis

```python
from graph_sitter.analysis import analyze_imports

# Analyze imports
import_analysis = analyze_imports(codebase)

print(f"Total imports: {import_analysis.total_imports}")
print(f"External: {import_analysis.external_imports}")
print(f"Unused: {import_analysis.unused_imports}")
print(f"Circular: {import_analysis.circular_imports}")
print(f"Complexity: {import_analysis.import_complexity_score}")
```

### Import Resolution

```python
from graph_sitter.analysis import hop_through_imports

# Resolve import chains
for import_stmt in codebase.imports:
    resolved = hop_through_imports(import_stmt)
    print(f"Import: {import_stmt} → {resolved}")
```

### Circular Dependencies

```python
from graph_sitter.analysis import find_circular_dependencies

# Find circular dependencies
circular_deps = find_circular_dependencies(codebase)

for cd in circular_deps:
    print(f"Circular dependency ({cd.severity}):")
    print(f"  Symbols: {[s.name for s in cd.symbols]}")
    print(f"  Description: {cd.description}")
```

### Symbol Dependencies

```python
from graph_sitter.analysis import analyze_symbol_dependencies

# Analyze symbol dependencies
symbol = codebase.get_symbol("DataProcessor")
deps = analyze_symbol_dependencies(symbol)

print(f"Direct dependencies: {deps['direct_dependencies']}")
print(f"Transitive dependencies: {deps['transitive_dependencies']}")
print(f"Reverse dependencies: {deps['reverse_dependencies']}")
print(f"Dependency depth: {deps['dependency_depth']}")
```

## 🗑️ Dead Code Detection

### Basic Dead Code Detection

```python
from graph_sitter.analysis import find_dead_code

# Find dead code
dead_code_items = find_dead_code(codebase)

for item in dead_code_items:
    print(f"Dead {item.type}: {item.symbol.name}")
    print(f"  Reason: {item.reason}")
    print(f"  Confidence: {item.confidence:.1%}")
    print(f"  Safe to remove: {item.safe_to_remove}")
```

### Specific Dead Code Types

```python
from graph_sitter.analysis import find_unused_imports, find_unused_variables

# Find specific types
unused_imports = find_unused_imports(codebase)
unused_variables = find_unused_variables(codebase)

print(f"Unused imports: {len(unused_imports)}")
print(f"Unused variables: {len(unused_variables)}")
```

### Cleanup Planning

```python
from graph_sitter.analysis import get_removal_plan, estimate_cleanup_impact

# Estimate impact
impact = estimate_cleanup_impact(codebase, dead_code_items)
print(f"Lines saved: {impact['estimated_lines_saved']}")
print(f"Files affected: {impact['files_affected']}")
print(f"Risk level: {impact['risk_level']}")

# Get removal plan
plan = get_removal_plan(codebase, dead_code_items)
print(f"Safe items: {len(plan.items)}")
print(f"Removal order: {plan.removal_order}")
print(f"Warnings: {plan.warnings}")
```

## 🚀 Enhanced Analysis

### Full Analysis

```python
from graph_sitter.analysis import run_full_analysis

# Run comprehensive analysis
report = run_full_analysis(codebase, "my-project")

print(f"Health score: {report.health_score}")
print(f"Issues found: {len(report.issues)}")
print(f"Recommendations: {len(report.recommendations)}")
```

### Function Context Analysis

```python
from graph_sitter.analysis import get_function_context_analysis

# Analyze function context
context = get_function_context_analysis(codebase, "process_data")

print(f"Metrics: {context['metrics']}")
print(f"Call graph: {context['call_graph']}")
print(f"Dependencies: {context['dependencies']}")
print(f"Is dead code: {context['is_dead_code']}")
```

### Health Assessment

```python
from graph_sitter.analysis import get_codebase_health_score

# Get health assessment
health = get_codebase_health_score(codebase)

print(f"Overall score: {health['overall_health_score']:.2f}")
print(f"Grade: {health['grade']}")

for component, score in health['component_scores'].items():
    print(f"  {component}: {score:.2f}")
```

### AI-Powered Queries

```python
from graph_sitter.analysis import query_analysis_data

# Query with natural language
result = await query_analysis_data(codebase, "What are the main quality issues?")
print(f"Analysis: {result['analysis']}")

result = await query_analysis_data(codebase, "Which functions need refactoring?")
print(f"Analysis: {result['analysis']}")
```

### Report Generation

```python
from graph_sitter.analysis import generate_analysis_report

# Generate reports
json_report = generate_analysis_report(codebase, 'json')
markdown_report = generate_analysis_report(codebase, 'markdown')

# Save reports
with open('analysis_report.json', 'w') as f:
    f.write(json_report)

with open('analysis_report.md', 'w') as f:
    f.write(markdown_report)
```

## 💾 Database Integration

### Database Setup

```python
from graph_sitter.analysis import create_analysis_database, store_analysis_report

# Create database
db = create_analysis_database("analysis.db")

# Store analysis report
report = run_full_analysis(codebase, "my-project")
report_id = store_analysis_report(report, "analysis.db")
```

### Querying Analysis Data

```python
from graph_sitter.analysis import (
    query_codebase_metrics,
    query_complex_functions,
    export_analysis_data
)

# Query metrics
metrics = query_codebase_metrics("my-project")
print(f"Health score: {metrics['health_score']}")

# Query complex functions
complex_funcs = query_complex_functions("my-project", min_complexity=10)
for func in complex_funcs:
    print(f"{func['name']}: complexity {func['cyclomatic_complexity']}")

# Export data
export_analysis_data("my-project", "analysis_export.json")
```

### Database Schema

The database stores:

- **Codebases**: Basic codebase information and metrics
- **Analysis Reports**: Complete analysis results with timestamps
- **Functions**: Detailed function metrics and properties
- **Classes**: Class metrics and inheritance information
- **Function Calls**: Call graph relationships
- **Dependencies**: Symbol dependency relationships
- **Imports**: Import analysis results
- **Issues**: Detected code issues with severity levels

## 🔧 Advanced Usage

### Custom Analysis Pipeline

```python
from graph_sitter.analysis import EnhancedCodebaseAnalyzer

# Create custom analyzer
analyzer = EnhancedCodebaseAnalyzer(codebase, "custom-analysis")

# Run individual components
metrics = analyzer.metrics_calculator.get_codebase_summary()
call_graph = analyzer.call_graph_analyzer.analyze_call_patterns()
dependencies = analyzer.dependency_analyzer.analyze_imports()
dead_code = analyzer.dead_code_detector.find_dead_code()

# Generate custom report
custom_report = {
    'metrics': metrics,
    'call_patterns': call_graph,
    'import_analysis': dependencies,
    'dead_code_count': len(dead_code)
}
```

### Integration with CI/CD

```python
#!/usr/bin/env python3
"""CI/CD Analysis Script"""

import sys
from graph_sitter import Codebase
from graph_sitter.analysis import run_full_analysis

def main():
    codebase = Codebase(".")
    report = run_full_analysis(codebase, "ci-analysis")
    
    # Check quality gates
    if report.health_score < 0.7:
        print(f"❌ Health score too low: {report.health_score:.2f}")
        sys.exit(1)
    
    critical_issues = [i for i in report.issues if i['severity'] == 'critical']
    if critical_issues:
        print(f"❌ Critical issues found: {len(critical_issues)}")
        sys.exit(1)
    
    print(f"✅ Quality gates passed. Health score: {report.health_score:.2f}")

if __name__ == "__main__":
    main()
```

### Performance Optimization

For large codebases:

```python
# Limit analysis scope
analyzer = EnhancedCodebaseAnalyzer(codebase)

# Analyze only changed files
changed_files = get_changed_files()  # Your implementation
filtered_functions = [
    f for f in codebase.functions 
    if f.filepath in changed_files
]

# Run targeted analysis
for func in filtered_functions:
    metrics = analyzer.metrics_calculator.analyze_function_metrics(func)
    # Process metrics...
```

## 📈 Metrics Reference

### Function Metrics

| Metric | Range | Description |
|--------|-------|-------------|
| Cyclomatic Complexity | 1+ | Number of decision points |
| Maintainability Index | 0-100 | Overall maintainability score |
| Documentation Coverage | 0-1 | Docstring and type annotation coverage |
| Test Coverage Estimate | 0-1 | Estimated test coverage |
| Impact Score | 0+ | Usage-based importance |

### Class Metrics

| Metric | Range | Description |
|--------|-------|-------------|
| Cohesion Score | 0-1 | LCOM-based cohesion measurement |
| Coupling Score | 0-1 | External dependency measurement |
| Inheritance Depth | 0+ | Number of parent classes |
| Method Count | 0+ | Total methods in class |

### Codebase Metrics

| Metric | Range | Description |
|--------|-------|-------------|
| Health Score | 0-1 | Overall codebase health |
| Technical Debt Score | 0-1 | Accumulated technical debt |
| Dead Code Percentage | 0-1 | Percentage of unused code |
| Documentation Coverage | 0-1 | Overall documentation coverage |

## 🎯 Best Practices

### Regular Analysis

1. **Daily Analysis**: Run basic metrics on CI/CD
2. **Weekly Deep Dive**: Full analysis with AI insights
3. **Monthly Review**: Historical trend analysis
4. **Release Analysis**: Comprehensive quality assessment

### Quality Gates

```python
def check_quality_gates(report):
    """Quality gate checks for CI/CD."""
    gates = {
        'health_score': 0.7,
        'max_critical_issues': 0,
        'max_high_issues': 5,
        'min_documentation': 0.6,
        'max_dead_code': 0.1
    }
    
    failures = []
    
    if report.health_score < gates['health_score']:
        failures.append(f"Health score too low: {report.health_score}")
    
    critical_issues = len([i for i in report.issues if i['severity'] == 'critical'])
    if critical_issues > gates['max_critical_issues']:
        failures.append(f"Too many critical issues: {critical_issues}")
    
    # Add more checks...
    
    return failures
```

### Trend Monitoring

```python
def analyze_trends(codebase_id, db_path="analysis.db"):
    """Analyze quality trends over time."""
    db = AnalysisDatabase(db_path)
    history = db.get_analysis_history(codebase_id, limit=30)
    
    # Calculate trends
    health_scores = [h['health_score'] for h in history]
    issue_counts = [h['total_issues'] for h in history]
    
    health_trend = calculate_trend(health_scores)
    issue_trend = calculate_trend(issue_counts)
    
    return {
        'health_trend': health_trend,
        'issue_trend': issue_trend,
        'current_health': health_scores[0] if health_scores else 0,
        'health_change': health_scores[0] - health_scores[-1] if len(health_scores) > 1 else 0
    }
```

## 🔮 Future Enhancements

### Planned Features

1. **Real-time Analysis**: Live code quality monitoring
2. **Machine Learning**: Predictive quality models
3. **Multi-language Support**: TypeScript, JavaScript, Java
4. **Team Analytics**: Developer-specific metrics
5. **Integration Ecosystem**: IDE plugins, dashboard widgets

### Extensibility

The system is designed for extensibility:

```python
class CustomAnalyzer:
    """Custom analyzer example."""
    
    def __init__(self, codebase):
        self.codebase = codebase
    
    def analyze_custom_patterns(self):
        """Implement custom analysis logic."""
        # Your custom analysis here
        pass

# Integrate with enhanced analyzer
analyzer = EnhancedCodebaseAnalyzer(codebase)
analyzer.custom_analyzer = CustomAnalyzer(codebase)
```

This comprehensive analysis system provides a complete foundation for understanding, monitoring, and improving codebase quality using all the capabilities documented in graph-sitter.com.

