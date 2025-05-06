#!/usr/bin/env bash
set -e

# Improved Test Script for graph-sitter
# This script provides a more reliable testing experience with better coverage handling

# Display colorful messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${BOLD}${BLUE}=== Graph-Sitter Improved Test Suite ===${NC}"

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

# Make memory monitor executable
chmod +x scripts/memory_monitor.sh

# Parse command line arguments
RUN_UNIT=false
RUN_INTEGRATION=false
RUN_ALL=false
RUN_COVERAGE=false
RUN_VERBOSE=false
SPECIFIC_TEST=""
NUM_CORES=$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)  # Auto-detect cores
SKIP_LARGE_REPOS=false
MAX_MEMORY_GB=31
FORCE_ALL=false
RETRY_COUNT=3
INCREMENTAL=false
SEQUENTIAL=false
FAIL_FAST=false
JUNIT_REPORT=true
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
            --skip-large-repos)
                SKIP_LARGE_REPOS=true
                ;;
            --max-memory-gb=*)
                MAX_MEMORY_GB="${arg#*=}"
                ;;
            --force-all)
                FORCE_ALL=true
                RUN_ALL=true
                ;;
            --retry=*)
                RETRY_COUNT="${arg#*=}"
                ;;
            --incremental)
                INCREMENTAL=true
                ;;
            --sequential)
                SEQUENTIAL=true
                NUM_CORES=1
                ;;
            --fail-fast)
                FAIL_FAST=true
                ;;
            --html-report)
                HTML_REPORT=true
                RUN_COVERAGE=true
                ;;
            --no-junit)
                JUNIT_REPORT=false
                ;;
            --help)
                echo -e "${CYAN}Usage: ./scripts/improved_test.sh [OPTIONS]${NC}"
                echo -e "${CYAN}Options:${NC}"
                echo -e "  --unit         Run unit tests"
                echo -e "  --integration  Run integration tests"
                echo -e "  --all          Run all tests"
                echo -e "  --coverage     Run with coverage"
                echo -e "  --verbose      Run with verbose output"
                echo -e "  --test=PATH    Run specific test file or directory"
                echo -e "  --cores=N      Number of CPU cores to use (default: auto-detect)"
                echo -e "  --skip-large-repos  Skip large repositories"
                echo -e "  --max-memory-gb=N  Maximum memory usage in GB (default: 31)"
                echo -e "  --force-all    Force run ALL tests including memory-intensive ones"
                echo -e "  --retry=N      Number of retries for tests that fail (default: 3)"
                echo -e "  --incremental  Run tests incrementally to avoid memory issues"
                echo -e "  --sequential   Run tests sequentially (sets --cores=1)"
                echo -e "  --fail-fast    Stop on first test failure"
                echo -e "  --html-report  Generate HTML coverage report"
                echo -e "  --no-junit     Disable JUnit XML report generation"
                echo -e "  --help         Show this help message"
                echo -e ""
                echo -e "If no options are provided, interactive mode will be used."
                exit 0
                ;;
        esac
    done
