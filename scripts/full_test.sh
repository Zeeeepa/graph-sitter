#!/usr/bin/env bash
set -e

# Full Test Script for graph-sitter
# This script runs comprehensive test suites with detailed output

# Display colorful messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${BOLD}${BLUE}=== Graph-Sitter Comprehensive Test Suite ===${NC}"

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
RUN_INTEGRATION=false
RUN_ALL=false
RUN_COVERAGE=false
RUN_VERBOSE=false
SPECIFIC_TEST=""
NUM_CORES=20  # Default to 20 cores for parallel testing

for arg in "$@"; do
    case $arg in
        --unit)
            RUN_UNIT=true
            ;;
        --integration)
            RUN_INTEGRATION=true
            ;;
        --all)
            RUN_ALL=true
            ;;
        --coverage)
            RUN_COVERAGE=true
            ;;
        --verbose)
            RUN_VERBOSE=true
            ;;
        --test=*)
            SPECIFIC_TEST="${arg#*=}"
            ;;
        --cores=*)
            NUM_CORES="${arg#*=}"
            ;;
        --help)
            echo -e "${CYAN}Usage: ./scripts/full_test.sh [OPTIONS]${NC}"
            echo -e "${CYAN}Options:${NC}"
            echo -e "  --unit         Run unit tests"
            echo -e "  --integration  Run integration tests"
            echo -e "  --all          Run all tests"
            echo -e "  --coverage     Run with coverage"
            echo -e "  --verbose      Run with verbose output"
            echo -e "  --test=PATH    Run specific test file or directory"
            echo -e "  --cores=N      Number of CPU cores to use (default: 20)"
            echo -e "  --help         Show this help message"
            exit 0
            ;;
    esac
done

# Set default if no option provided
if [ "$RUN_UNIT" = false ] && [ "$RUN_INTEGRATION" = false ] && [ "$RUN_ALL" = false ] && [ -z "$SPECIFIC_TEST" ]; then
    echo -e "${YELLOW}No test option specified. Running unit tests by default.${NC}"
    RUN_UNIT=true
fi

# Build pytest command
PYTEST_CMD="python -m pytest"

# Add verbosity
if [ "$RUN_VERBOSE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -vv"
else
    PYTEST_CMD="$PYTEST_CMD -v"
fi

# Add parallel processing
PYTEST_CMD="$PYTEST_CMD -n $NUM_CORES"

# Add coverage if requested
if [ "$RUN_COVERAGE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=graph_sitter --cov-report=term"
fi

# Create a memory monitoring function
monitor_memory() {
    local pid=$1
    local max_memory_gb=31
    local sleep_interval=1
    
    while ps -p $pid > /dev/null; do
        local memory_kb=$(ps -o rss= -p $pid)
        local memory_gb=$(echo "scale=2; $memory_kb / 1024 / 1024" | bc)
        
        if (( $(echo "$memory_gb > $max_memory_gb" | bc -l) )); then
            echo -e "${RED}Memory usage exceeded $max_memory_gb GB! Killing process to prevent segmentation fault.${NC}"
            kill -15 $pid
            return 1
        fi
        
        sleep $sleep_interval
    done
    
    return 0
}

# Determine which tests to run
if [ -n "$SPECIFIC_TEST" ]; then
    # Run specific test
    echo -e "${BLUE}Running specific test: ${SPECIFIC_TEST}${NC}"
    $PYTEST_CMD "$SPECIFIC_TEST" &
    TEST_PID=$!
    
    # Monitor memory usage
    monitor_memory $TEST_PID
    
    # Wait for test to complete
    wait $TEST_PID
    TEST_EXIT_CODE=$?
elif [ "$RUN_ALL" = true ]; then
    # Run all tests
    echo -e "${BLUE}Running all tests with $NUM_CORES parallel processes...${NC}"
    
    # Run tests without skipping any
    $PYTEST_CMD tests &
    TEST_PID=$!
    
    # Monitor memory usage
    monitor_memory $TEST_PID
    
    # Wait for test to complete
    wait $TEST_PID
    TEST_EXIT_CODE=$?
elif [ "$RUN_UNIT" = true ] && [ "$RUN_INTEGRATION" = true ]; then
    # Run both unit and integration tests
    echo -e "${BLUE}Running unit and integration tests with $NUM_CORES parallel processes...${NC}"
    
    $PYTEST_CMD tests/unit tests/integration &
    TEST_PID=$!
    
    # Monitor memory usage
    monitor_memory $TEST_PID
    
    # Wait for test to complete
    wait $TEST_PID
    TEST_EXIT_CODE=$?
elif [ "$RUN_INTEGRATION" = true ]; then
    # Run integration tests
    echo -e "${BLUE}Running integration tests with $NUM_CORES parallel processes...${NC}"
    
    $PYTEST_CMD tests/integration &
    TEST_PID=$!
    
    # Monitor memory usage
    monitor_memory $TEST_PID
    
    # Wait for test to complete
    wait $TEST_PID
    TEST_EXIT_CODE=$?
else
    # Run unit tests
    echo -e "${BLUE}Running unit tests with $NUM_CORES parallel processes...${NC}"
    $PYTEST_CMD tests/unit &
    TEST_PID=$!
    
    # Monitor memory usage
    monitor_memory $TEST_PID
    
    # Wait for test to complete
    wait $TEST_PID
    TEST_EXIT_CODE=$?
fi

# Display test results
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}${BOLD}All tests passed successfully!${NC}"
else
    echo -e "${RED}${BOLD}Some tests failed. Please check the error messages above.${NC}"
fi

# Display summary
echo -e "${BLUE}${BOLD}=== Test Summary ===${NC}"
echo -e "${YELLOW}Test exit code:${NC} $TEST_EXIT_CODE"
echo -e "${YELLOW}Python version:${NC} $(python --version)"
echo -e "${YELLOW}Parallel processes:${NC} $NUM_CORES"

# Display coverage report if requested
if [ "$RUN_COVERAGE" = true ]; then
    echo -e "${BLUE}${BOLD}=== Coverage Report ===${NC}"
    echo -e "${YELLOW}See above for detailed coverage information${NC}"
fi

exit $TEST_EXIT_CODE
