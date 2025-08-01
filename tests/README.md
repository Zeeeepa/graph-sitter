# Unified Error Interface Test Suite

This directory contains comprehensive tests for the unified error interface implementation in graph-sitter. The test suite is designed to thoroughly validate all aspects of the error handling functionality.

## Test Structure

```
tests/
├── conftest.py                           # Pytest configuration and shared fixtures
├── test_runner.py                        # Convenient test runner script
├── README.md                            # This file
├── integration/
│   └── test_unified_error_interface.py  # Integration tests with real codebases
├── unit/
│   └── extensions/
│       └── lsp/
│           └── test_serena_integration.py # Unit tests for individual components
└── performance/
    └── test_error_interface_performance.py # Performance and scalability tests
```

## Test Categories

### 1. Integration Tests (`tests/integration/`)

**File:** `test_unified_error_interface.py`

Tests the complete unified error interface with real codebases and LSP integration:

- **Basic Functionality Tests**
  - `test_errors_method_basic_functionality()` - Validates `errors()` method structure and return format
  - `test_errors_method_with_real_files()` - Tests error detection with actual Python files containing errors
  - `test_full_error_context_method()` - Validates `full_error_context()` method functionality
  - `test_resolve_errors_method()` - Tests bulk error resolution
  - `test_resolve_error_method()` - Tests individual error resolution

- **Performance Tests**
  - `test_errors_method_performance()` - Measures execution time for error detection
  - `test_errors_method_caching()` - Validates caching improves performance on repeated calls
  - `test_concurrent_access()` - Tests thread safety under concurrent access
  - `test_large_codebase_performance()` - Performance testing with larger codebases

- **Error Type Specific Tests**
  - `test_specific_error_types()` - Parameterized tests for different error types (syntax, import, type, undefined variables)

- **Edge Cases**
  - `test_full_error_context_with_invalid_id()` - Handling of invalid error IDs
  - `test_resolve_error_with_invalid_id()` - Error resolution with invalid IDs
  - `test_error_interface_integration()` - End-to-end workflow testing

### 2. Unit Tests (`tests/unit/extensions/lsp/`)

**File:** `test_serena_integration.py`

Tests individual components in isolation with mocked dependencies:

- **UnifiedErrorInterface Class Tests**
  - `test_unified_error_interface_initialization()` - Constructor and initialization
  - `test_lazy_lsp_integration_initialization()` - Lazy loading of LSP integration
  - `test_errors_method_empty_codebase()` - Behavior with empty codebases
  - `test_errors_method_with_files()` - Error detection with mocked file diagnostics
  - `test_build_error_context()` - Context building functionality
  - `test_generate_error_suggestions()` - Suggestion generation for different error types

- **Integration with Codebase Class**
  - `test_add_unified_error_interface_to_codebase()` - Method injection into Codebase class
  - `test_error_interface_instance_creation()` - Instance management
  - `test_codebase_methods_delegation()` - Proper delegation to error interface

- **Error Handling Tests**
  - `test_errors_method_lsp_failure()` - Graceful handling of LSP failures
  - `test_full_error_context_lsp_failure()` - Context generation when LSP fails
  - `test_resolve_errors_lsp_failure()` - Error resolution when LSP fails

### 3. Performance Tests (`tests/performance/`)

**File:** `test_error_interface_performance.py`

Comprehensive performance and scalability testing:

- **Performance Benchmarks**
  - `test_errors_method_performance_small()` - Small codebase (5 files) performance
  - `test_errors_method_performance_medium()` - Medium codebase (25 files) performance  
  - `test_errors_method_performance_large()` - Large codebase (100 files) performance
  - `test_caching_performance()` - Caching effectiveness measurement
  - `test_full_error_context_performance()` - Context generation performance
  - `test_resolve_errors_performance()` - Error resolution performance

- **Scalability Tests**
  - `test_concurrent_access_performance()` - Multi-threaded performance
  - `test_memory_usage_scaling()` - Memory usage with different codebase sizes
  - `test_repeated_operations_performance()` - Performance of repeated operations

- **Benchmark Suite**
  - `test_scalability_benchmark()` - Parameterized benchmarks across different scales
  - Synthetic codebase generation for consistent benchmarking

## Test Fixtures and Utilities

### Shared Fixtures (`conftest.py`)

