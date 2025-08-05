# Integration Tests

This directory contains integration tests for the graph-sitter project.

## Known Issues

Some integration tests require specific environment setup or may fail due to external dependencies:

1. **Test Directory Issues**: Tests in `codegen/cli/commands/test_reset.py` and `codegen/git/codebase/test_codebase_create_pr.py` 
   require specific temporary directory structures that may not be available in all environments. These tests are skipped by default
   in the `full_test.sh` script.

2. **Verified Codemods Tests**: Tests in `codemod/test_verified_codemods.py` require specific JSON data files that may not be 
   available in all environments. These tests are also skipped by default in the `full_test.sh` script.

## Running Integration Tests

To run integration tests, use the `full_test.sh` script:

```bash
./scripts/full_test.sh --integration
```

This will run all integration tests except for the problematic ones mentioned above.

If you want to run a specific integration test, use:

```bash
./scripts/full_test.sh --test=tests/integration/path/to/test.py
```

## Adding New Integration Tests

When adding new integration tests that require specific directory structures or external resources:

1. Add appropriate fixtures in a `conftest.py` file
2. Make sure the test can run in isolation
3. If the test requires specific directory structures, consider adding it to the skip list in `full_test.sh`

