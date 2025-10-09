# Implementation Guide for Graph-Sitter Refactoring

## Quick Reference: File Consolidation Plan

### Target Architecture

```
src/
├── analysis_utils.py          [✅ DONE] - Shared utilities
├── protocols.py                [✅ DONE] - Interface definitions
├── graph_sitter_adapter.py     [TODO] - Unified graph-sitter interface
├── autogenlib_adapter.py       [TODO] - Unified AI resolution
├── lib_analysis.py             [TODO] - Tool integrations (ruff, mypy, etc.)
├── main_analysis.py            [TODO] - CLI entry point
├── lsp_diagnostics.py          [ENHANCE] - Enhanced diagnostics manager
└── config.py                   [TODO] - Configuration management
```

### Migration Map

#### graph_sitter_adapter.py Sources:
- `graph_sitter_analysis.py` (1,675 lines) → Core analysis methods
- `graph_sitter_backend.py` (3,954 lines) → Backend implementation

**Key Classes to Consolidate:**
```python
# From graph_sitter_analysis.py
class GraphSitterAnalyzer:
    - get_codebase_overview()
    - get_file_details()
    - get_function_details()
    - get_class_details()
    - create_blast_radius_visualization()
    - create_call_trace_visualization()
    - find_dead_code()

# From graph_sitter_backend.py
class AnalysisEngine:
    - _analyze_errors_with_graph_sitter_enhanced()
    - _analyze_entrypoints_with_graph_sitter_enhanced()

# Merge into:
class GraphSitterAdapter:
    # Public API (from GraphSitterAnalyzerProtocol)
    # Private helpers (consolidated backend logic)
```

#### autogenlib_adapter.py Sources:
- `autogenlib_context.py` (569 lines) → Context generation
- `autogenlib_ai_resolve.py` (557 lines) → AI resolution

**Key Functions to Consolidate:**
```python
# From autogenlib_context.py
- get_ai_fix_context()
- get_llm_codebase_overview()
- get_comprehensive_symbol_context()

# From autogenlib_ai_resolve.py
- resolve_diagnostic_with_ai()
- resolve_runtime_error_with_ai()
- resolve_multiple_errors_with_ai()

# Merge into:
class AutoGenLibAdapter:
    def __init__(self, codebase, graph_sitter_adapter, lsp_manager)
    def resolve_error(self, error) -> dict
    def get_error_context(self, error) -> dict
    def resolve_multiple_errors(self, errors) -> list
```

#### lib_analysis.py Sources:
- `analysis.py` → RuffIntegration, LSPDiagnosticsCollector
- `analysisbig.py` → (Comprehensive analysis - has syntax error)

**Target Structure:**
```python
class BaseToolAnalyzer(ABC):
    @abstractmethod
    def analyze(self, target) -> list[AnalysisError]
    
class RuffAnalyzer(BaseToolAnalyzer):
    # Migrated from analysis.py RuffIntegration
    
class MypyAnalyzer(BaseToolAnalyzer):
    # New implementation
    
class PyRightAnalyzer(BaseToolAnalyzer):
    # New implementation
    
class AnalysisOrchestrator:
    # Coordinates multiple analyzers
```

---

## Implementation Strategy

### Phase 2A: GraphSitterAdapter (Steps 4-7)

**Step 4: Skeleton Structure**
```python
class GraphSitterAdapter:
    def __init__(self, codebase: Codebase):
        self.codebase = codebase
        self._graph = None  # NetworkX graph
        self._cache = {}
    
    # Protocol methods (stubs)
    def get_codebase_overview(self) -> dict: ...
    def get_file_details(self, path) -> dict: ...
    # etc.
```

**Step 5-6: Core Migration**
Priority methods to migrate first:
1. `get_codebase_overview()` - Most commonly used
2. `get_file_details()` - File analysis
3. `get_function_details()` - Function metrics
4. Backend parsing logic (private methods)

**Step 7: Visualizations**
- Use existing Plotly integration
- Consolidate from both files
- Add caching layer

### Phase 2B: AutoGenLibAdapter (Steps 8-11)

**Step 8: Skeleton Structure**
```python
class AutoGenLibAdapter:
    def __init__(
        self,
        codebase: Codebase,
        graph_sitter_adapter: GraphSitterAdapter,
        lsp_manager: LSPDiagnosticsManager,
        ai_config: dict = None
    ):
        self.codebase = codebase
        self.gs_adapter = graph_sitter_adapter
        self.lsp_manager = lsp_manager
        self.ai_config = ai_config or {}
        self._client = None  # OpenAI/Anthropic client
    
    def resolve_error(self, error) -> dict: ...
    def get_error_context(self, error) -> dict: ...
```

**Step 9-10: Context & Resolution**
Merge workflow:
1. Context gathering (from autogenlib_context.py)
2. AI prompt construction
3. Fix generation (from autogenlib_ai_resolve.py)
4. Fix validation

**Step 11: AI Configuration**
Support multiple providers:
- OpenAI (gpt-4, gpt-3.5-turbo)
- Anthropic (claude-3-opus, claude-3-sonnet)
- Local models (via ollama)

---

## CLI Design (main_analysis.py)

### Command Structure

```bash
# Repository analysis
python -m main_analysis --repo /path/to/repo
python -m main_analysis --repo /path/to/repo --tools ruff,mypy
python -m main_analysis --repo /path/to/repo --format json

# File analysis
python -m main_analysis --code /path/to/file.py
python -m main_analysis --code /path/to/file.py --tools all

# AI resolution
python -m main_analysis --resolve
python -m main_analysis --resolve --auto  # Non-interactive
python -m main_analysis --code file.py --resolve
```

