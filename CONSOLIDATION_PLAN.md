# File Consolidation Plan

## Executive Summary

Based on AST analysis of the 6 analysis files and 8 tool files, this document outlines the consolidation strategy into 4 files:

1. **autogenlib_adapter.py** - AutoGen library integration
2. **lsp_adapter.py** - LSP diagnostics and error handling
3. **graph_sitter_tools_adapter.py** - All Graph-Sitter tools consolidated
4. **codebase_analysis.py** - Main orchestration and GraphSitterAnalyzer

## Analysis Results

### Current State - 6 Analysis Files

| File | Lines | Classes | Functions | Key Responsibilities |
|------|-------|---------|-----------|---------------------|
| graph_sitter_analysis.py | 1,676 | 1 | 2 | GraphSitterAnalyzer (master class with 76 methods) |
| graph_sitter_backend.py | 3,954 | 11 | 10 | Analysis backends, API models, complexity calculations |
| lsp_diagnostics.py | 563 | 3 | 0 | LSPDiagnosticsManager, runtime error collection |
| autogenlib_adapter.py | 1,130 | 0 | 32 | AutoGen integration, AI fix context |
| analysisbig.py | ~3,400 | ? | ? | **SYNTAX ERROR - needs investigation** |
| analysis.py | 5,589 | 12 | 12 | Duplicate of backend + analyzer functionality |

**Total: ~12,912 lines, 27+ classes, 56+ functions**

### Current State - 8 Tool Files

| File | Lines | Classes | Functions | Purpose |
|------|-------|---------|-----------|---------|
| reveal_symbol_fn.py | 75 | 2 | 0 | Symbol function revelation |
| reveal_symbol.py | 316 | 2 | 6 | Symbol revelation with imports |
| mdx_docs_generation.py | 204 | 0 | 16 | MDX documentation generation |
| list_directory.py | 232 | 2 | 4 | Directory listing |
| generate_docs_json.py | 183 | 0 | 4 | JSON docs generation |
| document_functions.py | 119 | 0 | 3 | Function documentation |
| current_code_codebase.py | 94 | 1 | 5 | Current codebase access |
| codegen_sdk_codebase.py | 22 | 0 | 2 | Codegen SDK codebase |

**Total: ~1,245 lines, 7+ classes, 40+ functions**

## Key Dependencies Identified

### Cross-File Dependencies

```
graph_sitter_backend.py → autogenlib_adapter.py (resolve_diagnostic_with_ai)
lsp_diagnostics.py → autogenlib_adapter.py (get_ai_fix_context)
autogenlib_adapter.py → graph_sitter_analysis.py (GraphSitterAnalyzer)
autogenlib_adapter.py → lsp_diagnostics.py (EnhancedDiagnostic)
analysis.py → autogenlib_adapter.py (resolve_diagnostic_with_ai)
```

### External Dependencies (most common)

- `graph_sitter.Codebase` - Core codebase abstraction
- `graph_sitter.core.*` - Symbol, Function, Class, File, Import classes
- `graph_sitter.extensions.tools.*` - Various tools
- Standard library: `pathlib`, `typing`, `collections`, `re`, `logging`

## Consolidation Strategy

### 1. autogenlib_adapter.py (KEEP, ENHANCE)

**Source Files:**
- `src/autogenlib_adapter.py` (keep as base)

**Functions to Keep:**
- All 32 existing functions
- `get_llm_codebase_overview()`
- `get_comprehensive_symbol_context()`
- `get_file_context()`
- `get_autogenlib_enhanced_context()`
- `get_ai_fix_context()`
- `resolve_diagnostic_with_ai()` (from graph_sitter_backend.py and analysis.py)

**Dependencies:**
- `graph_sitter.Codebase`
- `graph_sitter.extensions.autogenlib.*`
- Will import from `lsp_adapter` for diagnostics
- Will import from `codebase_analysis` for GraphSitterAnalyzer

### 2. lsp_adapter.py (NEW FILE)

**Source Files:**
- `src/lsp_diagnostics.py` (primary source)

