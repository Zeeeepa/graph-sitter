# 🔍 Comprehensive Code Analysis System

**Consolidated analysis framework combining all existing tools and PR features**

This module consolidates functionality from:
- **PRs #211, #212, #213, #214, #215** - Advanced analysis features
- **analyze_codebase.py** - Core analysis functionality  
- **analyze_codebase_enhanced.py** - Graph-sitter integration
- **enhanced_analyzer.py** - Advanced analysis features
- **graph_sitter_enhancements.py** - Specialized functions

## 🏗️ Architecture

```
code_analysis/
├── core/                    # Core analysis engine
│   ├── engine.py           # Main AnalysisEngine & CodebaseAnalyzer
│   └── config.py           # Configuration & results management
├── metrics/                 # Code quality & complexity metrics
│   ├── quality.py          # Quality metrics calculation
│   └── complexity.py       # Complexity analysis
├── detection/               # Pattern & issue detection
│   ├── patterns.py         # Code patterns & anti-patterns
│   ├── dead_code.py        # Unused code detection
│   └── import_loops.py     # Circular import detection
├── visualization/           # Reporting & visualization
│   └── reports.py          # HTML reports & interactive viz
├── ai/                      # AI-powered features
│   ├── insights.py         # AI code analysis
│   └── training_data.py    # ML training data generation
├── integration/             # External integrations
│   └── graph_sitter_config.py  # Graph-sitter configuration
├── legacy/                  # Backward compatibility
│   └── compatibility.py    # Legacy tool wrappers
└── cli.py                   # Unified command-line interface
```

## 🚀 Quick Start

### Python API

```python
from graph_sitter.adapters.code_analysis import analyze_codebase, AnalysisPresets

# Basic analysis
result = analyze_codebase("/path/to/code")
result.print_summary()

# Comprehensive analysis
config = AnalysisPresets.comprehensive()
result = analyze_codebase("/path/to/code", config)

# Quality-focused analysis
config = AnalysisPresets.quality_focused()
result = analyze_codebase("/path/to/code", config)

# Custom analysis
from graph_sitter.adapters.code_analysis import AnalysisConfig
config = AnalysisConfig(
    enable_ai_analysis=True,
    generate_visualizations=True,
    ai_api_key="your-api-key"
)
result = analyze_codebase("/path/to/code", config)
```

### Command Line Interface

```bash
# Basic analysis
python -m graph_sitter.adapters.code_analysis.cli analyze /path/to/code

# Comprehensive analysis with HTML report
python -m graph_sitter.adapters.code_analysis.cli analyze /path/to/code --preset comprehensive --format html

# Quality analysis with threshold
python -m graph_sitter.adapters.code_analysis.cli quality /path/to/code --threshold 8.0

# AI-powered analysis
python -m graph_sitter.adapters.code_analysis.cli ai /path/to/code --api-key YOUR_KEY

# Quick analysis
python -m graph_sitter.adapters.code_analysis.cli quick /path/to/code
```

## ✨ Key Features

### 🔧 Core Analysis Engine
- **Unified Analysis**: Single engine for all analysis types
- **Graph-sitter Integration**: Advanced syntax tree analysis
- **Performance Optimized**: Parallel processing and caching
- **Error Handling**: Robust error recovery and reporting

### 📊 Advanced Metrics
- **Quality Metrics**: Maintainability index, technical debt
- **Complexity Analysis**: Cyclomatic complexity, Halstead metrics
- **Documentation Coverage**: Docstring and comment analysis
- **Test Coverage Estimation**: Automated test coverage estimation

### 🔍 Pattern Detection
- **Dead Code Detection**: Unused functions, classes, variables
- **Import Loop Detection**: Circular dependency analysis
- **Code Smells**: Anti-patterns and code quality issues
- **Security Analysis**: Security vulnerability detection

