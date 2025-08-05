# Advanced Analytics & Codebase Analysis System

This example demonstrates Graph-Sitter's comprehensive analytics system that provides deep insights into code quality, performance, security, and maintainability.

## Features

### 🔍 **Comprehensive Analysis**
- **Complexity Analysis**: Cyclomatic, cognitive, and Halstead complexity metrics
- **Performance Analysis**: Algorithm complexity, bottleneck identification, optimization opportunities
- **Security Analysis**: Vulnerability detection, security best practices validation
- **Dead Code Detection**: Unused functions, variables, imports, and unreachable code
- **Dependency Analysis**: Circular dependencies, coupling metrics, architecture violations

### 📊 **Rich Visualizations**
- Interactive dashboards with Plotly charts
- Severity distribution analysis
- File-level risk assessment
- Trend analysis capabilities
- Export to HTML, JSON, and Markdown

### 🚀 **High Performance**
- Parallel processing with configurable worker threads
- Incremental analysis with caching
- Optimized for large codebases (100K+ lines in under 5 minutes)
- Memory-efficient processing

### 🌐 **REST API**
- Complete HTTP API for all analytics operations
- Job management and status tracking
- Multiple export formats
- Dashboard generation endpoints

## Quick Start

```python
import graph_sitter
from graph_sitter.analytics import AnalyticsEngine, AnalysisConfig

# Load codebase
codebase = graph_sitter.Codebase.from_directory(".")

# Configure analysis
config = AnalysisConfig(
    enable_complexity=True,
    enable_performance=True,
    enable_security=True,
    enable_dead_code=True,
    enable_dependency=True
)

# Run analysis
engine = AnalyticsEngine(config)
report = engine.analyze_codebase(codebase)

print(f"Quality Score: {report.overall_quality_score:.1f}/100")
print(f"Issues Found: {report.total_findings}")
```

## Supported Languages

- **Python** (.py)
- **TypeScript** (.ts, .tsx)
- **JavaScript** (.js, .jsx)
- **Java** (.java)
- **C++** (.cpp, .cc, .cxx)
- **Rust** (.rs)
- **Go** (.go)

## Analysis Types

### Complexity Analysis
- **Cyclomatic Complexity**: Measures code complexity based on control flow
- **Cognitive Complexity**: Human-oriented complexity measurement
- **Halstead Metrics**: Volume, difficulty, and effort calculations
- **Maintainability Index**: Overall maintainability scoring
- **Nesting Depth**: Maximum nesting levels in functions

### Performance Analysis
- **Algorithm Complexity**: Big O notation estimation
- **Nested Loop Detection**: Identifies O(n²) and worse patterns
- **Resource Usage Patterns**: Memory and CPU usage analysis
- **Language-Specific Optimizations**: Framework-specific performance tips
- **Bottleneck Identification**: Performance hotspot detection

### Security Analysis
- **Vulnerability Detection**: SQL injection, XSS, command injection patterns
- **Hardcoded Secrets**: API keys, passwords, tokens in source code
- **Insecure Practices**: Unsafe deserialization, weak crypto, etc.
- **Best Practices Validation**: Authentication, authorization, input validation
- **Dependency Security**: Known vulnerable dependencies

### Dead Code Detection
- **Unused Functions**: Functions with no call sites
- **Unused Classes**: Classes that are never instantiated
- **Unused Imports**: Imports that are never referenced
- **Unreachable Code**: Code after return statements, etc.
- **Orphaned Modules**: Modules with no external dependencies

### Dependency Analysis
- **Circular Dependencies**: Dependency cycles detection
- **Coupling Metrics**: Afferent and efferent coupling
- **Architecture Violations**: Layer dependency violations
- **External Dependencies**: Third-party dependency analysis
- **Dependency Graphs**: Visual dependency relationships

## Configuration Options

```python
config = AnalysisConfig(
    # Analysis types
    enable_complexity=True,
    enable_performance=True,
    enable_security=True,
    enable_dead_code=True,
    enable_dependency=True,
    
    # Performance settings
    max_workers=4,
    timeout_seconds=300,
    incremental=True,
    cache_results=True,
    
    # Language filters
    languages={"python", "typescript", "javascript"},
    
    # File patterns
    include_patterns=["**/*.py", "**/*.ts", "**/*.js"],
    exclude_patterns=["**/node_modules/**", "**/venv/**"],
    
    # Analysis depth
    deep_analysis=False,
    
    # Output settings
    generate_reports=True,
    export_format="json"
)
```

## Dashboard Features

### Overview Section
- Quality score radar chart
- Key metrics cards
- Execution summary
- Analyzer status

### Severity Analysis
- Issue distribution pie charts
- Severity by analyzer breakdown
- Trend analysis (with historical data)

### File Analysis
- File risk scoring
- Top problematic files
- File-level metrics

### Recommendations
- Prioritized action items
- Quick wins identification
- Long-term improvements

## API Endpoints

### Analysis Operations
- `POST /analyze` - Start codebase analysis
- `GET /analyze/{job_id}/status` - Get analysis status
- `GET /analyze/{job_id}/results` - Get analysis results
- `DELETE /analyze/{job_id}` - Delete analysis results

