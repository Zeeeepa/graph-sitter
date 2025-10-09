# Integrated Analysis - Complete Code Analysis Framework

The Integrated Analysis module provides a unified interface for comprehensive codebase analysis, combining:

1. **Graph-sitter** - AST analysis, symbols, dependencies
2. **SolidLSP** - Type checking and diagnostics via Language Server Protocol
3. **AutoGenLib** - AI-powered error resolution

## Quick Start

```python
from integrated_analysis import analyze_repository

# Run full analysis with one line
results = analyze_repository("./my-project")

print(f"Files: {results.file_count}")
print(f"Errors: {len(results.errors)}")
print(f"Functions: {results.function_count}")
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  IntegratedAnalyzer                          │
│                                                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────────────┐   │
│  │  Codebase  │  │ LSPAdapter │  │ AutoGenLibAdapter  │   │
│  │ (graph-    │  │ (solidlsp) │  │  (AI fixes)        │   │
│  │  sitter)   │  │            │  │                    │   │
│  └────────────┘  └────────────┘  └────────────────────┘   │
│        │               │                    │               │
│        ▼               ▼                    ▼               │
│   Structure       Diagnostics           AI Fixes            │
│   Analysis        (errors/warnings)     (optional)          │
└─────────────────────────────────────────────────────────────┘
```

## Installation

The integrated analyzer uses existing graph-sitter infrastructure:

```bash
# Install graph-sitter with LSP support
pip install graph-sitter[lsp]

# For AI-powered fixes (optional)
pip install openai
export OPENAI_API_KEY="your-key-here"
```

## Usage Patterns

### Pattern 1: Structural Analysis Only

Fast analysis focusing on code structure:

```python
from integrated_analysis import IntegratedAnalyzer

analyzer = IntegratedAnalyzer(
    "./my-repo",
    enable_lsp=False,  # Disable for speed
    enable_autogenlib=False
)

# Analyze structure
structure = analyzer.analyze_structure()

print(f"Files: {structure['file_count']}")
print(f"Functions: {structure['function_count']}")
print(f"Classes: {structure['class_count']}")

# Access dependency graph
for file, deps in structure['dependencies'].items():
    print(f"{file}: {len(deps)} dependencies")
```

### Pattern 2: Diagnostics Collection

Get type errors, linting issues, etc.:

```python
analyzer = IntegratedAnalyzer(
    "./my-repo",
    enable_lsp=True  # Enable LSP diagnostics
)

# Get all diagnostics
diagnostics = analyzer.get_diagnostics()

# Categorized by severity
errors = diagnostics['errors']
warnings = diagnostics['warnings']
info = diagnostics['info']

# Process errors
for error in errors:
    print(f"{error.file_path}:{error.line} - {error.message}")
```

### Pattern 3: Full Analysis Pipeline

Complete analysis in one call:

```python
from integrated_analysis import analyze_repository

results = analyze_repository(
    "./my-repo",
    enable_lsp=True,
    enable_autogenlib=False
)

# AnalysisResults dataclass with everything
print(f"Files: {results.file_count}")
print(f"Functions: {results.function_count}")
print(f"Errors: {len(results.errors)}")
print(f"Dependencies: {len(results.dependency_graph)}")
```

### Pattern 4: AI-Powered Error Resolution

Generate and apply fixes using AI:

```python
analyzer = IntegratedAnalyzer(
    "./my-repo",
    enable_lsp=True,
    enable_autogenlib=True  # Requires OPENAI_API_KEY
)

# Get diagnostics
diagnostics = analyzer.get_diagnostics()

# Generate AI fixes for top errors
fixes = analyzer.generate_fixes(
    diagnostics['errors'],
    max_fixes=10
)

# Review and apply
for fix_data in fixes:
    diag = fix_data['diagnostic']
    fix = fix_data['fix']
    
    print(f"Error: {diag.message}")
    print(f"Fix: {fix['description']}")
    print(f"Code: {fix['code']}")
    
# Apply all fixes
applied_count = analyzer.apply_fixes(fixes)
print(f"Applied {applied_count} fixes")
```

## API Reference

### IntegratedAnalyzer

Main analysis class combining all tools.

#### Constructor

```python
IntegratedAnalyzer(
    repo_path: str,
    enable_lsp: bool = True,
    enable_autogenlib: bool = False,
    lsp_servers: Optional[List[str]] = None
)
```

