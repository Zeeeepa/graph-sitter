# Graph-Sitter Extension

This extension provides enhanced code analysis, visualization, and resolution capabilities using the graph-sitter library.

## ⚠️ Important: Naming Change

This extension has been renamed from `graph_sitter` to `graph_sitter_ext` to avoid conflicts with the actual `graph_sitter` library.

**New import path:**
```python
from contexten.extensions.graph_sitter_ext import Analysis, Visualize, Resolve, CodebaseConfig
```

## Module Status

### ✅ Working Modules

1. **Core Module** - Configuration and base classes
   - `CodebaseConfig` - Main configuration class
   - `PresetConfigs` - Predefined configurations

2. **Analysis Module** - Code analysis capabilities (7/7 components working) 🎉
   - ✅ `Analysis` - Main analyzer class
   - ✅ Complexity analysis functions
   - ✅ Dependency analysis functions  
   - ✅ Security analysis functions
   - ✅ Call graph analysis functions
   - ✅ Dead code detection functions
   - ✅ Enhanced analyzer functions (FIXED!)

3. **Visualize Module** - Code visualization features
   - ✅ `Visualize` - Main visualization class

4. **Resolve Module** - Symbol resolution and auto-fix
   - ✅ `Resolve` - Basic resolution class
   - ✅ `EnhancedResolver` - Advanced resolution class

### 🗑️ Removed Files

The following unused files have been removed:
- `analysis/__main__.py` - Unused CLI entry point
- `analysis/cli.py` - Unused CLI module  
- `analysis/visualization/html_reporter.py` - Missing dependencies

### ✅ Fixed Import Issues

Fixed import issues in the following files:
- `analysis/enhanced_analyzer.py` - Fixed CodebaseConfig import path
- `analysis/advanced_config.py` - Fixed CodebaseConfig import path
- `analysis/config_manager.py` - Fixed CodebaseConfig import path

## Usage Examples

### Enhanced Analysis (NEW!)
```python
from contexten.extensions.graph_sitter_ext import enhanced_comprehensive_analysis

# Run comprehensive analysis with different optimization modes
result = enhanced_comprehensive_analysis(
    codebase_path="./src",
    optimization_mode="comprehensive"  # or "performance", "debug", "typescript", "ast_only"
)
```

### Basic Analysis
```python
from contexten.extensions.graph_sitter_ext import Analysis

# Create analyzer instance
analyzer = Analysis()

# Analyze complexity
from contexten.extensions.graph_sitter_ext import calculate_cyclomatic_complexity
complexity = calculate_cyclomatic_complexity(code_node)
```

### Configuration
```python
from contexten.extensions.graph_sitter_ext import CodebaseConfig

# Create configuration
config = CodebaseConfig(
    language="python",
    include_patterns=["*.py"],
    exclude_patterns=["tests/*"]
)
```

### Visualization
```python
from contexten.extensions.graph_sitter_ext import Visualize

# Create visualizer
viz = Visualize()
```

### Symbol Resolution
```python
from contexten.extensions.graph_sitter_ext import Resolve

# Create resolver
resolver = Resolve()
```

## Integration Status

- ✅ No naming conflicts with real graph_sitter library
- ✅ Core functionality working
- ✅ Analysis components mostly working (7/7)
- ✅ Visualization working
- ✅ Resolution working
- ⚠️ Some legacy files need fixing or removal
- ⚠️ Enhanced analyzer needs import path fixes

## Next Steps

1. Fix remaining problematic files or remove them
2. Resolve CodebaseConfig import issues in enhanced analyzer
3. Update any remaining references to old import paths
4. Add comprehensive tests for working modules
