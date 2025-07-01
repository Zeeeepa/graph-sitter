# 🔄 Codemod Migration Guide: Enhanced Framework

This guide helps you migrate existing codemods to use the new enhanced framework with safety, performance, and error handling improvements.

## 📋 Quick Migration Checklist

- [ ] Replace base `Codemod` with `SafeCodemod`, `OptimizedCodemod`, or `RobustCodemod`
- [ ] Add validation rules for safety
- [ ] Configure file filters for performance
- [ ] Implement proper error handling
- [ ] Add logging and monitoring
- [ ] Test with dry-run capability
- [ ] Update documentation

## 🔄 Migration Patterns

### 1. Basic Safety Migration

**Before (Original Pattern):**
```python
from codemods.codemod import Codemod

class MyCodemod(Codemod, Skill):
    def execute(self, codebase: Codebase) -> None:
        for file in codebase.files:
            # Direct transformation without safety checks
            file.transform_something()
```

**After (Enhanced Pattern):**
```python
from codemods.enhanced_codemod import SafeCodemod, validate_syntax_valid

class MyCodemod(SafeCodemod, Skill):
    def __init__(self, *args, **kwargs):
        super().__init__("my_codemod", *args, **kwargs)
        
        # Add safety validations
        self.add_validation_rule(validate_syntax_valid, "All files must have valid syntax")
        self.add_validation_rule(self._custom_validation, "Custom business logic validation")
    
    def _custom_validation(self, codebase: Codebase) -> bool:
        # Custom validation logic
        return True
    
    def execute(self, codebase: Codebase) -> None:
        for file in codebase.files:
            try:
                file.transform_something()
            except Exception as e:
                self.logger.error(f"Failed to transform {file.filepath}: {e}")
                raise
```

### 2. Performance Optimization Migration

**Before (Inefficient Pattern):**
```python
class SlowCodemod(Codemod, Skill):
    def execute(self, codebase: Codebase) -> None:
        # Processes all files, even irrelevant ones
        for file in codebase.files:
            for function in file.functions:
                # Expensive operation on every function
                self.expensive_analysis(function)
```

**After (Optimized Pattern):**
```python
from codemods.enhanced_codemod import OptimizedCodemod, filter_by_extension, filter_by_size

class FastCodemod(OptimizedCodemod, Skill):
    def __init__(self, *args, **kwargs):
        super().__init__("fast_codemod", *args, **kwargs)
        
        # Add performance filters
        self.add_file_filter(filter_by_extension(['.py', '.ts']), "Python and TypeScript files only")
        self.add_file_filter(filter_by_size(1000), "Skip very large files")
        self.add_file_filter(self._relevant_files_only, "Files with relevant patterns")
        
        # Enable parallel processing if safe
        self.set_parallel_safe(True, max_workers=4)
    
    def _relevant_files_only(self, file: File) -> bool:
        # Custom logic to identify relevant files
        return "component" in file.filepath.lower()
    
    def transform_file(self, file: File) -> dict:
        """Transform a single file (used for parallel processing)."""
        try:
            transformed_count = 0
            for function in file.functions:
                if self._should_transform(function):
                    self.expensive_analysis(function)
                    transformed_count += 1
            
            return {
                'status': 'success',
                'transformed_count': transformed_count
            }
        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e)
            }
    
    def execute(self, codebase: Codebase) -> None:
        # Use parallel processing for better performance
        if self._parallel_safe:
            results = self.execute_parallel(codebase)
            self.logger.info(f"Parallel processing completed: {results}")
```

### 3. Comprehensive Error Handling Migration

**Before (Fragile Pattern):**
```python
class FragileCodemod(Codemod, Skill):
    def execute(self, codebase: Codebase) -> None:
        for file in codebase.files:
            # No error handling - one failure stops everything
            self.risky_transformation(file)
```

**After (Robust Pattern):**
```python
from codemods.enhanced_codemod import RobustCodemod

class RobustCodemod(RobustCodemod, Skill):
    def __init__(self, *args, **kwargs):
        super().__init__("robust_codemod", *args, **kwargs)
        
        # Configure error handling
        self.set_error_handling(
            continue_on_error=True,
            max_failures=5,
            failure_threshold=0.2  # Stop if more than 20% fail
        )
    
    def transform_file(self, file: File) -> dict:
        """Transform a single file with comprehensive error handling."""
        try:
            result = self.risky_transformation(file)
            return {
                'status': 'success',
                'result': result,
                'file': file.filepath
            }
        except SpecificError as e:
            # Handle specific known errors
            self.logger.warning(f"Known issue in {file.filepath}: {e}")
            return {
                'status': 'skipped',
                'reason': f"Known issue: {e}",
                'file': file.filepath
            }
        except Exception as e:
            # Handle unexpected errors
            self.logger.error(f"Unexpected error in {file.filepath}: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'error_type': type(e).__name__,
                'file': file.filepath
            }
    
    def execute(self, codebase: Codebase) -> None:
        results = self.execute_with_recovery(codebase)
        
        # Log comprehensive results
        self.logger.info(f"Transformation completed:")
        self.logger.info(f"  Success rate: {results['success_rate']:.2%}")
        self.logger.info(f"  Files processed: {results['total_files']}")
        self.logger.info(f"  Successful: {len(results['successful'])}")
        self.logger.info(f"  Failed: {len(results['failed'])}")
        self.logger.info(f"  Skipped: {len(results['skipped'])}")
```

