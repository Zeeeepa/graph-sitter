# Graph-sitter Examples

[![Documentation](https://img.shields.io/badge/docs-graph-sitter.com-blue)](https://graph-sitter.com)

This is a collection of examples using [Codegen](https://codegen.com). You can use these examples to learn how to use Codegen and build custom code transformations.

## Setup

We recommend using [`uv`](https://github.com/astral-sh/uv) with Python 3.13 for the best experience.

To install graph-sitter, please follow the [official installation guide](https://graph-sitter.com/introduction/installation). Once Graph-sitter is installed, use these steps to run the examples in this repository:

Install the graph_sitter.cli globally

```bash
uv tool install graph-sitter
```

Initialize Graph-sitter in your project

```bash
gs init
```

Activate the virtual environment

```bash
source .codegen/.venv/bin/activate
```

Your environment is now ready to run example codemods.

### IDE Configuration (Optional)

To configure your IDE for optimal use with Codegen, follow our [IDE setup guide](https://graph-sitter.com/introduction/ide-usage#configuring-your-ide-interpreter).

## Examples

Within the examples folder, each subdirectory contains a self-contained example with:

- An explanation of the transformation (`README.md`)
- A Graph-sitter script that performs the transformation (`run.py`)
- Sample code to transform, if not using a repository (`input_repo/`)

To see a transformation, simply run the `run.py` script within the desired directory.

## Learn More

- [Documentation](https://graph-sitter.com)
- [Getting Started Guide](https://graph-sitter.com/introduction/getting-started)
- [Tutorials](https://graph-sitter.com/tutorials/at-a-glance)
- [API Reference](https://graph-sitter.com/api-reference)

## Serena Integration Testing

This directory also contains comprehensive testing scripts for the enhanced Serena integration:

### `comprehensive_serena_demo.py`
Comprehensive demonstration and testing script for all Serena capabilities including refactoring, symbol intelligence, code actions, and real-time analysis.

```bash
# Run basic demo
python examples/comprehensive_serena_demo.py

# Run full test suite
python examples/comprehensive_serena_demo.py --test-all --verbose
```

### `test_web_eval_agent.py`
Specialized test script for the web-eval-agent repository with auto-detection and targeted testing.

```bash
# From web-eval-agent repository root:
python /path/to/graph-sitter/examples/test_web_eval_agent.py
```

### Features Tested
- ✅ Enhanced LSP Integration with multi-server support
- ✅ Advanced Refactoring Operations (rename, extract, inline, move)
- ✅ Symbol Intelligence with relationship tracking
- ✅ Code Actions with automated fixes
- ✅ Real-time Analysis with file monitoring
- ✅ Auto-initialization with Codebase class enhancement

The testing scripts provide detailed results including success rates, capability status, performance metrics, and integration health.

## Contributing

Have a useful example to share? We'd love to include it! Please see our [Contributing Guide](CONTRIBUTING.md) for instructions.

## License

The [Apache 2.0 license](LICENSE).
