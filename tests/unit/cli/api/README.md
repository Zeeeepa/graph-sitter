# API Validation Tests

This directory contains validation tests for the Codegen API endpoints.

## Test Files

- `test_client.py`: Unit tests for the `RestAPI` client class
- `test_schemas.py`: Unit tests for the API schemas
- `../../integration/cli/api/test_client_integration.py`: Integration tests for the API client

## Running the Tests

### Unit Tests

To run the unit tests:

```bash
uv run pytest tests/unit/cli/api/test_client.py -v
uv run pytest tests/unit/cli/api/test_schemas.py -v
```

### Integration Tests

To run the integration tests:

```bash
uv run pytest tests/integration/cli/api/test_client_integration.py -v
```

### All Tests

To run all API tests:

```bash
uv run pytest tests/unit/cli/api/ tests/integration/cli/api/ -v
```

## Test Coverage

To run the tests with coverage:

```bash
uv run pytest tests/unit/cli/api/ tests/integration/cli/api/ --cov=graph_sitter.cli.api -v
```

## Test Structure

### Client Tests

The client tests validate:

1. Authentication handling
2. Request/response handling
3. Error handling
4. Each API endpoint method

### Schema Tests

The schema tests validate:

1. Valid schema creation
2. Required field validation
3. Default values
4. Field types and constraints

### Integration Tests

The integration tests validate:

1. End-to-end API client functionality
2. Request formatting
3. Response parsing
4. Error handling

## Adding New Tests

When adding new API endpoints, please add corresponding tests in:

1. `test_client.py` for unit testing the client method
2. `test_schemas.py` for validating the input/output schemas
3. `test_client_integration.py` for integration testing the endpoint