else
    # Interactive mode - no arguments provided
    echo -e "${CYAN}${BOLD}Interactive Test Configuration${NC}"
    echo -e "${CYAN}Please provide the following information:${NC}"
    
    # Prompt for test type
    echo -e "${CYAN}Select test type:${NC}"
    echo -e "  ${CYAN}1) Unit tests only${NC}"
    echo -e "  ${CYAN}2) Integration tests only${NC}"
    echo -e "  ${CYAN}3) All tests${NC}"
    echo -e "  ${CYAN}4) Specific test${NC}"
    echo -e "  ${CYAN}5) Force ALL tests (including memory-intensive ones)${NC}"
    read -p "Enter your choice (1-5) [default: 1]: " test_type
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
        5)
            RUN_ALL=true
            FORCE_ALL=true
            ;;
        *)
            echo -e "${RED}Invalid choice. Defaulting to unit tests.${NC}"
            RUN_UNIT=true
            ;;
    esac
    
    # Prompt for number of cores
    echo -e "${CYAN}Number of CPU cores detected: ${NUM_CORES}${NC}"
    read -p "Number of CPU cores to use for parallel testing [default: ${NUM_CORES}]: " num_cores_input
    if [ -n "$num_cores_input" ]; then
        NUM_CORES=$num_cores_input
    fi
    
    # Prompt for sequential mode
    read -p "Run tests sequentially? (y/n) [default: n]: " sequential_option
    if [[ "$sequential_option" =~ ^[Yy]$ ]]; then
        SEQUENTIAL=true
        NUM_CORES=1
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
    
    # Prompt for fail-fast
    read -p "Stop on first test failure? (y/n) [default: n]: " fail_fast_option
    if [[ "$fail_fast_option" =~ ^[Yy]$ ]]; then
        FAIL_FAST=true
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
    
    # Prompt for skipping large repos if not forcing all tests
    if [ "$FORCE_ALL" = false ]; then
        read -p "Skip large repositories (like mypy) to prevent segmentation faults? (y/n) [default: n]: " skip_large_option
        if [[ "$skip_large_option" =~ ^[Yy]$ ]]; then
            SKIP_LARGE_REPOS=true
        fi
    fi
    
    # Prompt for max memory
    read -p "Maximum memory usage in GB [default: 31]: " max_memory_input
    if [ -n "$max_memory_input" ]; then
        MAX_MEMORY_GB=$max_memory_input
    fi
    
    # Prompt for incremental testing
    read -p "Run tests incrementally to avoid memory issues? (y/n) [default: n]: " incremental_option
    if [[ "$incremental_option" =~ ^[Yy]$ ]]; then
        INCREMENTAL=true
    fi
    
    # Prompt for retry count
    read -p "Number of retries for tests that fail [default: 3]: " retry_input
    if [ -n "$retry_input" ]; then
        RETRY_COUNT=$retry_input
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

# Add parallel processing if not sequential
if [ "$SEQUENTIAL" = false ]; then
    PYTEST_CMD="$PYTEST_CMD -n $NUM_CORES"
fi