**Classes to Move:**
- `EnhancedDiagnostic`
- `RuntimeErrorCollector`
- `LSPDiagnosticsManager`

**Responsibilities:**
- LSP server integration
- Runtime error collection
- UI interaction error collection
- Diagnostic enhancement
- Integration with SolidLSP

**Dependencies:**
- `graph_sitter.extensions.lsp.solidlsp.*`
- Will use `autogenlib_adapter` for AI-powered fixes

### 3. graph_sitter_tools_adapter.py (NEW FILE)

**Source Files (8 tool files to consolidate):**
- `reveal_symbol_fn.py` - Symbol function revelation
- `reveal_symbol.py` - Symbol revelation with import hopping
- `mdx_docs_generation.py` - MDX documentation
- `list_directory.py` - Directory listing
- `generate_docs_json.py` - JSON documentation
- `document_functions.py` - Function documentation
- `current_code_codebase.py` - Codebase access
- `codegen_sdk_codebase.py` - SDK codebase access

**Functions to Consolidate (~40 functions):**

From `reveal_symbol.py`:
- `truncate_source()` 
- `get_symbol_info()`
- `hop_through_imports()`

From `mdx_docs_generation.py` (16 functions):
- `render_mdx_page_for_class()`
- `render_mdx_page_title()`
- `render_mdx_inheritence_section()`
- ... (13 more)

From `list_directory.py`:
- `list_directory()`
- `get_directory_info()`
- `add_tree_item()`

From `generate_docs_json.py`:
- `generate_docs_json()`
- `process_class_doc()`
- `process_method()`

From `document_functions.py`:
- `hop_through_imports()`
- `get_extended_context()`
- `run()`

From `current_code_codebase.py`:
- `get_graphsitter_repo_path()`
- `get_codegen_codebase_base_path()`
- `get_current_code_codebase()`

From `codegen_sdk_codebase.py`:
- `get_codegen_sdk_subdirectories()`
- `get_codegen_sdk_codebase()`

**Structure:**
```python
class GraphSitterTools:
    """Unified interface for all Graph-Sitter tools."""
    
    # Symbol revelation tools
    @staticmethod
    def reveal_symbol(...) -> dict: ...
    
    @staticmethod
    def reveal_symbol_function(...) -> dict: ...
    
    # Documentation tools
    @staticmethod
    def generate_mdx_docs(...) -> str: ...
    
    @staticmethod
    def generate_json_docs(...) -> dict: ...
    
    @staticmethod
    def document_functions(...) -> str: ...
    
    # Navigation tools
    @staticmethod
    def list_directory(...) -> dict: ...
    
    # Codebase access tools
    @staticmethod
    def get_current_codebase() -> Codebase: ...
    
    @staticmethod
    def get_codegen_sdk_codebase() -> Codebase: ...
```

### 4. codebase_analysis.py (NEW FILE)

**Source Files:**
- `src/graph_sitter_analysis.py` (primary source - GraphSitterAnalyzer)
- `src/graph_sitter_backend.py` (backend models and complexity calculations)
- `src/analysis.py` (consolidate unique functionality, discard duplicates)
- `src/analysisbig.py` (investigate and salvage if possible)

**Main Class:**
- `GraphSitterAnalyzer` (76 methods from graph_sitter_analysis.py)

**Additional Classes (from backend/analysis.py):**
- `AnalyzeRequest`
- `ErrorAnalysisResponse`
- `EntrypointAnalysisResponse`
- `TransformationRequest`
- `VisualizationRequest`
- Other backend models (11 classes total)

**Functions (from backend/analysis.py):**
- `clone_repository()`
- `calculate_doi()`
- `get_operators_and_operands()`
- `calculate_halstead_volume()`
- `cc_rank()`
- Other complexity/analysis functions (10+ functions)

