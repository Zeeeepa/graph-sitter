# Graph-Sitter

A powerful code analysis framework with semantic understanding, dependency resolution, and comprehensive tooling for modern software development.

## 🚀 Features

- **Code Analysis**: Deep semantic analysis of codebases with symbol resolution
- **Dependency Tracking**: Comprehensive dependency analysis and visualization
- **Multi-Language Support**: Python, TypeScript, JavaScript, and more
- **Extension System**: Modular architecture with pluggable extensions
- **Dashboard Interface**: Modern web-based dashboard for project management
- **Real-time Updates**: WebSocket-powered live monitoring and updates
- **Cython Performance**: High-performance core modules written in Cython

## 📋 Prerequisites

Before installing Graph-Sitter, ensure you have the following prerequisites:

### System Requirements

- **Python 3.8+** (Python 3.13 recommended)
- **Node.js 16+** (for frontend components)
- **Git** (for version control)

### System Dependencies

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install -y gcc build-essential python3-dev libpixman-1-dev libcairo2-dev \
  libpango1.0-dev libjpeg-dev libgif-dev librsvg2-dev jq libssl-dev zlib1g-dev \
  libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev \
  libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev python3-openssl
```

#### macOS
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install jq openssl readline sqlite3 xz zlib tcl-tk
```

## 🛠️ Installation

### Quick Start (Recommended)

The fastest way to get started is using our automated setup script:

```bash
# Clone the repository
git clone https://github.com/Zeeeepa/graph-sitter.git
cd graph-sitter

# Run the full build script (sets up everything)
./scripts/fullbuild.sh

# Or run with tests
./scripts/fullbuild.sh --test
```

This script will:
- Install UV package manager
- Create and activate a virtual environment
- Install all dependencies
- Set up pre-commit hooks
- Compile Cython modules
- Install the package in development mode
- Optionally run tests

### Manual Installation

If you prefer manual installation or need more control:

#### 1. Install UV Package Manager

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.cargo/bin:$PATH"
```

#### 2. Create Virtual Environment

```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

#### 3. Install Dependencies

```bash
uv sync --dev
```

#### 4. Install Development Tools

```bash
uv tool install deptry
uv tool install pre-commit --with pre-commit-uv
pre-commit install
pre-commit install-hooks
```

#### 5. Build Cython Modules

```bash
# Quick build and test
./scripts/build_and_test.sh --test

# Or manually
python setup.py build_ext --inplace
uv pip install -e .
```

## 🏃‍♂️ Quick Start

### Basic Usage

```python
from graph_sitter import GraphSitter

# Initialize the analyzer
analyzer = GraphSitter()

# Analyze a codebase
result = analyzer.analyze_project("/path/to/your/project")

# Get dependency graph
dependencies = analyzer.get_dependencies()

# Resolve symbols
symbols = analyzer.resolve_symbols("MyClass")
```

### Running Tests

```bash
# Run all tests
python -m pytest tests/unit -v

# Run specific test file
python -m pytest tests/unit/test_specific.py -v

# Run with coverage
python -m pytest tests --cov=graph_sitter
```

### Starting the Dashboard

```bash
# Start the backend server
python src/contexten/backend/main.py

# In another terminal, start the frontend
cd src/contexten/frontend
npm install
npm run dev
```

The dashboard will be available at `http://localhost:3000`.

## 🏗️ Development Setup

### Development Environment

For active development, use the build script with test mode:

```bash
./scripts/build_and_test.sh --test
```

This will:
- Check for virtual environment
- Install Cython if needed
- Compile all Cython modules
- Install the package in development mode
- Run the test suite

### Pre-commit Hooks

Pre-commit hooks are automatically installed during setup. They include:
- Code formatting (Ruff, Biome)
- Linting (Ruff, Cython-lint)
- Type checking
- Dependency validation

To run pre-commit manually:
```bash
pre-commit run --all-files
```

### Extension Development

Graph-Sitter supports custom extensions. To create a new extension:

1. Create your extension in `src/graph_sitter/extensions/`
2. Implement the required interface
3. Register your extension in the configuration
4. Test your extension with the test suite

## 🚀 Deployment

### Production Deployment

#### 1. Environment Setup

```bash
# Clone and setup
git clone https://github.com/Zeeeepa/graph-sitter.git
cd graph-sitter

# Production build
./scripts/fullbuild.sh
```

#### 2. Configuration

Create a production configuration file:

```python
# config/production.py
DATABASE_URL = "postgresql://user:pass@localhost/graphsitter"
REDIS_URL = "redis://localhost:6379"
SECRET_KEY = "your-secret-key"
DEBUG = False
```

