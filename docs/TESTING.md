# Graph-Sitter Testing Guide

This document provides guidance on how to effectively test the Graph-Sitter codebase.

## Testing Scripts

Graph-Sitter provides several scripts to help with testing:

- `scripts/full_test.sh`: The main test script with comprehensive options
- `scripts/fullbuild.sh`: Script to set up the development environment and optionally run tests

## Quick Start

To run tests with the test script:

```bash
# Run unit tests (default)
./scripts/full_test.sh

# Run all tests
./scripts/full_test.sh --all

# Run with coverage
./scripts/full_test.sh --coverage

# Run specific test file or directory
./scripts/full_test.sh --test=tests/unit/sdk/core/test_file.py
```

## Interactive Mode

If you run the test script without arguments, it will enter interactive mode:

```bash
./scripts/full_test.sh
```

This will prompt you for:
- Test type (unit, integration, all, or specific test)
- Number of CPU cores to use
- Coverage options
- Verbose output options
- GitHub token for authentication (when needed for integration tests)
- Memory limits and other advanced options

## Advanced Options

The test script supports several advanced options:

```bash
# Run tests sequentially (no parallelism)
./scripts/full_test.sh --sequential

# Stop on first test failure
./scripts/full_test.sh --fail-fast

# Generate HTML coverage report
./scripts/full_test.sh --coverage --html-report

# Run tests incrementally (one file at a time)
./scripts/full_test.sh --incremental

# Set maximum memory usage (in GB)
./scripts/full_test.sh --max-memory-gb=16

# Skip large repositories that cause memory issues
./scripts/full_test.sh --skip-large-repos

# Force run ALL tests including memory-intensive ones
./scripts/full_test.sh --force-all
```

## Handling Memory Issues

Some tests, particularly those involving large repositories like `mypy`, can cause memory issues or segmentation faults. The test script includes memory monitoring to prevent these issues:

1. **Memory Monitoring**: The script monitors memory usage and gracefully terminates tests before they cause segmentation faults.

2. **Skip Large Repos**: Use `--skip-large-repos` to skip tests on large repositories that are known to cause memory issues.

3. **Incremental Testing**: Use `--incremental` to run tests one file at a time, which helps avoid memory issues.

4. **Memory Limits**: Set a custom memory limit with `--max-memory-gb=N`.

## Coverage Reports

The test script supports generating coverage reports:

```bash
# Run with coverage and generate terminal report
./scripts/full_test.sh --coverage

# Run with coverage and generate HTML report
./scripts/full_test.sh --coverage --html-report
```

The HTML report will be available at `htmlcov/index.html`.

## Troubleshooting

### Coverage Warnings

If you see warnings like:

```
CoverageWarning: Module graph_sitter was previously imported, but not measured (module-not-measured)
CoverageWarning: No data was collected. (no-data-collected)
```

These are normal when running with coverage and can be safely ignored. The test script configures coverage to minimize these warnings.

### SQLite Errors

If you encounter SQLite errors like:

```
DataError: Couldn't use data file '/path/to/.coverage.file': no such table: context
```

The test script configures coverage to avoid these errors by:
- Setting `COVERAGE_CONTEXT=off`
- Setting `COVERAGE_CORE=singleprocess`
- Cleaning up coverage files between test runs

### Segmentation Faults

If you encounter segmentation faults, try:

1. Running with `--skip-large-repos` to skip problematic repositories
2. Running with `--incremental` to run tests one file at a time
3. Setting a lower memory limit with `--max-memory-gb=16`
4. Running with `--sequential` to disable parallel testing

## GitHub Authentication

Some integration tests require GitHub authentication. You can provide a GitHub token:

```bash
export GITHUB_TOKEN=your_github_token
./scripts/full_test.sh --all
```

Or use interactive mode, which will prompt you for a token.

## Continuous Integration

For CI environments, it's recommended to use:

```bash
./scripts/full_test.sh --all --coverage --cores=$(nproc) --skip-large-repos
```

This will run all tests with coverage, using all available CPU cores, while skipping repositories that might cause memory issues.

