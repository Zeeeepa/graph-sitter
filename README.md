# PR Validation and Deployment System

A comprehensive system for validating and deploying Pull Requests using a combination of powerful tools:

- [pr-agent](https://github.com/Zeeeepa/pr-agent) for PR analysis and GitHub integration
- [grainchain](https://github.com/codegen-sh/grainchain) for sandbox environments
- [codegen](https://github.com/codegen-sh/codegen) for code analysis
- [graph-sitter](https://github.com/codegen-sh/graph-sitter) for static analysis

## Features

- 🚀 Automatic PR validation on creation/update
- 📋 Customizable command templates
- 🔍 Feature validation with static analysis
- 🖼️ UI testing with visual regression
- 🔄 GitHub deployment synchronization
- 🌍 Support for global variables

## Setup

1. Install dependencies:
```bash
pip install grainchain[all] pr-agent codegen graph-sitter
```

2. Configure environment variables:
```bash
export CODEGEN_ORG_ID="your-org-id"
export CODEGEN_API_TOKEN="your-api-token"
export GITHUB_TOKEN="your-github-token"
```

3. Configure validation settings in `src/config/validation.yml`

## Usage

The system automatically runs when a PR is created or updated. It performs:

1. Command template execution
2. Feature validation
3. UI testing
4. Deployment synchronization

## Configuration

### Command Templates

Define command templates in `src/config/validation.yml`:

```yaml
templates:
  - name: setup
    commands:
      - npm install
      - npm run build
```

### Global Variables

Set global variables in `src/config/validation.yml`:

```yaml
global_vars:
  NODE_ENV: test
  TEST_TIMEOUT: 30000
```

### Feature Validation

Configure validation rules:

```yaml
feature_validation:
  complexity_threshold: 10
  coverage_threshold: 80
```

### UI Testing

Configure UI test settings:

```yaml
ui_testing:
  browsers:
    - chromium
    - firefox
```

## Development

1. Clone the repository
2. Install development dependencies
3. Run tests:
```bash
python -m pytest
```

## Contributing

Please see our [Contributing Guide](CONTRIBUTING.md) for instructions on how to contribute to this project.

## License

MIT

