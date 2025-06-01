# Graph-Sitter Testing Guide

## Overview

This guide provides comprehensive information about the Graph-Sitter test suite, including structure, best practices, and maintenance procedures.

## Test Suite Structure

```
tests/
├── conftest.py                 # Main test configuration
├── integration/                # Integration tests
│   ├── codemod/               # Codemod integration tests
│   ├── codegen/               # Codegen integration tests
│   └── test_vector_index.py   # Vector index tests
├── shared/                     # Shared test utilities
│   ├── codemod/               # Codemod test utilities
│   ├── mocks/                 # Mock objects
│   ├── skills/                # Skills test framework
│   └── utils/                 # General test utilities
├── unit/                       # Unit tests
│   ├── extensions/            # Extension tests
│   ├── runner/                # Runner tests
│   └── sdk/                   # SDK tests
├── test_comprehensive_system.py  # System-wide tests
├── test_enhanced_codebase_ai.py  # AI enhancement tests
└── test_system_validation.py     # System validation tests
```

## Test Configuration

### pytest Configuration

The test suite is configured via `pyproject.toml`:

```toml
[tool.pytest.ini_options]
addopts = "--dist=loadgroup --junitxml=build/test-results/test/TEST.xml --strict-config --import-mode=importlib --cov-context=test --cov-config=pyproject.toml -p no:doctest"
pythonpath = "."
norecursedirs = "repos expected"
log_cli = 1
log_cli_level = "INFO"
xfail_strict = true
junit_duration_report = "call"
junit_logging = "all"
tmp_path_retention_policy = "failed"
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
```

### Test Categories

Tests are categorized by size using the `Size` enum:
- **Small**: Fast unit tests (< 1 second)
- **Medium**: Integration tests (< 30 seconds)
- **Large**: End-to-end tests (< 5 minutes)

Run specific test sizes:
```bash
pytest --size=small
pytest --size=medium
pytest --size=large
```

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/sdk/test_file.py

# Run tests with coverage
pytest --cov=src

# Run tests in parallel
pytest -n auto

# Run tests with specific markers
pytest -m "not slow"
```

### Test Options

Available command-line options:

- `--size`: Test size filter (small, medium, large)
- `--profile`: Enable profiling
- `--sync-graph`: Sync graph between tests
- `--log-parse`: Log parsing errors
- `--extra-repos`: Test on extra repositories
- `--token`: GitHub token for extra repos
- `--codemod-id`: Test specific codemod
- `--repo-id`: Test specific repository
- `--base-commit`: Test specific commit
- `--cli-api-key`: API key for skills tests

## Test Quality Metrics

### Current Status

- **Total test files**: 404
- **Skipped tests**: 128 (31.7%)
- **XFail tests**: 30 (7.4%)
- **Platform-specific skips**: 8

### Quality Thresholds

- **Skip ratio**: Should be < 30%
- **Test coverage**: Target > 80%
- **Test execution time**: < 10 minutes for full suite
- **Flaky test rate**: < 5%

## Common Test Issues and Solutions

### 1. Skipped Tests

**Issue**: High number of skipped tests reduces effective coverage.

**Common reasons**:
- `"No Autocommit"`: Autocommit functionality disabled
- `"macOS is case-insensitive"`: Platform-specific filesystem issues
- `"TODO"`: Incomplete implementations
- `"Blocked on CG-XXXX"`: Dependency on other tickets

**Solutions**:
- Use `@pytest.mark.skipif` for platform-specific skips
- Document TODO tests with tracking information
- Remove tests for permanently disabled features
- Complete blocked implementations

### 2. Platform-Specific Issues

**Issue**: Tests fail on macOS due to case-insensitive filesystem.

**Solution**:
```python
import sys
import pytest

@pytest.mark.skipif(sys.platform == "darwin", reason="macOS filesystem is case-insensitive")
def test_case_sensitive_feature():
    # Test implementation
    pass
```

### 3. Performance Issues

**Issue**: Tests take too long to execute.

**Solutions**:
- Use mocks instead of real network calls
- Optimize fixture scopes
- Add timeout decorators
- Parallelize test execution

```python
@pytest.mark.timeout(30)
def test_slow_operation():
    # Test implementation
    pass
```

### 4. Test Isolation

**Issue**: Tests interfere with each other.

**Solutions**:
- Use `monkeypatch` for environment variables
- Ensure proper cleanup in fixtures
- Use function-scoped fixtures for test data

```python
def test_with_env_var(monkeypatch):
    monkeypatch.setenv("TEST_VAR", "value")
    # Test implementation
```

## Fixture Best Practices

### Fixture Scopes

- **session**: Expensive setup (database connections, test clients)
- **module**: Shared across module tests
- **function**: Fresh data for each test (default)

```python
@pytest.fixture(scope="session")
def database():
    """Expensive database setup"""
    db = create_test_database()
    yield db
    db.cleanup()