### 🎨 Visualization & Reporting
- **Interactive HTML Reports**: Rich, interactive analysis reports
- **Tree-sitter Visualization**: Syntax tree visualization
- **Dependency Graphs**: Visual dependency mapping
- **Quality Dashboards**: Comprehensive quality dashboards

### 🤖 AI-Powered Analysis
- **Code Insights**: AI-generated code improvement suggestions
- **Issue Detection**: AI-powered bug and issue detection
- **Training Data**: ML training data generation
- **Multiple Providers**: OpenAI, Claude, local models

### ⚙️ Advanced Configuration
- **Preset Configurations**: Quick setup for common use cases
- **Custom Configuration**: Fine-grained control over all features
- **Graph-sitter Settings**: Advanced graph-sitter configuration
- **Performance Tuning**: Optimization for large codebases

## 📋 Analysis Presets

| Preset | Description | Features |
|--------|-------------|----------|
| `quick` | Fast analysis with basic metrics | Basic metrics, no AI/visualization |
| `standard` | Standard analysis with core features | All core features enabled |
| `comprehensive` | Full analysis with all features | Everything enabled except AI |
| `quality` | Quality-focused analysis | Quality metrics, patterns, documentation |
| `security` | Security-focused analysis | Security patterns, vulnerability detection |
| `ai-powered` | AI-powered analysis | AI insights, suggestions, training data |
| `enhanced` | Enhanced with graph-sitter features | Advanced graph-sitter integration |
| `performance` | Optimized for large codebases | Parallel processing, caching, lazy loading |

## 🔄 Migration from Legacy Tools

### From `analyze_codebase.py`
```python
# OLD
from graph_sitter.adapters.analyze_codebase import analyze_codebase
result = analyze_codebase("./src")

# NEW
from graph_sitter.adapters.code_analysis import analyze_codebase
result = analyze_codebase("./src")
```

### From `enhanced_analyzer.py`
```python
# OLD
from graph_sitter.adapters.enhanced_analyzer import EnhancedCodebaseAnalyzer
analyzer = EnhancedCodebaseAnalyzer()
result = analyzer.analyze_codebase_enhanced("./src")

# NEW
from graph_sitter.adapters.code_analysis import CodebaseAnalyzer, AnalysisPresets
analyzer = CodebaseAnalyzer(AnalysisPresets.enhanced())
result = analyzer.analyze("./src")
```

### Legacy Compatibility
The system provides full backward compatibility through the `legacy` module:

```python
# Legacy functions still work (with deprecation warnings)
from graph_sitter.adapters.code_analysis.legacy.compatibility import analyze_codebase
result = analyze_codebase("./src")  # Works but shows deprecation warning
```

## 📊 Results Structure

```python
class AnalysisResult:
    # Metadata
    analysis_id: str
    timestamp: str
    path: str
    analysis_duration: float
    success: bool
    
    # Basic statistics
    file_count: int
    function_count: int
    class_count: int
    import_count: int
    
    # Detailed analysis
    file_analysis: Dict[str, Any]
    function_analysis: Dict[str, Any]
    class_analysis: Dict[str, Any]
    import_analysis: Dict[str, Any]
    
    # Metrics
    quality_metrics: Dict[str, QualityMetrics]
    complexity_metrics: ComplexityMetrics
    
    # Pattern detection
    code_patterns: PatternResults
    dead_code: List[str]
    import_loops: List[Dict[str, Any]]
    
    # AI analysis (optional)
    ai_insights: Optional[AIResults]
    training_data: Optional[Dict[str, Any]]
    
    # Visualization
    visualization_data: Dict[str, Any]
    report_path: Optional[str]
```

## 🛠️ Configuration Options

### Basic Configuration
```python
from graph_sitter.adapters.code_analysis import AnalysisConfig

config = AnalysisConfig(
    analysis_level="comprehensive",
    enable_metrics=True,
    enable_pattern_detection=True,
    enable_ai_analysis=False,
    enable_visualization=True,
    enable_graph_sitter=True
)
```