# Add fail-fast if requested
if [ "$FAIL_FAST" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -x"
fi

# Add JUnit report if requested
if [ "$JUNIT_REPORT" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --junitxml=build/test-results/test/TEST.xml"
fi

# Add coverage if requested
if [ "$RUN_COVERAGE" = true ]; then
    # Use a better coverage configuration to avoid SQLite errors
    PYTEST_CMD="$PYTEST_CMD --cov=graph_sitter --cov-report=term --no-cov-on-fail"
    
    # Add HTML report if requested
    if [ "$HTML_REPORT" = true ]; then
        PYTEST_CMD="$PYTEST_CMD --cov-report=html"
    fi
    
    # Disable context for coverage to avoid SQLite errors
    export COVERAGE_CONTEXT=off
    
    # Set coverage config to avoid SQLite errors
    export COVERAGE_CORE=singleprocess
else
    # Disable coverage plugins to avoid errors when not using coverage
    PYTEST_CMD="$PYTEST_CMD -p no:cov"
fi

# Add skip for large repositories if requested and not forcing all tests
if [ "$SKIP_LARGE_REPOS" = true ] && [ "$FORCE_ALL" = false ]; then
    echo -e "${YELLOW}Skipping large repositories to prevent segmentation faults${NC}"
    # Skip mypy and other large repositories that cause segmentation faults
    PYTEST_CMD="$PYTEST_CMD -k 'not mypy'"
fi

# Create a log directory for memory monitoring
mkdir -p /tmp/graph-sitter-logs

# Create a memory monitoring function with improved handling
monitor_memory() {
    local pid=$1
    local max_memory_gb=$MAX_MEMORY_GB
    local log_file="/tmp/graph-sitter-logs/memory_usage_${pid}.log"
    
    # Start memory monitor in background
    scripts/memory_monitor.sh $pid $max_memory_gb 2 > $log_file 2>&1 &
    local monitor_pid=$!
    
    # Return the monitor PID so it can be killed later
    echo $monitor_pid
}

# Function to run tests with retry
run_tests_with_retry() {
    local cmd="$1"
    local test_name="$2"
    local retry_count=$RETRY_COUNT
    local success=false
    
    echo -e "${BLUE}Running $test_name...${NC}"
    
    for i in $(seq 1 $retry_count); do
        if [ $i -gt 1 ]; then
            echo -e "${YELLOW}Retry attempt $i of $retry_count...${NC}"
        fi
        
        # Run the test command
        echo -e "${CYAN}Command: $cmd${NC}"
        
        # Start memory monitor
        eval $cmd &
        TEST_PID=$!
        
        # Monitor memory usage
        MONITOR_PID=$(monitor_memory $TEST_PID)
        
        # Wait for test to complete
        wait $TEST_PID
        TEST_EXIT_CODE=$?
        
        # Kill memory monitor
        kill $MONITOR_PID 2>/dev/null || true
        
        echo -e "${BLUE}Process completed. Memory usage log saved to: /tmp/graph-sitter-logs/memory_usage_${TEST_PID}.log${NC}"
        
        if [ $TEST_EXIT_CODE -eq 0 ]; then
            echo -e "${GREEN}Tests passed successfully!${NC}"
            success=true
            break
        else
            echo -e "${RED}Tests failed on attempt $i with exit code $TEST_EXIT_CODE${NC}"
            
            # If this was the last attempt, exit with failure
            if [ $i -eq $retry_count ]; then
                echo -e "${RED}All retry attempts failed.${NC}"
                return $TEST_EXIT_CODE
            fi
            
            # Wait before retrying
            echo -e "${YELLOW}Waiting 5 seconds before retrying...${NC}"
            sleep 5
        fi
    done
    
    if [ "$success" = true ]; then
        return 0
    else
        return 1
    fi
}

# Function to run tests incrementally
run_tests_incrementally() {
    local test_path="$1"
    local success=true
    local failed_tests=()
    
    echo -e "${BLUE}Running tests incrementally to avoid memory issues...${NC}"
    
    # Get all test files
    local test_files=$(find "$test_path" -name "test_*.py" | sort)
    local total_files=$(echo "$test_files" | wc -l)
    local current=0
    
    echo -e "${YELLOW}Found $total_files test files${NC}"
    
    # Run each test file individually
    for test_file in $test_files; do
        current=$((current + 1))
        echo -e "${BLUE}[$current/$total_files] Running test: $test_file${NC}"
        
        # Build command for this test file
        local file_cmd="$PYTEST_CMD $test_file"
        
        # Run the test with retry
        run_tests_with_retry "$file_cmd" "$(basename $test_file)"
        TEST_EXIT_CODE=$?
        
        if [ $TEST_EXIT_CODE -ne 0 ]; then
            echo -e "${RED}Test failed: $test_file${NC}"
            failed_tests+=("$test_file")
            success=false
            
            # Stop if fail-fast is enabled
            if [ "$FAIL_FAST" = true ]; then
                echo -e "${RED}Stopping due to fail-fast option${NC}"
                break
            fi
        else
            echo -e "${GREEN}Test passed: $test_file${NC}"
        fi
        
        # Clean up between tests
        echo -e "${BLUE}Cleaning up between tests...${NC}"
        rm -f .coverage .coverage.* .coverage-*
        
        # Wait a moment to let memory be released
        sleep 2
    done
    
    # Report failed tests
    if [ "$success" = false ]; then
        echo -e "${RED}${BOLD}The following tests failed:${NC}"
        for failed_test in "${failed_tests[@]}"; do
            echo -e "${RED}- $failed_test${NC}"
        done
        return 1
    else
        echo -e "${GREEN}${BOLD}All tests passed!${NC}"
        return 0
    fi
}

# Display test configuration
echo -e "${BLUE}${BOLD}=== Test Configuration ===${NC}"
if [ -n "$SPECIFIC_TEST" ]; then
    echo -e "${YELLOW}Test path:${NC} $SPECIFIC_TEST"
elif [ "$RUN_ALL" = true ]; then
    echo -e "${YELLOW}Test type:${NC} All tests"
    if [ "$FORCE_ALL" = true ]; then
        echo -e "${YELLOW}Force ALL:${NC} Yes (including memory-intensive tests)"
    fi
elif [ "$RUN_UNIT" = true ] && [ "$RUN_INTEGRATION" = true ]; then
    echo -e "${YELLOW}Test type:${NC} Unit and integration tests"
elif [ "$RUN_INTEGRATION" = true ]; then
    echo -e "${YELLOW}Test type:${NC} Integration tests"
else
    echo -e "${YELLOW}Test type:${NC} Unit tests"
fi
echo -e "${YELLOW}Parallel processes:${NC} $NUM_CORES"
echo -e "${YELLOW}Sequential mode:${NC} $([ "$SEQUENTIAL" = true ] && echo "Enabled" || echo "Disabled")"
echo -e "${YELLOW}Coverage:${NC} $([ "$RUN_COVERAGE" = true ] && echo "Enabled" || echo "Disabled")"
echo -e "${YELLOW}HTML coverage report:${NC} $([ "$HTML_REPORT" = true ] && echo "Enabled" || echo "Disabled")"
echo -e "${YELLOW}JUnit XML report:${NC} $([ "$JUNIT_REPORT" = true ] && echo "Enabled" || echo "Disabled")"
echo -e "${YELLOW}Verbose output:${NC} $([ "$RUN_VERBOSE" = true ] && echo "Enabled" || echo "Disabled")"
echo -e "${YELLOW}Fail-fast:${NC} $([ "$FAIL_FAST" = true ] && echo "Enabled" || echo "Disabled")"
echo -e "${YELLOW}GitHub authentication:${NC} $([ -n "$GITHUB_TOKEN" ] && echo "Configured" || echo "Not configured")"
echo -e "${YELLOW}Skip large repositories:${NC} $([ "$SKIP_LARGE_REPOS" = true ] && [ "$FORCE_ALL" = false ] && echo "Yes" || echo "No")"
echo -e "${YELLOW}Maximum memory:${NC} ${MAX_MEMORY_GB} GB"
echo -e "${YELLOW}Retry count:${NC} ${RETRY_COUNT}"
echo -e "${YELLOW}Incremental testing:${NC} $([ "$INCREMENTAL" = true ] && echo "Enabled" || echo "Disabled")"

# Create temporary directories for integration tests
if [ "$RUN_INTEGRATION" = true ] || [ "$RUN_ALL" = true ] || [[ "$SPECIFIC_TEST" == *"integration"* ]]; then
    echo -e "${BLUE}Creating temporary directories for integration tests...${NC}"
    
    # Create base pytest directory
    mkdir -p /tmp/pytest-of-$(whoami)/pytest-0
    
    # Create directories for specific tests that need them
    for dir in "test_reset_unstaged_modificati0" "test_reset_unstaged_new_files_0" "test_reset_staged_changes_0" \
               "test_reset_staged_deletions_0" "test_reset_staged_renames_0" "test_reset_unstaged_renames_0" \
               "test_reset_staged_rename_with_0" "test_reset_with_mixed_states0" "test_reset_with_mixed_renames0" \
               "test_codebase_create_pr_active0"; do
        mkdir -p "/tmp/pytest-of-$(whoami)/pytest-0/$dir"
        echo -e "${GREEN}Created: /tmp/pytest-of-$(whoami)/pytest-0/$dir${NC}"
    done
    
    # Create symlinks for higher pytest directories (1-30)
    for i in {1..30}; do
        if [ ! -L "/tmp/pytest-of-$(whoami)/pytest-$i" ]; then
            ln -sf "/tmp/pytest-of-$(whoami)/pytest-0" "/tmp/pytest-of-$(whoami)/pytest-$i"
            echo -e "${GREEN}Created symlink: /tmp/pytest-of-$(whoami)/pytest-$i -> /tmp/pytest-of-$(whoami)/pytest-0${NC}"
        fi
    done
    
    # Start a background process to create symlinks for new pytest directories
    (
        while true; do
            for i in {31..100}; do
                if [ -d "/tmp/pytest-of-$(whoami)/pytest-$i" ] && [ ! -L "/tmp/pytest-of-$(whoami)/pytest-$i" ]; then
                    rm -rf "/tmp/pytest-of-$(whoami)/pytest-$i"
                    ln -sf "/tmp/pytest-of-$(whoami)/pytest-0" "/tmp/pytest-of-$(whoami)/pytest-$i"
                    echo -e "${GREEN}Created symlink: /tmp/pytest-of-$(whoami)/pytest-$i -> /tmp/pytest-of-$(whoami)/pytest-0${NC}"
                fi
            done
            sleep 1
        done
    ) &
    SYMLINK_PID=$!
    
    # Trap to kill the background process when the script exits
    trap "kill $SYMLINK_PID 2>/dev/null" EXIT
fi

# Determine which tests to run
if [ -n "$SPECIFIC_TEST" ]; then
    # Run specific test
    echo -e "${BLUE}Running specific test: ${SPECIFIC_TEST}${NC}"
    
    if [ "$INCREMENTAL" = true ] && [ -d "$SPECIFIC_TEST" ]; then
        # Run incrementally if it's a directory
        run_tests_incrementally "$SPECIFIC_TEST"
        TEST_EXIT_CODE=$?
    else
        # Run with retry
        run_tests_with_retry "$PYTEST_CMD \"$SPECIFIC_TEST\"" "specific test"
        TEST_EXIT_CODE=$?
    fi
elif [ "$RUN_ALL" = true ]; then
    # Run all tests
    echo -e "${BLUE}Running all tests with $NUM_CORES parallel processes...${NC}"
    echo -e "${YELLOW}Note: This may take a while and consume significant memory${NC}"
    
    if [ "$INCREMENTAL" = true ]; then
        # Run unit tests incrementally
        echo -e "${BLUE}Running unit tests incrementally...${NC}"
        run_tests_incrementally "tests/unit"
        UNIT_EXIT_CODE=$?
        
        # Run integration tests incrementally
        echo -e "${BLUE}Running integration tests incrementally...${NC}"
        run_tests_incrementally "tests/integration"
        INTEGRATION_EXIT_CODE=$?
        
        # Combine exit codes
        if [ $UNIT_EXIT_CODE -ne 0 ] || [ $INTEGRATION_EXIT_CODE -ne 0 ]; then
            TEST_EXIT_CODE=1
        else
            TEST_EXIT_CODE=0
        fi
    else
        # Run with retry
        run_tests_with_retry "$PYTEST_CMD tests" "all tests"
        TEST_EXIT_CODE=$?
    fi
elif [ "$RUN_UNIT" = true ] && [ "$RUN_INTEGRATION" = true ]; then
    # Run both unit and integration tests
    echo -e "${BLUE}Running unit and integration tests with $NUM_CORES parallel processes...${NC}"
    
    if [ "$INCREMENTAL" = true ]; then
        # Run unit tests incrementally
        echo -e "${BLUE}Running unit tests incrementally...${NC}"
        run_tests_incrementally "tests/unit"
        UNIT_EXIT_CODE=$?
        
        # Run integration tests incrementally
        echo -e "${BLUE}Running integration tests incrementally...${NC}"
        run_tests_incrementally "tests/integration"
        INTEGRATION_EXIT_CODE=$?
        
        # Combine exit codes
        if [ $UNIT_EXIT_CODE -ne 0 ] || [ $INTEGRATION_EXIT_CODE -ne 0 ]; then
            TEST_EXIT_CODE=1
        else
            TEST_EXIT_CODE=0
        fi
    else
        # Run with retry
        run_tests_with_retry "$PYTEST_CMD tests/unit tests/integration" "unit and integration tests"
        TEST_EXIT_CODE=$?
    fi
elif [ "$RUN_INTEGRATION" = true ]; then
    # Run integration tests
    echo -e "${BLUE}Running integration tests with $NUM_CORES parallel processes...${NC}"
    
    if [ "$INCREMENTAL" = true ]; then
        # Run incrementally
        run_tests_incrementally "tests/integration"
        TEST_EXIT_CODE=$?
    else
        # Run with retry
        run_tests_with_retry "$PYTEST_CMD tests/integration" "integration tests"
        TEST_EXIT_CODE=$?
    fi
else
    # Run unit tests
    echo -e "${BLUE}Running unit tests with $NUM_CORES parallel processes...${NC}"
    
    if [ "$INCREMENTAL" = true ]; then
        # Run incrementally
        run_tests_incrementally "tests/unit"
        TEST_EXIT_CODE=$?
    else
        # Run with retry
        run_tests_with_retry "$PYTEST_CMD tests/unit" "unit tests"
        TEST_EXIT_CODE=$?
    fi
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
    
    if [ "$HTML_REPORT" = true ]; then
        echo -e "${YELLOW}HTML coverage report generated in:${NC} htmlcov/index.html"
    fi
fi

exit $TEST_EXIT_CODE