@pytest.fixture(scope="function")
def test_data():
    """Fresh test data for each test"""
    return {"key": "value"}
```

### Fixture Dependencies

```python
@pytest.fixture
def user_data():
    return {"name": "test_user", "email": "test@example.com"}

@pytest.fixture
def authenticated_user(user_data, test_client):
    response = test_client.post("/login", json=user_data)
    return response.json()
```

## Test Utilities

### Shared Utilities

Located in `tests/shared/`:

- **`utils/normalize.py`**: Data normalization utilities
- **`utils/recursion.py`**: Recursive operation helpers
- **`skills/`**: Skills testing framework
- **`codemod/`**: Codemod testing utilities
- **`mocks/`**: Mock objects and helpers

### Mock Usage

```python
from tests.shared.mocks.mock_ai_helper import MockAIHelper

def test_ai_functionality():
    with MockAIHelper() as mock_ai:
        mock_ai.set_response("Expected response")
        result = ai_function()
        assert result == "Expected response"
```

## CI/CD Integration

### Autonomous CI Workflow

The test suite integrates with autonomous CI/CD:

- **Failure Analysis**: Automatic analysis of test failures
- **Performance Monitoring**: Track test execution times
- **Dependency Management**: Automated dependency updates
- **Test Optimization**: Identify and fix flaky tests

### Workflow Triggers

- **Push to develop**: Run full test suite
- **Pull requests**: Run affected tests
- **Scheduled**: Daily maintenance and optimization
- **Manual**: On-demand test optimization

## Maintenance Procedures

### Regular Maintenance

1. **Weekly**: Review skipped tests and re-enable where possible
2. **Monthly**: Analyze test performance and optimize slow tests
3. **Quarterly**: Review test coverage and add missing tests
4. **As needed**: Fix flaky tests and improve reliability

### Test Health Monitoring

Use the validation script to monitor test health:

```bash
python validate_system.py
```

This checks:
- Test suite structure
- Skip ratios
- Configuration validity
- CI/CD integration

### Optimization Tools

Available scripts for test maintenance:

```bash
# Analyze test suite
python scripts/test_analysis_and_optimization.py

# Fix common issues
python scripts/fix_test_issues.py

# Optimize test suite
python scripts/test_suite_optimizer.py
```

## Writing New Tests

### Test Structure

```python
import pytest
from src.module import function_to_test

class TestFunctionName:
    """Test class for function_to_test"""
    
    def test_basic_functionality(self):
        """Test basic functionality"""
        result = function_to_test("input")
        assert result == "expected_output"
    
    def test_edge_case(self):
        """Test edge case handling"""
        with pytest.raises(ValueError):
            function_to_test(None)
    
    @pytest.mark.parametrize("input,expected", [
        ("input1", "output1"),
        ("input2", "output2"),
    ])
    def test_multiple_inputs(self, input, expected):
        """Test multiple input scenarios"""
        result = function_to_test(input)
        assert result == expected
```

### Test Naming Conventions

- Test files: `test_*.py`
- Test classes: `TestClassName`
- Test methods: `test_descriptive_name`
- Fixtures: `descriptive_fixture_name`

### Test Documentation

- Include docstrings for test classes and complex tests
- Use descriptive test names
- Add comments for complex test logic
- Document test data and expected outcomes

## Troubleshooting

### Common Issues

1. **Import Errors**: Check `PYTHONPATH` and module structure
2. **Fixture Not Found**: Verify fixture scope and location
3. **Test Timeouts**: Add timeout decorators or optimize test
4. **Platform Failures**: Use platform-specific skips
5. **Flaky Tests**: Add retries or improve test isolation

### Debug Commands

```bash
# Run with verbose output
pytest -v

# Run with debug output
pytest -s

# Run specific test with debugging
pytest tests/test_file.py::test_function -v -s

# Run with profiling
pytest --profile

# Run with coverage report
pytest --cov=src --cov-report=html
```

## Best Practices

### Do's

- ✅ Use descriptive test names
- ✅ Test one thing per test method
- ✅ Use fixtures for setup and teardown
- ✅ Mock external dependencies
- ✅ Add timeouts for potentially slow tests
- ✅ Use parametrized tests for multiple scenarios
- ✅ Document complex test logic

### Don'ts

- ❌ Don't test implementation details
- ❌ Don't use hardcoded paths or values
- ❌ Don't skip tests without good reason
- ❌ Don't write tests that depend on external services
- ❌ Don't ignore test failures
- ❌ Don't write overly complex tests
- ❌ Don't forget to clean up resources

## Contributing

When contributing tests:

1. Follow the existing test structure
2. Add tests for new functionality
3. Update existing tests when modifying code
4. Ensure tests pass locally before submitting
5. Document any new test utilities
6. Consider test performance impact

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [Graph-Sitter SDK Documentation](../docs/)
- [CI/CD Workflow Documentation](../.github/workflows/)

---

For questions or issues with the test suite, please refer to the project documentation or create an issue in the repository.

