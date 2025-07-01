# 🛠️ Implementation Plan: graph_sitter/codebase Optimization

## 🎯 Overview

This document provides a detailed implementation plan for optimizing the `graph_sitter/codebase` component based on the comprehensive analysis. The plan is organized by priority and includes specific code changes, testing strategies, and validation criteria.

## 🚨 Phase 1: Critical Fixes (High Priority)

### 1.1 Transaction Performance Optimization

**File**: `src/graph_sitter/codebase/transaction_manager.py`

**Issue**: Unsorted list causing performance degradation
```python
# Current implementation (line 35)
queued_transactions: dict[Path, list[Transaction]]
```

**Solution**:
```python
# Add import
from sortedcontainers import SortedList

# Replace in __init__ method
def __init__(self) -> None:
    self.queued_transactions = defaultdict(lambda: SortedList(key=Transaction._to_sort_key))
    self.pending_undos = set()

# Update sort_transactions method
def sort_transactions(self) -> None:
    # No longer needed as SortedList maintains order automatically
    pass
```

**Testing**: Performance benchmarks with 1000+ transactions

### 1.2 Null Safety in Codeowner Parsing

**File**: `src/graph_sitter/codebase/flagging/groupers/codeowner_grouper.py`

**Issue**: Potential null pointer exception
```python
# Current problematic code
flag_owners = repo_operator.codeowners_parser.of(flag.filepath)  # TODO: handle codeowners_parser could be null
```

**Solution**:
```python
def _get_flag_owners(self, flag) -> list:
    """Safely get flag owners with null checking."""
    if not hasattr(self.repo_operator, 'codeowners_parser') or self.repo_operator.codeowners_parser is None:
        logger.warning(f"Codeowners parser not available for {flag.filepath}")
        return []
    
    try:
        return self.repo_operator.codeowners_parser.of(flag.filepath)
    except Exception as e:
        logger.error(f"Error parsing codeowners for {flag.filepath}: {e}")
        return []
```

### 1.3 Complete Group Creation Implementation

**File**: `src/graph_sitter/codebase/flagging/groupers/codeowner_grouper.py`

**Issue**: Missing implementation
```python
# Current code
msg = "TODO: implement single group creation"
raise NotImplementedError(msg)
```

**Solution**:
```python
def create_single_group(self, flag: CodeFlag) -> Group:
    """Create a single group for the given flag."""
    flag_owners = self._get_flag_owners(flag)
    
    if not flag_owners:
        # Fallback to default group
        return Group(
            flags=[flag],
            name=f"unowned_{flag.filepath.stem}",
            description=f"Unowned file: {flag.filepath}"
        )
    
    return Group(
        flags=[flag],
        name=f"owned_by_{'_'.join(flag_owners)}",
        description=f"Owned by: {', '.join(flag_owners)}"
    )
```

### 1.4 TypeScript AST Accuracy Improvements

**File**: `src/graph_sitter/codebase/node_classes/ts_node_classes.py`

**Issue**: Inaccurate type handling
```python
# Current problematic mappings
"type_identifier": Name,  # HACK
"intersection_type": TSUnionType,  # TODO: Not accurate, implement this properly
```

**Solution**:
```python
# Create proper TypeScript type classes
class TSTypeIdentifier(Name):
    """Proper TypeScript type identifier handling."""
    
    def __init__(self, node, file_node_id, ctx, parent):
        super().__init__(node, file_node_id, ctx, parent)
        self.is_type_reference = True

class TSIntersectionType(Expression):
    """Proper TypeScript intersection type handling."""
    
    def __init__(self, node, file_node_id, ctx, parent):
        super().__init__(node, file_node_id, ctx, parent)
        self.intersection_types = self._parse_intersection_types()
    
    def _parse_intersection_types(self):
        """Parse individual types in the intersection."""
        types = []
        for child in self.node.named_children:
            if child.type in TSExpressionMap:
                types.append(TSExpressionMap[child.type](child, self.file_node_id, self.ctx, self))
        return types

# Update mappings
TSExpressionMap.update({
    "type_identifier": TSTypeIdentifier,
    "intersection_type": TSIntersectionType,
})
```

## ⚡ Phase 2: Performance Optimization (Medium Priority)

### 2.1 Memory Usage Optimization

**File**: `src/graph_sitter/codebase/codebase_context.py`

**Enhancement**: Implement lazy loading for large codebases

