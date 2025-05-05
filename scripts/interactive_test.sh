#!/usr/bin/env bash
set -e

# Interactive Test Script for graph-sitter
# This script prompts for test parameters and runs comprehensive tests

# Display colorful messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m' # No Color

clear
echo -e "${BOLD}${BLUE}=== Graph-Sitter Interactive Test Suite ===${NC}"
echo -e "${YELLOW}This script will guide you through running tests for the graph-sitter repository.${NC}"
echo

# Ensure we're in the virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}No virtual environment detected. Activating...${NC}"
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    else
        echo -e "${RED}No .venv directory found. Would you like to run fullbuild.sh first? (y/n)${NC}"
        read -r setup_env
        if [[ "$setup_env" =~ ^[Yy]$ ]]; then
            bash ./scripts/fullbuild.sh
            source .venv/bin/activate
        else
            echo -e "${RED}Cannot proceed without a virtual environment. Exiting.${NC}"
            exit 1
        fi
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

# Prompt for test type
echo -e "${CYAN}${BOLD}Select test type:${NC}"
echo -e "  ${CYAN}1) Unit tests${NC}"
echo -e "  ${CYAN}2) Integration tests${NC}"
echo -e "  ${CYAN}3) All tests${NC}"
echo -e "  ${CYAN}4) Specific test${NC}"
read -p "Enter your choice (1-4) [default: 1]: " test_type
test_type=${test_type:-1}

# Prompt for number of cores
echo
echo -e "${CYAN}${BOLD}Number of CPU cores to use for parallel testing:${NC}"
available_cores=$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)
echo -e "${CYAN}(Detected ${available_cores} available cores)${NC}"
read -p "Enter number of cores [default: ${available_cores}]: " num_cores
num_cores=${num_cores:-$available_cores}

# Prompt for coverage
echo
echo -e "${CYAN}${BOLD}Would you like to generate a coverage report?${NC}"
read -p "Generate coverage report? (y/n) [default: n]: " coverage_option
coverage_option=${coverage_option:-n}

# Prompt for verbose output
echo
echo -e "${CYAN}${BOLD}Would you like verbose test output?${NC}"
read -p "Verbose output? (y/n) [default: n]: " verbose_option
verbose_option=${verbose_option:-n}

# Prompt for GitHub token if running integration tests
github_token=""
if [[ "$test_type" == "2" || "$test_type" == "3" ]]; then
    echo
    echo -e "${CYAN}${BOLD}GitHub authentication:${NC}"
    echo -e "${YELLOW}Some integration tests require GitHub authentication.${NC}"
    read -p "Would you like to provide a GitHub token? (y/n) [default: n]: " github_auth
    github_auth=${github_auth:-n}
    
    if [[ "$github_auth" =~ ^[Yy]$ ]]; then
        read -p "Enter your GitHub token: " github_token
        if [ -n "$github_token" ]; then
            export GITHUB_TOKEN="$github_token"
            echo -e "${GREEN}GitHub token set.${NC}"
        fi
    else
        echo -e "${YELLOW}No GitHub token provided. Some integration tests may be skipped or fail.${NC}"
    fi
fi

# Prompt for specific test if option 4 was selected
specific_test=""
if [[ "$test_type" == "4" ]]; then
    echo
    echo -e "${CYAN}${BOLD}Enter the path to the specific test:${NC}"
    echo -e "${YELLOW}Example: tests/unit/sdk/core/test_file.py${NC}"
    read -p "Test path: " specific_test
    
    if [ -z "$specific_test" ]; then
        echo -e "${RED}No test path provided. Exiting.${NC}"
        exit 1
    elif [ ! -e "$specific_test" ]; then
        echo -e "${RED}Test path does not exist: $specific_test${NC}"
        echo -e "${YELLOW}Available test directories:${NC}"
        find tests -type d -maxdepth 2 | sort | sed 's/^/  /'
        exit 1
    fi
fi

# Build pytest command
PYTEST_CMD="python -m pytest"

# Add verbosity
if [[ "$verbose_option" =~ ^[Yy]$ ]]; then
    PYTEST_CMD="$PYTEST_CMD -vv"
else
    PYTEST_CMD="$PYTEST_CMD -v"
fi

# Add parallel processing
PYTEST_CMD="$PYTEST_CMD -n $num_cores"

# Add coverage if requested
if [[ "$coverage_option" =~ ^[Yy]$ ]]; then
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

# Summary of selected options
echo
echo -e "${BLUE}${BOLD}=== Test Configuration ===${NC}"
case $test_type in
    1)
        echo -e "${YELLOW}Test type:${NC} Unit tests"
        ;;
    2)
        echo -e "${YELLOW}Test type:${NC} Integration tests"
        ;;
    3)
        echo -e "${YELLOW}Test type:${NC} All tests"
        ;;
    4)
        echo -e "${YELLOW}Test type:${NC} Specific test"
        echo -e "${YELLOW}Test path:${NC} $specific_test"
        ;;
esac
echo -e "${YELLOW}CPU cores:${NC} $num_cores"
echo -e "${YELLOW}Coverage:${NC} $(if [[ "$coverage_option" =~ ^[Yy]$ ]]; then echo "Yes"; else echo "No"; fi)"
echo -e "${YELLOW}Verbose:${NC} $(if [[ "$verbose_option" =~ ^[Yy]$ ]]; then echo "Yes"; else echo "No"; fi)"
echo -e "${YELLOW}GitHub auth:${NC} $(if [ -n "$github_token" ]; then echo "Yes"; else echo "No"; fi)"

# Confirm before running
echo
read -p "Proceed with these settings? (y/n) [default: y]: " confirm
confirm=${confirm:-y}

if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo -e "${RED}Test cancelled.${NC}"
    exit 0
fi

# Run the tests
echo
echo -e "${BLUE}${BOLD}=== Running Tests ===${NC}"

# Determine which tests to run
if [ -n "$specific_test" ]; then
    # Run specific test
    echo -e "${BLUE}Running specific test: ${specific_test}${NC}"
    $PYTEST_CMD "$specific_test" &
    TEST_PID=$!
elif [[ "$test_type" == "3" ]]; then
    # Run all tests
    echo -e "${BLUE}Running all tests with $num_cores parallel processes...${NC}"
    $PYTEST_CMD tests &
    TEST_PID=$!
elif [[ "$test_type" == "2" ]]; then
    # Run integration tests
    echo -e "${BLUE}Running integration tests with $num_cores parallel processes...${NC}"
    $PYTEST_CMD tests/integration &
    TEST_PID=$!
else
    # Run unit tests
    echo -e "${BLUE}Running unit tests with $num_cores parallel processes...${NC}"
    $PYTEST_CMD tests/unit &
    TEST_PID=$!
fi

# Monitor memory usage
monitor_memory $TEST_PID

# Wait for test to complete
wait $TEST_PID || true
TEST_EXIT_CODE=$?

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
echo -e "${YELLOW}Parallel processes:${NC} $num_cores"

# Display coverage report if requested
if [[ "$coverage_option" =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}${BOLD}=== Coverage Report ===${NC}"
    echo -e "${YELLOW}See above for detailed coverage information${NC}"
fi

exit $TEST_EXIT_CODE