**Parameters:**
- `repo_path` - Path to repository to analyze
- `enable_lsp` - Enable LSP diagnostics (default: True)
- `enable_autogenlib` - Enable AI fixes (default: False, requires OpenAI)
- `lsp_servers` - LSP servers to use (default: ["pyright"])

#### Methods

##### analyze_structure()

```python
def analyze_structure() -> Dict[str, Any]
```

Analyze code structure using graph-sitter.

**Returns:** Dictionary with:
- `file_count` - Number of files
- `function_count` - Number of functions
- `class_count` - Number of classes  
- `dependencies` - Dependency graph {file: [deps]}
- `files` - List of file paths
- `summary` - High-level summary

##### get_diagnostics()

```python
def get_diagnostics() -> Dict[str, List[Diagnostic]]
```

Get LSP diagnostics (requires `enable_lsp=True`).

**Returns:** Dictionary with:
- `errors` - List of Diagnostic objects (severity: error)
- `warnings` - List of Diagnostic objects (severity: warning)
- `info` - List of Diagnostic objects (severity: info/hint)

##### generate_fixes()

```python
def generate_fixes(
    diagnostics: Optional[List[Diagnostic]] = None,
    max_fixes: int = 10
) -> List[Dict[str, Any]]
```

Generate AI-powered fixes (requires `enable_autogenlib=True`).

**Parameters:**
- `diagnostics` - Diagnostics to fix (default: all errors)
- `max_fixes` - Maximum fixes to generate

**Returns:** List of fix dictionaries with:
- `diagnostic` - Original Diagnostic object
- `fix` - Fix details (code, description, etc.)
- `context` - Context used for generation

##### apply_fixes()

```python
def apply_fixes(fixes: List[Dict[str, Any]]) -> int
```

Apply generated fixes to codebase.

**Parameters:**
- `fixes` - Fixes from `generate_fixes()`

**Returns:** Number of fixes successfully applied

##### full_analysis()

```python
def full_analysis(
    generate_fixes: bool = False,
    max_fixes: int = 10
) -> AnalysisResults
```

Run complete analysis pipeline.

**Parameters:**
- `generate_fixes` - Generate AI fixes for errors
- `max_fixes` - Maximum fixes to generate

**Returns:** `AnalysisResults` dataclass with all data

##### health_check()

```python
def health_check() -> Dict[str, bool]
```

Check health of all components.

**Returns:** Dictionary with component status:
- `codebase` - Graph-sitter codebase initialized
- `lsp` - LSP adapter initialized
- `autogenlib` - AutoGenLib adapter initialized

### AnalysisResults

Dataclass containing complete analysis results.

```python
@dataclass
class AnalysisResults:
    # Structural data
    file_count: int
    function_count: int
    class_count: int
    symbol_count: int
    dependency_graph: Dict[str, List[str]]
    
    # Diagnostics
    errors: List[Diagnostic]
    warnings: List[Diagnostic]
    info: List[Diagnostic]
    
    # AI fixes (optional)
    suggested_fixes: Optional[List[Dict[str, Any]]] = None
    
    # Raw data
    raw_structure: Optional[Dict] = None
    raw_diagnostics: Optional[Dict] = None
```

### Diagnostic

LSP diagnostic object.

```python
@dataclass
class LSPDiagnostic:
    file_path: str
    line: int
    column: int
    end_line: int
    end_column: int
    severity: str  # "error", "warning", "information", "hint"
    message: str
    code: Optional[str] = None
    source: str = "lsp"
```

### Convenience Functions

#### analyze_repository()

```python
def analyze_repository(
    repo_path: str,
    enable_lsp: bool = True,
    enable_autogenlib: bool = False,
    generate_fixes: bool = False,
    max_fixes: int = 10
) -> AnalysisResults
```

Quick analysis with sensible defaults.

**Example:**
```python
results = analyze_repository("./my-project")
```

## Integration with Existing Tools

### Using with graph-sitter Codebase

```python
from graph_sitter import Codebase
from integrated_analysis import IntegratedAnalyzer

# Create codebase
codebase = Codebase("./my-repo")

# Use with integrated analyzer
analyzer = IntegratedAnalyzer("./my-repo")

# Codebase is available
assert analyzer.codebase.files == codebase.files
```

### Using with LSP Adapter

