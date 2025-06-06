# 🚀 Graph-sitter Comprehensive Analysis System

**The Ultimate Codebase Analysis Framework - Consolidated from All PRs and Code Files**

This directory contains the most comprehensive codebase analysis system, consolidating the best features from:
- **All PRs (#211, #212, #213, #214, #215)**: Advanced frameworks and modular architectures
- **graph_sitter_enhancements.py**: Enhanced graph-sitter integration functions
- **legacy_analyze_codebase.py**: Comprehensive analysis with tree-sitter patterns
- **legacy_analyze_codebase_enhanced.py**: Advanced graph-sitter pre-computed elements
- **legacy_enhanced_analyzer.py**: Enhanced analyzer with advanced configuration

## 🏗️ NEW ARCHITECTURE: Comprehensive Analysis Framework

### 📁 Modular Structure: `analysis/`

```
analysis/
├── core/                    # 🔧 Core analysis engine
│   ├── engine.py           # Main AnalysisEngine with all features
│   └── config.py           # AnalysisConfig & AnalysisResult
├── metrics/                 # 📊 Code quality & complexity metrics
│   ├── quality.py          # Maintainability, documentation coverage
│   └── complexity.py       # Cyclomatic, Halstead, cognitive complexity
├── detection/               # 🔍 Pattern & issue detection
│   ├── patterns.py         # Code patterns & anti-patterns
│   ├── dead_code.py        # Unused code detection
│   └── import_loops.py     # Circular import detection
├── visualization/           # 🎨 Tree-sitter visualization
│   └── tree_sitter.py      # Interactive syntax tree visualization
├── ai/                      # 🤖 AI-powered features
│   ├── insights.py         # AI code insights & suggestions
│   └── training_data.py    # ML training data generation
├── integration/             # ⚙️ Graph-sitter advanced settings
│   └── graph_sitter_config.py  # CodebaseConfig management
└── cli.py                   # 🖥️ Unified command-line interface
```

### ✨ Comprehensive Features

- **🔧 Unified Core Engine**: Consolidates all analysis capabilities from all sources
- **📊 Advanced Metrics**: Quality, complexity, maintainability analysis from all PRs
- **🎨 Rich Visualization**: Tree-sitter, D3.js, interactive HTML reports
- **🔍 Pattern Detection**: Code smells, anti-patterns, best practices detection
- **🔄 Import Loop Detection**: Circular dependency analysis with severity levels
- **💀 Dead Code Detection**: Unused functions, classes, variables, imports
- **🤖 AI Integration**: Training data generation, insights, automated analysis
- **⚙️ Graph-sitter Advanced Settings**: Full integration with all advanced options
- **🖥️ Comprehensive CLI**: All features accessible through unified interface
- **📚 Legacy Compatibility**: Preserved legacy tools for backward compatibility

## 🚀 Quick Start

### Command Line Interface

```bash
# Basic analysis
python -m graph_sitter.adapters.analysis.cli /path/to/code

# Comprehensive analysis with HTML report
python -m graph_sitter.adapters.analysis.cli /path/to/code --comprehensive --export-html report.html

# Tree-sitter analysis with visualization
python -m graph_sitter.adapters.analysis.cli /path/to/code --tree-sitter --visualize --open-browser

# Quality-focused analysis
python -m graph_sitter.adapters.analysis.cli /path/to/code --preset quality

# AI-powered analysis (requires API key)
python -m graph_sitter.adapters.analysis.cli /path/to/code --ai-insights --api-key YOUR_KEY

# Generate training data for ML
python -m graph_sitter.adapters.analysis.cli /path/to/code --generate-training-data

# Import loop detection
python -m graph_sitter.adapters.analysis.cli /path/to/code --detect-import-loops

# Dead code detection
python -m graph_sitter.adapters.analysis.cli /path/to/code --detect-dead-code

# Fast analysis with basic metrics
python -m graph_sitter.adapters.analysis.cli /path/to/code --fast

# Debug mode with verbose logging
python -m graph_sitter.adapters.analysis.cli /path/to/code --debug --verbose
```

### Python API

```python
from graph_sitter.adapters.analysis import analyze_codebase, AnalysisPresets

# Basic analysis
result = analyze_codebase("/path/to/code")
result.print_summary()

# Comprehensive analysis
config = AnalysisPresets.comprehensive()
result = analyze_codebase("/path/to/code", config)

# Quality-focused analysis
config = AnalysisPresets.quality_focused()
result = analyze_codebase("/path/to/code", config)

# AI-powered analysis
config = AnalysisPresets.ai_powered()
config.ai_api_key = "your-api-key"
result = analyze_codebase("/path/to/code", config)

# Custom analysis configuration
from graph_sitter.adapters.analysis import AnalysisConfig
config = AnalysisConfig(
    enable_metrics=True,
    enable_pattern_detection=True,
    enable_visualization=True,
    enable_ai_insights=True,
    enable_graph_sitter=True,
    debug=True
)
result = analyze_codebase("/path/to/code", config)

# Access specific results
print(f"Quality Score: {result.quality_metrics.get('maintainability_score', 0)}")
print(f"Dead Code Items: {len(result.dead_code)}")
print(f"Import Loops: {len(result.import_loops)}")
print(f"Pattern Issues: {len(result.patterns)}")

# Export results
result.save_to_file("analysis_results.json")
```

### Enhanced Analysis Methods

```python
from graph_sitter.adapters.analysis.core.engine import AnalysisEngine
from graph_sitter.adapters.analysis import AnalysisConfig

# Initialize engine with comprehensive config
config = AnalysisConfig(enable_graph_sitter=True, enable_ai_insights=True)
engine = AnalysisEngine(config)

# Analyze specific functions with enhanced metrics
function_metrics = engine.analyze_function_enhanced("process_data")
if function_metrics:
    print(f"Function: {function_metrics.name}")
    print(f"Complexity: {function_metrics.complexity}")
    print(f"Quality: {function_metrics.quality}")
    print(f"Dependencies: {function_metrics.dependencies}")
    print(f"AI Insights: {function_metrics.ai_insights}")

# Analyze specific classes with enhanced metrics
class_metrics = engine.analyze_class_enhanced("DataProcessor")
if class_metrics:
    print(f"Class: {class_metrics.name}")
    print(f"Methods: {len(class_metrics.methods)}")
    print(f"Inheritance: {class_metrics.inheritance}")
    print(f"Patterns: {class_metrics.patterns}")

# Detect import loops with enhanced analysis
import_loops = engine.detect_import_loops_enhanced()
for loop in import_loops:
    print(f"Import Loop: {loop.files}")
    print(f"Type: {loop.loop_type}, Severity: {loop.severity}")

# Detect dead code with enhanced analysis
dead_code = engine.detect_dead_code_enhanced()
for item in dead_code:
    print(f"Dead Code: {item.name} ({item.type}) in {item.file_path}")
    print(f"Reason: {item.reason}, Confidence: {item.confidence}")

# Generate training data for ML models
training_data = engine.generate_training_data_enhanced()
for item in training_data:
    print(f"Function: {item.function_name}")
    print(f"Quality Metrics: {item.quality_metrics}")
    print(f"Context: {item.context}")

# Analyze graph structure
graph_analysis = engine.analyze_graph_structure()
if graph_analysis:
    print(f"Nodes: {graph_analysis.total_nodes}")
    print(f"Edges: {graph_analysis.total_edges}")
    print(f"Density: {graph_analysis.graph_density}")
    print(f"Clustering: {graph_analysis.clustering_coefficient}")
```

## 🔧 Analysis Presets

### Basic Analysis
```python
config = AnalysisPresets.basic()
# Enables: Quality metrics only
# Use case: Quick code review
```

### Comprehensive Analysis
```python
config = AnalysisPresets.comprehensive()
# Enables: All features except AI (requires API key)
# Use case: Complete codebase assessment
```

### Quality-Focused Analysis
```python
config = AnalysisPresets.quality_focused()
# Enables: Quality metrics + pattern detection
# Use case: Code quality review and improvement
```

### Performance-Focused Analysis
```python
config = AnalysisPresets.performance_focused()
# Enables: Complexity metrics + performance patterns
# Use case: Performance optimization
```

### AI-Powered Analysis
```python
config = AnalysisPresets.ai_powered()
# Enables: All features + AI insights + training data
# Use case: Advanced analysis with AI assistance
```

## ⚙️ Graph-sitter Advanced Settings Integration

Based on [graph-sitter.com/introduction/advanced-settings](https://graph-sitter.com/introduction/advanced-settings):

```python
config = AnalysisConfig(
    enable_graph_sitter=True,
    advanced_graph_sitter_settings={
        'debug': True,                    # Verbose logging for debugging
        'method_usages': True,           # Method usage resolution
        'generics': True,                # Generic type resolution
        'full_range_index': True,        # Complete range-to-node indexing
        'exp_lazy_graph': True,          # Experimental lazy graph parsing
        'ts_language_engine': True,      # TypeScript compiler integration
        # Add more advanced settings as needed
    }
)
```

## 📊 Analysis Results Structure

```python
@dataclass
class AnalysisResult:
    path: str                           # Analyzed codebase path
    timestamp: float                    # Analysis timestamp
    analysis_duration: float            # Time taken for analysis
    config: AnalysisConfig             # Configuration used
    
    # Core metrics
    quality_metrics: Dict[str, Any]     # Quality and maintainability metrics
    complexity_metrics: Dict[str, Any]  # Complexity analysis results
    
    # Detection results
    patterns: List[Any]                 # Detected patterns and anti-patterns
    import_loops: List[ImportLoop]      # Circular import dependencies
    dead_code: List[DeadCodeItem]       # Unused code items
    
    # Visualization data
    visualizations: Dict[str, Any]      # Tree-sitter visualizations
    
    # AI-powered results
    ai_insights: Optional[Dict[str, Any]]      # AI-generated insights
    training_data: Optional[List[TrainingDataItem]]  # ML training data
```

## 🎨 Visualization Features

### Interactive HTML Reports
- **D3.js Visualizations**: Interactive syntax trees and dependency graphs
- **Quality Dashboards**: Comprehensive metrics visualization
- **Pattern Heatmaps**: Code smell and anti-pattern visualization
- **Dependency Networks**: Import relationship visualization
- **Timeline Analysis**: Code evolution and complexity trends

### Tree-sitter Query Patterns
```python
# Example tree-sitter query patterns for Python
FUNCTION_QUERY = """
(function_definition
  name: (identifier) @function.name
  parameters: (parameters) @function.params
  body: (block) @function.body)
"""

CLASS_QUERY = """
(class_definition
  name: (identifier) @class.name
  superclasses: (argument_list)? @class.bases
  body: (block) @class.body)
"""
```

## 🤖 AI Integration Features

### Training Data Generation
- **Function Context**: Complete function analysis with dependencies
- **Quality Metrics**: Automated quality scoring for ML training
- **Pattern Labels**: Labeled examples of code patterns and anti-patterns
- **Refactoring Examples**: Before/after code transformation examples

### AI Insights
- **Code Suggestions**: AI-powered improvement recommendations
- **Pattern Recognition**: Automated detection of complex patterns
- **Quality Assessment**: AI-driven code quality evaluation
- **Documentation Generation**: Automated docstring and comment generation

## 📚 Legacy Compatibility

### Legacy Tools Preserved
- **`legacy_analyze_codebase.py`**: Original comprehensive analysis tool
- **`legacy_analyze_codebase_enhanced.py`**: Enhanced version with graph-sitter
- **`legacy_enhanced_analyzer.py`**: Enhanced analyzer class

### Migration Path
```python
# Old way (legacy)
from graph_sitter.adapters.analysis.legacy_analyze_codebase import main
main(['path/to/code', '--comprehensive'])

# New way (recommended)
from graph_sitter.adapters.analysis import comprehensive_analysis
result = comprehensive_analysis('path/to/code')
```

## 🔍 Advanced Use Cases

### Continuous Integration
```bash
# Add to CI pipeline for code quality checks
python -m graph_sitter.adapters.analysis.cli . --preset quality --format json --output quality_report.json
```

### Code Review Automation
```python
# Automated code review with AI insights
config = AnalysisPresets.ai_powered()
config.ai_api_key = os.getenv('OPENAI_API_KEY')
result = analyze_codebase('.', config)

# Generate review comments
for insight in result.ai_insights.get('suggestions', []):
    print(f"Suggestion: {insight['message']}")
    print(f"File: {insight['file']}, Line: {insight['line']}")
```

### Performance Monitoring
```python
# Track code complexity over time
config = AnalysisPresets.performance_focused()
result = analyze_codebase('.', config)

# Store metrics for trending
metrics = {
    'timestamp': result.timestamp,
    'complexity': result.complexity_metrics,
    'quality': result.quality_metrics
}
```

### ML Model Training
```python
# Generate training data for custom ML models
config = AnalysisPresets.ai_powered()
config.generate_training_data = True
result = analyze_codebase('.', config)

# Export training data
training_data = result.training_data
with open('training_data.jsonl', 'w') as f:
    for item in training_data:
        f.write(json.dumps(asdict(item)) + '\n')
```

## 🛠️ Configuration Options

### Complete Configuration Reference
```python
config = AnalysisConfig(
    # Core features
    enable_metrics=True,                # Quality and complexity metrics
    enable_pattern_detection=True,      # Pattern and anti-pattern detection
    enable_visualization=True,          # Tree-sitter visualizations
    enable_ai_insights=True,           # AI-powered analysis
    enable_graph_sitter=True,          # Graph-sitter integration
    
    # Specific detection features
    detect_import_loops=True,          # Circular import detection
    detect_dead_code=True,             # Unused code detection
    detect_patterns=True,              # Code pattern detection
    
    # AI configuration
    ai_api_key="your-api-key",         # API key for AI services
    generate_training_data=True,       # Generate ML training data
    
    # Graph-sitter advanced settings
    lazy_loading=True,                 # Enable lazy graph loading
    advanced_graph_sitter_settings={   # Advanced graph-sitter options
        'method_usages': True,
        'generics': True,
        'full_range_index': True,
    },
    
    # Output configuration
    export_html=True,                  # Generate HTML reports
    html_output_path="report.html",    # HTML report path
    open_browser=True,                 # Open HTML report in browser
    
    # Performance and debugging
    debug=True,                        # Debug mode
    verbose=True,                      # Verbose logging
    quiet=False,                       # Quiet mode
    
    # File filtering
    include_tests=True,                # Include test files
    include_docs=True,                 # Include documentation files
    
    # Legacy compatibility
    legacy_mode=False,                 # Use legacy analysis mode
)
```

## 📈 Performance Optimization

### Fast Analysis Mode
```bash
# Quick analysis for large codebases
python -m graph_sitter.adapters.analysis.cli /path/to/code --fast
```

### Lazy Loading
```python
# Enable lazy loading for better performance
config = AnalysisConfig(
    enable_graph_sitter=True,
    lazy_loading=True,
    advanced_graph_sitter_settings={'exp_lazy_graph': True}
)
```

### Selective Analysis
```python
# Analyze only specific features for performance
config = AnalysisConfig(
    enable_metrics=True,           # Only quality metrics
    enable_pattern_detection=False,
    enable_visualization=False,
    enable_ai_insights=False
)
```

## 🔗 Integration Examples

### GitHub Actions
```yaml
name: Code Quality Analysis
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
        run: pip install graph-sitter
      - name: Run analysis
        run: python -m graph_sitter.adapters.analysis.cli . --preset quality --format json --output analysis.json
      - name: Upload results
        uses: actions/upload-artifact@v2
        with:
          name: analysis-results
          path: analysis.json
```

### Pre-commit Hook
```bash
#!/bin/bash
# .git/hooks/pre-commit
python -m graph_sitter.adapters.analysis.cli . --fast --quiet
if [ $? -ne 0 ]; then
    echo "Code quality check failed!"
    exit 1
fi
```

## 🎯 Best Practices

### 1. Choose the Right Preset
- **Basic**: Quick checks during development
- **Quality**: Code review and quality gates
- **Comprehensive**: Complete codebase assessment
- **AI-powered**: Advanced analysis with AI assistance

### 2. Configure for Your Needs
```python
# For large codebases
config = AnalysisConfig(
    enable_metrics=True,
    enable_pattern_detection=True,
    enable_visualization=False,  # Skip for performance
    lazy_loading=True
)

# For detailed analysis
config = AnalysisConfig(
    enable_metrics=True,
    enable_pattern_detection=True,
    enable_visualization=True,
    enable_ai_insights=True,
    debug=True
)
```

### 3. Use Appropriate Output Formats
- **JSON**: For CI/CD integration and automation
- **HTML**: For human-readable reports and presentations
- **Text**: For quick console output and debugging

### 4. Leverage AI Features Responsibly
- Always review AI-generated suggestions
- Use training data generation for custom models
- Protect API keys and sensitive information

## 🚀 Future Enhancements

The comprehensive analysis system is designed for extensibility:

- **Plugin Architecture**: Add custom analysis modules
- **Language Support**: Extend beyond Python and TypeScript
- **Cloud Integration**: Distributed analysis for large codebases
- **Real-time Analysis**: Live code quality monitoring
- **Advanced AI**: Custom ML models for domain-specific analysis

## 📞 Support and Contributing

This comprehensive system consolidates the best features from multiple PRs and code files. For issues, enhancements, or contributions:

1. Check existing functionality in the modular `analysis/` structure
2. Review legacy tools in `analysis/legacy_*` for reference
3. Follow the established patterns for new features
4. Ensure backward compatibility when possible

---

**🎉 The Ultimate Codebase Analysis Experience - All Features, One System!**

