# Feature Inventory & Porting Plan

## Phase 1: Critical Features (Must Have)

### graph_sitter_adapter.py
**From: graph_sitter_analysis.py (2,500 lines)**

CRITICAL:
- [x] get_codebase_overview() - Basic stats ✅
- [x] get_file_details() - File analysis ✅
- [x] get_function_details() - Function lookup ✅
- [x] get_class_details() - Class lookup ✅
- [ ] find_usages() - Symbol usage tracking (simplified ✅, needs enhancement)
- [ ] analyze_dependencies() - Dependency graph
- [ ] get_import_graph() - Full import analysis
- [ ] find_circular_dependencies() - Circular dep detection
- [ ] get_call_hierarchy() - Call chain analysis
- [ ] analyze_code_complexity() - Full complexity metrics
- [ ] find_dead_code() - Dead code detection (stubbed, needs impl)

IMPORTANT:
- [ ] generate_documentation() - Auto doc generation
- [ ] find_code_smells() - Pattern detection
- [ ] security_analysis() - Security scanning
- [ ] performance_hotspots() - Performance analysis

NICE_TO_HAVE:
- [ ] Visualization integration (stubbed ✅)
- [ ] Advanced metrics
- [ ] Custom query builder

### autogenlib_adapter.py  
**From: autogenlib_context.py (1,100 lines) + autogenlib_ai_resolve.py (700 lines)**

CRITICAL:
- [x] resolve_error() - Basic resolution ✅
- [ ] generate_comprehensive_context() - Full context for AI
- [ ] resolve_with_retry() - Retry logic
- [ ] batch_resolve() - Batch processing
- [ ] get_relevant_files() - Smart file selection
- [ ] extract_error_context() - Enhanced context extraction

IMPORTANT:
- [ ] auto_fix() - Automatic fixing
- [ ] generate_test() - Test generation
- [ ] suggest_refactoring() - Refactor suggestions

### lib_analysis.py
**From: lsp_diagnostics.py (900 lines)**

CRITICAL:
- [x] Tool integration (Ruff, Mypy, PyRight) ✅
- [ ] LSP diagnostics integration
- [ ] Enhanced error enrichment
- [ ] Runtime error correlation
- [ ] UI interaction error tracking

IMPORTANT:
- [ ] Custom tool registration
- [ ] Tool configuration from file
- [ ] Error prioritization
- [ ] Fix confidence scoring

## Phase 2: Important Features (Should Have)

- Documentation generation
- Security analysis  
- Test generation
- Refactoring suggestions
- Performance analysis

## Phase 3: Nice-to-Have Features (Could Have)

- Advanced visualizations
- Custom metrics
- Plugin system
- Advanced config options

## Entrypoint Requirements

**Primary Command: `gs-analyze <path>`**

Must support:
- JSON output for AI consumption
- Text output for human reading
- Markdown output for documentation
- Filtering by file/symbol
- Tool selection
- Output to file

**Usage:**
```bash
# Full analysis
gs-analyze ./src

# Specific file
gs-analyze ./src/main.py

# With specific tools
gs-analyze ./src --tools ruff,mypy

# JSON for AI
gs-analyze ./src --format json --output context.json

# Error resolution mode
gs-analyze ./src --resolve-errors --auto-fix
```

## Backward Compatibility

Old imports that must still work:
- `from src.analysis import GraphSitterAnalyzer`
- `from src.graph_sitter_analysis import ...`
- `from src.autogenlib_context import ...`

Strategy: Deprecation warnings + re-exports through new adapters
