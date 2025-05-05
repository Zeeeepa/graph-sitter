# Testing in Graph-Sitter

This document explains how to run tests in the Graph-Sitter project and addresses common issues.

## Running Tests

The project includes a comprehensive test script that can run unit tests, integration tests, or both:

```bash
# Run unit tests (default)
./scripts/full_test.sh

# Run all tests
./scripts/full_test.sh --all

# Run with coverage
./scripts/full_test.sh --coverage

# Run specific tests
./scripts/full_test.sh --test=tests/unit/path/to/test.py
```

## Coverage Issues

When running tests with coverage, you might encounter SQLite errors like:

```
DataError: Couldn't use data file '/path/to/.coverage.file': no such table: context
```

These errors occur because:

1. The pytest-cov plugin uses SQLite databases to store coverage data
2. When running tests in parallel with xdist, multiple processes try to access these databases simultaneously
3. The coverage context feature requires additional SQLite tables that may not be properly initialized in parallel mode

### Solutions

The `full_test.sh` script includes several fixes for these issues:

1. **Cleaning up existing coverage files** before running tests
2. **Disabling coverage context** by setting `COVERAGE_CONTEXT=off` when running with coverage
3. **Adding the `--no-cov-on-fail` flag** to prevent coverage errors from failing tests
4. **Disabling coverage plugins** when not explicitly running with coverage

## Memory Issues

Some tests, particularly those processing large repositories like `mypy`, may consume significant memory and cause segmentation faults. The test script includes memory monitoring to prevent these crashes by:

1. Monitoring memory usage of test processes
2. Gracefully terminating tests that exceed memory limits
3. Providing clear error messages when memory limits are reached

## GitHub Authentication

Some integration tests require GitHub authentication. You can provide a GitHub token:

1. Set the `GITHUB_TOKEN` environment variable before running tests
2. Or use the interactive mode of the test script, which will prompt for a token

## Interactive Mode

Running `./scripts/full_test.sh` without arguments enters interactive mode, which guides you through:

1. Selecting which tests to run
2. Setting the number of CPU cores for parallel testing
3. Enabling/disabling coverage
4. Providing GitHub authentication if needed

## Troubleshooting

If you encounter test failures:

1. **Coverage errors**: Run without coverage (`./scripts/full_test.sh` without `--coverage`)
2. **Segmentation faults**: Reduce the number of parallel processes (`--cores=4`)
3. **GitHub authentication errors**: Provide a valid GitHub token or skip GitHub-dependent tests
4. **SQLite errors**: Delete all `.coverage*` files and try again

