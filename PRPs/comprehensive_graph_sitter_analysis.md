# Comprehensive Graph-Sitter Codebase Analysis Enhancement PRP

## Core Principles
- **Context is King**: Include ALL necessary documentation, examples, and caveats
- **Validation Loops**: Provide executable tests/lints the AI can run and fix
- **Information Dense**: Use keywords and patterns from the codebase
- **Progressive Success**: Start simple, validate, then enhance
- **Global rules**: Be sure to follow all rules in CLAUDE.md

## Goal
Upgrade the existing codebase analysis script to use **100% real graph-sitter infrastructure** and provide **absolutely complete analysis coverage** including:
- ALL unused parameters using real code block traversal
- ALL wrong call sites using actual parameter/argument matching
- ALL import issues using real import resolution system
- ALL symbol usages using actual graph-sitter symbol tracking
- ALL dependencies using real graph traversal
- ALL dead code using actual reachability analysis
- ALL entry points using real decorator and inheritance analysis

**End State**: Production-ready comprehensive analysis tool that provides actionable insights for any codebase using only real graph-sitter classes and methods.

## Why
**Business Value:**
- Developers get accurate, actionable insights about code quality issues
- Automated detection of dead code, unused parameters, and architectural problems
- Reduces manual code review time and catches issues before they reach production
- Provides quantitative metrics for technical debt assessment

**Integration with Existing Features:**
- Builds on existing graph-sitter infrastructure and examples
- Uses real `Codebase.from_repo()` loading patterns
- Follows established patterns from `delete_dead_code/run.py` and `repo_analytics/run.py`

**Problems This Solves:**
- Current script uses incomplete analysis methods
- Missing comprehensive parameter usage analysis
- Inadequate call site validation
- Limited import dependency analysis
- Incomplete dead code detection
- No real graph traversal for dependency analysis

## What
**User-Visible Behavior:**
- CLI tool that analyzes any GitHub repository or local codebase
- Comprehensive reports in text, JSON, or Markdown format
- Detailed findings with file locations and line numbers
- Actionable recommendations for code improvements
- Progress indicators during analysis
- Rich console output with color coding

**Technical Requirements:**
- Use only real graph-sitter classes: `Codebase`, `Function`, `Class`, `Symbol`, `SourceFile`
- Real property access: `function.usages`, `function.call_sites`, `function.decorators`
- Actual code block analysis: `function.code_block.statements`
- Real import resolution: `file.imports`, import dependency graphs
- Genuine graph traversal for reachability analysis
- Complete parameter usage detection within function scopes

## Success Criteria
- ✅ Zero mock functions - all analysis uses real graph-sitter infrastructure
- ✅ Detects 100% of unused parameters in functions
- ✅ Identifies all incorrect function call sites with argument mismatches
- ✅ Finds all import issues: unused, circular, unresolved
- ✅ Tracks all symbol usages throughout the codebase
- ✅ Maps complete dependency graphs between code elements
- ✅ Identifies all dead code through reachability analysis
- ✅ Finds all entry points including decorated functions and top-level classes
- ✅ Processes real repositories without errors
- ✅ Generates actionable reports with specific file/line locations

## All Needed Context

### Documentation & References
**MUST READ - Include these in your context window:**

- **file**: `examples/examples/delete_dead_code/run.py`
  **why**: Shows real usage of `function.usages`, `function.call_sites`, `function.decorators` patterns

- **file**: `examples/examples/repo_analytics/run.py`  
  **why**: Demonstrates `function.code_block.statements`, complexity analysis, real codebase loading

- **file**: `src/graph_sitter/core/codebase.py`
  **why**: Core Codebase class with real methods and properties

- **file**: `src/graph_sitter/core/function.py`
  **why**: Function class with actual `usages`, `call_sites`, `parameters`, `decorators` properties

- **file**: `src/graph_sitter/core/class_definition.py`
  **why**: Class definition with real `methods`, `attributes`, `superclasses` properties

- **file**: `src/graph_sitter/core/symbol.py`
  **why**: Base Symbol class with actual usage tracking and dependency methods

- **file**: `src/graph_sitter/codebase/codebase_analysis.py`
  **why**: Existing analysis functions to enhance, not replace

### Current Codebase Tree
```
src/graph_sitter/
├── core/
│   ├── codebase.py          # Main Codebase class
│   ├── function.py          # Function with real properties
│   ├── class_definition.py  # Class with real methods/attributes
│   ├── symbol.py           # Base Symbol with usage tracking
│   └── file.py             # SourceFile with imports
├── codebase/
│   └── codebase_analysis.py # Existing analysis functions
└── examples/examples/
    ├── delete_dead_code/run.py    # Real dead code detection
    └── repo_analytics/run.py      # Real complexity analysis
```