### AI Configuration
```python
config.ai_config.enabled = True
config.ai_config.provider = "openai"  # or "claude", "local"
config.ai_config.api_key = "your-api-key"
config.ai_config.model = "gpt-4"
config.ai_config.analysis_types = ["quality", "security"]
```

### Performance Configuration
```python
config.performance_config.enable_parallel_processing = True
config.performance_config.max_worker_threads = 8
config.performance_config.enable_caching = True
config.performance_config.max_file_size_mb = 10
```

## 🎯 Use Cases

### Code Quality Assessment
```python
config = AnalysisPresets.quality_focused()
result = analyze_codebase("./src", config)

print(f"Quality Score: {result.quality_metrics['overall'].quality_score}/10")
print(f"Technical Debt: {result.quality_metrics['overall'].technical_debt_ratio:.2%}")
print(f"Documentation Coverage: {result.quality_metrics['overall'].documentation_coverage:.2%}")
```

### Dead Code Cleanup
```python
config = AnalysisConfig(enable_pattern_detection=True)
result = analyze_codebase("./src", config)

print(f"Dead code items found: {len(result.dead_code)}")
for item in result.dead_code:
    print(f"  - {item}")
```

### Security Analysis
```python
config = AnalysisPresets.security_focused()
config.ai_config.enabled = True
config.ai_config.api_key = "your-api-key"
result = analyze_codebase("./src", config)

if result.ai_insights:
    security_issues = [issue for issue in result.ai_insights.issues_detected 
                      if issue.get('type') == 'security']
    print(f"Security issues found: {len(security_issues)}")
```

### Training Data Generation
```python
config = AnalysisConfig(generate_training_data=True)
result = analyze_codebase("./src", config)

if result.training_data:
    print(f"Training examples generated: {len(result.training_data.get('examples', []))}")
```

## 🔧 Advanced Usage

### Custom Pattern Detection
```python
config = AnalysisConfig()
config.pattern_detection_config.custom_patterns = [
    "TODO.*FIXME",  # TODO/FIXME comments
    "print\\(",      # Debug print statements
    "console\\.log"  # Console.log statements
]
```

### Performance Optimization
```python
config = AnalysisPresets.performance_optimized()
config.performance_config.max_worker_threads = 16
config.performance_config.enable_caching = True
config.graph_sitter_config.enable_lazy_loading = True
```

### Custom Visualization
```python
config = AnalysisConfig()
config.visualization_config.theme = "dark"
config.visualization_config.include_source_code = True
config.visualization_config.auto_open_browser = True
```

## 📈 Performance

- **Parallel Processing**: Multi-threaded analysis for large codebases
- **Intelligent Caching**: Results caching for repeated analysis
- **Lazy Loading**: On-demand loading of graph-sitter features
- **Memory Optimization**: Efficient memory usage for large projects
- **Incremental Analysis**: Support for analyzing only changed files

## 🤝 Contributing

This consolidated system replaces multiple individual tools. When contributing:

1. **Add features to the appropriate module** (core, metrics, detection, etc.)
2. **Update the legacy compatibility layer** if changing existing APIs
3. **Add tests** for new functionality
4. **Update documentation** and examples
5. **Consider performance impact** on large codebases

## 📚 Documentation

- **API Reference**: See individual module docstrings
- **Configuration Guide**: See `config.py` for all options
- **Migration Guide**: See `legacy/compatibility.py`
- **Examples**: See `examples/` directory
- **CLI Reference**: Run `python -m code_analysis.cli --help`

## 🔗 Related

- **Graph-sitter Core**: Main graph-sitter functionality
- **Tree-sitter**: Syntax tree parsing
- **Contexten**: AI-powered development workflows
- **Codegen SDK**: Programmatic code generation

---

**Version**: 2.0.0  
**Compatibility**: Python 3.8+  
**License**: MIT  
**Maintainers**: Graph-sitter Analysis Team

