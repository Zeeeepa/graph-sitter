#!/usr/bin/env bash
set -e

# Build and Test Script for graph-sitter
# This script compiles Cython modules and runs tests

# Display colorful messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Graph-Sitter Build and Test Script ===${NC}"

# Ensure we're in the virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}No virtual environment detected. Activating...${NC}"
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    else
        echo -e "${RED}No .venv directory found. Please run 'uv venv' first.${NC}"
        exit 1
    fi
fi

# Install Cython if not already installed
echo -e "${YELLOW}Checking for Cython...${NC}"
if ! python -c "import Cython" &> /dev/null; then
    echo -e "${YELLOW}Installing Cython...${NC}"
    uv pip install cython
fi

# Compile Cython modules
echo -e "${YELLOW}Compiling Cython modules...${NC}"
python -m pip install -e .

# Check if compilation was successful
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Cython modules compiled successfully!${NC}"
else
    echo -e "${RED}Failed to compile Cython modules. Please check the error messages above.${NC}"
    exit 1
fi

# Run tests if requested
if [ "$1" == "--test" ] || [ "$1" == "-t" ]; then
    echo -e "${YELLOW}Running tests...${NC}"
    
    # Disable problematic plugins to avoid issues
    python -m pytest tests/unit -v -p no:xdist -p no:cov
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}All tests passed!${NC}"
    else
        echo -e "${RED}Some tests failed. Please check the error messages above.${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}Build completed successfully!${NC}"
echo -e "${YELLOW}You can now run tests with:${NC}"
echo -e "  python -m pytest tests/unit -v -p no:xdist -p no:cov"
echo -e "  python -m pytest tests/unit/specific/path/to/test_file.py -v -p no:xdist -p no:cov"
echo -e "${YELLOW}Or run with coverage:${NC}"
echo -e "  python -m pytest tests --cov=graph_sitter"