### Desired Codebase Tree
```
enhanced_analysis.py                    # Main enhanced analysis script
├── analyzers/
│   ├── __init__.py
│   ├── base_analyzer.py               # Base analyzer class
│   ├── dead_code_analyzer.py          # Real dead code detection
│   ├── parameter_analyzer.py          # Real unused parameter detection
│   ├── call_site_analyzer.py          # Real call site validation
│   ├── import_analyzer.py             # Real import analysis
│   ├── dependency_analyzer.py         # Real dependency mapping
│   └── entry_point_analyzer.py        # Real entry point detection
├── models/
│   ├── __init__.py
│   ├── analysis_result.py             # Result data models
│   └── code_issue.py                  # Issue representation
└── tests/
    ├── test_analyzers.py              # Real analyzer tests
    └── test_integration.py            # Integration tests with real repos
```

## Known Gotchas & Library Quirks

**CRITICAL: graph-sitter requires specific property access patterns**
- Use `function.usages` not `function.get_usages()`
- Access `function.call_sites` directly, not through methods
- `function.code_block.statements` provides real statement analysis
- `class.superclasses` gives actual inheritance, not `class.parents`

**CRITICAL: Real codebase loading patterns**
- Use `Codebase.from_repo('owner/repo')` for GitHub repos
- Use `Codebase('/path/to/repo')` for local repos
- Configure with `CodebaseConfig` for comprehensive analysis
- Handle loading errors gracefully - repos may have parsing issues

**CRITICAL: Symbol resolution and usage tracking**
- `symbol.symbol_usages` provides actual usage locations
- Import resolution through `file.imports` and `import.imported_symbol`
- Function calls via `statement.function_calls` in code blocks
- Parameter usage requires traversing `function.code_block` scope

## Implementation Blueprint

### Data Models and Structure
Create comprehensive data models for type safety and consistency:

**Pydantic Models:**
- `AnalysisResult` - Complete analysis results
- `CodeIssue` - Individual code issues with severity
- `DeadCodeItem` - Dead code findings
- `EntryPoint` - Entry point identification
- `DependencyGraph` - Code dependency relationships

### Task List (In Order)

**Task 1: CREATE analyzers/base_analyzer.py**
- MIRROR pattern from: `examples/examples/repo_analytics/run.py`
- CREATE base class with real codebase loading
- IMPLEMENT progress tracking and error handling
- PRESERVE existing graph-sitter configuration patterns

**Task 2: ENHANCE analyzers/dead_code_analyzer.py**
- MIRROR pattern from: `examples/examples/delete_dead_code/run.py`
- USE real `function.usages` and `function.call_sites` properties
- IMPLEMENT graph traversal from entry points
- DETECT unreachable functions, classes, and variables

**Task 3: CREATE analyzers/parameter_analyzer.py**
- USE real `function.parameters` and `function.code_block.statements`
- TRAVERSE function scope to find parameter usage
- IDENTIFY unused parameters excluding `self`, `cls`, `*args`, `**kwargs`
- HANDLE method vs function parameter patterns

**Task 4: CREATE analyzers/call_site_analyzer.py**
- USE real `statement.function_calls` from code blocks
- MATCH call arguments with function parameters
- VALIDATE argument count and types where possible
- DETECT undefined function calls

**Task 5: CREATE analyzers/import_analyzer.py**
- USE real `file.imports` and import resolution
- BUILD dependency graph with networkx
- DETECT circular imports using strongly connected components
- FIND unused and unresolved imports

**Task 6: CREATE analyzers/dependency_analyzer.py**
- TRAVERSE real symbol dependencies
- MAP complete dependency relationships
- IDENTIFY architectural issues and coupling
- GENERATE dependency visualization data

**Task 7: CREATE analyzers/entry_point_analyzer.py**
- USE real `function.decorators` for CLI/web entry points
- ANALYZE `class.superclasses` for inheritance hierarchies
- IDENTIFY main functions and top-level classes
- DETECT exported symbols and public APIs

**Task 8: INTEGRATE enhanced_analysis.py**
- ORCHESTRATE all analyzers with real codebase
- IMPLEMENT progress tracking and error handling
- GENERATE comprehensive reports
- SUPPORT multiple output formats

### Per Task Pseudocode