**Structure:**
```python
# Main imports
from autogenlib_adapter import *
from lsp_adapter import *
from graph_sitter_tools_adapter import *
from graph_sitter import Codebase
from graph_sitter.sdk.core.external_module import ExternalModule
from graph_sitter.sdk.core.import_resolution import Import
from graph_sitter.sdk.core.symbol import Symbol

class GraphSitterAnalyzer:
    """Comprehensive codebase analysis engine."""
    # 76 methods from graph_sitter_analysis.py
    
# Backend models
class AnalyzeRequest(BaseModel): ...
class ErrorAnalysisResponse(BaseModel): ...
# ... etc

# Utility functions
def calculate_doi(...): ...
def clone_repository(...): ...
# ... etc
```

## Dead Code Candidates

### From autogenlib_adapter.py
- None identified yet (all 32 functions appear to be used)

### From lsp_diagnostics.py
- Needs usage analysis

### From analysis.py and graph_sitter_backend.py
- **HIGH DUPLICATION**: These files are nearly identical
- `analysis.py` appears to be a superset of `graph_sitter_backend.py`
- Decision: Use `analysis.py` as primary source, discard `graph_sitter_backend.py` duplicates

### From analysisbig.py
- **SYNTAX ERROR**: File has parse error at line 3351
- Needs manual investigation before consolidation
- May contain dead/experimental code

## Consolidation Steps (Detailed)

### Phase 1: Prepare New Files (Steps 11-14)

1. Create skeleton for `lsp_adapter.py`
2. Create skeleton for `graph_sitter_tools_adapter.py`
3. Create skeleton for `codebase_analysis.py`
4. Update `autogenlib_adapter.py` with new imports

### Phase 2: Consolidate LSP (Step 16)

1. Move classes from `lsp_diagnostics.py` to `lsp_adapter.py`
   - `EnhancedDiagnostic`
   - `RuntimeErrorCollector`
   - `LSPDiagnosticsManager`
2. Update imports to use `autogenlib_adapter`
3. Add proper docstrings and type hints

### Phase 3: Consolidate Tools (Steps 17-18)

1. Create `GraphSitterTools` class in `graph_sitter_tools_adapter.py`
2. Move functions from 8 tool files:
   - Group by functionality (revelation, documentation, navigation, access)
   - Preserve all functionality
   - Deduplicate `hop_through_imports()` if it appears multiple times
3. Update imports and dependencies

### Phase 4: Consolidate Analysis (Step 19)

1. Move `GraphSitterAnalyzer` from `graph_sitter_analysis.py` to `codebase_analysis.py`
2. Move backend models from `analysis.py` to `codebase_analysis.py`
3. Move utility functions (complexity calculations, etc.)
4. Investigate `analysisbig.py` syntax error and salvage usable code
5. Add top-level imports:
   ```python
   from autogenlib_adapter import *
   from lsp_adapter import *
   from graph_sitter_tools_adapter import *
   ```

### Phase 5: Update Imports (Step 20-22)

1. Update all imports in the 4 new files
2. Update imports throughout the codebase
3. Verify no circular dependencies

## Testing Strategy

### Unit Tests
- Verify GraphSitterAnalyzer methods work correctly
- Test LSP diagnostics collection
- Test each tool in GraphSitterTools
- Test AutoGen integration functions

### Integration Tests
- Test full analysis workflow
- Test LSP + AutoGen integration
- Test tool usage from codebase_analysis

### Regression Tests
- Run existing test suite
- Verify no functionality lost
- Check examples still work

## Risk Mitigation

1. **Syntax Error in analysisbig.py**: Investigate before consolidation
2. **Large GraphSitterAnalyzer class**: Consider breaking into mixins if needed
3. **Circular dependencies**: Careful import ordering
4. **Lost functionality**: Comprehensive testing before removing old files

## Success Criteria

✅ All 83+ symbols preserved  
✅ No circular dependencies  
✅ All tests passing  
✅ Dead code removed  
✅ 4 clean, well-documented files  
✅ Clear separation of concerns  
✅ Improved maintainability  

## Next Steps

Execute consolidation following the 30-step plan, starting with Phase 1 (Steps 11-14): Creating skeleton files.

