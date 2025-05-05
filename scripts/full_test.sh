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
echo -e "${BLUE}Creating necessary directories for tests...${NC}"
mkdir -p tests/integration/verified_codemods/codemod_data

# Parse command line arguments
RUN_UNIT=false
RUN_INTEGRATION=false
RUN_ALL=false
RUN_COVERAGE=false
RUN_VERBOSE=false
SPECIFIC_TEST=""
NUM_CORES=10  # Default to 10 cores for parallel testing

# If arguments are provided, use them
if [ $# -gt 0 ]; then
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
                echo -e "  --cores=N      Number of CPU cores to use (default: 10)"
                echo -e "  --help         Show this help message"
                echo -e ""
                echo -e "If no options are provided, interactive mode will be used."
                exit 0
                ;;
        esac
    done
else
    # Interactive mode - no arguments provided
    # Prompt for test type
    echo -e "${CYAN}${BOLD}Select test type:${NC}"
    echo -e "  ${CYAN}1) Unit tests${NC}"
    echo -e "  ${CYAN}2) Integration tests${NC}"
    echo -e "  ${CYAN}3) All tests${NC}"
    echo -e "  ${CYAN}4) Specific test${NC}"
    read -p "Enter your choice (1-4) [default: 1]: " test_type
    test_type=${test_type:-1}
    
    case $test_type in
        1)
            RUN_UNIT=true
            ;;
        2)
            RUN_INTEGRATION=true
            ;;
        3)
            RUN_ALL=true
            ;;
        4)
            echo -e "${CYAN}Enter the path to the specific test:${NC}"
            echo -e "${YELLOW}Example: tests/unit/sdk/core/test_file.py${NC}"
            read -p "Test path: " SPECIFIC_TEST
            
            if [ -z "$SPECIFIC_TEST" ]; then
                echo -e "${RED}No test path provided. Defaulting to unit tests.${NC}"
                RUN_UNIT=true
            elif [ ! -e "$SPECIFIC_TEST" ]; then
                echo -e "${RED}Test path does not exist: $SPECIFIC_TEST${NC}"
                echo -e "${YELLOW}Available test directories:${NC}"
                find tests -type d -maxdepth 2 | sort | sed 's/^/  /'
                echo -e "${YELLOW}Defaulting to unit tests.${NC}"
                RUN_UNIT=true
                SPECIFIC_TEST=""
            fi
            ;;
        *)
            echo -e "${RED}Invalid choice. Defaulting to unit tests.${NC}"
            RUN_UNIT=true
            ;;
    esac
    
    # Prompt for number of cores
    available_cores=$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)
    read -p "Number of CPU cores to use for parallel testing [default: ${available_cores}]: " num_cores_input
    if [ -n "$num_cores_input" ]; then
        NUM_CORES=$num_cores_input
    else
        NUM_CORES=$available_cores
    fi
    
    # Prompt for coverage
    read -p "Run with coverage? (y/n) [default: n]: " coverage_option
    if [[ "$coverage_option" =~ ^[Yy]$ ]]; then
        RUN_COVERAGE=true
    fi
    
    # Prompt for verbose output
    read -p "Run with verbose output? (y/n) [default: n]: " verbose_option
    if [[ "$verbose_option" =~ ^[Yy]$ ]]; then
        RUN_VERBOSE=true
    fi
    
    # Prompt for GitHub token if running integration tests or all tests
    if [ "$RUN_INTEGRATION" = true ] || [ "$RUN_ALL" = true ] || [[ "$SPECIFIC_TEST" == *"integration"* ]]; then
        # Check if GITHUB_TOKEN is already set
        if [ -z "$GITHUB_TOKEN" ]; then
            echo -e "${YELLOW}Some integration tests require GitHub authentication.${NC}"
            read -p "Enter GitHub token (leave empty to skip GitHub-dependent tests): " github_token
            
            if [ -n "$github_token" ]; then
                export GITHUB_TOKEN="$github_token"
                echo -e "${GREEN}GitHub token set. Tests requiring GitHub authentication will be run.${NC}"
            else
                echo -e "${YELLOW}No GitHub token provided. Tests requiring GitHub authentication may be skipped.${NC}"
            fi
        else
            echo -e "${GREEN}GitHub token is already set in the environment.${NC}"
        fi
    fi
fi

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

# Display test configuration
echo -e "${BLUE}${BOLD}=== Test Configuration ===${NC}"
if [ -n "$SPECIFIC_TEST" ]; then
    echo -e "${YELLOW}Test path:${NC} $SPECIFIC_TEST"
elif [ "$RUN_ALL" = true ]; then
    echo -e "${YELLOW}Test type:${NC} All tests"
elif [ "$RUN_UNIT" = true ] && [ "$RUN_INTEGRATION" = true ]; then
    echo -e "${YELLOW}Test type:${NC} Unit and integration tests"
elif [ "$RUN_INTEGRATION" = true ]; then
    echo -e "${YELLOW}Test type:${NC} Integration tests"
else
    echo -e "${YELLOW}Test type:${NC} Unit tests"
fi
echo -e "${YELLOW}Parallel processes:${NC} $NUM_CORES"
echo -e "${YELLOW}Coverage:${NC} $([ "$RUN_COVERAGE" = true ] && echo "Enabled" || echo "Disabled")"
echo -e "${YELLOW}Verbose output:${NC} $([ "$RUN_VERBOSE" = true ] && echo "Enabled" || echo "Disabled")"
echo -e "${YELLOW}GitHub authentication:${NC} $([ -n "$GITHUB_TOKEN" ] && echo "Configured" || echo "Not configured")"

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
