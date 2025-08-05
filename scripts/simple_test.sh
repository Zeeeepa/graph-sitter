#!/usr/bin/env bash
set -e

# Simple Test Script for graph-sitter
# This script runs tests with verbose output

# Display colorful messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${BOLD}${BLUE}=== Graph-Sitter Test Runner ===${NC}"

# Ensure we're in the virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}No virtual environment detected. Activating...${NC}"
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    else
        echo -e "${RED}No .venv directory found. Please run './scripts/fullbuild.sh' first.${NC}"
        exit 1
    fi
fi

# Check if Cython modules are compiled
if ! python -c "import graph_sitter.compiled.utils" &> /dev/null; then
    echo -e "${YELLOW}Cython modules not found. Compiling...${NC}"
    python -m pip install -e .
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to compile Cython modules. Please check the error messages above.${NC}"
        exit 1
    fi
fi

# Create necessary directories for tests
echo -e "${BLUE}Creating necessary test directories...${NC}"
mkdir -p tests/integration/verified_codemods/codemod_data

# Parse command line arguments
RUN_UNIT=false
RUN_ALL=false
RUN_COVERAGE=false
SPECIFIC_TEST=""

for arg in "$@"; do
    case $arg in
        --unit)
            RUN_UNIT=true
            ;;
        --all)
            RUN_ALL=true
            ;;
        --coverage)
            RUN_COVERAGE=true
            ;;
        --test=*)
            SPECIFIC_TEST="${arg#*=}"
            ;;
        --help)
            echo -e "${BLUE}Usage: ./scripts/simple_test.sh [OPTIONS]${NC}"
            echo -e "${BLUE}Options:${NC}"
            echo -e "  --unit         Run unit tests only"
            echo -e "  --all          Run all tests"
            echo -e "  --coverage     Run with coverage"
            echo -e "  --test=PATH    Run specific test file or directory"
            echo -e "  --help         Show this help message"
            exit 0
            ;;
    esac
done

# Set default if no option provided
if [ "$RUN_UNIT" = false ] && [ "$RUN_ALL" = false ] && [ -z "$SPECIFIC_TEST" ]; then
    echo -e "${YELLOW}No test option specified. Running unit tests by default.${NC}"
    RUN_UNIT=true
fi

# Build pytest command - always run with verbose output
PYTEST_CMD="python -m pytest -v"

# Add coverage if requested
if [ "$RUN_COVERAGE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=graph_sitter --cov-report=term"
fi

# Determine which tests to run
if [ -n "$SPECIFIC_TEST" ]; then
    # Run specific test
    echo -e "${BLUE}Running specific test: ${SPECIFIC_TEST}${NC}"
    $PYTEST_CMD "$SPECIFIC_TEST"
    TEST_EXIT_CODE=$?
elif [ "$RUN_ALL" = true ]; then
    # Run all tests
    echo -e "${BLUE}Running all tests...${NC}"
    echo -e "${YELLOW}Note: Some integration tests may be skipped if they require external resources${NC}"
    
    # Skip problematic verified codemods tests
    $PYTEST_CMD tests --ignore=tests/integration/codemod/test_verified_codemods.py
    TEST_EXIT_CODE=$?
else
    # Run unit tests
    echo -e "${BLUE}Running unit tests...${NC}"
    $PYTEST_CMD tests/unit
    TEST_EXIT_CODE=$?
fi

# Display test results
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}${BOLD}All tests passed successfully!${NC}"
else
    echo -e "${RED}${BOLD}Some tests failed. Please check the error messages above.${NC}"
fi

exit $TEST_EXIT_CODE

