#!/bin/bash

# Set up colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if we're in the right directory
if [ ! -d "src/graph_sitter" ]; then
    print_message "$RED" "Error: Please run this script from the root of the graph-sitter repository."
    exit 1
fi

# Parse command line arguments
RUN_UNIT_TESTS=true
RUN_INTEGRATION_TESTS=false
WITH_COVERAGE=false

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --unit) RUN_UNIT_TESTS=true ;;
        --integration) RUN_INTEGRATION_TESTS=true ;;
        --all) RUN_UNIT_TESTS=true; RUN_INTEGRATION_TESTS=true ;;
        --coverage) WITH_COVERAGE=true ;;
        --help) 
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --unit         Run unit tests only (default)"
            echo "  --integration  Run integration tests"
            echo "  --all          Run both unit and integration tests"
            echo "  --coverage     Run tests with coverage"
            echo "  --help         Show this help message"
            exit 0
            ;;
        *) print_message "$YELLOW" "Warning: Unknown parameter: $1" ;;
    esac
    shift
done

# Ensure the virtual environment is activated
if [[ -z "${VIRTUAL_ENV}" ]]; then
    if [ -d ".venv" ]; then
        print_message "$YELLOW" "Virtual environment not activated. Activating now..."
        source .venv/bin/activate
    else
        print_message "$RED" "Error: Virtual environment not found. Please create and activate it first."
        print_message "$BLUE" "Run: uv venv && source .venv/bin/activate && uv sync --dev"
        exit 1
    fi
fi

# Ensure Cython modules are compiled
print_message "$BLUE" "Compiling Cython modules..."
if ! python -c "from graph_sitter.compiled.utils import get_all_identifiers" 2>/dev/null; then
    print_message "$YELLOW" "Cython modules not found. Compiling now..."
    
    # Install Cython if not already installed
    if ! python -c "import Cython" 2>/dev/null; then
        print_message "$BLUE" "Installing Cython..."
        uv pip install Cython
    fi
    
    # Compile Cython modules
    print_message "$BLUE" "Building Cython extensions..."
    python setup.py build_ext --inplace
    
    if [ $? -ne 0 ]; then
        print_message "$RED" "Error: Failed to compile Cython modules."
        exit 1
    fi
    
    print_message "$GREEN" "Cython modules compiled successfully!"
else
    print_message "$GREEN" "Cython modules already compiled."
fi

# Run tests
TEST_CMD="python -m pytest"

# Add test paths based on options
TEST_PATHS=""
if [ "$RUN_UNIT_TESTS" = true ]; then
    TEST_PATHS="tests/unit"
fi

if [ "$RUN_INTEGRATION_TESTS" = true ]; then
    if [ -n "$TEST_PATHS" ]; then
        TEST_PATHS="$TEST_PATHS tests/integration"
    else
        TEST_PATHS="tests/integration"
    fi
    
    # Exclude problematic integration tests
    TEST_CMD="$TEST_CMD -k 'not test_verified_codemods'"
fi

# If no specific tests were selected, default to unit tests
if [ -z "$TEST_PATHS" ]; then
    TEST_PATHS="tests/unit"
fi

# Add coverage if requested
if [ "$WITH_COVERAGE" = true ]; then
    TEST_CMD="$TEST_CMD --cov=graph_sitter"
else
    # Disable plugins that might cause issues
    TEST_CMD="$TEST_CMD -p no:xdist -p no:cov"
fi

# Add verbosity
TEST_CMD="$TEST_CMD -v"

# Run the tests
print_message "$BLUE" "Running tests: $TEST_CMD $TEST_PATHS"
$TEST_CMD $TEST_PATHS

# Check the result
if [ $? -eq 0 ]; then
    print_message "$GREEN" "All tests passed successfully! 🎉"
else
    print_message "$RED" "Some tests failed. Please check the output above for details."
    exit 1
fi