#### Task 2: Dead Code Analyzer
```python
def detect_dead_code(codebase: Codebase) -> List[DeadCodeItem]:
    # PATTERN: Start from real entry points (see delete_dead_code/run.py)
    entry_points = identify_entry_points(codebase)
    reachable = set()
    
    # CRITICAL: Use actual graph traversal
    for entry_point in entry_points:
        # REAL: Use function.usages and function.call_sites
        if hasattr(entry_point, 'usages'):
            for usage in entry_point.usages:
                reachable.add(usage.symbol)
    
    # REAL: Check all functions for reachability
    dead_functions = []
    for func in codebase.functions:
        # PATTERN: Skip test files (see delete_dead_code/run.py)
        if "test" in func.file.filepath:
            continue
            
        # REAL: Use actual properties
        if not func.usages and not func.call_sites and not func.decorators:
            dead_functions.append(DeadCodeItem(
                name=func.name,
                filepath=func.file.filepath,
                type="function",
                reason="No usages or call sites found"
            ))
    
    return dead_functions
```

#### Task 3: Parameter Analyzer
```python
def detect_unused_parameters(codebase: Codebase) -> List[CodeIssue]:
    # REAL: Use actual function properties
    issues = []
    
    for func in codebase.functions:
        # PATTERN: Skip test files and decorated functions
        if "test" in func.file.filepath or func.decorators:
            continue
            
        # REAL: Use actual parameters and code block
        for param in func.parameters:
            if param.name in ["self", "cls"] or param.name.startswith("*"):
                continue
                
            # CRITICAL: Traverse real code block for usage
            param_used = False
            if hasattr(func, 'code_block') and func.code_block:
                for stmt in func.code_block.statements:
                    # REAL: Check symbol usages in statements
                    for usage in stmt.symbol_usages:
                        if usage.name == param.name:
                            param_used = True
                            break
            
            if not param_used:
                issues.append(CodeIssue(
                    filepath=func.file.filepath,
                    line_number=param.start_position.line,
                    issue_type="Unused Parameter",
                    message=f"Parameter '{param.name}' is never used",
                    severity=IssueSeverity.MINOR
                ))
    
    return issues
```

## Integration Points

**CODEBASE LOADING:**
- pattern: `codebase = Codebase.from_repo('owner/repo', config=CodebaseConfig(...))`
- config: Enable all analysis flags for comprehensive coverage

**PROGRESS TRACKING:**
- add to: Rich Progress bars for each analysis phase
- pattern: `with Progress() as progress: task = progress.add_task(...)`

**ERROR HANDLING:**
- pattern: Graceful handling of parsing errors and missing properties
- logging: Detailed error messages with file context

## Validation Loop

### Level 1: Syntax & Style
```bash
# Run these FIRST - fix any errors before proceeding
ruff check enhanced_analysis.py --fix  # Auto-fix what's possible
mypy enhanced_analysis.py              # Type checking

# Expected: No errors. If errors, READ the error and fix.
```

### Level 2: Unit Tests
```python
# CREATE test_analyzers.py with real codebase tests:
def test_dead_code_detection():
    """Test with real small repository"""
    codebase = Codebase.from_repo('simple-test/repo')
    analyzer = DeadCodeAnalyzer(codebase)
    results = analyzer.analyze()
    
    # REAL: Validate actual results
    assert len(results) > 0
    assert all(isinstance(item, DeadCodeItem) for item in results)

def test_parameter_analysis():
    """Test unused parameter detection"""
    codebase = Codebase.from_repo('test-repo/unused-params')
    analyzer = ParameterAnalyzer(codebase)
    issues = analyzer.analyze()
    
    # REAL: Check for actual unused parameters
    unused_param_issues = [i for i in issues if i.issue_type == "Unused Parameter"]
    assert len(unused_param_issues) > 0

# Run and iterate until passing:
python -m pytest test_analyzers.py -v
# If failing: Read error, understand root cause, fix code, re-run (never mock to pass)
```

### Level 3: Integration Test
```bash
# Test with real repository
python enhanced_analysis.py fastapi/fastapi --output-format=json

# Expected: Complete analysis results with all categories populated
# If error: Check logs and handle real graph-sitter parsing issues
```

## Final Validation Checklist
- ✅ All tests pass: `python -m pytest tests/ -v`
- ✅ No linting errors: `ruff check enhanced_analysis.py`
- ✅ No type errors: `mypy enhanced_analysis.py`
- ✅ Real repository test successful: `python enhanced_analysis.py django/django`
- ✅ All analysis categories return results
- ✅ Error cases handled gracefully
- ✅ Output formats work correctly
- ✅ Performance acceptable for large repositories

## Anti-Patterns to Avoid
❌ **Don't create mock functions** - use only real graph-sitter infrastructure
❌ **Don't skip validation** because "it should work" - test with real repos
❌ **Don't ignore parsing errors** - handle them gracefully
❌ **Don't use hardcoded assumptions** - rely on actual graph-sitter properties
❌ **Don't catch all exceptions** - be specific about error handling
❌ **Don't assume property existence** - check with hasattr() before access
❌ **Don't ignore test files** - they often contain different patterns
❌ **Don't forget edge cases** - empty functions, abstract methods, decorators