### Implementation Outline

```python
import click
from rich.console import Console
from graph_sitter_adapter import GraphSitterAdapter
from autogenlib_adapter import AutoGenLibAdapter
from lib_analysis import AnalysisOrchestrator

@click.command()
@click.option('--repo', help='Repository path')
@click.option('--code', help='Single file path')
@click.option('--resolve', is_flag=True, help='AI resolution mode')
@click.option('--tools', default='all', help='Tools to run')
@click.option('--format', default='text', type=click.Choice(['text', 'json', 'html']))
def main(repo, code, resolve, tools, format):
    console = Console()
    
    if repo:
        run_repo_analysis(repo, tools, format, console)
    elif code:
        run_file_analysis(code, tools, format, console, resolve)
    elif resolve:
        run_resolution_mode(console)
    else:
        click.echo("Specify --repo, --code, or --resolve")
```

---

## Testing Strategy

### Unit Tests
```python
# tests/unit/test_graph_sitter_adapter.py
def test_get_codebase_overview():
    adapter = GraphSitterAdapter(sample_codebase)
    overview = adapter.get_codebase_overview()
    assert 'total_files' in overview
    assert overview['total_files'] > 0

# tests/unit/test_autogenlib_adapter.py
@mock.patch('openai.ChatCompletion.create')
def test_resolve_error(mock_openai):
    mock_openai.return_value = {...}
    adapter = AutoGenLibAdapter(...)
    result = adapter.resolve_error(sample_error)
    assert result['fix_code']
    assert result['confidence'] > 0
```

### Integration Tests
```python
# tests/integration/test_full_workflow.py
def test_analyze_and_resolve_workflow():
    # 1. Analyze with graph-sitter
    gs_adapter = GraphSitterAdapter(codebase)
    overview = gs_adapter.get_codebase_overview()
    
    # 2. Run tool analysis
    orchestrator = AnalysisOrchestrator()
    errors = orchestrator.run_analysis(target_path)
    
    # 3. Resolve with AI
    ai_adapter = AutoGenLibAdapter(...)
    fixes = ai_adapter.resolve_multiple_errors(errors[:5])
    
    assert len(fixes) > 0
```

---

## Backward Compatibility

### Deprecation Warnings

```python
# In old graph_sitter_analysis.py
import warnings

class GraphSitterAnalyzer:
    def __init__(self, *args, **kwargs):
        warnings.warn(
            "GraphSitterAnalyzer is deprecated. "
            "Use GraphSitterAdapter from graph_sitter_adapter instead.",
            DeprecationWarning,
            stacklevel=2
        )
        # Delegate to new adapter
        from graph_sitter_adapter import GraphSitterAdapter
        self._adapter = GraphSitterAdapter(*args, **kwargs)
    
    def get_codebase_overview(self):
        return self._adapter.get_codebase_overview()
```

---

## Performance Considerations

### Caching Strategy
```python
from functools import lru_cache

class GraphSitterAdapter:
    @lru_cache(maxsize=128)
    def get_file_details(self, file_path: str) -> dict:
        # Expensive operation cached
        ...
    
    def _invalidate_cache(self, file_path: str = None):
        if file_path:
            # Selective cache invalidation
            self.get_file_details.cache_clear()
```

### Parallel Execution
```python
from concurrent.futures import ThreadPoolExecutor

class AnalysisOrchestrator:
    def run_analysis(self, target, tools=None, parallel=True):
        if parallel:
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = {
                    executor.submit(tool.analyze, target): tool
                    for tool in self.enabled_tools
                }
                # Collect results as they complete
        else:
            # Sequential execution
```

---

## Configuration File Format

### .analysis.toml
```toml
[tools]
enabled = ["ruff", "mypy", "pyright"]

[tools.ruff]
config_file = "ruff.toml"
timeout = 300

[tools.mypy]
strict = true
config_file = "mypy.ini"

[ai]
provider = "openai"  # or "anthropic", "ollama"
model = "gpt-4"
temperature = 0.2
max_tokens = 2000

[ai.openai]
api_key_env = "OPENAI_API_KEY"

[output]
format = "text"  # or "json", "html"
show_fixes = true
max_errors = 100

[resolution]
auto_apply = false
confidence_threshold = 0.8
```

---

## Next Steps for Continuation

1. **Fix analysisbig.py syntax error** - Required for full consolidation
2. **Implement GraphSitterAdapter skeleton** - Foundation for Phase 2
3. **Migrate core analysis methods** - Essential functionality
4. **Create AutoGenLibAdapter** - AI integration
5. **Build lib_analysis.py** - Tool integrations
6. **Develop main_analysis.py CLI** - User interface

---

## Code Size Estimates

| File | Estimated Lines | Status |
|------|----------------|--------|
| graph_sitter_adapter.py | ~3,500 | TODO |
| autogenlib_adapter.py | ~800 | TODO |
| lib_analysis.py | ~1,200 | TODO |
| main_analysis.py | ~600 | TODO |
| config.py | ~200 | TODO |
| **Total New Code** | **~6,300** | |
| **Old Code to Remove** | **~11,000** | Phase 7 |
| **Net Reduction** | **~4,700 lines** | 35% |

---

This guide provides the roadmap for completing the remaining 27 steps. Each section can be expanded into full implementation as work progresses.