## 🎯 Choosing the Right Base Class

### SafeCodemod
**Use when:** You need basic safety mechanisms and rollback capabilities.
**Best for:** Simple transformations that need validation and rollback.

```python
class MySafeCodemod(SafeCodemod, Skill):
    # Adds: validation rules, backup/rollback, dry-run support
```

### OptimizedCodemod
**Use when:** You need performance optimizations and file filtering.
**Best for:** Transformations that process many files or have expensive operations.

```python
class MyOptimizedCodemod(OptimizedCodemod, Skill):
    # Adds: file filtering, parallel processing, performance monitoring
```

### RobustCodemod
**Use when:** You need comprehensive error handling and recovery.
**Best for:** Production transformations that must handle failures gracefully.

```python
class MyRobustCodemod(RobustCodemod, Skill):
    # Adds: error recovery, failure thresholds, detailed reporting
```

## 🔧 Common Migration Patterns

### Adding Validation Rules

```python
def __init__(self, *args, **kwargs):
    super().__init__("my_codemod", *args, **kwargs)
    
    # Built-in validation rules
    self.add_validation_rule(validate_syntax_valid, "Syntax validation")
    self.add_validation_rule(validate_git_clean, "Git status validation")
    
    # Custom validation rules
    self.add_validation_rule(self._validate_no_breaking_changes, "No breaking changes")

def _validate_no_breaking_changes(self, codebase: Codebase) -> bool:
    # Custom validation logic
    for file in codebase.files:
        if self._would_break_api(file):
            return False
    return True
```

### Adding File Filters

```python
def __init__(self, *args, **kwargs):
    super().__init__("my_codemod", *args, **kwargs)
    
    # Built-in filters
    self.add_file_filter(filter_by_extension(['.py']), "Python files only")
    self.add_file_filter(filter_by_size(500), "Small to medium files")
    self.add_file_filter(filter_by_pattern(r'src/.*'), "Source files only")
    
    # Custom filters
    self.add_file_filter(self._filter_relevant_files, "Relevant files only")

def _filter_relevant_files(self, file: File) -> bool:
    # Custom filtering logic
    return "component" in file.filepath and not file.filepath.endswith('.test.py')
```

### Implementing Parallel Processing

```python
def __init__(self, *args, **kwargs):
    super().__init__("my_codemod", *args, **kwargs)
    
    # Enable parallel processing (only if thread-safe!)
    self.set_parallel_safe(True, max_workers=4)

def transform_file(self, file: File) -> dict:
    """This method is called for each file in parallel."""
    try:
        # Your file transformation logic here
        result = self.process_file(file)
        return {'status': 'success', 'result': result}
    except Exception as e:
        return {'status': 'failed', 'error': str(e)}
```

## 🧪 Testing Enhanced Codemods

### Dry Run Testing

```python
# Test with dry run first
codemod = MyEnhancedCodemod()
dry_result = codemod.safe_execute(codebase, dry_run=True)

if dry_result['status'] == 'success':
    # Dry run successful, execute for real
    real_result = codemod.safe_execute(codebase, dry_run=False)
else:
    print(f"Dry run failed: {dry_result['error']}")
```

### Performance Testing

```python
from codemods.utils.performance_analyzer import CodemodBenchmark

benchmark = CodemodBenchmark()
result = benchmark.benchmark_codemod(my_codemod, codebase, iterations=3)
print(benchmark.generate_report())
```

### Error Handling Testing

```python
# Test error scenarios
codemod = MyRobustCodemod()
codemod.set_error_handling(
    continue_on_error=True,
    max_failures=1,  # Low threshold for testing
    failure_threshold=0.1
)

results = codemod.execute_with_recovery(codebase)
assert results['success_rate'] > 0.8  # Expect high success rate
```

## 📊 Migration Benefits

### Before Migration
- ❌ No safety mechanisms
- ❌ Poor error handling
- ❌ Inefficient processing
- ❌ No rollback capability
- ❌ Limited monitoring

### After Migration
- ✅ Pre-transformation validation
- ✅ Automatic rollback on failure
- ✅ File filtering and parallel processing
- ✅ Comprehensive error handling
- ✅ Detailed logging and metrics
- ✅ Dry-run capability
- ✅ Performance monitoring

## 🚀 Next Steps

1. **Start with SafeCodemod**: Migrate critical codemods to use basic safety features
2. **Add Performance Optimizations**: Use OptimizedCodemod for high-volume transformations
3. **Implement Error Handling**: Use RobustCodemod for production deployments
4. **Monitor and Iterate**: Use performance analyzer to identify further optimizations
5. **Update Documentation**: Document your enhanced codemods for team usage

## 📚 Additional Resources

- [Enhanced Codemod API Reference](src/codemods/enhanced_codemod.py)
- [Performance Analysis Tools](src/codemods/utils/performance_analyzer.py)
- [Example Enhanced Codemod](src/codemods/examples/enhanced_delete_unused_functions.py)
- [Validation Rules Library](src/codemods/enhanced_codemod.py#L200)
- [File Filters Library](src/codemods/enhanced_codemod.py#L250)

---

*This migration guide ensures your codemods are production-ready for autonomous CI/CD workflows.*