### Results Retrieval
- `GET /analyze/{job_id}/analyzer/{name}` - Get analyzer-specific results
- `GET /analyze/{job_id}/severity/{level}` - Get findings by severity
- `GET /analyze/{job_id}/file/{path}` - Get findings by file

### Visualization & Export
- `GET /analyze/{job_id}/dashboard` - Generate dashboard
- `POST /analyze/{job_id}/export` - Export report
- `GET /analyze/{job_id}/metrics` - Get metrics summary

### Management
- `GET /analyze/jobs` - List all analysis jobs
- `GET /analyzers` - Get supported analyzers

## Example Output

```json
{
  "codebase_name": "my-project",
  "overall_quality_score": 78.5,
  "total_findings": 42,
  "execution_time": 12.34,
  "analysis_results": {
    "complexity": {
      "quality_score": 82.1,
      "findings": [...],
      "metrics": {
        "average_cyclomatic_complexity": 3.2,
        "functions_analyzed": 156,
        "highest_complexity_functions": [...]
      }
    },
    "security": {
      "quality_score": 71.8,
      "findings": [...],
      "metrics": {
        "vulnerabilities_found": 3,
        "vulnerability_types": ["sql_injection", "xss"]
      }
    }
  },
  "recommendations": [
    "Fix 3 SQL injection vulnerabilities using parameterized queries",
    "Reduce complexity in 8 highly complex functions",
    "Remove 12 unused functions to reduce codebase size"
  ]
}
```

## Performance Benchmarks

- **Small Projects** (< 1K lines): < 5 seconds
- **Medium Projects** (1K - 10K lines): 10-30 seconds  
- **Large Projects** (10K - 100K lines): 1-5 minutes
- **Enterprise Projects** (100K+ lines): 3-10 minutes

## Integration Examples

### CI/CD Integration
```yaml
# GitHub Actions example
- name: Run Code Analytics
  run: |
    python -m graph_sitter.analytics.cli analyze . \
      --format json \
      --output analytics-report.json \
      --fail-on-critical
```

### Pre-commit Hook
```python
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: graph-sitter-analytics
        name: Graph-Sitter Analytics
        entry: python -m graph_sitter.analytics.cli
        language: system
        args: ['analyze', '--quick', '--fail-on-high']
```

### IDE Integration
```python
# VS Code extension integration
from graph_sitter.analytics import AnalyticsEngine

def analyze_current_file(file_path):
    codebase = graph_sitter.Codebase.from_file(file_path)
    engine = AnalyticsEngine()
    report = engine.analyze_codebase(codebase)
    return report.get_findings_by_file(file_path)
```

## Advanced Usage

### Custom Analyzers
```python
from graph_sitter.analytics.core.base_analyzer import BaseAnalyzer

class CustomAnalyzer(BaseAnalyzer):
    def __init__(self):
        super().__init__("custom")
        self.supported_languages = {"python"}
    
    def analyze(self, codebase, files):
        result = self.create_result()
        # Custom analysis logic
        return result

# Add to engine
engine.add_analyzer("custom", CustomAnalyzer())
```

### Incremental Analysis
```python
# Enable incremental analysis for faster subsequent runs
config = AnalysisConfig(
    incremental=True,
    cache_results=True
)

# First run - full analysis
report1 = engine.analyze_codebase(codebase)

# Subsequent runs - only analyze changed files
report2 = engine.analyze_codebase(codebase)  # Much faster
```

### Batch Processing
```python
# Analyze multiple codebases
codebases = [
    graph_sitter.Codebase.from_directory("project1"),
    graph_sitter.Codebase.from_directory("project2"),
    graph_sitter.Codebase.from_directory("project3")
]

reports = []
for codebase in codebases:
    report = engine.analyze_codebase(codebase)
    reports.append(report)

# Generate comparative analysis
comparative_dashboard = dashboard.create_comparative_dashboard(reports)
```

## Troubleshooting

### Common Issues

1. **Out of Memory**: Reduce `max_workers` or enable `incremental` analysis
2. **Timeout Errors**: Increase `timeout_seconds` for large codebases
3. **Missing Dependencies**: Install required language parsers
4. **Permission Errors**: Ensure read access to all source files

### Performance Tuning

```python
# For large codebases
config = AnalysisConfig(
    max_workers=8,  # Increase for more CPU cores
    timeout_seconds=600,  # 10 minutes
    incremental=True,
    cache_results=True,
    deep_analysis=False  # Disable for faster analysis
)

# For detailed analysis
config = AnalysisConfig(
    deep_analysis=True,
    max_workers=2,  # Reduce to avoid memory issues
    timeout_seconds=1800  # 30 minutes
)
```

## Contributing

The analytics system is designed to be extensible. You can:

1. **Add New Analyzers**: Implement `BaseAnalyzer` interface
2. **Extend Visualizations**: Add new chart types to `AnalyticsDashboard`
3. **Add Language Support**: Extend language detection and patterns
4. **Improve Performance**: Optimize analysis algorithms

See the [Contributing Guide](../../../CONTRIBUTING.md) for more details.

## License

This analytics system is part of Graph-Sitter and follows the same license terms.