#### 3. Database Setup

```bash
# Setup databases
./database/setup_all_databases.sh
```

#### 4. Start Services

```bash
# Start the backend API
uvicorn src.contexten.backend.main:app --host 0.0.0.0 --port 8000

# Start the frontend (build first)
cd src/contexten/frontend
npm run build
npm run start
```

### Docker Deployment

```dockerfile
# Dockerfile example
FROM python:3.13-slim

WORKDIR /app
COPY . .

RUN ./scripts/fullbuild.sh
EXPOSE 8000

CMD ["uvicorn", "src.contexten.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables

Key environment variables for deployment:

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/graphsitter
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=yourdomain.com,localhost

# Features
DEBUG=false
ENABLE_WEBSOCKETS=true
ENABLE_EXTENSIONS=true
```

## 🔧 Configuration

### Project Configuration

Graph-Sitter can be configured via `pyproject.toml`:

```toml
[tool.graph_sitter]
# Analysis settings
max_depth = 10
include_tests = true
exclude_patterns = ["node_modules", ".git", "__pycache__"]

# Extension settings
extensions = ["analyze", "visualize", "resolve"]

# Performance settings
cache_enabled = true
parallel_processing = true
```

### Extension Configuration

Extensions can be configured individually:

```toml
[tool.graph_sitter.extensions.analyze]
enabled = true
deep_analysis = true

[tool.graph_sitter.extensions.visualize]
enabled = true
output_format = "svg"
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Cython Compilation Errors

```bash
# Ensure you have the required system dependencies
sudo apt install gcc python3-dev  # Linux
brew install gcc  # macOS

# Clean and rebuild
python setup.py clean --all
./scripts/build_and_test.sh
```

#### 2. Import Errors

```bash
# Ensure the package is installed in development mode
uv pip install -e .

# Check if Cython modules are compiled
python -c "import graph_sitter.compiled.utils"
```

#### 3. Pre-commit Hook Failures

```bash
# Update pre-commit hooks
pre-commit autoupdate

# Run specific hook
pre-commit run biome-check --all-files
```

#### 4. WebSocket Connection Issues

- Ensure backend is running on the correct port
- Check firewall settings
- Verify CORS configuration in the backend

#### 5. Database Connection Issues

```bash
# Check database status
./database/setup_all_databases.sh

# Verify connection
python -c "from src.contexten.backend.database import test_connection; test_connection()"
```

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or set environment variable
export GRAPH_SITTER_DEBUG=true
```

### Performance Issues

If you experience performance issues:

1. **Enable caching**: Set `cache_enabled = true` in configuration
2. **Parallel processing**: Set `parallel_processing = true`
3. **Reduce analysis depth**: Lower `max_depth` setting
4. **Exclude unnecessary files**: Add patterns to `exclude_patterns`

## 📚 Documentation

- **API Reference**: [docs/api/](docs/api/)
- **Extension Guide**: [docs/extensions/](docs/extensions/)
- **Architecture Overview**: [docs/architecture/](docs/architecture/)
- **Contributing Guide**: [CONTRIBUTING.md](CONTRIBUTING.md)

## 🧪 Testing

### Running Tests

```bash
# All tests
python -m pytest tests/unit -v

# Specific test categories
python -m pytest tests/unit/core -v          # Core functionality
python -m pytest tests/unit/extensions -v   # Extensions
python -m pytest tests/unit/api -v          # API tests

# With coverage
python -m pytest tests --cov=graph_sitter --cov-report=html
```

### Test Configuration

Tests can be configured via `pytest.ini`:

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Run tests: `./scripts/build_and_test.sh --test`
5. Commit your changes: `git commit -m 'Add amazing feature'`
6. Push to the branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

### Code Style

We use automated code formatting and linting:
- **Python**: Ruff for formatting and linting
- **JavaScript/TypeScript**: Biome for formatting and linting
- **Cython**: cython-lint for Cython-specific linting

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/) and [React](https://reactjs.org/)
- Powered by [Tree-sitter](https://tree-sitter.github.io/) for parsing
- Uses [UV](https://github.com/astral-sh/uv) for fast Python package management
- Inspired by modern developer tools and static analysis frameworks

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/Zeeeepa/graph-sitter/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Zeeeepa/graph-sitter/discussions)
- **Documentation**: [Project Wiki](https://github.com/Zeeeepa/graph-sitter/wiki)

---

**Happy coding with Graph-Sitter! 🎉**

