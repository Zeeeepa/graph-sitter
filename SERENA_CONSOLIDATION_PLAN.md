# Serena LSP Integration Consolidation Plan

## Current Problems

### 1. Massive Redundancy
- `types.py` AND `serena_types.py` - duplicate type definitions
- `api.py` AND `advanced_api.py` - duplicate API layers  
- `error_analysis.py` AND `advanced_error_viewer.py` - duplicate error handling
- `integration.py` AND `lsp_integration.py` - duplicate integration logic
- `core.py` has overlapping functionality with multiple other files

### 2. Architectural Issues
- 12+ subdirectories with minimal content
- Over-engineered abstraction layers
- Circular dependencies and import hell
- Inconsistent async/sync patterns
- Empty files (advanced_api.py is 0 bytes)

### 3. Import Problems
- Try/except blocks for imports that should be guaranteed
- Missing exports requiring manual fixes
- Inconsistent import paths across the codebase

## Proposed Clean Architecture

```
src/graph_sitter/extensions/lsp/serena/
├── __init__.py           # Clean exports, no try/except blocks
├── types.py              # All type definitions (consolidated)
├── core.py               # Core Serena functionality
├── lsp_client.py         # LSP client and server management
├── diagnostics.py        # Error analysis and diagnostics
├── refactoring.py        # All refactoring operations
├── intelligence.py       # Symbol intelligence and search
├── integration.py        # Main integration with graph-sitter
└── utils.py              # Shared utilities
```

## Consolidation Steps

### Phase 1: Type System Cleanup
1. **Merge type definitions**:
   - Consolidate `types.py` + `serena_types.py` → `types.py`
   - Remove duplicate enums and dataclasses
   - Establish single source of truth for all types

### Phase 2: LSP Layer Consolidation  
2. **Merge LSP functionality**:
   - Consolidate `lsp/` subdirectory into `lsp_client.py`
   - Merge `lsp_integration.py` + `integration.py` → `integration.py`
   - Remove redundant server management code

### Phase 3: API Layer Simplification
3. **Consolidate API layers**:
   - Remove `advanced_api.py` (empty file)
   - Merge `api.py` functionality into `core.py`
   - Simplify public interface

### Phase 4: Feature Consolidation
4. **Merge feature modules**:
   - Consolidate `error_analysis.py` + `advanced_error_viewer.py` → `diagnostics.py`
   - Merge scattered refactoring code → `refactoring.py`
   - Consolidate intelligence features → `intelligence.py`

### Phase 5: Directory Cleanup
5. **Remove empty subdirectories**:
   - Merge useful code from subdirectories into main files
   - Remove empty or near-empty subdirectories
   - Clean up import paths

## Implementation Strategy

### Backward Compatibility
- Maintain import aliases in `__init__.py` during transition
- Use deprecation warnings for old import paths
- Gradual migration over multiple releases

### Testing Strategy
- Create comprehensive tests for consolidated modules
- Ensure all existing functionality is preserved
- Validate LSP integration remains intact

### Migration Order
1. Start with types (least risky)
2. Move to LSP client (self-contained)
3. Consolidate diagnostics (high impact)
4. Merge integration layers (most complex)
5. Clean up directories (final step)

## Expected Benefits

### Maintainability
- 80% reduction in file count (20+ files → 8 files)
- Clear module boundaries and responsibilities
- Elimination of circular dependencies

### Performance
- Faster imports (fewer modules to load)
- Reduced memory footprint
- Cleaner dependency graph

### Developer Experience
- Simpler import paths
- Clear API surface
- Better documentation possibilities
- Easier testing and debugging

## Risk Mitigation

### Breaking Changes
- Maintain backward-compatible imports during transition
- Document migration path for external users
- Provide clear deprecation timeline

### Integration Issues
- Extensive testing of LSP functionality
- Validation with existing graph-sitter integration
- Rollback plan if issues arise

## Success Metrics

- [ ] File count reduced from 20+ to 8
- [ ] All tests pass with consolidated structure
- [ ] No circular import dependencies
- [ ] LSP integration fully functional
- [ ] Import time improved by >50%
- [ ] Zero try/except import blocks in __init__.py
