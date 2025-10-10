# Migration Guide: Code Restructuring

## Overview

The codebase has been restructured from 6 files into 3 consolidated adapters for better organization and maintainability.

## New Structure

### 1. **graph_sitter_adapter.py** (1,660 lines, 75KB)
**Purpose**: Pure Graph-sitter operations

**Contains**:
- `GraphSitterAnalyzer` class (84 methods)
- All Graph-sitter core functionality
- No external tool dependencies

**Use for**:
- Codebase overview and analysis
- Symbol extraction and relationships
- Function/class analysis
- Dependency graphs
- Dead code detection
- Documentation generation

**Migration**:
```python
# OLD
from graph_sitter_analysis import GraphSitterAnalyzer

# NEW  
from graph_sitter_adapter import GraphSitterAnalyzer
```

---

### 2. **libs_adapter.py** (745 lines, 26KB)
**Purpose**: External tool integration

**Contains**:
- `RuffIntegration` (7 methods) - Ruff linting/formatting
- `LSPDiagnosticsCollector` (3 methods) - LSP diagnostics
- `ErrorDatabase` (6 methods) - SQLite error tracking
- `AutoGenLibFixer` (3 methods) - AI-powered fixes
- `AnalysisError`, `ToolConfig` - Shared data structures
- LSP types: `ErrorCodes`, `MessageType`, `DiagnosticSeverity`, etc.

**Re-exports**:
- From `lsp_diagnostics`: `LSPDiagnosticsManager`, `EnhancedDiagnostic`, `RuntimeErrorCollector`
- From `autogenlib_adapter`: All AI fix functions (32 functions)

**Use for**:
- Static analysis tool integration (Ruff, MyPy, Pylint, Bandit, etc.)
- LSP diagnostic collection
- Error database operations
- AI-powered error resolution

**Migration**:
```python
# OLD
from analysis import RuffIntegration, ErrorDatabase
from lsp_diagnostics import LSPDiagnosticsManager

# NEW
from libs_adapter import (
    RuffIntegration,
    ErrorDatabase, 
    LSPDiagnosticsManager,  # Re-exported
    resolve_diagnostic_with_ai,  # Re-exported from autogenlib
)
```

---

### 3. **main_analysis.py** (5,928 lines, 241KB)
**Purpose**: Orchestration, visualization, transformation, API, CLI

**Contains**:
- `ComprehensiveAnalyzer` (46 methods) - Primary orchestrator
- `AnalysisEngine` (41 methods) - Backend analysis engine
- `EnhancedVisualizationEngine` (18 methods) - Graphs and visualizations
- `TransformationEngine` (9 methods) - Code transformations
- `InteractiveAnalyzer` (8 methods) - Interactive CLI
- `ReportGenerator` (12 methods) - Report generation
- FastAPI endpoints - REST API
- CLI `main()` function

**Use for**:
- Full codebase analysis orchestration
- Visualization generation
- Code transformations
- Interactive analysis sessions
- Report generation
- REST API server
- Command-line interface

**Migration**:
```python
# OLD
from analysis import ComprehensiveAnalyzer, InteractiveAnalyzer
from graph_sitter_backend import AnalysisEngine, EnhancedVisualizationEngine

# NEW
from main_analysis import (
    ComprehensiveAnalyzer,
    AnalysisEngine,
    EnhancedVisualizationEngine,
    InteractiveAnalyzer,
)
```

---

## Still Separate (No Changes Required)

### **lsp_diagnostics.py**
- Still exists as standalone module
- Imported by `libs_adapter.py` for convenience
- No migration needed if you're already using it

### **autogenlib_adapter.py**  
- Still exists as standalone module
- Imported by `libs_adapter.py` for convenience
- No migration needed if you're already using it

---

## Deduplication Decisions

When multiple versions of classes existed, we chose the most comprehensive:

| Class | Winner | Reason |
|-------|--------|--------|
| `GraphSitterAnalyzer` | `graph_sitter_analysis.py` | 84 methods vs 11 |
| `ComprehensiveAnalyzer` | `analysisbig.py` | 46 methods vs 22 |
| `RuffIntegration` | `analysisbig.py` | 7 methods vs 4 |
| `ReportGenerator` | `analysisbig.py` | 12 methods vs 7 |
| `AnalysisEngine` | `graph_sitter_backend.py` | Most complete |

---

## Complete Example

```python
# Comprehensive analysis with new structure
from graph_sitter_adapter import GraphSitterAnalyzer
from libs_adapter import (
    RuffIntegration,
    LSPDiagnosticsManager,
    ErrorDatabase,
    resolve_diagnostic_with_ai,
)
from main_analysis import ComprehensiveAnalyzer

# Initialize
analyzer = GraphSitterAnalyzer(codebase)
ruff = RuffIntegration()
lsp = LSPDiagnosticsManager()

# Analyze
overview = analyzer.get_codebase_overview()
errors = ruff.run_comprehensive_analysis(project_path)
diagnostics = lsp.collect_diagnostics()

# Orchestrate full analysis
comprehensive = ComprehensiveAnalyzer(project_path)
results = comprehensive.run_comprehensive_analysis()
```

---

## Files Deleted

The following files have been consolidated and deleted:
- ✅ `src/analysis.py` → Consolidated into `libs_adapter.py` and `main_analysis.py`
- ✅ `src/graph_sitter_analysis.py` → Consolidated into `graph_sitter_adapter.py`
- ✅ `src/graph_sitter_backend.py` → Consolidated into `main_analysis.py`
- ✅ `src/analysisbig.py` → Consolidated into `libs_adapter.py` and `main_analysis.py`

---

## Summary

**Before**: 6 files, ~12K lines, significant duplication  
**After**: 3 adapters + 2 unchanged modules, clear separation of concerns

**Benefits**:
- ✅ Clear separation: Graph-sitter vs Tools vs Orchestration
- ✅ No duplication: Best versions chosen
- ✅ Better imports: Related functionality together
- ✅ Easier maintenance: Know where to find what
- ✅ Full integration: Everything works together

**Questions?** Check the module docstrings in each file for detailed information.
