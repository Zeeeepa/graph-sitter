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
mkdir -p build/test-results/test

# Clean up any existing coverage files
echo -e "${BLUE}Cleaning up existing coverage files...${NC}"
rm -f .coverage .coverage.* .coverage-* htmlcov/* build/test-results/test/TEST.xml

# Parse command line arguments
RUN_UNIT=false
RUN_INTEGRATION=false
RUN_ALL=false
RUN_COVERAGE=false
RUN_VERBOSE=false
INTERACTIVE=false
SPECIFIC_TEST=""
NUM_CORES=$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)  # Auto-detect cores
MAX_MEMORY_GB=31
GITHUB_TOKEN_PROVIDED=false
HTML_REPORT=false

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
            --max-memory=*)
                MAX_MEMORY_GB="${arg#*=}"
                ;;
            --github-token=*)
                export GITHUB_TOKEN="${arg#*=}"
                GITHUB_TOKEN_PROVIDED=true
                ;;
            --html-report)
                HTML_REPORT=true
                RUN_COVERAGE=true
                ;;
            --help)
                echo -e "${CYAN}Usage: ./scripts/full_test.sh [OPTIONS]${NC}"
                echo -e "${CYAN}Options:${NC}"
                echo -e "  --unit                Run unit tests only"
                echo -e "  --integration         Run integration tests only"
                echo -e "  --all                 Run all tests"
                echo -e "  --coverage            Run with coverage"
                echo -e "  --verbose             Run with verbose output"
                echo -e "  --test=PATH           Run specific test file or directory"
                echo -e "  --cores=N             Number of CPU cores to use (default: auto-detect)"
                echo -e "  --max-memory=N        Maximum memory usage in GB (default: 31)"
                echo -e "  --github-token=TOKEN  GitHub token for authentication"
                echo -e "  --html-report         Generate HTML coverage report"
                echo -e "  --help                Show this help message"
                exit 0
                ;;
        esac
    done
else
    # No arguments provided, use interactive mode
    INTERACTIVE=true
fi

# Interactive mode
if [ "$INTERACTIVE" = true ]; then
    echo -e "${CYAN}${BOLD}Interactive Test Configuration${NC}"
    echo -e "${CYAN}Please provide the following information:${NC}"
    
    # Prompt for test type
    echo -e "${CYAN}Select test type:${NC}"
    echo -e "  ${CYAN}1) Unit tests only${NC}"
    echo -e "  ${CYAN}2) Integration tests only${NC}"
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
    echo -e "${CYAN}Number of CPU cores detected: ${NUM_CORES}${NC}"
    read -p "Number of CPU cores to use [default: ${NUM_CORES}]: " num_cores_input
    if [ -n "$num_cores_input" ]; then
        NUM_CORES=$num_cores_input
    fi
    
    # Prompt for coverage
    read -p "Run with coverage? (y/n) [default: n]: " coverage_option
    if [[ "$coverage_option" =~ ^[Yy]$ ]]; then
        RUN_COVERAGE=true
        
        # Prompt for HTML report
        read -p "Generate HTML coverage report? (y/n) [default: n]: " html_report_option
        if [[ "$html_report_option" =~ ^[Yy]$ ]]; then
            HTML_REPORT=true
        fi
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
                GITHUB_TOKEN_PROVIDED=true
                echo -e "${GREEN}GitHub token set. Tests requiring GitHub authentication will be run.${NC}"
            else
                echo -e "${YELLOW}No GitHub token provided. Tests requiring GitHub authentication may be skipped.${NC}"
            fi
        else
            echo -e "${GREEN}GitHub token is already set in the environment.${NC}"
            GITHUB_TOKEN_PROVIDED=true
        fi
    fi
    
    # Prompt for max memory
    read -p "Maximum memory usage in GB [default: 31]: " max_memory_input
    if [ -n "$max_memory_input" ]; then
        MAX_MEMORY_GB=$max_memory_input
    fi
fi

# Build the pytest command
PYTEST_CMD="python -m pytest"

# Add verbose flag if requested
if [ "$RUN_VERBOSE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -v"
fi

# Add JUnit XML report
PYTEST_CMD="$PYTEST_CMD --junitxml=build/test-results/test/TEST.xml"

# Add parallel processing if more than 1 core
if [ "$NUM_CORES" -gt 1 ]; then
    PYTEST_CMD="$PYTEST_CMD -n $NUM_CORES"
fi

# Add coverage if requested
if [ "$RUN_COVERAGE" = true ]; then
    # Configure coverage to avoid SQLite errors
    PYTEST_CMD="$PYTEST_CMD --cov=graph_sitter --cov-report=term --no-cov-on-fail"
    
    # Add HTML report if requested
    if [ "$HTML_REPORT" = true ]; then
        PYTEST_CMD="$PYTEST_CMD --cov-report=html"
    fi
    
    # Disable context for coverage to avoid SQLite errors
    export COVERAGE_CONTEXT=off
fi

# Function to monitor memory usage
monitor_memory() {
    local pid=$1
    local max_memory_gb=$MAX_MEMORY_GB
    
    echo -e "${BLUE}Starting memory monitor for PID $pid${NC}"
    echo -e "${BLUE}Maximum memory: $max_memory_gb GB${NC}"
    
    while ps -p $pid > /dev/null; do
        # Get memory usage in KB
        MEMORY_KB=$(ps -o rss= -p $pid)
        
        # Convert to GB with 2 decimal places
        MEMORY_GB=$(echo "scale=2; $MEMORY_KB / 1024 / 1024" | bc)
        
        # Check if memory exceeds threshold
        if (( $(echo "$MEMORY_GB > $max_memory_gb" | bc -l) )); then
            echo -e "${RED}${BOLD}Memory usage exceeded ${max_memory_gb} GB!${NC}"
            echo -e "${RED}Sending SIGTERM to process ${pid} to prevent segmentation fault${NC}"
            kill -15 $pid
            
            # If process doesn't terminate within 5 seconds, force kill it
            sleep 5
            if ps -p $pid > /dev/null; then
                echo -e "${RED}Process did not terminate gracefully. Sending SIGKILL.${NC}"
                kill -9 $pid
            fi
            
            return 1
        fi
        
        sleep 2
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
echo -e "${YELLOW}HTML coverage report:${NC} $([ "$HTML_REPORT" = true ] && echo "Enabled" || echo "Disabled")"
echo -e "${YELLOW}Verbose output:${NC} $([ "$RUN_VERBOSE" = true ] && echo "Enabled" || echo "Disabled")"
echo -e "${YELLOW}Maximum memory:${NC} $MAX_MEMORY_GB GB"

# Check if GitHub token is set
if [ "$GITHUB_TOKEN_PROVIDED" = true ]; then
    echo -e "${GREEN}GitHub token is set. Tests requiring GitHub authentication will be run.${NC}"
else
    echo -e "${YELLOW}No GitHub token provided. Tests requiring GitHub authentication may be skipped.${NC}"
fi

# Run tests based on the selected options
if [ -n "$SPECIFIC_TEST" ]; then
    # Run specific test
    echo -e "${BLUE}Running specific test: $SPECIFIC_TEST${NC}"
    
    # Run the tests
    $PYTEST_CMD $SPECIFIC_TEST &
    TEST_PID=$!
    
    # Monitor memory usage
    monitor_memory $TEST_PID
    
    # Wait for test to complete
    wait $TEST_PID || true
    TEST_EXIT_CODE=$?
elif [ "$RUN_ALL" = true ]; then
    # Run all tests
    echo -e "${BLUE}Running all tests...${NC}"
    echo -e "${YELLOW}Note: Some integration tests may be skipped if they require external resources${NC}"
    
    # Run the tests
    $PYTEST_CMD tests &
    TEST_PID=$!
    
    # Monitor memory usage
    monitor_memory $TEST_PID
    
    # Wait for test to complete
    wait $TEST_PID || true
    TEST_EXIT_CODE=$?
elif [ "$RUN_UNIT" = true ] && [ "$RUN_INTEGRATION" = true ]; then
    # Run both unit and integration tests
    echo -e "${BLUE}Running unit and integration tests...${NC}"
    
    # Run the tests
    $PYTEST_CMD tests/unit tests/integration &
    TEST_PID=$!
    
    # Monitor memory usage
    monitor_memory $TEST_PID
    
    # Wait for test to complete
    wait $TEST_PID || true
    TEST_EXIT_CODE=$?
elif [ "$RUN_INTEGRATION" = true ]; then
    # Run integration tests
    echo -e "${BLUE}Running integration tests...${NC}"
    
    # Run the tests
    $PYTEST_CMD tests/integration &
    TEST_PID=$!
    
    # Monitor memory usage
    monitor_memory $TEST_PID
    
    # Wait for test to complete
    wait $TEST_PID || true
    TEST_EXIT_CODE=$?
else
    # Run unit tests
    echo -e "${BLUE}Running unit tests...${NC}"
    
    # Run the tests
    $PYTEST_CMD tests/unit &
    TEST_PID=$!
    
    # Monitor memory usage
    monitor_memory $TEST_PID
    
    # Wait for test to complete
    wait $TEST_PID || true
    TEST_EXIT_CODE=$?
fi

# Display test results
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}${BOLD}All tests passed successfully!${NC}"
else
    echo -e "${RED}${BOLD}Some tests failed. Please check the error messages above.${NC}"
fi

exit $TEST_EXIT_CODE