```python
from functools import lru_cache
from weakref import WeakValueDictionary

class CodebaseContext:
    def __init__(self):
        # Use weak references for cached objects
        self._file_cache = WeakValueDictionary()
        self._symbol_cache = WeakValueDictionary()
        
    @lru_cache(maxsize=1000)
    def get_file_cached(self, file_path: Path):
        """Cached file retrieval with LRU eviction."""
        if file_path in self._file_cache:
            return self._file_cache[file_path]
        
        file_obj = self._load_file(file_path)
        self._file_cache[file_path] = file_obj
        return file_obj
    
    def clear_cache(self):
        """Clear caches to free memory."""
        self._file_cache.clear()
        self._symbol_cache.clear()
        self.get_file_cached.cache_clear()
```

### 2.2 Enhanced Error Recovery

**File**: `src/graph_sitter/codebase/validation.py`

**Enhancement**: Add comprehensive error recovery

```python
import time
from typing import Optional
from dataclasses import dataclass

@dataclass
class ValidationResult:
    status: PostInitValidationStatus
    errors: list[str]
    warnings: list[str]
    recovery_actions: list[str]

def enhanced_post_init_validation(codebase: CodebaseType) -> ValidationResult:
    """Enhanced validation with error recovery suggestions."""
    errors = []
    warnings = []
    recovery_actions = []
    
    # Check for nodes
    if len(codebase.ctx.nodes) == 0:
        errors.append("No nodes found in codebase")
        recovery_actions.append("Check file parsing and language support")
        return ValidationResult(PostInitValidationStatus.NO_NODES, errors, warnings, recovery_actions)
    
    # Check import resolution with detailed analysis
    if len(codebase.imports) > 0:
        resolved_imports = [imp for imp in codebase.imports if imp.imported_symbol and imp.imported_symbol.node_type != NodeType.EXTERNAL]
        resolution_rate = len(resolved_imports) / len(codebase.imports)
        
        if resolution_rate < 0.2:
            warnings.append(f"Low import resolution rate: {resolution_rate:.2%}")
            recovery_actions.extend([
                "Check dependency installation",
                "Verify import paths",
                "Review language-specific configuration"
            ])
            return ValidationResult(PostInitValidationStatus.LOW_IMPORT_RESOLUTION_RATE, errors, warnings, recovery_actions)
    
    return ValidationResult(PostInitValidationStatus.SUCCESS, errors, warnings, recovery_actions)
```

### 2.3 Context Management Robustness

**File**: `src/graph_sitter/codebase/codebase_context.py`

**Enhancement**: Improve multi-project support

```python
class ProjectContext:
    """Individual project context for better isolation."""
    
    def __init__(self, project_config: ProjectConfig):
        self.config = project_config
        self.nodes = {}
        self.edges = []
        self.files = {}
        self.last_sync = None
    
    def validate_state(self) -> bool:
        """Validate project context state."""
        return len(self.nodes) > 0 and all(
            file_path.exists() for file_path in self.files.keys()
        )

class CodebaseContext:
    def __init__(self):
        self.projects: dict[str, ProjectContext] = {}
        self.active_project: Optional[str] = None
    
    def add_project(self, name: str, config: ProjectConfig) -> ProjectContext:
        """Add a new project context."""
        if name in self.projects:
            raise ValueError(f"Project {name} already exists")
        
        project_ctx = ProjectContext(config)
        self.projects[name] = project_ctx
        
        if self.active_project is None:
            self.active_project = name
        
        return project_ctx
    
    def switch_project(self, name: str) -> None:
        """Switch active project context."""
        if name not in self.projects:
            raise ValueError(f"Project {name} not found")
        
        self.active_project = name
        logger.info(f"Switched to project: {name}")
```

## 🧹 Phase 3: Code Quality & Testing (Low Priority)

### 3.1 Remove Unused Analysis Functions

**Analysis Required**: Audit `codebase_analysis.py` for unused functions

```python
# Add usage tracking decorator
def track_usage(func):
    """Decorator to track function usage."""
    if not hasattr(track_usage, 'usage_stats'):
        track_usage.usage_stats = {}
    
    def wrapper(*args, **kwargs):
        func_name = f"{func.__module__}.{func.__name__}"
        track_usage.usage_stats[func_name] = track_usage.usage_stats.get(func_name, 0) + 1
        return func(*args, **kwargs)
    
    return wrapper

# Apply to analysis functions
@track_usage
def get_codebase_summary(codebase: Codebase) -> str:
    # existing implementation
    pass

# Add usage reporting
def report_unused_functions():
    """Report functions that haven't been used."""
    unused = [func for func, count in track_usage.usage_stats.items() if count == 0]
    if unused:
        logger.warning(f"Unused functions detected: {unused}")
    return unused
```

