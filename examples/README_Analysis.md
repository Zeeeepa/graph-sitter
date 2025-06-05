# Graph-Sitter Analysis Feature

The Graph-Sitter Analysis feature provides comprehensive codebase analysis with full-context understanding, issue detection, and interactive reporting capabilities.

## Quick Start

```python
from graph_sitter import Codebase

# Analyze a local repository
codebase = Codebase("path/to/your/repo")
result = codebase.Analysis(output_dir="analysis_output")

# Or analyze a remote repository
codebase = Codebase.from_repo("owner/repository")
result = codebase.Analysis(output_dir="remote_analysis")
```

## Features

### 🔍 Comprehensive Analysis
- **Function-level analysis** with complexity metrics and risk assessment
- **Dependency analysis** including circular dependency detection
- **Dead code detection** to identify unused functions and classes
- **Call graph analysis** for understanding code relationships
- **Issue detection** with severity levels and recommendations

### 📊 Rich Reporting
- **JSON reports** with structured analysis data
- **HTML dashboards** (coming soon) with interactive visualizations
- **Health scoring** for overall codebase quality assessment
- **Actionable recommendations** for code improvements

### 🎯 Use Cases
- **Code quality assessment** before releases
- **Technical debt identification** and prioritization
- **Refactoring planning** with impact analysis
- **Onboarding assistance** for new team members
- **Architecture review** and documentation

## Analysis Output

The analysis generates several output files:

### 1. Enhanced Analysis (`enhanced_analysis.json`)
Contains comprehensive metrics and insights:
```json
{
  "codebase_id": "unique-identifier",
  "timestamp": "2025-06-05T14:00:00Z",
  "health_score": 0.85,
  "summary": {
    "total_functions": 42,
    "total_classes": 8,
    "total_files": 15
  },
  "issues": [...],
  "recommendations": [...],
  "metrics": {...}
}
```

### 2. Function Contexts (`function_contexts.json`)
Detailed analysis of each function:
```json
[
  {
    "name": "calculate_total",
    "filepath": "src/utils.py",
    "complexity_metrics": {
      "complexity_estimate": 5,
      "lines_of_code": 12
    },
    "risk_level": "low",
    "issues": [],
    "recommendations": []
  }
]
```

### 3. Visualizations Directory
Contains interactive charts and graphs (when enabled):
- Dependency graphs
- Complexity heatmaps
- Issue distribution charts
- Call flow diagrams

## Configuration Options

```python
# Basic analysis
result = codebase.Analysis()

# Custom output directory
result = codebase.Analysis(output_dir="custom_analysis")

# Advanced configuration (via analyzer directly)
from graph_sitter.analysis.unified_analyzer import UnifiedCodebaseAnalyzer

analyzer = UnifiedCodebaseAnalyzer(codebase, output_dir="advanced_analysis")
result = analyzer.run_comprehensive_analysis(
    create_visualizations=True,  # Enable interactive visualizations
    generate_training_data=True,  # Generate ML training data
    save_to_db=True  # Save to analysis database
)
```

## Working with Results

```python
# Access analysis results
result = codebase.Analysis()

# Get enhanced analysis data
enhanced = result.enhanced_analysis
print(f"Health Score: {enhanced.health_score}")
print(f"Total Issues: {len(enhanced.issues)}")

# Access function contexts
for func_context in result.function_contexts:
    if func_context.risk_level == "high":
        print(f"High-risk function: {func_context.name}")

# Get export file paths
for name, path in result.export_paths.items():
    print(f"{name}: {path}")
```

## Integration Examples

### CI/CD Pipeline
```yaml
# .github/workflows/analysis.yml
name: Code Analysis
on: [push, pull_request]

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install graph-sitter
      - name: Run analysis
        run: |
          python -c "
          from graph_sitter import Codebase
          result = Codebase('.').Analysis()
          print(f'Health Score: {result.enhanced_analysis.health_score}')
          "
```

### Quality Gate
```python
from graph_sitter import Codebase

def quality_gate(repo_path, min_health_score=0.7):
    """Enforce minimum code quality standards."""
    codebase = Codebase(repo_path)
    result = codebase.Analysis()
    
    health_score = result.enhanced_analysis.health_score
    high_risk_functions = [
        fc for fc in result.function_contexts 
        if fc.risk_level == "high"
    ]
    
    if health_score < min_health_score:
        raise ValueError(f"Health score {health_score} below threshold {min_health_score}")
    
    if len(high_risk_functions) > 5:
        raise ValueError(f"Too many high-risk functions: {len(high_risk_functions)}")
    
    print("✅ Quality gate passed!")
    return True
```

### Automated Refactoring Suggestions
```python
def get_refactoring_priorities(repo_path):
    """Get prioritized list of refactoring candidates."""
    codebase = Codebase(repo_path)
    result = codebase.Analysis()
    
    # Sort functions by complexity and risk
    candidates = sorted(
        result.function_contexts,
        key=lambda fc: (
            fc.risk_level == "high",
            fc.complexity_metrics.get("complexity_estimate", 0)
        ),
        reverse=True
    )
    
    return candidates[:10]  # Top 10 candidates
```

## Advanced Features

### Custom Analysis Plugins
```python
from graph_sitter.analysis.unified_analyzer import UnifiedCodebaseAnalyzer

class CustomAnalyzer(UnifiedCodebaseAnalyzer):
    def custom_security_analysis(self):
        """Add custom security analysis."""
        security_issues = []
        for func in self.codebase.functions:
            if "password" in func.source.lower():
                security_issues.append({
                    "function": func.name,
                    "issue": "Potential password handling",
                    "severity": "medium"
                })
        return security_issues

# Use custom analyzer
analyzer = CustomAnalyzer(codebase)
result = analyzer.run_comprehensive_analysis()
security_issues = analyzer.custom_security_analysis()
```

### Database Integration
```python
# Save analysis results to database for tracking over time
analyzer = UnifiedCodebaseAnalyzer(codebase, output_dir="analysis")
result = analyzer.run_comprehensive_analysis(save_to_db=True)

# Query historical data
from graph_sitter.analysis.database import AnalysisDatabase
db = AnalysisDatabase("analysis_history.db")
historical_scores = db.get_health_score_trend(codebase_id="my-project")
```

## Troubleshooting

### Common Issues

1. **Tree-sitter serialization errors**: Visualizations are disabled by default to avoid serialization issues with tree-sitter nodes.

2. **Large codebases**: For very large codebases, consider analyzing specific directories:
   ```python
   codebase = Codebase("src/")  # Analyze only src directory
   ```

3. **Memory usage**: Disable training data generation for large codebases:
   ```python
   result = analyzer.run_comprehensive_analysis(generate_training_data=False)
   ```

### Performance Tips

- Use `.gitignore` patterns to exclude unnecessary files
- Focus analysis on specific file types: `Codebase(path, extensions=['.py'])`
- Run analysis incrementally on changed files only

## Contributing

The analysis feature is actively developed. Contributions welcome for:
- New analysis metrics
- Visualization improvements
- Performance optimizations
- Integration examples

## License

Same as Graph-Sitter main project.

