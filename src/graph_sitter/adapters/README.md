# Graph-sitter Adapters

This directory contains adapters and integrations for the graph-sitter analysis system.

## Analysis Module - NEW ARCHITECTURE ✨

**The analysis functionality has been completely reorganized into a comprehensive, modular system:**

### 📁 New Structure: `analysis/`

```
analysis/
├── core/                    # Core analysis engine
│   ├── engine.py           # Main AnalysisEngine
│   └── config.py           # AnalysisConfig & AnalysisResult
├── metrics/                 # Code quality & complexity metrics
│   ├── quality.py          # Maintainability, Halstead metrics
│   └── complexity.py       # Cyclomatic, cognitive complexity
├── visualization/           # Tree-sitter visualization
│   └── tree_sitter.py      # Interactive syntax tree visualization
├── detection/               # Pattern & issue detection
│   ├── patterns.py         # Code patterns & anti-patterns
│   ├── import_loops.py     # Circular import detection
│   └── dead_code.py        # Unused code detection
├── integration/             # Graph-sitter advanced settings
│   └── graph_sitter_config.py  # CodebaseConfig management
├── ai/                      # AI-powered features
│   ├── insights.py         # AI code insights
│   └── training_data.py    # ML training data generation
└── cli.py                   # Unified command-line interface
```

### 🚀 Key Features

- **🔧 Core Analysis Engine**: Unified analysis with graph-sitter integration
- **📊 Advanced Metrics**: Quality, complexity, maintainability analysis
- **🎨 Tree-sitter Visualization**: Interactive syntax tree with D3.js export
- **🔍 Pattern Detection**: Code smells, anti-patterns, best practices
- **🔄 Import Loop Detection**: Circular dependency analysis
- **💀 Dead Code Detection**: Unused functions, classes, variables
- **🤖 AI Insights**: AI-powered code analysis (requires API keys)
- **⚙️ Graph-sitter Integration**: Full advanced settings support

### 📋 Usage Examples

```bash
# Basic analysis
python -m graph_sitter.adapters.analysis.cli /path/to/code

# Comprehensive analysis with all features
python -m graph_sitter.adapters.analysis.cli . --comprehensive

# Fast analysis
python -m graph_sitter.adapters.analysis.cli . --fast

# Export HTML visualization
python -m graph_sitter.adapters.analysis.cli . --export-html analysis.html

# JSON output
python -m graph_sitter.adapters.analysis.cli . --format json --output results.json

# Enable AI insights (requires API keys)
python -m graph_sitter.adapters.analysis.cli . --enable-ai --openai-key YOUR_KEY

# Debug mode with verbose logging
python -m graph_sitter.adapters.analysis.cli . --debug --verbose
```

### 🔧 Programmatic Usage

```python
from graph_sitter.adapters.analysis import AnalysisEngine, AnalysisConfig

# Create configuration
config = AnalysisConfig(
    enable_metrics=True,
    enable_visualization=True,
    enable_pattern_detection=True,
    debug=True
)

# Run analysis
engine = AnalysisEngine(config)
result = engine.analyze_codebase("/path/to/code")

# Export results
engine.export_results("analysis_results.json")
```

### ⚙️ Graph-sitter Advanced Settings Integration

Based on [graph-sitter.com/introduction/advanced-settings](https://graph-sitter.com/introduction/advanced-settings):

- **debug**: Verbose logging for debugging
- **method_usages**: Method usage resolution
- **generics**: Generic type resolution  
- **full_range_index**: Complete range-to-node indexing
- **exp_lazy_graph**: Experimental lazy graph parsing
- **ts_language_engine**: TypeScript compiler integration
- **And many more advanced options**

### 🏗️ Architecture Benefits

1. **Modular Design**: Each analysis type in separate modules
2. **Extensible**: Easy to add new analysis features
3. **Configurable**: Fine-grained control over analysis options
4. **Performance**: Optimized with graph-sitter advanced settings
5. **Integration**: Seamless graph-sitter codebase integration
6. **Backward Compatible**: Legacy analysis tools preserved

### 📚 Migration from Legacy Tools

Legacy analysis files have been moved to `analysis/legacy_*` for reference:
- `legacy_analyze_codebase.py` - Original comprehensive tool
- `legacy_analyze_codebase_enhanced.py` - Enhanced version
- `legacy_enhanced_analyzer.py` - Graph-sitter integration

**Use the new unified CLI for all analysis needs!**

## Features Based on README2.md Implementation

All features from the comprehensive README2.md specification have been implemented:

✅ **Codebase Parsing**: Local & remote repository support  
✅ **Language Detection**: Automatic Python/TypeScript detection  
✅ **Advanced Configuration**: Full CodebaseConfig integration  
✅ **File & Directory APIs**: Complete file manipulation support  
✅ **Symbol Analysis**: Functions, classes, imports, variables  
✅ **Quality Metrics**: Maintainability, Halstead, complexity  
✅ **Visualization**: Tree-sitter query patterns & HTML export  
✅ **Pattern Detection**: Code smells, anti-patterns, best practices  
✅ **AI Integration**: Training data generation & insights  
✅ **Import Analysis**: Dependency graphs & circular imports  

All functionality is based on: https://graph-sitter.com/tutorials/at-a-glance

## Legacy Information

Previous structure (now deprecated):
- **Main Analysis Tool**: `analyze_codebase.py` (moved to `analysis/legacy_analyze_codebase.py`)
- **Enhanced Features**: All analysis capabilities now in unified `analysis/` module

### Previous Usage (Legacy)
```bash
# OLD - Use new CLI instead
python analyze_codebase.py path/to/code --tree-sitter --visualize
```

### Current Usage (New)
```bash
# NEW - Unified CLI with all features
python -m graph_sitter.adapters.analysis.cli path/to/code --comprehensive
```