- **`temp_project_with_errors`** - Creates temporary project with various error types
- **`sample_python_files`** - Dictionary of Python files with different error patterns
- **`mock_lsp_diagnostics`** - Mock LSP diagnostic responses for testing
- **`mock_error_context`** - Mock error context data
- **`mock_codebase`** - Mock codebase instance for unit testing
- **`test_data_generator`** - Helper class for generating test data

### Test Data Patterns

The test suite includes files with these error patterns:

1. **Syntax Errors** - Missing parentheses, colons, indentation issues
2. **Import Errors** - Missing modules, incorrect import paths
3. **Type Errors** - Type mismatches, incorrect function signatures
4. **Undefined Variables** - NameError scenarios
5. **Attribute Errors** - Accessing non-existent attributes/methods
6. **Code Quality Issues** - Long lines, too many parameters, missing docstrings

## Running Tests

### Using the Test Runner

The `test_runner.py` script provides convenient ways to run different test suites:

```bash
# Run all tests (unit + integration)
python tests/test_runner.py

# Run only unit tests
python tests/test_runner.py --unit

# Run only integration tests  
python tests/test_runner.py --integration

# Run performance tests
python tests/test_runner.py --performance

# Run all tests with coverage
python tests/test_runner.py --all --coverage

# Quick development tests
python tests/test_runner.py quick

# Smoke tests for basic functionality
python tests/test_runner.py smoke

# Comprehensive test suite
python tests/test_runner.py comprehensive
```

### Using Pytest Directly

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/integration/test_unified_error_interface.py

# Run tests with coverage
pytest tests/ --cov=src/graph_sitter/extensions/lsp/serena --cov-report=html

# Run tests matching pattern
pytest -k "test_errors_method"

# Run tests with specific markers
pytest -m "not slow"

# Verbose output
pytest tests/ -v -s

# Run performance tests (requires explicit flag)
pytest tests/performance/ --run-performance
```

## Test Configuration

### Markers

- **`@pytest.mark.slow`** - Marks slow tests (skipped by default)
- **`@pytest.mark.integration`** - Integration tests
- **`@pytest.mark.unit`** - Unit tests  
- **`@pytest.mark.performance`** - Performance tests

### Command Line Options

- **`--run-slow`** - Include slow tests
- **`--run-performance`** - Include performance tests

## Expected Test Results

### Performance Benchmarks

Based on the test suite, expected performance characteristics:

- **Small Codebase (5 files)**: < 10 seconds, < 100MB memory
- **Medium Codebase (25 files)**: < 30 seconds, < 200MB memory  
- **Large Codebase (100 files)**: < 120 seconds, < 500MB memory

### Coverage Targets

- **Unit Tests**: > 90% code coverage
- **Integration Tests**: > 80% feature coverage
- **Error Scenarios**: 100% error path coverage

## Continuous Integration

The test suite is designed to work in CI environments:

```yaml
# Example CI configuration
- name: Run Tests
  run: |
    python tests/test_runner.py --all --coverage
    
- name: Run Performance Tests
  run: |
    python tests/test_runner.py --performance
```

## Debugging Tests

### Common Issues

1. **Import Errors**: Ensure `src/` is in Python path
2. **Missing Dependencies**: Install graph-sitter and related packages
3. **LSP Server Issues**: Mock LSP responses for consistent testing
4. **File Permissions**: Ensure test files can be created/deleted

### Debug Mode

```bash
# Run with debugging
pytest tests/ -v -s --tb=long --pdb

# Run single test with debugging
pytest tests/unit/extensions/lsp/test_serena_integration.py::TestUnifiedErrorInterfaceUnit::test_unified_error_interface_initialization -v -s --pdb
```

## Contributing to Tests

When adding new functionality to the unified error interface:

1. **Add Unit Tests** - Test individual components in isolation
2. **Add Integration Tests** - Test end-to-end functionality
3. **Add Performance Tests** - Ensure scalability is maintained
4. **Update Fixtures** - Add new test data patterns as needed
5. **Document Test Cases** - Update this README with new test descriptions

### Test Naming Convention

- `test_<method_name>_<scenario>()` - For method-specific tests
- `test_<feature>_<condition>()` - For feature tests
- `test_<error_type>_handling()` - For error handling tests

### Assertion Guidelines

- Use descriptive assertion messages
- Test both positive and negative cases
- Validate return types and structures
- Check error conditions and edge cases

## Test Data Management

Test data is managed through:

- **Fixtures** - For reusable test data
- **Temporary Directories** - For file-based tests
- **Mock Objects** - For external dependencies
- **Synthetic Data** - For performance testing

All test data is cleaned up automatically after test completion.