```python
from lsp_adapter import LSPAdapter
from integrated_analysis import IntegratedAnalyzer

# Direct LSP adapter usage
lsp = LSPAdapter("./my-repo")
diagnostics = lsp.get_all_diagnostics()

# Or via integrated analyzer
analyzer = IntegratedAnalyzer("./my-repo", enable_lsp=True)
diagnostics = analyzer.get_diagnostics()
```

### Using with AutoGenLib Adapter

```python
from autogenlib_adapter import AutoGenLibAdapter
from integrated_analysis import IntegratedAnalyzer

# Direct AutoGenLib usage
autogenlib = AutoGenLibAdapter(codebase_path="./my-repo")

# Or via integrated analyzer  
analyzer = IntegratedAnalyzer(
    "./my-repo",
    enable_autogenlib=True
)
```

## Performance Considerations

### Fast Analysis (< 1 second)

```python
# Disable LSP for speed
analyzer = IntegratedAnalyzer(
    repo_path,
    enable_lsp=False,
    enable_autogenlib=False
)
structure = analyzer.analyze_structure()
```

### Medium Analysis (< 10 seconds)

```python
# Enable LSP, disable AI
analyzer = IntegratedAnalyzer(
    repo_path,
    enable_lsp=True,
    enable_autogenlib=False
)
results = analyzer.full_analysis(generate_fixes=False)
```

### Complete Analysis (10-60 seconds)

```python
# All features enabled
results = analyze_repository(
    repo_path,
    enable_lsp=True,
    enable_autogenlib=True,
    generate_fixes=True,
    max_fixes=20
)
```

## Error Handling

The analyzer gracefully handles component failures:

```python
analyzer = IntegratedAnalyzer("./my-repo")

# Check what's available
health = analyzer.health_check()
if not health['lsp']:
    print("LSP not available, diagnostics will be empty")

# Analysis continues even if components fail
results = analyzer.full_analysis()  # Works with available components
```

## Examples

See `examples/integrated_analysis_example.py` for complete examples:

```bash
# Run all examples
python examples/integrated_analysis_example.py

# Run specific example
python examples/integrated_analysis_example.py --example 2
```

## Troubleshooting

### Import Errors

```python
# Add src to path if needed
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from integrated_analysis import IntegratedAnalyzer
```

### LSP Not Working

```bash
# Check LSP servers are installed
pip install pyright pylsp ruff-lsp

# Check in code
analyzer = IntegratedAnalyzer("./repo", enable_lsp=True)
if not analyzer.lsp_adapter:
    print("LSP failed to initialize")
```

### AI Fixes Not Working

```bash
# Check OpenAI API key
export OPENAI_API_KEY="your-key"

# Check AutoGenLib
pip install openai

# Check in code
analyzer = IntegratedAnalyzer("./repo", enable_autogenlib=True)
if not analyzer.autogenlib_adapter:
    print("AutoGenLib failed to initialize")
```

## Comparison with Other Tools

### vs. Raw graph-sitter

| Feature | graph-sitter | IntegratedAnalyzer |
|---------|-------------|-------------------|
| AST Analysis | ✅ | ✅ |
| Type Checking | ❌ | ✅ (via LSP) |
| Linting | ❌ | ✅ (via LSP) |
| AI Fixes | ❌ | ✅ (optional) |
| Unified API | ❌ | ✅ |

### vs. Individual Adapters

| Feature | Individual | Integrated |
|---------|-----------|-----------|
| Manual integration | ✅ | ❌ (automatic) |
| Separate calls | ✅ | ❌ (one call) |
| Error handling | Manual | Automatic |
| Complete results | Manual assembly | Single object |

## Future Enhancements

Planned features:
- [ ] HTML/JSON report generation
- [ ] Incremental analysis
- [ ] Custom LSP server configuration
- [ ] Plugin system for custom analyzers
- [ ] Performance profiling integration
- [ ] Security vulnerability scanning
- [ ] Code complexity metrics
- [ ] Test coverage analysis

## Contributing

To extend the IntegratedAnalyzer:

1. Add new adapter in `src/your_tool_adapter.py`
2. Import in `integrated_analysis.py`
3. Add to `__init__()` method
4. Add analysis method
5. Update `full_analysis()` to include new data
6. Add to `health_check()`
7. Update documentation

## License

Same as graph-sitter project.