### 3.2 Enhanced Configuration Management

**File**: `src/graph_sitter/codebase/config.py`

**Enhancement**: Simplify and validate configuration

```python
from pydantic import BaseModel, validator
from typing import Optional, List

class EnhancedCodebaseConfig(BaseModel):
    """Enhanced configuration with validation."""
    
    track_graph: bool = True
    max_file_size: int = 1024 * 1024  # 1MB default
    supported_extensions: List[str] = ['.py', '.ts', '.js']
    ignore_patterns: List[str] = []
    performance_mode: bool = False
    
    @validator('max_file_size')
    def validate_file_size(cls, v):
        if v <= 0:
            raise ValueError('max_file_size must be positive')
        return v
    
    @validator('supported_extensions')
    def validate_extensions(cls, v):
        if not v:
            raise ValueError('At least one extension must be supported')
        return v
    
    def get_effective_ignore_patterns(self) -> List[str]:
        """Get effective ignore patterns including defaults."""
        default_patterns = ['.git/*', 'node_modules/*', '*.min.js']
        return default_patterns + self.ignore_patterns
```

## 🧪 Testing Strategy

### Unit Tests
```python
# test_transaction_manager.py
def test_sorted_transactions_performance():
    """Test transaction sorting performance."""
    manager = TransactionManager()
    
    # Add 1000 transactions
    start_time = time.time()
    for i in range(1000):
        transaction = EditTransaction(...)
        manager.queue_transaction(transaction)
    
    elapsed = time.time() - start_time
    assert elapsed < 1.0, f"Transaction queuing took too long: {elapsed}s"

# test_codeowner_grouper.py
def test_null_codeowners_parser():
    """Test handling of null codeowners parser."""
    grouper = CodeownerGrouper()
    grouper.repo_operator.codeowners_parser = None
    
    flag = CodeFlag(...)
    owners = grouper._get_flag_owners(flag)
    assert owners == []
```

### Integration Tests
```python
# test_large_codebase.py
def test_large_codebase_performance():
    """Test performance with large codebases."""
    # Create test codebase with 1000+ files
    codebase = create_large_test_codebase()
    
    start_time = time.time()
    result = enhanced_post_init_validation(codebase)
    elapsed = time.time() - start_time
    
    assert elapsed < 10.0, f"Validation took too long: {elapsed}s"
    assert result.status == PostInitValidationStatus.SUCCESS
```

## 📊 Success Metrics & Validation

### Performance Benchmarks
- Transaction processing: < 100ms for 100 transactions
- Memory usage: < 500MB for 1000-file codebase
- Validation time: < 10s for large codebases

### Quality Metrics
- Test coverage: > 90%
- Error handling coverage: > 95%
- Documentation coverage: > 85%

### Monitoring & Alerting
```python
# Add performance monitoring
class PerformanceMonitor:
    def __init__(self):
        self.metrics = {}
    
    def record_operation(self, operation: str, duration: float, success: bool):
        """Record operation metrics."""
        if operation not in self.metrics:
            self.metrics[operation] = {'count': 0, 'total_time': 0, 'failures': 0}
        
        self.metrics[operation]['count'] += 1
        self.metrics[operation]['total_time'] += duration
        if not success:
            self.metrics[operation]['failures'] += 1
    
    def get_average_time(self, operation: str) -> float:
        """Get average operation time."""
        if operation not in self.metrics:
            return 0.0
        
        metrics = self.metrics[operation]
        return metrics['total_time'] / metrics['count'] if metrics['count'] > 0 else 0.0
```

## 🚀 Deployment Strategy

### Phase 1 Deployment (Critical Fixes)
1. Deploy transaction performance optimization
2. Add null safety checks
3. Implement missing group creation
4. Fix TypeScript AST handling

### Phase 2 Deployment (Performance)
1. Deploy memory optimization
2. Add enhanced error recovery
3. Implement context management improvements

### Phase 3 Deployment (Quality)
1. Remove unused functions
2. Deploy enhanced configuration
3. Add comprehensive monitoring

### Rollback Plan
- Maintain feature flags for new implementations
- Keep original implementations as fallbacks
- Monitor performance metrics post-deployment
- Automated rollback triggers for performance degradation

---

*This implementation plan ensures systematic improvement of the graph_sitter/codebase component while maintaining system stability and performance.*

